"""
Test suite for SpatialToken class.

Tests the fundamental spatial-semantic token representation,
including 3D position tracking and distance calculations.
"""

import pytest
import torch
from spatial_engine.core.spatial_token import SpatialToken


class TestSpatialToken:
    """Comprehensive test suite for SpatialToken."""

    def test_initialization(self):
        """Test SpatialToken can be created with valid inputs."""
        token = SpatialToken(
            token_id=42,
            position=(1.0, 2.0, 3.0),
            embedding=torch.randn(768),
            spatial_encoding=torch.randn(768)
        )

        assert token.token_id == 42
        assert token.position == (1.0, 2.0, 3.0)
        assert token.embedding.shape == (768,)
        assert token.spatial_encoding.shape == (768,)

    def test_distance_calculation(self):
        """Test Euclidean distance between two tokens."""
        token1 = SpatialToken(
            token_id=1,
            position=(0.0, 0.0, 0.0),
            embedding=torch.randn(768),
            spatial_encoding=torch.randn(768)
        )
        token2 = SpatialToken(
            token_id=2,
            position=(3.0, 4.0, 0.0),
            embedding=torch.randn(768),
            spatial_encoding=torch.randn(768)
        )

        distance = token1.distance_to(token2)
        assert distance == pytest.approx(5.0)  # 3-4-5 right triangle

    def test_full_embedding_shape(self):
        """Test full_embedding combines semantic + spatial correctly."""
        token = SpatialToken(
            token_id=1,
            position=(0.0, 0.0, 0.0),
            embedding=torch.randn(768),
            spatial_encoding=torch.randn(768)
        )

        full_emb = token.full_embedding
        assert full_emb.shape == (768,)

        # Verify it's actually the sum
        expected = token.embedding + token.spatial_encoding
        assert torch.allclose(full_emb, expected)

    def test_invalid_position(self):
        """Test error handling for invalid positions."""
        with pytest.raises((ValueError, TypeError)):
            token = SpatialToken(
                token_id=1,
                position=(1.0, 2.0),  # Only 2D, should be 3D!
                embedding=torch.randn(768),
                spatial_encoding=torch.randn(768)
            )

    def test_embedding_dimension_mismatch(self):
        """Test error handling for mismatched embedding dimensions."""
        with pytest.raises((ValueError, RuntimeError)):
            token = SpatialToken(
                token_id=1,
                position=(1.0, 2.0, 3.0),
                embedding=torch.randn(768),      # 768D
                spatial_encoding=torch.randn(384)  # 384D - mismatch!
            )
            # Validation happens in __post_init__

    @pytest.mark.parametrize("x,y,z,expected_norm", [
        (1.0, 0.0, 0.0, 1.0),           # Unit vector X
        (0.0, 1.0, 0.0, 1.0),           # Unit vector Y
        (0.0, 0.0, 1.0, 1.0),           # Unit vector Z
        (3.0, 4.0, 0.0, 5.0),           # 3-4-5 triangle
        (1.0, 1.0, 1.0, 1.732),         # Diagonal
        (5.0, 12.0, 0.0, 13.0),         # 5-12-13 triangle
    ])
    def test_position_norms(self, x, y, z, expected_norm):
        """Test distance calculations for various positions."""
        token = SpatialToken(
            token_id=1,
            position=(x, y, z),
            embedding=torch.randn(768),
            spatial_encoding=torch.randn(768)
        )
        origin = SpatialToken(
            token_id=0,
            position=(0.0, 0.0, 0.0),
            embedding=torch.randn(768),
            spatial_encoding=torch.randn(768)
        )

        distance = token.distance_to(origin)
        assert distance == pytest.approx(expected_norm, rel=1e-2)
