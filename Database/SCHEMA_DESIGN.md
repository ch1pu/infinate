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

# Database Schema Design
**Spatial Storage & Metadata Management**

---

## OVERVIEW

The database layer provides persistent storage for spatial indices, memory chunks, agent states, and system metadata. PostgreSQL serves as the primary database with pgvector extension for semantic search capabilities.

---

## 1. DATABASE ARCHITECTURE

### 1.1 Technology Stack

- **PostgreSQL 16** - Primary database
- **pgvector** - Vector similarity search
- **PostGIS** - Spatial data operations (optional)
- **TimescaleDB** - Time-series data (optional for metrics)
- **Redis** - Cache layer (separate from main DB)

### 1.2 Database Design Principles

1. **Normalized Schema** - 3NF for data integrity
2. **Spatial Indexing** - Optimized for 3D coordinate queries
3. **Vector Search** - Semantic similarity via pgvector
4. **JSONB Flexibility** - Metadata storage without schema changes
5. **Audit Trail** - Track all agent movements and context changes

---

## 2. CORE TABLES

### 2.1 Users & Authentication

```sql
-- Users table: Core user accounts
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,

    -- Account status
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    verification_token TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,

    -- Settings
    preferences JSONB DEFAULT '{}',

    CONSTRAINT email_valid CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Sessions table: Active user sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    refresh_token TEXT UNIQUE,

    -- Session data
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Client info
    ip_address INET,
    user_agent TEXT,
    device_id VARCHAR(255),

    CONSTRAINT token_not_empty CHECK (token != '')
);

-- API keys table: For programmatic access
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash TEXT NOT NULL,
    last_used TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    scopes TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, name)
);
```

### 2.2 Projects & Organization

```sql
-- Projects table: Container for memory spaces
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Basic info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    root_path TEXT NOT NULL,

    -- Configuration
    language VARCHAR(50) DEFAULT 'mixed',
    framework VARCHAR(100),

    -- Space boundaries
    space_min_x REAL DEFAULT -1000,
    space_min_y REAL DEFAULT -100,
    space_min_z REAL DEFAULT -1000,
    space_max_x REAL DEFAULT 1000,
    space_max_y REAL DEFAULT 100,
    space_max_z REAL DEFAULT 1000,

    -- Statistics
    total_chunks INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_files INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_indexed TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',

    CONSTRAINT name_not_empty CHECK (name != ''),
    UNIQUE(user_id, name)
);

-- Project collaborators: Share projects with other users
CREATE TABLE project_collaborators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    permissions JSONB DEFAULT '{}',
    invited_by UUID REFERENCES users(id),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(project_id, user_id),
    CONSTRAINT valid_role CHECK (role IN ('viewer', 'editor', 'admin'))
);
```

### 2.3 Memory Storage

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Memory chunks table: Core content storage
CREATE TABLE memory_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- File reference
    file_path TEXT NOT NULL,
    file_type VARCHAR(50),
    language VARCHAR(50),

    -- Content
    content TEXT NOT NULL,
    tokens INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL, -- Position within file
    total_chunks INTEGER NOT NULL, -- Total chunks in file

    -- Spatial position
    position_x REAL NOT NULL,
    position_y REAL NOT NULL,
    position_z REAL NOT NULL,

    -- Semantic embedding (384 dimensions for BGE-small)
    embedding vector(384),

    -- Relationships
    parent_chunk_id UUID REFERENCES memory_chunks(id),
    related_chunks UUID[] DEFAULT '{}',
    imports TEXT[] DEFAULT '{}', -- Files this chunk imports
    exports TEXT[] DEFAULT '{}', -- What this chunk exports

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    CONSTRAINT tokens_positive CHECK (tokens > 0)
);

