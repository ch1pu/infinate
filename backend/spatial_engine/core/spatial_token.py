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
    position: tuple[float, float, float]
    embedding: torch.Tensor
    spatial_encoding: torch.Tensor

    def __post_init__(self) -> None:
        """Validate inputs after initialization."""
        # Validate position is 3D
        if len(self.position) != 3:
            raise ValueError(f"Position must be 3D (x, y, z), got {len(self.position)}D")

        # Validate embedding dimensions match
        if self.embedding.shape != self.spatial_encoding.shape:
            raise ValueError(
                f"Embedding dimensions must match: "
                f"embedding={self.embedding.shape}, "
                f"spatial_encoding={self.spatial_encoding.shape}"
            )

    def distance_to(self, other: "SpatialToken") -> float:
        """
        Calculate 3D Euclidean distance to another token.

        Uses the standard Euclidean distance formula:
        d = sqrt((x2-x1)² + (y2-y1)² + (z2-z1)²)

        Args:
            other: Target SpatialToken to measure distance to

        Returns:
            Euclidean distance in 3D space (float)

        Example:
            >>> token1 = SpatialToken(position=(0, 0, 0), ...)
            >>> token2 = SpatialToken(position=(3, 4, 0), ...)
            >>> token1.distance_to(token2)
            5.0  # 3-4-5 right triangle

        Note:
            This is an O(1) operation.
        """
        x1, y1, z1 = self.position
        x2, y2, z2 = other.position
        return float(((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5)

    @property
    def full_embedding(self) -> torch.Tensor:
        """
        Combine semantic and spatial embeddings.

        The full embedding is the sum of:
        - Semantic embedding (what the token means)
        - Spatial encoding (where the token is located)

        Returns:
            Sum of semantic embedding and spatial encoding (torch.Tensor)

        Example:
            >>> token = SpatialToken(
            ...     token_id=42,
            ...     position=(1, 2, 3),
            ...     embedding=torch.ones(768),
            ...     spatial_encoding=torch.ones(768) * 0.5
            ... )
            >>> full_emb = token.full_embedding
            >>> torch.allclose(full_emb, torch.ones(768) * 1.5)
            True
        """
        return self.embedding + self.spatial_encoding
