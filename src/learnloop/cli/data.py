"""Local collection inspection and reproducible dataset artifacts."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated
import json
import typer

from learnloop.cli.app import app
from learnloop.cli.runtime import _dump, _load_vault_or_exit, _root
from learnloop.substrate.data_quality import data_quality_report
from learnloop.substrate.dataset import export_dataset
from learnloop.vault.paths import VaultPaths
from learnloop.db.repositories import Repository


def _database(vault: Path | None) -> Path:
    loaded = _load_vault_or_exit(_root(vault), json_output=True)
    return VaultPaths(loaded.root, loaded.config).sqlite_path


@app.command("data-quality")
def data_quality(
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Read-only JSON coverage report, with current-version denominators."""
    typer.echo(_dump(data_quality_report(_database(vault))))


@app.command("dataset-export")
def dataset_export(
    output: Annotated[Path, typer.Argument(help="New local output directory.")],
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Back up an active database and export evidence, labels and split metadata."""
    try:
        manifest = export_dataset(_database(vault), output)
    except (OSError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(_dump({"output": str(output.resolve()), "snapshot_sha256": manifest["snapshot_sha256"], "artifacts": len(manifest["artifacts"])}))


@app.command("adjudicate-remediation")
def adjudicate_remediation(
    attempt_id: Annotated[str, typer.Argument()],
    false_remediation: Annotated[bool, typer.Option("--false-remediation/--appropriate-remediation")],
    evidence: Annotated[Path, typer.Option("--evidence", help="JSON list of retained {table, id} evidence references.")],
    verifier_version: Annotated[str, typer.Option("--verifier-version")],
    author_kind: Annotated[str, typer.Option("--author-kind", help="human or machine")] = "human",
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Append an evidence-backed label; corrections append another adjudication."""
    try:
        refs = json.loads(evidence.read_text(encoding="utf-8"))
        if not isinstance(refs, list) or any(not isinstance(ref, dict) for ref in refs):
            raise ValueError("Evidence must be a JSON list of {table, id} objects.")
        identity = Repository(_database(vault)).record_false_remediation(attempt_id=attempt_id, value=false_remediation, evidence_refs=refs, author_kind=author_kind, verifier_version=verifier_version)
    except (OSError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(_dump({"adjudication_id": identity}))
