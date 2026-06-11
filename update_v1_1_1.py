#!/usr/bin/env python3
"""
Proteinspy v1.1.1 — docs update + version bump.
Run from the ROOT of your Proteinspy repository.
"""
import os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if not os.path.isdir(os.path.join(ROOT, "proteinspy_pkg")):
    print("ERROR: Run from the ROOT of the Proteinspy repository.")
    sys.exit(1)

written = []

def w(rel_path, content):
    full = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    written.append(rel_path)
    print(f"  [write]  {rel_path}")

def patch(rel_path, old, new):
    full = os.path.join(ROOT, rel_path)
    with open(full, "r", encoding="utf-8") as fh:
        content = fh.read()
    if old not in content:
        print(f"  [skip]   {rel_path} — pattern not found")
        return
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content.replace(old, new))
    written.append(rel_path)
    print(f"  [patch]  {rel_path}")

# ════════════════════════════════════════════════════════════════════════════
# DOCUMENTATION
# ════════════════════════════════════════════════════════════════════════════

w("docs/index.md", '''# Proteinspy

**Proteinspy** is a CLI tool and Python library for analysing protein structure files.

[![PyPI](https://img.shields.io/pypi/v/proteinspy)](https://pypi.org/project/proteinspy/)
[![Tests](https://github.com/AkhilTeja2209/Proteinspy/actions/workflows/test.yml/badge.svg)](https://github.com/AkhilTeja2209/Proteinspy/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)](https://pypi.org/project/proteinspy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/AkhilTeja2209/Proteinspy/blob/main/LICENSE)

---

## What is Proteinspy?

Proteinspy lets you analyse protein structure files directly from the terminal
or from a Python script — no GUI, no manual setup, no external tools required.

It is built on [gemmi](https://gemmi.readthedocs.io/), a fast C++ library for
crystallography, wrapped in a clean CLI with [Click](https://click.palletsprojects.com/)
and formatted output via [Rich](https://rich.readthedocs.io/).

---

## Supported file formats

| Extension | Format |
|---|---|
| `.cif`, `.mmcif`, `.pdbx` | mmCIF (recommended) |
| `.pdb`, `.ent` | Legacy PDB format |
| Any of the above + `.gz` | Gzip-compressed |

---

## Quick example

```bash
pip install proteinspy
proteinspy analyze 10AJ.cif
```

```
Resolution : 2.42 Å
Method     : X-RAY DIFFRACTION

Chains  (1 total)
 Chain ID   Type                    Residues
 A          PolymerType.PeptideL    455

Ligands  (2 found)
 Ligand ID   Chain   Seq Num
 T27         A       501
 MG          A       502
```

---

## Navigation

- [Installation](installation.md) — pip, Poetry, Windows notes
- [Usage](usage.md) — all commands with examples
- [API Reference](api.md) — Python library interface
- [Changelog](changelog.md) — version history
''')

w("docs/installation.md", '''# Installation

## From PyPI (recommended)

```bash
pip install proteinspy
```

## From source

```bash
git clone https://github.com/AkhilTeja2209/Proteinspy.git
cd Proteinspy/proteinspy_pkg
poetry install
```

---

## Windows note

If `proteinspy` is not recognised after installation, the Python Scripts
folder is not on your PATH. Run this once in PowerShell:

```powershell
$env:PATH += ";$env:APPDATA\\Python\\Python313\\Scripts"
[System.Environment]::SetEnvironmentVariable("PATH", $env:PATH, "User")
```

Then restart PowerShell and run `proteinspy` again.

---

## Requirements

- Python 3.10 or later
- Dependencies installed automatically: `gemmi`, `rich`, `click`

---

## Verify installation

```bash
proteinspy --version
# proteinspy, version 1.1.1
```
''')

