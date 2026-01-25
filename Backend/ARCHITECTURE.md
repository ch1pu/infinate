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

# Backend Architecture
**Core API & Spatial Engine**

---

## OVERVIEW

The backend provides the core API server, spatial memory engine, and AI inference coordination. It manages agent lifecycles, handles context streaming, performs semantic search via NPU acceleration, and orchestrates the entire spatial context system.

---

## 1. TECHNOLOGY STACK

### Core Technologies
- **Node.js 20 LTS** - JavaScript runtime
- **TypeScript 5.3+** - Type safety
- **Express.js** - Web framework
- **Socket.io** - Real-time WebSocket communication
- **PostgreSQL 16** - Metadata storage
- **Redis 7** - Caching and pub/sub
- **Python 3.11** - Spatial engine & AI inference
- **ONNX Runtime** - NPU acceleration
- **llama.cpp** - Local LLM inference

### Key Libraries
- **Fastify** - Alternative high-performance HTTP server
- **Prisma** - ORM for PostgreSQL
- **Bull** - Job queue management
- **Winston** - Logging
- **Jest** - Testing framework
- **PM2** - Process management

---

## 2. SERVICE ARCHITECTURE

```
Backend/
├── api-server/                 # Node.js API server
│   ├── src/
│   │   ├── controllers/        # Request handlers
│   │   ├── services/          # Business logic
│   │   ├── models/            # Data models
│   │   ├── middleware/        # Express middleware
│   │   ├── routes/            # API routes
│   │   ├── websocket/         # Socket.io handlers
│   │   ├── queue/             # Job queue processors
│   │   └── utils/             # Utility functions
│   └── package.json
│
├── spatial-engine/             # Python spatial indexing
│   ├── core/
│   │   ├── octree.py          # Octree implementation
│   │   ├── embedding.py       # NPU embedding generation
│   │   ├── streaming.py       # Context streaming
│   │   └── search.py          # Semantic search
│   ├── api/
│   │   ├── server.py          # FastAPI server
│   │   └── routes.py          # API endpoints
│   └── requirements.txt
│
├── inference-engine/           # Python AI inference
│   ├── models/
│   │   ├── llama.py           # Llama model wrapper
│   │   ├── mistral.py         # Mistral model wrapper
│   │   └── phi.py             # Phi-3 model wrapper
│   ├── server.py              # Inference server
│   └── requirements.txt
│
└── shared/                     # Shared utilities
    ├── types/                  # TypeScript types
    ├── proto/                  # Protocol buffers
    └── config/                 # Configuration files
```

---

## 3. API SERVER (Node.js)

### 3.1 Express Application Structure

**src/app.ts:**
```typescript
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import { createServer } from 'http';
import { Server } from 'socket.io';
import { errorHandler } from './middleware/errorHandler';
import { authMiddleware } from './middleware/auth';
import { rateLimiter } from './middleware/rateLimiter';
import { routes } from './routes';
import { initWebSocket } from './websocket';
import { initQueue } from './queue';

export function createApp() {
  const app = express();
  const httpServer = createServer(app);
  const io = new Server(httpServer, {
    cors: {
      origin: process.env.FRONTEND_URL || 'http://localhost:3000',
      credentials: true
    }
  });

  // Middleware
  app.use(helmet());
  app.use(cors());
  app.use(compression());
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true }));

  // Rate limiting
  app.use('/api', rateLimiter);

  // Authentication
  app.use('/api/protected', authMiddleware);

  // API Routes
  app.use('/api/v1', routes);

  // Health check
  app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date() });
  });

  // WebSocket initialization
  initWebSocket(io);

  // Job queue initialization
  initQueue();

  // Error handling
  app.use(errorHandler);

  return { app, httpServer, io };
}
```

### 3.2 API Routes

