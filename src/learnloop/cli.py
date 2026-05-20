from __future__ import annotations

import json as jsonlib
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel

from learnloop.codex.client import HttpCodexClient
from learnloop.codex.schemas import AuthoringProposal
from learnloop.codex.runtime import check_codex_runtime
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, AttemptValidationError, SelfGradeInput, complete_attempt_with_codex_fallback
from learnloop.services.doctor import run_doctor
from learnloop.services.followups import evaluate_negative_surprise_followup
from learnloop.services.patches import PatchApplicationError
from learnloop.services.proposals import (
    accept_items,
    edit_proposal_item,
    generate_authoring_proposal,
    list_proposals,
    persist_authoring_proposal,
    reject_items,
)
from learnloop.services.scheduler import SchedulerSession, build_due_queue, explain_practice_item
from learnloop.services.startup import run_startup_maintenance
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import add_note as add_note_to_vault
from learnloop.vault.loader import add_subject as add_subject_to_vault
from learnloop.vault.loader import init_vault, load_vault
from learnloop.vault.paths import VaultPaths, find_vault_root
from learnloop.vault.yaml_io import read_yaml

app = typer.Typer(no_args_is_help=True, help="LearnLoop local adaptive learning vault.")


def _root(vault: Path | None) -> Path:
    return vault.resolve() if vault else find_vault_root(Path.cwd())


def _repository(vault_root: Path) -> Repository:
    loaded = load_vault(vault_root)
    return Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)


def _split_items(items: str | None) -> list[str] | None:
    if not items:
        return None
    return [item.strip() for item in items.split(",") if item.strip()]


def _dump(value: object) -> str:
    value = _plain(value)
    return jsonlib.dumps(value, indent=2, sort_keys=True, default=str)


