# Proteinspy

This is a python package based on Poetry.

This repository can be used to find the _Resolution_, _Missing residues_, _Ligands_, and _Chains_ in any Protein sample uploaded. The sample must be in a .cif file for the pipeline to run properly. 

## 📚 Data
A sample [protein](https://github.com/AkhilTeja2209/Proteinspy/blob/main/Final_proj_1/10AJ.cif), has been given, and can also be accessed from the [PDB](https://www.rcsb.org), among many other samples. 

## 🗒️ Requirements
python [poetry](https://python-poetry.org/docs/) and its pre-requisites must be available on the system.

## 🚀 To run the pipeline,

1. For a mode based implementation
```bash
cd "<your complete folder path>"
poetry install    #installs all the dependencies of the package

poetry run proteinspy analyze 10AJ.cif    #replace the protein input name with your own file if you're using a different input or a filename
```

2. For an argument based implementation
```bash
cd "<your complete folder path>"
poetry install    #installs all the dependencies of the package

poetry run proteinspy resolution 10AJ.cif    #gives the resolution of the protein
poetry run proteinspy ligands 10AJ.cif       #gives the ligands in the protein
poetry run proteinspy missing 10AJ.cif       #gives the missing residues in the protein
poetry run proteinspy chains 10AJ.cif        #gives the chains in the protein
```

## 📈 Future Enhancements
- [ ] CLI UI/UX
- [ ] Containerisation, using docker
- [ ] Help section in CLI for better usability

## ⚠️ NOTE
This is an open-source project, and any contribtions, even if not mentioned in the future enhancements section, are welcome. 

---

**Version:** 1.0.0
