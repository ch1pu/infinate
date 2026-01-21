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

# INFINITE: Testing Strategy
**Comprehensive Testing Architecture for Quality Assurance**

---

## EXECUTIVE SUMMARY

This document defines the complete testing strategy for Infinite, covering unit testing, integration testing, end-to-end testing, performance testing, and security testing to ensure reliability, performance, and quality of the spatial context management system.

---

## 1. TESTING ARCHITECTURE OVERVIEW

### Testing Pyramid

```
         E2E Tests (10%)
        /            \
       /              \
      / Integration    \
     /   Tests (30%)   \
    /                  \
   /   Unit Tests      \
  /      (60%)         \
 /_____________________\
```

### Testing Stack

```typescript
interface TestingStack {
  unit: {
    framework: 'Vitest';
    coverage: 'c8';
    mocking: 'Vitest mocks';
  };

  integration: {
    framework: 'Jest';
    database: 'TestContainers';
    api: 'Supertest';
  };

  e2e: {
    framework: 'Playwright';
    browsers: ['Chrome', 'Firefox', 'Safari'];
    mobile: 'Device emulation';
  };

  performance: {
    load: 'k6';
    stress: 'Artillery';
    profiling: 'Clinic.js';
  };

  security: {
    static: 'ESLint Security';
    dynamic: 'OWASP ZAP';
    dependencies: 'Snyk';
  };
}
```

---

## 2. UNIT TESTING

### Frontend Unit Tests

```typescript
// Frontend/components/AgentAvatar.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AgentAvatar } from './AgentAvatar';

describe('AgentAvatar', () => {
  it('renders agent with correct model type', () => {
    const agent = {
      id: 'agent-1',
      model: 'llama-8b',
      position: { x: 0, y: 0, z: 0 },
      status: 'active'
    };

    render(<AgentAvatar agent={agent} />);

    expect(screen.getByTestId('agent-avatar')).toBeInTheDocument();
    expect(screen.getByText('Llama 8B')).toBeInTheDocument();
  });

  it('updates position when agent moves', async () => {
    const agent = {
      id: 'agent-1',
      position: { x: 0, y: 0, z: 0 }
    };

    const { rerender } = render(<AgentAvatar agent={agent} />);

    // Update position
    agent.position = { x: 100, y: 50, z: 75 };
    rerender(<AgentAvatar agent={agent} />);

    const avatar = screen.getByTestId('agent-avatar');
    expect(avatar).toHaveStyle({
      transform: 'translate3d(100px, 50px, 75px)'
    });
  });

  it('shows loading state during initialization', () => {
    const agent = { id: 'agent-1', status: 'loading' };

    render(<AgentAvatar agent={agent} />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });
});
```

### Backend Unit Tests

```typescript
// Backend/services/chunking.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { ChunkingService } from './chunking.service';

describe('ChunkingService', () => {
  let service: ChunkingService;

  beforeEach(() => {
    service = new ChunkingService({
      chunkSize: 300,
      overlap: 50
    });
  });

  describe('semantic chunking', () => {
    it('chunks text into appropriate sizes', async () => {
      const text = 'Lorem ipsum...'.repeat(100); // Long text

      const chunks = await service.semanticChunk(text);

      expect(chunks).toHaveLength(4);
      chunks.forEach(chunk => {
        expect(chunk.tokens).toBeLessThanOrEqual(300);
        expect(chunk.tokens).toBeGreaterThanOrEqual(200);
      });
    });

    it('maintains context overlap between chunks', async () => {
      const text = 'Sentence one. Sentence two. Sentence three.';

      const chunks = await service.semanticChunk(text);

      // Check overlap exists
      if (chunks.length > 1) {
        const overlap = findOverlap(chunks[0].content, chunks[1].content);
        expect(overlap.length).toBeGreaterThan(0);
      }
    });

    it('preserves code structure when chunking', async () => {
      const code = `
        function example() {
          const data = process();
          return transform(data);
        }
      `;

      const chunks = await service.structuralChunk(code, 'code');

      // Function should stay together
      expect(chunks).toHaveLength(1);
      expect(chunks[0].content).toContain('function example');
    });
  });

  describe('embedding generation', () => {
    it('generates correct dimension embeddings', async () => {
      const chunk = { content: 'Test content', tokens: 10 };

      const embedding = await service.generateEmbedding(chunk);

      expect(embedding).toHaveLength(384);
      expect(embedding.every(v => typeof v === 'number')).toBe(true);
    });

    it('caches embeddings for identical content', async () => {
      const chunk = { content: 'Cached content', tokens: 10 };

      const embedding1 = await service.generateEmbedding(chunk);
      const embedding2 = await service.generateEmbedding(chunk);

      expect(embedding1).toEqual(embedding2);
      expect(service.cacheHits).toBe(1);
    });
  });
});
```

