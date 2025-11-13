# Infrastructure Architecture
**Supporting Services for Infinite Spatial Context System**

---

> **⚠️ SECURITY NOTICE**: This document contains example configurations with placeholder values.
> All IP addresses, network ranges, passwords, and secrets shown are examples only.
> Replace with your actual production values. Never use default or example values in production.

---

## OVERVIEW

The infrastructure layer provides essential services that enable the spatial context system to function efficiently. This includes nginx routing, Redis caching, monitoring, logging, and performance optimization.

---

## 1. NGINX REVERSE PROXY

### 1.1 Core Configuration

**nginx.conf:**
```nginx
user nginx;
worker_processes auto;
worker_cpu_affinity auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

# Optimize for high throughput
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format with timing information
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript
               application/x-javascript application/json
               application/xml application/rss+xml
               application/javascript application/wasm;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=ai_limit:10m rate=10r/m;
    limit_req_zone $binary_remote_addr zone=spatial_limit:10m rate=50r/m;

    # Connection limiting
    limit_conn_zone $binary_remote_addr zone=addr:10m;

    # Cache configuration
    proxy_cache_path /var/cache/nginx/api levels=1:2
                     keys_zone=api_cache:10m max_size=1g
                     inactive=60m use_temp_path=off;

    proxy_cache_path /var/cache/nginx/static levels=1:2
                     keys_zone=static_cache:10m max_size=10g
                     inactive=7d use_temp_path=off;

    # Upstream definitions
    upstream frontend {
        least_conn;
        server frontend-app:3000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    upstream backend {
        least_conn;
        server backend-api:4000 max_fails=3 fail_timeout=30s;
        keepalive 64;
    }

    upstream spatial {
        least_conn;
        server spatial-engine:5000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    upstream ai {
        least_conn;
        server ai-inference:6000 max_fails=3 fail_timeout=30s;
        keepalive 16;
    }

    # Include site configurations
    include /etc/nginx/conf.d/*.conf;
}
```

### 1.2 Site Configuration

**conf.d/default.conf:**
```nginx
server {
    listen 80;
    listen [::]:80;
    server_name localhost;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name localhost;

    # SSL Configuration
    ssl_certificate /etc/nginx/certs/cert.crt;
    ssl_certificate_key /etc/nginx/certs/cert.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!RC4:!DHE;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        limit_conn addr 10;

        proxy_pass http://backend/;
        proxy_http_version 1.1;

        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Caching for GET requests
        proxy_cache api_cache;
        proxy_cache_methods GET HEAD;
        proxy_cache_valid 200 1m;
        proxy_cache_key "$scheme$request_method$host$request_uri";
        proxy_cache_use_stale error timeout invalid_header updating http_500 http_502 http_503 http_504;
        add_header X-Cache-Status $upstream_cache_status;
    }

    # WebSocket support for real-time updates
    location /ws/ {
        proxy_pass http://backend/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # WebSocket timeouts
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Spatial engine endpoints
    location /spatial/ {
        limit_req zone=spatial_limit burst=10 nodelay;

        proxy_pass http://spatial/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Longer timeouts for spatial operations
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # AI inference endpoints
    location /ai/ {
        limit_req zone=ai_limit burst=5 nodelay;

        proxy_pass http://ai/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Long timeouts for AI inference
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;

        # Disable buffering for streaming responses
        proxy_buffering off;
    }

    # Static assets with aggressive caching
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";

        # Enable gzip for static files
        gzip_static on;
    }

    # 3D assets (models, textures)
    location /assets/ {
        alias /usr/share/nginx/html/assets/;
        expires 7d;
        add_header Cache-Control "public";

        # CORS for 3D assets
        add_header Access-Control-Allow-Origin "*";
    }

    # Frontend app
    location / {
        proxy_pass http://frontend/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Cache static resources
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|wasm)$ {
            proxy_pass http://frontend;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

    # Health check endpoint
    location /health {
        access_log off;
        add_header Content-Type text/plain;
        return 200 "healthy\n";
    }

    # Metrics endpoint (internal only)
    location /metrics {
        allow 172.16.0.0/12;  # Docker network
        deny all;

        stub_status on;
        access_log off;
    }
}
```

