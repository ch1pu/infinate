# INFINITE: Database Seeding Plan
**Test Data and Initial Content Strategy**

---

## EXECUTIVE SUMMARY

This document provides a comprehensive plan for seeding the Infinite database with realistic test data, demo content, and initial configuration to support development, testing, and demonstrations of the spatial context system.

---

## 1. SEEDING STRATEGY OVERVIEW

### Data Categories

```typescript
interface SeedingCategories {
  system: {
    defaultUsers: User[];
    defaultRoles: Role[];
    systemConfig: Config[];
  };

  demo: {
    sampleCodebase: CodeProject[];
    documentation: Document[];
    conversations: ChatHistory[];
  };

  test: {
    performanceData: LargeDataset[];
    edgeCases: EdgeCase[];
    stressTestData: StressData[];
  };

  development: {
    mockUsers: User[];
    mockAgents: Agent[];
    mockQueries: Query[];
  };
}
```

### Seeding Environments

| Environment | Data Volume | Purpose |
|-------------|------------|---------|
| Development | 10K chunks | Feature development |
| Testing | 100K chunks | Integration tests |
| Demo | 50K chunks | Product demonstrations |
| Performance | 1M chunks | Load testing |
| Production | Minimal | Only system data |

---

## 2. SYSTEM SEED DATA

### Default Users and Roles

```typescript
// seeds/system/users.seed.ts
export const systemUsers = [
  {
    id: 'system-admin',
    email: 'admin@infinite.local',
    username: 'admin',
    password: 'ChangeMe123!', // Will be hashed
    roles: ['admin'],
    permissions: ['*:*:*'],
    is_active: true,
    is_verified: true,
    profile: {
      name: 'System Administrator',
      avatar: 'admin-avatar.png'
    }
  },
  {
    id: 'demo-user',
    email: 'demo@infinite.local',
    username: 'demo',
    password: 'DemoUser123!',
    roles: ['developer'],
    permissions: ['space:*:own', 'agent:*:own'],
    is_active: true,
    is_verified: true,
    profile: {
      name: 'Demo User',
      avatar: 'demo-avatar.png'
    }
  },
  {
    id: 'test-analyst',
    email: 'analyst@infinite.local',
    username: 'analyst',
    password: 'Analyst123!',
    roles: ['analyst'],
    permissions: ['space:read:all', 'query:create:own'],
    is_active: true,
    is_verified: true
  }
];

// seeds/system/roles.seed.ts
export const systemRoles = [
  {
    name: 'admin',
    description: 'Full system access',
    permissions: ['*:*:*'],
    priority: 100
  },
  {
    name: 'developer',
    description: 'Development access',
    permissions: [
      'space:*:team',
      'agent:*:own',
      'chunk:*:team',
      'query:*:own'
    ],
    priority: 50
  },
  {
    name: 'analyst',
    description: 'Read and analyze',
    permissions: [
      'space:read:all',
      'chunk:read:all',
      'query:create:own',
      'metrics:read:team'
    ],
    priority: 30
  },
  {
    name: 'viewer',
    description: 'Read only access',
    permissions: [
      'space:read:public',
      'chunk:read:public',
      'metrics:read:public'
    ],
    priority: 10
  }
];
```

### System Configuration

```typescript
// seeds/system/config.seed.ts
export const systemConfig = [
  {
    key: 'chunking.default_size',
    value: 300,
    type: 'integer',
    description: 'Default chunk size in tokens'
  },
  {
    key: 'chunking.default_overlap',
    value: 50,
    type: 'integer',
    description: 'Default overlap between chunks'
  },
  {
    key: 'embedding.default_model',
    value: 'bge-small-en-v1.5',
    type: 'string',
    description: 'Default embedding model'
  },
  {
    key: 'spatial.octree_max_depth',
    value: 8,
    type: 'integer',
    description: 'Maximum octree depth'
  },
  {
    key: 'spatial.octree_max_items',
    value: 8,
    type: 'integer',
    description: 'Maximum items per octree node'
  },
  {
    key: 'streaming.batch_size',
    value: 10,
    type: 'integer',
    description: 'Context streaming batch size'
  }
];
```

