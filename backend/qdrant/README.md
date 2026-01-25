<!--
Copyright 2025-2026 Adolfo Lopez (ch1pu)
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Adolfo Lopez (ch1pu) - github.com/ch1pu
Project: INFINATE - Infinite Context Spatial AI (github.com/ch1pu/infinate)

══════════════════════════════════════════════════════════════════════════════
BUILT BY A U.S. NAVY VETERAN | BUILT IN TEXAS | OPEN FOR OPPORTUNITIES
══════════════════════════════════════════════════════════════════════════════
I'm actively seeking software engineering roles. If you're reading this code
and like what you see, let's connect:
  - GitHub: github.com/ch1pu
  - Twitter/X: @2006_adolfo
  - Project: This codebase demonstrates O(k) spatial attention, achieving
    10,317x speedup over standard transformer attention with 89.58% test coverage.
══════════════════════════════════════════════════════════════════════════════
-->

# Qdrant Vector Database Setup

Qdrant is the primary vector database for Infinite's spatial token storage and retrieval.

## Quick Start

```bash
# Start Qdrant
cd /home/ch1pu/infinate/backend/qdrant
docker-compose up -d

# Verify it's running
docker-compose ps

# View logs
docker-compose logs -f

# Stop Qdrant
docker-compose down
```

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| HTTP API | http://localhost:6333 | REST API for queries |
| Dashboard | http://localhost:6333/dashboard | Web UI for management |
| gRPC | localhost:6334 | High-performance client |

## Python Usage

```python
from spatial_engine.vector_store.qdrant_adapter import QdrantAdapter

# Connect to local Qdrant container
adapter = QdrantAdapter(
    collection_name="spatial_memory",
    d_model=768,
    url="http://localhost:6333"
)

# Store tokens
embeddings = torch.randn(100, 768)
positions = torch.randn(100, 3) * 100
ids = adapter.store(embeddings, positions)

# Standard query
results = adapter.query(query_vector, query_position, k=50)

# M1.11 Warp Lane Query (find distant tokens)
results = adapter.query(
    query_vector,
    query_position,
    k=50,
    min_distance=100.0,  # Exclude nearby tokens
    radius=500.0         # Max range
)
```

## Testing Without Container

For unit tests, use in-memory mode (no Docker required):

```python
adapter = QdrantAdapter(
    collection_name="test",
    d_model=768,
    use_memory=True  # In-memory, no container needed
)
```

## Data Persistence

Data is stored in a Docker volume: `infinate_qdrant_data`

```bash
# View volume
docker volume inspect infinate_qdrant_data

# Backup (while running)
docker run --rm -v infinate_qdrant_data:/data -v $(pwd):/backup alpine tar czf /backup/qdrant_backup.tar.gz /data

# Delete volume (WARNING: deletes all data)
docker-compose down -v
```

## Configuration

Environment variables in docker-compose.yml:

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT__LOG_LEVEL` | INFO | Logging verbosity |
| `QDRANT__SERVICE__API_KEY` | (none) | API key for auth (production) |

## Troubleshooting

### Container won't start
```bash
# Check if port 6333 is in use
lsof -i :6333

# Check logs
docker-compose logs qdrant
```

### Connection refused
```bash
# Verify container is healthy
docker-compose ps

# Test API manually
curl http://localhost:6333/healthz
```

### Reset everything
```bash
docker-compose down -v
docker-compose up -d
```

## Milestone Reference

- **M1.6**: Vector Store Integration (Qdrant adapter created)
- **M1.11**: Strafe Jumping Navigation (added min_distance parameter)