**src/routes/index.ts:**
```typescript
import { Router } from 'express';
import { projectRoutes } from './projects';
import { agentRoutes } from './agents';
import { spatialRoutes } from './spatial';
import { inferenceRoutes } from './inference';
import { userRoutes } from './users';

export const routes = Router();

// Public routes
routes.use('/users', userRoutes);

// Protected routes
routes.use('/projects', projectRoutes);
routes.use('/agents', agentRoutes);
routes.use('/spatial', spatialRoutes);
routes.use('/inference', inferenceRoutes);

// Metrics endpoint
routes.get('/metrics', (req, res) => {
  // Return Prometheus metrics
  res.set('Content-Type', 'text/plain');
  res.send(getMetrics());
});
```

**src/routes/agents.ts:**
```typescript
import { Router } from 'express';
import { AgentController } from '../controllers/AgentController';

export const agentRoutes = Router();
const controller = new AgentController();

// Agent lifecycle
agentRoutes.post('/', controller.createAgent);
agentRoutes.get('/', controller.listAgents);
agentRoutes.get('/:id', controller.getAgent);
agentRoutes.delete('/:id', controller.deleteAgent);

// Agent control
agentRoutes.post('/:id/move', controller.moveAgent);
agentRoutes.post('/:id/teleport', controller.teleportAgent);
agentRoutes.post('/:id/query', controller.queryAgent);

// Context management
agentRoutes.get('/:id/context', controller.getContext);
agentRoutes.post('/:id/context/stream', controller.streamContext);
```

### 3.3 Controllers

**src/controllers/AgentController.ts:**
```typescript
import { Request, Response } from 'express';
import { AgentService } from '../services/AgentService';
import { SpatialService } from '../services/SpatialService';
import { InferenceService } from '../services/InferenceService';
import { WebSocketService } from '../services/WebSocketService';

export class AgentController {
  private agentService: AgentService;
  private spatialService: SpatialService;
  private inferenceService: InferenceService;
  private wsService: WebSocketService;

  constructor() {
    this.agentService = new AgentService();
    this.spatialService = new SpatialService();
    this.inferenceService = new InferenceService();
    this.wsService = WebSocketService.getInstance();
  }

  createAgent = async (req: Request, res: Response) => {
    try {
      const { projectId, model, name, position } = req.body;

      // Create agent in database
      const agent = await this.agentService.create({
        projectId,
        model,
        name,
        position: position || { x: 0, y: 0, z: 0 }
      });

      // Initialize model in inference engine
      await this.inferenceService.initializeModel(agent.id, model);

      // Load initial context based on position
      const context = await this.spatialService.loadContextAtPosition(
        projectId,
        agent.position
      );

      // Update agent with context
      await this.agentService.updateContext(agent.id, context);

      // Broadcast agent creation
      this.wsService.broadcast('agent:created', agent);

      res.json({ success: true, agent });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  };

  moveAgent = async (req: Request, res: Response) => {
    try {
      const { id } = req.params;
      const { targetPosition, speed } = req.body;

      // Calculate path
      const path = await this.spatialService.calculatePath(
        await this.agentService.getPosition(id),
        targetPosition
      );

      // Start movement animation
      const movement = await this.agentService.startMovement(id, path, speed);

      // Stream context updates during movement
      this.streamContextDuringMovement(id, path);

      // Broadcast movement
      this.wsService.broadcast('agent:moving', {
        agentId: id,
        path,
        duration: movement.duration
      });

      res.json({ success: true, movement });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  };

  queryAgent = async (req: Request, res: Response) => {
    try {
      const { id } = req.params;
      const { query } = req.body;

      // Find semantic location for query
      const location = await this.spatialService.findSemanticLocation(
        req.body.projectId,
        query
      );

      // Move agent to location
      await this.agentService.teleport(id, location);

      // Load relevant context
      const context = await this.spatialService.loadContextAtPosition(
        req.body.projectId,
        location
      );

      // Execute query with loaded context
      const response = await this.inferenceService.query(id, query, context);

      res.json({
        success: true,
        response,
        location,
        contextSize: context.tokens
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  };

  private async streamContextDuringMovement(agentId: string, path: Vector3[]) {
    for (const position of path) {
      // Load visible chunks at position
      const visibleChunks = await this.spatialService.getVisibleChunks(
        position,
        AGENT_VIEW_DISTANCE
      );

      // Calculate context window
      const context = await this.spatialService.buildContext(
        visibleChunks,
        MAX_CONTEXT_TOKENS
      );

      // Update agent context
      await this.agentService.updateContext(agentId, context);

      // Broadcast context update
      this.wsService.broadcast('agent:context:updated', {
        agentId,
        position,
        contextSize: context.tokens,
        chunks: context.chunks.length
      });

      // Small delay for smooth streaming
      await sleep(100);
    }
  }
}
```

