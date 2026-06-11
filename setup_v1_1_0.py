#!/usr/bin/env python3
"""
Proteinspy v1.1.0 — one-shot setup script.

Run from the ROOT of your Proteinspy repository:
    python setup_v1_1_0.py

What it does:
  1. Creates all new directories
  2. Writes every new/modified file
  3. Copies 10AJ.cif into tests/fixtures/
  4. Adds a deprecation comment to analysis.py
  5. Prints the git commands to run afterward
"""
import os
import shutil
import sys
import textwrap

# ── verify we are in the right place ────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if not os.path.isdir(os.path.join(ROOT, "proteinspy_pkg")):
    print("ERROR: Run this script from the ROOT of the Proteinspy repository.")
    print("       (The folder that contains proteinspy_pkg/ and README.md)")
    sys.exit(1)

PKG = os.path.join(ROOT, "proteinspy_pkg", "proteinspy")
TESTS = os.path.join(ROOT, "proteinspy_pkg", "tests")
GH = os.path.join(ROOT, ".github")

written = []

def w(rel_path: str, content: str) -> None:
    """Write *content* to *rel_path* (relative to repo root), creating dirs."""
    full = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    written.append(rel_path)
    print(f"  [write]  {rel_path}")


# ════════════════════════════════════════════════════════════════════════════
# FILE CONTENTS
# All content strings use r'''...''' so that backslash sequences
# (e.g. \b in Click docstrings) are written verbatim to disk.
# ════════════════════════════════════════════════════════════════════════════

F_EXCEPTIONS = r'''"""
Custom exceptions for Proteinspy.

All library-specific errors inherit from ProteinsyError so callers
can catch the whole family with a single except clause.
"""


class ProteinsyError(Exception):
    """Base exception for all Proteinspy errors."""


class FileNotFoundError(ProteinsyError):
    """Raised when the requested structure file does not exist."""


class InvalidFileFormatError(ProteinsyError):
    """Raised when a file cannot be parsed as a supported structure format."""


class AnalysisError(ProteinsyError):
    """Raised when an analysis step fails unexpectedly."""


class ExportError(ProteinsyError):
    """Raised when writing output to disk or serialising results fails."""
'''


F_UTILS_INIT = r'''"""Utility helpers for Proteinspy."""
'''

F_UTILS_HELPERS = r'''"""
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
'''


F_CORE_INIT = r'''"""Core parsing and validation layer."""
'''

F_CORE_PARSER = r'''"""
High-level parser interface.

Thin wrappers that forward to proteinspy.utils.helpers so that
the rest of the codebase has a single, stable import path.
"""
from __future__ import annotations

from proteinspy.utils.helpers import detect_format, read_structure

__all__ = ["detect_format", "read_structure"]
'''

F_CORE_VALIDATOR = r'''"""
Structure quality validator.

Produces human-readable warnings about common structural problems
without requiring external tools (DSSP, MolProbity, etc.).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from proteinspy.utils.helpers import read_structure

logger = logging.getLogger(__name__)

_RES_HIGH   = 2.0
_RES_MEDIUM = 3.0
_RES_LOW    = 3.5
_RES_POOR   = 4.5
_MISSING_WARN = 0.10


def validate_structure(path: str) -> Dict[str, Any]:
    """
    Run a battery of quick quality checks on a structure file.

    Checks performed (all derived from structure metadata — no external tools):
    * Crystallographic resolution and experimental method
    * Missing residue fraction per chain
    * Presence of a unit cell / space group
    * Number of models (NMR ensembles have many)

    Args:
        path: Path to a supported structure file.

    Returns:
        Dictionary with keys:
            warnings (list[str]): Human-readable warning messages.
            info (list[str]): Informational notes (not errors).
            pass (bool): True if no warnings were generated.
            resolution (float | None): Resolution in Angstroms.
            method (str): Experimental method string.
            model_count (int): Number of models in the file.
            missing_fraction (float): Fraction of residues missing.
    """
    import gemmi
    st = read_structure(path)
    warnings: List[str] = []
    info: List[str] = []

    resolution: Optional[float] = st.resolution if st.resolution and st.resolution > 0 else None
    method = "UNKNOWN"
    try:
        block = gemmi.cif.read(path).sole_block()
        m = block.find_value("_exptl.method")
        if m and m not in {"?", "."}:
            method = m.strip().strip("'\"")
    except Exception:
        pass

    if resolution is None:
        if method.upper() not in {"SOLUTION NMR", "SOLID-STATE NMR", "NEUTRON DIFFRACTION"}:
            warnings.append(
                "Resolution not available — structure may be a theoretical model "
                "or experimental metadata is incomplete."
            )
    else:
        if resolution > _RES_POOR:
            warnings.append(
                f"Very low resolution ({resolution:.2f} Å > {_RES_POOR} Å). "
                "Atomic positions are approximate; ligand binding sites may be unreliable."
            )
        elif resolution > _RES_LOW:
            warnings.append(
                f"Low resolution ({resolution:.2f} Å). "
                "Side-chain positions should be interpreted with caution."
            )
        elif resolution > _RES_MEDIUM:
            info.append(f"Moderate resolution ({resolution:.2f} Å).")
        else:
            info.append(f"Good resolution ({resolution:.2f} Å).")

    model_count = len(st)
    if model_count > 1:
        info.append(
            f"NMR ensemble detected ({model_count} models). "
            "Only the first model is used in analyses."
        )

    total_seq = 0
    total_missing = 0
    for chain in st[0]:
        polymer = chain.get_polymer()
        if len(polymer) == 0:
            continue
        entity_id = next((r.entity_id for r in polymer), None)
        if entity_id is None:
            continue
        entity = st.get_entity(entity_id)
        if entity is None:
            continue
        full_len = len(entity.full_sequence)
        observed = sum(1 for r in polymer if r.label_seq is not None)
        total_seq += full_len
        total_missing += max(0, full_len - observed)

    missing_fraction = (total_missing / total_seq) if total_seq > 0 else 0.0

    if missing_fraction > _MISSING_WARN:
        warnings.append(
            f"{missing_fraction * 100:.1f}% of residues are missing from ATOM records. "
            "Flexible loops or terminal regions may be disordered."
        )
    elif total_seq > 0:
        info.append(
            f"Low missing-residue fraction ({missing_fraction * 100:.1f}%) — good model completeness."
        )

    if not st.cell.is_crystal():
        info.append("No crystallographic unit cell found (expected for NMR or theoretical models).")

    return {
        "warnings": warnings,
        "info": info,
        "pass": len(warnings) == 0,
        "resolution": resolution,
        "method": method,
        "model_count": model_count,
        "missing_fraction": missing_fraction,
    }
'''


F_ANALYSIS_INIT = r'''"""Analysis sub-package — basic and advanced structure analyses."""
from proteinspy.analysis.basic import (
    get_resolution,
    get_chains,
    get_ligands,
    get_missing_residues,
)
from proteinspy.analysis.advanced import (
    get_bfactor_stats,
    get_disulfide_bonds,
    get_chain_interface,
)

__all__ = [
    "get_resolution",
    "get_chains",
    "get_ligands",
    "get_missing_residues",
    "get_bfactor_stats",
    "get_disulfide_bonds",
    "get_chain_interface",
]
'''


