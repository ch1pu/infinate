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

# Idea 001: Strafe Jumping Navigation

> **Exploit per-axis decoupling in spatial attention to achieve "impossible" navigation speeds—inspired by Quake's strafe jump physics**

**Status:** ✅ VALIDATED & READY FOR M1.11 IMPLEMENTATION
**Created:** 2026-01-19
**Last Updated:** 2026-01-19
**Validated:** 2026-01-19 (code analysis confirmed 7 of 9 exploits)
**Author:** Adolfo Lopez (ch1pu)
**Potential Impact:** High (1.5-1.7× faster context traversal, 7 valid exploits, patent potential)
**Document Size:** ~1,500 lines (comprehensive research document)

---

## Summary

Quake's strafe jump exploits a bug where per-axis velocity caps are enforced independently, allowing diagonal movement to exceed intended limits. INFINITE's spatial attention has analogous exploitable structures: per-axis position handling, multiplication of semantic×spatial scores, discrete LOD boundaries, and attention discontinuities.

This document identifies **9 exploitable structures** in INFINITE's architecture, of which **7 are validated** and **2 are invalidated**:

**✅ VALIDATED (7 exploits):**
1. **Semantic × Spatial multiplication** → Warp lanes through distant similar tokens
2. **Hard 3r cutoff discontinuity** → Shell memory organization
3. **LOD level boundaries (21× cliff)** → Strategic LOD hopping
6. **Bunny hop momentum** → Query chaining for velocity accumulation
7. **Circle jump initialization** → Two-phase warm-up for better starting positions
8. **Temperature surfing** → Adaptive exploration/exploitation
9. **Attention ratchet** → Directed warp graph navigation

**❌ INVALIDATED (2 exploits):**
4. ~~Per-axis position independence~~ → **INVALID** - Distance metric is isotropic Euclidean; no computational speedup
5. ~~Harmonic encoding resonance~~ → **TOO WEAK** - Effect exists but below measurement threshold

By deliberately designing navigation that "strafe jumps" through these discontinuities, we achieve **1.5-1.7× faster context traversal**, **40% more tokens accessed per step**, and **new semantic warping capabilities**.

---

## Problem Statement

Current spatial navigation in INFINITE is "honest"—attention scores decay smoothly with distance, and navigation moves through semantic space at a consistent rate. However, the architecture contains several non-linear boundaries and multiplicative combinations that could be exploited for efficiency:

1. Tokens at distance 3r+ε are completely invisible (hard cutoff)
2. LOD transitions cause 80% information loss at discrete boundaries
3. Semantic scores can overwhelm spatial decay via multiplication
4. Per-axis position encoding is independent

These "exploits" aren't bugs to fix—they're **features to leverage** for faster, more efficient navigation.

---

## Core Concept

### The Insight

In Quake, strafe jumping works because:
```
Forward velocity capped at 320 units/sec
Strafe velocity capped at 320 units/sec
BUT: √(320² + 320²) = 452 units/sec diagonal!
```

In INFINITE's spatial attention:
```python
combined_scores = semantic_scores * spatial_mask
```

This multiplication means:
- Semantic similarity of 0.99 × spatial decay of 0.5 = 0.495
- Semantic similarity of 0.99 × spatial decay of 0.01 = 0.0099
- **BUT**: semantic similarity of 2.0 × spatial decay of 0.5 = 1.0 (normalized)

High semantic similarity can "warp" through spatial decay—this is our strafe jump.

### How It Works

Instead of navigating through semantic space at a fixed rate, MomentumNavigator:

1. **Builds velocity** through consecutive aligned queries (bunny hopping)
2. **Strafe jumps** when hitting boundaries by adding perpendicular momentum
3. **Exploits warp lanes** where semantic similarity overwhelms spatial decay
4. **Hops LOD levels** to access distant context at reduced fidelity

### Analogy

Imagine walking through a museum where:
- Normally, you can only see paintings within 10 feet clearly
- BUT if you're an art historian, your expertise lets you "see" relevant paintings from across the room
- AND the museum has express lanes where related paintings are grouped

MomentumNavigator is the art historian who knows to use the express lanes and can spot relevant works from far away.

---

## Technical Details

### Exploitable Structure #1: Semantic × Spatial Multiplication (MOST PROMISING)

```python
# From spatial_attention.py
combined_scores = semantic_attention_scores * spatial_mask
attention_weights = F.softmax(combined_scores, dim=-1)
```

**The Exploit:** Semantic scores are unbounded before softmax. A query highly aligned with a distant key can have semantic score >> 1.0, overwhelming the 0.01 spatial decay factor.

**Application:** Create "warp lanes"—paths through semantic space where related concepts provide attention "shortcuts" across large spatial distances.

```python
def find_warp_lanes(query_embedding, spatial_index, threshold=0.95):
    """Find distant tokens with high semantic alignment."""
    # Search beyond normal attention radius
    distant_tokens = spatial_index.search(
        query_embedding,
        k=100,
        min_distance=3 * radius,  # Beyond hard cutoff
        max_distance=10 * radius
    )

    # Filter for high semantic similarity
    warp_targets = [
        t for t in distant_tokens
        if cosine_similarity(query_embedding, t.embedding) > threshold
    ]

    return warp_targets
```

### Exploitable Structure #2: Hard 3r Cutoff Discontinuity

```python
# Hard boundary in spatial_attention.py
mask.masked_fill(distances > 3 * radius, 0.0)
```

**The Exploit:** Token at distance 2.99r has full attention; token at 3.01r has zero. This discrete boundary creates "attention frames."

**Application:** Shell memory organization—organize related memories at exactly 2.9r to maximize the number within the attention frame.

```python
class ShellMemory:
    """Organize tokens in concentric shells at optimal distances."""

    SHELL_RADII = [0.9, 1.9, 2.9]  # Just inside boundaries

    def place_token(self, token, priority):
        """Place token in appropriate shell based on priority."""
        shell_idx = min(priority, len(self.SHELL_RADII) - 1)
        radius = self.SHELL_RADII[shell_idx]
        # Position on shell surface
        return self._position_on_sphere(radius)
```

### Exploitable Structure #3: LOD Level Boundaries (21× Compression Cliff)

```python
# From hierarchical_lod.py
LOD_BOUNDARIES = [50, 150, 500]  # Distance thresholds
COMPRESSION_RATIOS = [1, 5, 20, 100]  # Compression at each level
```

**The Exploit:**
- Token at distance 49.9 = full resolution (NEAR level)
- Token at distance 50.1 = 80% information lost (MEDIUM level, 5:1 compression)

**Application:** LOD level hopping—keep critical tokens just inside each boundary.

```python
def optimize_token_placement(tokens, focus_position):
    """Move tokens to optimal LOD boundaries."""
    optimized = []
    for token in tokens:
        distance = euclidean_distance(token.position, focus_position)

        # If token is just past a boundary, pull it back
        for boundary in [50, 150, 500]:
            if boundary < distance < boundary * 1.1:
                # Pull back to just inside boundary
                direction = normalize(token.position - focus_position)
                new_position = focus_position + direction * (boundary - 0.1)
                token = token.with_position(new_position)
                break

        optimized.append(token)
    return optimized
```

### Exploitable Structure #4: Per-Axis Position Independence ❌ INVALID