### 3.4 Services

**src/services/SpatialService.ts:**
```typescript
import axios from 'axios';
import { Redis } from 'ioredis';
import { PrismaClient } from '@prisma/client';

export class SpatialService {
  private spatialEngineUrl: string;
  private redis: Redis;
  private prisma: PrismaClient;

  constructor() {
    this.spatialEngineUrl = process.env.SPATIAL_ENGINE_URL || 'http://spatial-engine:5000';
    this.redis = new Redis(process.env.REDIS_URL);
    this.prisma = new PrismaClient();
  }

  async loadContextAtPosition(projectId: string, position: Vector3) {
    // Check cache first
    const cacheKey = `context:${projectId}:${position.x}:${position.y}:${position.z}`;
    const cached = await this.redis.get(cacheKey);
    if (cached) {
      return JSON.parse(cached);
    }

    // Query spatial engine
    const response = await axios.post(`${this.spatialEngineUrl}/context/load`, {
      projectId,
      position,
      radius: 100,
      maxTokens: 8192
    });

    const context = response.data;

    // Cache for 5 minutes
    await this.redis.setex(cacheKey, 300, JSON.stringify(context));

    return context;
  }

  async findSemanticLocation(projectId: string, query: string): Promise<Vector3> {
    // Generate embedding via NPU
    const embedding = await this.generateEmbedding(query);

    // Search spatial index
    const response = await axios.post(`${this.spatialEngineUrl}/search/semantic`, {
      projectId,
      embedding,
      topK: 1
    });

    return response.data.results[0].position;
  }

  async generateEmbedding(text: string): Promise<Float32Array> {
    const response = await axios.post(`${this.spatialEngineUrl}/embedding/generate`, {
      text,
      model: 'BGE-small-en-v1.5'
    });

    return new Float32Array(response.data.embedding);
  }

  async getVisibleChunks(position: Vector3, viewDistance: number) {
    const response = await axios.post(`${this.spatialEngineUrl}/frustum/query`, {
      position,
      viewDistance,
      fov: 60
    });

    return response.data.chunks;
  }

  async buildContext(chunks: any[], maxTokens: number) {
    // Sort by distance from center
    chunks.sort((a, b) => a.distance - b.distance);

    const context = {
      chunks: [],
      tokens: 0,
      text: ''
    };

    for (const chunk of chunks) {
      if (context.tokens + chunk.tokens <= maxTokens) {
        context.chunks.push(chunk);
        context.tokens += chunk.tokens;
        context.text += chunk.content + '\n\n';
      } else {
        break;
      }
    }

    return context;
  }
}
```

### 3.5 WebSocket Handlers

**src/websocket/index.ts:**
```typescript
import { Server, Socket } from 'socket.io';
import { verifyToken } from '../utils/auth';
import { AgentWebSocketHandler } from './handlers/AgentHandler';
import { SpatialWebSocketHandler } from './handlers/SpatialHandler';

export function initWebSocket(io: Server) {
  // Authentication middleware
  io.use(async (socket, next) => {
    try {
      const token = socket.handshake.auth.token;
      const user = await verifyToken(token);
      socket.data.user = user;
      next();
    } catch (error) {
      next(new Error('Authentication failed'));
    }
  });

  io.on('connection', (socket: Socket) => {
    console.log(`User ${socket.data.user.id} connected`);

    // Join user room
    socket.join(`user:${socket.data.user.id}`);

    // Initialize handlers
    const agentHandler = new AgentWebSocketHandler(io, socket);
    const spatialHandler = new SpatialWebSocketHandler(io, socket);

    // Register event handlers
    agentHandler.register();
    spatialHandler.register();

    // Handle disconnection
    socket.on('disconnect', () => {
      console.log(`User ${socket.data.user.id} disconnected`);
    });
  });

  // Periodic updates
  setInterval(() => {
    io.emit('heartbeat', { timestamp: Date.now() });
  }, 30000);
}
```

