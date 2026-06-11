"""Unit tests for proteinspy.utils.helpers (parser layer)"""
from __future__ import annotations

import pytest

from proteinspy.utils.helpers import detect_format, read_structure
from proteinspy.exceptions import InvalidFileFormatError


class TestDetectFormat:
    @pytest.mark.parametrize("path,expected", [
        ("protein.cif", "cif"), ("protein.mmcif", "cif"), ("protein.pdbx", "cif"),
        ("protein.cif.gz", "cif"), ("protein.pdb", "pdb"),
        ("protein.ent", "pdb"), ("protein.pdb.gz", "pdb"),
    ])
    def test_known_extensions(self, path, expected):
        assert detect_format(path) == expected

    def test_unknown_extension_raises(self):
        with pytest.raises(InvalidFileFormatError):
            detect_format("protein.xyz")

    def test_no_extension_raises(self):
        with pytest.raises(InvalidFileFormatError):
            detect_format("protein")


class TestReadStructure:
    def test_reads_cif(self, sample_cif):
        import gemmi
        assert isinstance(read_structure(sample_cif), gemmi.Structure)

    def test_structure_has_models(self, sample_cif):
        assert len(read_structure(sample_cif)) >= 1

    def test_structure_has_chains(self, sample_cif):
        assert len(list(read_structure(sample_cif)[0])) > 0

    def test_cache_returns_same_object(self, sample_cif):
        assert read_structure(sample_cif) is read_structure(sample_cif)

    def test_missing_file_raises(self, missing_file):
        from proteinspy.exceptions import FileNotFoundError as PSFNFError
        with pytest.raises(PSFNFError):
            read_structure(missing_file)
