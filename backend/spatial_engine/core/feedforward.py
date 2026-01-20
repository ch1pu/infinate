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
#     10,317x speedup over MIT's approach with 89.58% test coverage.
# ============================================================================

"""
feedforward.py - Standard feed-forward network for transformer blocks.

Implements the 2-layer MLP with GELU activation used in transformer architectures.
Follows the standard pattern: d_model → d_ff → d_model with expansion ratio of 4×.

Author: ch1pu
Milestone: 1.4 - Spatial Transformer Block
Architecture: Vaswani et al. (2017) "Attention is All You Need"
"""

import torch
import torch.nn as nn


class FeedForward(nn.Module):
    """
    2-layer MLP with GELU activation.

    Standard transformer feed-forward network:
    1. Linear expansion: d_model → d_ff (typically 4× expansion)
    2. GELU activation (smoother than ReLU)
    3. Dropout
    4. Linear contraction: d_ff → d_model
    5. Dropout

    Args:
        d_model: Input and output dimension (embedding size)
        d_ff: Hidden dimension (default: 4 × d_model)
        dropout: Dropout probability (default: 0.1)

    Shape:
        - Input: [batch, seq_len, d_model]
        - Output: [batch, seq_len, d_model]

    Examples:
        >>> ffn = FeedForward(d_model=768, d_ff=3072, dropout=0.1)
        >>> x = torch.randn(32, 1024, 768)
        >>> output = ffn(x)
        >>> assert output.shape == (32, 1024, 768)

    Note:
        GELU activation is used instead of ReLU for smoother gradients.
        GELU allows small negative values (GELU(-0.1) ≈ -0.046),
        while ReLU zeros all negatives.

    Reference:
        Vaswani et al. (2017): "Attention is All You Need"
        https://arxiv.org/abs/1706.03762
    """

    def __init__(
        self,
        d_model: int = 768,
        d_ff: int = 3072,
        dropout: float = 0.1,
    ) -> None:
        """
        Initialize FeedForward network.

        Args:
            d_model: Input/output dimension (embedding size)
            d_ff: Hidden dimension (typically 4 × d_model)
            dropout: Dropout probability for regularization
        """
        super().__init__()

        # Store parameters
        self.d_model = d_model
        self.d_ff = d_ff

        # Two linear transformations
        # Expansion: d_model → d_ff
        self.linear1 = nn.Linear(d_model, d_ff)

        # Contraction: d_ff → d_model
        self.linear2 = nn.Linear(d_ff, d_model)

        # GELU activation (smoother than ReLU)
        self.activation = nn.GELU()

        # Dropout for regularization
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through feed-forward network.

        Computation:
        1. x → Linear1 (expansion to d_ff)
        2. GELU activation
        3. Dropout
        4. Linear2 (contraction to d_model)
        5. Dropout

        Args:
            x: Input tensor [batch, seq_len, d_model]

        Returns:
            Output tensor [batch, seq_len, d_model]

        Examples:
            >>> ffn = FeedForward(d_model=768, d_ff=3072)
            >>> x = torch.randn(32, 1024, 768)
            >>> output = ffn(x)
            >>> assert output.shape == x.shape
        """
        # Expand to hidden dimension
        x = self.linear1(x)  # [batch, seq_len, d_model] → [batch, seq_len, d_ff]

        # GELU activation
        x = self.activation(x)

        # Dropout (active in training mode)
        x = self.dropout(x)

        # Contract back to d_model
        x = self.linear2(x)  # [batch, seq_len, d_ff] → [batch, seq_len, d_model]

        # Dropout (active in training mode)
        x = self.dropout(x)

        return x


# Test execution helper
if __name__ == "__main__":
    # Quick verification
    ffn = FeedForward(d_model=768, d_ff=3072, dropout=0.1)
    x = torch.randn(32, 1024, 768)
    output = ffn(x)
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print("✅ FeedForward working correctly!")
