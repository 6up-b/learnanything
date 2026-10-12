"""Placement state (learner field §5.2): what is assumed known, and what happened.

Everything here is read from immutable rows: ``assumption_decisions`` and
``assumption_returns`` (RECEIPT), ``practice_attempts``, ``reveal_events``,
``coldness_receipts`` and the Slice 1 M2 diagnosis ledgers
(``blind_grade_records``, ``attempt_diagnoses``) with the live diagnose jobs.
An assumption's outcome is never written back; its resolution (the receipt)
names the answer, the reason and what the diagnosis read:

- a miss on the LO after the decision (an answer short of clean full marks)
  is decided by the diagnosis, early or on schedule (owner decision
  2026-10-12): it returns the LO to learning only when the diagnosis
  attributes it to a knowledge gap (``causal_class = learner_state`` on a
  ``valid_measurement`` attribution). A slip, an item-contract or
  grader-interpretation problem, an unassessed (PF-c unverified) criterion or
  no gap attributed keeps the topic: assumed before ``first_review_due``, in
  maintenance from it on (the check resolves, reason recorded);
- while the miss's diagnosis is pending the decision waits (the assumption
  stays open, ``awaiting_diagnosis_attempt_id``); when no diagnosis can arrive
  (``diagnosis.split_enabled = false``, a joint grade, the diagnoser failed,
  was budget-skipped or rejected) today's rule applies (back to learning,
  reason ``no_diagnosis`` with the fallback named). Learner-side help (hints,
  priming, "don't know", assistance) is not a grading question: today's rule,
  reason ``learner_side``;
- a clean answer before ``first_review_due`` is early practice (an explicit,
  learner-requested exception to the review interval): recorded, never the
  check;
- from ``first_review_due`` on, the first clean (or kept) answer that the
  existing independence rule admits (``production_admissibility`` over the
  window since the item's previous attempt or the decision, whichever is
  later, plus any final coldness receipt) resolves it into maintenance; one
  the rule rejects is ineligible and the check waits;
- an "I don't know this" before any of that returns it.

Grades are read from the attempt row, where a blind grade lands like a joint
one and a regrade (which also re-queues the diagnosis) replaces it in place;
``grading_evidence``'s current rows name the unverified criteria.

Each LO's current placement intent is derived from its decisions, returns and
answers in time order (:class:`LearningObjectIntent`): ``assumed`` while an
assumption is open, ``maintenance`` after a passed check until a later miss the
diagnosis attributes to a knowledge gap (decided as above) or "I don't know
this", ``learning`` after a missed check, a lapse or "I don't know this" (with
or without an assumption) until a later explicit "I know this".

"Time order" is the durable ``(created_at, id)`` order across all three
ledgers (:func:`_order`). ``created_at`` has second precision, and every id is
a ULID from the one monotonic generator (``learnloop.ids.new_ulid``), so two
rows written in the same second still sort in the order they were written.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import nullcontext
from dataclasses import asdict, dataclass, field, replace
import json
from typing import Any

from learnloop.algorithm_versions import DIAGNOSIS_SPLIT_VERSIONS, PLACEMENT_VERSIONS
from learnloop.attempts.reveal_ledger import production_admissibility
from learnloop.db.repositories import Repository
from learnloop.field.types import LearnerPredictor
from learnloop.placement.rules import (
    CHECK_PASS,
    FALLBACK_BUDGET_SKIPPED,
    FALLBACK_DIAGNOSIS_FAILED,
    FALLBACK_NOT_BLIND_GRADED,
    FALLBACK_NOT_DIAGNOSED,
    FALLBACK_NOT_NEEDED,
    FALLBACK_REJECTED,
    FALLBACK_SPLIT_DISABLED,
    KEPT_REASONS,
    MISS_KEPT,
    MISS_PENDING,
    MISS_TO_LEARNING,
    PFC_UNVERIFIED_BLOCK,
    REASON_DIAGNOSIS_PENDING,
    REASON_NO_DIAGNOSIS,
    AnswerFacts,
    MissVerdict,
    answer_facts,
    check_verdict,
    decide_miss,
    diagnosis_reason,
    new_material_key,
    prerequisite_layers,
)
from learnloop.vault.models import LoadedVault

#: Placement intents (field §5.2): the routing an LO is under right now.
INTENT_ASSUMED = "assumed"
INTENT_MAINTENANCE = "maintenance"
INTENT_LEARNING = "learning"

PLACEMENT_TABLES = ("assumption_decisions", "assumption_returns", "placement_quick_checks")


def placement_active(vault: LoadedVault) -> bool:
    """F2 serves only at a placement version with the kill switch on."""

    return (
        vault.config.algorithms.algorithm_version in PLACEMENT_VERSIONS
        and bool(vault.config.placement.enabled)
    )


def diagnosis_can_arrive(vault: LoadedVault) -> bool:
    """Whether a queued live diagnosis can still land (``split_grading_active``).

    The post-attempt worker runs a live diagnosis only at a split version with
    ``diagnosis.split_enabled``; otherwise the job waits forever, so placement
    falls back to today's rule instead of waiting (owner decision 2026-10-12).
    """

    config = vault.config
    if config.algorithms.algorithm_version not in DIAGNOSIS_SPLIT_VERSIONS:
        return False
    return bool(getattr(getattr(config, "diagnosis", None), "split_enabled", True))


def initial_probes_enabled(vault: LoadedVault) -> bool:
    """Whether state sync opens an opening diagnostic episode per new LO."""

    return not placement_active(vault) or bool(vault.config.placement.initial_probes)


#: ``probe_episodes.trigger`` of the opening episode earlier versions opened per new LO.
OPENING_EPISODE_TRIGGER = "initial"


def opening_probes_ignored(vault: LoadedVault) -> bool:
    """Whether unanswered opening episodes are ignored (owner decision 2026-10-12).

    Under placement with ``placement.initial_probes = false``, an opening
    episode an earlier version opened and the learner never answered is not an
    open episode for serving, feedback routing or instrument generation.
    Nothing rewrites or closes it until the learner or an error acts on its LO
    (a door that opens an episode adopts it instead:
    ``probe_episodes.adopt_ignored_opening_episode``), so
    ``placement.enabled = false`` restores the predecessor exactly, and
    ``placement.initial_probes = true`` serves opening probes again.
    """

    return placement_active(vault) and not bool(vault.config.placement.initial_probes)


def unanswered_opening_episode_ids(connection: Any, episode_ids: Iterable[str] | None = None) -> frozenset[str]:
    """Open opening episodes exactly as state sync left them: nothing answered,
    nothing adopted.

    Pristine: ``trigger = 'initial'`` with no ``origin`` and no target decision
    (a door that adopts or relocks the episode stamps them: the causal quick
    check, a re-probe, the overconfidence list, a calibration or a golden-path
    baseline), and nothing answered under it ("answered" is
    ``probe_episodes.episode_has_observations``: a recorded probe observation,
    or a presentation the learner consumed, ``submitted``).
    """

    sql = (
        "SELECT e.id FROM probe_episodes e "
        "WHERE e.trigger = ? AND e.status IN ('pending_items', 'in_progress') "
        "AND e.origin IS NULL AND e.target_decision_json IS NULL "
        "AND NOT EXISTS (SELECT 1 FROM probe_presentations p "
        "WHERE p.probe_episode_id = e.id AND p.status = 'submitted') "
        "AND NOT EXISTS (SELECT 1 FROM probe_observations o "
        "JOIN practice_attempts a ON a.id = o.attempt_id "
        "JOIN probe_presentations p ON p.id = a.probe_presentation_id "
        "WHERE p.probe_episode_id = e.id)"
    )
    params: list[Any] = [OPENING_EPISODE_TRIGGER]
    if episode_ids is not None:
        wanted = sorted(set(episode_ids))
        if not wanted:
            return frozenset()
        sql += f" AND e.id IN ({','.join('?' for _ in wanted)})"
        params.extend(wanted)
    return frozenset(str(row[0]) for row in connection.execute(sql, params).fetchall())


def ignored_opening_episode_ids(vault: LoadedVault, repository: Repository) -> frozenset[str]:
    """The opening episodes placement ignores right now (empty when it does not)."""

    if not opening_probes_ignored(vault):
        return frozenset()
    with repository.connection() as connection:
        return unanswered_opening_episode_ids(connection)


def episode_ignored(vault: LoadedVault, repository: Repository, episode: Any) -> bool:
    """Whether this open episode is an unanswered opening episode placement ignores."""

    if episode is None or getattr(episode, "trigger", None) != OPENING_EPISODE_TRIGGER:
        return False
    if not opening_probes_ignored(vault):
        return False
    with repository.connection() as connection:
        return str(episode.id) in unanswered_opening_episode_ids(connection, [str(episode.id)])


def servable_open_episodes(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """``repository.open_probe_episodes()`` without the ignored opening episodes.

    The serving, feedback-routing and instrument-generation doors read this.
    A door that opens an episode on an LO (``enter_episode``, the re-probe
    triggers) adopts an ignored one instead of treating it as taken.
    """

    episodes = repository.open_probe_episodes()
    ignored = ignored_opening_episode_ids(vault, repository)
    if not ignored:
        return episodes
    return {lo: episode for lo, episode in episodes.items() if episode.id not in ignored}


def servable_open_episode(vault: LoadedVault, repository: Repository, learning_object_id: str) -> Any:
    """``repository.open_probe_episode(lo)``, or None when placement ignores it."""

    episode = repository.open_probe_episode(learning_object_id)
    if episode_ignored(vault, repository, episode):
        return None
    return episode


def placement_tables_present(connection: Any) -> bool:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?,?,?)", PLACEMENT_TABLES,
    ).fetchall()
    return len(rows) == len(PLACEMENT_TABLES)


@dataclass(frozen=True)
class Assumption:
    id: str
    learning_object_id: str
    source: str
    trigger_kind: str
    trigger_ref: str | None
    p: float | None
    q_used: float | None
    predictor: str
    predictor_version: str
    first_review_due: str
    quick_check_session_id: str | None
    algorithm_version: str
    created_at: str
    status: str = "open"  # open | passed | failed | returned
    resolved_at: str | None = None
    resolving_attempt_id: str | None = None
    #: Clean answers before ``first_review_due`` (explicit practice): never the check.
    early_answers: int = 0
    #: Clean (or kept) answers from the due date on that the independence rule rejected.
    ineligible_answers: int = 0
    #: Why it resolved (owner decision 2026-10-12): ``clean`` (full marks) or a
    #: kept reason (slip, item_contract, unassessed, no_gap_attributed) for
    #: ``passed``; knowledge_gap, learner_side or no_diagnosis for ``failed``;
    #: i_dont_know_this for ``returned``.
    resolution_reason: str | None = None
    #: The miss that decided it, as the diagnosis read it (the receipt).
    resolution: MissVerdict | None = None
    #: Misses before the due date the diagnosis did not attribute to a knowledge
    #: gap: the LO stayed assumed. ``(attempt id, reason)`` each.
    kept_answers: tuple[tuple[str, str], ...] = ()
    #: A miss whose diagnosis has not landed: the decision waits on it.
    awaiting_diagnosis_attempt_id: str | None = None

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LearningObjectIntent:
    """An LO's current placement routing, derived in time order (never stored)."""

    learning_object_id: str
    intent: str  # assumed | maintenance | learning
    since: str
    #: assumed | check_passed | check_missed | missed_in_maintenance | i_dont_know_this
    reason: str
    assumption_id: str | None = None
    #: Why, in the owner's terms (2026-10-12): for maintenance after the check,
    #: ``clean`` or the kept reason; for learning, knowledge_gap, learner_side,
    #: no_diagnosis or i_dont_know_this. None while assumed.
    outcome_reason: str | None = None
    #: The miss that decided the intent, as the diagnosis read it (the receipt).
    resolution: MissVerdict | None = None
    #: Misses in maintenance the diagnosis did not attribute to a knowledge gap:
    #: the LO stayed in maintenance. ``(attempt id, reason)`` each.
    kept_misses: tuple[tuple[str, str], ...] = ()
    #: A miss whose diagnosis has not landed: the intent waits on it.
    awaiting_diagnosis_attempt_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlacementState:
    active: bool
    assumptions: tuple[Assumption, ...] = ()
    returned_learning_object_ids: frozenset[str] = frozenset()
    answers_by_lo: Mapping[str, tuple[AnswerFacts, ...]] = field(default_factory=dict)
    intent_by_lo: Mapping[str, LearningObjectIntent] = field(default_factory=dict)

    @property
    def open_by_lo(self) -> dict[str, Assumption]:
        return {a.learning_object_id: a for a in self.assumptions if a.is_open}

    @property
    def latest_by_lo(self) -> dict[str, Assumption]:
        latest: dict[str, Assumption] = {}
        for assumption in self.assumptions:  # ordered by (created_at, id)
            latest[assumption.learning_object_id] = assumption
        return latest

    @property
    def decided_learning_object_ids(self) -> frozenset[str]:
        return frozenset(a.learning_object_id for a in self.assumptions)

    def _with_intent(self, intent: str) -> frozenset[str]:
        return frozenset(lo for lo, entry in self.intent_by_lo.items() if entry.intent == intent)

    @property
    def back_to_learning_learning_object_ids(self) -> frozenset[str]:
        """LOs back to learning: a missed check, a miss in maintenance, or "I
        don't know this" (with or without an assumption). New items are served
        again until a later explicit "I know this"."""

        return self._with_intent(INTENT_LEARNING)

    @property
    def maintained_learning_object_ids(self) -> frozenset[str]:
        """LOs whose check passed: in maintenance, remaining learning items withheld."""

        return self._with_intent(INTENT_MAINTENANCE)

    def due_learning_object_ids(self, now_iso: str) -> frozenset[str]:
        return frozenset(lo for lo, a in self.open_by_lo.items() if a.first_review_due <= now_iso)

    @property
    def awaiting_diagnosis_learning_object_ids(self) -> frozenset[str]:
        """LOs whose assumption or maintenance waits on a miss's diagnosis: they
        stay as they are, and no further check item is served meanwhile."""

        waiting = {a.learning_object_id for a in self.assumptions if a.is_open and a.awaiting_diagnosis_attempt_id}
        waiting |= {lo for lo, entry in self.intent_by_lo.items() if entry.awaiting_diagnosis_attempt_id}
        return frozenset(waiting)


