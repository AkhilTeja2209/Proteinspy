# Installation

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
$env:PATH += ";$env:APPDATA\Python\Python313\Scripts"
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