---

## 4. SPATIAL ENGINE (Python)

### 4.1 Octree Implementation

**spatial-engine/core/octree.py:**
```python
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
from collections import deque

@dataclass
class BoundingBox:
    min: np.ndarray
    max: np.ndarray

    def contains(self, point: np.ndarray) -> bool:
        return np.all(point >= self.min) and np.all(point <= self.max)

    def intersects(self, other: 'BoundingBox') -> bool:
        return np.all(self.max >= other.min) and np.all(self.min <= other.max)

class OctreeNode:
    def __init__(self, bounds: BoundingBox, depth: int = 0, max_depth: int = 10):
        self.bounds = bounds
        self.depth = depth
        self.max_depth = max_depth
        self.children: List[Optional[OctreeNode]] = [None] * 8
        self.chunks: List[MemoryChunk] = []
        self.is_leaf = True

    def insert(self, chunk: MemoryChunk):
        if not self.bounds.contains(chunk.position):
            return False

        if self.is_leaf:
            if len(self.chunks) < 8 or self.depth >= self.max_depth:
                self.chunks.append(chunk)
                return True
            else:
                self.subdivide()

        # Insert into appropriate child
        child_index = self.get_child_index(chunk.position)
        if self.children[child_index] is None:
            self.children[child_index] = self.create_child(child_index)

        return self.children[child_index].insert(chunk)

    def subdivide(self):
        self.is_leaf = False

        # Move existing chunks to children
        for chunk in self.chunks:
            child_index = self.get_child_index(chunk.position)
            if self.children[child_index] is None:
                self.children[child_index] = self.create_child(child_index)
            self.children[child_index].insert(chunk)

        self.chunks.clear()

    def create_child(self, index: int) -> 'OctreeNode':
        center = (self.bounds.min + self.bounds.max) / 2

        # Calculate child bounds based on index
        child_min = np.copy(self.bounds.min)
        child_max = np.copy(self.bounds.max)

        if index & 1:
            child_min[0] = center[0]
        else:
            child_max[0] = center[0]

        if index & 2:
            child_min[1] = center[1]
        else:
            child_max[1] = center[1]

        if index & 4:
            child_min[2] = center[2]
        else:
            child_max[2] = center[2]

        return OctreeNode(
            BoundingBox(child_min, child_max),
            self.depth + 1,
            self.max_depth
        )

    def get_child_index(self, point: np.ndarray) -> int:
        center = (self.bounds.min + self.bounds.max) / 2
        index = 0

        if point[0] >= center[0]:
            index |= 1
        if point[1] >= center[1]:
            index |= 2
        if point[2] >= center[2]:
            index |= 4

        return index

    def query_frustum(self, frustum: Frustum) -> List[MemoryChunk]:
        results = []

        if not frustum.intersects_box(self.bounds):
            return results

        if self.is_leaf:
            for chunk in self.chunks:
                if frustum.contains_point(chunk.position):
                    results.append(chunk)
        else:
            for child in self.children:
                if child is not None:
                    results.extend(child.query_frustum(frustum))

        return results

    def query_sphere(self, center: np.ndarray, radius: float) -> List[MemoryChunk]:
        results = []

        # Check if sphere intersects node bounds
        if not self.sphere_intersects_box(center, radius):
            return results

        if self.is_leaf:
            for chunk in self.chunks:
                if np.linalg.norm(chunk.position - center) <= radius:
                    results.append(chunk)
        else:
            for child in self.children:
                if child is not None:
                    results.extend(child.query_sphere(center, radius))

        return results

    def sphere_intersects_box(self, center: np.ndarray, radius: float) -> bool:
        # Find closest point on box to sphere center
        closest = np.clip(center, self.bounds.min, self.bounds.max)

        # Check if closest point is within sphere
        return np.linalg.norm(center - closest) <= radius
```

