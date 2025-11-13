"""
spatial_encoding.py - 3D spatial positional encoding.

This module implements positional encoding for continuous 3D coordinates,
extending standard transformer sinusoidal encoding from 1D sequences to
3D spatial memory.

Key Concepts:
    - Separate encoding for X, Y, Z dimensions
    - Sinusoidal patterns with logarithmic frequency bands
    - Position normalization to [-1, 1] range
    - Multi-scale position awareness

Example:
    >>> import torch
    >>> from spatial_engine.core.spatial_encoding import SpatialPositionEncoding
    >>>
    >>> encoder = SpatialPositionEncoding(d_model=768)
    >>> positions = torch.tensor([[[100.0, 50.0, 25.0]]])  # [batch, seq, 3]
    >>> encoding = encoder(positions)  # [batch, seq, 768]
    >>> encoding.shape
    torch.Size([1, 1, 768])

References:
    - SPATIAL_MODEL_ARCHITECTURE.md section 2.2 for implementation details
    - Original Transformer paper (Vaswani et al., 2017) for 1D encoding

Author: ch1pu (System Architect, Lead Developer)
Created: 2025-01-13
"""
