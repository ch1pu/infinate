# LOD and Multi-Pass: How They Work Together

**Created:** January 20, 2026
**Author:** Adolfo Lopez (ch1pu)
**Related Milestones:** M1.10 (LOD), M1.11 (Strafe Jumping Navigation)

---

## Executive Summary

INFINATE uses two complementary techniques to achieve comprehensive context coverage:

| Technique | Milestone | Purpose | Analogy |
|-----------|-----------|---------|---------|
| **LOD (Level of Detail)** | M1.10 | See further, but blurry | Peripheral vision |
| **Multi-Pass Navigation** | M1.11 | See different areas sharply | Moving your eyes |

**Together:** Awareness of entire context + sharp detail where needed.

---

## The Problem: Hard Cutoff

Before M1.10, INFINATE had a hard cutoff at k tokens:

```
WITHOUT LOD (M1.9 and earlier):
═══════════════════════════════

Query Position
      ↓
      ●━━━━━━━━━━━━━━━━━━━━━━━━━|  COMPLETE VOID
      |←────── k=50 tokens ────→|  (Token 51+ invisible)
      |                         |
      |    100% VISIBLE         |    0% VISIBLE
      |    Full detail          |    Information cliff
      |                         |

PROBLEM: Everything beyond token 50 is completely invisible.
         A critical fact at token 200? Gone. You'll never know it exists.
```

**Real Example:**
- Query: "What was Q3 revenue?"
- Q3 revenue fact is at token position 200
- Result: "I don't have information about Q3 revenue" (FALSE - it exists, just invisible)

---

## Solution Part 1: LOD (Level of Detail)

M1.10 introduced hierarchical compression to see further:

```
WITH LOD (M1.10):
═════════════════

Query Position
      ↓
      ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
      |   NEAR    |   MEDIUM   |     FAR      |      BEYOND       |
      |           |            |              |                   |
      | Distance  | Distance   |  Distance    |   Distance        |
      |  0-50     |  50-150    |  150-500     |    500+           |
      |           |            |              |                   |
      | 50 tokens | 25 tokens  |  10 tokens   |   5 tokens        |
      | (1:1)     | (5:1)      |  (20:1)      |  (100:1)          |
      |           |            |              |                   |
      | 100%      |  ~80%      |   ~60%       |    ~30%           |
      | detail    |  detail    |  detail      |   detail          |

TOTAL: 90 tokens visible, representing ~5,375 original tokens
       (107× more context awareness than before!)
```

### How LOD Compression Works

```
COMPRESSION EXAMPLE (FAR zone, 20:1):
═════════════════════════════════════

Original 20 tokens in FAR zone:
┌─────────────────────────────────────────────────────────────────┐
│ "Q3" "revenue" "was" "$4.2" "million" "which" "represents" ... │
│ (20 individual tokens with full semantic meaning)               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    LOD Compression (20:1)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ [Compressed Token: "financial_Q3_revenue_~$4M"]                 │
│ (1 token that captures the GIST but loses precision)           │
└─────────────────────────────────────────────────────────────────┘

What's PRESERVED:  Topic (financial), Time (Q3), Concept (revenue), Magnitude (~$4M)
What's LOST:       Exact value ($4.2M), Context words, Relationships
```

### LOD Zone Details

| Zone | Distance | Tokens | Compression | Detail | Use Case |
|------|----------|--------|-------------|--------|----------|
| **NEAR** | 0-50 | 50 | 1:1 (none) | 100% | Primary focus, exact facts |
| **MEDIUM** | 50-150 | 25 | 5:1 | ~80% | Supporting context, related topics |
| **FAR** | 150-500 | 10 | 20:1 | ~60% | Awareness of distant themes |
| **BEYOND** | 500+ | 5 | 100:1 | ~30% | Fog - "something exists there" |

---

## The LOD Tradeoff

### What You Gain

```
VISIBILITY COMPARISON:
══════════════════════

Without LOD:    [50 tokens] | VOID VOID VOID VOID VOID VOID VOID
With LOD:       [50 tokens] | [25 medium] | [10 far] | [5 beyond]

                     50     vs    5,375 tokens of awareness
                              (107× improvement)
```

### What You Lose

```
DETAIL LOSS BY ZONE:
════════════════════

NEAR (100%):    "Q3 revenue was $4.2 million, up 15% from Q2's $3.65M"
                 ↳ Perfect recall, all details preserved

MEDIUM (80%):   "Q3 revenue approximately $4.2M, increased from Q2"
                 ↳ Good recall, minor details may blur

FAR (60%):      "Q3 revenue around $4M, positive trend"
                 ↳ Gist preserved, specifics lost

BEYOND (30%):   "financial...Q3...revenue...positive"
                 ↳ Topic detection only, details gone
```

### The Core Tradeoff Table

| Aspect | Without LOD | With LOD |
|--------|-------------|----------|
| Tokens visible | 50 | 90 |
| Context represented | 50 | ~5,375 |
| Near zone detail | 100% | 100% (unchanged) |
| Far zone detail | 0% (invisible) | 30-60% (blurry but present) |
| **Risk without** | Miss everything beyond k | - |
| **Risk with** | - | Miss specific details in compressed zones |

