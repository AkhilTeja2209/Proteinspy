"""Integration tests for the Proteinspy Click CLI."""
from __future__ import annotations

import json
import pytest
from click.testing import CliRunner

from proteinspy.cli.main import main


@pytest.fixture
def runner():
    return CliRunner()


class TestMainGroup:
    def test_no_args_shows_help(self, runner):
        result = runner.invoke(main, [])
        assert result.exit_code == 0

    def test_version_flag(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0 and "1.1.0" in result.output


class TestAnalyzeCommand:
    def test_table_output(self, runner, sample_cif):
        result = runner.invoke(main, ["analyze", sample_cif])
        assert result.exit_code == 0

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["analyze", sample_cif, "--output", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "resolution" in parsed and "chains" in parsed

    def test_missing_file_exits_nonzero(self, runner, missing_file):
        result = runner.invoke(main, ["analyze", missing_file])
        assert result.exit_code != 0 or "Error" in result.output


class TestResolutionCommand:
    def test_table_output(self, runner, sample_cif):
        assert runner.invoke(main, ["resolution", sample_cif]).exit_code == 0

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["resolution", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "resolution" in parsed and "method" in parsed


class TestChainsCommand:
    def test_table_output(self, runner, sample_cif):
        assert runner.invoke(main, ["chains", sample_cif]).exit_code == 0

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["chains", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        assert json.loads(result.output)["chain_count"] > 0


class TestLigandsCommand:
    def test_table_output(self, runner, sample_cif):
        assert runner.invoke(main, ["ligands", sample_cif]).exit_code == 0

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["ligands", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        assert "ligand_count" in json.loads(result.output)


class TestMissingCommand:
    def test_table_output(self, runner, sample_cif):
        assert runner.invoke(main, ["missing", sample_cif]).exit_code == 0

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["missing", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        assert "missing_count" in json.loads(result.output)


class TestBfactorCommand:
    def test_table_output(self, runner, sample_cif):
        result = runner.invoke(main, ["bfactor", sample_cif])
        assert result.exit_code == 0 and "B-Factor" in result.output

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["bfactor", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "overall" in parsed and "by_chain" in parsed


class TestDisulfideCommand:
    def test_table_output(self, runner, sample_cif):
        assert runner.invoke(main, ["disulfide", sample_cif]).exit_code == 0

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["disulfide", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        assert "bond_count" in json.loads(result.output)


class TestInterfaceCommand:
    def test_table_output(self, runner, sample_cif):
        assert runner.invoke(main, ["interface", sample_cif]).exit_code == 0

    def test_custom_cutoff(self, runner, sample_cif):
        assert runner.invoke(main, ["interface", sample_cif, "--cutoff", "8.0"]).exit_code == 0


class TestValidateCommand:
    def test_table_output(self, runner, sample_cif):
        result = runner.invoke(main, ["validate", sample_cif])
        assert result.exit_code == 0 and "Validation" in result.output

    def test_json_output(self, runner, sample_cif):
        result = runner.invoke(main, ["validate", sample_cif, "-o", "json"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "pass" in parsed and "warnings" in parsed


class TestExportCommand:
    def test_export_json(self, runner, sample_cif, tmp_path):
        out = str(tmp_path / "report.json")
        result = runner.invoke(main, ["export", sample_cif, out])
        assert result.exit_code == 0
        import os
        assert os.path.exists(out)
        assert "resolution" in json.load(open(out))

    def test_export_csv(self, runner, sample_cif, tmp_path):
        out = str(tmp_path / "chains.csv")
        result = runner.invoke(main, ["export", sample_cif, out, "--analysis", "chains"])
        assert result.exit_code == 0
        import os
        assert os.path.exists(out)
