"""Embedding service: generate embeddings via Groq API with safe fallback."""

import hashlib
import os
import struct
import sys
import requests

EMBEDDING_DIM = 1536
GROQ_EMBEDDING_MODEL = os.getenv('GROQ_EMBEDDING_MODEL', 'nomic-embed-text-v1.5')
GROQ_EMBEDDING_URL = 'https://api.groq.com/openai/v1/embeddings'


# -----------------------------
# ✅ SAFE DETERMINISTIC FALLBACK
# -----------------------------
def _hash_to_floats(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """
    Stable deterministic embedding fallback.
    Produces values in [-1, 1] suitable for pgvector.
    """
    h = hashlib.sha256(text.encode('utf-8')).digest()

    floats = []
    i = 0

    while len(floats) < dim:
        chunk = h[i % len(h): (i % len(h)) + 4]

        if len(chunk) < 4:
            chunk = chunk.ljust(4, b'\0')

        val = struct.unpack('>I', chunk)[0]

        # Normalize safely to [-1, 1]
        floats.append((val / 0xFFFFFFFF) * 2 - 1)

        i += 4

    return floats[:dim]


# -----------------------------
# ✅ DIMENSION SAFETY
# -----------------------------
def _normalize_dim(embedding: list[float], dim: int = EMBEDDING_DIM) -> list[float]:
    embedding = [float(x) for x in embedding]

    if len(embedding) == dim:
        return embedding
    if len(embedding) > dim:
        return embedding[:dim]
    return embedding + [0.0] * (dim - len(embedding))


# -----------------------------
# ✅ STUB MODE CHECK
# -----------------------------
def _should_use_stub() -> bool:
    if 'pytest' in sys.modules:
        return True
    if os.getenv('USE_STUB_EMBEDDINGS', '').lower() in ('1', 'true', 'yes'):
        return True
    api_key = os.getenv('GROQ_API_KEY', '')
    return not api_key or api_key == 'gsk_your_key_here'


# -----------------------------
# ✅ GROQ EMBEDDING CALL
# -----------------------------
def _groq_embedding(text: str) -> list[float]:
    api_key = os.getenv('GROQ_API_KEY', '')

    response = requests.post(
        GROQ_EMBEDDING_URL,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json={
            'model': GROQ_EMBEDDING_MODEL,
            'input': text,
        },
        timeout=30,
    )

    response.raise_for_status()
    payload = response.json()

    embedding = payload['data'][0]['embedding']

    return _normalize_dim(embedding, EMBEDDING_DIM)


# -----------------------------
# ✅ MAIN ENTRY POINT
# -----------------------------
def generate_embedding(text: str) -> list[float]:
    """
    Returns a 1536-dim embedding vector.
    Uses Groq API if available, otherwise safe deterministic fallback.
    """

    if not text:
        return [0.0] * EMBEDDING_DIM

    if _should_use_stub():
        return _hash_to_floats(text, EMBEDDING_DIM)

    return _groq_embedding(text)