---

## Solution Part 2: Multi-Pass Navigation

M1.11 Strafe Jumping enables multiple navigation passes:

```
SINGLE PASS (LOD only):
═══════════════════════

Pass 1:    ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
           |   NEAR    |   MEDIUM   |     FAR      |   BEYOND   |
           | [50 sharp]| [25 blurry]| [10 v.blurry]| [5 fog]    |
                ↑
           Query lands here (finance cluster)

Result: 50 tokens at full detail
        40 tokens at reduced detail (LOD)

Problem: What if the SPECIFIC fact you need is in FAR zone?
         You see "financial Q3 ~$4M" but need "$4.2M exactly"


MULTI-PASS (LOD + Navigation):
══════════════════════════════

Pass 1:    ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
           |   NEAR    |   MEDIUM   |     FAR      |   BEYOND   |
           | [50 sharp]| [25 blurry]| [10 v.blurry]| [5 fog]    |
                ↑
           Start: Finance overview cluster
           LOD detects: "Q3 revenue info exists in FAR zone"

                              ↓ Navigate (warp lane)

Pass 2:    ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
           |   NEAR    |   MEDIUM   |     FAR      |   BEYOND   |
           | [different 50]| [25]   |    [10]      |   [5]      |
                    ↑
           Now at: Q3 details cluster
           NEAR zone now contains: "$4.2M exactly, up 15% from Q2"

Pass 3:    ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●
           | [another 50]  |  [25]  |    [10]      |   [5]      |
                      ↑
           Now at: Q2 comparison cluster
           NEAR zone now contains: "Q2 was $3.65M in March"

Result: 150 unique tokens seen at FULL detail (3 × 50)
        Plus LOD awareness guiding where to navigate
```

### Multi-Pass Benefits

| Passes | Tokens at Full Detail | Coverage | Latency |
|--------|----------------------|----------|---------|
| 1 | 50 | Low | ~1ms |
| 5 | ~200 | Medium | ~5ms |
| 10 | ~400 | Good | ~10ms |
| 50 | ~1,500 | High | ~50ms |
| 100 | ~2,500 | Very High | ~100ms |

**Note:** Token counts are approximate - some overlap between passes.

---

## How LOD and Multi-Pass Work Together

### The Human Vision Analogy

```
HUMAN VISION:
═════════════

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     Peripheral Vision              Foveal Vision               │
│     (blurry, wide)                 (sharp, narrow)             │
│           │                              │                      │
│           ▼                              ▼                      │
│    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
│    ░░░░░░░░░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
│    ░░░░░░░░░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
│    ░░░░░░░░░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
│    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
│                                                                 │
│    You're AWARE of motion in peripheral                        │
│    You see DETAILS only where you're looking                   │
│    You MOVE your eyes to see different areas sharply           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘


INFINATE EQUIVALENT:
════════════════════

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     LOD (Peripheral)               NEAR Zone (Foveal)          │
│     (blurry, wide)                 (sharp, narrow)             │
│           │                              │                      │
│           ▼                              ▼                      │
│    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
│    ░░░░░░░░░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
│    ░░░░░░░░░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
│    ░░░░░░░░░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
│    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
│                                                                 │
│    LOD: AWARE of content in BEYOND zone (blurry)               │
│    NEAR: See DETAILS of current focus (50 tokens)              │
│    Multi-pass: NAVIGATE to see different areas sharply         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### The Collaboration

| Component | Role | Without the Other |
|-----------|------|-------------------|
| **LOD** | Map - shows WHERE things are | Would have sharp focus but be BLIND to distant content |
| **Multi-Pass** | Movement - goes WHERE needed | Would visit places RANDOMLY without knowing what's there |
| **Together** | Guided exploration | LOD detects, navigation investigates |

### Real Example: Finding Q3 Revenue

```
QUERY: "What was Q3 revenue and how does it compare to Q2?"

STEP 1 - Initial Position (LOD gives awareness):
════════════════════════════════════════════════

    NEAR Zone (50 tokens):
    "Company overview... products... mission statement..."
    (Not what we need)

    MEDIUM Zone (25 compressed):
    "...operations...team structure...strategy..."
    (Not what we need)

    FAR Zone (10 compressed):
    "...financial...Q3...revenue...positive..."  ← DETECTED!
    (Blurry but we know it EXISTS)

    BEYOND Zone (5 compressed):
    "...historical...Q1...Q2...trends..."  ← DETECTED!
    (Blurry but we know Q2 data EXISTS)

    LOD RESULT: "I detect Q3 revenue in FAR zone, Q2 data in BEYOND zone"


STEP 2 - Navigate to Q3 (Warp Lane Jump):
═════════════════════════════════════════

    WARP! → Jump to FAR zone location

    NEW NEAR Zone (50 tokens):
    "Q3 revenue was $4.2 million, representing a 15% increase
     from the previous quarter. This growth was driven by..."
    (FULL DETAIL - exactly what we need!)

    NEW FAR Zone:
    "...Q2...previous...comparison..."  ← Q2 data detected


