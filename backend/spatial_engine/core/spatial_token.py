"""
spatial_token.py - Fundamental spatial-semantic token representation.

This module implements the SpatialToken dataclass, which combines semantic
embeddings with 3D spatial coordinates to enable O(k) constant complexity
attention in spatially-aware transformers.

Key Concepts:
    - Tokens exist at specific (x, y, z) coordinates in semantic space
    - Attention computed only over k nearest neighbors in space
    - Distance-based exponential decay prevents long-range dependencies

Example:
    >>> import torch
    >>> from spatial_engine.core.spatial_token import SpatialToken
    >>>
    >>> token = SpatialToken(
    ...     token_id=42,
    ...     position=(1.0, 2.0, 3.0),
    ...     embedding=torch.randn(768),
    ...     spatial_encoding=torch.randn(768)
    ... )
    >>> token.position
    (1.0, 2.0, 3.0)

References:
    - SPATIAL_MODEL_ARCHITECTURE.md section 2.1 for implementation
    - CORE_INNOVATION.md for theoretical foundation

Author: Infinite Project Team
Created: 2025-01-13
"""

from dataclasses import dataclass
from typing import Tuple
import torch


@dataclass
class SpatialToken:
    """
    Fundamental unit combining semantic and spatial information.

    Attributes:
        token_id: Vocabulary index (0 to vocab_size-1)
        position: 3D coordinates (x, y, z) in spatial memory
        embedding: Semantic embedding vector (typically 768D)
        spatial_encoding: 3D positional encoding (same dim as embedding)
    """

    token_id: int
    position: Tuple[float, float, float]
    embedding: torch.Tensor
    spatial_encoding: torch.Tensor
