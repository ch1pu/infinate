# INFINITE: Backend API Design
**RESTful, WebSocket, and gRPC API Specifications**

---

## EXECUTIVE SUMMARY

This document provides comprehensive API specifications for the Infinite backend, detailing all endpoints, request/response formats, authentication mechanisms, and performance requirements for the spatial context management system.

---

## 1. API OVERVIEW

### Base URLs

```yaml
Production:
  REST: https://api.infinite.local/v1
  WebSocket: wss://stream.infinite.local/v1
  gRPC: grpc://rpc.infinite.local:8082

Development:
  REST: http://localhost:8080/api/v1
  WebSocket: ws://localhost:8081/stream/v1
  gRPC: grpc://localhost:8082
```

### API Versioning

```http
# Header-based versioning
Accept: application/vnd.infinite.v1+json

# URL-based versioning (fallback)
GET /api/v1/agents
```

### Authentication

```http
# JWT Bearer Token
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# API Key (for service-to-service)
X-API-Key: inf_live_1234567890abcdef

# Session Cookie (web clients)
Cookie: infinite_session=...
```

---

## 2. REST API ENDPOINTS

### Memory Space Management

#### GET /api/v1/spaces
**List all memory spaces**

```typescript
// Response
{
  "spaces": [
    {
      "id": "space_abc123",
      "name": "Production Codebase",
      "created": "2025-01-01T00:00:00Z",
      "updated": "2025-01-15T12:00:00Z",
      "stats": {
        "chunks": 45678,
        "tokens": 23456789,
        "size_bytes": 567890123,
        "dimensions": {
          "x": [-1000, 1000],
          "y": [-500, 500],
          "z": [-1000, 1000]
        }
      },
      "config": {
        "chunk_size": 300,
        "overlap": 50,
        "embedding_model": "bge-small-en-v1.5"
      }
    }
  ],
  "total": 3,
  "page": 1,
  "per_page": 20
}
```

#### POST /api/v1/spaces
**Create new memory space**

```typescript
// Request
{
  "name": "Project Documentation",
  "description": "API and architecture docs",
  "config": {
    "chunk_size": 400,
    "chunk_overlap": 100,
    "embedding_model": "bge-small-en-v1.5",
    "indexing_strategy": "semantic"
  }
}

// Response (201 Created)
{
  "id": "space_xyz789",
  "name": "Project Documentation",
  "created": "2025-01-20T10:00:00Z",
  "status": "initializing",
  "estimated_ready": "2025-01-20T10:00:30Z"
}
```

#### GET /api/v1/spaces/{id}
**Get space details**

```typescript
// Response
{
  "id": "space_abc123",
  "name": "Production Codebase",
  "description": "Main application source code",
  "metadata": {
    "languages": ["typescript", "python", "rust"],
    "frameworks": ["react", "fastapi", "actix"],
    "last_indexed": "2025-01-15T12:00:00Z"
  },
  "bounds": {
    "min": {"x": -1000, "y": -500, "z": -1000},
    "max": {"x": 1000, "y": 500, "z": 1000}
  },
  "octree": {
    "depth": 8,
    "nodes": 156789,
    "leaf_nodes": 45678
  },
  "chunks": {
    "total": 45678,
    "by_type": {
      "code": 30000,
      "documentation": 10000,
      "comments": 5678
    }
  }
}
```

#### DELETE /api/v1/spaces/{id}
**Delete memory space**

```typescript
// Response (202 Accepted)
{
  "status": "deleting",
  "message": "Space deletion initiated",
  "job_id": "job_delete_123",
  "estimated_completion": "2025-01-20T10:05:00Z"
}
```

### Content Upload & Processing

#### POST /api/v1/spaces/{id}/upload
**Upload content to space**

```typescript
// Multipart form data
POST /api/v1/spaces/space_abc123/upload
Content-Type: multipart/form-data

// Form fields
file: (binary)
type: "code" | "documentation" | "conversation"
metadata: {"language": "typescript", "project": "frontend"}

// Response (202 Accepted)
{
  "upload_id": "upload_123",
  "status": "processing",
  "files": [
    {
      "name": "index.ts",
      "size": 45678,
      "status": "chunking"
    }
  ],
  "job_id": "job_process_456"
}
```

#### POST /api/v1/spaces/{id}/index
**Trigger indexing/reindexing**

```typescript
// Request
{
  "strategy": "incremental" | "full",
  "options": {
    "parallel_workers": 4,
    "batch_size": 100,
    "use_npu": true
  }
}

// Response (202 Accepted)
{
  "job_id": "job_index_789",
  "status": "started",
  "estimated_duration": 300,
  "progress_url": "/api/v1/jobs/job_index_789"
}
```

