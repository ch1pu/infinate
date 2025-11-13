# INFINITE: Database Migrations Plan
**Schema Evolution and Version Control Strategy**

---

## EXECUTIVE SUMMARY

This document defines the comprehensive migration strategy for Infinite's database, including initial schema creation, version control, rollback procedures, and data transformation patterns for maintaining database integrity through application evolution.

---

## 1. MIGRATION ARCHITECTURE

### Migration Framework

```typescript
// Using Prisma Migrate with custom extensions
interface MigrationSystem {
  framework: 'Prisma Migrate';
  customRunner: 'TypeScript migration scripts';
  versionControl: 'Sequential numbering + timestamps';
  rollbackSupport: 'Full forward and backward migrations';
  dataValidation: 'Pre and post migration checks';
}
```

### Migration File Structure

```
database/
├── migrations/
│   ├── 001_initial_schema/
│   │   ├── migration.sql
│   │   ├── up.ts           # Custom logic
│   │   ├── down.ts         # Rollback logic
│   │   └── validate.ts     # Validation
│   ├── 002_add_embeddings/
│   ├── 003_add_spatial_index/
│   └── current_schema.prisma
├── seeds/
│   ├── development.ts
│   ├── test.ts
│   └── production.ts
└── scripts/
    ├── backup.ts
    ├── restore.ts
    └── validate.ts
```

---

## 2. INITIAL MIGRATION (001)

### Core Tables Creation

```sql
-- 001_initial_schema/migration.sql

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,

    profile JSONB DEFAULT '{}',
    roles TEXT[] DEFAULT ARRAY['user'],
    permissions TEXT[] DEFAULT ARRAY[]::TEXT[],

    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    requires_2fa BOOLEAN DEFAULT false,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    token_hash TEXT NOT NULL UNIQUE,
    refresh_token_hash TEXT,

    device_id VARCHAR(255),
    device_info JSONB DEFAULT '{}',
    ip_address INET,

    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_sessions_user_id (user_id),
    INDEX idx_sessions_token_hash (token_hash),
    INDEX idx_sessions_expires_at (expires_at)
);

-- Memory spaces table
CREATE TABLE memory_spaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id),

    config JSONB DEFAULT '{
        "chunk_size": 300,
        "chunk_overlap": 50,
        "embedding_model": "bge-small-en-v1.5"
    }',

    bounds JSONB DEFAULT '{
        "min": {"x": -1000, "y": -500, "z": -1000},
        "max": {"x": 1000, "y": 500, "z": 1000}
    }',

    metadata JSONB DEFAULT '{}',
    stats JSONB DEFAULT '{
        "total_chunks": 0,
        "total_tokens": 0,
        "total_size_bytes": 0
    }',

    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_memory_spaces_owner_id (owner_id),
    INDEX idx_memory_spaces_name (name)
);

-- Chunks table
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    space_id UUID NOT NULL REFERENCES memory_spaces(id) ON DELETE CASCADE,

    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,

    tokens INTEGER NOT NULL,
    token_ids INTEGER[],

    type VARCHAR(50) NOT NULL CHECK (type IN ('code', 'documentation', 'conversation', 'data')),
    language VARCHAR(50),

    position_x REAL NOT NULL,
    position_y REAL NOT NULL,
    position_z REAL NOT NULL,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,

    INDEX idx_chunks_space_id (space_id),
    INDEX idx_chunks_position (position_x, position_y, position_z),
    INDEX idx_chunks_type (type),
    INDEX idx_chunks_content_hash (content_hash)
);

-- Agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    space_id UUID NOT NULL REFERENCES memory_spaces(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    model VARCHAR(100) NOT NULL,

    config JSONB DEFAULT '{
        "temperature": 0.7,
        "max_tokens": 2000,
        "context_window": 8192
    }',

    position_x REAL DEFAULT 0,
    position_y REAL DEFAULT 0,
    position_z REAL DEFAULT 0,

    orientation JSONB DEFAULT '{"yaw": 0, "pitch": 0, "roll": 0}',
    view_frustum JSONB DEFAULT '{
        "fov": 60,
        "near": 1,
        "far": 100
    }',

    context_state JSONB DEFAULT '{
        "loaded_chunks": [],
        "tokens_used": 0
    }',

    status VARCHAR(50) DEFAULT 'idle' CHECK (status IN ('idle', 'loading', 'active', 'error')),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_agents_user_id (user_id),
    INDEX idx_agents_space_id (space_id),
    INDEX idx_agents_status (status)
);

-- Queries table
CREATE TABLE queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    query_text TEXT NOT NULL,
    query_type VARCHAR(50),

    response TEXT,
    response_tokens INTEGER,

    context_chunks UUID[],

    processing_time_ms INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_queries_agent_id (agent_id),
    INDEX idx_queries_user_id (user_id),
    INDEX idx_queries_created_at (created_at)
);

-- Audit logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    actor_type VARCHAR(50) NOT NULL,
    actor_id VARCHAR(255) NOT NULL,
    actor_ip INET,

    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),

    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failure')),

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_audit_logs_actor (actor_type, actor_id),
    INDEX idx_audit_logs_resource (resource_type, resource_id),
    INDEX idx_audit_logs_created_at (created_at)
);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memory_spaces_updated_at BEFORE UPDATE ON memory_spaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chunks_updated_at BEFORE UPDATE ON chunks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Migration Validation Script

```typescript
// 001_initial_schema/validate.ts
export async function validate(db: Database): Promise<ValidationResult> {
  const checks: Check[] = [];

  // Check all tables exist
  const requiredTables = [
    'users', 'sessions', 'memory_spaces',
    'chunks', 'agents', 'queries', 'audit_logs'
  ];

  for (const table of requiredTables) {
    const exists = await db.tableExists(table);
    checks.push({
      name: `Table ${table} exists`,
      passed: exists,
      critical: true
    });
  }

  // Check indexes
  const requiredIndexes = [
    'idx_sessions_user_id',
    'idx_chunks_space_id',
    'idx_chunks_position'
  ];

  for (const index of requiredIndexes) {
    const exists = await db.indexExists(index);
    checks.push({
      name: `Index ${index} exists`,
      passed: exists,
      critical: false
    });
  }

  // Check triggers
  const triggerExists = await db.triggerExists('update_users_updated_at');
  checks.push({
    name: 'Updated_at triggers exist',
    passed: triggerExists,
    critical: false
  });

  return {
    passed: checks.every(c => !c.critical || c.passed),
    checks
  };
}
```

---

## 3. VECTOR EMBEDDINGS MIGRATION (002)

### Add pgvector Extension

```sql
-- 002_add_embeddings/migration.sql

