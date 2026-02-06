# Copyright 2025-2026 Adolfo Lopez (ch1pu)
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Adolfo Lopez (ch1pu) - github.com/ch1pu
# Project: INFINATE - Infinite Context Spatial AI (github.com/ch1pu/infinate)
#
# ============================================================================
# BUILT BY A U.S. NAVY VETERAN | BUILT IN TEXAS | OPEN FOR OPPORTUNITIES
# ============================================================================
# I'm actively seeking software engineering roles. If you're reading this code
# and like what you see, let's connect:
#   - GitHub: github.com/ch1pu
#   - Twitter/X: @2006_adolfo
#   - Project: This codebase demonstrates O(k) spatial attention, achieving
#     10,317x speedup over standard transformer attention with 89.58% test coverage.
# ============================================================================

"""
gpu_spatial_index.py - GPU-Resident Spatial Hash Index.

A PyTorch-native spatial hash grid that lives entirely on GPU VRAM.
Eliminates the O(n) CPU→GPU transfer bottleneck by keeping embeddings
GPU-resident and using spatial hashing for O(1) cell lookup + O(k) neighbor
retrieval.

Algorithm:
    1. load(): Hash all positions into cells via floor(position / cell_size)
       → 3D integer coords → single hash key. Sort tokens by hash key
       (groups same-cell tokens contiguously). Build CSR-style cell→offset
       lookup (cell_starts, cell_counts). All tensors stored on GPU.

    2. query(): Hash query position → query cell. Enumerate 27 neighbor
       cells (3×3×3 cube). Gather candidate indices from those cells.
       Compute distances. topk(k, largest=False) → return k nearest.

Performance:
    - Load: O(n log n) one-time sort (the "loading screen")
    - Query: O(1) cell lookup + O(candidates) distance + O(k log k) topk
    - With well-tuned cell_size, candidates ~ few hundred → effectively O(k)

Author: ch1pu (Adolfo Lopez)
Milestone: 1.11.5 - GPU-Resident Vector Store ("Loading Screen")
"""

from __future__ import annotations

import time

import torch

# Large prime for spatial hashing — reduces collisions in 3D grid
_HASH_PRIME_X = 73856093
_HASH_PRIME_Y = 19349663
_HASH_PRIME_Z = 83492791
_HASH_TABLE_SIZE = 1 << 20  # 1M buckets


