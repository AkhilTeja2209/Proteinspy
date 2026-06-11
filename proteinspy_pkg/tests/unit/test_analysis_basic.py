"""Unit tests for proteinspy.analysis.basic"""

from __future__ import annotations

import pytest

from proteinspy.analysis.basic import (
    get_chains,
    get_ligands,
    get_missing_residues,
    get_resolution,
)
from proteinspy.exceptions import FileNotFoundError, InvalidFileFormatError


class TestGetResolution:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_resolution(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_resolution(sample_cif)
        assert "resolution" in result
        assert "unit" in result
        assert "method" in result

    def test_resolution_is_float_or_none(self, sample_cif):
        result = get_resolution(sample_cif)
        assert result["resolution"] is None or isinstance(result["resolution"], float)

    def test_resolution_positive_when_present(self, sample_cif):
        result = get_resolution(sample_cif)
        if result["resolution"] is not None:
            assert result["resolution"] > 0

    def test_unit_set_when_resolution_present(self, sample_cif):
        result = get_resolution(sample_cif)
        if result["resolution"] is not None:
            assert result["unit"] == "Å"
        else:
            assert result["unit"] is None

    def test_method_is_string(self, sample_cif):
        result = get_resolution(sample_cif)
        assert isinstance(result["method"], str) and len(result["method"]) > 0

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_resolution(missing_file)


class TestGetChains:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_chains(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_chains(sample_cif)
        assert "chain_count" in result and "chains" in result

    def test_chain_count_matches_list(self, sample_cif):
        result = get_chains(sample_cif)
        assert result["chain_count"] == len(result["chains"])

    def test_chain_count_positive(self, sample_cif):
        assert get_chains(sample_cif)["chain_count"] > 0

    def test_chain_entry_structure(self, sample_cif):
        for ch in get_chains(sample_cif)["chains"]:
            assert "id" in ch and "type" in ch and "residue_count" in ch
            assert isinstance(ch["residue_count"], int) and ch["residue_count"] > 0

    def test_chain_ids_unique(self, sample_cif):
        ids = [ch["id"] for ch in get_chains(sample_cif)["chains"]]
        assert len(ids) == len(set(ids))

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_chains(missing_file)


class TestGetLigands:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_ligands(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_ligands(sample_cif)
        assert (
            "ligand_count" in result and "has_ligand" in result and "ligands" in result
        )

    def test_has_ligand_consistent(self, sample_cif):
        result = get_ligands(sample_cif)
        assert result["has_ligand"] == (result["ligand_count"] > 0)
        assert result["ligand_count"] == len(result["ligands"])

    def test_ligand_entry_structure(self, sample_cif):
        for lg in get_ligands(sample_cif)["ligands"]:
            assert "id" in lg and "chain" in lg and "seq_num" in lg

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_ligands(missing_file)


class TestGetMissingResidues:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_missing_residues(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_missing_residues(sample_cif)
        assert "missing_count" in result and "missing_residues" in result

    def test_count_matches_list(self, sample_cif):
        result = get_missing_residues(sample_cif)
        assert result["missing_count"] == len(result["missing_residues"])

    def test_missing_count_non_negative(self, sample_cif):
        assert get_missing_residues(sample_cif)["missing_count"] >= 0

    def test_residue_entry_structure(self, sample_cif):
        for mr in get_missing_residues(sample_cif)["missing_residues"]:
            assert "chain" in mr and "residue" in mr and "seq_num" in mr

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_missing_residues(missing_file)
