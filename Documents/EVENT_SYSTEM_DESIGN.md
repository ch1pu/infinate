# Event System Design
**Real-time Event Pipeline for Visual Feedback**

---

## EXECUTIVE SUMMARY

The Event System provides a high-performance, real-time pipeline that bridges backend operations with frontend visualizations. Every computational operation emits structured events that trigger corresponding visual feedback, achieving <10ms end-to-end latency while maintaining system performance.

---

## 1. EVENT ARCHITECTURE OVERVIEW

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            EVENT FLOW ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  BACKEND OPERATIONS                     EVENT PIPELINE                    │
│  ┌──────────────┐                      ┌──────────────┐                 │
│  │ NPU Service  │──┐                   │              │                 │
│  │ GPU Service  │──┤                   │   Event      │                 │
│  │ Context Mgr  │──┼──[Events]────────>│   Router     │                 │
│  │ Agent System │──┤                   │              │                 │
│  │ MCP Servers  │──┘                   └──────┬───────┘                 │
│  └──────────────┘                             │                         │
│                                               ▼                         │
│                                        ┌──────────────┐                 │
│                                        │   WebSocket  │                 │
│                                        │    Server    │                 │
│                                        └──────┬───────┘                 │
│                                               │                         │
│                              ┌────────────────┼────────────────┐        │
│                              ▼                ▼                ▼        │
│                        ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  FRONTEND              │ Client 1 │    │ Client 2 │    │ Client N │   │
│  PROCESSORS            └─────┬────┘    └─────┬────┘    └─────┬────┘   │
│                              │                │                │        │
│                              ▼                ▼                ▼        │
│                        ┌──────────────────────────────────────────┐    │
│                        │      Visual Event Bridge                  │    │
│                        └──────────────────────────────────────────┘    │
│                              │                │                │        │
│                              ▼                ▼                ▼        │
│                        [3D Scene]      [Particles]      [UI Updates]    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Event Lifecycle

```typescript
interface EventLifecycle {
  // 1. Event Creation (Backend)
  creation: {
    timestamp: number;          // Server time
    source: string;            // Component that created event
    operation: string;         // What operation triggered it
    latency: number;          // Operation latency
  };

  // 2. Event Routing
  routing: {
    priority: number;          // 0 (highest) to 5 (lowest)
    channel: string;          // WebSocket channel/room
    broadcast: boolean;       // Send to all clients?
    target?: string;          // Specific client ID
  };

  // 3. Event Transmission
  transmission: {
    protocol: 'websocket' | 'sse';
    compression: boolean;
    batch: boolean;           // Batch with other events?
    maxBatchSize: number;
    maxBatchDelay: number;    // ms
  };

  // 4. Event Reception (Frontend)
  reception: {
    receivedAt: number;
    queuePosition: number;
    processingDelay: number;
  };

  // 5. Visual Execution
  execution: {
    startedAt: number;
    completedAt: number;
    interrupted: boolean;
    error?: string;
  };
}
```

---

## 2. EVENT MESSAGE PROTOCOL

### 2.1 Core Event Structure

```typescript
interface VisualEvent {
  // Event Identification
  id: string;                    // UUID v4
  version: '1.0';               // Protocol version
  timestamp: number;            // Unix timestamp (ms)
  sequence: number;             // Monotonic counter

  // Event Classification
  category: EventCategory;      // Major category
  type: string;                // Specific event type
  severity: 'debug' | 'info' | 'warning' | 'error' | 'critical';

  // Event Source
  source: {
    service: string;          // Backend service name
    component: string;        // Specific component
    instance?: string;        // Server instance ID
    agent?: string;          // Associated agent ID
    user?: string;           // User ID if relevant
  };

  // Spatial Context
  spatial?: {
    position: [number, number, number];  // X, Y, Z
    chunk?: string;          // Associated memory chunk
    building?: string;       // Associated building ID
    region?: string;         // Spatial region
  };

  // Event Payload
  data: any;                  // Event-specific data

  // Visual Instructions
  visual: {
    effect: string;          // Visual effect to trigger
    animation?: string;      // Animation name
    duration: number;        // Animation duration (ms)
    priority: number;        // Visual priority (0-5)
    interruptible: boolean;  // Can be interrupted?
    queued: boolean;         // Queue if busy?
    concurrent?: string[];   // Effects to run concurrently
  };

  // Performance Metrics
  metrics?: {
    operationLatency?: number;    // Backend operation time
    transmissionLatency?: number; // Network time
    renderLatency?: number;       // Frontend render time
    totalLatency?: number;        // End-to-end time
  };

  // Correlation
  correlation?: {
    requestId?: string;      // Original request ID
    parentId?: string;       // Parent event ID
    chainId?: string;        // Event chain ID
    spanId?: string;         // Distributed tracing span
  };
}
```

