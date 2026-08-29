from __future__ import annotations
import json as jsonlib
import os
import sys
import textwrap
import threading
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Annotated, Any, Callable, Mapping, TextIO
import typer
from pydantic import BaseModel
from learnloop.attempt_types import default_attempt_type
from learnloop.clock import utc_now_iso
from learnloop.ai.routing import (
    client_for_provider as ai_client_for_provider,
    fallback_provider_for,
    provider_for_task,
    ready_client_for_task,
    runtime_for_provider as ai_runtime_for_provider,
)
from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.ai.runtime import legacy_codex_status
from learnloop.config import (
    CODEX_PROVIDER_NAMES,
    ConfigLoadError,
)
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    AttemptDraft,
    AttemptValidationError,
    SelfGradeInput,
    complete_attempt_with_ai_fallback,
    complete_attempt_with_codex_fallback,
)
from learnloop.ops.debug_time import DebugAdvanceError, advance_vault_days
from learnloop.goals.exam_seeding import (
    ExamSeedingError,
    exam_ingest_instructions,
    parse_exam_outcomes,
    seed_exam_attempts,
)
from learnloop.goals.exam_pool import reserve_exam_pool
from learnloop.goals.exam_session import (
    ExamSessionError,
    exam_availability,
    exam_report as exam_report_service,
    finish_exam,
    record_exam_answer,
    start_exam,
)
from learnloop.goals.exam_calibration import calibration_report as exam_calibration_report
from learnloop.ids import new_ulid
from learnloop.curriculum.concepts import ConceptMergeError, merge_concepts
from learnloop.ops.doctor import run_doctor
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.learner.hypothesis_claims import export_claim_events, purge_claim_events
from learnloop.attempts.observations import (
    ObservationTemplateError,
    parse_template_yaml,
    record_observation,
    register_observation_template,
)
from learnloop.content.proposals.patches import PatchApplicationError
from learnloop.diagnosis.probes import rank_error_type_candidates
from learnloop.content.authoring.practice_generation import (
    DiagnosticPracticePlan,
    PracticeExpansionError,
    build_diagnostic_practice_plan,
    build_goal_practice_plan,
    build_practice_expansion_plan,
    generate_diagnostic_practice_proposal,
    generate_goal_practice_proposal,
    generate_post_probe_practice_proposal,
)
from learnloop.learner.recall_calibration import (
    assert_recall_calibration_bands,
    format_recall_calibration_table,
    run_recall_calibration_harness,
)
from learnloop.content.sources.source_refs import source_ref_display_dto
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.shadow_rebuild import ShadowRebuildError, shadow_rebuild
from learnloop.content.proposals.proposals import (
    accept_items,
    authoring_context_stats,
    build_authoring_context,
    edit_proposal_item,
    generate_authoring_proposal,
    list_proposals,
    persist_authoring_proposal,
    reject_items,
)
from learnloop.diagnosis.diagnostic_gate import (
    BACKFILL_SKIPPED_EXISTING,
    BACKFILL_SKIPPED_UNREGISTERED,
    backfill_discrimination_rows,
)
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue, explain_practice_item
from learnloop.content.pipeline.source_ingestion import SourceIngestionError, ingest_canonical_source
from learnloop.ops.startup import run_startup_maintenance
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import add_note as add_note_to_vault
from learnloop.vault.loader import add_subject as add_subject_to_vault
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths, find_vault_root
from learnloop.vault.repository import open_vault_repository
from learnloop.vault.yaml_io import read_yaml, yaml_to_string

from learnloop.cli.render import *  # noqa: F401,F403

_INGEST_SPINNER_FRAMES = ("|", "/", "-", "\\")

_INGEST_PROGRESS_EVENT = "learnloop_ingest_progress"

def _root(vault: Path | None) -> Path:
    return vault.resolve() if vault else find_vault_root(Path.cwd())

def _repository(vault_root: Path) -> Repository:
    loaded = load_vault(vault_root)
    return open_vault_repository(
        loaded.root,
        VaultPaths(loaded.root, loaded.config).sqlite_path,
    )

def _load_vault_or_exit(vault_root: Path, *, json_output: bool = False):
    try:
        return load_vault(vault_root)
    except ConfigLoadError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_config", "path": str(exc.path), "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

def _contracts_env(vault: Path | None):
    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(loaded.root)
    return loaded, repository

def _split_items(items: str | None) -> list[str] | None:
    if not items:
        return None
    return [item.strip() for item in items.split(",") if item.strip()]

