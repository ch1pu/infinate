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
    10,317x speedup over MIT's approach with 89.58% test coverage.
══════════════════════════════════════════════════════════════════════════════
-->

# INFINITE: Project Structure
**Complete Directory Organization and File Layout**

---

## EXECUTIVE SUMMARY

This document defines the complete project structure for Infinite, detailing the organization of all directories, files, and resources for the spatial context management system.

---

## 1. ROOT STRUCTURE OVERVIEW

```
infinite/
├── .github/                  # GitHub configuration
├── .vscode/                  # VS Code settings
├── docker/                   # Docker configurations
├── docs/                     # User documentation
├── scripts/                  # Utility scripts
├── src/                      # Source code
│   ├── frontend/            # React application
│   ├── backend/             # Node.js server
│   └── shared/              # Shared types/utils
├── database/                 # Database files
│   ├── migrations/          # Schema migrations
│   ├── seeds/               # Seed data
│   └── scripts/             # DB utilities
├── tests/                    # Test suites
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── e2e/                 # End-to-end tests
│   └── performance/         # Performance tests
├── config/                   # Configuration files
├── public/                   # Static assets
├── .dockerignore            # Docker ignore rules
├── .env.example             # Environment template
├── .eslintrc.js             # ESLint config
├── .gitignore               # Git ignore rules
├── .prettierrc              # Prettier config
├── docker-compose.yml       # Docker orchestration
├── package.json             # NPM dependencies
├── README.md                # Project documentation
├── tsconfig.json            # TypeScript config
└── vitest.config.ts         # Test configuration
```

---

## 2. FRONTEND STRUCTURE

```
src/frontend/
├── public/
│   ├── index.html           # HTML entry point
│   ├── favicon.ico          # Favicon
│   └── manifest.json        # PWA manifest
├── src/
│   ├── components/          # React components
│   │   ├── world/          # 3D world components
│   │   │   ├── WorldRenderer.tsx
│   │   │   ├── VoxelEngine.tsx
│   │   │   ├── ChunkManager.tsx
│   │   │   └── OctreeVisualizer.tsx
│   │   ├── agent/          # Agent components
│   │   │   ├── AgentAvatar.tsx
│   │   │   ├── AgentController.tsx
│   │   │   └── ViewFrustum.tsx
│   │   ├── memory/         # Memory visualization
│   │   │   ├── MemoryPalace.tsx
│   │   │   ├── MemoryChunk.tsx
│   │   │   └── ClusterViewer.tsx
│   │   ├── controls/       # User controls
│   │   │   ├── NavigationControls.tsx
│   │   │   ├── SearchPanel.tsx
│   │   │   └── TeleportInterface.tsx
│   │   ├── hud/            # HUD elements
│   │   │   ├── ContextDisplay.tsx
│   │   │   ├── PerformanceMonitor.tsx
│   │   │   └── QueryInterface.tsx
│   │   └── common/         # Shared components
│   │       ├── Button.tsx
│   │       ├── Modal.tsx
│   │       └── Loading.tsx
│   ├── hooks/              # Custom React hooks
│   │   ├── useWebSocket.ts
│   │   ├── useThree.ts
│   │   ├── useAgent.ts
│   │   └── useContext.ts
│   ├── services/           # API services
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   ├── auth.ts
│   │   └── streaming.ts
│   ├── store/              # Redux store
│   │   ├── index.ts
│   │   ├── slices/
│   │   │   ├── agentSlice.ts
│   │   │   ├── worldSlice.ts
│   │   │   └── contextSlice.ts
│   │   └── middleware/
│   │       └── websocket.ts
│   ├── styles/             # Styles
│   │   ├── themes/
│   │   ├── globals.css
│   │   └── variables.css
│   ├── utils/              # Utilities
│   │   ├── three-helpers.ts
│   │   ├── math.ts
│   │   └── formatting.ts
│   ├── types/              # TypeScript types
│   │   ├── models.ts
│   │   ├── api.ts
│   │   └── three.ts
│   ├── shaders/            # WebGPU/GLSL shaders
│   │   ├── chunk.vert
│   │   ├── chunk.frag
│   │   └── particle.wgsl
│   ├── workers/            # Web Workers
│   │   ├── octree.worker.ts
│   │   └── streaming.worker.ts
│   ├── App.tsx             # Root component
│   ├── index.tsx           # Entry point
│   └── setupTests.ts       # Test setup
├── .env.local               # Local environment
├── package.json             # Frontend dependencies
├── tsconfig.json            # TypeScript config
├── vite.config.ts           # Vite configuration
└── README.md                # Frontend documentation
```