F_ANALYSIS_BASIC = r'''"""
Basic structure analyses.

All functions accept a file path and return a plain dictionary so results
are easily serialised to JSON or CSV. Structures are parsed via the cached
read_structure() helper, so re-analysing the same file is free.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import gemmi

from proteinspy.exceptions import AnalysisError
from proteinspy.utils.helpers import read_structure

logger = logging.getLogger(__name__)

_STANDARD_AA: frozenset = frozenset([
    "ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE",
    "LEU","LYS","MET","PHE","PRO","SER","THR","TRP","TYR","VAL",
    "SEC","PYL","UNK",
])
_STANDARD_NUC: frozenset = frozenset(["DA","DC","DG","DT","DI","A","C","G","U","I"])
_SOLVENT: frozenset = frozenset([
    "HOH","WAT","DOD","SO4","EDO","GOL","PEG","ACT","MPD",
    "PO4","CLR","DMS","FMT","TRS","IOD","BME","EPE",
])


def get_resolution(path: str) -> Dict[str, Any]:
    """
    Extract crystallographic or cryo-EM resolution from a structure file.

    Falls back to direct CIF tag parsing when the high-level Structure
    does not expose a resolution value.

    Args:
        path: Path to a .cif, .pdb, or .ent structure file (optionally .gz).

    Returns:
        Dictionary with keys:
            resolution (float | None): Resolution in Angstroms, or None.
            unit (str | None): "Å" when resolution is present, else None.
            method (str): Experimental method string.

    Raises:
        FileNotFoundError: If path does not exist.
        InvalidFileFormatError: If the file cannot be parsed.
        AnalysisError: If the analysis step itself fails.

    Example:
        >>> result = get_resolution("protein.cif")
        >>> print(f"Resolution: {result['resolution']} {result['unit']}")
        Resolution: 2.1 Å
    """
    try:
        st = read_structure(path)
        res: Optional[float] = st.resolution if st.resolution and st.resolution > 0 else None

        if res is None:
            try:
                block = gemmi.cif.read(path).sole_block()
                for tag in [
                    "_refine.ls_d_res_high",
                    "_reflns.d_resolution_high",
                    "_em_3d_reconstruction.resolution",
                ]:
                    val = block.find_value(tag)
                    if val and val not in {"?", "."}:
                        res = float(val)
                        break
            except Exception:
                pass

        method = "UNKNOWN"
        try:
            block = gemmi.cif.read(path).sole_block()
            m = block.find_value("_exptl.method")
            if m and m not in {"?", "."}:
                method = m.strip().strip("'\"")
        except Exception:
            pass

        return {"resolution": res, "unit": "Å" if res else None, "method": method}

    except Exception as exc:
        if "FileNotFound" in type(exc).__name__ or "InvalidFileFormat" in type(exc).__name__:
            raise
        raise AnalysisError(f"Resolution analysis failed for '{path}': {exc}") from exc


def get_chains(path: str) -> Dict[str, Any]:
    """
    Report all polymer chains in the first model of a structure.

    Args:
        path: Path to a supported structure file.

    Returns:
        Dictionary with keys:
            chain_count (int): Number of unique chains.
            chains (list[dict]): One entry per chain with id, type, residue_count.

    Raises:
        FileNotFoundError: If path does not exist.
        AnalysisError: If chain enumeration fails.
    """
    try:
        st = read_structure(path)
        chains: List[Dict[str, Any]] = []
        seen: set = set()

        for model in st:
            for chain in model:
                if chain.name in seen:
                    continue
                seen.add(chain.name)
                polymer = chain.get_polymer()
                ptype = (
                    str(polymer.check_polymer_type()) if len(polymer) > 0 else "non-polymer"
                )
                chains.append({
                    "id": chain.name,
                    "type": ptype,
                    "residue_count": sum(1 for _ in chain),
                })

        return {"chain_count": len(chains), "chains": chains}

    except Exception as exc:
        if "FileNotFound" in type(exc).__name__ or "InvalidFileFormat" in type(exc).__name__:
            raise
        raise AnalysisError(f"Chain analysis failed for '{path}': {exc}") from exc


def get_ligands(path: str) -> Dict[str, Any]:
    """
    Identify non-polymer, non-solvent ligand molecules in a structure.

    Args:
        path: Path to a supported structure file.

    Returns:
        Dictionary with keys:
            ligand_count (int): Total number of unique ligand instances.
            has_ligand (bool): True when ligand_count > 0.
            ligands (list[dict]): One entry per ligand with id, chain, seq_num.

    Raises:
        FileNotFoundError: If path does not exist.
        AnalysisError: If ligand detection fails.
    """
    try:
        st = read_structure(path)
        found: List[Dict[str, Any]] = []
        seen: set = set()

        for model in st:
            for chain in model:
                for res in chain:
                    if res.entity_type not in (
                        gemmi.EntityType.NonPolymer,
                        gemmi.EntityType.Unknown,
                    ):
                        continue
                    name = res.name.strip()
                    if name in _STANDARD_AA or name in _STANDARD_NUC or name in _SOLVENT:
                        continue
                    key = f"{name}:{chain.name}:{res.seqid}"
                    if key in seen:
                        continue
                    seen.add(key)
                    found.append({"id": name, "chain": chain.name, "seq_num": str(res.seqid)})

        if not found:
            try:
                block = gemmi.cif.read(path).sole_block()
                table = block.find("_pdbx_entity_nonpoly.", ["name", "comp_id"])
                for row in table:
                    comp = row[1].strip().strip("'\"")
                    if comp in _SOLVENT or comp in _STANDARD_AA:
                        continue
                    if comp in seen:
                        continue
                    seen.add(comp)
                    found.append({
                        "id": comp,
                        "chain": "?",
                        "seq_num": "?",
                        "name": row[0].strip().strip("'\""),
                    })
            except Exception:
                pass

        return {"ligand_count": len(found), "has_ligand": len(found) > 0, "ligands": found}

    except Exception as exc:
        if "FileNotFound" in type(exc).__name__ or "InvalidFileFormat" in type(exc).__name__:
            raise
        raise AnalysisError(f"Ligand analysis failed for '{path}': {exc}") from exc


def get_missing_residues(path: str) -> Dict[str, Any]:
    """
    Find residues present in the deposited sequence but absent from ATOM records.

    Args:
        path: Path to a supported structure file.

    Returns:
        Dictionary with keys:
            missing_count (int): Number of missing residues found.
            missing_residues (list[dict]): One entry per residue with chain, residue, seq_num.

    Raises:
        FileNotFoundError: If path does not exist.
        AnalysisError: If the analysis fails.
    """
    try:
        st = read_structure(path)
        missing: List[Dict[str, Any]] = []

        for model in st:
            for chain in model:
                polymer = chain.get_polymer()
                if len(polymer) == 0:
                    continue
                observed = {str(r.label_seq) for r in polymer if r.label_seq is not None}
                entity_id = next((r.entity_id for r in polymer), None)
                if entity_id is None:
                    continue
                entity = st.get_entity(entity_id)
                if entity is None:
                    continue
                for idx, mon in enumerate(entity.full_sequence, start=1):
                    if str(idx) not in observed:
                        missing.append({"chain": chain.name, "seq_num": idx, "residue": mon})

        cif_missing: List[Dict[str, Any]] = []
        try:
            block = gemmi.cif.read(path).sole_block()
            table = block.find(
                "_pdbx_unobs_or_zero_occ_residues.",
                ["auth_asym_id", "auth_comp_id", "auth_seq_id", "PDB_model_num", "polymer_flag"],
            )
            for row in table:
                if row[4].strip() != "Y":
                    continue
                cif_missing.append({
                    "chain": row[0].strip(),
                    "residue": row[1].strip(),
                    "seq_num": row[2].strip(),
                    "model": row[3].strip(),
                })
        except Exception:
            pass

        final = cif_missing if cif_missing else missing
        return {"missing_count": len(final), "missing_residues": final}

    except Exception as exc:
        if "FileNotFound" in type(exc).__name__ or "InvalidFileFormat" in type(exc).__name__:
            raise
        raise AnalysisError(f"Missing residue analysis failed for '{path}': {exc}") from exc
'''


F_ANALYSIS_ADVANCED = r'''"""
Advanced structure analyses.

All analyses are implemented using only gemmi — no external binaries required.
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List

from proteinspy.exceptions import AnalysisError
from proteinspy.utils.helpers import read_structure

logger = logging.getLogger(__name__)

_SS_DIST_MAX     = 2.5
_INTERFACE_CUTOFF = 5.0


def get_bfactor_stats(path: str) -> Dict[str, Any]:
    """
    Compute isotropic B-factor (temperature factor) statistics.

    B-factors reflect atomic mobility/disorder. High mean values or a large
    spread can indicate flexible regions or modelling problems.

    Args:
        path: Path to a supported structure file.

    Returns:
        Dictionary with keys:
            overall (dict): Global stats — min, max, mean, std, atom_count.
            by_chain (list[dict]): Per-chain breakdown with the same keys plus chain_id.

    Raises:
        AnalysisError: If B-factor extraction fails.
    """
    try:
        st = read_structure(path)
        all_bfactors: List[float] = []
        by_chain: List[Dict[str, Any]] = []

        for chain in st[0]:
            chain_bfactors: List[float] = []
            for res in chain:
                for atom in res:
                    b = atom.b_iso
                    if b > 0:
                        chain_bfactors.append(b)
                        all_bfactors.append(b)
            if chain_bfactors:
                by_chain.append({"chain_id": chain.name, **_compute_stats(chain_bfactors)})

        return {"overall": _compute_stats(all_bfactors), "by_chain": by_chain}

    except Exception as exc:
        if "FileNotFound" in type(exc).__name__ or "InvalidFileFormat" in type(exc).__name__:
            raise
        raise AnalysisError(f"B-factor analysis failed for '{path}': {exc}") from exc


def _compute_stats(values: List[float]) -> Dict[str, Any]:
    """Return min/max/mean/std/count for a list of floats."""
    if not values:
        return {"min": None, "max": None, "mean": None, "std": None, "atom_count": 0}
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return {
        "min": round(min(values), 3),
        "max": round(max(values), 3),
        "mean": round(mean, 3),
        "std": round(math.sqrt(variance), 3),
        "atom_count": n,
    }


def get_disulfide_bonds(path: str) -> Dict[str, Any]:
    """
    Detect disulfide bonds by measuring SG-SG distances between CYS residues.

    A pair of cysteine sulfur atoms (SG) separated by <= 2.5 Å is treated as
    a disulfide bond.

    Args:
        path: Path to a supported structure file.

    Returns:
        Dictionary with keys:
            bond_count (int): Number of disulfide bonds found.
            bonds (list[dict]): One entry per bond with chain_a, res_a, seqid_a,
                chain_b, res_b, seqid_b, distance_A.

    Raises:
        AnalysisError: If bond detection fails.
    """
    try:
        st = read_structure(path)
        model = st[0]
        sg_atoms: List[Dict[str, Any]] = []

        for chain in model:
            for res in chain:
                if res.name not in ("CYS", "DCYS"):
                    continue
                for atom in res:
                    if atom.name == "SG":
                        sg_atoms.append({
                            "chain": chain.name,
                            "res": res.name,
                            "seqid": str(res.seqid),
                            "pos": atom.pos,
                        })

        bonds: List[Dict[str, Any]] = []
        for i, a in enumerate(sg_atoms):
            for b in sg_atoms[i + 1:]:
                dist = a["pos"].dist(b["pos"])
                if dist <= _SS_DIST_MAX:
                    bonds.append({
                        "chain_a": a["chain"], "res_a": a["res"], "seqid_a": a["seqid"],
                        "chain_b": b["chain"], "res_b": b["res"], "seqid_b": b["seqid"],
                        "distance_A": round(dist, 3),
                    })

        return {"bond_count": len(bonds), "bonds": bonds}

    except Exception as exc:
        if "FileNotFound" in type(exc).__name__ or "InvalidFileFormat" in type(exc).__name__:
            raise
        raise AnalysisError(f"Disulfide bond detection failed for '{path}': {exc}") from exc


def get_chain_interface(path: str, cutoff: float = _INTERFACE_CUTOFF) -> Dict[str, Any]:
    """
    Identify residues at inter-chain interfaces using Ca distance.

    Two residues on different chains are considered to be at the interface
    when their Ca atoms are within cutoff Angstroms of each other.

    Args:
        path: Path to a supported structure file.
        cutoff: Distance threshold in Angstroms (default 5.0 Å).

    Returns:
        Dictionary with keys:
            interface_count (int): Number of unique chain-pair interfaces.
            interfaces (list[dict]): One entry per chain pair with chain_a, chain_b,
                contact_pairs, residues_a, residues_b.

    Raises:
        AnalysisError: If interface calculation fails.
    """
    try:
        st = read_structure(path)
        model = st[0]
        ca_index: Dict[str, List[tuple]] = {}

        for chain in model:
            polymer = chain.get_polymer()
            if len(polymer) == 0:
                continue
            positions = []
            for res in polymer:
                ca = res.find_atom("CA", "\0")
                if ca:
                    positions.append((str(res.seqid), ca.pos))
            if positions:
                ca_index[chain.name] = positions

        chain_names = list(ca_index.keys())
        interface_map: Dict[str, Dict[str, Any]] = {}

        for i, ca_name in enumerate(chain_names):
            for cb_name in chain_names[i + 1:]:
                key = f"{ca_name}|{cb_name}"
                res_a: set = set()
                res_b: set = set()
                contact_pairs = 0
                for seq_a, pos_a in ca_index[ca_name]:
                    for seq_b, pos_b in ca_index[cb_name]:
                        if pos_a.dist(pos_b) <= cutoff:
                            res_a.add(seq_a)
                            res_b.add(seq_b)
                            contact_pairs += 1
                if contact_pairs > 0:
                    interface_map[key] = {
                        "chain_a": ca_name,
                        "chain_b": cb_name,
                        "contact_pairs": contact_pairs,
                        "residues_a": sorted(res_a, key=lambda x: int(x) if x.isdigit() else 0),
                        "residues_b": sorted(res_b, key=lambda x: int(x) if x.isdigit() else 0),
                    }

        interfaces = list(interface_map.values())
        return {"interface_count": len(interfaces), "interfaces": interfaces}

    except Exception as exc:
        if "FileNotFound" in type(exc).__name__ or "InvalidFileFormat" in type(exc).__name__:
            raise
        raise AnalysisError(f"Chain interface analysis failed for '{path}': {exc}") from exc
'''


