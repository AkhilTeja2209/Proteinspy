# Proteinspy

[![PyPI](https://img.shields.io/pypi/v/proteinspy)](https://pypi.org/project/proteinspy/)
[![Tests](https://github.com/AkhilTeja2209/Proteinspy/actions/workflows/test.yml/badge.svg)](https://github.com/AkhilTeja2209/Proteinspy/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)](https://pypi.org/project/proteinspy/)
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
$scriptsPath = python -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"
$env:PATH += ";$scriptsPath"
[System.Environment]::SetEnvironmentVariable("PATH", $env:PATH, "User")
```

Then restart PowerShell and run `proteinspy` again.

---

## Quick start

```bash
# See all commands with
proteinspy
# Or
proteinspy --help

# Run all basic analyses on a structure file
proteinspy analyze my_protein.cif

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
proteinspy analyze    my_protein.cif
proteinspy resolution my_protein.cif
proteinspy chains     my_protein.cif
proteinspy ligands    my_protein.cif
proteinspy missing    my_protein.cif

# Advanced analyses
proteinspy bfactor   my_protein.cif
proteinspy disulfide my_protein.cif
proteinspy interface my_protein.cif --cutoff 8.0
proteinspy validate  my_protein.cif

# Output formats — any command supports --output / -o
proteinspy chains    my_protein.cif --output json
proteinspy bfactor   my_protein.cif --output csv
proteinspy analyze   my_protein.cif -o tsv

# Export to file (format inferred from extension)
proteinspy export my_protein.cif report.json
proteinspy export my_protein.cif chains.csv  --analysis chains
proteinspy export my_protein.cif bonds.json  --analysis disulfide
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
result = get_resolution("my_protein.cif")
print(result["resolution"], result["method"])

# Advanced
stats = get_bfactor_stats("my_protein.cif")
print(stats["overall"]["mean"])

# Export
write_output(get_chains("my_protein.cif"), "json", output_path="chains.json")
```
Check out [API Reference](https://akhilteja2209.github.io/Proteinspy/api/) for the list of all the functions.

---

## Requirements

- `pip` installed on device
- Python 3.10 or later
- Dependencies installed automatically: `gemmi`, `rich`, `click`

---

## Contributing

Contributions are welcome — new analyses, output formats, bug fixes, or docs.
See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, code standards,
and how to add a new analysis command.

---

## Documentation

Full Installation and usage guides at
[akhilteja2209.github.io/Proteinspy](https://akhilteja2209.github.io/Proteinspy/)

---

**Version:** 1.1.4