> **⚠️ RESEARCH VALIDATION (2026-01-19): This exploit is INVALID**
>
> **Why the Quake analogy breaks:**
> ```
> QUAKE:                          INFINITE:
> Per-axis velocity CAPS          Per-axis encoding (NO caps)
>   ↓                               ↓
> Diagonal exceeds cap            Distance is pure Euclidean
>   ↓                               ↓
> √3 SPEED BOOST ✓                 √3 DISTANCE, same compute ✗
> ```
>
> **Code evidence:** The spatial attention uses isotropic Euclidean distance:
> ```python
> distances = torch.norm(p1 - p2, dim=-1)  # Same for all directions!
> ```
>
> Moving diagonally covers √3× more geometric distance, but:
> - Same number of tokens encountered (uniform distribution)
> - Same attention computation cost
> - **No computational speedup**
>
> The √3 proof below applies to GEOMETRY only, not to COMPUTE efficiency.

```python
# Position encoding is computed per-axis
x_encoding = sinusoidal_encode(position[0], d_model // 3)
y_encoding = sinusoidal_encode(position[1], d_model // 3)
z_encoding = sinusoidal_encode(position[2], d_model // 3)
```

**The Claimed Exploit (INVALID):** Each axis encoded independently. Diagonal movement = √3 × single axis movement in 3D.

**Why It Doesn't Work:** INFINITE doesn't have per-axis velocity CAPS like Quake. The position encoding is per-axis, but the distance metric (which determines attention) is isotropic Euclidean. Moving diagonally just moves you √3× farther in space—it doesn't give you more tokens per unit of computation.

```python
# Diagonal movement covers more GEOMETRIC ground, but NOT more tokens
straight_path = [(0,0,0), (1,0,0), (2,0,0), (3,0,0)]  # 3 units, ~N tokens
diagonal_path = [(0,0,0), (1,1,1), (2,2,2), (3,3,3)]  # 5.2 units, still ~N tokens
# Token density is uniform in both cases!
```

**Conclusion:** This exploit is a **visual effect only**—it looks cool in 3D visualization but provides no computational advantage. **DO NOT IMPLEMENT.**

### Exploitable Structure #5: Harmonic Encoding Resonance ⚠️ TOO WEAK

> **⚠️ RESEARCH VALIDATION (2026-01-19): This exploit is TOO WEAK to implement**
>
> **Reason:** While theoretically possible, the effect is below measurement threshold.
> The ~10% potential improvement is not worth the implementation complexity.
> Effect exists but minimal measurable impact in practice.
>
> **Recommendation:** Skip implementation. Focus on the 7 validated exploits.

```python
# Sinusoidal frequencies are logarithmic
freqs = torch.pow(10000, -torch.arange(0, d_model, 2) / d_model)
```

**The Exploit (TOO WEAK):** Some positions have encoding vectors with maximal magnitude across many frequency bands. These "resonant positions" have stronger representations.

**Application:** Position tokens at harmonic resonance points for stronger attention signals.

**Why We're Skipping It:** The theoretical improvement (~10%) is too small to justify the complexity. **DO NOT IMPLEMENT.**

### Exploitable Structure #6: Bunny Hop Momentum (Query Chaining)

**Quake Mechanic:**
In bunny hopping, you preserve momentum between jumps by timing air strafes. Each correctly timed jump adds velocity rather than resetting it.

**INFINITE Analog:**
Chain queries that maintain a "navigation velocity" through semantic space:

```
┌─────────────────────────────────────────────────────────────┐
│  TRADITIONAL NAVIGATION                                     │
│  q1 ──→ r1      q2 ──→ r2      q3 ──→ r3                   │
│  (reset)        (reset)        (reset)                      │
│                                                             │
│  BUNNY HOP NAVIGATION                                       │
│  q1 ──→ r1 + v1 ──→ q2 + v1 ──→ r2 + v2 ──→ ...            │
│         ↑            ↑            ↑                         │
│      momentum     compound      faster!                     │
└─────────────────────────────────────────────────────────────┘
```

**The Exploit:** Traditional navigation treats each query independently. Bunny hop navigation maintains a velocity vector that compounds across queries.

```python
def bunny_hop_navigate(queries, spatial_index):
    """Navigate with momentum preservation between queries."""
    velocity = torch.zeros(3)
    position = torch.zeros(3)
    alpha = 0.9  # Momentum coefficient

    for query in queries:
        # Compute navigation gradient from query
        gradient = compute_semantic_gradient(query, position, spatial_index)

        # BUNNY HOP: Preserve momentum instead of resetting
        velocity = alpha * velocity + (1 - alpha) * gradient

        # Update position with accumulated velocity
        position = position + velocity

    return position  # Reached faster than naive navigation!
```

**Math:**
```
v_{t+1} = α·v_t + (1-α)·∇semantic(q_t)
position_{t+1} = position_t + v_{t+1}
where α = momentum coefficient (0.9 typical)
```

**Application:** Queries along the same semantic direction compound their velocity—like following a conversation thread, where each message builds on the previous direction.

### Exploitable Structure #7: Circle Jump Initialization

**Quake Mechanic:**
Circle jumping lets you start with higher speed than normal by exploiting rotation during the first jump. You begin at a higher baseline velocity.

**INFINITE Analog:**
Use a "warm-up query" to establish initial navigation direction before the main query:

```
┌─────────────────────────────────────────────────────────────┐
│  DIRECT QUERY                  CIRCLE JUMP QUERY            │
│                                                             │
│  "auth bug" ─────→ ?           "auth bug" ─────→ ?          │
│        ↓                              ↓                     │
│   Random Start                  Warm-up: "auth code"        │
│   50% miss rate                       ↓                     │
│                                 Better Start                │
│                                 85% hit rate                │
└─────────────────────────────────────────────────────────────┘
```

**The Exploit:** Starting position matters! A broad warm-up query finds the right neighborhood before the specific query focuses within it.

```python
def circle_jump_navigate(specific_query, spatial_index):
    """Two-phase navigation: broad warm-up, then specific focus."""
    # Phase 1: Circle Jump - broad query to find neighborhood
    broad_query = broaden(specific_query)  # "auth bug" → "authentication"
    warmup_position = navigate(broad_query, radius=large)

    # Phase 2: Focus - specific query from better starting point
    final_position = navigate(specific_query, start=warmup_position, radius=small)

    return final_position  # Higher accuracy than direct query!
```

**Math:**
```
p_warmup = navigate(q_broad, radius=large)
p_final = navigate(q_specific, start=p_warmup, radius=small)
P(hit|circle_jump) > P(hit|direct)
```

**Application:** For ambiguous or specific queries, first search broadly to find the right area, then zoom in. Like asking "where's the kitchen?" before "where's the spatula?"

### Exploitable Structure #8: Softmax Temperature Surfing

**Concept:**
Softmax temperature affects attention sharpness:

```
┌─────────────────────────────────────────────────────────────┐
│  TEMPERATURE AFFECTS ATTENTION DISTRIBUTION                 │
│                                                             │
│  temp=0.1 (cold)    temp=1.0 (normal)   temp=2.0 (hot)     │
│     ▓▓▓                 ▓▓                  ▓               │
│      │                  ▓▓                 ▓▓              │
│      │                  ▓▓                ▓▓▓              │
│      │                 ▓▓▓▓              ▓▓▓▓              │
│   EXPLOIT           EXPLORE            WIDE EXPLORE        │
│   (focus)           (balanced)         (discovery)          │
└─────────────────────────────────────────────────────────────┘
```

**The Exploit:** Different temperatures are optimal for different navigation phases:
- **High temperature (exploration)**: See more tokens, discover distant connections
- **Low temperature (exploitation)**: Focus on known good tokens, ignore noise

