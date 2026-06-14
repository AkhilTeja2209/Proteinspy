# Usage

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
proteinspy analyze my_protein.cif
proteinspy analyze my_protein.pdb --output json
```

---

### `resolution`

Report the crystallographic or cryo-EM resolution and experimental method.

```bash
proteinspy resolution my_protein.cif
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
proteinspy chains my_protein.cif
proteinspy chains my_protein.cif --output csv
```

---

### `ligands`

Identify all non-solvent ligand molecules.

```bash
proteinspy ligands my_protein.cif
proteinspy ligands my_protein.cif --output json
```

---

### `missing`

Find residues present in the deposited sequence but absent from ATOM records.

```bash
proteinspy missing my_protein.cif
```

---

### `bfactor`

Compute B-factor (temperature factor) statistics globally and per chain.
High B-factors indicate flexible or disordered regions.

```bash
proteinspy bfactor my_protein.cif
proteinspy bfactor my_protein.cif --output json
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
proteinspy disulfide my_protein.cif
proteinspy disulfide my_protein.cif --output json
```

---

### `interface`

Report residues at inter-chain interfaces using Cα–Cα distance.
The cutoff is configurable (default 5.0 Å).

```bash
proteinspy interface my_protein.cif
proteinspy interface my_protein.cif --cutoff 8.0
proteinspy interface my_protein.cif --output csv
```

---

### `validate`

Run a quick quality check on a structure file. Reports:

- Resolution with quality thresholds (< 2.0 Å excellent, > 3.5 Å warning)
- Missing residue fraction (warns if > 10%)
- NMR ensemble detection
- Unit cell presence

```bash
proteinspy validate my_protein.cif
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
proteinspy export my_protein.cif report.json

# Export specific analysis to CSV
proteinspy export my_protein.cif chains.csv --analysis chains

# Available analyses:
# resolution, chains, ligands, missing, bfactor, disulfide, interface, validate, all
proteinspy export my_protein.cif bonds.json --analysis disulfide
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
proteinspy chains my_protein.cif --output json
proteinspy chains my_protein.cif -o json
```

---

## Working with PDB format

All commands work identically with `.pdb` files:

```bash
proteinspy analyze  my_protein.pdb
proteinspy bfactor  my_protein.pdb --output json
proteinspy validate my_protein.pdb
```

Compressed files are also supported:

```bash
proteinspy analyze my_protein.cif.gz
proteinspy analyze my_protein.pdb.gz
```
