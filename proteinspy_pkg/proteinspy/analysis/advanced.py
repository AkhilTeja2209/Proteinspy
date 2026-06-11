"""
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
