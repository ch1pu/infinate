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

# Project Structure - Infinite Spatial AI

**Last Updated:** 2025-12-01
**Total Files:** 78 (source + documentation)
**Project Size:** ~500KB+ (documentation + code)
**Deepest Path:** 6 levels (backend/spatial_engine/core/tests/)

---

## Recently Modified (Last 7 Days)

Based on git history, the most recent work was on Milestone 1.3 (Spatial Attention):

| File | Modified | Description |
|------|----------|-------------|
| `Project/SESSION_2025-01-13_MILESTONE_1.3.md` | Nov 13 | Session notes for Milestone 1.3 |
| `Project/MILESTONE_1.3_COMPLETE.md` | Nov 13 | Completion report for O(k) attention |
| `Project/STATUS.md` | Nov 13 | Updated project status |
| `backend/spatial_engine/core/spatial_attention.py` | Nov 13 | O(k) spatial attention implementation |
| `backend/spatial_engine/core/tests/test_spatial_attention.py` | Nov 13 | 25 comprehensive tests |

---

## Directory Tree

```
/home/ch1pu/infinate/
|
|-- .claude/                            # Claude Code configuration
|   |-- commands-reference.md           # Command reference
|   |-- settings.local.json             # Local settings
|   |-- troubleshooting.md              # Troubleshooting guide
|
|-- Backend/                            # Backend architecture docs
|   |-- API_DESIGN.md                   # API design specification
|   |-- ARCHITECTURE.md                 # Backend architecture
|   |-- AUTHENTICATION.md               # Auth implementation
|   |-- BUILD_CHECKLIST.md              # Build checklist
|   |-- BUSINESS_LOGIC.md               # Business logic docs
|
|-- Database/                           # Database architecture docs
|   |-- BUILD_CHECKLIST.md              # Database build checklist
|   |-- INDEXING_STRATEGY.md            # Indexing strategy
|   |-- MIGRATIONS_PLAN.md              # Migration plans
|   |-- SCHEMA_DESIGN.md                # Schema design
|   |-- SEEDING_PLAN.md                 # Seeding plan
|
|-- Documents/                          # Core technical documentation
|   |-- 3D_RENDERING_ENGINE.md          # 3D rendering specs
|   |-- COMPLETE_SYSTEM_DOCUMENTATION.md # Full system docs
|   |-- CORE_INNOVATION.md              # O(k) complexity proof
|   |-- DOCKER_ARCHITECTURE.md          # Docker setup
|   |-- EVENT_SYSTEM_DESIGN.md          # Event system
|   |-- INFRASTRUCTURE.md               # Infrastructure specs
|   |-- SECURITY_PLAN.md                # Security plan
|   |-- SPATIAL_MODEL_ARCHITECTURE.md   # Spatial AI architecture
|   |-- SYSTEM_OVERVIEW.md              # System overview
|   |-- TESTING_STRATEGY.md             # Testing strategy
|   |-- VECTOR_STORE_INTEGRATION.md     # Vector store integration
|   |-- VISUAL_FEEDBACK_ARCHITECTURE.md # Visual feedback system
|
|-- Frontend/                           # Frontend architecture docs
|   |-- API_INTEGRATION.md              # API integration
|   |-- ARCHITECTURE.md                 # Frontend architecture
|   |-- BUILD_CHECKLIST.md              # Build checklist
|   |-- COMPONENTS_PLAN.md              # Component planning
|   |-- STYLING_STRATEGY.md             # Styling strategy
|
|-- Project/                            # Project management
|   |-- ARCHITECTURE_SUMMARY.md         # Architecture summary
|   |-- DEPENDENCIES.md                 # Dependencies
|   |-- DEVELOPMENT_ROADMAP.md          # Development roadmap
|   |-- HISTORY.md                      # Project history
|   |-- MILESTONE_1.1_COMPLETE.md       # SpatialToken complete
|   |-- MILESTONE_1.2_COMPLETE.md       # Encoding complete
|   |-- MILESTONE_1.3_COMPLETE.md       # Attention complete
|   |-- NEXT_STEPS.md                   # Next steps
|   |-- SESSION_2025-01-13_MILESTONE_1.3.md # Session notes
|   |-- STATUS.md                       # Current status
|   |-- STRUCTURE.md                    # Project structure
|
|-- Security/                           # Security documentation
|   |-- REMEDIATION_COMPLETE.md         # Remediation complete
|   |-- audit-report.md                 # Security audit
|   |-- compliance-checklist.md         # Compliance checklist
|   |-- findings.md                     # Security findings
|   |-- remediation-plan.md             # Remediation plan
|   |-- secrets-scan.md                 # Secrets scan results
|   |-- status.md                       # Security status
|
|-- backend/                            # Python spatial engine
|   |-- .coverage                       # Coverage data
|   |-- .gitignore                      # Git ignore
|   |-- .python-version                 # Python version (3.11)
|   |-- .venv/                          # Virtual environment
|   |-- htmlcov/                        # Coverage reports
|   |-- poetry.lock                     # Poetry lock file
|   |-- pyproject.toml                  # Poetry config
|   |-- spatial_engine/                 # Main Python package
|       |-- __init__.py
|       |-- core/                       # Core algorithms
|       |   |-- __init__.py
|       |   |-- spatial_attention.py    # O(k) attention (346 lines)
|       |   |-- spatial_encoding.py     # 3D encoding (197 lines)
|       |   |-- spatial_token.py        # Token class (124 lines)
|       |   |-- tests/
|       |       |-- __init__.py
|       |       |-- test_spatial_attention.py  # 25 tests
|       |       |-- test_spatial_encoding.py   # 13 tests
|       |       |-- test_spatial_token.py      # 8 tests
|       |-- models/                     # PyTorch models
|       |   |-- __init__.py
|       |   |-- tests/__init__.py
|       |-- utils/                      # Utilities
|       |   |-- __init__.py
|       |   |-- tests/__init__.py
|       |-- vector_store/               # Vector database
|           |-- __init__.py
|           |-- tests/__init__.py
|
|-- docs/                               # Development guides
|   |-- dev/                            # Best practices
|   |   |-- code-quality.md             # Code quality guide
|   |   |-- documentation-standards.md  # Doc standards
|   |   |-- hardware-optimization.md    # Hardware optimization
|   |   |-- python-standards.md         # Python standards
|   |   |-- testing-tdd.md              # TDD workflow
|   |-- milestones/                     # Milestone guides
|       |-- milestone-1.1-spatial-token.md
|       |-- milestone-1.3-spatial-attention.md
|
|-- research/                           # Research documentation
|   |-- AMD_RYZEN_AI_MAX_TECHNICAL_RESEARCH.md
|
|-- CLAUDE.md                           # Main project guide
|-- README.md                           # Project readme
|-- PROJECT_STRUCTURE.md                # This file
```

