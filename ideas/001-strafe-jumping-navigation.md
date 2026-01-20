# Idea 001: Strafe Jumping Navigation

> **Exploit per-axis decoupling in spatial attention to achieve "impossible" navigation speeds—inspired by Quake's strafe jump physics**

**Status:** 🔬 EXPLORING
**Created:** 2026-01-19
**Author:** Adolfo Lopez (ch1pu)
**Potential Impact:** High (1.4× faster context traversal, patent potential)

---

## Summary

Quake's strafe jump exploits a bug where per-axis velocity caps are enforced independently, allowing diagonal movement to exceed intended limits. INFINITE's spatial attention has analogous exploitable structures: per-axis position handling, multiplication of semantic×spatial scores, and discrete LOD boundaries. By deliberately designing navigation that "strafe jumps" through these discontinuities, we can achieve faster-than-normal context traversal while maintaining attention quality.

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

### Exploitable Structure #4: Per-Axis Position Independence

```python
# Position encoding is computed per-axis
x_encoding = sinusoidal_encode(position[0], d_model // 3)
y_encoding = sinusoidal_encode(position[1], d_model // 3)
z_encoding = sinusoidal_encode(position[2], d_model // 3)
```

**The Exploit:** Each axis encoded independently. Diagonal movement = √3 × single axis movement in 3D.

**Application:** Axis-aligned highways—paths along diagonal directions cover more semantic space per step.

```python
# Diagonal movement covers more ground
straight_path = [(0,0,0), (1,0,0), (2,0,0), (3,0,0)]  # 3 units
diagonal_path = [(0,0,0), (1,1,1), (2,2,2), (3,3,3)]  # 5.2 units (√3 × 3)
```

### Exploitable Structure #5: Harmonic Encoding Resonance

```python
# Sinusoidal frequencies are logarithmic
freqs = torch.pow(10000, -torch.arange(0, d_model, 2) / d_model)
```

**The Exploit:** Some positions have encoding vectors with maximal magnitude across many frequency bands. These "resonant positions" have stronger representations.

**Application:** Position tokens at harmonic resonance points for stronger attention signals.

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

## Expected Benefits

| Metric | Current | Expected | Improvement |
|--------|---------|----------|-------------|
| Context traversal speed | 1.0× baseline | 1.4× | 40% faster |
| Tokens accessed per step | ~50 (k) | ~70 (k + warps) | 40% more context |
| Navigation efficiency | Linear paths | Diagonal + warps | Qualitative improvement |
| Distant context access | Hard cutoff | Semantic warps | New capability |

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

- [ ] What's the optimal strafe angle for semantic space? (45° assumed from Quake)
- [ ] Should warp lanes be pre-computed or discovered dynamically?
- [ ] How does momentum interact with attention temperature?
- [ ] Can we visualize strafe jumps in the 3D UI?
- [ ] What's the failure mode when no warp lanes exist?

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

## Status History

| Date | Status | Notes |
|------|--------|-------|
| 2026-01-19 | 💡 BRAINSTORM | Initial concept during exploration |
| 2026-01-19 | 🔬 EXPLORING | Documented 5 exploitable structures, designed MomentumNavigator |

---

## Appendix: The Five Exploits Visualized

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
```