-- Enable pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to chunks
ALTER TABLE chunks
ADD COLUMN embedding vector(384);

-- Create specialized embeddings table for different models
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,

    model VARCHAR(100) NOT NULL,
    dimensions INTEGER NOT NULL,
    embedding vector(1536), -- Max dimensions for flexibility

    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(chunk_id, model),
    INDEX idx_embeddings_chunk_id (chunk_id),
    INDEX idx_embeddings_model (model)
);

-- Create vector similarity search index
CREATE INDEX idx_chunks_embedding_cosine ON chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Function for semantic search
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding vector(384),
    space_id UUID,
    limit_count INTEGER DEFAULT 10,
    min_similarity FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    similarity FLOAT,
    position_x REAL,
    position_y REAL,
    position_z REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.content,
        1 - (c.embedding <=> query_embedding) as similarity,
        c.position_x,
        c.position_y,
        c.position_z
    FROM chunks c
    WHERE
        c.space_id = search_similar_chunks.space_id
        AND c.embedding IS NOT NULL
        AND 1 - (c.embedding <=> query_embedding) >= min_similarity
    ORDER BY c.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
```

### Data Migration Script

```typescript
// 002_add_embeddings/up.ts
export async function up(db: Database): Promise<void> {
  // Get all chunks without embeddings
  const chunks = await db.query(`
    SELECT id, content
    FROM chunks
    WHERE embedding IS NULL
    LIMIT 1000
  `);

  // Generate embeddings in batches
  const batchSize = 32;
  for (let i = 0; i < chunks.length; i += batchSize) {
    const batch = chunks.slice(i, i + batchSize);

    // Generate embeddings using NPU/GPU
    const embeddings = await generateEmbeddings(
      batch.map(c => c.content)
    );

    // Update chunks with embeddings
    for (let j = 0; j < batch.length; j++) {
      await db.query(`
        UPDATE chunks
        SET embedding = $1::vector
        WHERE id = $2
      `, [embeddings[j], batch[j].id]);
    }

    console.log(`Processed ${i + batch.length}/${chunks.length} chunks`);
  }
}