### Memory Chunk Operations

#### GET /api/v1/chunks/{id}
**Get chunk details**

```typescript
// Response
{
  "id": "chunk_abc123",
  "space_id": "space_xyz789",
  "content": "export class AuthController {\n  async login(req: Request, res: Response) {\n    ...",
  "tokens": 234,
  "position": {
    "x": 125.67,
    "y": -45.23,
    "z": 89.45
  },
  "embedding": [0.123, -0.456, 0.789, ...], // 384 dimensions
  "metadata": {
    "file": "auth.controller.ts",
    "line_start": 45,
    "line_end": 67,
    "language": "typescript",
    "last_modified": "2025-01-15T10:00:00Z"
  },
  "neighbors": [
    {"id": "chunk_def456", "distance": 12.5},
    {"id": "chunk_ghi789", "distance": 15.3}
  ],
  "semantic_links": [
    {"id": "chunk_jkl012", "similarity": 0.89, "type": "imports"},
    {"id": "chunk_mno345", "similarity": 0.76, "type": "similar_logic"}
  ]
}
```

#### GET /api/v1/chunks
**Search chunks**

```typescript
// Query parameters
GET /api/v1/chunks?
  space_id=space_abc123&
  query=authentication&
  position=100,-50,75&
  radius=100&
  limit=20&
  min_similarity=0.7

// Response
{
  "chunks": [
    {
      "id": "chunk_abc123",
      "score": 0.92,
      "distance": 45.6,
      "preview": "...authentication flow...",
      "position": {"x": 125, "y": -45, "z": 89}
    }
  ],
  "total": 156,
  "page": 1,
  "query_time_ms": 23
}
```

### AI Agent Management

#### GET /api/v1/agents
**List all agents**

```typescript
// Response
{
  "agents": [
    {
      "id": "agent_llama_001",
      "name": "Llama Explorer",
      "model": {
        "type": "llama-8b",
        "quantization": "Q4_K_M",
        "context_window": 8192
      },
      "status": "active",
      "position": {"x": 100, "y": 0, "z": 50},
      "context": {
        "loaded_chunks": 15,
        "tokens_used": 6543,
        "tokens_available": 1649
      },
      "performance": {
        "tokens_per_second": 42.3,
        "avg_latency_ms": 23.7
      },
      "device": "gpu:0"
    }
  ]
}
```

#### POST /api/v1/agents
**Create new agent**

```typescript
// Request
{
  "name": "Code Analyzer",
  "model": "mistral-7b",
  "config": {
    "temperature": 0.7,
    "max_tokens": 2000,
    "device": "gpu",
    "quantization": "Q5_K_M"
  },
  "initial_position": {"x": 0, "y": 0, "z": 0}
}

// Response (201 Created)
{
  "id": "agent_mistral_002",
  "name": "Code Analyzer",
  "status": "initializing",
  "model_loading": {
    "progress": 0,
    "estimated_seconds": 15
  }
}
```

#### PUT /api/v1/agents/{id}/position
**Update agent position**

```typescript
// Request
{
  "position": {"x": 200, "y": 50, "z": -100},
  "orientation": {"yaw": 45, "pitch": 0, "roll": 0},
  "animation": "teleport" | "smooth" | "instant"
}

// Response
{
  "id": "agent_llama_001",
  "old_position": {"x": 100, "y": 0, "z": 50},
  "new_position": {"x": 200, "y": 50, "z": -100},
  "context_change": {
    "unloaded_chunks": 8,
    "loaded_chunks": 12,
    "tokens_delta": -234
  }
}
```

#### POST /api/v1/agents/{id}/query
**Submit query to agent**

```typescript
// Request
{
  "query": "Explain the authentication flow",
  "context_mode": "visible" | "all" | "relevant",
  "max_tokens": 500,
  "stream": true
}

// Response (if stream=false)
{
  "query_id": "query_123",
  "response": "The authentication flow consists of...",
  "usage": {
    "prompt_tokens": 6543,
    "completion_tokens": 234,
    "total_tokens": 6777
  },
  "context_chunks_used": ["chunk_abc123", "chunk_def456"],
  "processing_time_ms": 567
}
```

### Spatial Operations

#### POST /api/v1/spatial/search
**Semantic spatial search**

