"""
conftest.py - Shared pytest fixtures for integration tests.

Provides fixtures for:
- Docker PostgreSQL with pgvector
- In-memory Qdrant adapter
- SpatialTransformer instances
- Sample embeddings and positions
- GPU compatibility checking (M1.9)

Author: ch1pu
Milestone: 1.7 - Integration Testing
Updated: M1.9 - Test Stabilization (GPU skip fixture)
"""

import os
import time
from collections.abc import Generator

import pytest
import torch


# ---------------------------------------------------------------------------
# GPU Compatibility Check (M1.9)
# ---------------------------------------------------------------------------


def check_cuda_compatible() -> tuple[bool, str]:
    """Check if CUDA is available and compatible with PyTorch.

    RTX 50xx series (SM_120/Blackwell) is not yet supported by PyTorch 2.x.
    This function detects incompatible GPUs to allow graceful test skipping.

    Returns:
        Tuple of (is_compatible, reason_if_not)
    """
    if not torch.cuda.is_available():
        return False, "CUDA not available"

    try:
        cap = torch.cuda.get_device_capability()
        # RTX 50xx series (SM_120) not yet supported by PyTorch 2.x
        # SM_90 (Hopper) is the latest fully supported architecture
        if cap[0] >= 12:
            return False, f"GPU SM_{cap[0]}{cap[1]} not supported by PyTorch"
        return True, ""
    except Exception as e:
        return False, f"GPU capability check failed: {e}"


@pytest.fixture
def skip_incompatible_gpu():
    """Skip test if GPU is not compatible with PyTorch.

    Use this fixture for tests that require CUDA but may fail on
    unsupported GPU architectures like RTX 50xx (SM_120).

    Example:
        def test_gpu_feature(skip_incompatible_gpu):
            # Test will be skipped if GPU is incompatible
            model = MyModel().cuda()
            ...
    """
    is_compatible, reason = check_cuda_compatible()
    if torch.cuda.is_available() and not is_compatible:
        pytest.skip(reason)

from spatial_engine.core.spatial_transformer import SpatialTransformer
from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter

# Check if pgvector dependencies are available
try:
    import psycopg2

    from spatial_engine.vector_store.pgvector_adapter import PgvectorAdapter

    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    PgvectorAdapter = None  # type: ignore


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default dimensions
D_MODEL = 768
N_LAYERS = 3  # Smaller for tests
N_HEADS = 12
D_FF = 3072
SPATIAL_RADIUS = 50.0

# PostgreSQL test connection (from docker-compose.test.yml)
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5433")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "test")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "test")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "test_spatial")


def get_postgres_connection_string() -> str:
    """Get PostgreSQL connection string for tests."""
    return (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )


# ---------------------------------------------------------------------------
# Fixtures - Transformers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def spatial_transformer() -> SpatialTransformer:
    """Create a SpatialTransformer instance for testing.

    Returns:
        SpatialTransformer configured for testing
    """
    return SpatialTransformer(
        n_layers=N_LAYERS,
        d_model=D_MODEL,
        n_heads=N_HEADS,
        d_ff=D_FF,
        spatial_radius=SPATIAL_RADIUS,
        dropout=0.0,  # No dropout for deterministic tests
    )


@pytest.fixture(scope="function")
def small_transformer() -> SpatialTransformer:
    """Create a smaller SpatialTransformer for faster tests.

    Returns:
        SpatialTransformer with 2 layers
    """
    return SpatialTransformer(
        n_layers=2,
        d_model=256,
        n_heads=8,
        d_ff=1024,
        spatial_radius=SPATIAL_RADIUS,
        dropout=0.0,
    )


# ---------------------------------------------------------------------------
# Fixtures - Vector Stores
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def qdrant_adapter() -> Generator[QdrantAdapter, None, None]:
    """Create an in-memory Qdrant adapter for testing.

    Yields:
        QdrantAdapter in memory mode
    """
    adapter = QdrantAdapter(
        collection_name="test_collection",
        d_model=D_MODEL,
        use_memory=True,
    )
    yield adapter
    adapter.close()


@pytest.fixture(scope="function")
def qdrant_small() -> Generator[QdrantAdapter, None, None]:
    """Create a small Qdrant adapter (256 dims) for faster tests.

    Yields:
        QdrantAdapter with 256 dimensions
    """
    adapter = QdrantAdapter(
        collection_name="test_small",
        d_model=256,
        use_memory=True,
    )
    yield adapter
    adapter.close()


@pytest.fixture(scope="function")
def pgvector_adapter() -> Generator["PgvectorAdapter", None, None]:
    """Create a pgvector adapter connected to Docker PostgreSQL.

    Requires docker-compose.test.yml to be running.

    Yields:
        PgvectorAdapter connected to test database
    """
    if not PGVECTOR_AVAILABLE:
        pytest.skip("psycopg2 or pgvector not installed")

    connection_string = get_postgres_connection_string()

    # Try to connect with retries
    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            adapter = PgvectorAdapter(
                connection_string=connection_string,
                table_name=f"test_spatial_{int(time.time() * 1000)}",  # Unique table
                d_model=D_MODEL,
            )
            break
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                pytest.skip(
                    f"Could not connect to PostgreSQL: {e}. "
                    "Ensure docker-compose.test.yml is running."
                )

    yield adapter

    # Cleanup: drop table and close
    try:
        with adapter.connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {adapter.table_name};")
        adapter.connection.commit()
    except Exception:
        pass
    adapter.close()


