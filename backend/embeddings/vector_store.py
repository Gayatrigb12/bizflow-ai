"""Vector store helpers: upsert embeddings into the `knowledge_embeddings` table."""
from typing import Optional
from sqlalchemy.orm import Session
from backend.storage.models import KnowledgeEmbedding


def upsert_embedding(session: Session, object_type: str, object_id: int, embedding, metadata: Optional[dict] = None):
    """Insert or update an embedding for the given object.

    `embedding` should be either a list[float] (JSON fallback) or a pgvector Vector-compatible sequence.
    """
    existing = session.query(KnowledgeEmbedding).filter_by(object_type=object_type, object_id=object_id).one_or_none()
    if existing:
        existing.embedding = embedding
        existing.meta = metadata or existing.meta
    else:
        record = KnowledgeEmbedding(
            object_type=object_type,
            object_id=object_id,
            embedding=embedding,
            meta=metadata,
        )
        session.add(record)
        session.flush()
    return True
