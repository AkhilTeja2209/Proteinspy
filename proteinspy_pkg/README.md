# Proteinspy

This is a python package based on Poetry.

This repository can be used to find the _Resolution_, _Missing residues_, _Ligands_, and _Chains_ in any Protein sample uploaded. The sample must be in a `.cif` file format for the package to run properly. 

## 🔋 Installation

```bash
pip install proteinspy
```
### Windows note

If `proteinspy` is not recognized after installation, add the Python Scripts
folder to your PATH. Run this once in PowerShell:

```powershell
$env:PATH += ";$env:APPDATA\Python\Python313\Scripts"
[System.Environment]::SetEnvironmentVariable("PATH", $env:PATH, "User")
```

Then restart PowerShell and run `proteinspy` again.

## 💡 Getting Started

After installation, run this first to see all available commands:

```bash
proteinspy
```

Or use the help flag:

```bash
proteinspy --help
```

## 📚 Data
A sample [protein](https://github.com/AkhilTeja2209/Proteinspy/blob/main/Final_proj_1/10AJ.cif), has been given, and can also be accessed from the [PDB](https://www.rcsb.org), among many other samples. 

## 🗒️ Requirements
- python [poetry](https://python-poetry.org/docs/) and its pre-requisites \(`Python 3.9+` and `pip`).
- Dependencies installed automatically: `gemmi`, `rich`, `click`

## 🚀 To run the pipeline,

**Copy these and run them directly for quickest results.** 

### 1. For a mode based implementation
```bash
proteinspy analyze 10AJ.cif    #replace the protein input name with your own file if you're using a different input or a filename
```

### 2. For an argument based implementation
```bash
proteinspy resolution 10AJ.cif    #gives the resolution of the protein
proteinspy ligands 10AJ.cif       #gives the ligands in the protein
proteinspy missing 10AJ.cif       #gives the missing residues in the protein
proteinspy chains 10AJ.cif        #gives the chains in the protein
```

🟥 **Note:** swap the file name if you are using your own file

## 💻 Commands

**Format:** `proteinspy <command> <file.cif>`

| Command | Description |
|---|---|
| `proteinspy analyze` | Run all analyses — resolution, chains, ligands, missing residues |
| `proteinspy resolution` | Report crystallographic resolution only |
| `proteinspy chains` | Report all polymer chains only |
| `proteinspy ligands` | Report all ligand molecules only |
| `proteinspy missing` | Report all missing residues only |


## 📈 Future Enhancements
- [ ] CLI UI/UX
- [ ] Containerisation, using docker

## ⚠️ NOTE
This is an open-source project, and any contributions, even if not mentioned in the future enhancements section, are welcome. 

## 📃 Documentation
Full documentation at [https://akhilteja2209.github.io/Proteinspy/](https://akhilteja2209.github.io/Proteinspy/)

---

**Version:** 1.0.1