-- File metadata: Track complete files
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- File info
    path TEXT NOT NULL,
    name VARCHAR(255) NOT NULL,
    extension VARCHAR(50),
    size_bytes BIGINT,

    -- Content stats
    total_lines INTEGER,
    total_tokens INTEGER,
    chunk_count INTEGER DEFAULT 0,

    -- File hashes for change detection
    content_hash VARCHAR(64), -- SHA256
    structure_hash VARCHAR(64), -- For AST changes

    -- Timestamps
    file_created TIMESTAMP WITH TIME ZONE,
    file_modified TIMESTAMP WITH TIME ZONE,
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_checked TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Dependencies
    dependencies TEXT[] DEFAULT '{}',
    dependents TEXT[] DEFAULT '{}',

    UNIQUE(project_id, path)
);
```

### 2.4 Spatial Indexing

```sql
-- Octree nodes: Spatial index structure
CREATE TABLE octree_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Node hierarchy
    parent_id UUID REFERENCES octree_nodes(id) ON DELETE CASCADE,
    node_level INTEGER NOT NULL,
    octant_index INTEGER, -- 0-7 for which child of parent

    -- Bounding box
    min_x REAL NOT NULL,
    min_y REAL NOT NULL,
    min_z REAL NOT NULL,
    max_x REAL NOT NULL,
    max_y REAL NOT NULL,
    max_z REAL NOT NULL,

    -- Node data
    is_leaf BOOLEAN DEFAULT true,
    chunk_ids UUID[] DEFAULT '{}',
    child_ids UUID[] DEFAULT '{}',

    -- Statistics
    total_chunks INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    CONSTRAINT level_non_negative CHECK (node_level >= 0),
    CONSTRAINT octant_valid CHECK (octant_index IS NULL OR octant_index BETWEEN 0 AND 7)
);

-- Spatial regions: Named areas in 3D space
CREATE TABLE spatial_regions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Region info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    region_type VARCHAR(50), -- 'district', 'zone', 'cluster'

    -- Bounding box or sphere
    shape VARCHAR(20) NOT NULL DEFAULT 'box',
    center_x REAL,
    center_y REAL,
    center_z REAL,
    radius REAL,
    min_x REAL,
    min_y REAL,
    min_z REAL,
    max_x REAL,
    max_y REAL,
    max_z REAL,

    -- Visual properties
    color VARCHAR(7), -- Hex color
    icon VARCHAR(50),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    CONSTRAINT shape_valid CHECK (shape IN ('box', 'sphere')),
    UNIQUE(project_id, name)
);
```

### 2.5 Agent Management

```sql
-- Agents table: AI model instances
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Agent identity
    name VARCHAR(255) NOT NULL,
    model VARCHAR(50) NOT NULL,
    avatar_url TEXT,
    color VARCHAR(7), -- Hex color for visualization

    -- Current state
    position_x REAL DEFAULT 0,
    position_y REAL DEFAULT 0,
    position_z REAL DEFAULT 0,
    orientation REAL DEFAULT 0, -- Rotation in radians

    -- Movement
    target_x REAL,
    target_y REAL,
    target_z REAL,
    movement_speed REAL DEFAULT 10.0,
    is_moving BOOLEAN DEFAULT false,

    -- Context window
    context_window_size INTEGER DEFAULT 8192,
    context_tokens_used INTEGER DEFAULT 0,
    loaded_chunk_ids UUID[] DEFAULT '{}',

    -- Status
    status VARCHAR(20) DEFAULT 'idle',
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- State persistence
    context_state JSONB DEFAULT '{}',
    memory_state JSONB DEFAULT '{}',

    CONSTRAINT model_valid CHECK (model IN ('llama-8b', 'mistral-7b', 'phi-3', 'codellama-7b')),
    CONSTRAINT status_valid CHECK (status IN ('idle', 'thinking', 'moving', 'loading', 'generating'))
);

-- Agent history: Track all agent actions
CREATE TABLE agent_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,

    -- Position at time of action
    position_x REAL NOT NULL,
    position_y REAL NOT NULL,
    position_z REAL NOT NULL,

    -- Action details
    action_type VARCHAR(50) NOT NULL,
    action_data JSONB DEFAULT '{}',

    -- Context snapshot
    context_size INTEGER,
    loaded_chunks INTEGER,
    relevant_files TEXT[],

    -- Query/Response for inference actions
    query TEXT,
    response TEXT,
    tokens_generated INTEGER,
    generation_time_ms INTEGER,

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT action_type_valid CHECK (
        action_type IN (
            'created', 'moved', 'teleported', 'queried',
            'context_loaded', 'context_streamed', 'generated_response'
        )
    )
);