w("docs/usage.md", '''# Usage

## Basic syntax

```
proteinspy <command> <file> [--output table|json|csv|tsv]
```

All commands accept `.cif`, `.mmcif`, `.pdb`, `.ent`, and `.gz` compressed variants.

---

## Commands

### `analyze`

Run all basic analyses in one go — resolution, chains, ligands, missing residues.

```bash
proteinspy analyze protein.cif
proteinspy analyze protein.pdb --output json
```

---

### `resolution`

Report the crystallographic or cryo-EM resolution and experimental method.

```bash
proteinspy resolution protein.cif
```

**Output:**
```
Resolution : 2.42 Å
Method     : X-RAY DIFFRACTION
```

---

### `chains`

List all polymer chains with their type and residue count.

```bash
proteinspy chains protein.cif
proteinspy chains protein.cif --output csv
```

---

### `ligands`

Identify all non-solvent ligand molecules.

```bash
proteinspy ligands protein.cif
proteinspy ligands protein.cif --output json
```

---

### `missing`

Find residues present in the deposited sequence but absent from ATOM records.

```bash
proteinspy missing protein.cif
```

---

### `bfactor`

Compute B-factor (temperature factor) statistics globally and per chain.
High B-factors indicate flexible or disordered regions.

```bash
proteinspy bfactor protein.cif
proteinspy bfactor protein.cif --output json
```

**Output:**
```
B-Factor Statistics

  Overall — min: 26.34  max: 151.94  mean: 54.87  std: 16.54  atoms: 3424

 Chain   Min     Max      Mean    Std     Atoms
 A       26.34   151.94   54.87   16.54   3424
```

---

### `disulfide`

Detect disulfide bonds by measuring SG–SG distances between CYS residues.
Any pair with distance ≤ 2.5 Å is reported as a disulfide bond.

```bash
proteinspy disulfide protein.cif
proteinspy disulfide protein.cif --output json
```

---

### `interface`

Report residues at inter-chain interfaces using Cα–Cα distance.
The cutoff is configurable (default 5.0 Å).

```bash
proteinspy interface protein.cif
proteinspy interface protein.cif --cutoff 8.0
proteinspy interface protein.cif --output csv
```

---

### `validate`

Run a quick quality check on a structure file. Reports:

- Resolution with quality thresholds (< 2.0 Å excellent, > 3.5 Å warning)
- Missing residue fraction (warns if > 10%)
- NMR ensemble detection
- Unit cell presence

```bash
proteinspy validate protein.cif
```

**Output:**
```
Structure Validation  PASS

Info:
  • Good resolution (2.42 Å).
  • Low missing-residue fraction (1.9%) — good model completeness.

  No quality warnings.
```

---

### `export`

Export any analysis to a file. Format is inferred from the file extension.

```bash
# Export all analyses to JSON
proteinspy export protein.cif report.json

# Export specific analysis to CSV
proteinspy export protein.cif chains.csv --analysis chains

# Available analyses:
# resolution, chains, ligands, missing, bfactor, disulfide, interface, validate, all
proteinspy export protein.cif bonds.json --analysis disulfide
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

```bash
# These are all equivalent ways to specify the flag
proteinspy chains protein.cif --output json
proteinspy chains protein.cif -o json
```

---

## Working with PDB format

All commands work identically with `.pdb` files:

```bash
proteinspy analyze  protein.pdb
proteinspy bfactor  protein.pdb --output json
proteinspy validate protein.pdb
```

Compressed files are also supported:

```bash
proteinspy analyze protein.cif.gz
proteinspy analyze protein.pdb.gz
```
''')

