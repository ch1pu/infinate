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

# INFINITE: Database Indexing Strategy
**Performance Optimization Through Strategic Index Design**

---

## EXECUTIVE SUMMARY

This document defines the comprehensive indexing strategy for Infinite's PostgreSQL database, optimizing query performance for spatial searches, semantic similarity, real-time streaming, and high-concurrency operations while maintaining write performance.

---

## 1. INDEXING PRINCIPLES

### Core Strategy

```sql
-- Index Selection Criteria
/*
1. Selectivity > 0.95 for B-tree indexes
2. Frequently in WHERE, JOIN, ORDER BY clauses
3. Query frequency * impact > threshold
4. Write overhead < 10% performance impact
5. Index size < 10% of table size
*/
```

### Index Types Used

| Type | Use Case | Example |
|------|----------|---------|
| B-tree | Exact matches, ranges | user_id, created_at |
| Hash | Exact equality only | token_hash |
| GIN | Full-text search, arrays | metadata JSONB |
| GiST | Spatial, ranges | position coordinates |
| IVFFlat | Vector similarity | embeddings |
| BRIN | Large sequential data | audit logs |

---

## 2. PRIMARY INDEXES

### Users Table Indexes

```sql
-- Primary key (automatic B-tree)
-- Already created: PRIMARY KEY (id)

-- Unique constraints (automatic B-tree)
-- Already created: UNIQUE (email), UNIQUE (username)

-- Authentication lookups
CREATE INDEX idx_users_email_lower ON users (LOWER(email));
CREATE INDEX idx_users_active_verified ON users (is_active, is_verified)
    WHERE is_active = true;

-- Role-based queries
CREATE INDEX idx_users_roles_gin ON users USING GIN (roles);
CREATE INDEX idx_users_permissions_gin ON users USING GIN (permissions);

-- Login tracking
CREATE INDEX idx_users_last_login ON users (last_login_at DESC NULLS LAST);

-- Analyze for statistics
ANALYZE users;
```

### Sessions Table Indexes

```sql
-- User session lookups
CREATE INDEX idx_sessions_user_id_active ON sessions (user_id, expires_at)
    WHERE expires_at > CURRENT_TIMESTAMP;

-- Token validation (hash index for exact match)
CREATE INDEX idx_sessions_token_hash_hash ON sessions USING HASH (token_hash);

-- Session cleanup
CREATE INDEX idx_sessions_expires_at_partial ON sessions (expires_at)
    WHERE expires_at <= CURRENT_TIMESTAMP;

-- Device tracking
CREATE INDEX idx_sessions_device_id ON sessions (device_id)
    WHERE device_id IS NOT NULL;

-- IP-based queries
CREATE INDEX idx_sessions_ip_address ON sessions USING GIST (ip_address inet_ops);
```

### Memory Spaces Indexes

```sql
-- Owner lookups
CREATE INDEX idx_memory_spaces_owner_public ON memory_spaces (owner_id, is_public);

-- Name search (trigram for fuzzy matching)
CREATE INDEX idx_memory_spaces_name_trgm ON memory_spaces
    USING GIN (name gin_trgm_ops);

-- Metadata queries
CREATE INDEX idx_memory_spaces_metadata_gin ON memory_spaces
    USING GIN (metadata);

-- Stats tracking
CREATE INDEX idx_memory_spaces_stats_gin ON memory_spaces
    USING GIN (stats);

-- Spatial bounds
CREATE INDEX idx_memory_spaces_bounds_gin ON memory_spaces
    USING GIN (bounds);
```

---

## 3. SPATIAL INDEXING

### Chunks Table Spatial Indexes

```sql
-- 3D spatial index using cube extension
CREATE EXTENSION IF NOT EXISTS cube;

-- Create 3D point index
ALTER TABLE chunks ADD COLUMN position_cube cube;
UPDATE chunks SET position_cube = cube(ARRAY[position_x, position_y, position_z]);

CREATE INDEX idx_chunks_position_cube ON chunks
    USING GIST (position_cube);

-- Composite spatial index for range queries
CREATE INDEX idx_chunks_spatial_composite ON chunks
    (space_id, position_x, position_y, position_z);

-- Spatial partitioning index
CREATE INDEX idx_chunks_spatial_partition ON chunks
    (
        space_id,
        floor(position_x / 100)::int,
        floor(position_y / 100)::int,
        floor(position_z / 100)::int
    );

-- Type and position combination
CREATE INDEX idx_chunks_type_position ON chunks
    (space_id, type, position_x, position_y, position_z);

-- Hot chunks (frequently accessed)
CREATE INDEX idx_chunks_hot_access ON chunks
    (space_id, access_count DESC, accessed_at DESC)
    WHERE access_count > 10;
```

