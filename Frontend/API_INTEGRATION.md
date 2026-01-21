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

# INFINITE: Frontend API Integration Architecture
**WebSocket & REST API Communication Patterns**

---

## EXECUTIVE SUMMARY

This document defines how the Infinite frontend communicates with backend services for context streaming, AI inference, spatial indexing, and system orchestration. All APIs prioritize real-time performance with sub-100ms latency targets.

---

## 1. API ARCHITECTURE OVERVIEW

### Communication Channels

```typescript
// Three primary channels
const apiChannels = {
  rest: 'https://localhost:8080/api/v1',      // Configuration & queries
  websocket: 'wss://localhost:8081/stream',   // Real-time streaming
  grpc: 'localhost:8082',                     // High-performance RPC
};
```

### Protocol Selection Matrix

| Operation Type | Protocol | Reason |
|---------------|----------|---------|
| Context Streaming | WebSocket | Bidirectional, low-latency |
| AI Inference | WebSocket/gRPC | Stream responses |
| Spatial Queries | REST/gRPC | Request-response pattern |
| Configuration | REST | Stateless CRUD operations |
| Embeddings | gRPC | Binary efficiency |
| Metrics | WebSocket | Real-time monitoring |

---

## 2. WEBSOCKET STREAMING API

### Connection Management

```typescript
interface WebSocketManager {
  // Primary streaming connection
  primary: WebSocket;

  // Connection lifecycle
  connect(): Promise<void>;
  disconnect(): void;
  reconnect(): void;

  // Health monitoring
  ping(): void;
  heartbeat: number; // 30 second intervals

  // Auto-reconnect with exponential backoff
  reconnectStrategy: {
    initialDelay: 1000,
    maxDelay: 30000,
    multiplier: 1.5,
    maxRetries: 10
  };
}
```

### Message Protocol

```typescript
// All WebSocket messages follow this structure
interface WSMessage<T = any> {
  id: string;          // UUID for request tracking
  type: MessageType;   // Event type
  timestamp: number;   // Unix timestamp
  payload: T;          // Type-specific data
  metadata?: {
    priority: number;  // 0-10 priority level
    ttl?: number;      // Time to live in ms
    ack?: boolean;     // Requires acknowledgment
  };
}

enum MessageType {
  // Context operations
  CONTEXT_LOAD = 'context.load',
  CONTEXT_UNLOAD = 'context.unload',
  CONTEXT_STREAM = 'context.stream',

  // Agent operations
  AGENT_MOVE = 'agent.move',
  AGENT_TELEPORT = 'agent.teleport',
  AGENT_ROTATE = 'agent.rotate',

  // Query operations
  QUERY_SUBMIT = 'query.submit',
  QUERY_RESPONSE = 'query.response',
  QUERY_CANCEL = 'query.cancel',

  // System events
  SYSTEM_METRICS = 'system.metrics',
  SYSTEM_ERROR = 'system.error',
  SYSTEM_READY = 'system.ready'
}
```

### Context Streaming Events

```typescript
// Frontend → Backend: Request context for position
interface ContextLoadRequest {
  agentId: string;
  position: Vector3;
  frustum: {
    near: number;
    far: number;
    fov: number;
  };
  maxTokens: number;
  priority: 'immediate' | 'prefetch' | 'background';
}

// Backend → Frontend: Stream context chunks
interface ContextStreamResponse {
  agentId: string;
  chunks: Array<{
    id: string;
    position: Vector3;
    content: string;
    tokens: number;
    type: 'code' | 'docs' | 'conversation';
    metadata: {
      language?: string;
      timestamp?: number;
      embedding?: Float32Array;
    };
  }>;
  totalTokens: number;
  loadTime: number;
  complete: boolean;
}
```

### AI Query Streaming

```typescript
// Frontend → Backend: Submit query
interface QuerySubmitRequest {
  agentId: string;
  query: string;
  context: {
    includeVisible: boolean;
    includeHistory: boolean;
    maxTokens: number;
  };
  stream: boolean; // Stream response tokens
}

// Backend → Frontend: Stream AI response
interface QueryResponseStream {
  agentId: string;
  queryId: string;
  token?: string;      // Incremental token
  complete?: boolean;  // Stream complete
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  navigation?: {      // AI requests navigation
    target: Vector3;
    reason: string;
  };
}
```

