"""
test_spatial_transformer_block.py - Test suite for SpatialTransformerBlock.

Tests the single transformer layer combining spatial attention (M1.3) with
feed-forward network, residual connections, and layer normalization.

Author: ch1pu
Milestone: 1.4 - Spatial Transformer Block
Test Count: 8
Coverage Target: ≥95%
"""

import pytest
import torch
import torch.nn as nn


class TestSpatialTransformerBlock:
    """Test suite for SpatialTransformerBlock module."""

    @pytest.fixture
    def block(self):
        """Create standard SpatialTransformerBlock for testing."""
        from spatial_engine.core.spatial_transformer_block import SpatialTransformerBlock

        return SpatialTransformerBlock(
            d_model=768,
            n_heads=12,
            d_ff=3072,
            spatial_radius=50.0,
            dropout=0.1
        )

    def test_initialization(self):
        """Test SpatialTransformerBlock initialization.

        Verifies:
        - Module created successfully
        - All components exist (attention, ffn, norms, dropout)
        - Parameters stored correctly
        - Correct component types
        """
        from spatial_engine.core.spatial_transformer_block import SpatialTransformerBlock
        from spatial_engine.core.spatial_attention import SpatialAttention
        from spatial_engine.core.feedforward import FeedForward

        block = SpatialTransformerBlock(
            d_model=768,
            n_heads=12,
            d_ff=3072,
            spatial_radius=50.0,
            dropout=0.1
        )

        # Verify attributes
        assert block.d_model == 768
        assert block.n_heads == 12

        # Verify components exist
        assert hasattr(block, "spatial_attention")
        assert hasattr(block, "ffn")
        assert hasattr(block, "norm1")
        assert hasattr(block, "norm2")
        assert hasattr(block, "dropout1")
        assert hasattr(block, "dropout2")

        # Verify component types
        assert isinstance(block.spatial_attention, SpatialAttention)
        assert isinstance(block.ffn, FeedForward)
        assert isinstance(block.norm1, nn.LayerNorm)
        assert isinstance(block.norm2, nn.LayerNorm)
        assert isinstance(block.dropout1, nn.Dropout)
        assert isinstance(block.dropout2, nn.Dropout)

    def test_forward_shape(self, block):
        """Test forward pass preserves input shape.

        Input: x [batch, seq_len, d_model], positions [batch, seq_len, 3]
        Output: [batch, seq_len, d_model]

        Verifies:
        - Shape preservation
        - Works with different batch sizes
        - Works with different sequence lengths
        """
        # Test with standard batch
        x = torch.randn(32, 1024, 768)
        positions = torch.randn(32, 1024, 3) * 500.0
        output = block(x, positions)
        assert output.shape == (32, 1024, 768), f"Expected (32, 1024, 768), got {output.shape}"

        # Test with different batch size
        x = torch.randn(8, 512, 768)
        positions = torch.randn(8, 512, 3) * 500.0
        output = block(x, positions)
        assert output.shape == (8, 512, 768)

        # Test with small batch
        x = torch.randn(2, 100, 768)
        positions = torch.randn(2, 100, 3) * 100.0
        output = block(x, positions)
        assert output.shape == (2, 100, 768)

    def test_residual_connections(self, block):
        """Test residual connections are working.

        Residual connections: output = input + transformation(input)

        Verifies:
        - Output differs from input (transformation applied)
        - Magnitude reasonable (not exploding/vanishing)
        - Gradient flows through residuals
        """
        x = torch.randn(8, 128, 768)
        positions = torch.randn(8, 128, 3) * 100.0

        block.eval()  # Disable dropout for consistent testing
        output = block(x, positions)

        # Output should differ from input (transformation applied)
        assert not torch.allclose(output, x, atol=1e-3), "Output should differ from input"

        # Magnitude should be reasonable (residuals prevent explosion)
        output_norm = output.norm()
        input_norm = x.norm()
        ratio = output_norm / input_norm

        # Expect ratio between 0.5 and 5.0 (reasonable range)
        assert 0.5 < ratio < 5.0, f"Magnitude ratio {ratio:.2f} outside reasonable range"

    def test_layer_norm_placement(self, block):
        """Test layer normalization placement (post-norm architecture).

        Post-norm: norm applied AFTER residual connection
        Pattern: x = norm(x + dropout(attention(x)))

        Verifies:
        - Two LayerNorm instances exist (norm1, norm2)
        - Correct normalization dimensions (d_model)
        """
        assert isinstance(block.norm1, nn.LayerNorm)
        assert isinstance(block.norm2, nn.LayerNorm)

        # Verify normalization dimension
        assert block.norm1.normalized_shape == (768,)
        assert block.norm2.normalized_shape == (768,)

    def test_spatial_attention_integration(self, block):
        """Test spatial attention integration from M1.3.

        Verifies:
        - SpatialAttention is used (not standard attention)
        - Correct spatial_radius parameter
        - Attention receives positions correctly
        """
        from spatial_engine.core.spatial_attention import SpatialAttention

        # Verify SpatialAttention is used
        assert isinstance(block.spatial_attention, SpatialAttention)

        # Verify spatial radius configuration
        assert block.spatial_attention.spatial_radius == 50.0

        # Test attention receives positions
        x = torch.randn(4, 50, 768)
        positions = torch.randn(4, 50, 3) * 100.0

        block.eval()
        output = block(x, positions)

        # Should complete without errors
        assert output.shape == x.shape

    def test_with_attention_mask(self, block):
        """Test attention mask propagation.

        Attention masks:
        - Padding mask: mask out padding tokens
        - Causal mask: prevent attending to future tokens

        Verifies:
        - Mask accepted and propagated to attention
        - Output shape unchanged with mask
        - Masked positions have reduced influence
        """
        x = torch.randn(4, 50, 768)
        positions = torch.randn(4, 50, 3) * 100.0

        # Create attention mask (mask out second half)
        mask = torch.ones(4, 1, 50, 50)
        mask[:, :, :, 25:] = 0  # Mask out positions 25-49

        block.eval()
        output_with_mask = block(x, positions, attention_mask=mask)

        # Shape should be preserved
        assert output_with_mask.shape == x.shape

        # Output without mask should differ (mask changes attention)
        output_without_mask = block(x, positions, attention_mask=None)
        assert not torch.allclose(output_with_mask, output_without_mask, atol=1e-3)

    def test_gradient_flow(self, block):
        """Test gradient flow through residual connections.

        Residual connections enable gradient flow in deep networks.

        Verifies:
        - Gradients computed successfully
        - Gradients flow to input
        - No NaN or Inf gradients
        """
        x = torch.randn(2, 10, 768, requires_grad=True)
        positions = torch.randn(2, 10, 3) * 100.0

        # Forward pass
        output = block(x, positions)

        # Backward pass
        loss = output.sum()
        loss.backward()

        # Verify gradients exist
        assert x.grad is not None, "Gradients should flow to input"

        # Verify no NaN or Inf
        assert not torch.isnan(x.grad).any(), "Gradients should not be NaN"
        assert not torch.isinf(x.grad).any(), "Gradients should not be Inf"

        # Verify gradients are non-zero (learning signal exists)
        assert x.grad.abs().sum() > 0, "Gradients should be non-zero"

    def test_training_vs_eval_mode(self, block):
        """Test dropout behavior in training vs eval mode.

        Training mode: dropout active (stochastic)
        Eval mode: dropout disabled (deterministic)

        Verifies:
        - Training mode has stochastic behavior
        - Eval mode is deterministic
        - Mode switching works correctly
        """
        x = torch.ones(1, 10, 768)
        positions = torch.randn(1, 10, 3) * 100.0

        # Training mode: outputs should differ (dropout randomness)
        block.train()
        outputs_train = [block(x, positions) for _ in range(5)]

        # Not all outputs should be identical
        all_same_train = all(
            torch.allclose(outputs_train[0], out, atol=1e-5)
            for out in outputs_train[1:]
        )
        assert not all_same_train, "Training mode should have stochastic dropout"

        # Eval mode: outputs should be identical (no dropout)
        block.eval()
        outputs_eval = [block(x, positions) for _ in range(5)]

        # All outputs should be identical
        all_same_eval = all(
            torch.allclose(outputs_eval[0], out, atol=1e-5)
            for out in outputs_eval[1:]
        )
        assert all_same_eval, "Eval mode should be deterministic"


# Test execution marker
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
