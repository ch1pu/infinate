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

# INFINITE: Project Dependencies
**Complete Dependency List and Rationale**

---

## EXECUTIVE SUMMARY

This document lists all external dependencies required for the Infinite project, including NPM packages, system requirements, and third-party services, with rationale for each choice.

---

## 1. SYSTEM REQUIREMENTS

### Development Environment

| Requirement | Minimum Version | Recommended | Purpose |
|-------------|-----------------|-------------|---------|
| **Node.js** | 18.0.0 | 20.x LTS | JavaScript runtime |
| **npm/pnpm** | 8.0.0 | Latest | Package manager |
| **PostgreSQL** | 14 | 15+ | Primary database |
| **Redis** | 6.2 | 7.x | Caching layer |
| **Docker** | 20.10 | Latest | Containerization |
| **Git** | 2.30 | Latest | Version control |

### Hardware Requirements

| Component | Minimum | Recommended | Optimal |
|-----------|---------|-------------|---------|
| **CPU** | 4 cores | 8 cores | 16+ cores |
| **RAM** | 16 GB | 32 GB | 64 GB |
| **Storage** | 50 GB SSD | 100 GB NVMe | 500 GB NVMe |
| **GPU** | Integrated | GTX 1060 | RTX 4060+ |
| **NPU** | None | None | AMD XDNA 2 |

---

## 2. FRONTEND DEPENDENCIES

### Core Framework

```json
{
  "react": "^18.2.0",           // UI framework
  "react-dom": "^18.2.0",       // React DOM rendering
  "typescript": "^5.3.0",       // Type safety
  "vite": "^5.0.0"              // Build tool
}
```

### 3D Rendering

```json
{
  "three": "^0.159.0",                    // 3D graphics library
  "@react-three/fiber": "^8.15.0",        // React Three.js renderer
  "@react-three/drei": "^9.92.0",         // Three.js helpers
  "@react-three/postprocessing": "^2.15.0", // Post-processing effects
  "@react-three/xr": "^5.5.0"             // VR/AR support (optional)
}
```

**Rationale:** Three.js is the most mature WebGL library with excellent React integration through react-three-fiber.

### State Management

```json
{
  "@reduxjs/toolkit": "^2.0.0",   // State management
  "react-redux": "^9.0.0",         // React bindings
  "redux-persist": "^6.0.0",      // State persistence
  "immer": "^10.0.0"              // Immutable updates
}
```

**Rationale:** Redux Toolkit provides excellent DevEx with built-in best practices and TypeScript support.

### Styling

```json
{
  "@emotion/react": "^11.11.0",    // CSS-in-JS
  "@emotion/styled": "^11.11.0",   // Styled components
  "framer-motion": "^10.16.0"      // Animations
}
```

**Rationale:** Emotion provides excellent performance with runtime CSS generation and theming support.

### Networking

```json
{
  "axios": "^1.6.0",               // HTTP client
  "socket.io-client": "^4.6.0",    // WebSocket client
  "@grpc/grpc-js": "^1.9.0",      // gRPC client
  "@grpc/proto-loader": "^0.7.0"   // Proto loading
}
```

### UI Components

```json
{
  "@mui/material": "^5.15.0",      // Material UI (optional)
  "@radix-ui/react-*": "^1.0.0",   // Headless components
  "react-hook-form": "^7.48.0",    // Form management
  "react-query": "^3.39.0"         // Server state management
}
```

### Development Tools

```json
{
  "@vitejs/plugin-react": "^4.2.0",
  "@types/react": "^18.2.0",
  "@types/three": "^0.159.0",
  "eslint": "^8.55.0",
  "prettier": "^3.1.0",
  "vitest": "^1.0.0",
  "@testing-library/react": "^14.0.0",
  "@playwright/test": "^1.40.0"
}
```

---

## 3. BACKEND DEPENDENCIES

### Core Framework

```json
{
  "express": "^4.18.0",           // Web framework
  "typescript": "^5.3.0",         // Type safety
  "tsx": "^4.7.0",                // TypeScript execution
  "dotenv": "^16.3.0"             // Environment variables
}
```

### Database

