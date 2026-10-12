"""Plan, estimate and run the M1 offline review into a scratch copy (§12.1).

A run lives in one directory: ``scratch.sqlite`` (a backup-API copy of the
vault database plus the ``review_*`` tables) and ``run.json``. Stages are
idempotent - every unit of paid work checks for its row first - so an
interrupted or over-budget run resumes where it stopped without paying twice.

Stages: targets (stratified sample) -> planted learners -> blind grades (and
the joint grader's repeat / planted rerun) -> diagnoses per arm -> judge ->
grader probes -> manifest. Arms: (a) the stored joint diagnosis (no call),
(b) ``exact``, (c) ``hybrid``, (d) ``full``, (e) ``snapshot``, plus (b') a
repeat of (b) on a subset (noise floor), (b0) a history-free control on the
planted learners, and the (d) context-length sweep on the planted learners.
"""

from __future__ import annotations

import json
import math
import random
import sqlite3
import time
from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence

from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.routing import provider_for_task, ready_client_for_task
from learnloop.ai.spend import SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.ai.transport import READ_ONLY_WORKSPACE
from learnloop.attempts.ai_contracts import GradingContext, GradingProposal
from learnloop.attempts.blind_grading import (
    BLIND_GRADING_PROMPT_VERSION,
    blind_grading_context,
    blind_grading_context_hash,
    blind_grading_prompt,
    request_blind_grading_proposal,
    validate_blind_grading_proposal,
)
from learnloop.attempts.ai_contracts import GRADING_PROMPT_VERSION, grading_prompt
from learnloop.attempts.grading import (
    GradingValidationError,
    build_grading_context,
    grading_context_hash,
    request_grading_proposal,
    resolved_rubric,
    validate_codex_grading_proposal,
)
from learnloop.db.connection import connect
from learnloop.db.copies import backup_database
from learnloop.db.repositories import Repository
from learnloop.db.stores.diagnosis_review import (
    ensure_review_schema,
    insert_review_row,
    review_rows,
    update_run,
    update_target_positions,
)
from learnloop.db.stores.judgments import append_judgment
from learnloop.diagnosis.diagnostic_augmentation import diagnostic_verifier_observations
from learnloop.diagnosis.offline_review import judge as judging
from learnloop.diagnosis.offline_review import probes as probing
from learnloop.diagnosis.offline_review.planted import (
    SHAPES,
    PlantedCase,
    PlantedCaseInvalid,
    case_from_draft,
    cases_from_manifest,
    default_start,
    plantable_learning_objects,
    planted_history_store,
    request_planted_scenario,
    scenario_request,
)
from learnloop.diagnosis.offline_review.spend import OUTPUT_ALLOWANCE, ReviewSpend
from learnloop.diagnosis.split.context import (
    assemble_diagnosis_context,
    current_attempt_from,
    estimate_tokens,
    history_attempt_tokens,
)
from learnloop.diagnosis.split.contract import diagnosis_prompt
from learnloop.diagnosis.split.diagnoser import DiagnosisOutcome, run_diagnosis, supports_snapshot
from learnloop.diagnosis.split.history import (
    HistoryAttempt,
    StaticHistoryStore,
    VaultHistoryStore,
    learning_object_neighborhood,
)
from learnloop.diagnosis.split.legacy_view import legacy_view_from_grading_proposal, stored_legacy_view
from learnloop.diagnosis.split.retrieval import EmbeddingHistoryRetriever
from learnloop.diagnosis.split.settings import DIAGNOSIS_PROMPT_VERSION, DiagnosisSettings
from learnloop.ids import new_ulid
from learnloop.vault.models import LoadedVault, PracticeItem

RUN_FILE = "run.json"
STAGES_FILE = "stages.json"
SCRATCH_FILE = "scratch.sqlite"
REVIEW_VERSION = "slice1-m1-review-v1"
MAIN_ARMS = ("a", "b", "c", "d", "e")
ARM_MODES = {"b": "exact", "b_prime": "exact", "b0": "exact", "c": "hybrid", "d": "full", "e": "snapshot"}
DEFAULT_SWEEP_BUDGETS = (25_000, 50_000, 100_000)
MIN_SAMPLE = 40
_GRADED_SOURCES = ("ai", "codex")
_JOINT_HISTORY_LIMIT = 4


@dataclass(frozen=True)
class ReviewOptions:
    sample_size: int = 40
    seed: int = 20261012
    arms: tuple[str, ...] = MAIN_ARMS
    repeat_subset: int = 10
    planted_per_shape: int = 2
    planted_manifest: Any = None
    generate_planted: bool = True
    sweep_budgets: tuple[int, ...] = DEFAULT_SWEEP_BUDGETS
    sweep: bool = True
    probes: bool = True
    probe_items: int = 40
    joint_repeat: bool = True
    judge: bool = True
    attempt_ids: tuple[str, ...] = ()
    since: str | None = None
    settings: DiagnosisSettings = field(default_factory=DiagnosisSettings)

    def __post_init__(self) -> None:
        unknown = set(self.arms) - set(MAIN_ARMS)
        if unknown:
            raise ValueError(f"unknown arm(s): {', '.join(sorted(unknown))}")
        for name in ("sample_size", "repeat_subset", "planted_per_shape", "probe_items"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be nonnegative")

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["planted_manifest"] = self.planted_manifest is not None
        return payload


@dataclass
class ReviewClients:
    grading: Any | None = None
    diagnosis: Any | None = None
    judge: Any | None = None
    generator: Any | None = None
    embedding: Any | None = None
    notes: dict[str, str] = field(default_factory=dict)


REVIEW_ROUTES: tuple[tuple[str, str], ...] = (
    ("grading", "grading"),
    ("diagnosis", "diagnosis"),
    ("judge", "diagnosis_judge"),
    ("generator", "diagnosis_generator"),
    ("embedding", "embedding"),
)
_SUBSCRIPTION_PROFILE_TYPES = frozenset({"codex_sdk", "http", "http_adapter"})


def route_profiles(vault: LoadedVault) -> dict[str, dict[str, Any]]:
    """Each review route's configured provider, from config only (no client)."""

    config = vault.config
    profiles: dict[str, dict[str, Any]] = {}
    for _attribute, route in REVIEW_ROUTES:
        selection = provider_for_task(config, route)  # type: ignore[arg-type]
        name = selection.provider_name
        profile = config.ai.providers.get(name)
        if route == "embedding":
            model = config.embedding.model if config.embedding.enabled and name else None
        else:
            model = getattr(profile, "model", None) if profile is not None else (config.codex.model if name in {"codex", ""} else None)
        profile_type = profile.type if profile is not None else ("codex_sdk" if name == "codex" else None)
        profiles[route] = {
            "provider": name or None,
            "model": model,
            "profile_type": profile_type,
            "subscription": profile_type in _SUBSCRIPTION_PROFILE_TYPES,
            "enabled": bool(name) and (route != "embedding" or config.embedding.enabled),
        }
    return profiles


def resolve_review_clients(vault: LoadedVault) -> ReviewClients:
    """Ready clients for every review route; a missing one is a note, not an error."""

    clients = ReviewClients()
    for attribute, route in REVIEW_ROUTES:
        resolved = ready_client_for_task(vault.root, vault.config, route)  # type: ignore[arg-type]
        if resolved.ready:
            setattr(clients, attribute, resolved.client)
        else:
            clients.notes[route] = f"not ready: {resolved.runtime.message or resolved.runtime.status}"
    return clients


# ---------------------------------------------------------------------------
# Eligibility, data check, sampling
# ---------------------------------------------------------------------------


def eligible_attempts(
    vault: LoadedVault,
    repository: Repository,
    *,
    since: str | None = None,
) -> list[dict[str, Any]]:
    """Model-graded practice attempts with an error, an answer and a known item."""

    with repository.connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT a.id, a.practice_item_id, a.learning_object_id, a.attempt_type, "
            "a.learner_answer_md, a.rubric_score, a.created_at, m.grading_source "
            "FROM practice_attempts a JOIN attempt_feedback_metadata m ON m.attempt_id = a.id "
            "WHERE m.grading_source IN ('ai', 'codex') ORDER BY a.created_at, a.id"
        )]
        failing = {
            str(row[0])
            for row in connection.execute(
                "SELECT DISTINCT attempt_id FROM error_events WHERE attempt_id IS NOT NULL"
            )
        }
        failing.update(
            str(row[0])
            for row in connection.execute(
                "SELECT DISTINCT attempt_id FROM attempt_feedback_metadata WHERE fatal_errors_json NOT IN ('[]', '')"
            )
        )
    eligible = []
    for row in rows:
        item = vault.practice_items.get(str(row["practice_item_id"]))
        if item is None or not str(row.get("learner_answer_md") or "").strip():
            continue
        if row.get("attempt_type") in {"skip", "self_report", "guided_walkthrough", "dont_know"}:
            continue
        if since is not None and str(row["created_at"]) < since:
            continue
        maximum = float(resolved_rubric(vault, item).max_points)
        below_max = row.get("rubric_score") is not None and float(row["rubric_score"]) < maximum
        if str(row["id"]) in failing or below_max:
            eligible.append(row)
    return eligible