-- Agent tasks: Queue of tasks for agents
CREATE TABLE agent_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,

    -- Task details
    task_type VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 5,
    payload JSONB NOT NULL,

    -- Status
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,

    -- Results
    result JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT priority_valid CHECK (priority BETWEEN 1 AND 10),
    CONSTRAINT status_valid CHECK (
        status IN ('pending', 'running', 'completed', 'failed', 'cancelled')
    )
);
```

### 2.6 Semantic Search

```sql
-- Embedding cache: Store computed embeddings
CREATE TABLE embedding_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Text reference
    text_hash VARCHAR(64) PRIMARY KEY, -- SHA256 of text
    text_preview TEXT, -- First 200 chars

    -- Embedding
    model VARCHAR(50) NOT NULL,
    embedding vector(384),

    -- Usage stats
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    use_count INTEGER DEFAULT 1,

    -- TTL
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Search history: Track searches for analytics
CREATE TABLE search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Search details
    query TEXT NOT NULL,
    search_type VARCHAR(20) NOT NULL,

    -- Results
    result_count INTEGER,
    top_result_id UUID,
    clicked_result_id UUID,

    -- Performance
    search_time_ms INTEGER,

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT search_type_valid CHECK (search_type IN ('semantic', 'keyword', 'spatial'))
);
```

### 2.7 Metrics & Analytics

```sql
-- System metrics: Performance tracking
CREATE TABLE system_metrics (
    time TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Resource usage
    cpu_usage REAL,
    memory_usage REAL,
    gpu_usage REAL,
    npu_usage REAL,

    -- Performance metrics
    active_agents INTEGER,
    total_chunks_loaded INTEGER,
    context_switches_per_minute INTEGER,
    inference_requests_per_minute INTEGER,
    avg_inference_time_ms REAL,

    -- Database metrics
    db_connections INTEGER,
    db_query_time_ms REAL,
    cache_hit_ratio REAL
);

-- Create hypertable if using TimescaleDB
-- SELECT create_hypertable('system_metrics', 'time');

-- User activity: Track user interactions
CREATE TABLE user_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Activity details
    activity_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,

    -- Additional data
    details JSONB DEFAULT '{}',

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. INDEXES

### 3.1 Primary Indexes

```sql
-- User indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- Project indexes
CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_project_collaborators_project ON project_collaborators(project_id);
CREATE INDEX idx_project_collaborators_user ON project_collaborators(user_id);

-- Memory chunk indexes
CREATE INDEX idx_memory_chunks_project ON memory_chunks(project_id);
CREATE INDEX idx_memory_chunks_file ON memory_chunks(project_id, file_path);
CREATE INDEX idx_memory_chunks_position ON memory_chunks(position_x, position_y, position_z);
CREATE INDEX idx_memory_chunks_last_accessed ON memory_chunks(last_accessed);

-- Vector similarity index (using IVFFlat for pgvector)
CREATE INDEX idx_memory_chunks_embedding ON memory_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100); -- Adjust lists parameter based on data size

-- Octree indexes
CREATE INDEX idx_octree_nodes_project ON octree_nodes(project_id);
CREATE INDEX idx_octree_nodes_parent ON octree_nodes(parent_id);
CREATE INDEX idx_octree_nodes_bounds ON octree_nodes(
    project_id, min_x, min_y, min_z, max_x, max_y, max_z
);

-- Agent indexes
CREATE INDEX idx_agents_project ON agents(project_id);
CREATE INDEX idx_agents_status ON agents(status) WHERE is_active = true;
CREATE INDEX idx_agent_history_agent ON agent_history(agent_id);
CREATE INDEX idx_agent_history_timestamp ON agent_history(timestamp DESC);
CREATE INDEX idx_agent_tasks_agent ON agent_tasks(agent_id);
CREATE INDEX idx_agent_tasks_status ON agent_tasks(status) WHERE status IN ('pending', 'running');

-- Search indexes
CREATE INDEX idx_search_history_user ON search_history(user_id);
CREATE INDEX idx_search_history_project ON search_history(project_id);
CREATE INDEX idx_search_history_timestamp ON search_history(timestamp DESC);
```

