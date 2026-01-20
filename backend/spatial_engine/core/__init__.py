"""
Spatial Engine Core - Fundamental spatial algorithms and data structures.

This package provides the core components for spatially-aware AI:
- SpatialToken: Fundamental token with 3D position and embedding
- SpatialPositionEncoding: 3D sinusoidal position encodings
- SpatialAttention: O(k) constant complexity attention mechanism
- FeedForward: Standard transformer feedforward network
- SpatialTransformerBlock: Complete transformer block with spatial attention
- SpatialTransformer: Full spatial transformer model
- HierarchicalLOD: Level-of-Detail context compression (M1.10)
- SpatialAttentionWithLOD: LOD-enhanced attention wrapper (M1.10)

Example:
    >>> from spatial_engine.core import SpatialToken, SpatialAttention
    >>> import torch
    >>>
    >>> token = SpatialToken(
    ...     token_id=42,
    ...     position=(100.0, 50.0, 25.0),
    ...     embedding=torch.randn(768),
    ...     spatial_encoding=torch.randn(768)
    ... )
    >>>
    >>> attention = SpatialAttention(d_model=768, n_heads=12)
    >>> x = torch.randn(32, 1024, 768)
    >>> positions = torch.randn(32, 1024, 3) * 500.0
    >>> output = attention(x, positions)  # O(k) complexity!

Author: ch1pu (Adolfo Lopez) - Alpha Deploy LLC
License: Apache 2.0
"""

# Core data structures
from spatial_engine.core.spatial_token import SpatialToken

# Position encoding
from spatial_engine.core.spatial_encoding import SpatialPositionEncoding

# Attention mechanisms
from spatial_engine.core.spatial_attention import SpatialAttention

# Transformer components
from spatial_engine.core.feedforward import FeedForward
from spatial_engine.core.spatial_transformer_block import SpatialTransformerBlock
from spatial_engine.core.spatial_transformer import SpatialTransformer

# LOD system (M1.10)
from spatial_engine.core.lod import (
    LODLevel,
    LODConfig,
    HierarchicalLOD,
    DEFAULT_LOD_CONFIG,
)
from spatial_engine.core.spatial_attention_lod import (
    SpatialAttentionWithLOD,
    create_lod_attention,
)

__all__ = [
    # Core data structures
    "SpatialToken",
    # Position encoding
    "SpatialPositionEncoding",
    # Attention mechanisms
    "SpatialAttention",
    # Transformer components
    "FeedForward",
    "SpatialTransformerBlock",
    "SpatialTransformer",
    # LOD system (M1.10)
    "LODLevel",
    "LODConfig",
    "HierarchicalLOD",
    "DEFAULT_LOD_CONFIG",
    "SpatialAttentionWithLOD",
    "create_lod_attention",
]