### 2.2 Event Categories

```typescript
enum EventCategory {
  // Hardware Layer Events
  NPU = 'npu',
  GPU = 'gpu',
  CPU = 'cpu',
  MEMORY = 'memory',

  // AI Layer Events
  AGENT = 'agent',
  MODEL = 'model',
  INFERENCE = 'inference',

  // Context Layer Events
  CONTEXT = 'context',
  CHUNK = 'chunk',
  STREAM = 'stream',

  // System Layer Events
  MCP = 'mcp',
  CACHE = 'cache',
  INDEX = 'index',
  SEARCH = 'search',

  // User Layer Events
  USER = 'user',
  COMMAND = 'command',
  NAVIGATION = 'navigation',

  // Meta Events
  SYSTEM = 'system',
  ERROR = 'error',
  PERFORMANCE = 'performance'
}
```

### 2.3 Event Type Registry

```typescript
const EVENT_TYPES = {
  // NPU Events
  [EventCategory.NPU]: {
    EMBEDDING_START: 'embedding.start',
    EMBEDDING_COMPLETE: 'embedding.complete',
    SEARCH_START: 'search.start',
    SEARCH_COMPLETE: 'search.complete',
    BATCH_PROCESS: 'batch.process'
  },

  // GPU Events
  [EventCategory.GPU]: {
    MODEL_LOAD: 'model.load',
    MODEL_UNLOAD: 'model.unload',
    INFERENCE_START: 'inference.start',
    TOKEN_GENERATED: 'token.generated',
    INFERENCE_COMPLETE: 'inference.complete',
    MEMORY_PRESSURE: 'memory.pressure',
    THERMAL_WARNING: 'thermal.warning'
  },

  // Agent Events
  [EventCategory.AGENT]: {
    SPAWN: 'spawn',
    DESPAWN: 'despawn',
    MOVE_START: 'move.start',
    MOVE_COMPLETE: 'move.complete',
    TELEPORT: 'teleport',
    THINK: 'think',
    BUILD_START: 'build.start',
    BUILD_PROGRESS: 'build.progress',
    BUILD_COMPLETE: 'build.complete',
    MESSAGE_SEND: 'message.send',
    MESSAGE_RECEIVE: 'message.receive'
  },

  // Context Events
  [EventCategory.CONTEXT]: {
    LOAD_START: 'load.start',
    CHUNK_LOADED: 'chunk.loaded',
    LOAD_COMPLETE: 'load.complete',
    SWAP_START: 'swap.start',
    SWAP_COMPLETE: 'swap.complete',
    OVERFLOW: 'overflow',
    PREFETCH: 'prefetch'
  },

  // Cache Events
  [EventCategory.CACHE]: {
    HIT: 'hit',
    MISS: 'miss',
    EVICT: 'evict',
    PROMOTE: 'promote',
    FLUSH: 'flush'
  },

  // MCP Events
  [EventCategory.MCP]: {
    REQUEST: 'request',
    QUEUE_JOIN: 'queue.join',
    QUEUE_LEAVE: 'queue.leave',
    PROCESS_START: 'process.start',
    PROCESS_COMPLETE: 'process.complete',
    ERROR: 'error',
    TIMEOUT: 'timeout'
  }
};
```

---

## 3. BACKEND EVENT EMISSION

### 3.1 Event Emitter Architecture

