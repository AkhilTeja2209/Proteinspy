# Proteinspy

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
