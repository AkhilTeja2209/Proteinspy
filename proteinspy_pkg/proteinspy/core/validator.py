"""
Structure quality validator.

Produces human-readable warnings about common structural problems
without requiring external tools (DSSP, MolProbity, etc.).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from proteinspy.utils.helpers import read_structure

logger = logging.getLogger(__name__)

_RES_HIGH = 2.0
_RES_MEDIUM = 3.0
_RES_LOW = 3.5
_RES_POOR = 4.5
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

    resolution: Optional[float] = (
        st.resolution if st.resolution and st.resolution > 0 else None
    )
    method = "UNKNOWN"
    try:
        block = gemmi.cif.read(path).sole_block()
        m = block.find_value("_exptl.method")
        if m and m not in {"?", "."}:
            method = m.strip().strip("'\"")
    except Exception:
        pass

    if resolution is None:
        if method.upper() not in {
            "SOLUTION NMR",
            "SOLID-STATE NMR",
            "NEUTRON DIFFRACTION",
        }:
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
        info.append(
            "No crystallographic unit cell found (expected for NMR or theoretical models)."
        )

    return {
        "warnings": warnings,
        "info": info,
        "pass": len(warnings) == 0,
        "resolution": resolution,
        "method": method,
        "model_count": model_count,
        "missing_fraction": missing_fraction,
    }
