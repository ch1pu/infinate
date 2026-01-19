#!/usr/bin/env python3
"""
test_postgres_connection.py - Test PostgreSQL connection for integration tests.

Usage:
    poetry run python scripts/test_postgres_connection.py
"""

import sys


def test_connection():
    """Test PostgreSQL connection."""
    print("Testing PostgreSQL connection...")
    print("=" * 50)

    # Test 1: Import psycopg2
    try:
        import psycopg2
        print("✓ psycopg2 imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import psycopg2: {e}")
        return False

    # Test 2: Import pgvector
    try:
        from pgvector.psycopg2 import register_vector
        print("✓ pgvector imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pgvector: {e}")
        return False

    # Test 3: Connect to PostgreSQL
    connection_string = "postgresql://test:test@localhost:5433/test_spatial"
    print(f"\nConnecting to: {connection_string}")

    try:
        conn = psycopg2.connect(connection_string)
        print("✓ Connected to PostgreSQL")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return False

    # Test 4: Check PostgreSQL version
    try:
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"✓ PostgreSQL version: {version[:50]}...")
    except Exception as e:
        print(f"✗ Failed to query version: {e}")
        conn.close()
        return False

    # Test 5: Check pgvector extension
    try:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
        print("✓ pgvector extension enabled")
    except Exception as e:
        print(f"✗ Failed to enable pgvector: {e}")
        conn.close()
        return False

    # Test 6: Register pgvector type
    try:
        register_vector(conn)
        print("✓ pgvector type registered")
    except Exception as e:
        print(f"✗ Failed to register pgvector: {e}")
        conn.close()
        return False

    # Test 7: Create and query a test table
    try:
        cur.execute("DROP TABLE IF EXISTS test_vectors")
        cur.execute("CREATE TABLE test_vectors (id serial PRIMARY KEY, embedding vector(3))")
        cur.execute("INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]')")
        cur.execute("SELECT * FROM test_vectors")
        result = cur.fetchone()
        print(f"✓ Vector table test passed: {result}")
        cur.execute("DROP TABLE test_vectors")
        conn.commit()
    except Exception as e:
        print(f"✗ Failed vector table test: {e}")
        conn.close()
        return False

    conn.close()
    print("\n" + "=" * 50)
    print("All tests passed! PostgreSQL is ready for integration tests.")
    return True


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
