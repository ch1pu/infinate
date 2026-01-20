"""
Test suite for SpatialAttentionWithLOD integration.

Tests the LOD-enhanced spatial attention wrapper from Milestone 1.10:
- Initialization and configuration
- Forward pass with LOD compression
- Backward compatibility with SpatialAttention
- Quality preservation and context expansion

Author: ch1pu (Adolfo Lopez) - Alpha Deploy LLC
Created: 2025-01-19
Milestone: 1.10 - Hierarchical LOD System
"""

import pytest
import torch

from spatial_engine.core.lod import LODConfig, LODLevel
from spatial_engine.core.spatial_attention import SpatialAttention
from spatial_engine.core.spatial_attention_lod import (
    SpatialAttentionWithLOD,
    create_lod_attention,
)


class TestSpatialAttentionWithLODInit:
    """Tests for SpatialAttentionWithLOD initialization."""

    def test_initialization(self):
        """Test SpatialAttentionWithLOD can be instantiated."""
        attn = SpatialAttentionWithLOD(
            d_model=768,
            n_heads=12,
            spatial_radius=50.0,
        )

        assert attn.d_model == 768
        assert attn.n_heads == 12
        assert attn.spatial_radius == 50.0
        assert attn.enable_lod is True

    def test_initialization_with_custom_config(self):
        """Test initialization with custom LOD configuration."""
        custom_levels = [
            LODLevel("close", 0.0, 100.0, 1, 100),
            LODLevel("far", 100.0, float('inf'), 10, 10),
        ]
        config = LODConfig(levels=custom_levels)

        attn = SpatialAttentionWithLOD(
            d_model=768,
            n_heads=12,
            lod_config=config,
        )

        assert len(attn.lod.config.levels) == 2
        assert attn.lod.config.levels[0].name == "close"

    def test_initialization_lod_disabled(self):
        """Test initialization with LOD disabled."""
        attn = SpatialAttentionWithLOD(
            d_model=768,
            n_heads=12,
            enable_lod=False,
        )

        assert attn.enable_lod is False

    def test_has_spatial_attention(self):
        """Test wrapped SpatialAttention is accessible."""
        attn = SpatialAttentionWithLOD(d_model=768, n_heads=12)

        assert isinstance(attn.spatial_attention, SpatialAttention)
        assert attn.spatial_attention.d_model == 768

    def test_compression_methods(self):
        """Test both compression methods work."""
        attn_merge = SpatialAttentionWithLOD(
            d_model=768, n_heads=12, compression_method="merge"
        )
        attn_cluster = SpatialAttentionWithLOD(
            d_model=768, n_heads=12, compression_method="cluster"
        )

        assert attn_merge.lod.compression_method == "merge"
        assert attn_cluster.lod.compression_method == "cluster"