### Database Unit Tests

```typescript
// Database/repositories/chunk.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { ChunkRepository } from './chunk.repository';
import { createTestDatabase, cleanupTestDatabase } from '../test-utils';

describe('ChunkRepository', () => {
  let repo: ChunkRepository;
  let db: TestDatabase;

  beforeAll(async () => {
    db = await createTestDatabase();
    repo = new ChunkRepository(db);
  });

  afterAll(async () => {
    await cleanupTestDatabase(db);
  });

  it('creates chunk with spatial position', async () => {
    const chunk = await repo.create({
      content: 'Test chunk',
      tokens: 50,
      position: { x: 100, y: 50, z: 75 },
      spaceId: 'space-1'
    });

    expect(chunk.id).toBeDefined();
    expect(chunk.position_x).toBe(100);
    expect(chunk.position_y).toBe(50);
    expect(chunk.position_z).toBe(75);
  });

  it('finds chunks within radius', async () => {
    // Create test chunks
    await repo.createMany([
      { position: { x: 0, y: 0, z: 0 } },
      { position: { x: 10, y: 10, z: 10 } },
      { position: { x: 100, y: 100, z: 100 } }
    ]);

    const nearby = await repo.findWithinRadius(
      { x: 0, y: 0, z: 0 },
      20
    );

    expect(nearby).toHaveLength(2);
    expect(nearby[0].distance).toBeLessThan(20);
  });

  it('performs vector similarity search', async () => {
    const queryEmbedding = new Float32Array(384).fill(0.5);

    const similar = await repo.findSimilar(queryEmbedding, 10);

    expect(similar).toHaveLength(10);
    expect(similar[0].similarity).toBeGreaterThan(0.7);
  });
});
```

---

## 3. INTEGRATION TESTING

### API Integration Tests

```typescript
// tests/integration/api.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import { app } from '../../src/app';
import { setupTestDatabase, teardownTestDatabase } from '../utils';

describe('API Integration', () => {
  let token: string;

  beforeAll(async () => {
    await setupTestDatabase();

    // Get auth token
    const response = await request(app)
      .post('/auth/login')
      .send({ email: 'test@example.com', password: 'TestPass123!' });

    token = response.body.token;
  });

  afterAll(async () => {
    await teardownTestDatabase();
  });

  describe('POST /api/spaces', () => {
    it('creates memory space with authentication', async () => {
      const response = await request(app)
        .post('/api/spaces')
        .set('Authorization', `Bearer ${token}`)
        .send({
          name: 'Test Space',
          description: 'Integration test space'
        });

      expect(response.status).toBe(201);
      expect(response.body).toHaveProperty('id');
      expect(response.body.name).toBe('Test Space');
    });

    it('rejects without authentication', async () => {
      const response = await request(app)
        .post('/api/spaces')
        .send({ name: 'Unauthorized' });

      expect(response.status).toBe(401);
    });
  });

  describe('WebSocket Integration', () => {
    it('establishes WebSocket connection', async () => {
      const ws = new WebSocket('ws://localhost:8081/stream');

      await new Promise((resolve) => {
        ws.on('open', resolve);
      });

      expect(ws.readyState).toBe(WebSocket.OPEN);

      ws.close();
    });

    it('streams context chunks', async () => {
      const ws = new WebSocket('ws://localhost:8081/stream');
      const chunks: any[] = [];

      ws.on('message', (data) => {
        chunks.push(JSON.parse(data.toString()));
      });

      ws.send(JSON.stringify({
        type: 'context.stream.start',
        payload: { agentId: 'agent-1', position: { x: 0, y: 0, z: 0 } }
      }));

      await new Promise(resolve => setTimeout(resolve, 1000));

      expect(chunks.length).toBeGreaterThan(0);
      expect(chunks[0].type).toBe('context.chunk');
    });
  });
});
```

