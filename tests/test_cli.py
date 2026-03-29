"""Tests for HyperChain CLI."""
from click.testing import CliRunner
from hyperchain.cli import main


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output

def test_init_creates_config(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--dir", str(tmp_path / "myproject")])
    assert result.exit_code == 0
    assert (tmp_path / "myproject" / "hyperchain.json").exists()

def test_audit_verify_empty(tmp_path):
    runner = CliRunner()
    (tmp_path / "audit").mkdir()
    result = runner.invoke(main, ["audit", "verify", "--dir", str(tmp_path / "audit")])
    assert result.exit_code == 0