F_IO_INIT = r'''"""I/O helpers — writers for structure analysis results."""
from proteinspy.io.writers import to_json, to_csv, write_output

__all__ = ["to_json", "to_csv", "write_output"]
'''

F_IO_WRITERS = r'''"""
Output formatters for analysis results.

Supported formats: json, csv, tsv.
"""
from __future__ import annotations

import csv
import io
import json
import logging
import os
from typing import Any, Dict, Literal, Optional

from proteinspy.exceptions import ExportError

logger = logging.getLogger(__name__)

OutputFormat = Literal["json", "csv", "tsv"]


def to_json(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Serialise analysis results to a JSON string.

    Args:
        data: Dictionary returned by any analysis function.
        indent: Pretty-print indentation level (default 2).

    Returns:
        UTF-8 JSON string.
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ExportError(f"JSON serialisation failed: {exc}") from exc


def to_csv(data: Dict[str, Any], delimiter: str = ",") -> str:
    """
    Serialise analysis results to a flat CSV/TSV string.

    List-valued keys are expanded so that each list element becomes one row.
    Scalar keys are repeated on every row.

    Args:
        data: Dictionary returned by any analysis function.
        delimiter: Field separator — "," for CSV, "\\t" for TSV.

    Returns:
        String containing header + data rows.
    """
    try:
        buf = io.StringIO()
        scalars: Dict[str, Any] = {}
        list_val: list = []

        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                list_val = v
            elif not isinstance(v, (list, dict)):
                scalars[k] = v

        if list_val:
            fieldnames = list(scalars.keys()) + list(list_val[0].keys())
            writer = csv.DictWriter(
                buf, fieldnames=fieldnames, delimiter=delimiter, extrasaction="ignore"
            )
            writer.writeheader()
            for row in list_val:
                writer.writerow({**scalars, **row})
        else:
            writer = csv.DictWriter(buf, fieldnames=list(scalars.keys()), delimiter=delimiter)
            writer.writeheader()
            writer.writerow(scalars)

        return buf.getvalue()

    except Exception as exc:
        raise ExportError(f"CSV serialisation failed: {exc}") from exc


def write_output(
    data: Dict[str, Any],
    fmt: OutputFormat,
    output_path: Optional[str] = None,
) -> str:
    """
    Format data and optionally write it to a file.

    Args:
        data: Analysis result dictionary.
        fmt: One of "json", "csv", or "tsv".
        output_path: If given, the formatted string is written to this path.

    Returns:
        Formatted string.

    Raises:
        ExportError: If formatting or file writing fails.
        ValueError: If fmt is not a supported format.
    """
    if fmt == "json":
        content = to_json(data)
    elif fmt == "csv":
        content = to_csv(data, delimiter=",")
    elif fmt == "tsv":
        content = to_csv(data, delimiter="\t")
    else:
        raise ValueError(f"Unsupported output format: '{fmt}'. Choose from json, csv, tsv.")

    if output_path:
        try:
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            logger.info("Output written to %s", output_path)
        except OSError as exc:
            raise ExportError(f"Cannot write to '{output_path}': {exc}") from exc

    return content
'''


F_CLI_INIT = r'''"""Click-based command-line interface for Proteinspy."""
'''