def _parse_mode_mix(mode_mix: str | None) -> dict[str, int] | None:
    """Parse ``--mode-mix`` (e.g. ``teach_back=2,short_answer=3``) into counts.

    Raises ValueError with a learner-facing message on malformed entries,
    empty modes, duplicate modes, or counts below 1.
    """

    if not mode_mix:
        return None
    parsed: dict[str, int] = {}
    for entry in mode_mix.split(","):
        entry = entry.strip()
        if not entry:
            continue
        mode, separator, raw_count = entry.partition("=")
        mode = mode.strip()
        if not separator or not mode:
            raise ValueError(f"Invalid --mode-mix entry '{entry}': expected '<practice_mode>=<count>'.")
        try:
            count = int(raw_count.strip())
        except ValueError:
            raise ValueError(f"Invalid --mode-mix count for '{mode}': '{raw_count.strip()}' is not an integer.")
        if count < 1:
            raise ValueError(f"Invalid --mode-mix count for '{mode}': counts must be >= 1.")
        if mode in parsed:
            raise ValueError(f"Duplicate --mode-mix practice mode '{mode}'.")
        parsed[mode] = count
    if not parsed:
        raise ValueError("--mode-mix is empty; expected entries like 'teach_back=2,short_answer=3'.")
    return parsed

def _resolve_focus(
    loaded,
    *,
    focus_concepts: str | None,
    focus_facets: str | None,
    from_goal: str | None,
    json_output: bool,
) -> tuple[list[str] | None, list[str] | None]:
    """Merge --focus-concepts/--focus-facets with a goal's concept anchors.

    Exits with code 1 when --from-goal names an unknown or non-active goal.
    """

    concepts = _split_items(focus_concepts) or []
    facets = _split_items(focus_facets) or []
    if from_goal:
        goal = next((goal for goal in loaded.goals if goal.id == from_goal), None)
        if goal is None or goal.status != "active":
            reason = "not found" if goal is None else f"not active (status={goal.status})"
            message = f"Goal {from_goal} is {reason}."
            if json_output:
                typer.echo(_dump({"version": 1, "error": "invalid_goal", "goal_id": from_goal, "message": message}))
            else:
                typer.echo(message, err=True)
            raise typer.Exit(code=1)
        for anchor in goal.facet_scope.concepts:
            if anchor not in concepts:
                concepts.append(anchor)
        for facet in goal.facet_scope.facets:
            if facet not in facets:
                facets.append(facet)
    return (concepts or None, facets or None)

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

def _provider_for_task(config, task: str, explicit: str | None = None) -> str:
    return provider_for_task(config, task, explicit_provider=explicit).provider_name

def _fallback_provider_for_task(config, task: str, explicit: str | None = None) -> str | None:
    selection = provider_for_task(config, task, explicit_provider=explicit)
    return fallback_provider_for(config, selection)

def _runtime_for_provider(vault_root: Path, config, provider_name: str):
    return ai_runtime_for_provider(vault_root, config, provider_name)

def _client_for_provider(
    vault_root: Path,
    config,
    provider_name: str,
    *,
    codex_timeout_seconds: int | None = None,
):
    return ai_client_for_provider(
        vault_root,
        config,
        provider_name,
        timeout_seconds=codex_timeout_seconds,
    )

def _ready_provider_for_task(
    vault_root: Path,
    config,
    task: str,
    explicit: str | None = None,
    *,
    codex_timeout_seconds: int | None = None,
):
    return tuple(
        ready_client_for_task(
            vault_root,
            config,
            task,
            explicit=explicit,
            timeout_seconds=codex_timeout_seconds,
        )
    )

def _runtime_status_for_cli(provider_name: str, status: str) -> str:
    """Keep pre-provider-refactor Codex CLI error codes stable."""

    return (
        legacy_codex_status(status)
        if provider_name in CODEX_PROVIDER_NAMES
        else status
    )

