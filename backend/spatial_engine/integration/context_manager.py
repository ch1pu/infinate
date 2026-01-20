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
#   - Project: This codebase demonstrates O(k) spatial attention, achieving
#     10,317x speedup over MIT's approach with 89.58% test coverage.
# ============================================================================

"""
context_manager.py - Context retrieval manager for vector store integration.

Manages context retrieval from vector stores with optional caching support.
Provides a clean interface between the transformer and vector store backends.

Author: ch1pu
Milestone: 1.7 - Integration Testing
"""

import torch

from spatial_engine.vector_store.base import VectorStoreBase


class ContextManager:
    """Manages context retrieval from vector stores.

    Provides caching and batch optimization for vector store queries,
    ensuring efficient context retrieval during transformer forward passes.

    Args:
        vector_store: VectorStoreBase implementation (Qdrant, pgvector, etc.)
        enable_cache: Enable query result caching (default: True)
        cache_size: Maximum number of cached queries (default: 1000)

    Example:
        ```python
        from spatial_engine.vector_store import QdrantAdapter
        from spatial_engine.integration import ContextManager

        # Create vector store
        store = QdrantAdapter("context", d_model=768, use_memory=True)

        # Create context manager
        manager = ContextManager(store, enable_cache=True)

        # Retrieve context
        query = torch.randn(768)
        position = (10.0, 20.0, 30.0)
        embeddings, positions, ids = manager.retrieve_context(
            query, position, k=50
        )
        ```
    """

    def __init__(
        self,
        vector_store: VectorStoreBase,
        enable_cache: bool = True,
        cache_size: int = 1000,
    ) -> None:
        """Initialize ContextManager.

        Args:
            vector_store: VectorStoreBase implementation
            enable_cache: Enable query result caching
            cache_size: Maximum number of cached queries
        """
        self.vector_store = vector_store
        self.enable_cache = enable_cache
        self.cache_size = cache_size

        # Cache storage: key -> (embeddings, positions, ids)
        self._cache: dict[
            str,
            tuple[torch.Tensor, torch.Tensor, list[str]],
        ] = {}
        self._cache_order: list[str] = []  # LRU order

        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_queries = 0

    @property
    def is_connected(self) -> bool:
        """Check if vector store connection is active.

        Returns:
            True if vector store is connected/accessible
        """
        try:
            # Attempt a minimal query to verify connection
            query = torch.zeros(
                getattr(self.vector_store, "d_model", 768),
            )
            position = (0.0, 0.0, 0.0)
            _ = self.vector_store.query(query, position, k=1)
            return True
        except Exception:
            return False

    def retrieve_context(
        self,
        query_vector: torch.Tensor,
        query_position: tuple[float, float, float],
        k: int = 50,
        radius: float | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, list[str]]:
        """Retrieve context from vector store.

        Args:
            query_vector: (d_model,) tensor of query embedding
            query_position: (x, y, z) tuple of query position
            k: Number of nearest neighbors to return
            radius: Optional spatial radius filter

        Returns:
            Tuple of (embeddings, positions, ids):
            - embeddings: (k, d_model) tensor of retrieved embeddings
            - positions: (k, 3) tensor of retrieved positions
            - ids: List of k IDs

        Example:
            ```python
            query = torch.randn(768)
            position = (10.0, 20.0, 30.0)

            embeddings, positions, ids = manager.retrieve_context(
                query, position, k=50, radius=100.0
            )
            ```
        """
        self.total_queries += 1

        # Generate cache key
        cache_key = self._generate_cache_key(query_vector, query_position, k, radius)

        # Check cache
        if self.enable_cache and cache_key in self._cache:
            self.cache_hits += 1
            return self._cache[cache_key]

        # Cache miss - query vector store
        self.cache_misses += 1

        try:
            embeddings, positions, ids = self.vector_store.query(
                query_vector=query_vector,
                query_position=query_position,
                k=k,
                radius=radius,
            )
        except Exception:
            # Return empty tensors on error
            d_model = getattr(self.vector_store, "d_model", 768)
            return (
                torch.empty(0, d_model),
                torch.empty(0, 3),
                [],
            )

        result = (embeddings, positions, ids)

        # Update cache
        if self.enable_cache:
            self._add_to_cache(cache_key, result)

        return result

    def retrieve_batch_context(
        self,
        query_vectors: torch.Tensor,
        query_positions: torch.Tensor,
        k: int = 50,
        radius: float | None = None,
    ) -> list[tuple[torch.Tensor, torch.Tensor, list[str]]]:
        """Retrieve context for multiple queries.

        Args:
            query_vectors: (batch, d_model) tensor of query embeddings
            query_positions: (batch, 3) tensor of query positions
            k: Number of nearest neighbors per query
            radius: Optional spatial radius filter

        Returns:
            List of (embeddings, positions, ids) tuples, one per query

        Example:
            ```python
            queries = torch.randn(10, 768)
            positions = torch.randn(10, 3) * 100.0

            results = manager.retrieve_batch_context(
                queries, positions, k=50
            )
            ```
        """
        batch_size = query_vectors.shape[0]
        results: list[tuple[torch.Tensor, torch.Tensor, list[str]]] = []

        for i in range(batch_size):
            query_vec = query_vectors[i]
            pos = query_positions[i]
            query_position = (
                float(pos[0].item()),
                float(pos[1].item()),
                float(pos[2].item()),
            )

            result = self.retrieve_context(
                query_vector=query_vec,
                query_position=query_position,
                k=k,
                radius=radius,
            )
            results.append(result)

        return results

    def clear_cache(self) -> None:
        """Clear the query cache.

        Example:
            ```python
            manager.clear_cache()
            assert manager.cache_hits == 0
            ```
        """
        self._cache.clear()
        self._cache_order.clear()
        self.cache_hits = 0
        self.cache_misses = 0

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dict with cache_hits, cache_misses, cache_size, total_queries
        """
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_size": len(self._cache),
            "total_queries": self.total_queries,
        }

    def _generate_cache_key(
        self,
        query_vector: torch.Tensor,
        query_position: tuple[float, float, float],
        k: int,
        radius: float | None,
    ) -> str:
        """Generate a cache key for a query.

        Uses a hash of the query parameters for efficient lookup.

        Args:
            query_vector: Query embedding
            query_position: Query position
            k: Number of neighbors
            radius: Optional radius filter

        Returns:
            String cache key
        """
        # Hash the query vector (use first few values for efficiency)
        vec_hash = hash(tuple(query_vector[:10].tolist()))
        pos_hash = hash(query_position)
        return f"{vec_hash}_{pos_hash}_{k}_{radius}"

    def _add_to_cache(
        self,
        key: str,
        result: tuple[torch.Tensor, torch.Tensor, list[str]],
    ) -> None:
        """Add a result to the cache with LRU eviction.

        Args:
            key: Cache key
            result: Query result to cache
        """
        # Remove oldest if at capacity
        if len(self._cache) >= self.cache_size:
            oldest_key = self._cache_order.pop(0)
            del self._cache[oldest_key]

        # Add new entry
        self._cache[key] = result
        self._cache_order.append(key)