---

## File Type Distribution

| Type | Count | Description |
|------|-------|-------------|
| `.md` | 55 | Documentation files |
| `.py` | 21 | Python source/test files |
| `.toml` | 1 | Poetry configuration |
| `.json` | 1 | Claude settings |

---

## Code Statistics

### Python Source Files (excluding tests)

| File | Lines | Purpose |
|------|-------|---------|
| `spatial_token.py` | 124 | SpatialToken dataclass |
| `spatial_encoding.py` | 197 | 3D positional encoding |
| `spatial_attention.py` | 346 | O(k) spatial attention |
| **Total** | **667** | Core implementation |

### Python Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `test_spatial_token.py` | 8 | 100% |
| `test_spatial_encoding.py` | 13 | 95% |
| `test_spatial_attention.py` | 25 | 98% |
| **Total** | **46** | **97%** |

---

## Implementation Status

| Component | Status | Lines | Tests |
|-----------|--------|-------|-------|
| SpatialToken (1.1) | Complete | 124 | 8/8 |
| SpatialEncoding (1.2) | Complete | 197 | 13/13 |
| SpatialAttention (1.3) | Complete | 346 | 24/25 |
| SpatialTransformer (1.4) | Pending | 0 | 0 |
| Hierarchical LOD (1.5) | Pending | 0 | 0 |
| Vector Store (1.6) | Pending | 0 | 0 |

---

## Quality Metrics

| Metric | Value | Target |
|--------|-------|--------|
| Test Coverage | 99% | 90% |
| Tests Passing | 53/54 | 100% |
| mypy Errors | 0 | 0 |
| ruff Issues | 0 | 0 |
| black Formatted | Yes | Yes |

---

## Notes

- **Virtual Environment:** `.venv/` contains Poetry-managed dependencies
- **Coverage Reports:** `htmlcov/` contains HTML coverage reports
- **1 Failed Test:** `test_device_placement` - GPU hardware incompatibility (RTX 5060 CUDA sm_120 not supported)
- **Next Milestone:** 1.4 - Spatial Transformer Block

---

**Generated:** 2025-12-01
**Status:** Up to date
