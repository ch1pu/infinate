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
conftest_m1114.py - M1.11.4 pytest fixtures for Full Pipeline GPU Coverage.

Phase A fixtures: Testing 4 previously-untested pipeline stages on GPU:
  Stage 1: SpatialToken (dataclass with CUDA tensors)
  Stage 2: SpatialPositionEncoding (nn.Module with buffer)
  Stage 4: SpatialTransformer (nn.Module with ModuleList)
  Stage 5: VectorStore GPU transfer (simulated CPU→GPU path)

Phase B fixtures: Full pipeline vs O(n²) baseline comparison:
  NavigationAttention (GPU/CPU) for full 7-stage pipeline benchmarks

Chains M1.11.3 fixtures for gpu_device and shared infrastructure.

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11.4 - Full Pipeline GPU Coverage (Phase A + B)
"""

import pytest
import torch

from spatial_engine.core.spatial_encoding import SpatialPositionEncoding
from spatial_engine.core.spatial_transformer import SpatialTransformer
from spatial_engine.integration.navigation_attention import NavigationAttention

# Chain M1.11.3 fixtures (which chains M1.11.2 -> M1.11)
pytest_plugins = ["spatial_engine.tests.conftest_m1113"]

# M1.11.4 constants (match M1.11.3 d_model, smaller layers for fast verification)
M1114_D_MODEL = 256
M1114_N_HEADS = 8
M1114_N_LAYERS = 2
M1114_D_FF = 1024
M1114_K_NEIGHBORS = 50
M1114_SPATIAL_RADIUS = 50.0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def m1114_spatial_encoding_gpu(gpu_device: torch.device) -> SpatialPositionEncoding:
    """SpatialPositionEncoding on GPU for Stage 2 tests.

    Args:
        gpu_device: CUDA device fixture from conftest_m1113

    Returns:
        SpatialPositionEncoding moved to GPU
    """
    return SpatialPositionEncoding(d_model=M1114_D_MODEL).to(gpu_device)


@pytest.fixture
def m1114_spatial_transformer_gpu(gpu_device: torch.device) -> SpatialTransformer:
    """SpatialTransformer (2 layers) on GPU for Stage 4 tests.

    Args:
        gpu_device: CUDA device fixture from conftest_m1113

    Returns:
        SpatialTransformer moved to GPU
    """
    return SpatialTransformer(
        n_layers=M1114_N_LAYERS,
        d_model=M1114_D_MODEL,
        n_heads=M1114_N_HEADS,
        d_ff=M1114_D_FF,
        spatial_radius=M1114_SPATIAL_RADIUS,
        dropout=0.1,
    ).to(gpu_device)


@pytest.fixture
def m1114_spatial_transformer_cpu() -> SpatialTransformer:
    """SpatialTransformer (2 layers) on CPU for parity checks.

    Returns:
        SpatialTransformer on CPU
    """
    return SpatialTransformer(
        n_layers=M1114_N_LAYERS,
        d_model=M1114_D_MODEL,
        n_heads=M1114_N_HEADS,
        d_ff=M1114_D_FF,
        spatial_radius=M1114_SPATIAL_RADIUS,
        dropout=0.1,
    )


_CPU_DEVICE = torch.device("cpu")


@pytest.fixture
def m1114_positions_factory():  # type: ignore[no-untyped-def]
    """Factory for creating position tensors on a specific device.

    Returns:
        PositionsFactory instance with create() method
    """

    class PositionsFactory:
        """Creates reproducible position tensors on a specified device."""

        def create(
            self,
            batch: int,
            seq_len: int,
            device: torch.device = _CPU_DEVICE,
            seed: int = 42,
        ) -> torch.Tensor:
            """Create 3D position tensors.

            Args:
                batch: Batch size
                seq_len: Sequence length
                device: Target device
                seed: Random seed for reproducibility

            Returns:
                Positions tensor [batch, seq_len, 3] on device
            """
            torch.manual_seed(seed)
            return torch.randn(batch, seq_len, 3, device=device) * 500.0

    return PositionsFactory()


@pytest.fixture
def m1114_simulated_vectorstore_results():  # type: ignore[no-untyped-def]
    """Factory for simulated VectorStore results (always CPU tensors).

    Simulates the output of QdrantSpatialAdapter.search_spatial() which
    returns torch.tensor() without device param, always producing CPU tensors.

    Returns:
        VectorStoreResultsFactory with create() method
    """

    class VectorStoreResultsFactory:
        """Creates simulated VectorStore results on CPU."""

        def create(
            self,
            k: int = M1114_K_NEIGHBORS,
            d_model: int = M1114_D_MODEL,
            seed: int = 42,
        ) -> tuple[torch.Tensor, torch.Tensor, list[str]]:
            """Create simulated VectorStore search results.

            Args:
                k: Number of results (neighbors)
                d_model: Embedding dimension
                seed: Random seed for reproducibility

            Returns:
                (embeddings [k, d_model], positions [k, 3], ids [k]) all on CPU
            """
            torch.manual_seed(seed)
            embeddings = torch.randn(k, d_model)
            positions = torch.randn(k, 3) * 500.0
            ids = [f"token_{i}" for i in range(k)]
            return embeddings, positions, ids

    return VectorStoreResultsFactory()


# ---------------------------------------------------------------------------
# Phase B Fixtures: Full pipeline vs O(n²) baseline
# ---------------------------------------------------------------------------


@pytest.fixture
def m1114_nav_attention_gpu(gpu_device: torch.device) -> NavigationAttention:
    """NavigationAttention on GPU for full pipeline tests.

    Combines stages 3 (SpatialAttention), 6 (LOD), and 7 (Navigation)
    into one module for benchmarking the complete INFINATE pipeline.

    Args:
        gpu_device: CUDA device fixture from conftest_m1113

    Returns:
        NavigationAttention moved to GPU
    """
    return NavigationAttention(
        d_model=M1114_D_MODEL,
        spatial_radius=M1114_SPATIAL_RADIUS,
        k_neighbors=M1114_K_NEIGHBORS,
        enable_navigation=True,
        enable_lod=True,
        navigation_max_steps=10,
    ).to(gpu_device)


@pytest.fixture
def m1114_nav_attention_cpu() -> NavigationAttention:
    """NavigationAttention on CPU for comparison.

    Returns:
        NavigationAttention on CPU
    """
    return NavigationAttention(
        d_model=M1114_D_MODEL,
        spatial_radius=M1114_SPATIAL_RADIUS,
        k_neighbors=M1114_K_NEIGHBORS,
        enable_navigation=True,
        enable_lod=True,
        navigation_max_steps=10,
    )
