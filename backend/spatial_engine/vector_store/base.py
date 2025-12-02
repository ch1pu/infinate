"""
base.py - Abstract base class for vector store adapters.

Defines the common interface for all vector store implementations
(Qdrant, pgvector, etc.) to ensure consistency across adapters.

Author: ch1pu
Milestone: 1.6 - Vector Store Integration
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import torch


class VectorStoreBase(ABC):
    """Abstract base class for vector store adapters.

    Defines the common interface that all vector store implementations must follow.
    This ensures that Qdrant, pgvector, and any future adapters have consistent APIs.

    The vector store serves as the spatial memory layer for the transformer,
    enabling unlimited context through efficient similarity search combined with
    spatial proximity filtering.

    Example:
        ```python
        # Subclass must implement all abstract methods
        class MyVectorStore(VectorStoreBase):
            def store(self, embeddings, positions, ids=None, metadata=None):
                # Implementation here
                pass

            def query(self, query_vector, query_position, k=50, radius=None):
                # Implementation here
                pass

            def delete(self, ids):
                # Implementation here
                pass

            def close(self):
                # Implementation here
                pass
        ```
    """

    @abstractmethod
    def store(
        self,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
        ids: Optional[list[str]] = None,
        metadata: Optional[list[dict[str, Any]]] = None,
    ) -> list[str]:
        """Store spatial tokens in the vector database.

        Args:
            embeddings: (batch_size, d_model) tensor of token embeddings
            positions: (batch_size, 3) tensor of 3D positions
            ids: Optional list of IDs (generated if not provided)
            metadata: Optional list of metadata dicts (one per token)

        Returns:
            List of IDs for the stored tokens

        Example:
            ```python
            embeddings = torch.randn(10, 768)
            positions = torch.randn(10, 3) * 100.0
            metadata = [{"text": f"Token {i}"} for i in range(10)]

            ids = store.store(embeddings, positions, metadata=metadata)
            ```
        """
        pass

    @abstractmethod
    def query(
        self,
        query_vector: torch.Tensor,
        query_position: tuple[float, float, float],
        k: int = 50,
        radius: Optional[float] = None,
    ) -> tuple[torch.Tensor, torch.Tensor, list[str]]:
        """Query for similar tokens using vector similarity and spatial proximity.

        Combines semantic similarity (via embedding) with spatial proximity (via position)
        to retrieve the most relevant tokens. This is mathematically equivalent to the
        spatial attention mechanism.

        Args:
            query_vector: (d_model,) tensor of query embedding
            query_position: (x, y, z) tuple of query position
            k: Number of nearest neighbors to return
            radius: Optional spatial radius filter (only return tokens within this distance)

        Returns:
            Tuple of (embeddings, positions, ids):
            - embeddings: (k, d_model) tensor of retrieved embeddings
            - positions: (k, 3) tensor of retrieved positions
            - ids: List of k IDs

        Example:
            ```python
            query_vector = torch.randn(768)
            query_position = (10.0, 20.0, 30.0)

            embeddings, positions, ids = store.query(
                query_vector,
                query_position,
                k=50,
                radius=100.0  # Only tokens within 100 units
            )
            ```
        """
        pass

    @abstractmethod
    def delete(self, ids: list[str]) -> int:
        """Delete tokens by ID.

        Args:
            ids: List of token IDs to delete

        Returns:
            Number of tokens successfully deleted

        Example:
            ```python
            deleted_count = store.delete(["id1", "id2", "id3"])
            assert deleted_count == 3
            ```
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the connection to the vector store.

        Clean up any resources (connections, file handles, etc.).

        Example:
            ```python
            store.close()
            ```
        """
        pass