---

## 2. REDIS CACHE ARCHITECTURE

### 2.1 Redis Configuration

**redis.conf:**
```conf
# Network
bind 0.0.0.0
protected-mode yes
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300

# General
daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""
databases 16

# Snapshotting
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data

# Replication
replica-read-only yes

# Security
requirepass ${REDIS_PASSWORD}

# Limits
maxclients 10000
maxmemory 2gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Append only mode
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Lua scripting
lua-time-limit 5000

# Cluster
cluster-enabled no

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Event notification
notify-keyspace-events ""

# Advanced config
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
```

### 2.2 Redis Usage Patterns

**Data Structures & Use Cases:**

1. **Session Storage**
```javascript
// Store user session
await redis.setex(
  `session:${sessionId}`,
  3600, // 1 hour TTL
  JSON.stringify({
    userId,
    agentPositions,
    contextState
  })
);
```

2. **Agent Coordination**
```javascript
// Agent state management
await redis.hset('agents', agentId, JSON.stringify({
  model: 'llama-8b',
  position: { x: 100, y: 50, z: 200 },
  contextWindow: { current: 6420, max: 8192 },
  status: 'active'
}));

// Publish agent movement
await redis.publish('agent:movement', JSON.stringify({
  agentId,
  from: oldPosition,
  to: newPosition
}));
```

3. **Context Caching**
```javascript
// Cache loaded context chunks
await redis.zadd(
  `context:${agentId}`,
  Date.now(), // Score is timestamp
  JSON.stringify(chunk)
);

// Expire old context
await redis.zremrangebyscore(
  `context:${agentId}`,
  0,
  Date.now() - 300000 // 5 minutes
);
```

4. **Semantic Search Cache**
```javascript
// Cache embedding results
await redis.setex(
  `embedding:${hash(text)}`,
  86400, // 24 hour TTL
  JSON.stringify(embedding)
);

// Cache search results
await redis.setex(
  `search:${query}`,
  300, // 5 minute TTL
  JSON.stringify(results)
);
```

5. **Rate Limiting**
```javascript
// Implement sliding window rate limiting
const key = `ratelimit:${userId}:${endpoint}`;
const now = Date.now();
const window = 60000; // 1 minute

await redis.zadd(key, now, `${now}-${requestId}`);
await redis.zremrangebyscore(key, 0, now - window);
const count = await redis.zcard(key);
await redis.expire(key, 60);

if (count > limit) {
  throw new Error('Rate limit exceeded');
}
```

6. **Real-time Updates**
```javascript
// Pub/Sub for real-time coordination
// Publisher
await redis.publish('spatial:updates', JSON.stringify({
  type: 'chunk_loaded',
  agentId,
  chunkId,
  position
}));

// Subscriber
redis.subscribe('spatial:updates');
redis.on('message', (channel, message) => {
  const update = JSON.parse(message);
  // Handle real-time update
});
```

---

## 3. POSTGRESQL CONFIGURATION

### 3.1 Database Schema

