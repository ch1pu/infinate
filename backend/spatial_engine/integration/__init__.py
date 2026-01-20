"""
integration - Integration module connecting SpatialTransformer with VectorStore.

This module provides the bridge between the spatial transformer architecture
and the vector store backends (Qdrant, pgvector), enabling unlimited context
through database-backed spatial memory.

Author: ch1pu
Milestone: 1.7 - Integration Testing

Classes:
    TransformerBridge: Connects SpatialTransformer to VectorStore for queries
    ContextManager: Manages context retrieval from vector stores

Example:
    ```python
    from spatial_engine.integration import TransformerBridge, ContextManager
    from spatial_engine.core import SpatialTransformer
    from spatial_engine.vector_store import QdrantAdapter

    # Create components
    transformer = SpatialTransformer(n_layers=6, d_model=768)
    vector_store = QdrantAdapter("spatial_memory", d_model=768, use_memory=True)

    # Create bridge
    bridge = TransformerBridge(
        transformer=transformer,
        vector_store=vector_store,
        k_neighbors=50
    )

    # Forward pass queries vector store automatically
    output = bridge(x, positions)
    ```
"""

from spatial_engine.integration.context_manager import ContextManager
from spatial_engine.integration.navigation_attention import (
    BaselineAttention,
    NavigationAttention,
    NavigationMetrics,
)
from spatial_engine.integration.transformer_bridge import TransformerBridge

__all__ = [
    "TransformerBridge",
    "ContextManager",
    "NavigationAttention",
    "BaselineAttention",
    "NavigationMetrics",
]
