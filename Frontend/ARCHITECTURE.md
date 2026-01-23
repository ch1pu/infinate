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

# Frontend Architecture
**3D Visualization & User Interface**

---

## OVERVIEW

The frontend provides an immersive 3D visualization of the spatial memory palace, allowing users to observe AI agents navigating through code and knowledge. Built with React, Three.js, and WebGPU, it delivers a simple 3D interface that makes AI context management intuitive and visual.

---

## 1. TECHNOLOGY STACK

### Core Technologies
- **React 18.2+** - Component framework with concurrent features
- **TypeScript 5.3+** - Type safety and better DX
- **Three.js + React Three Fiber** - 3D graphics and scene management
- **WebGPU/WebGL2** - Hardware-accelerated rendering
- **Zustand** - State management
- **Socket.io Client** - Real-time updates
- **Tailwind CSS** - UI styling
- **Vite** - Build tooling and HMR

### 3D Libraries
- **@react-three/fiber** - React renderer for Three.js
- **@react-three/drei** - Useful helpers and abstractions
- **@react-three/postprocessing** - Post-processing effects
- **three-stdlib** - Standard library of Three.js utilities
- **leva** - GUI controls for debugging

---

## 2. APPLICATION STRUCTURE

```
Frontend/
├── src/
│   ├── components/
│   │   ├── World/              # 3D world components
│   │   │   ├── MemoryPalace.tsx
│   │   │   ├── Agent.tsx
│   │   │   ├── MemoryChunk.tsx
│   │   │   ├── ViewFrustum.tsx
│   │   │   └── NavigationGrid.tsx
│   │   ├── UI/                  # 2D interface components
│   │   │   ├── HUD.tsx
│   │   │   ├── ContextMeter.tsx
│   │   │   ├── AgentPanel.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   └── MiniMap.tsx
│   │   ├── Controls/            # User input handling
│   │   │   ├── CameraControls.tsx
│   │   │   ├── KeyboardControls.tsx
│   │   │   └── MouseControls.tsx
│   │   └── Effects/             # Visual effects
│   │       ├── PostProcessing.tsx
│   │       ├── Lighting.tsx
│   │       └── Particles.tsx
│   ├── hooks/                   # Custom React hooks
│   │   ├── useWebSocket.ts
│   │   ├── useAgents.ts
│   │   ├── useSpatialIndex.ts
│   │   └── usePerformance.ts
│   ├── stores/                  # Zustand stores
│   │   ├── worldStore.ts
│   │   ├── agentStore.ts
│   │   ├── contextStore.ts
│   │   └── uiStore.ts
│   ├── utils/                   # Utility functions
│   │   ├── octree.ts
│   │   ├── frustumCulling.ts
│   │   ├── levelOfDetail.ts
│   │   └── webgpu.ts
│   ├── workers/                 # Web Workers
│   │   ├── spatial.worker.ts
│   │   ├── physics.worker.ts
│   │   └── streaming.worker.ts
│   ├── shaders/                 # Custom shaders
│   │   ├── voxel.vert
│   │   ├── voxel.frag
│   │   └── outline.glsl
│   ├── types/                   # TypeScript types
│   │   ├── world.ts
│   │   ├── agent.ts
│   │   └── api.ts
│   └── App.tsx                  # Root component
```

---

## 3. COMPONENT ARCHITECTURE

### 3.1 Core Components

