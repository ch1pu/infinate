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
conftest_m1112.py - M1.11.2 pytest fixtures for Full Pipeline E2E Tests.

Provides NavigationAttention fixtures that exercise the FULL pipeline
(Qdrant -> Navigator -> LOD -> SpatialAttention -> Output), reusing
M1.11 fixtures for Qdrant adapters and test data.

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11.2 - Full Pipeline Qdrant E2E Tests
"""

import pytest
import torch

from spatial_engine.integration.navigation_attention import NavigationAttention

# Reuse all M1.11 fixtures (Qdrant adapters, data, warp detector, etc.)
pytest_plugins = ["spatial_engine.tests.conftest_m111"]

# M1.11.2 constants (match M1.11)
M1112_D_MODEL = 256
M1112_K_NEIGHBORS = 50
M1112_SPATIAL_RADIUS = 50.0


# ---------------------------------------------------------------------------
# Pytest Marker Configuration
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Register M1.11.2 markers."""
    config.addinivalue_line("markers", "m1112: M1.11.2 Full Pipeline E2E tests")
    config.addinivalue_line(
        "markers", "m1112_integration: M1.11.2 full pipeline integration tests"
    )


# ---------------------------------------------------------------------------
# NavigationAttention Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def m1112_nav_attention() -> NavigationAttention:
    """NavigationAttention with full pipeline enabled (navigation + LOD).

    Function-scoped for fresh state per test.

    Returns:
        NavigationAttention configured for M1.11.2 full pipeline tests
    """
    return NavigationAttention(
        d_model=M1112_D_MODEL,
        n_heads=8,
        k_neighbors=M1112_K_NEIGHBORS,
        spatial_radius=M1112_SPATIAL_RADIUS,
        enable_navigation=True,
        enable_lod=True,
        navigation_max_steps=10,
    )


@pytest.fixture
def m1112_nav_attention_no_nav() -> NavigationAttention:
    """NavigationAttention with navigation disabled (baseline for benchmarks).

    Uses LOD but no navigator — stays at start position.

    Returns:
        NavigationAttention with enable_navigation=False
    """
    return NavigationAttention(
        d_model=M1112_D_MODEL,
        n_heads=8,
        k_neighbors=M1112_K_NEIGHBORS,
        spatial_radius=M1112_SPATIAL_RADIUS,
        enable_navigation=False,
        enable_lod=True,
        navigation_max_steps=10,
    )