---

## 3. DEMO CODEBASE SEED

### Sample Project Structure

```typescript
// seeds/demo/codebase.seed.ts
export async function seedDemoCodebase(): Promise<void> {
  // Create demo space
  const space = await createMemorySpace({
    name: 'Demo React Application',
    description: 'Full-stack React application with Node.js backend',
    config: {
      chunk_size: 300,
      chunk_overlap: 50,
      embedding_model: 'bge-small-en-v1.5'
    }
  });

  // Seed frontend code
  await seedFrontendCode(space.id);

  // Seed backend code
  await seedBackendCode(space.id);

  // Seed documentation
  await seedDocumentation(space.id);

  // Generate embeddings
  await generateEmbeddings(space.id);

  // Build spatial index
  await buildSpatialIndex(space.id);
}

async function seedFrontendCode(spaceId: string): Promise<void> {
  const frontendFiles = [
    {
      path: 'src/App.tsx',
      content: `
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import { AuthProvider } from './contexts/AuthContext';
import { api } from './services/api';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await api.getCurrentUser();
        setUser(response.data);
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <ThemeProvider theme={theme}>
      <AuthProvider value={{ user, setUser }}>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/" element={<Navigate to="/dashboard" />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
      `,
      type: 'code',
      language: 'typescript'
    },
    {
      path: 'src/components/Dashboard.tsx',
      content: `
import React, { useState, useEffect } from 'react';
import { Grid, Paper, Typography } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import DataVisualization from './DataVisualization';
import MetricsPanel from './MetricsPanel';
import ActivityFeed from './ActivityFeed';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState(null);
  const [activities, setActivities] = useState([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    const [metricsData, activitiesData] = await Promise.all([
      api.getMetrics(),
      api.getActivities()
    ]);
    setMetrics(metricsData);
    setActivities(activitiesData);
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h4">
          Welcome back, {user?.name}!
        </Typography>
      </Grid>
      <Grid item xs={12} md={8}>
        <DataVisualization data={metrics} />
      </Grid>
      <Grid item xs={12} md={4}>
        <MetricsPanel metrics={metrics} />
      </Grid>
      <Grid item xs={12}>
        <ActivityFeed activities={activities} />
      </Grid>
    </Grid>
  );
};

export default Dashboard;
      `,
      type: 'code',
      language: 'typescript'
    },
    // Add more frontend files...
  ];

  for (const file of frontendFiles) {
    await chunkAndStore(file, spaceId);
  }
}
```

### Backend Code Seeding

```typescript
async function seedBackendCode(spaceId: string): Promise<void> {
  const backendFiles = [
    {
      path: 'src/server.ts',
      content: `
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { createServer } from 'http';
import { Server } from 'socket.io';
import { authRouter } from './routes/auth';
import { apiRouter } from './routes/api';
import { errorHandler } from './middleware/errorHandler';
import { connectDatabase } from './database';

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:3000'
  }
});

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(morgan('combined'));

// Routes
app.use('/auth', authRouter);
app.use('/api', apiRouter);