# ---------------------------------------------------------------------------
# Fixtures - Sample Data
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def sample_embeddings() -> torch.Tensor:
    """Generate sample embeddings for testing.

    Returns:
        Tensor of shape (100, D_MODEL) with random embeddings
    """
    torch.manual_seed(42)  # For reproducibility
    return torch.randn(100, D_MODEL)


@pytest.fixture(scope="function")
def sample_positions() -> torch.Tensor:
    """Generate sample 3D positions for testing.

    Returns:
        Tensor of shape (100, 3) with random positions
    """
    torch.manual_seed(42)
    return torch.randn(100, 3) * 100.0  # Scale to reasonable range


@pytest.fixture(scope="function")
def sample_batch() -> tuple[torch.Tensor, torch.Tensor]:
    """Generate a sample input batch for transformer.

    Returns:
        Tuple of (x, positions) tensors:
        - x: (1, 128, D_MODEL) input embeddings
        - positions: (1, 128, 3) 3D positions
    """
    torch.manual_seed(42)
    x = torch.randn(1, 128, D_MODEL)
    positions = torch.randn(1, 128, 3) * 100.0
    return x, positions


@pytest.fixture(scope="function")
def small_batch() -> tuple[torch.Tensor, torch.Tensor]:
    """Generate a smaller input batch for faster tests.

    Returns:
        Tuple of (x, positions) tensors:
        - x: (1, 64, 256) input embeddings
        - positions: (1, 64, 3) 3D positions
    """
    torch.manual_seed(42)
    x = torch.randn(1, 64, 256)
    positions = torch.randn(1, 64, 3) * 100.0
    return x, positions


# ---------------------------------------------------------------------------
# Fixtures - Pre-populated Vector Stores
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def qdrant_with_data(
    qdrant_adapter: QdrantAdapter,
    sample_embeddings: torch.Tensor,
    sample_positions: torch.Tensor,
) -> QdrantAdapter:
    """Create Qdrant adapter with pre-populated test data.

    Args:
        qdrant_adapter: Empty Qdrant adapter
        sample_embeddings: Sample embeddings to store
        sample_positions: Sample positions to store

    Returns:
        QdrantAdapter with 100 tokens stored
    """
    qdrant_adapter.store(sample_embeddings, sample_positions)
    return qdrant_adapter


@pytest.fixture(scope="function")
def pgvector_with_data(
    pgvector_adapter: "PgvectorAdapter",
    sample_embeddings: torch.Tensor,
    sample_positions: torch.Tensor,
) -> "PgvectorAdapter":
    """Create pgvector adapter with pre-populated test data.

    Args:
        pgvector_adapter: Empty pgvector adapter
        sample_embeddings: Sample embeddings to store
        sample_positions: Sample positions to store

    Returns:
        PgvectorAdapter with 100 tokens stored
    """
    pgvector_adapter.store(sample_embeddings, sample_positions)
    return pgvector_adapter


# ---------------------------------------------------------------------------
# Pytest Markers
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "benchmark: mark test as a performance benchmark",
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running",
    )
    config.addinivalue_line(
        "markers",
        "requires_docker: mark test as requiring Docker PostgreSQL",
    )
    # M1.8 markers
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
    # M1.9 markers
    config.addinivalue_line(
        "markers",
        "m19: mark test as M1.9 stability test",
    )


# ---------------------------------------------------------------------------
# Pytest Hooks
# ---------------------------------------------------------------------------


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add requires_docker marker to pgvector tests
        if "pgvector" in item.name.lower():
            item.add_marker(pytest.mark.requires_docker)


# ---------------------------------------------------------------------------
# M1.9 Fixtures - Stability Test Support
# ---------------------------------------------------------------------------

# Import integration components (may not be available during early development)
try:
    from spatial_engine.integration.transformer_bridge import TransformerBridge

    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False
    TransformerBridge = None  # type: ignore

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
):
    """Factory for creating bridges with automatic warmup.

    This factory creates TransformerBridge instances with pre-populated
    vector stores and automatic warmup queries to eliminate cold-start
    variance in benchmarks.

    Args:
        m19_transformer: The shared transformer instance

    Yields:
        Factory function that creates warmed-up bridges
    """
    if not BRIDGE_AVAILABLE:
        pytest.skip("TransformerBridge not available")

    created_adapters: list[QdrantAdapter] = []

    def create_bridge(
        context_size: int,
        k_neighbors: int = 50,
        warmup_queries: int = 5,
    ):
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
