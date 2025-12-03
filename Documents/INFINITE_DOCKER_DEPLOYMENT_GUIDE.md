# Infinite Docker Deployment Guide

**Project:** Infinite Spatial AI System
**Domain:** infinite.alphadeploy.org
**Owner:** Adolfo Lopez (ch1pu) - United States Navy Veteran
**Last Updated:** December 2, 2025
**Status:** Ready for implementation (after M1.6/M1.7 complete)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Infrastructure Components](#infrastructure-components)
3. [Docker Compose Configuration](#docker-compose-configuration)
4. [Nginx Configuration](#nginx-configuration)
5. [Cloudflare Tunnel Setup](#cloudflare-tunnel-setup)
6. [Environment Variables](#environment-variables)
7. [Deployment Steps](#deployment-steps)
8. [Monitoring & Health Checks](#monitoring--health-checks)

---

## Architecture Overview

Based on your existing project patterns (RSH, budget, AgentInvest), here's the Infinite deployment architecture:

```
Internet (HTTPS)
    ↓
Cloudflare Tunnel (infinite.alphadeploy.org)
    ↓
Nginx Reverse Proxy (port 80)
    ↓
    ├─→ Frontend (React + Three.js, port 3000)
    │   └─ 3D visualization UI
    │
    └─→ Backend (Python FastAPI, port 8000)
        ├─ Spatial Engine API
        └─ Vector Store Integration
            ├─ PostgreSQL + pgvector (port 5432)
            ├─ Qdrant (port 6333)
            └─ Redis (port 6379)
```

### Key Design Principles (From Your Projects)

✅ **Follows RSH Pattern:**
- Cloudflare Tunnel for public access
- Nginx reverse proxy
- Health checks on all services
- Resource limits on containers

✅ **Follows Budget Pattern:**
- Simple nginx.conf structure
- Frontend/backend upstreams
- WebSocket support (for real-time updates)

✅ **Follows AgentInvest Pattern:**
- Multiple databases (PostgreSQL, Redis)
- Healthchecks on all services
- Volume persistence
- Docker network isolation

---

## Infrastructure Components

### 1. PostgreSQL + pgvector

**Purpose:** Primary database with vector similarity search

**Image:** `pgvector/pgvector:pg15`

**Features:**
- pgvector extension for spatial indexing
- Stores token metadata
- Vector similarity queries

### 2. Qdrant

**Purpose:** High-performance vector database

**Image:** `qdrant/qdrant:latest`

**Features:**
- Fast k-NN search
- HNSW indexing
- REST API

### 3. Redis

**Purpose:** Caching layer

**Image:** `redis:7-alpine`

**Features:**
- Session caching
- Query result caching
- Real-time pub/sub

### 4. Backend (Python FastAPI)

**Purpose:** Spatial engine API

**Tech Stack:**
- Python 3.11
- FastAPI
- PyTorch (spatial attention)
- Spatial engine (`/home/ch1pu/infinate/backend/spatial_engine/`)

### 5. Frontend (React + Three.js)

**Purpose:** 3D visualization UI

**Tech Stack:**
- React 18
- Three.js + React Three Fiber
- TypeScript
- Vite

### 6. Nginx

**Purpose:** Reverse proxy and load balancer

**Image:** `nginx:alpine`

**Routes:**
- `/` → Frontend
- `/api/` → Backend API
- `/ws` → WebSocket (real-time updates)

### 7. Cloudflared

**Purpose:** Expose app via Cloudflare Tunnel

**Image:** `cloudflare/cloudflared:latest`

**Features:**
- Auto HTTPS
- DDoS protection
- No port forwarding needed

---

## Docker Compose Configuration

### Full docker-compose.yml

Create `/home/ch1pu/infinate/docker-compose.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL with pgvector extension
  postgres:
    image: pgvector/pgvector:pg15
    container_name: infinite-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-infinite}
      POSTGRES_USER: ${POSTGRES_USER:-infinite_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change_me_in_production}
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "127.0.0.1:5432:5432"  # Bind to localhost only for security
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - infinite-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-infinite_user} -d ${POSTGRES_DB:-infinite}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  # Qdrant vector database
  qdrant:
    image: qdrant/qdrant:latest
    container_name: infinite-qdrant
    restart: unless-stopped
    ports:
      - "127.0.0.1:6333:6333"  # Bind to localhost only
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - infinite-network
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:6333/healthz"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  # Redis cache
  redis:
    image: redis:7-alpine
    container_name: infinite-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD:-change_me_in_production} --maxmemory 256mb --maxmemory-policy allkeys-lru --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - infinite-network
    # Port removed - Redis accessible only within Docker network for security
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M

  # Python backend (FastAPI + spatial engine)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: infinite-backend
    restart: unless-stopped
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    environment:
      - POSTGRES_URL=postgresql://${POSTGRES_USER:-infinite_user}:${POSTGRES_PASSWORD:-change_me_in_production}@postgres:5432/${POSTGRES_DB:-infinite}
      - QDRANT_URL=http://qdrant:6333
      - REDIS_URL=redis://:${REDIS_PASSWORD:-change_me_in_production}@redis:6379
      - API_SECRET_KEY=${API_SECRET_KEY:-change_me_in_production}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-https://infinite.alphadeploy.org}
      - ENVIRONMENT=${ENVIRONMENT:-development}
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - infinite-network
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  # React frontend (development mode with HMR)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: infinite-frontend
    restart: unless-stopped
    command: npm run dev -- --host 0.0.0.0
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=/api
      - VITE_WS_URL=/ws
    depends_on:
      - backend
    networks:
      - infinite-network
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: infinite-nginx
    restart: unless-stopped
    ports:
      - "0.0.0.0:80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - backend
    networks:
      - infinite-network
    deploy:
      resources:
        limits:
          cpus: '0.25'
          memory: 128M
        reservations:
          cpus: '0.1'
          memory: 64M

  # Cloudflare Tunnel (exposes app via infinite.alphadeploy.org)
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: infinite-cloudflared
    restart: unless-stopped
    command: tunnel --no-autoupdate run
    environment:
      - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    depends_on:
      - nginx
    networks:
      - infinite-network
    deploy:
      resources:
        limits:
          cpus: '0.25'
          memory: 128M
        reservations:
          cpus: '0.1'
          memory: 64M

volumes:
  postgres_data:
    driver: local
  qdrant_data:
    driver: local
  redis_data:
    driver: local

networks:
  infinite-network:
    driver: bridge
```

### Production docker-compose.prod.yml

For production deployment (optimized builds):

```yaml
version: '3.8'

services:
  # ... (same postgres, qdrant, redis, cloudflared as above)

  # Production backend (optimized)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: infinite-backend
    restart: unless-stopped
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    environment:
      - POSTGRES_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - QDRANT_URL=http://qdrant:6333
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - API_SECRET_KEY=${API_SECRET_KEY}
      - ALLOWED_ORIGINS=https://infinite.alphadeploy.org
      - ENVIRONMENT=production
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - infinite-network
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '2.0'
          memory: 2G

  # Production frontend (static build served by nginx)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: infinite-frontend
    restart: unless-stopped
    depends_on:
      - backend
    networks:
      - infinite-network
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M

  # ... (rest same as development)
```

---

## Nginx Configuration

### nginx/nginx.conf

Create `/home/ch1pu/infinate/nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    # Upstream servers
    upstream frontend {
        server frontend:5173;  # Vite dev server port
    }

    upstream backend {
        server backend:8000;   # FastAPI port
    }

    # Map to detect Cloudflare Tunnel traffic
    map $http_cf_connecting_ip $is_cloudflare {
        default 1;     # Has CF-Connecting-IP header = Cloudflare traffic
        ""      0;     # No CF-Connecting-IP header = Local traffic
    }

    server {
        listen 80;
        server_name infinite.alphadeploy.org localhost;
        client_max_body_size 10M;

        # Trust Cloudflare proxy IPs (for real client IP restoration)
        set_real_ip_from 173.245.48.0/20;
        set_real_ip_from 103.21.244.0/22;
        set_real_ip_from 103.22.200.0/22;
        set_real_ip_from 103.31.4.0/22;
        set_real_ip_from 141.101.64.0/18;
        set_real_ip_from 108.162.192.0/18;
        set_real_ip_from 190.93.240.0/20;
        set_real_ip_from 188.114.96.0/20;
        set_real_ip_from 197.234.240.0/22;
        set_real_ip_from 198.41.128.0/17;
        set_real_ip_from 162.158.0.0/15;
        set_real_ip_from 104.16.0.0/13;
        set_real_ip_from 104.24.0.0/14;
        set_real_ip_from 172.64.0.0/13;
        set_real_ip_from 131.0.72.0/22;

        # Use CF-Connecting-IP header for real client IP
        real_ip_header CF-Connecting-IP;
        real_ip_recursive on;

        # Security Headers
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # Frontend (React + Three.js)
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Rate limiting (10 requests/second)
            limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
            limit_req zone=api burst=20 nodelay;
        }

        # WebSocket for real-time updates
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # Vite HMR WebSocket (development only)
        location /vite-hmr {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_set_header Host $host;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

---

## Cloudflare Tunnel Setup

### Step 1: Create Tunnel in Cloudflare Dashboard

1. Go to https://one.dash.cloudflare.com/
2. Navigate to **Networks → Tunnels**
3. Click **"Create a tunnel"**
4. Name: `infinite-demo`
5. Click **"Save tunnel"**

### Step 2: Configure Public Hostname

1. In tunnel settings, click **"Public Hostname"** tab
2. Click **"Add a public hostname"**
3. Configure:
   - **Subdomain:** `infinite`
   - **Domain:** `alphadeploy.org`
   - **Service Type:** `HTTP`
   - **URL:** `nginx:80`
4. Click **"Save hostname"**

### Step 3: Get Tunnel Token

1. Click **"Configure"** tab
2. Select **"Docker"** connector
3. Copy the tunnel token (long base64 string starting with `eyJ...`)
4. Add to `.env` file:
   ```bash
   CLOUDFLARE_TUNNEL_TOKEN=eyJh...your-tunnel-token...
   ```

### Step 4: Start Tunnel

```bash
cd /home/ch1pu/infinate
docker compose up -d cloudflared
```

### Step 5: Verify

```bash
# Check tunnel status
docker logs infinite-cloudflared

# Test public URL
curl https://infinite.alphadeploy.org/health
# Should return: healthy
```

---

## Environment Variables

### .env File

Create `/home/ch1pu/infinate/.env`:

```bash
# Database Configuration
POSTGRES_DB=infinite
POSTGRES_USER=infinite_user
POSTGRES_PASSWORD=<GENERATE_SECURE_PASSWORD>

# Redis Configuration
REDIS_PASSWORD=<GENERATE_SECURE_PASSWORD>

# API Configuration
API_SECRET_KEY=<GENERATE_SECURE_KEY>
ALLOWED_ORIGINS=https://infinite.alphadeploy.org

# Cloudflare Tunnel
CLOUDFLARE_TUNNEL_TOKEN=<YOUR_TUNNEL_TOKEN>

# Environment
ENVIRONMENT=production
```

### Generate Secure Secrets

```bash
# Generate PostgreSQL password
openssl rand -base64 32

# Generate Redis password
openssl rand -base64 32

# Generate API secret key
openssl rand -base64 64
```

### .env.example

Create `/home/ch1pu/infinate/.env.example`:

```bash
# Database Configuration
POSTGRES_DB=infinite
POSTGRES_USER=infinite_user
POSTGRES_PASSWORD=change_me_in_production

# Redis Configuration
REDIS_PASSWORD=change_me_in_production

# API Configuration
API_SECRET_KEY=change_me_in_production
ALLOWED_ORIGINS=https://infinite.alphadeploy.org

# Cloudflare Tunnel
# Get your tunnel token from: https://one.dash.cloudflare.com/ → Networks → Tunnels
CLOUDFLARE_TUNNEL_TOKEN=your-cloudflare-tunnel-token-here

# Environment
ENVIRONMENT=development
```

---

## Deployment Steps

### Prerequisites

- ✅ Infinite M1.6 (Vector Store Integration) complete
- ✅ Infinite M1.7 (Integration Testing) complete
- ✅ Home server running (WSL2 Ubuntu)
- ✅ Cloudflare account configured
- ✅ Docker installed

### Step 1: Create Dockerfiles

**Backend Dockerfile** (`/home/ch1pu/infinate/backend/Dockerfile`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile** (`/home/ch1pu/infinate/frontend/Dockerfile.dev`):

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Run development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### Step 2: Create .env File

```bash
cd /home/ch1pu/infinate
cp .env.example .env

# Edit .env with your secrets
nano .env
```

### Step 3: Create Cloudflare Tunnel

Follow steps in [Cloudflare Tunnel Setup](#cloudflare-tunnel-setup)

### Step 4: Start Services

```bash
cd /home/ch1pu/infinate

# Start all services
docker compose up -d

# Check logs
docker compose logs -f

# Verify all services healthy
docker compose ps
```

### Step 5: Verify Deployment

```bash
# Check health endpoint
curl http://localhost/health
# Should return: healthy

# Check public URL
curl https://infinite.alphadeploy.org/health
# Should return: healthy

# Test API endpoint
curl https://infinite.alphadeploy.org/api/status
```

### Step 6: Monitor Services

```bash
# View logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f cloudflared

# Check resource usage
docker stats

# Check service status
docker compose ps
```

---

## Monitoring & Health Checks

### Built-in Health Checks

All services have health checks configured in `docker-compose.yml`:

- **PostgreSQL**: `pg_isready` every 10s
- **Qdrant**: HTTP health endpoint every 10s
- **Redis**: `ping` command every 10s

### Custom Health Monitoring Script

Create `/home/ch1pu/infinate/scripts/health-check.sh`:

```bash
#!/bin/bash

# Health check script for Infinite demo
# Run this via cron every 5 minutes

HEALTH_URL="https://infinite.alphadeploy.org/health"
ALERT_EMAIL="adolfo@alphadeploy.org"

# Check health endpoint
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$RESPONSE" != "200" ]; then
    echo "ALERT: Infinite demo is DOWN (HTTP $RESPONSE)" | mail -s "Infinite Demo Alert" $ALERT_EMAIL

    # Attempt auto-restart
    cd /home/ch1pu/infinate
    docker compose restart
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "ALERT: Disk usage at ${DISK_USAGE}%" | mail -s "Disk Space Alert" $ALERT_EMAIL
fi

# Check container status
EXITED_CONTAINERS=$(docker ps -a --filter "status=exited" --filter "name=infinite-" --format "{{.Names}}")
if [ ! -z "$EXITED_CONTAINERS" ]; then
    echo "ALERT: Containers exited: $EXITED_CONTAINERS" | mail -s "Container Alert" $ALERT_EMAIL

    # Attempt auto-restart
    cd /home/ch1pu/infinate
    docker compose up -d
fi
```

### Add to Crontab

```bash
# Edit crontab
crontab -e

# Add health check every 5 minutes
*/5 * * * * /home/ch1pu/infinate/scripts/health-check.sh
```

---

## Troubleshooting

### Issue: Cloudflare Tunnel Not Connecting

**Check:**
```bash
docker logs infinite-cloudflared
```

**Solution:**
- Verify tunnel token is correct in `.env`
- Ensure tunnel is active in Cloudflare dashboard
- Restart cloudflared: `docker compose restart cloudflared`

### Issue: Database Connection Failed

**Check:**
```bash
docker logs infinite-backend | grep -i "database"
```

**Solution:**
- Verify PostgreSQL is healthy: `docker compose ps postgres`
- Check credentials in `.env`
- Restart services: `docker compose restart postgres backend`

### Issue: Frontend Not Loading

**Check:**
```bash
docker logs infinite-frontend
docker logs infinite-nginx
```

**Solution:**
- Verify nginx config: `docker exec infinite-nginx nginx -t`
- Check frontend build: `docker compose logs frontend`
- Restart nginx: `docker compose restart nginx`

---

## Backup Strategy

### Database Backups

Create `/home/ch1pu/infinate/scripts/backup-db.sh`:

```bash
#!/bin/bash

# Backup PostgreSQL database
BACKUP_DIR="/home/ch1pu/infinate/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/infinite_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Dump database
docker exec infinite-postgres pg_dump -U infinite_user infinite > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "infinite_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

### Add to Crontab (Daily at 2 AM)

```bash
crontab -e

# Add daily backup
0 2 * * * /home/ch1pu/infinate/scripts/backup-db.sh
```

---

## Summary

### What You Get

✅ **Full production deployment** of Infinite demo
✅ **Public URL:** `https://infinite.alphadeploy.org`
✅ **Auto HTTPS** via Cloudflare
✅ **DDoS protection** via Cloudflare
✅ **Health monitoring** with auto-restart
✅ **Daily backups** automated
✅ **Resource limits** to prevent crashes

### Cost

**Total:** ~$10/month (electricity for home server only)

### Timeline

**Earliest Deployment:** January 2026 (after M1.6/M1.7 complete)

---

**Ready to deploy when Infinite reaches 45-50% completion!**

Last Updated: December 2, 2025
Adolfo Lopez (ch1pu) - United States Navy Veteran
