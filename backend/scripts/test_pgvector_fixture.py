#!/usr/bin/env python3
"""
test_pgvector_fixture.py - Debug the pgvector fixture issue.

Usage:
    poetry run python scripts/test_pgvector_fixture.py
"""

import time
import torch


def test_fixture():
    """Reproduce what the conftest fixture does."""
    print("Testing pgvector fixture logic...")
    print("=" * 50)

    # Step 1: Check imports (same as conftest)
    try:
        import psycopg2
        from spatial_engine.vector_store.pgvector_adapter import PgvectorAdapter
        print("✓ Imports successful")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

    # Step 2: Build connection string (same as conftest)
    import os
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5433")
    POSTGRES_USER = os.environ.get("POSTGRES_USER", "test")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "test")
    POSTGRES_DB = os.environ.get("POSTGRES_DB", "test_spatial")

    connection_string = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    print(f"Connection string: {connection_string}")

    # Step 3: Create adapter (same as conftest)
    D_MODEL = 768
    table_name = f"test_spatial_{int(time.time() * 1000)}"
    print(f"Table name: {table_name}")
    print(f"D_MODEL: {D_MODEL}")

    try:
        print("\nCreating PgvectorAdapter...")
        adapter = PgvectorAdapter(
            connection_string=connection_string,
            table_name=table_name,
            d_model=D_MODEL,
        )
        print("✓ PgvectorAdapter created successfully")
    except Exception as e:
        print(f"✗ PgvectorAdapter creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: Store some data (same as pgvector_with_data fixture)
    try:
        print("\nStoring sample data...")
        torch.manual_seed(42)
        embeddings = torch.randn(100, D_MODEL)
        positions = torch.randn(100, 3) * 100.0
        ids = adapter.store(embeddings, positions)
        print(f"✓ Stored {len(ids)} tokens")
    except Exception as e:
        print(f"✗ Store failed: {e}")
        import traceback
        traceback.print_exc()
        adapter.close()
        return False

    # Step 5: Query the data
    try:
        print("\nQuerying data...")
        query_vec = torch.randn(D_MODEL)
        query_pos = (0.0, 0.0, 0.0)
        emb, pos, result_ids = adapter.query(query_vec, query_pos, k=10)
        print(f"✓ Query returned {len(result_ids)} results")
        print(f"  Embeddings shape: {emb.shape}")
        print(f"  Positions shape: {pos.shape}")
    except Exception as e:
        print(f"✗ Query failed: {e}")
        import traceback
        traceback.print_exc()
        adapter.close()
        return False

    # Step 6: Cleanup
    try:
        print("\nCleaning up...")
        with adapter.connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        adapter.connection.commit()
        adapter.close()
        print("✓ Cleanup successful")
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("All fixture tests passed!")
    return True


if __name__ == "__main__":
    import sys
    success = test_fixture()
    sys.exit(0 if success else 1)
