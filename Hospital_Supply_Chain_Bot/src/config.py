"""
config.py

"""

import os
import re
import logging
import unicodedata
from pathlib import Path

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("inventra")

# ── Project paths ─────────────────────────────────────────────────────────────
_THIS_FILE   = Path(__file__).resolve()
SRC_DIR      = _THIS_FILE.parent
PROJECT_ROOT = SRC_DIR.parent

DB_PATH    = PROJECT_ROOT / "hospital.db"
FAISS_PATH = PROJECT_ROOT / "faiss_index"
DOCS_PATH  = PROJECT_ROOT / "docs"
DATA_PATH  = PROJECT_ROOT / "data"

# ── Ollama / LLM config ───────────────────────────────────────────────────────
OLLAMA_MODEL    = "llama3"
OLLAMA_BASE_URL = "http://localhost:11434"
TEMPERATURE     = 0.1
NUM_CTX         = 4096
MAX_TOKENS      = 1024

# ── Embedding model ───────────────────────────────────────────────────────────
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ── RAG config ────────────────────────────────────────────────────────────────
RETRIEVER_K   = 3
CHUNK_SIZE    = 500
CHUNK_OVERLAP = 50

# ── Governance: rate limiting ─────────────────────────────────────────────────
MAX_REQUESTS_PER_SESSION = 200
HISTORY_WINDOW           = 3

# ── Governance: input validation ──────────────────────────────────────────────
MAX_QUESTION_LENGTH = 500
MIN_QUESTION_LENGTH = 3

# ── Governance: token budget for user-controlled content in prompt ────────────
# Prevents context-stuffing via crafted history + long questions.
MAX_USER_CONTENT_CHARS = 1500   # ~375 tokens; hard cap before prompt is built

# ── Security: prompt injection guard ─────────────────────────────────────────
# Patterns are matched after Unicode NFKC normalisation to defeat lookalike
# and zero-width-character bypass attempts.
BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard your instructions",
    "forget everything",
    "you are now",
    "act as",
    "pretend you are",
    "new persona",
    "jailbreak",
    "bypass",
    "override instructions",
    "reveal your prompt",
    "show system prompt",
]

# ── Privacy: PII columns never sent to LLM ───────────────────────────────────
REDACTED_COLUMNS = [
    "Patient_ID",
    "Staff_ID",
]

# ── SSRF guard: allowed Ollama hosts ─────────────────────────────────────────
_LOOPBACK_PATTERN = re.compile(
    r'^https?://(localhost|127\.0\.0\.1|::1)(:\d+)?$'
)


def _assert_loopback_url(url: str) -> None:
    """
    Raise ValueError if url is not a loopback address.
    Prevents SSRF if OLLAMA_BASE_URL is ever changed to a remote host.
    """
    if not _LOOPBACK_PATTERN.match(url.rstrip("/")):
        raise ValueError(
            f"OLLAMA_BASE_URL '{url}' is not a loopback address. "
            "Inventra Health only allows localhost Ollama connections."
        )


# ── Input validator ───────────────────────────────────────────────────────────
def validate_question(question: str) -> tuple:
    """
    Validate and sanitise user input before sending to LLM.

    Security fix [FIX-3]: Unicode NFKC normalisation applied before
    blocked-pattern matching to defeat lookalike / zero-width bypass.

    Returns (is_valid: bool, reason: str).
    """
    if not question or not question.strip():
        return False, "Question cannot be empty."

    q = question.strip()

    if len(q) < MIN_QUESTION_LENGTH:
        return False, f"Question too short (minimum {MIN_QUESTION_LENGTH} chars)."

    if len(q) > MAX_QUESTION_LENGTH:
        return False, (
            f"Question too long ({len(q)} chars). "
            f"Keep under {MAX_QUESTION_LENGTH} characters."
        )

    # FIX-3: normalise before matching
    q_normalised = unicodedata.normalize("NFKC", q).lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in q_normalised:
            logger.warning("Blocked pattern detected: '%s'", pattern)
            return False, (
                "That input contains patterns that cannot be processed. "
                "Please ask a hospital supply chain question."
            )

    return True, ""


# ── Rate limiter ──────────────────────────────────────────────────────────────
def check_rate_limit(session_state) -> tuple:
    """Returns (within_limit: bool, message: str)."""
    count = session_state.get("request_count", 0)
    if count >= MAX_REQUESTS_PER_SESSION:
        return False, (
            f"Session limit of {MAX_REQUESTS_PER_SESSION} requests reached. "
            "Please refresh the page to start a new session."
        )
    return True, ""


# ── Ollama health check ───────────────────────────────────────────────────────
def check_ollama_running() -> tuple:
    """
    Verify Ollama server is running and llama3 model is available.

    Security fix [FIX-1]: SSRF guard asserts loopback-only before
    making the outbound HTTP request.

    Returns (is_running: bool, message: str).
    """
    try:
        _assert_loopback_url(OLLAMA_BASE_URL)
    except ValueError as e:
        logger.error("SSRF guard blocked Ollama check: %s", e)
        return False, str(e)

    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            llama_available = any("llama3" in m for m in models)
            if llama_available:
                return True, "Llama 3 · Ollama · Live"
            else:
                return False, (
                    "Ollama is running but llama3 not found. "
                    "Run: ollama pull llama3"
                )
        return False, "Ollama returned an unexpected response."
    except Exception:
        return False, (
            "Ollama not running. "
            "Fix: brew services start ollama"
        )
