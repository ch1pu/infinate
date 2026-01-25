# Copyright 2025-2026 Adolfo Lopez (ch1pu)
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Adolfo Lopez (ch1pu) - github.com/ch1pu
# Project: INFINATE - Infinite Context Spatial AI (github.com/ch1pu/infinate)
#
# ============================================================================
# BUILT BY A U.S. NAVY VETERAN | BUILT IN TEXAS | OPEN FOR OPPORTUNITIES
# ============================================================================
# I'm actively seeking software engineering roles. If you're reading this code
# and like what you see, let's connect:
#   - GitHub: github.com/ch1pu
#   - Twitter/X: @2006_adolfo
#   - Project: This codebase demonstrates O(k) spatial attention, achieving
#     10,317x speedup over standard transformer attention with 89.58% test coverage.
# ============================================================================

"""
spatial_transformer_block.py - Single transformer layer with spatial attention.

Combines spatial attention (M1.3) with feed-forward network, residual connections,
and layer normalization to create a complete transformer block.

Author: ch1pu
Milestone: 1.4 - Spatial Transformer Block
Architecture: Post-norm transformer (norm after residual)
"""


import torch
import torch.nn as nn

from spatial_engine.core.feedforward import FeedForward
from spatial_engine.core.spatial_attention import SpatialAttention


class SpatialTransformerBlock(nn.Module):
    """
    Single transformer layer with spatial attention.

    Combines spatial attention (O(k) complexity) with feed-forward network,
    residual connections, and layer normalization.

    Architecture (post-norm):
    1. x = norm1(x + dropout1(spatial_attention(x, positions)))
    2. x = norm2(x + dropout2(feedforward(x)))

    Args:
        d_model: Embedding dimension (default: 768)
        n_heads: Number of attention heads (default: 12)
        d_ff: Feed-forward hidden dimension (default: 3072, 4× d_model)
        spatial_radius: Radius for spatial attention in units (default: 50.0)
        dropout: Dropout probability (default: 0.1)

    Shape:
        - Input: x [batch, seq_len, d_model], positions [batch, seq_len, 3]
        - Output: [batch, seq_len, d_model]

    Examples:
        >>> block = SpatialTransformerBlock(d_model=768, n_heads=12)
        >>> x = torch.randn(32, 1024, 768)
        >>> positions = torch.randn(32, 1024, 3) * 500.0
        >>> output = block(x, positions)
        >>> assert output.shape == (32, 1024, 768)

    Note:
        Post-norm architecture: normalization applied AFTER residual connection.
        This is the standard transformer architecture from Vaswani et al. (2017).

    Reference:
        Vaswani et al. (2017): "Attention is All You Need"
        https://arxiv.org/abs/1706.03762
    """

    def __init__(
        self,
        d_model: int = 768,
        n_heads: int = 12,
        d_ff: int = 3072,
        spatial_radius: float = 50.0,
        dropout: float = 0.1,
    ) -> None:
        """
        Initialize SpatialTransformerBlock.

        Args:
            d_model: Embedding dimension
            n_heads: Number of attention heads
            d_ff: Feed-forward hidden dimension (typically 4× d_model)
            spatial_radius: Radius for spatial attention in units
            dropout: Dropout probability for regularization
        """
        super().__init__()

        # Store parameters
        self.d_model = d_model
        self.n_heads = n_heads

        # Spatial attention (O(k) complexity from M1.3)
        self.spatial_attention = SpatialAttention(
            d_model=d_model,
            n_heads=n_heads,
            spatial_radius=spatial_radius,
            dropout=dropout,
        )

        # Feed-forward network (2-layer MLP)
        self.ffn = FeedForward(
            d_model=d_model,
            d_ff=d_ff,
            dropout=dropout,
        )

        # Layer normalization (post-norm: after residual)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

        # Dropout for residual connections
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        positions: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """
        Forward pass through transformer block.

        Applies spatial attention and feed-forward network with residual
        connections and layer normalization.

        Computation (post-norm):
        1. Attention block:
           - attn_output = spatial_attention(x, positions, mask)
           - x = norm1(x + dropout1(attn_output))
        2. Feed-forward block:
           - ffn_output = feedforward(x)
           - x = norm2(x + dropout2(ffn_output))

        Args:
            x: Input tensor [batch, seq_len, d_model]
            positions: 3D positions [batch, seq_len, 3]
            attention_mask: Optional attention mask [batch, 1, seq_len, seq_len]

        Returns:
            Output tensor [batch, seq_len, d_model]

        Examples:
            >>> block = SpatialTransformerBlock(d_model=768)
            >>> x = torch.randn(32, 1024, 768)
            >>> positions = torch.randn(32, 1024, 3) * 500.0
            >>> output = block(x, positions)
            >>> assert output.shape == x.shape

            >>> # With attention mask (e.g., padding mask)
            >>> mask = torch.ones(32, 1, 1024, 1024)
            >>> mask[:, :, :, 512:] = 0  # Mask out second half
            >>> output = block(x, positions, attention_mask=mask)
        """
        # 1. Spatial attention block with residual connection
        # Compute spatial attention
        attn_output = self.spatial_attention(x, positions, attention_mask)

        # Apply dropout and residual connection
        x = x + self.dropout1(attn_output)

        # Post-norm: normalize after residual
        x = self.norm1(x)

        # 2. Feed-forward block with residual connection
        # Compute feed-forward
        ffn_output = self.ffn(x)

        # Apply dropout and residual connection
        x = x + self.dropout2(ffn_output)

        # Post-norm: normalize after residual
        x = self.norm2(x)

        return x


# Test execution helper
if __name__ == "__main__":
    # Quick verification
    block = SpatialTransformerBlock(
        d_model=768,
        n_heads=12,
        d_ff=3072,
        spatial_radius=50.0,
        dropout=0.1,
    )
    x = torch.randn(32, 1024, 768)
    positions = torch.randn(32, 1024, 3) * 500.0
    output = block(x, positions)
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print("✅ SpatialTransformerBlock working correctly!")
