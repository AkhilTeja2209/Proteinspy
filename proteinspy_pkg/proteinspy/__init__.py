"""
Proteinspy — Protein structure analysis from the terminal.

Public API
----------
>>> from proteinspy import get_resolution, get_chains
>>> get_resolution("protein.cif")
{'resolution': 2.1, 'unit': 'Å', 'method': 'X-RAY DIFFRACTION'}
"""

from proteinspy.analysis.basic import (
    get_chains,
    get_ligands,
    get_missing_residues,
    get_resolution,
)
from proteinspy.analysis.advanced import (
    get_bfactor_stats,
    get_chain_interface,
    get_disulfide_bonds,
)
from proteinspy.core.validator import validate_structure
from proteinspy.io.writers import to_json, to_csv, write_output

__version__ = "1.1.5"
__author__ = "AkhilTeja2209"
__license__ = "MIT"

__all__ = [
    "get_resolution",
    "get_chains",
    "get_ligands",
    "get_missing_residues",
    "get_bfactor_stats",
    "get_disulfide_bonds",
    "get_chain_interface",
    "validate_structure",
    "to_json",
    "to_csv",
    "write_output",
]
