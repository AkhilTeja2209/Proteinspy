# Changelog

All notable changes to Proteinspy are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.5] - 2026-06-14

### Fixed
- Unstable PyPI documentation update
- Testing fallacies during production release; version dynamically checked without the requirement of future updates.

---

## [1.1.4] - 2026-06-13

**Notice:** Unstable release version

### Fixed
- Inconsistent details in documentation and PyPI.
- Features made up-to-date in the documentation.

---

## [1.1.3] - 2026-06-11

### Fixed
- Visual updates to PyPI to make it consistent and fix the description.

---

## [1.1.2] - 2026-06-11

### Fixed
- Fixed PyPI homepage description to reflect all the latest changes, including all the features introduced in v1.1.0.

---

## [1.1.1] - 2026-06-11

### Fixed
- Added the new CLI commands, API Interface, and Python package fuctions to documentation.
- Rewrote the documentation website.

### Changed
- Denounced Python 3.9 support.
- 10AJ.cif, the sample protein to test package functions is no longer shipped with the package download; only supported when cloning the repository for Proteinspy usage.

---

## [1.1.0] - 2025-06-11

### Added

**New CLI commands**
- `bfactor` — B-factor (temperature factor) statistics, global and per chain
  (min, max, mean, std, atom count)
- `disulfide` — detect CYS–CYS disulfide bonds by SG–SG distance (≤ 2.5 Å),
  reporting both chains, residue names, sequence IDs, and exact distance
- `interface` — inter-chain interface residues by Cα–Cα distance with a
  configurable `--cutoff` (default 5.0 Å)
- `validate` — quick quality check reporting resolution warnings, missing
  residue fraction, NMR ensemble detection, and unit cell presence
- `export` — write any single analysis or the full set to `.json`, `.csv`,
  or `.tsv`; output format inferred from the file extension

**`--output` / `-o` flag on every command**
- All existing commands (`analyze`, `resolution`, `chains`, `ligands`,
  `missing`) and all new commands now accept `--output table|json|csv|tsv`
- `table` (default) — existing Rich terminal output, unchanged
- `json` — pretty-printed, machine-readable JSON
- `csv` — comma-separated, list keys expanded to one row each
- `tsv` — tab-separated equivalent for bioinformatics pipelines

**PDB / ENT format support**
- Structure files ending in `.pdb`, `.ent`, `.pdb.gz`, or `.ent.gz` are
  now accepted by every command in addition to `.cif`/`.mmcif`/`.pdbx`

**Package architecture**
- `proteinspy/analysis/basic.py` — the four original analyses, rewritten
  with full type hints, Google-style docstrings, and structured error handling
- `proteinspy/analysis/advanced.py` — three new analyses (B-factor,
  disulfide, interface)
- `proteinspy/cli/main.py` — Click CLI, moved from `__main__.py` and extended
- `proteinspy/core/parser.py` — unified structure reader
- `proteinspy/core/validator.py` — quality validator
- `proteinspy/io/writers.py` — JSON / CSV / TSV serialisers
- `proteinspy/utils/helpers.py` — `@lru_cache`-backed `read_structure()`,
  format detection
- `proteinspy/exceptions.py` — `ProteinsyError` hierarchy
  (`FileNotFoundError`, `InvalidFileFormatError`, `AnalysisError`,
  `ExportError`)

**Testing — 114 tests**
- `tests/unit/test_analysis_basic.py` (26 tests)
- `tests/unit/test_analysis_advanced.py` (24 tests)
- `tests/unit/test_parser.py` (14 tests)
- `tests/unit/test_validator.py` (9 tests)
- `tests/unit/test_writers.py` (16 tests)
- `tests/integration/test_cli.py` (25 tests — every command, table + JSON output)
- `tests/fixtures/10AJ.cif` — bundled test structure

**CI / CD**
- `.github/workflows/test.yml` — matrix across Python 3.9–3.12 on Ubuntu,
  macOS, and Windows; includes Black formatting check, Pylint, and Mypy
- `.github/workflows/publish.yml` — trusted PyPI publishing on GitHub Release
  (no API key required)

**Repository hygiene**
- `.gitignore` — Python, Poetry, pytest, mypy, IDE, and OS artefacts
- `CONTRIBUTING.md` — Poetry setup, test commands, code standards, template
  for adding a new analysis function
- `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`

### Changed

- `pyproject.toml` — `click` added as a declared runtime dependency (was used
  but undeclared — a packaging bug); `gemmi` and `rich` pinned to minimum
  known-good versions (`^0.6.5` and `^13.0`) instead of wildcards; dev
  dependencies (`pytest`, `black`, `pylint`, `mypy`, `mkdocs`) now tracked
  in `[tool.poetry.group.dev.dependencies]`; pytest, coverage, Black, mypy,
  and Pylint config added; `classifiers` expanded to include Python version
  tags and more specific topic tags; entry point updated to
  `proteinspy.cli.main:main`
- `__init__.py` — now exports all 8 analysis functions, 3 I/O helpers,
  `validate_structure`, `__version__`, `__author__`, `__license__`, and a
  proper `__all__`
- `__main__.py` — reduced to a 3-line entry point; CLI logic lives in
  `cli/main.py`
- README — updated to document all new commands, `--output` flag, supported
  file formats, Python API, and badges

### Deprecated

- `proteinspy/analysis.py` — the original single-file implementation is kept
  for historical reference but is no longer imported by the package. A comment
  at the top of the file explains this. Users on v1.0.x are unaffected; the
  `analysis/` sub-package exports all four original functions unchanged.

---

## [1.0.2] - 2026-06-06

### Fixed
- Resolved packaging issue where `click` was used but not declared as a
  dependency (fully fixed in v1.1.0 with pinned version)

---

## [1.0.1] - 2026-06-06

### Fixed
- Minor bug fixes in missing residue detection for structures with multiple
  models

---

## [1.0.0] - 2026-06-06

### Added
- Initial release
- `analyze` command — runs resolution, chains, ligands, missing residues
- `resolution` command
- `chains` command
- `ligands` command
- `missing` command
- `.cif` / `.mmcif` format support via gemmi
- Rich terminal output
- PyPI distribution via Poetry
- MkDocs documentation via GitHub Pages
