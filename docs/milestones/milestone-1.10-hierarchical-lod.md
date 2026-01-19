# Milestone 1.10: Hierarchical Level-of-Detail (LOD) System

**Status:** 📋 PLANNED
**Estimated Duration:** 3-4 days (24-32 hours)
**Dependencies:** M1.3 (Spatial Attention), M1.4 (Spatial Transformer)
**Priority:** HIGH (Core Innovation - Open Source under Apache 2.0)
**License:** Apache 2.0 - Free to use, modify, and distribute

---

## Overview

This milestone implements a Hierarchical Level-of-Detail (LOD) system for context compression, applying techniques from computer graphics to AI semantic memory. Instead of a hard cutoff at k neighbors, LOD provides graceful degradation of detail with distance, enabling 100× more visible context for the same computational cost.

### The Problem

Current O(k) spatial attention has a **hard information cliff**:

```
Token 50:  ████████████ Full attention (weight: 0.02)
Token 51:  ░░░░░░░░░░░░ ZERO attention (weight: 0.00) ← Information lost!
```

### The Solution

Hierarchical LOD provides **smooth falloff** with distance-based compression:

```
NEAR (r < r1):      50 tokens at FULL detail
MEDIUM (r1-r2):     25 compressed tokens (represent 125 original) → 5:1
FAR (r2-r3):        10 compressed tokens (represent 200 original) → 20:1
BEYOND (r > r3):    5 metadata tokens (represent 5,000 original) → 100:1
                    ─────────────────────────────────────────────────────
TOTAL:              90 tokens represent 5,375 original = 60× compression
```

### Why This Matters

| Aspect | Current O(k) | With LOD |
|--------|--------------|----------|
| **Visible tokens** | k (e.g., 50) | k + compressed (e.g., 5,000+) |
| **Distant context** | Completely lost | Preserved (compressed) |
| **Information boundary** | Hard cliff | Smooth gradient |
| **Compute cost** | O(k) | O(k) (same!) |
| **Answer quality** | Good for local | Better for broad questions |

---

## Technical Design

### LOD Levels

```python
@dataclass
class LODLevel:
    name: str
    min_radius: float
    max_radius: float
    compression_ratio: int  # 1 = full, 5 = 5:1, etc.
    max_tokens: int

LOD_CONFIG = [
    LODLevel("near",   0.0,   50.0,  1,   50),   # Full detail
    LODLevel("medium", 50.0,  150.0, 5,   25),   # 5:1 compression
    LODLevel("far",    150.0, 500.0, 20,  10),   # 20:1 compression
    LODLevel("beyond", 500.0, inf,   100, 5),    # 100:1 metadata
]
```

### Core Algorithm