def _rows(connection: Any, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(params))
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def _contamination_classes(connection: Any, attempt_ids: Iterable[str]) -> dict[str, str]:
    """Latest recorded contamination class per attempt (most contaminated wins)."""

    wanted = sorted(set(attempt_ids))
    if not wanted:
        return {}
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='causal_activity_classification_events'"
    ).fetchone()
    if exists is None:
        return {}
    from learnloop.causal_activity_policy import CONTAMINATION_PRECEDENCE

    result: dict[str, str] = {}
    for start in range(0, len(wanted), 500):
        chunk = wanted[start:start + 500]
        rows = _rows(
            connection,
            "SELECT attempt_id, contamination_class FROM causal_activity_classification_events "
            f"WHERE attempt_id IN ({','.join('?' for _ in chunk)})",
            chunk,
        )
        for row in rows:
            attempt_id = str(row["attempt_id"])
            current = result.get(attempt_id)
            candidate = str(row["contamination_class"] or "verification")
            if candidate not in CONTAMINATION_PRECEDENCE:
                continue
            if current is None or CONTAMINATION_PRECEDENCE.index(candidate) < CONTAMINATION_PRECEDENCE.index(current):
                result[attempt_id] = candidate
    return result


def _criterion_maxima(connection: Any, contract_ids: Iterable[str]) -> dict[tuple[str, str], float]:
    """``(contract id, criterion id) -> max_points`` from the content-addressed
    assessment contracts the evidence rows were graded against."""

    wanted = sorted({str(value) for value in contract_ids if value})
    maxima: dict[tuple[str, str], float] = {}
    for start in range(0, len(wanted), 500):
        chunk = wanted[start:start + 500]
        rows = connection.execute(
            "SELECT id, contract_json FROM assessment_contract_versions "
            f"WHERE id IN ({','.join('?' for _ in chunk)})",
            chunk,
        ).fetchall()
        for contract_id, contract_json in rows:
            for criterion in (json.loads(contract_json or "{}").get("criteria") or []):
                if criterion.get("id") is not None and criterion.get("max_points") is not None:
                    maxima[(str(contract_id), str(criterion["id"]))] = float(criterion["max_points"])
    return maxima


