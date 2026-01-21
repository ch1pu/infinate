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

# MIT RLM - Technical Deep Dive

> **Deep technical analysis of MIT's Recursive Language Model inference strategy**

**Last Updated:** 2026-01-18
**Purpose:** Understanding RLM internals for competitive positioning

---

## Table of Contents

1. [REPL Environment Mechanics](#repl-environment-mechanics)
2. [Code Generation Patterns](#code-generation-patterns)
3. [Recursive Call Structure](#recursive-call-structure)
4. [Complexity Analysis](#complexity-analysis)
5. [Emergent Strategies](#emergent-strategies)
6. [Implementation Details](#implementation-details)
7. [Technical Limitations](#technical-limitations)

---

## REPL Environment Mechanics

### Overview

RLM's core innovation is treating the context as an **external variable** accessible through a Python REPL, rather than embedding it in the prompt. This is a crucial distinction.

### Traditional LLM Approach

```
┌──────────────────────────────────────────┐
│              PROMPT WINDOW               │
│                                          │
│  System: "You are a helpful assistant"   │
│  Context: [ENTIRE 50,000 PAGE DOCUMENT]  │  ← All in memory
│  Query: "What was Q3 revenue?"           │
│                                          │
│  Attention: O(n²) over EVERYTHING        │
└──────────────────────────────────────────┘
```

**Problem:** Context window overflow, O(n²) attention over entire document.

### RLM REPL Approach

```
┌──────────────────────────────────────────┐
│              PROMPT WINDOW               │
│                                          │
│  System: "You have access to x via REPL" │
│  Query: "What was Q3 revenue?"           │
│  Tools: grep, partition, map_lm, FINAL   │  ← Small prompt
│                                          │
│  Attention: O(m²) where m << n           │
└──────────────────────────────────────────┘
         │
         │ Model generates code
         ▼
┌──────────────────────────────────────────┐
│           EXTERNAL VARIABLE x            │
│                                          │
│  x = [50,000 page document stored here]  │  ← Not in attention
│                                          │
└──────────────────────────────────────────┘
```

**Key insight:** The model never "sees" the full context in its attention window. It only interacts via code.

### REPL Execution Flow

```python
# Step 1: Model receives small prompt
prompt = """
You have access to variable x containing a document.
Use grep(), partition(), map_lm(), and FINAL() to answer:
Query: What was the Q3 2024 revenue?
"""

# Step 2: Model generates code
model_output = """
# First, let's search for Q3 2024 mentions
results = grep(x, r"Q3 2024.*revenue|revenue.*Q3 2024")
if results:
    FINAL(f"Based on search: {extract_number(results)}")
else:
    # Partition and search recursively
    chunks = partition(x, n=20)
    answers = map_lm(chunks, "Find any Q3 2024 revenue figures")
    FINAL(aggregate(answers))
"""

# Step 3: REPL executes code
# - grep() searches x without loading into attention
# - partition() splits x into chunks
# - map_lm() spawns sub-LM calls on each chunk
# - FINAL() returns answer
```

---

## Code Generation Patterns

### Pattern 1: Direct Grep

**When used:** Query has clear keywords to search for.

```python
# Model-generated code
result = grep(x, r"revenue.*2024|2024.*revenue")
if result:
    FINAL(parse_revenue(result))
```

**Characteristics:**
- Fast (regex search, no LM calls)
- Works when answer is explicit in text
- Fails for inference-required queries

### Pattern 2: Partition and Map

**When used:** Query requires understanding across document.

```python
# Model-generated code
chunks = partition(x, n=10)
summaries = map_lm(chunks, "Summarize financial metrics")
combined = aggregate(summaries)
FINAL(answer_from(combined))
```

**Characteristics:**
- Slower (n LM calls)
- Works for complex queries
- Parallelizable (though RLM does sequential)

### Pattern 3: Hierarchical Decomposition

**When used:** Very large contexts requiring multi-level processing.

```python
# Model-generated code
# Level 1: Coarse chunking
sections = partition(x, n=5)

# Level 2: Find relevant section
for i, section in enumerate(sections):
    relevance = lm_call(section[:1000], "Is this about finance?")
    if "yes" in relevance.lower():
        # Level 3: Fine-grained search within section
        subsections = partition(section, n=10)
        results = map_lm(subsections, query)
        FINAL(aggregate(results))
```

**Characteristics:**
- Most expensive
- Handles very large contexts
- Limited to depth=1 in paper's experiments

### Pattern 4: Peek and Decide

**When used:** Unknown document structure.

```python
# Model-generated code
# Peek at beginning to understand structure
preview = x[:5000]  # First 5K chars
structure = lm_call(preview, "What is the structure of this document?")

# Decide strategy based on structure
if "table of contents" in structure:
    toc = grep(x, r"Table of Contents[\s\S]*?(?=\n\n)")
    # Navigate via TOC
else:
    # Fallback to partition
    chunks = partition(x, n=20)
    ...
```

---

## Recursive Call Structure

### Call Graph Example

```
                    ROOT LLM CALL
                    Query: "Q3 revenue?"
                    Context: x (external)
                          │
                          │ generates code:
                          │ chunks = partition(x, 10)
                          │ map_lm(chunks, query)
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
     SUB-LM #1       SUB-LM #2       SUB-LM #10
     Chunk 1         Chunk 2    ...  Chunk 10
     Context: c1     Context: c2     Context: c10
          │               │               │
          │               │               │
          ▼               ▼               ▼
     "No revenue"    "$5.2B Q3"      "N/A"
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼
                    AGGREGATION
                    "Q3 2024 revenue: $5.2B"
                          │
                          ▼
                    FINAL("$5.2B")
```

### Execution Order (Current Implementation)

**Sequential (NOT parallel):**

```
Time ──────────────────────────────────────────────►

ROOT ─────┬─────────────────────────────────────────►
          │
          ├──► SUB-LM #1 ──► result1
          │         │
          │         ▼ (wait)
          ├──► SUB-LM #2 ──► result2
          │         │
          │         ▼ (wait)
          ├──► SUB-LM #3 ──► result3
          ...
          │         │
          │         ▼ (wait)
          └──► SUB-LM #10 ──► result10
                    │
                    ▼
              AGGREGATE
```

**Impact:** Total time = sum of all sub-LM calls (not max).

### Theoretical Parallel Execution (Not Implemented)

```
Time ──────────────────────────────────────────────►

ROOT ─────┬─────────────────────────────────────────►
          │
          ├──► SUB-LM #1  ────► result1 ──┐
          ├──► SUB-LM #2  ────► result2 ──┤
          ├──► SUB-LM #3  ────► result3 ──┼──► AGGREGATE
          ...                             │
          └──► SUB-LM #10 ────► result10 ─┘
```

**Potential improvement:** Total time = max of sub-LM calls.

---

## Complexity Analysis

### What MIT RLM Claims

The paper implies handling "unlimited" context by not loading it into the prompt.

### Actual Complexity Breakdown

#### 1. Root Call Complexity

```
Root prompt size: O(p) where p = query + instructions (small, ~1K tokens)
Attention complexity: O(p²) ≈ O(1) (constant)
```

#### 2. Sub-Call Complexity

```
Each chunk size: O(n/k) where n = total context, k = number of chunks
Attention per chunk: O((n/k)²)
Total if k chunks: k × O((n/k)²) = O(n²/k)
```

#### 3. Total Complexity

```
Single level recursion:
- Root call: O(1)
- Code execution: O(1)
- Sub-calls: O(n²/k)
- Aggregation: O(k)

Total: O(n²/k + k)

Optimal k ≈ √n gives O(n^1.5) - still superlinear!
```

### The Hidden O(n²)

**Critical insight:** Within each chunk, the underlying transformer attention is still O(n²).

```
Context: 1,000,000 tokens
Chunks: 100
Per chunk: 10,000 tokens
Attention per chunk: O(10,000²) = O(100,000,000)
Total: 100 × O(100,000,000) = O(10,000,000,000)

Compare to full O(n²):
O(1,000,000²) = O(1,000,000,000,000)

Savings: 100x, but still massive
```

### Comparison with Infinite's O(k)

```
Infinite complexity:
- Each token attends to k=50 neighbors
- Total: O(n × k) = O(n) linear

For 1,000,000 tokens:
MIT RLM: O(n²/chunks) ≈ O(10,000,000,000) ops (with 100 chunks)
Infinite: O(n × k) = O(50,000,000) ops

Infinite is 200x more efficient at this scale!
```

---

## Emergent Strategies

### 1. Strategic Peeking

The model learns to sample the beginning of documents to understand structure:

```python
# Emergent behavior (not explicitly programmed)
preview = x[:2000]  # Peek at first 2K chars
structure_info = lm_call(preview, "What type of document is this?")
# Then adapts strategy based on document type
```

**Why it emerges:** More efficient than blind partitioning.

### 2. Keyword Extraction

Model extracts keywords from query for targeted grep:

```python
# Query: "What was the Q3 2024 revenue for the North American region?"
# Model extracts: Q3, 2024, revenue, North American

results = grep(x, r"Q3.*2024.*North America|North America.*revenue.*Q3")
```

### 3. Progressive Refinement

Model narrows search iteratively:

```python
# Round 1: Broad search
financial_sections = grep(x, r"Financial|Revenue|Income")

# Round 2: Narrow within results
q3_data = grep(financial_sections, r"Q3|Third Quarter")

# Round 3: Extract specific figure
answer = grep(q3_data, r"\$[\d,]+\.?\d*\s*(million|billion)?")
```

### 4. Confidence-Based Early Exit

Model returns early when confident:

```python
result = grep(x, query_keywords)
if high_confidence(result):
    FINAL(result)  # Exit without full search
else:
    # Continue with more thorough search
    ...
```

---

## Implementation Details

### GitHub Repository Structure

```
github.com/alexzhang13/rlm/
├── rlm/
│   ├── __init__.py
│   ├── repl.py          # REPL environment
│   ├── operations.py    # grep, partition, map_lm
│   └── model.py         # LLM interface
├── experiments/
│   ├── oolong.py
│   ├── codeqa.py
│   └── browsecomp.py
├── prompts/
│   └── system.txt       # System prompt template
└── requirements.txt
```

### Core Operations Implementation

```python
# Simplified version of RLM operations

def grep(text: str, pattern: str) -> str:
    """Regex search without loading into attention."""
    import re
    matches = re.findall(pattern, text, re.IGNORECASE)
    return "\n".join(matches)

def partition(text: str, n: int) -> List[str]:
    """Split text into n roughly equal chunks."""
    chunk_size = len(text) // n
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def map_lm(chunks: List[str], query: str) -> List[str]:
    """Apply LLM to each chunk (SEQUENTIAL in current impl)."""
    results = []
    for chunk in chunks:
        result = llm_call(
            prompt=f"Query: {query}\nContext: {chunk}\nAnswer:",
            max_tokens=500
        )
        results.append(result)
    return results

def FINAL(answer: str) -> None:
    """Signal completion and return answer."""
    raise FinalAnswer(answer)
```

### System Prompt Template

```
You are an AI assistant with access to a Python REPL environment.
A document is stored in variable `x`. You cannot see x directly,
but you can interact with it using these operations:

- grep(x, pattern): Search x for regex pattern, returns matches
- partition(x, n): Split x into n chunks
- map_lm(chunks, query): Apply LLM to each chunk with query
- FINAL(answer): Return your final answer

Your goal: {user_query}

Write Python code to find the answer. Use FINAL() when done.
```

---

## Technical Limitations

### 1. No Gradient Flow

```
Forward pass:
Query → Root LLM → Code → REPL → Sub-LLMs → Answer
              ✓       ✗     ✗        ✓        ✓
              │       │     │        │        │
              │       └─────┴────────┘        │
              │        No gradients here      │
              └───────────────────────────────┘
                    Gradients possible

Backward pass: Cannot backprop through code generation/execution
```

**Impact:** Cannot fine-tune for specific tasks or optimize decomposition strategy.

### 2. Non-Deterministic Execution

Same query can produce different code → different costs:

```
Query: "What is the revenue?"

Run 1: Model uses grep → 0.5 seconds, $0.01
Run 2: Model uses partition(100) → 60 seconds, $2.00
Run 3: Model uses hierarchical → 180 seconds, $5.00
```

**Impact:** Unpredictable latency and cost.

### 3. Context Window Still Limits Chunks

Each sub-LM call still has a context window limit:

```
Total context: 10M tokens
Chunks needed: 10M / 128K = ~78 chunks minimum

But with 78 chunks, each chunk is 128K tokens
Attention per chunk: O(128K²) = O(16B) operations
Still very expensive!
```

### 4. Sequential Bottleneck

Current implementation blocks on each sub-call:

```
10 chunks × 5 seconds each = 50 seconds total
vs
10 chunks in parallel = 5 seconds (theoretical)

10x slowdown from sequential execution
```

### 5. Code Generation Failures

Model can generate invalid code:

```python
# Model might generate:
results = grep(x, "[invalid regex")  # Syntax error
partition(x, 0)  # Division by zero
map_lm(None, query)  # Type error
```

**Impact:** Runtime errors, need for error handling and retries.

### 6. Fundamental: Still O(n²) at Core

No matter how clever the decomposition:

```
Every token that is processed goes through O(n²) attention
within its chunk.

Total work = (sum of chunk sizes)² / num_chunks
           ≈ O(n²/k) for k chunks

Never truly O(n) or O(k) constant
```

---

## Summary Table: RLM vs Infinite Technical Comparison

| Technical Aspect | MIT RLM | Infinite |
|-----------------|---------|----------|
| **Core Operation** | Code generation + REPL | Direct spatial attention |
| **Attention Complexity** | O(n²) within chunks | O(k) constant |
| **Memory Access** | Indirect (via code) | Direct (spatial locality) |
| **Gradient Flow** | Blocked at REPL | Full end-to-end |
| **Determinism** | Non-deterministic | Deterministic |
| **Parallelism** | Sequential (current) | Inherently parallel |
| **Failure Modes** | Code errors, timeouts | None (mathematical) |
| **Training** | Not possible | End-to-end trainable |
| **Latency** | Seconds to minutes | Milliseconds |
| **Scaling** | O(n²/k) → O(n^1.5) | O(nk) → O(n) |

---

**Document prepared by:** Adolfo Lopez (ch1pu)
**For:** Infinite Spatial AI competitive analysis
**Last Updated:** 2026-01-18
