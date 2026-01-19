"""
conftest.py - Shared pytest fixtures for integration tests.

Provides fixtures for:
- Docker PostgreSQL with pgvector
- In-memory Qdrant adapter
- SpatialTransformer instances
- Sample embeddings and positions

Author: ch1pu
Milestone: 1.7 - Integration Testing
"""

import os
import time
from typing import Generator

import pytest
import torch

from spatial_engine.core.spatial_transformer import SpatialTransformer
from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter
from spatial_engine.vector_store.base import VectorStoreBase

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