### Database Integration Tests

```typescript
// tests/integration/database.test.ts
import { describe, it, expect } from 'vitest';
import { TestContainers } from 'testcontainers';

describe('Database Integration', () => {
  let container: StartedTestContainer;
  let db: DatabaseConnection;

  beforeAll(async () => {
    // Start PostgreSQL container
    container = await new PostgreSqlContainer()
      .withDatabase('test')
      .withUsername('test')
      .withPassword('test')
      .start();

    db = await connectToDatabase(container.getConnectionUri());

    // Run migrations
    await runMigrations(db);
  });

  afterAll(async () => {
    await db.close();
    await container.stop();
  });

  it('handles concurrent transactions', async () => {
    const promises = Array(10).fill(0).map((_, i) => {
      return db.transaction(async (tx) => {
        await tx.query('INSERT INTO chunks (content) VALUES ($1)', [`Chunk ${i}`]);
        return i;
      });
    });

    const results = await Promise.all(promises);
    expect(results).toHaveLength(10);

    const count = await db.query('SELECT COUNT(*) FROM chunks');
    expect(count.rows[0].count).toBe('10');
  });

  it('maintains referential integrity', async () => {
    const space = await db.query('INSERT INTO spaces (name) VALUES ($1) RETURNING id', ['Test']);
    const spaceId = space.rows[0].id;

    // Try to delete space with chunks
    await expect(
      db.query('DELETE FROM spaces WHERE id = $1', [spaceId])
    ).rejects.toThrow(/foreign key constraint/);
  });
});
```

---

## 4. END-TO-END TESTING

### Playwright E2E Tests

```typescript
// tests/e2e/user-journey.spec.ts
import { test, expect } from '@playwright/test';

test.describe('User Journey', () => {
  test('complete workflow from login to query', async ({ page }) => {
    // 1. Login
    await page.goto('http://localhost:3000');
    await page.fill('[data-testid=email]', 'demo@infinite.local');
    await page.fill('[data-testid=password]', 'DemoPass123!');
    await page.click('[data-testid=login-button]');

    // Wait for dashboard
    await expect(page).toHaveURL('/dashboard');

    // 2. Create memory space
    await page.click('[data-testid=create-space]');
    await page.fill('[data-testid=space-name]', 'E2E Test Space');
    await page.click('[data-testid=create-button]');

    // 3. Upload content
    await page.setInputFiles('[data-testid=file-upload]', 'test-files/sample.ts');
    await expect(page.locator('[data-testid=upload-progress]')).toHaveText('100%');

    // 4. Navigate 3D space
    await page.click('[data-testid=3d-view]');
    await page.mouse.move(400, 300);
    await page.mouse.down();
    await page.mouse.move(500, 400);
    await page.mouse.up();

    // Verify agent moved
    const position = await page.locator('[data-testid=agent-position]').textContent();
    expect(position).not.toBe('0, 0, 0');

    // 5. Submit query
    await page.fill('[data-testid=query-input]', 'Explain the authentication flow');
    await page.keyboard.press('Enter');

    // Wait for response
    await expect(page.locator('[data-testid=response]')).toContainText('authentication');

    // 6. Verify context loaded
    const contextCount = await page.locator('[data-testid=context-meter]').textContent();
    expect(parseInt(contextCount!)).toBeGreaterThan(0);
  });

  test('handles errors gracefully', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Test network failure
    await page.route('**/api/**', route => route.abort());

    await page.fill('[data-testid=email]', 'test@example.com');
    await page.fill('[data-testid=password]', 'password');
    await page.click('[data-testid=login-button]');

    await expect(page.locator('[data-testid=error-message]'))
      .toContainText('Network error');
  });
});
```

### Mobile E2E Tests

