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

# INFINITE: Frontend Styling Strategy
**Visual Design System for 3D Spatial Context**

---

## EXECUTIVE SUMMARY

This document defines the comprehensive styling approach for Infinite's 3D interface, combining WebGPU shaders, CSS-in-JS, and dynamic theming to create a futuristic, performant, and accessible visual experience.

---

## 1. DESIGN PHILOSOPHY

### Core Principles

**1. Depth Through Light**
- Use lighting to create spatial hierarchy
- Shadows indicate proximity and importance
- Glowing elements draw attention

**2. Information Density**
- Maximum information without clutter
- Progressive disclosure based on zoom level
- Context-aware detail rendering

**3. Motion as Meaning**
- Smooth transitions convey relationships
- Particle effects indicate data flow
- Pulsing shows activity

**4. Semantic Color**
- Colors represent data types
- Gradients show relationships
- Opacity indicates relevance

---

## 2. COLOR SYSTEM

### Primary Palette

```scss
// Core Brand Colors
$infinite-primary: #00D4FF;      // Cyan - Primary actions
$infinite-secondary: #FF00FF;     // Magenta - AI agents
$infinite-accent: #00FF88;        // Mint - Success states
$infinite-warning: #FFB800;       // Amber - Warnings
$infinite-error: #FF0044;         // Red - Errors
$infinite-neutral: #1A1F2E;       // Dark blue-gray - Base

// Semantic Memory Colors
$memory-code: #4A90E2;            // Blue - Code chunks
$memory-docs: #7ED321;            // Green - Documentation
$memory-conversation: #BD10E0;    // Purple - Conversations
$memory-system: #F5A623;          // Gold - System prompts
$memory-data: #9B9B9B;           // Gray - Raw data

// AI Model Colors
$model-llama: #FF6B6B;           // Warm red
$model-mistral: #4ECDC4;         // Teal
$model-phi: #95E1D3;             // Light mint
$model-custom: #FFA07A;          // Light salmon
```

### Dark Theme (Default)

```typescript
const darkTheme = {
  // Background layers
  bg: {
    primary: '#0A0E1A',      // Deep space
    secondary: '#141823',     // Elevated surfaces
    tertiary: '#1C2230',      // Cards
    overlay: 'rgba(0,0,0,0.8)',
  },

  // Text hierarchy
  text: {
    primary: '#FFFFFF',
    secondary: '#B4B9C6',
    tertiary: '#737B8C',
    disabled: '#4A5361',
  },

  // 3D World
  world: {
    sky: 'linear-gradient(180deg, #0A0E1A 0%, #1A1F2E 100%)',
    ground: '#0D1117',
    grid: 'rgba(100, 200, 255, 0.1)',
    fog: 'rgba(10, 14, 26, 0.95)',
  },

  // Glass morphism
  glass: {
    background: 'rgba(20, 24, 35, 0.7)',
    border: 'rgba(255, 255, 255, 0.1)',
    shadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
    blur: 'blur(12px)',
  },
};
```

### Light Theme (Alternative)

```typescript
const lightTheme = {
  bg: {
    primary: '#FFFFFF',
    secondary: '#F7F9FC',
    tertiary: '#EFF3F8',
    overlay: 'rgba(255,255,255,0.9)',
  },

  text: {
    primary: '#1A1F2E',
    secondary: '#4A5361',
    tertiary: '#737B8C',
    disabled: '#B4B9C6',
  },

  world: {
    sky: 'linear-gradient(180deg, #E3F2FF 0%, #FFFFFF 100%)',
    ground: '#F0F4F8',
    grid: 'rgba(0, 100, 200, 0.1)',
    fog: 'rgba(255, 255, 255, 0.9)',
  },
};
```

---

## 3. WEBGPU SHADER STYLING

### Voxel Chunk Shaders