def pfc_unverified_attempt_ids(connection: Any) -> frozenset[str]:
    """Attempts whose current grade is PF-c unverified (Slice 1 M2).

    The attempt row carries the current grade (a regrade rewrites it in place):
    PF-c's valid-alternative gate sets ``manual_review_reason`` to its block
    reason on the live grade and on a regrade alike. Each criterion's current
    evidence is its latest unsuperseded ``grading_evidence`` row in write
    order (a regrade appends rows and may leave the live grade's rows
    unsuperseded). An attempt qualifies when a current criterion carries the
    gate's ``negative_evidence_blocked`` block and no other current criterion
    is below its maximum: a located error on a verified criterion is still a
    miss. A verified criterion whose maximum cannot be read (no assessment
    contract on the attempt) is not counted as a located error.
    """

    attempt_columns = {row[1] for row in connection.execute("PRAGMA table_info(practice_attempts)").fetchall()}
    evidence_columns = {row[1] for row in connection.execute("PRAGMA table_info(grading_evidence)").fetchall()}
    if "manual_review_reason" not in attempt_columns or not {
        "attribution_json", "assessment_contract_version_id",
    } <= evidence_columns:
        return frozenset()
    candidates = [
        str(row[0])
        for row in connection.execute(
            "SELECT id FROM practice_attempts WHERE manual_review_reason = ? ORDER BY id",
            (PFC_UNVERIFIED_BLOCK,),
        ).fetchall()
    ]
    if not candidates:
        return frozenset()
    current: dict[str, dict[str, Mapping[str, Any]]] = defaultdict(dict)
    contracts: dict[str, set[str]] = defaultdict(set)
    for start in range(0, len(candidates), 500):
        chunk = candidates[start:start + 500]
        rows = _rows(
            connection,
            "SELECT id, attempt_id, criterion_id, points_awarded, attribution_json, "
            "assessment_contract_version_id, superseded_at, created_at FROM grading_evidence "
            f"WHERE attempt_id IN ({','.join('?' for _ in chunk)}) ORDER BY attempt_id, created_at, id",
            chunk,
        )
        for row in rows:
            attempt_id = str(row["attempt_id"])
            if row["assessment_contract_version_id"]:
                contracts[attempt_id].add(str(row["assessment_contract_version_id"]))
            if row["superseded_at"] is None:  # later writes overwrite earlier ones
                current[attempt_id][str(row["criterion_id"])] = row
    maxima = _criterion_maxima(connection, (cid for ids in contracts.values() for cid in ids))

    def unverified(row: Mapping[str, Any]) -> bool:
        try:
            attribution = json.loads(row.get("attribution_json") or "null")
        except ValueError:
            return False
        return isinstance(attribution, dict) and (
            attribution.get("negative_evidence_blocked") == PFC_UNVERIFIED_BLOCK
        )

    def maximum(attempt_id: str, criterion_id: str) -> float | None:
        values = {
            maxima[(contract_id, criterion_id)]
            for contract_id in contracts.get(attempt_id, ())
            if (contract_id, criterion_id) in maxima
        }
        return min(values) if values else None

    result: set[str] = set()
    for attempt_id, rows in current.items():
        if not any(unverified(row) for row in rows.values()):
            continue
        located = any(
            (limit := maximum(attempt_id, criterion_id)) is not None
            and float(row["points_awarded"]) + 1e-9 < limit
            for criterion_id, row in rows.items()
            if not unverified(row)
        )
        if not located:
            result.add(attempt_id)
    return frozenset(result)