### 4.2 NPU Embedding Generation

**spatial-engine/core/embedding.py:**
```python
import onnxruntime as ort
import numpy as np
from typing import List, Union
import hashlib
import redis
from transformers import AutoTokenizer

class NPUEmbeddingGenerator:
    def __init__(self, model_path: str, cache_enabled: bool = True):
        # Initialize ONNX Runtime with NPU provider
        providers = ['VitisAIExecutionProvider', 'CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)

        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-small-en-v1.5')

        # Initialize cache
        self.cache_enabled = cache_enabled
        if cache_enabled:
            self.redis = redis.Redis.from_url(os.environ['REDIS_URL'])

        # Model configuration
        self.max_length = 512
        self.embedding_dim = 384

    def generate(self, text: Union[str, List[str]]) -> np.ndarray:
        if isinstance(text, str):
            text = [text]

        embeddings = []

        for t in text:
            # Check cache
            if self.cache_enabled:
                cached = self.get_cached(t)
                if cached is not None:
                    embeddings.append(cached)
                    continue

            # Tokenize
            inputs = self.tokenizer(
                t,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors='np'
            )

            # Run inference on NPU
            outputs = self.session.run(None, {
                'input_ids': inputs['input_ids'],
                'attention_mask': inputs['attention_mask']
            })

            # Extract embedding (mean pooling)
            embedding = outputs[0].mean(axis=1).squeeze()

            # Normalize
            embedding = embedding / np.linalg.norm(embedding)

            # Cache result
            if self.cache_enabled:
                self.cache_embedding(t, embedding)

            embeddings.append(embedding)

        return np.array(embeddings)

    def get_cached(self, text: str) -> Optional[np.ndarray]:
        key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
        data = self.redis.get(key)
        if data:
            return np.frombuffer(data, dtype=np.float32).reshape(-1)
        return None

    def cache_embedding(self, text: str, embedding: np.ndarray):
        key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
        self.redis.setex(key, 86400, embedding.tobytes())  # 24 hour TTL

    def batch_generate(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = self.generate(batch)
            embeddings.extend(batch_embeddings)

        return np.array(embeddings)
```

### 4.3 Context Streaming

**spatial-engine/core/streaming.py:**
```python
import asyncio
import numpy as np
from typing import List, AsyncGenerator
from dataclasses import dataclass

@dataclass
class StreamingContext:
    position: np.ndarray
    velocity: np.ndarray
    view_distance: float
    max_tokens: int
    update_frequency: float = 0.1  # 10 Hz

class ContextStreamer:
    def __init__(self, octree: OctreeNode, embedding_generator: NPUEmbeddingGenerator):
        self.octree = octree
        self.embedding_generator = embedding_generator
        self.active_streams = {}

    async def stream_context(
        self,
        agent_id: str,
        initial_position: np.ndarray,
        target_position: np.ndarray,
        speed: float,
        view_distance: float = 100.0,
        max_tokens: int = 8192
    ) -> AsyncGenerator[dict, None]:
        """Stream context updates as agent moves"""

        # Calculate path and movement vector
        direction = target_position - initial_position
        distance = np.linalg.norm(direction)
        direction = direction / distance  # Normalize

        duration = distance / speed
        steps = int(duration / 0.1)  # 10 Hz updates

        current_position = initial_position.copy()
        loaded_chunks = set()

        for step in range(steps):
            # Update position
            current_position += direction * speed * 0.1

            # Query visible chunks
            visible_chunks = self.octree.query_sphere(current_position, view_distance)

            # Sort by distance
            visible_chunks.sort(key=lambda c: np.linalg.norm(c.position - current_position))

            # Build context window
            context = {
                'position': current_position.tolist(),
                'chunks': [],
                'tokens': 0,
                'added': [],
                'removed': []
            }

            current_chunk_ids = set()

            for chunk in visible_chunks:
                if context['tokens'] + chunk.tokens <= max_tokens:
                    context['chunks'].append({
                        'id': chunk.id,
                        'position': chunk.position.tolist(),
                        'content': chunk.content,
                        'tokens': chunk.tokens,
                        'distance': np.linalg.norm(chunk.position - current_position)
                    })
                    context['tokens'] += chunk.tokens
                    current_chunk_ids.add(chunk.id)

                    if chunk.id not in loaded_chunks:
                        context['added'].append(chunk.id)

            # Track removed chunks
            for chunk_id in loaded_chunks - current_chunk_ids:
                context['removed'].append(chunk_id)

            loaded_chunks = current_chunk_ids

            yield context

            await asyncio.sleep(0.1)

    async def predictive_prefetch(
        self,
        current_position: np.ndarray,
        velocity: np.ndarray,
        view_distance: float,
        prediction_time: float = 2.0
    ) -> List[MemoryChunk]:
        """Predictively prefetch chunks based on movement"""

        # Predict future position
        predicted_position = current_position + velocity * prediction_time

        # Query chunks at predicted position
        predicted_chunks = self.octree.query_sphere(predicted_position, view_distance)

        # Filter chunks not currently visible
        current_chunks = set(c.id for c in self.octree.query_sphere(current_position, view_distance))

        prefetch_chunks = [c for c in predicted_chunks if c.id not in current_chunks]

        return prefetch_chunks
```