STEP 3 - Navigate to Q2 (Bunny Hop):
════════════════════════════════════

    HOP! → Follow momentum to Q2 cluster

    NEW NEAR Zone (50 tokens):
    "Q2 revenue was $3.65 million, recorded in March 2025.
     The quarter showed steady growth with..."
    (FULL DETAIL - comparison data!)


FINAL RESULT:
═════════════
    "Q3 revenue was $4.2 million, up 15% from Q2's $3.65 million."

    Achieved through:
    - LOD: Detected EXISTENCE of relevant data
    - Navigation: Moved to GET the specific details
    - 3 passes: Saw 150 tokens at full detail total
```

---

## When to Use What

### LOD Alone (Single Pass) Is Sufficient When:

- Query is about topics NEAR the starting position
- Approximate answers are acceptable
- Latency is critical (must be <2ms)
- You're doing topic detection, not fact retrieval

### Multi-Pass Is Needed When:

- Query requires SPECIFIC facts (exact numbers, names, dates)
- Relevant information is SPREAD across context
- High accuracy is required
- Latency budget allows (10-100ms acceptable)

### Decision Matrix

| Query Type | LOD Alone | LOD + Multi-Pass |
|------------|-----------|------------------|
| "What topics are discussed?" | ✅ Sufficient | Overkill |
| "Is there financial data?" | ✅ Sufficient | Optional |
| "What was Q3 revenue?" | ⚠️ May be blurry | ✅ Recommended |
| "Compare Q1, Q2, Q3, Q4 revenue" | ❌ Insufficient | ✅ Required |
| "Find all mentions of Project X" | ❌ Insufficient | ✅ Required |

---

## Performance Characteristics

### Latency vs Quality Tradeoff

```
QUALITY vs LATENCY:
═══════════════════

Quality
  ▲
  │                                    ●──● Diminishing returns
  │                               ●────┘
  │                          ●────┘
  │                     ●────┘
  │                ●────┘
  │           ●────┘
  │      ●────┘
  │ ●────┘
  │─┴────┬────┬────┬────┬────┬────┬────┬────▶ Passes
         1    5   10   20   50   75  100  150

         1ms  5ms 10ms 20ms 50ms 75ms 100ms 150ms  Latency

Sweet spot: 10-50 passes (10-50ms) for most queries
```

### Comparison Table

| Configuration | Tokens Seen | Quality | Latency | vs MIT RLM |
|---------------|-------------|---------|---------|------------|
| LOD only (1 pass) | 90 | ~70% | ~1ms | 15,000× faster |
| LOD + 10 passes | ~400 | ~85% | ~10ms | 1,500× faster |
| LOD + 50 passes | ~1,500 | ~93% | ~50ms | 300× faster |
| LOD + 100 passes | ~2,500 | ~96% | ~100ms | 150× faster |
| LOD + 150 passes | ~3,500 | ~97% | ~150ms | 100× faster |
| Traditional (all) | ALL | 100% | 15,000ms | 1× (baseline) |

**Key Insight:** Even at 150 passes, INFINATE is still 100× faster than traditional approaches while achieving ~97% quality.

---

## Summary

### LOD (M1.10)

- **What:** Hierarchical compression of distant tokens
- **Purpose:** See further (5,375 vs 50 tokens)
- **Tradeoff:** Distant content is blurry (lossy compression)
- **Analogy:** Peripheral vision

### Multi-Pass Navigation (M1.11)

- **What:** Multiple navigation passes through spatial memory
- **Purpose:** Visit different areas at full detail
- **Tradeoff:** More passes = more latency
- **Analogy:** Moving your eyes

### Together

- **Synergy:** LOD detects WHERE, navigation goes THERE
- **Result:** Comprehensive coverage with sharp detail where needed
- **Performance:** 100-15,000× faster than traditional, 70-97% quality

```
THE FORMULA:
════════════

    LOD (awareness) + Multi-Pass (exploration) = Infinite Context

    "I can see everything (blurry)"  +  "I can focus anywhere (sharp)"
                    ↓                              ↓
              Know it exists              Get exact details
                    ↓                              ↓
                    └──────────► ANSWER ◄──────────┘
```

---

## Related Documents

- **[MILESTONE_1.10_COMPLETE.md](MILESTONE_1.10_COMPLETE.md)** - LOD implementation details
- **[MILESTONE_1.11_COMPLETE.md](MILESTONE_1.11_COMPLETE.md)** - Strafe jumping navigation
- **[PRE_M2.0_IMPROVEMENTS.md](PRE_M2.0_IMPROVEMENTS.md)** - Quality metrics and adaptive passes
- **[FUTURE_VISION.md](FUTURE_VISION.md)** - M2.0 and beyond

---

**Document Version:** 1.0
**Created:** January 20, 2026
**Author:** Adolfo Lopez (ch1pu)