// WebSocket handling
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  socket.on('subscribe', (room) => {
    socket.join(room);
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

// Error handling
app.use(errorHandler);

// Start server
const PORT = process.env.PORT || 3001;

async function start() {
  await connectDatabase();
  httpServer.listen(PORT, () => {
    console.log(\`Server running on port \${PORT}\`);
  });
}

start().catch(console.error);
      `,
      type: 'code',
      language: 'typescript'
    },
    {
      path: 'src/controllers/auth.controller.ts',
      content: `
import { Request, Response, NextFunction } from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { User } from '../models/User';
import { validateEmail, validatePassword } from '../utils/validation';

export class AuthController {
  async register(req: Request, res: Response, next: NextFunction) {
    try {
      const { email, password, name } = req.body;

      // Validation
      if (!validateEmail(email)) {
        return res.status(400).json({ error: 'Invalid email' });
      }

      if (!validatePassword(password)) {
        return res.status(400).json({
          error: 'Password must be at least 8 characters'
        });
      }

      // Check existing user
      const existing = await User.findOne({ email });
      if (existing) {
        return res.status(409).json({ error: 'User already exists' });
      }

      // Hash password
      const hashedPassword = await bcrypt.hash(password, 10);

      // Create user
      const user = await User.create({
        email,
        password: hashedPassword,
        name
      });

      // Generate token
      const token = jwt.sign(
        { userId: user.id },
        process.env.JWT_SECRET!,
        { expiresIn: '7d' }
      );

      res.status(201).json({
        user: { id: user.id, email: user.email, name: user.name },
        token
      });
    } catch (error) {
      next(error);
    }
  }

  async login(req: Request, res: Response, next: NextFunction) {
    try {
      const { email, password } = req.body;

      // Find user
      const user = await User.findOne({ email });
      if (!user) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      // Verify password
      const valid = await bcrypt.compare(password, user.password);
      if (!valid) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      // Generate token
      const token = jwt.sign(
        { userId: user.id },
        process.env.JWT_SECRET!,
        { expiresIn: '7d' }
      );

      res.json({
        user: { id: user.id, email: user.email, name: user.name },
        token
      });
    } catch (error) {
      next(error);
    }
  }
}
      `,
      type: 'code',
      language: 'typescript'
    }
    // Add more backend files...
  ];

  for (const file of backendFiles) {
    await chunkAndStore(file, spaceId);
  }
}
```

---

## 4. DOCUMENTATION SEEDING

### Technical Documentation

```typescript
// seeds/demo/documentation.seed.ts
export const documentationSeed = [
  {
    title: 'API Documentation',
    content: `
# API Documentation

## Authentication

All API requests require authentication using JWT tokens.

### POST /auth/login
Authenticate user and receive access token.

**Request:**
\`\`\`json
{
  "email": "user@example.com",
  "password": "securepassword"
}
\`\`\`

**Response:**
\`\`\`json
{
  "token": "eyJ...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
\`\`\`

### Headers
Include the token in subsequent requests:
\`\`\`
Authorization: Bearer eyJ...
\`\`\`

## Endpoints

### GET /api/users
Retrieve list of users.

### GET /api/users/:id
Get specific user details.

### POST /api/users
Create new user.

### PUT /api/users/:id
Update user information.

### DELETE /api/users/:id
Delete user account.
    `,
    type: 'documentation',
    category: 'api'
  },
  {
    title: 'Architecture Overview',
    content: `
# System Architecture

## Overview
The system follows a microservices architecture with the following components:

1. **Frontend**: React-based SPA
2. **API Gateway**: Node.js/Express
3. **Authentication Service**: JWT-based auth
4. **Database**: PostgreSQL with Redis cache
5. **Message Queue**: RabbitMQ for async operations

## Data Flow
1. User interacts with React frontend
2. Frontend makes API calls to backend
3. Backend validates request and processes
4. Data is stored in PostgreSQL
5. Cache is updated in Redis
6. Response sent back to frontend

## Scalability
- Horizontal scaling through Docker Swarm
- Load balancing with Nginx
- Database replication for read scaling
- Redis clustering for cache distribution
    `,
    type: 'documentation',
    category: 'architecture'
  }
];
```

---

## 5. CONVERSATION HISTORY SEEDING

### Sample Conversations

```typescript
// seeds/demo/conversations.seed.ts
export const conversationSeed = [
  {
    id: 'conv-001',
    participants: ['user-001', 'assistant'],
    messages: [
      {
        role: 'user',
        content: 'How do I implement authentication in the app?',
        timestamp: '2024-01-15T10:00:00Z'
      },
      {
        role: 'assistant',
        content: `To implement authentication, you'll need to:

1. Set up the auth controller in src/controllers/auth.controller.ts
2. Configure JWT tokens with a secure secret
3. Implement login and register endpoints
4. Add authentication middleware to protected routes
5. Store tokens securely on the frontend

The auth controller already handles password hashing with bcrypt and
generates JWT tokens. Make sure to validate input and handle errors properly.`,
        timestamp: '2024-01-15T10:00:15Z'
      },
      {
        role: 'user',
        content: 'What about session management?',
        timestamp: '2024-01-15T10:01:00Z'
      },
      {
        role: 'assistant',
        content: `For session management, you have several options:

1. **JWT with Refresh Tokens**: Store short-lived access tokens (15min)
   and longer-lived refresh tokens (7 days)

2. **Redis Sessions**: Store session data in Redis with TTL

3. **Database Sessions**: Store in PostgreSQL with cleanup job

The current implementation uses JWT. To add refresh tokens:
- Generate both access and refresh tokens on login
- Store refresh token in httpOnly cookie
- Implement /auth/refresh endpoint
- Rotate refresh tokens on use`,
        timestamp: '2024-01-15T10:01:20Z'
      }
    ]
  },
  {
    id: 'conv-002',
    participants: ['user-002', 'assistant'],
    messages: [
      {
        role: 'user',
        content: 'Explain the database schema',
        timestamp: '2024-01-16T14:30:00Z'
      },
      {
        role: 'assistant',
        content: `The database schema includes:

**users** table:
- id (UUID, primary key)
- email (unique)
- password_hash
- name
- created_at, updated_at

**sessions** table:
- id (UUID)
- user_id (foreign key)
- token_hash
- expires_at

**projects** table:
- id (UUID)
- user_id (foreign key)
- name
- description
- settings (JSONB)

Relationships:
- Users have many Sessions (1:N)
- Users have many Projects (1:N)
- Projects have many Tasks (1:N)`,
        timestamp: '2024-01-16T14:30:30Z'
      }
    ]
  }
];
```

---

## 6. PERFORMANCE TEST DATA

### Large Dataset Generation

```typescript
// seeds/test/performance.seed.ts
export async function generatePerformanceData(): Promise<void> {
  const CHUNK_COUNT = 100000;
  const BATCH_SIZE = 1000;

  console.log(`Generating ${CHUNK_COUNT} chunks for performance testing...`);

  for (let i = 0; i < CHUNK_COUNT; i += BATCH_SIZE) {
    const chunks = [];

    for (let j = 0; j < BATCH_SIZE && i + j < CHUNK_COUNT; j++) {
      chunks.push(generateRandomChunk(i + j));
    }

    await bulkInsertChunks(chunks);

    console.log(`Inserted ${i + BATCH_SIZE} / ${CHUNK_COUNT} chunks`);
  }

  // Generate embeddings
  await generateEmbeddingsForAll();

  // Build spatial index
  await rebuildSpatialIndex();
}

function generateRandomChunk(index: number): Chunk {
  const types = ['code', 'documentation', 'conversation', 'data'];
  const languages = ['typescript', 'python', 'rust', 'go', 'java'];

  return {
    content: generateRealisticContent(index),
    type: types[index % types.length],
    language: languages[index % languages.length],
    tokens: 200 + Math.floor(Math.random() * 300),
    position_x: (Math.random() - 0.5) * 2000,
    position_y: (Math.random() - 0.5) * 1000,
    position_z: (Math.random() - 0.5) * 2000,
    metadata: {
      synthetic: true,
      index: index,
      batch: Math.floor(index / 1000)
    }
  };
}

function generateRealisticContent(index: number): string {
  const templates = [
    `function processData${index}(input: any): Result {
  // Validate input
  if (!input || typeof input !== 'object') {
    throw new Error('Invalid input');
  }

  // Process data
  const result = transformData(input);

  // Apply business logic
  const processed = applyRules(result);

  return {
    id: '${index}',
    data: processed,
    timestamp: Date.now()
  };
}`,
    `class DataProcessor${index} {
  private config: Config;

  constructor(config: Config) {
    this.config = config;
  }

  async process(data: any[]): Promise<ProcessedData> {
    const validated = await this.validate(data);
    const transformed = await this.transform(validated);
    return this.optimize(transformed);
  }
}`,
    `# Documentation Section ${index}

This section covers the implementation details of feature ${index}.

## Overview
The feature processes incoming data and applies transformations.

## Implementation
1. Data validation
2. Transformation pipeline
3. Output generation

## Usage
\`\`\`typescript
const processor = new Processor();
const result = await processor.run(data);
\`\`\`
`
  ];

  return templates[index % templates.length];
}
```

---

## 7. EDGE CASE DATA

### Boundary Testing Data

```typescript
// seeds/test/edge-cases.seed.ts
export const edgeCaseSeed = [
  {
    name: 'Empty chunk',
    content: '',
    tokens: 0,
    position: { x: 0, y: 0, z: 0 }
  },
  {
    name: 'Maximum size chunk',
    content: 'x'.repeat(10000), // Very long content
    tokens: 600, // Maximum tokens
    position: { x: 1000, y: 500, z: 1000 } // Boundary position
  },
  {
    name: 'Unicode content',
    content: '你好世界 🌍 مرحبا بالعالم Здравствуй мир',
    tokens: 50,
    position: { x: -500, y: 0, z: 500 }
  },
  {
    name: 'Special characters',
    content: '!@#$%^&*()_+-=[]{}|;\':",./<>?`~',
    tokens: 20,
    position: { x: 100, y: -100, z: 100 }
  },
  {
    name: 'Nested JSON',
    content: JSON.stringify({
      level1: {
        level2: {
          level3: {
            level4: {
              level5: 'deeply nested'
            }
          }
        }
      }
    }, null, 2),
    tokens: 100,
    position: { x: 0, y: 250, z: -250 }
  }
];
```

---

## 8. SEEDING SCRIPT

### Main Seeding Orchestrator

```typescript
// seeds/index.ts
import { PrismaClient } from '@prisma/client';
import { systemUsers, systemRoles, systemConfig } from './system';
import { seedDemoCodebase } from './demo/codebase.seed';
import { generatePerformanceData } from './test/performance.seed';

const prisma = new PrismaClient();

async function main() {
  const environment = process.env.SEED_ENV || 'development';

  console.log(`Seeding database for ${environment} environment...`);

  // Always seed system data
  await seedSystemData();

  // Environment-specific seeding
  switch (environment) {
    case 'development':
      await seedDevelopmentData();
      break;
    case 'test':
      await seedTestData();
      break;
    case 'demo':
      await seedDemoData();
      break;
    case 'performance':
      await seedPerformanceData();
      break;
    case 'production':
      console.log('Production seeding - only system data added');
      break;
  }

  console.log('Seeding completed successfully');
}

async function seedSystemData() {
  // Seed roles
  for (const role of systemRoles) {
    await prisma.role.upsert({
      where: { name: role.name },
      update: {},
      create: role
    });
  }

  // Seed system users
  for (const user of systemUsers) {
    const hashedPassword = await hashPassword(user.password);
    await prisma.user.upsert({
      where: { email: user.email },
      update: {},
      create: {
        ...user,
        password: hashedPassword
      }
    });
  }

  // Seed configuration
  for (const config of systemConfig) {
    await prisma.config.upsert({
      where: { key: config.key },
      update: { value: config.value },
      create: config
    });
  }
}

async function seedDevelopmentData() {
  console.log('Seeding development data...');

  // Create demo space with sample code
  await seedDemoCodebase();

  // Add sample agents
  await createSampleAgents();

  // Add query history
  await createQueryHistory();

  console.log('Development data seeded');
}

async function seedTestData() {
  console.log('Seeding test data...');

  // Smaller dataset for faster tests
  await generateTestDataset(1000);

  // Edge cases
  await seedEdgeCases();

  console.log('Test data seeded');
}

async function seedDemoData() {
  console.log('Seeding demo data...');

  // Complete demo environment
  await seedDemoCodebase();
  await seedDocumentation();
  await seedConversations();
  await createDemoAgents();

  console.log('Demo data seeded');
}

async function seedPerformanceData() {
  console.log('Seeding performance test data...');

  // Large dataset for load testing
  await generatePerformanceData();

  console.log('Performance data seeded');
}

// Run seeding
main()
  .catch((error) => {
    console.error('Seeding failed:', error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
```

---

## 9. SEEDING COMMANDS

### Package.json Scripts

```json
{
  "scripts": {
    "seed": "tsx seeds/index.ts",
    "seed:dev": "SEED_ENV=development tsx seeds/index.ts",
    "seed:test": "SEED_ENV=test tsx seeds/index.ts",
    "seed:demo": "SEED_ENV=demo tsx seeds/index.ts",
    "seed:perf": "SEED_ENV=performance tsx seeds/index.ts",
    "seed:prod": "SEED_ENV=production tsx seeds/index.ts",
    "seed:reset": "npm run db:reset && npm run seed:dev",
    "db:reset": "prisma migrate reset --force"
  }
}
```

### Docker Seeding

```dockerfile
# Dockerfile.seed
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
COPY prisma ./prisma
COPY seeds ./seeds

RUN npm ci

ENV DATABASE_URL=postgresql://user:password@db:5432/infinite

CMD ["npm", "run", "seed:demo"]
```

---

## 10. VALIDATION & VERIFICATION

### Post-Seeding Validation

```typescript
// seeds/validate.ts
export async function validateSeeding(): Promise<ValidationResult> {
  const checks = [];

  // Check user count
  const userCount = await prisma.user.count();
  checks.push({
    name: 'Users seeded',
    expected: 3,
    actual: userCount,
    passed: userCount >= 3
  });

  // Check chunk count
  const chunkCount = await prisma.chunk.count();
  const minChunks = getMinChunksForEnvironment();
  checks.push({
    name: 'Chunks seeded',
    expected: minChunks,
    actual: chunkCount,
    passed: chunkCount >= minChunks
  });

  // Check embeddings
  const embeddingCount = await prisma.chunk.count({
    where: { embedding: { not: null } }
  });
  checks.push({
    name: 'Embeddings generated',
    expected: chunkCount,
    actual: embeddingCount,
    passed: embeddingCount === chunkCount
  });

  // Check spatial index
  const octreeNodes = await prisma.octreeNode.count();
  checks.push({
    name: 'Spatial index built',
    expected: true,
    actual: octreeNodes > 0,
    passed: octreeNodes > 0
  });

  return {
    passed: checks.every(c => c.passed),
    checks
  };
}
```

---

## SUCCESS METRICS

### Seeding Performance
- Development: <30 seconds
- Test: <1 minute
- Demo: <2 minutes
- Performance: <30 minutes for 1M chunks

### Data Quality
- 100% valid embeddings
- Proper spatial distribution
- Realistic content variety
- No duplicate chunks

### Environment Readiness
- All features testable
- Realistic demo scenarios
- Performance baselines established
- Edge cases covered

---

**Environments:** Development, Test, Demo, Performance, Production
**Data Volume:** 1K to 1M chunks depending on environment
**Seed Time:** 30 seconds to 30 minutes
**Validation:** Comprehensive post-seeding checks