# Contributing to Proteinspy

Thank you for considering a contribution! Every improvement — bug fix,
new analysis, documentation update — is welcome.

---

## Table of Contents

1. [Getting started](#getting-started)
2. [Development setup](#development-setup)
3. [Running tests](#running-tests)
4. [Code standards](#code-standards)
5. [Submitting a PR](#submitting-a-pr)
6. [Adding a new analysis](#adding-a-new-analysis)

---

## Getting started

1. Fork the repository on GitHub.
2. Clone your fork:

   ```bash
   git clone https://github.com/<your-username>/Proteinspy.git
   cd Proteinspy/proteinspy_pkg
   ```

3. Create a feature branch:

   ```bash
   git checkout -b feat/my-new-analysis
   ```

---

## Development setup

Proteinspy uses [Poetry](https://python-poetry.org/) for dependency management.

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install all dependencies including dev extras
poetry install --with dev

# Activate the virtual environment
poetry shell
```

---

## Running tests

```bash
# All tests with coverage report
poetry run pytest

# Fast run — no coverage
poetry run pytest --no-cov -q

# Single test file
poetry run pytest tests/unit/test_analysis_basic.py -v

# Integration tests only
poetry run pytest tests/integration/ -v
```

---

## Code standards

| Tool | Purpose | Run with |
|------|---------|----------|
| **Black** | Auto-formatting | `poetry run black proteinspy tests` |
| **Pylint** | Linting | `poetry run pylint proteinspy` |
| **Mypy** | Static type checking | `poetry run mypy proteinspy` |

Requirements:
- PEP 8 compliant (Black handles formatting automatically)
- Type hints on all public functions
- Docstrings on all public functions using Google-style format
- Test coverage >= 80% for new code

---

## Submitting a PR

1. Ensure all tests pass and the linter is happy
2. Update `docs/` and `CHANGELOG.md` if relevant
3. Open a pull request against `main`
4. Link the related issue in the PR description
5. Wait for CI to go green before requesting review

---

## Adding a new analysis

New analyses belong in `proteinspy/analysis/`:
- **Basic** metadata → `basic.py`
- **Advanced** structural analyses → `advanced.py`
- **New module** for large feature sets → new file, imported in `analysis/__init__.py`

Every new analysis function must:
1. Accept `path: str` as its first argument
2. Return a plain `dict` (JSON-serialisable)
3. Raise `AnalysisError` on failure
4. Have a docstring with `Args`, `Returns`, `Raises`, and at least one `Example`
5. Be wired into the CLI in `proteinspy/cli/main.py`
6. Have unit tests in `tests/unit/` and CLI tests in `tests/integration/test_cli.py`

```python
# Template for a new analysis function
from __future__ import annotations
from typing import Any, Dict
from proteinspy.exceptions import AnalysisError
from proteinspy.utils.helpers import read_structure

def get_my_feature(path: str) -> Dict[str, Any]:
    """
    One-line summary.

    Args:
        path: Path to a supported structure file.

    Returns:
        Dictionary with keys ``...``.

    Raises:
        AnalysisError: If the analysis fails.

    Example:
        >>> result = get_my_feature("protein.cif")
    """
    try:
        st = read_structure(path)
        # ... implementation ...
        return {"result": ...}
    except Exception as exc:
        raise AnalysisError(f"my_feature failed: {exc}") from exc
```
