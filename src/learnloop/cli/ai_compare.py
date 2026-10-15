"""`learnloop ai compare`: the same real work on several subscription profiles, side by side.

Owner direction (2026-10-15, the ChatGPT plan as a peer of Codex): before a
route moves from Codex to the ChatGPT plan, the owner runs one batch of real
work through both and reads the differences. The command is owner-run (the
plan's sign-in is interactive and the owner's) on a backup-API copy of a
vault, never a working vault.

The work, identical for every profile:

* **grading**: a few attempts blind-graded with the learner-blind grader's
  context and wire model (:func:`~learnloop.attempts.blind_grading.blind_grading_context`
  without the C2 verifier observations, so every profile reads the same
  prompt), then validated. Nothing is written.
* **one diagnosis**, in the ``snapshot`` history mode by default
  (:func:`~learnloop.diagnosis.split.diagnoser.run_diagnosis`): Codex reads the
  as-of export in its sandbox; the ChatGPT plan is served it by LearnLoop
  (``learnloop.ai.chatgpt_plan.workspace``), so its record of what it read is
  exact. Nothing is written.
* **one structured generation**: a teach-back authoring draft for one graded
  item (:func:`~learnloop.tutor.teach_back.request_teach_back_authoring`).

The report holds ids and numbers only (no learner text, no model prose): per
call its validity, latency, physical requests and tokens; per profile its
totals and plan-allowance behaviour (the ChatGPT plan's pause state before and
after, usage-limit errors); per pair of profiles their agreement (grading
scores and criteria, diagnosis causal classes and cited attempts, generation
validity).

Only subscription profiles run (Codex, the ChatGPT plan: billing
``subscription``, cost estimated from reported usage, Slice A plan §5 rule 6).
The call cap is the plan itself: a dry run states it and a run never makes a
call outside it. Every model call leaves a receipt in the vault copy.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from itertools import combinations
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import time
from typing import Any, Iterator

from learnloop.ai.chatgpt_plan.session import PlanSession
from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import tee_model_calls
from learnloop.ai.routing import (
    client_for_provider,
    is_generation_profile,
    runtime_for_provider,
    serves_read_only_workspace,
)
from learnloop.ai.spend import is_subscription_transport
from learnloop.attempts.blind_grading import (
    blind_grading_context,
    blind_grading_prompt,
    request_blind_grading_proposal,
    validate_blind_grading_proposal,
)
from learnloop.attempts.grading import GradingValidationError, resolved_rubric
from learnloop.db.copies import copy_tree_with_databases
from learnloop.diagnosis.split.diagnoser import run_diagnosis
from learnloop.diagnosis.split.live import (
    current_attempt_for,
    joint_grade_record,
    live_history_store,
    needs_diagnosis,
    settings_from_config,
)
from learnloop.tutor.teach_back import request_teach_back_authoring, teach_back_authoring_context
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

COMPARE_VERSION = 1
DEFAULT_GRADING_ATTEMPTS = 3
DIAGNOSIS_MODES = ("snapshot", "full", "exact")
#: Prompt-side token estimate: ~4 bytes of UTF-8 per token.
_BYTES_PER_TOKEN = 4
#: Attempt types the blind grader never grades as ordinary answers.
_SKIPPED_ATTEMPT_TYPES = frozenset({"teach_back", "dont_know"})


class CompareRefused(ValueError):
    """The comparison cannot run as asked; ``code`` names why (for ``--json``)."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CompareRequest:
    profiles: tuple[str, ...]
    grading_attempts: int = DEFAULT_GRADING_ATTEMPTS
    #: Explicit grading targets (replace the automatic choice).
    attempt_ids: tuple[str, ...] = ()
    diagnosis: bool = True
    diagnosis_attempt_id: str | None = None
    diagnosis_mode: str = "snapshot"
    generation: bool = True
    #: The whole-operation deadline of each call (a workspace turn's rounds included).
    timeout_seconds: int = 900


@dataclass
class Targets:
    grading: list[str] = field(default_factory=list)
    diagnosis: str | None = None
    generation_item: str | None = None
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"grading": list(self.grading), "diagnosis": self.diagnosis,
                "generation_item": self.generation_item, "notes": list(self.notes)}