```wgsl
// Vertex shader for memory chunks
@vertex
fn vs_main(
  @location(0) position: vec3<f32>,
  @location(1) normal: vec3<f32>,
  @location(2) uv: vec2<f32>,
  @builtin(instance_index) instance: u32
) -> VertexOutput {
  var out: VertexOutput;

  // Apply instance transform
  let world_pos = instance_data[instance].transform * vec4(position, 1.0);

  // Pulse effect based on relevance
  let pulse = sin(uniforms.time * 2.0) * 0.05 * instance_data[instance].relevance;
  out.position = uniforms.mvp * (world_pos + vec4(0.0, pulse, 0.0, 0.0));

  // Color by memory type
  out.color = getMemoryColor(instance_data[instance].memory_type);

  // Glow intensity based on recency
  out.glow = instance_data[instance].recency;

  return out;
}

// Fragment shader with glow effect
@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
  var color = in.color;

  // Edge glow effect
  let edge = 1.0 - dot(in.normal, normalize(in.view_dir));
  let glow = pow(edge, 2.0) * in.glow;

  // Add emission
  color.rgb += vec3(0.0, 0.8, 1.0) * glow * 0.5;

  // Fog effect for depth
  let fog_factor = smoothstep(fog.near, fog.far, in.depth);
  color.rgb = mix(color.rgb, fog.color, fog_factor);

  return color;
}
```

### Agent Avatar Shaders

```wgsl
// Holographic AI agent effect
@fragment
fn fs_agent(in: VertexOutput) -> @location(0) vec4<f32> {
  // Hologram scanlines
  let scanline = sin(in.world_pos.y * 100.0 + uniforms.time * 2.0);
  let scanline_alpha = smoothstep(0.0, 0.1, scanline);

  // Fresnel rim lighting
  let fresnel = pow(1.0 - dot(in.normal, in.view_dir), 2.0);

  // Animated neural network pattern
  let neural = fbm_noise(in.position.xy * 10.0 + uniforms.time);

  // Combine effects
  var color = agent_colors[in.agent_type];
  color.rgb += vec3(fresnel) * 0.5;
  color.rgb += neural * 0.2;
  color.a *= scanline_alpha * 0.9;

  return color;
}
```

### Particle System Shaders

```wgsl
// Data flow particles
@fragment
fn fs_particle(in: ParticleInput) -> @location(0) vec4<f32> {
  // Soft particle edges
  let dist = length(in.uv - vec2(0.5));
  let alpha = smoothstep(0.5, 0.0, dist);

  // Trail effect
  let trail = smoothstep(0.0, 1.0, in.age / in.lifetime);

  // Color by data type
  var color = getDataColor(in.data_type);
  color.rgb *= (1.0 - trail * 0.5); // Fade over time
  color.a *= alpha * (1.0 - trail);

  // Add glow
  color.rgb += vec3(0.5) * pow(1.0 - dist, 3.0);

  return color;
}
```

---

## 4. CSS-IN-JS ARCHITECTURE

### Styled Components Setup

```typescript
import styled from '@emotion/styled';
import { css, keyframes } from '@emotion/react';

// Global theme provider
const theme = {
  colors: darkTheme,
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
  },
  typography: {
    mono: '"JetBrains Mono", "Fira Code", monospace',
    sans: '"Inter", -apple-system, BlinkMacSystemFont, sans-serif',
    display: '"Orbitron", "Exo 2", sans-serif',
  },
  animation: {
    fast: '150ms',
    normal: '300ms',
    slow: '500ms',
  },
  blur: {
    sm: 'blur(4px)',
    md: 'blur(8px)',
    lg: 'blur(16px)',
  },
};
```

### Glass Morphism Components

```typescript
const GlassPanel = styled.div<{ intensity?: number }>`
  background: ${props => `rgba(20, 24, 35, ${props.intensity || 0.7})`};
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.37),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);

  position: relative;
  overflow: hidden;

  // Subtle gradient overlay
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.2),
      transparent
    );
  }
`;
```

### Neon Glow Effects