def _run_canonical_ingest_command(
    source: str,
    *,
    kind: str,
    subject: str | None,
    learning_objects: list[str] | None,
    goal: str | None,
    allow_auto_captions: bool | None,
    instructions: str | None,
    ai_provider: str | None,
    json_output: bool,
    progress_json: bool,
    vault: Path | None,
    purpose: str = "canonical_ingest",
    spinner_label: str = "Ingesting canonical source",
    pdf_engine: str | None = None,
    pdf_use_llm: bool | None = None,
):
    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    progress: Callable[[str, dict[str, Any]], None] | None = _json_ingest_progress if progress_json else None
    if progress is not None:
        progress("preparing", {})
    provider_name, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "canonical_ingest", ai_provider)
    if not runtime.ready:
        runtime_status = _runtime_status_for_cli(provider_name, runtime.status)
        runtime_label = "Codex runtime" if provider_name in CODEX_PROVIDER_NAMES else "AI provider"
        message = runtime.message or f"{runtime_label} is {runtime_status}."
        if json_output:
            typer.echo(_dump({"version": 1, "error": runtime_status, "message": message}))
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
        with _AsciiSpinner(
            f"{spinner_label} with {provider_name}",
            enabled=not json_output,
        ):
            return ingest_canonical_source(
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
                purpose=purpose,
                pdf_engine=pdf_engine,
                pdf_use_llm=pdf_use_llm,
                progress=progress,
            )
    except typer.Exit:
        raise
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "ingest_failed", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

def _ingest_runner(vault_root: Path):
    from learnloop.content.pipeline.runner import IngestRunner

    loaded = load_vault(vault_root)
    repository = _repository(loaded.root)
    runner_config = loaded.config.ingest.runner
    return IngestRunner(
        repository,
        vault_root=vault_root,
        worker_id=f"cli-{os.getpid()}",
        lease_ttl_seconds=runner_config.lease_ttl_seconds,
    )

def _batch_json(
    runner,
    batch_id: str,
    *,
    batch: dict[str, Any] | None = None,
    jobs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    batch = batch if batch is not None else runner.repo.get_ingest_batch(batch_id)
    if batch is None:
        return {}
    jobs = jobs if jobs is not None else runner.repo.ingest_jobs_for_batch(batch_id)
    return {
        "id": batch["id"],
        "workflow_type": batch["workflow_type"],
        "status": batch["status"],
        "subject_id": batch.get("subject_id"),
        "cancel_requested": bool(batch.get("cancel_requested")),
        "created_at": batch.get("created_at"),
        "finished_at": batch.get("finished_at"),
        "jobs": [
            {
                "id": job["id"],
                "ordinal": job["ordinal"],
                "job_type": job["job_type"],
                "status": job["status"],
                "phase": job.get("phase"),
                "message": job.get("message"),
                "attempt_count": job.get("attempt_count", 0),
                "current_window": job.get("current_window"),
                "total_windows": job.get("total_windows"),
                "usage": job.get("usage") or {},
                "result": job.get("result"),
                "error": job.get("error"),
            }
            for job in jobs
        ],
    }

def _show_source_set(root: Path, set_id: str, json_output: bool) -> None:
    from learnloop.vault.loader import load_vault

    vault_loaded = load_vault(root)
    source_set = next((s for s in vault_loaded.source_sets if s.id == set_id), None)
    if source_set is None:
        typer.echo(f"Source set '{set_id}' does not exist.", err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "source_set": source_set.model_dump(mode="json")}))
        return
    typer.echo(f"{source_set.id}  [{source_set.subject_id}]  {source_set.title}")
    for member in source_set.members:
        scope = ", ".join(
            f"{scope.unit_id}{'/' + scope.role_override if scope.role_override else ''}" for scope in member.scope
        ) or "(whole artifact)"
        typer.echo(f"  {member.source_id} @ {member.revision_id}  role={member.default_role}  scope={scope}")

def _find_goal_or_exit(loaded, goal_id: str):
    for goal in loaded.goals:
        if goal.id == goal_id:
            return goal
    typer.echo(f"Goal {goal_id} not found.")
    raise typer.Exit(1)

_WRAP_WIDTH = 96

_ATTEMPT_COVERED_FIELDS = {
    "id",
    "practice_item_id",
    "learning_object_id",
    "subject",
    "concept",
    "practice_mode",
    "attempt_type",
    "session_id",
    "created_at",
    "updated_at",
    "rubric_score",
    "correctness",
    "confidence",
    "grader_confidence",
    "error_type",
    "hints_used",
    "latency_seconds",
    "manual_review",
    "manual_review_reason",
    "learner_answer_md",
    "grading_evidence",
    "surprise",
}