### Octree Indexing

```sql
-- Octree node traversal
CREATE INDEX idx_octree_nodes_traversal ON octree_nodes
    (space_id, parent_id, level, octant);

-- Bounds-based queries
CREATE INDEX idx_octree_nodes_bounds_cube ON octree_nodes
    USING GIST (
        cube(ARRAY[bounds_min_x, bounds_min_y, bounds_min_z,
                   bounds_max_x, bounds_max_y, bounds_max_z])
    );

-- Leaf node queries
CREATE INDEX idx_octree_nodes_leaf_chunks ON octree_nodes
    (space_id, is_leaf, chunk_count DESC)
    WHERE is_leaf = true;

-- Node children lookup
CREATE INDEX idx_octree_nodes_children ON octree_nodes
    (parent_id)
    WHERE parent_id IS NOT NULL;
```

---

## 4. VECTOR SIMILARITY INDEXES

### Embedding Indexes

```sql
-- Vector similarity search (IVFFlat)
CREATE INDEX idx_chunks_embedding_ivfflat ON chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- L2 distance alternative
CREATE INDEX idx_chunks_embedding_l2 ON chunks
    USING ivfflat (embedding vector_l2_ops)
    WITH (lists = 100);

-- Inner product for normalized vectors
CREATE INDEX idx_chunks_embedding_ip ON chunks
    USING ivfflat (embedding vector_ip_ops)
    WITH (lists = 100);

-- Partial index for chunks with embeddings
CREATE INDEX idx_chunks_embedding_exists ON chunks
    (space_id, type)
    WHERE embedding IS NOT NULL;

-- Multi-model embeddings
CREATE INDEX idx_embeddings_model_chunk ON embeddings
    (model, chunk_id);

CREATE INDEX idx_embeddings_vector ON embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 200);
```

### Optimizing Vector Indexes

```sql
-- Maintenance script for vector indexes
DO $$
BEGIN
    -- Set maintenance work memory for index creation
    SET maintenance_work_mem = '2GB';

    -- Optimal lists calculation: sqrt(number of rows)
    -- For 1M vectors, use ~1000 lists
    -- For 10K vectors, use ~100 lists

    -- Periodic reindexing for optimal performance
    REINDEX INDEX CONCURRENTLY idx_chunks_embedding_ivfflat;
END $$;
```

---

## 5. QUERY OPTIMIZATION INDEXES

### Agent Queries

```sql
-- Agent position and status
CREATE INDEX idx_agents_active_position ON agents
    (space_id, status, position_x, position_y, position_z)
    WHERE status IN ('active', 'loading');

-- User's agents
CREATE INDEX idx_agents_user_space ON agents
    (user_id, space_id, status);

-- Context state queries
CREATE INDEX idx_agents_context_gin ON agents
    USING GIN (context_state);

-- Agent view frustum
CREATE INDEX idx_agents_frustum_gin ON agents
    USING GIN (view_frustum);
```

### Query History

```sql
-- User query history
CREATE INDEX idx_queries_user_recent ON queries
    (user_id, created_at DESC);

-- Agent query tracking
CREATE INDEX idx_queries_agent_recent ON queries
    (agent_id, created_at DESC);

-- Query type analysis
CREATE INDEX idx_queries_type_time ON queries
    (query_type, created_at DESC)
    WHERE query_type IS NOT NULL;

-- Context chunk lookups
CREATE INDEX idx_queries_chunks_gin ON queries
    USING GIN (context_chunks);

-- Performance tracking
CREATE INDEX idx_queries_slow ON queries
    (created_at DESC)
    WHERE processing_time_ms > 1000;
```

---

## 6. PERFORMANCE MONITORING INDEXES

### Access Pattern Indexes

```sql
-- Chunk access patterns
CREATE INDEX idx_chunk_access_patterns_recent ON chunk_access_patterns
    (chunk_id, accessed_at DESC);

-- Agent access tracking
CREATE INDEX idx_chunk_access_patterns_agent ON chunk_access_patterns
    (agent_id, accessed_at DESC)
    WHERE agent_id IS NOT NULL;

-- Time-based analysis
CREATE INDEX idx_chunk_access_patterns_hourly ON chunk_access_patterns
    (date_trunc('hour', accessed_at), access_type);

-- BRIN index for time-series data
CREATE INDEX idx_chunk_access_patterns_brin ON chunk_access_patterns
    USING BRIN (accessed_at);
```

