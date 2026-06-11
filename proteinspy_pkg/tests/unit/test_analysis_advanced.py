"""Unit tests for proteinspy.analysis.advanced"""
from __future__ import annotations

import pytest

from proteinspy.analysis.advanced import (
    get_bfactor_stats, get_chain_interface, get_disulfide_bonds,
)


class TestGetBfactorStats:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_bfactor_stats(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_bfactor_stats(sample_cif)
        assert "overall" in result and "by_chain" in result

    def test_overall_stats_keys(self, sample_cif):
        overall = get_bfactor_stats(sample_cif)["overall"]
        for key in ("min", "max", "mean", "std", "atom_count"):
            assert key in overall

    def test_atom_count_positive(self, sample_cif):
        assert get_bfactor_stats(sample_cif)["overall"]["atom_count"] > 0

    def test_min_le_mean_le_max(self, sample_cif):
        ov = get_bfactor_stats(sample_cif)["overall"]
        if ov["min"] is not None:
            assert ov["min"] <= ov["mean"] <= ov["max"]

    def test_std_non_negative(self, sample_cif):
        ov = get_bfactor_stats(sample_cif)["overall"]
        if ov["std"] is not None:
            assert ov["std"] >= 0

    def test_by_chain_is_list(self, sample_cif):
        assert isinstance(get_bfactor_stats(sample_cif)["by_chain"], list)

    def test_by_chain_has_chain_id(self, sample_cif):
        for entry in get_bfactor_stats(sample_cif)["by_chain"]:
            assert "chain_id" in entry and isinstance(entry["chain_id"], str)

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_bfactor_stats(missing_file)


class TestGetDisulfideBonds:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_disulfide_bonds(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_disulfide_bonds(sample_cif)
        assert "bond_count" in result and "bonds" in result

    def test_count_matches_list(self, sample_cif):
        result = get_disulfide_bonds(sample_cif)
        assert result["bond_count"] == len(result["bonds"])

    def test_bond_count_non_negative(self, sample_cif):
        assert get_disulfide_bonds(sample_cif)["bond_count"] >= 0

    def test_bond_entry_structure(self, sample_cif):
        for bond in get_disulfide_bonds(sample_cif)["bonds"]:
            for key in ("chain_a","res_a","seqid_a","chain_b","res_b","seqid_b","distance_A"):
                assert key in bond

    def test_bond_distance_in_range(self, sample_cif):
        for bond in get_disulfide_bonds(sample_cif)["bonds"]:
            assert 0 < bond["distance_A"] <= 2.5

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_disulfide_bonds(missing_file)


class TestGetChainInterface:
    def test_returns_dict(self, sample_cif):
        assert isinstance(get_chain_interface(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = get_chain_interface(sample_cif)
        assert "interface_count" in result and "interfaces" in result

    def test_count_matches_list(self, sample_cif):
        result = get_chain_interface(sample_cif)
        assert result["interface_count"] == len(result["interfaces"])

    def test_interface_entry_structure(self, sample_cif):
        for iface in get_chain_interface(sample_cif)["interfaces"]:
            for key in ("chain_a","chain_b","contact_pairs","residues_a","residues_b"):
                assert key in iface

    def test_contact_pairs_positive(self, sample_cif):
        for iface in get_chain_interface(sample_cif)["interfaces"]:
            assert iface["contact_pairs"] > 0

    def test_chain_a_ne_chain_b(self, sample_cif):
        for iface in get_chain_interface(sample_cif)["interfaces"]:
            assert iface["chain_a"] != iface["chain_b"]

    def test_custom_cutoff_stricter(self, sample_cif):
        loose = get_chain_interface(sample_cif, cutoff=10.0)
        tight = get_chain_interface(sample_cif, cutoff=3.0)
        assert tight["interface_count"] <= loose["interface_count"]

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            get_chain_interface(missing_file)