### 3.2 Full-Text Search Indexes

```sql
-- Enable pg_trgm for fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Full-text search on content
ALTER TABLE memory_chunks ADD COLUMN content_tsv tsvector;
UPDATE memory_chunks SET content_tsv = to_tsvector('english', content);
CREATE INDEX idx_memory_chunks_content_fts ON memory_chunks USING gin(content_tsv);

-- Trigger to update tsvector on insert/update
CREATE OR REPLACE FUNCTION update_content_tsv() RETURNS trigger AS $$
BEGIN
    NEW.content_tsv := to_tsvector('english', NEW.content);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_content_tsv
BEFORE INSERT OR UPDATE ON memory_chunks
FOR EACH ROW EXECUTE FUNCTION update_content_tsv();

-- Trigram indexes for fuzzy search
CREATE INDEX idx_memory_chunks_file_path_trgm ON memory_chunks USING gin(file_path gin_trgm_ops);
CREATE INDEX idx_projects_name_trgm ON projects USING gin(name gin_trgm_ops);
```

---

## 4. FUNCTIONS & PROCEDURES

### 4.1 Spatial Query Functions

```sql
-- Function to find chunks within a sphere
CREATE OR REPLACE FUNCTION find_chunks_in_sphere(
    p_project_id UUID,
    p_center_x REAL,
    p_center_y REAL,
    p_center_z REAL,
    p_radius REAL
)
RETURNS TABLE(
    id UUID,
    distance REAL,
    content TEXT,
    tokens INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        mc.id,
        SQRT(
            POWER(mc.position_x - p_center_x, 2) +
            POWER(mc.position_y - p_center_y, 2) +
            POWER(mc.position_z - p_center_z, 2)
        ) AS distance,
        mc.content,
        mc.tokens
    FROM memory_chunks mc
    WHERE mc.project_id = p_project_id
        AND SQRT(
            POWER(mc.position_x - p_center_x, 2) +
            POWER(mc.position_y - p_center_y, 2) +
            POWER(mc.position_z - p_center_z, 2)
        ) <= p_radius
    ORDER BY distance;
END;
$$ LANGUAGE plpgsql;

-- Function to find chunks in frustum (simplified)
CREATE OR REPLACE FUNCTION find_chunks_in_frustum(
    p_project_id UUID,
    p_position_x REAL,
    p_position_y REAL,
    p_position_z REAL,
    p_direction_x REAL,
    p_direction_y REAL,
    p_direction_z REAL,
    p_fov REAL,
    p_near REAL,
    p_far REAL
)
RETURNS TABLE(id UUID, distance REAL) AS $$
DECLARE
    v_cos_half_fov REAL;
BEGIN
    v_cos_half_fov := COS(RADIANS(p_fov / 2));

    RETURN QUERY
    SELECT
        mc.id,
        SQRT(
            POWER(mc.position_x - p_position_x, 2) +
            POWER(mc.position_y - p_position_y, 2) +
            POWER(mc.position_z - p_position_z, 2)
        ) AS distance
    FROM memory_chunks mc
    WHERE mc.project_id = p_project_id
        -- Distance check
        AND SQRT(
            POWER(mc.position_x - p_position_x, 2) +
            POWER(mc.position_y - p_position_y, 2) +
            POWER(mc.position_z - p_position_z, 2)
        ) BETWEEN p_near AND p_far
        -- Simplified cone check (would need proper frustum math)
    ORDER BY distance;
END;
$$ LANGUAGE plpgsql;
```

### 4.2 Semantic Search Functions

