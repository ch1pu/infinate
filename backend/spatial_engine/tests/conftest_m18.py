"""
conftest_m18.py - Extended pytest fixtures for M1.8 benchmarking.

Provides fixtures for:
- Large context testing (100K+ tokens)
- MIT RLM reference data
- Extended scaling test sizes
- Benchmark runner utilities

Author: ch1pu
Milestone: 1.8 - Extended Benchmarking & MIT RLM Comparison
"""

import time
from collections.abc import Callable, Generator

import pytest
import torch

from spatial_engine.benchmarks.mit_comparison import (
    MIT_REFERENCES,
    MITBenchmarkRunner,
)
from spatial_engine.core.spatial_transformer import SpatialTransformer
from spatial_engine.integration.transformer_bridge import TransformerBridge
from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Benchmark model configuration (smaller for faster tests)
BENCH_D_MODEL = 256
BENCH_N_LAYERS = 2
BENCH_N_HEADS = 8
BENCH_D_FF = 1024
BENCH_SPATIAL_RADIUS = 50.0


# ---------------------------------------------------------------------------
# Fixtures - Benchmark Utilities
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def benchmark_runner() -> MITBenchmarkRunner:
    """Create benchmark runner for M1.8 tests.

    Returns:
        MITBenchmarkRunner with default settings
    """
    return MITBenchmarkRunner(
        warmup_runs=5,
        measurement_runs=20,
        gc_between_runs=True,
    )


@pytest.fixture(scope="module")
def fast_benchmark_runner() -> MITBenchmarkRunner:
    """Create fast benchmark runner for quick tests.

    Returns:
        MITBenchmarkRunner with fewer iterations
    """
    return MITBenchmarkRunner(
        warmup_runs=2,
        measurement_runs=5,
        gc_between_runs=True,
    )


# ---------------------------------------------------------------------------
# Fixtures - Transformers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def bench_transformer() -> SpatialTransformer:
    """Create transformer for benchmarking.

    Returns:
        SpatialTransformer optimized for benchmark tests
    """
    return SpatialTransformer(
        n_layers=BENCH_N_LAYERS,
        d_model=BENCH_D_MODEL,
        n_heads=BENCH_N_HEADS,
        d_ff=BENCH_D_FF,
        spatial_radius=BENCH_SPATIAL_RADIUS,
        dropout=0.0,  # No dropout for deterministic tests
    )


# ---------------------------------------------------------------------------
# Fixtures - MIT Reference Data
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mit_reference_data() -> dict:
    """Provide MIT RLM reference data from paper.

    Returns:
        Dict with MIT reference data for each dataset
    """
    return MIT_REFERENCES


@pytest.fixture(scope="module")
def mit_reference_contexts() -> dict[str, int]:
    """MIT RLM reference context sizes.

    Returns:
        Dict mapping dataset name to token count
    """
    return {
        "codeqa": 100_000,  # ~100K tokens
        "oolong": 500_000,  # ~500K tokens
        "browsecomp": 10_000_000,  # ~10M tokens (we'll scale down for tests)
    }


# ---------------------------------------------------------------------------
# Fixtures - Scaling Test Sizes
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def scaling_test_sizes() -> list[int]:
    """Standard scaling test sizes from 1K to 128K.

    Returns:
        List of context sizes for scaling tests
    """
    return [1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000]


@pytest.fixture(scope="module")
def small_scaling_sizes() -> list[int]:
    """Smaller scaling test sizes for faster tests.

    Returns:
        List of context sizes for quick scaling tests
    """
    return [500, 1000, 2000, 4000]


@pytest.fixture(scope="module")
def k_values() -> list[int]:
    """Values of k (neighbors) to test.

    Returns:
        List of k values for O(k) verification
    """
    return [25, 50, 100, 200]


@pytest.fixture(scope="module")
def batch_sizes() -> list[int]:
    """Batch sizes for throughput testing.

    Returns:
        List of batch sizes
    """
    return [1, 4, 16, 64]


# ---------------------------------------------------------------------------
# Fixtures - Large Context Bridges
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def bridge_factory(
    bench_transformer: SpatialTransformer,
) -> Callable[[int], TransformerBridge]:
    """Factory for creating bridges with specified context size.

    Args:
        bench_transformer: Transformer to use in bridge

    Returns:
        Callable that creates bridge with given context size
    """
    created_adapters: list[QdrantAdapter] = []

    def create_bridge(context_size: int, k_neighbors: int = 50) -> TransformerBridge:
        """Create bridge with specified context size.

        Args:
            context_size: Number of tokens to store in vector store
            k_neighbors: Number of neighbors for attention

        Returns:
            TransformerBridge with populated vector store
        """
        adapter = QdrantAdapter(
            collection_name=f"bench_{context_size}_{int(time.time() * 1000)}",
            d_model=BENCH_D_MODEL,
            use_memory=True,
        )
        created_adapters.append(adapter)

        # Generate and store embeddings
        torch.manual_seed(42)
        embeddings = torch.randn(context_size, BENCH_D_MODEL)
        positions = torch.randn(context_size, 3) * 500.0
        adapter.store(embeddings, positions)

        return TransformerBridge(
            transformer=bench_transformer,
            vector_store=adapter,
            k_neighbors=k_neighbors,
        )

    yield create_bridge

    # Cleanup all created adapters
    import contextlib

    for adapter in created_adapters:
        with contextlib.suppress(Exception):
            adapter.close()