export async function down(db: Database): Promise<void> {
  // Remove embedding columns
  await db.query(`
    ALTER TABLE chunks DROP COLUMN IF EXISTS embedding;
    DROP TABLE IF EXISTS embeddings;
    DROP EXTENSION IF EXISTS vector;
  `);
}
```

---

## 4. SPATIAL INDEXING MIGRATION (003)

### Add Spatial Index Tables

```sql
-- 003_add_spatial_index/migration.sql

-- Octree nodes table
CREATE TABLE octree_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    space_id UUID NOT NULL REFERENCES memory_spaces(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES octree_nodes(id) ON DELETE CASCADE,

    level INTEGER NOT NULL,
    octant INTEGER CHECK (octant >= 0 AND octant <= 7),

    bounds_min_x REAL NOT NULL,
    bounds_min_y REAL NOT NULL,
    bounds_min_z REAL NOT NULL,
    bounds_max_x REAL NOT NULL,
    bounds_max_y REAL NOT NULL,
    bounds_max_z REAL NOT NULL,

    chunk_ids UUID[] DEFAULT ARRAY[]::UUID[],
    chunk_count INTEGER DEFAULT 0,

    is_leaf BOOLEAN DEFAULT true,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_octree_nodes_space_id (space_id),
    INDEX idx_octree_nodes_parent_id (parent_id),
    INDEX idx_octree_nodes_level (level),
    INDEX idx_octree_nodes_bounds (bounds_min_x, bounds_min_y, bounds_min_z,
                                   bounds_max_x, bounds_max_y, bounds_max_z)
);

-- Spatial relationships table
CREATE TABLE chunk_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    related_chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,

    relationship_type VARCHAR(50) NOT NULL,
    strength FLOAT DEFAULT 0.5,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(chunk_id, related_chunk_id, relationship_type),
    INDEX idx_chunk_relationships_chunk_id (chunk_id),
    INDEX idx_chunk_relationships_related_chunk_id (related_chunk_id),
    INDEX idx_chunk_relationships_type (relationship_type)
);

-- Function for frustum query
CREATE OR REPLACE FUNCTION query_frustum_chunks(
    eye_x REAL, eye_y REAL, eye_z REAL,
    look_x REAL, look_y REAL, look_z REAL,
    fov REAL, aspect REAL,
    near_plane REAL, far_plane REAL,
    space_id UUID
)
RETURNS TABLE (
    chunk_id UUID,
    distance REAL,
    in_frustum BOOLEAN
) AS $$
DECLARE
    -- Frustum plane equations will be calculated here
BEGIN
    -- Simplified frustum test (would need full implementation)
    RETURN QUERY
    SELECT
        c.id as chunk_id,
        sqrt(
            power(c.position_x - eye_x, 2) +
            power(c.position_y - eye_y, 2) +
            power(c.position_z - eye_z, 2)
        ) as distance,
        true as in_frustum -- Simplified, would need actual frustum test
    FROM chunks c
    WHERE
        c.space_id = query_frustum_chunks.space_id
        AND sqrt(
            power(c.position_x - eye_x, 2) +
            power(c.position_y - eye_y, 2) +
            power(c.position_z - eye_z, 2)
        ) <= far_plane
    ORDER BY distance;
END;
$$ LANGUAGE plpgsql;

-- Add spatial clustering info
ALTER TABLE memory_spaces
ADD COLUMN spatial_index JSONB DEFAULT '{
    "type": "octree",
    "max_depth": 8,
    "max_items_per_node": 8
}';
```

---

## 5. PERFORMANCE OPTIMIZATION MIGRATION (004)

### Add Performance Tables

```sql
-- 004_performance_optimization/migration.sql

-- Chunk access patterns table
CREATE TABLE chunk_access_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,

    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    access_type VARCHAR(50),
    context_size INTEGER,

    INDEX idx_chunk_access_patterns_chunk_id (chunk_id),
    INDEX idx_chunk_access_patterns_agent_id (agent_id),
    INDEX idx_chunk_access_patterns_accessed_at (accessed_at)
);