```sql
-- Function for semantic similarity search
CREATE OR REPLACE FUNCTION semantic_search(
    p_project_id UUID,
    p_query_embedding vector(384),
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    id UUID,
    file_path TEXT,
    content TEXT,
    similarity REAL,
    position_x REAL,
    position_y REAL,
    position_z REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        mc.id,
        mc.file_path,
        mc.content,
        1 - (mc.embedding <=> p_query_embedding) AS similarity,
        mc.position_x,
        mc.position_y,
        mc.position_z
    FROM memory_chunks mc
    WHERE mc.project_id = p_project_id
        AND mc.embedding IS NOT NULL
    ORDER BY mc.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Hybrid search combining semantic and keyword
CREATE OR REPLACE FUNCTION hybrid_search(
    p_project_id UUID,
    p_query_text TEXT,
    p_query_embedding vector(384),
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    id UUID,
    file_path TEXT,
    content TEXT,
    score REAL
) AS $$
BEGIN
    RETURN QUERY
    WITH semantic_results AS (
        SELECT
            mc.id,
            1 - (mc.embedding <=> p_query_embedding) AS semantic_score
        FROM memory_chunks mc
        WHERE mc.project_id = p_project_id
            AND mc.embedding IS NOT NULL
    ),
    keyword_results AS (
        SELECT
            mc.id,
            ts_rank(mc.content_tsv, plainto_tsquery('english', p_query_text)) AS keyword_score
        FROM memory_chunks mc
        WHERE mc.project_id = p_project_id
            AND mc.content_tsv @@ plainto_tsquery('english', p_query_text)
    )
    SELECT
        mc.id,
        mc.file_path,
        mc.content,
        COALESCE(sr.semantic_score * 0.7, 0) + COALESCE(kr.keyword_score * 0.3, 0) AS score
    FROM memory_chunks mc
    LEFT JOIN semantic_results sr ON mc.id = sr.id
    LEFT JOIN keyword_results kr ON mc.id = kr.id
    WHERE mc.project_id = p_project_id
        AND (sr.id IS NOT NULL OR kr.id IS NOT NULL)
    ORDER BY score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
```

### 4.3 Agent Management Functions

```sql
-- Update agent context window
CREATE OR REPLACE FUNCTION update_agent_context(
    p_agent_id UUID,
    p_chunk_ids UUID[],
    p_tokens_used INTEGER
)
RETURNS VOID AS $$
BEGIN
    UPDATE agents
    SET
        loaded_chunk_ids = p_chunk_ids,
        context_tokens_used = p_tokens_used,
        last_active = CURRENT_TIMESTAMP
    WHERE id = p_agent_id;

    -- Update last_accessed for chunks
    UPDATE memory_chunks
    SET
        last_accessed = CURRENT_TIMESTAMP,
        access_count = access_count + 1
    WHERE id = ANY(p_chunk_ids);
END;
$$ LANGUAGE plpgsql;

-- Record agent movement
CREATE OR REPLACE FUNCTION record_agent_movement(
    p_agent_id UUID,
    p_new_x REAL,
    p_new_y REAL,
    p_new_z REAL,
    p_action_type VARCHAR(50) DEFAULT 'moved'
)
RETURNS VOID AS $$
DECLARE
    v_old_position RECORD;
BEGIN
    -- Get current position
    SELECT position_x, position_y, position_z
    INTO v_old_position
    FROM agents
    WHERE id = p_agent_id;

    -- Update agent position
    UPDATE agents
    SET
        position_x = p_new_x,
        position_y = p_new_y,
        position_z = p_new_z,
        last_active = CURRENT_TIMESTAMP
    WHERE id = p_agent_id;

    -- Record in history
    INSERT INTO agent_history (
        agent_id,
        position_x,
        position_y,
        position_z,
        action_type,
        action_data
    ) VALUES (
        p_agent_id,
        p_new_x,
        p_new_y,
        p_new_z,
        p_action_type,
        jsonb_build_object(
            'from', jsonb_build_object(
                'x', v_old_position.position_x,
                'y', v_old_position.position_y,
                'z', v_old_position.position_z
            ),
            'to', jsonb_build_object(
                'x', p_new_x,
                'y', p_new_y,
                'z', p_new_z
            )
        )
    );
END;
$$ LANGUAGE plpgsql;
```

---

## 5. TRIGGERS

### 5.1 Update Triggers