**App.tsx - Root Component:**
```typescript
import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { Stats, Loader } from '@react-three/drei';
import { EffectComposer } from '@react-three/postprocessing';
import { MemoryPalace } from './components/World/MemoryPalace';
import { HUD } from './components/UI/HUD';
import { CameraControls } from './components/Controls/CameraControls';
import { useWebSocket } from './hooks/useWebSocket';
import { usePerformanceMonitor } from './hooks/usePerformance';

export default function App() {
  const { connected } = useWebSocket();
  const performance = usePerformanceMonitor();

  return (
    <div className="w-full h-screen relative">
      <Canvas
        camera={{ position: [0, 50, 100], fov: 60 }}
        gl={{
          antialias: true,
          powerPreference: 'high-performance',
          alpha: false,
          stencil: false,
        }}
        dpr={[1, 2]}
        performance={{ min: 0.5, max: 1 }}
      >
        <Suspense fallback={null}>
          {/* Lighting */}
          <ambientLight intensity={0.4} />
          <directionalLight position={[100, 100, 50]} intensity={0.6} />

          {/* 3D World */}
          <MemoryPalace />

          {/* Camera */}
          <CameraControls />

          {/* Post-processing */}
          <EffectComposer>
            {/* Effects here */}
          </EffectComposer>
        </Suspense>

        {/* Performance stats in dev */}
        {process.env.NODE_ENV === 'development' && <Stats />}
      </Canvas>

      {/* 2D UI Overlay */}
      <HUD connected={connected} fps={performance.fps} />

      {/* Loading indicator */}
      <Loader />
    </div>
  );
}
```

### 3.2 3D World Components

**MemoryPalace.tsx - Main 3D World:**
```typescript
import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { InstancedMesh, Vector3 } from 'three';
import { useWorldStore } from '../../stores/worldStore';
import { useFrustumCulling } from '../../hooks/useFrustumCulling';
import { VoxelChunk } from './VoxelChunk';
import { Agent } from './Agent';

export function MemoryPalace() {
  const { chunks, agents, updateVisibility } = useWorldStore();
  const visibleChunks = useFrustumCulling(chunks);

  // Level of Detail (LOD) system
  const lodChunks = useMemo(() => {
    return visibleChunks.map(chunk => ({
      ...chunk,
      lod: calculateLOD(chunk.position, cameraPosition)
    }));
  }, [visibleChunks, cameraPosition]);

  // Update visibility every frame
  useFrame((state) => {
    updateVisibility(state.camera);
  });

  return (
    <group name="memory-palace">
      {/* Render memory chunks as voxel buildings */}
      {lodChunks.map(chunk => (
        <VoxelChunk
          key={chunk.id}
          chunk={chunk}
          lod={chunk.lod}
        />
      ))}

      {/* Render AI agents */}
      {agents.map(agent => (
        <Agent
          key={agent.id}
          agent={agent}
        />
      ))}

      {/* Grid floor */}
      <gridHelper args={[1000, 100, '#444', '#222']} />
    </group>
  );
}
```

**Agent.tsx - AI Agent Visualization:**
```typescript
import React, { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Mesh, ConeGeometry, Vector3 } from 'three';
import { Text, Trail, Sphere } from '@react-three/drei';
import { ViewFrustum } from './ViewFrustum';

interface AgentProps {
  agent: {
    id: string;
    model: string;
    position: Vector3;
    orientation: number;
    contextWindow: {
      current: number;
      max: number;
    };
    isActive: boolean;
  };
}

export function Agent({ agent }: AgentProps) {
  const meshRef = useRef<Mesh>(null);
  const [trail, setTrail] = useState<Vector3[]>([]);

  // Smooth movement animation
  useFrame((state, delta) => {
    if (meshRef.current) {
      // Lerp position for smooth movement
      meshRef.current.position.lerp(agent.position, delta * 5);

      // Rotate to face movement direction
      meshRef.current.rotation.y = agent.orientation;

      // Pulsing effect when active
      if (agent.isActive) {
        const scale = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.1;
        meshRef.current.scale.setScalar(scale);
      }
    }
  });

  return (
    <group position={agent.position}>
      {/* Agent body */}
      <mesh ref={meshRef}>
        <sphereGeometry args={[2, 16, 16]} />
        <meshStandardMaterial
          color={agent.isActive ? '#00ff88' : '#4488ff'}
          emissive={agent.isActive ? '#00ff88' : '#2244aa'}
          emissiveIntensity={0.2}
        />
      </mesh>

      {/* Model label */}
      <Text
        position={[0, 4, 0]}
        fontSize={1}
        color="white"
        anchorX="center"
        anchorY="bottom"
      >
        {agent.model}
      </Text>

      {/* Context meter */}
      <group position={[0, 3, 0]}>
        <mesh>
          <planeGeometry args={[4, 0.5]} />
          <meshBasicMaterial color="#222" />
        </mesh>
        <mesh position={[-2 + (agent.contextWindow.current / agent.contextWindow.max) * 2, 0, 0.01]}>
          <planeGeometry args={[(agent.contextWindow.current / agent.contextWindow.max) * 4, 0.5]} />
          <meshBasicMaterial color="#00ff88" />
        </mesh>
      </group>

      {/* View frustum cone */}
      <ViewFrustum
        fov={60}
        near={1}
        far={100}
        color={agent.isActive ? '#00ff8844' : '#4488ff44'}
      />

      {/* Movement trail */}
      <Trail
        width={1}
        length={20}
        color="#4488ff"
        attenuation={(t) => t * t}
      >
        <mesh>
          <sphereGeometry args={[0.5]} />
          <meshBasicMaterial />
        </mesh>
      </Trail>
    </group>
  );
}
```