### Performance Metrics

```sql
-- Metric name lookups
CREATE INDEX idx_performance_metrics_name_time ON performance_metrics
    (metric_name, recorded_at DESC);

-- Tag-based queries
CREATE INDEX idx_performance_metrics_tags_gin ON performance_metrics
    USING GIN (tags);

-- Time-series queries (BRIN for sequential data)
CREATE INDEX idx_performance_metrics_time_brin ON performance_metrics
    USING BRIN (recorded_at)
    WITH (pages_per_range = 128);

-- Aggregation queries
CREATE INDEX idx_performance_metrics_hourly ON performance_metrics
    (metric_name, date_trunc('hour', recorded_at));
```

---

## 7. SPECIALIZED INDEXES

### Full-Text Search

```sql
-- Content search
ALTER TABLE chunks ADD COLUMN content_tsv tsvector;

UPDATE chunks
SET content_tsv = to_tsvector('english', content);

CREATE INDEX idx_chunks_content_fts ON chunks
    USING GIN (content_tsv);

-- Trigger to maintain tsvector
CREATE TRIGGER chunks_content_tsv_trigger
BEFORE INSERT OR UPDATE ON chunks
FOR EACH ROW EXECUTE FUNCTION
    tsvector_update_trigger(content_tsv, 'pg_catalog.english', content);

-- Metadata search
CREATE INDEX idx_chunks_metadata_gin_path ON chunks
    USING GIN (metadata jsonb_path_ops);
```

### Hash-Based Deduplication

```sql
-- Content hash for deduplication
CREATE INDEX idx_chunks_content_hash_space ON chunks
    (space_id, content_hash);

-- Unique partial index for active chunks
CREATE UNIQUE INDEX idx_chunks_hash_unique_active ON chunks
    (space_id, content_hash)
    WHERE updated_at > CURRENT_TIMESTAMP - INTERVAL '7 days';
```

### Audit Trail

```sql
-- Audit log queries
CREATE INDEX idx_audit_logs_actor_composite ON audit_logs
    (actor_type, actor_id, created_at DESC);

CREATE INDEX idx_audit_logs_resource_composite ON audit_logs
    (resource_type, resource_id, created_at DESC);

-- Time-based partitioning index
CREATE INDEX idx_audit_logs_daily ON audit_logs
    (date_trunc('day', created_at), action);

-- BRIN for append-only audit logs
CREATE INDEX idx_audit_logs_created_brin ON audit_logs
    USING BRIN (created_at)
    WITH (pages_per_range = 32);
```

---

## 8. INDEX MAINTENANCE

### Automated Maintenance Script

```sql
-- Function to analyze index usage
CREATE OR REPLACE FUNCTION analyze_index_usage()
RETURNS TABLE (
    index_name text,
    table_name text,
    index_size text,
    index_scans bigint,
    rows_read bigint,
    rows_fetched bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        indexrelname::text,
        tablename::text,
        pg_size_pretty(pg_relation_size(indexrelid)),
        idx_scan,
        idx_tup_read,
        idx_tup_fetch
    FROM pg_stat_user_indexes
    ORDER BY idx_scan DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to identify missing indexes
CREATE OR REPLACE FUNCTION suggest_missing_indexes()
RETURNS TABLE (
    table_name text,
    column_name text,
    query_count bigint
) AS $$
BEGIN
    -- Analyze pg_stat_statements for common WHERE clauses
    -- This is simplified - real implementation would parse queries
    RETURN QUERY
    SELECT
        schemaname || '.' || tablename,
        'Analyze queries manually',
        seq_scan
    FROM pg_stat_user_tables
    WHERE seq_scan > 1000
    ORDER BY seq_scan DESC;
END;
$$ LANGUAGE plpgsql;
```

### Index Bloat Detection

```sql
-- Check index bloat
CREATE OR REPLACE FUNCTION check_index_bloat()
RETURNS TABLE (
    index_name text,
    bloat_ratio numeric,
    wasted_bytes text,
    recommendation text
) AS $$
BEGIN
    RETURN QUERY
    WITH index_bloat AS (
        SELECT
            schemaname || '.' || tablename AS table_name,
            indexname,
            pg_relation_size(indexrelid) AS index_size,
            pg_stat_get_live_tuples(indexrelid) AS live_tuples,
            pg_stat_get_dead_tuples(indexrelid) AS dead_tuples
        FROM pg_stat_user_indexes
    )
    SELECT
        indexname::text,
        ROUND((dead_tuples::numeric / NULLIF(live_tuples, 0)) * 100, 2),
        pg_size_pretty((index_size * dead_tuples / NULLIF(live_tuples + dead_tuples, 1))::bigint),
        CASE
            WHEN dead_tuples > live_tuples * 0.2 THEN 'REINDEX RECOMMENDED'
            ELSE 'OK'
        END
    FROM index_bloat
    WHERE dead_tuples > 0
    ORDER BY dead_tuples DESC;
END;
$$ LANGUAGE plpgsql;
```