def load_answers(
    connection: Any, learning_object_ids: Iterable[str] | None = None,
) -> dict[str, tuple[AnswerFacts, ...]]:
    """Every recorded answer per LO, in (created_at, id) order. Skips excluded."""

    columns = (
        "id, learning_object_id, practice_item_id, attempt_type, correctness, hints_used, "
        "primed, declared_dont_know, manual_review, created_at"
    )
    if learning_object_ids is None:
        rows = _rows(connection, f"SELECT {columns} FROM practice_attempts ORDER BY created_at, id")
    else:
        wanted = sorted(set(learning_object_ids))
        rows = []
        for start in range(0, len(wanted), 500):
            chunk = wanted[start:start + 500]
            rows.extend(_rows(
                connection,
                f"SELECT {columns} FROM practice_attempts "
                f"WHERE learning_object_id IN ({','.join('?' for _ in chunk)})",
                chunk,
            ))
        rows.sort(key=lambda row: (str(row["created_at"]), str(row["id"])))
    classes = _contamination_classes(connection, (str(row["id"]) for row in rows))
    unverified = pfc_unverified_attempt_ids(connection) if rows else frozenset()
    grouped: dict[str, list[AnswerFacts]] = defaultdict(list)
    for row in rows:
        facts = answer_facts(
            row,
            contamination_class=classes.get(str(row["id"])),
            grade_unverified=str(row["id"]) in unverified,
        )
        if facts is not None:
            grouped[facts.learning_object_id].append(facts)
    return {lo: tuple(answers) for lo, answers in grouped.items()}