### 3.3 UI Components

**HUD.tsx - Heads-Up Display:**
```typescript
import React from 'react';
import { ContextMeter } from './ContextMeter';
import { AgentPanel } from './AgentPanel';
import { SearchBar } from './SearchBar';
import { MiniMap } from './MiniMap';
import { useAgentStore } from '../../stores/agentStore';

interface HUDProps {
  connected: boolean;
  fps: number;
}

export function HUD({ connected, fps }: HUDProps) {
  const { activeAgent, agents } = useAgentStore();

  return (
    <>
      {/* Top bar */}
      <div className="absolute top-0 left-0 right-0 p-4 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-white text-sm">
            {connected ? 'Connected' : 'Disconnected'}
          </span>
          <span className="text-white text-sm">
            FPS: {fps}
          </span>
        </div>

        <SearchBar />

        <div className="text-white text-sm">
          Agents: {agents.length}
        </div>
      </div>

      {/* Left panel - Agent list */}
      <AgentPanel agents={agents} />

      {/* Bottom - Context meter */}
      {activeAgent && (
        <ContextMeter
          current={activeAgent.contextWindow.current}
          max={activeAgent.contextWindow.max}
          chunks={activeAgent.contextWindow.chunks}
        />
      )}

      {/* Bottom right - Minimap */}
      <MiniMap />
    </>
  );
}
```

**SearchBar.tsx - Semantic Search Interface:**
```typescript
import React, { useState, useCallback } from 'react';
import { useSpatialStore } from '../../stores/spatialStore';
import { useAgentStore } from '../../stores/agentStore';

export function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const { searchSemantic } = useSpatialStore();
  const { teleportAgent } = useAgentStore();

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const results = await searchSemantic(query);
      setResults(results);
    } finally {
      setLoading(false);
    }
  }, [query, searchSemantic]);

  const handleResultClick = useCallback((result) => {
    // Teleport active agent to result location
    teleportAgent(result.position);
    setResults([]);
    setQuery('');
  }, [teleportAgent]);

  return (
    <div className="relative">
      <div className="flex items-center bg-gray-900/80 backdrop-blur rounded-lg px-4 py-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search memory space..."
          className="bg-transparent text-white placeholder-gray-400 outline-none w-64"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="ml-2 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? '...' : 'Search'}
        </button>
      </div>

      {/* Search results dropdown */}
      {results.length > 0 && (
        <div className="absolute top-full mt-2 w-full bg-gray-900/95 backdrop-blur rounded-lg shadow-xl max-h-64 overflow-auto">
          {results.map((result, i) => (
            <button
              key={i}
              onClick={() => handleResultClick(result)}
              className="w-full text-left px-4 py-2 hover:bg-gray-800 text-white"
            >
              <div className="font-medium">{result.file}</div>
              <div className="text-sm text-gray-400">{result.snippet}</div>
              <div className="text-xs text-blue-400">
                Distance: {result.distance.toFixed(1)}m | Relevance: {(result.score * 100).toFixed(0)}%
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## 4. STATE MANAGEMENT

### 4.1 World Store (Zustand)

**stores/worldStore.ts:**
```typescript
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { Vector3, Camera } from 'three';

