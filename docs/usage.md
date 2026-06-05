# Usage



## Getting a sample file



A sample file `10AJ.cif` is included in the repository. You can also download any structure from [RCSB PDB](https://www.rcsb.org) — search for a protein and download the mmCIF format.



## Interactive (analyze) mode



Runs all analyses in one go and displays a full structured report:



```bash

proteinspy analyze 10AJ.cif

```



## Argument mode



Run individual analyses:



```bash

proteinspy resolution 10AJ.cif   # crystallographic resolution in Å

proteinspy chains 10AJ.cif       # all chain IDs and types

proteinspy ligands 10AJ.cif      # ligand names and counts

proteinspy missing 10AJ.cif      # missing residue positions

```



## Using with Poetry (from source)



Prefix all commands with `poetry run`:



```bash

poetry run proteinspy analyze 10AJ.cif

poetry run proteinspy resolution 10AJ.cif

```