def _echo_practice_attempt(attempt_id: str, payload: dict, repository: Repository) -> None:
    typer.echo(
        typer.style("practice attempt ", bold=True)
        + typer.style(str(payload.get("id", attempt_id)), fg=typer.colors.CYAN)
    )
    _echo_kv("practice item", payload.get("practice_item_id"))
    _echo_kv("learning object", payload.get("learning_object_id"))
    _echo_kv("subject", payload.get("subject"))
    _echo_kv("concept", payload.get("concept"))
    _echo_kv("mode", payload.get("practice_mode"))
    _echo_kv("attempt type", payload.get("attempt_type"))
    _echo_kv("session", payload.get("session_id"))
    _echo_kv("created at", payload.get("created_at"))
    if payload.get("updated_at") and payload.get("updated_at") != payload.get("created_at"):
        _echo_kv("updated at", payload.get("updated_at"))

    _echo_section("score")
    _echo_kv("rubric score", payload.get("rubric_score"))
    _echo_kv("correctness", payload.get("correctness"))
    _echo_kv("confidence", payload.get("confidence"))
    _echo_kv("grader confidence", payload.get("grader_confidence"))
    if payload.get("error_type"):
        typer.echo(f"  {_dim('error type:')} " + typer.style(str(payload["error_type"]), fg=typer.colors.RED))
    if payload.get("hints_used"):
        _echo_kv("hints used", payload.get("hints_used"))
    _echo_kv("latency seconds", payload.get("latency_seconds"))
    if payload.get("manual_review"):
        _echo_kv("manual review", payload.get("manual_review_reason") or "yes")

    answer = payload.get("learner_answer_md")
    if answer:
        _echo_section("learner answer")
        for line in _wrap_text(answer):
            typer.echo(line)

    evidence_rows = payload.get("grading_evidence") or []
    if evidence_rows:
        _echo_section("grading evidence")
        for row in evidence_rows:
            row = _plain(row)
            if not isinstance(row, dict):
                continue
            points = row.get("points_awarded")
            if isinstance(points, (int, float)):
                earned = points > 0
                mark = typer.style("✓" if earned else "✗", fg=typer.colors.GREEN if earned else typer.colors.RED)
                points_label = " " + typer.style(f"points={points:g}", fg=typer.colors.GREEN if earned else typer.colors.RED)
            else:
                mark = typer.style("·", fg=typer.colors.BRIGHT_BLACK)
                points_label = ""
            confidence = row.get("learner_confidence")
            confidence_label = f" {_dim(f'learner={confidence}')}" if confidence else ""
            criterion = typer.style(str(row.get("criterion_id", "?")), fg=typer.colors.CYAN)
            typer.echo(f"  {mark} {criterion}{points_label}{confidence_label}")
            for field in ("evidence", "notes"):
                if row.get(field):
                    for line in _wrap_text(row[field], indent="      "):
                        typer.echo(line)

    feedback = repository.fetch_attempt_feedback_metadata(attempt_id)
    if feedback:
        parts: list[str] = []
        if feedback.get("feedback_md"):
            parts.extend(_wrap_text(feedback["feedback_md"]))
        if feedback.get("fatal_errors"):
            parts.append(
                "  " + typer.style("fatal errors: " + ", ".join(str(item) for item in feedback["fatal_errors"]), fg=typer.colors.RED)
            )
        for suggestion in feedback.get("repair_suggestions") or []:
            if not isinstance(suggestion, dict):
                parts.extend(_wrap_text(str(suggestion), indent="  - "))
                continue
            facets = suggestion.get("target_evidence_families") or []
            label = suggestion.get("practice_mode") or "repair"
            facet_label = " " + _dim("(facets: ") + typer.style(", ".join(facets), fg=typer.colors.CYAN) + _dim(")") if facets else ""
            parts.append("  → " + typer.style(str(label), fg=typer.colors.YELLOW) + facet_label)
            if suggestion.get("rationale"):
                parts.extend(_wrap_text(suggestion["rationale"], indent="    "))
        if parts:
            _echo_section("feedback")
            source = feedback.get("grading_source")
            if source:
                typer.echo(f"  {_dim('graded by:')} {source}")
            for line in parts:
                typer.echo(line)

    surprise = payload.get("surprise")
    if isinstance(surprise, dict):
        _echo_section("surprise")
        _echo_kv("predictive surprise", surprise.get("predictive_surprise"))
        _echo_kv("bayesian surprise", surprise.get("bayesian_surprise"))
        _echo_kv("direction", surprise.get("surprise_direction"))
        predicted = surprise.get("predicted_score_dist")
        if isinstance(predicted, dict):
            _echo_kv("expected correctness", predicted.get("expected_correctness"))
        observed = surprise.get("observed_joint_bucket")
        if isinstance(observed, dict) and observed:
            _echo_kv(
                "observed",
                " ".join(f"{key}={value}" for key, value in sorted(observed.items())),
            )
        triggered = surprise.get("triggered_actions") or []
        if triggered:
            _echo_kv("triggered actions", ", ".join(str(action) for action in triggered))

    error_events = repository.error_events_for_attempt(attempt_id)
    if error_events:
        _echo_section("error attributions")
        for event in error_events:
            is_misc = bool(event.get("is_misconception"))
            kind = typer.style("misconception", fg=typer.colors.RED) if is_misc else _dim("error")
            severity = event.get("severity")
            severity_label = f" severity={severity:.2f}" if isinstance(severity, (int, float)) else ""
            status = str(event.get("status"))
            status_styled = typer.style(status, fg=typer.colors.YELLOW if status == "active" else typer.colors.GREEN)
            error_type = typer.style(str(event.get("error_type")), fg=typer.colors.RED if is_misc else None)
            typer.echo(f"  {_dim(event.get('id'))} {error_type} ({kind}){severity_label} status={status_styled}")

    extras = {
        key: value
        for key, value in payload.items()
        if key not in _ATTEMPT_COVERED_FIELDS and value not in (None, "", [], {})
    }
    if extras:
        _echo_section("other fields")
        for key in sorted(extras):
            value = extras[key]
            if isinstance(value, (dict, list)):
                value = jsonlib.dumps(value, sort_keys=True, default=str)
            typer.echo(f"  {_dim(key + ':')} {value}")