```typescript
const neonGlow = (color: string) => css`
  text-shadow:
    0 0 5px ${color},
    0 0 10px ${color},
    0 0 20px ${color},
    0 0 40px ${color};

  animation: ${keyframes`
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
  `} 2s ease-in-out infinite;
`;

const NeonText = styled.h2`
  font-family: ${props => props.theme.typography.display};
  color: ${props => props.theme.colors.infinite.primary};
  ${props => neonGlow(props.theme.colors.infinite.primary)};
`;
```

### Data Visualization Components

```typescript
const MemoryChunkStyle = styled.div<{ type: MemoryType; relevance: number }>`
  // Base shape
  width: ${props => 50 + props.relevance * 50}px;
  height: ${props => 100 + props.relevance * 100}px;

  // Dynamic color based on type
  background: ${props => {
    const baseColor = memoryTypeColors[props.type];
    return `linear-gradient(135deg, ${baseColor}88, ${baseColor}44)`;
  }};

  // Glow effect for high relevance
  box-shadow: ${props => props.relevance > 0.7 ? `
    0 0 20px ${memoryTypeColors[props.type]}66,
    0 0 40px ${memoryTypeColors[props.type]}33
  ` : 'none'};

  // Pulsing animation for active chunks
  &.active {
    animation: ${keyframes`
      0% { transform: scale(1); }
      50% { transform: scale(1.05); }
      100% { transform: scale(1); }
    `} 2s ease-in-out infinite;
  }

  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-5px);
    box-shadow:
      0 10px 30px rgba(0, 0, 0, 0.3),
      0 0 30px ${props => memoryTypeColors[props.type]}88;
  }
`;
```

---

## 5. HUD & OVERLAY STYLING

### Futuristic HUD Elements

```scss
.hud-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1000;

  // Top bar
  .status-bar {
    position: absolute;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 20px;
    pointer-events: auto;

    .metric {
      background: rgba(10, 14, 26, 0.8);
      border: 1px solid rgba(0, 212, 255, 0.3);
      padding: 8px 16px;
      border-radius: 4px;
      font-family: 'JetBrains Mono';
      font-size: 12px;
      color: #00D4FF;

      &::before {
        content: '';
        position: absolute;
        top: -1px;
        left: -1px;
        right: -1px;
        bottom: -1px;
        background: linear-gradient(45deg, #00D4FF, transparent);
        opacity: 0;
        border-radius: 4px;
        animation: pulse 2s infinite;
      }

      @keyframes pulse {
        0%, 100% { opacity: 0; }
        50% { opacity: 0.3; }
      }
    }
  }

  // Corner brackets
  .corner-bracket {
    position: absolute;
    width: 40px;
    height: 40px;
    border: 2px solid rgba(0, 212, 255, 0.5);

    &.top-left {
      top: 10px;
      left: 10px;
      border-right: none;
      border-bottom: none;
    }

    &.top-right {
      top: 10px;
      right: 10px;
      border-left: none;
      border-bottom: none;
    }

    &.bottom-left {
      bottom: 10px;
      left: 10px;
      border-right: none;
      border-top: none;
    }

    &.bottom-right {
      bottom: 10px;
      right: 10px;
      border-left: none;
      border-top: none;
    }
  }
}
```

### Context Window Meter

```typescript
const ContextMeter = styled.div`
  width: 300px;
  height: 30px;
  background: rgba(20, 24, 35, 0.9);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 15px;
  padding: 3px;
  position: relative;

  .fill {
    height: 100%;
    border-radius: 12px;
    background: linear-gradient(
      90deg,
      #00D4FF 0%,
      #00FF88 50%,
      #FFB800 75%,
      #FF0044 100%
    );
    background-size: 300% 100%;
    background-position: ${props => `${props.percentage * 3}% 0`};
    transition: all 0.3s ease;
    box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
  }

  .label {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: white;
    font-size: 11px;
    font-family: 'JetBrains Mono';
    font-weight: bold;
    text-shadow: 0 0 10px rgba(0, 0, 0, 0.8);
  }

  .segments {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    padding: 3px;

    .segment {
      flex: 1;
      border-right: 1px solid rgba(0, 0, 0, 0.3);

      &:last-child {
        border-right: none;
      }
    }
  }
