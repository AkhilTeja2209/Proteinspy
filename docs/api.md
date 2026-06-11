# API Reference

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