w("docs/api.md", '''# API Reference

All analysis functions are available as a Python library in addition to the CLI.

## Installation

```python
from proteinspy import (
    # Basic analyses
    get_resolution,
    get_chains,
    get_ligands,
    get_missing_residues,
    # Advanced analyses
    get_bfactor_stats,
    get_disulfide_bonds,
    get_chain_interface,
    # Validation
    validate_structure,
    # I/O
    to_json,
    to_csv,
    write_output,
)
```

---

## Basic analyses

### `get_resolution(path)`

Extract crystallographic or cryo-EM resolution.

```python
result = get_resolution("protein.cif")
# {'resolution': 2.42, 'unit': 'Å', 'method': 'X-RAY DIFFRACTION'}
```

**Returns:** `dict` with keys `resolution` (float or None), `unit` (str or None), `method` (str)

---

### `get_chains(path)`

List all polymer chains in the first model.

```python
result = get_chains("protein.cif")
# {
#   'chain_count': 2,
#   'chains': [
#     {'id': 'A', 'type': 'PolymerType.PeptideL', 'residue_count': 300},
#     {'id': 'B', 'type': 'PolymerType.PeptideL', 'residue_count': 280},
#   ]
# }
```

**Returns:** `dict` with keys `chain_count` (int), `chains` (list of dicts)

---

### `get_ligands(path)`

Identify non-solvent ligand molecules.

```python
result = get_ligands("protein.cif")
# {'ligand_count': 1, 'has_ligand': True,
#  'ligands': [{'id': 'ATP', 'chain': 'A', 'seq_num': '501'}]}
```

**Returns:** `dict` with keys `ligand_count` (int), `has_ligand` (bool), `ligands` (list)

---

### `get_missing_residues(path)`

Find residues present in the sequence but absent from ATOM records.

```python
result = get_missing_residues("protein.cif")
# {'missing_count': 5,
#  'missing_residues': [{'chain': 'A', 'residue': 'GLY', 'seq_num': 12}, ...]}
```

**Returns:** `dict` with keys `missing_count` (int), `missing_residues` (list)

---

## Advanced analyses

### `get_bfactor_stats(path)`

Compute B-factor statistics globally and per chain.

```python
result = get_bfactor_stats("protein.cif")
# {
#   'overall': {'min': 10.2, 'max': 89.4, 'mean': 32.1, 'std': 12.3, 'atom_count': 3424},
#   'by_chain': [{'chain_id': 'A', 'min': 10.2, ...}, ...]
# }
```

**Returns:** `dict` with keys `overall` (dict), `by_chain` (list of dicts)

---

### `get_disulfide_bonds(path)`

Detect CYS–CYS disulfide bonds by SG–SG distance (≤ 2.5 Å).

```python
result = get_disulfide_bonds("protein.cif")
# {
#   'bond_count': 2,
#   'bonds': [
#     {'chain_a': 'A', 'res_a': 'CYS', 'seqid_a': '14',
#      'chain_b': 'A', 'res_b': 'CYS', 'seqid_b': '38',
#      'distance_A': 2.031},
#   ]
# }
```

**Returns:** `dict` with keys `bond_count` (int), `bonds` (list of dicts)

---

### `get_chain_interface(path, cutoff=5.0)`

Find residues at inter-chain interfaces by Cα distance.

```python
result = get_chain_interface("protein.cif", cutoff=5.0)
# {
#   'interface_count': 1,
#   'interfaces': [
#     {'chain_a': 'A', 'chain_b': 'B', 'contact_pairs': 42,
#      'residues_a': ['101', '102', ...], 'residues_b': ['5', '6', ...]},
#   ]
# }
```

**Parameters:**
- `path` — path to structure file
- `cutoff` — Cα–Cα distance threshold in Å (default 5.0)

**Returns:** `dict` with keys `interface_count` (int), `interfaces` (list of dicts)

---

## Validation

### `validate_structure(path)`

Run a quick quality check on a structure file.

```python
result = validate_structure("protein.cif")
# {
#   'pass': True,
#   'warnings': [],
#   'info': ['Good resolution (2.42 Å).', 'Low missing-residue fraction (1.9%).'],
#   'resolution': 2.42,
#   'method': 'X-RAY DIFFRACTION',
#   'model_count': 1,
#   'missing_fraction': 0.019,
# }
```

**Returns:** `dict` with keys `pass` (bool), `warnings` (list), `info` (list),
`resolution`, `method`, `model_count`, `missing_fraction`

---

## I/O helpers

### `to_json(data, indent=2)`

Serialise any analysis result to a JSON string.

```python
from proteinspy import get_chains, to_json
print(to_json(get_chains("protein.cif")))
```

---

### `to_csv(data, delimiter=",")`

Serialise any analysis result to CSV. List-valued keys are expanded to one row each.

```python
from proteinspy import get_chains, to_csv
print(to_csv(get_chains("protein.cif")))
```

---

### `write_output(data, fmt, output_path=None)`

Format data and optionally write to a file.

```python
from proteinspy import get_bfactor_stats, write_output

data = get_bfactor_stats("protein.cif")

# Print to terminal
print(write_output(data, "json"))

# Write to file
write_output(data, "csv", output_path="bfactors.csv")
```

**Parameters:**
- `data` — dict returned by any analysis function
- `fmt` — one of `"json"`, `"csv"`, `"tsv"`
- `output_path` — optional file path to write to

---

## Error handling

All functions raise from the `ProteinsyError` hierarchy:

```python
from proteinspy.exceptions import (
    ProteinsyError,          # base — catch all library errors
    FileNotFoundError,       # file does not exist
    InvalidFileFormatError,  # cannot parse the file
    AnalysisError,           # analysis step failed
    ExportError,             # write/serialise failed
)

try:
    result = get_resolution("missing.cif")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except ProteinsyError as e:
    print(f"Proteinspy error: {e}")
```
''')

