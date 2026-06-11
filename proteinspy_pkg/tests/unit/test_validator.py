"""Unit tests for proteinspy.core.validator"""
from __future__ import annotations

import pytest
from proteinspy.core.validator import validate_structure


class TestValidateStructure:
    def test_returns_dict(self, sample_cif):
        assert isinstance(validate_structure(sample_cif), dict)

    def test_required_keys(self, sample_cif):
        result = validate_structure(sample_cif)
        for key in ("warnings","info","pass","resolution","method","model_count","missing_fraction"):
            assert key in result

    def test_warnings_is_list(self, sample_cif):
        assert isinstance(validate_structure(sample_cif)["warnings"], list)

    def test_info_is_list(self, sample_cif):
        assert isinstance(validate_structure(sample_cif)["info"], list)

    def test_pass_is_bool(self, sample_cif):
        assert isinstance(validate_structure(sample_cif)["pass"], bool)

    def test_pass_consistent_with_warnings(self, sample_cif):
        result = validate_structure(sample_cif)
        assert result["pass"] == (len(result["warnings"]) == 0)

    def test_model_count_positive(self, sample_cif):
        assert validate_structure(sample_cif)["model_count"] >= 1

    def test_missing_fraction_in_range(self, sample_cif):
        frac = validate_structure(sample_cif)["missing_fraction"]
        assert 0.0 <= frac <= 1.0

    def test_missing_file_raises(self, missing_file):
        with pytest.raises(Exception):
            validate_structure(missing_file)
