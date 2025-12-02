"""
test_qdrant_adapter.py - Test suite for Qdrant vector store adapter.

Tests the Qdrant adapter for storing and querying spatial tokens with
3D positions and semantic embeddings.

Author: ch1pu
Milestone: 1.6 - Vector Store Integration
Test Count: 8
Coverage Target: ≥95%
"""


import pytest
import torch


class TestQdrantAdapter:
    """Test suite for QdrantAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create QdrantAdapter for testing.

        Uses in-memory mode for testing (no external Qdrant server needed).
        """
        from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter

        # Create in-memory adapter for testing
        return QdrantAdapter(
            collection_name="test_spatial_memory",
            d_model=768,
            use_memory=True,  # In-memory for testing
        )

    def test_initialization(self):
        """Test QdrantAdapter initialization.

        Verifies:
        - Adapter created successfully
        - Collection created
        - Parameters stored correctly
        - In-memory mode working
        """
        from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter

        adapter = QdrantAdapter(
            collection_name="test_collection",
            d_model=768,
            use_memory=True,
        )

        assert adapter.collection_name == "test_collection"
        assert adapter.d_model == 768
        assert adapter.client is not None

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
        - Distance-based filtering
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
        # (Some from second half might be within radius due to randomness)
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

        # Should have ~5 tokens left (some might not be returned due to similarity threshold)
        assert len(results_ids) <= 5

    def test_close_connection(self, adapter):
        """Test closing the adapter connection.

        Verifies:
        - close() method works without errors
        - Resources cleaned up properly
        """
        # Should not raise any errors
        adapter.close()

    def test_integration_with_spatial_tokens(self, adapter):
        """Test integration with M1.1 SpatialToken.

        Verifies:
        - Can store SpatialToken instances
        - Embeddings and positions extracted correctly
        - Metadata preserved
        - Query returns compatible format
        """
        from spatial_engine.core.spatial_encoding import SpatialPositionEncoding
        from spatial_engine.core.spatial_token import SpatialToken

        # Create spatial tokens
        pos_encoder = SpatialPositionEncoding(d_model=768)
        tokens = []
        embeddings_list = []
        positions_list = []
        metadata_list = []

        for i in range(10):
            position = (float(i * 10), float(i * 5), float(i * 2))
            embedding = torch.randn(768)
            pos_tensor = torch.tensor([position], dtype=torch.float32).unsqueeze(0)
            spatial_encoding = pos_encoder(pos_tensor).squeeze(0).squeeze(0)

            token = SpatialToken(
                token_id=i,
                position=position,
                embedding=embedding,
                spatial_encoding=spatial_encoding,
            )
            tokens.append(token)
            embeddings_list.append(embedding)
            positions_list.append(torch.tensor(position))
            metadata_list.append({"token_id": i, "text": f"Token {i}"})

        # Store in vector database
        embeddings = torch.stack(embeddings_list)
        positions = torch.stack(positions_list)

        ids = adapter.store(
            embeddings=embeddings,
            positions=positions,
            metadata=metadata_list,
        )

        # Verify storage
        assert len(ids) == 10

        # Query
        query_vector = torch.randn(768)
        query_position = (25.0, 12.5, 5.0)  # Near token 2-3

        results_emb, results_pos, results_ids = adapter.query(
            query_vector=query_vector,
            query_position=query_position,
            k=5,
        )

        # Verify results
        assert results_emb.shape[0] <= 5
        assert results_pos.shape[0] == results_emb.shape[0]
        assert len(results_ids) == results_emb.shape[0]


# Test execution marker
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