---

## 3. REST API ENDPOINTS

### Memory Management

```typescript
// GET /api/v1/memory/spaces
interface GetMemorySpacesResponse {
  spaces: Array<{
    id: string;
    name: string;
    totalChunks: number;
    totalTokens: number;
    bounds: BoundingBox;
    created: Date;
    modified: Date;
  }>;
}

// POST /api/v1/memory/upload
interface UploadMemoryRequest {
  spaceId: string;
  content: string | File;
  type: 'code' | 'documentation' | 'conversation';
  metadata?: Record<string, any>;
}

// POST /api/v1/memory/index
interface IndexMemoryRequest {
  spaceId: string;
  strategy: 'semantic' | 'structural' | 'temporal';
  options: {
    chunkSize: number;      // 200-500 tokens
    overlap: number;        // Token overlap
    embeddingModel: string; // BGE-small, etc.
  };
}

// GET /api/v1/memory/chunk/:id
interface GetChunkResponse {
  id: string;
  content: string;
  tokens: number;
  position: Vector3;
  embedding: number[];
  neighbors: string[]; // Adjacent chunk IDs
  metadata: Record<string, any>;
}
```

### Agent Management

```typescript
// GET /api/v1/agents
interface GetAgentsResponse {
  agents: Array<{
    id: string;
    model: string;
    status: 'idle' | 'loading' | 'processing';
    position: Vector3;
    contextWindow: {
      current: number;
      max: number;
    };
    performance: {
      tokensPerSecond: number;
      latency: number;
    };
  }>;
}

// POST /api/v1/agents/create
interface CreateAgentRequest {
  model: 'llama-8b' | 'mistral-7b' | 'phi-3';
  config: {
    temperature: number;
    maxTokens: number;
    device: 'cpu' | 'gpu' | 'npu';
    quantization: '4bit' | '8bit' | '16bit';
  };
  initialPosition?: Vector3;
}

// PUT /api/v1/agents/:id/navigate
interface NavigateAgentRequest {
  target: Vector3 | string; // Position or chunk ID
  speed: 'instant' | 'fast' | 'normal';
  reason?: string;
}
```

### Spatial Queries

```typescript
// POST /api/v1/spatial/search
interface SpatialSearchRequest {
  query: string;
  center?: Vector3;
  radius?: number;
  limit?: number;
  filters?: {
    type?: string[];
    minScore?: number;
    dateRange?: [Date, Date];
  };
}

interface SpatialSearchResponse {
  results: Array<{
    chunkId: string;
    position: Vector3;
    score: number;
    preview: string;
    distance?: number;
  }>;
  searchTime: number;
}

// GET /api/v1/spatial/neighbors
interface GetNeighborsRequest {
  position: Vector3;
  radius: number;
  limit?: number;
}

// POST /api/v1/spatial/cluster
interface ClusterAnalysisRequest {
  spaceId: string;
  algorithm: 'kmeans' | 'dbscan' | 'hierarchical';
  parameters: Record<string, any>;
}
```

### System Configuration

```typescript
// GET /api/v1/config
interface GetConfigResponse {
  models: Array<{
    id: string;
    name: string;
    parameters: number;
    contextWindow: number;
    available: boolean;
  }>;
  hardware: {
    cpu: CPUInfo;
    gpu: GPUInfo[];
    npu: NPUInfo;
    memory: MemoryInfo;
  };
  performance: {
    targetFPS: number;
    maxConcurrentAgents: number;
    chunkCacheSize: number;
  };
}

// PUT /api/v1/config/performance
interface UpdatePerformanceRequest {
  rendering: {
    quality: 'low' | 'medium' | 'high' | 'ultra';
    targetFPS: number;
    shadows: boolean;
    postProcessing: boolean;
  };
  streaming: {
    chunkSize: number;
    prefetchDistance: number;
    maxConcurrent: number;
  };
  ai: {
    maxTokensPerSecond: number;
    batchSize: number;
    useNPU: boolean;
  };
}
```