`;
```

---

## 6. ANIMATION SYSTEM

### Transition Timing Functions

```typescript
const easings = {
  // Natural movements
  easeOut: 'cubic-bezier(0.23, 1, 0.32, 1)',
  easeInOut: 'cubic-bezier(0.445, 0.05, 0.55, 0.95)',

  // Mechanical movements
  sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',

  // Elastic effects
  elastic: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',

  // Smooth deceleration
  smooth: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
};
```

### Loading Animations

```typescript
const loadingPulse = keyframes`
  0% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1.1);
  }
  100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
`;

const dataFlow = keyframes`
  0% {
    transform: translateY(100%) scale(0);
    opacity: 0;
  }
  10% {
    transform: translateY(80%) scale(0.3);
    opacity: 0.5;
  }
  50% {
    transform: translateY(0%) scale(1);
    opacity: 1;
  }
  90% {
    transform: translateY(-80%) scale(0.3);
    opacity: 0.5;
  }
  100% {
    transform: translateY(-100%) scale(0);
    opacity: 0;
  }
`;

const neuralPulse = keyframes`
  0% {
    clip-path: circle(0% at 50% 50%);
  }
  50% {
    clip-path: circle(100% at 50% 50%);
  }
  100% {
    clip-path: circle(0% at 50% 50%);
  }
`;
```

### Micro-interactions

```scss
// Button hover effects
.button-futuristic {
  position: relative;
  background: linear-gradient(135deg, #00D4FF22, #00D4FF11);
  border: 1px solid #00D4FF44;
  color: #00D4FF;
  padding: 12px 24px;
  overflow: hidden;
  transition: all 0.3s ease;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, #00D4FF44, transparent);
    transition: left 0.5s ease;
  }

  &:hover {
    border-color: #00D4FF;
    box-shadow:
      0 0 20px #00D4FF44,
      inset 0 0 20px #00D4FF11;
    transform: translateY(-2px);

    &::before {
      left: 100%;
    }
  }

  &:active {
    transform: translateY(0);
    box-shadow:
      0 0 10px #00D4FF44,
      inset 0 0 10px #00D4FF22;
  }
}
```

---

## 7. RESPONSIVE DESIGN

### Breakpoint System

```typescript
const breakpoints = {
  mobile: '@media (max-width: 640px)',
  tablet: '@media (max-width: 1024px)',
  desktop: '@media (min-width: 1025px)',
  wide: '@media (min-width: 1440px)',
  ultrawide: '@media (min-width: 2560px)',
};

// Responsive scaling for 3D viewport
const getViewportScale = () => {
  const width = window.innerWidth;

  if (width < 640) return 0.7;  // Mobile
  if (width < 1024) return 0.85; // Tablet
  if (width < 1440) return 1.0;  // Desktop
  if (width < 2560) return 1.2;  // Wide
  return 1.5; // Ultrawide
};
```

### Adaptive UI Density

```typescript
const adaptiveDensity = css`
  ${breakpoints.mobile} {
    // Compact mode
    font-size: 12px;
    padding: 4px 8px;

    .hud-panel {
      transform: scale(0.8);
      transform-origin: top left;
    }
  }

  ${breakpoints.tablet} {
    // Comfortable mode
    font-size: 14px;
    padding: 8px 12px;
  }

  ${breakpoints.desktop} {
    // Standard mode
    font-size: 14px;
    padding: 10px 16px;
  }

  ${breakpoints.ultrawide} {
    // Spacious mode
    font-size: 16px;
    padding: 12px 20px;

    .hud-panel {
      transform: scale(1.2);
    }
  }
`;
```

---

## 8. ACCESSIBILITY STYLING

### High Contrast Mode

