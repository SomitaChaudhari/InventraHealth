"""
retriever.py
------------

"""

import logging
from typing import List, Tuple

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src.config import FAISS_PATH, EMBED_MODEL, RETRIEVER_K

logger = logging.getLogger("inventra.retriever")


def load_embeddings() -> HuggingFaceEmbeddings:
    """Load sentence-transformers model. CPU only. ~90MB first download."""
    logger.info("Loading embedding model: %s", EMBED_MODEL)
    return HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"}
    )


def load_vectorstore(embeddings: HuggingFaceEmbeddings = None) -> FAISS:
    """Load pre-built FAISS index from disk."""
    if not FAISS_PATH.exists():

        logger.error("FAISS index not found at %s", FAISS_PATH)
        raise FileNotFoundError(
            "FAISS index not found. "
            "Please run notebooks/02_build_faiss.ipynb to build it first."
        )
    if embeddings is None:
        embeddings = load_embeddings()
    logger.info("Loading FAISS index from: %s", FAISS_PATH)
    return FAISS.load_local(
        str(FAISS_PATH), embeddings, allow_dangerous_deserialization=True
    )


def load_retriever(k: int = RETRIEVER_K) -> Tuple:
    """One-call loader: embeddings + vectorstore + retriever."""
    embeddings  = load_embeddings()
    vectorstore = load_vectorstore(embeddings)
    retriever   = vectorstore.as_retriever(search_kwargs={"k": k})
    logger.info("Retriever ready (k=%d)", k)
    return embeddings, vectorstore, retriever


def search(retriever, query: str) -> List[Document]:
    logger.debug("Query: %s", query[:80])
    return retriever.invoke(query)


def search_to_text(retriever, query: str) -> str:
    """Return retrieved PDF chunks as a single formatted string."""
    docs = search(retriever, query)
    if not docs:
        return "[No relevant knowledge base content found]"
    sections = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown").split("/")[-1]
        sections.append(f"[{source}]\n{doc.page_content}")
    return "\n\n".join(sections)


def get_index_info() -> dict:
    if not FAISS_PATH.exists():
        return {"exists": False}
    files = list(FAISS_PATH.iterdir())
    return {
        "exists":   True,
        "files":    [f.name for f in files],
        "sizes_kb": {f.name: round(f.stat().st_size / 1024, 1) for f in files},
    }
