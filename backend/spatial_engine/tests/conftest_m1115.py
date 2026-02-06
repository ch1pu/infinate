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
conftest_m1115.py - M1.11.5 pytest fixtures for GPU-Resident Vector Store.

Provides fixtures for GPUSpatialIndex testing:
  - Empty index on GPU
  - Loaded indices at various token counts (1K, 10K)

Chains M1.11.4 fixtures for gpu_device and shared infrastructure.

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11.5 - GPU-Resident Vector Store ("Loading Screen")
"""

import pytest
import torch

from spatial_engine.vector_store.gpu_spatial_index import GPUSpatialIndex

# Chain M1.11.4 fixtures (which chains M1.11.3 -> M1.11.2 -> M1.11)
pytest_plugins = ["spatial_engine.tests.conftest_m1114"]

# M1.11.5 constants
M1115_CELL_SIZE = 50.0
M1115_VRAM_BUDGET_GB = 10.0
M1115_D_MODEL = 256  # Match M1.11.4


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def m1115_gpu_spatial_index(gpu_device: torch.device) -> GPUSpatialIndex:
    """Empty GPUSpatialIndex on GPU.

    Args:
        gpu_device: CUDA device fixture from conftest_m1113

    Returns:
        Empty GPUSpatialIndex ready for load()
    """
    return GPUSpatialIndex(
        cell_size=M1115_CELL_SIZE,
        vram_budget_gb=M1115_VRAM_BUDGET_GB,
        device=gpu_device,
    )


@pytest.fixture
def m1115_loaded_index_1k(gpu_device: torch.device) -> GPUSpatialIndex:
    """GPUSpatialIndex loaded with 1K tokens.

    Args:
        gpu_device: CUDA device fixture from conftest_m1113

    Returns:
        GPUSpatialIndex with 1,000 tokens loaded
    """
    index = GPUSpatialIndex(
        cell_size=M1115_CELL_SIZE,
        vram_budget_gb=M1115_VRAM_BUDGET_GB,
        device=gpu_device,
    )
    torch.manual_seed(42)
    embeddings = torch.randn(1000, M1115_D_MODEL)
    positions = torch.randn(1000, 3) * 500.0
    index.load(embeddings, positions)
    return index


@pytest.fixture
def m1115_loaded_index_10k(gpu_device: torch.device) -> GPUSpatialIndex:
    """GPUSpatialIndex loaded with 10K tokens.

    Args:
        gpu_device: CUDA device fixture from conftest_m1113

    Returns:
        GPUSpatialIndex with 10,000 tokens loaded
    """
    index = GPUSpatialIndex(
        cell_size=M1115_CELL_SIZE,
        vram_budget_gb=M1115_VRAM_BUDGET_GB,
        device=gpu_device,
    )
    torch.manual_seed(42)
    embeddings = torch.randn(10000, M1115_D_MODEL)
    positions = torch.randn(10000, 3) * 500.0
    index.load(embeddings, positions)
    return index
