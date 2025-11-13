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
