"""
Vector Store Integration Module.

Provides adapters for Qdrant and pgvector to enable unlimited context
through spatial memory organization.

Author: ch1pu
Milestone: 1.6 - Vector Store Integration
"""

from spatial_engine.vector_store import spatial_index
from spatial_engine.vector_store.base import VectorStoreBase
from spatial_engine.vector_store.pgvector_adapter import PgvectorAdapter
from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter

__all__ = [
    "VectorStoreBase",
    "QdrantAdapter",
    "PgvectorAdapter",
    "spatial_index",
]