-- Query cache table
CREATE TABLE query_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    query_hash VARCHAR(64) NOT NULL UNIQUE,
    query_text TEXT NOT NULL,

    result JSONB NOT NULL,
    result_chunks UUID[],

    hit_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    INDEX idx_query_cache_query_hash (query_hash),
    INDEX idx_query_cache_expires_at (expires_at)
);

-- Performance metrics table
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),

    tags JSONB DEFAULT '{}',

    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_performance_metrics_name (metric_name),
    INDEX idx_performance_metrics_recorded_at (recorded_at),
    INDEX idx_performance_metrics_tags (tags)
);

-- Add materialized view for hot chunks
CREATE MATERIALIZED VIEW hot_chunks AS
SELECT
    c.id,
    c.space_id,
    c.content,
    c.position_x,
    c.position_y,
    c.position_z,
    c.embedding,
    COUNT(cap.id) as access_count,
    MAX(cap.accessed_at) as last_accessed
FROM chunks c
JOIN chunk_access_patterns cap ON c.id = cap.chunk_id
WHERE cap.accessed_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
GROUP BY c.id
HAVING COUNT(cap.id) > 5
ORDER BY COUNT(cap.id) DESC;

CREATE INDEX idx_hot_chunks_space_id ON hot_chunks(space_id);
CREATE INDEX idx_hot_chunks_access_count ON hot_chunks(access_count);

-- Refresh materialized view every 5 minutes
CREATE OR REPLACE FUNCTION refresh_hot_chunks()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY hot_chunks;
END;
$$ LANGUAGE plpgsql;
```

---

## 6. MIGRATION EXECUTION STRATEGY

### Migration Runner

```typescript
class MigrationRunner {
  private db: Database;
  private migrations: Migration[];

  async run(): Promise<void> {
    // Check current version
    const currentVersion = await this.getCurrentVersion();

    // Get pending migrations
    const pending = this.migrations.filter(m => m.version > currentVersion);

    if (pending.length === 0) {
      console.log('Database is up to date');
      return;
    }

    for (const migration of pending) {
      await this.executeMigration(migration);
    }
  }

  private async executeMigration(migration: Migration): Promise<void> {
    const transaction = await this.db.beginTransaction();

    try {
      console.log(`Running migration ${migration.version}: ${migration.name}`);

      // Pre-migration backup
      await this.createBackup(`before_${migration.version}`);

      // Run validation
      const preValidation = await migration.validatePre(this.db);
      if (!preValidation.passed) {
        throw new Error(`Pre-validation failed: ${preValidation.message}`);
      }

      // Execute SQL
      await transaction.execute(migration.sql);

      // Execute custom logic
      if (migration.up) {
        await migration.up(transaction);
      }

      // Post-validation
      const postValidation = await migration.validatePost(transaction);
      if (!postValidation.passed) {
        throw new Error(`Post-validation failed: ${postValidation.message}`);
      }

      // Update version
      await transaction.execute(`
        INSERT INTO migration_history (version, name, executed_at)
        VALUES ($1, $2, $3)
      `, [migration.version, migration.name, new Date()]);

      await transaction.commit();
      console.log(`Migration ${migration.version} completed successfully`);

    } catch (error) {
      await transaction.rollback();
      console.error(`Migration ${migration.version} failed:`, error);

      // Attempt rollback
      if (migration.down) {
        await this.rollback(migration);
      }

      throw error;
    }
  }