```typescript
test.describe('Mobile Experience', () => {
  test.use({
    viewport: { width: 375, height: 667 },
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)',
    hasTouch: true
  });

  test('responsive layout works on mobile', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Check hamburger menu
    await expect(page.locator('[data-testid=mobile-menu]')).toBeVisible();

    // Test touch navigation
    await page.tap('[data-testid=mobile-menu]');
    await expect(page.locator('[data-testid=nav-drawer]')).toBeVisible();

    // Test touch gestures in 3D view
    await page.tap('[data-testid=3d-view]');
    await page.locator('[data-testid=3d-canvas]').tap({ position: { x: 100, y: 100 } });

    // Pinch to zoom
    await page.touchscreen.pinch(100, 100, 200, 200);
  });
});
```

---

## 5. PERFORMANCE TESTING

### Load Testing with k6

```javascript
// tests/performance/load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp to 200
    { duration: '5m', target: 200 },  // Stay at 200
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    errors: ['rate<0.01'],             // Error rate under 1%
  },
};

export default function () {
  // Login
  const loginRes = http.post('http://localhost:8080/auth/login', {
    email: 'test@example.com',
    password: 'TestPass123!'
  });

  check(loginRes, {
    'login successful': (r) => r.status === 200,
    'token received': (r) => r.json('token') !== undefined,
  });

  errorRate.add(loginRes.status !== 200);

  const token = loginRes.json('token');
  const headers = { Authorization: `Bearer ${token}` };

  // Spatial query
  const spatialRes = http.get(
    'http://localhost:8080/api/chunks?position=0,0,0&radius=100',
    { headers }
  );

  check(spatialRes, {
    'spatial query successful': (r) => r.status === 200,
    'chunks returned': (r) => r.json('chunks').length > 0,
  });

  // WebSocket test
  const ws = http.ws('ws://localhost:8081/stream', null, function (socket) {
    socket.on('open', () => {
      socket.send(JSON.stringify({
        type: 'context.stream.start',
        payload: { agentId: 'test-agent' }
      }));
    });

    socket.on('message', (data) => {
      check(data, {
        'websocket message received': (d) => d !== null,
      });
    });

    socket.setTimeout(() => socket.close(), 5000);
  });

  sleep(1);
}
```

### Stress Testing

```javascript
// tests/performance/stress-test.js
export const options = {
  scenarios: {
    stress: {
      executor: 'ramping-arrival-rate',
      startRate: 1,
      timeUnit: '1s',
      preAllocatedVUs: 100,
      maxVUs: 1000,
      stages: [
        { duration: '2m', target: 10 },   // Below normal load
        { duration: '5m', target: 100 },  // Normal load
        { duration: '2m', target: 300 },  // Around breaking point
        { duration: '5m', target: 300 },  // Stay at breaking point
        { duration: '2m', target: 500 },  // Beyond breaking point
        { duration: '10m', target: 500 }, // Stay beyond breaking
        { duration: '2m', target: 0 },    // Recovery
      ],
    },
  },
};
```

### Memory Profiling

```typescript
// tests/performance/memory-profile.ts
import { performance } from 'perf_hooks';
import v8 from 'v8';

class MemoryProfiler {
  private baseline: number;
  private snapshots: HeapSnapshot[] = [];

  start(): void {
    // Force garbage collection
    if (global.gc) {
      global.gc();
    }

    this.baseline = process.memoryUsage().heapUsed;
    console.log(`Baseline memory: ${this.formatBytes(this.baseline)}`);
  }

  async profileChunkLoading(): Promise<void> {
    const iterations = 1000;
    const chunks: any[] = [];

    for (let i = 0; i < iterations; i++) {
      chunks.push(await this.loadChunk(i));

      if (i % 100 === 0) {
        this.takeSnapshot(`After ${i} chunks`);
      }
    }

    // Check for memory leaks
    this.analyzeSnapshots();
  }

  private takeSnapshot(label: string): void {
    const heap = v8.getHeapSnapshot();
    const usage = process.memoryUsage();

    this.snapshots.push({
      label,
      heap,
      heapUsed: usage.heapUsed,
      external: usage.external,
      timestamp: Date.now()
    });

    console.log(`${label}: ${this.formatBytes(usage.heapUsed)}`);
  }

  private analyzeSnapshots(): void {
    // Check for linear memory growth (leak indicator)
    const growthRate = this.calculateGrowthRate();

    if (growthRate > 0.1) { // 10% growth per iteration
      console.error('Potential memory leak detected!');
      this.dumpHeapSnapshot();
    }
  }
}
```

