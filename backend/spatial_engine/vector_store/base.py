# Copyright 2025-2026 Adolfo Lopez (ch1pu)
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Adolfo Lopez (ch1pu) - github.com/ch1pu
# Project: INFINATE - Infinite Context Spatial AI (github.com/ch1pu/infinate)
#
# ============================================================================
# BUILT BY A U.S. NAVY VETERAN | BUILT IN TEXAS | OPEN FOR OPPORTUNITIES
# ============================================================================
# I'm actively seeking software engineering roles. If you're reading this code
# and like what you see, let's connect:
#   - GitHub: github.com/ch1pu
#   - Twitter/X: @2006_adolfo
#   - Project: This codebase demonstrates O(k) spatial attention, achieving
#     10,317x speedup over MIT's approach with 89.58% test coverage.
# ============================================================================

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
        min_distance: Optional[float] = None,
    ) -> tuple[torch.Tensor, torch.Tensor, list[str]]:
        """Query for similar tokens using vector similarity and spatial proximity.

        Combines semantic similarity (via embedding) with spatial proximity (via position)
        to retrieve the most relevant tokens. This is mathematically equivalent to the
        spatial attention mechanism.

        Args:
            query_vector: (d_model,) tensor of query embedding
            query_position: (x, y, z) tuple of query position
            k: Number of nearest neighbors to return
            radius: Optional max spatial radius filter (only tokens within this distance)
            min_distance: Optional min spatial radius filter (only tokens beyond this distance)
                          Added in M1.11 for warp lane detection.

        Returns:
            Tuple of (embeddings, positions, ids):
            - embeddings: (k, d_model) tensor of retrieved embeddings
            - positions: (k, 3) tensor of retrieved positions
            - ids: List of k IDs

        Example:
            ```python
            query_vector = torch.randn(768)
            query_position = (10.0, 20.0, 30.0)

            # Standard query - tokens within 100 units
            embeddings, positions, ids = store.query(
                query_vector,
                query_position,
                k=50,
                radius=100.0
            )

            # Warp lane query - distant tokens only (M1.11)
            embeddings, positions, ids = store.query(
                query_vector,
                query_position,
                k=50,
                min_distance=100.0,  # Beyond normal attention
                radius=500.0         # But not too far
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