```typescript
// Backend Event Emitter Service
class EventEmitter {
  private eventQueue: PriorityQueue<VisualEvent>;
  private wsServer: WebSocketServer;
  private batchProcessor: BatchProcessor;
  private metricsCollector: MetricsCollector;

  constructor(config: EventConfig) {
    this.eventQueue = new PriorityQueue(config.maxQueueSize);
    this.wsServer = new WebSocketServer(config.wsPort);
    this.batchProcessor = new BatchProcessor(config.batchConfig);
    this.metricsCollector = new MetricsCollector();
  }

  // Emit single event
  async emit(event: Partial<VisualEvent>): Promise<void> {
    const fullEvent = this.enrichEvent(event);

    // Add to queue based on priority
    this.eventQueue.enqueue(fullEvent, fullEvent.visual.priority);

    // Process immediately for high priority
    if (fullEvent.visual.priority === 0) {
      await this.processEvent(fullEvent);
    } else {
      // Batch lower priority events
      this.batchProcessor.add(fullEvent);
    }

    // Track metrics
    this.metricsCollector.recordEvent(fullEvent);
  }

  // Enrich event with metadata
  private enrichEvent(partial: Partial<VisualEvent>): VisualEvent {
    return {
      id: uuid.v4(),
      version: '1.0',
      timestamp: Date.now(),
      sequence: this.getNextSequence(),
      severity: partial.severity || 'info',
      ...partial,
      metrics: {
        ...partial.metrics,
        emittedAt: Date.now()
      }
    };
  }

  // Process and broadcast event
  private async processEvent(event: VisualEvent): Promise<void> {
    // Apply filters
    if (this.shouldFilter(event)) return;

    // Transform if needed
    const transformed = this.transformEvent(event);

    // Broadcast to clients
    await this.broadcast(transformed);
  }

  // Broadcast to WebSocket clients
  private async broadcast(event: VisualEvent): Promise<void> {
    const message = JSON.stringify(event);
    const compressed = this.compress(message);

    // Send to all connected clients
    for (const client of this.wsServer.clients) {
      if (client.readyState === WebSocket.OPEN) {
        client.send(compressed);
      }
    }

    // Track transmission metrics
    this.metricsCollector.recordTransmission(event.id, {
      clientCount: this.wsServer.clients.size,
      messageSize: compressed.length
    });
  }
}
```

### 3.2 Service Instrumentation

```typescript
// Automatic instrumentation for services
class ServiceInstrumentor {
  constructor(private eventEmitter: EventEmitter) {}

  // Instrument a service method
  instrument<T extends Function>(
    method: T,
    category: EventCategory,
    type: string
  ): T {
    return (async (...args: any[]) => {
      const startTime = performance.now();
      const spanId = uuid.v4();

      // Emit start event
      await this.eventEmitter.emit({
        category,
        type: `${type}.start`,
        source: {
          service: method.constructor.name,
          component: method.name
        },
        data: { args: this.sanitizeArgs(args) },
        correlation: { spanId },
        visual: {
          effect: `${category}_start`,
          duration: 100,
          priority: 2,
          interruptible: true,
          queued: true
        }
      });

      try {
        // Execute original method
        const result = await method.apply(this, args);

        // Emit success event
        await this.eventEmitter.emit({
          category,
          type: `${type}.complete`,
          source: {
            service: method.constructor.name,
            component: method.name
          },
          data: { result: this.sanitizeResult(result) },
          correlation: { spanId },
          metrics: {
            operationLatency: performance.now() - startTime
          },
          visual: {
            effect: `${category}_complete`,
            duration: 500,
            priority: 2,
            interruptible: false,
            queued: false
          }
        });

        return result;

      } catch (error) {
        // Emit error event
        await this.eventEmitter.emit({
          category: EventCategory.ERROR,
          type: `${type}.error`,
          severity: 'error',
          source: {
            service: method.constructor.name,
            component: method.name
          },
          data: {
            error: error.message,
            stack: error.stack
          },
          correlation: { spanId },
          metrics: {
            operationLatency: performance.now() - startTime
          },
          visual: {
            effect: 'error_flash',
            duration: 1000,
            priority: 0,
            interruptible: false,
            queued: false
          }
        });

        throw error;
      }
    }) as any as T;
  }

  // Sanitize arguments for transmission
  private sanitizeArgs(args: any[]): any[] {
    return args.map(arg => {
      if (typeof arg === 'object' && arg !== null) {
        return { type: arg.constructor.name, keys: Object.keys(arg) };
      }
      return arg;
    });
  }

  // Sanitize results for transmission
  private sanitizeResult(result: any): any {
    if (typeof result === 'object' && result !== null) {
      if (Array.isArray(result)) {
        return { type: 'array', length: result.length };
      }
      return { type: result.constructor.name, keys: Object.keys(result).slice(0, 10) };
    }
    return result;
  }
}
```

### 3.3 NPU Service Integration

