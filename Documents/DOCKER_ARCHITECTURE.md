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

# Docker Container Architecture
**Infinite Spatial Context System**

---

## CONTAINER OVERVIEW

The Infinite system uses a fully containerized architecture with 7 primary containers orchestrated via Docker Compose. Each container has specific responsibilities and hardware affinity.

```yaml
# Container Architecture
infinite-system/
├── nginx-proxy         # Reverse proxy & load balancer
├── frontend-app        # 3D visualization (React/Three.js)
├── backend-api         # Core API server (Node.js/Express)
├── spatial-engine      # Memory indexing & streaming (Python)
├── ai-inference        # Model runtime (Python/llama.cpp)
├── postgres-db         # Metadata & configuration
└── redis-cache         # Session & real-time data
```

---

## 1. CONTAINER SPECIFICATIONS

### 1.1 nginx-proxy (Reverse Proxy)

**Purpose:** Route requests, handle SSL, serve static assets

**Base Image:** `nginx:alpine`

**Configuration:**
```dockerfile
FROM nginx:alpine

# Install dependencies
RUN apk add --no-cache openssl

# Generate self-signed cert for development
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/cert.key -out /etc/nginx/cert.crt \
    -subj "/C=US/ST=State/L=City/O=Infinite/CN=localhost"

# Copy configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

EXPOSE 80 443

HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1
```

**Environment Variables:**
```yaml
UPSTREAM_FRONTEND: frontend-app:3000
UPSTREAM_BACKEND: backend-api:4000
UPSTREAM_SPATIAL: spatial-engine:5000
RATE_LIMIT: 100r/m
CACHE_SIZE: 1g
```

**Volume Mounts:**
```yaml
volumes:
  - ./nginx/conf.d:/etc/nginx/conf.d:ro
  - ./nginx/certs:/etc/nginx/certs:ro
  - nginx-cache:/var/cache/nginx
```

**Resource Limits:**
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

### 1.2 frontend-app (3D Visualization)

**Purpose:** Render 3D memory palace, handle user interaction

**Base Image:** `node:20-alpine`

**Dockerfile:**
```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source and build
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.frontend.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --quiet --tries=1 --spider http://localhost:3000 || exit 1
```

**Environment Variables:**
```yaml
REACT_APP_API_URL: http://backend-api:4000
REACT_APP_WS_URL: ws://backend-api:4000
REACT_APP_SPATIAL_URL: http://spatial-engine:5000
RENDER_TARGET: webgpu  # or webgl2
GPU_PREFERENCE: integrated  # Use iGPU for rendering
```

**GPU Binding (iGPU):**
```yaml
devices:
  - /dev/dri/renderD128:/dev/dri/renderD128  # iGPU access
environment:
  - MESA_LOADER_DRIVER_OVERRIDE=radeonsi
  - DRI_PRIME=0  # Select integrated GPU
```

### 1.3 backend-api (Core API Server)

**Purpose:** Handle API requests, coordinate agents, manage sessions

**Base Image:** `node:20-alpine`

**Dockerfile:**
```dockerfile
FROM node:20-alpine

WORKDIR /app

# Install native dependencies
RUN apk add --no-cache python3 make g++

# Install Node.js dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy application
COPY . .

EXPOSE 4000

# Run with PM2 for process management
RUN npm install -g pm2
CMD ["pm2-runtime", "start", "ecosystem.config.js"]

HEALTHCHECK --interval=30s --timeout=3s \
  CMD node healthcheck.js || exit 1
```

**Environment Variables:**
```yaml
NODE_ENV: production
PORT: 4000
DATABASE_URL: postgresql://user:pass@postgres-db:5432/infinite
REDIS_URL: redis://redis-cache:6379
JWT_SECRET: ${JWT_SECRET}
SPATIAL_ENGINE_URL: http://spatial-engine:5000
AI_INFERENCE_URL: http://ai-inference:6000
MAX_AGENTS: 3
CONTEXT_WINDOW_SIZE: 8192
```

**Resource Allocation:**
```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G
    reservations:
      cpus: '2.0'
      memory: 2G
```

### 1.4 spatial-engine (Memory Indexing)

**Purpose:** Spatial indexing, embeddings, context streaming

