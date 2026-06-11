# Changelog

See [CHANGELOG.md](https://github.com/AkhilTeja2209/Proteinspy/blob/main/CHANGELOG.md)
on GitHub for the full version history.

---

## v1.1.1 — 2025-06-11

Metadata and documentation update. No functional changes.

- Updated PyPI package description to reflect v1.1.0 features
- Comprehensive documentation rewrite covering all new commands
- Python minimum version updated to 3.10 in package metadata

---

## v1.1.0 — 2025-06-11

Major feature release.

- New commands: `bfactor`, `disulfide`, `interface`, `validate`, `export`
- `--output table|json|csv|tsv` flag on every command
- `.pdb` / `.ent` / `.gz` format support
- Full package restructure with `core/`, `analysis/`, `cli/`, `io/`, `utils/`
- 111 tests across unit and integration layers
- GitHub Actions CI on Python 3.10–3.12 (Ubuntu + macOS)
- Custom exception hierarchy, `@lru_cache` structure parsing, full type hints

---

## v1.0.2 — 2025-05-01

- Minor packaging fixes

---

## v1.0.0 — 2025-04-01

- Initial release: `analyze`, `resolution`, `chains`, `ligands`, `missing`
- `.cif` format support via gemmi
- Rich terminal output, PyPI distribution