---

## 3. BACKEND STRUCTURE

```
src/backend/
├── src/
│   ├── api/                # API layer
│   │   ├── routes/         # Route definitions
│   │   │   ├── auth.routes.ts
│   │   │   ├── space.routes.ts
│   │   │   ├── chunk.routes.ts
│   │   │   ├── agent.routes.ts
│   │   │   └── query.routes.ts
│   │   ├── controllers/    # Request handlers
│   │   │   ├── auth.controller.ts
│   │   │   ├── space.controller.ts
│   │   │   ├── chunk.controller.ts
│   │   │   ├── agent.controller.ts
│   │   │   └── query.controller.ts
│   │   ├── middleware/     # Express middleware
│   │   │   ├── auth.middleware.ts
│   │   │   ├── validation.middleware.ts
│   │   │   ├── error.middleware.ts
│   │   │   └── logging.middleware.ts
│   │   └── validators/     # Input validation
│   │       ├── auth.validator.ts
│   │       └── chunk.validator.ts
│   ├── core/               # Business logic
│   │   ├── chunking/       # Chunking engine
│   │   │   ├── chunker.ts
│   │   │   ├── strategies/
│   │   │   │   ├── semantic.ts
│   │   │   │   ├── structural.ts
│   │   │   │   └── adaptive.ts
│   │   │   └── tokenizer.ts
│   │   ├── spatial/        # Spatial indexing
│   │   │   ├── octree.ts
│   │   │   ├── mapper.ts
│   │   │   └── queries.ts
│   │   ├── embedding/      # Embedding generation
│   │   │   ├── generator.ts
│   │   │   ├── npu.ts
│   │   │   └── cache.ts
│   │   ├── streaming/      # Context streaming
│   │   │   ├── streamer.ts
│   │   │   ├── prefetch.ts
│   │   │   └── priority.ts
│   │   └── ai/             # AI orchestration
│   │       ├── models.ts
│   │       ├── inference.ts
│   │       └── orchestrator.ts
│   ├── services/           # External services
│   │   ├── database.ts
│   │   ├── redis.ts
│   │   ├── websocket.ts
│   │   ├── grpc.ts
│   │   └── monitoring.ts
│   ├── models/             # Data models
│   │   ├── user.model.ts
│   │   ├── space.model.ts
│   │   ├── chunk.model.ts
│   │   ├── agent.model.ts
│   │   └── query.model.ts
│   ├── repositories/       # Data access layer
│   │   ├── user.repository.ts
│   │   ├── space.repository.ts
│   │   ├── chunk.repository.ts
│   │   └── agent.repository.ts
│   ├── utils/              # Utilities
│   │   ├── logger.ts
│   │   ├── crypto.ts
│   │   ├── validation.ts
│   │   └── errors.ts
│   ├── types/              # TypeScript types
│   │   ├── express.d.ts
│   │   ├── models.ts
│   │   └── config.ts
│   ├── config/             # Configuration
│   │   ├── index.ts
│   │   ├── database.ts
│   │   ├── redis.ts
│   │   └── security.ts
│   ├── jobs/               # Background jobs
│   │   ├── cleanup.job.ts
│   │   ├── indexing.job.ts
│   │   └── metrics.job.ts
│   ├── grpc/               # gRPC definitions
│   │   ├── protos/
│   │   │   └── spatial.proto
│   │   └── services/
│   │       └── spatial.service.ts
│   ├── app.ts              # Express app setup
│   ├── server.ts           # Server entry point
│   └── cluster.ts          # Cluster mode
├── .env                     # Environment variables
├── package.json             # Backend dependencies
├── tsconfig.json            # TypeScript config
├── nodemon.json             # Development config
└── README.md                # Backend documentation
```

---

## 4. DATABASE STRUCTURE