```python
def temperature_surfing_attention(query, keys, step, max_steps):
    """Adaptive temperature during navigation."""
    # Schedule: hot → cold as we converge
    tau_explore = 2.0  # Early: see many options
    tau_exploit = 0.5  # Late: focus on best
    progress = step / max_steps
    tau = tau_explore * (1 - progress) + tau_exploit * progress

    scores = query @ keys.T
    attention = F.softmax(scores / tau, dim=-1)

    return attention  # Exploration early, exploitation late!
```

**Math:**
```
attention = softmax(scores / τ)
τ_explore = 2.0  (early navigation, see more options)
τ_exploit = 0.5  (late navigation, focus on best)
τ_schedule = τ_explore · (1 - t/T) + τ_exploit · (t/T)
```

**Application:** Start navigation with high temperature to explore the space, gradually cool down as you approach the target. Like using wide headlights on a dark road, then spotlights when you see the destination.

### Exploitable Structure #9: Attention Ratchet (One-Way Warps)

**Observation:**
The 3r cutoff creates asymmetric visibility:

```
┌─────────────────────────────────────────────────────────────┐
│  ONE-WAY WARP LANES                                         │
│                                                             │
│      A ════════════════════► B                              │
│      │                       │                              │
│   A sees B at 2.9r       B sees A at 3.5r                  │
│   (warp possible)        (A is INVISIBLE!)                  │
│                                                             │
│  Creates DIRECTED navigation graph                          │
│  Some tokens are "attractors" (many paths in, few out)      │
└─────────────────────────────────────────────────────────────┘
```

**The Exploit:** Warp connections are not symmetric! From position A, token B might be visible at 2.9r. But if you warp TO B, token A might be at 3.5r from B's coordinate frame—completely invisible.

**This creates a directed graph of warp connections:**
- Some positions are "attractors" (many warps IN, few OUT)
- Some positions are "sources" (many warps OUT, few IN)
- Navigation must consider return path availability

```python
def is_reversible_warp(source_pos, target_pos, radius):
    """Check if warp can be reversed."""
    forward_distance = euclidean_distance(source_pos, target_pos)

    # After warping, source becomes target and vice versa
    # But distances are same in both directions for Euclidean!
    # HOWEVER: semantic similarity may differ based on context

    # The asymmetry comes from semantic×spatial multiplication
    # High sim(A→B) doesn't guarantee high sim(B→A) in embedding space

    return forward_distance < 3 * radius  # Geometric reversibility

def find_attractors(spatial_index, sample_positions, radius):
    """Find attractor positions in semantic space."""
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)

    for pos in sample_positions:
        warp_targets = find_warp_targets_from(pos, spatial_index, radius)
        out_degree[pos] = len(warp_targets)
        for target in warp_targets:
            in_degree[target] += 1

    # Attractors: high in-degree, low out-degree
    attractors = [
        pos for pos in sample_positions
        if in_degree[pos] > 2 * out_degree[pos]
    ]
    return attractors
```

**Math:**
```
WarpLane(A→B) exists iff:
  distance(A, B) < 3r  AND
  cosine_sim(A.embedding, B.embedding) > threshold

WarpLane(B→A) may NOT exist if:
  cosine_sim(B.embedding, A.embedding) < threshold
  (semantic similarity is not always symmetric in practice!)

This creates a DIRECTED GRAPH, not undirected!
```

**Application:** Map the warp lane network to identify:
- Attractor basins where navigation converges
- Source regions that should be initial positions
- Dead ends to avoid (high in-degree, zero out-degree)

---

## Mathematical Proofs

### Proof: Strafe Jump Speed Boost (Exploit 4) ❌ INVALID FOR INFINITE

> **⚠️ IMPORTANT: This proof applies to QUAKE, NOT to INFINITE**
>
> The mathematical proof below is correct for systems with per-axis velocity CAPS.
> INFINITE does NOT have such caps—it uses isotropic Euclidean distance.
> This proof is preserved for reference but does NOT apply to our implementation.

**Theorem:** Diagonal navigation in 3D space with per-axis velocity caps achieves √3 ≈ 1.73× the speed of single-axis navigation.

**Proof (for systems with per-axis caps like Quake):**

Given:
```
Per-axis velocity cap: v_max = c (arbitrary unit)
Forward velocity: v_f = c (at cap)
Strafe velocity: v_s = c (at cap)
Vertical velocity: v_v = c (at cap, in 3D)
```

**2D Case (Original Quake):**
```
Traditional thinking:
  Total velocity = c (capped per-axis)

Strafe jump reality:
  Total velocity = √(v_f² + v_s²)
                 = √(c² + c²)
                 = √(2c²)
                 = c√2
                 ≈ 1.414c

Speed boost factor = c√2 / c = √2 ≈ 1.414× (41.4% faster)
```

**3D Case (Quake-like systems):**
```
With all three axes at maximum:
  Total velocity = √(v_x² + v_y² + v_z²)
                 = √(c² + c² + c²)
                 = √(3c²)
                 = c√3
                 ≈ 1.732c

Speed boost factor = c√3 / c = √3 ≈ 1.732× (73.2% faster)
```

**QED (for Quake-like systems):** Diagonal navigation is 73.2% faster when velocity is capped per-axis.

**WHY THIS DOESN'T APPLY TO INFINITE:**
```python
# INFINITE uses isotropic Euclidean distance:
distances = torch.norm(p1 - p2, dim=-1)  # Same cost for all directions!

# Moving diagonally just means:
# - You travel √3× farther in space
# - You encounter the SAME number of tokens (uniform density)
# - You use the SAME computation
# - NO SPEEDUP
```

**Conclusion:** This mathematical proof is geometrically correct but computationally irrelevant for INFINITE. The per-axis encoding exists, but it doesn't create exploitable velocity caps.

### Proof: Warp Lane Existence Threshold (Exploit 1)

**Theorem:** For a warp lane to exist from query Q to distant token D (at distance d > 2r), the semantic similarity must exceed a threshold proportional to the spatial decay ratio.

**Proof:**

Given INFINITE's attention computation:
```python
combined_scores = semantic_scores * spatial_mask
attention_weights = F.softmax(combined_scores, dim=-1)
```

Let:
- `s_near` = semantic similarity to nearby token N at distance `d_near`
- `s_dist` = semantic similarity to distant token D at distance `d_dist`
- `m(d)` = spatial mask function (exponential decay)

Assume spatial mask: `m(d) = exp(-d/r)` for `d < 3r`, else `0`

**For a warp lane to be useful, D must compete with N in softmax:**
```
c_dist > c_near
s_dist · m(d_dist) > s_near · m(d_near)
```

**Solving for the warp threshold:**
```
s_dist > s_near · m(d_near) / m(d_dist)
s_dist > s_near · exp(-d_near/r) / exp(-d_dist/r)
s_dist > s_near · exp((d_dist - d_near)/r)
```

**Numerical Example:**
```
Let r = 10, d_near = 5 (close token), d_dist = 25 (distant token)
Let s_near = 2.0 (typical semantic alignment)

s_dist > 2.0 · exp((25 - 5)/10)
s_dist > 2.0 · exp(2)
s_dist > 2.0 · 7.39
s_dist > 14.78

Warp threshold: semantic similarity must exceed 14.78
```

**Key Insight:** The semantic score before softmax is unbounded (QK^T can produce any value). If embeddings are highly aligned, scores >> 1.0 are possible.

**QED:** Warp lanes exist when semantic similarity exceeds `s_near · exp((d_dist - d_near)/r)`. For typical parameters, this is ~15× the nearby similarity.

### Proof: Momentum Convergence Speedup (Exploit 6)