---

## 4. GRPC HIGH-PERFORMANCE API

### Protocol Buffers Definition

```protobuf
syntax = "proto3";

service SpatialIndex {
  rpc GetEmbedding(EmbeddingRequest) returns (EmbeddingResponse);
  rpc BatchQuery(BatchQueryRequest) returns (stream QueryResult);
  rpc StreamContext(StreamContextRequest) returns (stream ContextChunk);
}

message Vector3 {
  float x = 1;
  float y = 2;
  float z = 3;
}

message EmbeddingRequest {
  string text = 1;
  string model = 2;
  bool use_npu = 3;
}

message EmbeddingResponse {
  repeated float embedding = 1;
  int32 dimensions = 2;
  int32 compute_time_ms = 3;
}

message ContextChunk {
  string id = 1;
  bytes content = 2;
  Vector3 position = 3;
  int32 tokens = 4;
  int64 timestamp = 5;
}
```

### gRPC Client Implementation

```typescript
import * as grpc from '@grpc/grpc-js';
import { SpatialIndexClient } from './generated/spatial_grpc_pb';

class GRPCClient {
  private client: SpatialIndexClient;

  constructor() {
    this.client = new SpatialIndexClient(
      'localhost:8082',
      grpc.credentials.createInsecure()
    );
  }

  async getEmbedding(text: string): Promise<Float32Array> {
    return new Promise((resolve, reject) => {
      const request = new EmbeddingRequest();
      request.setText(text);
      request.setModel('bge-small');
      request.setUseNpu(true);

      this.client.getEmbedding(request, (err, response) => {
        if (err) reject(err);
        else resolve(new Float32Array(response.getEmbeddingList()));
      });
    });
  }

  streamContext(position: Vector3): AsyncIterableIterator<ContextChunk> {
    const request = new StreamContextRequest();
    request.setPosition(position);

    const stream = this.client.streamContext(request);
    return {
      async *[Symbol.asyncIterator]() {
        for await (const chunk of stream) {
          yield chunk;
        }
      }
    };
  }
}
```

---

## 5. API CLIENT ARCHITECTURE

### Service Layer Organization

```typescript
// Core API service structure
class APIService {
  private rest: RESTClient;
  private websocket: WebSocketClient;
  private grpc: GRPCClient;

  // Service modules
  public memory: MemoryService;
  public agents: AgentService;
  public spatial: SpatialService;
  public streaming: StreamingService;
  public query: QueryService;

  constructor(config: APIConfig) {
    this.initializeClients(config);
    this.initializeServices();
  }
}

// Individual service example
class StreamingService {
  private ws: WebSocketClient;
  private cache: Map<string, ContextChunk>;
  private queue: PriorityQueue<StreamRequest>;

  async streamContext(request: ContextLoadRequest): Promise<void> {
    // Add to priority queue
    this.queue.push({
      priority: this.calculatePriority(request),
      request
    });

    // Process queue
    await this.processQueue();
  }

  private calculatePriority(request: ContextLoadRequest): number {
    // Distance-based priority
    const distance = request.position.length();
    const urgency = request.priority === 'immediate' ? 1000 : 0;
    return urgency - distance;
  }
}
```

### Error Handling

```typescript
class APIError extends Error {
  constructor(
    public code: string,
    public status: number,
    message: string,
    public details?: any
  ) {
    super(message);
  }
}

class ErrorHandler {
  static async handle(error: any): Promise<void> {
    if (error instanceof APIError) {
      switch (error.code) {
        case 'CONTEXT_OVERFLOW':
          // Reduce context window
          break;
        case 'MODEL_UNAVAILABLE':
          // Switch to fallback model
          break;
        case 'RATE_LIMIT':
          // Implement backoff
          break;
      }
    }

    // Log and report
    console.error('API Error:', error);
    telemetry.recordError(error);
  }
}
```

### Caching Strategy