F_CLI_MAIN = r'''"""
Proteinspy CLI — analyse protein structure files from the terminal.

Supported input formats
-----------------------
.cif / .mmcif / .pdbx     mmCIF (preferred)
.pdb / .ent               legacy PDB format
*.gz                      compressed variants of the above

Output formats (--output / -o)
-------------------------------
table   Rich terminal table (default)
json    Machine-readable JSON
csv     Comma-separated values
tsv     Tab-separated values
"""
from __future__ import annotations

import sys

import click
from rich import box
from rich.console import Console
from rich.table import Table

from proteinspy.analysis.advanced import (
    get_bfactor_stats,
    get_chain_interface,
    get_disulfide_bonds,
)
from proteinspy.analysis.basic import (
    get_chains,
    get_ligands,
    get_missing_residues,
    get_resolution,
)
from proteinspy.core.validator import validate_structure
from proteinspy.exceptions import ProteinsyError
from proteinspy.io.writers import write_output

console = Console()

_OUTPUT_OPTION = click.option(
    "--output", "-o", "output_fmt",
    type=click.Choice(["table", "json", "csv", "tsv"], case_sensitive=False),
    default="table", show_default=True, help="Output format.",
)


def _err(msg: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {msg}")
    sys.exit(1)


def _maybe_print(data: dict, fmt: str, display_fn) -> None:
    if fmt == "table":
        display_fn()
    else:
        click.echo(write_output(data, fmt))


def show_resolution(path: str) -> None:
    r = get_resolution(path)
    console.print("\n[bold cyan]Resolution[/bold cyan]")
    if r["resolution"]:
        console.print(f"  Resolution : [bold]{r['resolution']} {r['unit']}[/bold]")
    else:
        console.print("  Resolution : [yellow]Not available[/yellow]")
    console.print(f"  Method     : {r['method']}\n")


def show_chains(path: str) -> None:
    r = get_chains(path)
    console.print(f"[bold cyan]Chains[/bold cyan]  ({r['chain_count']} total)\n")
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("Chain ID", justify="center")
    t.add_column("Type")
    t.add_column("Residues", justify="right")
    for ch in r["chains"]:
        t.add_row(ch["id"], ch["type"], str(ch["residue_count"]))
    console.print(t)
    console.print()


def show_ligands(path: str) -> None:
    r = get_ligands(path)
    console.print(f"[bold cyan]Ligands[/bold cyan]  ({r['ligand_count']} found)\n")
    if not r["has_ligand"]:
        console.print("  [yellow]No ligands detected.[/yellow]\n")
        return
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("Ligand ID", justify="center")
    t.add_column("Chain", justify="center")
    t.add_column("Seq Num", justify="right")
    for lg in r["ligands"]:
        t.add_row(lg["id"], lg.get("chain", "?"), lg.get("seq_num", "?"))
    console.print(t)
    console.print()


def show_missing(path: str) -> None:
    r = get_missing_residues(path)
    console.print(f"[bold cyan]Missing Residues[/bold cyan]  ({r['missing_count']} found)\n")
    if r["missing_count"] == 0:
        console.print("  [green]No missing residues.[/green]\n")
        return
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("Chain", justify="center")
    t.add_column("Residue", justify="center")
    t.add_column("Seq #", justify="right")
    for mr in r["missing_residues"]:
        t.add_row(mr.get("chain", "?"), mr.get("residue", "?"), str(mr.get("seq_num", "?")))
    console.print(t)
    console.print()


def show_bfactor(path: str) -> None:
    r = get_bfactor_stats(path)
    ov = r["overall"]
    console.print("\n[bold cyan]B-Factor Statistics[/bold cyan]\n")
    console.print(
        f"  Overall  — min: [bold]{ov['min']}[/bold]  max: [bold]{ov['max']}[/bold]  "
        f"mean: [bold]{ov['mean']}[/bold]  std: [bold]{ov['std']}[/bold]  atoms: {ov['atom_count']}\n"
    )
    if r["by_chain"]:
        t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
        t.add_column("Chain", justify="center")
        t.add_column("Min", justify="right")
        t.add_column("Max", justify="right")
        t.add_column("Mean", justify="right")
        t.add_column("Std", justify="right")
        t.add_column("Atoms", justify="right")
        for ch in r["by_chain"]:
            t.add_row(ch["chain_id"], str(ch["min"]), str(ch["max"]),
                      str(ch["mean"]), str(ch["std"]), str(ch["atom_count"]))
        console.print(t)
    console.print()


def show_disulfide(path: str) -> None:
    r = get_disulfide_bonds(path)
    console.print(f"\n[bold cyan]Disulfide Bonds[/bold cyan]  ({r['bond_count']} found)\n")
    if r["bond_count"] == 0:
        console.print("  [yellow]No disulfide bonds detected.[/yellow]\n")
        return
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("Chain A", justify="center")
    t.add_column("Res A", justify="center")
    t.add_column("Seq A", justify="right")
    t.add_column("Chain B", justify="center")
    t.add_column("Res B", justify="center")
    t.add_column("Seq B", justify="right")
    t.add_column("Distance (Å)", justify="right")
    for b in r["bonds"]:
        t.add_row(b["chain_a"], b["res_a"], b["seqid_a"],
                  b["chain_b"], b["res_b"], b["seqid_b"], str(b["distance_A"]))
    console.print(t)
    console.print()


def show_interface(path: str) -> None:
    r = get_chain_interface(path)
    console.print(f"\n[bold cyan]Chain Interfaces[/bold cyan]  ({r['interface_count']} found)\n")
    if r["interface_count"] == 0:
        console.print("  [yellow]No inter-chain interfaces detected.[/yellow]\n")
        return
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("Chain A", justify="center")
    t.add_column("Chain B", justify="center")
    t.add_column("Contact Pairs", justify="right")
    t.add_column("Residues A")
    t.add_column("Residues B")
    for iface in r["interfaces"]:
        ra = ", ".join(iface["residues_a"][:8])
        if len(iface["residues_a"]) > 8:
            ra += f" … (+{len(iface['residues_a']) - 8})"
        rb = ", ".join(iface["residues_b"][:8])
        if len(iface["residues_b"]) > 8:
            rb += f" … (+{len(iface['residues_b']) - 8})"
        t.add_row(iface["chain_a"], iface["chain_b"], str(iface["contact_pairs"]), ra, rb)
    console.print(t)
    console.print()


def show_validate(path: str) -> None:
    r = validate_structure(path)
    status = "[bold green]PASS[/bold green]" if r["pass"] else "[bold red]FAIL[/bold red]"
    console.print(f"\n[bold cyan]Structure Validation[/bold cyan]  {status}\n")
    if r["info"]:
        console.print("[bold]Info:[/bold]")
        for note in r["info"]:
            console.print(f"  [dim]•[/dim] {note}")
        console.print()
    if r["warnings"]:
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for warn in r["warnings"]:
            console.print(f"  [yellow]⚠[/yellow]  {warn}")
        console.print()
    else:
        console.print("  [green]No quality warnings.[/green]\n")


def print_help() -> None:
    console.print()
    console.print("[bold green]Proteinspy CLI[/bold green]", justify="center")
    console.print()
    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", expand=True)
    t.add_column("Command", style="bold yellow", min_width=22)
    t.add_column("Description")
    rows = [
        ("--help",      "Show this help message and exit"),
        ("--version",   "Show the package version and exit"),
        ("analyze",     "Run all basic analyses (resolution, chains, ligands, missing residues)"),
        ("resolution",  "Crystallographic resolution and experimental method"),
        ("chains",      "Polymer chains with type and residue count"),
        ("ligands",     "Non-solvent ligand molecules"),
        ("missing",     "Residues present in sequence but absent from ATOM records"),
        ("bfactor",     "B-factor statistics — global and per-chain"),
        ("disulfide",   "Disulfide bonds detected by SG-SG distance (<= 2.5 Å)"),
        ("interface",   "Inter-chain interface residues by Ca distance"),
        ("validate",    "Quick quality check — resolution, completeness, model count"),
        ("export",      "Export any analysis result to a JSON / CSV / TSV file"),
    ]
    for cmd, desc in rows:
        t.add_row(cmd, desc)
    console.print(t)
    console.print()
    console.print(
        "Usage: [bold]proteinspy [cyan]<command>[/cyan] "
        "<file.cif|file.pdb> [[dim]--output table|json|csv|tsv[/dim]][/bold]"
    )
    console.print("Example: [bold]proteinspy analyze 10AJ.cif[/bold]")
    console.print("Example: [bold]proteinspy bfactor protein.pdb --output json[/bold]")
    console.print()


CONTEXT_SETTINGS = dict(help_option_names=["--help", "-h"])


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.version_option(version="1.1.0", prog_name="proteinspy")
@click.pass_context
def main(ctx: click.Context) -> None:
    """proteinspy — Analyse a protein structure file (.cif or .pdb)."""
    if ctx.invoked_subcommand is None:
        print_help()


@main.command("analyze")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_analyze(structure_file: str, output_fmt: str) -> None:
    """Run all basic analyses on a structure file."""
    try:
        if output_fmt != "table":
            combined = {
                "resolution": get_resolution(structure_file),
                "chains": get_chains(structure_file),
                "ligands": get_ligands(structure_file),
                "missing_residues": get_missing_residues(structure_file),
            }
            click.echo(write_output(combined, output_fmt))
        else:
            console.rule(f"[bold blue]proteinspy — {structure_file}[/bold blue]")
            show_resolution(structure_file)
            show_chains(structure_file)
            show_ligands(structure_file)
            show_missing(structure_file)
            console.rule()
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("resolution")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_resolution(structure_file: str, output_fmt: str) -> None:
    """Report crystallographic resolution only."""
    try:
        data = get_resolution(structure_file)
        _maybe_print(data, output_fmt, lambda: show_resolution(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("chains")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_chains(structure_file: str, output_fmt: str) -> None:
    """Report all polymer chains."""
    try:
        data = get_chains(structure_file)
        _maybe_print(data, output_fmt, lambda: show_chains(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("ligands")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_ligands(structure_file: str, output_fmt: str) -> None:
    """Report all non-solvent ligands."""
    try:
        data = get_ligands(structure_file)
        _maybe_print(data, output_fmt, lambda: show_ligands(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("missing")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_missing(structure_file: str, output_fmt: str) -> None:
    """Report all missing residues."""
    try:
        data = get_missing_residues(structure_file)
        _maybe_print(data, output_fmt, lambda: show_missing(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("bfactor")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_bfactor(structure_file: str, output_fmt: str) -> None:
    """B-factor statistics — global and per-chain."""
    try:
        data = get_bfactor_stats(structure_file)
        _maybe_print(data, output_fmt, lambda: show_bfactor(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("disulfide")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_disulfide(structure_file: str, output_fmt: str) -> None:
    """Detect disulfide bonds by SG-SG distance."""
    try:
        data = get_disulfide_bonds(structure_file)
        _maybe_print(data, output_fmt, lambda: show_disulfide(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("interface")
@click.argument("structure_file")
@click.option("--cutoff", default=5.0, show_default=True, type=float,
              help="Ca-Ca distance threshold in Angstroms.")
@_OUTPUT_OPTION
def cmd_interface(structure_file: str, cutoff: float, output_fmt: str) -> None:
    """Report inter-chain interface residues."""
    try:
        data = get_chain_interface(structure_file, cutoff=cutoff)
        _maybe_print(data, output_fmt, lambda: show_interface(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("validate")
@click.argument("structure_file")
@_OUTPUT_OPTION
def cmd_validate(structure_file: str, output_fmt: str) -> None:
    """Quick quality check (resolution, completeness, model count)."""
    try:
        data = validate_structure(structure_file)
        _maybe_print(data, output_fmt, lambda: show_validate(structure_file))
    except ProteinsyError as exc:
        _err(str(exc))


@main.command("export")
@click.argument("structure_file")
@click.argument("output_file")
@click.option(
    "--analysis", "-a",
    type=click.Choice(
        ["resolution","chains","ligands","missing","bfactor",
         "disulfide","interface","validate","all"], case_sensitive=False,
    ),
    default="all", show_default=True, help="Which analysis to export.",
)
def cmd_export(structure_file: str, output_file: str, analysis: str) -> None:
    """
    Export analysis results to a file.

    Output format is inferred from the OUTPUT_FILE extension
    (.json -> JSON, .csv -> CSV, .tsv -> TSV).

    \b
    Examples:
      proteinspy export protein.cif report.json
      proteinspy export protein.cif chains.csv --analysis chains
    """
    import os as _os
    ext = _os.path.splitext(output_file.lower())[1].lstrip(".")
    fmt = {"json": "json", "csv": "csv", "tsv": "tsv"}.get(ext, "json")

    _analysis_map = {
        "resolution": get_resolution, "chains": get_chains,
        "ligands": get_ligands, "missing": get_missing_residues,
        "bfactor": get_bfactor_stats, "disulfide": get_disulfide_bonds,
        "interface": get_chain_interface, "validate": validate_structure,
    }

    try:
        if analysis == "all":
            data = {k: fn(structure_file) for k, fn in _analysis_map.items()}
        else:
            data = _analysis_map[analysis](structure_file)
        write_output(data, fmt, output_path=output_file)
        console.print(
            f"[green]✓[/green] Exported [bold]{analysis}[/bold] "
            f"analysis to [bold]{output_file}[/bold] ({fmt.upper()})"
        )
    except ProteinsyError as exc:
        _err(str(exc))
'''


F_PKG_INIT = r'''"""
Proteinspy — Protein structure analysis from the terminal.

Public API
----------
>>> from proteinspy import get_resolution, get_chains
>>> get_resolution("protein.cif")
{'resolution': 2.1, 'unit': 'Å', 'method': 'X-RAY DIFFRACTION'}
"""
from proteinspy.analysis.basic import (
    get_chains, get_ligands, get_missing_residues, get_resolution,
)
from proteinspy.analysis.advanced import (
    get_bfactor_stats, get_chain_interface, get_disulfide_bonds,
)
from proteinspy.core.validator import validate_structure
from proteinspy.io.writers import to_json, to_csv, write_output

__version__ = "1.1.0"
__author__  = "AkhilTeja2209"
__license__ = "MIT"

__all__ = [
    "get_resolution", "get_chains", "get_ligands", "get_missing_residues",
    "get_bfactor_stats", "get_disulfide_bonds", "get_chain_interface",
    "validate_structure",
    "to_json", "to_csv", "write_output",
]
'''