**Base Image:** `python:3.11-slim`

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install NPU runtime
RUN pip install onnxruntime-amd

# Copy application
COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", \
     "--timeout", "120", "app:create_app()"]

HEALTHCHECK --interval=30s --timeout=5s \
  CMD python healthcheck.py || exit 1
```

**NPU Access Configuration:**
```yaml
devices:
  - /dev/xdna:/dev/xdna  # NPU device access
environment:
  - ONNX_RUNTIME_PROVIDER=VitisAI
  - NPU_ENABLED=true
  - EMBEDDING_MODEL=BGE-small-en-v1.5
  - EMBEDDING_BATCH_SIZE=32
  - VECTOR_DIMENSION=384
  - OCTREE_MAX_DEPTH=12
  - CHUNK_SIZE=400  # tokens per chunk
```

**Volume Mounts:**
```yaml
volumes:
  - ./models:/app/models:ro
  - spatial-index:/app/index
  - embeddings-cache:/app/cache
```

### 1.5 ai-inference (Model Runtime)

**Purpose:** Run AI models, handle inference requests

**Base Image:** `pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime`

**Dockerfile:**
```dockerfile
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install llama.cpp with CUDA support
RUN apt-get update && apt-get install -y \
    git cmake build-essential \
    && git clone https://github.com/ggerganov/llama.cpp \
    && cd llama.cpp \
    && mkdir build && cd build \
    && cmake .. -DLLAMA_CUDA=ON \
    && cmake --build . --config Release \
    && cd ../.. \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 6000

CMD ["python", "inference_server.py"]

HEALTHCHECK --interval=30s --timeout=10s \
  CMD python healthcheck.py || exit 1
```

**GPU Configuration (dGPU - RTX 5060):**
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
environment:
  - NVIDIA_VISIBLE_DEVICES=0
  - CUDA_VISIBLE_DEVICES=0
  - MODEL_PATH=/models
  - MAX_CONCURRENT_MODELS=3
  - DEFAULT_CONTEXT_LENGTH=8192
  - GPU_LAYERS=35  # Offload layers to GPU
  - MAIN_GPU=0
  - TENSOR_SPLIT=1.0  # Use full GPU
```

**Model Configuration:**
```yaml
models:
  - name: llama-8b
    path: /models/llama-2-8b.gguf
    context_length: 8192
    gpu_layers: 35
    threads: 4
  - name: mistral-7b
    path: /models/mistral-7b-instruct.gguf
    context_length: 32768
    gpu_layers: 32
    threads: 4
  - name: phi-3
    path: /models/phi-3-mini.gguf
    context_length: 4096
    gpu_layers: 24
    threads: 2
```

### 1.6 postgres-db (Metadata Storage)

**Purpose:** Store metadata, agent states, user data

**Base Image:** `postgres:16-alpine`

**Configuration:**
```yaml
postgres-db:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: infinite
    POSTGRES_USER: infinite_user
    POSTGRES_PASSWORD: ${DB_PASSWORD}
    POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.utf8"
  volumes:
    - postgres-data:/var/lib/postgresql/data
    - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
  ports:
    - "5432:5432"
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U infinite_user"]
    interval: 10s
    timeout: 5s
    retries: 5
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '1.0'
        memory: 1G
```

### 1.7 redis-cache (Cache & Pub/Sub)

**Purpose:** Session storage, real-time updates, caching

**Base Image:** `redis:7-alpine`

**Configuration:**
```yaml
redis-cache:
  image: redis:7-alpine
  command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
  volumes:
    - redis-data:/data
    - ./redis.conf:/usr/local/etc/redis/redis.conf:ro
  ports:
    - "6379:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 2G
      reservations:
        cpus: '0.5'
        memory: 512M
```

---

## 2. DOCKER COMPOSE ORCHESTRATION

### 2.1 Complete docker-compose.yml

