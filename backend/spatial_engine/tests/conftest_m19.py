"""
conftest_m19.py - M1.9 pytest fixtures for test stabilization.

Provides:
- GPU compatibility checking
- Improved stress test fixtures with warmup
- Trimmed statistics utilities for handling GC/system variance

Author: ch1pu
Milestone: 1.9 - Test Stabilization & Full Coverage Documentation
"""

import statistics
import time
from collections.abc import Callable

import pytest
import torch

from spatial_engine.core.spatial_transformer import SpatialTransformer
from spatial_engine.integration.transformer_bridge import TransformerBridge
from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter

# M1.9 benchmark configuration
M19_D_MODEL = 256
M19_N_LAYERS = 2
M19_N_HEADS = 8


@pytest.fixture(scope="module")
def m19_transformer() -> SpatialTransformer:
    """Transformer for M1.9 stability tests.

    Uses smaller dimensions for faster testing while still
    validating the core O(k) complexity behavior.

    Returns:
        SpatialTransformer configured for M1.9 stability tests
    """
    return SpatialTransformer(
        n_layers=M19_N_LAYERS,
        d_model=M19_D_MODEL,
        n_heads=M19_N_HEADS,
        d_ff=1024,
        spatial_radius=50.0,
        dropout=0.0,
    )


@pytest.fixture(scope="function")
def m19_bridge_factory(
    m19_transformer: SpatialTransformer,
) -> Callable[..., TransformerBridge]:
    """Factory for creating bridges with automatic warmup.

    This factory creates TransformerBridge instances with pre-populated
    vector stores and automatic warmup queries to eliminate cold-start
    variance in benchmarks.

    Args:
        m19_transformer: The shared transformer instance

    Yields:
        Factory function that creates warmed-up bridges

    Example:
        def test_something(m19_bridge_factory):
            bridge = m19_bridge_factory(1000, warmup_queries=5)
            # Bridge is now ready with 1000 tokens and warmed up
    """
    created_adapters: list[QdrantAdapter] = []

    def create_bridge(
        context_size: int,
        k_neighbors: int = 50,
        warmup_queries: int = 5,
    ) -> TransformerBridge:
        """Create a bridge with specified context size and warmup.

        Args:
            context_size: Number of tokens to store in vector store
            k_neighbors: Number of neighbors for spatial attention
            warmup_queries: Number of warmup queries to run

        Returns:
            TransformerBridge ready for benchmarking
        """
        adapter = QdrantAdapter(
            collection_name=f"m19_{context_size}_{int(time.time() * 1000)}",
            d_model=M19_D_MODEL,
            use_memory=True,
        )
        created_adapters.append(adapter)

        # Store tokens with reproducible positions
        torch.manual_seed(42)
        embeddings = torch.randn(context_size, M19_D_MODEL)
        positions = torch.randn(context_size, 3) * 500.0
        adapter.store(embeddings, positions)

        bridge = TransformerBridge(
            transformer=m19_transformer,
            vector_store=adapter,
            k_neighbors=k_neighbors,
        )

        # Auto-warmup to eliminate cold-start variance
        if warmup_queries > 0:
            x = torch.randn(1, 64, M19_D_MODEL)
            pos = torch.randn(1, 64, 3) * 100.0
            for _ in range(warmup_queries):
                _ = bridge(x, pos)

        return bridge

    yield create_bridge

    # Cleanup all created adapters
    import contextlib

    for adapter in created_adapters:
        with contextlib.suppress(Exception):
            adapter.close()


def trimmed_statistics(data: list[float], trim_pct: float = 0.1) -> dict:
    """Calculate trimmed statistics (excluding outliers).

    This is essential for stable benchmarks in the presence of
    GC pauses, system interrupts, and other sources of variance.

    Args:
        data: List of measurements (e.g., latencies in ms)
        trim_pct: Percentage to trim from each end (default 10%)

    Returns:
        Dict with:
        - mean: Trimmed mean
        - std: Trimmed standard deviation
        - cv: Coefficient of variation (std/mean * 100)
        - max: Maximum of trimmed data
        - min: Minimum of trimmed data
        - raw_max: Maximum of original data (for worst-case analysis)
        - raw_mean: Mean of original data (for comparison)

    Example:
        >>> data = [10, 11, 12, 100, 11, 10, 9, 12]  # 100 is outlier
        >>> stats = trimmed_statistics(data, trim_pct=0.1)
        >>> stats['mean']  # ~10.8, excluding the 100
    """
    if not data:
        return {"mean": 0, "std": 0, "cv": 0, "max": 0, "min": 0, "raw_max": 0, "raw_mean": 0}

    trim_count = max(1, int(len(data) * trim_pct))
    sorted_data = sorted(data)

    # Ensure we have enough data points after trimming
    if len(sorted_data) > 2 * trim_count:
        trimmed = sorted_data[trim_count:-trim_count]
    else:
        trimmed = sorted_data

    mean = statistics.mean(trimmed)
    std = statistics.stdev(trimmed) if len(trimmed) > 1 else 0
    cv = (std / mean * 100) if mean > 0 else 0

    return {
        "mean": mean,
        "std": std,
        "cv": cv,
        "max": max(trimmed),
        "min": min(trimmed),
        "raw_max": max(data),
        "raw_mean": statistics.mean(data),
    }


# ---------------------------------------------------------------------------
# M1.9 Test Marker Configuration
# ---------------------------------------------------------------------------

# Note: The m19 marker is registered in conftest.py's pytest_configure
# This file provides the fixtures; markers are handled centrally
