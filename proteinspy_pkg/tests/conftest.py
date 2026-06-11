"""
Shared pytest fixtures for Proteinspy tests.
"""

from __future__ import annotations

import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_CIF = os.path.join(FIXTURES_DIR, "10AJ.cif")


@pytest.fixture(scope="session")
def sample_cif() -> str:
    """Return the absolute path to the bundled test CIF file."""
    assert os.path.exists(SAMPLE_CIF), f"Test fixture missing: {SAMPLE_CIF}"
    return SAMPLE_CIF


@pytest.fixture(scope="session")
def missing_file(tmp_path_factory) -> str:
    """Return a path that does not exist on disk."""
    return str(tmp_path_factory.mktemp("data") / "nonexistent.cif")
