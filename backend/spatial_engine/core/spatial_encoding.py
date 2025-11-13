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

import math

import torch
import torch.nn as nn


class SpatialPositionEncoding(nn.Module):
    """
    3D spatial positional encoding with sinusoidal patterns.

    Extends standard transformer positional encoding from 1D sequences
    to continuous 3D coordinates. Each dimension (X, Y, Z) is encoded
    independently with sinusoidal patterns at multiple frequency scales.

    Args:
        d_model: Embedding dimension (must be divisible by 3 ideally)
        max_position: Maximum expected position value for normalization
        temperature: Temperature parameter for frequency scaling (default: 10000)

    Attributes:
        d_model: Embedding dimension
        max_position: Maximum position for normalization
        temperature: Frequency scaling temperature
        d_per_dim: Dimensions allocated per spatial axis (d_model // 3)
        freqs: Registered frequency buffer [d_per_dim // 2]
    """

    def __init__(
        self,
        d_model: int = 768,
        max_position: float = 1000.0,
        temperature: float = 10000.0,
    ) -> None:
        super().__init__()

        self.d_model = d_model
        self.max_position = max_position
        self.temperature = temperature

        # Each dimension (x, y, z) gets d_model/3 features
        self.d_per_dim = d_model // 3

        # Generate frequency bands (non-trainable)
        freqs = self._generate_frequencies()
        self.register_buffer("freqs", freqs)

    def _generate_frequencies(self) -> torch.Tensor:
        """
        Generate logarithmic frequency bands for sinusoidal encoding.

        Returns:
            Frequency tensor [d_per_dim // 2]
        """
        # Logarithmic spacing like original transformer
        # freqs = exp(linspace(0, -log(temperature), num_freqs))
        num_freqs = self.d_per_dim // 2

        freqs = torch.exp(
            torch.linspace(0, -math.log(self.temperature), num_freqs)
        )

        return freqs

    def encode_dimension(
        self, coords: torch.Tensor, dim_idx: int
    ) -> torch.Tensor:
        """
        Encode single spatial dimension (x, y, or z).

        Args:
            coords: Coordinates for one dimension
                    [batch] for single positions or
                    [batch, seq_len] for sequences
            dim_idx: Dimension index (0=X, 1=Y, 2=Z)

        Returns:
            Encoding tensor
            [batch, d_per_dim] for single positions or
            [batch, seq_len, d_per_dim] for sequences

        Example:
            >>> encoder = SpatialPositionEncoding(d_model=768)
            >>> x_coords = torch.tensor([0.0, 100.0, 500.0])  # [3]
            >>> x_enc = encoder.encode_dimension(x_coords, dim_idx=0)
            >>> x_enc.shape
            torch.Size([3, 256])
        """
        # Check if 1D input (single position per batch)
        is_1d = coords.dim() == 1

        # Normalize to [-1, 1] range
        coords_norm = coords / self.max_position

        # Reshape for broadcasting
        if is_1d:
            # [batch] -> [batch, 1]
            coords_norm = coords_norm.unsqueeze(-1)
        else:
            # [batch, seq_len] -> [batch, seq_len, 1]
            coords_norm = coords_norm.unsqueeze(-1)

        # Compute angles: coord * freq * 2π
        # freqs: [num_freqs]
        # coords_norm: [batch, 1] or [batch, seq_len, 1]
        # angles: [batch, num_freqs] or [batch, seq_len, num_freqs]
        angles = coords_norm * self.freqs * 2 * math.pi

        # Compute sin and cos components
        sin_enc = torch.sin(angles)
        cos_enc = torch.cos(angles)

        # Concatenate
        # result: [batch, d_per_dim] or [batch, seq_len, d_per_dim]
        encoding = torch.cat([sin_enc, cos_enc], dim=-1)

        return encoding

    def forward(self, positions_3d: torch.Tensor) -> torch.Tensor:
        """
        Encode 3D positions into high-dimensional space.

        Combines independent X, Y, Z encodings into unified representation
        for spatial attention computation.

        Args:
            positions_3d: 3D coordinates [batch, seq_len, 3] where
                         last dimension is (x, y, z)

        Returns:
            Spatial encoding [batch, seq_len, d_model]

        Raises:
            ValueError: If input tensor is not 3D or last dimension is not 3

        Example:
            >>> encoder = SpatialPositionEncoding(d_model=768)
            >>> positions = torch.tensor([[[100.0, 50.0, 25.0]]])  # [1, 1, 3]
            >>> encoding = encoder(positions)
            >>> encoding.shape
            torch.Size([1, 1, 768])

        Note:
            If d_model is not divisible by 3, the encoding will be padded
            to reach d_model dimensions.
        """
        # Validate input shape
        if positions_3d.dim() != 3:
            raise ValueError(
                f"positions_3d must be 3D tensor [batch, seq_len, 3], "
                f"got {positions_3d.dim()}D tensor"
            )

        if positions_3d.shape[-1] != 3:
            raise ValueError(
                f"Last dimension must be 3 (x, y, z), got {positions_3d.shape[-1]}"
            )

        batch, seq_len, spatial_dim = positions_3d.shape

        # Extract x, y, z coordinates
        x = positions_3d[:, :, 0]  # [batch, seq_len]
        y = positions_3d[:, :, 1]  # [batch, seq_len]
        z = positions_3d[:, :, 2]  # [batch, seq_len]

        # Encode each dimension independently
        x_enc = self.encode_dimension(x, dim_idx=0)  # [batch, seq_len, d_per_dim]
        y_enc = self.encode_dimension(y, dim_idx=1)  # [batch, seq_len, d_per_dim]
        z_enc = self.encode_dimension(z, dim_idx=2)  # [batch, seq_len, d_per_dim]

        # Concatenate all dimensions
        # [batch, seq_len, 3 * d_per_dim]
        encoding = torch.cat([x_enc, y_enc, z_enc], dim=-1)

        # Pad if d_model not divisible by 3
        if encoding.shape[-1] < self.d_model:
            padding_size = self.d_model - encoding.shape[-1]
            encoding = torch.nn.functional.pad(
                encoding, (0, padding_size), mode="constant", value=0
            )

        return encoding