def _table_present(connection: Any, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def load_miss_verdicts(
    connection: Any,
    answers: Iterable[AnswerFacts],
    *,
    diagnosis_live: bool,
) -> dict[str, MissVerdict]:
    """How the diagnosis decides each graded miss (owner decision 2026-10-12).

    Read from the Slice 1 M2 ledgers the way every other reader does: the
    attempt's latest blind grade, its latest live diagnosis (in force only when
    it completed for that grade, ``Repository._diagnosis_in_force``) and the
    live diagnose jobs. In order:

    - not blind-graded (a joint grade): no diagnosis can arrive, today's rule;
    - a live diagnosis job queued or running while one can arrive: pending;
    - a diagnosis in force: its reading (:func:`placement.rules.diagnosis_reason`);
    - ``diagnosis_live`` false (``diagnosis.split_enabled = false``): today's rule;
    - the latest live diagnosis failed, was budget-skipped, rejected or not
      needed (or none was ever queued): today's rule, saying which.
    """

    wanted = sorted({a.attempt_id for a in answers if a.graded_miss})
    if not wanted:
        return {}
    if not all(_table_present(connection, name) for name in ("blind_grade_records", "attempt_diagnoses", "post_attempt_jobs")):
        return {
            attempt_id: MissVerdict(attempt_id, MISS_TO_LEARNING, REASON_NO_DIAGNOSIS, fallback=FALLBACK_NOT_BLIND_GRADED)
            for attempt_id in wanted
        }
    records: dict[str, dict[str, Any]] = {}
    diagnoses: dict[str, dict[str, Any]] = {}
    open_jobs: dict[str, str] = {}
    for start in range(0, len(wanted), 500):
        chunk = wanted[start:start + 500]
        marks = ",".join("?" for _ in chunk)
        for row in _rows(
            connection,
            f"SELECT id, attempt_id, record_json FROM blind_grade_records WHERE attempt_id IN ({marks}) "
            "ORDER BY attempt_id, created_at, id",
            chunk,
        ):
            records[str(row["attempt_id"])] = row  # the latest wins
        for row in _rows(
            connection,
            "SELECT id, attempt_id, blind_grade_record_id, status, proposal_json, error FROM attempt_diagnoses "
            f"WHERE mode = 'live' AND attempt_id IN ({marks}) ORDER BY attempt_id, created_at, id",
            chunk,
        ):
            diagnoses[str(row["attempt_id"])] = row  # the latest wins
        for row in _rows(
            connection,
            "SELECT attempt_id, state, payload_json FROM post_attempt_jobs "
            f"WHERE kind = 'diagnose' AND state IN ('queued', 'leased') AND attempt_id IN ({marks}) "
            "ORDER BY attempt_id, created_at, id",
            chunk,
        ):
            if str((_json(row["payload_json"], {}) or {}).get("mode") or "live") == "live":
                open_jobs[str(row["attempt_id"])] = str(row["state"])

    verdicts: dict[str, MissVerdict] = {}
    for attempt_id in wanted:
        record = records.get(attempt_id)

        def fallback(reason: str, *, diagnosis_id: str | None = None) -> MissVerdict:
            return MissVerdict(
                attempt_id, MISS_TO_LEARNING, REASON_NO_DIAGNOSIS, fallback=reason, diagnosis_id=diagnosis_id,
                blind_grade_record_id=str(record["id"]) if record is not None else None,
                job_state=open_jobs.get(attempt_id),
            )

        if record is None:
            verdicts[attempt_id] = fallback(FALLBACK_NOT_BLIND_GRADED)
            continue
        if diagnosis_live and attempt_id in open_jobs:
            verdicts[attempt_id] = MissVerdict(
                attempt_id, MISS_PENDING, REASON_DIAGNOSIS_PENDING,
                blind_grade_record_id=str(record["id"]), job_state=open_jobs[attempt_id],
            )
            continue
        latest = diagnoses.get(attempt_id)
        in_force = (
            latest is not None
            and latest["status"] == "completed"
            and (latest["blind_grade_record_id"] is None or str(latest["blind_grade_record_id"]) == str(record["id"]))
        )
        if in_force:
            proposal = _json(latest["proposal_json"], {}) or {}
            attributions = list((_json(record["record_json"], {}) or {}).get("error_attributions") or [])
            scopes = {
                int(row.get("index", position)): str(row.get("validity_scope") or "unknown")
                for position, row in enumerate(attributions) if isinstance(row, Mapping)
            }
            classes = {
                int(event.get("event_index", -1)): str(event.get("causal_class") or "unknown")
                for event in proposal.get("event_diagnoses") or [] if isinstance(event, Mapping)
            }
            reason = diagnosis_reason(scopes, classes)
            verdicts[attempt_id] = MissVerdict(
                attempt_id,
                MISS_TO_LEARNING if reason not in KEPT_REASONS else MISS_KEPT,
                reason,
                diagnosis_id=str(latest["id"]),
                blind_grade_record_id=str(record["id"]),
                events=tuple(
                    (index, scopes.get(index, "unknown"), classes.get(index))
                    for index in sorted(set(scopes) | set(classes))
                ),
            )
            continue
        if not diagnosis_live:
            verdicts[attempt_id] = fallback(FALLBACK_SPLIT_DISABLED)
            continue
        if latest is None:
            verdicts[attempt_id] = fallback(FALLBACK_NOT_DIAGNOSED)
            continue
        status, error = str(latest["status"]), str(latest["error"] or "")
        if status == "skipped" and error == "budget":
            reason = FALLBACK_BUDGET_SKIPPED
        elif status == "skipped" and error == "not_needed":
            reason = FALLBACK_NOT_NEEDED
        elif status == "validation_rejected":
            reason = FALLBACK_REJECTED
        elif status == "failed":
            reason = FALLBACK_DIAGNOSIS_FAILED
        else:
            # Completed for an earlier grade with no re-diagnosis queued.
            reason = FALLBACK_NOT_DIAGNOSED
        verdicts[attempt_id] = fallback(reason, diagnosis_id=str(latest["id"]))
    return verdicts


class _BorrowedRepository(Repository):
    """Repository reads inside the caller's connection and snapshot; never commits."""

    def __init__(self, connection: Any):  # noqa: D107 - no store state beyond the handle
        self._borrowed = connection

    def connection(self):  # type: ignore[override]
        return nullcontext(self._borrowed)


_COLD_DIMENSIONS = ("unassisted", "answer_leakage")


def _final_receipt_veto(connection: Any, attempt_id: str) -> str | None:
    """Why a final coldness receipt makes the attempt non-independent, if it does.

    The cold lane records explicit unassisted and answer-leakage dimensions and
    derives its own ``qualifies_as_cold_retrieval`` claim (delay + unassisted +
    no hard exposure). Any final receipt for the attempt that fails either
    dimension, or that does not qualify the attempt as cold retrieval (False,
    or unknown when the receipt could not be constructed), vetoes it (the
    field's strict rule). None when no receipt exists or every receipt passes."""

    rows = connection.execute(
        "SELECT dimensions_json, derived_json FROM coldness_receipts "
        "WHERE cold_attempt_id = ? AND stage = 'final' ORDER BY id",
        (attempt_id,),
    ).fetchall()
    veto: str | None = None
    for raw_dimensions, raw_derived in rows:
        dimensions = json.loads(raw_dimensions or "{}")
        if any((dimensions.get(name) or {}).get("status") != "pass" for name in _COLD_DIMENSIONS):
            return "coldness_receipt_not_independent"
        if json.loads(raw_derived or "{}").get("qualifies_as_cold_retrieval") is not True:
            veto = "coldness_receipt_not_cold_retrieval"
    return veto


def evaluate_independence(
    connection: Any,
    answers: Iterable[AnswerFacts],
    *,
    since_floor: str | None = None,
) -> tuple[AnswerFacts, ...]:
    """Each answer with its independence facts from the existing rules.

    The window ends at the answer and starts at the item's previous attempt
    (any attempt closes a reveal window, as in the field's coldness rule) or at
    ``since_floor`` (an assumption's decision), whichever is later; with
    neither, any earlier reveal on the item or its LO counts (fail-closed).
    ``production_admissibility`` scans ``reveal_events`` over that window, and a
    final coldness receipt for the attempt must pass its unassisted and
    answer-leakage dimensions and qualify the attempt as cold retrieval.
    """

    repository = _BorrowedRepository(connection)
    evaluated: list[AnswerFacts] = []
    for answer in answers:
        prior = connection.execute(
            "SELECT created_at FROM practice_attempts WHERE practice_item_id = ? "
            "AND (created_at < ? OR (created_at = ? AND id < ?)) ORDER BY created_at DESC, id DESC LIMIT 1",
            (answer.practice_item_id, answer.created_at, answer.created_at, answer.attempt_id),
        ).fetchone()
        bounds = [value for value in (prior[0] if prior else None, since_floor) if value]
        since = max(bounds) if bounds else None
        admissibility = production_admissibility(
            repository,
            practice_item_id=answer.practice_item_id,
            learning_object_id=answer.learning_object_id,
            produced_at=answer.created_at,
            since=since,
        )
        receipt_veto = _final_receipt_veto(connection, answer.attempt_id)
        reason = admissibility.reason or receipt_veto
        evaluated.append(replace(
            answer,
            independent=admissibility.admissible and receipt_veto is None,
            independence_reason=reason,
            reveal_event_id=admissibility.reveal_event_id,
            independence_since=since,
        ))
    return tuple(evaluated)


IndependenceCheck = Callable[[AnswerFacts, str], AnswerFacts]


def _order(created_at: Any, row_id: Any) -> tuple[str, str]:
    """The durable order of a decision, return or answer (module docstring)."""

    return (str(created_at), str(row_id))


def _resolve(
    decision: Mapping[str, Any],
    returns: Sequence[Mapping[str, Any]],
    answers: Sequence[AnswerFacts],
    independence: IndependenceCheck,
    graded: Mapping[str, MissVerdict],
) -> Assumption:
    base = Assumption(
        id=str(decision["id"]),
        learning_object_id=str(decision["learning_object_id"]),
        source=str(decision["source"]),
        trigger_kind=str(decision["trigger_kind"]),
        trigger_ref=decision.get("trigger_ref"),
        p=decision.get("p"),
        q_used=decision.get("q_used"),
        predictor=str(decision["predictor"]),
        predictor_version=str(decision["predictor_version"]),
        first_review_due=str(decision["first_review_due"]),
        quick_check_session_id=decision.get("quick_check_session_id"),
        algorithm_version=str(decision["algorithm_version"]),
        created_at=str(decision["created_at"]),
    )
    returned = min(
        (r for r in returns if r.get("assumption_id") == base.id),
        key=lambda r: _order(r["created_at"], r["id"]),
        default=None,
    )
    returned_at = str(returned["created_at"]) if returned is not None else None
    returned_order = _order(returned["created_at"], returned["id"]) if returned is not None else None
    decided_order = _order(base.created_at, base.id)
    early = ineligible = 0
    kept: list[tuple[str, str]] = []

    def counts() -> dict[str, Any]:
        return {"early_answers": early, "ineligible_answers": ineligible, "kept_answers": tuple(kept)}

    for answer in answers:
        answer_order = _order(answer.created_at, answer.attempt_id)
        if answer_order <= decided_order:
            continue
        if returned_order is not None and returned_order <= answer_order:
            break
        verdict: MissVerdict | None = None
        if not answer.learner_clean:
            # A miss, early or on schedule (an unassessed PF-c grade included):
            # the diagnosis decides it (owner decision 2026-10-12).
            verdict = decide_miss(answer, graded)
            if verdict.outcome == MISS_PENDING:
                if returned_at is not None:
                    # A later "I don't know this" does not wait on the
                    # diagnosis: the learner returned the LO themselves.
                    return replace(
                        base, status="returned", resolved_at=returned_at, resolution_reason="i_dont_know_this",
                        **counts(),
                    )
                # The decision waits on the diagnosis; the LO stays assumed.
                return replace(base, awaiting_diagnosis_attempt_id=answer.attempt_id, **counts())
            if verdict.outcome == MISS_TO_LEARNING:
                # A knowledge gap (or today's rule, said so) quietly returns
                # the LO to learning, early or on schedule.
                return replace(
                    base, status="failed", resolved_at=answer.created_at, resolving_attempt_id=answer.attempt_id,
                    resolution_reason=verdict.reason, resolution=verdict, **counts(),
                )
        if answer.created_at < base.first_review_due:
            # Explicit practice inside the review interval is recorded, but it
            # is a repetition, not the delayed check. A kept miss leaves the LO
            # assumed.
            if verdict is None:
                early += 1
            else:
                kept.append((answer.attempt_id, verdict.reason))
            continue
        checked = independence(answer, base.created_at)
        if verdict is None and check_verdict(checked) == CHECK_PASS:
            return replace(
                base, status="passed", resolved_at=answer.created_at, resolving_attempt_id=answer.attempt_id,
                resolution_reason="clean", **counts(),
            )
        if verdict is not None and checked.independent is True:
            # The diagnosis keeps the topic in maintenance: the check resolves,
            # with the reason on the receipt.
            return replace(
                base, status="passed", resolved_at=answer.created_at, resolving_attempt_id=answer.attempt_id,
                resolution_reason=verdict.reason, resolution=verdict, **counts(),
            )
        # A clean or kept answer the independence rule rejects: the check waits.
        ineligible += 1
    if returned_at is not None:
        return replace(
            base, status="returned", resolved_at=returned_at, resolution_reason="i_dont_know_this", **counts(),
        )
    return replace(base, **counts())


def _intent(
    learning_object_id: str,
    decision: Assumption | None,
    latest_return: Mapping[str, Any] | None,
    answers: Sequence[AnswerFacts],
    graded: Mapping[str, MissVerdict],
) -> LearningObjectIntent | None:
    """The LO's current routing from its latest decision and latest return.

    Whichever of the two comes later in the durable order wins, so an "I know
    this" in the same second as an earlier "I don't know this" supersedes it."""

    if latest_return is not None and (
        decision is None
        or _order(latest_return["created_at"], latest_return["id"]) > _order(decision.created_at, decision.id)
    ):
        linked = latest_return.get("assumption_id")
        return LearningObjectIntent(
            learning_object_id, INTENT_LEARNING, str(latest_return["created_at"]), "i_dont_know_this",
            str(linked) if linked else None, outcome_reason="i_dont_know_this",
        )
    if decision is None:
        return None
    if decision.status == "open":
        return LearningObjectIntent(
            learning_object_id, INTENT_ASSUMED, decision.created_at, "assumed", decision.id,
            awaiting_diagnosis_attempt_id=decision.awaiting_diagnosis_attempt_id,
        )
    if decision.status == "returned":
        return LearningObjectIntent(
            learning_object_id, INTENT_LEARNING, str(decision.resolved_at), "i_dont_know_this", decision.id,
            outcome_reason="i_dont_know_this",
        )
    if decision.status == "failed":
        return LearningObjectIntent(
            learning_object_id, INTENT_LEARNING, str(decision.resolved_at), "check_missed", decision.id,
            outcome_reason=decision.resolution_reason, resolution=decision.resolution,
        )
    # Passed: maintenance until a later miss the diagnosis attributes to a
    # knowledge gap (a lapse) returns it (owner decision 2026-10-12).
    resolving = next(
        (index for index, answer in enumerate(answers) if answer.attempt_id == decision.resolving_attempt_id), None,
    )
    later = answers[resolving + 1:] if resolving is not None else ()
    kept: list[tuple[str, str]] = []
    for answer in later:
        if answer.learner_clean:
            continue
        verdict = decide_miss(answer, graded)
        if verdict.outcome == MISS_PENDING:
            # The intent waits on the diagnosis: still in maintenance.
            return LearningObjectIntent(
                learning_object_id, INTENT_MAINTENANCE, str(decision.resolved_at), "check_passed", decision.id,
                outcome_reason=decision.resolution_reason, resolution=decision.resolution,
                kept_misses=tuple(kept), awaiting_diagnosis_attempt_id=answer.attempt_id,
            )
        if verdict.outcome == MISS_TO_LEARNING:
            return LearningObjectIntent(
                learning_object_id, INTENT_LEARNING, answer.created_at, "missed_in_maintenance", decision.id,
                outcome_reason=verdict.reason, resolution=verdict, kept_misses=tuple(kept),
            )
        kept.append((answer.attempt_id, verdict.reason))
    return LearningObjectIntent(
        learning_object_id, INTENT_MAINTENANCE, str(decision.resolved_at), "check_passed", decision.id,
        outcome_reason=decision.resolution_reason, resolution=decision.resolution, kept_misses=tuple(kept),
    )


def load_placement_state_from_connection(
    connection: Any,
    *,
    active: bool,
    diagnosis_live: bool = True,
) -> PlacementState:
    """Placement state over one connection.

    ``diagnosis_live`` (:func:`diagnosis_can_arrive`) says whether a queued
    diagnosis can still land; when it cannot, a graded miss falls back to
    today's rule instead of waiting. Callers holding the vault pass it.
    """

    if not placement_tables_present(connection):
        return PlacementState(active=active)
    decisions = _rows(connection, "SELECT * FROM assumption_decisions ORDER BY created_at, id")
    returns = _rows(connection, "SELECT * FROM assumption_returns ORDER BY created_at, id")
    los = {str(row["learning_object_id"]) for row in decisions} | {
        str(row["learning_object_id"]) for row in returns
    }
    answers = load_answers(connection, los) if los else {}
    graded = load_miss_verdicts(
        connection, (answer for rows in answers.values() for answer in rows), diagnosis_live=diagnosis_live,
    )

    def independence(answer: AnswerFacts, since_floor: str) -> AnswerFacts:
        return evaluate_independence(connection, (answer,), since_floor=since_floor)[0]

    assumptions = tuple(
        _resolve(decision, returns, answers.get(str(decision["learning_object_id"]), ()), independence, graded)
        for decision in decisions
    )
    latest_decision: dict[str, Assumption] = {}
    for assumption in assumptions:  # ordered by (created_at, id)
        latest_decision[assumption.learning_object_id] = assumption
    latest_return: dict[str, Mapping[str, Any]] = {}
    for row in returns:  # ordered by (created_at, id)
        latest_return[str(row["learning_object_id"])] = row
    intents = {
        lo: intent
        for lo in sorted(los)
        if (
            intent := _intent(lo, latest_decision.get(lo), latest_return.get(lo), answers.get(lo, ()), graded)
        ) is not None
    }
    return PlacementState(
        active=active,
        assumptions=assumptions,
        returned_learning_object_ids=frozenset(str(r["learning_object_id"]) for r in returns),
        answers_by_lo=answers,
        intent_by_lo=intents,
    )


def load_placement_state(vault: LoadedVault, repository: Repository) -> PlacementState:
    with repository.connection() as connection:
        return load_placement_state_from_connection(
            connection, active=placement_active(vault), diagnosis_live=diagnosis_can_arrive(vault),
        )


# -- serving helpers ---------------------------------------------------------


def prerequisite_learning_objects(vault: LoadedVault, learning_object_id: str) -> set[str]:
    """LOs on the concepts this LO declares as prerequisites (field §5.2 order).

    Declared by the LO's own ``prerequisites`` (concept ids) or by a
    ``prerequisite`` relation edge into its concept. Direction is respected;
    no other relation type orders anything (knowledge model §8.1, G5)."""

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return set()
    concepts = set(learning_object.prerequisites)
    concepts.update(
        edge.source for edge in vault.edges
        if edge.relation_type == "prerequisite" and edge.target == learning_object.concept
    )
    concepts.discard(learning_object.concept)
    return {
        lo.id for lo in vault.learning_objects.values() if lo.concept in concepts
    } - {learning_object_id}


def order_new_material(
    vault: LoadedVault,
    predictor: LearnerPredictor,
    items: Sequence[tuple[str, str]],
    *,
    taught_first: Iterable[str] = (),
) -> list[tuple[str, dict[str, float]]]:
    """Order (practice_item_id, learning_object_id) pairs of new material.

    Prerequisite layer first (over the new LOs only), then LOs the learner
    asked confused questions about or needed help on (taught first), then the
    active predictor's predicted success, easiest first; ties by item id.
    Returns each item with the components that explain its place.
    """

    learning_objects = {lo for _item, lo in items}
    layers = prerequisite_layers(
        learning_objects,
        {lo: prerequisite_learning_objects(vault, lo) for lo in learning_objects},
    )
    first = set(taught_first)
    keyed = []
    for item_id, lo in items:
        p = predictor.predict_item(item_id).p_success
        keyed.append((
            new_material_key(
                layer=layers.get(lo, 0), taught_first=lo in first,
                predicted_success=p, practice_item_id=item_id,
            ),
            item_id,
            {
                "placement_layer": float(layers.get(lo, 0)),
                "taught_first": 1.0 if lo in first else 0.0,
                "placement_predicted_success": p,
            },
        ))
    keyed.sort(key=lambda entry: entry[0])
    return [(item_id, components) for _key, item_id, components in keyed]


def choose_check_items(
    predictor: LearnerPredictor,
    candidates: Mapping[str, Sequence[str]],
    *,
    attempted_item_ids: Iterable[str] = (),
) -> dict[str, str]:
    """One first-review item per due assumed LO: a normal cold item.

    Never-attempted items first; among them the median predicted success
    (lower median), so the check is neither the easiest nor the hardest item.
    Ties by item id. Deterministic given the predictor snapshot (G8).
    """

    attempted = set(attempted_item_ids)
    chosen: dict[str, str] = {}
    for lo, item_ids in sorted(candidates.items()):
        pool = sorted(set(item_ids))
        if not pool:
            continue
        fresh = [item_id for item_id in pool if item_id not in attempted]
        pool = fresh or pool
        ranked = sorted(pool, key=lambda item_id: (predictor.predict_item(item_id).p_success, item_id))
        chosen[lo] = ranked[(len(ranked) - 1) // 2]
    return chosen


def assumption_summary(state: PlacementState) -> dict[str, Any]:
    return {
        "active": state.active,
        "open": {lo: a.as_dict() for lo, a in sorted(state.open_by_lo.items())},
        "intents": {lo: entry.as_dict() for lo, entry in sorted(state.intent_by_lo.items())},
        "returned_learning_object_ids": sorted(state.returned_learning_object_ids),
        # Misses whose diagnosis has not landed: these LOs wait as they are.
        "awaiting_diagnosis_learning_object_ids": sorted(state.awaiting_diagnosis_learning_object_ids),
    }