def data_check(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    eligible = eligible_attempts(vault, repository)
    by_lo: dict[str, int] = {}
    for row in eligible:
        by_lo[str(row["learning_object_id"])] = by_lo.get(str(row["learning_object_id"]), 0) + 1
    return {
        "graded_wrong_answers": len(eligible),
        "learning_objects": len(by_lo),
        "max_share_one_lo": round(max(by_lo.values()) / len(eligible), 3) if eligible else None,
        "threshold": MIN_SAMPLE,
        "meets_threshold": len(eligible) >= MIN_SAMPLE,
    }


def select_sample(rows: Sequence[Mapping[str, Any]], size: int, seed: int) -> list[Mapping[str, Any]]:
    """Stratified across LOs and time quartiles; deterministic for a seed."""

    if size <= 0 or not rows:
        return []
    ordered = sorted(rows, key=lambda row: (str(row["created_at"]), str(row["id"])))
    quartile = {str(row["id"]): min(3, (index * 4) // len(ordered)) for index, row in enumerate(ordered)}
    strata: dict[tuple[str, int], list[Mapping[str, Any]]] = {}
    for row in ordered:
        strata.setdefault((str(row["learning_object_id"]), quartile[str(row["id"])]), []).append(row)
    rng = random.Random(seed)
    keys = sorted(strata)
    rng.shuffle(keys)
    for key in keys:
        rng.shuffle(strata[key])
    chosen: list[Mapping[str, Any]] = []
    while len(chosen) < size and any(strata[key] for key in keys):
        for key in keys:
            if strata[key] and len(chosen) < size:
                chosen.append(strata[key].pop())
    return chosen


# ---------------------------------------------------------------------------
# Plan and estimate
# ---------------------------------------------------------------------------


def _placeholder_blind(item: PracticeItem, vault: LoadedVault) -> dict[str, Any]:
    rubric = resolved_rubric(vault, item)
    return {
        "rubric_score": 0,
        "max_points": float(rubric.max_points),
        "criteria": [{"criterion_id": criterion.id, "points_awarded": 0.0, "evidence": ""} for criterion in rubric.criteria],
        "fatal_errors": [],
        "local_analysis_md": "x" * 600,
        "repaired_traces": [],
        "error_attributions": [],
    }


def unavailable_arms(*, embedding_ready: bool, workspace_ready: bool) -> dict[str, str]:
    """Arms the routes cannot run, with the honest reason (§12.1)."""

    skipped: dict[str, str] = {}
    if not embedding_ready:
        skipped["c"] = "no ready embedding route (embedding.enabled and an openai_embedding profile)"
    if not workspace_ready:
        skipped["e"] = "the diagnosis provider lacks READ_ONLY_WORKSPACE (Codex SDK only in M1)"
    return skipped


def plan_review(
    vault: LoadedVault,
    repository: Repository,
    options: ReviewOptions,
    *,
    clients: ReviewClients | None = None,
    skip_arms: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Targets and a per-route call/token estimate. Makes no call, writes nothing."""

    skip_arms = dict(skip_arms or {})
    if clients is not None and not skip_arms:
        skip_arms = unavailable_arms(
            embedding_ready=clients.embedding is not None,
            workspace_ready=clients.diagnosis is not None and supports_snapshot(clients.diagnosis),
        )
    options = replace(options, arms=tuple(arm for arm in options.arms if arm not in skip_arms))
    check = data_check(vault, repository)
    eligible = eligible_attempts(vault, repository, since=options.since)
    if options.attempt_ids:
        wanted = set(options.attempt_ids)
        sample = [row for row in eligible if str(row["id"]) in wanted]
        missing = sorted(wanted - {str(row["id"]) for row in sample})
    else:
        sample = select_sample(eligible, options.sample_size, options.seed)
        missing = []
    planted_cases = 0
    if options.planted_manifest is not None:
        manifest_rows = options.planted_manifest.get("cases") if isinstance(options.planted_manifest, Mapping) else options.planted_manifest
        planted_cases = len(manifest_rows or [])
    elif options.generate_planted:
        planted_cases = options.planted_per_shape * len(SHAPES)
    n_real = len(sample)
    targets = n_real + planted_cases
    settings = options.settings
    store = VaultHistoryStore(vault, repository)
    mode_tokens: dict[str, list[int]] = {}
    grading_tokens: list[int] = []
    for row in sample:
        item = vault.practice_items[str(row["practice_item_id"])]
        answer = str(row.get("learner_answer_md") or "")
        context = blind_grading_context(
            vault, item, attempt_id=str(row["id"]), learner_answer_md=answer,
            verifier_observations=[],
        )
        grading_tokens.append(estimate_tokens(blind_grading_prompt(context)))
        current = current_attempt_from(
            vault, item, attempt_id=str(row["id"]), completed_at=str(row["created_at"]),
            learner_answer_md=answer, blind_grade=_placeholder_blind(item, vault),
        )
        for arm in options.arms:
            if arm == "a":
                continue
            mode = ARM_MODES[arm]
            assembled = assemble_diagnosis_context(vault, store, current, settings, mode="exact" if mode in {"snapshot", "hybrid"} else mode)
            tokens = estimate_tokens(diagnosis_prompt(assembled))
            if mode == "snapshot":
                tokens += 20_000  # rough allowance for the files the agent reads
            mode_tokens.setdefault(arm, []).append(tokens)

    def mean(values: Sequence[int], default: int) -> int:
        return int(sum(values) / len(values)) if values else default

    calls: dict[str, int] = {"grading": 0, "diagnosis": 0, "diagnosis_judge": 0, "diagnosis_generator": 0, "embedding": 0}
    tokens: dict[str, int] = {key: 0 for key in calls}
    grade_in = mean(grading_tokens, 6_000)
    blind_calls = targets + (n_real if options.joint_repeat else 0) + planted_cases
    probe_items = min(options.probe_items, n_real) if options.probes else 0
    probe_grades = 3 * probe_items
    calls["grading"] = blind_calls + probe_grades
    tokens["grading"] = calls["grading"] * (grade_in + OUTPUT_ALLOWANCE["grading"])
    diag_calls = 0
    diag_tokens = 0
    for arm in options.arms:
        if arm == "a":
            continue
        per = mean(mode_tokens.get(arm, []), 12_000) + OUTPUT_ALLOWANCE["diagnosis"]
        diag_calls += targets
        diag_tokens += targets * per
    repeat = min(options.repeat_subset, targets) if "b" in options.arms else 0
    diag_calls += repeat + planted_cases
    diag_tokens += (repeat + planted_cases) * (mean(mode_tokens.get("b", []), 12_000) + OUTPUT_ALLOWANCE["diagnosis"])
    sweep_points = (len(options.sweep_budgets) + 1) if options.sweep and "d" in options.arms else 0
    diag_calls += planted_cases * sweep_points
    diag_tokens += planted_cases * sum(
        budget + OUTPUT_ALLOWANCE["diagnosis"]
        for budget in (*options.sweep_budgets, settings.full_history_token_budget)
    ) if sweep_points else 0
    calls["diagnosis"] = diag_calls
    tokens["diagnosis"] = diag_tokens
    if options.judge:
        calls["diagnosis_judge"] = targets * 4 + planted_cases
        tokens["diagnosis_judge"] = calls["diagnosis_judge"] * (8_000 + OUTPUT_ALLOWANCE["diagnosis_judge"])
    calls["diagnosis_generator"] = (planted_cases if options.generate_planted and options.planted_manifest is None else 0) + probe_grades
    tokens["diagnosis_generator"] = calls["diagnosis_generator"] * (3_000 + OUTPUT_ALLOWANCE["diagnosis_generator"])
    if "c" in options.arms:
        failures = sum(1 for attempt in store.all_attempts() if attempt.non_pass)
        calls["embedding"] = math.ceil(failures / 32) + targets
        tokens["embedding"] = (failures + targets) * 300
    return {
        "review_version": REVIEW_VERSION,
        "data_check": check,
        "eligible": len(eligible),
        "sample": [str(row["id"]) for row in sample],
        "missing_attempt_ids": missing,
        "planted_cases": planted_cases,
        "targets": targets,
        "arms": list(options.arms),
        "skipped_arms": {arm: reason for arm, reason in skip_arms.items()},
        "calls": calls,
        "estimated_tokens": tokens,
        "options": options.as_dict(),
        "clients": {
            route: (
                {"provider": getattr(client, "provider_name", None), "model": getattr(client, "model", None) or getattr(client, "model_id", None)}
                if client is not None else None
            )
            for route, client in (
                (("grading", clients.grading), ("diagnosis", clients.diagnosis), ("diagnosis_judge", clients.judge),
                 ("diagnosis_generator", clients.generator), ("embedding", clients.embedding))
                if clients is not None else ()
            )
        },
        "client_notes": dict(clients.notes) if clients is not None else {},
    }


def estimate_spend(plan: Mapping[str, Any], spend: ReviewSpend) -> dict[str, Any]:
    """The plan's admission estimate per route; ``admissible`` false names why."""

    per_route: dict[str, Any] = {}
    total = SpendEstimate(estimated_usd=0.0)
    usd: float | None = 0.0
    reasons: list[str] = []
    for route, calls in plan["calls"].items():
        if not calls:
            continue
        if route not in spend.routes:
            per_route[route] = {"calls": calls, "estimated_tokens": plan["estimated_tokens"][route], "client": None}
            continue
        info = spend.routes[route]
        tokens = int(plan["estimated_tokens"][route])
        estimate = spend.estimate(route, calls=calls, input_tokens=tokens, output_tokens=0)
        cost = None if info.price_per_million is None else tokens * info.price_per_million / 1_000_000
        per_route[route] = {
            **info.as_dict(),
            "calls": calls,
            "estimated_tokens": tokens,
            "estimated_usd": cost,
        }
        if estimate.estimated_usd is None:
            reasons.append(f"unknown price for metered route {route}")
            usd = None
        else:
            total = SpendEstimate(
                calls=total.calls + estimate.calls,
                total_tokens=total.total_tokens + estimate.total_tokens,
                estimated_usd=(total.estimated_usd or 0.0) + estimate.estimated_usd,
            )
            if usd is not None and info.billing == "metered":
                usd += estimate.estimated_usd
    admissible = not reasons
    if admissible:
        try:
            spend.check(total)
        except SpendLimitExceeded as exc:
            admissible = False
            reasons.append(str(exc))
    return {
        "routes": per_route,
        "metered_estimated_usd": usd,
        "total_calls": total.calls,
        "caps": spend.caps.as_dict(),
        "admissible": admissible,
        "reasons": reasons,
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


class ReviewRun:
    """One run directory: the scratch copy, its run row and the spend meter."""

    def __init__(
        self,
        vault: LoadedVault,
        run_dir: Path,
        options: ReviewOptions,
        clients: ReviewClients,
        spend: ReviewSpend,
        *,
        progress: Callable[[str], None] | None = None,
    ) -> None:
        self.vault = vault
        self.run_dir = Path(run_dir)
        self.options = options
        self.clients = clients
        self.spend = spend
        self.progress = progress or (lambda _message: None)
        self.scratch_path = self.run_dir / SCRATCH_FILE
        self.run_id = ""
        self.repository: Repository | None = None
        self.notes: dict[str, Any] = {}
        self._plain_store: VaultHistoryStore | None = None

    def plain_store(self) -> VaultHistoryStore:
        """The scratch copy's history without blind overlays (loaded once)."""

        if self._plain_store is None:
            self._plain_store = VaultHistoryStore(self.vault, self.repository)
        return self._plain_store

    # -- setup ------------------------------------------------------------------

    def open(self, source_sqlite: Path) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        run_file = self.run_dir / RUN_FILE
        if run_file.exists() and self.scratch_path.exists():
            self.run_id = str(json.loads(run_file.read_text(encoding="utf-8"))["run_id"])
            self.repository = Repository.attach(self.scratch_path)
            return
        if self.scratch_path.exists():
            raise ValueError(f"{self.scratch_path} exists without {RUN_FILE}; choose an empty run directory")
        if Path(source_sqlite).resolve() == self.scratch_path.resolve():
            raise ValueError("the run directory must not hold the vault database")
        backup_database(Path(source_sqlite), self.scratch_path)
        self.run_id = new_ulid()
        self.repository = Repository.attach(self.scratch_path)
        with self.repository.connection() as connection:
            has_ledger = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='judgment_ledger'"
            ).fetchone()
        if not has_ledger:
            # Bring the COPY to migration head so the ledger exists; the vault
            # itself is never migrated by a review.
            self.repository = Repository(self.scratch_path)
        with closing(connect(self.scratch_path)) as connection, connection:
            ensure_review_schema(connection, run_id=self.run_id)
            insert_review_row(
                connection,
                "review_runs",
                {
                    "id": self.run_id,
                    "status": "running",
                    "seed": self.options.seed,
                    "plan_json": self.options.as_dict(),
                    "manifest_json": {},
                },
            )
        run_file.write_text(
            json.dumps(
                {"run_id": self.run_id, "review_version": REVIEW_VERSION, "vault_root": str(self.vault.root), "options": self.options.as_dict()},
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        with closing(connect(self.scratch_path)) as connection, connection:
            yield connection

    def _rows(self, table: str, *, order_by: str = "rowid", **where: Any) -> list[dict[str, Any]]:
        scope = {"run_id": self.run_id, **where} if table != "review_context_receipts" else where
        with closing(connect(self.scratch_path, read_only=True)) as connection:
            return review_rows(connection, table, where=scope, order_by=order_by)

    # -- paid call wrapper ------------------------------------------------------

    @contextmanager
    def paid(self, route: str, purpose: str, *, stage: str, input_tokens: int, subject_id: str | None = None, arm: str | None = None) -> Iterator[None]:
        info = self.spend.routes[route]
        with self.spend.request(route, purpose, input_tokens=input_tokens) as call:
            status = "completed"
            started = time.monotonic()
            try:
                yield
            except BaseException:
                status = "failed"
                raise
            finally:
                output_estimate = OUTPUT_ALLOWANCE.get(route, 2_000)
                usage = call.usage
                with self._write() as connection:
                    insert_review_row(
                        connection,
                        "review_calls",
                        {
                            "run_id": self.run_id,
                            "stage": stage,
                            "route": route,
                            "purpose": purpose,
                            "subject_id": subject_id,
                            "arm": arm,
                            "provider": info.provider,
                            "model": info.model,
                            "billing": info.billing,
                            "cost_basis": "estimated_only" if info.billing == "subscription" else "reported",
                            "input_tokens": usage.input_tokens or input_tokens,
                            "output_tokens": usage.output_tokens or None,
                            "cached_input_tokens": usage.cached_input_tokens or None,
                            "reasoning_tokens": usage.reasoning_tokens or None,
                            "estimated_usd": self.spend.call_cost(route, usage, input_tokens, output_estimate),
                            "latency_seconds": round(time.monotonic() - started, 3),
                            "status": status,
                        },
                    )

    def guard_for(self, route: str, *, stage: str, subject_id: str | None, arm: str | None) -> Callable[[str, int], Any]:
        def guard(purpose: str, tokens: int):
            return self.paid(route, purpose, stage=stage, input_tokens=tokens, subject_id=subject_id, arm=arm)

        return guard

    # -- stages -----------------------------------------------------------------

    def stage_targets(self, plan: Mapping[str, Any]) -> None:
        if self._rows("review_targets", kind="real"):
            return
        rows = {str(row["id"]): row for row in eligible_attempts(self.vault, self.repository, since=self.options.since)}
        order = list(plan["sample"])
        random.Random(self.options.seed + 1).shuffle(order)
        with self._write() as connection:
            for position, attempt_id in enumerate(order):
                row = rows[attempt_id]
                insert_review_row(
                    connection,
                    "review_targets",
                    {
                        "id": attempt_id,
                        "run_id": self.run_id,
                        "kind": "real",
                        "attempt_id": attempt_id,
                        "practice_item_id": str(row["practice_item_id"]),
                        "learning_object_id": str(row["learning_object_id"]),
                        "completed_at": str(row["created_at"]),
                        "stratum": str(row["learning_object_id"]),
                        "position": position,
                    },
                )

    def _stage_done(self, name: str) -> bool:
        path = self.run_dir / STAGES_FILE
        return path.exists() and json.loads(path.read_text(encoding="utf-8")).get(name) == "done"

    def _mark_stage(self, name: str) -> None:
        path = self.run_dir / STAGES_FILE
        stages = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        stages[name] = "done"
        path.write_text(json.dumps(stages, indent=2, sort_keys=True), encoding="utf-8")

    def stage_planted(self) -> None:
        # Runs once per run: a resume must not re-draft rejected cases or
        # reshuffle target positions under work that already used them.
        if self._stage_done("planted"):
            return
        self._stage_planted()
        self._mark_stage("planted")

    def _insert_case(self, case: PlantedCase) -> None:
        """Checkpoint one planted case (and its target) as soon as it exists."""

        position = len(self._rows("review_targets"))
        item = self.vault.practice_items[case.target.practice_item_id]
        with self._write() as connection:
            insert_review_row(
                connection,
                "review_planted_cases",
                {
                    "id": case.case_id,
                    "run_id": self.run_id,
                    "shape": case.shape,
                    "target_attempt_id": case.target.attempt_id,
                    "truth_json": case.truth(),
                    "history_json": case.as_record(),
                    "source": case.source,
                },
            )
            insert_review_row(
                connection,
                "review_targets",
                {
                    "id": case.target.attempt_id,
                    "run_id": self.run_id,
                    "kind": "planted",
                    "attempt_id": case.target.attempt_id,
                    "practice_item_id": item.id,
                    "learning_object_id": item.learning_object_id,
                    "completed_at": case.target.completed_at,
                    "stratum": f"planted:{case.shape}",
                    "planted_case_id": case.case_id,
                    "position": position,
                },
            )

    def _stage_planted(self) -> None:
        existing = self._rows("review_planted_cases")
        options = self.options
        if options.planted_manifest is not None:
            if not existing:
                for case in cases_from_manifest(options.planted_manifest, vault=self.vault, start=default_start()):
                    self._insert_case(case)
        elif not options.generate_planted or options.planted_per_shape == 0:
            return
        elif self.clients.generator is None:
            self.notes["planted"] = "skipped: no ready diagnosis_generator route and no --planted-manifest"
            return
        else:
            preferred = [row["learning_object_id"] for row in self._rows("review_targets", kind="real")]
            los = plantable_learning_objects(self.vault, preferred)
            if not los:
                self.notes["planted"] = "skipped: no learning object has two practice items in its neighbourhood"
                return
            counts = {shape: sum(1 for row in existing if row["shape"] == shape) for shape in SHAPES}
            rotation = len(existing)
            for shape in SHAPES:
                tries = 0
                # Up to two drafts per wanted case; a rejected draft is recorded.
                while counts[shape] < options.planted_per_shape and tries < 2 * options.planted_per_shape:
                    tries += 1
                    lo_id = los[rotation % len(los)]
                    rotation += 1
                    prompt, allowed = scenario_request(self.vault, shape, lo_id)
                    try:
                        with self.paid("diagnosis_generator", "diagnosis_planted_scenario", stage="planted", input_tokens=estimate_tokens(prompt), subject_id=lo_id):
                            draft = request_planted_scenario(self.clients.generator, prompt)
                        case = case_from_draft(
                            shape, draft, vault=self.vault, learning_object_id=lo_id, allowed_items=allowed,
                            start=default_start() + timedelta(days=30 * rotation),
                        )
                    except (AIInterrupted, SpendLimitExceeded):
                        raise
                    except (PlantedCaseInvalid, AIProviderUnavailable, ValueError) as exc:
                        self.notes.setdefault("planted_rejected", []).append(
                            {"shape": shape, "learning_object_id": lo_id, "reason": type(exc).__name__, "detail": str(exc)[:200]}
                        )
                        continue
                    self._insert_case(case)
                    counts[shape] += 1
        # Interleave planted targets among the real ones (mixed in unlabelled).
        targets = self._rows("review_targets", order_by="position")
        order = [row["id"] for row in targets]
        random.Random(self.options.seed + 2).shuffle(order)
        with self._write() as connection:
            update_target_positions(connection, {target_id: position for position, target_id in enumerate(order)})

    def planted_cases(self) -> dict[str, PlantedCase]:
        return {
            row["target_attempt_id"]: PlantedCase.from_record(row["history"])
            for row in self._rows("review_planted_cases")
        }

    def target_answer(self, target: Mapping[str, Any], planted: Mapping[str, PlantedCase]) -> str:
        if target["kind"] == "planted":
            return planted[target["attempt_id"]].target.learner_answer_md
        with closing(connect(self.scratch_path, read_only=True)) as connection:
            row = connection.execute("SELECT learner_answer_md FROM practice_attempts WHERE id = ?", (target["attempt_id"],)).fetchone()
        return str(row[0] or "") if row else ""

    def blind_grade(self, *, attempt_id: str, item: PracticeItem, answer: str, purpose: str, stage: str) -> dict[str, Any] | None:
        """Blind-grade one answer once; returns the validated record or None."""

        existing = self._rows("review_blind_grades", attempt_id=attempt_id, purpose=purpose)
        if existing and existing[0]["status"] == "completed":
            return existing[0].get("record")
        if self.clients.grading is None:
            return None
        context = blind_grading_context(
            self.vault, item, attempt_id=attempt_id, learner_answer_md=answer,
            verifier_observations=diagnostic_verifier_observations(answer, item.expected_answer if isinstance(item.expected_answer, str) else json.dumps(item.expected_answer, sort_keys=True)),
        )
        prompt = blind_grading_prompt(context)
        status, record, proposal_json, error = "failed", None, None, None
        try:
            with self.paid("grading", "blind_grading", stage=stage, input_tokens=estimate_tokens(prompt), subject_id=attempt_id):
                proposal = request_blind_grading_proposal(self.clients.grading, context)
            proposal_json = proposal.model_dump(mode="json")
            validated = validate_blind_grading_proposal(
                proposal, attempt_id=attempt_id, item=item, vault=self.vault, learner_answer_md=answer,
            )
            record = validated.as_record()
            status = "completed"
        except (AIInterrupted, SpendLimitExceeded):
            raise
        except (AIProviderUnavailable, GradingValidationError, ValueError) as exc:
            error = type(exc).__name__
        with self._write() as connection:
            insert_review_row(
                connection,
                "review_blind_grades",
                {
                    "run_id": self.run_id,
                    "attempt_id": attempt_id,
                    "purpose": purpose,
                    "status": status,
                    "provider": getattr(self.clients.grading, "provider_name", None),
                    "model": getattr(self.clients.grading, "model", None),
                    "prompt_version": BLIND_GRADING_PROMPT_VERSION,
                    "context_hash": blind_grading_context_hash(context),
                    "proposal_json": proposal_json,
                    "record_json": record,
                    "error": error,
                },
                or_replace=True,
            )
        return record

    def _joint_history(self, item: PracticeItem, prior: Sequence[HistoryAttempt]) -> list[dict[str, Any]]:
        """Today's C4 filter (same facet AND same surface family), as of the attempt."""

        wanted = {self.vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets}
        surface = item.surface_family or item.id
        history = []
        for attempt in reversed(prior):
            previous = self.vault.practice_items.get(attempt.practice_item_id)
            if previous is None or not attempt.learner_answer_md.strip():
                continue
            facets = {self.vault.canonical_facet_id(str(facet)) for facet in previous.evidence_facets}
            if not (wanted & facets) or (previous.surface_family or previous.id) != surface:
                continue
            history.append(
                {
                    "attempt_id": attempt.attempt_id,
                    "learner_trace_md": attempt.learner_answer_md,
                    "created_at": attempt.completed_at,
                    "surface_family": surface,
                    "shared_facets": sorted(wanted & facets),
                }
            )
            if len(history) >= _JOINT_HISTORY_LIMIT:
                break
        history.reverse()
        return history

    def joint_grade(self, *, attempt_id: str, item: PracticeItem, answer: str, prior: Sequence[HistoryAttempt], purpose: str, stage: str) -> tuple[GradingProposal | None, dict[str, Any] | None]:
        """Today's joint grader (C4 history, causal fields) on one answer."""

        existing = self._rows("review_blind_grades", attempt_id=attempt_id, purpose=purpose)
        if existing and existing[0]["status"] == "completed":
            proposal_json = existing[0].get("proposal")
            proposal = GradingProposal.model_validate(proposal_json) if proposal_json else None
            return proposal, existing[0].get("record")
        if self.clients.grading is None:
            return None, None
        base = build_grading_context(self.vault, item, attempt_id=attempt_id, learner_answer_md=answer)
        expected = item.expected_answer if isinstance(item.expected_answer, str) else json.dumps(item.expected_answer, sort_keys=True)
        context = replace(
            base,
            verifier_observations=diagnostic_verifier_observations(answer, expected),
            diagnostic_history=self._joint_history(item, prior),
        )
        prompt = grading_prompt(context)
        status, record, proposal, error = "failed", None, None, None
        try:
            with self.paid("grading", "grading", stage=stage, input_tokens=estimate_tokens(prompt), subject_id=attempt_id, arm="a"):
                proposal = request_grading_proposal(self.clients.grading, context)
            validated = validate_codex_grading_proposal(proposal, attempt_id=attempt_id, item=item, vault=self.vault, learner_answer_md=answer)
            record = {
                "grader_mode": "joint",
                "rubric_score": validated.rubric_score,
                "max_points": float(resolved_rubric(self.vault, item).max_points),
                "criteria": [{"criterion_id": row.criterion_id, "points_awarded": row.points_awarded} for row in validated.criterion_evidence],
                "fatal_errors": list(validated.fatal_errors),
                "first_divergences": [row.first_divergence for row in validated.error_attributions if row.first_divergence],
                "c4_history_attempt_ids": [row["attempt_id"] for row in context.diagnostic_history],
            }
            status = "completed"
        except (AIInterrupted, SpendLimitExceeded):
            raise
        except (AIProviderUnavailable, GradingValidationError, ValueError) as exc:
            error = type(exc).__name__
        with self._write() as connection:
            insert_review_row(
                connection,
                "review_blind_grades",
                {
                    "run_id": self.run_id,
                    "attempt_id": attempt_id,
                    "purpose": purpose,
                    "status": status,
                    "provider": getattr(self.clients.grading, "provider_name", None),
                    "model": getattr(self.clients.grading, "model", None),
                    "prompt_version": GRADING_PROMPT_VERSION,
                    "context_hash": grading_context_hash(context),
                    "proposal_json": proposal.model_dump(mode="json") if proposal is not None else None,
                    "record_json": record,
                    "error": error,
                },
                or_replace=True,
            )
        return proposal, record

    def real_store(self) -> VaultHistoryStore:
        overlay = {
            row["attempt_id"]: row["record"]
            for row in self._rows("review_blind_grades", purpose="primary", status="completed")
            if row.get("record")
        }
        return VaultHistoryStore(self.vault, self.repository, blind_grades=overlay)

    def stage_grades(self) -> None:
        planted = self.planted_cases()
        targets = self._rows("review_targets", order_by="position")
        real_store = self.plain_store()
        for target in targets:
            item = self.vault.practice_items[target["practice_item_id"]]
            answer = self.target_answer(target, planted)
            self.progress(f"blind grade {target['position'] + 1}/{len(targets)}")
            self.blind_grade(attempt_id=target["attempt_id"], item=item, answer=answer, purpose="primary", stage="blind_grading")
            if target["kind"] == "real" and self.options.joint_repeat:
                ref = real_store.ref(target["attempt_id"])
                prior = real_store.attempts_before(ref) if ref is not None else []
                self.joint_grade(attempt_id=target["attempt_id"], item=item, answer=answer, prior=prior, purpose="joint_repeat", stage="joint_repeat")
            if target["kind"] == "planted" and "a" in self.options.arms:
                case = planted[target["attempt_id"]]
                store = planted_history_store(self.vault, case)
                proposal, _record = self.joint_grade(
                    attempt_id=target["attempt_id"], item=item, answer=answer,
                    prior=store.attempts, purpose="joint_planted", stage="joint_planted",
                )
                if proposal is not None and not self._rows("review_diagnoses", target_id=target["id"], arm="a"):
                    view = legacy_view_from_grading_proposal(
                        proposal, history_attempt_ids=[row["attempt_id"] for row in self._joint_history(item, store.attempts)],
                    )
                    self._insert_diagnosis(target["id"], "a", "legacy_view", status="completed", proposal=view, provider=getattr(self.clients.grading, "provider_name", None), model=getattr(self.clients.grading, "model", None), prompt_version=GRADING_PROMPT_VERSION)

    def _insert_diagnosis(self, target_id: str, arm: str, mode: str, *, status: str, proposal: Mapping[str, Any] | None, provider: str | None = None, model: str | None = None, prompt_version: str | None = None, outcome: DiagnosisOutcome | None = None, error: str | None = None) -> str:
        with self._write() as connection:
            diagnosis_id = insert_review_row(
                connection,
                "review_diagnoses",
                {
                    "run_id": self.run_id,
                    "target_id": target_id,
                    "arm": arm,
                    "mode": mode,
                    "status": status,
                    "provider": provider,
                    "model": model,
                    "prompt_version": prompt_version,
                    "proposal_json": dict(proposal) if proposal is not None else None,
                    "validation_report_json": dict(outcome.validation_report) if outcome is not None else {},
                    "anchoring_suspect": bool(outcome.anchoring_suspect) if outcome is not None else False,
                    "unknown_id_count": outcome.unknown_id_count if outcome is not None else 0,
                    "latency_seconds": outcome.latency_seconds if outcome is not None else None,
                    "error": error if error is not None else (outcome.error if outcome is not None else None),
                },
                or_replace=True,
            )
            if outcome is not None:
                receipt = outcome.receipt
                insert_review_row(
                    connection,
                    "review_context_receipts",
                    {
                        "diagnosis_id": diagnosis_id,
                        "context_hash": outcome.context_hash,
                        "failure_attempt_ids_json": receipt.get("failure_attempt_ids") or [],
                        "success_attempt_ids_json": receipt.get("success_attempt_ids") or [],
                        "history_attempt_ids_json": receipt.get("history_attempt_ids") or [],
                        "hypothesis_ids_json": receipt.get("hypothesis_ids") or [],
                        "registry_candidate_ids_json": receipt.get("registry_candidate_ids") or [],
                        "prerequisite_refs_json": receipt.get("prerequisite_refs") or [],
                        "retrieval_json": {key: value for key, value in receipt.items() if key not in {"validated_citations"}},
                        "anchoring_suspect": bool(outcome.anchoring_suspect),
                        "validated_citations_json": outcome.validated_citations,
                    },
                )
        return diagnosis_id

    def _retriever(self) -> EmbeddingHistoryRetriever | None:
        if self.clients.embedding is None:
            return None
        retriever = EmbeddingHistoryRetriever(
            client=self.clients.embedding,
            sqlite_path=self.scratch_path,
            guard=lambda purpose, tokens: self.paid("embedding", purpose, stage="embedding", input_tokens=tokens),
        )
        return retriever

    def _sweep_store(self, case: PlantedCase, base: StaticHistoryStore, budget: int, real: VaultHistoryStore) -> StaticHistoryStore:
        """Planted needles interleaved among real distractors sized to ``budget``."""

        target_item = self.vault.practice_items[case.target.practice_item_id]
        neighborhood = learning_object_neighborhood(self.vault, target_item.learning_object_id)
        wanted = set(neighborhood.all_ids())
        distractors = [attempt for attempt in reversed(real.all_attempts()) if attempt.learning_object_id in wanted]
        needles = list(base.attempts)
        needle_tokens = sum(history_attempt_tokens(attempt, neighborhood, with_answer=attempt.non_pass) for attempt in needles)
        room = max(0, budget - needle_tokens - 6_000)
        chosen: list[HistoryAttempt] = []
        used = 0
        for attempt in distractors:
            cost = history_attempt_tokens(attempt, neighborhood, with_answer=attempt.non_pass)
            if used + cost > room:
                break
            chosen.append(attempt)
            used += cost
        chosen.reverse()
        combined: list[HistoryAttempt] = list(chosen)
        for index, needle in enumerate(needles):
            position = round((index + 1) * (len(combined) + 1) / (len(needles) + 1))
            combined.insert(min(position, len(combined)), needle)
        anchor = datetime.fromisoformat(case.target.completed_at.replace("Z", "+00:00"))
        retimed = []
        for index, attempt in enumerate(combined):
            stamp = (anchor - timedelta(hours=len(combined) - index)).isoformat().replace("+00:00", "Z")
            retimed.append(replace(attempt, completed_at=stamp))
        return StaticHistoryStore(attempts=retimed, hypotheses=list(base.hypotheses))

    def stage_diagnoses(self) -> None:
        options = self.options
        settings = options.settings
        planted = self.planted_cases()
        targets = self._rows("review_targets", order_by="position")
        blind = {
            row["attempt_id"]: row["record"]
            for row in self._rows("review_blind_grades", purpose="primary", status="completed")
            if row.get("record")
        }
        real_store = self.real_store()
        diagnosis_client = self.clients.diagnosis
        retriever = self._retriever() if "c" in options.arms else None
        if "c" in options.arms and retriever is None:
            self.notes["arm_c"] = "skipped: no ready embedding route (embedding.enabled and a ready openai_embedding profile are required)"
        if "e" in options.arms and diagnosis_client is not None and not supports_snapshot(diagnosis_client):
            self.notes["arm_e"] = "skipped: the diagnosis provider lacks READ_ONLY_WORKSPACE (Codex SDK only in M1)"
        if retriever is not None:
            prepared = [attempt for attempt in real_store.all_attempts() if attempt.non_pass]
            for case in planted.values():
                prepared.extend(planted_history_store(self.vault, case).attempts)
            try:
                retriever.prepare(prepared)
            except (AIInterrupted, SpendLimitExceeded):
                raise
            except (AIProviderUnavailable, ValueError) as exc:
                self.notes["embedding_prepare"] = f"failed: {type(exc).__name__}; arm (c) falls back to exact per diagnosis"
        repeat_ids = {row["id"] for row in targets[: options.repeat_subset]}
        for index, target in enumerate(targets):
            record = blind.get(target["attempt_id"])
            item = self.vault.practice_items[target["practice_item_id"]]
            is_planted = target["kind"] == "planted"
            if "a" in options.arms and not is_planted and not self._rows("review_diagnoses", target_id=target["id"], arm="a"):
                view = stored_legacy_view(self.repository, target["attempt_id"])
                self._insert_diagnosis(
                    target["id"], "a", "legacy_view",
                    status="completed" if view is not None else "skipped",
                    proposal=view, error=None if view is not None else "no_stored_joint_diagnosis",
                    prompt_version=GRADING_PROMPT_VERSION,
                )
            if record is None or diagnosis_client is None:
                continue
            answer = self.target_answer(target, planted)
            current = current_attempt_from(
                self.vault, item, attempt_id=target["attempt_id"], completed_at=target["completed_at"],
                learner_answer_md=answer, blind_grade=record,
            )
            store = planted_history_store(self.vault, planted[target["attempt_id"]]) if is_planted else real_store
            rubric = resolved_rubric(self.vault, item)
            runs: list[tuple[str, str, Any, int | None, DiagnosisSettings]] = []
            for arm in ("b", "c", "d", "e"):
                if arm in options.arms:
                    runs.append((arm, ARM_MODES[arm], store, None, settings))
            if "b" in options.arms and target["id"] in repeat_ids:
                runs.append(("b_prime", "exact", store, None, settings))
            if is_planted:
                runs.append(("b0", "exact", StaticHistoryStore(), None, replace(settings, history_error_limit=0, history_success_limit=0)))
                if options.sweep and "d" in options.arms:
                    budgets = sorted(set(options.sweep_budgets) | {settings.full_history_token_budget})
                    for budget in budgets:
                        sweep_store = self._sweep_store(planted[target["attempt_id"]], store, budget, real_store)
                        runs.append((f"d_sweep_{budget}", "full", sweep_store, budget, settings))
            for arm, mode, arm_store, budget, arm_settings in runs:
                done = self._rows("review_diagnoses", target_id=target["id"], arm=arm)
                if done and done[0]["status"] != "failed":
                    continue
                if arm == "c" and retriever is None:
                    self._insert_diagnosis(target["id"], arm, mode, status="skipped", proposal=None, error="embeddings_unavailable")
                    continue
                self.progress(f"diagnose {index + 1}/{len(targets)} arm {arm}")
                outcome = run_diagnosis(
                    diagnosis_client,
                    vault=self.vault,
                    item=item,
                    rubric=rubric,
                    store=arm_store,
                    current=current,
                    settings=arm_settings,
                    mode=mode,
                    retriever=retriever if arm == "c" else None,
                    guard=self.guard_for("diagnosis", stage="diagnosis", subject_id=target["id"], arm=arm),
                    token_budget=budget,
                )
                self._insert_diagnosis(
                    target["id"], arm, mode,
                    status=outcome.status, proposal=outcome.proposal,
                    provider=outcome.provider, model=outcome.model,
                    prompt_version=DIAGNOSIS_PROMPT_VERSION, outcome=outcome,
                )

    # -- judging ----------------------------------------------------------------

    def _ledger_has(self, task: str, left_kind: str, left_id: str, pass_index: int, revision: str) -> bool:
        """Whether this judgment pass ran on exactly these inputs (``revision``)."""

        with closing(connect(self.scratch_path, read_only=True)) as connection:
            rows = connection.execute(
                "SELECT rationale FROM judgment_ledger WHERE task = ? AND left_kind = ? AND left_id = ?",
                (task, left_kind, left_id),
            ).fetchall()
        for row in rows:
            try:
                rationale = json.loads(row[0])
            except (TypeError, ValueError):
                continue
            if rationale.get("pass") == pass_index and rationale.get("revision") == revision:
                return True
        return False

    def _append(self, connection: sqlite3.Connection, **values: Any) -> None:
        append_judgment(
            connection,
            judge="llm",
            judge_model=str(getattr(self.clients.judge, "model", None) or getattr(self.clients.judge, "provider_name", None) or "unknown"),
            **values,
        )

    def _item_view(self, item: PracticeItem) -> dict[str, Any]:
        expected = item.expected_answer
        return {
            "prompt": item.prompt,
            "reference_solution": expected if isinstance(expected, str) else json.dumps(expected, sort_keys=True),
        }

    def stage_judge(self) -> None:
        if not self.options.judge:
            return
        if self.clients.judge is None:
            self.notes["judge"] = "skipped: no ready diagnosis_judge route"
            return
        planted = self.planted_cases()
        targets = self._rows("review_targets", order_by="position")
        for index, target in enumerate(targets):
            rows = self._rows("review_diagnoses", target_id=target["id"])
            diagnoses = judging.judged_arm_rows(rows)
            item = self.vault.practice_items[target["practice_item_id"]]
            answer = self.target_answer(target, planted)
            judged_arms = list(diagnoses)
            revision = judging.diagnosis_judgment_revision(diagnoses)
            if len(judged_arms) >= 2:
                for pass_index in (0, 1):
                    if self._ledger_has("diagnosis_best", "review_target", target["id"], pass_index, revision):
                        continue
                    labels = judging.assign_labels(judged_arms, seed=self.options.seed + index, pass_index=pass_index)
                    arm_to_label = {arm: label for label, arm in labels.items()}
                    pairs = [
                        (arm_to_label[left], arm_to_label[right])
                        if pass_index == 0 else (arm_to_label[right], arm_to_label[left])
                        for left, right in judging.PAIRS_OF_INTEREST
                        if left in arm_to_label and right in arm_to_label
                    ]
                    prompt = judging.diagnosis_judgment_prompt(
                        item=self._item_view(item),
                        learner_answer_md=answer,
                        labelled={label: judging.judge_view(diagnoses[arm]["proposal"]) for label, arm in labels.items()},
                        pairs=pairs,
                    )
                    self.progress(f"judge {index + 1}/{len(targets)} pass {pass_index + 1}")
                    try:
                        with self.paid("diagnosis_judge", "diagnosis_review_judgment", stage="judge", input_tokens=estimate_tokens(prompt), subject_id=target["id"]):
                            verdict = judging.request_diagnosis_judgment(self.clients.judge, prompt)
                    except (AIInterrupted, SpendLimitExceeded):
                        raise
                    except (AIProviderUnavailable, ValueError) as exc:
                        self.notes.setdefault("judge_failures", []).append({"target": target["id"], "pass": pass_index, "error": type(exc).__name__})
                        continue
                    digest = judging.input_hash(prompt)
                    with self._write() as connection:
                        for rating in verdict.ratings:
                            arm = labels.get(rating.label)
                            if arm is None:
                                continue
                            self._append(
                                connection, task="diagnosis_rating", left_kind="review_diagnosis", left_id=diagnoses[arm]["id"],
                                prompt_version=judging.JUDGE_PROMPT_VERSION, input_hash=digest, verdict=rating.rating,
                                rationale=judging.stable_json({"pass": pass_index, "revision": revision, "label": rating.label, "reason": rating.reason}),
                            )
                        for pair in verdict.pairs:
                            left_arm, right_arm = labels.get(pair.left), labels.get(pair.right)
                            if left_arm is None or right_arm is None or left_arm == right_arm:
                                continue
                            first, second, preferred = judging.canonical_pair(left_arm, right_arm, pair.preferred)
                            self._append(
                                connection, task="diagnosis_pairwise", left_kind="review_diagnosis", left_id=diagnoses[first]["id"],
                                right_kind="review_diagnosis", right_id=diagnoses[second]["id"],
                                prompt_version=judging.JUDGE_PROMPT_VERSION, input_hash=digest, verdict=preferred,
                                rationale=judging.stable_json({"pass": pass_index, "revision": revision, "pair": [first, second], "reason": pair.reason}),
                            )
                        best_arm = labels.get(verdict.best)
                        self._append(
                            connection, task="diagnosis_best", left_kind="review_target", left_id=target["id"],
                            prompt_version=judging.JUDGE_PROMPT_VERSION, input_hash=digest,
                            verdict=diagnoses[best_arm]["id"] if best_arm else "none",
                            rationale=judging.stable_json({"pass": pass_index, "revision": revision, "best_arm": best_arm}),
                        )
            self._judge_links(target, rows, answer, item, planted, index)
            if target["kind"] == "planted":
                self._judge_planted(target, rows, planted[target["attempt_id"]], item, answer, index)

    def _judge_links(self, target, rows, answer, item, planted, index) -> None:
        links = judging.cited_links(rows)
        if not links:
            return
        revision = judging.link_judgment_revision(links)
        planted_case = planted.get(target["attempt_id"]) if target["kind"] == "planted" else None
        store = planted_history_store(self.vault, planted_case) if planted_case is not None else None
        cited_rows: dict[str, HistoryAttempt] = {}
        for cited in links:
            attempt = store.attempt(cited) if store is not None else None
            if attempt is None:
                attempt = self.plain_store().attempt(cited)
            if attempt is not None:
                cited_rows[cited] = attempt
        order = sorted(cited_rows)
        for pass_index in (0, 1):
            if self._ledger_has("same_cause_pass", "attempt", target["attempt_id"], pass_index, revision):
                continue
            ordered = order if pass_index == 0 else list(reversed(order))
            labels = {f"L{position + 1}": cited for position, cited in enumerate(ordered)}
            prompt = judging.link_judgment_prompt(
                current={"item": self._item_view(item), "learner_answer_md": answer},
                links={
                    label: {
                        "earlier_item": self.vault.practice_items[cited_rows[cited].practice_item_id].prompt
                        if cited_rows[cited].practice_item_id in self.vault.practice_items else "",
                        "earlier_answer_md": cited_rows[cited].learner_answer_md,
                    }
                    for label, cited in labels.items()
                },
            )
            try:
                with self.paid("diagnosis_judge", "diagnosis_link_judgment", stage="judge_links", input_tokens=estimate_tokens(prompt), subject_id=target["id"]):
                    verdict = judging.request_link_judgment(self.clients.judge, prompt)
            except (AIInterrupted, SpendLimitExceeded):
                raise
            except (AIProviderUnavailable, ValueError) as exc:
                self.notes.setdefault("judge_failures", []).append({"target": target["id"], "links_pass": pass_index, "error": type(exc).__name__})
                continue
            digest = judging.input_hash(prompt)
            with self._write() as connection:
                for row in verdict.links:
                    cited = labels.get(row.label)
                    if cited is None:
                        continue
                    self._append(
                        connection, task="same_cause", left_kind="attempt", left_id=target["attempt_id"],
                        right_kind="attempt", right_id=cited,
                        prompt_version=judging.LINK_JUDGE_PROMPT_VERSION, input_hash=digest, verdict=row.verdict,
                        rationale=judging.stable_json({"pass": pass_index, "revision": revision, "reason": row.reason, "arms": sorted(set(links[cited]["arms"])), "relations": sorted({str(value) for value in links[cited]["relations"]})}),
                    )
                self._append(
                    connection, task="same_cause_pass", left_kind="attempt", left_id=target["attempt_id"],
                    prompt_version=judging.LINK_JUDGE_PROMPT_VERSION, input_hash=digest, verdict="judged",
                    rationale=judging.stable_json({"pass": pass_index, "revision": revision, "links": len(labels)}),
                )

    def _judge_planted(self, target, rows, case: PlantedCase, item, answer, index) -> None:
        statements = judging.planted_statements(rows)
        if not statements:
            return
        revision = judging.planted_judgment_revision(statements)
        if self._ledger_has("planted_cause_pass", "review_target", target["id"], 0, revision):
            return
        ids = sorted(statements)
        random.Random(self.options.seed + 7 + index).shuffle(ids)
        labels = {f"S{position + 1}": diagnosis_id for position, diagnosis_id in enumerate(ids)}
        truth = case.truth()
        prompt = judging.planted_cause_prompt(
            item=self._item_view(item),
            learner_answer_md=answer,
            target_cause=truth["target_cause"],
            other_causes=list(truth["other_causes"].values()),
            labelled_causes={label: statements[diagnosis_id] for label, diagnosis_id in labels.items()},
        )
        try:
            with self.paid("diagnosis_judge", "diagnosis_planted_cause_judgment", stage="judge_planted", input_tokens=estimate_tokens(prompt), subject_id=target["id"]):
                verdict = judging.request_planted_cause_judgment(self.clients.judge, prompt)
        except (AIInterrupted, SpendLimitExceeded):
            raise
        except (AIProviderUnavailable, ValueError) as exc:
            self.notes.setdefault("judge_failures", []).append({"target": target["id"], "planted": True, "error": type(exc).__name__})
            return
        digest = judging.input_hash(prompt)
        with self._write() as connection:
            for row in verdict.matches:
                diagnosis_id = labels.get(row.label)
                if diagnosis_id is None:
                    continue
                self._append(
                    connection, task="planted_cause_match", left_kind="review_diagnosis", left_id=diagnosis_id,
                    prompt_version=judging.PLANTED_JUDGE_PROMPT_VERSION, input_hash=digest, verdict=row.matches,
                    rationale=judging.stable_json({"pass": 0, "revision": revision, "reason": row.reason}),
                )
            self._append(
                connection, task="planted_cause_pass", left_kind="review_target", left_id=target["id"],
                prompt_version=judging.PLANTED_JUDGE_PROMPT_VERSION, input_hash=digest, verdict="judged",
                rationale=judging.stable_json({"pass": 0, "revision": revision}),
            )

    # -- probes -------------------------------------------------------------------

    def stage_probes(self) -> None:
        if not self.options.probes:
            return
        if self.clients.generator is None or self.clients.grading is None:
            self.notes["probes"] = "skipped: the probes need ready diagnosis_generator and grading routes"
            return
        targets = [row for row in self._rows("review_targets", order_by="position") if row["kind"] == "real"]
        seen: list[str] = []
        for target in targets:
            if target["practice_item_id"] not in seen:
                seen.append(target["practice_item_id"])
        items = [self.vault.practice_items[item_id] for item_id in seen if probing.is_reference_bearing(self.vault.practice_items[item_id])]
        items = items[: self.options.probe_items]
        blind = {row["attempt_id"]: row["record"] for row in self._rows("review_blind_grades", purpose="primary", status="completed") if row.get("record")}
        done = {(row["probe"], row["practice_item_id"]) for row in self._rows("review_probes")}
        for position, item in enumerate(items):
            self.progress(f"probes {position + 1}/{len(items)}")
            if ("valid_alternative", item.id) not in done:
                self._probe_valid_alternative(item)
            if ("synthetic_error", item.id) not in done:
                self._probe_synthetic(item)
            if ("paraphrase", item.id) not in done:
                source = next((target for target in targets if target["practice_item_id"] == item.id and target["attempt_id"] in blind), None)
                if source is not None:
                    self._probe_paraphrase(item, source, blind[source["attempt_id"]])

    def _record_probe(self, probe: str, item: PracticeItem, *, status: str, known: float | None, maximum: float | None, blind_score: float | None, detail: Mapping[str, Any]) -> None:
        with self._write() as connection:
            insert_review_row(
                connection,
                "review_probes",
                {
                    "run_id": self.run_id,
                    "probe": probe,
                    "practice_item_id": item.id,
                    "status": status,
                    "known_score": known,
                    "max_points": maximum,
                    "blind_score": blind_score,
                    "detail_json": dict(detail),
                },
                or_ignore=True,
            )

    def _generate(self, purpose: str, prompt: str, request: Callable[[Any, str], Any], subject: str) -> Any | None:
        try:
            with self.paid("diagnosis_generator", purpose, stage="probes", input_tokens=estimate_tokens(prompt), subject_id=subject):
                return request(self.clients.generator, prompt)
        except (AIInterrupted, SpendLimitExceeded):
            raise
        except (AIProviderUnavailable, ValueError):
            return None

    def _probe_valid_alternative(self, item: PracticeItem) -> None:
        maximum = float(resolved_rubric(self.vault, item).max_points)
        draft = self._generate("diagnosis_valid_alternative", probing.valid_alternative_prompt(self.vault, item), probing.request_valid_alternative, item.id)
        if draft is None:
            self._record_probe("valid_alternative", item, status="generation_failed", known=None, maximum=maximum, blind_score=None, detail={})
            return
        check = probing.verify_alternative(item, draft)
        if check["status"] != "verified":
            self._record_probe("valid_alternative", item, status="unverified", known=None, maximum=maximum, blind_score=None, detail=check)
            return
        probe_id = f"probe_{new_ulid()}"
        record = self.blind_grade(attempt_id=probe_id, item=item, answer=draft.derivation_md, purpose="probe_valid_alternative", stage="probes")
        self._record_probe(
            "valid_alternative", item, status="graded" if record else "grading_failed", known=maximum, maximum=maximum,
            blind_score=float(record["rubric_score"]) if record else None,
            detail={**check, "probe_attempt_id": probe_id},
        )

    def _probe_synthetic(self, item: PracticeItem) -> None:
        draft = self._generate("diagnosis_synthetic_error", probing.synthetic_error_prompt(self.vault, item), probing.request_synthetic_error, item.id)
        maximum = float(resolved_rubric(self.vault, item).max_points)
        if draft is None:
            self._record_probe("synthetic_error", item, status="generation_failed", known=None, maximum=maximum, blind_score=None, detail={})
            return
        # The outcome is established from the answer itself (a stated final
        # answer shown to differ from the reference), never from the
        # generator's declaration; only "not full marks" is known.
        check = probing.verify_synthetic_error(self.vault, item, draft)
        if check["status"] != "verified_wrong":
            self._record_probe("synthetic_error", item, status=check["status"], known=None, maximum=maximum, blind_score=None, detail=check)
            return
        probe_id = f"probe_{new_ulid()}"
        record = self.blind_grade(attempt_id=probe_id, item=item, answer=draft.answer_md, purpose="probe_synthetic_error", stage="probes")
        self._record_probe(
            "synthetic_error", item, status="graded" if record else "grading_failed", known=None, maximum=maximum,
            blind_score=float(record["rubric_score"]) if record else None,
            detail={**check, "probe_attempt_id": probe_id},
        )

    def _probe_paraphrase(self, item: PracticeItem, target: Mapping[str, Any], original: Mapping[str, Any]) -> None:
        answer = self.target_answer(target, {})
        draft = self._generate("diagnosis_paraphrase", probing.paraphrase_prompt(self.vault, item, answer), probing.request_paraphrase, item.id)
        maximum = float(resolved_rubric(self.vault, item).max_points)
        if draft is None:
            self._record_probe("paraphrase", item, status="generation_failed", known=None, maximum=maximum, blind_score=None, detail={})
            return
        probe_id = f"probe_{new_ulid()}"
        record = self.blind_grade(attempt_id=probe_id, item=item, answer=draft.answer_md, purpose="probe_paraphrase", stage="probes")
        self._record_probe(
            "paraphrase", item, status="graded" if record else "grading_failed",
            known=float(original.get("rubric_score") or 0.0), maximum=maximum,
            blind_score=float(record["rubric_score"]) if record else None,
            detail={"source_attempt_id": target["attempt_id"], "probe_attempt_id": probe_id},
        )

    # -- finish -------------------------------------------------------------------

    def finish(self, status: str) -> dict[str, Any]:
        manifest = {
            "review_version": REVIEW_VERSION,
            "run_id": self.run_id,
            "algorithm_version": self.vault.config.algorithms.algorithm_version,
            "prompt_versions": {
                "blind_grading": BLIND_GRADING_PROMPT_VERSION,
                "joint_grading": GRADING_PROMPT_VERSION,
                "diagnosis": DIAGNOSIS_PROMPT_VERSION,
                "judge": judging.JUDGE_PROMPT_VERSION,
                "link_judge": judging.LINK_JUDGE_PROMPT_VERSION,
                "planted_judge": judging.PLANTED_JUDGE_PROMPT_VERSION,
            },
            "settings": asdict(self.options.settings),
            "options": self.options.as_dict(),
            "spend": self.spend.summary(),
            "notes": self.notes,
            "client_notes": dict(self.clients.notes),
            "read_only_workspace_supported": bool(
                self.clients.diagnosis is not None and self.clients.diagnosis.supports(READ_ONLY_WORKSPACE)
            ) if self.clients.diagnosis is not None else False,
        }
        with self._write() as connection:
            update_run(connection, self.run_id, status=status, manifest=manifest)
        return manifest


def run_review(
    vault: LoadedVault,
    *,
    source_sqlite: Path,
    run_dir: Path,
    options: ReviewOptions,
    clients: ReviewClients,
    caps: SpendCaps,
    price_per_million: float | None = None,
    cancelled: Callable[[], bool] | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Run (or resume) every stage; returns the manifest and stage status."""

    missing = [route for route, client in (("grading", clients.grading), ("diagnosis", clients.diagnosis)) if client is None]
    if missing:
        # Without a blind grader or a diagnoser there is nothing to review:
        # refuse before copying anything rather than "complete" an empty run.
        return {
            "status": "unavailable",
            "reason": "no ready route for " + ", ".join(missing),
            "client_notes": dict(clients.notes),
            "run_dir": None,
            "run_id": None,
            "estimate": None,
            "manifest": None,
        }
    spend = ReviewSpend(caps, cancelled=cancelled, price_per_million=price_per_million)
    for route, client in (
        ("grading", clients.grading),
        ("diagnosis", clients.diagnosis),
        ("diagnosis_judge", clients.judge),
        ("diagnosis_generator", clients.generator),
        ("embedding", clients.embedding),
    ):
        if client is not None:
            spend.register(route, client)
    resuming = (Path(run_dir) / RUN_FILE).exists()
    plan = plan_review(vault, Repository.attach(source_sqlite, read_only=True), options, clients=clients)
    try:
        estimate = estimate_spend(plan, spend)
    except AIInterrupted:
        return {"status": "cancelled", "run_dir": None, "run_id": None, "estimate": None, "manifest": None}
    if not estimate["admissible"] and not resuming:
        # Refused before anything is copied: a fresh run must fit its caps.
        # A resumed run skips this whole-plan check (finished work is not
        # re-paid); per-request admission still enforces every cap.
        return {"status": "over_budget", "run_dir": None, "run_id": None, "estimate": estimate, "manifest": None}
    run = ReviewRun(vault, run_dir, options, clients, spend, progress=progress)
    run.open(source_sqlite)
    assert run.repository is not None
    spend.collector.sink = lambda action, event: run.repository.record_model_event(
        action, event, owner_kind="diagnosis_review", owner_id=run.run_id
    )
    status = "complete"
    try:
        with spend.collector.observing():
            run.stage_targets(plan)
            run.stage_planted()
            run.stage_grades()
            run.stage_diagnoses()
            run.stage_judge()
            run.stage_probes()
    except (AIInterrupted, KeyboardInterrupt):
        status = "cancelled"
    except SpendLimitExceeded as exc:
        status = "over_budget"
        run.notes["over_budget"] = str(exc)
    manifest = run.finish(status)
    return {"status": status, "run_dir": str(run_dir), "run_id": run.run_id, "estimate": estimate, "manifest": manifest}


__all__ = [
    "REVIEW_ROUTES",
    "resolve_review_clients",
    "route_profiles",
    "ARM_MODES",
    "DEFAULT_SWEEP_BUDGETS",
    "MAIN_ARMS",
    "MIN_SAMPLE",
    "REVIEW_VERSION",
    "RUN_FILE",
    "SCRATCH_FILE",
    "ReviewClients",
    "ReviewOptions",
    "ReviewRun",
    "data_check",
    "eligible_attempts",
    "unavailable_arms",
    "estimate_spend",
    "plan_review",
    "run_review",
    "select_sample",
]
