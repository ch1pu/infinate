"""
pgvector_adapter.py - PostgreSQL + pgvector adapter for spatial tokens.

Integrates PostgreSQL with pgvector extension to provide spatial memory
storage with efficient vector similarity search.

Author: ch1pu
Milestone: 1.6 - Vector Store Integration
"""

import uuid
from typing import Any, Optional

import torch

try:
    import psycopg2  # type: ignore
    from psycopg2.extras import execute_values  # type: ignore

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None  # type: ignore
    execute_values = None  # type: ignore

from spatial_engine.vector_store.base import VectorStoreBase


class PgvectorAdapter(VectorStoreBase):
    """PostgreSQL + pgvector adapter for storing and querying spatial tokens.

    Uses pgvector extension for efficient vector similarity search, combined
    with spatial indexing on 3D positions.

    Args:
        connection_string: PostgreSQL connection string
        table_name: Name of the table for storing tokens
        d_model: Embedding dimension (e.g., 768)

    Example:
        ```python
        adapter = PgvectorAdapter(
            connection_string="postgresql://user:pass@localhost:5432/db",
            table_name="spatial_memory",
            d_model=768
        )

        # Store tokens
        embeddings = torch.randn(10, 768)
        positions = torch.randn(10, 3) * 100.0
        ids = adapter.store(embeddings, positions)

        # Query tokens
        query_vector = torch.randn(768)
        results = adapter.query(query_vector, (0.0, 0.0, 0.0), k=50)
        ```
    """

    def __init__(
        self,
        connection_string: str,
        table_name: str,
        d_model: int,
    ):
        """Initialize pgvector adapter."""
        self.connection_string = connection_string
        self.table_name = table_name
        self.d_model = d_model

        # Create connection
        self.connection = psycopg2.connect(connection_string)
        self.connection.autocommit = True

        # Create table and indexes
        self._create_table()

    def _create_table(self) -> None:
        """Create table with pgvector extension and indexes."""
        with self.connection.cursor() as cursor:
            # Enable pgvector extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # Create table
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    embedding vector({self.d_model}),
                    position_x REAL,
                    position_y REAL,
                    position_z REAL,
                    metadata JSONB
                );
                """
            )

            # Create vector index for similarity search
            try:
                cursor.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
                    ON {self.table_name}
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                    """
                )
            except Exception:
                # Index might fail if table is empty, will be created on first insert
                pass

            # Create spatial indexes
            cursor.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_position_x_idx
                ON {self.table_name} (position_x);
                """
            )
            cursor.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_position_y_idx
                ON {self.table_name} (position_y);
                """
            )
            cursor.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {self.table_name}_position_z_idx
                ON {self.table_name} (position_z);
                """
            )

    def store(
        self,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
        ids: Optional[list[str]] = None,
        metadata: Optional[list[dict[str, Any]]] = None,
    ) -> list[str]:
        """Store spatial tokens in PostgreSQL.

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

        # Prepare data for insertion
        values = []
        for i in range(batch_size):
            embedding_list = embeddings[i].cpu().numpy().tolist()
            position_x = float(positions[i, 0].item())
            position_y = float(positions[i, 1].item())
            position_z = float(positions[i, 2].item())

            # Convert metadata to JSONB
            import json

            metadata_json = json.dumps(metadata[i])

            values.append(
                (
                    ids[i],
                    embedding_list,
                    position_x,
                    position_y,
                    position_z,
                    metadata_json,
                )
            )

        # Insert into database
        with self.connection.cursor() as cursor:
            execute_values(
                cursor,
                f"""
                INSERT INTO {self.table_name}
                (id, embedding, position_x, position_y, position_z, metadata)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    position_x = EXCLUDED.position_x,
                    position_y = EXCLUDED.position_y,
                    position_z = EXCLUDED.position_z,
                    metadata = EXCLUDED.metadata;
                """,
                values,
            )

        return ids

    def query(
        self,
        query_vector: torch.Tensor,
        query_position: tuple[float, float, float],
        k: int = 50,
        radius: Optional[float] = None,
    ) -> tuple[torch.Tensor, torch.Tensor, list[str]]:
        """Query for similar tokens using vector similarity and spatial proximity.

        Args:
            query_vector: (d_model,) tensor of query embedding
            query_position: (x, y, z) tuple of query position
            k: Number of nearest neighbors to return
            radius: Optional spatial radius filter

        Returns:
            Tuple of (embeddings, positions, ids)

        Example:
            ```python
            query_vector = torch.randn(768)
            query_position = (10.0, 20.0, 30.0)

            embeddings, positions, ids = adapter.query(
                query_vector,
                query_position,
                k=50,
                radius=100.0
            )
            ```
        """
        # Convert query vector to list
        query_vec = query_vector.cpu().numpy().tolist()
        qx, qy, qz = query_position

        # Build SQL query
        if radius is not None:
            # With spatial filter
            sql = f"""
                SELECT id, embedding, position_x, position_y, position_z
                FROM {self.table_name}
                WHERE
                    position_x BETWEEN %s AND %s
                    AND position_y BETWEEN %s AND %s
                    AND position_z BETWEEN %s AND %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """
            params = (
                qx - radius,
                qx + radius,
                qy - radius,
                qy + radius,
                qz - radius,
                qz + radius,
                query_vec,
                k,
            )
        else:
            # Without spatial filter
            sql = f"""
                SELECT id, embedding, position_x, position_y, position_z
                FROM {self.table_name}
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """
            params = (query_vec, k)

        # Execute query
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            results = cursor.fetchall()

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

        for row in results:
            id_, embedding_vec, pos_x, pos_y, pos_z = row

            # Convert embedding
            embedding = torch.tensor(embedding_vec, dtype=torch.float32)
            embeddings_list.append(embedding)

            # Convert position
            position = torch.tensor([pos_x, pos_y, pos_z], dtype=torch.float32)
            positions_list.append(position)

            # Get ID
            ids_list.append(id_)

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

        # Delete from database
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                DELETE FROM {self.table_name}
                WHERE id = ANY(%s);
                """,
                (ids,),
            )
            deleted_count = cursor.rowcount

        return deleted_count

    def close(self) -> None:
        """Close connection to PostgreSQL.

        Example:
            ```python
            adapter.close()
            ```
        """
        if self.connection:
            self.connection.close()
            self.connection = None