```python
class HierarchicalLOD:
    """Hierarchical Level-of-Detail for spatial attention."""

    def __init__(
        self,
        lod_config: list[LODLevel],
        compression_method: str = "cluster",  # "merge", "cluster", "learned"
        d_model: int = 768,
    ):
        self.lod_config = lod_config
        self.compression_method = compression_method
        self.d_model = d_model

        if compression_method == "learned":
            self.compressor = LODCompressor(d_model)

    def assign_lod_levels(
        self,
        query_position: torch.Tensor,  # [batch, 3]
        key_positions: torch.Tensor,   # [batch, n, 3]
    ) -> dict[str, torch.Tensor]:
        """Assign each token to an LOD level based on distance."""

        # Compute distances from query to all keys
        distances = torch.cdist(
            query_position.unsqueeze(1),  # [batch, 1, 3]
            key_positions                  # [batch, n, 3]
        ).squeeze(1)  # [batch, n]

        # Assign LOD levels
        lod_assignments = {}
        for level in self.lod_config:
            mask = (distances >= level.min_radius) & (distances < level.max_radius)
            lod_assignments[level.name] = mask

        return lod_assignments

    def compress_tokens(
        self,
        tokens: torch.Tensor,      # [batch, n, d_model]
        positions: torch.Tensor,   # [batch, n, 3]
        lod_level: LODLevel,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Compress tokens at a given LOD level."""

        if lod_level.compression_ratio == 1:
            # Full detail - no compression
            return tokens, positions

        if self.compression_method == "merge":
            return self._merge_compression(tokens, positions, lod_level)
        elif self.compression_method == "cluster":
            return self._cluster_compression(tokens, positions, lod_level)
        elif self.compression_method == "learned":
            return self._learned_compression(tokens, positions, lod_level)

    def _merge_compression(
        self,
        tokens: torch.Tensor,
        positions: torch.Tensor,
        lod_level: LODLevel,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Simple averaging of nearby tokens."""
        batch, n, d = tokens.shape
        ratio = lod_level.compression_ratio

        # Group tokens and average
        n_groups = min(n // ratio, lod_level.max_tokens)
        if n_groups == 0:
            return tokens[:, :1], positions[:, :1]

        # Reshape and mean
        group_size = n // n_groups
        tokens_grouped = tokens[:, :n_groups * group_size].view(batch, n_groups, group_size, d)
        positions_grouped = positions[:, :n_groups * group_size].view(batch, n_groups, group_size, 3)

        compressed_tokens = tokens_grouped.mean(dim=2)      # [batch, n_groups, d]
        compressed_positions = positions_grouped.mean(dim=2)  # [batch, n_groups, 3]

        return compressed_tokens, compressed_positions

    def _cluster_compression(
        self,
        tokens: torch.Tensor,
        positions: torch.Tensor,
        lod_level: LODLevel,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """K-means clustering to find representative tokens."""
        batch, n, d = tokens.shape
        n_clusters = min(n // lod_level.compression_ratio, lod_level.max_tokens)

        if n_clusters == 0:
            return tokens[:, :1], positions[:, :1]

        # Simple k-means (can be optimized with GPU implementation)
        compressed_tokens = []
        compressed_positions = []

        for b in range(batch):
            # Use position-based clustering
            centroids, assignments = self._kmeans(
                positions[b], n_clusters, max_iters=10
            )

            # Compute cluster representatives (mean of assigned tokens)
            cluster_tokens = torch.zeros(n_clusters, d, device=tokens.device)
            cluster_positions = torch.zeros(n_clusters, 3, device=positions.device)

            for c in range(n_clusters):
                mask = (assignments == c)
                if mask.sum() > 0:
                    cluster_tokens[c] = tokens[b, mask].mean(dim=0)
                    cluster_positions[c] = positions[b, mask].mean(dim=0)

            compressed_tokens.append(cluster_tokens)
            compressed_positions.append(cluster_positions)

        return torch.stack(compressed_tokens), torch.stack(compressed_positions)

    def _kmeans(
        self,
        positions: torch.Tensor,  # [n, 3]
        k: int,
        max_iters: int = 10,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Simple k-means clustering."""
        n = positions.shape[0]

        # Initialize centroids randomly
        indices = torch.randperm(n)[:k]
        centroids = positions[indices].clone()

        for _ in range(max_iters):
            # Assign to nearest centroid
            distances = torch.cdist(positions, centroids)
            assignments = distances.argmin(dim=1)

            # Update centroids
            new_centroids = torch.zeros_like(centroids)
            for c in range(k):
                mask = (assignments == c)
                if mask.sum() > 0:
                    new_centroids[c] = positions[mask].mean(dim=0)
                else:
                    new_centroids[c] = centroids[c]

            if torch.allclose(centroids, new_centroids):
                break
            centroids = new_centroids

        return centroids, assignments

    def forward(
        self,
        query: torch.Tensor,           # [batch, d_model]
        query_position: torch.Tensor,  # [batch, 3]
        keys: torch.Tensor,            # [batch, n, d_model]
        key_positions: torch.Tensor,   # [batch, n, 3]
        values: torch.Tensor,          # [batch, n, d_model]
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Apply hierarchical LOD to get multi-scale context.

        Returns:
            lod_keys: Compressed keys at all LOD levels
            lod_values: Compressed values at all LOD levels
            lod_positions: Compressed positions at all LOD levels
        """
        # Assign LOD levels
        lod_assignments = self.assign_lod_levels(query_position, key_positions)

        all_keys = []
        all_values = []
        all_positions = []

        for level in self.lod_config:
            mask = lod_assignments[level.name]

            # Extract tokens at this level
            level_keys = self._extract_masked(keys, mask)
            level_values = self._extract_masked(values, mask)
            level_positions = self._extract_masked(key_positions, mask)

            # Compress if needed
            compressed_keys, compressed_positions = self.compress_tokens(
                level_keys, level_positions, level
            )
            compressed_values, _ = self.compress_tokens(
                level_values, level_positions, level
            )

            all_keys.append(compressed_keys)
            all_values.append(compressed_values)
            all_positions.append(compressed_positions)

        # Concatenate all LOD levels
        lod_keys = torch.cat(all_keys, dim=1)
        lod_values = torch.cat(all_values, dim=1)
        lod_positions = torch.cat(all_positions, dim=1)

        return lod_keys, lod_values, lod_positions

    def _extract_masked(
        self,
        tensor: torch.Tensor,  # [batch, n, d]
        mask: torch.Tensor,    # [batch, n]
    ) -> torch.Tensor:
        """Extract tokens where mask is True, handling variable counts."""
        batch, n, d = tensor.shape
        max_count = mask.sum(dim=1).max().item()

        if max_count == 0:
            return torch.zeros(batch, 1, d, device=tensor.device)

        result = torch.zeros(batch, max_count, d, device=tensor.device)
        for b in range(batch):
            indices = mask[b].nonzero(as_tuple=True)[0]
            result[b, :len(indices)] = tensor[b, indices]

        return result
```

