"""
Test suite for SpatialPositionEncoding class.

Tests 3D spatial positional encoding with sinusoidal patterns,
following ch1pu's revolutionary architecture for O(k) attention.

Author: ch1pu (System Architect, Lead Developer)
Created: 2025-01-13
"""

import math
import time

import pytest
import torch

from spatial_engine.core.spatial_encoding import SpatialPositionEncoding


class TestSpatialPositionEncoding:
    """Comprehensive test suite for 3D spatial positional encoding."""

    @pytest.fixture
    def encoder(self):
        """Create standard encoder (768D, max_position=1000)."""
        return SpatialPositionEncoding(
            d_model=768, max_position=1000.0, temperature=10000.0
        )

    def test_initialization(self):
        """Test SpatialPositionEncoding can be instantiated."""
        encoder = SpatialPositionEncoding(d_model=768)

        assert encoder.d_model == 768
        assert encoder.max_position == 1000.0
        assert encoder.d_per_dim == 256  # 768 / 3

    def test_output_shape(self, encoder):
        """Test output has correct dimensions [batch, seq_len, d_model]."""
        batch_size = 4
        seq_len = 128

        positions = torch.randn(batch_size, seq_len, 3) * 500.0
        encoding = encoder(positions)

        assert encoding.shape == (batch_size, seq_len, 768)

    def test_single_dimension_encoding(self, encoder):
        """Test encode_dimension() for individual X/Y/Z."""
        coords = torch.tensor([[0.0, 100.0, 500.0]])  # [1, 3]

        x_enc = encoder.encode_dimension(coords[:, 0], dim_idx=0)

        assert x_enc.shape == (1, 256)  # d_per_dim

    def test_frequency_generation(self, encoder):
        """Test frequency bands are computed correctly."""
        freqs = encoder.freqs

        # Should have d_per_dim // 2 frequencies
        assert freqs.shape == (128,)  # 256 / 2

        # Frequencies should decay exponentially
        assert freqs[0] > freqs[-1]
        assert torch.all(freqs > 0)

    def test_position_normalization(self, encoder):
        """Test positions are normalized to [-1, 1]."""
        # Position at max_position should normalize to 1.0
        positions = torch.tensor([[[1000.0, 1000.0, 1000.0]]])
        encoding = encoder(positions)

        # Encoding should not overflow
        assert torch.all(torch.isfinite(encoding))
        assert torch.all(torch.abs(encoding) < 100)  # Reasonable range

    def test_sinusoidal_pattern(self, encoder):
        """Test sin/cos components are present."""
        positions = torch.tensor([[[100.0, 200.0, 300.0]]])
        encoding = encoder(positions)

        # Should have both positive and negative values (sin/cos)
        assert torch.any(encoding > 0)
        assert torch.any(encoding < 0)

        # Should be bounded by [-1, 1] approximately
        assert torch.all(encoding >= -2.0)
        assert torch.all(encoding <= 2.0)

    @pytest.mark.parametrize("d_model", [384, 512, 768, 1024])
    def test_different_d_model(self, d_model):
        """Test encoding works with different embedding dimensions."""
        encoder = SpatialPositionEncoding(d_model=d_model)
        positions = torch.randn(2, 10, 3) * 500.0

        encoding = encoder(positions)

        assert encoding.shape == (2, 10, d_model)

    def test_batch_processing(self, encoder):
        """Test batches are processed correctly."""
        batch_size = 16
        seq_len = 64

        positions = torch.randn(batch_size, seq_len, 3) * 500.0
        encoding = encoder(positions)

        assert encoding.shape == (batch_size, seq_len, 768)

        # Each batch should be independent
        encoding_batch0 = encoder(positions[0:1])
        assert torch.allclose(encoding[0], encoding_batch0[0], rtol=1e-5)

    @pytest.mark.parametrize(
        "x,y,z",
        [
            (0.0, 0.0, 0.0),  # Origin
            (1000.0, 1000.0, 1000.0),  # Max position
            (-500.0, -500.0, -500.0),  # Negative positions
            (1.5, 2.7, 3.9),  # Fractional
        ],
    )
    def test_edge_positions(self, encoder, x, y, z):
        """Test encoding at edge case positions."""
        positions = torch.tensor([[[x, y, z]]])
        encoding = encoder(positions)

        assert encoding.shape == (1, 1, 768)
        assert torch.all(torch.isfinite(encoding))

    def test_deterministic(self, encoder):
        """Test same position always produces same encoding."""
        positions = torch.tensor([[[123.45, 678.90, 234.56]]])

        encoding1 = encoder(positions)
        encoding2 = encoder(positions)

        assert torch.allclose(encoding1, encoding2, rtol=1e-7)

    @pytest.mark.benchmark
    def test_batch_performance(self):
        """Benchmark: <60ms for batch of 32 sequences × 1024 tokens (CPU)."""
        encoder = SpatialPositionEncoding(d_model=768)

        # Realistic batch size
        positions = torch.randn(32, 1024, 3) * 500.0

        # Warmup (10 iterations)
        for _ in range(10):
            _ = encoder(positions)

        # Benchmark (100 iterations)
        start = time.perf_counter()
        iterations = 100

        for _ in range(iterations):
            encoding = encoder(positions)  # noqa: F841

        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / iterations) * 1000

        # Performance target: <60ms for CPU execution
        # Note: GPU execution would be <5ms
        assert avg_ms < 60.0, f"Too slow: {avg_ms:.2f}ms (target: <60ms on CPU)"

        print(f"✓ Spatial encoding: {avg_ms:.2f}ms per batch (32×1024 positions)")