---

## 6. SECURITY TESTING

### Security Test Suite

```typescript
// tests/security/security.test.ts
describe('Security Tests', () => {
  describe('Authentication Security', () => {
    it('prevents brute force attacks', async () => {
      const attempts = 10;
      const results = [];

      for (let i = 0; i < attempts; i++) {
        const response = await request(app)
          .post('/auth/login')
          .send({
            email: 'test@example.com',
            password: 'WrongPassword' + i
          });

        results.push(response.status);
      }

      // Should be rate limited after 5 attempts
      expect(results.slice(5)).toContain(429);
    });

    it('validates JWT signatures', async () => {
      const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.tampered.signature';

      const response = await request(app)
        .get('/api/protected')
        .set('Authorization', `Bearer ${tamperedToken}`);

      expect(response.status).toBe(401);
    });
  });

  describe('Input Validation', () => {
    it('prevents SQL injection', async () => {
      const maliciousInput = "'; DROP TABLE users; --";

      const response = await request(app)
        .get('/api/search')
        .query({ q: maliciousInput });

      expect(response.status).toBe(200);

      // Verify table still exists
      const tableExists = await db.query(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users')"
      );
      expect(tableExists.rows[0].exists).toBe(true);
    });

    it('prevents XSS attacks', async () => {
      const xssPayload = '<script>alert("XSS")</script>';

      const response = await request(app)
        .post('/api/comments')
        .send({ content: xssPayload });

      expect(response.body.content).not.toContain('<script>');
      expect(response.body.content).toBe('&lt;script&gt;alert("XSS")&lt;/script&gt;');
    });

    it('prevents path traversal', async () => {
      const response = await request(app)
        .get('/api/files/../../../etc/passwd');

      expect(response.status).toBe(400);
    });
  });

  describe('Authorization Security', () => {
    it('enforces role-based access', async () => {
      const userToken = await getToken('user@example.com');

      const response = await request(app)
        .delete('/api/admin/users/123')
        .set('Authorization', `Bearer ${userToken}`);

      expect(response.status).toBe(403);
    });

    it('prevents privilege escalation', async () => {
      const userToken = await getToken('user@example.com');

      const response = await request(app)
        .put('/api/users/self')
        .set('Authorization', `Bearer ${userToken}`)
        .send({ roles: ['admin'] });

      expect(response.status).toBe(403);
    });
  });
});
```

### Penetration Testing

```yaml
# tests/security/zap-scan.yaml
env:
  contexts:
    - name: "Infinite"
      urls:
        - "http://localhost:3000"
      authentication:
        method: "json"
        loginUrl: "http://localhost:8080/auth/login"
        loginRequestData: '{"email":"test@example.com","password":"TestPass123!"}'

  policies:
    - name: "API Security"
      rules:
        - id: 10003  # Vulnerable JS Library
          threshold: "medium"
        - id: 10010  # Cookie No HttpOnly
          threshold: "high"
        - id: 10011  # Cookie Without Secure Flag
          threshold: "high"
        - id: 10015  # Incomplete Set of Headers
          threshold: "medium"
```

---

## 7. TEST DATA MANAGEMENT

### Test Data Factory

```typescript
// tests/factories/index.ts
import { Factory } from 'fishery';
import { faker } from '@faker-js/faker';

export const userFactory = Factory.define<User>(() => ({
  id: faker.datatype.uuid(),
  email: faker.internet.email(),
  username: faker.internet.userName(),
  password: faker.internet.password(),
  createdAt: faker.date.past()
}));

export const chunkFactory = Factory.define<Chunk>(() => ({
  id: faker.datatype.uuid(),
  content: faker.lorem.paragraphs(3),
  tokens: faker.datatype.number({ min: 100, max: 500 }),
  position: {
    x: faker.datatype.float({ min: -1000, max: 1000 }),
    y: faker.datatype.float({ min: -500, max: 500 }),
    z: faker.datatype.float({ min: -1000, max: 1000 })
  },
  embedding: Array(384).fill(0).map(() => faker.datatype.float({ min: -1, max: 1 }))
}));

export const agentFactory = Factory.define<Agent>(() => ({
  id: faker.datatype.uuid(),
  name: faker.name.firstName() + ' Agent',
  model: faker.helpers.arrayElement(['llama-8b', 'mistral-7b', 'phi-3']),
  position: {
    x: faker.datatype.float({ min: -100, max: 100 }),
    y: 0,
    z: faker.datatype.float({ min: -100, max: 100 })
  },
  status: faker.helpers.arrayElement(['idle', 'active', 'loading'])
}));

// Usage
const testUser = userFactory.build();
const testChunks = chunkFactory.buildList(10);
const testAgent = agentFactory.build({ model: 'llama-8b' });
```

