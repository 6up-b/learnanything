from __future__ import annotations

import json as jsonlib
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Annotated, Any, Mapping

import typer
from pydantic import BaseModel

from learnloop.attempt_types import default_attempt_type
from learnloop.ai.client import make_ai_provider_client
from learnloop.ai.routing import fallback_provider_for, provider_for_task
from learnloop.ai.runtime import check_ai_runtime
from learnloop.codex.client import make_codex_client
from learnloop.codex.schemas import AuthoringProposal
from learnloop.codex.runtime import check_codex_runtime
from learnloop.config import ConfigLoadError
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    AttemptValidationError,
    SelfGradeInput,
    complete_attempt_with_ai_fallback,
    complete_attempt_with_codex_fallback,
)
from learnloop.services.debug_time import DebugAdvanceError, advance_vault_days
from learnloop.services.doctor import run_doctor
from learnloop.services.followups import evaluate_attempt_intervention_followup
from learnloop.services.observations import (
    ObservationTemplateError,
    parse_template_yaml,
    record_observation,
    register_observation_template,
)
from learnloop.services.patches import PatchApplicationError
from learnloop.services.probes import rank_error_type_candidates
from learnloop.services.practice_generation import (
    DiagnosticPracticePlan,
    PracticeExpansionError,
    build_diagnostic_practice_plan,
    build_practice_expansion_plan,
    generate_diagnostic_practice_proposal,
    generate_post_probe_practice_proposal,
)
from learnloop.services.recall_calibration import (
    assert_recall_calibration_bands,
    format_recall_calibration_table,
    run_recall_calibration_harness,
)
from learnloop.services.replay import rebuild_derived_state
from learnloop.services.proposals import (
    accept_items,
    authoring_context_stats,
    build_authoring_context,
    edit_proposal_item,
    generate_authoring_proposal,
    list_proposals,
    persist_authoring_proposal,
    reject_items,
)
from learnloop.services.scheduler import SchedulerSession, build_due_queue, explain_practice_item
from learnloop.services.source_ingestion import SourceIngestionError, ingest_canonical_source
from learnloop.services.startup import run_startup_maintenance
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import add_note as add_note_to_vault
from learnloop.vault.loader import add_subject as add_subject_to_vault
from learnloop.vault.loader import init_vault, load_vault
from learnloop.vault.paths import VaultPaths, find_vault_root
from learnloop.vault.yaml_io import read_yaml, yaml_to_string

app = typer.Typer(no_args_is_help=True, help="LearnLoop local adaptive learning vault.")


def _root(vault: Path | None) -> Path:
    return vault.resolve() if vault else find_vault_root(Path.cwd())


def _repository(vault_root: Path) -> Repository:
    loaded = load_vault(vault_root)
    return Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)


def _load_vault_or_exit(vault_root: Path, *, json_output: bool = False):
    try:
        return load_vault(vault_root)
    except ConfigLoadError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_config", "path": str(exc.path), "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)


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