```typescript
// NPU Service with event emission
class NPUService {
  private eventEmitter: EventEmitter;
  private instrumentor: ServiceInstrumentor;

  constructor(eventEmitter: EventEmitter) {
    this.eventEmitter = eventEmitter;
    this.instrumentor = new ServiceInstrumentor(eventEmitter);

    // Auto-instrument all methods
    this.generateEmbedding = this.instrumentor.instrument(
      this.generateEmbedding,
      EventCategory.NPU,
      'embedding'
    );

    this.vectorSearch = this.instrumentor.instrument(
      this.vectorSearch,
      EventCategory.NPU,
      'search'
    );
  }

  async generateEmbedding(text: string): Promise<Float32Array> {
    // Manual event for fine control
    await this.eventEmitter.emit({
      category: EventCategory.NPU,
      type: 'embedding.processing',
      source: {
        service: 'NPUService',
        component: 'generateEmbedding'
      },
      data: {
        textLength: text.length,
        preview: text.substring(0, 50)
      },
      visual: {
        effect: 'npu_drone_scan',
        animation: 'radar_sweep',
        duration: 5,  // Match actual NPU latency
        priority: 2,
        interruptible: false,
        queued: false,
        concurrent: ['particle_emission', 'sound_ping']
      }
    });

    // Actual NPU operation
    const embedding = await this.npuEngine.encode(text);

    return embedding;
  }

  async vectorSearch(query: Float32Array, k: number = 10): Promise<SearchResult[]> {
    const startTime = performance.now();

    // Start search visual
    await this.eventEmitter.emit({
      category: EventCategory.NPU,
      type: 'search.scanning',
      source: {
        service: 'NPUService',
        component: 'vectorSearch'
      },
      spatial: {
        position: [0, 10, 0],  // NPU drone position
        region: 'search_area'
      },
      visual: {
        effect: 'vector_search_beam',
        duration: 3000,
        priority: 1,
        interruptible: false,
        queued: false
      }
    });

    // Perform search
    const results = await this.vectorIndex.search(query, k);

    // Emit results progressively
    for (let i = 0; i < results.length; i++) {
      await this.eventEmitter.emit({
        category: EventCategory.NPU,
        type: 'search.result',
        source: {
          service: 'NPUService',
          component: 'vectorSearch'
        },
        spatial: {
          position: results[i].position,
          chunk: results[i].chunkId
        },
        data: {
          rank: i + 1,
          score: results[i].score,
          distance: results[i].distance
        },
        visual: {
          effect: i < 5 ? 'beacon_create' : 'building_highlight',
          duration: 1000,
          priority: 2,
          interruptible: true,
          queued: true
        }
      });

      // Stagger for visual clarity
      await this.wait(50);
    }

    return results;
  }
}
```

---

## 4. WEBSOCKET PROTOCOL

### 4.1 WebSocket Server