### Integration with SpatialAttention

```python
class SpatialAttentionWithLOD(nn.Module):
    """Spatial attention with hierarchical LOD."""

    def __init__(
        self,
        d_model: int = 768,
        n_heads: int = 12,
        spatial_radius: float = 50.0,
        lod_config: list[LODLevel] = None,
        compression_method: str = "cluster",
    ):
        super().__init__()

        self.spatial_attention = SpatialAttention(
            d_model=d_model,
            n_heads=n_heads,
            spatial_radius=spatial_radius,
        )

        self.lod = HierarchicalLOD(
            lod_config=lod_config or DEFAULT_LOD_CONFIG,
            compression_method=compression_method,
            d_model=d_model,
        )

    def forward(
        self,
        x: torch.Tensor,           # [batch, seq_len, d_model]
        positions: torch.Tensor,   # [batch, seq_len, 3]
    ) -> torch.Tensor:
        """Forward pass with LOD-enhanced attention."""

        batch, seq_len, d_model = x.shape
        outputs = []

        for i in range(seq_len):
            query = x[:, i]                    # [batch, d_model]
            query_pos = positions[:, i]        # [batch, 3]

            # Get LOD-compressed context
            lod_keys, lod_values, lod_positions = self.lod(
                query=query,
                query_position=query_pos,
                keys=x,
                key_positions=positions,
                values=x,
            )

            # Apply spatial attention over LOD-compressed context
            output = self.spatial_attention.single_query_attention(
                query=query,
                query_position=query_pos,
                keys=lod_keys,
                key_positions=lod_positions,
                values=lod_values,
            )

            outputs.append(output)

        return torch.stack(outputs, dim=1)
```

---

## Implementation Plan

### Day 1: LOD Level Assignment (6-8 hours)

**Phase 1.1: Core Data Structures**
```
□ Define LODLevel dataclass
□ Define LODConfig with default levels
□ Create HierarchicalLOD base class
□ Implement distance computation
□ Implement LOD level assignment
□ Write unit tests for assignment
```

**Deliverables:**
- `spatial_engine/core/lod.py` - LOD data structures
- `spatial_engine/core/tests/test_lod.py` - Unit tests
- LOD assignment working with 100% test coverage

### Day 2: Token Compression Methods (6-8 hours)