def _echo_causal_episode(episode: dict[str, Any] | None) -> None:
    _echo_section("causal episode")
    if episode is None or not isinstance(episode.get("receipt"), dict):
        typer.echo("  No P1 diagnosis receipt was recorded.")
        return
    receipt = episode["receipt"]
    _echo_kv("receipt", receipt.get("id"))
    _echo_kv("schema", receipt.get("schema_version"))
    _echo_kv(
        "decision policy",
        episode.get("decision_policy_version") or "pre-P2",
    )
    _echo_kv("support authority", receipt.get("support_authority"))
    _echo_kv(
        "permitted uses",
        ", ".join(str(value) for value in receipt.get("permitted_uses") or [])
        or "none",
    )

    typer.echo(f"  {_dim('criterion outcomes:')}")
    for row in receipt.get("criterion_outcomes") or []:
        if not isinstance(row, dict):
            continue
        assessable = bool(row.get("assessable"))
        passed = bool(row.get("passed"))
        mark = "✓" if passed else ("✗" if assessable else "·")
        color = (
            typer.colors.GREEN
            if passed
            else (typer.colors.RED if assessable else typer.colors.BRIGHT_BLACK)
        )
        typer.echo(
            "    "
            + typer.style(mark, fg=color)
            + f" {row.get('criterion_id')} "
            + _dim(
                f"{row.get('points_awarded')}/{row.get('points_possible')}"
                + ("" if assessable else " unassessable")
            )
        )

    hypotheses = {
        str(value["id"]): value
        for value in episode.get("hypotheses") or []
        if isinstance(value, dict)
    }
    support = receipt.get("support_scores") or {}
    trace_states = episode.get("trace_consistency") or {}
    typer.echo(f"  {_dim('candidate causes:')}")
    for ref in receipt.get("hypotheses") or []:
        if not isinstance(ref, dict):
            continue
        hypothesis = hypotheses.get(str(ref.get("id") or ""))
        if hypothesis is None:
            continue
        score = support.get(str(hypothesis["id"]))
        score_label = (
            f" support={float(score):.2f}"
            if isinstance(score, (int, float))
            else " support=unscored"
        )
        status = str(hypothesis.get("status") or "candidate")
        typer.echo(
            f"    {_dim(hypothesis['id'])} "
            + typer.style(
                f"[{status}]",
                fg=(
                    typer.colors.BRIGHT_BLACK
                    if status == "open_set"
                    else typer.colors.YELLOW
                ),
            )
            + score_label
            + _dim(
                " trace="
                + str(trace_states.get(str(hypothesis["id"]), "unknown"))
            )
        )
        for line in _wrap_text(
            str(hypothesis.get("statement") or ""),
            indent="      ",
        ):
            typer.echo(line)
        evidence = hypothesis.get("evidence")
        if isinstance(evidence, dict) and evidence.get("observed_evidence"):
            for line in _wrap_text(
                "evidence: " + str(evidence["observed_evidence"]),
                indent="      ",
            ):
                typer.echo(_dim(line))

    cover = receipt.get("common_repair_cover") or {}
    selection = receipt.get("repair_selection") or {}
    selected = selection.get("selected") if isinstance(selection, dict) else None
    typer.echo(f"  {_dim('repair decision:')}")
    if isinstance(selected, dict):
        repair_class = selected.get("repair_class") or {}
        _echo_kv("selected class", repair_class.get("id"))
        _echo_kv("operator", repair_class.get("operator"))
        _echo_kv(
            "common cover",
            "yes"
            if cover.get("covers_plausible_set")
            else "no",
        )
        minimality = selected.get("minimality") or {}
        _echo_kv("latent changes", minimality.get("latent_change_cost"))
        _echo_kv("checkpoint changes", minimality.get("checkpoint_change_cost"))
        _echo_kv("trace edit cost", minimality.get("trace_edit_cost"))
        _echo_kv("estimated minutes", minimality.get("estimated_minutes"))
    else:
        typer.echo("    No safe structural repair was selected.")
    for rejected in (
        selection.get("rejected") if isinstance(selection, dict) else []
    ) or []:
        if not isinstance(rejected, dict):
            continue
        typer.echo(
            "    rejected "
            + str(rejected.get("repair_class_id"))
            + ": "
            + ", ".join(str(value) for value in rejected.get("reasons") or [])
        )
    probe = episode.get("probe_need") or {}
    if probe:
        _echo_kv("probe need: divergent", "yes" if probe.get("divergent") else "no")
        _echo_kv(
            "probe need: common cover",
            "yes" if probe.get("common_repair_cover") else "no",
        )
        _echo_kv(
            "probe need: incomplete repair mapping",
            "yes" if probe.get("incomplete_repair_mapping") else "no",
        )
        if probe.get("reason"):
            for line in _wrap_text(
                str(probe["reason"]), indent="    "
            ):
                typer.echo(line)