**init.sql:**
```sql
-- Create database
CREATE DATABASE infinite;
\c infinite;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    root_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Memory chunks table
CREATE TABLE memory_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    content TEXT NOT NULL,
    tokens INTEGER NOT NULL,
    position_x REAL NOT NULL,
    position_y REAL NOT NULL,
    position_z REAL NOT NULL,
    embedding VECTOR(384),  -- Requires pgvector extension
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    model VARCHAR(50) NOT NULL,
    position_x REAL DEFAULT 0,
    position_y REAL DEFAULT 0,
    position_z REAL DEFAULT 0,
    context_state JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent history table
CREATE TABLE agent_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    position_x REAL NOT NULL,
    position_y REAL NOT NULL,
    position_z REAL NOT NULL,
    action VARCHAR(50) NOT NULL,
    context_summary TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Spatial index table
CREATE TABLE spatial_index (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    node_level INTEGER NOT NULL,
    min_x REAL NOT NULL,
    min_y REAL NOT NULL,
    min_z REAL NOT NULL,
    max_x REAL NOT NULL,
    max_y REAL NOT NULL,
    max_z REAL NOT NULL,
    chunk_ids UUID[] DEFAULT '{}',
    child_nodes UUID[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Create indexes
CREATE INDEX idx_memory_chunks_project ON memory_chunks(project_id);
CREATE INDEX idx_memory_chunks_position ON memory_chunks(position_x, position_y, position_z);
CREATE INDEX idx_memory_chunks_embedding ON memory_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_agents_project ON agents(project_id);
CREATE INDEX idx_agent_history_agent ON agent_history(agent_id);
CREATE INDEX idx_agent_history_timestamp ON agent_history(timestamp);
CREATE INDEX idx_spatial_index_project ON spatial_index(project_id);
CREATE INDEX idx_spatial_index_bounds ON spatial_index(min_x, min_y, min_z, max_x, max_y, max_z);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token);

-- Create update trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memory_chunks_updated_at BEFORE UPDATE ON memory_chunks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 3.2 Performance Tuning

**postgresql.conf optimizations:**
```conf
# Memory
shared_buffers = 512MB
effective_cache_size = 1536MB
maintenance_work_mem = 128MB
work_mem = 4MB

# Checkpoint
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1

# Connection pooling
max_connections = 200
superuser_reserved_connections = 3

# Logging
log_min_duration_statement = 100
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 0

# Autovacuum
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 30s
```

---

## 4. MONITORING STACK

### 4.1 Prometheus Configuration

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files:
  - "alerts.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'backend-api'
    static_configs:
      - targets: ['backend-api:4000']
    metrics_path: '/metrics'

  - job_name: 'spatial-engine'
    static_configs:
      - targets: ['spatial-engine:5000']
    metrics_path: '/metrics'

  - job_name: 'ai-inference'
    static_configs:
      - targets: ['ai-inference:6000']
    metrics_path: '/metrics'
```

### 4.2 Alert Rules

**alerts.yml:**
```yaml
groups:
  - name: infinite_alerts
    interval: 30s
    rules:
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 90% (current value: {{ $value }})"

      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% (current value: {{ $value }})"

      - alert: PostgresDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"
          description: "PostgreSQL database is not responding"

      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"
          description: "Redis cache is not responding"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time"
          description: "95th percentile response time is above 1 second"

      - alert: LowGPUMemory
        expr: nvidia_gpu_memory_free_bytes / nvidia_gpu_memory_total_bytes < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low GPU memory"
          description: "GPU memory usage is above 90%"
```

### 4.3 Grafana Dashboards

**Dashboard Configuration (JSON):**
```json
{
  "dashboard": {
    "title": "Infinite Spatial Context System",
    "panels": [
      {
        "title": "System Overview",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Context Loading Performance",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 0 },
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(context_load_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Agent Activity",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 8 },
        "targets": [
          {
            "expr": "sum(agents_active)",
            "legendFormat": "Active Agents"
          }
        ]
      },
      {
        "title": "GPU/NPU Utilization",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 8 },
        "targets": [
          {
            "expr": "nvidia_gpu_utilization",
            "legendFormat": "GPU %"
          },
          {
            "expr": "npu_utilization",
            "legendFormat": "NPU %"
          }
        ]
      }
    ]
  }
}
```

---

## 5. LOGGING ARCHITECTURE

### 5.1 Centralized Logging with ELK Stack

**docker-compose.logging.yml:**
```yaml
version: '3.9'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - xpack.security.enabled=false
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    networks:
      - logging-net

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline:ro
    networks:
      - logging-net
      - backend-net

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    networks:
      - logging-net

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - logging-net

networks:
  logging-net:
    driver: bridge
```

### 5.2 Log Aggregation Pipeline

