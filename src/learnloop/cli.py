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
from learnloop.services.exam_seeding import (
    ExamSeedingError,
    exam_ingest_instructions,
    parse_exam_outcomes,
    seed_exam_attempts,
)
from learnloop.services.exam_pool import reserve_exam_pool
from learnloop.services.exam_session import (
    ExamSessionError,
    exam_availability,
    exam_report as exam_report_service,
    finish_exam,
    record_exam_answer,
    start_exam,
)
from learnloop.services.exam_calibration import calibration_report as exam_calibration_report
from learnloop.services.grading import confidence_to_grader_confidence, resolved_rubric
from learnloop.services.attempts import GradeAttribution, ResolvedGrade, _rubric_score
from learnloop.ids import new_ulid
from learnloop.services.concepts import ConceptMergeError, merge_concepts
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
    build_goal_practice_plan,
    build_practice_expansion_plan,
    generate_diagnostic_practice_proposal,
    generate_goal_practice_proposal,
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
from learnloop.services.diagnostic_gate import (
    BACKFILL_SKIPPED_EXISTING,
    BACKFILL_SKIPPED_UNREGISTERED,
    backfill_discrimination_rows,
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

_INGEST_SPINNER_FRAMES = ("|", "/", "-", "\\")
_INGEST_PROGRESS_EVENT = "learnloop_ingest_progress"


def _format_elapsed(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def _json_ingest_progress(phase: str, details: dict[str, Any]) -> None:
    payload = {_INGEST_PROGRESS_EVENT: {"phase": phase, **details}}
    print(jsonlib.dumps(payload, sort_keys=True, separators=(",", ":")), file=sys.stderr, flush=True)


class _AsciiSpinner:
    def __init__(
        self,
        label: str,
        *,
        enabled: bool,
        stream: TextIO | None = None,
        interval: float = 0.2,
    ) -> None:
        self.label = label
        self.enabled = enabled
        self.stream = stream or sys.stderr
        self.interval = interval
        self._interactive = False
        self._last_width = 0
        self._started = 0.0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self):
        if not self.enabled:
            return self
        self._started = time.monotonic()
        self._interactive = bool(getattr(self.stream, "isatty", lambda: False)())
        if not self._interactive:
            self._write(f"{self.label}... this can take around 200s.\n")
            return self
        self._thread = threading.Thread(target=self._spin, name="learnloop-ingest-spinner", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, _exc, _traceback) -> bool:
        if not self.enabled:
            return False
        elapsed = _format_elapsed(time.monotonic() - self._started)
        status = "Failed" if exc_type else "Done"
        if self._interactive:
            self._stop.set()
            if self._thread is not None:
                self._thread.join(timeout=self.interval * 2)
            self._write_status(f"{status}: {self.label} in {elapsed}.")
            self._write("\n")
        else:
            self._write(f"{status}: {self.label} in {elapsed}.\n")
        return False

    def _spin(self) -> None:
        frame_index = 0
        while not self._stop.is_set():
            elapsed = _format_elapsed(time.monotonic() - self._started)
            frame = _INGEST_SPINNER_FRAMES[frame_index]
            self._write_status(f"{frame} {self.label} elapsed {elapsed} (usually around 200s)")
            frame_index = (frame_index + 1) % len(_INGEST_SPINNER_FRAMES)
            self._stop.wait(self.interval)

    def _write_status(self, line: str) -> None:
        padding = " " * max(0, self._last_width - len(line))
        self._write(f"\r{line}{padding}")
        self._last_width = len(line)

    def _write(self, text: str) -> None:
        try:
            self.stream.write(text)
            self.stream.flush()
        except OSError:
            self.enabled = False
            self._stop.set()


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


@app.command("upgrade")
def upgrade(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Atomically activate the mvp-0.7 knowledge model for this vault (KM §15)."""

    from learnloop.services.vault_upgrade import upgrade_to_mvp07

    result = upgrade_to_mvp07(_root(vault))
    if result.upgraded:
        typer.echo(f"Upgraded vault: {result.from_version} -> {result.to_version}")
        return
    typer.echo(f"Vault not upgraded (currently {result.from_version}):")
    for problem in result.problems:
        typer.echo(f"  - {problem}")
    raise typer.Exit(code=1)


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
    related_los: Annotated[
        str | None,
        typer.Option("--related-los", help="Comma-separated learning object ids to link this note to."),
    ] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    note_body = file.read_text(encoding="utf-8") if file else body
    try:
        path = add_note_to_vault(
            _root(vault),
            subject_id,
            note_id,
            title,
            note_body,
            source_type=source_type,
            related_los=_split_items(related_los),
        )
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
    pdf_engine: Annotated[
        str | None,
        typer.Option("--pdf-engine", help="PDF extraction engine override: auto, marker, or pypdf."),
    ] = None,
    pdf_llm: Annotated[
        bool | None,
        typer.Option("--pdf-llm/--no-pdf-llm", help="Toggle marker's VLM boost for difficult scans/math (see [ingest.pdf])."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    progress_json: Annotated[bool, typer.Option("--progress-json", hidden=True)] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    result = _run_canonical_ingest_command(
        source,
        kind=kind,
        subject=subject,
        learning_objects=learning_objects,
        goal=goal,
        allow_auto_captions=allow_auto_captions,
        instructions=instructions,
        ai_provider=ai_provider,
        pdf_engine=pdf_engine,
        pdf_use_llm=pdf_llm,
        json_output=json_output,
        progress_json=progress_json,
        vault=vault,
    )
    if json_output:
        typer.echo(_dump({"version": 1, "ingest": result.as_dict()}))
        return
    _echo_ingest_summary(result)


@app.command("ingest-exam")
def ingest_exam(
    source: Annotated[str, typer.Argument(help="URL or local past-exam file to ingest.")],
    kind: Annotated[
        str,
        typer.Option("--kind", help="Source kind: auto, website_page, youtube_video, arxiv_html, or textbook_chapter."),
    ] = "auto",
    subject: Annotated[str | None, typer.Option("--subject", help="Target subject id.")] = None,
    goal: Annotated[str | None, typer.Option("--goal", help="Active goal id to link ingested concepts to.")] = None,
    instructions: Annotated[
        str | None,
        typer.Option("--instructions", help="Extra instructions appended to the exam-ingest instructions."),
    ] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for ingestion.")] = None,
    pdf_engine: Annotated[
        str | None,
        typer.Option("--pdf-engine", help="PDF extraction engine override: auto, marker, or pypdf."),
    ] = None,
    pdf_llm: Annotated[
        bool | None,
        typer.Option("--pdf-llm/--no-pdf-llm", help="Toggle marker's VLM boost for difficult scans/math (see [ingest.pdf])."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    progress_json: Annotated[bool, typer.Option("--progress-json", hidden=True)] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Ingest a past practice exam: one tagged practice item per exam question.

    Runs the standard canonical ingest pipeline with exam-specific instructions
    (one practice_item per question, tagged exam_q:<n> + exam_question, each
    with a rubric, evidence facets, and a learning object). After reviewing and
    accepting the proposal, seed your per-question outcomes with
    `learnloop seed-exam-attempts --outcomes <file>`.
    """

    result = _run_canonical_ingest_command(
        source,
        kind=kind,
        subject=subject,
        learning_objects=None,
        goal=goal,
        allow_auto_captions=None,
        instructions=exam_ingest_instructions(instructions),
        ai_provider=ai_provider,
        pdf_engine=pdf_engine,
        pdf_use_llm=pdf_llm,
        json_output=json_output,
        progress_json=progress_json,
        vault=vault,
        purpose="exam_ingest",
        spinner_label="Ingesting past exam",
    )
    if json_output:
        typer.echo(_dump({"version": 1, "ingest": result.as_dict()}))
        return
    _echo_ingest_summary(result)
    typer.echo(
        "Next: review/accept the proposal (learnloop proposals / learnloop accept), "
        "then run: learnloop seed-exam-attempts --outcomes <outcomes.json>"
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


def _echo_ingest_summary(result) -> None:
    reused = "Reused" if result.reused_existing else "Persisted"
    typer.echo(
        f"{reused} proposal {result.patch_id} from {result.source_note_id}: "
        f"auto_applied={result.auto_applied_count} "
        f"review_required={result.review_required_count} invalid={result.invalid_count}"
    )


def _ingest_runner(vault_root: Path):
    from learnloop.services.ingest_runner import IngestRunner

    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    runner_config = loaded.config.ingest.runner
    return IngestRunner(
        repository,
        vault_root=vault_root,
        worker_id=f"cli-{os.getpid()}",
        lease_ttl_seconds=runner_config.lease_ttl_seconds,
    )


def _batch_json(runner, batch_id: str) -> dict[str, Any]:
    batch = runner.repo.get_ingest_batch(batch_id)
    if batch is None:
        return {}
    jobs = runner.repo.ingest_jobs_for_batch(batch_id)
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


@app.command("import")
def import_sources(
    sources: Annotated[list[str], typer.Argument(help="URLs, arXiv ids, or local files to import.")],
    subject: Annotated[str | None, typer.Option("--subject", help="Optional subject id for the batch.")] = None,
    inventory: Annotated[bool, typer.Option("--inventory", help="Also queue role-specific unit inventories (M3 seam).")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the durable batch as JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Import sources into the vault library through the durable queue (§6.1).

    Enqueues one durable ``import`` job per source and drains them in the
    foreground when no sidecar worker holds the lease."""

    from learnloop.services.ingest_runner import JobSpec

    vault_root = _root(vault)
    _load_vault_or_exit(vault_root, json_output=json_output)
    runner = _ingest_runner(vault_root)
    specs: list[JobSpec] = []
    for source in sources:
        import_index = len(specs)
        specs.append(JobSpec("import", {"source": source}))
        if inventory:
            specs.append(JobSpec("inventory", {"source": source}, depends_on=(import_index,)))
    workflow = "import_inventory" if inventory else "import"
    batch_id = runner.enqueue_batch(workflow, specs, subject_id=subject)
    runner.recover_stale_leases()
    runner.drain()
    payload = _batch_json(runner, batch_id)
    if json_output:
        typer.echo(_dump({"version": 1, "batch": payload}))
        return
    typer.echo(f"Batch {payload['id']} [{payload['status']}]")
    for job in payload["jobs"]:
        detail = job.get("error", {}).get("message") if job.get("error") else job.get("message")
        typer.echo(f"  {job['ordinal']:>2} {job['job_type']:<16} {job['status']:<12} {detail or ''}")


@app.command("quick-add")
def quick_add_cmd(
    source: Annotated[str, typer.Argument(help="URL or local file to turn into a study map.")],
    subject: Annotated[str | None, typer.Option("--subject", help="Target subject id for the study map.")] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the single confirmation prompt.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Quick add (§1): paste one source -> auto-selected units, suggested role,
    default brief, ONE confirmation, then a priority build batch to a study map.

    Imports the source first when it has no completed extraction (acquisition is
    deterministic and token-free — not a consent checkpoint), then plans, confirms
    once, and drains the priority [inventory -> synthesis] batch."""

    from learnloop.services.quick_add import QuickAddError, enqueue_quick_add, plan_quick_add
    from learnloop_sidecar.ingest_jobs import DurableIngestJobs

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    if subject is not None and subject not in loaded.subjects:
        message = f"Subject '{subject}' does not exist."
        typer.echo(_dump({"version": 1, "error": "unknown_subject", "message": message}) if json_output else message, err=not json_output)
        raise typer.Exit(code=1)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    jobs = DurableIngestJobs()
    jobs.bind(repository, vault_root, background=False, lease_ttl_seconds=loaded.config.ingest.runner.lease_ttl_seconds)

    def _plan():
        return plan_quick_add(repository, loaded.config, loaded, source, subject_id=subject)

    try:
        try:
            plan = _plan()
        except QuickAddError as exc:
            if exc.code != "quick_add_requires_import":
                raise
            if not json_output:
                typer.echo(f"Importing {source} ...")
            jobs.enqueue_import([source], subject_id=subject)  # background=False drains inline
            plan = _plan()
    except QuickAddError as exc:
        typer.echo(_dump({"version": 1, "error": exc.code, "message": str(exc)}) if json_output else f"{exc.code}: {exc}", err=not json_output)
        raise typer.Exit(code=1)

    confirmation = plan.confirmation()
    if not json_output:
        typer.echo(f"Quick add: {confirmation['title']}")
        scope = "whole source" if confirmation["whole_source"] else f"{confirmation['selected_unit_count']} unit(s)"
        typer.echo(f"  role: {confirmation['suggested_role']}{' (ambiguous — flagged)' if confirmation['role_ambiguous'] else ''}")
        typer.echo(f"  scope: {scope}, ~{confirmation['selected_tokens']} tokens")
        typer.echo(f"  estimated input: ~{confirmation['estimated_input_tokens']} tokens")
        if confirmation["requires_external_ai"]:
            stages = ", ".join(sorted({str(c.get('stage')) for c in confirmation['external_ai_consent']}))
            typer.echo(f"  external AI: yes ({stages})")
    if not yes and not json_output:
        typer.confirm("Proceed with import + synthesis?", abort=True)

    try:
        result = enqueue_quick_add(loaded, jobs, plan)  # background=False drains inline
    except QuickAddError as exc:
        typer.echo(_dump({"version": 1, "error": exc.code, "message": str(exc)}) if json_output else f"{exc.code}: {exc}", err=not json_output)
        raise typer.Exit(code=1)

    batch = _batch_json(jobs._require_runner(), result["batch_id"])
    if json_output:
        typer.echo(_dump({"version": 1, "quick_add": result, "batch": batch}))
        return
    typer.echo(f"Batch {batch['id']} [{batch['status']}] -> source set {result['source_set_id']}")
    for job in batch["jobs"]:
        detail = job.get("error", {}).get("message") if job.get("error") else job.get("message")
        typer.echo(f"  {job['ordinal']:>2} {job['job_type']:<20} {job['status']:<12} {detail or ''}")


ingest_batches_app = typer.Typer(no_args_is_help=True, help="Inspect and control durable ingest batches (§6.2).")
app.add_typer(ingest_batches_app, name="ingest-batches")


@ingest_batches_app.command("list")
def ingest_batches_list(
    limit: Annotated[int, typer.Option("--limit", help="Max batches to list.")] = 30,
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    runner = _ingest_runner(_root(vault))
    batches = [_batch_json(runner, batch["id"]) for batch in runner.repo.list_ingest_batches(limit=limit)]
    if json_output:
        typer.echo(_dump({"version": 1, "batches": batches}))
        return
    if not batches:
        typer.echo("No ingest batches.")
        return
    for batch in batches:
        done = sum(1 for job in batch["jobs"] if job["status"] == "completed")
        typer.echo(f"{batch['id']} [{batch['status']}] {batch['workflow_type']} {done}/{len(batch['jobs'])} jobs")


@ingest_batches_app.command("show")
def ingest_batches_show(
    batch_id: Annotated[str, typer.Argument(help="Batch id.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    runner = _ingest_runner(_root(vault))
    batch = _batch_json(runner, batch_id)
    if not batch:
        typer.echo(_dump({"version": 1, "error": "ingest_batch_not_found"}) if json_output else f"Batch {batch_id} not found.", err=not json_output)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "batch": batch}))
        return
    typer.echo(f"Batch {batch['id']} [{batch['status']}] {batch['workflow_type']}")
    for job in batch["jobs"]:
        typer.echo(f"  {job['ordinal']:>2} {job['job_type']:<16} {job['status']:<12} phase={job.get('phase')}")


@ingest_batches_app.command("cancel")
def ingest_batches_cancel(
    batch_id: Annotated[str, typer.Argument(help="Batch id.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    runner = _ingest_runner(_root(vault))
    if runner.repo.get_ingest_batch(batch_id) is None:
        typer.echo(f"Batch {batch_id} not found.", err=True)
        raise typer.Exit(code=1)
    runner.cancel_batch(batch_id)
    batch = _batch_json(runner, batch_id)
    typer.echo(_dump({"version": 1, "batch": batch}) if json_output else f"Batch {batch_id} [{batch['status']}]")


@ingest_batches_app.command("resume")
def ingest_batches_resume(
    batch_id: Annotated[str, typer.Argument(help="Batch id.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    runner = _ingest_runner(_root(vault))
    if runner.repo.get_ingest_batch(batch_id) is None:
        typer.echo(f"Batch {batch_id} not found.", err=True)
        raise typer.Exit(code=1)
    runner.resume_batch(batch_id)
    runner.recover_stale_leases()
    runner.drain()
    batch = _batch_json(runner, batch_id)
    typer.echo(_dump({"version": 1, "batch": batch}) if json_output else f"Batch {batch_id} [{batch['status']}]")


@app.command("source-outline")
def source_outline_command(
    ref: Annotated[str, typer.Argument(help="Extraction, revision, or artifact id to outline.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit the outline as JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Deterministic outline of a source's extraction — zero agent runs (§3/§5.7)."""

    from learnloop.services.source_outline import build_source_outline, resolve_extraction_id

    vault_root = _root(vault)
    repository = _repository(vault_root)
    extraction_id = resolve_extraction_id(repository, ref)
    if extraction_id is None:
        typer.echo(f"No extraction resolves for '{ref}'.", err=True)
        raise typer.Exit(code=1)
    outline = build_source_outline(repository, extraction_id)
    if json_output:
        typer.echo(_dump({"version": 1, "outline": outline.model_dump(mode="json")}))
        return
    typer.echo(f"{outline.title}  [{outline.extractor} {outline.extractor_version}]")
    typer.echo(f"  units={outline.unit_count} blocks={outline.block_count} ~{outline.approx_tokens} tokens")
    if outline.difficult_page_count:
        typer.echo(f"  {outline.difficult_page_count} difficult page(s) flagged for repair")
    for unit in outline.units:
        signals = ",".join(f"{k}={v}" for k, v in unit.structural_signals.items() if v)
        flags = f" flags={','.join(unit.health_flags)}" if unit.health_flags else ""
        typer.echo(f"  {unit.ordinal:>2} {unit.unit_id:<8} {unit.label[:40]:<40} ~{unit.approx_tokens:>6}t {signals}{flags}")


@app.command("select-units")
def select_units_command(
    extraction_id: Annotated[str, typer.Argument(help="Extraction id to record a selection for.")],
    units: Annotated[list[str], typer.Option("--unit", help="Selected unit id (repeatable).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the stored selection as JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Persist a per-extraction unit selection (§5.3)."""

    from learnloop.services.source_unit_selection import SelectionValidationError, save_unit_selection

    repository = _repository(_root(vault))
    try:
        selection = save_unit_selection(repository, extraction_id, list(units or []))
    except SelectionValidationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "selection": selection}))
        return
    typer.echo(f"Selected {len(selection['selected_unit_ids'])} unit(s): {', '.join(selection['selected_unit_ids'])}")


source_set_app = typer.Typer(no_args_is_help=True, help="Create and manage source collections (§4.3).")
app.add_typer(source_set_app, name="source-set")


@source_set_app.command("create")
def source_set_create(
    set_id: Annotated[str, typer.Argument(help="Source-set id.")],
    subject_id: Annotated[str, typer.Option("--subject", help="Subject id the set belongs to.")],
    title: Annotated[str, typer.Option("--title", help="Human title.")] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Create an empty source collection (§4.3)."""

    from learnloop.vault.writer import upsert_source_set

    root = _root(vault)
    upsert_source_set(root, {"id": set_id, "subject_id": subject_id, "title": title or set_id, "members": []})
    _show_source_set(root, set_id, json_output)


@source_set_app.command("add")
def source_set_add(
    set_id: Annotated[str, typer.Argument(help="Source-set id.")],
    source_id: Annotated[str, typer.Option("--source", help="Library source id.")],
    revision_id: Annotated[str, typer.Option("--revision", help="Pinned revision id (required, §4.3).")],
    role: Annotated[str, typer.Option("--role", help="Membership role (open string).")] = "reference",
    units: Annotated[list[str] | None, typer.Option("--unit", help="Scope unit id (repeatable). Empty = whole artifact.")] = None,
    priority: Annotated[int, typer.Option("--priority")] = 1,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Add a pinned source to a collection (membership owns role/scope, §4.3)."""

    from learnloop.vault.loader import load_vault
    from learnloop.vault.writer import upsert_source_set

    root = _root(vault)
    vault_loaded = load_vault(root)
    source_set = next((s for s in vault_loaded.source_sets if s.id == set_id), None)
    if source_set is None:
        typer.echo(f"Source set '{set_id}' does not exist; create it first.", err=True)
        raise typer.Exit(code=1)
    members = [member.model_dump(mode="json", exclude_none=False) for member in source_set.members]
    members = [member for member in members if member.get("source_id") != source_id]
    members.append(
        {
            "source_id": source_id,
            "revision_id": revision_id,
            "default_role": role,
            "scope": [{"unit_id": unit_id, "role_override": None} for unit_id in (units or [])],
            "priority": priority,
        }
    )
    upsert_source_set(
        root,
        {"id": set_id, "subject_id": source_set.subject_id, "title": source_set.title, "members": members},
    )
    _show_source_set(root, set_id, json_output)


@source_set_app.command("update")
def source_set_update(
    set_id: Annotated[str, typer.Argument(help="Source-set id.")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Update a collection's title (membership edits use add)."""

    from learnloop.vault.writer import upsert_source_set

    root = _root(vault)
    payload: dict[str, object] = {"id": set_id}
    if title is not None:
        payload["title"] = title
    upsert_source_set(root, payload)
    _show_source_set(root, set_id, json_output)


@source_set_app.command("list")
def source_set_list(
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """List source collections."""

    from learnloop.vault.loader import load_vault

    vault_loaded = load_vault(_root(vault))
    rows = [
        {"id": s.id, "subject_id": s.subject_id, "title": s.title, "members": len(s.members)}
        for s in vault_loaded.source_sets
    ]
    if json_output:
        typer.echo(_dump({"version": 1, "source_sets": rows}))
        return
    for row in rows:
        typer.echo(f"{row['id']:<28} {row['subject_id']:<18} members={row['members']}  {row['title']}")


@source_set_app.command("show")
def source_set_show(
    set_id: Annotated[str, typer.Argument(help="Source-set id.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Show a collection's members, roles, and scopes."""

    _show_source_set(_root(vault), set_id, json_output)


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


@app.command("inventory")
def inventory_command(
    ref: Annotated[str, typer.Argument(help="Revision / extraction / artifact id.")],
    units: Annotated[list[str] | None, typer.Option("--unit", help="Unit id to inventory (repeatable).")] = None,
    role: Annotated[str, typer.Option("--role", help="Confirmed role (§4.2).")] = "reference",
    profile: Annotated[str | None, typer.Option("--profile", help="semantic|practice|assessment|combined.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Run role-aware unit inventories over selected units (§7)."""

    from learnloop.services.source_outline import resolve_extraction_id
    from learnloop.services.source_unit_inventory import run_unit_inventory

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    extraction_id = resolve_extraction_id(repository, ref)
    if extraction_id is None:
        typer.echo(f"No extraction resolves for '{ref}'.", err=True)
        raise typer.Exit(code=1)
    unit_ids = list(units or [])
    if not unit_ids:
        selection = repository.get_unit_selection(extraction_id)
        unit_ids = (selection or {}).get("selected_unit_ids", [])
    if not unit_ids:
        typer.echo("No units to inventory (pass --unit or record a selection first).", err=True)
        raise typer.Exit(code=1)

    runtime = check_codex_runtime(vault_root, loaded.config.codex)
    client = make_codex_client(loaded.config.codex, vault_root) if runtime.ready else None
    if client is None:
        typer.echo(runtime.message or "Codex runtime is unavailable.", err=True)
        raise typer.Exit(code=1)

    results = []
    for unit_id in unit_ids:
        result = run_unit_inventory(
            repository,
            extraction_id,
            unit_id,
            role=role,
            profile=profile,
            client=client,
            input_budget_tokens=loaded.config.ingest.budgets.inventory_input_tokens,
        )
        results.append(
            {"unit_id": unit_id, "inventory_id": result.inventory_id, "profile": result.profile, "cache_hit": result.cache_hit}
        )
    if json_output:
        typer.echo(_dump({"version": 1, "extraction_id": extraction_id, "units": results}))
        return
    for row in results:
        marker = "cached" if row["cache_hit"] else "new"
        typer.echo(f"  {row['unit_id']:<12} {row['profile']:<10} {marker}  {row['inventory_id']}")


@app.command("source-coverage")
def source_coverage_command(
    set_id: Annotated[str, typer.Argument(help="Source-set id.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Deterministic coverage + readiness preview for a collection (§9.3)."""

    from learnloop.services.source_coverage import build_source_coverage

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    source_set = next((s for s in loaded.source_sets if s.id == set_id), None)
    if source_set is None:
        typer.echo(f"Source set '{set_id}' does not exist.", err=True)
        raise typer.Exit(code=1)
    report = build_source_coverage(repository, loaded, source_set)
    if json_output:
        typer.echo(_dump({"version": 1, "coverage": report}))
        return
    typer.echo(f"Coverage for {report['source_set_id']} ({report['subject_id']})")
    typer.echo(f"  ready={report['readiness']['ready']}")
    for flag in report["readiness"]["flags"]:
        typer.echo(f"  ! {flag['code']}: {flag['message']}")


@app.command("synthesize")
def synthesize_command(
    set_id: Annotated[str, typer.Argument(help="Source-set id.")],
    mode: Annotated[str, typer.Option("--mode", help="auto|bootstrap|append.")] = "auto",
    brief_file: Annotated[Path | None, typer.Option("--brief-file", help="JSON synthesis brief (§8.3).")] = None,
    apply_map: Annotated[bool, typer.Option("--apply", help="Accept the study map under the vault lock (requires mvp-0.7).")] = False,
    create_goal: Annotated[bool, typer.Option("--create-goal", help="Create an exam-prep Goal wired to the minted facets.")] = False,
    new_revision: Annotated[list[str] | None, typer.Option("--new-revision", help="Revision id(s) newly added/changed (append mode).")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Create or UPDATE a study map from a source set (§8 bootstrap / §10 append).

    mode=auto routes to append when the vault already has an applied study map
    (facets present), else bootstrap — adding a member to a set with a study map
    updates it incrementally with a bounded affected-neighborhood pass."""

    from learnloop.services.source_append import append_source
    from learnloop.services.source_set_synthesis import StudyMapError, create_study_map

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    if not any(s.id == set_id for s in loaded.source_sets):
        typer.echo(f"Source set '{set_id}' does not exist.", err=True)
        raise typer.Exit(code=1)
    brief: dict = {}
    if brief_file is not None:
        brief = jsonlib.loads(brief_file.read_text(encoding="utf-8"))

    runtime = check_codex_runtime(vault_root, loaded.config.codex)
    client = make_codex_client(loaded.config.codex, vault_root) if runtime.ready else None
    if client is None:
        typer.echo(runtime.message or "Codex runtime is unavailable.", err=True)
        raise typer.Exit(code=1)

    resolved_mode = mode
    if mode == "auto":
        resolved_mode = "append" if loaded.evidence_facets else "bootstrap"

    if resolved_mode == "append":
        try:
            append = append_source(vault_root, set_id, client=client, brief=brief,
                                   new_revision_ids=new_revision)
        except StudyMapError as exc:
            if json_output:
                typer.echo(_dump({"version": 1, "error": exc.code, "message": str(exc),
                                  "diagnostics": exc.diagnostics}))
            else:
                typer.echo(f"{exc.code}: {exc}", err=True)
            raise typer.Exit(code=1)
        if json_output:
            typer.echo(_dump({"version": 1, "append": append.as_dict()}))
            return
        typer.echo(f"Updated study map for {append.subject_id} ({append.change_kind}) — proposal {append.proposal_id}")
        typer.echo(f"  auto-applied={len(append.auto_applied_item_ids)} review={len(append.review_item_ids)} items={append.item_counts}")
        typer.echo(f"  study-map diff: {append.study_map_diff}")
        return

    try:
        result = create_study_map(
            vault_root, set_id, client=client, brief=brief, mode=resolved_mode,
            apply=apply_map, create_goal=create_goal,
        )
    except StudyMapError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": exc.code, "message": str(exc),
                              "diagnostics": exc.diagnostics, "lockReasons": exc.lock_reasons}))
        else:
            typer.echo(f"{exc.code}: {exc}", err=True)
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(_dump({"version": 1, "studyMap": result.as_dict()}))
        return
    typer.echo(f"Study map for {result.subject_id} ({result.mode}) — proposal {result.proposal_id}")
    typer.echo(f"  reused={result.reused} applied={result.applied} items={result.item_counts}")
    if result.generation_needs:
        typer.echo(f"  identifiability needs: {len(result.generation_needs)}")
    for diag in result.gate_diagnostics:
        if diag["severity"] != "hard_fail":
            typer.echo(f"  ~ {diag['gate']}: {diag['message']}")


@app.command("maintenance-feed")
def maintenance_feed_command(
    action: Annotated[str, typer.Option("--action", help="list|dismiss|snooze.")] = "list",
    notice_id: Annotated[str | None, typer.Option("--notice", help="Notice id for dismiss/snooze.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Maintenance feed (§11): deterministic notices with per-type aging policies."""

    from learnloop.services.maintenance_feed import dismiss_notice, generate_maintenance_feed, snooze_notice

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(vault_root, loaded.config).sqlite_path)
    if action == "dismiss" and notice_id:
        dismiss_notice(repository, notice_id)
    elif action == "snooze" and notice_id:
        snooze_notice(repository, notice_id)
    feed = generate_maintenance_feed(loaded, repository)
    if json_output:
        typer.echo(_dump({"version": 1, "notices": feed}))
        return
    if not feed:
        typer.echo("Maintenance feed is clear.")
        return
    for notice in feed:
        typer.echo(f"[{notice['severity']}] {notice['notice_type']}: {notice['title']}  -> {notice['action'].get('action')} ({notice['id']})")


@app.command("exam-readiness")
def exam_readiness_command(
    subject: Annotated[str | None, typer.Option("--subject", help="Restrict to one subject.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Lightweight exam-readiness-by-task-family report (§15) — deterministic, no LLM."""

    from learnloop.services.exam_readiness import exam_readiness_report

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(vault_root, loaded.config).sqlite_path)
    report = exam_readiness_report(loaded, repository, subject_id=subject)
    if json_output:
        typer.echo(_dump({"version": 1, "report": report.as_dict()}))
        return
    typer.echo(f"Exam readiness (Ready vs Demonstrated) — {len(report.rows)} task families")
    for row in report.rows:
        ready = f"{row.ready:.2f}" if row.ready is not None else "n/a"
        typer.echo(f"  {row.task_family}: weight={row.normalized_weight:.2f} ready={ready} demonstrated={row.demonstrated_fraction:.2f}")


@app.command("resolve-conflict")
def resolve_conflict_command(
    conflict_id: Annotated[str, typer.Argument(help="source_conflict id.")],
    kind: Annotated[str, typer.Option("--kind", help="prefer_for_context|keep_both_scoped|notation_mapping|dismiss.")],
    resolution_file: Annotated[Path | None, typer.Option("--resolution-file", help="JSON resolution payload.")] = None,
    rationale: Annotated[str | None, typer.Option("--rationale")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Resolve an open source conflict (§10.2) — never applies either side."""

    from learnloop.services.conflict_resolution import ConflictResolutionError, resolve_conflict

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(vault_root, loaded.config).sqlite_path)
    payload = jsonlib.loads(resolution_file.read_text(encoding="utf-8")) if resolution_file else {}
    try:
        conflict = resolve_conflict(repository, conflict_id, resolution_kind=kind,
                                    resolution=payload, actor="cli", rationale=rationale)
    except ConflictResolutionError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "conflict": conflict}))
        return
    typer.echo(f"Conflict {conflict_id} -> {conflict['status']} ({kind})")


@app.command("synthesis-eval")
def synthesis_eval_command(
    subject: Annotated[str, typer.Argument(help="Fixture subject id (informational; keyed per prompt version).")],
    set_id: Annotated[str | None, typer.Option("--set", help="Source set to synthesize + score (live provider run).")] = None,
    gold: Annotated[Path | None, typer.Option("--gold", help="Gold registry YAML (defaults to the bundled fixture).")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Score a synthesized study map against a hand-authored gold registry (§14)."""

    from learnloop.codex.prompts import SOURCE_SET_SYNTHESIS_PROMPT_VERSION
    from learnloop.services.source_set_synthesis import create_study_map
    from learnloop.services.synthesis_eval import (
        default_gold_path,
        evaluate,
        extract_candidate_from_vault,
        load_gold,
    )

    gold_path = gold or default_gold_path()
    gold_data = load_gold(gold_path)

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    if set_id is not None:
        runtime = check_codex_runtime(vault_root, loaded.config.codex)
        client = make_codex_client(loaded.config.codex, vault_root) if runtime.ready else None
        if client is None:
            typer.echo(runtime.message or "Codex runtime is unavailable.", err=True)
            raise typer.Exit(code=1)
        create_study_map(vault_root, set_id, client=client, brief={}, apply=True)
        loaded = load_vault(vault_root)
    candidate = extract_candidate_from_vault(loaded, prompt_version=SOURCE_SET_SYNTHESIS_PROMPT_VERSION)
    report = evaluate(gold_data, candidate)
    if json_output:
        typer.echo(_dump({"version": 1, "eval": report.as_dict()}))
        return
    typer.echo(report.format_text())


@app.command("build-plan")
def build_plan_command(
    refs: Annotated[list[str], typer.Argument(help="Extraction/revision/artifact ids to plan.")],
    subject: Annotated[str | None, typer.Option("--subject", help="Target subject id (Create-vs-Update routing).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the build plan as JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Deterministic build plan with per-stage token estimates (§8.6.2)."""

    from learnloop.services.build_plan import build_build_plan
    from learnloop.services.source_outline import resolve_extraction_id

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    selections: list[dict[str, Any]] = []
    for ref in refs:
        extraction_id = resolve_extraction_id(repository, ref)
        if extraction_id is None:
            typer.echo(f"No extraction resolves for '{ref}'.", err=True)
            raise typer.Exit(code=1)
        selections.append({"extraction_id": extraction_id, "selected_unit_ids": []})
    plan = build_build_plan(repository, loaded.config, loaded, subject_id=subject, selections=selections)
    if json_output:
        typer.echo(_dump({"version": 1, "plan": plan.as_dict()}))
        return
    totals = plan.as_dict()["totals"]
    typer.echo(f"Build plan  routing={plan.routing}  provider={plan.provider}")
    typer.echo(
        f"  units={totals['selected_unit_count']} calls={totals['calls']} "
        f"input~{totals['input_tokens']}t output<={totals['max_output_tokens']}t "
        f"cache_savings~{totals['cache_savings_tokens']}t"
    )
    for stage in plan.stages:
        marker = " OVER-CEILING" if stage.exceeds_ceiling else ""
        typer.echo(
            f"  {stage.stage:<12} calls={stage.calls} input~{stage.input_tokens}t "
            f"out<={stage.max_output_tokens}t ceiling={stage.ceiling}{marker}"
        )
    for warning in plan.warnings:
        typer.echo(f"  ! {warning}")


@app.command("repair-extraction")
def repair_extraction_command(
    revision_id: Annotated[str, typer.Argument(help="Source revision id to repair.")],
    pages: Annotated[str, typer.Option("--pages", help="Page ranges, e.g. '3-5,8'.")],
    force_ocr: Annotated[bool, typer.Option("--force-ocr", help="Force OCR on the repaired pages.")] = False,
    inline_math: Annotated[bool, typer.Option("--inline-math", help="Request inline-math extraction.")] = False,
    table_processing: Annotated[bool, typer.Option("--table-processing", help="Request table processing.")] = False,
    use_llm: Annotated[bool, typer.Option("--use-llm", help="Approve the external VLM boost (external egress).")] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Record CLI consent and run the repair.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the durable batch as JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Consent-gated page-range extraction repair (§2.5). Requires ``--yes``."""

    from learnloop.services.ingest_runner import JobSpec

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    if not yes:
        typer.echo("Refusing to run repair without --yes (consent is required).", err=True)
        raise typer.Exit(code=1)
    page_list = [segment.strip() for segment in pages.split(",") if segment.strip()]
    provider = loaded.config.ingest.pdf.llm_service if use_llm else "local"
    consent = {
        "provider": provider,
        "purpose": "extraction_repair",
        "pages": page_list,
        "cached": False,
        "consented_via": "cli --yes",
        "external": bool(use_llm),
    }
    repair_options = {
        "force_ocr": force_ocr,
        "inline_math": inline_math,
        "table_processing": table_processing,
        "use_llm": use_llm,
    }
    runner = _ingest_runner(vault_root)
    if runner.repo.get_source_revision(revision_id) is None:
        typer.echo(f"Revision '{revision_id}' was not found.", err=True)
        raise typer.Exit(code=1)
    batch_id = runner.enqueue_batch(
        "extraction_repair",
        [
            JobSpec(
                "extraction_repair",
                {
                    "revision_id": revision_id,
                    "pages": page_list,
                    "repair_options": repair_options,
                    "consent": consent,
                },
            )
        ],
    )
    runner.recover_stale_leases()
    runner.drain()
    payload = _batch_json(runner, batch_id)
    if json_output:
        typer.echo(_dump({"version": 1, "batch": payload}))
        return
    typer.echo(f"Repair batch {payload['id']} [{payload['status']}]")
    for job in payload["jobs"]:
        detail = job.get("error", {}).get("message") if job.get("error") else job.get("message")
        typer.echo(f"  {job['job_type']:<18} {job['status']:<12} {detail or ''}")


@app.command("seed-exam-attempts")
def seed_exam_attempts_command(
    outcomes: Annotated[Path, typer.Option("--outcomes", help="JSON file with per-question exam outcomes.")],
    exam_date: Annotated[
        str | None,
        typer.Option("--exam-date", help="Exam date (YYYY-MM-DD). Overrides the outcomes file's exam_date."),
    ] = None,
    subject: Annotated[str | None, typer.Option("--subject", help="Only match exam items in this subject.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Report what would be seeded without writing.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Seed backdated exam_evidence attempts from a past exam's outcomes.

    Matches outcomes against practice items tagged exam_q:<n> (created by
    `learnloop ingest-exam`), records one discounted attempt per question dated
    at the exam date, then rebuilds derived state so mastery/FSRS replay in
    time order.
    """

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    try:
        payload = _load_mapping_file(outcomes, label="outcomes file")
        parsed = parse_exam_outcomes(payload, exam_date_override=exam_date)
        result = seed_exam_attempts(
            loaded,
            repository,
            outcomes=parsed,
            subject=subject,
            dry_run=dry_run,
        )
    except (ExamSeedingError, ValueError, OSError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "exam_seeding_failed", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "exam_seeding": result.as_dict()}))
        return
    for entry in result.entries:
        if entry.status in {"seeded", "would_seed"}:
            verb = "Seeded" if entry.status == "seeded" else "Would seed"
            typer.echo(
                f"{verb} q{entry.question} -> {entry.practice_item_id} "
                f"(score={entry.score:.2f}, rubric_score={entry.rubric_score})"
            )
        elif entry.status == "skipped_existing":
            typer.echo(f"Skipped q{entry.question} -> {entry.practice_item_id}: {entry.detail}")
        else:
            typer.echo(f"Warning q{entry.question} -> {entry.practice_item_id}: {entry.detail}")
    summary = (
        f"exam_date={result.exam_date} seeded={result.seeded_count} "
        f"skipped={result.skipped_existing_count} no_outcome={result.no_outcome_count}"
    )
    if dry_run:
        summary = f"[dry-run] {summary}"
    elif result.rebuild is not None:
        summary += (
            f" rebuilt_learning_objects={result.rebuild.rebuilt_learning_objects}"
            f" replayed_attempts={result.rebuild.replayed_attempts}"
        )
    typer.echo(summary)


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


@app.command("facet-candidates")
def facet_candidates_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = True,
) -> None:
    """Harvest facet candidates and lexical review pairs (knowledge-model §3.3).

    Similarity is review-only and never merges; no similarity artifact is
    persisted as identity.
    """

    from learnloop.services.facet_candidates import harvest_facet_candidates

    vault_root = _root(vault)
    loaded = _load_vault_or_exit(vault_root, json_output=json_output)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    result = harvest_facet_candidates(loaded, repository)
    if json_output:
        typer.echo(_dump(result))
        return
    typer.echo(f"{len(result['candidates'])} candidate(s), {len(result['review_pairs'])} review pair(s).")
    for pair in result["review_pairs"]:
        typer.echo(f"  review: {pair['left']} ~ {pair['right']} ({pair['similarity']})")


@app.command("merge-concepts")
def merge_concepts_command(
    canonical_id: Annotated[str, typer.Argument(help="Concept id to keep.")],
    duplicate_id: Annotated[str, typer.Argument(help="Concept id to merge into the canonical concept.")],
    add_alias: Annotated[
        bool,
        typer.Option("--alias/--no-alias", help="Add duplicate id, title, and aliases to the canonical concept."),
    ] = True,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show planned file changes without writing.")] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Allow merging concepts with conflicting type/description metadata."),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    try:
        result = merge_concepts(
            _root(vault),
            canonical_id,
            duplicate_id,
            add_alias=add_alias,
            dry_run=dry_run,
            force=force,
        )
    except ConceptMergeError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "concept_merge_failed", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "merge": result.as_dict()}))
        return
    prefix = "Would merge" if dry_run else "Merged"
    typer.echo(f"{prefix} {duplicate_id} into {canonical_id}.")
    if result.changed_files:
        typer.echo("Changed files:")
        for path in result.changed_files:
            typer.echo(f"  {path}")
    if result.change_batch_id:
        typer.echo(f"Change batch: {result.change_batch_id}")


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


def _wrap_text(text: str, *, indent: str = "  ") -> list[str]:
    lines: list[str] = []
    for paragraph in str(text).splitlines():
        if not paragraph.strip():
            continue
        lines.extend(
            textwrap.wrap(paragraph.strip(), width=_WRAP_WIDTH, initial_indent=indent, subsequent_indent=indent)
        )
    return lines


def _dim(text: object) -> str:
    return typer.style(str(text), fg=typer.colors.BRIGHT_BLACK)


def _echo_section(title: str) -> None:
    typer.echo("")
    typer.secho(f"── {title} " + "─" * max(2, _WRAP_WIDTH - len(title) - 4), fg=typer.colors.YELLOW)


def _echo_kv(label: str, value: object) -> None:
    if value is None or value == "" or value == [] or value == {}:
        return
    if isinstance(value, float):
        value = f"{value:.3f}"
    typer.echo(f"  {_dim(label + ':')} {value}")


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
    elif ":t=" in identifier and identifier.split(":t=", 1)[0] in loaded.notes:
        entity_type = "note"
        payload = loaded.notes[identifier.split(":t=", 1)[0]]
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
    elif entity_type == "practice_attempt" and isinstance(payload, dict):
        _echo_practice_attempt(identifier, payload, repository)
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
def misconceptions(
    all_errors: Annotated[bool, typer.Option("--all-errors", help="Include all active error events, not only misconceptions.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """List active error events, defaulting to misconceptions only."""

    loaded = load_vault(_root(vault))
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    events = repository.active_error_events()
    if not all_errors:
        events = [event for event in events if event.is_misconception]
    rows = [
        {
            "id": event.id,
            "error_type": event.error_type,
            "title": (error_type.title if (error_type := loaded.error_types.get(event.error_type)) else None),
            "is_misconception": event.is_misconception,
            "severity": event.severity,
            "learning_object_id": event.learning_object_id,
            "created_at": event.created_at,
        }
        for event in events
    ]
    if json_output:
        typer.echo(_dump({"version": 1, "misconceptions": rows}))
        return
    if not rows:
        typer.echo("No active misconceptions." if not all_errors else "No active error events.")
        return
    for row in rows:
        kind = "misconception" if row["is_misconception"] else "error"
        typer.echo(
            f"{row['id']} {row['error_type']} ({kind}) severity={row['severity']:.2f} "
            f"lo={row['learning_object_id']} created={row['created_at']}"
        )
        if row["title"]:
            typer.echo(f"  - {row['title']}")


@app.command("resolve-error")
def resolve_error(
    event_id: Annotated[str, typer.Argument(help="Error event SQL id.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Mark an active error event as resolved."""

    repository = _repository(_root(vault))
    resolved = repository.resolve_error_event(event_id)
    if json_output:
        typer.echo(_dump({"version": 1, "event_id": event_id, "resolved": resolved}))
    elif resolved:
        typer.echo(f"Resolved error event {event_id}.")
    else:
        typer.echo(f"Error event {event_id} not found or already resolved.", err=True)
    if not resolved:
        raise typer.Exit(code=1)


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
    try:
        count = reject_items(_root(vault), patch_id, _split_items(items))
    except PatchApplicationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
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
    focus_concepts: Annotated[str | None, typer.Option("--focus-concepts", help="Comma-separated concept ids to concentrate the proposal on.")] = None,
    focus_facets: Annotated[str | None, typer.Option("--focus-facets", help="Comma-separated evidence facet ids to concentrate the proposal on.")] = None,
    from_goal: Annotated[str | None, typer.Option("--from-goal", help="Active goal id whose concept anchors seed the focus concepts.")] = None,
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
        resolved_focus_concepts, resolved_focus_facets = _resolve_focus(
            loaded,
            focus_concepts=focus_concepts,
            focus_facets=focus_facets,
            from_goal=from_goal,
            json_output=json_output,
        )
        context = build_authoring_context(
            loaded,
            subjects=_split_items(subjects),
            note_ids=_split_items(notes),
            instructions=instructions,
            focus_concepts=resolved_focus_concepts,
            focus_facets=resolved_focus_facets,
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
        resolved_focus_concepts, resolved_focus_facets = _resolve_focus(
            loaded,
            focus_concepts=focus_concepts,
            focus_facets=focus_facets,
            from_goal=from_goal,
            json_output=json_output,
        )
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
                focus_concepts=resolved_focus_concepts,
                focus_facets=resolved_focus_facets,
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
    focus_concepts: Annotated[str | None, typer.Option("--focus-concepts", help="Comma-separated concept ids; restrict targets to LOs on these concepts.")] = None,
    focus_facets: Annotated[str | None, typer.Option("--focus-facets", help="Comma-separated evidence facet ids for new items to target.")] = None,
    from_goal: Annotated[str | None, typer.Option("--from-goal", help="Active goal id whose concept anchors seed the focus concepts.")] = None,
    los: Annotated[str | None, typer.Option("--los", help="Comma-separated learning-object ids to target; bypasses the item-count deficit gate but keeps the completed-probe gate.")] = None,
    mode_mix: Annotated[str | None, typer.Option("--mode-mix", help="Hard per-LO practice-mode counts, e.g. 'teach_back=2,short_answer=3'.")] = None,
    instructions: Annotated[str | None, typer.Option("--instructions", help="Extra generation instructions.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for practice generation.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show targets without calling Codex.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    subject_ids = _split_items(subjects)
    try:
        parsed_mode_mix = _parse_mode_mix(mode_mix)
    except ValueError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "invalid_mode_mix", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    learning_object_ids = _split_items(los)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    resolved_focus_concepts, resolved_focus_facets = _resolve_focus(
        loaded,
        focus_concepts=focus_concepts,
        focus_facets=focus_facets,
        from_goal=from_goal,
        json_output=json_output,
    )
    try:
        plan = build_practice_expansion_plan(
            loaded,
            repository,
            subjects=subject_ids,
            target_items_per_lo=target_items_per_lo,
            max_new_per_lo=max_new_per_lo,
            max_los=max_los,
            focus_concepts=resolved_focus_concepts,
            learning_object_ids=learning_object_ids,
            mode_mix=parsed_mode_mix,
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
            focus_concepts=resolved_focus_concepts,
            focus_facets=resolved_focus_facets,
            extra_instructions=instructions,
            codex_revision=getattr(runtime, "actual_revision", None),
            learning_object_ids=learning_object_ids,
            mode_mix=parsed_mode_mix,
        )
    except Exception as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "codex_failed" if provider_name == "codex" else "ai_failed", "message": str(exc), "plan": plan.as_dict()}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if result.mode_mix_violations:
        if json_output:
            typer.echo(
                _dump(
                    {
                        "version": 1,
                        "error": "mode_mix_violation",
                        "proposal_id": result.patch_id,
                        "mode_mix_violations": result.mode_mix_violations,
                        "mode_mix_warnings": result.mode_mix_warnings,
                        "plan": result.plan.as_dict(),
                    }
                )
            )
        else:
            typer.echo(f"Persisted practice-generation proposal {result.patch_id}, but the mode mix was not honored:", err=True)
            for violation in result.mode_mix_violations:
                typer.secho(f"- {violation}", fg=typer.colors.RED, err=True)
            for warning in result.mode_mix_warnings:
                typer.secho(f"- warning: {warning}", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(
            _dump(
                {
                    "version": 1,
                    "proposal_id": result.patch_id,
                    "plan": result.plan.as_dict(),
                    "mode_mix_warnings": result.mode_mix_warnings,
                }
            )
        )
    else:
        typer.echo(f"Persisted practice-generation proposal {result.patch_id}.")
        for warning in result.mode_mix_warnings:
            typer.secho(f"Mode-mix warning: {warning}", fg=typer.colors.YELLOW, err=True)
        _echo_practice_generation_plan(result.plan)


@app.command("populate-goal")
def populate_goal(
    goal_id: Annotated[str, typer.Argument(help="Active goal id to populate with Practice Items.")],
    target_items_per_lo: Annotated[int, typer.Option("--target-items-per-lo", min=1, help="Desired practicable (non-exam-reserved) Practice Item count per scope LO.")] = 5,
    max_new_per_lo: Annotated[int, typer.Option("--max-new-per-lo", min=1, help="Maximum new Practice Items to ask for per LO.")] = 3,
    instructions: Annotated[str | None, typer.Option("--instructions", help="Extra generation instructions.")] = None,
    ai_provider: Annotated[str | None, typer.Option("--ai-provider", help="AI provider profile to use for practice generation.")] = None,
    review: Annotated[bool, typer.Option("--review", help="Leave the proposal pending review instead of auto-accepting.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show targets without calling the AI provider.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Generate Practice Items covering an active goal's scope.

    Unlike ``generate-practice``, the completed-probe gate is waived and items
    reserved for the goal's held-out exam do not count as existing supply, so a
    freshly created goal (whose exam pool may have quarantined most of its
    items) becomes practicable in one shot. Auto-accepts the proposal unless
    ``--review`` is passed.
    """

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)

    def _fail(error: str, message: str, **extra: object) -> None:
        if json_output:
            typer.echo(_dump({"version": 1, "error": error, "message": message, **extra}))
        else:
            typer.echo(message, err=True)
        raise typer.Exit(code=1)

    goal = next((candidate for candidate in loaded.goals if candidate.id == goal_id), None)
    if goal is None or goal.status != "active":
        reason = "not found" if goal is None else f"not active (status={goal.status})"
        _fail("invalid_goal", f"Goal {goal_id} is {reason}.", goal_id=goal_id)
    try:
        plan, at_risk_facets = build_goal_practice_plan(
            loaded,
            repository,
            goal,
            target_items_per_lo=target_items_per_lo,
            max_new_per_lo=max_new_per_lo,
        )
    except PracticeExpansionError as exc:
        _fail("invalid_generation_request", str(exc))
    if dry_run:
        if json_output:
            typer.echo(_dump({"version": 1, "plan": plan.as_dict(), "at_risk_facets": at_risk_facets}))
        else:
            _echo_practice_generation_plan(plan)
            if at_risk_facets:
                typer.echo(f"At-risk facets in focus: {', '.join(at_risk_facets)}")
        return
    if not plan.targets:
        _fail(
            "no_targets",
            f"Goal {goal_id}'s learning objects already have enough practicable items.",
            plan=plan.as_dict(),
        )
    provider_name, runtime, client = _ready_provider_for_task(vault_root, loaded.config, "authoring", ai_provider)
    if not runtime.ready:
        runtime_label = "Codex runtime" if provider_name == "codex" else "AI provider"
        _fail(runtime.status, runtime.message or f"{runtime_label} is {runtime.status}.", plan=plan.as_dict())
    try:
        result = generate_goal_practice_proposal(
            vault_root,
            client,
            goal_id=goal_id,
            target_items_per_lo=target_items_per_lo,
            max_new_per_lo=max_new_per_lo,
            extra_instructions=instructions,
            codex_revision=getattr(runtime, "actual_revision", None),
        )
    except Exception as exc:
        _fail(
            "codex_failed" if provider_name == "codex" else "ai_failed",
            str(exc),
            plan=plan.as_dict(),
        )
    applied_count = 0
    if not review:
        try:
            apply_result = accept_items(vault_root, result.patch_id)
            applied_count = apply_result.applied_count
        except PatchApplicationError as exc:
            _fail("accept_failed", str(exc), proposal_id=result.patch_id, plan=result.plan.as_dict())
    if json_output:
        typer.echo(
            _dump(
                {
                    "version": 1,
                    "goal_id": goal_id,
                    "proposal_id": result.patch_id,
                    "accepted": not review,
                    "applied_count": applied_count,
                    "plan": result.plan.as_dict(),
                    "at_risk_facets": at_risk_facets,
                }
            )
        )
    else:
        if review:
            typer.echo(f"Persisted goal-population proposal {result.patch_id}; review it with `proposals`.")
        else:
            typer.echo(f"Populated goal {goal_id}: accepted proposal {result.patch_id} ({applied_count} item(s)).")
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


@app.command("misconception-gate-backfill")
def misconception_gate_backfill(
    force: Annotated[bool, typer.Option("--force", help="Re-run and overwrite existing discrimination rows.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Backfill sim discrimination rows for keyed (item, misconception) pairs (spec §6).

    Deterministic grader only (no AI provider). By default respects existing rows;
    ``--force`` re-runs every pair.
    """

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    results = backfill_discrimination_rows(loaded, repository, force=force)

    backfilled: list[Any] = []
    skipped_existing: list[Any] = []
    skipped_unregistered: list[Any] = []
    for result in results:
        if BACKFILL_SKIPPED_UNREGISTERED in result.reasons:
            skipped_unregistered.append(result)
        elif BACKFILL_SKIPPED_EXISTING in result.reasons:
            skipped_existing.append(result)
        else:
            backfilled.append(result)

    summary = {
        "backfilled": len(backfilled),
        "skipped_existing": len(skipped_existing),
        "skipped_unregistered": len(skipped_unregistered),
    }
    if json_output:
        typer.echo(
            _dump(
                {
                    "version": 1,
                    "backfilled": [r.as_dict() for r in backfilled],
                    "skipped_existing": [r.as_dict() for r in skipped_existing],
                    "skipped_unregistered": [r.as_dict() for r in skipped_unregistered],
                    "summary": summary,
                }
            )
        )
        return
    if not results:
        typer.echo("No keyed (item, misconception) pairs found.")
        return
    for result in backfilled:
        verdict = "accepted" if result.accepted else "rejected"
        typer.echo(
            f"{result.practice_item_id} / {result.misconception_id}: {verdict} "
            f"[sens_lb={result.sensitivity_lb():.2f} spec_lb={result.specificity_lb():.2f}]"
        )
    for result in skipped_existing:
        typer.echo(
            f"{result.practice_item_id} / {result.misconception_id}: skipped (existing row) "
            f"[sens_lb={result.sensitivity_lb():.2f} spec_lb={result.specificity_lb():.2f}]"
        )
    for result in skipped_unregistered:
        typer.echo(
            f"{result.practice_item_id} / {result.misconception_id}: skipped (misconception not registered)"
        )
    typer.echo(
        f"Backfilled {summary['backfilled']}, "
        f"skipped {summary['skipped_existing']} existing, "
        f"{summary['skipped_unregistered']} unregistered."
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
        ai_client=client if runtime.ready else None,
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


@app.command("eval")
def eval_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    section: Annotated[
        str, typer.Option("--section", help="predictions|gates|retention|propensity|all")
    ] = "all",
    bins: Annotated[int, typer.Option("--bins", help="Calibration bin count.")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Calibration report over logged decisions (read-only)."""

    from learnloop.services.evaluation import build_eval_report

    valid = {"predictions", "gates", "retention", "propensity"}
    sections = valid if section == "all" else {part.strip() for part in section.split(",") if part.strip()}
    unknown = sections - valid
    if unknown:
        typer.echo(f"Unknown section(s): {', '.join(sorted(unknown))}. Valid: {', '.join(sorted(valid))}.", err=True)
        raise typer.Exit(code=2)
    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    report = build_eval_report(loaded, repository, sections=sections, bins=bins)
    if json_output:
        typer.echo(_dump({"version": 1, "eval": report.as_dict()}))
        return
    typer.echo(report.format_text())


exam_app = typer.Typer(no_args_is_help=True, help="Held-out practice-exam pool, session, and calibration.")
app.add_typer(exam_app, name="exam")


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


def _resolve_self_grade(loaded, item, points: dict[str, float], *, confidence: int, fatal_errors, error_type):
    """Resolve a CLI self-grade into a ResolvedGrade (no mastery writes).

    Mirrors ``complete_self_graded_attempt`` so ``exam answer`` reuses the same
    self-grade rubric input as ``learnloop attempt``, but hands the resolved
    grade to the exam session instead of applying it immediately.
    """

    rubric = resolved_rubric(loaded, item)
    criterion_points = {criterion.id: float(points.get(criterion.id, 0.0)) for criterion in rubric.criteria}
    fatal = list(fatal_errors or [])
    rubric_score = _rubric_score(rubric, criterion_points, fatal)
    grader_confidence = confidence_to_grader_confidence(confidence)
    attributions = []
    if error_type:
        error = loaded.error_types.get(error_type)
        attributions.append(
            GradeAttribution(
                error_type=error_type,
                severity=error.severity_default if error is not None else 0.5,
                is_misconception=error.is_misconception if error is not None else False,
            )
        )
    evidence_rows = [
        {
            "id": new_ulid(),
            "criterion_id": criterion.id,
            "points_awarded": criterion_points[criterion.id],
            "evidence": f"Exam self-grade awarded {criterion_points[criterion.id]:g}/{criterion.points:g}.",
            "notes": None,
            "local_grader_id": "self",
            "grader_tier": 1,
            "learner_confidence": "hedged" if confidence <= 2 else "confident",
            "created_at": utc_now_iso(None),
        }
        for criterion in rubric.criteria
    ]
    return ResolvedGrade(
        rubric_score=rubric_score,
        criterion_points=criterion_points,
        evidence_rows=evidence_rows,
        error_attributions=attributions,
        grader_confidence=grader_confidence,
        confidence=confidence,
        manual_review_reason="low_self_confidence" if grader_confidence < 0.4 else None,
        fatal_errors=fatal,
    )


@exam_app.command("reserve")
def exam_reserve_command(
    goal: Annotated[str, typer.Option("--goal", help="Goal id to reserve a held-out exam pool for.")],
    item_count: Annotated[int | None, typer.Option("--item-count", help="Override the goal's exam item_count.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    goal_obj = _goal_or_exit(loaded, goal, json_output=json_output)
    report = reserve_exam_pool(loaded, repository, goal_obj, item_count=item_count)
    if json_output:
        typer.echo(_dump({"version": 1, "exam_pool": report.as_dict()}))
        return
    typer.echo(
        f"Reserved {len(report.reserved_item_ids)} items for {goal} "
        f"(already_reserved={report.already_reserved}); "
        f"covered {len(report.covered_facets)} facets, uncovered {report.uncovered_facets}."
    )


@exam_app.command("start")
def exam_start_command(
    goal: Annotated[str, typer.Option("--goal", help="Goal id to start a held-out exam for.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    _goal_or_exit(loaded, goal, json_output=json_output)
    try:
        session = start_exam(loaded, repository, goal)
    except ExamSessionError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "exam_session_error", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "exam_session": session}))
        return
    typer.echo(
        f"Exam session {session['session_id']} ({session['status']}) with "
        f"{len(session['item_order'])} items; already_started={session['already_started']}."
    )


@exam_app.command("answer")
def exam_answer_command(
    session: Annotated[str, typer.Option("--session", help="Exam session id.")],
    practice_item_id: Annotated[str, typer.Argument(help="Practice item id being answered.")],
    answer: Annotated[str | None, typer.Option("--answer", help="Learner answer markdown.")] = None,
    criterion_points: Annotated[str | None, typer.Option("--criterion-points", help="Comma-separated criterion=points pairs.")] = None,
    fatal_errors: Annotated[str | None, typer.Option("--fatal-errors", help="Comma-separated fatal rubric error ids.")] = None,
    confidence: Annotated[int, typer.Option("--confidence", min=1, max=5, help="Self-grade confidence 1..5.")] = 3,
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
    answer_text = answer if answer is not None else typer.prompt("Answer", default="")
    points = _parse_points(criterion_points)
    rubric = loaded.rubric_for_item(item)
    if not points and rubric is not None:
        for criterion in rubric.criteria:
            raw = typer.prompt(f"{criterion.id} points", default="0")
            try:
                points[criterion.id] = float(raw)
            except ValueError:
                typer.echo(f"{criterion.id} points must be numeric.", err=True)
                raise typer.Exit(code=1)
    try:
        grade = _resolve_self_grade(
            loaded, item, points, confidence=confidence, fatal_errors=_split_items(fatal_errors), error_type=error_type
        )
        result = record_exam_answer(
            loaded, repository, session, practice_item_id, answer_md=answer_text, resolved_grade=grade
        )
    except (ExamSessionError, ValueError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "exam_answer_error", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "exam_answer": result}))
        return
    typer.echo(
        f"Recorded exam answer for {practice_item_id}: score={result['rubric_score']} "
        f"correctness={result['correctness']:.2f}"
    )


@exam_app.command("finish")
def exam_finish_command(
    session: Annotated[str, typer.Option("--session", help="Exam session id to finish.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    try:
        report = finish_exam(loaded, repository, session)
    except ExamSessionError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "exam_session_error", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    if json_output:
        typer.echo(_dump({"version": 1, "exam_report": report}))
        return
    typer.echo(
        f"Exam {session} finished: answered={report['answered_count']}/{report['item_count']} "
        f"overall_score={report['overall_score']} brier={report['brier']}"
    )


@app.command("exam-calibration")
def exam_calibration_command(
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Report exam prediction/outcome calibration (Brier, log loss, reliability bins)."""

    vault_root = _root(vault)
    loaded = load_vault(vault_root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    sync_vault_state(loaded, repository)
    report = exam_calibration_report(loaded, repository)
    if json_output:
        typer.echo(_dump({"version": 1, "exam_calibration": report}))
        return
    items = report["items"]
    facets = report["facets"]
    typer.echo(
        f"Item predictions: n={items['n']} brier={items['brier']} log_loss={items['log_loss']}"
    )
    typer.echo(f"Facet projections: n={facets['n']} brier={facets['brier']}")


fit_app = typer.Typer(no_args_is_help=True, help="Fit algorithm parameters from logged attempts.")
app.add_typer(fit_app, name="fit")


@fit_app.command("fsrs")
def fit_fsrs_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Fit and report without persisting.")] = False,
) -> None:
    """Fit FSRS weights to this learner's own review log (pure Python)."""

    from learnloop.services.fitted_params import FSRS_WEIGHTS_SCOPE
    from learnloop.services.fsrs import FSRS6_DEFAULT_WEIGHTS
    from learnloop.services.fsrs_fitting import FIT_INDICES, FsrsFittingError, fit_fsrs_weights
    from learnloop.services.review_log import reconstruct_review_log

    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    review_log = reconstruct_review_log(loaded, repository)
    try:
        result = fit_fsrs_weights(review_log, config=loaded.config.fitting.fsrs)
    except FsrsFittingError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "insufficient_reviews", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    persisted_id: str | None = None
    if result.improved and not dry_run:
        persisted_id = repository.insert_fitted_parameters(
            scope=FSRS_WEIGHTS_SCOPE,
            params={
                "weights": list(result.weights),
                "fitted_indices": list(result.fitted_indices),
                "pinned_from": "fsrs6_defaults",
            },
            algorithm_version=loaded.config.algorithms.algorithm_version,
            training_rows_count=result.predicted_count,
            training_data_through=result.data_through,
            metrics={
                "log_loss_default": result.log_loss_default,
                "log_loss_fitted": result.log_loss_fitted,
                "relative_improvement": result.relative_improvement,
                "iterations": result.iterations,
                "converged": result.converged,
                "fitter": "fsrs_fitting.v1",
            },
        )

    if json_output:
        typer.echo(
            _dump(
                {
                    "version": 1,
                    "fit": result,
                    "persisted_id": persisted_id,
                    "activated": persisted_id is not None,
                }
            )
        )
        return
    typer.echo(
        f"Reviews: {result.review_count} total, {result.predicted_count} usable "
        f"(skipped {review_log.skipped_attempts} attempts missing from vault)."
    )
    typer.echo(
        f"Log-loss: default {result.log_loss_default:.4f} -> fitted {result.log_loss_fitted:.4f} "
        f"({result.relative_improvement:+.1%}, {result.iterations} iterations, converged={result.converged})"
    )
    for index in FIT_INDICES:
        typer.echo(f"  w{index}: {FSRS6_DEFAULT_WEIGHTS[index]:.4f} -> {result.weights[index]:.4f}")
    if persisted_id is not None:
        typer.echo(f"Activated fitted set {persisted_id}.")
    elif result.improved and dry_run:
        typer.echo("Dry run: improved fit not persisted.")
    else:
        typer.echo(
            "Fitted weights do not beat defaults by the configured margin; nothing persisted "
            f"(need >= {loaded.config.fitting.fsrs.min_relative_improvement:.1%} improvement)."
        )


@fit_app.command("gate")
def fit_gate_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Fit and report without persisting.")] = False,
    min_labels: Annotated[int, typer.Option("--min-labels", help="Minimum strong labels (overrides + ratings).")] = 20,
    l2: Annotated[float, typer.Option("--l2")] = 0.1,
    epochs: Annotated[int, typer.Option("--epochs")] = 500,
    learning_rate: Annotated[float, typer.Option("--lr")] = 0.5,
) -> None:
    """Fit follow-up gate weights from manual-override + usefulness labels."""

    from learnloop.services.fitted_params import FOLLOWUP_GATE_SCOPE
    from learnloop.services.gate_fit import GateFitError, assemble_gate_training_set, fit_gate_weights
    from learnloop.services.gate_score import GATE_FEATURE_VERSION

    root = _root(vault)
    loaded = _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    examples = assemble_gate_training_set(repository, loaded.config)
    strong = sum(1 for example in examples if example.label_source != "silent_gate")
    if strong < min_labels:
        message = (
            f"Only {strong} strong gate labels (manual overrides + ratings); "
            f"need at least {min_labels} to fit. Keep using ⇧D and the usefulness rating."
        )
        if json_output:
            typer.echo(_dump({"version": 1, "error": "insufficient_labels", "message": message}))
        else:
            typer.echo(message, err=True)
        raise typer.Exit(code=1)
    try:
        result = fit_gate_weights(examples, l2=l2, epochs=epochs, learning_rate=learning_rate)
    except GateFitError as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "unfittable", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    persisted_id: str | None = None
    if not dry_run:
        persisted_id = repository.insert_fitted_parameters(
            scope=FOLLOWUP_GATE_SCOPE,
            params={
                "weights": result.weights,
                "bias": result.bias,
                "feature_version": GATE_FEATURE_VERSION,
            },
            algorithm_version=loaded.config.algorithms.algorithm_version,
            training_rows_count=result.n_examples,
            metrics={
                "auc": result.auc,
                "accuracy": result.accuracy,
                "log_loss": result.log_loss,
                "n_positive": result.n_positive,
                "n_negative": result.n_negative,
                "label_source_counts": result.label_source_counts,
                "fitter": "gate_fit.v2",
                "feature_version": GATE_FEATURE_VERSION,
            },
        )
    if json_output:
        typer.echo(_dump({"version": 1, "fit": result, "persisted_id": persisted_id}))
        return
    typer.echo(
        f"Labels: {result.n_examples} total ({result.n_positive} positive / {result.n_negative} negative), "
        f"{result.n_strong_labels} strong; sources {result.label_source_counts}"
    )
    typer.echo(f"AUC {result.auc:.3f}  accuracy {result.accuracy:.3f}  log-loss {result.log_loss:.4f}")
    for name, weight in sorted(result.weights.items()):
        typer.echo(f"  {name}: {weight:+.3f}")
    typer.echo(f"  bias: {result.bias:+.3f}")
    if persisted_id is not None:
        typer.echo(f"Activated fitted gate weights {persisted_id} (gate_mode=score uses them immediately).")
    else:
        typer.echo("Dry run: not persisted.")


@fit_app.command("show")
def fit_show_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    scope: Annotated[str | None, typer.Option("--scope", help="Filter by scope.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """List fitted parameter sets (newest first)."""

    root = _root(vault)
    _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    rows = repository.list_fitted_parameters(scope)
    if json_output:
        typer.echo(_dump({"version": 1, "fitted_parameters": rows}))
        return
    if not rows:
        typer.echo("No fitted parameter sets.")
        return
    for row in rows:
        marker = "*" if row["active"] else " "
        metrics = row.get("metrics") or {}
        detail = ", ".join(
            f"{key}={value}" for key, value in sorted(metrics.items()) if isinstance(value, (int, float))
        )
        typer.echo(
            f"{marker} {row['id']}  {row['scope']}  fitted_at={row['fitted_at']}  "
            f"rows={row['training_rows_count']}  {detail}"
        )


@fit_app.command("deactivate")
def fit_deactivate_command(
    scope: Annotated[str, typer.Argument(help="Fitted-parameter scope (e.g. fsrs_weights).")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    fitted_id: Annotated[str | None, typer.Option("--id", help="Deactivate only this set id.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Deactivate the active fitted set for a scope; defaults apply afterwards."""

    root = _root(vault)
    _load_vault_or_exit(root, json_output=json_output)
    repository = _repository(root)
    count = repository.deactivate_fitted_parameters(scope, fitted_id=fitted_id)
    if json_output:
        typer.echo(_dump({"version": 1, "deactivated": count, "scope": scope}))
        return
    typer.echo(f"Deactivated {count} fitted set(s) for scope {scope}; defaults now apply.")


@app.command("probe-coverage")
def probe_coverage_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
) -> None:
    """Hypothesis-contrast / family coverage report (probe redesign §9.5).

    For every decision-relevant hypothesis distinction an episode could
    instantiate, checks that at least two signature-distinct family templates
    can separate it — one direct/minimal and one shifted instrument.
    """

    from learnloop.services.probe_coverage import family_coverage_report

    root = _root(vault)
    loaded = load_vault(root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    report = family_coverage_report(loaded, repository)
    if json_output:
        typer.echo(_dump(report))
        return
    totals = report["totals"]
    typer.echo(
        f"LOs: {totals['learning_objects']} ({totals['learning_objects_with_bindings']} with instrument bindings)"
    )
    typer.echo(
        f"Hypothesis contrasts: {totals['contrasts']} total, "
        f"{totals['contrasts_fully_covered']} fully covered, "
        f"{totals['contrasts_uncovered']} with no separating instrument"
    )
    if totals["integrative_gaps"]:
        typer.echo(f"Integrative/long-form family gaps: {totals['integrative_gaps']} LOs")
    for entry in report["learning_objects"]:
        if not entry["uncovered_contrasts"] and not entry["needs_integrative_family"]:
            continue
        typer.echo(f"- {entry['learning_object_id']}:")
        for pair in entry["uncovered_contrasts"]:
            typer.echo(f"    uncovered: {pair[0]} vs {pair[1]}")
        if entry["needs_integrative_family"]:
            typer.echo("    missing integrative/long-form family")


@app.command("probe-instances")
def probe_instances_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    learning_object_id: Annotated[str | None, typer.Option("--lo", help="Only this Learning Object's pending episode.")] = None,
    seed: Annotated[int, typer.Option("--seed", help="Deterministic generation seed.")] = 0,
    no_llm: Annotated[bool, typer.Option("--no-llm", help="Skip LLM surfaces; use only parametric templates.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON summary.")] = False,
) -> None:
    """Resolve pending diagnostic episodes through instance generation from
    admitted family/card bindings (probe redesign §10). Surfaces come from the
    configured AI provider when available (§9.2) and fall back to the
    parametric templates."""

    from learnloop.ai.routing import provider_for_task
    from learnloop.services.probe_instance_generation import generate_instances_for_episode
    from learnloop_sidecar.handlers.ai_providers import client_for_provider, runtime_for_provider

    root = _root(vault)
    loaded = load_vault(root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    ai_client = None
    if not no_llm and loaded.config.probe.generation.llm_surfaces:
        provider_name = provider_for_task(loaded.config, "authoring").provider_name
        runtime = runtime_for_provider(loaded, provider_name)
        if runtime.ready:
            ai_client = client_for_provider(loaded, provider_name)
    summaries = []
    for lo_id, episode in sorted(repository.open_probe_episodes().items()):
        if episode.status != "pending_items":
            continue
        if learning_object_id is not None and lo_id != learning_object_id:
            continue
        summary = generate_instances_for_episode(
            repository, loaded, episode.id, seed=seed, ai_client=ai_client
        )
        summaries.append(summary.as_dict())
        loaded = load_vault(root)
    if json_output:
        typer.echo(_dump({"version": 1, "episodes": summaries}))
        return
    if not summaries:
        typer.echo("No pending diagnostic episodes to resolve.")
        return
    for summary in summaries:
        generated = summary["generated"]
        typer.echo(
            f"{summary['learning_object_id']}: {len(generated)} instances "
            f"({'unparked' if summary['episode_unparked'] else 'still pending review'})"
        )
        for instance in generated:
            typer.echo(
                f"    {instance['practice_item_id']} [{instance['family_template_id']} "
                f"v{instance['family_template_version']}, {instance['review_status']}, "
                f"{instance.get('generator_id', 'probe_family_parametric')}]"
            )


@app.command("probe-audit")
def probe_audit_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """Probe pilot audit (probe redesign §13, Checkpoint 4): predicted-vs-realized
    EIG, negative realized information, time calibration, cross-surface
    replication, downstream outcomes, regrade agreement, evidence-source
    separation, shadow-policy comparison, and the replay determinism check."""

    from learnloop.services.probe_audit import pilot_report

    root = _root(vault)
    loaded = load_vault(root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    report = pilot_report(loaded, repository)
    _write_or_echo_report(report, json_output=json_output, output=output)
    if json_output and output is None:
        return
    eig = report["eig_calibration"]
    typer.echo(
        f"EIG: {eig['observations']} qualifying observations, "
        f"expected {eig['mean_expected_eig']} vs realized {eig['mean_realized_information']} nats, "
        f"negative-information rate {eig['negative_information_rate']}"
    )
    time_report = report["time_calibration"]
    typer.echo(
        f"Time: {time_report['observations']} observations, "
        f"mean error {time_report['mean_error_seconds']}s "
        f"(abs {time_report['mean_absolute_error_seconds']}s)"
    )
    replication = report["cross_surface_replication"]
    typer.echo(
        f"Cross-surface replication: {replication['replicated']}/"
        f"{replication['episodes_with_cross_surface_pairs']} "
        f"(rate {replication['replication_rate']})"
    )
    downstream = report["downstream_outcomes"]
    typer.echo(
        f"Downstream (proxy): {downstream['episodes_with_before_and_after']} measurable episodes, "
        f"mean success delta {downstream['mean_success_delta']}"
    )
    determinism = report["replay_determinism"]
    failures = len(determinism["failures"])
    typer.echo(
        f"Replay determinism: {determinism['episodes_checked']} episodes checked — "
        + ("OK" if determinism["deterministic"] else f"{failures} FAILURES")
    )


@app.command("graph-identifiability")
def graph_identifiability_command(
    subject: Annotated[str | None, typer.Option("--subject", help="Restrict to one subject id.")] = None,
    schedule_probes: Annotated[bool, typer.Option("--schedule-probes", help="Persist a discriminating probe / coarsen need per finding (§11.3).")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Assessment identifiability doctor (knowledge-model §11.3).

    Analyzes each subject's criterion-by-facet-capability matrix, recipe
    structure, and compositional records for the seven non-identifiability
    warnings, reporting unresolved bundles rather than false facet-specific
    precision. Findings can be turned into discriminating-probe generation needs.
    """

    from learnloop.services.identifiability import graph_identifiability_report

    root = _root(vault)
    loaded = load_vault(root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    report = graph_identifiability_report(
        loaded, repository, subject_id=subject, schedule_probes=schedule_probes
    )
    _write_or_echo_report(report, json_output=json_output, output=output)
    if json_output and output is None:
        return
    totals = report["totals"]
    typer.echo(
        f"Identifiability: {totals['findings']} non-identifiable distinction(s), "
        f"{totals['scheduled_probes']} discriminating probe(s) scheduled."
    )
    for subject_report in report["subjects"]:
        if not subject_report["findings"]:
            continue
        typer.echo(f"  {subject_report['subject_id']}: {subject_report['counts']['findings']} finding(s)")
        for bundle in subject_report["unresolved_bundles"]:
            typer.echo(f"    [check {bundle['check']}] {bundle['message']}")


@app.command("residual-diagnostics")
def residual_diagnostics_command(
    subject: Annotated[str | None, typer.Option("--subject", help="Restrict to one subject id.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Residual-dependence diagnostics (knowledge-model §8.4).

    Report-only, deterministic structure hints from residual dependence between
    facets sharing tasks, systematic combined-task failure, context-specific
    residuals, and indistinguishable response signatures. Never mutates structure.
    """

    from learnloop.services.residual_diagnostics import residual_dependence_report

    root = _root(vault)
    loaded = load_vault(root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    report = residual_dependence_report(loaded, repository, subject_id=subject)
    _write_or_echo_report(report, json_output=json_output, output=output)
    if json_output and output is None:
        return
    typer.echo(
        f"Residual diagnostics: {report['totals']['suggestions']} structure suggestion(s) "
        f"across {report['totals']['facet_pairs']} co-tasked facet pair(s)."
    )
    for suggestion in report["suggestions"]:
        typer.echo(f"  [{suggestion['kind']}] {suggestion['message']}")


@app.command("probe-regrade")
def probe_regrade_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, help="Maximum observations to regrade.")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON summary.")] = False,
) -> None:
    """Re-grade a sample of probe observations and record grader agreement per
    family and grader version (probe redesign §7.6, Checkpoint 4.4).
    Non-destructive: original evidence is never superseded."""

    from learnloop.ai.routing import provider_for_task
    from learnloop.services.probe_audit import grading_confusion_report, run_probe_regrade_checks
    from learnloop_sidecar.handlers.ai_providers import client_for_provider, runtime_for_provider

    root = _root(vault)
    loaded = load_vault(root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    provider_name = provider_for_task(loaded.config, "grading").provider_name
    runtime = runtime_for_provider(loaded, provider_name)
    client = client_for_provider(loaded, provider_name) if runtime.ready else None
    if client is None:
        typer.echo(f"Grading provider {provider_name} is unavailable; cannot regrade.")
        raise typer.Exit(code=1)
    summary = run_probe_regrade_checks(loaded, repository, client, limit=limit)
    report = grading_confusion_report(repository)
    if json_output:
        typer.echo(_dump({"version": 1, "run": summary, "confusion": report}))
        return
    typer.echo(
        f"Regraded {summary['recorded']}/{summary['attempted']} sampled observations "
        f"({summary['failed']} failed)."
    )
    for key, scope in report["scopes"].items():
        typer.echo(f"- {key}: agreement {scope['agreement_rate']} over {scope['checks']} checks")


@app.command("taxonomy-regrade-check")
def taxonomy_regrade_check_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, help="Maximum attempts to regrade.")] = 20,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON report.")] = False,
) -> None:
    """Non-destructive mechanism-taxonomy regrade check (knowledge-model §10.1/§16).

    Re-grades a sample of graded attempts under the current GRADING_PROMPT_VERSION
    and reports whether any error-type attribution regresses when compared through
    the §10.1 legacy map. Writes no belief state. Exits non-zero on a regression."""

    from learnloop.ai.routing import provider_for_task
    from learnloop.services.taxonomy_regrade import run_taxonomy_regrade_checks
    from learnloop_sidecar.handlers.ai_providers import client_for_provider, runtime_for_provider

    root = _root(vault)
    loaded = load_vault(root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    provider_name = provider_for_task(loaded.config, "grading").provider_name
    runtime = runtime_for_provider(loaded, provider_name)
    client = client_for_provider(loaded, provider_name) if runtime.ready else None
    if client is None:
        typer.echo(f"Grading provider {provider_name} is unavailable; cannot regrade.")
        raise typer.Exit(code=1)
    report = run_taxonomy_regrade_checks(loaded, repository, client, limit=limit)
    if json_output:
        typer.echo(_dump({"version": 1, "report": report}))
    else:
        typer.echo(
            f"Taxonomy regrade check under {report['prompt_version']}: "
            f"checked {report['checked']}/{report['attempted']} attempts, "
            f"{report['regression_count']} regressions ({report['failed']} failed)."
        )
        for regression in report["regressions"]:
            typer.echo(
                f"- {regression['attempt_id']}: dropped "
                f"{', '.join(regression['dropped_mechanisms'])}"
            )
    if not report["no_regressions"]:
        raise typer.Exit(code=1)


@app.command("probe-families")
def probe_families_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    promote: Annotated[str | None, typer.Option("--promote", help="Promote family:version to trusted (gates must recommend it unless --force).")] = None,
    retire: Annotated[str | None, typer.Option("--retire", help="Retire family:version.")] = None,
    revise: Annotated[str | None, typer.Option("--revise", help="Create the next draft version of a family id.")] = None,
    force: Annotated[bool, typer.Option("--force", help="Apply --promote even when the metric gates do not recommend it.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON overview.")] = False,
) -> None:
    """Family-version lifecycle (probe redesign §9.7, Checkpoint 4.7):
    metric-gated trusted/revise/retire transitions with a persisted audit trail.
    Without flags, prints every family version's status and recommendation."""

    from learnloop.services.probe_lifecycle import (
        LifecycleTransitionError,
        apply_family_lifecycle_transition,
        evaluate_family_lifecycle,
        family_lifecycle_overview,
        revise_family_version,
    )

    def parse_ref(ref: str) -> tuple[str, int]:
        family_id, _, version = ref.partition(":")
        if not family_id or not version.isdigit():
            raise typer.BadParameter(f"expected family:version, got {ref!r}")
        return family_id, int(version)

    root = _root(vault)
    loaded = load_vault(root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)

    try:
        if promote is not None:
            family_id, version = parse_ref(promote)
            assessment = evaluate_family_lifecycle(loaded, repository, family_id, version)
            if assessment.recommendation != "promote_to_trusted" and not force:
                typer.echo(
                    f"Refusing to promote {family_id} v{version}: recommendation is "
                    f"{assessment.recommendation} ({'; '.join(assessment.reasons)}). Use --force to override."
                )
                raise typer.Exit(code=1)
            apply_family_lifecycle_transition(
                repository,
                family_id=family_id,
                version=version,
                to_status="trusted",
                reason={**assessment.as_dict(), "forced": force},
            )
            typer.echo(f"Promoted {family_id} v{version} to trusted.")
            return
        if retire is not None:
            family_id, version = parse_ref(retire)
            assessment = evaluate_family_lifecycle(loaded, repository, family_id, version)
            apply_family_lifecycle_transition(
                repository,
                family_id=family_id,
                version=version,
                to_status="retired",
                reason=assessment.as_dict(),
            )
            typer.echo(f"Retired {family_id} v{version}. Historical observations replay unchanged.")
            return
        if revise is not None:
            new_version = revise_family_version(repository, revise)
            typer.echo(f"Created {revise} v{new_version} as draft.")
            return
    except LifecycleTransitionError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1)

    assessments = family_lifecycle_overview(loaded, repository)
    if json_output:
        typer.echo(_dump({"version": 1, "families": [a.as_dict() for a in assessments]}))
        return
    if not assessments:
        typer.echo("No probe family versions stored.")
        return
    for assessment in assessments:
        metrics = assessment.metrics
        typer.echo(
            f"{assessment.family_id} v{assessment.version} [{assessment.status}] -> "
            f"{assessment.recommendation} "
            f"(real n={metrics.real_sample_size}, obs={metrics.eligible_observations}, "
            f"neg-info={metrics.negative_information_rate}, "
            f"regrade={metrics.regrade_agreement} over {metrics.regrade_checks})"
        )
        for reason in assessment.reasons:
            typer.echo(f"    {reason}")


@app.command("probe-gate")
def probe_gate_command(
    learning_object_id: Annotated[str, typer.Argument(help="Learning Object whose family/card bindings to gate.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    family: Annotated[str | None, typer.Option("--family", help="Only this family template id.")] = None,
    trials: Annotated[int, typer.Option("--trials", min=1, max=10, help="Planted trials per hypothesis.")] = 3,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the JSON results.")] = False,
) -> None:
    """Run the §9.6 family admission gate with LLM planted-trial traces for one
    Learning Object's applicable family/card bindings. Outcomes are recorded
    under evidence_source='synthetic_gate' only — structural and simulation
    validity, never real-learner calibration."""

    from learnloop.ai.routing import provider_for_task
    from learnloop.services.probe_instance_generation import (
        applicable_families,
        run_llm_family_gate,
    )
    from learnloop_sidecar.handlers.ai_providers import client_for_provider, runtime_for_provider

    root = _root(vault)
    loaded = load_vault(root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    learning_object = loaded.learning_objects.get(learning_object_id)
    if learning_object is None:
        typer.echo(f"Unknown Learning Object {learning_object_id}.")
        raise typer.Exit(code=1)
    provider_name = provider_for_task(loaded.config, "authoring").provider_name
    runtime = runtime_for_provider(loaded, provider_name)
    client = client_for_provider(loaded, provider_name) if runtime.ready else None
    if client is None:
        typer.echo(f"AI provider {provider_name} is unavailable; the gate needs planted trials.")
        raise typer.Exit(code=1)

    results: list[dict[str, Any]] = []
    for template in applicable_families(loaded, learning_object, repository):
        if family is not None and template.id != family:
            continue
        gate = run_llm_family_gate(
            loaded, repository, learning_object_id, template, client, trials_per_hypothesis=trials
        )
        if gate is None:
            results.append({"family_template_id": template.id, "version": template.version, "ran": False})
            continue
        results.append(
            {
                "family_template_id": template.id,
                "version": template.version,
                "ran": True,
                "accepted": gate.accepted,
                "reasons": gate.reasons,
                "reverse_match_accuracy": gate.reverse_match_accuracy,
            }
        )
    if json_output:
        typer.echo(_dump({"version": 1, "learning_object_id": learning_object_id, "families": results}))
        return
    if not results:
        typer.echo("No applicable family templates for this Learning Object.")
        return
    for entry in results:
        if not entry["ran"]:
            typer.echo(f"{entry['family_template_id']} v{entry['version']}: skipped (cannot bind or no trials)")
            continue
        verdict = "ACCEPTED" if entry["accepted"] else "REJECTED"
        typer.echo(f"{entry['family_template_id']} v{entry['version']}: {verdict}")
        for slot, acc in sorted(entry["reverse_match_accuracy"].items()):
            typer.echo(f"    reverse-match {slot}: {acc:.2f}")
        for reason in entry["reasons"]:
            typer.echo(f"    {reason}")


sim_app = typer.Typer(
    no_args_is_help=True,
    help="Synthetic-student simulation harness and config sensitivity sweeps.",
)
app.add_typer(sim_app, name="sim")


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


@sim_app.command("probe-validation")
def sim_probe_validation_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root (copied per run, never written).")] = None,
    seeds: Annotated[int, typer.Option("--seeds", min=1, help="Runs per planted type.")] = 5,
    planted: Annotated[str | None, typer.Option("--planted", help="Comma-separated planted types (default: all).")] = None,
    learning_object_id: Annotated[str | None, typer.Option("--lo", help="Target Learning Object (default: first with an open episode).")] = None,
    label_threshold: Annotated[float, typer.Option("--label-threshold", help="Per-type classification accuracy gate.")] = 0.6,
    action_threshold: Annotated[float, typer.Option("--action-threshold", help="Per-type instructional-action accuracy gate.")] = 0.6,
    sets: Annotated[list[str] | None, typer.Option("--set", help="Config override param.path=value (repeatable).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """Checkpoint-3 episode validation against planted latent hypothesis types.

    Drives the real selection/presentation/observation/completion loop against
    planted `surface_only`, `confuses_with`, `schema_without_transfer`,
    `unfamiliar`, and `robust_initial_grasp` students, and gates on per-type
    classification and instructional-action accuracy (the Checkpoint-4 entry
    gate of spec_probe_eig_redesign.md).
    """

    import tempfile

    from learnloop.sim.diagnostic_validation import PLANTED_TYPES, run_probe_validation

    source_root = _root(vault)
    planted_types = (
        tuple(part.strip() for part in planted.split(",") if part.strip())
        if planted
        else PLANTED_TYPES
    )
    workdir = Path(tempfile.mkdtemp(prefix="learnloop-probe-validation-"))
    report = run_probe_validation(
        source_root,
        workdir,
        planted_types=planted_types,
        seeds=tuple(range(11, 11 + seeds)),
        learning_object_id=learning_object_id,
        config_overrides=_parse_sim_sets(sets),
    )
    payload = report.as_dict()
    payload["passes"] = report.passes(
        label_accuracy_threshold=label_threshold, action_accuracy_threshold=action_threshold
    )
    _write_or_echo_report(payload, json_output=json_output, output=output)
    if json_output and output is None:
        return
    typer.echo(f"Run dir: {workdir}")
    for planted_type, summary in payload["by_planted"].items():
        typer.echo(
            f"{planted_type}: label {summary['label_accuracy']:.2f}, "
            f"action {summary['action_accuracy']:.2f}, "
            f"mean observations {summary['mean_observations']:.1f} ({summary['runs']} runs)"
        )
    typer.echo(
        f"Overall: label {payload['overall_label_accuracy']:.2f}, "
        f"action {payload['overall_action_accuracy']:.2f} — "
        f"{'PASS' if payload['passes'] else 'FAIL'} at label>={label_threshold} action>={action_threshold}"
    )
    if not payload["passes"]:
        raise typer.Exit(code=1)


@sim_app.command("probe-pilot")
def sim_probe_pilot_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Fixture vault root (copied per run, never written).")] = None,
    seeds: Annotated[int, typer.Option("--seeds", min=1, help="Runs per planted type.")] = 3,
    planted: Annotated[str | None, typer.Option("--planted", help="Comma-separated planted types (default: all).")] = None,
    learning_object_id: Annotated[str | None, typer.Option("--lo", help="Target Learning Object.")] = None,
    label_threshold: Annotated[float, typer.Option("--label-threshold", help="Checkpoint 4 entry gate: per-type classification accuracy.")] = 0.6,
    action_threshold: Annotated[float, typer.Option("--action-threshold", help="Checkpoint 4 entry gate: per-type action accuracy.")] = 0.6,
    sets: Annotated[list[str] | None, typer.Option("--set", help="Config override param.path=value (repeatable).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """Checkpoint-4 fixture-vault pilot: enforce the Checkpoint-3 sim entry
    gate, drive the full episode accounting against planted students, then run
    the §13 audit (predicted-vs-realized EIG, negative information, time
    calibration, cross-surface replication, shadow policies) and the replay
    determinism check on every run vault."""

    import tempfile

    from learnloop.services.probe_audit import pilot_report
    from learnloop.sim.diagnostic_validation import PLANTED_TYPES, run_probe_validation

    source_root = _root(vault)
    planted_types = (
        tuple(part.strip() for part in planted.split(",") if part.strip())
        if planted
        else PLANTED_TYPES
    )
    workdir = Path(tempfile.mkdtemp(prefix="learnloop-probe-pilot-"))
    validation = run_probe_validation(
        source_root,
        workdir,
        planted_types=planted_types,
        seeds=tuple(range(11, 11 + seeds)),
        learning_object_id=learning_object_id,
        config_overrides=_parse_sim_sets(sets),
    )
    entry_gate_passes = validation.passes(
        label_accuracy_threshold=label_threshold, action_accuracy_threshold=action_threshold
    )

    # Audit every run vault the validation produced; aggregate determinism.
    audits: list[dict] = []
    deterministic = True
    for run_root in sorted(workdir.glob("run_*")):
        try:
            run_vault = load_vault(run_root)
        except Exception:
            continue
        run_repository = Repository(VaultPaths(run_vault.root, run_vault.config).sqlite_path)
        audit = pilot_report(run_vault, run_repository)
        audit["run"] = run_root.name
        deterministic = deterministic and audit["replay_determinism"]["deterministic"]
        audits.append(audit)

    payload = {
        "version": 1,
        "entry_gate": {
            "passes": entry_gate_passes,
            "label_threshold": label_threshold,
            "action_threshold": action_threshold,
            **validation.as_dict(),
        },
        "replay_deterministic": deterministic,
        "audits": audits,
    }
    _write_or_echo_report(payload, json_output=json_output, output=output)
    if json_output and output is None:
        return
    typer.echo(f"Run dir: {workdir}")
    typer.echo(
        f"Entry gate (Checkpoint 3 sim validation): {'PASS' if entry_gate_passes else 'FAIL'} "
        f"at label>={label_threshold} action>={action_threshold}"
    )
    total_observations = sum(a["eig_calibration"]["observations"] for a in audits)
    negative = sum(a["eig_calibration"]["negative_information_count"] for a in audits)
    typer.echo(
        f"Audited {len(audits)} run vaults: {total_observations} qualifying observations, "
        f"{negative} with negative realized information."
    )
    typer.echo(f"Replay determinism: {'OK' if deterministic else 'FAILED'}")
    if not entry_gate_passes or not deterministic:
        raise typer.Exit(code=1)


@sim_app.command("benchmark-forgetting")
def sim_benchmark_forgetting_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root (read-only).")] = None,
    train_fraction: Annotated[float, typer.Option("--train-fraction", min=0.1, max=0.9, help="Temporal split point.")] = 0.7,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """Offline DAS3H-style forgetting benchmark (probe redesign Checkpoint 5.6).

    Fits a time-window logistic model on the vault's attempt history and
    compares held-out next-attempt prediction against frequency baselines.
    Report-only: never replaces durable state or facet mappings."""

    from learnloop.sim.offline_benchmarks import run_forgetting_benchmark

    root = _root(vault)
    loaded = load_vault(root)
    repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
    report = run_forgetting_benchmark(repository, train_fraction=train_fraction)
    _write_or_echo_report(report, json_output=json_output, output=output)
    if json_output and output is None:
        return
    if report["status"] != "ok":
        typer.echo(f"{report['status']}: {report.get('examples', 0)} examples "
                   f"(need {report.get('minimum_examples')})")
        return
    typer.echo(f"Train {report['train_examples']} / test {report['test_examples']} attempts.")
    for name, metrics in report["results"].items():
        typer.echo(f"- {name}: log loss {metrics['log_loss']}, Brier {metrics['brier']}")
    typer.echo(f"Best by log loss: {report['best_by_log_loss']} (report-only; nothing auto-adopted)")


@sim_app.command("run")
def sim_run_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root (never written by default).")] = None,
    profile: Annotated[str, typer.Option("--profile", help="Built-in profile name or profile YAML path.")] = "intermediate_with_misconception",
    days: Annotated[int, typer.Option("--days", help="Simulated days.")] = 60,
    items_per_day: Annotated[int, typer.Option("--items-per-day", help="Attempts per simulated day.")] = 6,
    seed: Annotated[int, typer.Option("--seed", help="Student RNG seed.")] = 42,
    fresh_copy: Annotated[bool, typer.Option("--fresh-copy/--in-place", help="Copy the vault to a tmp run dir (default) or simulate in place.")] = True,
    reset_state: Annotated[bool, typer.Option("--reset-state/--keep-state", help="Drop derived SQLite state in the run copy (default: reset).")] = True,
    sets: Annotated[list[str] | None, typer.Option("--set", help="Config override param.path=value (repeatable).")] = None,
    primed_retries: Annotated[bool, typer.Option("--primed-retries/--no-primed-retries", help="After each failed attempt, re-read the source and retry a sibling item as a primed attempt.")] = False,
    goal_due_day: Annotated[int | None, typer.Option("--goal-due-day", help="Set every active goal's due date N sim-days in (exercises the projection horizon and ramping goal quota).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """Simulate a synthetic student through the real scheduling/belief pipeline."""

    from learnloop.sim.profiles import ProfileError, load_profile
    from learnloop.sim.runner import SimulationError, run_simulation

    source_root = _root(vault)
    try:
        student_profile = load_profile(profile)
        run_root = _sim_run_root(source_root, fresh_copy=fresh_copy, reset_state=reset_state)
        report = run_simulation(
            run_root,
            student_profile,
            days=days,
            items_per_day=items_per_day,
            seed=seed,
            config_overrides=_parse_sim_sets(sets),
            primed_retries=primed_retries,
            goal_due_day=goal_due_day,
        )
    except (ProfileError, SimulationError, ConfigLoadError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "sim_failed", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    payload = report.as_dict()
    _write_or_echo_report(payload, json_output=json_output, output=output)
    if json_output and output is None:
        return
    metrics = report.metrics
    belief = metrics.get("belief_vs_truth", {})
    calibration = metrics.get("calibration", {})
    counts = metrics.get("counts", {})
    typer.echo(f"Run dir: {run_root}")
    typer.echo(
        f"Simulated {days} days x {items_per_day} items as {student_profile.name} (seed {seed}): "
        f"{counts.get('attempts', 0)} attempts."
    )
    typer.echo(
        f"Belief vs truth: MAE={belief.get('mae')} "
        f"(day1 {belief.get('daily_mae_first')} -> final {belief.get('daily_mae_last')}), "
        f"sign agreement {belief.get('sign_agreement_rate')}"
    )
    typer.echo(
        f"Calibration: brier={calibration.get('brier')} log_loss={calibration.get('log_loss')} "
        f"n={calibration.get('n')}"
    )
    typer.echo(
        f"Counts: followups={counts.get('followups_triggered')} "
        f"dont_know={counts.get('dont_know_attempts')} "
        f"error_events={counts.get('error_events_created')} "
        f"resolved={counts.get('error_events_resolved')}"
    )
    for planted in metrics.get("misconceptions", {}).get("planted", []):
        verdict = "DETECTED" if planted.get("detected") else "NOT DETECTED"
        typer.echo(
            f"Misconception {planted['error_type']} on {planted['facet_id']}: {verdict} "
            f"(first error event day {planted.get('first_error_event_day')}, "
            f"known_gap day {planted.get('first_known_gap_day')}, "
            f"{planted.get('error_events')} events, "
            f"{planted.get('error_events_resolved')} resolved)"
        )
    false_positives = metrics.get("misconceptions", {}).get("false_positive_misconception_types", [])
    if false_positives:
        typer.echo(f"False-positive misconception types: {', '.join(false_positives)}")
    for goal_entry in metrics.get("goals", {}).get("per_goal", []):
        typer.echo(
            f"Goal {goal_entry['goal_id']} (due day {goal_entry['due_day']}): "
            f"truth at target {goal_entry['truth_at_target_fraction_at_due']} at due, "
            f"{goal_entry['truth_at_target_fraction_due_plus_30']} at due+30d; "
            f"belief on-track {goal_entry['belief_on_track_fraction_at_due']}; "
            f"frontier empty day {goal_entry['frontier_empty_day']}"
        )


@sim_app.command("sweep")
def sim_sweep_command(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root (never written; each run uses a fresh copy).")] = None,
    spec: Annotated[Path | None, typer.Option("--spec", help="Sweep spec YAML (defaults to the packaged default_sweep.yaml).")] = None,
    profile: Annotated[str, typer.Option("--profile", help="Built-in profile name or profile YAML path.")] = "intermediate_with_misconception",
    days: Annotated[int, typer.Option("--days", help="Simulated days per run.")] = 30,
    items_per_day: Annotated[int, typer.Option("--items-per-day", help="Attempts per simulated day.")] = 6,
    seed: Annotated[int, typer.Option("--seed", help="Student RNG seed (shared by all runs).")] = 42,
    reset_state: Annotated[bool, typer.Option("--reset-state/--keep-state", help="Drop derived SQLite state in each run copy (default: reset).")] = True,
    sets: Annotated[list[str] | None, typer.Option("--set", help="Baseline config override param.path=value (repeatable).")] = None,
    primed_retries: Annotated[bool, typer.Option("--primed-retries/--no-primed-retries", help="Enable primed source-review retries in every run (needed for the priming_b_offset sweep).")] = False,
    goal_due_day: Annotated[int | None, typer.Option("--goal-due-day", help="Set every active goal's due date N sim-days in for all runs (needed for the goal quota sweeps).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit the full JSON report.")] = False,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write the full JSON report to a file.")] = None,
) -> None:
    """Sweep config parameters and report which ones change scheduling decisions."""

    import tempfile

    from learnloop.sim.profiles import ProfileError, load_profile
    from learnloop.sim.runner import SimulationError
    from learnloop.sim.sweep import SweepSpecError, load_sweep_spec, run_sweep

    source_root = _root(vault)
    try:
        student_profile = load_profile(profile)
        entries = load_sweep_spec(spec)
        work_dir = Path(tempfile.mkdtemp(prefix="learnloop-sweep-"))
        report = run_sweep(
            source_root,
            student_profile,
            sweep_spec=entries,
            days=days,
            items_per_day=items_per_day,
            seed=seed,
            work_dir=work_dir,
            reset_state=reset_state,
            base_overrides=_parse_sim_sets(sets),
            primed_retries=primed_retries,
            goal_due_day=goal_due_day,
        )
    except (ProfileError, SimulationError, SweepSpecError, ConfigLoadError) as exc:
        if json_output:
            typer.echo(_dump({"version": 1, "error": "sweep_failed", "message": str(exc)}))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)

    payload = report.as_dict()
    _write_or_echo_report(payload, json_output=json_output, output=output)
    if json_output and output is None:
        return
    typer.echo(f"Sweep work dir: {work_dir}")
    typer.echo(
        f"Baseline: {student_profile.name}, {days} days x {items_per_day} items, seed {seed}."
    )
    header = f"{'param=value':<62} {'topK':>6} {'tau':>6} {'dFllw':>6} {'dErr':>6} {'dMAE':>9}  verdict"
    typer.echo(header)
    typer.echo("-" * len(header))
    for result in report.results:
        if result.get("verdict") == "error":
            typer.echo(f"{result['param_path']}={result['value']}: ERROR {result['error']}")
            continue
        label = f"{result['param_path']}={result['value']}"
        counts = result["count_deltas"]
        metric_deltas = result["metric_deltas"]
        topk = result.get("mean_topk_overlap")
        tau = result.get("mean_kendall_tau")
        mae = metric_deltas.get("belief_mae")
        typer.echo(
            f"{label:<62} "
            f"{topk if topk is not None else '-':>6} "
            f"{tau if tau is not None else '-':>6} "
            f"{counts.get('followups_triggered', 0):>6} "
            f"{counts.get('error_events_created', 0):>6} "
            f"{mae if mae is not None else '-':>9}  "
            f"{result['verdict']}"
        )