F_PKG_MAIN = r'''"""Entry point — allows `python -m proteinspy`."""
from proteinspy.cli.main import main

if __name__ == "__main__":
    main()
'''

F_ANALYSIS_PY_COMMENT = r'''# analysis.py
#
# This is the original single-file implementation from v1.0.x.
# As of v1.1.0 this module has been superseded by the analysis/ sub-package
# (analysis/basic.py and analysis/advanced.py), which contains the same
# four functions plus type hints, error handling, caching, and new analyses.
#
# This file is kept for historical reference and so that older tags of this
# repo remain functional. It is NOT imported by the package in v1.1.0+.
# Use `from proteinspy.analysis import get_resolution` etc. instead.

'''


F_PYPROJECT = r'''[tool.poetry]
name = "proteinspy"
version = "1.1.0"
description = "A CLI tool and Python library to analyse protein structures from .cif and .pdb files"
authors = ["AkhilTeja2209 <your_email@example.com>"]
readme = "README.md"
license = "MIT"
homepage = "https://akhilteja2209.github.io/Proteinspy/"
repository = "https://github.com/AkhilTeja2209/Proteinspy"
documentation = "https://akhilteja2209.github.io/Proteinspy/"
keywords = [
    "protein", "bioinformatics", "structural-biology",
    "pdb", "cif", "mmcif", "cryo-em", "x-ray", "nmr", "gemmi",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
    "Topic :: Scientific/Engineering :: Chemistry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Operating System :: OS Independent",
    "Environment :: Console",
]

packages = [{ include = "proteinspy" }]

[tool.poetry.dependencies]
python  = "^3.9"
gemmi   = "^0.6.5"
rich    = "^13.0"
click   = "^8.1"

[tool.poetry.extras]
advanced = ["biopython", "prody"]
viz      = ["matplotlib", "plotly"]

[tool.poetry.group.dev.dependencies]
pytest          = "^7.4"
pytest-cov      = "^4.1"
black           = "^24.0"
pylint          = "^3.0"
mypy            = "^1.0"
mkdocs          = "^1.6"
mkdocs-material = "^9.5"

[tool.poetry.scripts]
proteinspy = "proteinspy.cli.main:main"

[build-system]
requires      = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts   = "-v --cov=proteinspy --cov-report=term-missing --cov-report=html"

[tool.coverage.run]
branch = true
source = ["proteinspy"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
]

[tool.black]
line-length    = 88
target-version = ["py39", "py310", "py311", "py312"]

[tool.mypy]
python_version = "3.9"
strict         = false
ignore_missing_imports = true

[tool.pylint.main]
max-line-length = 88

[tool.pylint."messages control"]
disable = [
    "missing-module-docstring",
    "too-few-public-methods",
    "broad-except",
]
'''


F_TESTS_CONFTEST = r'''"""
Shared pytest fixtures for Proteinspy tests.
"""
from __future__ import annotations

import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_CIF   = os.path.join(FIXTURES_DIR, "10AJ.cif")


@pytest.fixture(scope="session")
def sample_cif() -> str:
    """Return the absolute path to the bundled test CIF file."""
    assert os.path.exists(SAMPLE_CIF), (
        f"Test fixture missing: {SAMPLE_CIF}"
    )
    return SAMPLE_CIF


@pytest.fixture(scope="session")
def missing_file(tmp_path_factory) -> str:
    """Return a path that does not exist on disk."""
    return str(tmp_path_factory.mktemp("data") / "nonexistent.cif")
'''

F_TEST_BASIC = r'''"""Unit tests for proteinspy.analysis.basic"""
from __future__ import annotations

import pytest

from proteinspy.analysis.basic import (
    get_chains, get_ligands, get_missing_residues, get_resolution,
)
from proteinspy.exceptions import FileNotFoundError, InvalidFileFormatError


class TestGetResolution:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_resolution(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_resolution(sample_cif)
        assert "resolution" in result
        assert "unit" in result
        assert "method" in result

    def test_resolution_is_float_or_none(self, sample_cif):
        result = get_resolution(sample_cif)
        assert result["resolution"] is None or isinstance(result["resolution"], float)

    def test_resolution_positive_when_present(self, sample_cif):
        result = get_resolution(sample_cif)
        if result["resolution"] is not None:
            assert result["resolution"] > 0

    def test_unit_set_when_resolution_present(self, sample_cif):
        result = get_resolution(sample_cif)
        if result["resolution"] is not None:
            assert result["unit"] == "Å"
        else:
            assert result["unit"] is None

    def test_method_is_string(self, sample_cif):
        result = get_resolution(sample_cif)
        assert isinstance(result["method"], str) and len(result["method"]) > 0

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_resolution(missing_file)


class TestGetChains:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_chains(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_chains(sample_cif)
        assert "chain_count" in result and "chains" in result

    def test_chain_count_matches_list(self, sample_cif):
        result = get_chains(sample_cif)
        assert result["chain_count"] == len(result["chains"])

    def test_chain_count_positive(self, sample_cif):
        assert get_chains(sample_cif)["chain_count"] > 0

    def test_chain_entry_structure(self, sample_cif):
        for ch in get_chains(sample_cif)["chains"]:
            assert "id" in ch and "type" in ch and "residue_count" in ch
            assert isinstance(ch["residue_count"], int) and ch["residue_count"] > 0

    def test_chain_ids_unique(self, sample_cif):
        ids = [ch["id"] for ch in get_chains(sample_cif)["chains"]]
        assert len(ids) == len(set(ids))

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_chains(missing_file)


class TestGetLigands:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_ligands(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_ligands(sample_cif)
        assert "ligand_count" in result and "has_ligand" in result and "ligands" in result

    def test_has_ligand_consistent(self, sample_cif):
        result = get_ligands(sample_cif)
        assert result["has_ligand"] == (result["ligand_count"] > 0)
        assert result["ligand_count"] == len(result["ligands"])

    def test_ligand_entry_structure(self, sample_cif):
        for lg in get_ligands(sample_cif)["ligands"]:
            assert "id" in lg and "chain" in lg and "seq_num" in lg

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_ligands(missing_file)


class TestGetMissingResidues:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_missing_residues(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_missing_residues(sample_cif)
        assert "missing_count" in result and "missing_residues" in result

    def test_count_matches_list(self, sample_cif):
        result = get_missing_residues(sample_cif)
        assert result["missing_count"] == len(result["missing_residues"])

    def test_missing_count_non_negative(self, sample_cif):
        assert get_missing_residues(sample_cif)["missing_count"] >= 0

    def test_residue_entry_structure(self, sample_cif):
        for mr in get_missing_residues(sample_cif)["missing_residues"]:
            assert "chain" in mr and "residue" in mr and "seq_num" in mr

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_missing_residues(missing_file)
'''


F_TEST_ADVANCED = r'''"""Unit tests for proteinspy.analysis.advanced"""
from __future__ import annotations

import pytest

from proteinspy.analysis.advanced import (
    get_bfactor_stats, get_chain_interface, get_disulfide_bonds,
)


class TestGetBfactorStats:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_bfactor_stats(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_bfactor_stats(sample_cif)
        assert "overall" in result and "by_chain" in result

    def test_overall_stats_keys(self, sample_cif):
        overall = get_bfactor_stats(sample_cif)["overall"]
        for key in ("min", "max", "mean", "std", "atom_count"):
            assert key in overall

    def test_atom_count_positive(self, sample_cif):
        assert get_bfactor_stats(sample_cif)["overall"]["atom_count"] > 0

    def test_min_le_mean_le_max(self, sample_cif):
        ov = get_bfactor_stats(sample_cif)["overall"]
        if ov["min"] is not None:
            assert ov["min"] <= ov["mean"] <= ov["max"]

    def test_std_non_negative(self, sample_cif):
        ov = get_bfactor_stats(sample_cif)["overall"]
        if ov["std"] is not None:
            assert ov["std"] >= 0

    def test_by_chain_is_list(self, sample_cif):
        assert isinstance(get_bfactor_stats(sample_cif)["by_chain"], list)

    def test_by_chain_has_chain_id(self, sample_cif):
        for entry in get_bfactor_stats(sample_cif)["by_chain"]:
            assert "chain_id" in entry and isinstance(entry["chain_id"], str)

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_bfactor_stats(missing_file)


class TestGetDisulfideBonds:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_disulfide_bonds(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_disulfide_bonds(sample_cif)
        assert "bond_count" in result and "bonds" in result

    def test_count_matches_list(self, sample_cif):
        result = get_disulfide_bonds(sample_cif)
        assert result["bond_count"] == len(result["bonds"])

    def test_bond_count_non_negative(self, sample_cif):
        assert get_disulfide_bonds(sample_cif)["bond_count"] >= 0

    def test_bond_entry_structure(self, sample_cif):
        for bond in get_disulfide_bonds(sample_cif)["bonds"]:
            for key in ("chain_a","res_a","seqid_a","chain_b","res_b","seqid_b","distance_A"):
                assert key in bond

    def test_bond_distance_in_range(self, sample_cif):
        for bond in get_disulfide_bonds(sample_cif)["bonds"]:
            assert 0 < bond["distance_A"] <= 2.5

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_disulfide_bonds(missing_file)


class TestGetChainInterface:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_chain_interface(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_chain_interface(sample_cif)
        assert "interface_count" in result and "interfaces" in result

    def test_count_matches_list(self, sample_cif):
        result = get_chain_interface(sample_cif)
        assert result["interface_count"] == len(result["interfaces"])

    def test_interface_entry_structure(self, sample_cif):
        for iface in get_chain_interface(sample_cif)["interfaces"]:
            for key in ("chain_a","chain_b","contact_pairs","residues_a","residues_b"):
                assert key in iface

    def test_contact_pairs_positive(self, sample_cif):
        for iface in get_chain_interface(sample_cif)["interfaces"]:
            assert iface["contact_pairs"] > 0

    def test_chain_a_ne_chain_b(self, sample_cif):
        for iface in get_chain_interface(sample_cif)["interfaces"]:
            assert iface["chain_a"] != iface["chain_b"]

    def test_custom_cutoff_stricter(self, sample_cif):
        loose = get_chain_interface(sample_cif, cutoff=10.0)
        tight = get_chain_interface(sample_cif, cutoff=3.0)
        assert tight["interface_count"] <= loose["interface_count"]

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_chain_interface(missing_file)
'''

