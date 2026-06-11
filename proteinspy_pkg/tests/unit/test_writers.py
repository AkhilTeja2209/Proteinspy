"""Unit tests for proteinspy.io.writers"""
from __future__ import annotations

import json
import os
import pytest

from proteinspy.io.writers import to_csv, to_json, write_output
from proteinspy.exceptions import ExportError

SIMPLE = {"resolution": 2.1, "unit": "Å", "method": "X-RAY DIFFRACTION"}
WITH_LIST = {
    "chain_count": 2,
    "chains": [
        {"id": "A", "type": "PolymerType.PeptideL", "residue_count": 100},
        {"id": "B", "type": "PolymerType.PeptideL", "residue_count": 80},
    ],
}


class TestToJson:
    def test_returns_string(self):
        assert isinstance(to_json(SIMPLE), str)

    def test_valid_json(self):
        assert json.loads(to_json(SIMPLE))["resolution"] == 2.1

    def test_indented_by_default(self):
        assert "\n" in to_json(SIMPLE, indent=2)

    def test_unicode_preserved(self):
        assert "Å" in to_json({"unit": "Å"})

    def test_list_dict(self):
        assert len(json.loads(to_json(WITH_LIST))["chains"]) == 2


class TestToCsv:
    def test_returns_string(self):
        assert isinstance(to_csv(SIMPLE), str)

    def test_header_present(self):
        first = to_csv(SIMPLE).splitlines()[0]
        assert "resolution" in first or "method" in first

    def test_data_row_present(self):
        lines = [l for l in to_csv(SIMPLE).splitlines() if l.strip()]
        assert len(lines) >= 2

    def test_list_dict_expands_rows(self):
        lines = [l for l in to_csv(WITH_LIST).splitlines() if l.strip()]
        assert len(lines) == 3  # header + 2 chain rows

    def test_tsv_uses_tab(self):
        assert "\t" in to_csv(SIMPLE, delimiter="\t")


class TestWriteOutput:
    def test_json_format(self):
        assert json.loads(write_output(SIMPLE, "json"))["method"] == "X-RAY DIFFRACTION"

    def test_csv_format(self):
        result = write_output(SIMPLE, "csv")
        assert isinstance(result, str) and ("resolution" in result or "method" in result)

    def test_tsv_format(self):
        assert "\t" in write_output(SIMPLE, "tsv")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            write_output(SIMPLE, "xml")

    def test_writes_to_file(self, tmp_path):
        out = str(tmp_path / "output.json")
        write_output(SIMPLE, "json", output_path=out)
        assert os.path.exists(out)
        assert json.load(open(out))["resolution"] == 2.1

    def test_file_content_matches_return(self, tmp_path):
        out = str(tmp_path / "output.json")
        returned = write_output(SIMPLE, "json", output_path=out)
        assert returned == open(out).read()
