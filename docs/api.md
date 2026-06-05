# API Reference

## CLI Commands

All commands follow the pattern:

**proteinspy \<command> <file.cif>**


| Command | Description | Output |
|---|---|---|
| `analyze` | Full report — all fields | Structured rich panel |
| `resolution` | Crystallographic resolution | Value in Ångströms |
| `chains` | Polymer chains | Chain IDs and entity types |
| `ligands` | Non-polymer ligands | Ligand names and instance counts |
| `missing` | Missing residues | Residue names and sequence positions |



## Input Format



Only `.cif` (mmCIF) files are supported.



Sources:

- [RCSB PDB](https://www.rcsb.org) — download any entry as mmCIF

- [PDBe](https://www.ebi.ac.uk/pdbe/)

- [AlphaFold](https://alphafold.ebi.ac.uk/) structure predictions exported as mmCIF