F_TEST_PARSER = r'''"""Unit tests for proteinspy.utils.helpers (parser layer)"""
from __future__ import annotations

import pytest

from proteinspy.utils.helpers import detect_format, read_structure
from proteinspy.exceptions import InvalidFileFormatError


class TestDetectFormat:
    @pytest.mark.parametrize("path,expected", [
        ("protein.cif", "cif"), ("protein.mmcif", "cif"), ("protein.pdbx", "cif"),
        ("protein.cif.gz", "cif"), ("protein.pdb", "pdb"),
        ("protein.ent", "pdb"), ("protein.pdb.gz", "pdb"),
    ])
    def test_known_extensions(self, path, expected):
        assert detect_format(path) == expected

    def test_unknown_extension_raises(self):
        with pytest.raises(InvalidFileFormatError):
            detect_format("protein.xyz")

    def test_no_extension_raises(self):
        with pytest.raises(InvalidFileFormatError):
            detect_format("protein")


class TestReadStructure:
    def test_reads_cif(self, sample_cif):
        import gemmi
        assert isinstance(read_structure(sample_cif), gemmi.Structure)

    def test_structure_has_models(self, sample_cif):
        assert len(read_structure(sample_cif)) >= 1

    def test_structure_has_chains(self, sample_cif):
        assert len(list(read_structure(sample_cif)[0])) > 0

    def test_cache_returns_same_object(self, sample_cif):
        assert read_structure(sample_cif) is read_structure(sample_cif)

    def test_missing_file_raises(self, missing_file):
        from proteinspy.exceptions import FileNotFoundError as PSFNFError
        with pytest.raises(PSFNFError):
            read_structure(missing_file)
'''

F_TEST_VALIDATOR = r'''"""Unit tests for proteinspy.core.validator"""
from __future__ import annotations

import pytest
from proteinspy.core.validator import validate_structure


class TestValidateStructure:
    def test_returns_dict(self, sample_cif):
        assert isinstance(validate_structure(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = validate_structure(sample_cif)
        for key in ("warnings","info","pass","resolution","method","model_count","missing_fraction"):
            assert key in result

    def test_warnings_is_list(self, sample_cif):
        assert isinstance(validate_structure(sample_cif)["warnings"], list)

    def test_info_is_list(self, sample_cif):
        assert isinstance(validate_structure(sample_cif)["info"], list)

    def test_pass_is_bool(self, sample_cif):
        assert isinstance(validate_structure(sample_cif)["pass"], bool)

    def test_pass_consistent_with_warnings(self, sample_cif):
        result = validate_structure(sample_cif)
        assert result["pass"] == (len(result["warnings"]) == 0)

    def test_model_count_positive(self, sample_cif):
        assert validate_structure(sample_cif)["model_count"] >= 1

    def test_missing_fraction_in_range(self, sample_cif):
        frac = validate_structure(sample_cif)["missing_fraction"]
        assert 0.0 <= frac <= 1.0

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            validate_structure(missing_file)
'''

F_TEST_WRITERS = r'''"""Unit tests for proteinspy.io.writers"""
from __future__ import annotations

import json
import os
import pytest

from proteinspy.io.writers import to_csv, to_json, write_output
from proteinspy.exceptions import ExportError

SIMPLE = {"resolution": 2.1, "unit": "Å", "method": "X-RAY DIFFRACTION"}
WITH_LIST = {
    "chain_count": 2,
    "chains": [
        {"id": "A", "type": "PolymerType.PeptideL", "residue_count": 100},
        {"id": "B", "type": "PolymerType.PeptideL", "residue_count": 80},
    ],
}


class TestToJson:
    def test_returns_string(self):
        assert isinstance(to_json(SIMPLE), str)

    def test_valid_json(self):
        assert json.loads(to_json(SIMPLE))["resolution"] == 2.1

    def test_indented_by_default(self):
        assert "\n" in to_json(SIMPLE, indent=2)

    def test_unicode_preserved(self):
        assert "Å" in to_json({"unit": "Å"})

    def test_list_dict(self):
        assert len(json.loads(to_json(WITH_LIST))["chains"]) == 2


class TestToCsv:
    def test_returns_string(self):
        assert isinstance(to_csv(SIMPLE), str)

    def test_header_present(self):
        first = to_csv(SIMPLE).splitlines()[0]
        assert "resolution" in first or "method" in first

    def test_data_row_present(self):
        lines = [l for l in to_csv(SIMPLE).splitlines() if l.strip()]
        assert len(lines) >= 2

    def test_list_dict_expands_rows(self):
        lines = [l for l in to_csv(WITH_LIST).splitlines() if l.strip()]
        assert len(lines) == 3  # header + 2 chain rows

    def test_tsv_uses_tab(self):
        assert "\t" in to_csv(SIMPLE, delimiter="\t")


class TestWriteOutput:
    def test_json_format(self):
        assert json.loads(write_output(SIMPLE, "json"))["method"] == "X-RAY DIFFRACTION"

    def test_csv_format(self):
        result = write_output(SIMPLE, "csv")
        assert isinstance(result, str) and ("resolution" in result or "method" in result)

    def test_tsv_format(self):
        assert "\t" in write_output(SIMPLE, "tsv")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            write_output(SIMPLE, "xml")

    def test_writes_to_file(self, tmp_path):
        out = str(tmp_path / "output.json")
        write_output(SIMPLE, "json", output_path=out)
        assert os.path.exists(out)
        assert json.load(open(out))["resolution"] == 2.1

    def test_file_content_matches_return(self, tmp_path):
        out = str(tmp_path / "output.json")
        returned = write_output(SIMPLE, "json", output_path=out)
        assert returned == open(out).read()
'''

F_TEST_CLI = r'''"""Integration tests for the Proteinspy Click CLI."""
from __future__ import annotations

import json
import pytest
from click.testing import CliRunner

from proteinspy.cli.main import main


@pytest.fixture
def runner():
    return CliRunner()


class TestMainGroup:
    def test_no_args_shows_help(self, runner):
        result = runner.invoke(main, [])
        assert result.exit_code == 0

    def test_version_flag(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0 and "1.1.0" in result.output


class TestAnalyzeCommand:
    def test_table_output(self, runner, sample_cif):
        result = runner.invoke(main, ["analyze", sample_cif])
        assert result.exit_code == 0

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["analyze", sample_cif, "--output", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "resolution" in parsed and "chains" in parsed

    def test_missing_file_exits_nonzero(self, runner, missing_file):
        result = runner.invoke(main, ["analyze", missing_file])
        assert result.exit_code != 0 or "Error" in result.output


class TestResolutionCommand:
    def test_table_output(self, runner, sample_cif):
        assert runner.invoke(main, ["resolution", sample_cif]).exit_code == 0

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["resolution", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "resolution" in parsed and "method" in parsed


class TestChainsCommand:
    def test_table_output(self, runner, sample_cif):
        assert runner.invoke(main, ["chains", sample_cif]).exit_code == 0

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["chains", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        assert json.loads(result.output)["chain_count"] > 0


class TestLigandsCommand:
    def test_table_output(self, runner, sample_cif):
        assert runner.invoke(main, ["ligands", sample_cif]).exit_code == 0

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["ligands", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        assert "ligand_count" in json.loads(result.output)


class TestMissingCommand:
    def test_table_output(self, runner, sample_cif):
        assert runner.invoke(main, ["missing", sample_cif]).exit_code == 0

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["missing", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        assert "missing_count" in json.loads(result.output)


class TestBfactorCommand:
    def test_table_output(self, runner, sample_cif):
        result = runner.invoke(main, ["bfactor", sample_cif])
        assert result.exit_code == 0 and "B-Factor" in result.output

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["bfactor", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "overall" in parsed and "by_chain" in parsed


class TestDisulfideCommand:
    def test_table_output(self, runner, sample_cif):
        assert runner.invoke(main, ["disulfide", sample_cif]).exit_code == 0

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["disulfide", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        assert "bond_count" in json.loads(result.output)


class TestInterfaceCommand:
    def test_table_output(self, runner, sample_cif):
        assert runner.invoke(main, ["interface", sample_cif]).exit_code == 0

    def test_custom_cutoff(self, runner, sample_cif):
        assert runner.invoke(main, ["interface", sample_cif, "--cutoff", "8.0"]).exit_code == 0


class TestValidateCommand:
    def test_table_output(self, runner, sample_cif):
        result = runner.invoke(main, ["validate", sample_cif])
        assert result.exit_code == 0 and "Validation" in result.output

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["validate", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "pass" in parsed and "warnings" in parsed


class TestExportCommand:
    def test_export_json(self, runner, sample_cif, tmp_path):
        out = str(tmp_path / "report.json")
        result = runner.invoke(main, ["export", sample_cif, out])
        assert result.exit_code == 0
        import os
        assert os.path.exists(out)
        assert "resolution" in json.load(open(out))

    def test_export_csv(self, runner, sample_cif, tmp_path):
        out = str(tmp_path / "chains.csv")
        result = runner.invoke(main, ["export", sample_cif, out, "--analysis", "chains"])
        assert result.exit_code == 0
        import os
        assert os.path.exists(out)
'''