```yaml
version: '3.9'

services:
  nginx-proxy:
    build: ./nginx
    container_name: infinite-nginx
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      frontend-app:
        condition: service_healthy
      backend-api:
        condition: service_healthy
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - nginx-cache:/var/cache/nginx
    networks:
      - frontend-net
      - backend-net
    restart: unless-stopped

  frontend-app:
    build: ./Frontend
    container_name: infinite-frontend
    environment:
      - REACT_APP_API_URL=http://backend-api:4000
      - RENDER_TARGET=webgpu
      - GPU_PREFERENCE=integrated
    devices:
      - /dev/dri/renderD128:/dev/dri/renderD128
    volumes:
      - ./Frontend/public:/app/public:ro
    networks:
      - frontend-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:3000"]
      interval: 30s
      timeout: 3s

  backend-api:
    build: ./Backend
    container_name: infinite-backend
    environment:
      - NODE_ENV=production
      - PORT=4000
      - DATABASE_URL=postgresql://infinite_user:${DB_PASSWORD}@postgres-db:5432/infinite
      - REDIS_URL=redis://redis-cache:6379
      - JWT_SECRET=${JWT_SECRET}
      - SPATIAL_ENGINE_URL=http://spatial-engine:5000
      - AI_INFERENCE_URL=http://ai-inference:6000
    depends_on:
      postgres-db:
        condition: service_healthy
      redis-cache:
        condition: service_healthy
    volumes:
      - ./Backend/uploads:/app/uploads
    networks:
      - frontend-net
      - backend-net
      - ai-net
    restart: unless-stopped

  spatial-engine:
    build: ./Backend/spatial
    container_name: infinite-spatial
    devices:
      - /dev/xdna:/dev/xdna
    environment:
      - ONNX_RUNTIME_PROVIDER=VitisAI
      - NPU_ENABLED=true
      - EMBEDDING_MODEL=BGE-small-en-v1.5
      - DATABASE_URL=postgresql://infinite_user:${DB_PASSWORD}@postgres-db:5432/infinite
      - REDIS_URL=redis://redis-cache:6379
    depends_on:
      postgres-db:
        condition: service_healthy
      redis-cache:
        condition: service_healthy
    volumes:
      - ./models/embeddings:/app/models:ro
      - spatial-index:/app/index
      - embeddings-cache:/app/cache
    networks:
      - backend-net
      - ai-net
    restart: unless-stopped

  ai-inference:
    build: ./Backend/inference
    container_name: infinite-ai
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=0
      - MODEL_PATH=/models
      - MAX_CONCURRENT_MODELS=3
      - DEFAULT_CONTEXT_LENGTH=8192
      - REDIS_URL=redis://redis-cache:6379
    volumes:
      - ./models/llm:/models:ro
      - model-cache:/root/.cache
    networks:
      - ai-net
    restart: unless-stopped

  postgres-db:
    image: postgres:16-alpine
    container_name: infinite-postgres
    environment:
      - POSTGRES_DB=infinite
      - POSTGRES_USER=infinite_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./Database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - backend-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U infinite_user"]
      interval: 10s
      timeout: 5s

  redis-cache:
    image: redis:7-alpine
    container_name: infinite-redis
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - backend-net
      - ai-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s

networks:
  frontend-net:
    driver: bridge
  backend-net:
    driver: bridge
    internal: true
  ai-net:
    driver: bridge
    internal: true

volumes:
  nginx-cache:
  postgres-data:
  redis-data:
  spatial-index:
  embeddings-cache:
  model-cache:
```

### 2.2 Network Architecture

**Three Isolated Networks:**

1. **frontend-net** (Public-facing)
   - nginx-proxy
   - frontend-app
   - backend-api

2. **backend-net** (Internal services)
   - backend-api
   - spatial-engine
   - postgres-db
   - redis-cache

3. **ai-net** (AI workloads)
   - spatial-engine (NPU access)
   - ai-inference (GPU access)
   - redis-cache (coordination)

### 2.3 Environment Configuration

> **⚠️ SECURITY WARNING**: Never use the placeholder values below in production!
> Replace ALL `CHANGE_ME_*` values with strong, randomly-generated secrets.
> See `.env.example` for secure secret generation commands.