class GPUSpatialIndex:
    """GPU-resident spatial hash index for O(k) neighbor queries.

    Stores embeddings and positions entirely on GPU VRAM. Uses spatial
    hashing to group nearby tokens, enabling fast neighbor lookups
    without brute-force distance computation over all n tokens.

    Args:
        cell_size: Size of each spatial hash cell. Tokens within one cell
            are considered immediate neighbors. Default 50.0 matches the
            LOD "near" radius.
        vram_budget_gb: Maximum VRAM budget in gigabytes. load() will
            reject if estimated usage exceeds this.
        device: CUDA device to store tensors on.

    Example:
        >>> index = GPUSpatialIndex(cell_size=50.0, device=torch.device("cuda"))
        >>> load_time = index.load(embeddings, positions)
        >>> emb, pos, idx = index.query(query_position, k=50)
    """

    def __init__(
        self,
        cell_size: float = 50.0,
        vram_budget_gb: float = 10.0,
        device: torch.device | None = None,
    ) -> None:
        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.cell_size = cell_size
        self.vram_budget_gb = vram_budget_gb
        self.device = device

        # Populated by load()
        self._embeddings: torch.Tensor | None = None
        self._positions: torch.Tensor | None = None
        self._sort_indices: torch.Tensor | None = None
        self._hash_keys: torch.Tensor | None = None
        self._cell_starts: torch.Tensor | None = None
        self._cell_counts: torch.Tensor | None = None
        self._n_tokens: int = 0

    def _estimate_vram_bytes(self, n: int, d_model: int) -> int:
        """Estimate VRAM usage for n tokens with d_model dimensions.

        Args:
            n: Number of tokens
            d_model: Embedding dimension

        Returns:
            Estimated bytes of VRAM needed
        """
        emb_bytes = n * d_model * 4  # float32
        pos_bytes = n * 3 * 4  # float32
        idx_bytes = n * 8  # int64
        hash_bytes = n * 8  # int64
        table_bytes = _HASH_TABLE_SIZE * 8 * 2  # starts + counts, int64
        return emb_bytes + pos_bytes + idx_bytes + hash_bytes + table_bytes

    def _hash_positions(self, positions: torch.Tensor) -> torch.Tensor:
        """Hash 3D positions into 1D bucket indices.

        Uses the standard spatial hashing formula with large primes
        to distribute 3D grid cells into a flat hash table.

        Args:
            positions: Positions tensor [n, 3]

        Returns:
            Hash keys tensor [n] with values in [0, _HASH_TABLE_SIZE)
        """
        cells = torch.floor(positions / self.cell_size).long()
        hashes = (
            cells[:, 0] * _HASH_PRIME_X ^ cells[:, 1] * _HASH_PRIME_Y ^ cells[:, 2] * _HASH_PRIME_Z
        )
        return hashes % _HASH_TABLE_SIZE

    def load(
        self,
        embeddings: torch.Tensor,
        positions: torch.Tensor,
    ) -> float:
        """Load embeddings and positions into GPU-resident spatial hash.

        This is the "loading screen" — a one-time O(n log n) operation
        that sorts tokens by spatial hash and builds the lookup table.
        After this, every query is O(k).

        Args:
            embeddings: Token embeddings [n, d_model] (any device)
            positions: Token positions [n, 3] (any device)

        Returns:
            Load time in seconds

        Raises:
            ValueError: If estimated VRAM exceeds budget
        """
        n, d_model = embeddings.shape

        # Check VRAM budget
        estimated_bytes = self._estimate_vram_bytes(n, d_model)
        estimated_gb = estimated_bytes / (1024**3)
        if estimated_gb > self.vram_budget_gb:
            raise ValueError(
                f"Estimated VRAM {estimated_gb:.2f} GB exceeds budget "
                f"{self.vram_budget_gb:.2f} GB for {n:,} tokens"
            )

        start = time.perf_counter()

        # Transfer to GPU
        gpu_embeddings = embeddings.to(self.device)
        gpu_positions = positions.to(self.device)

        # Hash all positions
        hash_keys = self._hash_positions(gpu_positions)

        # Sort by hash key — groups same-cell tokens contiguously
        sort_indices = torch.argsort(hash_keys)
        sorted_hashes = hash_keys[sort_indices]

        # Build CSR-style lookup: cell_starts[hash] and cell_counts[hash]
        cell_starts = torch.full((_HASH_TABLE_SIZE,), -1, dtype=torch.long, device=self.device)
        cell_counts = torch.zeros(_HASH_TABLE_SIZE, dtype=torch.long, device=self.device)

        # Count tokens per cell
        unique_hashes, counts = torch.unique(sorted_hashes, return_counts=True)
        cell_counts[unique_hashes] = counts

        # Find start offsets using cumsum
        # For each unique hash, find where it first appears in sorted order
        # Use searchsorted on the sorted hashes
        starts = torch.searchsorted(sorted_hashes, unique_hashes)
        cell_starts[unique_hashes] = starts

        # Store everything — sorted order for spatial locality
        self._embeddings = gpu_embeddings[sort_indices]
        self._positions = gpu_positions[sort_indices]
        self._sort_indices = sort_indices
        self._hash_keys = sorted_hashes
        self._cell_starts = cell_starts
        self._cell_counts = cell_counts
        self._n_tokens = n

        elapsed = time.perf_counter() - start
        return elapsed

    def query(
        self,
        query_position: torch.Tensor,
        k: int = 50,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Query k nearest neighbors using spatial hash lookup.

        O(1) cell lookup + O(candidates) distance + O(k log k) topk.
        With well-tuned cell_size, candidates are a few hundred at most.

        Args:
            query_position: Query position [3] (any device, will be moved)
            k: Number of nearest neighbors to return

        Returns:
            (embeddings [k, d_model], positions [k, 3], indices [k])
            where indices are into the original sorted order
        """
        assert self._embeddings is not None, "Index not loaded. Call load() first."

        query_pos = query_position.to(self.device)
        if query_pos.dim() == 0:
            query_pos = query_pos.unsqueeze(0)

        # Hash query position to find its cell
        query_cell = torch.floor(query_pos / self.cell_size).long()

        # Enumerate 27 neighbor cells (3×3×3 cube)
        offsets = torch.tensor(
            [[dx, dy, dz] for dx in range(-1, 2) for dy in range(-1, 2) for dz in range(-1, 2)],
            dtype=torch.long,
            device=self.device,
        )
        neighbor_cells = query_cell.unsqueeze(0) + offsets  # [27, 3]

        # Hash the 27 neighbor cells
        neighbor_hashes = (
            neighbor_cells[:, 0] * _HASH_PRIME_X
            ^ neighbor_cells[:, 1] * _HASH_PRIME_Y
            ^ neighbor_cells[:, 2] * _HASH_PRIME_Z
        ) % _HASH_TABLE_SIZE

        # Gather candidate indices from all neighbor cells
        candidate_indices_list = []
        for h in neighbor_hashes:
            h_val = h.item()
            start = self._cell_starts[h_val].item()
            count = self._cell_counts[h_val].item()
            if start >= 0 and count > 0:
                candidate_indices_list.append(
                    torch.arange(start, start + count, device=self.device)
                )

        if candidate_indices_list:
            candidates = torch.cat(candidate_indices_list)
        else:
            candidates = torch.tensor([], dtype=torch.long, device=self.device)

        k_actual = min(k, self._n_tokens)

        if len(candidates) >= k_actual:
            # Enough candidates from spatial hash — use them
            candidate_positions = self._positions[candidates]
            distances = torch.norm(candidate_positions - query_pos.unsqueeze(0), dim=-1)
            _, topk_local = torch.topk(distances, k_actual, largest=False)
            topk_idx = candidates[topk_local]
        else:
            # Not enough candidates in neighbor cells — fall back to brute force
            # This happens when query is far from data or cell_size is too small
            distances = torch.norm(self._positions - query_pos.unsqueeze(0), dim=-1)
            _, topk_idx = torch.topk(distances, k_actual, largest=False)

        return (
            self._embeddings[topk_idx],
            self._positions[topk_idx],
            topk_idx,
        )

    @property
    def token_count(self) -> int:
        """Number of tokens loaded in the index."""
        return self._n_tokens

    @property
    def vram_usage_mb(self) -> float:
        """Estimated VRAM usage in megabytes."""
        if self._embeddings is None:
            return 0.0

        total_bytes = 0
        for tensor in [
            self._embeddings,
            self._positions,
            self._sort_indices,
            self._hash_keys,
            self._cell_starts,
            self._cell_counts,
        ]:
            if tensor is not None:
                total_bytes += tensor.nelement() * tensor.element_size()

        return total_bytes / (1024 * 1024)

    @property
    def is_loaded(self) -> bool:
        """Whether the index has been loaded with data."""
        return self._embeddings is not None and self._n_tokens > 0