interface MemoryChunk {
  id: string;
  position: Vector3;
  size: number;
  type: string;
  content: string;
  tokens: number;
  lastAccessed: Date;
}

interface WorldState {
  chunks: MemoryChunk[];
  visibleChunks: Set<string>;
  octree: OctreeNode;

  // Actions
  loadChunks: (chunks: MemoryChunk[]) => void;
  updateVisibility: (camera: Camera) => void;
  addChunk: (chunk: MemoryChunk) => void;
  removeChunk: (id: string) => void;
  updateChunkPosition: (id: string, position: Vector3) => void;
}

export const useWorldStore = create<WorldState>()(
  subscribeWithSelector((set, get) => ({
    chunks: [],
    visibleChunks: new Set(),
    octree: createOctree(),

    loadChunks: (chunks) => {
      const octree = buildOctree(chunks);
      set({ chunks, octree });
    },

    updateVisibility: (camera) => {
      const frustum = new Frustum();
      frustum.setFromProjectionMatrix(camera.projectionMatrix);

      const visible = new Set<string>();
      const chunks = get().chunks;

      chunks.forEach(chunk => {
        if (frustum.containsPoint(chunk.position)) {
          visible.add(chunk.id);
        }
      });

      set({ visibleChunks: visible });
    },

    addChunk: (chunk) => {
      set(state => ({
        chunks: [...state.chunks, chunk],
        octree: insertIntoOctree(state.octree, chunk)
      }));
    },

    removeChunk: (id) => {
      set(state => ({
        chunks: state.chunks.filter(c => c.id !== id),
        octree: removeFromOctree(state.octree, id)
      }));
    },

    updateChunkPosition: (id, position) => {
      set(state => ({
        chunks: state.chunks.map(c =>
          c.id === id ? { ...c, position } : c
        )
      }));
    }
  }))
);
```

### 4.2 Agent Store

**stores/agentStore.ts:**
```typescript
import { create } from 'zustand';
import { Vector3 } from 'three';

interface Agent {
  id: string;
  model: string;
  position: Vector3;
  targetPosition: Vector3;
  orientation: number;
  speed: number;
  contextWindow: {
    current: number;
    max: number;
    chunks: string[];
  };
  isActive: boolean;
  path: Vector3[];
}

interface AgentState {
  agents: Agent[];
  activeAgent: Agent | null;

  // Actions
  addAgent: (agent: Agent) => void;
  removeAgent: (id: string) => void;
  updateAgentPosition: (id: string, position: Vector3) => void;
  setActiveAgent: (id: string) => void;
  teleportAgent: (position: Vector3) => void;
  updateContextWindow: (id: string, context: Partial<Agent['contextWindow']>) => void;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: [],
  activeAgent: null,

  addAgent: (agent) => {
    set(state => ({
      agents: [...state.agents, agent],
      activeAgent: state.activeAgent || agent
    }));
  },

  removeAgent: (id) => {
    set(state => ({
      agents: state.agents.filter(a => a.id !== id),
      activeAgent: state.activeAgent?.id === id ? null : state.activeAgent
    }));
  },

  updateAgentPosition: (id, position) => {
    set(state => ({
      agents: state.agents.map(a =>
        a.id === id ? { ...a, position, targetPosition: position } : a
      )
    }));
  },

  setActiveAgent: (id) => {
    const agent = get().agents.find(a => a.id === id);
    set({ activeAgent: agent || null });
  },

  teleportAgent: (position) => {
    const activeAgent = get().activeAgent;
    if (activeAgent) {
      set(state => ({
        agents: state.agents.map(a =>
          a.id === activeAgent.id
            ? { ...a, position, targetPosition: position }
            : a
        )
      }));
    }
  },