```typescript
interface CacheConfig {
  memory: {
    maxSize: number;    // MB
    ttl: number;        // Seconds
    strategy: 'lru' | 'lfu' | 'fifo';
  };
  disk: {
    enabled: boolean;
    path: string;
    maxSize: number;    // GB
  };
}

class APICache {
  private memory: Map<string, CacheEntry>;
  private disk: DiskCache;

  async get<T>(key: string): Promise<T | null> {
    // Check memory cache
    const memEntry = this.memory.get(key);
    if (memEntry && !this.isExpired(memEntry)) {
      return memEntry.data as T;
    }

    // Check disk cache
    if (this.disk.enabled) {
      return await this.disk.get<T>(key);
    }

    return null;
  }

  async set<T>(key: string, data: T, ttl?: number): Promise<void> {
    // Memory cache
    this.memory.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.config.memory.ttl
    });

    // Disk cache for important data
    if (this.shouldPersist(key, data)) {
      await this.disk.set(key, data);
    }
  }
}
```

---

## 6. REAL-TIME SYNCHRONIZATION

### State Synchronization

```typescript
interface SyncManager {
  // Sync agent position
  syncPosition(agentId: string, position: Vector3): void;

  // Sync context window
  syncContext(agentId: string, chunks: string[]): void;

  // Sync performance metrics
  syncMetrics(metrics: PerformanceMetrics): void;

  // Conflict resolution
  resolveConflict(local: any, remote: any): any;
}

// Redux middleware for auto-sync
const syncMiddleware: Middleware = store => next => action => {
  const result = next(action);

  // Auto-sync relevant actions
  if (action.type.startsWith('agent/')) {
    syncManager.syncAgent(action.payload);
  }

  return result;
};
```

### Optimistic Updates

```typescript
class OptimisticUpdater {
  private pending: Map<string, PendingUpdate>;

  async update<T>(
    id: string,
    optimistic: T,
    request: () => Promise<T>
  ): Promise<T> {
    // Apply optimistic update immediately
    this.applyOptimistic(id, optimistic);

    try {
      // Make actual request
      const result = await request();

      // Confirm update
      this.confirmUpdate(id, result);

      return result;
    } catch (error) {
      // Rollback on failure
      this.rollbackUpdate(id);
      throw error;
    }
  }
}
```

---

## 7. PERFORMANCE OPTIMIZATION

### Request Batching

```typescript
class BatchProcessor {
  private batch: Map<string, any[]> = new Map();
  private timer: NodeJS.Timeout | null = null;

  async add<T>(type: string, request: T): Promise<void> {
    if (!this.batch.has(type)) {
      this.batch.set(type, []);
    }

    this.batch.get(type)!.push(request);

    // Start batch timer
    if (!this.timer) {
      this.timer = setTimeout(() => this.flush(), 50);
    }
  }

  private async flush(): Promise<void> {
    const batches = new Map(this.batch);
    this.batch.clear();
    this.timer = null;

    // Process each batch type
    for (const [type, requests] of batches) {
      await this.processBatch(type, requests);
    }
  }
}
```

### Connection Pooling

```typescript
class ConnectionPool {
  private connections: WebSocket[] = [];
  private available: WebSocket[] = [];
  private maxConnections = 5;

  async acquire(): Promise<WebSocket> {
    if (this.available.length > 0) {
      return this.available.pop()!;
    }

    if (this.connections.length < this.maxConnections) {
      const ws = await this.createConnection();
      this.connections.push(ws);
      return ws;
    }

    // Wait for available connection
    return await this.waitForConnection();
  }

  release(ws: WebSocket): void {
    if (ws.readyState === WebSocket.OPEN) {
      this.available.push(ws);
    } else {
      this.removeConnection(ws);
    }
  }
}
```

---

## 8. MONITORING & TELEMETRY

### API Metrics Collection

