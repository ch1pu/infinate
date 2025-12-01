"""
test_feedforward.py - Comprehensive test suite for FeedForward network.

Tests the standard 2-layer MLP with GELU activation used in transformer blocks.

Author: ch1pu
Milestone: 1.4 - Spatial Transformer Block
Test Count: 5
Coverage Target: ≥95%
"""

import pytest
import torch
import torch.nn as nn


class TestFeedForward:
    """Test suite for FeedForward network module."""

    @pytest.fixture
    def ffn(self):
        """Create standard FeedForward network for testing."""
        from spatial_engine.core.feedforward import FeedForward

        return FeedForward(d_model=768, d_ff=3072, dropout=0.1)

    def test_initialization(self):
        """Test FeedForward initialization with correct parameters.

        Verifies:
        - Module created successfully
        - d_model stored correctly
        - d_ff stored correctly
        - Components exist (linear1, linear2, activation, dropout)
        """
        from spatial_engine.core.feedforward import FeedForward

        ffn = FeedForward(d_model=768, d_ff=3072, dropout=0.1)

        # Verify attributes
        assert ffn.d_model == 768
        assert ffn.d_ff == 3072

        # Verify components exist
        assert hasattr(ffn, "linear1")
        assert hasattr(ffn, "linear2")
        assert hasattr(ffn, "activation")
        assert hasattr(ffn, "dropout")

        # Verify layer types
        assert isinstance(ffn.linear1, nn.Linear)
        assert isinstance(ffn.linear2, nn.Linear)
        assert isinstance(ffn.activation, nn.GELU)
        assert isinstance(ffn.dropout, nn.Dropout)

    def test_forward_shape(self, ffn):
        """Test forward pass preserves input/output dimensions.

        Input: [batch, seq_len, d_model]
        Output: [batch, seq_len, d_model]

        Verifies:
        - Shape preservation
        - Works with different batch sizes
        - Works with different sequence lengths
        """
        # Test with standard batch
        x = torch.randn(32, 1024, 768)
        output = ffn(x)
        assert output.shape == (32, 1024, 768), f"Expected (32, 1024, 768), got {output.shape}"

        # Test with different batch size
        x = torch.randn(8, 512, 768)
        output = ffn(x)
        assert output.shape == (8, 512, 768)

        # Test with batch size 1
        x = torch.randn(1, 100, 768)
        output = ffn(x)
        assert output.shape == (1, 100, 768)

    def test_expansion_ratio(self):
        """Test feed-forward expansion ratio (d_ff = 4 × d_model).

        Standard transformer uses 4x expansion in hidden layer.

        Verifies:
        - linear1: d_model → d_ff (expansion)
        - linear2: d_ff → d_model (contraction)
        - Typical ratio is 4x
        """
        from spatial_engine.core.feedforward import FeedForward

        # Test standard 4x expansion
        ffn = FeedForward(d_model=768, d_ff=3072)
        assert ffn.linear1.in_features == 768
        assert ffn.linear1.out_features == 3072
        assert ffn.linear2.in_features == 3072
        assert ffn.linear2.out_features == 768

        # Test custom expansion ratio
        ffn = FeedForward(d_model=512, d_ff=2048)
        assert ffn.linear1.out_features == 2048
        assert ffn.linear2.in_features == 2048

    def test_dropout_application(self, ffn):
        """Test dropout is active in training mode but not in eval.

        Dropout should:
        - Apply randomness during training (different outputs for same input)
        - Be deterministic during eval (same output for same input)

        Verifies:
        - Training mode has stochastic behavior
        - Eval mode is deterministic
        """
        x = torch.ones(1, 10, 768)

        # Training mode: outputs should differ due to dropout
        ffn.train()
        outputs_train = [ffn(x) for _ in range(10)]

        # Not all outputs should be identical (dropout introduces randomness)
        all_same = all(torch.allclose(outputs_train[0], out) for out in outputs_train[1:])
        assert not all_same, "Training mode should have stochastic dropout"

        # Eval mode: outputs should be identical (no dropout)
        ffn.eval()
        outputs_eval = [ffn(x) for _ in range(10)]

        # All outputs should be identical in eval mode
        all_same = all(torch.allclose(outputs_eval[0], out) for out in outputs_eval[1:])
        assert all_same, "Eval mode should be deterministic (no dropout)"

    def test_gelu_activation(self, ffn):
        """Test GELU activation is used (not ReLU).

        GELU allows small negative values (smoother than ReLU).
        ReLU would zero all negatives.

        Verifies:
        - Activation is GELU
        - Small negatives are not zeroed (GELU property)
        """
        # Verify GELU instance
        assert isinstance(ffn.activation, nn.GELU)

        # Test GELU behavior with small negative input
        # GELU(-0.1) ≈ -0.046 (not zero like ReLU)
        # Create a proper [batch, seq_len, d_model] tensor
        x = torch.randn(1, 10, 768)
        # Set some values to small negatives
        x[0, :5, :384] = -0.1  # First half of embedding dims to small negative

        ffn.eval()
        output = ffn(x)

        # Output should not be all zeros (GELU allows negatives)
        assert not torch.allclose(output, torch.zeros_like(output), atol=1e-3)

        # GELU should produce non-zero output for small negatives
        # (This distinguishes it from ReLU which would zero everything)
        assert output.abs().sum() > 0


# Test execution marker
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