```json
{
  "@prisma/client": "^5.7.0",     // ORM client
  "prisma": "^5.7.0",              // ORM CLI
  "pg": "^8.11.0",                 // PostgreSQL driver
  "pgvector": "^0.1.0"             // Vector operations
}
```

**Rationale:** Prisma provides excellent TypeScript support and migration management.

### Authentication & Security

```json
{
  "jsonwebtoken": "^9.0.0",        // JWT tokens
  "bcrypt": "^5.1.0",              // Password hashing
  "argon2": "^0.31.0",             // Better password hashing
  "helmet": "^7.1.0",              // Security headers
  "cors": "^2.8.5",                // CORS support
  "express-rate-limit": "^7.1.0",  // Rate limiting
  "express-validator": "^7.0.0"    // Input validation
}
```

### Real-time Communication

```json
{
  "socket.io": "^4.6.0",           // WebSocket server
  "@grpc/grpc-js": "^1.9.0",      // gRPC server
  "ws": "^8.16.0"                  // Low-level WebSocket
}
```

### AI/ML Integration

```json
{
  "node-llama-cpp": "^2.8.0",      // Llama.cpp bindings
  "@xenova/transformers": "^2.10.0", // Transformers.js
  "onnxruntime-node": "^1.16.0"    // ONNX runtime
}
```

**Rationale:** node-llama-cpp provides native bindings for efficient LLM inference.

### Caching & Queuing

```json
{
  "ioredis": "^5.3.0",             // Redis client
  "bull": "^4.11.0",               // Job queue
  "node-cache": "^5.1.2"           // Memory cache
}
```

### Utilities

```json
{
  "winston": "^3.11.0",            // Logging
  "joi": "^17.11.0",               // Schema validation
  "zod": "^3.22.0",                // TypeScript validation
  "uuid": "^9.0.0",                // UUID generation
  "lodash": "^4.17.21",            // Utility functions
  "dayjs": "^1.11.0"               // Date manipulation
}
```

### Development Tools

```json
{
  "nodemon": "^3.0.0",
  "ts-node": "^10.9.0",
  "@types/node": "^20.10.0",
  "@types/express": "^4.17.0",
  "eslint": "^8.55.0",
  "prettier": "^3.1.0",
  "jest": "^29.7.0",
  "supertest": "^6.3.0"
}
```

---

## 4. DATABASE EXTENSIONS

### PostgreSQL Extensions

```sql
-- Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- Cryptographic functions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Trigram search
CREATE EXTENSION IF NOT EXISTS "cube";           -- N-dimensional cubes
CREATE EXTENSION IF NOT EXISTS "vector";         -- Vector similarity search
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Query statistics
```

**Rationale:** These extensions enable core functionality like spatial indexing and vector search.

---

## 5. DOCKER IMAGES

### Base Images

```dockerfile
# Frontend
FROM node:20-alpine AS frontend-base

# Backend
FROM node:20-alpine AS backend-base

# PostgreSQL
FROM postgres:15-alpine

# Redis
FROM redis:7-alpine

# Nginx
FROM nginx:alpine
```

**Rationale:** Alpine images provide minimal size with necessary functionality.

---

## 6. BUILD & TESTING DEPENDENCIES

### Build Tools

```json
{
  "webpack": "^5.89.0",            // Module bundler (fallback)
  "esbuild": "^0.19.0",            // Fast bundler
  "tsup": "^8.0.0",                // TypeScript bundler
  "rollup": "^4.9.0"               // Library bundler
}
```

### Testing Frameworks

```json
{
  "vitest": "^1.0.0",              // Unit testing
  "jest": "^29.7.0",               // Integration testing
  "@playwright/test": "^1.40.0",   // E2E testing
  "k6": "^0.48.0",                 // Load testing
  "@faker-js/faker": "^8.3.0",     // Test data generation
  "fishery": "^2.2.0"              // Test factories
}
```

### Code Quality

```json
{
  "eslint": "^8.55.0",
  "eslint-config-airbnb": "^19.0.0",
  "eslint-plugin-react": "^7.33.0",
  "prettier": "^3.1.0",
  "husky": "^8.0.0",
  "lint-staged": "^15.2.0",
  "commitlint": "^18.4.0"
}
```