```typescript
interface APIMetrics {
  requests: {
    total: number;
    success: number;
    failure: number;
    pending: number;
  };
  latency: {
    p50: number;
    p95: number;
    p99: number;
  };
  bandwidth: {
    sent: number;
    received: number;
  };
  errors: {
    count: number;
    types: Record<string, number>;
  };
}

class MetricsCollector {
  private metrics: APIMetrics;
  private intervals: Map<string, number> = new Map();

  recordRequest(type: string, duration: number, success: boolean): void {
    this.metrics.requests.total++;

    if (success) {
      this.metrics.requests.success++;
    } else {
      this.metrics.requests.failure++;
    }

    this.updateLatency(duration);
  }

  private updateLatency(duration: number): void {
    // Update percentile calculations
    // Using approximate streaming percentiles algorithm
  }
}
```

---

## 9. SECURITY IMPLEMENTATION

### Authentication

```typescript
interface AuthConfig {
  type: 'jwt' | 'oauth' | 'api-key';
  endpoint: string;
  refreshInterval: number;
}

class AuthManager {
  private token: string | null = null;
  private refreshTimer: NodeJS.Timeout | null = null;

  async authenticate(): Promise<void> {
    const response = await fetch(this.config.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(this.credentials)
    });

    const { token, expiresIn } = await response.json();
    this.token = token;

    // Schedule refresh
    this.scheduleRefresh(expiresIn);
  }

  getAuthHeader(): Record<string, string> {
    return {
      'Authorization': `Bearer ${this.token}`
    };
  }
}
```

### Request Signing

```typescript
class RequestSigner {
  sign(request: any): void {
    const timestamp = Date.now();
    const nonce = crypto.randomBytes(16).toString('hex');

    const signature = this.generateSignature({
      ...request,
      timestamp,
      nonce
    });

    request.headers = {
      ...request.headers,
      'X-Timestamp': timestamp.toString(),
      'X-Nonce': nonce,
      'X-Signature': signature
    };
  }

  private generateSignature(data: any): string {
    return crypto
      .createHmac('sha256', this.secret)
      .update(JSON.stringify(data))
      .digest('hex');
  }
}
```

---

## 10. TESTING STRATEGY

### API Mocking

```typescript
class MockAPIServer {
  private server: Server;
  private ws: WebSocketServer;

  async start(): Promise<void> {
    // Mock REST endpoints
    this.server = createServer((req, res) => {
      this.handleRequest(req, res);
    });

    // Mock WebSocket
    this.ws = new WebSocketServer({ server: this.server });
    this.ws.on('connection', this.handleWebSocket);

    await this.server.listen(8080);
  }

  registerMock(endpoint: string, response: any): void {
    this.mocks.set(endpoint, response);
  }
}

// Usage in tests
beforeEach(async () => {
  mockServer = new MockAPIServer();
  await mockServer.start();

  mockServer.registerMock('/api/v1/agents', {
    agents: [/* mock data */]
  });
});
```

### Integration Tests

```typescript
describe('Context Streaming', () => {
  it('should stream context based on position', async () => {
    const api = new APIService(testConfig);

    // Move agent to position
    await api.agents.navigate('agent-1', new Vector3(10, 0, 10));

    // Wait for context stream
    const context = await waitFor(() =>
      api.streaming.getLoadedContext('agent-1')
    );

    // Verify correct chunks loaded
    expect(context.chunks).toHaveLength(5);
    expect(context.totalTokens).toBeLessThan(8192);
  });
});
```

---

## SUCCESS METRICS

### Performance Targets
- WebSocket latency: <50ms
- REST response time: <100ms p95
- Context streaming: <100ms to first chunk
- Embedding generation: <10ms on NPU

### Reliability Targets
- 99.9% API availability
- Automatic reconnection within 5s
- Zero data loss during disconnections
- Graceful degradation on errors

### Scalability Targets
- Support 10 concurrent agents
- Handle 1000 chunks/second streaming
- 100,000 cached embeddings
- 10GB memory space indexing

---

**API Endpoint Count:** 25+ REST, 15+ WebSocket events, 5+ gRPC methods
**Protocols:** REST, WebSocket, gRPC
**Testing Coverage:** Unit, Integration, E2E
**Security:** JWT auth, request signing, TLS