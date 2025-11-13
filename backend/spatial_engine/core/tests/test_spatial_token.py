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