---

## 7. MONITORING & OBSERVABILITY

### APM & Metrics

```json
{
  "prom-client": "^15.1.0",        // Prometheus metrics
  "@opentelemetry/api": "^1.7.0",  // OpenTelemetry
  "@sentry/node": "^7.91.0",       // Error tracking
  "winston": "^3.11.0",            // Logging
  "morgan": "^1.10.0"              // HTTP logging
}
```

**Rationale:** OpenTelemetry provides vendor-neutral observability.

---

## 8. SECURITY DEPENDENCIES

### Security Scanning

```json
{
  "snyk": "^1.1266.0",             // Vulnerability scanning
  "npm-audit": "^0.1.0",           // Dependency audit
  "helmet": "^7.1.0",              // Security headers
  "express-mongo-sanitize": "^2.2.0", // NoSQL injection prevention
  "xss": "^1.0.14"                 // XSS sanitization
}
```

---

## 9. OPTIONAL DEPENDENCIES

### Advanced Features

```json
{
  // Machine Learning
  "@tensorflow/tfjs-node": "^4.15.0",  // TensorFlow.js
  "sharp": "^0.33.0",                  // Image processing

  // Documentation
  "swagger-ui-express": "^5.0.0",      // API documentation
  "typedoc": "^0.25.0",                // TypeScript docs

  // Performance
  "compression": "^1.7.4",             // Response compression
  "cluster": "^0.7.7",                 // Node clustering

  // Internationalization
  "i18next": "^23.7.0",                // i18n support
  "react-i18next": "^14.0.0"           // React i18n
}
```

---

## 10. VERSION LOCKING STRATEGY

### Package Lock Files

```bash
# Use exact versions in production
npm ci               # Install from package-lock.json
pnpm install --frozen-lockfile

# Update strategy
npm update --save    # Update minor versions
npm audit fix        # Security updates
```

### Dependency Updates

```json
{
  "scripts": {
    "deps:check": "npm-check-updates",
    "deps:update": "npm-check-updates -u",
    "deps:audit": "npm audit",
    "deps:clean": "npm prune"
  }
}
```

---

## 11. BUNDLE SIZE ANALYSIS

### Expected Bundle Sizes

| Package | Size (minified) | Size (gzipped) | Impact |
|---------|----------------|----------------|--------|
| React | 42.2 KB | 13.4 KB | Core |
| Three.js | 598 KB | 147 KB | Heavy |
| Redux | 10.8 KB | 3.2 KB | Light |
| Socket.io | 93.7 KB | 30.8 KB | Medium |
| **Total Frontend** | ~2.5 MB | ~750 KB | Acceptable |

### Optimization Strategies

```javascript
// Dynamic imports for code splitting
const Three = () => import('three');
const SocketIO = () => import('socket.io-client');

// Tree shaking
import { specific } from 'lodash-es';

// Production builds
NODE_ENV=production npm run build
```

---

## 12. LICENSE COMPATIBILITY

### License Summary

| Category | License | Compatible | Notes |
|----------|---------|------------|-------|
| **React ecosystem** | MIT | ✅ | Permissive |
| **Three.js** | MIT | ✅ | Permissive |
| **PostgreSQL** | PostgreSQL | ✅ | Permissive |
| **Redis** | BSD-3 | ✅ | Permissive |
| **Node.js** | MIT | ✅ | Permissive |
| **Prisma** | Apache 2.0 | ✅ | Permissive |

**Project License:** Apache 2.0 (Compatible with all dependencies)

---

## SUCCESS METRICS

### Dependency Health
- Zero critical vulnerabilities
- <5% outdated packages
- 100% license compatibility
- <3MB production bundle

### Performance Impact
- <100ms boot time impact
- <10% memory overhead
- No blocking dependencies
- Efficient tree shaking

### Maintenance
- Monthly dependency updates
- Automated security scanning
- Version lock files committed
- Clear update procedures

---

**Total NPM Packages:** ~150-200
**Production Dependencies:** ~80-100
**Development Dependencies:** ~70-100
**Bundle Size Target:** <3MB gzipped