w("docs/changelog.md", '''# Changelog

See [CHANGELOG.md](https://github.com/AkhilTeja2209/Proteinspy/blob/main/CHANGELOG.md)
on GitHub for the full version history.

---

## v1.1.1 — 2025-06-11

Metadata and documentation update. No functional changes.

- Updated PyPI package description to reflect v1.1.0 features
- Comprehensive documentation rewrite covering all new commands
- Python minimum version updated to 3.10 in package metadata

---

## v1.1.0 — 2025-06-11

Major feature release.

- New commands: `bfactor`, `disulfide`, `interface`, `validate`, `export`
- `--output table|json|csv|tsv` flag on every command
- `.pdb` / `.ent` / `.gz` format support
- Full package restructure with `core/`, `analysis/`, `cli/`, `io/`, `utils/`
- 111 tests across unit and integration layers
- GitHub Actions CI on Python 3.10–3.12 (Ubuntu + macOS)
- Custom exception hierarchy, `@lru_cache` structure parsing, full type hints

---

## v1.0.2 — 2025-05-01

- Minor packaging fixes

---

## v1.0.0 — 2025-04-01

- Initial release: `analyze`, `resolution`, `chains`, `ligands`, `missing`
- `.cif` format support via gemmi
- Rich terminal output, PyPI distribution
''')

# ════════════════════════════════════════════════════════════════════════════
# VERSION BUMP — 1.1.0 → 1.1.1
# ════════════════════════════════════════════════════════════════════════════

print("\n[ version bump ]")

patch("proteinspy_pkg/pyproject.toml",
      'version = "1.1.0"',
      'version = "1.1.1"')

patch("proteinspy_pkg/proteinspy/__init__.py",
      '__version__ = "1.1.0"',
      '__version__ = "1.1.1"')

patch("proteinspy_pkg/proteinspy/cli/main.py",
      'version="1.1.0"',
      'version="1.1.1"')

# ════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════════════

print(f"\n{'=' * 60}")
print(f"  Done — {len(written)} files written / patched")
print(f"{'=' * 60}\n")
print("Next steps:\n")
print("  git add -A")
print('  git commit -m "docs: rewrite documentation, bump version to v1.1.1"')
print("  git push\n")
print("Then go to GitHub → Releases → Draft a new release:")
print("  Tag:   v1.1.1")
print("  Title: v1.1.1 — documentation update")
print("  Body:  Metadata and documentation update. No functional changes.")