```
database/
├── migrations/              # Prisma migrations
│   ├── 001_initial_schema/
│   │   ├── migration.sql
│   │   ├── up.ts
│   │   ├── down.ts
│   │   └── validate.ts
│   ├── 002_add_embeddings/
│   ├── 003_add_spatial_index/
│   └── migration_lock.toml
├── seeds/                   # Seed data
│   ├── system/             # System data
│   │   ├── users.seed.ts
│   │   ├── roles.seed.ts
│   │   └── config.seed.ts
│   ├── demo/               # Demo data
│   │   ├── codebase.seed.ts
│   │   ├── documentation.seed.ts
│   │   └── conversations.seed.ts
│   ├── test/               # Test data
│   │   ├── performance.seed.ts
│   │   └── edge-cases.seed.ts
│   └── index.ts            # Seed orchestrator
├── scripts/                 # Database utilities
│   ├── backup.sh
│   ├── restore.sh
│   ├── optimize.sql
│   └── analyze.sql
├── schema.prisma            # Prisma schema
└── README.md                # Database documentation
```

---

## 5. DOCKER STRUCTURE

```
docker/
├── frontend/               # Frontend container
│   ├── Dockerfile
│   └── nginx.conf
├── backend/                # Backend container
│   ├── Dockerfile
│   └── entrypoint.sh
├── postgres/               # Database container
│   ├── Dockerfile
│   ├── init.sql
│   └── postgresql.conf
├── redis/                  # Cache container
│   ├── Dockerfile
│   └── redis.conf
├── nginx/                  # Reverse proxy
│   ├── Dockerfile
│   ├── nginx.conf
│   └── ssl/
│       ├── cert.pem
│       └── key.pem
└── docker-compose.override.yml  # Local overrides
```

---

## 6. TEST STRUCTURE

```
tests/
├── unit/                   # Unit tests
│   ├── frontend/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── utils/
│   ├── backend/
│   │   ├── controllers/
│   │   ├── services/
│   │   └── utils/
│   └── shared/
├── integration/            # Integration tests
│   ├── api/
│   │   ├── auth.test.ts
│   │   ├── chunks.test.ts
│   │   └── streaming.test.ts
│   ├── database/
│   │   ├── queries.test.ts
│   │   └── transactions.test.ts
│   └── websocket/
│       └── streaming.test.ts
├── e2e/                    # End-to-end tests
│   ├── specs/
│   │   ├── user-journey.spec.ts
│   │   ├── navigation.spec.ts
│   │   └── query.spec.ts
│   └── fixtures/
│       └── test-data.json
├── performance/            # Performance tests
│   ├── load/
│   │   └── load-test.js
│   ├── stress/
│   │   └── stress-test.js
│   └── benchmarks/
│       └── operations.bench.ts
├── security/               # Security tests
│   ├── auth.security.ts
│   ├── injection.security.ts
│   └── zap-scan.yaml
├── fixtures/               # Test fixtures
│   ├── users.json
│   ├── chunks.json
│   └── queries.json
├── utils/                  # Test utilities
│   ├── setup.ts
│   ├── factories.ts
│   └── helpers.ts
└── coverage/               # Coverage reports
    └── index.html
```

---

## 7. CONFIGURATION STRUCTURE

```
config/
├── environments/           # Environment configs
│   ├── development.json
│   ├── test.json
│   ├── staging.json
│   └── production.json
├── webpack/                # Build configs
│   ├── webpack.common.js
│   ├── webpack.dev.js
│   └── webpack.prod.js
├── jest/                   # Test configs
│   ├── jest.config.js
│   └── setupTests.js
├── eslint/                 # Linting configs
│   ├── .eslintrc.base.js
│   ├── .eslintrc.frontend.js
│   └── .eslintrc.backend.js
├── prettier/               # Formatting
│   └── .prettierrc.js
└── docker/                 # Container configs
    └── docker-compose.base.yml
```

---

## 8. DOCUMENTATION STRUCTURE

```
docs/
├── api/                    # API documentation
│   ├── openapi.yaml
│   ├── postman/
│   │   └── collection.json
│   └── examples/
│       ├── auth.md
│       └── queries.md
├── architecture/           # Architecture docs
│   ├── overview.md
│   ├── components.md
│   ├── data-flow.md
│   └── decisions.md
├── guides/                 # User guides
│   ├── getting-started.md
│   ├── installation.md
│   ├── configuration.md
│   └── deployment.md
├── development/            # Dev documentation
│   ├── setup.md
│   ├── contributing.md
│   ├── testing.md
│   └── debugging.md
└── images/                 # Documentation assets
    ├── architecture.png
    ├── screenshots/
    └── diagrams/
```