F_README = r'''# Proteinspy

[![PyPI](https://img.shields.io/pypi/v/proteinspy)](https://pypi.org/project/proteinspy/)
[![Tests](https://github.com/AkhilTeja2209/Proteinspy/actions/workflows/test.yml/badge.svg)](https://github.com/AkhilTeja2209/Proteinspy/actions/workflows/test.yml)
[![Python](https://img.shields.io/pypi/pyversions/proteinspy)](https://pypi.org/project/proteinspy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A CLI tool and Python library for analysing protein structure files.

Supports `.cif`, `.mmcif`, `.pdb`, `.ent`, and their `.gz` compressed variants.
Full documentation: [akhilteja2209.github.io/Proteinspy](https://akhilteja2209.github.io/Proteinspy/)

---

## Installation

```bash
pip install proteinspy
```

### Windows note

If `proteinspy` is not recognised after installation, add the Python Scripts
folder to your PATH. Run this once in PowerShell:

```powershell
$env:PATH += ";$env:APPDATA\Python\Python313\Scripts"
[System.Environment]::SetEnvironmentVariable("PATH", $env:PATH, "User")
```

Then restart PowerShell and run `proteinspy` again.

---

## Quick start

```bash
# See all commands
proteinspy

# Run all basic analyses on a structure file
proteinspy analyze 10AJ.cif

# Works with PDB format too
proteinspy analyze my_protein.pdb
```

---

## Commands

**Format:** `proteinspy <command> <file> [--output table|json|csv|tsv]`

### Basic analyses

| Command | Description |
|---|---|
| `analyze` | Run all basic analyses — resolution, chains, ligands, missing residues |
| `resolution` | Crystallographic resolution and experimental method |
| `chains` | All polymer chains with type and residue count |
| `ligands` | Non-solvent ligand molecules |
| `missing` | Residues present in the sequence but absent from ATOM records |

### Advanced analyses

| Command | Description |
|---|---|
| `bfactor` | B-factor (temperature factor) statistics — global and per chain |
| `disulfide` | Disulfide bonds detected by SG–SG distance (≤ 2.5 Å) |
| `interface` | Inter-chain interface residues by Cα distance (default cutoff 5.0 Å) |
| `validate` | Quick quality check — resolution, completeness, model count |
| `export` | Export any analysis to a `.json`, `.csv`, or `.tsv` file |

### Examples

```bash
# Basic analyses
proteinspy analyze    10AJ.cif
proteinspy resolution 10AJ.cif
proteinspy chains     10AJ.cif
proteinspy ligands    10AJ.cif
proteinspy missing    10AJ.cif

# Advanced analyses
proteinspy bfactor   protein.cif
proteinspy disulfide protein.cif
proteinspy interface protein.cif --cutoff 8.0
proteinspy validate  protein.cif

# Output formats — any command supports --output / -o
proteinspy chains    protein.cif --output json
proteinspy bfactor   protein.cif --output csv
proteinspy analyze   protein.cif -o tsv

# Export to file (format inferred from extension)
proteinspy export protein.cif report.json
proteinspy export protein.cif chains.csv  --analysis chains
proteinspy export protein.cif bonds.json  --analysis disulfide
```

---

## Output formats

Every command accepts `--output` (or `-o`):

| Format | Flag | Use case |
|---|---|---|
| Rich table | `--output table` | Default — coloured terminal output |
| JSON | `--output json` | Downstream scripts, APIs |
| CSV | `--output csv` | Excel, pandas, R |
| TSV | `--output tsv` | Tab-separated, bioinformatics pipelines |

---

## Supported file formats

| Extension | Format |
|---|---|
| `.cif`, `.mmcif`, `.pdbx` | mmCIF (recommended) |
| `.pdb`, `.ent` | Legacy PDB format |
| Any of the above + `.gz` | Gzip-compressed |

---

## Python API

You can import and use every analysis function directly:

```python
from proteinspy import get_resolution, get_chains, get_bfactor_stats
from proteinspy import to_json, write_output

# Basic
result = get_resolution("protein.cif")
print(result["resolution"], result["method"])

# Advanced
stats = get_bfactor_stats("protein.cif")
print(stats["overall"]["mean"])

# Export
write_output(get_chains("protein.cif"), "json", output_path="chains.json")
```

---

## Requirements

- Python 3.9 or later
- Dependencies installed automatically: `gemmi`, `rich`, `click`

---

## Contributing

Contributions are welcome — new analyses, output formats, bug fixes, or docs.
See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, code standards,
and how to add a new analysis command.

---

## Documentation

Full API reference and usage guides at
[akhilteja2209.github.io/Proteinspy](https://akhilteja2209.github.io/Proteinspy/)

---

**Version:** 1.1.0
'''


F_CHANGELOG = r'''# Changelog

All notable changes to Proteinspy are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2025-06-11

### Added

**New CLI commands**
- `bfactor` — B-factor (temperature factor) statistics, global and per chain
  (min, max, mean, std, atom count)
- `disulfide` — detect CYS–CYS disulfide bonds by SG–SG distance (≤ 2.5 Å),
  reporting both chains, residue names, sequence IDs, and exact distance
- `interface` — inter-chain interface residues by Cα–Cα distance with a
  configurable `--cutoff` (default 5.0 Å)
- `validate` — quick quality check reporting resolution warnings, missing
  residue fraction, NMR ensemble detection, and unit cell presence
- `export` — write any single analysis or the full set to `.json`, `.csv`,
  or `.tsv`; output format inferred from the file extension

**`--output` / `-o` flag on every command**
- All existing commands (`analyze`, `resolution`, `chains`, `ligands`,
  `missing`) and all new commands now accept `--output table|json|csv|tsv`
- `table` (default) — existing Rich terminal output, unchanged
- `json` — pretty-printed, machine-readable JSON
- `csv` — comma-separated, list keys expanded to one row each
- `tsv` — tab-separated equivalent for bioinformatics pipelines

**PDB / ENT format support**
- Structure files ending in `.pdb`, `.ent`, `.pdb.gz`, or `.ent.gz` are
  now accepted by every command in addition to `.cif`/`.mmcif`/`.pdbx`

**Package architecture**
- `proteinspy/analysis/basic.py` — the four original analyses, rewritten
  with full type hints, Google-style docstrings, and structured error handling
- `proteinspy/analysis/advanced.py` — three new analyses (B-factor,
  disulfide, interface)
- `proteinspy/cli/main.py` — Click CLI, moved from `__main__.py` and extended
- `proteinspy/core/parser.py` — unified structure reader
- `proteinspy/core/validator.py` — quality validator
- `proteinspy/io/writers.py` — JSON / CSV / TSV serialisers
- `proteinspy/utils/helpers.py` — `@lru_cache`-backed `read_structure()`,
  format detection
- `proteinspy/exceptions.py` — `ProteinsyError` hierarchy
  (`FileNotFoundError`, `InvalidFileFormatError`, `AnalysisError`,
  `ExportError`)

**Testing — 114 tests**
- `tests/unit/test_analysis_basic.py` (26 tests)
- `tests/unit/test_analysis_advanced.py` (24 tests)
- `tests/unit/test_parser.py` (14 tests)
- `tests/unit/test_validator.py` (9 tests)
- `tests/unit/test_writers.py` (16 tests)
- `tests/integration/test_cli.py` (25 tests — every command, table + JSON output)
- `tests/fixtures/10AJ.cif` — bundled test structure

**CI / CD**
- `.github/workflows/test.yml` — matrix across Python 3.9–3.12 on Ubuntu,
  macOS, and Windows; includes Black formatting check, Pylint, and Mypy
- `.github/workflows/publish.yml` — trusted PyPI publishing on GitHub Release
  (no API key required)

**Repository hygiene**
- `.gitignore` — Python, Poetry, pytest, mypy, IDE, and OS artefacts
- `CONTRIBUTING.md` — Poetry setup, test commands, code standards, template
  for adding a new analysis function
- `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`

### Changed

- `pyproject.toml` — `click` added as a declared runtime dependency (was used
  but undeclared — a packaging bug); `gemmi` and `rich` pinned to minimum
  known-good versions (`^0.6.5` and `^13.0`) instead of wildcards; dev
  dependencies (`pytest`, `black`, `pylint`, `mypy`, `mkdocs`) now tracked
  in `[tool.poetry.group.dev.dependencies]`; pytest, coverage, Black, mypy,
  and Pylint config added; `classifiers` expanded to include Python version
  tags and more specific topic tags; entry point updated to
  `proteinspy.cli.main:main`
- `__init__.py` — now exports all 8 analysis functions, 3 I/O helpers,
  `validate_structure`, `__version__`, `__author__`, `__license__`, and a
  proper `__all__`
- `__main__.py` — reduced to a 3-line entry point; CLI logic lives in
  `cli/main.py`
- README — updated to document all new commands, `--output` flag, supported
  file formats, Python API, and badges

### Deprecated

- `proteinspy/analysis.py` — the original single-file implementation is kept
  for historical reference but is no longer imported by the package. A comment
  at the top of the file explains this. Users on v1.0.x are unaffected; the
  `analysis/` sub-package exports all four original functions unchanged.

---

## [1.0.2] - 2025-05-01

### Fixed
- Resolved packaging issue where `click` was used but not declared as a
  dependency (fully fixed in v1.1.0 with pinned version)

---

## [1.0.1] - 2025-04-15

### Fixed
- Minor bug fixes in missing residue detection for structures with multiple
  models

---

## [1.0.0] - 2025-04-01

### Added
- Initial release
- `analyze` command — runs resolution, chains, ligands, missing residues
- `resolution` command
- `chains` command
- `ligands` command
- `missing` command
- `.cif` / `.mmcif` format support via gemmi
- Rich terminal output
- PyPI distribution via Poetry
- MkDocs documentation via GitHub Pages
'''