@pytest.fixture(scope="function")
def small_context_bridge(
    bench_transformer: SpatialTransformer,
) -> Generator[TransformerBridge, None, None]:
    """Bridge with 1K tokens for quick tests.

    Yields:
        TransformerBridge with 1K tokens in vector store
    """
    adapter = QdrantAdapter(
        collection_name="small_context_1k",
        d_model=BENCH_D_MODEL,
        use_memory=True,
    )

    torch.manual_seed(42)
    embeddings = torch.randn(1000, BENCH_D_MODEL)
    positions = torch.randn(1000, 3) * 500.0
    adapter.store(embeddings, positions)

    bridge = TransformerBridge(
        transformer=bench_transformer,
        vector_store=adapter,
        k_neighbors=50,
    )

    yield bridge
    adapter.close()


@pytest.fixture(scope="function")
def medium_context_bridge(
    bench_transformer: SpatialTransformer,
) -> Generator[TransformerBridge, None, None]:
    """Bridge with 10K tokens for medium tests.

    Yields:
        TransformerBridge with 10K tokens in vector store
    """
    adapter = QdrantAdapter(
        collection_name="medium_context_10k",
        d_model=BENCH_D_MODEL,
        use_memory=True,
    )

    torch.manual_seed(42)
    embeddings = torch.randn(10000, BENCH_D_MODEL)
    positions = torch.randn(10000, 3) * 500.0
    adapter.store(embeddings, positions)

    bridge = TransformerBridge(
        transformer=bench_transformer,
        vector_store=adapter,
        k_neighbors=50,
    )

    yield bridge
    adapter.close()


@pytest.fixture(scope="function")
def large_context_bridge(
    bench_transformer: SpatialTransformer,
) -> Generator[TransformerBridge, None, None]:
    """Bridge with 100K tokens for MIT CodeQA scale testing.

    Yields:
        TransformerBridge with 100K tokens in vector store
    """
    adapter = QdrantAdapter(
        collection_name="large_context_100k",
        d_model=BENCH_D_MODEL,
        use_memory=True,
    )

    # Generate 100K tokens in batches to avoid memory issues
    torch.manual_seed(42)
    batch_size = 10000
    for i in range(10):  # 10 batches of 10K = 100K
        embeddings = torch.randn(batch_size, BENCH_D_MODEL)
        positions = torch.randn(batch_size, 3) * 500.0 + (i * 100)  # Offset positions
        adapter.store(embeddings, positions)

    bridge = TransformerBridge(
        transformer=bench_transformer,
        vector_store=adapter,
        k_neighbors=50,
    )

    yield bridge
    adapter.close()


# ---------------------------------------------------------------------------
# Fixtures - Test Input Data
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def bench_input() -> tuple[torch.Tensor, torch.Tensor]:
    """Standard benchmark input (1 batch, 128 tokens).

    Returns:
        Tuple of (x, positions) tensors
    """
    torch.manual_seed(42)
    x = torch.randn(1, 128, BENCH_D_MODEL)
    positions = torch.randn(1, 128, 3) * 100.0
    return x, positions


@pytest.fixture(scope="function")
def small_bench_input() -> tuple[torch.Tensor, torch.Tensor]:
    """Small benchmark input (1 batch, 64 tokens).

    Returns:
        Tuple of (x, positions) tensors
    """
    torch.manual_seed(42)
    x = torch.randn(1, 64, BENCH_D_MODEL)
    positions = torch.randn(1, 64, 3) * 100.0
    return x, positions


@pytest.fixture(scope="function")
def large_bench_input() -> tuple[torch.Tensor, torch.Tensor]:
    """Large benchmark input (1 batch, 256 tokens).

    Returns:
        Tuple of (x, positions) tensors
    """
    torch.manual_seed(42)
    x = torch.randn(1, 256, BENCH_D_MODEL)
    positions = torch.randn(1, 256, 3) * 100.0
    return x, positions


# ---------------------------------------------------------------------------
# Pytest Markers
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Register M1.8 specific pytest markers."""
    config.addinivalue_line(
        "markers",
        "mit_comparison: mark test as MIT RLM comparison benchmark",
    )
    config.addinivalue_line(
        "markers",
        "extended_scaling: mark test as extended scaling benchmark",
    )
    config.addinivalue_line(
        "markers",
        "stress: mark test as stress/stability test",
    )