### 4.4 FastAPI Server

**spatial-engine/api/server.py:**
```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from typing import List, Optional
import asyncio

from ..core.octree import OctreeNode, BoundingBox
from ..core.embedding import NPUEmbeddingGenerator
from ..core.streaming import ContextStreamer
from ..core.search import SemanticSearch

app = FastAPI(title="Spatial Engine API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
bounds = BoundingBox(np.array([-1000, -100, -1000]), np.array([1000, 100, 1000]))
octree = OctreeNode(bounds, max_depth=12)
embedding_generator = NPUEmbeddingGenerator('/models/bge-small.onnx')
context_streamer = ContextStreamer(octree, embedding_generator)
semantic_search = SemanticSearch(octree, embedding_generator)

# API Models
class Vector3(BaseModel):
    x: float
    y: float
    z: float

class MemoryChunkCreate(BaseModel):
    content: str
    file_path: str
    position: Vector3
    tokens: int

class ContextQuery(BaseModel):
    project_id: str
    position: Vector3
    radius: float = 100.0
    max_tokens: int = 8192

class SemanticQuery(BaseModel):
    project_id: str
    query: str
    top_k: int = 10

@app.post("/chunk/create")
async def create_chunk(chunk: MemoryChunkCreate):
    """Add a memory chunk to spatial index"""
    # Generate embedding
    embedding = embedding_generator.generate(chunk.content)[0]

    # Create chunk object
    memory_chunk = MemoryChunk(
        content=chunk.content,
        position=np.array([chunk.position.x, chunk.position.y, chunk.position.z]),
        embedding=embedding,
        tokens=chunk.tokens
    )

    # Insert into octree
    success = octree.insert(memory_chunk)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to insert chunk")

    return {"success": True, "id": memory_chunk.id}

@app.post("/context/load")
async def load_context(query: ContextQuery):
    """Load context at specific position"""
    position = np.array([query.position.x, query.position.y, query.position.z])

    # Query chunks within radius
    chunks = octree.query_sphere(position, query.radius)

    # Sort by distance
    chunks.sort(key=lambda c: np.linalg.norm(c.position - position))

    # Build context window
    context = {
        "chunks": [],
        "tokens": 0
    }

    for chunk in chunks:
        if context["tokens"] + chunk.tokens <= query.max_tokens:
            context["chunks"].append({
                "id": chunk.id,
                "content": chunk.content,
                "tokens": chunk.tokens,
                "distance": float(np.linalg.norm(chunk.position - position))
            })
            context["tokens"] += chunk.tokens
        else:
            break

    return context

@app.post("/search/semantic")
async def semantic_search(query: SemanticQuery):
    """Find semantically similar chunks"""
    results = await semantic_search.search(
        query.query,
        query.project_id,
        query.top_k
    )

    return {
        "results": [
            {
                "id": r.id,
                "content": r.content[:200],  # Preview
                "position": r.position.tolist(),
                "score": float(r.score)
            }
            for r in results
        ]
    }

@app.post("/embedding/generate")
async def generate_embedding(text: str):
    """Generate embedding using NPU"""
    embedding = embedding_generator.generate(text)[0]
    return {"embedding": embedding.tolist()}

@app.websocket("/stream/context/{agent_id}")
async def stream_context(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for context streaming"""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            # Start streaming context updates
            async for context_update in context_streamer.stream_context(
                agent_id=agent_id,
                initial_position=np.array(data["from"]),
                target_position=np.array(data["to"]),
                speed=data.get("speed", 10.0),
                view_distance=data.get("viewDistance", 100.0),
                max_tokens=data.get("maxTokens", 8192)
            ):
                await websocket.send_json(context_update)

    except Exception as e:
        await websocket.close(code=1000, reason=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "octree_depth": octree.depth,
        "npu_available": embedding_generator.session.get_providers()[0] == 'VitisAIExecutionProvider'
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
```