F_GITIGNORE = r'''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg
*.egg-info/
dist/
build/
.eggs/

# Virtual environments
.venv/
venv/
env/
.env

# Testing & coverage
.pytest_cache/
.coverage
htmlcov/
coverage.xml
*.cover
.hypothesis/

# Type checking
.mypy_cache/

# IDEs
.vscode/
.idea/
*.sublime-project
*.sublime-workspace

# OS
.DS_Store
Thumbs.db
desktop.ini

# MkDocs
site/

# Jupyter
.ipynb_checkpoints/
*.ipynb

# Temporary files
*.tmp
*.bak
*.swp
'''

F_CONTRIBUTING = r'''# Contributing to Proteinspy

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
'''

F_CODE_OF_CONDUCT = r'''# Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, caste, color, religion, or sexual
identity and orientation.

## Our Standards

Examples of behaviour that contributes to a positive environment:
- Demonstrating empathy and kindness toward other people
- Being respectful of differing opinions, viewpoints, and experiences
- Giving and gracefully accepting constructive feedback
- Accepting responsibility and apologising to those affected by our mistakes

Examples of unacceptable behaviour:
- The use of sexualised language or imagery, and sexual attention or advances
- Trolling, insulting or derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without their explicit permission

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behaviour may be
reported to the project maintainer. All complaints will be reviewed and
investigated promptly and fairly.

## Attribution

This Code of Conduct is adapted from the
[Contributor Covenant](https://www.contributor-covenant.org), version 2.1.
'''


F_CI_TEST = r'''name: Tests

on:
  push:
    branches: ["main", "develop"]
  pull_request:
    branches: ["main"]

jobs:
  test:
    name: Python ${{ matrix.python-version }} on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
        os: [ubuntu-latest, macos-latest, windows-latest]
    defaults:
      run:
        working-directory: proteinspy_pkg
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          virtualenvs-create: true
          virtualenvs-in-project: true
      - name: Load cached venv
        id: cached-poetry-dependencies
        uses: actions/cache@v4
        with:
          path: proteinspy_pkg/.venv
          key: venv-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('proteinspy_pkg/poetry.lock') }}
      - name: Install dependencies
        if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
        run: poetry install --with dev
      - name: Run tests with coverage
        run: poetry run pytest
      - name: Upload coverage to Codecov
        if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          fail_ci_if_error: false

  lint:
    name: Lint & type-check
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: proteinspy_pkg
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install Poetry
        uses: snok/install-poetry@v1
      - name: Install dependencies
        run: poetry install --with dev
      - name: Black formatting check
        run: poetry run black --check proteinspy tests
      - name: Pylint
        run: poetry run pylint proteinspy --fail-under=7.0
      - name: Mypy type check
        run: poetry run mypy proteinspy
'''

F_CI_PUBLISH = r'''name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    name: Build and publish
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    defaults:
      run:
        working-directory: proteinspy_pkg
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install Poetry
        uses: snok/install-poetry@v1
      - name: Install dependencies
        run: poetry install --only main
      - name: Run tests before publishing
        run: |
          poetry install --with dev
          poetry run pytest --no-cov -q
      - name: Build package
        run: poetry build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: proteinspy_pkg/dist/
'''

F_ISSUE_BUG = r'''---
name: Bug report
about: Something is not working as expected
title: "[BUG] "
labels: bug
assignees: ''
---

## Describe the bug
A clear and concise description of what the bug is.

## Command or code that triggered it
```bash
proteinspy analyze my_protein.cif
```

## Expected behaviour
What you expected to happen.

## Actual behaviour
Paste the full error output here.

## Environment
- OS: [e.g. Ubuntu 22.04 / Windows 11 / macOS 14]
- Python version: [e.g. 3.11]
- Proteinspy version: (`proteinspy --version`)
- Input file format: [e.g. `.cif`, `.pdb`]

## Additional context
Add any other context or screenshots here.
'''

F_ISSUE_FEATURE = r'''---
name: Feature request
about: Suggest a new analysis, output format, or improvement
title: "[FEATURE] "
labels: enhancement
assignees: ''
---

## Is your feature request related to a problem?
A clear description of the problem.

## Describe the solution you would like
What you want to happen.

## Biological / scientific context
Why is this useful in a structural biology or bioinformatics workflow?

## Additional context
Any references, papers, or examples.
'''


# ════════════════════════════════════════════════════════════════════════════
# MAIN — write everything to disk
# ════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("\n" + "=" * 60)
    print("  Proteinspy v1.1.0 — setup script")
    print("=" * 60)
    print(f"\nRepo root : {ROOT}\n")

    # ── proteinspy package files ────────────────────────────────────────────
    print("[ proteinspy package files ]")

    # Modified existing files
    w("proteinspy_pkg/proteinspy/__init__.py",   F_PKG_INIT)
    w("proteinspy_pkg/proteinspy/__main__.py",   F_PKG_MAIN)
    w("proteinspy_pkg/pyproject.toml",           F_PYPROJECT)

    # New sub-packages
    w("proteinspy_pkg/proteinspy/exceptions.py",          F_EXCEPTIONS)
    w("proteinspy_pkg/proteinspy/utils/__init__.py",      F_UTILS_INIT)
    w("proteinspy_pkg/proteinspy/utils/helpers.py",       F_UTILS_HELPERS)
    w("proteinspy_pkg/proteinspy/core/__init__.py",       F_CORE_INIT)
    w("proteinspy_pkg/proteinspy/core/parser.py",         F_CORE_PARSER)
    w("proteinspy_pkg/proteinspy/core/validator.py",      F_CORE_VALIDATOR)
    w("proteinspy_pkg/proteinspy/analysis/__init__.py",   F_ANALYSIS_INIT)
    w("proteinspy_pkg/proteinspy/analysis/basic.py",      F_ANALYSIS_BASIC)
    w("proteinspy_pkg/proteinspy/analysis/advanced.py",   F_ANALYSIS_ADVANCED)
    w("proteinspy_pkg/proteinspy/io/__init__.py",         F_IO_INIT)
    w("proteinspy_pkg/proteinspy/io/writers.py",          F_IO_WRITERS)
    w("proteinspy_pkg/proteinspy/cli/__init__.py",        F_CLI_INIT)
    w("proteinspy_pkg/proteinspy/cli/main.py",            F_CLI_MAIN)

    # ── patch analysis.py with deprecation comment ──────────────────────────
    print("\n[ patching analysis.py with deprecation comment ]")
    analysis_py = os.path.join(ROOT, "proteinspy_pkg", "proteinspy", "analysis.py")
    if os.path.exists(analysis_py):
        with open(analysis_py, "r", encoding="utf-8") as fh:
            original = fh.read()
        if "superseded" not in original:          # don't double-patch
            with open(analysis_py, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(F_ANALYSIS_PY_COMMENT + original)
            print(f"  [patch]  proteinspy_pkg/proteinspy/analysis.py")
        else:
            print(f"  [skip]   analysis.py already patched")
    else:
        print(f"  [skip]   analysis.py not found (nothing to patch)")

    # ── tests ───────────────────────────────────────────────────────────────
    print("\n[ test suite ]")
    w("proteinspy_pkg/tests/__init__.py",                         "")
    w("proteinspy_pkg/tests/conftest.py",                         F_TESTS_CONFTEST)
    w("proteinspy_pkg/tests/fixtures/.gitkeep",                   "")
    w("proteinspy_pkg/tests/unit/__init__.py",                    "")
    w("proteinspy_pkg/tests/unit/test_analysis_basic.py",        F_TEST_BASIC)
    w("proteinspy_pkg/tests/unit/test_analysis_advanced.py",     F_TEST_ADVANCED)
    w("proteinspy_pkg/tests/unit/test_parser.py",                F_TEST_PARSER)
    w("proteinspy_pkg/tests/unit/test_validator.py",             F_TEST_VALIDATOR)
    w("proteinspy_pkg/tests/unit/test_writers.py",               F_TEST_WRITERS)
    w("proteinspy_pkg/tests/integration/__init__.py",            "")
    w("proteinspy_pkg/tests/integration/test_cli.py",            F_TEST_CLI)

    # copy 10AJ.cif into fixtures/
    src = os.path.join(ROOT, "proteinspy_pkg", "10AJ.cif")
    dst = os.path.join(ROOT, "proteinspy_pkg", "tests", "fixtures", "10AJ.cif")
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy2(src, dst)
        print(f"  [copy]   proteinspy_pkg/tests/fixtures/10AJ.cif")
    elif os.path.exists(dst):
        print(f"  [exists] proteinspy_pkg/tests/fixtures/10AJ.cif")
    else:
        print(f"  [WARN]   10AJ.cif not found at {src} — copy it manually")

    # ── repo root files ─────────────────────────────────────────────────────
    print("\n[ repo root files ]")
    w("README.md",           F_README)
    w("CHANGELOG.md",        F_CHANGELOG)
    w(".gitignore",          F_GITIGNORE)
    w("CONTRIBUTING.md",     F_CONTRIBUTING)
    w("CODE_OF_CONDUCT.md",  F_CODE_OF_CONDUCT)

    # ── GitHub Actions & issue templates ────────────────────────────────────
    print("\n[ GitHub Actions & issue templates ]")
    w(".github/workflows/test.yml",                    F_CI_TEST)
    w(".github/workflows/publish.yml",                 F_CI_PUBLISH)
    w(".github/ISSUE_TEMPLATE/bug_report.md",          F_ISSUE_BUG)
    w(".github/ISSUE_TEMPLATE/feature_request.md",     F_ISSUE_FEATURE)

    # ── summary ─────────────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  Done — {len(written)} files written / updated")
    print(f"{'=' * 60}\n")
    print("Next steps — run these commands from the repo root:\n")
    print("  cd proteinspy_pkg")
    print("  poetry install --with dev")
    print("  poetry run pytest --no-cov -q")
    print("  cd ..")
    print("  git add -A")
    print('  git commit -m "feat: v1.1.0 — advanced analyses, PDB support, 114 tests, CI"')
    print("  git push\n")
    print("Then create a GitHub Release tagged v1.1.0 to trigger auto-publish to PyPI.\n")


if __name__ == "__main__":
    main()
