"""
Retrieval-augmented generation (RAG) for the public chatbot, using real
semantic embeddings via Google's Gemini Embedding API.

Unlike keyword/TF-IDF matching, embeddings capture MEANING — "cost" and
"pricing" are recognized as related even though they're different words.
Using a hosted API instead of a local model (like sentence-transformers)
avoids downloading ~500MB of model weights and keeps memory usage on the
server tiny, since Google's servers do the actual embedding computation —
we just send text and get a vector back.

Document chunks are embedded once and cached in memory (they don't change
at runtime). Each question is embedded fresh, then compared to every cached
chunk via cosine similarity to find the most relevant ones.
"""

import os


import numpy as np
from google import genai
from google.genai import types

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")
EMBEDDING_MODEL = "gemini-embedding-001"

_genai_client = None
_chunks: list[dict] = []  # [{"source": ..., "heading": ..., "text": ...}]
_chunk_embeddings: np.ndarray | None = None


def _get_genai_client() -> genai.Client:
    """Lazily creates the client so a missing API key doesn't crash the app
    on startup — only when the chatbot is actually used."""
    global _genai_client
    if _genai_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file — see .env.example."
            )
        _genai_client = genai.Client(api_key=api_key)
    return _genai_client


def _embed(text: str, task_type: str) -> np.ndarray:
    """Calls Gemini's embedding API and returns a normalized numpy vector.
    task_type is "RETRIEVAL_DOCUMENT" for knowledge base chunks (indexed
    once) or "RETRIEVAL_QUERY" for a user's question (asymmetric embedding —
    Gemini embeds these two roles slightly differently for better retrieval
    quality)."""
    client = _get_genai_client()
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    vector = np.array(response.embeddings[0].values)
    norm = np.linalg.norm(vector)
    return vector / norm if norm > 0 else vector


def _load_and_chunk_knowledge_base() -> list[dict]:
    """Each markdown file becomes ONE chunk, not split by subsection.
    This guarantees that when a file like pricing.md is relevant, the LLM
    gets the whole thing — every tier — rather than risking an incomplete
    subset if only some of its sections happen to rank in the top_k."""
    chunks = []
    for filename in sorted(os.listdir(KNOWLEDGE_DIR)):
        if not filename.endswith(".md"):
            continue
        path = os.path.join(KNOWLEDGE_DIR, filename)
        with open(path, encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            continue
        first_line = content.split("\n", 1)[0].lstrip("#").strip()
        chunks.append({"source": filename, "heading": first_line, "text": content})
    return chunks


def _ensure_index_built():
    """Embeds every knowledge base chunk once, lazily, on first use, and
    caches the result in memory for the lifetime of the server process."""
    global _chunks, _chunk_embeddings
    if _chunk_embeddings is not None:
        return
    _chunks = _load_and_chunk_knowledge_base()
    embeddings = [_embed(c["text"], task_type="RETRIEVAL_DOCUMENT") for c in _chunks]
    _chunk_embeddings = np.array(embeddings)


def retrieve_relevant_chunks(query: str, top_k: int = 3) -> list[dict]:
    """Returns the top_k knowledge base chunks most semantically relevant
    to the query, using real embedding-based cosine similarity."""
    _ensure_index_built()
    if not _chunks:
        return []

    query_vector = _embed(query, task_type="RETRIEVAL_QUERY")
    similarities = _chunk_embeddings @ query_vector  # cosine similarity (vectors are normalized)
    top_indices = np.argsort(similarities)[::-1][:top_k]

    return [_chunks[i] for i in top_indices]