```typescript
// Request
{
  "query": "database connection handling",
  "center": {"x": 0, "y": 0, "z": 0},
  "radius": 500,
  "limit": 50,
  "filters": {
    "types": ["code", "documentation"],
    "languages": ["python", "typescript"],
    "min_similarity": 0.7
  }
}

// Response
{
  "results": [
    {
      "chunk_id": "chunk_db_001",
      "position": {"x": 145, "y": 23, "z": -67},
      "distance": 167.8,
      "similarity": 0.89,
      "preview": "class DatabaseConnection...",
      "highlights": ["connection", "database", "pool"]
    }
  ],
  "clusters": [
    {
      "center": {"x": 150, "y": 20, "z": -70},
      "radius": 50,
      "chunk_count": 15,
      "dominant_theme": "database"
    }
  ],
  "search_time_ms": 45
}
```

#### GET /api/v1/spatial/frustum
**Get chunks in view frustum**

```typescript
// Request
POST /api/v1/spatial/frustum
{
  "position": {"x": 100, "y": 50, "z": 0},
  "direction": {"x": 0.7, "y": 0, "z": 0.7},
  "fov": 60,
  "near": 1,
  "far": 100
}

// Response
{
  "visible_chunks": [
    {
      "id": "chunk_vis_001",
      "position": {"x": 120, "y": 45, "z": 20},
      "distance": 28.3,
      "size": 234,
      "lod_level": 0
    }
  ],
  "total_visible": 234,
  "total_tokens": 45678,
  "recommended_load": ["chunk_vis_001", "chunk_vis_002"]
}
```

### System Monitoring

#### GET /api/v1/system/status
**Get system status**

```typescript
// Response
{
  "status": "healthy",
  "uptime": 3600,
  "version": "1.0.0",
  "hardware": {
    "cpu": {
      "model": "AMD Ryzen AI Max+ 395",
      "cores": 16,
      "usage": 34.5
    },
    "gpu": [
      {
        "model": "NVIDIA RTX 5060",
        "memory_used": 4567,
        "memory_total": 8192,
        "temperature": 67
      }
    ],
    "npu": {
      "model": "AMD XDNA 2",
      "tops": 50,
      "usage": 45.6
    },
    "memory": {
      "used": 12345,
      "total": 32768,
      "cached": 4567
    }
  },
  "models": {
    "loaded": ["llama-8b", "mistral-7b"],
    "available": ["phi-3", "qwen-7b"]
  },
  "performance": {
    "avg_query_time_ms": 234,
    "queries_per_second": 4.3,
    "active_connections": 12
  }
}
```

#### GET /api/v1/system/metrics
**Get performance metrics**

```typescript
// Response
{
  "timestamp": "2025-01-20T12:00:00Z",
  "period": "last_5_minutes",
  "metrics": {
    "requests": {
      "total": 1234,
      "success": 1200,
      "error": 34,
      "rate_per_second": 4.1
    },
    "latency": {
      "p50": 23,
      "p95": 67,
      "p99": 123,
      "max": 456
    },
    "context_streaming": {
      "chunks_loaded": 5678,
      "chunks_unloaded": 4567,
      "cache_hits": 3456,
      "cache_misses": 1234,
      "hit_rate": 0.73
    },
    "ai_inference": {
      "queries_processed": 234,
      "tokens_generated": 45678,
      "avg_tokens_per_second": 38.5
    }
  }
}
```

---

## 3. WEBSOCKET API

### Connection Protocol

```typescript
// Connection handshake
ws://localhost:8081/stream/v1?token={jwt_token}

// Initial message from server
{
  "type": "connection.established",
  "id": "conn_abc123",
  "timestamp": 1234567890,
  "server_version": "1.0.0",
  "capabilities": ["streaming", "binary", "compression"]
}

// Client acknowledgment
{
  "type": "connection.acknowledge",
  "client_version": "1.0.0",
  "requested_features": ["streaming", "compression"]
}
```

### Message Types

#### Context Streaming

```typescript
// Client -> Server: Request context stream
{
  "id": "msg_001",
  "type": "context.stream.start",
  "payload": {
    "agent_id": "agent_llama_001",
    "position": {"x": 100, "y": 0, "z": 50},
    "radius": 100,
    "max_tokens": 8000,
    "priority": "high"
  }
}

// Server -> Client: Stream chunks
{
  "id": "msg_001_resp",
  "type": "context.chunk",
  "payload": {
    "chunk_id": "chunk_abc123",
    "content": "...",
    "tokens": 234,
    "position": {"x": 110, "y": 5, "z": 45},
    "sequence": 1,
    "total": 15
  }
}

// Server -> Client: Stream complete
{
  "id": "msg_001_complete",
  "type": "context.stream.complete",
  "payload": {
    "total_chunks": 15,
    "total_tokens": 6789,
    "load_time_ms": 234
  }
}
```

