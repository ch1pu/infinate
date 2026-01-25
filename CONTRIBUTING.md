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

# Contributing to Infinite

Thank you for your interest in contributing to Infinite! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing Requirements](#testing-requirements)
- [Commit Conventions](#commit-conventions)
- [Pull Request Process](#pull-request-process)
- [Developer Certificate of Origin](#developer-certificate-of-origin)
- [Getting Help](#getting-help)

---

## Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

---

## Getting Started

### Prerequisites

- **Python 3.11+** (required)
- **Poetry** (dependency management)
- **Git** (version control)
- **WSL2/Linux** (recommended for development)

### Finding Issues to Work On

1. Check the [Issues](https://github.com/ch1pu/infinate/issues) page
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on an issue to express interest before starting work
4. Wait for maintainer confirmation before beginning

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/infinate.git
cd infinate
```

### 2. Set Up Python Environment

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install Poetry
pip install --upgrade pip
pip install poetry

# Install dependencies (including dev dependencies)
poetry install
```

### 3. Verify Installation

```bash
# Check versions
poetry run python --version  # Should be 3.11+
poetry run pytest --version

# Run tests to verify setup
poetry run pytest -m unit -v
```

### 4. Set Up Pre-commit Hooks (Recommended)

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

---

## Code Style

We enforce consistent code style using automated tools.

### Python Code Style

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Black** | Code formatting | `pyproject.toml` |
| **Ruff** | Linting | `pyproject.toml` |
| **mypy** | Type checking | `pyproject.toml` (strict mode) |

### Running Code Quality Checks

```bash
# Format code with Black
poetry run black spatial_engine/

# Lint with Ruff (auto-fix)
poetry run ruff check --fix spatial_engine/

# Type check with mypy (strict mode)
poetry run mypy spatial_engine/

# Run all checks
poetry run black spatial_engine/ && poetry run ruff check spatial_engine/ && poetry run mypy spatial_engine/
```

### Type Hints

All public functions and methods **must** have type hints:

```python
# ✅ Good
def calculate_distance(
    position_a: tuple[float, float, float],
    position_b: tuple[float, float, float]
) -> float:
    """Calculate Euclidean distance between two 3D positions."""
    ...

# ❌ Bad - missing type hints
def calculate_distance(position_a, position_b):
    ...
```

### Docstrings

Use Google-style docstrings for all public APIs:

```python
def spatial_attention(
    query: torch.Tensor,
    keys: torch.Tensor,
    k: int = 50
) -> torch.Tensor:
    """Compute O(k) spatial attention.

    Args:
        query: Query tensor of shape (batch, seq_len, dim).
        keys: Key tensor of shape (batch, seq_len, dim).
        k: Number of nearest neighbors to attend to.

    Returns:
        Attention output tensor of shape (batch, seq_len, dim).

    Raises:
        ValueError: If k is greater than sequence length.
    """
    ...
```

---

## Testing Requirements

### Coverage Requirements

- **Minimum coverage: 90%**
- All new code must include tests
- Tests must pass before PR can be merged

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run unit tests only (fast)
poetry run pytest -m unit

# Run with coverage report
poetry run pytest --cov=spatial_engine --cov-report=html

# Fail if coverage below 90%
poetry run pytest --cov=spatial_engine --cov-fail-under=90
```

### Test-Driven Development (TDD)

We follow TDD methodology. Write tests first:

```python
# 1. RED: Write failing test
def test_spatial_token_distance():
    token1 = SpatialToken(position=(0, 0, 0), ...)
    token2 = SpatialToken(position=(3, 4, 0), ...)
    assert token1.distance_to(token2) == 5.0  # FAILS

# 2. GREEN: Write minimal implementation to pass
# 3. REFACTOR: Improve code quality, add docs
```

### Test File Naming

- Test files: `test_<module>.py`
- Test functions: `test_<description>()`
- Test classes: `Test<ClassName>`

---

## Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/) for clear, semantic commit history.

### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |

### Examples

```bash
# Feature
git commit -m "feat(core): implement spatial attention mechanism"

# Bug fix
git commit -m "fix(attention): correct distance calculation for edge cases"

# Documentation
git commit -m "docs(readme): add installation instructions"

# With body
git commit -m "feat(core): add k-nearest neighbor search

Implements efficient spatial indexing using R-tree.
Achieves O(log n) lookup time.

Refs: #123"
```

---

## Pull Request Process

### 1. Create a Branch

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow code style guidelines
- Write tests for new code
- Update documentation if needed
- Keep commits atomic and well-described

### 3. Verify Before Submitting

```bash
# Run full quality check
poetry run pytest --cov=spatial_engine --cov-fail-under=90
poetry run mypy spatial_engine/
poetry run ruff check spatial_engine/
poetry run black --check spatial_engine/
```

### 4. Submit Pull Request

1. Push your branch to your fork
2. Open a PR against `main` branch
3. Fill out the PR template completely
4. Link related issues using `Fixes #123` or `Refs #123`

### 5. PR Review Process

- All PRs require at least one approval
- CI must pass (tests, linting, type checking)
- Address all review comments
- Squash commits before merge (if requested)

### PR Title Format

Use conventional commit format for PR titles:

```
feat(core): implement spatial attention mechanism
fix(api): resolve memory leak in token cache
docs(contributing): add development setup guide
```

---

## Developer Certificate of Origin

By contributing to this project, you certify that:

1. The contribution was created in whole or in part by you and you have the right to submit it under the Apache 2.0 License; or

2. The contribution is based upon previous work that, to the best of your knowledge, is covered under an appropriate open source license and you have the right under that license to submit that work with modifications; or

3. The contribution was provided directly to you by some other person who certified (1) or (2) and you have not modified it.

### Sign-off Your Commits

Add a sign-off line to your commits using `-s` flag:

```bash
git commit -s -m "feat(core): implement spatial attention"
```

This adds a line like:
```
Signed-off-by: Your Name <your.email@example.com>
```

---

## Getting Help

### Resources

- **Documentation**: Check `docs/` directory
- **README**: [README.md](README.md)
- **Architecture**: [Documents/SPATIAL_MODEL_ARCHITECTURE.md](Documents/SPATIAL_MODEL_ARCHITECTURE.md)

### Communication

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Pull Request Comments**: For code-specific feedback

### Response Times

- We aim to respond to issues within 48 hours
- PR reviews typically take 1-3 business days
- Complex PRs may take longer

---

## Recognition

Contributors are recognized in:
- GitHub's contributor graph
- Release notes for significant contributions
- README.md for major features

---

## License

By contributing to Infinite, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).

---

Thank you for contributing to Infinite! Your efforts help advance the frontier of spatial AI research.