  private async rollback(migration: Migration): Promise<void> {
    console.log(`Rolling back migration ${migration.version}`);

    const transaction = await this.db.beginTransaction();

    try {
      if (migration.down) {
        await migration.down(transaction);
      }

      await transaction.execute(`
        DELETE FROM migration_history
        WHERE version = $1
      `, [migration.version]);

      await transaction.commit();
      console.log(`Rollback completed for migration ${migration.version}`);

    } catch (error) {
      await transaction.rollback();
      console.error(`Rollback failed for migration ${migration.version}:`, error);
      throw error;
    }
  }
}
```

---

## 7. DATA MIGRATION PATTERNS

### Large Table Migration

```typescript
async function migrateLargeTable(
  source: string,
  destination: string,
  batchSize: number = 1000
): Promise<void> {
  let offset = 0;
  let hasMore = true;

  while (hasMore) {
    // Read batch
    const batch = await db.query(`
      SELECT * FROM ${source}
      ORDER BY id
      LIMIT ${batchSize}
      OFFSET ${offset}
    `);

    if (batch.length === 0) {
      hasMore = false;
      break;
    }

    // Transform and insert
    const transformed = batch.map(transformRow);
    await db.batchInsert(destination, transformed);

    offset += batchSize;

    // Progress reporting
    console.log(`Migrated ${offset} rows`);

    // Prevent overload
    await delay(100);
  }
}
```

### Zero-Downtime Migration

```typescript
async function zeroDowntimeMigration(): Promise<void> {
  // Step 1: Add new column with default
  await db.execute(`
    ALTER TABLE chunks
    ADD COLUMN new_field TEXT DEFAULT 'default_value'
  `);

  // Step 2: Backfill in batches
  await backfillColumn('chunks', 'new_field', calculateValue);

  // Step 3: Add NOT NULL constraint after backfill
  await db.execute(`
    ALTER TABLE chunks
    ALTER COLUMN new_field SET NOT NULL
  `);

  // Step 4: Remove default
  await db.execute(`
    ALTER TABLE chunks
    ALTER COLUMN new_field DROP DEFAULT
  `);
}
```

---

## 8. TESTING MIGRATIONS

### Migration Test Suite

```typescript
describe('Migration Tests', () => {
  let testDb: Database;

  beforeEach(async () => {
    // Create test database
    testDb = await createTestDatabase();
  });

  afterEach(async () => {
    // Clean up
    await dropTestDatabase(testDb);
  });

  test('Migration 001 creates all tables', async () => {
    const runner = new MigrationRunner(testDb);
    await runner.runMigration('001');

    const tables = await testDb.getTables();
    expect(tables).toContain('users');
    expect(tables).toContain('chunks');
    expect(tables).toContain('agents');
  });

  test('Migration rollback works', async () => {
    const runner = new MigrationRunner(testDb);

    await runner.runMigration('002');
    const before = await testDb.tableExists('embeddings');
    expect(before).toBe(true);

    await runner.rollback('002');
    const after = await testDb.tableExists('embeddings');
    expect(after).toBe(false);
  });

  test('Data migration preserves integrity', async () => {
    // Insert test data
    await testDb.insert('chunks', testChunks);

    // Run migration
    await runner.runMigration('002');

    // Verify data integrity
    const chunks = await testDb.query('SELECT * FROM chunks');
    expect(chunks).toHaveLength(testChunks.length);
    chunks.forEach(chunk => {
      expect(chunk.embedding).toBeDefined();
    });
  });
});
```

---

## 9. PRODUCTION MIGRATION CHECKLIST

### Before Migration
- [ ] Full database backup completed
- [ ] Migration tested on staging
- [ ] Rollback plan documented
- [ ] Maintenance window scheduled
- [ ] Team notified

### During Migration
- [ ] Application in maintenance mode
- [ ] Migration script running
- [ ] Progress monitored
- [ ] Validation checks passing
- [ ] Performance metrics normal

### After Migration
- [ ] Application health checked
- [ ] Query performance validated
- [ ] Rollback unnecessary
- [ ] Monitoring alerts configured
- [ ] Documentation updated

---

## 10. MIGRATION SCHEDULE

### Phase 1: Foundation (Week 1)
- Migration 001: Initial schema
- Migration 002: Vector embeddings
- Migration 003: Spatial indexing

### Phase 2: Optimization (Week 2)
- Migration 004: Performance tables
- Migration 005: Indexes optimization
- Migration 006: Materialized views

### Phase 3: Features (Week 3)
- Migration 007: Multi-tenancy
- Migration 008: Versioning support
- Migration 009: Advanced search

### Phase 4: Scaling (Week 4)
- Migration 010: Partitioning
- Migration 011: Sharding preparation
- Migration 012: Archive tables

---

## SUCCESS METRICS

### Migration Performance
- Each migration <5 minutes
- Zero data loss
- Rollback possible within 1 minute
- 100% validation pass rate

### Database Performance
- Query latency <50ms p95
- Index usage >90%
- No table scans in hot paths
- Connection pool optimized

---

**Total Migrations Planned:** 12
**Rollback Support:** Full
**Testing Coverage:** 100%
**Production Ready:** Week 4