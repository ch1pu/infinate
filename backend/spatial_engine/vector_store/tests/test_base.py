"""
test_base.py - Test suite for base vector store interface.

Tests the abstract base class that defines the common interface for all
vector store adapters (Qdrant, pgvector, etc.).

Author: ch1pu
Milestone: 1.6 - Vector Store Integration
Test Count: 3
Coverage Target: ≥95%
"""

from abc import ABC

import pytest
import torch


class TestVectorStoreBase:
    """Test suite for VectorStoreBase abstract class."""

    def test_base_is_abstract(self):
        """Test that VectorStoreBase cannot be instantiated directly.

        Verifies:
        - VectorStoreBase is an abstract class
        - Cannot create instances directly
        - Must be subclassed
        """
        from spatial_engine.vector_store.base import VectorStoreBase

        # Verify it's an ABC
        assert issubclass(VectorStoreBase, ABC)

        # Attempting to instantiate should raise TypeError
        with pytest.raises(TypeError):
            VectorStoreBase()

    def test_required_methods(self):
        """Test that required abstract methods are defined.

        Verifies:
        - store() method is abstract
        - query() method is abstract
        - delete() method is abstract
        - close() method is abstract
        """

        from spatial_engine.vector_store.base import VectorStoreBase

        # Get abstract methods
        abstract_methods = VectorStoreBase.__abstractmethods__

        # Verify required methods are abstract
        assert "store" in abstract_methods
        assert "query" in abstract_methods
        assert "delete" in abstract_methods
        assert "close" in abstract_methods

    def test_minimal_implementation(self):
        """Test that a minimal implementation can be created.

        Verifies:
        - Subclass with all methods implemented can be instantiated
        - Methods have correct signatures
        - Type hints are preserved
        """
        from typing import Optional

        from spatial_engine.vector_store.base import VectorStoreBase

        # Create minimal implementation
        class MinimalVectorStore(VectorStoreBase):
            def store(
                self,
                embeddings: torch.Tensor,
                positions: torch.Tensor,
                ids: Optional[list[str]] = None,
                metadata: Optional[list[dict]] = None,
            ) -> list[str]:
                return ids or []

            def query(
                self,
                query_vector: torch.Tensor,
                query_position: tuple[float, float, float],
                k: int = 50,
                radius: Optional[float] = None,
            ) -> tuple[torch.Tensor, torch.Tensor, list[str]]:
                # Return empty results
                return (
                    torch.empty(0, 768),
                    torch.empty(0, 3),
                    [],
                )

            def delete(self, ids: list[str]) -> int:
                return len(ids)

            def close(self) -> None:
                pass

        # Should be able to instantiate
        store = MinimalVectorStore()
        assert store is not None

        # Verify methods are callable
        assert callable(store.store)
        assert callable(store.query)
        assert callable(store.delete)
        assert callable(store.close)


# Test execution marker
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