---

## 5. AI INFERENCE ENGINE

### 5.1 Model Management

**inference-engine/models/base.py:**
```python
from abc import ABC, abstractmethod
import numpy as np
from typing import List, Dict, Any

class BaseModel(ABC):
    def __init__(self, model_path: str, context_length: int = 8192):
        self.model_path = model_path
        self.context_length = context_length
        self.model = None

    @abstractmethod
    def load(self):
        """Load model into memory"""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        context: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """Generate response"""
        pass

    @abstractmethod
    def unload(self):
        """Unload model from memory"""
        pass

    def format_context(self, context_chunks: List[Dict]) -> str:
        """Format context chunks for model input"""
        formatted = "Context:\n"

        for chunk in context_chunks:
            formatted += f"\n[File: {chunk.get('file_path', 'unknown')}]\n"
            formatted += chunk['content']
            formatted += "\n---\n"

        return formatted
```

**inference-engine/models/llama.py:**
```python
from llama_cpp import Llama
from .base import BaseModel

class LlamaModel(BaseModel):
    def load(self):
        self.model = Llama(
            model_path=self.model_path,
            n_ctx=self.context_length,
            n_gpu_layers=35,  # Offload to GPU
            n_threads=8,
            use_mmap=True,
            use_mlock=False,
            verbose=False
        )

    def generate(
        self,
        prompt: str,
        context: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        # Build full prompt with context
        full_prompt = f"{context}\n\nQuery: {prompt}\n\nResponse:"

        # Generate
        response = self.model(
            full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=["Query:", "\n\n"]
        )

        return response['choices'][0]['text'].strip()

    def unload(self):
        del self.model
        self.model = None
```

### 5.2 Inference Server

**inference-engine/server.py:**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from typing import Dict, List, Optional
import torch

from models.llama import LlamaModel
from models.mistral import MistralModel
from models.phi import PhiModel

app = FastAPI(title="AI Inference Engine")

# Model registry
models: Dict[str, BaseModel] = {}
model_classes = {
    'llama-8b': LlamaModel,
    'mistral-7b': MistralModel,
    'phi-3': PhiModel
}

# Request models
class InitializeRequest(BaseModel):
    agent_id: str
    model: str
    context_length: Optional[int] = 8192

class GenerateRequest(BaseModel):
    agent_id: str
    prompt: str
    context: List[Dict]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9

@app.post("/initialize")
async def initialize_model(request: InitializeRequest):
    """Initialize model for agent"""
    if request.agent_id in models:
        return {"message": "Model already initialized"}

    if request.model not in model_classes:
        raise HTTPException(status_code=400, detail="Unknown model")

    # Load model
    model_class = model_classes[request.model]
    model_path = f"/models/{request.model}.gguf"

    model = model_class(model_path, request.context_length)
    model.load()

    models[request.agent_id] = model

    return {"success": True, "message": "Model initialized"}

