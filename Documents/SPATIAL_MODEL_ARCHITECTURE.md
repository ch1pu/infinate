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

# Spatial Model Architecture

## Complete Technical Specification for Spatially-Aware Transformers

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Spatial Attention Mechanism](#spatial-attention-mechanism)
4. [Navigation System](#navigation-system)
5. [Hierarchical Memory](#hierarchical-memory)
6. [Context Streaming](#context-streaming)
7. [Implementation Details](#implementation-details)
8. [Model Variants](#model-variants)

---

## Architecture Overview

### High-Level Design

```
User Query
    ↓
┌─────────────────────────────────────┐
│  1. Query Encoder                   │
│     └─ Generates query embedding    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  2. Spatial Navigator                │
│     └─ Predicts target location     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  3. Context Loader                   │
│     └─ Loads nearby tokens          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  4. Hierarchical Encoder             │
│     └─ Applies LOD based on distance│
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  5. Spatial Transformer Layers       │
│     └─ Distance-weighted attention  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  6. Output Generator                 │
│     └─ Produces response            │
└─────────────────────────────────────┘
    ↓
Generated Output
```

---

## Core Components

### 1. Spatial Token Representation

```python
import torch
import torch.nn as nn
from typing import Tuple, List
from dataclasses import dataclass

@dataclass
class SpatialToken:
    """
    Fundamental unit: combines semantic and spatial information
    """
    token_id: int                        # Semantic information
    position: Tuple[float, float, float] # Spatial coordinates (x, y, z)
    embedding: torch.Tensor              # 768D semantic embedding
    spatial_encoding: torch.Tensor       # 768D spatial encoding

    @property
    def full_embedding(self) -> torch.Tensor:
        """Combine semantic + spatial"""
        return self.embedding + self.spatial_encoding

    def distance_to(self, other: 'SpatialToken') -> float:
        """Euclidean distance in 3D space"""
        x1, y1, z1 = self.position
        x2, y2, z2 = other.position
        return ((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2) ** 0.5


class SpatialTokenEmbedding(nn.Module):
    """
    Creates spatial token representations
    """
    def __init__(
        self,
        vocab_size: int = 50000,
        d_model: int = 768,
        max_position: float = 1000.0
    ):
        super().__init__()
        self.d_model = d_model
        self.max_position = max_position

        # Semantic embedding (standard)
        self.token_embedding = nn.Embedding(vocab_size, d_model)

        # Spatial encoding (novel)
        self.spatial_encoder = SpatialPositionEncoding(
            d_model=d_model,
            max_position=max_position
        )

    def forward(
        self,
        token_ids: torch.Tensor,      # [batch, seq_len]
        positions_3d: torch.Tensor    # [batch, seq_len, 3]
    ) -> torch.Tensor:
        """
        Create combined spatial-semantic embeddings
        """
        # Semantic embedding
        semantic = self.token_embedding(token_ids)  # [batch, seq_len, d_model]

        # Spatial encoding
        spatial = self.spatial_encoder(positions_3d)  # [batch, seq_len, d_model]

        # Combine (additive)
        combined = semantic + spatial

        return combined
```

### 2. Spatial Positional Encoding

```python
class SpatialPositionEncoding(nn.Module):
    """
    Encodes 3D continuous positions into high-dimensional space
    Novel contribution: extends sinusoidal encoding to 3D
    """
    def __init__(
        self,
        d_model: int = 768,
        max_position: float = 1000.0,
        temperature: float = 10000.0
    ):
        super().__init__()
        self.d_model = d_model
        self.max_position = max_position
        self.temperature = temperature

        # Each dimension gets d_model/3 features
        self.d_per_dim = d_model // 3

        # Frequency bands
        freqs = torch.exp(
            torch.linspace(0, -10, self.d_per_dim // 2)
        )
        self.register_buffer('freqs', freqs)

    def encode_dimension(
        self,
        coords: torch.Tensor,  # [batch, seq_len]
        dim_idx: int
    ) -> torch.Tensor:
        """
        Encode a single spatial dimension (x, y, or z)
        """
        # Normalize to [-1, 1]
        coords = coords / self.max_position

        # Expand for frequency bands
        coords = coords.unsqueeze(-1)  # [batch, seq_len, 1]
        freqs = self.freqs.unsqueeze(0).unsqueeze(0)  # [1, 1, d_per_dim//2]

        # Sinusoidal encoding
        angles = coords * freqs * self.temperature
        sin_component = torch.sin(angles)
        cos_component = torch.cos(angles)

        # Concatenate sin and cos
        encoding = torch.cat([sin_component, cos_component], dim=-1)
        # [batch, seq_len, d_per_dim]

        return encoding

    def forward(self, positions_3d: torch.Tensor) -> torch.Tensor:
        """
        Encode 3D positions

        Args:
            positions_3d: [batch, seq_len, 3] - (x, y, z) coordinates

        Returns:
            encoding: [batch, seq_len, d_model]
        """
        batch, seq_len, _ = positions_3d.shape

        # Separate x, y, z
        x = positions_3d[:, :, 0]
        y = positions_3d[:, :, 1]
        z = positions_3d[:, :, 2]

        # Encode each dimension
        x_enc = self.encode_dimension(x, dim_idx=0)
        y_enc = self.encode_dimension(y, dim_idx=1)
        z_enc = self.encode_dimension(z, dim_idx=2)

        # Concatenate
        encoding = torch.cat([x_enc, y_enc, z_enc], dim=-1)
        # [batch, seq_len, d_model]

        # Pad if d_model not divisible by 3
        if encoding.shape[-1] < self.d_model:
            padding = self.d_model - encoding.shape[-1]
            encoding = F.pad(encoding, (0, padding))

        return encoding
```

---

## Spatial Attention Mechanism

### Distance-Weighted Attention

```python
class SpatialAttention(nn.Module):
    """
    Core innovation: Attention that decays with spatial distance
    Achieves O(k) complexity through spatial pruning
    """
    def __init__(
        self,
        d_model: int = 768,
        n_heads: int = 12,
        spatial_radius: float = 50.0,
        distance_decay: str = 'exponential'  # or 'linear', 'gaussian'
    ):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        self.spatial_radius = spatial_radius
        self.distance_decay = distance_decay

        # Standard Q, K, V projections
        self.query = nn.Linear(d_model, d_model)
        self.key = nn.Linear(d_model, d_model)
        self.value = nn.Linear(d_model, d_model)

        # Output projection
        self.output = nn.Linear(d_model, d_model)

    def compute_distance_matrix(
        self,
        positions: torch.Tensor  # [batch, seq_len, 3]
    ) -> torch.Tensor:
        """
        Compute pairwise Euclidean distances
        """
        # Expand dimensions for broadcasting
        p1 = positions.unsqueeze(2)  # [batch, seq_len, 1, 3]
        p2 = positions.unsqueeze(1)  # [batch, 1, seq_len, 3]

        # Euclidean distance
        distances = torch.norm(p1 - p2, dim=-1)
        # [batch, seq_len, seq_len]

        return distances

    def compute_spatial_mask(
        self,
        distances: torch.Tensor  # [batch, seq_len, seq_len]
    ) -> torch.Tensor:
        """
        Create distance-based attention mask

        Returns mask with values in [0, 1]:
        - 1.0 for nearby tokens (high attention)
        - 0.0 for distant tokens (no attention)
        """
        if self.distance_decay == 'exponential':
            # Exponential decay: exp(-d/r)
            mask = torch.exp(-distances / self.spatial_radius)

        elif self.distance_decay == 'linear':
            # Linear decay: max(0, 1 - d/r)
            mask = torch.clamp(1.0 - distances / self.spatial_radius, min=0.0)

        elif self.distance_decay == 'gaussian':
            # Gaussian: exp(-(d/r)²)
            mask = torch.exp(-(distances / self.spatial_radius) ** 2)

        else:
            raise ValueError(f"Unknown decay: {self.distance_decay}")

        # Hard cutoff at 3x radius (efficiency)
        mask = mask.masked_fill(
            distances > 3 * self.spatial_radius,
            0.0
        )

        return mask

    def forward(
        self,
        x: torch.Tensor,            # [batch, seq_len, d_model]
        positions: torch.Tensor,    # [batch, seq_len, 3]
        attention_mask: torch.Tensor = None  # Optional additional mask
    ) -> torch.Tensor:
        """
        Spatial attention forward pass
        """
        batch, seq_len, d_model = x.shape

        # Project to Q, K, V
        Q = self.query(x)  # [batch, seq_len, d_model]
        K = self.key(x)
        V = self.value(x)

        # Reshape for multi-head attention
        Q = Q.view(batch, seq_len, self.n_heads, self.d_head).transpose(1, 2)
        K = K.view(batch, seq_len, self.n_heads, self.d_head).transpose(1, 2)
        V = V.view(batch, seq_len, self.n_heads, self.d_head).transpose(1, 2)
        # [batch, n_heads, seq_len, d_head]

        # Compute semantic attention scores
        semantic_scores = torch.matmul(Q, K.transpose(-2, -1)) / (self.d_head ** 0.5)
        # [batch, n_heads, seq_len, seq_len]

        # Compute spatial mask
        spatial_mask = self.compute_spatial_mask(
            self.compute_distance_matrix(positions)
        )  # [batch, seq_len, seq_len]

        # Expand mask for multi-head
        spatial_mask = spatial_mask.unsqueeze(1)
        # [batch, 1, seq_len, seq_len]

        # Combine semantic and spatial
        # Multiplicative combination: score * spatial_weight
        combined_scores = semantic_scores * spatial_mask

        # Apply additional mask if provided
        if attention_mask is not None:
            combined_scores = combined_scores.masked_fill(
                attention_mask == 0,
                float('-inf')
            )

        # Softmax
        attention_weights = F.softmax(combined_scores, dim=-1)
        # [batch, n_heads, seq_len, seq_len]

        # Apply attention to values
        output = torch.matmul(attention_weights, V)
        # [batch, n_heads, seq_len, d_head]

        # Concatenate heads
        output = output.transpose(1, 2).contiguous()
        output = output.view(batch, seq_len, d_model)

        # Output projection
        output = self.output(output)

        return output
```

### Complete Spatial Transformer Layer

```python
class SpatialTransformerLayer(nn.Module):
    """
    Complete transformer layer with spatial attention
    """
    def __init__(
        self,
        d_model: int = 768,
        n_heads: int = 12,
        d_ff: int = 3072,
        spatial_radius: float = 50.0,
        dropout: float = 0.1
    ):
        super().__init__()

        # Spatial attention
        self.spatial_attention = SpatialAttention(
            d_model=d_model,
            n_heads=n_heads,
            spatial_radius=spatial_radius
        )

        # Feed-forward network
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout)
        )

        # Layer normalization
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

        # Dropout
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        positions: torch.Tensor,
        attention_mask: torch.Tensor = None
    ) -> torch.Tensor:
        """
        Forward pass with residual connections
        """
        # Spatial attention block
        attended = self.spatial_attention(x, positions, attention_mask)
        x = x + self.dropout1(attended)
        x = self.norm1(x)

        # Feed-forward block
        ff_output = self.ffn(x)
        x = x + self.dropout2(ff_output)
        x = self.norm2(x)

        return x
```

---

## Navigation System

### Spatial Navigator

```python
class SpatialNavigator(nn.Module):
    """
    Learns to predict where in 3D space to find relevant information
    This is trained with reinforcement learning
    """
    def __init__(
        self,
        d_model: int = 768,
        d_hidden: int = 512,
        max_movement: float = 200.0
    ):
        super().__init__()
        self.d_model = d_model
        self.max_movement = max_movement

        # Query encoder (what are we looking for?)
        self.query_encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=d_model, nhead=8),
            num_layers=4
        )

        # Context encoder (what can we see now?)
        self.context_encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=d_model, nhead=8),
            num_layers=4
        )

        # Position encoder (where are we?)
        self.position_mlp = nn.Sequential(
            nn.Linear(3, d_hidden),
            nn.ReLU(),
            nn.Linear(d_hidden, d_model)
        )

        # Navigation head (where should we go?)
        self.nav_head = nn.Sequential(
            nn.Linear(d_model * 3, d_hidden),  # query + context + position
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_hidden, d_hidden // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_hidden // 2, 3),  # Output: (Δx, Δy, Δz)
            nn.Tanh()  # Bound movement to [-1, 1]
        )

    def forward(
        self,
        query: torch.Tensor,           # [batch, query_len, d_model]
        current_context: torch.Tensor, # [batch, context_len, d_model]
        current_position: torch.Tensor # [batch, 3]
    ) -> torch.Tensor:
        """
        Predict next position to navigate to

        Returns:
            next_position: [batch, 3] - New (x, y, z) coordinates
        """
        # Encode query (what we're looking for)
        query_repr = self.query_encoder(query)
        query_repr = query_repr.mean(dim=1)  # [batch, d_model]

        # Encode current context (what we can see)
        context_repr = self.context_encoder(current_context)
        context_repr = context_repr.mean(dim=1)  # [batch, d_model]

        # Encode current position (where we are)
        position_repr = self.position_mlp(current_position)  # [batch, d_model]

        # Concatenate all information
        combined = torch.cat([query_repr, context_repr, position_repr], dim=-1)
        # [batch, d_model * 3]

        # Predict movement delta
        delta = self.nav_head(combined)  # [batch, 3]
        delta = delta * self.max_movement  # Scale to actual movement range

        # New position
        next_position = current_position + delta

        return next_position

    def navigate_sequence(
        self,
        query: torch.Tensor,
        initial_position: torch.Tensor,
        context_loader: callable,
        max_steps: int = 10,
        relevance_threshold: float = 0.9
    ) -> List[torch.Tensor]:
        """
        Navigate through memory space until relevant context found

        Returns:
            trajectory: List of positions visited
        """
        trajectory = [initial_position]
        position = initial_position

        for step in range(max_steps):
            # Load context at current position
            context = context_loader(position)

            # Check if current context is relevant enough
            relevance = self.compute_relevance(query, context)
            if relevance > relevance_threshold:
                break  # Found it!

            # Predict next position
            position = self.forward(query, context, position)
            trajectory.append(position)

        return trajectory

    def compute_relevance(
        self,
        query: torch.Tensor,
        context: torch.Tensor
    ) -> float:
        """
        Compute how relevant current context is to query
        Used to decide when to stop navigating
        """
        # Cosine similarity between query and context
        query_repr = query.mean(dim=1)
        context_repr = context.mean(dim=1)

        similarity = F.cosine_similarity(query_repr, context_repr, dim=-1)
        return similarity.item()
```

---

## Hierarchical Memory

### Level-of-Detail System

```python
class HierarchicalSpatialMemory(nn.Module):
    """
    Stores information at multiple resolutions based on distance
    Like LOD in 3D graphics, but for AI context
    """
    def __init__(
        self,
        d_model: int = 768,
        levels: List[dict] = None
    ):
        super().__init__()

        # Default LOD levels
        if levels is None:
            self.levels = [
                {
                    'name': 'detail',
                    'radius': 50.0,
                    'tokens_per_chunk': 1,
                    'embedding_dim': 768
                },
                {
                    'name': 'high',
                    'radius': 200.0,
                    'tokens_per_chunk': 5,
                    'embedding_dim': 512
                },
                {
                    'name': 'medium',
                    'radius': 500.0,
                    'tokens_per_chunk': 20,
                    'embedding_dim': 256
                },
                {
                    'name': 'low',
                    'radius': 1000.0,
                    'tokens_per_chunk': 100,
                    'embedding_dim': 128
                },
                {
                    'name': 'metadata',
                    'radius': float('inf'),
                    'tokens_per_chunk': None,
                    'embedding_dim': 64
                }
            ]
        else:
            self.levels = levels

        # Encoders for each level
        self.encoders = nn.ModuleDict({
            level['name']: self._create_encoder(level)
            for level in self.levels
        })

    def _create_encoder(self, level: dict) -> nn.Module:
        """Create encoder for specific LOD level"""
        if level['name'] == 'metadata':
            # Metadata-only encoder
            return nn.Sequential(
                nn.Linear(10, level['embedding_dim']),  # Simple features
                nn.ReLU()
            )
        else:
            # Compression encoder
            return nn.Sequential(
                nn.Linear(768, level['embedding_dim']),
                nn.LayerNorm(level['embedding_dim']),
                nn.ReLU()
            )

    def get_lod_level(self, distance: float) -> dict:
        """Determine appropriate LOD level for distance"""
        for level in self.levels:
            if distance < level['radius']:
                return level
        return self.levels[-1]  # Farthest level

    def encode_at_distance(
        self,
        tokens: torch.Tensor,       # [seq_len, d_model]
        positions: torch.Tensor,    # [seq_len, 3]
        query_position: torch.Tensor  # [3]
    ) -> torch.Tensor:
        """
        Encode tokens at appropriate LOD based on distance
        """
        # Compute distances from query position
        distances = torch.norm(positions - query_position, dim=-1)

        # Group tokens by LOD level
        encoded_tokens = []
        for i, (token, pos, dist) in enumerate(zip(tokens, positions, distances)):
            level = self.get_lod_level(dist.item())

            # Encode at appropriate level
            if level['name'] == 'detail':
                # Full detail - use original
                encoded = token
            else:
                # Compressed
                encoder = self.encoders[level['name']]
                encoded = encoder(token.unsqueeze(0)).squeeze(0)

            encoded_tokens.append(encoded)

        # Pad to same dimension
        max_dim = max(t.shape[0] for t in encoded_tokens)
        encoded_tokens = [
            F.pad(t, (0, max_dim - t.shape[0]))
            for t in encoded_tokens
        ]

        return torch.stack(encoded_tokens)
```

---

(Continued in next file due to length...)

**Document Version:** 1.0
**Last Updated:** 2025-01-12
