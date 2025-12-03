# Alpha Deploy Design System

**Project:** Alpha Deploy LLC Brand & Design Guidelines
**Owner:** Adolfo Lopez (ch1pu) - United States Navy Veteran
**Company:** Alpha Deploy LLC
**Applies To:** alphadeploy.org + infinite.alphadeploy.org
**Last Updated:** December 2, 2025

---

## Table of Contents

1. [Brand Overview](#1-brand-overview)
2. [Logo & Identity](#2-logo--identity)
3. [Color System](#3-color-system)
4. [Typography](#4-typography)
5. [Spacing & Layout](#5-spacing--layout)
6. [Component Library](#6-component-library)
7. [Iconography](#7-iconography)
8. [Motion & Animation](#8-motion--animation)
9. [3D Design Guidelines](#9-3d-design-guidelines)
10. [Responsive Design](#10-responsive-design)
11. [Accessibility](#11-accessibility)
12. [Application Guidelines](#12-application-guidelines)

---

## 1. Brand Overview

### Brand Essence

**Alpha Deploy** represents the intersection of:
- **Military Precision** - Disciplined, reliable, mission-focused
- **Technical Innovation** - Revolutionary AI breakthroughs
- **Entrepreneurial Spirit** - Veteran-owned startup energy

### Brand Pillars

| Pillar | Description | Visual Expression |
|--------|-------------|-------------------|
| **Precision** | Technical accuracy, proven results | Clean lines, grid systems |
| **Innovation** | Revolutionary technology | Futuristic aesthetics, glow effects |
| **Trust** | Veteran credibility, reliability | Navy blue, gold accents |
| **Power** | High-performance AI systems | Bold typography, strong contrast |

### Voice & Tone

**Technical but Accessible:**
- Use precise technical language
- Explain complex concepts simply
- Show confidence in claims
- Back claims with data

**Professional but Human:**
- Friendly, approachable
- Proud veteran heritage
- Passionate about innovation
- Not corporate-speak

### Target Audience Considerations

| Audience | Priority | Tone Adjustment |
|----------|----------|-----------------|
| Enterprise Buyers | High | Emphasize ROI, reliability |
| Grant Evaluators | High | Emphasize innovation, technical merit |
| VCs | Medium | Emphasize market opportunity |
| Technical Partners | Medium | Emphasize architecture, performance |
| Press | Low | Emphasize story, differentiation |

---

## 2. Logo & Identity

### Primary Logo

**Concept:** Stylized "A" that suggests:
- Spatial/3D depth (layered appearance)
- Forward momentum (arrow-like)
- Stability (triangular base)
- Technology (sharp, precise angles)

**Logo Specifications:**

```
+------------------------------------------+
|                                          |
|            /\                            |
|           /  \                           |
|          /    \                          |
|         /      \                         |
|        /   /\   \                        |
|       /   /  \   \                       |
|      /   /    \   \                      |
|     /___/______\___\                     |
|                                          |
|       ALPHA DEPLOY                       |
|                                          |
+------------------------------------------+
```

**Dimensions:**
- Minimum width: 120px (digital), 1 inch (print)
- Clear space: Logo height / 4 on all sides
- Aspect ratio: Maintain always

### Logo Variants

| Variant | Use Case |
|---------|----------|
| **Full Logo** | Primary use, headers, hero sections |
| **Logo Mark Only** | Favicons, avatars, tight spaces |
| **Horizontal** | Navigation bars, email signatures |
| **Monochrome** | Single-color applications |
| **Reverse** | Dark backgrounds |

### Logo Colors

| Context | Primary | Secondary |
|---------|---------|-----------|
| Light Background | Navy 900 | Gold accent |
| Dark Background | White | Cyan accent |
| Monochrome | Navy 900 or White | N/A |

### Logo Don'ts

- Do NOT stretch or distort
- Do NOT rotate
- Do NOT add effects (shadows, gradients)
- Do NOT place on busy backgrounds
- Do NOT change colors outside brand palette
- Do NOT reduce below minimum size

### Favicon

**Sizes Required:**
- 16x16 px (browser tab)
- 32x32 px (browser tab, high DPI)
- 180x180 px (Apple touch icon)
- 192x192 px (Android Chrome)
- 512x512 px (PWA)

**Design:** Logo mark "A" only, simplified for small sizes

---

## 3. Color System

### Primary Palette (Navy Theme)

**Navy Blue Family:**

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `navy-950` | `#06101f` | 6, 16, 31 | Deepest background |
| `navy-900` | `#0a1628` | 10, 22, 40 | Primary background |
| `navy-800` | `#0f2744` | 15, 39, 68 | Secondary background |
| `navy-700` | `#1a3a5c` | 26, 58, 92 | Card backgrounds |
| `navy-600` | `#2d5a87` | 45, 90, 135 | Borders, dividers |
| `navy-500` | `#3d7ab0` | 61, 122, 176 | Inactive elements |
| `navy-400` | `#5a9bd4` | 90, 155, 212 | Hover states |
| `navy-300` | `#8ec2eb` | 142, 194, 235 | Light accents |

### Accent Colors

**Gold (Veteran Pride):**

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `gold-600` | `#b8860b` | 184, 134, 11 | Dark gold |
| `gold-500` | `#d4af37` | 212, 175, 55 | Primary gold |
| `gold-400` | `#e5c158` | 229, 193, 88 | Light gold |

**Electric Blue (Technology):**

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `electric-600` | `#0066cc` | 0, 102, 204 | Dark electric |
| `electric-500` | `#00a8ff` | 0, 168, 255 | Primary CTAs |
| `electric-400` | `#33bbff` | 51, 187, 255 | Hover |
| `electric-300` | `#66ccff` | 102, 204, 255 | Light accent |

**Cyan (Innovation):**

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `cyan-500` | `#00ffff` | 0, 255, 255 | Glow effects |
| `cyan-400` | `#33ffff` | 51, 255, 255 | Highlights |
| `cyan-300` | `#66ffff` | 102, 255, 255 | Soft glow |

### Semantic Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `success` | `#22c55e` | Positive states, completion |
| `warning` | `#eab308` | Caution, in-progress |
| `error` | `#ef4444` | Errors, critical |
| `info` | `#3b82f6` | Information, help |

### Neutral Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `white` | `#ffffff` | Primary text |
| `gray-100` | `#f3f4f6` | Light backgrounds |
| `gray-200` | `#e5e7eb` | Borders (light mode) |
| `gray-300` | `#d1d5db` | Disabled text |
| `gray-400` | `#9ca3af` | Secondary text |
| `gray-500` | `#6b7280` | Muted text |
| `gray-600` | `#4b5563` | Dark text |
| `gray-700` | `#374151` | Headings (light mode) |
| `gray-800` | `#1f2937` | Body (light mode) |
| `gray-900` | `#111827` | Primary (light mode) |
| `black` | `#000000` | Pure black (use sparingly) |

### Color Application

**Landing Page (alphadeploy.org):**
- Background: `navy-900`
- Cards: `navy-700` with 50% opacity
- Text: `white` (primary), `gray-400` (secondary)
- CTAs: `electric-500` with gradient to `electric-600`
- Accents: `gold-500` for veteran elements

**Demo Site (infinite.alphadeploy.org):**
- Background: `navy-950` (darker for 3D contrast)
- UI Panels: `navy-800` with 80% opacity, blur
- Text: `white` (primary), `gray-400` (secondary)
- CTAs: `electric-500`
- 3D Tokens: Color by type (see 3D guidelines)
- Glow effects: `cyan-500`

### CSS Custom Properties

```css
:root {
  /* Navy */
  --color-navy-950: #06101f;
  --color-navy-900: #0a1628;
  --color-navy-800: #0f2744;
  --color-navy-700: #1a3a5c;
  --color-navy-600: #2d5a87;

  /* Gold */
  --color-gold-500: #d4af37;

  /* Electric Blue */
  --color-electric-600: #0066cc;
  --color-electric-500: #00a8ff;
  --color-electric-400: #33bbff;

  /* Cyan */
  --color-cyan-500: #00ffff;

  /* Semantic */
  --color-success: #22c55e;
  --color-warning: #eab308;
  --color-error: #ef4444;

  /* Text */
  --color-text-primary: #ffffff;
  --color-text-secondary: #9ca3af;
  --color-text-muted: #6b7280;
}
```

### Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#06101f',
          900: '#0a1628',
          800: '#0f2744',
          700: '#1a3a5c',
          600: '#2d5a87',
          500: '#3d7ab0',
          400: '#5a9bd4',
          300: '#8ec2eb',
        },
        gold: {
          600: '#b8860b',
          500: '#d4af37',
          400: '#e5c158',
        },
        electric: {
          600: '#0066cc',
          500: '#00a8ff',
          400: '#33bbff',
          300: '#66ccff',
        },
        cyan: {
          500: '#00ffff',
          400: '#33ffff',
          300: '#66ffff',
        },
      },
    },
  },
};
```

---

## 4. Typography

### Font Stack

**Primary Font (Headings + Body):**
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

**Monospace Font (Code):**
```css
font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

### Type Scale

| Name | Size | Weight | Line Height | Letter Spacing | Use Case |
|------|------|--------|-------------|----------------|----------|
| `display-xl` | 72px (4.5rem) | 800 | 1.0 | -0.02em | Hero headlines |
| `display-lg` | 60px (3.75rem) | 800 | 1.1 | -0.02em | Major headlines |
| `display-md` | 48px (3rem) | 700 | 1.1 | -0.01em | Section headers |
| `display-sm` | 36px (2.25rem) | 700 | 1.2 | -0.01em | Subsection headers |
| `heading-xl` | 30px (1.875rem) | 600 | 1.3 | 0 | Card titles |
| `heading-lg` | 24px (1.5rem) | 600 | 1.3 | 0 | Widget titles |
| `heading-md` | 20px (1.25rem) | 600 | 1.4 | 0 | List headers |
| `heading-sm` | 18px (1.125rem) | 600 | 1.4 | 0 | Small headers |
| `body-lg` | 18px (1.125rem) | 400 | 1.6 | 0 | Lead paragraphs |
| `body-md` | 16px (1rem) | 400 | 1.6 | 0 | Body text |
| `body-sm` | 14px (0.875rem) | 400 | 1.5 | 0 | Secondary text |
| `caption` | 12px (0.75rem) | 500 | 1.4 | 0.02em | Labels, captions |
| `overline` | 12px (0.75rem) | 700 | 1.2 | 0.1em | Overlines, badges |

### Responsive Typography

```css
/* Hero headline - scales with viewport */
.display-xl {
  font-size: clamp(2.5rem, 5vw + 1rem, 4.5rem);
  font-weight: 800;
  line-height: 1.0;
  letter-spacing: -0.02em;
}

/* Section headers */
.display-md {
  font-size: clamp(2rem, 3vw + 0.5rem, 3rem);
  font-weight: 700;
  line-height: 1.1;
}

/* Card titles */
.heading-xl {
  font-size: clamp(1.5rem, 2vw + 0.5rem, 1.875rem);
  font-weight: 600;
  line-height: 1.3;
}
```

### Font Loading

```html
<!-- Preload critical fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Typography Rules

**Headlines:**
- Always use title case for H1, H2
- Sentence case for H3 and below
- Maximum 3 lines for headlines
- No orphans (single words on last line)

**Body Text:**
- Maximum 75 characters per line
- Left-aligned (never justified)
- Adequate paragraph spacing (1.5x line height)
- Use bold sparingly for emphasis

**Code:**
- Use monospace font
- Syntax highlighting for code blocks
- Inline code: light background, slight border-radius

---

## 5. Spacing & Layout

### Spacing Scale

**Base Unit:** 4px (0.25rem)

| Token | Value | Rem | Use Case |
|-------|-------|-----|----------|
| `space-0` | 0px | 0 | No spacing |
| `space-1` | 4px | 0.25rem | Tight inline spacing |
| `space-2` | 8px | 0.5rem | Icon gaps, dense lists |
| `space-3` | 12px | 0.75rem | Button padding |
| `space-4` | 16px | 1rem | Standard gap |
| `space-5` | 20px | 1.25rem | Medium gap |
| `space-6` | 24px | 1.5rem | Card padding |
| `space-8` | 32px | 2rem | Section internal |
| `space-10` | 40px | 2.5rem | Large gaps |
| `space-12` | 48px | 3rem | Section padding |
| `space-16` | 64px | 4rem | Section margins |
| `space-20` | 80px | 5rem | Major sections |
| `space-24` | 96px | 6rem | Page sections |
| `space-32` | 128px | 8rem | Hero spacing |

### Grid System

**Container Widths:**

| Name | Max Width | Use Case |
|------|-----------|----------|
| `container-sm` | 640px | Narrow content |
| `container-md` | 768px | Medium content |
| `container-lg` | 1024px | Standard content |
| `container-xl` | 1280px | Wide content |
| `container-2xl` | 1536px | Full-width layouts |

**Column Grid:**

```css
.grid-layout {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--space-6);
}

/* Responsive */
@media (max-width: 768px) {
  .grid-layout {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

### Layout Patterns

**Landing Page Sections:**
- Full viewport hero (100vh)
- Alternating left/right content sections
- 3-column portfolio grid (1-column mobile)
- Centered CTAs

**Demo Site Layout:**
- Full viewport 3D canvas
- Overlay UI panels (fixed position)
- Responsive panel sizes
- Collapsible sidebar

---

## 6. Component Library

### Buttons

**Primary Button:**
```css
.btn-primary {
  background: linear-gradient(135deg, var(--color-electric-500), var(--color-electric-600));
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 168, 255, 0.4);
}

.btn-primary:active {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}
```

**Secondary Button:**
```css
.btn-secondary {
  background: transparent;
  color: var(--color-electric-500);
  padding: 10px 22px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  border: 2px solid var(--color-electric-500);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: rgba(0, 168, 255, 0.1);
}
```

**Ghost Button:**
```css
.btn-ghost {
  background: transparent;
  color: var(--color-text-secondary);
  padding: 10px 22px;
  border-radius: 8px;
  font-weight: 500;
  font-size: 16px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-ghost:hover {
  color: white;
  background: rgba(255, 255, 255, 0.05);
}
```

**Button Sizes:**

| Size | Padding | Font Size | Border Radius |
|------|---------|-----------|---------------|
| `sm` | 8px 16px | 14px | 6px |
| `md` | 12px 24px | 16px | 8px |
| `lg` | 16px 32px | 18px | 10px |
| `xl` | 20px 40px | 20px | 12px |

### Cards

**Standard Card:**
```css
.card {
  background: rgba(26, 58, 92, 0.5); /* navy-700 at 50% */
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 168, 255, 0.2);
  border-radius: 16px;
  padding: 24px;
  transition: all 0.3s ease;
}

.card:hover {
  border-color: rgba(0, 168, 255, 0.5);
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}
```

**Metric Card:**
```css
.card-metric {
  background: rgba(15, 39, 68, 0.8); /* navy-800 at 80% */
  backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 168, 255, 0.15);
  border-radius: 12px;
  padding: 16px 20px;
}

.card-metric-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--color-electric-500);
}

.card-metric-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
```

### Inputs

**Text Input:**
```css
.input {
  background: rgba(10, 22, 40, 0.8); /* navy-900 at 80% */
  border: 1px solid rgba(45, 90, 135, 0.5); /* navy-600 */
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 16px;
  color: white;
  transition: all 0.2s ease;
}

.input:focus {
  outline: none;
  border-color: var(--color-electric-500);
  box-shadow: 0 0 0 3px rgba(0, 168, 255, 0.2);
}

.input::placeholder {
  color: var(--color-text-muted);
}
```

**Search Input:**
```css
.input-search {
  background: rgba(10, 22, 40, 0.8);
  border: 1px solid transparent;
  border-radius: 24px;
  padding: 12px 20px 12px 48px;
  font-size: 16px;
  color: white;
  background-image: url('search-icon.svg');
  background-repeat: no-repeat;
  background-position: 16px center;
}
```

### Badges

**Status Badge:**
```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge-success {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.badge-warning {
  background: rgba(234, 179, 8, 0.2);
  color: #eab308;
}

.badge-info {
  background: rgba(0, 168, 255, 0.2);
  color: #00a8ff;
}
```

### Progress Indicators

**Progress Bar:**
```css
.progress {
  background: rgba(45, 90, 135, 0.3); /* navy-600 */
  border-radius: 999px;
  height: 8px;
  overflow: hidden;
}

.progress-fill {
  background: linear-gradient(90deg, var(--color-electric-500), var(--color-cyan-500));
  height: 100%;
  border-radius: 999px;
  transition: width 0.3s ease;
}
```

**Circular Progress:**
```css
.progress-circle {
  transform: rotate(-90deg);
}

.progress-circle-bg {
  fill: none;
  stroke: rgba(45, 90, 135, 0.3);
  stroke-width: 4;
}

.progress-circle-fill {
  fill: none;
  stroke: var(--color-electric-500);
  stroke-width: 4;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.3s ease;
}
```

### Tooltips

```css
.tooltip {
  position: relative;
}

.tooltip-content {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-8px);
  background: var(--color-navy-800);
  border: 1px solid rgba(0, 168, 255, 0.3);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
}

.tooltip:hover .tooltip-content {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(-12px);
}
```

---

## 7. Iconography

### Icon Style Guidelines

**Style:** Line icons with rounded ends
**Stroke Width:** 2px
**Corner Radius:** Rounded (not sharp)
**Size Consistency:** 24px default, scale proportionally

### Icon Sizes

| Size | Pixels | Use Case |
|------|--------|----------|
| `xs` | 16px | Inline with small text |
| `sm` | 20px | Buttons, badges |
| `md` | 24px | Standard icons |
| `lg` | 32px | Feature icons |
| `xl` | 48px | Hero icons |

### Icon Library

**Navigation:**
- Menu (hamburger)
- Close (X)
- Arrow Left/Right
- Chevron Up/Down/Left/Right
- External Link

**Actions:**
- Search
- Plus/Add
- Minus/Remove
- Edit/Pencil
- Delete/Trash
- Copy
- Download
- Upload
- Share

**Status:**
- Check/Checkmark
- X/Cross
- Warning Triangle
- Info Circle
- Question Circle

**Social:**
- GitHub
- LinkedIn
- Email

**3D/Spatial:**
- Cube (token)
- Grid
- Camera
- Rotate
- Zoom In/Out
- Fullscreen
- Play/Pause

### Icon Colors

**Default:** `gray-400` (#9ca3af)
**Hover:** `white` (#ffffff)
**Active:** `electric-500` (#00a8ff)
**Disabled:** `gray-600` (#4b5563)

---

## 8. Motion & Animation

### Timing Functions

| Name | CSS | Use Case |
|------|-----|----------|
| `ease-default` | `cubic-bezier(0.4, 0, 0.2, 1)` | General transitions |
| `ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | Exit animations |
| `ease-out` | `cubic-bezier(0, 0, 0.2, 1)` | Enter animations |
| `ease-bounce` | `cubic-bezier(0.68, -0.55, 0.27, 1.55)` | Playful interactions |

### Duration Scale

| Name | Duration | Use Case |
|------|----------|----------|
| `instant` | 75ms | Micro-interactions |
| `fast` | 150ms | Button hovers |
| `normal` | 200ms | Standard transitions |
| `slow` | 300ms | Panel transitions |
| `slower` | 500ms | Page transitions |

### Standard Animations

**Fade In:**
```css
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-out forwards;
}
```

**Slide Up:**
```css
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-slide-up {
  animation: slideUp 0.4s ease-out forwards;
}
```

**Scale In:**
```css
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-scale-in {
  animation: scaleIn 0.3s ease-out forwards;
}
```

**Glow Pulse:**
```css
@keyframes glowPulse {
  0%, 100% {
    box-shadow: 0 0 10px rgba(0, 168, 255, 0.3);
  }
  50% {
    box-shadow: 0 0 20px rgba(0, 168, 255, 0.6);
  }
}

.animate-glow {
  animation: glowPulse 2s ease-in-out infinite;
}
```

### Scroll Animations

```javascript
// Intersection Observer for scroll animations
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('animate-slide-up');
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.animate-on-scroll').forEach(el => {
  observer.observe(el);
});
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## 9. 3D Design Guidelines

### Token Visualization

**Token Colors by Type:**

| Type | Hex | Description |
|------|-----|-------------|
| Code | `#3b82f6` | Blue - Programming content |
| Text | `#22c55e` | Green - Documentation, prose |
| Query | `#eab308` | Gold - User queries |
| Result | `#06b6d4` | Cyan - Query results |
| System | `#8b5cf6` | Purple - System prompts |
| Error | `#ef4444` | Red - Errors |

**Token Materials:**

```javascript
// Standard token material
const tokenMaterial = new THREE.MeshStandardMaterial({
  color: 0x3b82f6,
  metalness: 0.3,
  roughness: 0.7,
  emissive: 0x3b82f6,
  emissiveIntensity: 0.1,
});

// Selected token material
const selectedMaterial = new THREE.MeshStandardMaterial({
  color: 0x3b82f6,
  metalness: 0.3,
  roughness: 0.5,
  emissive: 0x3b82f6,
  emissiveIntensity: 0.4,
});

// Attention token material (animated)
const attentionMaterial = new THREE.MeshStandardMaterial({
  color: 0x06b6d4,
  metalness: 0.5,
  roughness: 0.3,
  emissive: 0x00ffff,
  emissiveIntensity: 0.6,
});
```

### Scene Lighting

**Three-Point Lighting Setup:**

```javascript
// Key Light (main directional)
const keyLight = new THREE.DirectionalLight(0xffffff, 0.8);
keyLight.position.set(50, 100, 50);

// Fill Light (softer, opposite side)
const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
fillLight.position.set(-30, 50, -30);

// Ambient (base illumination)
const ambient = new THREE.AmbientLight(0xffffff, 0.4);

// Hemisphere (sky/ground gradient)
const hemi = new THREE.HemisphereLight(0x87ceeb, 0x1a1a2e, 0.3);
```

### Glow Effects

**Bloom Post-Processing:**

```javascript
const bloom = new UnrealBloomPass({
  strength: 0.4,
  radius: 0.8,
  threshold: 0.6,
});
```

**Emissive Materials:**
- Default tokens: emissiveIntensity 0.1
- Selected tokens: emissiveIntensity 0.4
- Attention tokens: emissiveIntensity 0.6
- Query point: emissiveIntensity 1.0

### Attention Beams

**Line Material:**

```javascript
const beamMaterial = new THREE.LineDashedMaterial({
  color: 0x00ffff,
  dashSize: 3,
  gapSize: 1,
  transparent: true,
  opacity: 0.6,
});
```

**Animated Beam:**
- Color gradient: Gold (query) to Cyan (result)
- Width: Proportional to attention weight
- Animation: Particles flowing along path
- Duration: 1.5 seconds

### Grid Design

**Spatial Grid:**

```javascript
const gridHelper = new THREE.GridHelper(
  1000,  // Size
  100,   // Divisions
  0x2d5a87,  // Center line color (navy-600)
  0x1a3a5c   // Grid line color (navy-700)
);
```

### Background/Skybox

**Gradient Background:**
- Top: `#0a1628` (navy-900)
- Bottom: `#06101f` (navy-950)
- Stars: Sparse white points (optional)

**No HDRI:** Keep background simple to focus on tokens

---

## 10. Responsive Design

### Breakpoints

| Name | Width | Device |
|------|-------|--------|
| `xs` | < 640px | Mobile portrait |
| `sm` | 640-767px | Mobile landscape |
| `md` | 768-1023px | Tablet |
| `lg` | 1024-1279px | Laptop |
| `xl` | 1280-1535px | Desktop |
| `2xl` | >= 1536px | Wide screens |

### Mobile Considerations

**Landing Page:**
- Stack portfolio cards vertically
- Hamburger menu for navigation
- Larger touch targets (min 44x44px)
- Reduce hero text size
- Full-width CTAs

**Demo Site:**
- Bottom sheet for controls (not sidebar)
- Simplified UI with expand option
- Touch gestures for 3D navigation
- Reduce particle count
- Lower render resolution

### Responsive Patterns

**Container:**
```css
.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 16px;
}

@media (min-width: 640px) {
  .container {
    padding: 0 24px;
  }
}

@media (min-width: 1024px) {
  .container {
    padding: 0 32px;
  }
}
```

**Grid Responsive:**
```css
.portfolio-grid {
  display: grid;
  gap: 24px;
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .portfolio-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .portfolio-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

---

## 11. Accessibility

### Color Contrast

**Minimum Ratios (WCAG AA):**
- Normal text (< 18px): 4.5:1
- Large text (>= 18px bold or 24px): 3:1
- UI components: 3:1

**Our Palette Compliance:**

| Combination | Ratio | Status |
|-------------|-------|--------|
| White on Navy-900 | 13.4:1 | Pass |
| Gray-400 on Navy-900 | 5.7:1 | Pass |
| Electric-500 on Navy-900 | 6.2:1 | Pass |
| Gold-500 on Navy-900 | 5.8:1 | Pass |

### Focus States

```css
/* Custom focus ring */
.focus-visible {
  outline: 2px solid var(--color-electric-500);
  outline-offset: 2px;
}

/* Remove default outline when using custom */
*:focus {
  outline: none;
}

*:focus-visible {
  outline: 2px solid var(--color-electric-500);
  outline-offset: 2px;
}
```

### Screen Reader Support

**Skip Links:**
```html
<a href="#main-content" class="sr-only focus:not-sr-only">
  Skip to main content
</a>
```

**ARIA Labels:**
```html
<button aria-label="Open navigation menu">
  <MenuIcon />
</button>

<div role="region" aria-label="Portfolio projects">
  ...
</div>
```

**Live Regions:**
```html
<div aria-live="polite" aria-atomic="true">
  Query results: 50 tokens found
</div>
```

### Keyboard Navigation

- All interactive elements focusable
- Logical tab order
- Escape closes modals/menus
- Arrow keys for lists/grids
- Enter/Space activates buttons

---

## 12. Application Guidelines

### Landing Page Implementation

**Header:**
```html
<nav class="fixed top-0 w-full bg-navy-900/95 backdrop-blur-md z-50">
  <div class="container mx-auto px-6 py-4 flex justify-between items-center">
    <a href="/" class="flex items-center gap-3">
      <img src="/logo.svg" alt="Alpha Deploy" class="h-10">
      <span class="font-bold text-xl text-white">Alpha Deploy</span>
    </a>
    <!-- Navigation -->
  </div>
</nav>
```

**Hero Section:**
```html
<section class="min-h-screen flex items-center justify-center bg-gradient-to-b from-navy-900 to-navy-950">
  <div class="container mx-auto px-6 text-center">
    <h1 class="display-xl text-white mb-6">
      Revolutionary Spatial AI Systems
    </h1>
    <p class="body-lg text-gray-400 max-w-2xl mx-auto mb-8">
      Building unlimited context AI with O(k) constant complexity.
    </p>
    <div class="flex gap-4 justify-center">
      <a href="#contact" class="btn-primary btn-lg">Request Demo</a>
      <a href="#portfolio" class="btn-secondary btn-lg">View Portfolio</a>
    </div>
  </div>
</section>
```

**Portfolio Card:**
```html
<div class="card group">
  <div class="mb-4">
    <span class="badge badge-info">40% Complete</span>
  </div>
  <h3 class="heading-xl text-white mb-2">Infinite</h3>
  <p class="body-md text-gray-400 mb-4">
    O(k) spatial attention system for unlimited AI context.
  </p>
  <ul class="text-sm text-gray-400 space-y-2 mb-6">
    <li>O(k) constant complexity</li>
    <li>3D spatial memory</li>
    <li>97/98 tests passing</li>
  </ul>
  <a href="#" class="btn-secondary w-full">Learn More</a>
</div>
```

### Demo Site Implementation

**HUD Panel:**
```tsx
<div className="absolute top-4 right-4 w-80">
  <div className="card-metric mb-4">
    <div className="card-metric-label">Tokens</div>
    <div className="card-metric-value">{tokenCount.toLocaleString()}</div>
  </div>

  <div className="card-metric mb-4">
    <div className="card-metric-label">FPS</div>
    <div className="card-metric-value">{fps}</div>
  </div>

  <div className="card p-4">
    <h3 className="heading-sm text-white mb-3">Query</h3>
    <input
      type="text"
      className="input w-full mb-3"
      placeholder="Search tokens..."
    />
    <button className="btn-primary w-full">Search</button>
  </div>
</div>
```

**Tutorial Overlay:**
```tsx
<div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
  <div className="card max-w-lg mx-4 animate-scale-in">
    <h2 className="heading-xl text-white mb-4">{step.title}</h2>
    <p className="body-md text-gray-400 mb-6">{step.content}</p>
    <div className="flex justify-between">
      <button className="btn-ghost">Skip Tutorial</button>
      <button className="btn-primary">Next</button>
    </div>
  </div>
</div>
```

---

## Summary

This design system provides a comprehensive foundation for both Alpha Deploy frontend projects:

**Brand Identity:**
- Navy blue primary palette (veteran credibility)
- Gold and cyan accents (innovation)
- Professional, technical tone

**Visual Language:**
- Clean, modern typography (Inter)
- Consistent spacing scale
- Glassmorphism cards with glow effects
- Smooth, purposeful animations

**Component Library:**
- Buttons (primary, secondary, ghost)
- Cards (standard, metric)
- Inputs and forms
- Badges and progress indicators
- Icons and tooltips

**3D Guidelines:**
- Token colors by type
- Lighting and materials
- Glow and bloom effects
- Grid and background design

**Accessibility:**
- WCAG AA color contrast
- Focus states for keyboard users
- Screen reader support
- Reduced motion preference

**Application:**
- Responsive patterns for all devices
- Implementation examples
- Consistent experience across sites

---

**Document Version:** 1.0
**Created:** December 2, 2025
**Author:** ch1pu (Adolfo Lopez)
**Status:** Ready for Implementation