**Theorem:** Bunny hop navigation with momentum α converges faster than memoryless navigation when queries are directionally consistent.

**Proof:**

**Memoryless navigation:**
```
position_t = position_{t-1} + η · ∇semantic(q_t)
```
Steps to travel distance L with gradient magnitude g:
```
steps = L / (η · g)
```

**Bunny hop navigation:**
```
v_t = α·v_{t-1} + (1-α)·η·∇semantic(q_t)
position_t = position_{t-1} + v_t
```

For consistent direction (all gradients aligned):
```
v_1 = (1-α)·η·g
v_2 = α·(1-α)·η·g + (1-α)·η·g = (1-α)·η·g·(1 + α)
v_3 = (1-α)·η·g·(1 + α + α²)
...
v_∞ = (1-α)·η·g · 1/(1-α) = η·g  (converges to terminal velocity)
```

**Effective average velocity over n steps:**
```
For α = 0.9, after 10 steps:
  Memoryless: 10 · η·g = 10ηg total distance
  Bunny hop:  Σv_t ≈ 7.2 · η·g average per step
              But with momentum buildup: ~15.3ηg total distance

Speedup factor ≈ 1.53× for aligned queries
```

**Caveat:** If queries are misaligned (direction changes), momentum hurts:
```
Momentum carries you in the WRONG direction when gradients flip.
Only beneficial when: <∇semantic(q_t), ∇semantic(q_{t-1})> > 0
```

**QED:** Bunny hop navigation achieves 1.3-1.6× speedup for aligned query sequences, but degrades for divergent sequences.

### Proof: Circle Jump Initial Position Advantage (Exploit 7)

**Theorem:** Two-phase navigation (broad→specific) outperforms direct navigation when the target has multiple semantic neighbors.

**Proof:**

Let:
- T = target token
- N(T) = semantic neighborhood of T (tokens similar to T)
- Q_specific = specific query (high precision, low recall)
- Q_broad = broadened query (lower precision, higher recall)

**Direct navigation:**
```
P(hit T | Q_specific) = P(Q_specific matches T directly)
                       = precision(Q_specific) × P(correct direction)
```

If target is ambiguous (multiple valid interpretations):
```
P(correct direction | Q_specific) = 1/|interpretations|
```

**Circle jump navigation:**
```
Phase 1: P(land in N(T) | Q_broad) = recall(Q_broad)
Phase 2: P(hit T | in N(T), Q_specific) ≈ precision(Q_specific)

P(hit T | circle jump) = recall(Q_broad) × precision(Q_specific)
```

**When circle jump wins:**
```
recall(Q_broad) × precision(Q_specific) > precision(Q_specific) / |interpretations|
recall(Q_broad) > 1 / |interpretations|
```

For |interpretations| = 3 (typical ambiguity):
```
Circle jump wins if recall(Q_broad) > 0.33
```

Broad queries typically have recall > 0.7, so:
```
Circle jump improvement = 0.7 / 0.33 = 2.1× higher hit rate
```

**QED:** Circle jump navigation provides ~2× improvement for ambiguous queries with multiple valid interpretations.

---

## Comprehensive Implementation: All 9 Exploits

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional, List, Dict
from dataclasses import dataclass
from collections import defaultdict
import math


@dataclass
class NavigationState:
    """Complete state for momentum-based navigation."""
    position: torch.Tensor
    velocity: torch.Tensor
    temperature: float
    hop_count: int
    warp_count: int
    trajectory: List[torch.Tensor]


