"""Retriever: perform similarity search using pgvector when available,
with a JSON fallback that computes Euclidean distance in Python."""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.storage.models import KnowledgeEmbedding


def _euclidean(a: List[float], b: List[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def similarity_search(session: Session, query_embedding: List[float], top_k: int = 5):
    """Return top_k matching embeddings with distance."""

    results = []
    dialect = session.bind.dialect.name

    # ----------------------------
    # ✅ POSTGRES + PGVECTOR PATH
    # ----------------------------
    if dialect == "postgresql":
        sql = text("""
            SELECT
                id,
                object_type,
                object_id,
                metadata,
                embedding <=> CAST(:q AS vector) AS distance
            FROM knowledge_embeddings
            ORDER BY distance ASC
            LIMIT :k
        """)

        rows = session.execute(
            sql,
            {"q": query_embedding, "k": top_k}
        ).fetchall()

        for r in rows:
            results.append({
                "id": r[0],
                "object_type": r[1],
                "object_id": r[2],
                "metadata": r[3],
                "distance": float(r[4])
            })

        return results

    # ----------------------------
    # 🟡 FALLBACK (NON-POSTGRES / NO VECTOR EXTENSION)
    # ----------------------------
    records = session.query(KnowledgeEmbedding).all()
    scored = []

    for r in records:
        emb = r.embedding

        if not isinstance(emb, list):
            continue

        d = _euclidean(emb, query_embedding)
        scored.append((d, r))

    scored.sort(key=lambda x: x[0])

    for d, r in scored[:top_k]:
        results.append({
            "id": r.id,
            "object_type": r.object_type,
            "object_id": r.object_id,
            "metadata": r.metadata,
            "distance": d
        })

    return results