"""
test_integration_core.py - Core integration tests for transformer-vectorstore bridge.

Tests the integration between SpatialTransformer and VectorStore backends,
verifying end-to-end functionality with both Qdrant and pgvector.

Author: ch1pu
Milestone: 1.7 - Integration Testing
TDD Phase: RED (tests written first, implementation follows)

Test Count: 17 tests
- TestTransformerBridge: 3 tests
- TestQdrantIntegration: 5 tests
- TestPgvectorIntegration: 5 tests
- TestEdgeCases: 4 tests
"""

import pytest
import torch

from spatial_engine.core.spatial_transformer import SpatialTransformer
from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter
from spatial_engine.integration import TransformerBridge, ContextManager


# ---------------------------------------------------------------------------
# TestTransformerBridge - Core Bridge Tests (3 tests)
# ---------------------------------------------------------------------------


class TestTransformerBridge:
    """Test TransformerBridge initialization and basic functionality."""

    def test_bridge_initialization(
        self,
        spatial_transformer: SpatialTransformer,
        qdrant_adapter: QdrantAdapter,
    ) -> None:
        """Verify TransformerBridge initializes correctly with components.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=qdrant_adapter,
            k_neighbors=50,
        )

        assert bridge.transformer is spatial_transformer
        assert bridge.vector_store is qdrant_adapter
        assert bridge.k_neighbors == 50

    def test_bridge_connects_transformer_to_vectorstore(
        self,
        spatial_transformer: SpatialTransformer,
        qdrant_with_data: QdrantAdapter,
    ) -> None:
        """Verify bridge connects transformer to vector store for queries.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=qdrant_with_data,
            k_neighbors=50,
        )

        # Create test input
        x = torch.randn(1, 32, 768)
        positions = torch.randn(1, 32, 3) * 100.0

        # Forward pass should work without errors
        output = bridge(x, positions)

        # Output shape should match input
        assert output.shape == x.shape

    def test_bridge_query_during_forward(
        self,
        spatial_transformer: SpatialTransformer,
        qdrant_with_data: QdrantAdapter,
    ) -> None:
        """Verify bridge queries vector store during forward pass.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=qdrant_with_data,
            k_neighbors=10,
        )

        # Create test input
        x = torch.randn(1, 16, 768)
        positions = torch.randn(1, 16, 3) * 100.0

        # Forward pass
        output = bridge(x, positions)

        # Bridge should have context from vector store
        # (implementation will track this)
        assert hasattr(bridge, "last_context_count")
        assert bridge.last_context_count > 0


# ---------------------------------------------------------------------------
# TestQdrantIntegration - Qdrant-specific Tests (5 tests)
# ---------------------------------------------------------------------------


class TestQdrantIntegration:
    """Test integration with Qdrant vector store."""

    def test_qdrant_query_during_forward_pass(
        self,
        spatial_transformer: SpatialTransformer,
        qdrant_with_data: QdrantAdapter,
        sample_batch: tuple[torch.Tensor, torch.Tensor],
    ) -> None:
        """Verify Qdrant is queried during transformer forward pass.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=qdrant_with_data,
            k_neighbors=20,
        )

        x, positions = sample_batch

        # Forward pass
        output = bridge(x, positions)

        # Output should be valid tensor
        assert output.shape == x.shape
        assert not torch.isnan(output).any()
        assert not torch.isinf(output).any()

    def test_qdrant_handles_batch_queries(
        self,
        spatial_transformer: SpatialTransformer,
        qdrant_with_data: QdrantAdapter,
    ) -> None:
        """Verify Qdrant handles batch queries efficiently.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=qdrant_with_data,
            k_neighbors=50,
        )

        # Batch of 4 sequences
        x = torch.randn(4, 64, 768)
        positions = torch.randn(4, 64, 3) * 100.0

        output = bridge(x, positions)

        assert output.shape == (4, 64, 768)

    def test_qdrant_error_handling(
        self,
        spatial_transformer: SpatialTransformer,
    ) -> None:
        """Verify graceful handling of Qdrant errors.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        # Create adapter with invalid collection (will be empty)
        adapter = QdrantAdapter(
            collection_name="empty_test",
            d_model=768,
            use_memory=True,
        )

        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=adapter,
            k_neighbors=50,
        )

        # Forward pass with empty vector store should still work
        x = torch.randn(1, 32, 768)
        positions = torch.randn(1, 32, 3) * 100.0

        # Should not raise, just return transformer output without context
        output = bridge(x, positions)
        assert output.shape == x.shape

        adapter.close()

    def test_qdrant_cache_behavior(
        self,
        spatial_transformer: SpatialTransformer,
        qdrant_with_data: QdrantAdapter,
    ) -> None:
        """Verify caching behavior for repeated queries.

        RED Phase: This test will fail until ContextManager is implemented.
        """
        context_manager = ContextManager(
            vector_store=qdrant_with_data,
            enable_cache=True,
        )

        # Same query twice
        query = torch.randn(768)
        position = (10.0, 20.0, 30.0)

        result1 = context_manager.retrieve_context(query, position, k=20)
        result2 = context_manager.retrieve_context(query, position, k=20)

        # Cache hit should return same results
        assert context_manager.cache_hits >= 1
        assert torch.allclose(result1[0], result2[0])

    def test_qdrant_memory_cleanup(
        self,
        spatial_transformer: SpatialTransformer,
        qdrant_adapter: QdrantAdapter,
    ) -> None:
        """Verify memory is properly cleaned up after operations.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        # Store some data
        embeddings = torch.randn(50, 768)
        positions = torch.randn(50, 3) * 100.0
        qdrant_adapter.store(embeddings, positions)

        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=qdrant_adapter,
            k_neighbors=20,
        )

        # Run multiple forward passes
        for _ in range(10):
            x = torch.randn(1, 32, 768)
            pos = torch.randn(1, 32, 3) * 100.0
            _ = bridge(x, pos)

        # Memory should be bounded (no leaks)
        # Implementation will track this
        assert hasattr(bridge, "memory_ok")
        assert bridge.memory_ok is True


# ---------------------------------------------------------------------------
# TestPgvectorIntegration - pgvector-specific Tests (5 tests)
# ---------------------------------------------------------------------------


class TestPgvectorIntegration:
    """Test integration with PostgreSQL + pgvector."""

    @pytest.mark.requires_docker
    def test_pgvector_query_during_forward_pass(
        self,
        spatial_transformer: SpatialTransformer,
        pgvector_with_data,
        sample_batch: tuple[torch.Tensor, torch.Tensor],
    ) -> None:
        """Verify pgvector is queried during transformer forward pass.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=pgvector_with_data,
            k_neighbors=20,
        )

        x, positions = sample_batch

        # Forward pass
        output = bridge(x, positions)

        # Output should be valid tensor
        assert output.shape == x.shape
        assert not torch.isnan(output).any()

    @pytest.mark.requires_docker
    def test_pgvector_handles_batch_queries(
        self,
        spatial_transformer: SpatialTransformer,
        pgvector_with_data,
    ) -> None:
        """Verify pgvector handles batch queries efficiently.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=pgvector_with_data,
            k_neighbors=50,
        )

        # Batch of 4 sequences
        x = torch.randn(4, 64, 768)
        positions = torch.randn(4, 64, 3) * 100.0

        output = bridge(x, positions)

        assert output.shape == (4, 64, 768)

    @pytest.mark.requires_docker
    def test_pgvector_error_handling(
        self,
        spatial_transformer: SpatialTransformer,
        pgvector_adapter,
    ) -> None:
        """Verify graceful handling of pgvector errors.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        # pgvector_adapter is empty
        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=pgvector_adapter,
            k_neighbors=50,
        )

        # Forward pass with empty vector store should still work
        x = torch.randn(1, 32, 768)
        positions = torch.randn(1, 32, 3) * 100.0

        output = bridge(x, positions)
        assert output.shape == x.shape

    @pytest.mark.requires_docker
    def test_pgvector_connection_pooling(
        self,
        pgvector_with_data,
    ) -> None:
        """Verify connection pooling works correctly.

        RED Phase: This test will fail until ContextManager is implemented.
        """
        context_manager = ContextManager(
            vector_store=pgvector_with_data,
            enable_cache=False,
        )

        # Multiple queries should reuse connection
        for i in range(10):
            query = torch.randn(768)
            position = (float(i), float(i), float(i))
            _ = context_manager.retrieve_context(query, position, k=10)

        # Connection should still be valid
        assert context_manager.is_connected

    @pytest.mark.requires_docker
    def test_pgvector_memory_cleanup(
        self,
        spatial_transformer: SpatialTransformer,
        pgvector_with_data,
    ) -> None:
        """Verify memory is properly cleaned up after pgvector operations.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=pgvector_with_data,
            k_neighbors=20,
        )

        # Run multiple forward passes
        for _ in range(10):
            x = torch.randn(1, 32, 768)
            pos = torch.randn(1, 32, 3) * 100.0
            _ = bridge(x, pos)

        # Memory should be bounded
        assert hasattr(bridge, "memory_ok")
        assert bridge.memory_ok is True


# ---------------------------------------------------------------------------
# TestEdgeCases - Edge Case Tests (4 tests)
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_vector_store(
        self,
        spatial_transformer: SpatialTransformer,
    ) -> None:
        """Verify behavior with empty vector store.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        # Create empty adapter
        adapter = QdrantAdapter(
            collection_name="empty_edge_case",
            d_model=768,
            use_memory=True,
        )

        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=adapter,
            k_neighbors=50,
        )

        # Should work without context
        x = torch.randn(1, 32, 768)
        positions = torch.randn(1, 32, 3) * 100.0

        output = bridge(x, positions)
        assert output.shape == x.shape

        adapter.close()

    def test_large_batch_queries(
        self,
        spatial_transformer: SpatialTransformer,
        qdrant_with_data: QdrantAdapter,
    ) -> None:
        """Verify handling of large batch queries.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=qdrant_with_data,
            k_neighbors=50,
        )

        # Large batch
        x = torch.randn(8, 256, 768)
        positions = torch.randn(8, 256, 3) * 100.0

        output = bridge(x, positions)

        assert output.shape == (8, 256, 768)

    def test_malformed_positions(
        self,
        spatial_transformer: SpatialTransformer,
        qdrant_with_data: QdrantAdapter,
    ) -> None:
        """Verify handling of edge-case positions.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=qdrant_with_data,
            k_neighbors=50,
        )

        # Test with extreme positions
        x = torch.randn(1, 32, 768)
        positions = torch.randn(1, 32, 3) * 1e6  # Very large positions

        # Should handle gracefully
        output = bridge(x, positions)
        assert output.shape == x.shape
        assert not torch.isnan(output).any()

    def test_transformer_state_consistency(
        self,
        spatial_transformer: SpatialTransformer,
        qdrant_with_data: QdrantAdapter,
    ) -> None:
        """Verify transformer state remains consistent after bridge operations.

        RED Phase: This test will fail until TransformerBridge is implemented.
        """
        # Get initial state
        initial_params = {
            name: param.clone()
            for name, param in spatial_transformer.named_parameters()
        }

        bridge = TransformerBridge(
            transformer=spatial_transformer,
            vector_store=qdrant_with_data,
            k_neighbors=50,
        )

        # Run forward pass (no training)
        spatial_transformer.eval()
        x = torch.randn(1, 32, 768)
        positions = torch.randn(1, 32, 3) * 100.0

        _ = bridge(x, positions)

        # Verify parameters unchanged (eval mode)
        for name, param in spatial_transformer.named_parameters():
            assert torch.allclose(
                param, initial_params[name]
            ), f"Parameter {name} changed during inference"
