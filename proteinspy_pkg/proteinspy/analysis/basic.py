"""
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

_STANDARD_AA: frozenset = frozenset(
    [
        "ALA",
        "ARG",
        "ASN",
        "ASP",
        "CYS",
        "GLN",
        "GLU",
        "GLY",
        "HIS",
        "ILE",
        "LEU",
        "LYS",
        "MET",
        "PHE",
        "PRO",
        "SER",
        "THR",
        "TRP",
        "TYR",
        "VAL",
        "SEC",
        "PYL",
        "UNK",
    ]
)
_STANDARD_NUC: frozenset = frozenset(
    ["DA", "DC", "DG", "DT", "DI", "A", "C", "G", "U", "I"]
)
_SOLVENT: frozenset = frozenset(
    [
        "HOH",
        "WAT",
        "DOD",
        "SO4",
        "EDO",
        "GOL",
        "PEG",
        "ACT",
        "MPD",
        "PO4",
        "CLR",
        "DMS",
        "FMT",
        "TRS",
        "IOD",
        "BME",
        "EPE",
    ]
)


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
        res: Optional[float] = (
            st.resolution if st.resolution and st.resolution > 0 else None
        )

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
        if (
            "FileNotFound" in type(exc).__name__
            or "InvalidFileFormat" in type(exc).__name__
        ):
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
                    str(polymer.check_polymer_type())
                    if len(polymer) > 0
                    else "non-polymer"
                )
                chains.append(
                    {
                        "id": chain.name,
                        "type": ptype,
                        "residue_count": sum(1 for _ in chain),
                    }
                )

        return {"chain_count": len(chains), "chains": chains}

    except Exception as exc:
        if (
            "FileNotFound" in type(exc).__name__
            or "InvalidFileFormat" in type(exc).__name__
        ):
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
                    if (
                        name in _STANDARD_AA
                        or name in _STANDARD_NUC
                        or name in _SOLVENT
                    ):
                        continue
                    key = f"{name}:{chain.name}:{res.seqid}"
                    if key in seen:
                        continue
                    seen.add(key)
                    found.append(
                        {"id": name, "chain": chain.name, "seq_num": str(res.seqid)}
                    )

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
                    found.append(
                        {
                            "id": comp,
                            "chain": "?",
                            "seq_num": "?",
                            "name": row[0].strip().strip("'\""),
                        }
                    )
            except Exception:
                pass

        return {
            "ligand_count": len(found),
            "has_ligand": len(found) > 0,
            "ligands": found,
        }

    except Exception as exc:
        if (
            "FileNotFound" in type(exc).__name__
            or "InvalidFileFormat" in type(exc).__name__
        ):
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
                observed = {
                    str(r.label_seq) for r in polymer if r.label_seq is not None
                }
                entity_id = next((r.entity_id for r in polymer), None)
                if entity_id is None:
                    continue
                entity = st.get_entity(entity_id)
                if entity is None:
                    continue
                for idx, mon in enumerate(entity.full_sequence, start=1):
                    if str(idx) not in observed:
                        missing.append(
                            {"chain": chain.name, "seq_num": idx, "residue": mon}
                        )

        cif_missing: List[Dict[str, Any]] = []
        try:
            block = gemmi.cif.read(path).sole_block()
            table = block.find(
                "_pdbx_unobs_or_zero_occ_residues.",
                [
                    "auth_asym_id",
                    "auth_comp_id",
                    "auth_seq_id",
                    "PDB_model_num",
                    "polymer_flag",
                ],
            )
            for row in table:
                if row[4].strip() != "Y":
                    continue
                cif_missing.append(
                    {
                        "chain": row[0].strip(),
                        "residue": row[1].strip(),
                        "seq_num": row[2].strip(),
                        "model": row[3].strip(),
                    }
                )
        except Exception:
            pass

        final = cif_missing if cif_missing else missing
        return {"missing_count": len(final), "missing_residues": final}

    except Exception as exc:
        if (
            "FileNotFound" in type(exc).__name__
            or "InvalidFileFormat" in type(exc).__name__
        ):
            raise
        raise AnalysisError(
            f"Missing residue analysis failed for '{path}': {exc}"
        ) from exc
