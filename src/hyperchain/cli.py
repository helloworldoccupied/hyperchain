"""HyperChain CLI — init, audit commands."""
from __future__ import annotations
import json
from pathlib import Path
import click
from hyperchain import __version__
from hyperchain.audit_chain import AuditChain

@click.group()
@click.version_option(__version__)
def main():
    """HyperChain: Enterprise Multi-AI Governance Framework."""

@main.command()
@click.option("--dir", default=".", help="Project directory")
def init(dir: str):
    """Initialize a new HyperChain project."""
    project = Path(dir)
    project.mkdir(parents=True, exist_ok=True)
    config = {
        "version": "0.1.0",
        "pipeline": "code-review",
        "max_negotiation_rounds": 5,
        "guards": ["guard_destructive_bash"],
        "audit": {"storage": "./audit", "auto_save": True},
    }
    config_path = project / "hyperchain.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    click.echo(f"Initialized HyperChain project at {project}")

@main.group()
def audit():
    """Audit chain commands."""

@audit.command()
@click.option("--dir", required=True, help="Audit chain directory")
def verify(dir: str):
    """Verify audit chain integrity."""
    chain = AuditChain(storage=dir)
    chain.load()
    if not chain.entries:
        click.echo("Audit chain is empty.")
        return
    try:
        chain.verify_integrity()
        click.echo(f"Audit chain intact ({len(chain.entries)} entries)")
    except Exception as e:
        click.echo(f"Audit chain BROKEN: {e}", err=True)
        raise SystemExit(1)

@audit.command()
@click.option("--dir", required=True, help="Audit chain directory")
@click.option("--task", required=True, help="Task ID")
@click.option("--output", required=True, help="Output file")
def export(dir: str, task: str, output: str):
    """Export audit report for a task."""
    chain = AuditChain(storage=dir)
    chain.load()
    chain.export_report(task, output, format="json")
    click.echo(f"Report exported to {output}")