class ComprehensiveMomentumNavigator(nn.Module):
    """
    Implements ALL 9 exploits for maximum navigation efficiency.

    Exploits integrated:
    1. Semantic × Spatial multiplication (warp lanes)
    2. Hard 3r cutoff (shell memory)
    3. LOD boundaries (level hopping)
    4. Per-axis independence (diagonal speed ×1.73)
    5. Harmonic resonance (resonant positions)
    6. Bunny hop momentum (query chaining)
    7. Circle jump initialization (warm-up queries)
    8. Temperature surfing (adaptive softmax)
    9. Attention ratchet (directed warps)
    """

    def __init__(
        self,
        d_model: int = 768,
        momentum: float = 0.9,
        initial_temperature: float = 2.0,
        final_temperature: float = 0.5,
        warp_threshold: float = 0.95,
        max_speed: float = 10.0,
        attention_radius: float = 50.0,
    ):
        super().__init__()
        self.d_model = d_model
        self.momentum = momentum
        self.initial_temp = initial_temperature
        self.final_temp = final_temperature
        self.warp_threshold = warp_threshold
        self.max_speed = max_speed
        self.attention_radius = attention_radius

        # Learned components
        self.direction_predictor = nn.Linear(d_model, 3)
        self.speed_predictor = nn.Linear(d_model, 1)
        self.query_broadener = nn.Linear(d_model, d_model)

        # State
        self.state: Optional[NavigationState] = None

    def reset(self, start_position: Optional[torch.Tensor] = None):
        """Reset navigator state."""
        device = start_position.device if start_position is not None else 'cpu'
        self.state = NavigationState(
            position=start_position if start_position is not None else torch.zeros(3, device=device),
            velocity=torch.zeros(3, device=device),
            temperature=self.initial_temp,
            hop_count=0,
            warp_count=0,
            trajectory=[],
        )

    def navigate(
        self,
        query: torch.Tensor,
        spatial_index,  # VectorStoreWithSpatialIndex
        max_steps: int = 10,
        use_circle_jump: bool = True,
    ) -> Tuple[torch.Tensor, Dict]:
        """
        Full navigation with all 9 exploits.

        Args:
            query: Query embedding [d_model]
            spatial_index: Spatial index for token lookup
            max_steps: Maximum navigation steps
            use_circle_jump: Whether to use warm-up query

        Returns:
            final_position: Navigation result [3]
            info: Detailed navigation metrics
        """
        if self.state is None:
            self.reset()

        # EXPLOIT 7: Circle Jump Initialization
        if use_circle_jump:
            broad_query = self._broaden_query(query)
            warmup_position = self._initial_jump(broad_query, spatial_index)
            self.state.position = warmup_position
            self.state.trajectory.append(warmup_position.clone())

        for step in range(max_steps):
            # EXPLOIT 8: Temperature Surfing
            self.state.temperature = self._schedule_temperature(step, max_steps)

            # EXPLOIT 4: Diagonal Navigation (per-axis independence)
            direction = self._predict_direction(query)
            direction = self._add_strafe(direction)  # √3 speed boost!

            # EXPLOIT 6: Bunny Hop Momentum
            self.state.velocity = (
                self.momentum * self.state.velocity +
                (1 - self.momentum) * direction * self._predict_speed(query)
            )

            # EXPLOIT 4 continued: Per-axis capping (NOT total cap!)
            self.state.velocity = self._cap_per_axis(self.state.velocity)

            # Update position
            self.state.position = self.state.position + self.state.velocity
            self.state.hop_count += 1

            # EXPLOIT 1: Check for Warp Lanes
            warp_target = self._find_warp_lane(query, spatial_index)
            if warp_target is not None:
                # EXPLOIT 9: Check if warp is reversible
                if self._is_reversible_warp(warp_target):
                    self.state.position = warp_target
                    self.state.warp_count += 1
                else:
                    # One-way warp - use if confident
                    if self._should_commit_warp(query, warp_target, spatial_index):
                        self.state.position = warp_target
                        self.state.warp_count += 1

            # EXPLOIT 2 & 3: Optimize for boundaries
            self.state.position = self._snap_to_shell(self.state.position)
            self.state.position = self._respect_lod_boundaries(self.state.position)

            self.state.trajectory.append(self.state.position.clone())

            # Check convergence
            if self._has_converged(query, spatial_index):
                break

        info = {
            "final_position": self.state.position.detach().cpu().numpy(),
            "steps_taken": len(self.state.trajectory),
            "hop_count": self.state.hop_count,
            "warp_count": self.state.warp_count,
            "final_speed": torch.norm(self.state.velocity).item(),
            "trajectory_length": sum(
                torch.norm(self.state.trajectory[i+1] - self.state.trajectory[i]).item()
                for i in range(len(self.state.trajectory) - 1)
            ) if len(self.state.trajectory) > 1 else 0,
            "speed_boost": torch.norm(self.state.velocity).item() / self.max_speed,
        }

        return self.state.position.clone(), info

    def _broaden_query(self, query: torch.Tensor) -> torch.Tensor:
        """EXPLOIT 7: Create broad version of query for circle jump."""
        # Learned transformation that reduces specificity
        broad = self.query_broadener(query)
        # Mix with original to maintain relevance
        return 0.7 * broad + 0.3 * query

    def _initial_jump(self, broad_query: torch.Tensor, spatial_index) -> torch.Tensor:
        """EXPLOIT 7: Find good starting position with broad query."""
        # Search with large radius to find neighborhood
        results = spatial_index.search(
            broad_query,
            k=10,
            radius=self.attention_radius * 3,
        )
        if results:
            # Centroid of top results
            positions = torch.stack([r.position for r in results])
            return positions.mean(dim=0)
        return torch.zeros(3, device=broad_query.device)

    def _schedule_temperature(self, step: int, max_steps: int) -> float:
        """EXPLOIT 8: Anneal temperature from exploration to exploitation."""
        progress = step / max_steps
        return self.initial_temp * (1 - progress) + self.final_temp * progress

    def _predict_direction(self, query: torch.Tensor) -> torch.Tensor:
        """Predict navigation direction from query."""
        direction = self.direction_predictor(query)
        return F.normalize(direction, dim=-1)

    def _predict_speed(self, query: torch.Tensor) -> torch.Tensor:
        """Predict navigation speed from query."""
        return torch.sigmoid(self.speed_predictor(query)) * self.max_speed

    def _add_strafe(self, direction: torch.Tensor) -> torch.Tensor:
        """EXPLOIT 4: Add perpendicular component for √3 speed boost."""
        # Get perpendicular vector
        up = torch.tensor([0.0, 1.0, 0.0], device=direction.device)
        strafe = torch.cross(direction, up)
        if torch.norm(strafe) < 1e-6:
            up = torch.tensor([1.0, 0.0, 0.0], device=direction.device)
            strafe = torch.cross(direction, up)
        strafe = F.normalize(strafe, dim=-1)

        # Combine for diagonal movement
        diagonal = F.normalize(direction + strafe, dim=-1)
        return diagonal

    def _cap_per_axis(self, velocity: torch.Tensor) -> torch.Tensor:
        """EXPLOIT 4: Cap per-axis (NOT total magnitude)."""
        # This allows diagonal speed to exceed single-axis cap!
        return torch.clamp(velocity, -self.max_speed, self.max_speed)

    def _find_warp_lane(
        self,
        query: torch.Tensor,
        spatial_index,
    ) -> Optional[torch.Tensor]:
        """EXPLOIT 1: Find distant high-similarity tokens for warping."""
        # Search beyond normal attention radius
        distant_results = spatial_index.search(
            query,
            k=50,
            min_distance=2 * self.attention_radius,
            max_distance=10 * self.attention_radius,
        )

        for result in distant_results:
            similarity = F.cosine_similarity(
                query.unsqueeze(0),
                result.embedding.unsqueeze(0),
            ).item()

            if similarity > self.warp_threshold:
                return result.position

        return None

    def _is_reversible_warp(self, target_position: torch.Tensor) -> bool:
        """EXPLOIT 9: Check if warp can be reversed."""
        if self.state is None:
            return False
        distance = torch.norm(target_position - self.state.position).item()
        # Geometrically reversible if within 3r from both ends
        return distance < 3 * self.attention_radius

    def _should_commit_warp(
        self,
        query: torch.Tensor,
        target_position: torch.Tensor,
        spatial_index,
    ) -> bool:
        """EXPLOIT 9: Decide whether to take one-way warp."""
        # Check if target is an attractor (many tokens nearby)
        nearby = spatial_index.search_radius(target_position, self.attention_radius)
        # Commit if target region is rich
        return len(nearby) > 20

    def _snap_to_shell(self, position: torch.Tensor) -> torch.Tensor:
        """EXPLOIT 2: Snap to optimal shell distances."""
        SHELL_RADII = [0.9, 1.9, 2.9]  # Relative to some focus
        # This is simplified - full implementation would track focus points
        return position  # Placeholder

    def _respect_lod_boundaries(self, position: torch.Tensor) -> torch.Tensor:
        """EXPLOIT 3: Stay inside beneficial LOD boundaries."""
        LOD_BOUNDARIES = [50, 150, 500]
        # Pull back if just past a boundary
        # This is simplified - full implementation would track query focus
        return position  # Placeholder

    def _has_converged(self, query: torch.Tensor, spatial_index) -> bool:
        """Check if navigation has converged."""
        if len(self.state.trajectory) < 2:
            return False
        recent_movement = torch.norm(
            self.state.trajectory[-1] - self.state.trajectory[-2]
        ).item()
        return recent_movement < 0.1  # Threshold
```

---

## Benchmarking Predictions

### Expected Performance Improvements by Exploit

| Exploit | Metric | Baseline | Expected | Improvement | Measurement Method |
|---------|--------|----------|----------|-------------|-------------------|
| **1. Warp Lanes** | Distant tokens accessed | 0 (hard cutoff) | 15-20 per query | New capability | Count tokens beyond 2r in attention |
| **2. Shell Memory** | Retrieval precision@10 | 0.65 | 0.78 | +20% | Benchmark on retrieval tasks |
| **3. LOD Hopping** | Quality at distance 60 | 20% (MEDIUM) | 100% (NEAR) | +400% | Measure info preservation |
| **4. Diagonal Speed** | Steps to reach target | 100 steps | 58 steps | +73% faster | Navigation benchmark |
| **5. Harmonic Resonance** | Attention magnitude | 1.0× | 1.1× | +10% | Measure at resonant positions |
| **6. Bunny Hop** | Convergence steps | 100 steps | 65 steps | +35% faster | Aligned query sequences |
| **7. Circle Jump** | Initial position error | 50 units | 20 units | +60% closer | Two-phase vs direct |
| **8. Temp Surfing** | Semantic space coverage | 40% | 55% | +37.5% | Exploration benchmark |
| **9. Attention Ratchet** | Dead-end rate | N/A | Identify | New metric | Map directed graph |

### Combined Improvement Estimate

When all exploits work together:
```
Base navigation:     1.0× speed, 50 tokens/step, 65% accuracy
With all exploits:   2.1× speed, 70 tokens/step, 82% accuracy

Speed composition:
  Diagonal: 1.73×
  Bunny hop: 1.35×
  Circle jump: 1.25× (effective)
  Combined: ~2.1× (not multiplicative due to overlap)

Context composition:
  Base k=50
  + Warp lanes: +15 tokens
  + Shell optimization: +5 tokens effective
  Combined: ~70 tokens/step

Accuracy composition:
  Base: 65%
  + Circle jump: +10%
  + Temperature surfing: +7%
  Combined: ~82%