def _plain(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return _plain(asdict(value))
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _parse_points(value: str | None) -> dict[str, float]:
    if not value:
        return {}
    points: dict[str, float] = {}
    for pair in value.split(","):
        if not pair.strip():
            continue
        if "=" not in pair:
            raise typer.BadParameter("criterion points must use criterion=points pairs")
        criterion_id, raw_points = pair.split("=", 1)
        criterion_id = criterion_id.strip()
        try:
            points[criterion_id] = float(raw_points)
        except ValueError as exc:
            raise typer.BadParameter(f"{criterion_id} points must be numeric") from exc
    return points


def _json_queue(queue: list) -> dict[str, object]:
    return {
        "version": 1,
        "items": [
            {
                "practice_item_id": item.practice_item_id,
                "learning_object_id": item.learning_object_id,
                "priority": item.priority,
                "components": item.components,
                "selected_mode": item.selected_mode,
                "reasons": item.plain_english,
            }
            for item in queue
        ],
    }


@app.command()
def init(
    path: Annotated[Path, typer.Argument(help="Vault directory to create.")] = Path("."),
) -> None:
    created = init_vault(path)
    typer.echo(f"Initialized LearnLoop vault at {created}")


@app.command("add-subject")
def add_subject(
    subject_id: Annotated[str, typer.Argument(help="Kebab-case subject id.")],
    title: Annotated[str, typer.Argument(help="Display title.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    path = add_subject_to_vault(_root(vault), subject_id, title)
    typer.echo(f"Added subject at {path}")


@app.command("add-note")
def add_note(
    subject_id: Annotated[str, typer.Argument(help="Subject id.")],
    note_id: Annotated[str, typer.Argument(help="Note id, with or without note_ prefix.")],
    title: Annotated[str, typer.Argument(help="Note title.")],
    body: Annotated[str, typer.Option("--body", help="Inline note body.")] = "",
    file: Annotated[Path | None, typer.Option("--file", help="Markdown file to use as note body.")] = None,
    source_type: Annotated[
        str,
        typer.Option(
            "--source-type",
            help="Source type: learner_note, canonical_source, or imported.",
        ),
    ] = "learner_note",
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    note_body = file.read_text(encoding="utf-8") if file else body
    try:
        path = add_note_to_vault(_root(vault), subject_id, note_id, title, note_body, source_type=source_type)
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--source-type") from exc
    typer.echo(f"Added note at {path}")


@app.command()
def doctor(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    fix_state: Annotated[bool, typer.Option("--fix-state", help="Safely sync derived SQLite state.")] = False,
) -> None:
    report = run_doctor(_root(vault), fix_state=fix_state)
    if json_output:
        typer.echo(_dump(report.as_dict()))
        if not report.clean:
            raise typer.Exit(code=1)
        return
    if report.clean:
        typer.echo("No doctor issues found.")
        return
    for issue in report.issues:
        location = f" ({issue.path})" if issue.path else ""
        subject = f" {issue.entity_id}" if issue.entity_id else ""
        typer.echo(f"{issue.severity}: {issue.code}{subject}: {issue.message}{location}")
    raise typer.Exit(code=1)


@app.command()
def review(
    limit: Annotated[int | None, typer.Option("--limit", help="Maximum queue length.")] = None,
    available_minutes: Annotated[int | None, typer.Option("--available-minutes", help="Session length.")] = None,
    energy: Annotated[str | None, typer.Option("--energy", help="Session energy label.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    loaded = load_vault(_root(vault))
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    run_startup_maintenance(loaded, repository)
    queue = build_due_queue(
        loaded,
        repository,
        limit=limit,
        session=SchedulerSession(available_minutes=available_minutes, energy=energy),
    )
    if json_output:
        typer.echo(_dump(_json_queue(queue)))
        return
    if not queue:
        typer.echo("No scheduled items.")
        return
    for index, item in enumerate(queue, start=1):
        reasons = "; ".join(item.plain_english)
        typer.echo(f"{index}. {item.practice_item_id} priority={item.priority:.3f} mode={item.selected_mode} - {reasons}")


@app.command()
def why(
    practice_item_id: Annotated[str, typer.Argument(help="Practice item id.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    loaded = load_vault(_root(vault))
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    run_startup_maintenance(loaded, repository)
    item = explain_practice_item(loaded, repository, practice_item_id)
    if item is None:
        latest = repository.latest_scheduler_explanation(practice_item_id)
        if latest is None:
            if json_output:
                typer.echo(_dump({"version": 1, "error": "not_found", "practice_item_id": practice_item_id}))
            else:
                typer.echo(f"No scheduler explanation for {practice_item_id}.")
            raise typer.Exit(code=1)
        if json_output:
            typer.echo(_dump({"version": 1, "source": "latest", "explanation": latest}))
            return
        typer.echo(_dump(latest))
        return
    payload = {
        "version": 1,
        "source": "current",
        "practice_item_id": item.practice_item_id,
        "priority": item.priority,
        "components": item.components,
        "reasons": item.plain_english,
    }
    if json_output:
        typer.echo(_dump(payload))
    else:
        typer.echo(_dump({key: value for key, value in payload.items() if key != "version"}))


@app.command()
def show(
    identifier: Annotated[str, typer.Argument(help="Entity or SQL id.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    loaded = load_vault(_root(vault))
    payload: object | None = None
    entity_type: str | None = None
    if identifier in loaded.learning_objects:
        entity_type = "learning_object"
        payload = loaded.learning_objects[identifier]
    elif identifier in loaded.practice_items:
        entity_type = "practice_item"
        payload = loaded.practice_items[identifier]
    elif identifier in loaded.concepts:
        entity_type = "concept"
        payload = loaded.concepts[identifier]
    elif identifier in loaded.error_types:
        entity_type = "error_type"
        payload = loaded.error_types[identifier]
    elif identifier in loaded.notes:
        entity_type = "note"
        payload = loaded.notes[identifier]
    elif identifier in loaded.subjects:
        entity_type = "subject"
        subject = loaded.subjects[identifier]
        payload = {"metadata": subject.metadata.model_dump(mode="json"), "path": subject.path, "body": subject.body}
    else:
        for edge in loaded.edges:
            if edge.id == identifier:
                entity_type = "concept_edge"
                payload = edge
                break
    if payload is None:
        repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
        record = repository.find_record(identifier)
        if record is not None:
            entity_type, payload = record
            if entity_type == "practice_attempt" and isinstance(payload, dict):
                payload = {
                    **payload,
                    "grading_evidence": repository.fetch_grading_evidence(identifier),
                    "surprise": repository.latest_attempt_surprise(identifier),
                }
            elif entity_type == "proposal" and isinstance(payload, dict):
                payload = {
                    **payload,
                    "items": repository.proposal_items(identifier),
                }
    if payload is None:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "not_found", "identifier": identifier}))
        else:
            typer.echo(f"No entity found for {identifier}.")
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "type": entity_type, "id": identifier, "record": payload}))
    else:
        typer.echo(_dump(payload if not isinstance(payload, tuple) else {"type": entity_type, "record": payload}))


@app.command()
def proposals(
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    batches = list_proposals(_root(vault))
    if json_output:
        typer.echo(_dump({"version": 1, "proposals": batches}))
        return
    if not batches:
        typer.echo("No proposals.")
        return
    for batch in batches:
        typer.echo(f"{batch['id']} status={batch['status_cache']} purpose={batch['purpose']} summary={batch['summary'] or ''}")


@app.command()
def accept(
    patch_id: Annotated[str, typer.Argument(help="Proposal batch id.")],
    items: Annotated[str | None, typer.Option("--items", help="Comma-separated proposal item SQL ids.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    try:
        result = accept_items(_root(vault), patch_id, _split_items(items))
    except PatchApplicationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    typer.echo(f"Accepted and applied {result.applied_count} proposal item(s).")


@app.command()
def reject(
    patch_id: Annotated[str, typer.Argument(help="Proposal batch id.")],
    items: Annotated[str | None, typer.Option("--items", help="Comma-separated proposal item SQL ids.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    count = reject_items(_root(vault), patch_id, _split_items(items))
    typer.echo(f"Rejected {count} proposal item(s).")


@app.command("edit-proposal-item")
def edit_proposal_item_command(
    patch_id: Annotated[str, typer.Argument(help="Proposal batch id.")],
    item_id: Annotated[str, typer.Argument(help="Proposal item SQL id.")],
    file: Annotated[Path, typer.Option("--file", help="YAML or JSON replacement payload.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    try:
        payload = read_yaml(file) if file.suffix.lower() in {".yaml", ".yml"} else jsonlib.loads(file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Edited payload must be a mapping/object")
        item = edit_proposal_item(_root(vault), patch_id, item_id, payload)
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_edit", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "proposal_item": item}))
    else:
        typer.echo(f"Edited proposal item {item_id} validation_status={item['validation_status']}.")


@app.command()
def propose(
    file: Annotated[Path | None, typer.Option("--file", help="AuthoringProposal JSON/YAML file to import.")] = None,
    subjects: Annotated[str | None, typer.Option("--subjects", help="Comma-separated subject ids for Codex context.")] = None,
    notes: Annotated[str | None, typer.Option("--notes", help="Comma-separated note ids for Codex context.")] = None,
    instructions: Annotated[str | None, typer.Option("--instructions", help="Extra authoring instructions.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    if file is None:
        loaded = load_vault(vault_root)
        runtime = check_codex_runtime(vault_root, loaded.config.codex)
        if not runtime.ready:
            message = runtime.message or f"Codex runtime is {runtime.status}."
            if json_output:
                typer.echo(_dump({"version": 1, "error": runtime.status, "message": message}))
            else:
                typer.echo(message, err=True)
            raise typer.Exit(code=1)
        try:
            patch_id = generate_authoring_proposal(
                vault_root,
                HttpCodexClient(loaded.config.codex),
                subjects=_split_items(subjects),
                note_ids=_split_items(notes),
                instructions=instructions,
                codex_revision=runtime.actual_revision,
            )
        except Exception as exc:
            if json_output:
                typer.echo(_dump({"version": 1, "error": "codex_failed", "message": str(exc)}))
            else:
                typer.echo(str(exc), err=True)
            raise typer.Exit(code=1)
        if json_output:
            typer.echo(_dump({"version": 1, "proposal_id": patch_id}))
        else:
            typer.echo(f"Persisted proposal {patch_id}.")
        return
    try:
        raw = read_yaml(file) if file.suffix.lower() in {".yaml", ".yml"} else jsonlib.loads(file.read_text(encoding="utf-8"))
        proposal = AuthoringProposal.model_validate(raw)
        patch_id = persist_authoring_proposal(vault_root, proposal, provider="import")
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_proposal", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "proposal_id": patch_id}))
    else:
        typer.echo(f"Persisted proposal {patch_id}.")


@app.command()
def attempt(
    practice_item_id: Annotated[str, typer.Argument(help="Practice item id.")],
    answer: Annotated[str | None, typer.Option("--answer", help="Learner answer markdown.")] = None,
    criterion_points: Annotated[str | None, typer.Option("--criterion-points", help="Comma-separated criterion=points pairs.")] = None,
    fatal_errors: Annotated[str | None, typer.Option("--fatal-errors", help="Comma-separated fatal rubric error ids.")] = None,
    confidence: Annotated[int, typer.Option("--confidence", min=1, max=5, help="Self-grade confidence 1..5.")] = 3,
    attempt_type: Annotated[str, typer.Option("--attempt-type", help="Attempt type.")] = "independent_attempt",
    hints_used: Annotated[int, typer.Option("--hints-used", min=0, help="Number of hints used.")] = 0,
    error_type: Annotated[str | None, typer.Option("--error-type", help="Optional error taxonomy id or literal.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    item = loaded.practice_items.get(practice_item_id)
    if item is None:
        typer.echo(f"No Practice Item found for {practice_item_id}.", err=True)
        raise typer.Exit(code=1)
    rubric = loaded.rubric_for_item(item)
    answer_text = answer if answer is not None else typer.prompt("Answer", default="")
    points = _parse_points(criterion_points)
    if not points and rubric is not None:
        for criterion in rubric.criteria:
            raw = typer.prompt(f"{criterion.id} points", default="0")
            try:
                points[criterion.id] = float(raw)
            except ValueError:
                typer.echo(f"{criterion.id} points must be numeric.", err=True)
                raise typer.Exit(code=1)
    try:
        runtime = check_codex_runtime(vault_root, loaded.config.codex)
        result = complete_attempt_with_codex_fallback(
            loaded,
            repository,
            AttemptDraft(
                practice_item_id=practice_item_id,
                learner_answer_md=answer_text,
                attempt_type=attempt_type,
                hints_used=hints_used,
            ),
            SelfGradeInput(
                criterion_points=points,
                fatal_errors=_split_items(fatal_errors),
                confidence=confidence,
                error_type=error_type,
            ),
            runtime=runtime,
            codex_client=HttpCodexClient(loaded.config.codex) if runtime.ready else None,
        )
    except (AttemptValidationError, ValueError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "validation_error", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    evaluate_negative_surprise_followup(
        loaded,
        repository,
        attempt_id=result.attempt_id,
        learning_object_id=result.learning_object_id,
        practice_item_id=result.practice_item_id,
        surprise_direction=result.surprise_direction,
        bayesian_surprise=result.bayesian_surprise,
        grader_confidence=result.grader_confidence,
        error_event_written=bool(result.error_event_ids),
    )
    if json_output:
        typer.echo(_dump({"version": 1, "attempt": result.as_dict()}))
        return
    typer.echo(
        f"Recorded {result.attempt_id}: score={result.rubric_score} "
        f"rating={result.fsrs_rating} due={result.due_at} mastery={result.mastery_mean:.2f}"
    )


@app.command()
def today(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    from learnloop.tui.app import run

    run(_root(vault))
