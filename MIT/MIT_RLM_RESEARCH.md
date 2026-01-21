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

# MIT Recursive Language Models (RLM) - Research Documentation

> **Research Summary:** MIT's approach to handling long contexts through recursive decomposition and code generation

**Last Updated:** 2026-01-18
**Researcher:** Adolfo Lopez (ch1pu)
**Purpose:** Competitive analysis for Infinite spatial AI system

---

## Table of Contents

1. [Paper Overview](#paper-overview)
2. [Authors and Affiliations](#authors-and-affiliations)
3. [Core Concept](#core-concept)
4. [How RLM Works](#how-rlm-works)
5. [Architecture Diagram](#architecture-diagram)
6. [Benchmark Results](#benchmark-results)
7. [Limitations](#limitations)
8. [Key Insights](#key-insights)
9. [Source Links](#source-links)

---

## Paper Overview

| Attribute | Value |
|-----------|-------|
| **Title** | Recursive Language Models |
| **arXiv ID** | 2512.24601 |
| **Release Date** | December 31, 2025 |
| **Version** | v1 |
| **Category** | cs.CL (Computation and Language) |
| **Primary Claim** | Enable LLMs to handle contexts beyond their window without finetuning |

### Abstract Summary

RLM (Recursive Language Model) is a novel inference strategy that enables language models to handle long documents—equivalent to thousands of books—without requiring fine-tuning or architectural modifications. The approach uses a REPL (Read-Eval-Print-Loop) environment where the context is stored as a Python variable, and the model generates code to recursively decompose and search through the information.

---

## Authors and Affiliations

| Author | Affiliation | Role |
|--------|-------------|------|
| **Alex L. Zhang** | MIT OASYS Lab | Lead Author |
| **Tim Kraska** | MIT OASYS Lab | Co-Author |
| **Omar Khattab** | MIT OASYS Lab | Co-Author |

**Research Lab:** MIT OASYS (Online Adaptive SYStem) Lab
**Focus Area:** Database systems, machine learning systems, query optimization

---

## Core Concept

### The Problem RLM Solves

Modern LLMs have limited context windows (typically 8K-128K tokens). When documents exceed this limit, the model cannot process them directly. Current solutions include:

1. **RAG (Retrieval-Augmented Generation)** - But requires knowing what to retrieve upfront
2. **Fine-tuning for longer contexts** - Expensive and may degrade quality
3. **Chunking and summarization** - Loses information

### RLM's Solution

RLM treats the long document as an **external variable** accessible through a Python REPL environment. Instead of loading the entire context into the prompt, the model:

1. Writes Python code to search/filter the context
2. Recursively spawns sub-LM instances to process chunks
3. Aggregates results to answer the query

**Key Insight:** The model can *reason about* the context without *loading* it all into the attention window.

---

## How RLM Works

### Step-by-Step Process

```
1. QUERY RECEIVED
   User asks: "What was the revenue in Q3 2024?"
   Context: 50,000 page financial document (far exceeds context window)

2. ROOT LLM INVOCATION
   - Query placed in prompt
   - Context stored as Python variable `x` (NOT in prompt)
   - Model has access to REPL environment

3. CODE GENERATION
   Model writes Python code to interact with context:

   ```python
   # Search for Q3 2024 revenue mentions
   relevant = grep(x, "Q3 2024.*revenue")

   # Or partition and map
   chunks = partition(x, n=10)
   results = map_lm(chunks, "Find revenue figures")
   ```

4. RECURSIVE DECOMPOSITION
   - Sub-LM instances process each chunk
   - Each sub-LM can further decompose if needed
   - Results aggregated bottom-up

5. FINAL ANSWER
   Model outputs: FINAL("The Q3 2024 revenue was $X.XX billion")
```

### The REPL Environment

RLM provides the model with these core operations:

| Operation | Description | Example |
|-----------|-------------|---------|
| `grep(text, pattern)` | Search for regex pattern | `grep(x, "revenue")` |
| `partition(text, n)` | Split into n chunks | `partition(x, 10)` |
| `map_lm(chunks, query)` | Apply LM to each chunk | `map_lm(chunks, "summarize")` |
| `FINAL(answer)` | Return final answer | `FINAL("$5.2B")` |

### Emergent Behaviors

The paper documents several emergent strategies the model learns without explicit training:

1. **Peeking** - Sampling beginning of context to understand structure
2. **Grepping** - Using regex patterns to find relevant sections
3. **Chunking** - Dividing context for parallel processing
4. **Depth-first search** - Recursively drilling into promising sections

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        USER QUERY                           │
│            "What was the Q3 2024 revenue?"                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      ROOT LLM CALL                          │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │     PROMPT      │    │       REPL ENVIRONMENT          │ │
│  │                 │    │                                 │ │
│  │  Query: "..."   │    │  x = [50,000 pages of text]     │ │
│  │  Tools: grep,   │    │                                 │ │
│  │  partition,     │    │  (context NOT in prompt,        │ │
│  │  map_lm, FINAL  │    │   only accessible via code)     │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ LLM generates code:
                              │ chunks = partition(x, 10)
                              │ results = map_lm(chunks, "find revenue")
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   RECURSIVE SUB-LM CALLS                    │
│                                                             │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐      ┌─────────┐   │
│   │ Sub-LM  │  │ Sub-LM  │  │ Sub-LM  │ ...  │ Sub-LM  │   │
│   │ Chunk 1 │  │ Chunk 2 │  │ Chunk 3 │      │ Chunk N │   │
│   └────┬────┘  └────┬────┘  └────┬────┘      └────┬────┘   │
│        │            │            │                 │        │
│        ▼            ▼            ▼                 ▼        │
│   [Result 1]   [Result 2]   [Result 3]  ...  [Result N]    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Results aggregated
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FINAL ANSWER                           │
│           FINAL("The Q3 2024 revenue was $5.2B")           │
└─────────────────────────────────────────────────────────────┘
```

---

## Benchmark Results

### Datasets Tested

| Dataset | Context Size | Task Type |
|---------|--------------|-----------|
| **OOLONG** | ~500K tokens | Document QA |
| **CodeQA** | ~50K-100K tokens | Code understanding |
| **BrowseComp+** | 6-11M tokens | Multi-document research |

### Performance Improvements

| Dataset | Baseline | RLM | Improvement |
|---------|----------|-----|-------------|
| **OOLONG** | 44.0% | 56.5% | **+28.4%** |
| **CodeQA** | 20.0% | 56.0% | **+180%** (relative) |
| **BrowseComp+** | 0.0% | 91.33% | **Breakthrough** |

### Cost Analysis

| Metric | Value |
|--------|-------|
| **Average Cost per Query** | ~$0.99 |
| **Token Volume** | 6-11M tokens processed |
| **Cost Efficiency** | ~100x cheaper than loading full context |

### Runtime Characteristics

| Metric | Value |
|--------|-------|
| **Typical Runtime** | "Few seconds to several minutes" |
| **Variance** | High (95th percentile much higher than median) |
| **Determinism** | Non-deterministic (depends on model's code choices) |

---

## Limitations

### 1. Sequential Blocking Execution

RLM currently executes recursive calls **sequentially**, not in parallel. The paper acknowledges:

> "RLM currently executes all recursive calls sequentially, with no support for asynchronous execution."

**Impact:** Linear scaling with number of chunks, longer runtimes.

### 2. High Variance in Cost and Runtime

The paper reports:

> "Costs spike dramatically at the 95th percentile"

**Impact:** Unpredictable latency and cost, difficult to budget.

### 3. Not Trained End-to-End

RLM relies on:
- In-context learning (prompting)
- Existing model's code generation abilities
- No gradient flow through the recursive structure

**Impact:** Cannot optimize for specific tasks, relies on general capabilities.

### 4. Limited Recursion Depth

From the paper:

> "We only tested depth=1 recursion in our experiments"

**Impact:** May not scale to truly massive contexts requiring deep decomposition.

### 5. Underlying Attention Still O(n²)

**Critical limitation:** When any chunk is actually processed, the underlying transformer attention is still O(n²) within that chunk.

**Impact:** Does not solve the fundamental complexity problem, just avoids it through clever decomposition.

### 6. Requires Code-Capable Models

RLM requires models that can:
- Generate valid Python code
- Understand REPL execution patterns
- Reason about recursive decomposition

**Impact:** Not applicable to all LLMs, particularly smaller models.

---

## Key Insights

### What RLM Gets Right

1. **Clever abstraction** - Treating context as external variable is elegant
2. **No finetuning required** - Works with existing models
3. **Demonstrates emergent capabilities** - Models learn strategies without explicit training
4. **Practical results** - Significant improvements on benchmarks

### What RLM Misses

1. **It's a wrapper, not a solution** - The underlying attention problem remains
2. **Indirection cost** - Code generation + execution adds latency
3. **Non-deterministic** - Same query can have wildly different costs
4. **Not trainable** - Cannot backprop through recursive structure

### The Fundamental Difference from Infinite

| Aspect | MIT RLM | Infinite |
|--------|---------|----------|
| **Approach** | Inference strategy (wrapper) | Architecture change |
| **Core Attention** | Still O(n²) | True O(k) |
| **Memory Access** | Via code generation | Direct spatial attention |
| **Latency** | Seconds to minutes | Milliseconds |
| **Determinism** | High variance | Deterministic |
| **Trainability** | Not end-to-end | Full gradient flow |

---

## Source Links

### Primary Sources

| Resource | URL |
|----------|-----|
| **arXiv Paper** | https://arxiv.org/abs/2512.24601 |
| **arXiv HTML** | https://arxiv.org/html/2512.24601v1 |
| **GitHub Repository** | https://github.com/alexzhang13/rlm |
| **Author Blog Post** | https://alexzhang13.github.io/blog/2025/rlm/ |
| **HuggingFace Papers** | https://huggingface.co/papers/2512.24601 |

### Citations

```bibtex
@misc{zhang2025recursive,
    title={Recursive Language Models},
    author={Alex L. Zhang and Tim Kraska and Omar Khattab},
    year={2025},
    eprint={2512.24601},
    archivePrefix={arXiv},
    primaryClass={cs.CL}
}
```

---

## Related Reading

- **Infinite Spatial AI** - `/home/ch1pu/infinate/Documents/CORE_INNOVATION.md`
- **O(k) Complexity Proof** - `/home/ch1pu/infinate/Documents/SPATIAL_MODEL_ARCHITECTURE.md`
- **Comparison Document** - `/home/ch1pu/infinate/MIT/COMPARISON_INFINITE_VS_MIT_RLM.md`

---

**Research conducted by:** Adolfo Lopez (ch1pu)
**For project:** Infinite Spatial AI System
**Company:** Alpha Deploy LLC (pre-formation)
**Purpose:** Competitive analysis and differentiation documentation
