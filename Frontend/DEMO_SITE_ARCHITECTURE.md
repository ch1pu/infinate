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

# Infinite Demo Site Architecture

**Project:** infinite.alphadeploy.org Interactive 3D Demo
**Owner:** Adolfo Lopez (ch1pu) - United States Navy Veteran
**Company:** Alpha Deploy LLC
**Domain:** infinite.alphadeploy.org
**Deployment:** Docker + Cloudflare Tunnel (home server)
**Last Updated:** December 2, 2025

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Overview](#2-project-overview)
3. [Technology Stack](#3-technology-stack)
4. [System Architecture](#4-system-architecture)
5. [Directory Structure](#5-directory-structure)
6. [Component Architecture](#6-component-architecture)
7. [Three.js Scene Architecture](#7-threejs-scene-architecture)
8. [State Management](#8-state-management)
9. [API Integration](#9-api-integration)
10. [Performance Optimization](#10-performance-optimization)
11. [User Experience Design](#11-user-experience-design)
12. [Deployment Strategy](#12-deployment-strategy)
13. [Build Checklist](#13-build-checklist)
14. [Testing Strategy](#14-testing-strategy)

---

## 1. Executive Summary

### Purpose

Create an interactive 3D demonstration site that:
- Provides live proof of O(k) spatial attention complexity
- Enables investors/buyers to experience Infinite firsthand
- Differentiates Alpha Deploy from all competitors (nobody has 3D spatial AI demo)
- Converts enterprise inquiries through hands-on experience
- Creates "wow factor" for licensing negotiations

### Key Outcomes

| Metric | Target |
|--------|--------|
| **Render Performance** | 60 FPS stable |
| **Initial Load** | < 3 seconds |
| **API Response** | < 500ms |
| **Demo Session** | 5-minute guided walkthrough |
| **Conversion Goal** | Demo request after experience |
| **Monthly Cost** | ~$10 (electricity) |

### Target Audiences

1. **Enterprise Buyers** - Anthropic, OpenAI, Google DeepMind executives
2. **Grant Evaluators** - Technical reviewers wanting proof
3. **Venture Capitalists** - AI-focused investors
4. **Technical Partners** - Research collaborators
5. **Press/Media** - Tech journalists seeking demo access

### Timeline

**Prerequisite:** Infinite M1.6 (Vector Store) and M1.7 (Integration Testing) complete

**Estimated:** January 2026 deployment

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Scene Setup | 2-3 days | Basic 3D world rendering |
| Token Visualization | 2-3 days | Spatial tokens in 3D |
| Interaction System | 2-3 days | Click-to-place, camera controls |
| API Integration | 2-3 days | Backend communication |
| Tutorial System | 1-2 days | Guided walkthrough |
| Polish & Optimization | 2-3 days | 60 FPS, mobile support |
| **Total** | **12-17 days** | **Production demo** |

---

## 2. Project Overview

### Goals

**Primary Goals:**
- Live, interactive proof of O(k) spatial attention
- Hands-on experience for non-technical stakeholders
- Visual demonstration of 3D spatial memory
- Real-time performance metrics display

**Secondary Goals:**
- Educational content about spatial AI
- Lead generation for enterprise licensing
- Technical validation for due diligence
- Press/media demo resource

### What Makes This Demo Unique

**Industry First:**
- No other AI company has a 3D interactive demo
- Visual proof of theoretical claims
- Investors can verify O(k) complexity themselves
- simple 3D interface makes AI intuitive

**Technical Differentiators:**
- Real spatial attention running (not simulation)
- Live vector store queries
- Actual token placement in 3D coordinates
- Real-time complexity metrics

### Success Metrics

**Technical Success:**
- Maintain 60 FPS with 10,000 tokens visible
- API responses < 500ms
- Zero crashes in 24-hour uptime test
- Works on mobile and desktop

**Business Success:**
- 100% of demo sessions complete tutorial
- 10+ enterprise demo requests per month
- Featured in 2+ tech publications
- Used in all licensing negotiations

---

## 3. Technology Stack

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.2+ | Component framework |
| **TypeScript** | 5.3+ | Type safety |
| **Vite** | 5.0+ | Build tool, HMR |
| **Three.js** | 0.160+ | 3D rendering engine |
| **React Three Fiber** | 8.15+ | React renderer for Three.js |
| **@react-three/drei** | 9.0+ | Three.js helpers |
| **@react-three/postprocessing** | 2.15+ | Visual effects |
| **Zustand** | 4.4+ | State management |
| **Socket.io Client** | 4.7+ | Real-time communication |
| **Tailwind CSS** | 3.4+ | UI styling |

### Backend Technologies (Already Planned)

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11 | Spatial engine |
| **FastAPI** | 0.100+ | REST API |
| **PyTorch** | 2.0+ | Spatial attention |
| **PostgreSQL + pgvector** | 15 | Vector database |
| **Qdrant** | Latest | High-performance vectors |
| **Redis** | 7 | Caching, sessions |

### Infrastructure

| Service | Purpose |
|---------|---------|
| **Docker Compose** | Container orchestration |
| **Nginx** | Reverse proxy |
| **Cloudflare Tunnel** | Public access |
| **WSL2 Ubuntu** | Host environment |

### Why This Stack?

**React Three Fiber:**
- Declarative 3D with React
- Excellent performance
- Large ecosystem
- Easy state management integration

**Zustand over Redux:**
- Simpler API for 3D apps
- Better performance for frequent updates
- Smaller bundle size
- No boilerplate

**Vite:**
- Fastest development experience
- Native ESM support
- Excellent Three.js integration
- Optimal production builds

---

## 4. System Architecture

### High-Level Architecture

```
                                    INTERNET
                                       |
                                       v
                         +---------------------------+
                         |    Cloudflare Tunnel      |
                         |    (infinite.alphadeploy.org)
                         +---------------------------+
                                       |
                                       v
                         +---------------------------+
                         |    Nginx Reverse Proxy    |
                         |    (Port 80)              |
                         +---------------------------+
                                       |
                    +------------------+------------------+
                    |                                     |
                    v                                     v
         +------------------+                  +------------------+
         |    Frontend      |                  |    Backend       |
         |    (React +      | <--- REST/WS --> |    (FastAPI)     |
         |    Three.js)     |                  +------------------+
         |    Port 5173     |                           |
         +------------------+              +-----------+-----------+
                                           |           |           |
                                           v           v           v
                                     +--------+ +--------+ +--------+
                                     |Postgres| | Qdrant | | Redis  |
                                     |pgvector| |        | |        |
                                     +--------+ +--------+ +--------+
```

### Data Flow

```
User Interaction (Click/Place Token)
         |
         v
React Component (TokenPlacer)
         |
         v
Zustand Store (tokenStore.addToken)
         |
         v
API Client (POST /api/tokens)
         |
         v
FastAPI Backend
         |
    +----+----+
    |         |
    v         v
pgvector   Qdrant
(index)    (search)
    |         |
    +----+----+
         |
         v
Spatial Engine (attention calculation)
         |
         v
WebSocket Broadcast (to all clients)
         |
         v
React State Update
         |
         v
Three.js Re-render
```

### Component Communication

```
                    +-------------------+
                    |      App.tsx      |
                    +-------------------+
                           |
          +----------------+----------------+
          |                                 |
          v                                 v
+------------------+              +------------------+
|  Canvas (3D)     |              |   UI Overlay     |
+------------------+              +------------------+
         |                                 |
    +----+----+                      +-----+-----+
    |         |                      |           |
    v         v                      v           v
+-------+ +-------+             +-------+   +-------+
| Scene | | Camera|             | HUD   |   | Panel |
+-------+ +-------+             +-------+   +-------+
    |
    +---+---+---+---+
    |   |   |   |
    v   v   v   v
Tokens Grid Lights Effects
```

---

## 5. Directory Structure

```
frontend/
|
|-- src/
|   |
|   |-- main.tsx                    # Entry point
|   |-- App.tsx                     # Root component
|   |-- vite-env.d.ts               # Vite types
|   |
|   |-- components/
|   |   |
|   |   |-- three/                  # 3D Components
|   |   |   |-- Scene.tsx           # Main 3D scene container
|   |   |   |-- SpatialWorld.tsx    # World with tokens
|   |   |   |-- TokenMesh.tsx       # Individual token visualization
|   |   |   |-- TokenCluster.tsx    # Grouped tokens (instancing)
|   |   |   |-- AttentionBeam.tsx   # Visualize attention connections
|   |   |   |-- SpatialGrid.tsx     # 3D coordinate grid
|   |   |   |-- ViewFrustum.tsx     # Attention range visualization
|   |   |   |-- CameraControls.tsx  # Orbit/fly camera
|   |   |   |-- Lighting.tsx        # Scene lighting
|   |   |   |-- Effects.tsx         # Post-processing
|   |   |   |-- Skybox.tsx          # Background environment
|   |   |   |-- TokenPlacer.tsx     # Click-to-place handler
|   |   |   |-- ParticleSystem.tsx  # Ambient particles
|   |   |   |-- SelectionBox.tsx    # Multi-select tokens
|   |   |   |-- NavigationPath.tsx  # Show query path
|   |   |   |-- HoverInfo.tsx       # 3D tooltip on hover
|   |   |   |-- PerformanceStats.tsx # FPS counter in 3D
|   |   |
|   |   |-- ui/                     # 2D UI Components
|   |   |   |-- HUD.tsx             # Heads-up display container
|   |   |   |-- MetricsPanel.tsx    # O(k) complexity metrics
|   |   |   |-- TokenCounter.tsx    # Total tokens display
|   |   |   |-- PerformanceGauge.tsx # Real-time FPS/latency
|   |   |   |-- QueryInput.tsx      # Natural language query
|   |   |   |-- ResultsPanel.tsx    # Query results display
|   |   |   |-- ControlPanel.tsx    # Demo controls
|   |   |   |-- TutorialOverlay.tsx # Guided walkthrough
|   |   |   |-- TutorialStep.tsx    # Individual tutorial step
|   |   |   |-- WelcomeModal.tsx    # First-time visitor modal
|   |   |   |-- MiniMap.tsx         # Top-down navigation
|   |   |   |-- ComplexityChart.tsx # O(k) vs O(n^2) comparison
|   |   |   |-- LoadingScreen.tsx   # Initial load animation
|   |   |   |-- ErrorBoundary.tsx   # Error handling UI
|   |   |   |-- InfoTooltip.tsx     # Educational tooltips
|   |   |   |-- Button.tsx          # Styled button
|   |   |   |-- Card.tsx            # Info card
|   |   |   |-- Badge.tsx           # Status badges
|   |   |
|   |   |-- layout/                 # Layout Components
|   |       |-- MainLayout.tsx      # Full-page layout
|   |       |-- SplitView.tsx       # 3D + panel layout
|   |       |-- FullscreenMode.tsx  # Immersive mode
|   |
|   |-- stores/                     # Zustand State
|   |   |-- tokenStore.ts           # Token state management
|   |   |-- cameraStore.ts          # Camera position/orientation
|   |   |-- queryStore.ts           # Query state and results
|   |   |-- tutorialStore.ts        # Tutorial progress
|   |   |-- settingsStore.ts        # User preferences
|   |   |-- performanceStore.ts     # Performance metrics
|   |   |-- connectionStore.ts      # WebSocket state
|   |
|   |-- hooks/                      # Custom Hooks
|   |   |-- useWebSocket.ts         # WebSocket connection
|   |   |-- useTokens.ts            # Token CRUD operations
|   |   |-- useQuery.ts             # Semantic query operations
|   |   |-- usePerformance.ts       # FPS monitoring
|   |   |-- useFrustumCulling.ts    # Visibility optimization
|   |   |-- useKeyboard.ts          # Keyboard shortcuts
|   |   |-- useWindowSize.ts        # Responsive handling
|   |   |-- useTutorial.ts          # Tutorial navigation
|   |   |-- useAPI.ts               # API client hook
|   |
|   |-- services/                   # API Services
|   |   |-- api.ts                  # Base API client
|   |   |-- tokenService.ts         # Token API endpoints
|   |   |-- queryService.ts         # Query API endpoints
|   |   |-- metricsService.ts       # Metrics API endpoints
|   |   |-- websocket.ts            # WebSocket service
|   |
|   |-- types/                      # TypeScript Types
|   |   |-- token.ts                # Token interfaces
|   |   |-- query.ts                # Query interfaces
|   |   |-- scene.ts                # Three.js types
|   |   |-- api.ts                  # API response types
|   |   |-- metrics.ts              # Performance metrics types
|   |
|   |-- utils/                      # Utility Functions
|   |   |-- spatial.ts              # 3D math utilities
|   |   |-- colors.ts               # Color schemes
|   |   |-- formatting.ts           # Number/text formatting
|   |   |-- validation.ts           # Input validation
|   |   |-- constants.ts            # App constants
|   |
|   |-- shaders/                    # Custom Shaders
|   |   |-- token.vert              # Token vertex shader
|   |   |-- token.frag              # Token fragment shader
|   |   |-- attention.glsl          # Attention beam shader
|   |   |-- grid.glsl               # Grid shader
|   |
|   |-- assets/                     # Static Assets
|   |   |-- textures/               # 3D textures
|   |   |-- models/                 # 3D models (if any)
|   |   |-- icons/                  # UI icons
|   |   |-- fonts/                  # Custom fonts
|   |
|   |-- styles/                     # CSS
|       |-- index.css               # Tailwind imports
|       |-- animations.css          # Custom animations
|       |-- three-overrides.css     # Three.js canvas styles
|
|-- public/
|   |-- favicon.ico
|   |-- og-image.png
|   |-- robots.txt
|
|-- index.html
|-- vite.config.ts
|-- tsconfig.json
|-- tsconfig.node.json
|-- tailwind.config.js
|-- postcss.config.js
|-- package.json
|-- Dockerfile.dev
|-- Dockerfile.prod
|-- .env.example
|-- .gitignore
```

---

## 6. Component Architecture

### 6.1 Component Hierarchy

```
App.tsx
|
+-- ErrorBoundary
|   |
|   +-- MainLayout
|       |
|       +-- LoadingScreen (conditional)
|       |
|       +-- WelcomeModal (first visit)
|       |
|       +-- Canvas (React Three Fiber)
|       |   |
|       |   +-- Scene
|       |       |
|       |       +-- Lighting
|       |       +-- Skybox
|       |       +-- SpatialGrid
|       |       +-- CameraControls
|       |       +-- TokenPlacer
|       |       |
|       |       +-- SpatialWorld
|       |       |   |
|       |       |   +-- TokenCluster (instanced)
|       |       |   +-- AttentionBeam (multiple)
|       |       |   +-- ViewFrustum
|       |       |   +-- NavigationPath
|       |       |   +-- HoverInfo
|       |       |
|       |       +-- ParticleSystem
|       |       +-- Effects
|       |       +-- PerformanceStats
|       |
|       +-- HUD
|           |
|           +-- MetricsPanel
|           +-- TokenCounter
|           +-- PerformanceGauge
|           +-- QueryInput
|           +-- ResultsPanel
|           +-- ControlPanel
|           +-- MiniMap
|           +-- ComplexityChart
|           +-- TutorialOverlay
```

### 6.2 Core 3D Components

#### Scene.tsx
**Purpose:** Main 3D scene container

**Responsibilities:**
- Initialize Three.js scene
- Manage scene-level state
- Coordinate child components
- Handle window resize

**Props:**
```typescript
interface SceneProps {
  showGrid: boolean;
  showStats: boolean;
  quality: 'low' | 'medium' | 'high';
}
```

**Implementation Pattern:**
```typescript
import { Canvas } from '@react-three/fiber';
import { Suspense } from 'react';

export function Scene({ showGrid, showStats, quality }: SceneProps) {
  return (
    <Canvas
      camera={{ position: [0, 50, 100], fov: 60 }}
      gl={{
        antialias: quality !== 'low',
        powerPreference: 'high-performance',
      }}
      dpr={quality === 'high' ? [1, 2] : [1, 1.5]}
    >
      <Suspense fallback={null}>
        <Lighting />
        <Skybox />
        {showGrid && <SpatialGrid />}
        <CameraControls />
        <TokenPlacer />
        <SpatialWorld />
        <ParticleSystem />
        <Effects quality={quality} />
        {showStats && <PerformanceStats />}
      </Suspense>
    </Canvas>
  );
}
```

#### TokenMesh.tsx
**Purpose:** Individual token visualization

**Responsibilities:**
- Render token as 3D object
- Color based on token type/relevance
- Show hover/selection states
- Animate when part of attention

**Props:**
```typescript
interface TokenMeshProps {
  token: SpatialToken;
  isSelected: boolean;
  isInAttention: boolean;
  onClick: () => void;
  onHover: (hovering: boolean) => void;
}
```

**Visual Design:**
- Shape: Rounded cube (voxel style)
- Size: 1 unit base, scales with embedding magnitude
- Colors: Based on token type (code=blue, text=green, etc.)
- Glow: When part of current attention
- Outline: When selected

#### TokenCluster.tsx
**Purpose:** Efficient rendering of many tokens via instancing

**Responsibilities:**
- Use InstancedMesh for performance
- Batch similar tokens
- Update instance matrices
- Handle culling

**Performance Target:** 10,000+ tokens at 60 FPS

**Implementation Pattern:**
```typescript
import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { InstancedMesh, Matrix4, Color } from 'three';

export function TokenCluster({ tokens }: { tokens: SpatialToken[] }) {
  const meshRef = useRef<InstancedMesh>(null);

  const [matrices, colors] = useMemo(() => {
    const m = new Array(tokens.length);
    const c = new Array(tokens.length);
    const tempMatrix = new Matrix4();

    tokens.forEach((token, i) => {
      tempMatrix.setPosition(token.position.x, token.position.y, token.position.z);
      m[i] = tempMatrix.clone();
      c[i] = getTokenColor(token.type);
    });

    return [m, c];
  }, [tokens]);

  useFrame(() => {
    if (meshRef.current) {
      tokens.forEach((token, i) => {
        meshRef.current!.setMatrixAt(i, matrices[i]);
        meshRef.current!.setColorAt(i, colors[i]);
      });
      meshRef.current.instanceMatrix.needsUpdate = true;
      if (meshRef.current.instanceColor) {
        meshRef.current.instanceColor.needsUpdate = true;
      }
    }
  });

  return (
    <instancedMesh ref={meshRef} args={[null, null, tokens.length]}>
      <boxGeometry args={[0.8, 0.8, 0.8]} />
      <meshStandardMaterial />
    </instancedMesh>
  );
}
```

#### AttentionBeam.tsx
**Purpose:** Visualize attention connections between tokens

**Responsibilities:**
- Draw lines/beams between tokens
- Color intensity = attention weight
- Animate during attention calculation
- Show query-to-result paths

**Visual Design:**
- Style: Glowing lines with particle trail
- Color: Gradient from query (gold) to result (cyan)
- Animation: Pulse along path during attention
- Width: Proportional to attention weight

#### ViewFrustum.tsx
**Purpose:** Show the spatial attention range

**Responsibilities:**
- Render semi-transparent cone/sphere
- Indicate k-nearest neighborhood
- Update as camera moves
- Show capacity (how many tokens in range)

**Visual Design:**
- Shape: Sphere centered on query point
- Radius: Based on k (nearest neighbors)
- Opacity: Gradient from center to edge
- Color: Light blue with cyan edges

### 6.3 Core UI Components

#### MetricsPanel.tsx
**Purpose:** Display O(k) complexity proof

**Responsibilities:**
- Show sequence size vs. computation time
- Compare O(k) vs O(n^2) curves
- Real-time update during demo
- Highlight efficiency gain

**Display Format:**
```
+------------------------------------------+
| O(k) COMPLEXITY VERIFICATION             |
+------------------------------------------+
| Sequence Size  | Expected O(n^2) | Actual |
|----------------|-----------------|--------|
| 1,000 tokens   | 1.0x baseline   | 1.0x   |
| 2,000 tokens   | 4.0x            | 2.52x  |
| 4,000 tokens   | 16.0x           | 10.05x |
+------------------------------------------+
| Efficiency Gain: 37% better than O(n^2)  |
+------------------------------------------+
```

#### QueryInput.tsx
**Purpose:** Natural language query interface

**Responsibilities:**
- Text input for queries
- Voice input (optional)
- Query suggestions
- Recent queries history
- Loading state during search

**User Flow:**
1. User types: "Find authentication code"
2. Submit triggers backend search
3. Results appear in ResultsPanel
4. Matching tokens highlighted in 3D

#### TutorialOverlay.tsx
**Purpose:** Guided walkthrough for new users

**Responsibilities:**
- Step-by-step tutorial
- Highlight relevant UI elements
- Progress indicator
- Skip/next controls
- Complete callback

**Tutorial Steps:**
1. Welcome to Infinite Spatial AI
2. Understanding 3D Token Space
3. Placing Your First Token
4. Running a Spatial Query
5. Observing O(k) Complexity
6. Try It Yourself

**Implementation:**
```typescript
const TUTORIAL_STEPS = [
  {
    id: 'welcome',
    title: 'Welcome to Infinite',
    content: 'Experience the world\'s first O(k) spatial attention system.',
    highlight: null,
    position: 'center',
  },
  {
    id: 'space',
    title: '3D Token Space',
    content: 'Tokens exist at 3D coordinates. Nearby tokens = related concepts.',
    highlight: 'canvas',
    position: 'right',
  },
  {
    id: 'place',
    title: 'Place a Token',
    content: 'Click anywhere in the 3D space to place a token.',
    highlight: 'canvas',
    position: 'right',
    action: 'click',
  },
  // ... more steps
];
```

#### ComplexityChart.tsx
**Purpose:** Visual comparison of O(k) vs O(n^2)

**Responsibilities:**
- Line chart comparing scaling
- Real-time data points
- Animated drawing
- Interactive hover for details

**Chart Data:**
```typescript
const chartData = {
  labels: ['1K', '2K', '4K', '8K', '16K', '32K'],
  datasets: [
    {
      label: 'O(n^2) Traditional',
      data: [1, 4, 16, 64, 256, 1024],
      color: '#ef4444', // Red
    },
    {
      label: 'O(k) Infinite',
      data: [1, 2.52, 10.05, 38.2, 145, 552],
      color: '#22c55e', // Green
    },
  ],
};
```

---

## 7. Three.js Scene Architecture

### 7.1 Scene Graph

```
Scene
|
+-- AmbientLight (intensity: 0.4)
|
+-- DirectionalLight (position: [50, 100, 50], intensity: 0.8)
|   +-- DirectionalLightHelper (debug mode only)
|
+-- Skybox (CubeTextureLoader with gradient)
|
+-- SpatialGrid
|   +-- GridHelper (1000x1000, divisions: 100)
|   +-- AxisHelper (debug mode only)
|
+-- TokensGroup
|   +-- InstancedMesh (tokens)
|   +-- AttentionBeams (Line2 with gradient)
|
+-- QueryVisualization
|   +-- QueryPoint (glowing sphere)
|   +-- ViewFrustum (transparent sphere)
|   +-- NavigationPath (animated line)
|
+-- ParticleSystem (Points, ambient particles)
|
+-- PostProcessing
    +-- EffectComposer
        +-- BloomPass
        +-- VignettePass
```

### 7.2 Camera System

**Camera Modes:**

1. **Orbit Mode (Default)**
   - Rotate around scene center
   - Zoom in/out
   - Pan horizontally
   - Best for overview

2. **Fly Mode**
   - WASD movement
   - Mouse look
   - Best for exploration

3. **Follow Mode**
   - Track query point
   - Smooth transitions
   - Best during queries

**Camera Controls Implementation:**
```typescript
import { OrbitControls, FlyControls, PerspectiveCamera } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';

export function CameraControls({ mode }: { mode: 'orbit' | 'fly' | 'follow' }) {
  const { target } = useCameraStore();

  return (
    <>
      <PerspectiveCamera makeDefault position={[0, 50, 100]} fov={60} />

      {mode === 'orbit' && (
        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          minDistance={10}
          maxDistance={500}
          maxPolarAngle={Math.PI / 2.1}
        />
      )}

      {mode === 'fly' && (
        <FlyControls
          movementSpeed={20}
          rollSpeed={0.5}
          dragToLook
        />
      )}
    </>
  );
}
```

### 7.3 Lighting Setup

**Three-Point Lighting:**

```typescript
export function Lighting() {
  return (
    <>
      {/* Key Light - Main directional */}
      <directionalLight
        position={[50, 100, 50]}
        intensity={0.8}
        castShadow
        shadow-mapSize={[2048, 2048]}
      />

      {/* Fill Light - Softer, from opposite */}
      <directionalLight
        position={[-30, 50, -30]}
        intensity={0.3}
      />

      {/* Ambient - Base illumination */}
      <ambientLight intensity={0.4} />

      {/* Hemisphere - Sky/ground gradient */}
      <hemisphereLight
        skyColor="#87ceeb"
        groundColor="#1a1a2e"
        intensity={0.3}
      />
    </>
  );
}
```

### 7.4 Post-Processing Effects

**Effects Pipeline:**

```typescript
import { EffectComposer, Bloom, Vignette, ChromaticAberration } from '@react-three/postprocessing';

export function Effects({ quality }: { quality: 'low' | 'medium' | 'high' }) {
  if (quality === 'low') return null;

  return (
    <EffectComposer>
      <Bloom
        luminanceThreshold={0.6}
        luminanceSmoothing={0.9}
        intensity={quality === 'high' ? 0.4 : 0.2}
      />

      <Vignette
        eskil={false}
        offset={0.1}
        darkness={0.5}
      />

      {quality === 'high' && (
        <ChromaticAberration
          offset={[0.002, 0.002]}
        />
      )}
    </EffectComposer>
  );
}
```

### 7.5 Token Visualization Design

**Token Appearance by Type:**

| Type | Color | Shape | Glow |
|------|-------|-------|------|
| Code | `#3b82f6` (Blue) | Cube | Low |
| Text | `#22c55e` (Green) | Rounded cube | Low |
| Query | `#eab308` (Gold) | Sphere | High |
| Result | `#06b6d4` (Cyan) | Cube | Medium |
| System | `#8b5cf6` (Purple) | Octahedron | Low |

**Token States:**

| State | Visual Change |
|-------|--------------|
| Default | Base color, no glow |
| Hovered | Brighten 20%, outline |
| Selected | Brighten 40%, thick outline |
| In Attention | Pulse animation, glow |
| Query Result | Connect with beam |

---

## 8. State Management

### 8.1 Store Architecture

**Zustand Stores:**

```
stores/
|-- tokenStore.ts      # Token data and operations
|-- cameraStore.ts     # Camera position and mode
|-- queryStore.ts      # Query state and results
|-- tutorialStore.ts   # Tutorial progress
|-- settingsStore.ts   # User preferences
|-- performanceStore.ts # Performance metrics
|-- connectionStore.ts # WebSocket state
```

### 8.2 Token Store

```typescript
// stores/tokenStore.ts
import { create } from 'zustand';
import { Vector3 } from 'three';

interface SpatialToken {
  id: string;
  content: string;
  type: 'code' | 'text' | 'query' | 'result' | 'system';
  position: { x: number; y: number; z: number };
  embedding: number[];
  createdAt: Date;
  metadata: Record<string, any>;
}

interface TokenState {
  tokens: SpatialToken[];
  selectedIds: Set<string>;
  hoveredId: string | null;
  attentionTokenIds: Set<string>;

  // Actions
  addToken: (token: SpatialToken) => void;
  removeToken: (id: string) => void;
  updatePosition: (id: string, position: Vector3) => void;
  selectToken: (id: string) => void;
  deselectToken: (id: string) => void;
  clearSelection: () => void;
  setHovered: (id: string | null) => void;
  setAttentionTokens: (ids: string[]) => void;
  loadTokens: (tokens: SpatialToken[]) => void;
  clearTokens: () => void;
}

export const useTokenStore = create<TokenState>((set, get) => ({
  tokens: [],
  selectedIds: new Set(),
  hoveredId: null,
  attentionTokenIds: new Set(),

  addToken: (token) => {
    set((state) => ({
      tokens: [...state.tokens, token],
    }));
  },

  removeToken: (id) => {
    set((state) => ({
      tokens: state.tokens.filter((t) => t.id !== id),
      selectedIds: new Set([...state.selectedIds].filter((i) => i !== id)),
    }));
  },

  updatePosition: (id, position) => {
    set((state) => ({
      tokens: state.tokens.map((t) =>
        t.id === id ? { ...t, position: { x: position.x, y: position.y, z: position.z } } : t
      ),
    }));
  },

  selectToken: (id) => {
    set((state) => ({
      selectedIds: new Set([...state.selectedIds, id]),
    }));
  },

  deselectToken: (id) => {
    set((state) => {
      const newSelected = new Set(state.selectedIds);
      newSelected.delete(id);
      return { selectedIds: newSelected };
    });
  },

  clearSelection: () => set({ selectedIds: new Set() }),

  setHovered: (id) => set({ hoveredId: id }),

  setAttentionTokens: (ids) => set({ attentionTokenIds: new Set(ids) }),

  loadTokens: (tokens) => set({ tokens }),

  clearTokens: () => set({ tokens: [], selectedIds: new Set(), attentionTokenIds: new Set() }),
}));
```

### 8.3 Query Store

```typescript
// stores/queryStore.ts
import { create } from 'zustand';

interface QueryResult {
  tokenId: string;
  distance: number;
  score: number;
}

interface QueryMetrics {
  queryTime: number;
  tokensSearched: number;
  tokensReturned: number;
  complexity: string; // 'O(k)' or 'O(n^2)'
}

interface QueryState {
  query: string;
  isLoading: boolean;
  results: QueryResult[];
  metrics: QueryMetrics | null;
  error: string | null;
  history: string[];

  // Actions
  setQuery: (query: string) => void;
  executeQuery: () => Promise<void>;
  clearResults: () => void;
  clearError: () => void;
}

export const useQueryStore = create<QueryState>((set, get) => ({
  query: '',
  isLoading: false,
  results: [],
  metrics: null,
  error: null,
  history: [],

  setQuery: (query) => set({ query }),

  executeQuery: async () => {
    const { query } = get();
    if (!query.trim()) return;

    set({ isLoading: true, error: null });

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, k: 50 }),
      });

      if (!response.ok) throw new Error('Query failed');

      const data = await response.json();

      set({
        results: data.results,
        metrics: data.metrics,
        isLoading: false,
        history: [...get().history.slice(-9), query],
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Unknown error',
        isLoading: false,
      });
    }
  },

  clearResults: () => set({ results: [], metrics: null }),

  clearError: () => set({ error: null }),
}));
```

### 8.4 Performance Store

```typescript
// stores/performanceStore.ts
import { create } from 'zustand';

interface PerformanceMetrics {
  fps: number;
  frameTime: number;
  drawCalls: number;
  triangles: number;
  visibleTokens: number;
  totalTokens: number;
  apiLatency: number;
  wsLatency: number;
}

interface ComplexityData {
  sequenceSize: number;
  expectedTime: number; // O(n^2)
  actualTime: number;   // O(k)
}

interface PerformanceState {
  metrics: PerformanceMetrics;
  complexityHistory: ComplexityData[];

  // Actions
  updateMetrics: (partial: Partial<PerformanceMetrics>) => void;
  addComplexityDataPoint: (data: ComplexityData) => void;
  resetComplexityHistory: () => void;
}

export const usePerformanceStore = create<PerformanceState>((set, get) => ({
  metrics: {
    fps: 60,
    frameTime: 16.67,
    drawCalls: 0,
    triangles: 0,
    visibleTokens: 0,
    totalTokens: 0,
    apiLatency: 0,
    wsLatency: 0,
  },
  complexityHistory: [],

  updateMetrics: (partial) => {
    set((state) => ({
      metrics: { ...state.metrics, ...partial },
    }));
  },

  addComplexityDataPoint: (data) => {
    set((state) => ({
      complexityHistory: [...state.complexityHistory.slice(-19), data],
    }));
  },

  resetComplexityHistory: () => set({ complexityHistory: [] }),
}));
```

---

## 9. API Integration

### 9.1 API Endpoints

**Backend Endpoints (FastAPI):**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/status` | Health check |
| GET | `/api/tokens` | List all tokens |
| POST | `/api/tokens` | Create token |
| DELETE | `/api/tokens/{id}` | Delete token |
| POST | `/api/query` | Semantic query |
| GET | `/api/metrics` | Performance metrics |
| WS | `/ws` | Real-time updates |

### 9.2 API Client

```typescript
// services/api.ts
const API_BASE = import.meta.env.VITE_API_URL || '/api';

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Token operations
  async getTokens(): Promise<SpatialToken[]> {
    return this.request('/tokens');
  }

  async createToken(data: CreateTokenRequest): Promise<SpatialToken> {
    return this.request('/tokens', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteToken(id: string): Promise<void> {
    await this.request(`/tokens/${id}`, { method: 'DELETE' });
  }

  // Query operations
  async query(queryText: string, k: number = 50): Promise<QueryResponse> {
    return this.request('/query', {
      method: 'POST',
      body: JSON.stringify({ query: queryText, k }),
    });
  }

  // Metrics
  async getMetrics(): Promise<MetricsResponse> {
    return this.request('/metrics');
  }
}

export const api = new APIClient(API_BASE);
```

### 9.3 WebSocket Integration

```typescript
// services/websocket.ts
import { io, Socket } from 'socket.io-client';
import { useTokenStore } from '../stores/tokenStore';
import { usePerformanceStore } from '../stores/performanceStore';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(url: string): void {
    this.socket = io(url, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    // Real-time token updates
    this.socket.on('token:created', (token: SpatialToken) => {
      useTokenStore.getState().addToken(token);
    });

    this.socket.on('token:deleted', (id: string) => {
      useTokenStore.getState().removeToken(id);
    });

    this.socket.on('token:updated', (token: SpatialToken) => {
      useTokenStore.getState().updatePosition(
        token.id,
        new Vector3(token.position.x, token.position.y, token.position.z)
      );
    });

    // Attention updates
    this.socket.on('attention:computed', (data: { tokenIds: string[], metrics: any }) => {
      useTokenStore.getState().setAttentionTokens(data.tokenIds);
      usePerformanceStore.getState().addComplexityDataPoint(data.metrics);
    });

    // Performance metrics
    this.socket.on('metrics:update', (metrics: Partial<PerformanceMetrics>) => {
      usePerformanceStore.getState().updateMetrics(metrics);
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  emit(event: string, data: any): void {
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }
}

export const wsService = new WebSocketService();
```

### 9.4 Custom Hooks

```typescript
// hooks/useTokens.ts
import { useEffect } from 'react';
import { useTokenStore } from '../stores/tokenStore';
import { api } from '../services/api';

export function useTokens() {
  const { tokens, addToken, removeToken, loadTokens } = useTokenStore();

  useEffect(() => {
    // Initial load
    api.getTokens().then(loadTokens).catch(console.error);
  }, [loadTokens]);

  const createToken = async (position: Vector3, content: string) => {
    const token = await api.createToken({
      content,
      position: { x: position.x, y: position.y, z: position.z },
    });
    addToken(token);
    return token;
  };

  const deleteToken = async (id: string) => {
    await api.deleteToken(id);
    removeToken(id);
  };

  return {
    tokens,
    createToken,
    deleteToken,
  };
}

// hooks/useQuery.ts
import { useCallback } from 'react';
import { useQueryStore } from '../stores/queryStore';
import { useTokenStore } from '../stores/tokenStore';

export function useQuery() {
  const { query, setQuery, executeQuery, results, metrics, isLoading, error } = useQueryStore();
  const { setAttentionTokens } = useTokenStore();

  const runQuery = useCallback(async () => {
    await executeQuery();
    const resultIds = useQueryStore.getState().results.map(r => r.tokenId);
    setAttentionTokens(resultIds);
  }, [executeQuery, setAttentionTokens]);

  return {
    query,
    setQuery,
    runQuery,
    results,
    metrics,
    isLoading,
    error,
  };
}
```

---

## 10. Performance Optimization

### 10.1 Rendering Optimization

**Instanced Rendering:**
- Use InstancedMesh for tokens
- Single draw call for all similar objects
- Update matrices in batch
- Target: 10,000+ tokens at 60 FPS

**Frustum Culling:**
- Only render visible tokens
- Use Three.js built-in frustum
- Spatial partitioning (Octree)
- Target: < 3000 visible at once

**Level of Detail (LOD):**
- Far tokens: Simple shapes
- Medium tokens: Standard cubes
- Near tokens: Detailed with effects
- Transition smoothly between levels

### 10.2 Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| FPS | 60 | 30 |
| Frame Time | 16.67ms | 33ms |
| Initial Load | < 3s | < 5s |
| API Response | < 500ms | < 1000ms |
| Token Count | 10,000+ | 5,000 |

### 10.3 Bundle Optimization

**Vite Configuration:**

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({ open: false, gzipSize: true }),
  ],
  build: {
    target: 'esnext',
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          'three': ['three'],
          'react-three': ['@react-three/fiber', '@react-three/drei', '@react-three/postprocessing'],
          'vendor': ['react', 'react-dom', 'zustand', 'socket.io-client'],
        },
      },
    },
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
  },
  optimizeDeps: {
    exclude: ['three'],
  },
});
```

**Code Splitting:**
- Lazy load tutorial components
- Lazy load settings panel
- Dynamic import for heavy effects
- Split Three.js into separate chunk

### 10.4 Memory Management

**Token Data:**
- Keep only visible tokens in GPU memory
- Stream tokens as camera moves
- Dispose of unused geometries
- Pool reusable objects

**WebSocket:**
- Throttle updates (max 30/sec)
- Batch small updates
- Compress payloads

---

## 11. User Experience Design

### 11.1 First-Time User Flow

```
1. Landing (0s)
   |
   +-- Loading Screen (0-3s)
       - Show progress
       - Preload 3D assets
       - Establish WebSocket
   |
   +-- Welcome Modal (3s)
       - Brief intro to Infinite
       - Option: Start Tutorial / Skip
   |
   +-- Tutorial (if chosen)
       |
       +-- Step 1: 3D Space Intro
       +-- Step 2: Token Placement
       +-- Step 3: Semantic Query
       +-- Step 4: O(k) Demonstration
       +-- Step 5: Free Exploration
   |
   +-- Main Demo
       - Full interactivity
       - Metrics visible
       - Help available
```

### 11.2 Control Scheme

**Mouse:**
| Action | Result |
|--------|--------|
| Left Click (empty) | Place token |
| Left Click (token) | Select token |
| Right Drag | Rotate camera |
| Scroll | Zoom in/out |
| Middle Drag | Pan camera |

**Keyboard:**
| Key | Action |
|-----|--------|
| W/A/S/D | Move camera (fly mode) |
| Space | Toggle fly mode |
| Enter | Execute query |
| Escape | Clear selection |
| H | Toggle HUD |
| G | Toggle grid |
| T | Start tutorial |
| ? | Help overlay |

### 11.3 Mobile Support

**Touch Controls:**
| Gesture | Action |
|---------|--------|
| Single tap | Select/place token |
| Two-finger drag | Rotate camera |
| Pinch | Zoom |
| Three-finger drag | Pan |

**Mobile Optimizations:**
- Reduce particle count
- Lower resolution
- Simplified effects
- Touch-friendly UI buttons
- Portrait and landscape support

### 11.4 Accessibility

**Visual:**
- High contrast mode option
- Colorblind-friendly palette
- Scalable UI elements
- Motion reduction option

**Input:**
- Full keyboard navigation
- Screen reader announcements for key events
- Clear focus indicators
- Sufficient touch target sizes

---

## 12. Deployment Strategy

### 12.1 Docker Configuration

**Frontend Dockerfile.prod:**

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Frontend nginx.conf:**

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_proxied any;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Cache static assets
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### 12.2 Environment Variables

**Frontend .env:**

```bash
# API Configuration
VITE_API_URL=/api
VITE_WS_URL=/ws

# Feature Flags
VITE_ENABLE_TUTORIAL=true
VITE_ENABLE_VOICE_INPUT=false
VITE_ENABLE_MOBILE=true

# Performance
VITE_MAX_TOKENS=10000
VITE_DEFAULT_QUALITY=medium

# Analytics (optional)
VITE_GA_ID=
```

### 12.3 Integration with Docker Compose

The frontend integrates with the full stack defined in `INFINITE_DOCKER_DEPLOYMENT_GUIDE.md`:

```yaml
# Part of docker-compose.yml
services:
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
```

---

## 13. Build Checklist

### Phase 1: Project Setup (Day 1)

- [ ] Initialize Vite project with React + TypeScript
- [ ] Install Three.js and React Three Fiber
- [ ] Install Zustand, Socket.io client
- [ ] Configure Tailwind CSS
- [ ] Set up directory structure
- [ ] Create base TypeScript types
- [ ] Configure ESLint and Prettier
- [ ] Create Dockerfile.dev and Dockerfile.prod

### Phase 2: Core 3D Scene (Days 2-3)

- [ ] Create Scene.tsx with Canvas setup
- [ ] Implement Lighting.tsx (three-point lighting)
- [ ] Create Skybox.tsx (gradient background)
- [ ] Implement SpatialGrid.tsx (coordinate grid)
- [ ] Create CameraControls.tsx (orbit mode first)
- [ ] Add basic post-processing (bloom, vignette)
- [ ] Verify 60 FPS baseline

### Phase 3: Token System (Days 4-5)

- [ ] Create tokenStore.ts (Zustand)
- [ ] Implement TokenMesh.tsx (single token)
- [ ] Create TokenCluster.tsx (instanced rendering)
- [ ] Implement TokenPlacer.tsx (click to place)
- [ ] Add token color scheme by type
- [ ] Implement hover and selection states
- [ ] Test with 1000+ tokens

### Phase 4: API Integration (Days 6-7)

- [ ] Create api.ts (REST client)
- [ ] Implement websocket.ts (Socket.io)
- [ ] Create useTokens.ts hook
- [ ] Create useQuery.ts hook
- [ ] Connect token creation to backend
- [ ] Connect query execution to backend
- [ ] Test full data flow

### Phase 5: Attention Visualization (Days 8-9)

- [ ] Create AttentionBeam.tsx (connection lines)
- [ ] Create ViewFrustum.tsx (attention range)
- [ ] Implement attention animation
- [ ] Connect to WebSocket attention events
- [ ] Add NavigationPath.tsx (query path)
- [ ] Verify visual clarity of attention

### Phase 6: UI Components (Days 10-11)

- [ ] Create HUD.tsx container
- [ ] Implement MetricsPanel.tsx
- [ ] Create QueryInput.tsx
- [ ] Implement ResultsPanel.tsx
- [ ] Create PerformanceGauge.tsx
- [ ] Implement ComplexityChart.tsx
- [ ] Create MiniMap.tsx

### Phase 7: Tutorial System (Day 12)

- [ ] Create tutorialStore.ts
- [ ] Implement TutorialOverlay.tsx
- [ ] Create TutorialStep.tsx
- [ ] Define all tutorial steps
- [ ] Add step highlighting
- [ ] Implement progress tracking
- [ ] Create WelcomeModal.tsx

### Phase 8: Polish & Optimization (Days 13-15)

- [ ] Implement fly camera mode
- [ ] Add keyboard shortcuts
- [ ] Optimize for mobile
- [ ] Performance tuning (target 60 FPS)
- [ ] Bundle optimization
- [ ] Cross-browser testing
- [ ] Error handling and boundaries
- [ ] Loading states and feedback

### Phase 9: Deployment (Days 16-17)

- [ ] Build production Docker image
- [ ] Test with docker-compose
- [ ] Verify Cloudflare Tunnel integration
- [ ] Performance testing under load
- [ ] Final bug fixes
- [ ] Documentation updates
- [ ] Launch to infinite.alphadeploy.org

---

## 14. Testing Strategy

### 14.1 Unit Tests

**Testing Stack:**
- Vitest (test runner)
- React Testing Library (component tests)
- MSW (API mocking)

**Test Coverage Targets:**
- Stores: 90%+
- Hooks: 80%+
- Utils: 95%+
- Components: 70%+

**Example Tests:**

```typescript
// stores/tokenStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useTokenStore } from './tokenStore';

describe('tokenStore', () => {
  beforeEach(() => {
    useTokenStore.setState({ tokens: [], selectedIds: new Set() });
  });

  it('adds a token', () => {
    const token = {
      id: '1',
      content: 'test',
      type: 'text',
      position: { x: 0, y: 0, z: 0 },
      embedding: [],
      createdAt: new Date(),
      metadata: {},
    };

    useTokenStore.getState().addToken(token);

    expect(useTokenStore.getState().tokens).toHaveLength(1);
    expect(useTokenStore.getState().tokens[0].id).toBe('1');
  });

  it('removes a token', () => {
    // ... test implementation
  });
});
```

### 14.2 Integration Tests

**Focus Areas:**
- API communication
- WebSocket events
- State synchronization
- Camera controls
- Token placement flow

### 14.3 E2E Tests

**Testing Stack:**
- Playwright

**Critical Paths:**
1. First-time user completes tutorial
2. User places token and sees it in 3D
3. User runs query and sees results
4. Complexity metrics update correctly

### 14.4 Performance Tests

**Benchmarks:**
- Initial load time
- Time to interactive
- FPS with 1K, 5K, 10K tokens
- Memory usage over time
- API response times

**Tools:**
- Lighthouse CI
- React DevTools Profiler
- Three.js stats panel

---

## Summary

### Key Deliverables

This architecture document provides:

1. **Complete technical specification** for the Infinite demo site
2. **Component hierarchy** with 50+ React components
3. **Three.js scene architecture** for 3D visualization
4. **State management** with Zustand stores
5. **API integration** with REST and WebSocket
6. **Performance optimization** strategies
7. **Tutorial system** for user onboarding
8. **Deployment configuration** for Docker

### Implementation Priorities

1. **Core 3D scene** - Foundation for everything
2. **Token visualization** - Main demo feature
3. **API integration** - Real backend data
4. **Attention visualization** - Prove O(k) complexity
5. **UI and metrics** - User feedback
6. **Tutorial** - Onboarding
7. **Polish** - Production-ready

### Success Criteria

- 60 FPS with 10,000 tokens
- < 3 second initial load
- Complete tutorial in 5 minutes
- Wow factor for investor demos
- Zero crashes in production

---

**Document Version:** 1.0
**Created:** December 2, 2025
**Author:** ch1pu (Adolfo Lopez)
**Status:** Ready for Implementation (after M1.6/M1.7)
