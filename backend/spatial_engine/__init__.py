"""
Spatial Engine - Core AI memory management system with 3D spatial awareness.

This package provides the foundation for spatially-aware AI models with O(k)
constant complexity attention mechanism, enabling truly unlimited context.

Modules:
    core: Fundamental spatial algorithms (tokens, attention, navigation)
    models: PyTorch models for spatial transformers
    vector_store: Integration with vector databases (Qdrant, pgvector)
    utils: Utility functions for spatial operations

Key Features:
    - O(k) constant complexity (not O(n²))
    - Truly unlimited context (billions of tokens)
    - 3D spatial memory organization
    - Distance-based attention decay
    - Learned navigation through semantic space
    - Direct vector database integration

Example:
    >>> from spatial_engine.core import SpatialToken
    >>> import torch
    >>>
    >>> token = SpatialToken(
    ...     token_id=42,
    ...     position=(100.0, 50.0, 25.0),
    ...     embedding=torch.randn(768),
    ...     spatial_encoding=torch.randn(768)
    ... )
    >>> token.distance_to(other_token)
    75.5

References:
    - CORE_INNOVATION.md: Theoretical foundation
    - SPATIAL_MODEL_ARCHITECTURE.md: Technical implementation
    - VECTOR_STORE_INTEGRATION.md: Database layer

Author: Infinite Project Team
License: Apache 2.0
"""

__version__ = "0.1.0"
__author__ = "Infinite Project Team"
__license__ = "Apache 2.0"

# Version info
VERSION = (0, 1, 0)