# -- safety ------------------------------------------------------------------------------


def tracked_database_reason(vault: LoadedVault) -> str | None:
    """Why this vault must not be compared on, or None.

    A vault whose database git tracks is a working vault (the owner's
    ``fixtures/linear_algebra``, ``probability`` and ``arxiv_v2`` are): the
    comparison writes receipts and runs migrations, so it runs on a backup-API
    copy instead (``--copy-from``).
    """

    database = VaultPaths(vault.root, vault.config).sqlite_path
    git = shutil.which("git")
    if git is None or not database.exists():
        return None
    try:
        result = subprocess.run(
            [git, "-C", str(database.parent), "ls-files", "--error-unmatch", "--", database.name],
            capture_output=True, text=True, timeout=20, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return (f"{vault.root} is a working vault (git tracks {database.name}). Compare on a backup-API copy: "
            f"learnloop ai compare --copy-from {vault.root} --vault fixtures-local/<name> ...")


def copy_vault(source: Path, destination: Path) -> list[Path]:
    """A backup-API copy of ``source`` at ``destination`` (which must not exist yet)."""

    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_dir():
        raise CompareRefused(f"--copy-from {source} is not a directory.", code="copy_source_missing")
    if destination.exists():
        raise CompareRefused(f"--vault {destination} already exists; --copy-from needs a new directory.",
                             code="copy_destination_exists")
    if source == destination or source in destination.parents:
        raise CompareRefused("--vault must lie outside the vault it copies.", code="copy_inside_source")
    destination.parent.mkdir(parents=True, exist_ok=True)
    return copy_tree_with_databases(source, destination)


def check_profiles(vault: LoadedVault, request: CompareRequest) -> list[dict[str, Any]]:
    """Each named profile's identity and readiness; refuses a profile that cannot run here."""

    config = vault.config
    if not request.profiles:
        raise CompareRefused("Name at least one profile with --profiles.", code="no_profiles")
    if request.diagnosis_mode not in DIAGNOSIS_MODES:
        raise CompareRefused(f"--diagnosis-mode must be one of {', '.join(DIAGNOSIS_MODES)}.", code="bad_mode")
    rows = []
    for name in request.profiles:
        profile = config.ai.providers.get(name)
        if profile is None:
            raise CompareRefused(f"No provider profile named {name!r} in this vault.", code="unknown_profile")
        if not is_generation_profile(config, name):
            raise CompareRefused(f"{name!r} is an embedding or decision-model profile; it cannot grade.",
                                 code="not_generation")
        if not is_subscription_transport(profile=profile):
            raise CompareRefused(
                f"{name!r} is metered ({profile.type}); the comparison runs subscription profiles only "
                "(Codex, chatgpt_plan).", code="metered_profile")
        runtime = runtime_for_provider(vault.root, config, name)
        rows.append({
            "provider": name, "type": profile.type, "model": profile.model, "billing": "subscription",
            "ready": runtime.ready, "message": runtime.message,
            "read_only_workspace": serves_read_only_workspace(config, name),
        })
    return rows


# -- targets -----------------------------------------------------------------------------


def _record_for(vault: LoadedVault, repository: Any, attempt_id: str) -> dict[str, Any] | None:
    stored = repository.latest_blind_grade_record(attempt_id)
    if stored is not None:
        return dict(stored.get("record") or {})
    row = repository.fetch_practice_attempt(attempt_id)
    return joint_grade_record(vault, repository, row) if row is not None else None


def select_targets(vault: LoadedVault, repository: Any, request: CompareRequest, *, store: Any = None) -> Targets:
    """The attempts to grade, the attempt to diagnose and the item to generate from.

    Deterministic: the most recent non-pass and pass attempts first, then the
    most recent others; the diagnosis is the latest non-pass attempt that
    needs one and has history before it.
    """

    store = store if store is not None else live_history_store(vault, repository)
    attempts = store.all_attempts()
    by_id = {attempt.attempt_id: attempt for attempt in attempts}
    targets = Targets()

    def gradeable(attempt: Any) -> bool:
        return (attempt.practice_item_id in vault.practice_items and bool(attempt.learner_answer_md.strip())
                and attempt.attempt_type not in _SKIPPED_ATTEMPT_TYPES)

    if request.attempt_ids:
        for attempt_id in request.attempt_ids:
            attempt = by_id.get(attempt_id)
            if attempt is None or not gradeable(attempt):
                raise CompareRefused(f"Attempt {attempt_id!r} is not a gradeable attempt in this vault.",
                                     code="unknown_attempt")
        targets.grading = list(dict.fromkeys(request.attempt_ids))
    elif request.grading_attempts > 0:
        recent = [attempt for attempt in reversed(attempts) if gradeable(attempt)]
        chosen: list[str] = []
        for wanted in (True, False):  # the latest non-pass, then the latest pass
            pick = next((a.attempt_id for a in recent if a.non_pass == wanted), None)
            if pick is not None and len(chosen) < request.grading_attempts:
                chosen.append(pick)
        for attempt in recent:
            if len(chosen) >= request.grading_attempts:
                break
            if attempt.attempt_id not in chosen:
                chosen.append(attempt.attempt_id)
        order = {attempt.attempt_id: index for index, attempt in enumerate(attempts)}
        targets.grading = sorted(chosen, key=order.__getitem__)
        if len(chosen) < request.grading_attempts:
            targets.notes.append(f"only {len(chosen)} gradeable attempts in this vault")

    if request.diagnosis:
        if request.diagnosis_attempt_id:
            if request.diagnosis_attempt_id not in by_id:
                raise CompareRefused(f"Attempt {request.diagnosis_attempt_id!r} is not in this vault.",
                                     code="unknown_attempt")
            targets.diagnosis = request.diagnosis_attempt_id
        else:
            for index in range(len(attempts) - 1, 0, -1):
                attempt = attempts[index]
                if not (attempt.non_pass and gradeable(attempt)):
                    continue
                record = _record_for(vault, repository, attempt.attempt_id)
                if record and needs_diagnosis(record):
                    targets.diagnosis = attempt.attempt_id
                    break
            if targets.diagnosis is None:
                targets.notes.append("no non-pass attempt with history needs a diagnosis; diagnosis skipped")

    if request.generation:
        for attempt_id in [*targets.grading, *([targets.diagnosis] if targets.diagnosis else [])]:
            item = vault.practice_items.get(by_id[attempt_id].practice_item_id)
            if item is not None and item.learning_object_id in vault.learning_objects:
                targets.generation_item = item.id
                break
        if targets.generation_item is None:
            item = next((item for item in sorted(vault.practice_items.values(), key=lambda value: value.id)
                         if item.status == "active" and item.learning_object_id in vault.learning_objects), None)
            targets.generation_item = item.id if item is not None else None
        if targets.generation_item is None:
            targets.notes.append("no active item with a learning object; generation skipped")
    return targets


# -- the work ----------------------------------------------------------------------------


class _Meter:
    """The model calls one comparison call made, from the receipts' own events."""

    def __init__(self) -> None:
        self.starts: dict[str, dict[str, Any]] = {}
        self.finishes: list[dict[str, Any]] = []

    def __call__(self, action: str, event: dict[str, Any]) -> None:
        if action == "start":
            self.starts[str(event.get("id"))] = dict(event)
        elif action == "finish":
            self.finishes.append(dict(event))

    def summary(self) -> dict[str, Any]:
        physical = [event for event in self.finishes
                    if (self.starts.get(str(event.get("id"))) or {}).get("parent_call_id")]
        if not physical:
            # No child receipt: a transport that reports on the operation itself
            # counts once if it reported usage; a local refusal sent nothing.
            physical = [event for event in self.finishes
                        if isinstance(event.get("input_tokens"), int) or isinstance(event.get("output_tokens"), int)]
        tokens: dict[str, int | None] = {}
        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens"):
            values = [event.get(key) for event in physical if isinstance(event.get(key), int)]
            tokens[key] = sum(values) if values else None
        rounds = 0
        served: list[str] = []
        for event in physical:
            try:
                usage = json.loads(event.get("usage_json") or "{}")
            except (TypeError, ValueError):
                continue
            workspace = (usage.get("chatgpt_plan") or {}).get("workspace") if isinstance(usage, dict) else None
            if isinstance(workspace, dict):
                rounds = max(rounds, int(workspace.get("round") or 0))
                served.extend(str(path) for path in workspace.get("carries") or workspace.get("served") or [])
        return {
            "physical_requests": len(physical),
            "resolved_models": sorted({str(event["resolved_model"]) for event in physical
                                       if event.get("resolved_model")}),
            **tokens,
            **({"workspace_rounds": rounds} if rounds else {}),
            **({"workspace_served_files": len(dict.fromkeys(served))} if served else {}),
        }


@contextmanager
def _measured() -> Iterator[_Meter]:
    meter = _Meter()
    with tee_model_calls(meter):
        yield meter


def _error_class(exc: BaseException) -> str:
    return type(exc).__name__


def _grade(vault: LoadedVault, client: Any, attempt: Any) -> dict[str, Any]:
    item = vault.practice_items[attempt.practice_item_id]
    context = blind_grading_context(vault, item, attempt_id=attempt.attempt_id,
                                    learner_answer_md=attempt.learner_answer_md)
    proposal = request_blind_grading_proposal(client, context)
    try:
        validated = validate_blind_grading_proposal(
            proposal, attempt_id=attempt.attempt_id, item=item, vault=vault,
            learner_answer_md=attempt.learner_answer_md,
        )
    except (GradingValidationError, ValueError) as exc:
        return {"parsed": True, "valid": False, "error": _error_class(exc)}
    record = validated.as_record()
    return {
        "parsed": True, "valid": True,
        "rubric_score": record.get("rubric_score"), "max_points": record.get("max_points"),
        "criteria": {str(row["criterion_id"]): row.get("points_awarded") for row in record.get("criteria") or []},
        "fatal_errors": len(record.get("fatal_errors") or []),
        "error_attributions": len(record.get("error_attributions") or []),
        "grader_confidence": record.get("grader_confidence"),
    }


def _diagnose(vault: LoadedVault, repository: Any, client: Any, attempt_id: str, *, store: Any,
              mode: str) -> dict[str, Any]:
    row = repository.fetch_practice_attempt(attempt_id)
    record = _record_for(vault, repository, attempt_id)
    current = current_attempt_for(vault, row, record or {}, repository) if row is not None else None
    if current is None:
        return {"parsed": False, "valid": False, "error": "item_missing"}
    item = vault.practice_items[str(row["practice_item_id"])]
    outcome = run_diagnosis(client, vault=vault, item=item, rubric=resolved_rubric(vault, item), store=store,
                            current=current, settings=settings_from_config(vault), mode=mode)  # type: ignore[arg-type]
    proposal = outcome.proposal or {}
    snapshot = (outcome.receipt or {}).get("snapshot") or {}
    opened = snapshot.get("opened")
    result: dict[str, Any] = {
        "status": outcome.status,
        "parsed": outcome.proposal is not None,
        "valid": outcome.status == "completed",
        "error": outcome.error,
        "unknown_id_count": outcome.unknown_id_count,
        "evidence_attempt_ids": list(proposal.get("evidence_attempt_ids") or []),
        "causal_classes": sorted(str(event.get("causal_class")) for event in proposal.get("event_diagnoses") or []),
        "event_diagnoses": len(proposal.get("event_diagnoses") or []),
        "abstentions": len(proposal.get("abstentions") or []),
    }
    if mode == "snapshot":
        result["snapshot"] = {
            "file_count": snapshot.get("file_count"),
            "opened_reported": opened is not None,
            "opened_count": len(opened) if isinstance(opened, list) else None,
        }
    return result


def _generate(vault: LoadedVault, client: Any, item_id: str) -> dict[str, Any]:
    # The teach-back authoring context exactly as the tutor builds it.
    item = vault.practice_items[item_id]
    lo = vault.learning_objects[item.learning_object_id]
    context, _criteria = teach_back_authoring_context(vault, item, lo, quest_sentence=None)
    draft = request_teach_back_authoring(client, context)
    allowed = {str(facet["id"]) for facet in context.allowed_facets}
    drafted = [*draft.core_criteria, *([draft.transfer_criterion] if draft.transfer_criterion else [])]
    checks = {
        "prompt_present": bool(draft.prompt_md.strip()),
        "expected_answer_present": bool(draft.expected_answer_md.strip()),
        "core_criteria_within_limit": 1 <= len(draft.core_criteria) <= context.max_core_criteria,
        "facets_known": all(set(criterion.facet_ids) <= allowed for criterion in drafted),
    }
    return {"parsed": True, "valid": all(checks.values()), "checks": checks,
            "core_criteria": len(draft.core_criteria)}


#: How much of a failure's message a call record keeps (provider messages, not learner text).
_DETAIL_LIMIT = 500


class _FailureRecorder:
    """The profile's client, forwarding everything, that remembers its last failure.

    A diagnosis records only the failure's class (``run_diagnosis`` handles
    it), so the report takes the message from here.
    """

    def __init__(self, client: Any) -> None:
        self._client = client
        self.failure: BaseException | None = None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def complete(self, request: Any) -> Any:
        try:
            return self._client.complete(request)
        except Exception as exc:
            self.failure = exc
            raise


def _timed(work: Callable[[], dict[str, Any]], recorder: _FailureRecorder | None = None) -> dict[str, Any]:
    """Run one comparison call; an interrupt propagates, any other failure is recorded."""

    if recorder is not None:
        recorder.failure = None
    started = time.monotonic()
    with _measured() as meter:
        try:
            result = work()
        except AIInterrupted:
            raise
        except (AIProviderUnavailable, ValueError) as exc:
            result = {"parsed": False, "valid": False, "error": _error_class(exc), "detail": str(exc)}
    if result.get("error") and not result.get("detail") and recorder is not None and recorder.failure is not None:
        result["detail"] = str(recorder.failure)
    if result.get("detail"):
        result["detail"] = str(result["detail"])[:_DETAIL_LIMIT]
    return {**result, "seconds": round(time.monotonic() - started, 3), **meter.summary()}


_ALLOWANCE_ERRORS = frozenset({"ChatGPTPlanUsageExhausted", "ChatGPTPlanNotEligible", "ChatGPTSignInRequired"})


def plan_allowance(profile_type: str) -> dict[str, Any] | None:
    """The ChatGPT plan's local allowance state (no network); None for other types."""

    if profile_type != "chatgpt_plan":
        return None
    status = PlanSession().status().as_dict()
    usage_limit = status.get("usage_limit") or {}
    return {"state": status.get("state"), "paused_until": status.get("paused_until"),
            "usage_limit_code": usage_limit.get("code"), "usage_limit_at": usage_limit.get("at")}


# -- plan and run ---------------------------------------------------------------------------


def _estimated_tokens(vault: LoadedVault, repository: Any, targets: Targets, request: CompareRequest,
                      store: Any) -> dict[str, Any]:
    """Prompt-side estimates per call kind (no request); the output side is the model's."""

    grading = []
    for attempt_id in targets.grading:
        attempt = store.attempt(attempt_id)
        item = vault.practice_items[attempt.practice_item_id]
        prompt = blind_grading_prompt(blind_grading_context(vault, item, attempt_id=attempt_id,
                                                            learner_answer_md=attempt.learner_answer_md))
        grading.append(len(prompt.encode("utf-8")) // _BYTES_PER_TOKEN)
    estimate: dict[str, Any] = {"grading_input_tokens": grading}
    if targets.diagnosis is not None:
        estimate["diagnosis_input_tokens"] = None
        estimate["diagnosis_note"] = (
            "the inline context plus whatever the diagnoser reads of the snapshot export (a ChatGPT-plan "
            "turn resends its history each round; served text is capped by max_workspace_chars)"
            if request.diagnosis_mode == "snapshot" else "the assembled context")
    return estimate


def plan_compare(vault: LoadedVault, repository: Any, request: CompareRequest) -> dict[str, Any]:
    """What a run would do: profiles, targets, calls; builds no client and sends nothing."""

    profiles = check_profiles(vault, request)
    store = live_history_store(vault, repository)
    targets = select_targets(vault, repository, request, store=store)
    calls_per_profile = len(targets.grading) + int(targets.diagnosis is not None) + int(
        targets.generation_item is not None)
    return {
        "version": COMPARE_VERSION,
        "profiles": profiles,
        "targets": targets.as_dict(),
        "diagnosis_mode": request.diagnosis_mode,
        "calls_per_profile": calls_per_profile,
        "max_calls": calls_per_profile * len(profiles),
        "timeout_seconds": request.timeout_seconds,
        "estimate": _estimated_tokens(vault, repository, targets, request, store),
        "billing": "subscription (cost estimated from reported usage; no dollar cap)",
    }


def run_compare(
    vault: LoadedVault,
    repository: Any,
    request: CompareRequest,
    *,
    client_factory: Callable[[str], Any] | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Run the plan on every ready profile; returns the report (ids and numbers only)."""

    plan = plan_compare(vault, repository, request)
    targets = Targets(**{key: value for key, value in plan["targets"].items()})
    store = live_history_store(vault, repository)
    factory = client_factory or (lambda name: client_for_provider(
        vault.root, vault.config, name, timeout_seconds=request.timeout_seconds))
    say = progress or (lambda _message: None)
    calls_made = 0
    results: list[dict[str, Any]] = []
    for profile in plan["profiles"]:
        name = profile["provider"]
        row: dict[str, Any] = {**profile, "grading": {}, "diagnosis": None, "generation": None}
        results.append(row)
        if not profile["ready"]:
            row["error"] = profile["message"] or "not ready"
            say(f"{name}: not ready ({row['error']})")
            continue
        try:
            client = _FailureRecorder(factory(name))
        except AIProviderUnavailable as exc:
            row["error"] = str(exc)
            say(f"{name}: {exc}")
            continue
        row["allowance_before"] = plan_allowance(profile["type"])
        stopped: str | None = None

        def call(label: str, work: Callable[[], dict[str, Any]]) -> dict[str, Any] | None:
            nonlocal calls_made, stopped
            if stopped is not None:
                return {"parsed": False, "valid": False, "error": f"not_run: {stopped}"}
            if calls_made >= plan["max_calls"]:  # pragma: no cover - the loop never exceeds its plan
                raise CompareRefused("The comparison reached its call cap.", code="call_cap")
            calls_made += 1
            say(f"{name}: {label}")
            outcome = _timed(work, client)
            if outcome.get("error") in _ALLOWANCE_ERRORS:
                # The plan refuses locally from here on: stop this profile.
                stopped = str(outcome["error"])
            return outcome

        for attempt_id in targets.grading:
            attempt = store.attempt(attempt_id)
            row["grading"][attempt_id] = call(f"grading {attempt_id}", lambda attempt=attempt: _grade(vault, client, attempt))
        if targets.diagnosis is not None:
            if request.diagnosis_mode == "snapshot" and not profile["read_only_workspace"]:
                row["diagnosis"] = {"parsed": False, "valid": False, "error": "provider_lacks_read_only_workspace"}
            else:
                row["diagnosis"] = call(
                    f"{request.diagnosis_mode} diagnosis {targets.diagnosis}",
                    lambda: _diagnose(vault, repository, client, targets.diagnosis, store=store,
                                      mode=request.diagnosis_mode))
        if targets.generation_item is not None:
            row["generation"] = call(f"teach-back authoring {targets.generation_item}",
                                     lambda: _generate(vault, client, targets.generation_item))
        row["allowance_after"] = plan_allowance(profile["type"])
        row["stopped"] = stopped
        row["summary"] = _profile_summary(row)
    recorded = {attempt_id: _recorded_grade(store.attempt(attempt_id)) for attempt_id in targets.grading}
    for row in results:
        row["vs_recorded_grade"] = _grading_agreement(
            {attempt_id: grade for attempt_id, grade in row["grading"].items()}, recorded)
    return {
        **plan,
        "results": results,
        "agreement": _agreement(results),
        "calls_made": calls_made,
    }


# -- summaries -----------------------------------------------------------------------------


def _calls(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    calls = [call for call in (row.get("grading") or {}).values() if call]
    calls += [call for call in (row.get("diagnosis"), row.get("generation")) if call]
    return [call for call in calls if "seconds" in call]


def _profile_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    calls = _calls(row)
    seconds = [call["seconds"] for call in calls]
    totals = {key: sum(call.get(key) or 0 for call in calls)
              for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens",
                          "physical_requests")}
    count = len(calls) or 1
    return {
        "calls": len(calls),
        "valid": sum(1 for call in calls if call.get("valid")),
        "parsed": sum(1 for call in calls if call.get("parsed")),
        "errors": sorted({str(call["error"]) for call in calls if call.get("error")}),
        "seconds_median": round(statistics.median(seconds), 3) if seconds else None,
        "seconds_max": max(seconds) if seconds else None,
        **totals,
        "tokens_per_call": round((totals["input_tokens"] + totals["output_tokens"]) / count, 1) if calls else None,
        "output_tokens_per_call": round(totals["output_tokens"] / count, 1) if calls else None,
        "allowance_errors": sum(1 for call in calls if call.get("error") in _ALLOWANCE_ERRORS),
    }


def _recorded_grade(attempt: Any) -> dict[str, Any] | None:
    if attempt is None or attempt.score is None or not attempt.max_points:
        return None
    return {"valid": True, "rubric_score": attempt.score, "max_points": attempt.max_points, "criteria": None}


def _grading_agreement(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    pairs = []
    for attempt_id, one in left.items():
        other = right.get(attempt_id)
        if not (one and other and one.get("valid") and other.get("valid")):
            continue
        maximum = float(one.get("max_points") or other.get("max_points") or 0) or None
        a, b = float(one["rubric_score"]), float(other["rubric_score"])
        criteria = None
        if one.get("criteria") is not None and other.get("criteria") is not None:
            ids = set(one["criteria"]) | set(other["criteria"])
            same = sum(1 for key in ids if one["criteria"].get(key) == other["criteria"].get(key))
            criteria = same / len(ids) if ids else None
        pairs.append({
            "attempt_id": attempt_id, "scores": [a, b], "max_points": maximum, "exact": a == b,
            "abs_diff_fraction": abs(a - b) / maximum if maximum else None,
            "full_credit_agrees": (a == maximum) == (b == maximum) if maximum else None,
            "criterion_agreement": criteria,
        })

    def mean(key: str) -> float | None:
        values = [pair[key] for pair in pairs if pair[key] is not None]
        return round(sum(float(value) for value in values) / len(values), 4) if values else None

    return {
        "compared": len(pairs),
        "exact_rate": mean("exact"),
        "mean_abs_diff_fraction": mean("abs_diff_fraction"),
        "full_credit_agreement": mean("full_credit_agrees"),
        "criterion_agreement": mean("criterion_agreement"),
        "pairs": pairs,
    }


def _jaccard(one: Sequence[str], other: Sequence[str]) -> float | None:
    union = set(one) | set(other)
    return round(len(set(one) & set(other)) / len(union), 4) if union else None


def _agreement(results: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    pairs = []
    for left, right in combinations([row for row in results if row.get("ready")], 2):
        entry: dict[str, Any] = {
            "profiles": [left["provider"], right["provider"]],
            "grading": _grading_agreement(left.get("grading") or {}, right.get("grading") or {}),
        }
        one, other = left.get("diagnosis"), right.get("diagnosis")
        if one and other:
            both = bool(one.get("valid") and other.get("valid"))
            entry["diagnosis"] = {
                "both_valid": both,
                "same_causal_classes": one.get("causal_classes") == other.get("causal_classes") if both else None,
                "evidence_jaccard": _jaccard(one.get("evidence_attempt_ids") or [],
                                             other.get("evidence_attempt_ids") or []) if both else None,
                "unknown_ids": [one.get("unknown_id_count"), other.get("unknown_id_count")],
            }
        one, other = left.get("generation"), right.get("generation")
        if one and other:
            entry["generation"] = {"both_valid": bool(one.get("valid") and other.get("valid")),
                                   "valid": [bool(one.get("valid")), bool(other.get("valid"))]}
        pairs.append(entry)
    return pairs


__all__ = [
    "COMPARE_VERSION",
    "CompareRefused",
    "CompareRequest",
    "DEFAULT_GRADING_ATTEMPTS",
    "DIAGNOSIS_MODES",
    "Targets",
    "check_profiles",
    "copy_vault",
    "plan_allowance",
    "plan_compare",
    "run_compare",
    "select_targets",
    "tracked_database_reason",
]