```typescript
const highContrastTheme = {
  ...darkTheme,
  colors: {
    ...darkTheme.colors,
    text: {
      primary: '#FFFFFF',
      secondary: '#FFFFFF',
      tertiary: '#CCCCCC',
      disabled: '#999999',
    },
    borders: '#FFFFFF',
    focus: '#FFFF00',
  },
};

// Focus indicators
const focusStyle = css`
  &:focus-visible {
    outline: 3px solid ${theme.colors.focus};
    outline-offset: 2px;
    box-shadow: 0 0 0 6px rgba(255, 255, 0, 0.2);
  }
`;
```

### Motion Reduction

```scss
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  // Keep essential animations but reduce intensity
  .loading-spinner {
    animation-duration: 2s !important;
  }

  .data-particle {
    display: none; // Remove purely decorative animations
  }
}
```

### Color Blind Modes

```typescript
const colorBlindModes = {
  protanopia: {
    // Red-blind adjustments
    memory: {
      code: '#0066CC',
      docs: '#009933',
      conversation: '#CC6600',
    },
  },
  deuteranopia: {
    // Green-blind adjustments
    memory: {
      code: '#0066CC',
      docs: '#CC6600',
      conversation: '#9933CC',
    },
  },
  tritanopia: {
    // Blue-blind adjustments
    memory: {
      code: '#CC0066',
      docs: '#00CC66',
      conversation: '#CC6600',
    },
  },
};
```

---

## 9. PERFORMANCE OPTIMIZATIONS

### CSS Containment

```scss
.memory-chunk {
  contain: layout style paint;
  will-change: transform, opacity;

  // GPU acceleration
  transform: translateZ(0);
  backface-visibility: hidden;
  perspective: 1000px;
}
```

### Variable Caching

```typescript
// Cache expensive calculations
const memoizedStyles = useMemo(() => ({
  chunkStyle: calculateChunkStyle(chunkData),
  particleStyle: generateParticleStyle(particleCount),
  gridStyle: computeGridStyle(gridSize),
}), [chunkData, particleCount, gridSize]);
```

### Conditional Rendering

```typescript
const QualityAwareComponent = () => {
  const quality = useGraphicsQuality();

  return (
    <>
      {/* Always render core elements */}
      <CoreVisualization />

      {/* Conditionally render effects */}
      {quality >= 'medium' && <ParticleEffects />}
      {quality >= 'high' && <VolumetricLighting />}
      {quality === 'ultra' && <ReflectionProbes />}
    </>
  );
};
```

---

## 10. STYLE GUIDE ENFORCEMENT

### Linting Configuration

```json
{
  "extends": ["stylelint-config-standard", "stylelint-config-styled-components"],
  "rules": {
    "color-hex-length": "long",
    "declaration-colon-newline-after": null,
    "selector-class-pattern": "^[a-z][a-zA-Z0-9]+$",
    "custom-property-pattern": "^[a-z][a-zA-Z0-9]+$",
    "max-nesting-depth": 3
  }
}
```

### Component Styling Rules

1. **Use CSS-in-JS for component styles**
2. **Global styles only for resets and fonts**
3. **Theme variables for all colors and spacing**
4. **Semantic naming for custom properties**
5. **Mobile-first responsive design**
6. **GPU acceleration for animations**
7. **Accessibility as default, not afterthought**

---

## SUCCESS METRICS

### Visual Performance
- 60 FPS with all effects enabled
- <16ms paint time per frame
- <100ms style recalculation
- Smooth transitions without jank

### Design Consistency
- All components use theme variables
- Consistent animation timings
- Unified color system across 3D and 2D
- Coherent visual language

### Accessibility Score
- WCAG AAA color contrast
- Full keyboard navigation
- Screen reader compatible
- Reduced motion support

---

**Style System:** WebGPU shaders + CSS-in-JS + Dynamic theming
**Color Modes:** Dark (default), Light, High Contrast, Color Blind
**Animation:** GPU-accelerated, reduced motion support
**Performance:** 60 FPS target, progressive enhancement