**logstash/pipeline/logstash.conf:**
```ruby
input {
  beats {
    port => 5044
  }
}

filter {
  if [docker][container][name] =~ /infinite-/ {
    grok {
      match => {
        "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}"
      }
    }

    mutate {
      add_field => {
        "service" => "%{[docker][container][name]}"
      }
    }

    if [service] == "infinite-ai" {
      grok {
        match => {
          "message" => "tokens/sec: %{NUMBER:tokens_per_sec:float}"
        }
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "infinite-%{+YYYY.MM.dd}"
  }
}
```

---

## 6. SECURITY INFRASTRUCTURE

### 6.1 Network Security

**Firewall Rules (iptables):**
```bash
# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow SSH (restrict to your trusted network CIDR - replace example)
iptables -A INPUT -p tcp --dport 22 -s YOUR_TRUSTED_NETWORK_CIDR -j ACCEPT

# Docker networks (standard Docker CIDR range)
iptables -A INPUT -s 172.16.0.0/12 -j ACCEPT
```

### 6.2 SSL/TLS Configuration

**Generate production certificates:**
```bash
# Using Let's Encrypt
certbot certonly --standalone \
  -d infinite.example.com \
  --agree-tos \
  --email admin@example.com
```

### 6.3 Secrets Management

> **⚠️ SECURITY**: Replace example values with actual secrets from secure source.
> Never use "strong_password" or "redis_password" in production!

**Docker secrets:**
```bash
# Create secrets (use actual generated secrets, not these placeholders!)
echo "CHANGE_ME_generate_with_openssl_rand_hex_32" | docker secret create db_password -
echo "CHANGE_ME_generate_with_openssl_rand_base64_32" | docker secret create jwt_secret -
echo "CHANGE_ME_generate_with_openssl_rand_hex_32" | docker secret create redis_password -

# Use in docker-compose
services:
  backend-api:
    secrets:
      - db_password
      - jwt_secret
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password
      JWT_SECRET_FILE: /run/secrets/jwt_secret
```

---

## 7. BACKUP & DISASTER RECOVERY

### 7.1 Automated Backups

**backup.sh:**
```bash
#!/bin/bash

BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
docker exec infinite-postgres pg_dumpall -U postgres > "$BACKUP_DIR/postgres.sql"

# Backup Redis
docker exec infinite-redis redis-cli --rdb "$BACKUP_DIR/redis.rdb"

# Backup volumes
docker run --rm \
  -v infinite_spatial-index:/data \
  -v "$BACKUP_DIR":/backup \
  alpine tar czf /backup/spatial-index.tar.gz -C /data .

# Upload to S3 (optional)
aws s3 sync "$BACKUP_DIR" "s3://infinite-backups/$(date +%Y%m%d_%H%M%S)/"

# Clean old backups (keep 30 days)
find /backups -mtime +30 -delete
```

**Cron job:**
```cron
0 2 * * * /opt/infinite/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### 7.2 Restore Procedures

**restore.sh:**
```bash
#!/bin/bash

BACKUP_PATH="$1"

# Stop services
docker-compose down

# Restore PostgreSQL
docker-compose up -d postgres-db
docker exec -i infinite-postgres psql -U postgres < "$BACKUP_PATH/postgres.sql"

# Restore Redis
docker-compose up -d redis-cache
docker exec infinite-redis redis-cli --pipe < "$BACKUP_PATH/redis.rdb"

# Restore volumes
docker run --rm \
  -v infinite_spatial-index:/data \
  -v "$BACKUP_PATH":/backup \
  alpine tar xzf /backup/spatial-index.tar.gz -C /data

# Start all services
docker-compose up -d
```

---

## CONCLUSION

This infrastructure architecture provides:
- **High Performance:** Optimized nginx, Redis caching, connection pooling
- **Reliability:** Health checks, monitoring, alerting
- **Security:** SSL/TLS, network isolation, secrets management
- **Observability:** Centralized logging, metrics, dashboards
- **Resilience:** Automated backups, disaster recovery procedures

The infrastructure layer ensures the Infinite spatial context system operates efficiently, securely, and reliably at scale.