def _goal_or_exit(loaded, goal_id: str, *, json_output: bool):
    for goal in loaded.goals:
        if goal.id == goal_id:
            return goal
    message = f"No goal found for {goal_id}."
    if json_output:
        typer.echo(_dump({"version": 1, "error": "unknown_goal", "message": message}))
    else:
        typer.echo(message, err=True)
    raise typer.Exit(code=1)

EXAM_SELF_GRADE_REFUSAL = (
    "Exam answers need an AI grading provider (self-grading a held-out exam "
    "would not be a measurement). Configure a provider and retry."
)

def _exam_answer_refusal(code: str, message: str, *, json_output: bool) -> None:
    if json_output:
        typer.echo(_dump({"version": 1, "error": code, "message": message}))
    else:
        typer.echo(message, err=True)
    raise typer.Exit(code=1)

def _stage7_manifest(path: Path) -> Any:
    try:
        return jsonlib.loads(path.read_text(encoding="utf-8"))
    except (OSError, jsonlib.JSONDecodeError) as exc:
        raise ValueError(f"could not read Stage-7 JSON manifest {path}: {exc}") from exc

def _parse_sim_sets(sets: list[str] | None) -> dict[str, Any]:
    from learnloop.sim.runner import coerce_override_value

    overrides: dict[str, Any] = {}
    for raw in sets or []:
        if "=" not in raw:
            raise typer.BadParameter(f"--set expects param.path=value, got {raw!r}")
        path, value = raw.split("=", 1)
        overrides[path.strip()] = coerce_override_value(value)
    return overrides

def _sim_run_root(source_root: Path, *, fresh_copy: bool, reset_state: bool) -> Path:
    import tempfile

    from learnloop.sim.runner import prepare_run_vault

    if not fresh_copy:
        return source_root
    run_parent = Path(tempfile.mkdtemp(prefix="learnloop-sim-"))
    return prepare_run_vault(source_root, run_parent / "vault", reset_state=reset_state)

def _write_or_echo_report(payload: dict, *, json_output: bool, output: Path | None) -> None:
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(_dump(payload), encoding="utf-8")
        typer.echo(f"Wrote report to {output}")
    elif json_output:
        typer.echo(_dump(payload))

__all__ = [name for name in globals() if not name.startswith("__")]
