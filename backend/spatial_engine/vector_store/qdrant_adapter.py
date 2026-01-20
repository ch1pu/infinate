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
qdrant_adapter.py - Qdrant vector database adapter for spatial tokens.

Integrates Qdrant vector database to provide unlimited context through
efficient similarity search combined with spatial proximity filtering.

Author: ch1pu
Milestone: 1.6 - Vector Store Integration
"""

import uuid
from typing import TYPE_CHECKING, Any, Optional

import torch

if TYPE_CHECKING:
    from qdrant_client import QdrantClient as QdrantClientType
else:
    QdrantClientType = Any  # type: ignore

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        FieldCondition,
        Filter,
        PointStruct,
        Range,
        VectorParams,
    )

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    QdrantClient = None  # type: ignore

from spatial_engine.vector_store.base import VectorStoreBase


class QdrantAdapter(VectorStoreBase):
    """Qdrant adapter for storing and querying spatial tokens.

    Uses Qdrant's HNSW indexing for fast similarity search, combined with
    spatial filtering based on 3D positions.

    Args:
        collection_name: Name of the Qdrant collection
        d_model: Embedding dimension (e.g., 768)
        use_memory: If True, use in-memory mode (for testing)
        url: Qdrant server URL (if not using memory mode)
        api_key: Optional API key for Qdrant Cloud

    Example:
        ```python
        # In-memory mode for testing
        adapter = QdrantAdapter(
            collection_name="spatial_memory",
            d_model=768,
            use_memory=True
        )

        # Production mode with Qdrant server
        adapter = QdrantAdapter(
            collection_name="spatial_memory",
            d_model=768,
            url="http://localhost:6333"
        )
        ```
    """

    def __init__(
        self,
        collection_name: str,
        d_model: int,
        use_memory: bool = False,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize Qdrant adapter."""
        self.collection_name = collection_name
        self.d_model = d_model

        # Create Qdrant client
        if use_memory:
            self.client = QdrantClient(":memory:")
        elif url:
            self.client = QdrantClient(url=url, api_key=api_key)
        else:
            # Default to localhost
            self.client = QdrantClient(url="http://localhost:6333")

        # Create collection if it doesn't exist
        self._create_collection()

    def _create_collection(self) -> None:
        """Create Qdrant collection with appropriate configuration."""
        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]

        if self.collection_name not in collection_names:
            # Create collection with cosine similarity
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.d_model,
                    distance=Distance.COSINE,
                ),
            )

    def store(
        self,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
        ids: Optional[list[str]] = None,
        metadata: Optional[list[dict[str, Any]]] = None,
    ) -> list[str]:
        """Store spatial tokens in Qdrant.

        Args:
            embeddings: (batch_size, d_model) tensor of embeddings
            positions: (batch_size, 3) tensor of 3D positions
            ids: Optional list of IDs (generated if not provided)
            metadata: Optional list of metadata dicts

        Returns:
            List of IDs for stored tokens

        Example:
            ```python
            embeddings = torch.randn(10, 768)
            positions = torch.randn(10, 3) * 100.0
            metadata = [{"text": f"Token {i}"} for i in range(10)]

            ids = adapter.store(embeddings, positions, metadata=metadata)
            ```
        """
        batch_size = embeddings.shape[0]

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(batch_size)]

        # Default metadata
        if metadata is None:
            metadata = [{} for _ in range(batch_size)]

        # Create points for Qdrant
        points = []
        for i in range(batch_size):
            # Convert embedding to list
            embedding_vec = embeddings[i].cpu().numpy().tolist()

            # Add position to payload
            payload = metadata[i].copy()
            payload["position_x"] = float(positions[i, 0].item())
            payload["position_y"] = float(positions[i, 1].item())
            payload["position_z"] = float(positions[i, 2].item())

            # Create point
            point = PointStruct(
                id=ids[i],
                vector=embedding_vec,
                payload=payload,
            )
            points.append(point)

        # Upload to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        return ids

    def query(
        self,
        query_vector: torch.Tensor,
        query_position: tuple[float, float, float],
        k: int = 50,
        radius: Optional[float] = None,
        min_distance: Optional[float] = None,
    ) -> tuple[torch.Tensor, torch.Tensor, list[str]]:
        """Query for similar tokens using vector similarity and spatial proximity.

        Args:
            query_vector: (d_model,) tensor of query embedding
            query_position: (x, y, z) tuple of query position
            k: Number of nearest neighbors to return
            radius: Optional maximum spatial radius filter
            min_distance: Optional minimum distance filter (for warp lane detection)
                         Tokens closer than min_distance are excluded.

        Returns:
            Tuple of (embeddings, positions, ids)

        Example:
            ```python
            query_vector = torch.randn(768)
            query_position = (10.0, 20.0, 30.0)

            # Standard query with max radius
            embeddings, positions, ids = adapter.query(
                query_vector,
                query_position,
                k=50,
                radius=100.0
            )

            # Warp lane query: find distant tokens (M1.11)
            embeddings, positions, ids = adapter.query(
                query_vector,
                query_position,
                k=50,
                min_distance=100.0,  # Exclude nearby tokens
                radius=500.0         # But within max range
            )
            ```
        """
        # Convert query vector to list
        query_vec = query_vector.cpu().numpy().tolist()
        qx, qy, qz = query_position

        # Build spatial filter if radius provided
        query_filter = None
        filter_conditions = []

        if radius is not None:
            # Create range filters for each dimension (bounding box approximation)
            # Qdrant doesn't natively support spherical range queries
            filter_conditions.extend([
                FieldCondition(
                    key="position_x",
                    range=Range(gte=qx - radius, lte=qx + radius),
                ),
                FieldCondition(
                    key="position_y",
                    range=Range(gte=qy - radius, lte=qy + radius),
                ),
                FieldCondition(
                    key="position_z",
                    range=Range(gte=qz - radius, lte=qz + radius),
                ),
            ])

        if filter_conditions:
            query_filter = Filter(must=filter_conditions)

        # If min_distance is set, we need to fetch extra results for post-filtering
        # since Qdrant doesn't support "greater than distance" natively
        fetch_limit = k
        if min_distance is not None:
            # Fetch 3x more to account for filtering (heuristic)
            fetch_limit = k * 3

        # Query Qdrant
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vec,
            limit=fetch_limit,
            query_filter=query_filter,
            with_vectors=True,
            with_payload=True,
        )

        # Extract points from response
        results = response.points

        # Extract results
        if len(results) == 0:
            return (
                torch.empty(0, self.d_model),
                torch.empty(0, 3),
                [],
            )

        embeddings_list = []
        positions_list = []
        ids_list = []

        # M1.11: Pre-compute min_distance_squared for efficient filtering
        min_distance_sq = min_distance * min_distance if min_distance is not None else None

        for result in results:
            # Get position from payload
            payload = result.payload or {}
            pos_x = payload.get("position_x", 0.0)
            pos_y = payload.get("position_y", 0.0)
            pos_z = payload.get("position_z", 0.0)

            # M1.11: Filter by min_distance (post-filtering since Qdrant lacks native support)
            if min_distance_sq is not None:
                dist_sq = (pos_x - qx) ** 2 + (pos_y - qy) ** 2 + (pos_z - qz) ** 2
                if dist_sq <= min_distance_sq:
                    continue  # Skip tokens too close

            # Get embedding from vector
            embedding = torch.tensor(result.vector, dtype=torch.float32)
            embeddings_list.append(embedding)

            # Get position
            position = torch.tensor([pos_x, pos_y, pos_z], dtype=torch.float32)
            positions_list.append(position)

            # Get ID
            ids_list.append(str(result.id))

            # Stop once we have k results
            if len(embeddings_list) >= k:
                break

        # Handle empty results after filtering
        if len(embeddings_list) == 0:
            return (
                torch.empty(0, self.d_model),
                torch.empty(0, 3),
                [],
            )

        # Stack into tensors
        embeddings = torch.stack(embeddings_list)
        positions = torch.stack(positions_list)

        return embeddings, positions, ids_list

    def delete(self, ids: list[str]) -> int:
        """Delete tokens by ID.

        Args:
            ids: List of token IDs to delete

        Returns:
            Number of tokens deleted

        Example:
            ```python
            deleted_count = adapter.delete(["id1", "id2", "id3"])
            ```
        """
        if len(ids) == 0:
            return 0

        # Delete from Qdrant
        from qdrant_client.models import PointIdsList

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=ids),  # type: ignore
        )

        return len(ids)

    def close(self) -> None:
        """Close connection to Qdrant.

        Example:
            ```python
            adapter.close()
            ```
        """
        # Qdrant client doesn't require explicit closing
        # Resources will be released automatically
        pass
