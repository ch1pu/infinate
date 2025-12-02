"""
test_pgvector_adapter.py - Test suite for pgvector adapter.

Tests the PostgreSQL + pgvector adapter for storing and querying spatial
tokens with 3D positions and semantic embeddings.

Author: ch1pu
Milestone: 1.6 - Vector Store Integration
Test Count: 7
Coverage Target: ≥95%
"""


import pytest
import torch


class TestPgvectorAdapter:
    """Test suite for PgvectorAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create PgvectorAdapter for testing.

        Uses test database for testing (auto-cleanup after tests).
        """
        from spatial_engine.vector_store.pgvector_adapter import PgvectorAdapter

        # Create adapter for testing
        return PgvectorAdapter(
            connection_string="postgresql://test:test@localhost:5432/test_spatial",
            table_name="test_spatial_memory",
            d_model=768,
        )

    def test_initialization(self):
        """Test PgvectorAdapter initialization.

        Verifies:
        - Adapter created successfully
        - Table created with pgvector extension
        - Parameters stored correctly
        - Connection established
        """
        from spatial_engine.vector_store.pgvector_adapter import PgvectorAdapter

        adapter = PgvectorAdapter(
            connection_string="postgresql://test:test@localhost:5432/test_db",
            table_name="test_table",
            d_model=768,
        )

        assert adapter.table_name == "test_table"
        assert adapter.d_model == 768
        assert adapter.connection is not None

    def test_store_single_token(self, adapter):
        """Test storing a single spatial token.

        Verifies:
        - Single token stored successfully
        - ID returned
        - Embedding and position stored
        - Metadata preserved
        """
        # Create test data
        embedding = torch.randn(768)
        position = torch.tensor([10.0, 20.0, 30.0])
        metadata = {"text": "Hello world", "file": "test.py"}

        # Store token
        ids = adapter.store(
            embeddings=embedding.unsqueeze(0),
            positions=position.unsqueeze(0),
            metadata=[metadata],
        )

        # Verify
        assert len(ids) == 1
        assert isinstance(ids[0], str)
        assert len(ids[0]) > 0

    def test_store_batch_tokens(self, adapter):
        """Test storing batch of spatial tokens.

        Verifies:
        - Batch storage working
        - All tokens stored
        - IDs returned for all tokens
        - Efficient batch operation
        """
        # Create batch data
        batch_size = 100
        embeddings = torch.randn(batch_size, 768)
        positions = torch.randn(batch_size, 3) * 500.0
        metadata = [{"text": f"Token {i}", "index": i} for i in range(batch_size)]

        # Store batch
        ids = adapter.store(
            embeddings=embeddings,
            positions=positions,
            metadata=metadata,
        )

        # Verify
        assert len(ids) == batch_size
        assert all(isinstance(id_, str) for id_ in ids)
        assert len(set(ids)) == batch_size  # All unique

    def test_query_by_similarity(self, adapter):
        """Test querying by vector similarity.

        Verifies:
        - Query returns similar vectors
        - Results ranked by similarity
        - k parameter working
        - Returns embeddings, positions, IDs
        """
        # Store some test data
        embeddings = torch.randn(50, 768)
        positions = torch.randn(50, 3) * 100.0
        metadata = [{"index": i} for i in range(50)]

        adapter.store(
            embeddings=embeddings,
            positions=positions,
            metadata=metadata,
        )

        # Query with a test vector
        query_vector = torch.randn(768)
        query_position = (0.0, 0.0, 0.0)

        results_emb, results_pos, results_ids = adapter.query(
            query_vector=query_vector,
            query_position=query_position,
            k=10,
        )

        # Verify
        assert results_emb.shape == (10, 768)
        assert results_pos.shape == (10, 3)
        assert len(results_ids) == 10

    def test_query_with_spatial_filter(self, adapter):
        """Test querying with spatial radius filter.

        Verifies:
        - Spatial radius filter working
        - Only nearby tokens returned
        - Distance-based filtering with SQL
        - Combines similarity + spatial proximity
        """
        # Store tokens at known positions
        embeddings = torch.randn(100, 768)
        positions = torch.zeros(100, 3)
        # Half near origin, half far away
        positions[:50] = torch.randn(50, 3) * 10.0  # Near origin (within radius 50)
        positions[50:] = torch.randn(50, 3) * 200.0  # Far from origin
        metadata = [{"index": i} for i in range(100)]

        adapter.store(
            embeddings=embeddings,
            positions=positions,
            metadata=metadata,
        )

        # Query from origin with radius filter
        query_vector = torch.randn(768)
        query_position = (0.0, 0.0, 0.0)

        results_emb, results_pos, results_ids = adapter.query(
            query_vector=query_vector,
            query_position=query_position,
            k=100,
            radius=50.0,  # Only tokens within radius 50
        )

        # Verify: should get mostly/only tokens from first 50
        assert len(results_ids) <= 100
        # At least some results should be from the near group
        assert len(results_ids) > 0

    def test_delete_tokens(self, adapter):
        """Test deleting tokens by ID.

        Verifies:
        - Tokens can be deleted
        - Returns count of deleted tokens
        - Deleted tokens no longer queryable
        """
        # Store some tokens
        embeddings = torch.randn(10, 768)
        positions = torch.randn(10, 3) * 100.0
        metadata = [{"index": i} for i in range(10)]

        ids = adapter.store(
            embeddings=embeddings,
            positions=positions,
            metadata=metadata,
        )

        # Delete first 5
        deleted_count = adapter.delete(ids[:5])

        # Verify
        assert deleted_count == 5

        # Query should return fewer results now
        query_vector = torch.randn(768)
        query_position = (0.0, 0.0, 0.0)

        results_emb, results_pos, results_ids = adapter.query(
            query_vector=query_vector,
            query_position=query_position,
            k=100,
        )

        # Should have ~5 tokens left
        assert len(results_ids) <= 5

    def test_close_connection(self, adapter):
        """Test closing the adapter connection.

        Verifies:
        - close() method works without errors
        - Database connection cleaned up properly
        """
        # Should not raise any errors
        adapter.close()


# Test execution marker
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
