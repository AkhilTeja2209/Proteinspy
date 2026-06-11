"""
High-level parser interface.

Thin wrappers that forward to proteinspy.utils.helpers so that
the rest of the codebase has a single, stable import path.
"""
from __future__ import annotations

from proteinspy.utils.helpers import detect_format, read_structure

__all__ = ["detect_format", "read_structure"]