**Phase 1.2: Compression Implementations**
```
□ Implement merge compression (averaging)
□ Implement cluster compression (k-means)
□ Implement learned compression (autoencoder) - optional
□ Write unit tests for each method
□ Benchmark compression quality
```

**Deliverables:**
- Merge compression working
- Cluster compression working
- Tests for compression quality (semantic preservation)

### Day 3: Integration with SpatialAttention (6-8 hours)

**Phase 1.3: Attention Integration**
```
□ Create SpatialAttentionWithLOD class
□ Integrate LOD into attention forward pass
□ Handle variable-length LOD outputs
□ Ensure gradient flow through compression
□ Write integration tests
```

**Deliverables:**
- `spatial_engine/core/spatial_attention_lod.py`
- Integration tests passing
- End-to-end forward pass working

### Day 4: Testing & Benchmarks (6-8 hours)

**Phase 1.4: Validation & Documentation**
```
□ Write comprehensive test suite (20+ tests)
□ Benchmark: context expansion ratio
□ Benchmark: quality preservation
□ Benchmark: latency impact
□ Compare LOD vs pure O(k) on real queries
□ Documentation and code cleanup
```

**Deliverables:**
- Full test suite passing
- Benchmark results documented
- Quality metrics validated

---

## Test Plan

### Unit Tests (15 tests)

```python
class TestLODLevelAssignment:
    def test_near_level_assignment(self): ...
    def test_medium_level_assignment(self): ...
    def test_far_level_assignment(self): ...
    def test_beyond_level_assignment(self): ...
    def test_boundary_conditions(self): ...

class TestTokenCompression:
    def test_merge_compression_ratio(self): ...
    def test_merge_preserves_semantics(self): ...
    def test_cluster_compression_ratio(self): ...
    def test_cluster_finds_representatives(self): ...
    def test_compression_gradient_flow(self): ...

class TestHierarchicalLOD:
    def test_full_lod_pipeline(self): ...
    def test_lod_output_shapes(self): ...
    def test_lod_context_expansion(self): ...
    def test_lod_with_empty_levels(self): ...
    def test_lod_determinism(self): ...
```

### Integration Tests (10 tests)

```python
class TestSpatialAttentionWithLOD:
    def test_forward_pass_shapes(self): ...
    def test_attention_weights_sum_to_one(self): ...
    def test_lod_improves_context_coverage(self): ...
    def test_lod_vs_pure_ok_quality(self): ...
    def test_lod_latency_overhead(self): ...

class TestLODBenchmarks:
    def test_context_expansion_ratio(self): ...
    def test_compression_quality_near(self): ...
    def test_compression_quality_far(self): ...
    def test_scaling_with_context_size(self): ...
    def test_memory_usage(self): ...
```

### Expected Results

| Metric | Target | Notes |
|--------|--------|-------|
| Context expansion | 60-100× | 90 LOD tokens = 5,000+ original |
| Quality preservation (near) | >99% | Full detail maintained |
| Quality preservation (far) | >85% | Acceptable degradation |
| Latency overhead | <20% | Compression cost |
| Memory overhead | <50% | Additional LOD structures |

---

## Success Criteria

### Must Have
- [ ] LOD level assignment working correctly
- [ ] At least 2 compression methods (merge + cluster)
- [ ] Integration with SpatialAttention
- [ ] 25+ tests passing
- [ ] 90%+ code coverage
- [ ] Context expansion ≥50×

### Should Have
- [ ] Learned compression (autoencoder)
- [ ] GPU-optimized k-means
- [ ] Configurable LOD thresholds
- [ ] Benchmark suite

### Nice to Have
- [ ] Dynamic LOD adjustment based on query
- [ ] Attention visualization for LOD levels
- [ ] Integration with vector store

---

## Files to Create

```
backend/spatial_engine/core/
├── lod.py                      # LOD data structures and algorithms
├── spatial_attention_lod.py    # LOD-enhanced attention
└── tests/
    ├── test_lod.py             # LOD unit tests
    └── test_spatial_attention_lod.py  # Integration tests

backend/spatial_engine/benchmarks/
└── lod_benchmarks.py           # LOD performance benchmarks

docs/milestones/
└── milestone-1.10-hierarchical-lod.md  # This document
```