**.env File:**
```env
# Database
DB_PASSWORD=CHANGE_ME_generate_32char_password_openssl_rand_hex_32
DB_ROOT_PASSWORD=CHANGE_ME_generate_32char_password_openssl_rand_hex_32

# Security
JWT_SECRET=CHANGE_ME_generate_256bit_secret_openssl_rand_base64_32
ENCRYPTION_KEY=your_encryption_key_here

# Redis
REDIS_PASSWORD=CHANGE_ME_never_use_default_redis_password

# NPU Configuration
NPU_DEVICE=/dev/xdna
ONNX_PROVIDERS=VitisAIExecutionProvider,CPUExecutionProvider

# GPU Configuration
CUDA_VISIBLE_DEVICES=0
GPU_MEMORY_FRACTION=0.95

# Model Paths
EMBEDDING_MODEL_PATH=/models/embeddings/bge-small-en-v1.5
LLM_MODEL_PATH=/models/llm

# Performance
WORKER_PROCESSES=4
MAX_CONNECTIONS=1000
CACHE_SIZE=2GB
```

---

## 3. CONTAINER COMMUNICATION

### 3.1 API Gateway Pattern

```
Client Request
     ↓
nginx-proxy (Port 80/443)
     ↓
Route based on path:
├─ /api/* → backend-api:4000
├─ /spatial/* → spatial-engine:5000
├─ /ws/* → backend-api:4000 (WebSocket)
└─ /* → frontend-app:3000
```

### 3.2 Service Discovery

All services communicate via Docker's internal DNS:
- `postgres-db` resolves to PostgreSQL container
- `redis-cache` resolves to Redis container
- `spatial-engine` resolves to spatial indexing service
- `ai-inference` resolves to model runtime

### 3.3 Health Checks

Every container implements health checks:
```yaml
healthcheck:
  test: [custom health check command]
  interval: 30s     # Check every 30 seconds
  timeout: 5s       # Timeout after 5 seconds
  retries: 3        # Mark unhealthy after 3 failures
  start_period: 60s # Grace period for startup
```

---

## 4. DEVELOPMENT VS PRODUCTION

### 4.1 Development Overrides

**docker-compose.dev.yml:**
```yaml
version: '3.9'

services:
  frontend-app:
    build:
      context: ./Frontend
      target: development
    volumes:
      - ./Frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - REACT_APP_DEBUG=true
    command: npm start

  backend-api:
    build:
      context: ./Backend
      target: development
    volumes:
      - ./Backend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - DEBUG=true
    command: npm run dev

  postgres-db:
    ports:
      - "5432:5432"  # Expose for debugging

  redis-cache:
    ports:
      - "6379:6379"  # Expose for debugging
```

**Usage:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 4.2 Production Optimizations

**docker-compose.prod.yml:**
```yaml
version: '3.9'

services:
  nginx-proxy:
    image: infinite/nginx:latest
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s

  backend-api:
    image: infinite/backend:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s

  ai-inference:
    deploy:
      placement:
        constraints:
          - node.labels.gpu == true
```

---

## 5. DEPLOYMENT COMMANDS

### 5.1 Build & Start

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### 5.2 Scaling

```bash
# Scale backend API
docker-compose up -d --scale backend-api=3

# Scale AI inference
docker-compose up -d --scale ai-inference=2
```

### 5.3 Maintenance

```bash
# Backup database
docker exec infinite-postgres pg_dump -U infinite_user infinite > backup.sql

# Restore database
docker exec -i infinite-postgres psql -U infinite_user infinite < backup.sql

# Clear Redis cache
docker exec infinite-redis redis-cli FLUSHALL

# Update single service
docker-compose up -d --no-deps --build backend-api
```

---

## 6. MONITORING & LOGGING

### 6.1 Prometheus Metrics

Add Prometheus container:
```yaml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus-data:/prometheus
  ports:
    - "9090:9090"
  networks:
    - backend-net
```

### 6.2 Grafana Dashboards

Add Grafana container:
```yaml
grafana:
  image: grafana/grafana:latest
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  volumes:
    - grafana-data:/var/lib/grafana
    - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
  ports:
    - "3001:3000"
  networks:
    - backend-net
```

### 6.3 Log Aggregation

Use Docker's logging driver:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service"
```

---

## CONCLUSION

This Docker architecture provides:
- **Isolation:** Each service in its own container
- **Scalability:** Easy horizontal scaling
- **Hardware Optimization:** GPU/NPU access where needed
- **Security:** Network isolation, secrets management
- **Development Efficiency:** Hot reload in dev mode
- **Production Readiness:** Health checks, resource limits, logging

The containerized approach ensures consistent deployment across environments while maximizing hardware utilization for the revolutionary spatial context system.