# Embeddings package for Milestone 3
from backend.embeddings.embedding_service import generate_embedding
from backend.embeddings.vector_store import upsert_embedding
from backend.embeddings.retriever import similarity_search

__all__ = ['generate_embedding', 'upsert_embedding', 'similarity_search']