### Maintenance Schedule

```sql
-- Weekly maintenance
CREATE OR REPLACE FUNCTION weekly_index_maintenance()
RETURNS void AS $$
BEGIN
    -- Update statistics
    ANALYZE;

    -- Reindex bloated indexes
    FOR idx IN
        SELECT index_name
        FROM check_index_bloat()
        WHERE recommendation = 'REINDEX RECOMMENDED'
    LOOP
        EXECUTE format('REINDEX INDEX CONCURRENTLY %I', idx.index_name);
    END LOOP;

    -- Refresh materialized views
    REFRESH MATERIALIZED VIEW CONCURRENTLY hot_chunks;
END;
$$ LANGUAGE plpgsql;

-- Schedule with pg_cron
SELECT cron.schedule('weekly-index-maintenance', '0 2 * * 0',
    'SELECT weekly_index_maintenance()');
```

---

## 9. QUERY OPTIMIZATION EXAMPLES

### Spatial Range Query

```sql
-- Optimized spatial range query using indexes
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id, content, position_x, position_y, position_z
FROM chunks
WHERE
    space_id = 'uuid-here'
    AND position_cube <@ cube(ARRAY[-100, -100, -100, 100, 100, 100])
ORDER BY
    position_x, position_y, position_z
LIMIT 100;

-- Uses: idx_chunks_position_cube
-- Expected: Index scan, <10ms
```

### Semantic Similarity Search

```sql
-- Optimized vector similarity search
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id, content,
    1 - (embedding <=> $1::vector) as similarity
FROM chunks
WHERE
    space_id = $2
    AND embedding IS NOT NULL
ORDER BY embedding <=> $1::vector
LIMIT 20;

-- Uses: idx_chunks_embedding_ivfflat
-- Expected: Index scan, <50ms for 1M vectors
```

### Context Loading Query

```sql
-- Optimized context loading for agent
EXPLAIN (ANALYZE, BUFFERS)
WITH visible_chunks AS (
    SELECT chunk_id, distance
    FROM query_frustum_chunks(
        $1, $2, $3,  -- eye position
        $4, $5, $6,  -- look direction
        60, 1.77,    -- fov, aspect
        1, 100,      -- near, far
        $7           -- space_id
    )
    WHERE distance <= 100
)
SELECT
    c.id, c.content, c.tokens, c.type,
    vc.distance
FROM chunks c
JOIN visible_chunks vc ON c.id = vc.chunk_id
ORDER BY vc.distance
LIMIT 50;

-- Uses: Multiple indexes in combination
-- Expected: <100ms
```

---

## 10. PERFORMANCE TARGETS

### Index Performance Metrics

| Query Type | Target Latency | Index Used |
|------------|---------------|------------|
| Point lookup | <1ms | B-tree primary |
| Range scan | <10ms | B-tree composite |
| Spatial query | <50ms | GiST cube |
| Vector similarity | <100ms | IVFFlat |
| Full-text search | <50ms | GIN tsvector |
| JSONB query | <20ms | GIN jsonb_path_ops |

### Index Size Targets

```sql
-- Monitor index sizes
SELECT
    schemaname || '.' || tablename AS table,
    indexname,
    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) AS size,
    idx_scan as scans
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC;
```

Target: Total index size < 30% of table size

---

## SUCCESS METRICS

### Index Effectiveness
- 95% of queries use indexes
- <5% sequential scans
- Index hit rate >99%
- No unused indexes after 30 days

### Query Performance
- P50 latency <10ms
- P95 latency <100ms
- P99 latency <500ms
- Zero timeout queries

### Maintenance Health
- Index bloat <20%
- Statistics updated weekly
- No invalid indexes
- Automated maintenance running

---

**Total Indexes:** 50+ strategic indexes
**Index Types:** B-tree, Hash, GIN, GiST, IVFFlat, BRIN
**Maintenance:** Weekly automated optimization
**Monitoring:** Continuous performance tracking