#### Agent Updates

```typescript
// Client -> Server: Move agent
{
  "id": "msg_002",
  "type": "agent.move",
  "payload": {
    "agent_id": "agent_llama_001",
    "target": {"x": 200, "y": 50, "z": 100},
    "speed": 10
  }
}

// Server -> Client: Position updates (continuous)
{
  "type": "agent.position.update",
  "payload": {
    "agent_id": "agent_llama_001",
    "position": {"x": 150, "y": 25, "z": 75},
    "velocity": {"x": 5, "y": 2.5, "z": 2.5},
    "context_changes": {
      "loaded": ["chunk_new_001"],
      "unloaded": ["chunk_old_001"]
    }
  }
}
```

#### Query Streaming

```typescript
// Client -> Server: Submit streaming query
{
  "id": "msg_003",
  "type": "query.submit",
  "payload": {
    "agent_id": "agent_llama_001",
    "query": "Explain this function",
    "stream": true,
    "max_tokens": 500
  }
}

// Server -> Client: Stream tokens
{
  "type": "query.token",
  "payload": {
    "query_id": "query_123",
    "token": "The",
    "position": 0
  }
}

{
  "type": "query.token",
  "payload": {
    "query_id": "query_123",
    "token": " function",
    "position": 1
  }
}

// Server -> Client: Query complete
{
  "type": "query.complete",
  "payload": {
    "query_id": "query_123",
    "total_tokens": 234,
    "usage": {
      "prompt": 6543,
      "completion": 234
    }
  }
}
```

### Binary Protocol

```typescript
// Binary message format for performance
// [1 byte: type][4 bytes: length][N bytes: payload]

enum BinaryMessageType {
  EMBEDDING = 0x01,      // Float32 arrays
  CHUNK_BATCH = 0x02,    // Multiple chunks
  POSITION_BATCH = 0x03, // Position updates
  METRICS = 0x04         // Performance data
}

// Example: Embedding message
// Type: 0x01
// Length: 1540 (384 floats * 4 bytes + 4 byte chunk_id)
// Payload: [chunk_id:uint32][embedding:float32[384]]
```

---

## 4. GRPC API

### Service Definitions

```protobuf
syntax = "proto3";

package infinite.v1;

// High-performance spatial index service
service SpatialIndex {
  // Generate embeddings using NPU
  rpc GenerateEmbedding(EmbeddingRequest) returns (EmbeddingResponse);

  // Batch generate embeddings
  rpc BatchGenerateEmbeddings(BatchEmbeddingRequest) returns (stream EmbeddingResponse);

  // Stream context chunks based on position
  rpc StreamContext(ContextStreamRequest) returns (stream ContextChunk);

  // Perform spatial query
  rpc SpatialQuery(SpatialQueryRequest) returns (SpatialQueryResponse);

  // Get octree node data
  rpc GetOctreeNode(OctreeNodeRequest) returns (OctreeNode);
}

// AI inference service
service AIInference {
  // Stream inference tokens
  rpc StreamInference(InferenceRequest) returns (stream InferenceToken);

  // Batch inference
  rpc BatchInference(BatchInferenceRequest) returns (BatchInferenceResponse);

  // Get model info
  rpc GetModelInfo(ModelInfoRequest) returns (ModelInfo);
}
```

### Message Definitions

```protobuf
message Vector3 {
  float x = 1;
  float y = 2;
  float z = 3;
}

message EmbeddingRequest {
  string text = 1;
  string model = 2;
  bool use_npu = 3;
  int32 dimensions = 4;
}

message EmbeddingResponse {
  string id = 1;
  repeated float embedding = 2;
  int32 dimensions = 3;
  int64 compute_time_us = 4;
  string device_used = 5;
}

message ContextChunk {
  string id = 1;
  bytes content = 2;
  Vector3 position = 3;
  int32 tokens = 4;
  repeated float embedding = 5;
  map<string, string> metadata = 6;
}

message ContextStreamRequest {
  string agent_id = 1;
  Vector3 position = 2;
  float radius = 3;
  int32 max_tokens = 4;
  repeated string filters = 5;
}

message InferenceRequest {
  string model_id = 1;
  string prompt = 2;
  int32 max_tokens = 3;
  float temperature = 4;
  bool stream = 5;
  map<string, string> parameters = 6;
}

message InferenceToken {
  string token = 1;
  int32 position = 2;
  float logprob = 3;
  int64 timestamp_us = 4;
}
```