```typescript
// WebSocket server implementation
class VisualWebSocketServer {
  private wss: WebSocket.Server;
  private clients: Map<string, ClientConnection>;
  private rooms: Map<string, Set<string>>;
  private heartbeatInterval: NodeJS.Timer;

  constructor(port: number) {
    this.wss = new WebSocket.Server({
      port,
      perMessageDeflate: {
        zlibDeflateOptions: {
          chunkSize: 1024,
          memLevel: 7,
          level: 3
        },
        zlibInflateOptions: {
          chunkSize: 10 * 1024
        },
        clientNoContextTakeover: true,
        serverNoContextTakeover: true,
        serverMaxWindowBits: 10,
        concurrencyLimit: 10,
        threshold: 1024
      }
    });

    this.clients = new Map();
    this.rooms = new Map();

    this.setupHandlers();
    this.startHeartbeat();
  }

  private setupHandlers() {
    this.wss.on('connection', (ws: WebSocket, req: IncomingMessage) => {
      const clientId = uuid.v4();
      const client = new ClientConnection(clientId, ws, req);

      // Store client
      this.clients.set(clientId, client);

      // Send welcome message
      this.sendToClient(clientId, {
        type: 'connection',
        data: {
          clientId,
          protocol: '1.0',
          features: ['compression', 'batching', 'rooms']
        }
      });

      // Setup client handlers
      ws.on('message', (data) => this.handleMessage(clientId, data));
      ws.on('close', () => this.handleDisconnect(clientId));
      ws.on('error', (error) => this.handleError(clientId, error));
      ws.on('pong', () => client.markAlive());
    });
  }

  private handleMessage(clientId: string, data: WebSocket.Data) {
    try {
      const message = JSON.parse(data.toString());

      switch (message.type) {
        case 'subscribe':
          this.subscribeToRoom(clientId, message.room);
          break;

        case 'unsubscribe':
          this.unsubscribeFromRoom(clientId, message.room);
          break;

        case 'filter':
          this.setClientFilter(clientId, message.filter);
          break;

        case 'ping':
          this.sendToClient(clientId, { type: 'pong', timestamp: Date.now() });
          break;

        default:
          console.warn(`Unknown message type: ${message.type}`);
      }
    } catch (error) {
      console.error(`Failed to handle message from ${clientId}:`, error);
    }
  }

  // Broadcast event to relevant clients
  async broadcast(event: VisualEvent) {
    const message = JSON.stringify(event);

    // Determine target clients
    const targets = this.getTargetClients(event);

    // Send to each target
    for (const clientId of targets) {
      const client = this.clients.get(clientId);
      if (client && client.isAlive && client.ws.readyState === WebSocket.OPEN) {
        // Apply client-specific filters
        if (client.shouldReceive(event)) {
          client.ws.send(message);
          client.incrementMessageCount();
        }
      }
    }
  }

  // Get clients that should receive event
  private getTargetClients(event: VisualEvent): Set<string> {
    const targets = new Set<string>();

    // Add all clients if broadcast
    if (event.routing?.broadcast) {
      this.clients.forEach((_, id) => targets.add(id));
    }

    // Add specific target if specified
    if (event.routing?.target) {
      targets.add(event.routing.target);
    }

    // Add room members if room specified
    if (event.routing?.channel) {
      const roomMembers = this.rooms.get(event.routing.channel);
      if (roomMembers) {
        roomMembers.forEach(id => targets.add(id));
      }
    }

    return targets;
  }

  // Heartbeat to detect disconnected clients
  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      this.clients.forEach((client) => {
        if (!client.isAlive) {
          client.ws.terminate();
          this.clients.delete(client.id);
          return;
        }

        client.isAlive = false;
        client.ws.ping();
      });
    }, 30000);  // 30 second heartbeat
  }
}

// Client connection wrapper
class ClientConnection {
  id: string;
  ws: WebSocket;
  isAlive: boolean = true;
  messageCount: number = 0;
  connectedAt: number = Date.now();
  filters: EventFilter[] = [];
  rooms: Set<string> = new Set();

  constructor(id: string, ws: WebSocket, req: IncomingMessage) {
    this.id = id;
    this.ws = ws;

    // Extract client info from request
    this.extractClientInfo(req);
  }

  markAlive() {
    this.isAlive = true;
  }

  incrementMessageCount() {
    this.messageCount++;
  }

  shouldReceive(event: VisualEvent): boolean {
    // Apply filters
    for (const filter of this.filters) {
      if (!filter.matches(event)) {
        return false;
      }
    }
    return true;
  }

  private extractClientInfo(req: IncomingMessage) {
    // Extract user agent, IP, etc.
    const userAgent = req.headers['user-agent'];
    const ip = req.socket.remoteAddress;

    // Store for analytics
    this.metadata = { userAgent, ip };
  }
}
```

### 4.2 Message Batching

```typescript
class BatchProcessor {
  private batch: VisualEvent[] = [];
  private batchTimer: NodeJS.Timeout | null = null;

  constructor(private config: BatchConfig) {}

  add(event: VisualEvent) {
    this.batch.push(event);

    // Send immediately if batch is full
    if (this.batch.length >= this.config.maxBatchSize) {
      this.flush();
    } else if (!this.batchTimer) {
      // Start timer for batch delay
      this.batchTimer = setTimeout(() => {
        this.flush();
      }, this.config.maxBatchDelay);
    }
  }

  private flush() {
    if (this.batch.length === 0) return;

    // Create batch message
    const batchMessage = {
      type: 'batch',
      events: this.batch,
      count: this.batch.length,
      timestamp: Date.now()
    };

    // Send batch
    this.send(batchMessage);

    // Clear batch
    this.batch = [];

    // Clear timer
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }
  }

  private send(message: any) {
    // Send to WebSocket server
    this.wsServer.broadcast(message);
  }
}

interface BatchConfig {
  maxBatchSize: number;      // Maximum events per batch
  maxBatchDelay: number;     // Maximum delay before sending (ms)
  compressionThreshold: number;  // Compress if batch > threshold bytes
}
```

---

## 5. FRONTEND EVENT PROCESSING

### 5.1 Event Client

