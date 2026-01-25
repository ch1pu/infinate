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

# INFINITE: Hardware Architecture & Optimization

**Multi-Device Acceleration Strategy for Spatial AI Engine**

**Version:** 1.0
**Last Updated:** December 1, 2025
**Author:** ch1pu (System Architect)
**Status:** Architecture Complete

---

## Executive Summary

INFINITE leverages a sophisticated multi-hardware architecture to achieve optimal performance for spatial AI workloads. By distributing tasks across NPU, iGPU, dGPU, and CPU based on their strengths, we maximize throughput while minimizing latency.

**Key Insight:** Different AI workloads have different computational characteristics. NPUs excel at INT8 matrix operations, GPUs at FP16 tensor math, and CPUs at complex control flow and memory access patterns.

---

## Table of Contents

1. [Hardware Overview](#1-hardware-overview)
2. [Device Task Distribution](#2-device-task-distribution)
3. [NPU Architecture (XDNA 2)](#3-npu-architecture-xdna-2)
4. [GPU Architecture](#4-gpu-architecture)
5. [CPU Architecture (Zen 5)](#5-cpu-architecture-zen-5)
6. [Memory Architecture](#6-memory-architecture)
7. [Device Communication](#7-device-communication)
8. [Performance Optimization](#8-performance-optimization)
9. [Power Management](#9-power-management)
10. [Fallback Strategies](#10-fallback-strategies)

---

## 1. Hardware Overview

### 1.1 Primary Platform: AMD AI Max 350 (Strix Halo)

```
+================================================================+
|                    AMD AI Max 350 (Strix Halo)                  |
+================================================================+
|                                                                  |
|  +---------------------------+   +---------------------------+  |
|  |        CPU: Zen 5         |   |        NPU: XDNA 2        |  |
|  +---------------------------+   +---------------------------+  |
|  | - 8 cores / 16 threads    |   | - 50 TOPS (INT8)          |  |
|  | - Up to 5.2 GHz boost     |   | - 16-bit brain float      |  |
|  | - 32MB L3 cache           |   | - 128 AI Engine tiles     |  |
|  | - DDR5-6400 support       |   | - Dedicated AI memory     |  |
|  | - PCIe 5.0 lanes          |   | - ONNX Runtime support    |  |
|  +---------------------------+   +---------------------------+  |
|                                                                  |
|  +---------------------------+                                  |
|  |   iGPU: Radeon 890M       |                                  |
|  +---------------------------+                                  |
|  | - 40 Compute Units        |                                  |
|  | - RDNA 3.5 architecture   |                                  |
|  | - 2.9 GHz boost clock     |                                  |
|  | - Hardware ray tracing    |                                  |
|  | - WebGPU/Vulkan support   |                                  |
|  | - AV1 encode/decode       |                                  |
|  +---------------------------+                                  |
|                                                                  |
|  System Memory: 64GB DDR5-6400                                  |
|  - Unified memory architecture                                   |
|  - Shared between CPU, NPU, iGPU                                |
|                                                                  |
+================================================================+
```

### 1.2 Optional Discrete GPU: RTX 5060

```
+================================================================+
|                    NVIDIA RTX 5060                               |
+================================================================+
|                                                                  |
|  +----------------------------------------------------------+  |
|  |                   Ada Lovelace Architecture               |  |
|  +----------------------------------------------------------+  |
|  | - 16GB GDDR6X VRAM                                        |  |
|  | - 4th Gen Tensor Cores                                    |  |
|  | - 3rd Gen RT Cores                                        |  |
|  | - ~12 TFLOPS FP32                                         |  |
|  | - ~200 TOPS INT8 (Tensor)                                 |  |
|  | - CUDA 12.x support                                       |  |
|  | - PCIe 4.0 x16                                            |  |
|  +----------------------------------------------------------+  |
|                                                                  |
|  Memory Bandwidth: ~300 GB/s                                    |
|  TDP: ~150W                                                      |
|                                                                  |
+================================================================+
```

### 1.3 Hardware Selection Rationale

| Component | Selection | Reason |
|-----------|-----------|--------|
| **NPU** | AMD XDNA 2 (50 TOPS) | Power-efficient embeddings, always-on |
| **iGPU** | Radeon 890M (40 CUs) | Dedicated 3D rendering, no VRAM contention |
| **dGPU** | RTX 5060 (16GB) | Large VRAM for LLMs, Tensor Cores for attention |
| **CPU** | Zen 5 (8 cores) | Fast single-thread for indexing, orchestration |
| **RAM** | 64GB DDR5-6400 | Large octree, context buffers, LLM offload |

---

## 2. Device Task Distribution

### 2.1 Workload Assignment Matrix

```
+------------------------------------------------------------------+
|                    WORKLOAD ASSIGNMENT                            |
+------------------------------------------------------------------+
|                                                                    |
|  Workload                    Primary    Secondary   Fallback      |
|  --------                    -------    ---------   --------      |
|                                                                    |
|  Embedding Generation        NPU        dGPU        CPU           |
|  (BGE-small, 384D)          <5ms       <10ms       <50ms          |
|                                                                    |
|  Spatial Attention           dGPU       NPU*        CPU           |
|  (O(k) mechanism)           <50ms      <100ms      <500ms         |
|                                                                    |
|  LLM Inference               dGPU       CPU*        N/A           |
|  (7B-8B models)             ~2s        ~10s        -              |
|                                                                    |
|  3D Rendering                iGPU       dGPU*       CPU           |
|  (Three.js/WebGPU)          16ms       16ms        slow           |
|                                                                    |
|  Octree Indexing             CPU        N/A         N/A           |
|  (Spatial queries)          <5ms       -           -              |
|                                                                    |
|  API Handling                CPU        N/A         N/A           |
|  (Node.js async)            <10ms      -           -              |
|                                                                    |
|  Context Streaming           CPU+SSD    N/A         N/A           |
|  (Sequential I/O)           <50ms      -           -              |
|                                                                    |
|  * = Non-optimal but functional                                   |
|                                                                    |
+------------------------------------------------------------------+
```

### 2.2 Hardware Selection Logic

```python
class HardwareSelector:
    """Dynamically select optimal hardware for each task"""

    def __init__(self):
        self.npu_available = self._detect_npu()
        self.dgpu_available = self._detect_dgpu()
        self.igpu_available = self._detect_igpu()

    def select_for_embedding(self, batch_size: int) -> str:
        """
        NPU: Best for small batches (1-32)
        dGPU: Better for large batches (32+)
        CPU: Fallback
        """
        if self.npu_available and batch_size <= 32:
            return 'npu'
        elif self.dgpu_available:
            return 'dgpu'
        else:
            return 'cpu'

    def select_for_attention(self, seq_length: int) -> str:
        """
        dGPU: Best for all sequence lengths (Tensor Cores)
        NPU: Acceptable for small sequences
        CPU: Emergency fallback only
        """
        if self.dgpu_available:
            return 'dgpu'
        elif self.npu_available and seq_length <= 512:
            return 'npu'
        else:
            return 'cpu'

    def select_for_llm(self, model_size: str) -> str:
        """
        dGPU: Required for reasonable inference speed
        CPU: Extremely slow but possible
        """
        if self.dgpu_available:
            return 'dgpu'
        else:
            return 'cpu'  # Warning: ~5x slower

    def _detect_npu(self) -> bool:
        try:
            import onnxruntime as ort
            return 'VitisAIExecutionProvider' in ort.get_available_providers()
        except:
            return False

    def _detect_dgpu(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False

    def _detect_igpu(self) -> bool:
        # Check for AMD iGPU via Mesa/Vulkan
        import subprocess
        result = subprocess.run(['vulkaninfo'], capture_output=True, text=True)
        return 'AMD Radeon' in result.stdout
```

### 2.3 Task Distribution Diagram

```
USER REQUEST
     |
     v
+----+----+
| Router  |
+----+----+
     |
     +--------------------+--------------------+
     |                    |                    |
     v                    v                    v
+---------+         +-----------+        +---------+
| FAST    |         | COMPUTE   |        | RENDER  |
| PATH    |         | PATH      |        | PATH    |
+---------+         +-----------+        +---------+
     |                    |                    |
     v                    v                    v
+----+----+         +-----+-----+        +----+----+
| NPU     |         | dGPU      |        | iGPU    |
| XDNA 2  |         | RTX 5060  |        | Radeon  |
+---------+         +-----------+        +---------+
|         |         |           |        |         |
| Embed   |         | Attention |        | 3D      |
| <5ms    |         | <50ms     |        | 16ms    |
|         |         |           |        |         |
| Small   |         | LLM       |        | 60 FPS  |
| inference|        | ~2s       |        |         |
+---------+         +-----------+        +---------+
     |                    |                    |
     +--------------------+--------------------+
                         |
                         v
                    RESPONSE
```

---

## 3. NPU Architecture (XDNA 2)

### 3.1 XDNA 2 Overview

AMD's XDNA 2 (Neural Processing Unit) is a dedicated AI accelerator optimized for:
- INT8 matrix multiplication (50 TOPS)
- 16-bit brain float operations
- Low-power inference (<10W TDP)
- Real-time embedding generation

### 3.2 NPU Programming Model

```python
# NPU access via ONNX Runtime with VitisAI provider

import onnxruntime as ort
import numpy as np

class NPUEmbeddingGenerator:
    """Generate embeddings using AMD XDNA 2 NPU"""

    def __init__(self, model_path: str):
        # Configure NPU execution
        providers = [
            ('VitisAIExecutionProvider', {
                'target': 'DPUCZDX8G',  # XDNA 2 target
                'config_file': 'config.json'
            }),
            ('CPUExecutionProvider', {})  # Fallback
        ]

        self.session = ort.InferenceSession(
            model_path,
            providers=providers
        )

        # Verify NPU is being used
        active_provider = self.session.get_providers()[0]
        print(f"Using provider: {active_provider}")

    def generate(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for text batch"""
        # Tokenize
        input_ids, attention_mask = self.tokenize(texts)

        # Run on NPU
        outputs = self.session.run(
            None,  # All outputs
            {
                'input_ids': input_ids.astype(np.int64),
                'attention_mask': attention_mask.astype(np.int64)
            }
        )

        # Mean pooling
        embeddings = outputs[0].mean(axis=1)

        # L2 normalize
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        return embeddings
```

### 3.3 NPU Model Optimization

```bash
# Quantize model for NPU (INT8)

# 1. Export to ONNX
python export_onnx.py --model BAAI/bge-small-en-v1.5 --output bge-small.onnx

# 2. Quantize with VitisAI
vai_q_onnx \
    --model bge-small.onnx \
    --output bge-small-int8.onnx \
    --calibration_dataset calibration_data.npy \
    --quantization_type int8

# 3. Compile for XDNA 2
vai_c_xdna \
    --model bge-small-int8.onnx \
    --output bge-small-xdna.xmodel \
    --target DPUCZDX8G
```

### 3.4 NPU Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| **Peak TOPS** | 50 (INT8) | Matrix multiplication |
| **Power** | <10W TDP | Always-on capability |
| **Latency** | <5ms | Single embedding |
| **Throughput** | 200+ emb/s | Batched (32) |
| **Memory** | Shared DDR5 | Zero-copy with CPU |

### 3.5 NPU Use Cases in INFINITE

1. **Real-time embedding generation**
   - User queries -> embeddings (<5ms)
   - New code chunks -> spatial positions
   - Search queries -> semantic navigation

2. **Small model inference**
   - Classification heads
   - Similarity scoring
   - Quick reranking

3. **Preprocessing**
   - Input validation
   - Token counting
   - Feature extraction

---

## 4. GPU Architecture

### 4.1 Integrated GPU (Radeon 890M)

**Role:** Dedicated 3D rendering for visualization

```
RADEON 890M ARCHITECTURE
========================

+--------------------------------------------------+
|                 RDNA 3.5 Architecture             |
|                                                   |
|  +--------------------------------------------+  |
|  |            40 Compute Units                |  |
|  |                                            |  |
|  |  +------+  +------+  +------+  +------+   |  |
|  |  | CU0  |  | CU1  |  |  ... |  | CU39 |   |  |
|  |  +------+  +------+  +------+  +------+   |  |
|  |                                            |  |
|  |  Each CU: 64 stream processors             |  |
|  |  Total: 2560 stream processors             |  |
|  +--------------------------------------------+  |
|                                                   |
|  +--------------------------------------------+  |
|  |              Ray Accelerators              |  |
|  |  - Hardware RT for soft shadows            |  |
|  |  - Used for ambient occlusion in 3D view   |  |
|  +--------------------------------------------+  |
|                                                   |
|  Memory: Shared with system (up to 8GB)          |
|  Boost Clock: 2.9 GHz                            |
|  Compute: ~8 TFLOPS FP32                         |
|                                                   |
+--------------------------------------------------+
```

**Rendering Pipeline:**

```
Scene Graph (Three.js)
        |
        v
+------------------+
| WebGPU/Vulkan    |
| Command Buffer   |
+------------------+
        |
        v
+------------------+
| Mesa radeonsi    |
| Driver           |
+------------------+
        |
        v
+------------------+
| iGPU (890M)      |
| Rasterization    |
+------------------+
        |
        v
    Framebuffer
```

### 4.2 Discrete GPU (RTX 5060)

**Role:** AI compute (attention, LLM inference)

```
RTX 5060 ARCHITECTURE
=====================

+--------------------------------------------------+
|              Ada Lovelace Architecture            |
|                                                   |
|  +--------------------------------------------+  |
|  |          Streaming Multiprocessors          |  |
|  |                                             |  |
|  |  +--------+  +--------+  +--------+        |  |
|  |  |  SM0   |  |  SM1   |  |  ...   |        |  |
|  |  +--------+  +--------+  +--------+        |  |
|  |                                             |  |
|  |  Each SM:                                   |  |
|  |  - 128 CUDA cores (FP32)                    |  |
|  |  - 4 Tensor Cores (4th Gen)                 |  |
|  |  - 1 RT Core (3rd Gen)                      |  |
|  +--------------------------------------------+  |
|                                                   |
|  +--------------------------------------------+  |
|  |            Tensor Cores (Key!)             |  |
|  |                                             |  |
|  |  - FP16 matrix operations                   |  |
|  |  - INT8 quantized inference                 |  |
|  |  - ~200 TOPS (INT8)                         |  |
|  |  - Perfect for spatial attention!           |  |
|  +--------------------------------------------+  |
|                                                   |
|  VRAM: 16GB GDDR6X                               |
|  Bandwidth: ~300 GB/s                            |
|  TDP: ~150W                                       |
|                                                   |
+--------------------------------------------------+
```

### 4.3 GPU Task Assignment

```
+----------------------------------------------------------------+
|                   GPU TASK ASSIGNMENT                           |
+----------------------------------------------------------------+
|                                                                  |
|  TASK                      GPU      REASON                      |
|  ----                      ---      ------                      |
|                                                                  |
|  3D Rendering              iGPU     - Dedicated, no contention  |
|  (Three.js scene)                   - WebGPU/Vulkan native      |
|                                     - Frees dGPU for AI         |
|                                                                  |
|  Spatial Attention         dGPU     - Tensor Cores for FP16     |
|  (O(k) mechanism)                   - Large VRAM for matrices   |
|                                     - CUDA optimized            |
|                                                                  |
|  LLM Inference             dGPU     - 16GB VRAM for 7B model    |
|  (llama.cpp)                        - GPU layers offload        |
|                                     - 35+ layers on GPU         |
|                                                                  |
|  Large Batch Embed         dGPU     - When batch > 32           |
|  (fallback from NPU)                - Tensor Cores efficient    |
|                                                                  |
+----------------------------------------------------------------+
```

### 4.4 GPU Memory Management

```python
class GPUMemoryManager:
    """Manage VRAM allocation for AI workloads"""

    def __init__(self, vram_gb: int = 16):
        self.total_vram = vram_gb * 1024  # MB
        self.allocations = {}

    def plan_allocation(self) -> dict:
        """
        Plan VRAM usage for INFINITE workloads

        Returns:
            Allocation plan in MB
        """
        return {
            # LLM model (7B @ 4-bit)
            'llm_weights': 5000,      # ~5GB for GGUF Q4_K_M

            # Attention computation
            'attention_matrices': 2000,  # Q, K, V projections
            'attention_cache': 1000,     # KV cache

            # Embeddings
            'embedding_model': 500,      # BGE-small if dGPU fallback
            'batch_buffer': 500,         # Input/output tensors

            # Activations
            'forward_pass': 2000,        # Intermediate activations

            # Reserved
            'cuda_overhead': 1000,       # CUDA runtime
            'headroom': 4000,            # Safety margin

            # Total: ~16GB
        }

    def allocate_for_attention(self, batch_size: int, seq_len: int) -> bool:
        """Check if attention computation fits in VRAM"""
        # Memory per token: ~768 bytes (FP16 hidden dim)
        # QKV projections: 3x
        # Attention scores: seq_len^2 (but sparse in O(k))
        # Output: 1x

        base_memory = batch_size * seq_len * 768 * 2  # FP16
        qkv_memory = base_memory * 3
        attention_memory = batch_size * seq_len * 50 * 2  # O(k), k=50

        total_mb = (qkv_memory + attention_memory) / (1024 * 1024)

        return total_mb < self.allocations.get('attention_matrices', 2000)
```

---

## 5. CPU Architecture (Zen 5)

### 5.1 Zen 5 Overview

```
ZEN 5 ARCHITECTURE
==================

+--------------------------------------------------+
|                  8 Cores / 16 Threads             |
|                                                   |
|  +------+  +------+  +------+  +------+          |
|  | Core |  | Core |  | Core |  | Core |          |
|  |  0   |  |  1   |  |  2   |  |  3   |          |
|  +------+  +------+  +------+  +------+          |
|                                                   |
|  +------+  +------+  +------+  +------+          |
|  | Core |  | Core |  | Core |  | Core |          |
|  |  4   |  |  5   |  |  6   |  |  7   |          |
|  +------+  +------+  +------+  +------+          |
|                                                   |
|  +--------------------------------------------+  |
|  |              L3 Cache: 32MB               |  |
|  |  (Shared across all cores)                 |  |
|  +--------------------------------------------+  |
|                                                   |
|  Per-Core:                                        |
|  - L1i: 32KB, L1d: 32KB                          |
|  - L2: 1MB                                        |
|  - Base: 3.8 GHz, Boost: 5.2 GHz                 |
|                                                   |
|  Features:                                        |
|  - AVX-512 (critical for embeddings fallback)    |
|  - SMT (2 threads per core)                      |
|  - DDR5-6400 memory controller                   |
|                                                   |
+--------------------------------------------------+
```

### 5.2 CPU Task Assignment

| Task | Cores | Priority | Notes |
|------|-------|----------|-------|
| **Node.js API** | 2 | High | Async I/O, event loop |
| **Octree Indexing** | 2 | High | Spatial queries, O(log n) |
| **Context Streaming** | 1 | Medium | I/O bound, sequential |
| **Python Orchestration** | 1 | Medium | GIL limited |
| **PostgreSQL** | 1 | Low | Query processing |
| **Redis** | 0.5 | Low | In-memory, fast |
| **System** | 0.5 | Low | OS overhead |

### 5.3 CPU Optimization Strategies

```python
# 1. Octree optimized for cache
class CacheOptimizedOctree:
    """
    Layout octree nodes for cache efficiency:
    - Node data fits in single cache line (64 bytes)
    - Children stored contiguously
    - Hot data (bounds, pointers) first
    """

    def __init__(self):
        # Pack node data into 64 bytes
        self.node_dtype = np.dtype([
            ('min_x', 'f4'),       # 4 bytes
            ('min_y', 'f4'),       # 4 bytes
            ('min_z', 'f4'),       # 4 bytes
            ('max_x', 'f4'),       # 4 bytes
            ('max_y', 'f4'),       # 4 bytes
            ('max_z', 'f4'),       # 4 bytes
            ('children', 'u4', 8), # 32 bytes (8 child indices)
            ('flags', 'u4'),       # 4 bytes
            ('padding', 'u4'),     # 4 bytes
        ])  # Total: 64 bytes = 1 cache line

# 2. SIMD for distance calculations
def simd_distance_batch(positions1: np.ndarray, positions2: np.ndarray) -> np.ndarray:
    """Use AVX-512 for vectorized distance computation"""
    # NumPy automatically uses SIMD via BLAS/LAPACK
    diff = positions1 - positions2
    return np.sqrt(np.sum(diff ** 2, axis=-1))

# 3. Thread pool for parallel queries
from concurrent.futures import ThreadPoolExecutor

class ParallelOctreeQuery:
    def __init__(self, num_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=num_workers)

    def query_multiple_spheres(self, octree, centers, radii):
        """Query multiple spheres in parallel"""
        futures = [
            self.executor.submit(octree.query_sphere, c, r)
            for c, r in zip(centers, radii)
        ]
        return [f.result() for f in futures]
```

---

## 6. Memory Architecture

### 6.1 Unified Memory Model

```
MEMORY HIERARCHY
================

+------------------------------------------------------------------+
|                         DDR5-6400 (64GB)                          |
|                                                                    |
|  +--------------------------------------------------------------+ |
|  |                      System Regions                           | |
|  +--------------------------------------------------------------+ |
|  |                                                                | |
|  |  +------------------+    +------------------+                  | |
|  |  | CPU Accessible   |    | NPU Accessible   |                  | |
|  |  | (All 64GB)       |    | (Shared view)    |                  | |
|  |  +------------------+    +------------------+                  | |
|  |           |                      |                             | |
|  |           +----------+-----------+                             | |
|  |                      |                                         | |
|  |              +-------+-------+                                 | |
|  |              | Zero-Copy     |                                 | |
|  |              | Regions       |                                 | |
|  |              +---------------+                                 | |
|  |                                                                | |
|  |  +------------------+    +------------------+                  | |
|  |  | iGPU Shared      |    | Python Heap      |                  | |
|  |  | (Up to 8GB)      |    | (8GB allocated)  |                  | |
|  |  +------------------+    +------------------+                  | |
|  |                                                                | |
|  +--------------------------------------------------------------+ |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|                      dGPU VRAM (16GB GDDR6X)                      |
|                                                                    |
|  +--------------------------------------------------------------+ |
|  |                      GPU Regions                              | |
|  +--------------------------------------------------------------+ |
|  |                                                                | |
|  |  +------------------+    +------------------+                  | |
|  |  | LLM Weights      |    | Attention       |                  | |
|  |  | (5GB)            |    | Matrices (2GB)  |                  | |
|  |  +------------------+    +------------------+                  | |
|  |                                                                | |
|  |  +------------------+    +------------------+                  | |
|  |  | KV Cache         |    | Activations     |                  | |
|  |  | (1GB)            |    | (2GB)           |                  | |
|  |  +------------------+    +------------------+                  | |
|  |                                                                | |
|  |  +------------------+    +------------------+                  | |
|  |  | Batch Buffers    |    | Reserved        |                  | |
|  |  | (1GB)            |    | (5GB)           |                  | |
|  |  +------------------+    +------------------+                  | |
|  |                                                                | |
|  +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
```

### 6.2 Memory Allocation Strategy

```python
class MemoryAllocator:
    """Manage memory across all devices"""

    ALLOCATIONS = {
        # System RAM (64GB)
        'os_reserved': 8 * 1024,      # 8GB
        'nodejs_api': 4 * 1024,       # 4GB
        'python_spatial': 8 * 1024,   # 8GB
        'postgres_buffers': 4 * 1024, # 4GB
        'redis_cache': 2 * 1024,      # 2GB
        'llm_cpu_layers': 8 * 1024,   # 8GB (CPU offload)
        'octree_index': 4 * 1024,     # 4GB
        'igpu_shared': 8 * 1024,      # 8GB
        'free_headroom': 18 * 1024,   # 18GB

        # GPU VRAM (16GB)
        'llm_gpu_weights': 5 * 1024,  # 5GB
        'attention_compute': 3 * 1024, # 3GB
        'embedding_batch': 1 * 1024,  # 1GB
        'activations': 2 * 1024,      # 2GB
        'vram_headroom': 5 * 1024,    # 5GB
    }

    @classmethod
    def verify_allocations(cls):
        """Verify memory allocations fit available resources"""
        ram_used = sum([
            cls.ALLOCATIONS['os_reserved'],
            cls.ALLOCATIONS['nodejs_api'],
            cls.ALLOCATIONS['python_spatial'],
            cls.ALLOCATIONS['postgres_buffers'],
            cls.ALLOCATIONS['redis_cache'],
            cls.ALLOCATIONS['llm_cpu_layers'],
            cls.ALLOCATIONS['octree_index'],
            cls.ALLOCATIONS['igpu_shared'],
            cls.ALLOCATIONS['free_headroom'],
        ])

        vram_used = sum([
            cls.ALLOCATIONS['llm_gpu_weights'],
            cls.ALLOCATIONS['attention_compute'],
            cls.ALLOCATIONS['embedding_batch'],
            cls.ALLOCATIONS['activations'],
            cls.ALLOCATIONS['vram_headroom'],
        ])

        assert ram_used <= 64 * 1024, f"RAM overflow: {ram_used}MB > 64GB"
        assert vram_used <= 16 * 1024, f"VRAM overflow: {vram_used}MB > 16GB"

        return True
```

### 6.3 Zero-Copy Data Transfer

```python
# NPU <-> CPU zero-copy via shared memory

import numpy as np

class ZeroCopyBuffer:
    """Shared memory buffer for NPU/CPU data exchange"""

    def __init__(self, shape, dtype=np.float32):
        # Allocate page-aligned memory
        size = np.prod(shape) * np.dtype(dtype).itemsize
        self.buffer = np.empty(shape, dtype=dtype)

        # Mark as shared (no copy for NPU access)
        # This is handled by VitisAI runtime automatically

    def as_npu_input(self):
        """Get buffer as NPU input (zero-copy)"""
        return self.buffer

    def as_cpu_output(self):
        """Get buffer as CPU output (zero-copy)"""
        return self.buffer
```

---

## 7. Device Communication

### 7.1 Inter-Device Data Flow

```
DATA FLOW BETWEEN DEVICES
=========================

                         USER QUERY
                              |
                              v
+------------------------------------------------------------------+
|                          CPU (Zen 5)                              |
|                                                                    |
|  1. Parse query                                                   |
|  2. Route to NPU for embedding                                    |
|                                                                    |
+------------------------------------------------------------------+
              |
              | Text query (CPU -> NPU)
              | Zero-copy via shared memory
              v
+------------------------------------------------------------------+
|                          NPU (XDNA 2)                             |
|                                                                    |
|  3. Generate 384D embedding                                       |
|  4. Return embedding vector                                       |
|                                                                    |
+------------------------------------------------------------------+
              |
              | Embedding (NPU -> CPU)
              | Zero-copy via shared memory
              v
+------------------------------------------------------------------+
|                          CPU (Zen 5)                              |
|                                                                    |
|  5. Octree query (find k nearest tokens)                         |
|  6. Load context chunks from PostgreSQL                          |
|  7. Prepare attention inputs                                      |
|                                                                    |
+------------------------------------------------------------------+
              |
              | Context tensors (CPU -> GPU)
              | PCIe 4.0 x16 transfer
              v
+------------------------------------------------------------------+
|                          dGPU (RTX 5060)                          |
|                                                                    |
|  8. O(k) spatial attention                                        |
|  9. LLM inference                                                 |
|  10. Generate response                                            |
|                                                                    |
+------------------------------------------------------------------+
              |
              | Response text (GPU -> CPU)
              | PCIe transfer
              v
+------------------------------------------------------------------+
|                          CPU (Zen 5)                              |
|                                                                    |
|  11. Format response                                              |
|  12. Send to frontend via WebSocket                              |
|                                                                    |
+------------------------------------------------------------------+
              |
              | Render command (CPU -> iGPU)
              | Shared memory
              v
+------------------------------------------------------------------+
|                          iGPU (Radeon 890M)                       |
|                                                                    |
|  13. Update 3D visualization                                      |
|  14. Render agent movement                                        |
|  15. Display context loading animation                            |
|                                                                    |
+------------------------------------------------------------------+
              |
              v
           DISPLAY
```

### 7.2 Communication Latencies

| Transfer | Method | Latency | Bandwidth |
|----------|--------|---------|-----------|
| CPU <-> NPU | Shared DDR5 | ~1us | 100+ GB/s |
| CPU <-> iGPU | Shared DDR5 | ~1us | 100+ GB/s |
| CPU <-> dGPU | PCIe 4.0 x16 | ~10us | ~32 GB/s |
| dGPU VRAM internal | GDDR6X | ~1ns | ~300 GB/s |
| CPU <-> SSD | NVMe | ~10us | ~7 GB/s |
| CPU <-> Redis | Socket | ~100us | ~1 GB/s |

### 7.3 Async Pipeline

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncPipeline:
    """Asynchronous pipeline for device coordination"""

    def __init__(self):
        self.npu_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='npu')
        self.gpu_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='gpu')
        self.cpu_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='cpu')

    async def process_query(self, query: str) -> str:
        """Process query through multi-device pipeline"""

        loop = asyncio.get_event_loop()

        # Step 1: NPU embedding (async)
        embedding_task = loop.run_in_executor(
            self.npu_executor,
            self.npu_embed,
            query
        )

        # Step 2: CPU octree query (after embedding)
        embedding = await embedding_task
        context_task = loop.run_in_executor(
            self.cpu_executor,
            self.cpu_octree_query,
            embedding
        )

        # Step 3: GPU attention + inference (after context)
        context = await context_task
        response_task = loop.run_in_executor(
            self.gpu_executor,
            self.gpu_inference,
            query, context
        )

        response = await response_task
        return response
```

---

## 8. Performance Optimization

### 8.1 Optimization Targets

| Component | Current | Target | Optimization |
|-----------|---------|--------|--------------|
| Embedding | <5ms | <5ms | NPU acceleration |
| Octree Query | <10ms | <5ms | Cache optimization |
| Attention | <100ms | <50ms | Sparse + GPU |
| LLM Inference | ~3s | ~2s | Full GPU offload |
| Context Load | <100ms | <50ms | Predictive prefetch |
| 3D Render | 16ms | 16ms | iGPU dedicated |
| API Response | <50ms | <20ms | Redis caching |

### 8.2 Profiling Tools

```python
class HardwareProfiler:
    """Profile performance across all devices"""

    @staticmethod
    def profile_npu():
        """Profile NPU embedding performance"""
        import time

        npu = NPUEmbeddingGenerator('bge-small-xdna.onnx')

        # Warm up
        for _ in range(10):
            npu.generate(["warmup"])

        # Benchmark
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            npu.generate(["test query for embedding"])
            latencies.append((time.perf_counter() - start) * 1000)

        return {
            'mean_ms': np.mean(latencies),
            'p50_ms': np.percentile(latencies, 50),
            'p99_ms': np.percentile(latencies, 99),
            'throughput': 1000 / np.mean(latencies)
        }

    @staticmethod
    def profile_gpu_attention(batch_size: int = 32, seq_len: int = 1024):
        """Profile GPU spatial attention"""
        import torch

        device = torch.device('cuda')
        attention = SpatialAttention(d_model=768, n_heads=12).to(device)

        # Warm up
        x = torch.randn(batch_size, seq_len, 768, device=device)
        positions = torch.randn(batch_size, seq_len, 3, device=device) * 100

        for _ in range(10):
            _ = attention(x, positions)
            torch.cuda.synchronize()

        # Benchmark
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)

        latencies = []
        for _ in range(100):
            start.record()
            _ = attention(x, positions)
            end.record()
            torch.cuda.synchronize()
            latencies.append(start.elapsed_time(end))

        return {
            'mean_ms': np.mean(latencies),
            'p50_ms': np.percentile(latencies, 50),
            'p99_ms': np.percentile(latencies, 99),
            'throughput_tokens': batch_size * seq_len * 1000 / np.mean(latencies)
        }
```

### 8.3 Optimization Checklist

- [ ] **NPU Optimizations**
  - [ ] INT8 quantization for BGE-small
  - [ ] XDNA 2 compilation with vai_c
  - [ ] Batch size tuning (optimal: 16-32)
  - [ ] Memory pinning for zero-copy

- [ ] **GPU Optimizations**
  - [ ] FP16 mixed precision for attention
  - [ ] Tensor Core utilization (cuBLAS)
  - [ ] Flash Attention 2 integration
  - [ ] KV cache optimization
  - [ ] Full GPU offload for LLM

- [ ] **CPU Optimizations**
  - [ ] AVX-512 for vector operations
  - [ ] Cache-aligned data structures
  - [ ] NUMA-aware allocation
  - [ ] Thread pool sizing

- [ ] **Memory Optimizations**
  - [ ] Zero-copy transfers (NPU, iGPU)
  - [ ] Pinned memory for GPU transfers
  - [ ] Memory pooling
  - [ ] Gradient checkpointing

---

## 9. Power Management

### 9.1 Power Profiles

| Profile | NPU | iGPU | dGPU | CPU | Total | Use Case |
|---------|-----|------|------|-----|-------|----------|
| **Idle** | 1W | 5W | 10W | 15W | ~31W | Background |
| **Light** | 5W | 15W | 50W | 30W | ~100W | Browsing |
| **Normal** | 10W | 20W | 100W | 45W | ~175W | Inference |
| **Boost** | 10W | 25W | 150W | 65W | ~250W | Training |

### 9.2 Dynamic Power Scaling

```python
class PowerManager:
    """Manage power across devices"""

    def set_profile(self, profile: str):
        """Set system-wide power profile"""
        if profile == 'idle':
            self._set_npu_power(1)    # 1W
            self._set_gpu_power(10)   # 10W
            self._set_cpu_tdp(15)     # 15W
        elif profile == 'normal':
            self._set_npu_power(10)   # 10W
            self._set_gpu_power(100)  # 100W
            self._set_cpu_tdp(45)     # 45W
        elif profile == 'boost':
            self._set_npu_power(10)   # 10W (max)
            self._set_gpu_power(150)  # 150W (max)
            self._set_cpu_tdp(65)     # 65W (max)

    def auto_scale(self, workload_type: str):
        """Automatically scale power based on workload"""
        if workload_type == 'embedding_only':
            # Only NPU active
            self.set_profile('light')
        elif workload_type == 'inference':
            # Full pipeline
            self.set_profile('normal')
        elif workload_type == 'batch_processing':
            # Maximum throughput
            self.set_profile('boost')
```

---

## 10. Fallback Strategies

### 10.1 Graceful Degradation

```
FALLBACK HIERARCHY
==================

Primary Path           Fallback 1            Fallback 2
------------           ----------            ----------

Embedding:
NPU (XDNA 2)    -->    dGPU (Tensor)   -->   CPU (AVX-512)
<5ms                   <10ms                  <50ms

Attention:
dGPU (Tensor)   -->    NPU (INT8)      -->   CPU (Slow)
<50ms                  <100ms                 <500ms

LLM:
dGPU (Full)     -->    CPU (Hybrid)    -->   API (Cloud)*
~2s                    ~10s                   ~1s
                                              * Last resort

Rendering:
iGPU (WebGPU)   -->    dGPU (Vulkan)   -->   CPU (Software)
60fps                  60fps                  5fps
```

### 10.2 Fallback Implementation

```python
class ResilientHardware:
    """Hardware abstraction with automatic fallback"""

    def __init__(self):
        self.npu = self._try_init_npu()
        self.dgpu = self._try_init_dgpu()
        self.igpu = self._try_init_igpu()

    def embed(self, text: str) -> np.ndarray:
        """Generate embedding with fallback"""
        if self.npu:
            try:
                return self.npu.embed(text)
            except Exception as e:
                logger.warning(f"NPU failed: {e}, falling back to GPU")

        if self.dgpu:
            try:
                return self.dgpu.embed(text)
            except Exception as e:
                logger.warning(f"GPU failed: {e}, falling back to CPU")

        # CPU fallback (always available)
        return self.cpu_embed(text)

    def attention(self, x, positions):
        """Compute attention with fallback"""
        if self.dgpu:
            try:
                return self.dgpu.attention(x, positions)
            except torch.cuda.OutOfMemoryError:
                logger.warning("GPU OOM, falling back to CPU")

        # CPU fallback
        logger.warning("Using CPU for attention (slow)")
        return self.cpu_attention(x, positions)
```

### 10.3 Error Recovery

```python
class HardwareErrorRecovery:
    """Recover from hardware errors"""

    def __init__(self):
        self.error_counts = defaultdict(int)
        self.disabled_devices = set()

    def handle_error(self, device: str, error: Exception):
        """Handle hardware error with recovery strategy"""
        self.error_counts[device] += 1

        if self.error_counts[device] > 3:
            # Too many errors, disable device
            self.disabled_devices.add(device)
            logger.error(f"Disabled {device} due to repeated errors")

            # Notify monitoring
            self.alert(f"Device {device} disabled: {error}")

        # Attempt recovery
        if device == 'npu':
            self._reset_npu()
        elif device == 'dgpu':
            self._clear_gpu_memory()
            self._reset_cuda()

    def _reset_npu(self):
        """Reset NPU state"""
        import onnxruntime as ort
        ort.get_default_session_options().clear()

    def _clear_gpu_memory(self):
        """Clear GPU memory cache"""
        import torch
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

    def _reset_cuda(self):
        """Reset CUDA context"""
        import torch
        torch.cuda.reset_peak_memory_stats()
```

---

## Summary

The INFINITE hardware architecture leverages a sophisticated multi-device strategy:

1. **NPU (XDNA 2):** Always-on, power-efficient embedding generation
2. **dGPU (RTX 5060):** High-performance AI compute with Tensor Cores
3. **iGPU (Radeon 890M):** Dedicated 3D rendering without VRAM contention
4. **CPU (Zen 5):** Orchestration, indexing, and I/O handling

This architecture enables:
- **<5ms embeddings** via NPU
- **<50ms spatial attention** via GPU Tensor Cores
- **60 FPS 3D visualization** via dedicated iGPU
- **Unlimited context** through O(k) complexity

With graceful fallbacks ensuring the system remains functional even when specific hardware is unavailable.

---

**Document Version:** 1.0
**Last Updated:** December 1, 2025
**Author:** ch1pu (System Architect)
**Status:** Architecture Complete