```sql
-- Auto-update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all relevant tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_memory_chunks_updated_at
    BEFORE UPDATE ON memory_chunks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### 5.2 Statistics Triggers

```sql
-- Update project statistics when chunks change
CREATE OR REPLACE FUNCTION update_project_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE projects
        SET
            total_chunks = total_chunks + 1,
            total_tokens = total_tokens + NEW.tokens
        WHERE id = NEW.project_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE projects
        SET
            total_chunks = total_chunks - 1,
            total_tokens = total_tokens - OLD.tokens
        WHERE id = OLD.project_id;
    ELSIF TG_OP = 'UPDATE' AND NEW.tokens != OLD.tokens THEN
        UPDATE projects
        SET total_tokens = total_tokens - OLD.tokens + NEW.tokens
        WHERE id = NEW.project_id;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_project_stats_trigger
AFTER INSERT OR UPDATE OR DELETE ON memory_chunks
FOR EACH ROW EXECUTE FUNCTION update_project_stats();
```

---

## 6. PERFORMANCE OPTIMIZATION

### 6.1 Partitioning Strategy

```sql
-- Partition agent_history by month for better performance
CREATE TABLE agent_history_2024_01 PARTITION OF agent_history
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE agent_history_2024_02 PARTITION OF agent_history
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Auto-create partitions (requires pg_partman extension)
```

### 6.2 Query Optimization

```sql
-- Materialized view for frequently accessed project stats
CREATE MATERIALIZED VIEW project_statistics AS
SELECT
    p.id,
    p.name,
    COUNT(DISTINCT mc.file_path) AS file_count,
    COUNT(mc.id) AS chunk_count,
    SUM(mc.tokens) AS total_tokens,
    AVG(mc.tokens) AS avg_tokens_per_chunk,
    MAX(mc.updated_at) AS last_updated
FROM projects p
LEFT JOIN memory_chunks mc ON p.id = mc.project_id
GROUP BY p.id, p.name;

CREATE UNIQUE INDEX idx_project_statistics_id ON project_statistics(id);

-- Refresh periodically
CREATE OR REPLACE FUNCTION refresh_project_statistics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY project_statistics;
END;
$$ LANGUAGE plpgsql;
```

### 6.3 Connection Pooling

```sql
-- Connection pool settings (in postgresql.conf)
-- max_connections = 200
-- shared_buffers = 512MB
-- effective_cache_size = 2GB
-- work_mem = 4MB
-- maintenance_work_mem = 128MB

-- Monitor connections
CREATE VIEW active_connections AS
SELECT
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query,
    query_start
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start DESC;
```

---

## 7. BACKUP & MAINTENANCE

### 7.1 Backup Strategy

```sql
-- Backup script (run via cron)
-- pg_dump -U postgres -d infinite -F custom -f backup_$(date +%Y%m%d).dump

-- Point-in-time recovery setup
-- archive_mode = on
-- archive_command = 'test ! -f /backup/wal/%f && cp %p /backup/wal/%f'
```

### 7.2 Maintenance Tasks

```sql
-- Vacuum and analyze schedule
CREATE OR REPLACE FUNCTION perform_maintenance()
RETURNS void AS $$
BEGIN
    -- Vacuum analyze main tables
    VACUUM ANALYZE memory_chunks;
    VACUUM ANALYZE agents;
    VACUUM ANALYZE agent_history;

    -- Reindex if needed
    REINDEX INDEX idx_memory_chunks_embedding;

    -- Update statistics
    ANALYZE;
END;
$$ LANGUAGE plpgsql;

-- Clean old sessions
CREATE OR REPLACE FUNCTION clean_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP;
    DELETE FROM embedding_cache WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;
```

---

## CONCLUSION

This database schema provides:
- **Efficient spatial queries** via custom functions and indexes
- **Vector similarity search** using pgvector
- **Complete audit trail** of agent actions
- **Flexible metadata storage** via JSONB
- **Optimized performance** through proper indexing and partitioning
- **Scalability** for millions of memory chunks

The schema supports the revolutionary spatial context system while maintaining data integrity and query performance.