class TestSpatialAttentionWithLODForward:
    """Tests for SpatialAttentionWithLOD forward pass."""

    @pytest.fixture
    def attn(self):
        """Create standard LOD attention for testing."""
        return SpatialAttentionWithLOD(
            d_model=768,
            n_heads=12,
            spatial_radius=50.0,
            compression_method="cluster",
        )

    def test_forward_pass_shapes(self, attn):
        """Test forward pass produces correct output shapes."""
        batch_size = 4
        seq_len = 32

        x = torch.randn(batch_size, seq_len, 768)
        positions = torch.randn(batch_size, seq_len, 3) * 200.0

        output = attn(x, positions)

        assert output.shape == (batch_size, seq_len, 768)

    def test_output_dtype_device(self, attn):
        """Test output has correct dtype and device."""
        x = torch.randn(2, 16, 768)
        positions = torch.randn(2, 16, 3) * 100.0

        output = attn(x, positions)

        assert output.dtype == x.dtype
        assert output.device == x.device

    def test_attention_weights_valid(self, attn):
        """Test attention weights are valid probabilities."""
        x = torch.randn(2, 16, 768)
        positions = torch.randn(2, 16, 3) * 100.0

        weights = attn.get_attention_weights(x, positions)

        # Weights should be in [0, 1]
        assert torch.all(weights >= 0.0)
        assert torch.all(weights <= 1.0)

    def test_gradient_flow(self, attn):
        """Test gradients flow through LOD attention."""
        x = torch.randn(2, 16, 768, requires_grad=True)
        positions = torch.randn(2, 16, 3) * 100.0

        output = attn(x, positions)
        loss = output.sum()
        loss.backward()

        assert x.grad is not None
        assert x.grad.abs().sum() > 0

    def test_lod_disabled_bypass(self):
        """Test LOD disabled bypasses compression."""
        attn = SpatialAttentionWithLOD(
            d_model=768, n_heads=12, enable_lod=False
        )

        x = torch.randn(2, 16, 768)
        positions = torch.randn(2, 16, 3) * 100.0

        # Should work without LOD compression
        output = attn(x, positions)

        assert output.shape == (2, 16, 768)

    def test_forward_with_attention_mask(self, attn):
        """Test forward pass with attention mask."""
        batch_size = 2
        seq_len = 16

        x = torch.randn(batch_size, seq_len, 768)
        positions = torch.randn(batch_size, seq_len, 3) * 100.0

        # Create causal mask
        mask = torch.ones(batch_size, 1, seq_len, seq_len)
        mask = torch.tril(mask)

        output = attn(x, positions, attention_mask=mask)

        assert output.shape == (batch_size, seq_len, 768)
        assert torch.all(torch.isfinite(output))

    def test_forward_with_context(self, attn):
        """Test forward pass with external context."""
        batch_size = 2
        seq_len = 16
        context_len = 100

        x = torch.randn(batch_size, seq_len, 768)
        positions = torch.randn(batch_size, seq_len, 3)
        context = torch.randn(batch_size, context_len, 768)
        context_pos = torch.randn(batch_size, context_len, 3) * 300.0

        output = attn(x, positions, context=context, context_positions=context_pos)

        assert output.shape == (batch_size, seq_len, 768)


class TestLODContextExpansion:
    """Tests for LOD context expansion functionality."""

    @pytest.fixture
    def attn(self):
        """Create LOD attention for testing."""
        return SpatialAttentionWithLOD(d_model=768, n_heads=12)

    def test_context_expansion_ratio(self, attn):
        """Test context expansion ratio is reported correctly."""
        ratio = attn.context_expansion_ratio

        # Default config gives ~10× expansion
        assert ratio > 9.0
        assert ratio < 11.0

    def test_lod_statistics(self, attn):
        """Test LOD statistics are computed correctly."""
        positions = torch.randn(4, 100, 3) * 300.0

        stats = attn.get_lod_statistics(positions)

        assert 'total_tokens' in stats
        assert 'context_expansion' in stats
        assert 'near_count' in stats
        assert 'medium_count' in stats
        assert 'far_count' in stats
        assert 'beyond_count' in stats

        assert stats['total_tokens'] == 100

    def test_lod_improves_context_coverage(self, attn):
        """Test LOD provides better context coverage than hard cutoff."""
        batch_size = 4
        seq_len = 200

        # Create positions spread across LOD levels
        positions = torch.randn(batch_size, seq_len, 3) * 500.0

        stats = attn.get_lod_statistics(positions)

        # With LOD, we should have tokens at multiple levels
        # Note: counts are summed across all batches
        total_visible = (
            stats['near_count'] +
            stats['medium_count'] +
            stats['far_count'] +
            stats['beyond_count']
        )

        # All tokens across all batches should be assigned
        assert total_visible == batch_size * seq_len