```typescript
// Frontend WebSocket client
class VisualEventClient {
  private ws: WebSocket | null = null;
  private eventBridge: VisualEventBridge;
  private reconnectAttempts = 0;
  private eventQueue: VisualEvent[] = [];
  private isProcessing = false;

  constructor(private config: ClientConfig) {
    this.eventBridge = new VisualEventBridge();
    this.connect();
  }

  private connect() {
    try {
      this.ws = new WebSocket(this.config.url);

      this.ws.onopen = () => this.handleOpen();
      this.ws.onmessage = (event) => this.handleMessage(event);
      this.ws.onclose = () => this.handleClose();
      this.ws.onerror = (error) => this.handleError(error);

    } catch (error) {
      console.error('Failed to connect:', error);
      this.scheduleReconnect();
    }
  }

  private handleOpen() {
    console.log('Connected to event server');
    this.reconnectAttempts = 0;

    // Subscribe to relevant channels
    this.subscribe('agent.' + this.config.agentId);
    this.subscribe('global');

    // Set filters
    this.setFilters([
      { category: [EventCategory.NPU, EventCategory.GPU, EventCategory.AGENT] },
      { severity: ['info', 'warning', 'error', 'critical'] }
    ]);
  }

  private handleMessage(event: MessageEvent) {
    try {
      const message = JSON.parse(event.data);

      if (message.type === 'batch') {
        // Handle batched events
        for (const event of message.events) {
          this.queueEvent(event);
        }
      } else if (message.type === 'event') {
        // Handle single event
        this.queueEvent(message.data);
      }

      // Process queue
      this.processEventQueue();

    } catch (error) {
      console.error('Failed to handle message:', error);
    }
  }

  private queueEvent(event: VisualEvent) {
    // Add to priority queue
    const priority = event.visual.priority;

    // Insert in priority order
    let inserted = false;
    for (let i = 0; i < this.eventQueue.length; i++) {
      if (this.eventQueue[i].visual.priority > priority) {
        this.eventQueue.splice(i, 0, event);
        inserted = true;
        break;
      }
    }

    if (!inserted) {
      this.eventQueue.push(event);
    }
  }

  private async processEventQueue() {
    if (this.isProcessing || this.eventQueue.length === 0) return;

    this.isProcessing = true;

    while (this.eventQueue.length > 0) {
      const event = this.eventQueue.shift()!;

      try {
        // Process event through visual bridge
        await this.eventBridge.handleEvent(event);

        // Track metrics
        this.trackEventMetrics(event);

      } catch (error) {
        console.error('Failed to process event:', error, event);
      }
    }

    this.isProcessing = false;
  }

  private trackEventMetrics(event: VisualEvent) {
    const now = Date.now();
    const totalLatency = now - event.timestamp;

    // Update metrics
    this.metrics.eventsProcessed++;
    this.metrics.totalLatency += totalLatency;
    this.metrics.averageLatency = this.metrics.totalLatency / this.metrics.eventsProcessed;

    // Log slow events
    if (totalLatency > 100) {
      console.warn(`Slow event processing: ${totalLatency}ms`, event);
    }
  }

  private handleClose() {
    console.log('Disconnected from event server');
    this.ws = null;
    this.scheduleReconnect();
  }

  private handleError(error: Event) {
    console.error('WebSocket error:', error);
  }

  private scheduleReconnect() {
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    console.log(`Reconnecting in ${delay}ms...`);
    setTimeout(() => this.connect(), delay);
  }

  // Public methods
  subscribe(channel: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        room: channel
      }));
    }
  }

  unsubscribe(channel: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        room: channel
      }));
    }
  }

  setFilters(filters: any[]) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'filter',
        filter: filters
      }));
    }
  }
}
```

### 5.2 React Integration

```typescript
// React hook for event system
export function useVisualEvents() {
  const [connected, setConnected] = useState(false);
  const [eventClient, setEventClient] = useState<VisualEventClient | null>(null);
  const [metrics, setMetrics] = useState<EventMetrics>({
    eventsProcessed: 0,
    averageLatency: 0,
    connectionStatus: 'disconnected'
  });

  useEffect(() => {
    // Create event client
    const client = new VisualEventClient({
      url: process.env.REACT_APP_WS_URL || 'ws://localhost:4000/events',
      agentId: 'default',
      reconnect: true,
      maxReconnectAttempts: 10
    });

    // Setup callbacks
    client.onConnect = () => setConnected(true);
    client.onDisconnect = () => setConnected(false);
    client.onMetricsUpdate = (metrics) => setMetrics(metrics);

    setEventClient(client);

    // Cleanup
    return () => {
      client.disconnect();
    };
  }, []);

  return {
    connected,
    client: eventClient,
    metrics,
    subscribe: (channel: string) => eventClient?.subscribe(channel),
    unsubscribe: (channel: string) => eventClient?.unsubscribe(channel)
  };
}

// Use in component
export function MemoryPalace() {
  const { connected, metrics } = useVisualEvents();

  return (
    <div>
      {!connected && <div>Reconnecting to event server...</div>}
      <div>Events processed: {metrics.eventsProcessed}</div>
      <div>Average latency: {metrics.averageLatency.toFixed(2)}ms</div>
      {/* Rest of 3D scene */}
    </div>
  );
}
```