@app.post("/generate")
async def generate(request: GenerateRequest):
    """Generate response"""
    if request.agent_id not in models:
        raise HTTPException(status_code=400, detail="Model not initialized")

    model = models[request.agent_id]

    # Format context
    context = model.format_context(request.context)

    # Generate response
    try:
        response = await asyncio.to_thread(
            model.generate,
            request.prompt,
            context,
            request.max_tokens,
            request.temperature,
            request.top_p
        )

        return {
            "response": response,
            "tokens_used": len(context.split()) + len(response.split()),
            "model": type(model).__name__
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/unload/{agent_id}")
async def unload_model(agent_id: str):
    """Unload model from memory"""
    if agent_id not in models:
        raise HTTPException(status_code=404, detail="Model not found")

    models[agent_id].unload()
    del models[agent_id]

    return {"success": True, "message": "Model unloaded"}

@app.get("/status")
async def get_status():
    """Get inference engine status"""
    gpu_available = torch.cuda.is_available()
    gpu_count = torch.cuda.device_count() if gpu_available else 0

    return {
        "models_loaded": len(models),
        "active_agents": list(models.keys()),
        "gpu_available": gpu_available,
        "gpu_count": gpu_count,
        "cuda_version": torch.version.cuda if gpu_available else None
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6000)
```

---

## 6. DATABASE MODELS

### 6.1 Prisma Schema

**prisma/schema.prisma:**
```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(uuid())
  email     String   @unique
  username  String   @unique
  password  String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  projects  Project[]
  sessions  Session[]
}

model Project {
  id          String   @id @default(uuid())
  name        String
  description String?
  rootPath    String
  userId      String
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  metadata    Json     @default("{}")

  user         User          @relation(fields: [userId], references: [id])
  memoryChunks MemoryChunk[]
  agents       Agent[]
  spatialIndex SpatialIndex[]
}

model MemoryChunk {
  id        String   @id @default(uuid())
  projectId String
  filePath  String
  content   String
  tokens    Int
  positionX Float
  positionY Float
  positionZ Float
  embedding Float[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  metadata  Json     @default("{}")

  project Project @relation(fields: [projectId], references: [id])

  @@index([projectId])
  @@index([positionX, positionY, positionZ])
}

model Agent {
  id           String   @id @default(uuid())
  projectId    String
  name         String
  model        String
  positionX    Float    @default(0)
  positionY    Float    @default(0)
  positionZ    Float    @default(0)
  contextState Json     @default("{}")
  createdAt    DateTime @default(now())
  lastActive   DateTime @default(now())

  project Project        @relation(fields: [projectId], references: [id])
  history AgentHistory[]

  @@index([projectId])
}

model AgentHistory {
  id             String   @id @default(uuid())
  agentId        String
  positionX      Float
  positionY      Float
  positionZ      Float
  action         String
  contextSummary String?
  timestamp      DateTime @default(now())

  agent Agent @relation(fields: [agentId], references: [id])

  @@index([agentId])
  @@index([timestamp])
}

model SpatialIndex {
  id         String   @id @default(uuid())
  projectId  String
  nodeLevel  Int
  minX       Float
  minY       Float
  minZ       Float
  maxX       Float
  maxY       Float
  maxZ       Float
  chunkIds   String[]
  childNodes String[]
  metadata   Json     @default("{}")

  project Project @relation(fields: [projectId], references: [id])

  @@index([projectId])
  @@index([minX, minY, minZ, maxX, maxY, maxZ])
}

model Session {
  id        String   @id @default(uuid())
  userId    String
  token     String   @unique
  expiresAt DateTime
  createdAt DateTime @default(now())
  ipAddress String?
  userAgent String?

  user User @relation(fields: [userId], references: [id])

  @@index([userId])
  @@index([token])
}
```

---

## CONCLUSION

This backend architecture provides:
- **Scalable API server** with Express.js and TypeScript
- **Spatial memory engine** with octree indexing and NPU acceleration
- **AI inference coordination** supporting multiple models
- **Real-time updates** via WebSocket
- **Efficient caching** with Redis
- **Robust data persistence** with PostgreSQL

The system enables the revolutionary spatial context management that gives local AI models effectively infinite memory.