class TestBackwardCompatibility:
    """Tests for backward compatibility with SpatialAttention."""

    def test_same_interface_as_spatial_attention(self):
        """Test SpatialAttentionWithLOD has same basic interface."""
        base_attn = SpatialAttention(d_model=768, n_heads=12)
        lod_attn = SpatialAttentionWithLOD(d_model=768, n_heads=12)

        x = torch.randn(2, 16, 768)
        positions = torch.randn(2, 16, 3) * 50.0  # Near positions

        # Both should work with same inputs
        output_base = base_attn(x, positions)
        output_lod = lod_attn(x, positions)

        assert output_base.shape == output_lod.shape

    def test_lod_disabled_matches_base(self):
        """Test LOD disabled produces similar results to base attention."""
        base_attn = SpatialAttention(
            d_model=768, n_heads=12, spatial_radius=50.0
        )
        lod_attn = SpatialAttentionWithLOD(
            d_model=768, n_heads=12, spatial_radius=50.0, enable_lod=False
        )

        # Copy weights for exact match
        lod_attn.spatial_attention.load_state_dict(base_attn.state_dict())

        # Put both in eval mode to disable dropout (which causes randomness)
        base_attn.eval()
        lod_attn.eval()

        # Set seed after models are created to ensure identical inputs
        torch.manual_seed(42)
        x = torch.randn(2, 16, 768)
        positions = torch.randn(2, 16, 3) * 50.0

        output_base = base_attn(x, positions)
        output_lod = lod_attn(x, positions)

        # With LOD disabled and same weights, should be identical
        assert torch.allclose(output_base, output_lod, atol=1e-5)


class TestCreateLODAttention:
    """Tests for create_lod_attention factory function."""

    def test_factory_default(self):
        """Test factory creates valid attention with defaults."""
        attn = create_lod_attention()

        assert isinstance(attn, SpatialAttentionWithLOD)
        assert attn.d_model == 768
        assert attn.n_heads == 12

    def test_factory_custom_params(self):
        """Test factory with custom parameters."""
        attn = create_lod_attention(
            d_model=512,
            n_heads=8,
            spatial_radius=100.0,
            compression_method="merge",
        )

        assert attn.d_model == 512
        assert attn.n_heads == 8
        assert attn.spatial_radius == 100.0
        assert attn.lod.compression_method == "merge"

    def test_factory_custom_levels(self):
        """Test factory with custom LOD levels."""
        custom_levels = [
            LODLevel("close", 0.0, 100.0, 1, 100),
            LODLevel("distant", 100.0, float('inf'), 50, 10),
        ]

        attn = create_lod_attention(custom_levels=custom_levels)

        assert len(attn.lod.config.levels) == 2


class TestLODPerformance:
    """Performance-related tests for LOD attention."""

    def test_large_sequence_handling(self):
        """Test LOD attention handles large sequences."""
        attn = SpatialAttentionWithLOD(d_model=768, n_heads=12)

        batch_size = 2
        seq_len = 512

        x = torch.randn(batch_size, seq_len, 768)
        positions = torch.randn(batch_size, seq_len, 3) * 500.0

        output = attn(x, positions)

        assert output.shape == (batch_size, seq_len, 768)
        assert torch.all(torch.isfinite(output))

    def test_output_quality_near_tokens(self):
        """Test near tokens maintain high quality output."""
        attn = SpatialAttentionWithLOD(d_model=768, n_heads=12)

        # All near positions (within radius 50)
        x = torch.randn(2, 32, 768)
        positions = torch.randn(2, 32, 3) * 10.0  # Very close

        output = attn(x, positions)

        # Output should be finite and have reasonable magnitude
        assert torch.all(torch.isfinite(output))
        assert output.std() > 0.01  # Not all zeros


class TestDevicePlacement:
    """Tests for device placement."""

    def test_cpu_execution(self):
        """Test LOD attention works on CPU."""
        attn = SpatialAttentionWithLOD(d_model=768, n_heads=12)

        x = torch.randn(2, 16, 768)
        positions = torch.randn(2, 16, 3) * 100.0

        output = attn(x, positions)

        assert output.device.type == "cpu"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_gpu_execution(self):
        """Test LOD attention works on GPU."""
        try:
            cap = torch.cuda.get_device_capability()
            if cap[0] >= 12:
                pytest.skip("GPU compute capability not supported by current PyTorch")
        except Exception:
            pytest.skip("GPU capability check failed")

        attn = SpatialAttentionWithLOD(d_model=768, n_heads=12).cuda()

        x = torch.randn(2, 16, 768).cuda()
        positions = torch.randn(2, 16, 3).cuda() * 100.0

        output = attn(x, positions)

        assert output.device.type == "cuda"