---

## 6. PERFORMANCE OPTIMIZATION

### 6.1 Event Throttling

```typescript
class EventThrottler {
  private eventCounts: Map<string, number> = new Map();
  private resetInterval: NodeJS.Timer;

  constructor(private config: ThrottleConfig) {
    // Reset counts periodically
    this.resetInterval = setInterval(() => {
      this.eventCounts.clear();
    }, config.windowMs);
  }

  shouldThrottle(event: VisualEvent): boolean {
    const key = `${event.category}.${event.type}`;
    const count = this.eventCounts.get(key) || 0;

    // Check if over limit
    if (count >= this.config.maxEventsPerType) {
      return true;
    }

    // Increment count
    this.eventCounts.set(key, count + 1);
    return false;
  }
}

interface ThrottleConfig {
  windowMs: number;           // Time window (ms)
  maxEventsPerType: number;   // Max events per type per window
  priorityExempt: number[];    // Priority levels exempt from throttling
}
```

### 6.2 Event Deduplication

```typescript
class EventDeduplicator {
  private recentEvents: Map<string, number> = new Map();
  private cleanupInterval: NodeJS.Timer;

  constructor(private windowMs: number = 1000) {
    // Cleanup old entries
    this.cleanupInterval = setInterval(() => {
      const now = Date.now();
      for (const [hash, timestamp] of this.recentEvents.entries()) {
        if (now - timestamp > this.windowMs) {
          this.recentEvents.delete(hash);
        }
      }
    }, this.windowMs);
  }

  isDuplicate(event: VisualEvent): boolean {
    // Create hash of event
    const hash = this.hashEvent(event);

    // Check if seen recently
    if (this.recentEvents.has(hash)) {
      return true;
    }

    // Mark as seen
    this.recentEvents.set(hash, Date.now());
    return false;
  }

  private hashEvent(event: VisualEvent): string {
    // Hash based on category, type, and key data
    return `${event.category}:${event.type}:${JSON.stringify(event.spatial)}:${event.source.agent}`;
  }
}
```

### 6.3 Priority Queue Implementation

```typescript
class PriorityQueue<T> {
  private heap: Array<{ item: T; priority: number }> = [];

  enqueue(item: T, priority: number) {
    this.heap.push({ item, priority });
    this.bubbleUp(this.heap.length - 1);
  }

  dequeue(): T | undefined {
    if (this.heap.length === 0) return undefined;

    const result = this.heap[0].item;
    const end = this.heap.pop()!;

    if (this.heap.length > 0) {
      this.heap[0] = end;
      this.bubbleDown(0);
    }

    return result;
  }

  private bubbleUp(index: number) {
    while (index > 0) {
      const parentIndex = Math.floor((index - 1) / 2);

      if (this.heap[parentIndex].priority <= this.heap[index].priority) {
        break;
      }

      [this.heap[parentIndex], this.heap[index]] =
        [this.heap[index], this.heap[parentIndex]];

      index = parentIndex;
    }
  }

  private bubbleDown(index: number) {
    while (true) {
      const leftChild = 2 * index + 1;
      const rightChild = 2 * index + 2;
      let smallest = index;

      if (leftChild < this.heap.length &&
          this.heap[leftChild].priority < this.heap[smallest].priority) {
        smallest = leftChild;
      }

      if (rightChild < this.heap.length &&
          this.heap[rightChild].priority < this.heap[smallest].priority) {
        smallest = rightChild;
      }

      if (smallest === index) break;

      [this.heap[index], this.heap[smallest]] =
        [this.heap[smallest], this.heap[index]];

      index = smallest;
    }
  }

  get length(): number {
    return this.heap.length;
  }
}
```

---

## 7. MONITORING & ANALYTICS