def _load_mapping_file(file: Path, *, label: str = "file") -> dict[str, Any]:
    loaded = read_yaml(file) if file.suffix.lower() in {".yaml", ".yml"} else jsonlib.loads(file.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{label} must be a mapping/object")
    return dict(loaded)


def _parse_observation_response(
    response_json: str | None,
    response_file: Path | None,
) -> dict[str, Any]:
    if response_json and response_file:
        raise ValueError("Use either --response-json or --response-file, not both.")
    if response_file is not None:
        return _load_mapping_file(response_file, label="Observation response")
    if response_json:
        try:
            loaded = jsonlib.loads(response_json)
        except jsonlib.JSONDecodeError as exc:
            raise ValueError(f"Invalid --response-json: {exc}") from exc
        if not isinstance(loaded, Mapping):
            raise ValueError("Observation response must be a JSON object.")
        return dict(loaded)
    return {}


def _observation_template_yaml(file: Path) -> str:
    if file.suffix.lower() in {".yaml", ".yml"}:
        return file.read_text(encoding="utf-8")
    return yaml_to_string(_load_mapping_file(file, label="Observation template"))


def _observation_template_payload(template: Mapping[str, Any]) -> dict[str, Any]:
    template_body = parse_template_yaml(str(template["template_yaml"]))
    return {
        "id": template["id"],
        "domain": template["domain"],
        "version": template["version"],
        "title": template["title"],
        "emits_attempt": bool(template["emits_attempt"]),
        "active": bool(template["active"]),
        "created_at": template["created_at"],
        "updated_at": template["updated_at"],
        "template": template_body,
    }


def _observation_result_payload(result) -> dict[str, Any]:
    return {
        "observation_event_id": result.observation_event_id,
        "binding_mode": result.binding_mode,
        "emitted_attempt_id": result.emitted_attempt_id,
        "attempt": result.attempt_result.as_dict() if result.attempt_result is not None else None,
    }


def _json_queue(queue: list) -> dict[str, object]:
    return {
        "version": 1,
        "items": [
            {
                "practice_item_id": item.practice_item_id,
                "learning_object_id": item.learning_object_id,
                "priority": item.priority,
                "components": item.components,
                "readiness_factor": item.readiness_factor,
                "selected_mode": item.selected_mode,
                "reasons": item.plain_english,
            }
            for item in queue
        ],
    }


def _echo_practice_generation_plan(plan) -> None:
    if not plan.targets:
        typer.echo("No completed probe Learning Objects need more Practice Items.")
        return
    typer.echo(f"Targets: {len(plan.targets)} Learning Object(s), {plan.requested_new_items} requested Practice Item(s).")
    for target in plan.targets:
        typer.echo(
            f"- {target.learning_object_id}: existing={target.existing_practice_items} "
            f"new={target.requested_new_items} probe={target.probe_attempts_completed}/{target.probe_attempts_target}"
        )


def _echo_diagnostic_generation_plan(plan: DiagnosticPracticePlan) -> None:
    if not plan.targets:
        typer.echo("No pending intervention needs require diagnostic Practice Items.")
        return
    typer.echo(f"Targets: {len(plan.targets)} intervention need(s), {plan.requested_new_items} requested diagnostic item(s).")
    for target in plan.targets:
        typer.echo(
            f"- {target.need_id}: {target.learning_object_id} facets={','.join(target.target_facets)} "
            f"band={target.recommended_difficulty_band[0]:.2f}-{target.recommended_difficulty_band[1]:.2f}"
        )


def _provider_for_task(config, task: str, explicit: str | None = None) -> str:
    return provider_for_task(config, task, explicit_provider=explicit).provider_name


def _use_ai_provider(config, task: str, explicit: str | None = None) -> bool:
    return not provider_for_task(config, task, explicit_provider=explicit).uses_legacy_codex


def _fallback_provider_for_task(config, task: str, explicit: str | None = None) -> str | None:
    selection = provider_for_task(config, task, explicit_provider=explicit)
    return fallback_provider_for(config, selection)


def _runtime_for_provider(vault_root: Path, config, provider_name: str):
    if provider_name == "codex":
        return check_codex_runtime(vault_root, config.codex)
    return check_ai_runtime(vault_root, config, provider_name=provider_name)


def _client_for_provider(vault_root: Path, config, provider_name: str):
    if provider_name == "codex":
        return make_codex_client(config.codex, vault_root)
    return make_ai_provider_client(config, vault_root, provider_name=provider_name)


def _ready_provider_for_task(vault_root: Path, config, task: str, explicit: str | None = None):
    provider_name = _provider_for_task(config, task, explicit)
    runtime = _runtime_for_provider(vault_root, config, provider_name)
    if runtime.ready:
        return provider_name, runtime, _client_for_provider(vault_root, config, provider_name)
    fallback = _fallback_provider_for_task(config, task, explicit)
    if fallback:
        fallback_runtime = _runtime_for_provider(vault_root, config, fallback)
        if fallback_runtime.ready:
            return fallback, fallback_runtime, _client_for_provider(vault_root, config, fallback)
    return provider_name, runtime, None


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
def ingest(
    source: Annotated[str, typer.Argument(help="URL or local source file to ingest.")],
    kind: Annotated[
        str,
        typer.Option("--kind", help="Source kind: auto, website_page, youtube_video, arxiv_html, or textbook_chapter."),
    ] = "auto",
    subject: Annotated[str | None, typer.Option("--subject", help="Target subject id.")] = None,
    learning_objects: Annotated[
        list[str] | None,
        typer.Option("--learning-object", help="Existing Learning Object anchor. Can be repeated."),
    ] = None,
    goal: Annotated[str | None, typer.Option("--goal", help="Active goal id to link ingested concepts to.")] = None,
    allow_auto_captions: Annotated[
        bool | None,
        typer.Option("--allow-auto-captions", help="Allow generated YouTube captions when human captions are unavailable."),
    ] = None,
    instructions: Annotated[str | None, typer.Option("--instructions", help="Extra canonical-ingestor instructions.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for ingestion.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    provider_name, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "canonical_ingest", ai_provider)
    if not runtime.ready:
        runtime_label = "Codex runtime" if provider_name == "codex" else "AI provider"
        message = runtime.message or f"{runtime_label} is {runtime.status}."
        if json_output:
            typer.echo(_dump({"version": 1, "error": runtime.status, "message": message}))
        else:
            typer.echo(message, err=True)
        raise typer.Exit(code=1)
    try:
        retry_provider = _provider_for_task(loaded.config, "canonical_ingest_retry")
        retry_client = None
        retry_runtime = None
        if retry_provider and retry_provider != provider_name:
            retry_runtime = _runtime_for_provider(vault_root, loaded.config, retry_provider)
            retry_client = _client_for_provider(vault_root, loaded.config, retry_provider) if retry_runtime.ready else None
        result = ingest_canonical_source(
            vault_root,
            source,
            client,
            kind=kind,  # type: ignore[arg-type]
            subject_id=subject,
            learning_object_ids=learning_objects,
            goal_id=goal,
            allow_auto_captions=allow_auto_captions,
            instructions=instructions,
            model=getattr(client, "model", None),
            codex_revision=getattr(runtime, "actual_revision", None),
            retry_client=retry_client,
            retry_model=getattr(retry_client, "model", None) if retry_client is not None else None,
            retry_provider_revision=getattr(retry_runtime, "actual_revision", None) if retry_runtime is not None else None,
        )
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "ingest_failed", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "ingest": result.as_dict()}))
        return
    reused = "Reused" if result.reused_existing else "Persisted"
    typer.echo(
        f"{reused} proposal {result.patch_id} from {result.source_note_id}: "
        f"auto_applied={result.auto_applied_count} "
        f"review_required={result.review_required_count} invalid={result.invalid_count}"
    )


@app.command()
def doctor(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    fix_state: Annotated[bool, typer.Option("--fix-state", help="Safely sync derived SQLite state.")] = False,
    ai: Annotated[bool, typer.Option("--ai", help="Include active AI provider health.")] = False,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to check.")] = None,
) -> None:
    report = run_doctor(_root(vault), fix_state=fix_state, ai=ai, ai_provider=ai_provider)
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
        "readiness_factor": item.readiness_factor,
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
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    payload: object | None = None
    entity_type: str | None = None
    if identifier in loaded.learning_objects:
        entity_type = "learning_object"
        payload = loaded.learning_objects[identifier].model_dump(mode="json")
        payload["content_events"] = repository.content_events_for_entity("learning_object", identifier)
        payload["active_source_events"] = repository.active_source_events_for_entity("learning_object", identifier)
    elif identifier in loaded.practice_items:
        entity_type = "practice_item"
        payload = loaded.practice_items[identifier].model_dump(mode="json")
        payload["content_events"] = repository.content_events_for_entity("practice_item", identifier)
        payload["active_source_events"] = repository.active_source_events_for_entity("practice_item", identifier)
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
        for item in batch.get("items", []):
            typer.echo(
                f"  - {item['id']} {item['item_type']} {item['operation']} "
                f"decision={item['decision']} validation={item['validation_status']}"
            )


@app.command()
def accept(
    patch_id: Annotated[str, typer.Argument(help="Proposal batch id.")],
    items: Annotated[str | None, typer.Option("--items", help="Comma-separated proposal item SQL ids.")] = None,
    all_items: Annotated[bool, typer.Option("--all", help="Accept every pending proposal item in the batch.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    if all_items and items:
        typer.echo("--all cannot be combined with --items.", err=True)
        raise typer.Exit(code=1)
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
    subjects: Annotated[str | None, typer.Option("--subjects", help="Comma-separated subject ids for AI context.")] = None,
    notes: Annotated[str | None, typer.Option("--notes", help="Comma-separated note ids for AI context.")] = None,
    instructions: Annotated[str | None, typer.Option("--instructions", help="Extra authoring instructions.")] = None,
    context_stats: Annotated[bool, typer.Option("--context-stats", help="Print authoring context size without running an AI provider.")] = False,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for authoring.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    if context_stats:
        if file is not None:
            message = "--context-stats cannot be combined with --file."
            if json_output:
                typer.echo(_dump({"version": 1, "error": "invalid_request", "message": message}))
            else:
                typer.echo(message, err=True)
            raise typer.Exit(code=1)
        loaded = load_vault(vault_root)
        context = build_authoring_context(
            loaded,
            subjects=_split_items(subjects),
            note_ids=_split_items(notes),
            instructions=instructions,
        )
        stats = authoring_context_stats(context)
        if json_output:
            typer.echo(_dump({"version": 1, "authoring_context": stats}))
            return
        counts = stats["counts"]
        chars = stats["chars"]
        sections = chars["sections"]
        typer.echo(
            "Authoring context: "
            f"{counts['subjects']} subject(s), {counts['notes']} note(s), "
            f"{counts['concepts']} concept(s), {counts['learning_objects']} LO(s), "
            f"{counts['practice_items']} PI(s), {counts['goals']} goal(s)."
        )
        typer.echo(
            f"Prompt+schema: {chars['prompt_plus_schema']} chars "
            f"(~{stats['approx_tokens']['prompt_plus_schema']} tokens by chars/4)."
        )
        typer.echo(
            "Sections: "
            f"notes={sections['notes']} chars, concepts={sections['concepts']}, "
            f"learning_objects={sections['learning_objects']}, practice_items={sections['practice_items']}."
        )
        return
    if file is None:
        loaded = load_vault(vault_root)
        provider_name, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "authoring", ai_provider)
        if not runtime.ready:
            runtime_label = "Codex runtime" if provider_name == "codex" else "AI provider"
            message = runtime.message or f"{runtime_label} is {runtime.status}."
            if json_output:
                typer.echo(_dump({"version": 1, "error": runtime.status, "message": message}))
            else:
                typer.echo(message, err=True)
            raise typer.Exit(code=1)
        try:
            patch_id = generate_authoring_proposal(
                vault_root,
                client,
                subjects=_split_items(subjects),
                note_ids=_split_items(notes),
                instructions=instructions,
                model=getattr(client, "model", None),
                codex_revision=getattr(runtime, "actual_revision", None),
            )
        except Exception as exc:
            if json_output:
                typer.echo(_dump({"version": 1, "error": "codex_failed" if provider_name == "codex" else "ai_failed", "message": str(exc)}))
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


@app.command("generate-practice")
def generate_practice(
    subjects: Annotated[str | None, typer.Option("--subjects", help="Comma-separated subject ids to scan.")] = None,
    target_items_per_lo: Annotated[int, typer.Option("--target-items-per-lo", min=1, help="Desired active Practice Item count per completed-probe LO.")] = 5,
    max_new_per_lo: Annotated[int, typer.Option("--max-new-per-lo", min=1, help="Maximum new Practice Items to ask for per LO.")] = 3,
    max_los: Annotated[int | None, typer.Option("--max-los", min=1, help="Maximum completed-probe LOs to target.")] = None,
    instructions: Annotated[str | None, typer.Option("--instructions", help="Extra generation instructions.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for practice generation.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show targets without calling Codex.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    subject_ids = _split_items(subjects)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    try:
        plan = build_practice_expansion_plan(
            loaded,
            repository,
            subjects=subject_ids,
            target_items_per_lo=target_items_per_lo,
            max_new_per_lo=max_new_per_lo,
            max_los=max_los,
        )
    except PracticeExpansionError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_generation_request", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if dry_run:
        if json_output:
            typer.echo(_dump({"version": 1, "plan": plan.as_dict()}))
        else:
            _echo_practice_generation_plan(plan)
        return
    if not plan.targets:
        message = "No completed probe Learning Objects need more Practice Items."
        if json_output:
            typer.echo(_dump({"version": 1, "error": "no_targets", "message": message, "plan": plan.as_dict()}))
        else:
            typer.echo(message)
        raise typer.Exit(code=1)
    provider_name, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "authoring", ai_provider)
    if not runtime.ready:
        runtime_label = "Codex runtime" if provider_name == "codex" else "AI provider"
        message = runtime.message or f"{runtime_label} is {runtime.status}."
        if json_output:
            typer.echo(_dump({"version": 1, "error": runtime.status, "message": message, "plan": plan.as_dict()}))
        else:
            typer.echo(message, err=True)
        raise typer.Exit(code=1)
    try:
        result = generate_post_probe_practice_proposal(
            vault_root,
            client,
            subjects=subject_ids,
            target_items_per_lo=target_items_per_lo,
            max_new_per_lo=max_new_per_lo,
            max_los=max_los,
            extra_instructions=instructions,
            codex_revision=getattr(runtime, "actual_revision", None),
        )
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "codex_failed" if provider_name == "codex" else "ai_failed", "message": str(exc), "plan": plan.as_dict()}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "proposal_id": result.patch_id, "plan": result.plan.as_dict()}))
    else:
        typer.echo(f"Persisted practice-generation proposal {result.patch_id}.")
        _echo_practice_generation_plan(result.plan)


@app.command("generate-diagnostics")
def generate_diagnostics(
    learning_object_id: Annotated[str | None, typer.Option("--learning-object-id", help="Limit to one Learning Object id.")] = None,
    max_needs: Annotated[int, typer.Option("--max-needs", min=1, help="Maximum pending intervention needs to target.")] = 3,
    instructions: Annotated[str | None, typer.Option("--instructions", help="Extra diagnostic-generation instructions.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for diagnostic generation.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show targets without calling Codex.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    try:
        plan = build_diagnostic_practice_plan(
            loaded,
            repository,
            learning_object_id=learning_object_id,
            max_needs=max_needs,
        )
    except PracticeExpansionError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_generation_request", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if dry_run:
        if json_output:
            typer.echo(_dump({"version": 1, "plan": plan.as_dict()}))
        else:
            _echo_diagnostic_generation_plan(plan)
        return
    if not plan.targets:
        message = "No pending intervention needs require diagnostic Practice Items."
        if json_output:
            typer.echo(_dump({"version": 1, "error": "no_targets", "message": message, "plan": plan.as_dict()}))
        else:
            typer.echo(message)
        raise typer.Exit(code=1)
    provider_name, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "authoring", ai_provider)
    if not runtime.ready:
        runtime_label = "Codex runtime" if provider_name == "codex" else "AI provider"
        message = runtime.message or f"{runtime_label} is {runtime.status}."
        if json_output:
            typer.echo(_dump({"version": 1, "error": runtime.status, "message": message, "plan": plan.as_dict()}))
        else:
            typer.echo(message, err=True)
        raise typer.Exit(code=1)
    try:
        result = generate_diagnostic_practice_proposal(
            vault_root,
            client,
            learning_object_id=learning_object_id,
            max_needs=max_needs,
            extra_instructions=instructions,
            codex_revision=getattr(runtime, "actual_revision", None),
        )
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "codex_failed" if provider_name == "codex" else "ai_failed", "message": str(exc), "plan": plan.as_dict()}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "proposal_id": result.patch_id, "plan": result.plan.as_dict(), "fulfilled_need_ids": result.fulfilled_need_ids}))
    else:
        typer.echo(f"Persisted diagnostic-generation proposal {result.patch_id}.")
        _echo_diagnostic_generation_plan(result.plan)


