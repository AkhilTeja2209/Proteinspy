"""
Shared utility functions used across Proteinspy modules.
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Optional

import gemmi

from proteinspy.exceptions import FileNotFoundError, InvalidFileFormatError

logger = logging.getLogger(__name__)

_CIF_EXTS = {".cif", ".mmcif", ".pdbx"}
_PDB_EXTS = {".pdb", ".ent"}
_COMPRESSED_EXTS = {".gz"}


def detect_format(path: str) -> str:
    """
    Detect the structure file format from its extension.

    Args:
        path: Path to the structure file.

    Returns:
        One of ``"cif"`` or ``"pdb"``.

    Raises:
        InvalidFileFormatError: If the extension is not recognised.
    """
    base = path
    if base.endswith(".gz"):
        base = base[:-3]

    _, ext = os.path.splitext(base.lower())
    if ext in _CIF_EXTS:
        return "cif"
    if ext in _PDB_EXTS:
        return "pdb"
    raise InvalidFileFormatError(
        f"Unrecognised file extension '{ext}'. "
        f"Supported formats: {sorted(_CIF_EXTS | _PDB_EXTS)} (optionally .gz compressed)"
    )


@lru_cache(maxsize=32)
def read_structure(path: str) -> gemmi.Structure:
    """
    Parse a structure file into a gemmi.Structure.

    Results are cached by path so repeated calls within a session are free.

    Args:
        path: Path to a .cif, .pdb, .ent, or compressed (.gz) variant.

    Returns:
        Parsed gemmi.Structure.

    Raises:
        FileNotFoundError: If path does not exist.
        InvalidFileFormatError: If the file cannot be parsed.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Structure file not found: {path}")

    fmt = detect_format(path)
    logger.debug("Reading structure %s (format=%s)", path, fmt)

    try:
        st = gemmi.read_structure(path)
    except Exception as exc:
        logger.error("Failed to parse %s: %s", path, exc)
        raise InvalidFileFormatError(
            f"Cannot parse structure file '{path}': {exc}"
        ) from exc

    return st


def angstrom(value: Optional[float]) -> Optional[str]:
    """Format value as an Angstrom string, or return None."""
    return f"{value:.2f} Å" if value is not None else None