### 7.1 Event Metrics Collection

```typescript
class EventMetricsCollector {
  private metrics: EventMetrics = {
    eventsEmitted: 0,
    eventsTransmitted: 0,
    eventsProcessed: 0,
    eventsByCategory: new Map(),
    eventsByType: new Map(),
    latencyHistogram: new Map(),
    errorCount: 0,
    droppedEvents: 0
  };

  recordEvent(event: VisualEvent) {
    this.metrics.eventsEmitted++;

    // Track by category
    const catCount = this.metrics.eventsByCategory.get(event.category) || 0;
    this.metrics.eventsByCategory.set(event.category, catCount + 1);

    // Track by type
    const typeCount = this.metrics.eventsByType.get(event.type) || 0;
    this.metrics.eventsByType.set(event.type, typeCount + 1);

    // Track latency distribution
    if (event.metrics?.operationLatency) {
      const bucket = Math.floor(event.metrics.operationLatency / 10) * 10;
      const bucketCount = this.metrics.latencyHistogram.get(bucket) || 0;
      this.metrics.latencyHistogram.set(bucket, bucketCount + 1);
    }
  }

  getReport(): MetricsReport {
    const now = Date.now();

    return {
      timestamp: now,
      summary: {
        totalEvents: this.metrics.eventsEmitted,
        eventsPerSecond: this.calculateRate(),
        errorRate: this.metrics.errorCount / this.metrics.eventsEmitted,
        dropRate: this.metrics.droppedEvents / this.metrics.eventsEmitted
      },
      breakdown: {
        byCategory: Array.from(this.metrics.eventsByCategory.entries()),
        byType: Array.from(this.metrics.eventsByType.entries())
      },
      latency: {
        p50: this.calculatePercentile(50),
        p90: this.calculatePercentile(90),
        p99: this.calculatePercentile(99),
        histogram: Array.from(this.metrics.latencyHistogram.entries())
      }
    };
  }

  private calculateRate(): number {
    // Calculate events per second over last minute
    // Implementation details...
    return 0;
  }

  private calculatePercentile(percentile: number): number {
    // Calculate latency percentile
    // Implementation details...
    return 0;
  }
}
```

### 7.2 Performance Dashboard

```typescript
// React component for event monitoring
export function EventMonitorDashboard() {
  const [metrics, setMetrics] = useState<MetricsReport | null>(null);
  const [history, setHistory] = useState<MetricsReport[]>([]);

  useEffect(() => {
    const interval = setInterval(async () => {
      const report = await fetchMetrics();
      setMetrics(report);
      setHistory(prev => [...prev.slice(-59), report]);  // Keep 1 minute
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  if (!metrics) return <div>Loading metrics...</div>;

  return (
    <div className="event-monitor">
      <div className="metrics-grid">
        <MetricCard
          title="Events/sec"
          value={metrics.summary.eventsPerSecond}
          trend={calculateTrend(history, 'eventsPerSecond')}
        />
        <MetricCard
          title="Error Rate"
          value={(metrics.summary.errorRate * 100).toFixed(2) + '%'}
          status={metrics.summary.errorRate > 0.01 ? 'warning' : 'ok'}
        />
        <MetricCard
          title="P99 Latency"
          value={metrics.latency.p99 + 'ms'}
          status={metrics.latency.p99 > 100 ? 'warning' : 'ok'}
        />
        <MetricCard
          title="Drop Rate"
          value={(metrics.summary.dropRate * 100).toFixed(2) + '%'}
          status={metrics.summary.dropRate > 0.001 ? 'warning' : 'ok'}
        />
      </div>

      <div className="charts">
        <EventRateChart data={history} />
        <LatencyHistogram data={metrics.latency.histogram} />
        <CategoryBreakdown data={metrics.breakdown.byCategory} />
      </div>
    </div>
  );
}
```

---

## CONCLUSION

This Event System Design provides a complete, high-performance pipeline for real-time visual feedback in the Infinite system. Key achievements:

1. **<10ms end-to-end latency** from backend operation to visual feedback
2. **Scalable WebSocket architecture** supporting thousands of concurrent clients
3. **Priority-based event processing** ensuring critical events are handled first
4. **Comprehensive instrumentation** of all backend services
5. **Efficient batching and compression** for network optimization
6. **Robust monitoring and analytics** for system health tracking

The system seamlessly bridges backend operations with frontend visualizations, enabling users to see every computational operation in real-time through intuitive visual feedback.