@app.command("debug-advance")
def debug_advance(
    days: Annotated[int, typer.Argument(help="Number of days to advance the vault's derived learning state.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Debug-only: simulate time passing by aging SQLite learning-state timestamps."""

    try:
        result = advance_vault_days(_root(vault), days)
    except DebugAdvanceError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_debug_advance", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "debug_advance": result.as_dict()}))
    else:
        typer.echo(
            f"Advanced vault by {result.days} day(s): shifted "
            f"{result.shifted_cells} timestamp value(s) in derived SQLite state."
        )


@app.command("rebuild-derived-state")
def rebuild_derived_state_command(
    learning_objects: Annotated[
        list[str] | None,
        typer.Option("--learning-object", help="Learning Object id to rebuild. Can be repeated."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Replay persisted attempt logs to rebuild derived learning state."""

    loaded = load_vault(_root(vault))
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    result = rebuild_derived_state(loaded, repository, learning_object_ids=learning_objects)
    if json_output:
        typer.echo(_dump({"version": 1, "rebuild": result.as_dict()}))
    else:
        typer.echo(
            f"Rebuilt {result.rebuilt_learning_objects} Learning Object(s), "
            f"replayed {result.replayed_attempts} attempt(s), "
            f"algorithm_version={result.algorithm_version}."
        )


@app.command("recall-calibration")
def recall_calibration(
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    assert_bands: Annotated[bool, typer.Option("--assert", help="Exit non-zero when a severity band fails.")] = False,
) -> None:
    """Developer harness for recall-coverage intervention calibration scenarios."""

    rows = run_recall_calibration_harness()
    if assert_bands:
        try:
            assert_recall_calibration_bands(rows)
        except AssertionError as exc:
            if json_output:
                typer.echo(_dump({"version": 1, "error": "calibration_failed", "message": str(exc), "rows": [row.as_dict() for row in rows]}))
            else:
                typer.echo(format_recall_calibration_table(rows))
                typer.echo(str(exc), err=True)
            raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "rows": [row.as_dict() for row in rows]}))
    else:
        typer.echo(format_recall_calibration_table(rows))


@app.command("observation-templates")
def observation_templates(
    include_all: Annotated[bool, typer.Option("--all", help="Include inactive templates.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    repository = _repository(_root(vault))
    templates = [
        _observation_template_payload(template)
        for template in repository.observation_templates(active_only=not include_all)
    ]
    if json_output:
        typer.echo(_dump({"version": 1, "observation_templates": templates}))
        return
    if not templates:
        typer.echo("No observation templates.")
        return
    for template in templates:
        active = "active" if template["active"] else "inactive"
        emits = "emits attempt" if template["emits_attempt"] else "observation only"
        typer.echo(
            f"{template['id']} {template['domain']} v{template['version']} "
            f"{active} - {template['title']} ({emits})"
        )


@app.command("register-observation-template")
def register_observation_template_command(
    file: Annotated[Path, typer.Option("--file", help="Observation template YAML or JSON.")],
    domain: Annotated[str, typer.Option("--domain", help="Template domain.")],
    version: Annotated[str, typer.Option("--version", help="Template version.")],
    title: Annotated[str, typer.Option("--title", help="Template title.")],
    active: Annotated[bool, typer.Option("--active/--inactive", help="Whether the template is active.")] = True,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    repository = _repository(vault_root)
    try:
        template_yaml = _observation_template_yaml(file)
        template_id = register_observation_template(
            repository,
            domain=domain,
            version=version,
            title=title,
            template_yaml=template_yaml,
            active=active,
        )
        template = repository.fetch_observation_template(template_id)
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_observation_template", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if template is None:
        raise typer.Exit(code=1)
    payload = _observation_template_payload(template)
    if json_output:
        typer.echo(_dump({"version": 1, "observation_template": payload}))
    else:
        typer.echo(f"Registered observation template {payload['id']}.")


@app.command("record-observation")
def record_observation_command(
    template_id: Annotated[str, typer.Argument(help="Observation template id.")],
    response_json: Annotated[str | None, typer.Option("--response-json", help="Observation response JSON object.")] = None,
    response_file: Annotated[Path | None, typer.Option("--response-file", help="Observation response YAML or JSON.")] = None,
    subject: Annotated[str | None, typer.Option("--subject", help="Related subject id.")] = None,
    learning_object_id: Annotated[
        str | None,
        typer.Option("--learning-object-id", help="Resolved Learning Object binding."),
    ] = None,
    practice_item_id: Annotated[
        str | None,
        typer.Option("--practice-item-id", help="Resolved Practice Item binding."),
    ] = None,
    session_id: Annotated[str | None, typer.Option("--session-id", help="Related session id.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    try:
        result = record_observation(
            loaded,
            repository,
            template_id=template_id,
            response=_parse_observation_response(response_json, response_file),
            related_learning_object_id=learning_object_id,
            related_practice_item_id=practice_item_id,
            session_id=session_id,
            subject=subject,
        )
    except (ObservationTemplateError, AttemptValidationError, ValueError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_observation", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    payload = _observation_result_payload(result)
    if json_output:
        typer.echo(_dump({"version": 1, "observation": payload}))
    else:
        emitted = f", emitted attempt {payload['emitted_attempt_id']}" if payload["emitted_attempt_id"] else ""
        typer.echo(
            f"Recorded observation {payload['observation_event_id']} "
            f"binding={payload['binding_mode']}{emitted}."
        )


@app.command("misconception-candidates")
def misconception_candidates(
    practice_item_id: Annotated[str, typer.Argument(help="Practice item id to attach a misconception to.")],
    query: Annotated[str | None, typer.Option("--query", help="Fuzzy-match text as the learner types.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, help="Maximum candidates to surface.")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Rank error-type candidates for the self-grade misconception picker (spec §12.5)."""

    loaded = load_vault(_root(vault))
    item = loaded.practice_items.get(practice_item_id)
    if item is None:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "not_found", "practice_item_id": practice_item_id}))
        else:
            typer.echo(f"No Practice Item found for {practice_item_id}.", err=True)
        raise typer.Exit(code=1)
    candidates = rank_error_type_candidates(loaded, item=item, query=query, limit=limit)
    if json_output:
        typer.echo(_dump({"version": 1, "candidates": candidates}))
        return
    if not candidates:
        typer.echo("No error types in the taxonomy yet.")
        return
    for candidate in candidates:
        kind = "misconception" if candidate.is_misconception else "error"
        typer.echo(
            f"{candidate.error_type} ({kind}) - {candidate.title} "
            f"[closeness={candidate.closeness:.2f} score={candidate.score:.2f}]"
        )


@app.command()
def attempt(
    practice_item_id: Annotated[str, typer.Argument(help="Practice item id.")],
    answer: Annotated[str | None, typer.Option("--answer", help="Learner answer markdown.")] = None,
    criterion_points: Annotated[str | None, typer.Option("--criterion-points", help="Comma-separated criterion=points pairs.")] = None,
    fatal_errors: Annotated[str | None, typer.Option("--fatal-errors", help="Comma-separated fatal rubric error ids.")] = None,
    confidence: Annotated[int, typer.Option("--confidence", min=1, max=5, help="Self-grade confidence 1..5.")] = 3,
    attempt_type: Annotated[str | None, typer.Option("--attempt-type", help="Attempt type. Defaults to the first recording type allowed by the item.")] = None,
    hints_used: Annotated[int, typer.Option("--hints-used", min=0, help="Number of hints used.")] = 0,
    error_type: Annotated[str | None, typer.Option("--error-type", help="Optional error taxonomy id or literal.")] = None,
    session_id: Annotated[str | None, typer.Option("--session-id", help="Related session id.")] = None,
    available_minutes: Annotated[int | None, typer.Option("--available-minutes", help="Remaining session minutes.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for grading.")] = None,
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
        resolved_attempt_type = attempt_type or default_attempt_type(item.attempt_types_allowed)
        draft = AttemptDraft(
            practice_item_id=practice_item_id,
            learner_answer_md=answer_text,
            attempt_type=resolved_attempt_type,
            hints_used=hints_used,
            session_id=session_id,
        )
        fallback_grade = SelfGradeInput(
            criterion_points=points,
            fatal_errors=_split_items(fatal_errors),
            confidence=confidence,
            error_type=error_type,
        )
        provider_name, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "grading", ai_provider)
        if provider_name != "codex":
            result = complete_attempt_with_ai_fallback(
                loaded,
                repository,
                draft,
                fallback_grade,
                runtime=runtime,
                ai_client=client if runtime.ready else None,
            )
        else:
            result = complete_attempt_with_codex_fallback(
                loaded,
                repository,
                draft,
                fallback_grade,
                runtime=runtime,
                codex_client=client if runtime.ready else None,
            )
    except (AttemptValidationError, ValueError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "validation_error", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    evaluate_attempt_intervention_followup(
        loaded,
        repository,
        result=result,
        available_minutes=available_minutes,
        session_id=session_id,
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