---

## 5. ERROR HANDLING

### Error Response Format

```typescript
{
  "error": {
    "code": "CONTEXT_OVERFLOW",
    "message": "Context window exceeded maximum token limit",
    "details": {
      "requested_tokens": 9000,
      "max_tokens": 8192,
      "suggestion": "Reduce search radius or filter chunks"
    },
    "trace_id": "trace_abc123",
    "timestamp": "2025-01-20T12:00:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request data |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict |
| `CONTEXT_OVERFLOW` | 413 | Context window exceeded |
| `RATE_LIMIT` | 429 | Rate limit exceeded |
| `MODEL_UNAVAILABLE` | 503 | AI model not available |
| `INTERNAL_ERROR` | 500 | Server error |

---

## 6. RATE LIMITING

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1234567890
X-RateLimit-Burst: 50
```

### Rate Limit Rules

```typescript
const rateLimits = {
  anonymous: {
    requests_per_minute: 60,
    burst: 10
  },
  authenticated: {
    requests_per_minute: 600,
    burst: 50
  },
  premium: {
    requests_per_minute: 6000,
    burst: 200
  }
};
```

---

## 7. CACHING STRATEGY

### Cache Headers

```http
# Response headers
Cache-Control: public, max-age=3600
ETag: "abc123def456"
Last-Modified: Wed, 21 Oct 2025 07:28:00 GMT

# Request headers
If-None-Match: "abc123def456"
If-Modified-Since: Wed, 21 Oct 2025 07:28:00 GMT
```

### Cacheable Endpoints

```typescript
const cacheRules = {
  '/api/v1/chunks/{id}': {
    ttl: 3600,
    vary: ['Accept', 'Authorization']
  },
  '/api/v1/spaces': {
    ttl: 300,
    invalidate_on: ['POST', 'PUT', 'DELETE']
  },
  '/api/v1/system/status': {
    ttl: 10,
    cache: 'no-store'
  }
};
```

---

## 8. PAGINATION

### Pagination Parameters

```typescript
// Request
GET /api/v1/chunks?page=2&per_page=50&sort=relevance&order=desc

// Response
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 50,
    "total": 1234,
    "total_pages": 25,
    "has_next": true,
    "has_prev": true
  },
  "links": {
    "first": "/api/v1/chunks?page=1&per_page=50",
    "prev": "/api/v1/chunks?page=1&per_page=50",
    "next": "/api/v1/chunks?page=3&per_page=50",
    "last": "/api/v1/chunks?page=25&per_page=50"
  }
}
```

---

## 9. API TESTING

### Health Check Endpoint

```http
GET /api/v1/health

Response:
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "npu": "healthy",
    "gpu": "healthy"
  },
  "timestamp": "2025-01-20T12:00:00Z"
}
```

### Test Endpoints

```http
# Echo test
POST /api/v1/test/echo
Body: {"message": "test"}
Response: {"echo": "test", "timestamp": 1234567890}

# Latency test
GET /api/v1/test/latency?delay=100
Response: {"requested_delay": 100, "actual_delay": 101}

# Load test endpoint
POST /api/v1/test/load
Body: {"chunks": 100, "tokens": 5000}
Response: {"status": "completed", "time_ms": 234}
```

---

## 10. PERFORMANCE REQUIREMENTS

### Latency Targets

| Endpoint Type | P50 | P95 | P99 |
|--------------|-----|-----|-----|
| GET chunk | 10ms | 25ms | 50ms |
| Spatial search | 25ms | 50ms | 100ms |
| Context stream | 50ms | 100ms | 200ms |
| AI query | 100ms | 500ms | 1000ms |

### Throughput Targets

- 10,000 requests/second (read)
- 1,000 requests/second (write)
- 100 concurrent WebSocket connections
- 50 concurrent AI inference requests

### SLA Commitments

- 99.9% uptime
- <100ms P95 latency for reads
- <500ms P95 latency for writes
- Zero data loss

---

## SUCCESS METRICS

### API Performance
- All endpoints meet latency targets
- 99.9% availability
- Horizontal scalability to 10K RPS

### Developer Experience
- Comprehensive documentation
- Consistent error handling
- Intuitive endpoint design

### Security
- JWT authentication implemented
- Rate limiting enforced
- Input validation on all endpoints

---

**Total Endpoints:** 40+ REST, 20+ WebSocket events, 10+ gRPC methods
**Protocols:** REST (primary), WebSocket (streaming), gRPC (performance)
**Authentication:** JWT, API keys, session cookies
**Performance:** Sub-100ms P95 for critical paths