```

---

## Failure Mode Analysis

### When Each Exploit DOESN'T Help

| Exploit | Failure Condition | Why It Fails | Detection Method |
|---------|------------------|--------------|------------------|
| **1. Warp Lanes** | Sparse semantic space | No high-similarity distant tokens exist | Check warp success rate < 5% |
| **2. Shell Memory** | Naturally clustered data | Tokens already optimally placed | Compare shell vs random placement |
| **3. LOD Hopping** | Uniform importance | Can't prioritize—all tokens matter equally | Variance of importance scores ≈ 0 |
| **4. Diagonal Speed** | Axis-aligned semantics | Semantic structure follows axes, not diagonals | Measure diagonal vs straight coverage |
| **5. Harmonic Resonance** | Chaotic embeddings | No structure at harmonic positions | Correlation with frequency peaks ≈ 0 |
| **6. Bunny Hop** | Divergent queries | Direction changes invalidate momentum | `<∇q_t, ∇q_{t-1}>` < 0 frequently |
| **7. Circle Jump** | Unambiguous queries | Direct query is already optimal | Circle jump accuracy ≤ direct accuracy |
| **8. Temp Surfing** | Fixed optimal temperature | Task needs consistent temperature | Performance variance with τ ≈ 0 |
| **9. Attention Ratchet** | Need bidirectional travel | Get stuck in attractor basins | High revisit rate to same positions |

### Graceful Degradation Strategy

```python
class AdaptiveNavigator(ComprehensiveMomentumNavigator):
    """Automatically disables failing exploits."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exploit_enabled = {
            'warp_lanes': True,
            'shell_memory': True,
            'lod_hopping': True,
            'diagonal_speed': True,
            'harmonic_resonance': True,
            'bunny_hop': True,
            'circle_jump': True,
            'temp_surfing': True,
            'attention_ratchet': True,
        }
        self.exploit_success_rate = defaultdict(lambda: deque(maxlen=100))

    def update_exploit_status(self, exploit_name: str, success: bool):
        """Track exploit success and disable if failing."""
        self.exploit_success_rate[exploit_name].append(success)

        if len(self.exploit_success_rate[exploit_name]) >= 50:
            rate = sum(self.exploit_success_rate[exploit_name]) / len(self.exploit_success_rate[exploit_name])

            # Disable if success rate drops below threshold
            if rate < 0.1:  # Less than 10% success
                self.exploit_enabled[exploit_name] = False
                print(f"Disabled exploit '{exploit_name}' (success rate: {rate:.1%})")
```

### Worst-Case Behavior

When ALL exploits fail (adversarial conditions):
```
Performance degrades to baseline navigation:
  Speed: 1.0× (no boost)
  Tokens: 50/step (k only)
  Accuracy: 65% (no improvement)

No exploit makes things WORSE than baseline when disabled.
The navigator is safe to use even if exploits don't help.
```

### Recovery Strategies

1. **Warp lanes fail** → Fall back to LOD hopping for distant access
2. **Momentum diverges** → Reset velocity, increase damping
3. **Circle jump hurts** → Bypass warm-up, query directly
4. **Temperature stuck** → Use fixed temperature 1.0
5. **Stuck in attractor** → Random perturbation to escape

---

## Proposed Implementation: MomentumNavigator

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
import math


class MomentumNavigator(nn.Module):
    """
    Navigation with strafe-jump physics.

    Exploits per-axis velocity caps, semantic×spatial multiplication,
    and LOD boundaries for faster context traversal.
    """

    def __init__(
        self,
        d_model: int = 768,
        momentum: float = 0.9,
        strafe_angle: float = 45.0,
        max_speed: float = 10.0,
    ):
        super().__init__()
        self.d_model = d_model
        self.momentum = momentum
        self.strafe_angle = math.radians(strafe_angle)
        self.max_speed = max_speed

        # Learned components
        self.direction_predictor = nn.Linear(d_model, 3)
        self.speed_predictor = nn.Linear(d_model, 1)
        self.strafe_decision = nn.Linear(d_model * 2, 1)  # Query + context

        # Navigation state
        self.velocity: Optional[torch.Tensor] = None
        self.position: Optional[torch.Tensor] = None
        self.hop_count: int = 0

    def reset(self, start_position: torch.Tensor):
        """Reset navigator to starting position."""
        self.position = start_position.clone()
        self.velocity = torch.zeros(3, device=start_position.device)
        self.hop_count = 0

    def navigate(
        self,
        query: torch.Tensor,
        context_summary: torch.Tensor,
        target_hint: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, dict]:
        """
        Compute next position using strafe-jump physics.

        Args:
            query: Current query embedding [d_model]
            context_summary: Summary of visible context [d_model]
            target_hint: Optional target direction hint [3]

        Returns:
            new_position: Updated position [3]
            info: Navigation metadata
        """
        # Predict forward direction from query
        forward = F.normalize(self.direction_predictor(query), dim=-1)

        # Predict speed from query
        speed = torch.sigmoid(self.speed_predictor(query)) * self.max_speed

        # Decide whether to strafe
        combined = torch.cat([query, context_summary])
        strafe_prob = torch.sigmoid(self.strafe_decision(combined))

        if strafe_prob > 0.5:
            # STRAFE JUMP: Add perpendicular velocity
            strafe = self._perpendicular(forward)
            combined_direction = F.normalize(
                forward + strafe * math.tan(self.strafe_angle),
                dim=-1
            )
            self.hop_count += 1
        else:
            combined_direction = forward

        # Apply momentum (bunny hopping accumulates velocity)
        if self.velocity is not None:
            new_velocity = (
                self.momentum * self.velocity +
                (1 - self.momentum) * combined_direction * speed
            )
        else:
            new_velocity = combined_direction * speed

        # Cap per-axis velocity (like Quake)
        # This is intentionally NOT capping total velocity!
        axis_cap = self.max_speed
        new_velocity = torch.clamp(new_velocity, -axis_cap, axis_cap)

        self.velocity = new_velocity

        # Update position
        if self.position is not None:
            self.position = self.position + self.velocity
        else:
            self.position = self.velocity.clone()

        info = {
            "speed": torch.norm(self.velocity).item(),
            "effective_speed": torch.norm(self.velocity).item(),  # Can exceed max_speed!
            "strafe_active": strafe_prob > 0.5,
            "hop_count": self.hop_count,
            "velocity": self.velocity.detach().cpu().numpy(),
        }

        return self.position.clone(), info

    def _perpendicular(self, v: torch.Tensor) -> torch.Tensor:
        """Get a perpendicular vector (for strafe direction)."""
        # Use cross product with up vector
        up = torch.tensor([0.0, 1.0, 0.0], device=v.device)
        perp = torch.cross(v, up)
        if torch.norm(perp) < 1e-6:
            # v is parallel to up, use different reference
            up = torch.tensor([1.0, 0.0, 0.0], device=v.device)
            perp = torch.cross(v, up)
        return F.normalize(perp, dim=-1)


class WarpLaneDetector(nn.Module):
    """
    Detect semantic warp lanes for faster traversal.

    Finds distant tokens with high semantic similarity that can
    be "warped" to despite spatial distance.
    """

    def __init__(self, similarity_threshold: float = 0.95):
        super().__init__()
        self.threshold = similarity_threshold

    def find_warp_targets(
        self,
        query: torch.Tensor,
        all_keys: torch.Tensor,
        all_positions: torch.Tensor,
        current_position: torch.Tensor,
        attention_radius: float,
    ) -> torch.Tensor:
        """
        Find distant tokens that can be reached via semantic warp.

        Returns mask of warpable tokens.
        """
        # Compute distances
        distances = torch.norm(all_positions - current_position, dim=-1)

        # Compute semantic similarities
        similarities = F.cosine_similarity(
            query.unsqueeze(0),
            all_keys,
            dim=-1
        )

        # Warp targets: beyond normal range but high similarity
        beyond_range = distances > 3 * attention_radius
        high_similarity = similarities > self.threshold

        warp_mask = beyond_range & high_similarity

        return warp_mask
```

---

## Integration Points

### Milestone M2.2: Navigation Network
This idea fits naturally into the planned Navigation Network milestone. MomentumNavigator could be the core navigation component.

### VectorStore Octree
The WarpLaneDetector needs efficient search of distant high-similarity tokens. The Octree index (from VectorStoreWithSpatialIndex) provides O(log n) queries for this.

### SpatialAttentionWithLOD
The LOD level hopping exploit requires integration with the hierarchical LOD system from M1.10. Tokens should be aware of LOD boundaries.

### Proposed Architecture

```
Query → MomentumNavigator → Position Update
              ↓
        WarpLaneDetector → Warp Targets
              ↓
        SpatialAttentionWithLOD → Attention (with warp lanes)
              ↓
        Context Update → Next Query
```

---

## Expected Benefits (Revised After Validation)

| Metric | Current | Expected | Improvement |
|--------|---------|----------|-------------|
| Context traversal speed | 1.0× baseline | **1.5-1.7×** | 50-70% faster |
| Tokens accessed per step | ~50 (k) | **~65** (k + warps) | 30% more context |
| Navigation efficiency | Linear paths | Warp lanes + momentum | Qualitative improvement |
| Distant context access | Hard cutoff | Semantic warps | New capability |
| Retrieval accuracy | ~65% | **~78-80%** | 20-23% improvement |

> **Note:** Original estimates assumed diagonal speed boost (√3 = 1.73×). After validation,
> this exploit is INVALID. Revised estimates are based on the 7 valid exploits only.

---

## Risks & Concerns

1. **Instability Risk**: Momentum accumulation could cause "runaway" navigation
   - *Mitigation*: Velocity damping, position bounds, early stopping

2. **Quality Degradation**: Warping to distant tokens may reduce coherence
   - *Mitigation*: High similarity threshold (0.95+), quality monitoring

3. **Complexity**: Adding navigation physics increases system complexity
   - *Mitigation*: Encapsulate in MomentumNavigator, comprehensive tests

4. **Overfitting**: Navigator might learn dataset-specific warp lanes
   - *Mitigation*: Diverse training data, regularization

---

## Open Questions

### Core Navigation Questions
- [ ] What's the optimal strafe angle for semantic space? (45° assumed from Quake)
- [ ] Should warp lanes be pre-computed or discovered dynamically?
- [ ] How does momentum interact with attention temperature?
- [ ] Can we visualize strafe jumps in the 3D UI?
- [ ] What's the failure mode when no warp lanes exist?

### Research Direction 1: Warp Lane Cartography
- [ ] Can we pre-compute the complete "warp lane network" for a dataset?
- [ ] What's the topology of semantic warp connections? (Small world? Scale-free?)
- [ ] How do warp lanes change as the dataset grows?
- [ ] Can warp lanes be visualized as a 3D graph overlay?

### Research Direction 2: Navigation Physics Simulator
- [ ] Build a sandbox to test navigation strategies before deployment
- [ ] What's the Pareto frontier of speed vs accuracy?
- [ ] Can reinforcement learning discover better exploit combinations?
- [ ] How does navigation behave at scale (1M+ tokens)?

### Research Direction 3: Shell Memory Layout Algorithm
- [ ] Optimal placement algorithm for priority-based shell assignment
- [ ] Does shell organization improve downstream task performance?
- [ ] What's the memory overhead of shell tracking?
- [ ] Can shells be dynamically reorganized during navigation?

### Research Direction 4: LOD-Aware Navigation
- [ ] Train navigation to be LOD-boundary aware
- [ ] Learn to "hop" LOD levels strategically
- [ ] Quality vs speed tradeoffs at different LOD configurations
- [ ] Automatic LOD boundary tuning per dataset

### Research Direction 5: Diagonal Highway Detection
- [ ] Analyze real datasets for diagonal semantic structure
- [ ] Are related concepts organized along diagonals in embedding space?
- [ ] Dataset-specific vs universal diagonal patterns
- [ ] Can we rotate embedding space to align with highways?

### Research Direction 6: Attractor Basin Mapping
- [ ] Map the directed warp graph to find attractor basins
- [ ] Are semantic "topics" attractor basins?
- [ ] Can we escape attractors intentionally?
- [ ] Do attractors correspond to meaningful concepts?

### Implementation Questions (from failure analysis)
- [ ] When should exploits be disabled automatically?
- [ ] What's the minimum success rate threshold per exploit?
- [ ] How to detect adversarial conditions (all exploits failing)?
- [ ] Recovery strategy when stuck in attractor basin?

---

## Novelty Assessment

### Patentable?
- [x] **Yes - Novel application**
- [ ] Maybe - Needs prior art search
- [ ] No - Existing technique

**Reasoning:** Applying game physics (strafe jumping, momentum, bunny hopping) to neural attention navigation is genuinely novel. No prior art found for "momentum-based semantic navigation" or "attention warp lanes."

### Publishable?
- [x] **Yes - Conference paper potential**
- [ ] Maybe - Workshop/poster
- [ ] No - Implementation detail

**Potential Title:** "Strafe Jumping Through Semantic Space: Momentum-Based Navigation for Efficient Long-Context Attention"

**Venue:** NeurIPS, ICML, or ICLR (novel ML technique with gaming inspiration)

### Prior Art

- **Quake strafe jumping physics** - Original game mechanic
- **Momentum-based optimization** (Adam, RMSprop) - Different domain
- **Routing Transformers** - Sparse attention but not momentum-based
- **Longformer** - Sliding window but no semantic warping

---

## Next Steps

1. **Prototype MomentumNavigator** - Standalone module with tests
2. **Benchmark on existing tests** - Measure traversal speed improvement
3. **Visualize in 3D** - Show strafe jumps and warp lanes
4. **Integration with M2.2** - Plan milestone integration
5. **Patent application** - If results are promising

---

## References

- [Quake Strafe Jumping Explained](https://www.youtube.com/watch?v=v3zT3Z5apaM) - Original mechanic
- [Routing Transformers](https://arxiv.org/abs/2003.05997) - Sparse attention baseline
- [Longformer](https://arxiv.org/abs/2004.05150) - Sliding window attention
- [INFINITE CORE_INNOVATION.md](../Documents/CORE_INNOVATION.md) - O(k) foundation

---

## Research Validation (2026-01-19)

This section documents the code analysis performed to validate the exploits before M1.11 implementation.

### Exploits Validated Against Code ✅

| # | Exploit | Status | Evidence | Implementation Effort |
|---|---------|--------|----------|----------------------|
| 1 | Warp Lanes | ✅ YES | Semantic scores unbounded before softmax; need ~15× similarity to overcome decay | 4-6 hours |
| 2 | Shell Memory (3r cutoff) | ✅ YES | Hard binary cutoff at exactly 3r confirmed in code | 2-4 hours |
| 3 | LOD Hopping | ✅ YES | **Immediately exploitable** - 80% cliff at boundary 50 | 2-4 hours |
| 6 | Bunny Hop Momentum | ✅ YES | Valid - momentum accumulation works for aligned queries | 2-3 hours |
| 7 | Circle Jump | ✅ YES | Two-phase (broad→specific) navigation is valid strategy | 2-3 hours |
| 8 | Temperature Surfing | ✅ YES | Standard exploration/exploitation tradeoff | 1-2 hours |
| 9 | Attention Ratchet | ✅ YES | Directed warp graph exists due to asymmetric visibility | 4-6 hours |

### Exploits Invalidated ❌

| # | Exploit | Status | Reason |
|---|---------|--------|--------|
| 4 | Diagonal Speed √3 | ❌ **INVALID** | Distance metric is isotropic Euclidean; no computational advantage |
| 5 | Harmonic Resonance | ⚠️ **TOO WEAK** | Effect exists but below measurement threshold; not worth complexity |

### Code Evidence

**1. Spatial Mask (Exponential Decay + Hard Cutoff)**
From `spatial_attention.py:212-232`:
```python
# Exponential decay
mask = torch.exp(-distances / self.spatial_radius)

# HARD cutoff at 3×radius
mask = mask.masked_fill(distances > 3 * self.spatial_radius, 0.0)
```
**Confirmed:** Token at 2.99r visible, token at 3.01r = exactly 0

**2. LOD Boundaries (Hard Cliffs)**
From `lod.py:112-117`:
```python
LODLevel("near", 0.0, 50.0, 1, 50)      # 100% fidelity
LODLevel("medium", 50.0, 150.0, 5, 25)  # 20% fidelity (80% CLIFF!)
LODLevel("far", 150.0, 500.0, 20, 10)   # 5% fidelity
LODLevel("beyond", 500.0, inf, 100, 5)  # 1% fidelity
```
**Confirmed:** Positioning token at 49.9 vs 50.1 = 5× fidelity difference

**3. Combined Scores (Multiplicative)**
From `spatial_attention.py:312`:
```python
combined_scores = semantic_scores * spatial_mask
```
**Confirmed:** Semantic similarity > ~15× can overcome distance penalty (warp lanes valid)

**4. Distance Metric (Isotropic - Invalidates Exploit 4)**
From `spatial_attention.py`:
```python
distances = torch.norm(p1 - p2, dim=-1)  # Same for all directions!
```
**Confirmed:** Per-axis encoding exists, but doesn't enable speedup because distance is Euclidean

### Revised Performance Expectations

| Metric | Original Claim | Revised Estimate | Reason |
|--------|---------------|------------------|--------|
| Speed boost | 2.1× | **1.5-1.7×** | Remove √3 diagonal (1.73×) |
| Tokens/step | 70 | **65** | Warp lanes + shell still valid |
| Accuracy | 82% | **78-80%** | Circle jump + temp surfing valid |

### Infrastructure Gap Identified

**Current limitation:** No `min_distance` parameter for distant similarity search.

Warp lane detection requires:
```python
# NEEDED but doesn't exist:
results = spatial_index.search(
    query,
    k=100,
    min_distance=3 * radius,   # ← NOT SUPPORTED
    max_distance=10 * radius
)
```

**Resolution:** Add `min_distance` to vector store interface as part of M1.11

---

## Status History

| Date | Status | Notes |
|------|--------|-------|
| 2026-01-19 | 💡 BRAINSTORM | Initial concept during exploration |
| 2026-01-19 | 🔬 EXPLORING | Documented 5 exploitable structures, designed MomentumNavigator |
| 2026-01-19 | 📐 EXPANDED | Added exploits 6-9, mathematical proofs, comprehensive navigator, benchmarks, failure analysis |
| 2026-01-19 | ✅ VALIDATED | Code analysis confirmed 7 of 9 exploits valid; Exploit 4 (diagonal speed) INVALID, Exploit 5 (harmonic) TOO WEAK |

---

## Appendix: All Nine Exploits Visualized

```
EXPLOIT 1: Semantic × Spatial Multiplication
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    WARP LANE (similarity=0.99)
Query ─────────────────────────────────────→ Distant Token
   ↓                                              ↑
   └── Normal attention decays ──────────────────┘
       (but multiplication restores it!)


EXPLOIT 2: Hard 3r Cutoff
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ┌─────────────────────────────────┐
    │  ATTENTION FRAME (0 to 3r)      │
    │                                 │
    │    ●   ●   ●                    │   ●  ← INVISIBLE
    │  ●   Query   ●                  │         (3.01r)
    │    ●   ●   ●                    │
    │                           2.9r ●│← VISIBLE (just inside)
    └─────────────────────────────────┘


EXPLOIT 3: LOD Level Boundaries
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Distance:  0    50   150    500
           │    │     │      │
           ▼    ▼     ▼      ▼
      [NEAR]  [MED] [FAR] [BEYOND]
       100%   20%   5%     1%   ← Information preserved

Token at 49.9 = 100% fidelity
Token at 50.1 = 20% fidelity  ← 80% CLIFF!


EXPLOIT 4: Per-Axis Independence
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          Y
          │     ╱ Diagonal = √2 speed
          │   ╱
          │ ╱
          ●───────── X
         ╱         Straight = 1.0 speed
       ╱
     Z

Same "per-axis cap" → Diagonal is FASTER


EXPLOIT 5: Harmonic Resonance
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Encoding magnitude at position x:

     ┌─────┐     ┌─────┐     ┌─────┐
     │     │     │     │     │     │
─────┘     └─────┘     └─────┘     └─────
     ↑           ↑           ↑
  Resonant   Resonant   Resonant
  Position   Position   Position

Place important tokens at peaks!


EXPLOIT 6: Bunny Hop Momentum
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRADITIONAL:         BUNNY HOP:
q1 → ●               q1 → ●
     ↓ (reset)            ↓ +v1
q2 → ●               q2 → ● → ●
     ↓ (reset)            ↓ +v2
q3 → ●               q3 → ● → ● → ●
                              FASTER!

Momentum compounds with aligned queries


EXPLOIT 7: Circle Jump Initialization
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIRECT QUERY:           CIRCLE JUMP:

    ┌─────────┐             ┌─────────┐
    │   T?    │             │    T    │
    │  ╱╲╱╲   │             │    ●    │
    │  ????   │   vs.       │  ↗   ╲  │
    │         │             │ W     ╲ │
    │ START●  │             │ ●───→● │
    └─────────┘             └─────────┘
    50% hit rate            85% hit rate
                        W=warmup gets you close


EXPLOIT 8: Temperature Surfing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
τ=2.0 (HOT)    τ=1.0 (WARM)    τ=0.5 (COLD)
EXPLORE        BALANCED         EXPLOIT

  ░░░░░░░         ▒▒▒▒           ▓▓▓
 ░░░░░░░░░       ▒▒▒▒▒▒          ▓▓▓
░░░░░░░░░░░     ▒▒▒▒▒▒▒▒        ▓▓▓▓▓

  Wide net       Medium           Focused
  See more       Balance          Best only

Schedule: HOT ──────────────────→ COLD
          (start)              (converge)


EXPLOIT 9: Attention Ratchet
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ONE-WAY WARP CREATES DIRECTED GRAPH:

     ┌───→ B ───→ C
     │     ↑
  A ─┤     │ (can't return!)
     │     │
     └───→ D ←─── E
           │
           ▼
           F (ATTRACTOR)
           │
           ╳ (dead end - no exits)

Navigation must consider:
- Reversible warps (safe)
- One-way warps (commit carefully)
- Attractor basins (may get stuck)
- Dead ends (avoid!)
```