---

## Open Source & Innovation Context

This milestone implements **Innovation #3** from the original architecture - now released as open source under Apache 2.0.

**Hierarchical LOD for Context Compression**
- **Status:** Open Source (Apache 2.0 License)
- **Novelty:** Novel application of graphics technique to AI semantic memory
- **Prior Art:** LOD exists in graphics, but this is the first application to AI context

**Why This Is Significant:**
This innovation was originally valued at $1M-$5M as a patentable technology. By releasing it as open source, we're contributing a novel technique to the AI community that enables:

1. Distance-based LOD level assignment for AI context
2. Token compression methods (merge, cluster, learned)
3. Multi-scale attention over mixed LOD representations
4. Smooth information falloff (vs hard cutoff)

**The code and algorithms are free for anyone to use, modify, and build upon.**

---

## Comparison: Before vs After LOD

### Query: "How does authentication work?"

**Without LOD (Current O(k=50)):**
```
Visible: auth.py (50 tokens)
Hidden:  middleware.py, session.py, user_model.py, permissions.py, ...
Result:  Misses related context, narrow answer
```

**With LOD:**
```
NEAR:    auth.py full detail (50 tokens)
MEDIUM:  middleware.py, session.py summaries (25 tokens → 125 original)
FAR:     user_model.py, permissions.py overviews (10 tokens → 200 original)
BEYOND:  "database/, tests/" metadata (5 tokens → 5,000 original)
         ────────────────────────────────────────────────────────────
TOTAL:   90 tokens see 5,375 tokens of context
Result:  Comprehensive understanding, better answer
```

---

## Dependencies

### Required (Complete)
- [x] M1.3 Spatial Attention - Distance computation, attention mechanism
- [x] M1.4 Spatial Transformer - Integration point

### Optional (Helpful)
- [ ] M1.6 Vector Store - Could provide distant context for BEYOND level

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Compression loses important info | HIGH | MEDIUM | Validate with quality benchmarks |
| K-means too slow | MEDIUM | LOW | Use GPU implementation or simpler merge |
| Variable-length outputs complex | MEDIUM | MEDIUM | Pad to fixed size per level |
| Gradient flow through compression | HIGH | LOW | Use differentiable operations |

---

## References

### Internal Documents
- [CORE_INNOVATION.md](../../Documents/CORE_INNOVATION.md) - O(k) complexity foundation
- [milestone-1.3-spatial-attention.md](milestone-1.3-spatial-attention.md) - Base spatial attention
- [SOLO_DEVELOPER_MANIFESTO.md](../../MIT/SOLO_DEVELOPER_MANIFESTO.md) - Why this is open source

### External References
- Level of Detail (Computer Graphics) - Wikipedia
- "Efficient Transformers: A Survey" - Tay et al. 2020
- "Longformer: The Long-Document Transformer" - Beltagy et al. 2020

---

## Timeline

```
Day 1: LOD Level Assignment
       ├── Data structures
       ├── Distance computation
       ├── Level assignment
       └── Unit tests

Day 2: Token Compression
       ├── Merge compression
       ├── Cluster compression
       ├── Quality tests
       └── Benchmarks

Day 3: Integration
       ├── SpatialAttentionWithLOD
       ├── Forward pass
       ├── Gradient flow
       └── Integration tests

Day 4: Validation
       ├── Full test suite
       ├── Performance benchmarks
       ├── Documentation
       └── Code review
```

---

**Status:** 📋 PLANNED
**Next Action:** Begin Day 1 - LOD Level Assignment
**Estimated Start:** TBD
**Estimated Completion:** 3-4 days after start

---

**Author:** Adolfo Lopez (ch1pu)
**Created:** January 19, 2026
**Project:** INFINITE - O(k) Spatial Attention
**License:** Apache 2.0 - Open Source