  updateContextWindow: (id, context) => {
    set(state => ({
      agents: state.agents.map(a =>
        a.id === id
          ? { ...a, contextWindow: { ...a.contextWindow, ...context } }
          : a
      )
    }));
  }
}));
```

---

## 5. PERFORMANCE OPTIMIZATION

### 5.1 Level of Detail (LOD)

```typescript
// utils/levelOfDetail.ts
export class LODSystem {
  private levels = [
    { distance: 50, detail: 'high' },
    { distance: 100, detail: 'medium' },
    { distance: 200, detail: 'low' },
    { distance: Infinity, detail: 'billboard' }
  ];

  calculateLOD(objectPosition: Vector3, cameraPosition: Vector3): string {
    const distance = objectPosition.distanceTo(cameraPosition);

    for (const level of this.levels) {
      if (distance <= level.distance) {
        return level.detail;
      }
    }

    return 'billboard';
  }

  getGeometryForLOD(lod: string, baseGeometry: BufferGeometry): BufferGeometry {
    switch (lod) {
      case 'high':
        return baseGeometry;
      case 'medium':
        return this.simplifyGeometry(baseGeometry, 0.5);
      case 'low':
        return this.simplifyGeometry(baseGeometry, 0.25);
      case 'billboard':
        return new PlaneGeometry(1, 1);
      default:
        return baseGeometry;
    }
  }

  private simplifyGeometry(geometry: BufferGeometry, ratio: number): BufferGeometry {
    // Implement geometry simplification
    // Using three-mesh-simplifier or custom algorithm
    return geometry;
  }
}
```

### 5.2 Frustum Culling

```typescript
// hooks/useFrustumCulling.ts
import { useMemo } from 'react';
import { useThree } from '@react-three/fiber';
import { Frustum, Matrix4 } from 'three';

export function useFrustumCulling(objects: any[]) {
  const { camera } = useThree();

  return useMemo(() => {
    const frustum = new Frustum();
    const matrix = new Matrix4().multiplyMatrices(
      camera.projectionMatrix,
      camera.matrixWorldInverse
    );
    frustum.setFromProjectionMatrix(matrix);

    return objects.filter(obj => {
      // Check if object's bounding sphere intersects frustum
      return frustum.intersectsSphere(obj.boundingSphere);
    });
  }, [objects, camera]);
}
```

### 5.3 Web Workers

**workers/spatial.worker.ts:**
```typescript
// Offload spatial calculations to worker
self.addEventListener('message', (event) => {
  const { type, data } = event.data;

  switch (type) {
    case 'BUILD_OCTREE':
      const octree = buildOctree(data.chunks);
      self.postMessage({ type: 'OCTREE_BUILT', data: octree });
      break;

    case 'QUERY_FRUSTUM':
      const visible = queryFrustum(data.frustum, data.octree);
      self.postMessage({ type: 'FRUSTUM_RESULT', data: visible });
      break;

    case 'FIND_NEAREST':
      const nearest = findNearest(data.position, data.octree, data.count);
      self.postMessage({ type: 'NEAREST_RESULT', data: nearest });
      break;
  }
});

function buildOctree(chunks: any[]) {
  // Octree construction logic
  return octree;
}

function queryFrustum(frustum: any, octree: any) {
  // Frustum culling logic
  return visibleNodes;
}

function findNearest(position: any, octree: any, count: number) {
  // K-nearest neighbor search
  return nearestNodes;
}
```

---

## 6. RENDERING PIPELINE

### 6.1 WebGPU Support

```typescript
// utils/webgpu.ts
export async function initWebGPU(): Promise<GPUDevice | null> {
  if (!navigator.gpu) {
    console.warn('WebGPU not supported, falling back to WebGL2');
    return null;
  }

  const adapter = await navigator.gpu.requestAdapter({
    powerPreference: 'high-performance',
  });

  if (!adapter) {
    console.warn('No WebGPU adapter found');
    return null;
  }

  const device = await adapter.requestDevice({
    requiredFeatures: ['texture-compression-etc2'],
    requiredLimits: {
      maxTextureDimension2D: 8192,
      maxBufferSize: 268435456, // 256MB
    },
  });

  return device;
}
```

### 6.2 Custom Shaders

**shaders/voxel.vert:**
```glsl
attribute vec3 position;
attribute vec3 normal;
attribute vec2 uv;
attribute float ao;

uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;
uniform vec3 cameraPosition;

varying vec3 vNormal;
varying vec2 vUv;
varying float vAO;
varying float vDistance;

void main() {
  vec4 worldPosition = modelMatrix * vec4(position, 1.0);
  vec4 viewPosition = viewMatrix * worldPosition;

  vNormal = normalize(normalMatrix * normal);
  vUv = uv;
  vAO = ao;
  vDistance = length(cameraPosition - worldPosition.xyz);

  gl_Position = projectionMatrix * viewPosition;
}
```

**shaders/voxel.frag:**
```glsl
precision highp float;

uniform vec3 color;
uniform float opacity;
uniform sampler2D map;
uniform vec3 fogColor;
uniform float fogNear;
uniform float fogFar;

varying vec3 vNormal;
varying vec2 vUv;
varying float vAO;
varying float vDistance;

void main() {
  vec4 texColor = texture2D(map, vUv);
  vec3 finalColor = texColor.rgb * color;

  // Apply ambient occlusion
  finalColor *= vAO;

  // Simple lighting
  vec3 light = normalize(vec3(0.5, 1.0, 0.3));
  float diffuse = max(dot(vNormal, light), 0.0);
  finalColor *= (0.6 + 0.4 * diffuse);

  // Apply fog
  float fogFactor = smoothstep(fogNear, fogFar, vDistance);
  finalColor = mix(finalColor, fogColor, fogFactor);

  gl_FragColor = vec4(finalColor, opacity * texColor.a);
}
```

---

## 7. BUILD & DEPLOYMENT

### 7.1 Vite Configuration

**vite.config.ts:**
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { compression } from 'vite-plugin-compression2';
import glsl from 'vite-plugin-glsl';

export default defineConfig({
  plugins: [
    react(),
    glsl(),
    compression({
      algorithm: 'gzip',
      exclude: [/\.(br)$/],
    }),
    compression({
      algorithm: 'brotliCompress',
      exclude: [/\.(gz)$/],
    }),
  ],
  build: {
    target: 'esnext',
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          'three': ['three'],
          'react-three': ['@react-three/fiber', '@react-three/drei'],
          'vendor': ['react', 'react-dom', 'zustand'],
        },
      },
    },
  },
  optimizeDeps: {
    exclude: ['three'],
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:4000',
      '/ws': {
        target: 'ws://localhost:4000',
        ws: true,
      },
    },
  },
});
```

### 7.2 Performance Monitoring

```typescript
// hooks/usePerformance.ts
import { useEffect, useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';

export function usePerformanceMonitor() {
  const [fps, setFps] = useState(60);
  const [drawCalls, setDrawCalls] = useState(0);
  const [triangles, setTriangles] = useState(0);
  const frameCount = useRef(0);
  const lastTime = useRef(performance.now());

  useFrame((state) => {
    frameCount.current++;

    const now = performance.now();
    const delta = now - lastTime.current;

    if (delta >= 1000) {
      setFps(Math.round((frameCount.current * 1000) / delta));
      frameCount.current = 0;
      lastTime.current = now;

      // Get renderer stats
      const info = state.gl.info;
      setDrawCalls(info.render.calls);
      setTriangles(info.render.triangles);
    }
  });

  return { fps, drawCalls, triangles };
}
```

---

## CONCLUSION

This frontend architecture provides:
- **Immersive 3D visualization** of AI memory space
- **Real-time updates** via WebSocket
- **Optimized rendering** with LOD, frustum culling, and WebGPU
- **Intuitive controls** for navigation and interaction
- **Performance monitoring** and optimization
- **Modular component structure** for maintainability

The simple 3D interface makes the complex spatial context system approachable and understandable for developers.