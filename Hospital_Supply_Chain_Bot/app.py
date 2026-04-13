"""
app.py
------
Inventra Health — Streamlit UI (local Ollama version).

Security fixes applied:
  [FIX-6] XSS via user input: all user-supplied text is escaped with
          html.escape() before injection into unsafe_allow_html blocks.
  [FIX-7] XSS via LLM output: all LLM-derived text segments in
          render_bot_bubble() are escaped with html.escape() before
          embedding in HTML strings rendered inside iframes.

Run:
    streamlit run app.py

Requirements:
    brew services start ollama
    ollama pull llama3
"""

import os
import re
import sys
from html import escape   

import streamlit as st
import streamlit.components.v1 as components

_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.append(_BASE)   #avoids shadow-import risk

from src.config    import validate_question, check_rate_limit, check_ollama_running
from src.database  import get_kpi_counts, get_critical_items
from src.retriever import load_retriever
from src.chain     import load_llm, ask

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Inventra Health · Supply Chain Intelligence",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #070b14;
    color: #e2e8f0;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }
section[data-testid="stSidebar"] {
    background: #0d1226 !important;
    border-right: 1px solid #1e2d5a !important;
}
.top-header {
    background: #0d1226;
    border-bottom: 1px solid #1e2d5a;
    padding: 14px 28px;
    display: flex; align-items: center; justify-content: space-between;
}
.brand-wrap { display: flex; align-items: center; gap: 14px; }
.brand-icon {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, #3b5bdb 0%, #7c3aed 100%);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center; font-size: 20px;
}
.brand-title { font-family: 'Space Mono', monospace; font-size: 18px; font-weight: 700; color: #e8eaf6; }
.brand-subtitle { font-size: 10px; color: #4a5568; letter-spacing:.12em; text-transform:uppercase; margin-top:2px; }
.status-row { display: flex; align-items: center; gap: 6px; font-size: 11px; }
.status-ok  { color: #4db6ac; }
.status-err { color: #f48fb1; }
.pulse-dot { width:8px; height:8px; border-radius:50%; background:#1D9E75; box-shadow:0 0 6px #1D9E75; }
.pulse-err { width:8px; height:8px; border-radius:50%; background:#f44336; box-shadow:0 0 6px #f44336; }
.kpi-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:16px; }
.kpi-card {
    background:#111827; border:1px solid #1e2d5a;
    border-radius:10px; padding:12px 14px;
    transition: border-color .2s, transform .15s;
}
.kpi-card:hover { border-color:#3b5bdb; transform:translateY(-1px); }
.kpi-val { font-family:'Space Mono',monospace; font-size:22px; font-weight:700; color:#e8eaf6; line-height:1; }
.kpi-label { font-size:10px; color:#5c7cfa; margin-top:4px; }
.kpi-badge { display:inline-block; font-size:9px; font-weight:600; padding:2px 7px; border-radius:20px; margin-top:5px; }
.badge-red   { background:#2d1b1b; color:#f48fb1; }
.badge-amber { background:#2d2200; color:#ffcc80; }
.badge-green { background:#1b2d1b; color:#a5d6a7; }
.alert-card {
    background:#0f172a; border:1px solid #1e2d5a;
    border-left:3px solid #f44336; border-radius:8px;
    padding:9px 12px; margin-bottom:6px; font-size:12px; color:#94a3b8;
}
.alert-card.warn { border-left-color:#ff9800; }
.alert-name { font-weight:600; color:#e2e8f0; font-size:13px; }
.sec-label {
    font-size:9px; font-weight:600; color:#2d4a8a;
    letter-spacing:.12em; text-transform:uppercase; margin:14px 0 8px;
}
.stButton > button {
    width:100% !important; background:#111827 !important;
    border:1px solid #1e2d5a !important; border-radius:8px !important;
    color:#7986cb !important; font-size:12px !important;
    padding:8px 12px !important; text-align:left !important;
    transition:all .15s !important; margin-bottom:4px !important;
}
.stButton > button:hover { background:#1e2d5a !important; border-color:#3b5bdb !important; color:#90caf9 !important; }
.stButton > button[kind="primary"] {
    background:linear-gradient(135deg,#3b5bdb,#7c3aed) !important;
    border:none !important; color:#fff !important;
    font-weight:600 !important; text-align:center !important;
}
.stButton > button[kind="primary"]:hover { opacity:.9 !important; }
.chat-wrap { padding:20px 28px; min-height:400px; }
.msg-user {
    display:flex; gap:12px; align-items:flex-start;
    flex-direction:row-reverse; margin-bottom:6px;
}
.av-user {
    width:32px; height:32px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:11px; font-weight:700; flex-shrink:0;
    font-family:'Space Mono',monospace;
    background:#1e2d5a; color:#90caf9;
}
.bubble-user {
    max-width:80%; padding:12px 16px;
    border-radius:14px; border-top-right-radius:4px;
    font-size:13px; line-height:1.65;
    background:#1e2d5a; color:#90caf9;
}
.bubble-err {
    background:#2d1212; border:1px solid #4d1f1f;
    color:#f48fb1; padding:10px 14px; border-radius:10px;
    font-size:13px; margin:4px 0;
}
.input-area { border-top:1px solid #1a2547; padding:16px 28px; background:#080c18; }
.stTextInput > div > div > input {
    background:#111827 !important; border:1px solid #1e2d5a !important;
    border-radius:10px !important; color:#e2e8f0 !important;
    font-size:13px !important; padding:12px 16px !important;
}
.stTextInput > div > div > input:focus { border-color:#3b5bdb !important; box-shadow:0 0 0 2px rgba(59,91,219,.15) !important; }
.stTextInput > div > div > input::placeholder { color:#2d4a8a !important; }
hr { border-color:#1a2547 !important; }
[data-testid="stSidebarContent"] { padding:16px 14px !important; }
.stSpinner > div { border-top-color:#3b5bdb !important; }
.offline-warn {
    background:#2d2200; border:1px solid #4d3800;
    border-radius:10px; padding:14px 18px;
    color:#ffcc80; font-size:13px; margin:12px 28px; line-height:1.6;
}
iframe { border:none !important; background:transparent !important; }
</style>
""", unsafe_allow_html=True)


# ── Shared iframe styles injected into every component ────────────────────────
_IFRAME_BASE = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: transparent;
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
    line-height: 1.65;
    color: #cbd5e1;
    padding: 0;
    overflow: hidden;
  }
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
</style>
"""


# ── Bot bubble renderer ───────────────────────────────────────────────────────
def render_bot_bubble(text: str) -> str:
    """
    Parse structured plain-text LLM response.
    Returns HTML string for injection into components.html iframe.

    Security fix [FIX-7]: every LLM-derived text segment is passed
    through html.escape() before being embedded in the HTML string.
    This prevents prompt-injection or hallucinated HTML from executing
    inside the iframe.
    """
    SECTIONS = {
        "summary":             ("#5c7cfa", "#0d1f3c"),
        "top issues":          ("#f48fb1", "#2d1212"),
        "vendor issues":       ("#f48fb1", "#2d1212"),
        "actions":             ("#a5d6a7", "#1b2d1b"),
        "operational actions": ("#a5d6a7", "#1b2d1b"),
        "key findings":        ("#ffcc80", "#2d2200"),
        "opportunities":       ("#ffcc80", "#2d2200"),
        "next steps":          ("#a5d6a7", "#1b2d1b"),
    }

    lines   = text.split("\n")
    html    = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if in_list:
                html.append("</div>")
                in_list = False
            html.append('<div style="height:8px"></div>')
            continue

        lower = stripped.lower().rstrip(":")
        if lower in SECTIONS:
            if in_list:
                html.append("</div>")
                in_list = False
            color, bg = SECTIONS[lower]
            label = escape(stripped.rstrip(":"))   # FIX-7
            html.append(
                f'<div style="display:inline-block;background:{bg};color:{color};'
                f'font-size:10px;font-weight:600;letter-spacing:.08em;'
                f'text-transform:uppercase;padding:3px 11px;border-radius:20px;'
                f'margin:6px 0 8px">{label}</div>'
            )
            continue

        m = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if m:
            if not in_list:
                html.append('<div style="display:flex;flex-direction:column;gap:7px;padding-left:2px">')
                in_list = True
            num  = escape(m.group(1))   # FIX-7
            body = m.group(2)

            if " \u2014 " in body:
                name, rest = body.split(" \u2014 ", 1)
                body_html = (
                    f'<span style="color:#e2e8f0;font-weight:500">{escape(name)}</span>'
                    f'<span style="color:#3b4f6b"> \u2014 </span>'
                    f'<span style="color:#94a3b8">{escape(rest)}</span>'
                )
            elif " - " in body:
                name, rest = body.split(" - ", 1)
                body_html = (
                    f'<span style="color:#e2e8f0;font-weight:500">{escape(name)}</span>'
                    f'<span style="color:#3b4f6b"> - </span>'
                    f'<span style="color:#94a3b8">{escape(rest)}</span>'
                )
            else:
                body_html = f'<span style="color:#cbd5e1">{escape(body)}</span>'

            html.append(
                f'<div style="display:flex;gap:10px;align-items:flex-start">'
                f'<span style="color:#3b5bdb;font-family:monospace;'
                f'font-size:11px;font-weight:700;min-width:20px;flex-shrink:0;'
                f'margin-top:2px">{num}.</span>'
                f'<span style="font-size:13px;line-height:1.65">{body_html}</span>'
                f'</div>'
            )
            continue

        if in_list:
            html.append("</div>")
            in_list = False
        html.append(
            f'<p style="margin:3px 0;font-size:13px;color:#94a3b8;line-height:1.65">'
            f'{escape(stripped)}</p>'   # FIX-7
        )

    if in_list:
        html.append("</div>")

    return "\n".join(html)


def bot_iframe(inner_html: str, height: int = 200) -> None:
    """Wrap inner_html in the avatar+bubble layout and render via components.html."""
    full = f"""
    {_IFRAME_BASE}
    <div style="display:flex;gap:12px;align-items:flex-start;padding:2px 0 4px">
      <div style="width:32px;height:32px;border-radius:50%;flex-shrink:0;
                  background:linear-gradient(135deg,#3b5bdb,#7c3aed);
                  display:flex;align-items:center;justify-content:center;
                  font-size:11px;font-weight:700;color:#fff;font-family:monospace">IH</div>
      <div style="background:#111827;border:1px solid #1e2d5a;
                  border-radius:14px;border-top-left-radius:4px;
                  padding:16px 18px;flex:1;min-width:0">
        {inner_html}
      </div>
    </div>
    """
    components.html(full, height=height, scrolling=False)


# ── Cached loaders ────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading FAISS + embedding model...")
def _load_retriever():
    _, _, retriever = load_retriever()
    return retriever

@st.cache_resource(show_spinner="Connecting to Ollama (Llama 3)...")
def _load_llm():
    return load_llm()

@st.cache_data(ttl=300)
def _load_kpis():
    return get_kpi_counts()

@st.cache_data(ttl=300)
def _load_critical():
    return get_critical_items()


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {"chat_history": [], "pending_question": "", "request_count": 0}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Load resources ────────────────────────────────────────────────────────────
ollama_ok, ollama_msg = check_ollama_running()
retriever = _load_retriever()
llm       = _load_llm() if ollama_ok else None
kpis      = _load_kpis()
critical  = _load_critical()


# ── Top header ────────────────────────────────────────────────────────────────
dot_html   = '<div class="pulse-dot"></div>' if ollama_ok else '<div class="pulse-err"></div>'
status_cls = "status-ok" if ollama_ok else "status-err"

st.markdown(f"""
<div class="top-header">
  <div class="brand-wrap">
    <div class="brand-icon">⚕</div>
    <div>
      <div class="brand-title">Inventra Health</div>
      <div class="brand-subtitle">Hospital Supply Chain Intelligence · AI Powered · Somita Chaudhari</div>
    </div>
  </div>
  <div class="status-row {status_cls}">
    {dot_html}
    {escape(ollama_msg)}
  </div>
</div>
""", unsafe_allow_html=True)

if not ollama_ok:
    st.markdown(f"""
    <div class="offline-warn">
      <strong>Ollama is not running.</strong> {escape(ollama_msg)}<br>
      Open Terminal and run: <code>brew services start ollama</code>
      then refresh this page.
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="background:#0d1226;border:1px solid #1e2d5a;border-radius:10px;padding:12px 16px 10px;margin-bottom:16px;text-align:center">
      <div style="width:36px;height:36px;background:linear-gradient(135deg,#3b5bdb,#7c3aed);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;margin:0 auto 8px">⚕</div>
      <div style="font-family:'Space Mono',monospace;font-size:13px;font-weight:700;letter-spacing:1.5px;color:#e8eaf6;margin-bottom:3px">INVENTRA HEALTH</div>
      <div style="font-size:8px;letter-spacing:2px;color:#2d4a8a;margin-bottom:8px">HOSPITAL SUPPLY CHAIN</div>
      <div style="width:30px;height:1px;background:#1e2d5a;margin:0 auto 6px"></div>
      <div style="font-size:11px;color:#5c7cfa;letter-spacing:0.5px">Somita Chaudhari</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sec-label">KPI Overview</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-val">{kpis['critical']}</div>
        <div class="kpi-label">Critical items</div>
        <div class="kpi-badge badge-red">Urgent</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val">{kpis['restock']}</div>
        <div class="kpi-label">Restock alerts</div>
        <div class="kpi-badge badge-amber">Active</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val">{kpis['delayed']}</div>
        <div class="kpi-label">Vendor delays</div>
        <div class="kpi-badge badge-amber">Delayed</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val">${kpis['total_spend_millions']}M</div>
        <div class="kpi-label">Total spend</div>
        <div class="kpi-badge badge-green">17 months</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-label">Critical alerts</div>', unsafe_allow_html=True)
    for _, row in critical.head(4).iterrows():
        sev = "" if row["Days_Until_Stockout"] <= 1 else "warn"
        st.markdown(f"""
        <div class="alert-card {sev}">
          <div class="alert-name">{escape(str(row['Item_Name']))}</div>
          <div>{row['Days_Until_Stockout']:.1f} days left · {escape(str(row['Vendor_ID']))}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-label">Quick actions</div>', unsafe_allow_html=True)
    for label, question in [
        ("🔴  Critical items now",    "Which items are most critical right now?"),
        ("🚚  Vendor delay report",   "Give me a full vendor delay report"),
        ("🏥  ICU supply usage",      "What supplies do ICU patients use most?"),
        ("💰  This month's spend",    "Summarise spending by category with totals"),
        ("📦  Overstock report",      "Which items are currently overstocked?"),
        ("👥  Staff overtime",        "Show staff overtime and workload issues"),
    ]:
        if st.button(label, key=f"q_{label}", disabled=not ollama_ok):
            st.session_state.pending_question = question
            st.rerun()

    st.markdown("---")
    sc = "#4db6ac" if ollama_ok else "#f48fb1"
    sl = "Llama 3 running locally" if ollama_ok else "Ollama offline"
    st.markdown(f"""
    <div style="font-size:10px;color:{sc};margin-bottom:6px">{sl}</div>
    <div style="font-size:10px;color:#2d4a8a;line-height:1.8">
    LangChain · FAISS · SQLite<br>
    5 datasets · 1,509 records · RAG<br>
    Requests this session: {st.session_state.request_count}/200
    </div>
    """, unsafe_allow_html=True)


# ── Chat area ─────────────────────────────────────────────────────────────────
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

# ── Welcome message ───────────────────────────────────────────────────────────
if not st.session_state.chat_history:
    if ollama_ok:
        welcome_inner = f"""
        <div style="font-size:16px;font-weight:600;color:#e8eaf6;
                    font-family:'Space Mono',monospace;margin-bottom:14px;
                    letter-spacing:-.01em">Inventra Health</div>

        <p style="font-size:13px;color:#94a3b8;line-height:1.75;margin:0 0 10px">
          Good to have you here. I am your hospital supply chain operations
          analyst - built to give you fast, specific, data-backed decisions.
        </p>

        <p style="font-size:13px;color:#94a3b8;line-height:1.75;margin:0 0 16px">
          I have live access to your
          <span style="color:#90caf9">inventory</span>,
          <span style="color:#90caf9">vendor performance</span>,
          <span style="color:#90caf9">financials</span>,
          <span style="color:#90caf9">patient demand</span>, and
          <span style="color:#90caf9">staff data</span>.
          Ask me anything about stockouts, delays, spending, or workload.
        </p>

        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">
          <span style="background:#0d1f3c;color:#90caf9;font-size:11px;
                       padding:4px 12px;border-radius:20px">{kpis['restock']} Restock alerts</span>
          <span style="background:#2d1212;color:#f48fb1;font-size:11px;
                       padding:4px 12px;border-radius:20px">{kpis['critical']} Critical items</span>
          <span style="background:#2d2200;color:#ffcc80;font-size:11px;
                       padding:4px 12px;border-radius:20px">{kpis['delayed']} Vendor delays</span>
          <span style="background:#1b2d1b;color:#a5d6a7;font-size:11px;
                       padding:4px 12px;border-radius:20px">${kpis['total_spend_millions']}M tracked</span>
        </div>

        <div style="border-top:1px solid #1e2d5a;padding-top:12px;
                    display:flex;align-items:center;gap:8px">
          <div style="width:6px;height:6px;border-radius:50%;flex-shrink:0;
                      background:#1D9E75;box-shadow:0 0 4px #1D9E75"></div>
          <span style="font-size:10px;color:#4a5568;line-height:1.6">
            Enterprise-grade security · HIPAA-aligned data governance
          </span>
        </div>
        """
        bot_iframe(welcome_inner, height=320)
    else:
        offline_inner = """
        <div style="font-size:16px;font-weight:600;color:#e8eaf6;
                    font-family:'Space Mono',monospace;margin-bottom:10px">Inventra Health</div>
        <p style="font-size:13px;color:#94a3b8;line-height:1.75;margin:0">
          Ready — but Ollama is currently offline.<br><br>
          Open Terminal and run:<br>
          <code style="background:#1e2d5a;color:#90caf9;padding:2px 8px;
                       border-radius:4px;font-size:12px">brew services start ollama</code>
          <br><br>Then refresh this page.
        </p>
        """
        bot_iframe(offline_inner, height=200)


# ── Conversation history ──────────────────────────────────────────────────────
for user_msg, bot_msg in st.session_state.chat_history:

    # escape user_msg before injecting into unsafe HTML block
    st.markdown(f"""
    <div class="msg-user">
      <div class="av-user">S</div>
      <div class="bubble-user">{escape(user_msg)}</div>
    </div>""", unsafe_allow_html=True)


    rendered = render_bot_bubble(bot_msg)
    height   = min(900, max(180, len(bot_msg) // 2 + 80))
    bot_iframe(rendered, height=height)

st.markdown("</div>", unsafe_allow_html=True)


# ── Input ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="input-area">', unsafe_allow_html=True)
c1, c2 = st.columns([6, 1])
with c1:
    user_input = st.text_input(
        label="",
        placeholder=(
            "Ask about inventory, vendors, spending, patient demand..."
            if ollama_ok else
            "Start Ollama first — brew services start ollama"
        ),
        key="chat_input",
        label_visibility="collapsed",
        disabled=not ollama_ok
    )
with c2:
    send = st.button(
        "Ask ↗", type="primary",
        use_container_width=True,
        disabled=not ollama_ok
    )
st.markdown("</div>", unsafe_allow_html=True)


# ── Handle send ───────────────────────────────────────────────────────────────
question = None
if send and user_input.strip():
    question = user_input.strip()
elif st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = ""

if question and llm:
    within_limit, limit_msg = check_rate_limit(st.session_state)
    if not within_limit:
        st.markdown(
            f'<div class="bubble-err">{escape(limit_msg)}</div>',
            unsafe_allow_html=True
        )
    else:
        is_valid, reason = validate_question(question)
        if not is_valid:
            st.markdown(
                f'<div class="bubble-err">Cannot process: {escape(reason)}</div>',
                unsafe_allow_html=True
            )
        else:
            with st.spinner("Inventra Health is analysing your data..."):
                answer = ask(
                    question=question,
                    llm=llm,
                    retriever=retriever,
                    history=st.session_state.chat_history
                )
            st.session_state.chat_history.append((question, answer))
            st.session_state.request_count += 1
            st.rerun()