---

## 8. CONTINUOUS TESTING

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:unit

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          # Simple password OK for ephemeral CI test database (not production!)
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Run integration tests
        run: npm run test:integration

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:e2e

      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/

  performance-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Run k6 tests
        uses: grafana/k6-action@v0.3.0
        with:
          filename: tests/performance/load-test.js
```

---

## 9. TEST COVERAGE REQUIREMENTS

### Coverage Targets

```javascript
// vitest.config.ts
export default defineConfig({
  test: {
    coverage: {
      provider: 'c8',
      reporter: ['text', 'json', 'html', 'lcov'],
      statements: 80,
      branches: 75,
      functions: 80,
      lines: 80,

      exclude: [
        'node_modules',
        'tests',
        '**/*.test.ts',
        '**/*.spec.ts',
        '**/index.ts',
        '**/*.d.ts'
      ],

      watermarks: {
        statements: [80, 90],
        branches: [75, 85],
        functions: [80, 90],
        lines: [80, 90]
      }
    }
  }
});
```

### Coverage Report

```bash
# Generate coverage report
npm run test:coverage

# Output
------------------------|---------|----------|---------|---------|
File                    | % Stmts | % Branch | % Funcs | % Lines |
------------------------|---------|----------|---------|---------|
All files               |   85.32 |    78.45 |   82.10 |   85.32 |
 src/                   |   88.20 |    81.30 |   85.60 |   88.20 |
  chunking.service.ts   |   92.45 |    85.20 |   90.00 |   92.45 |
  spatial.service.ts    |   86.70 |    79.50 |   84.30 |   86.70 |
  auth.service.ts       |   89.20 |    82.10 |   87.50 |   89.20 |
------------------------|---------|----------|---------|---------|
```

---

## 10. TEST REPORTING

### Test Dashboard

```html
<!-- test-report.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Infinite Test Results</title>
</head>
<body>
  <h1>Test Results Dashboard</h1>

  <div class="metrics">
    <div class="metric">
      <h3>Unit Tests</h3>
      <p>456/456 Passed</p>
      <p>Coverage: 85.3%</p>
    </div>

    <div class="metric">
      <h3>Integration Tests</h3>
      <p>89/89 Passed</p>
      <p>Duration: 2m 34s</p>
    </div>

    <div class="metric">
      <h3>E2E Tests</h3>
      <p>23/23 Passed</p>
      <p>Browsers: Chrome, Firefox, Safari</p>
    </div>

    <div class="metric">
      <h3>Performance</h3>
      <p>P95 Latency: 234ms</p>
      <p>Error Rate: 0.08%</p>
    </div>
  </div>

  <div class="trends">
    <canvas id="coverage-trend"></canvas>
    <canvas id="performance-trend"></canvas>
  </div>
</body>
</html>
```

---

## SUCCESS METRICS

### Test Quality
- >80% code coverage
- <2% test flakiness
- <5 minute test suite runtime
- 100% critical path coverage

### Test Effectiveness
- >95% bug detection rate
- <5% bugs escape to production
- <24 hour bug fix time
- >90% regression prevention

### Performance Standards
- P95 latency <500ms under load
- 0% data corruption
- <0.1% error rate
- 99.9% uptime

---

**Testing Framework:** Vitest, Jest, Playwright
**Coverage Target:** 80% minimum
**Test Types:** Unit, Integration, E2E, Performance, Security
**CI/CD:** GitHub Actions with parallel execution