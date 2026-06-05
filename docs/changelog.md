# Changelog

## v1.0.1 — 2026-06-06

### Changes
- Added rich-formatted help table — run `proteinspy` with no arguments to see all commands
- Added `--version` flag
- Fixed CLI entry point
- Renamed package folder from `Final_proj_1` to `proteinspy_pkg`
- Updated README with getting started instructions and command reference

## v1.0.0 — 2026-06-05

### Initial Release
- `analyze` command: full structured protein report
- `resolution`, `chains`, `ligands`, `missing` subcommands
- Rich terminal output via `rich`
- CIF/mmCIF parsing via `gemmi`
- CLI framework via `click`
- Sample structure `10AJ.cif` included
- Published to PyPI: `pip install proteinspy`
- Documentation live at https://akhilteja2209.github.io/Proteinspy/
