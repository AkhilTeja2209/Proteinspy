# Proteinspy

A Poetry-based Python package to analyze protein 3D structure from `.cif` files.

Proteinspy extracts key structural metadata from mmCIF files using gemmi and displays results beautifully in the terminal using rich.

## What it extracts

| Feature | Description |
|---|---|
| Resolution | Crystallographic resolution in Angstroms |
| Chains | All polymer chains in the structure |
| Ligands | Non-polymer ligand molecules present |
| Missing Residues | Gaps in the sequence not resolved in the structure |

## Quick Start

Install and run:

    pip install proteinspy
    proteinspy analyze 10AJ.cif

See [Installation](installation.md) for full setup, and [Usage](usage.md) for all commands.