---

## 9. SCRIPTS STRUCTURE

```
scripts/
├── setup/                  # Setup scripts
│   ├── install.sh
│   ├── configure.sh
│   └── init-db.sh
├── build/                  # Build scripts
│   ├── build.sh
│   ├── bundle.sh
│   └── optimize.sh
├── deploy/                 # Deployment scripts
│   ├── deploy.sh
│   ├── rollback.sh
│   └── health-check.sh
├── development/            # Dev scripts
│   ├── dev.sh
│   ├── watch.sh
│   └── debug.sh
├── maintenance/            # Maintenance scripts
│   ├── backup.sh
│   ├── cleanup.sh
│   └── update.sh
└── utils/                  # Utility scripts
    ├── generate-types.sh
    ├── analyze-bundle.sh
    └── check-deps.sh
```

---

## 10. GITHUB STRUCTURE

```
.github/
├── workflows/              # GitHub Actions
│   ├── ci.yml             # Continuous Integration
│   ├── cd.yml             # Continuous Deployment
│   ├── test.yml           # Test runner
│   ├── security.yml       # Security scanning
│   └── release.yml        # Release automation
├── ISSUE_TEMPLATE/         # Issue templates
│   ├── bug_report.md
│   ├── feature_request.md
│   └── config.yml
├── PULL_REQUEST_TEMPLATE.md
├── CODEOWNERS              # Code ownership
├── dependabot.yml          # Dependency updates
└── FUNDING.yml             # Funding information
```

---

## 11. FILE NAMING CONVENTIONS

### TypeScript/JavaScript Files
- Components: `PascalCase.tsx` (e.g., `AgentAvatar.tsx`)
- Hooks: `camelCase.ts` starting with 'use' (e.g., `useAgent.ts`)
- Services: `camelCase.service.ts` (e.g., `auth.service.ts`)
- Utils: `kebab-case.ts` (e.g., `three-helpers.ts`)
- Types: `camelCase.types.ts` (e.g., `models.types.ts`)
- Tests: `*.test.ts` or `*.spec.ts`

### Configuration Files
- JSON: `kebab-case.json` (e.g., `docker-compose.json`)
- YAML: `kebab-case.yaml` (e.g., `openapi.yaml`)
- Environment: `.env.{environment}` (e.g., `.env.production`)

### Documentation Files
- Markdown: `UPPER_SNAKE_CASE.md` for key docs (e.g., `README.md`)
- Guides: `kebab-case.md` (e.g., `getting-started.md`)

---

## 12. IMPORT ORGANIZATION

### Import Order (ESLint enforced)
```typescript
// 1. External imports
import React from 'react';
import { useSelector } from 'react-redux';

// 2. Internal absolute imports
import { AgentAvatar } from '@/components/agent';
import { useWebSocket } from '@/hooks';

// 3. Relative imports
import { WorldRenderer } from './WorldRenderer';
import type { AgentProps } from './types';

// 4. Style imports
import styles from './Agent.module.css';
```

### Path Aliases
```json
{
  "paths": {
    "@/*": ["src/*"],
    "@components/*": ["src/components/*"],
    "@services/*": ["src/services/*"],
    "@utils/*": ["src/utils/*"],
    "@types/*": ["src/types/*"],
    "@hooks/*": ["src/hooks/*"],
    "@core/*": ["src/core/*"]
  }
}
```

---

## SUCCESS METRICS

### Code Organization
- Clear separation of concerns
- Consistent file structure
- Logical grouping
- Easy navigation

### Maintainability
- Self-documenting structure
- Consistent naming
- Clear dependencies
- Modular design

### Scalability
- Room for growth
- Pattern consistency
- Easy to extend
- Performance considered

---

**Total Files Estimate:** 300-400 files
**Lines of Code Estimate:** 50,000-75,000 lines
**Documentation:** 25,000+ lines
**Test Coverage Target:** 80%+