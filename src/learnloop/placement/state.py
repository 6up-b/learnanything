"""Placement state (learner field §5.2): what is assumed known, and what happened.

Everything here is read from immutable rows: ``assumption_decisions`` and
``assumption_returns`` (RECEIPT), ``practice_attempts``, ``reveal_events``,
``coldness_receipts`` and the Slice 1 M2 diagnosis ledgers
(``blind_grade_records``, ``attempt_diagnoses``), plus two facts of the live
diagnose jobs (WORKFLOW rows, never deleted): when the first was queued, and
the write-once hold stamp the split's kill switch puts on them
(``payload.split_held_at``).
An assumption's outcome is never written back; its resolution (the receipt)
names the answer, the reason and what the diagnosis read:

- a miss on the LO after the decision (an answer short of clean full marks)
  is decided by the diagnosis, early or on schedule (owner decision
  2026-10-12): it is kept only on a positive non-gap reading (a slip, an
  item-contract or grader-interpretation problem, the interaction rather than
  knowledge, or an unassessed PF-c criterion): assumed before
  ``first_review_due``, in maintenance from it on (the check resolves, reason
  recorded). A knowledge gap (``causal_class = learner_state`` on a
  ``valid_measurement`` attribution), or a diagnosis that leaves any part of
  the miss without a non-gap reading (``no_gap_attributed``), returns it to
  learning;
- a miss is decided once (:func:`load_miss_verdicts`), by whichever comes
  first: the first live diagnosis that lands for the grade it read, the kill
  switch holding its diagnosis (``diagnosis.split_enabled = false``), or the
  wait deadline. A later regrade, ``diagnose retry``, re-queue, release or
  switch toggle never reopens or changes it. While none has happened the
  decision waits (the assumption stays open,
  ``awaiting_diagnosis_attempt_id``), at most ``rules.DIAGNOSIS_WAIT_DAYS``
  from the miss's first diagnose job; then, or when no diagnosis can arrive
  (the switch held it, a joint grade, the diagnoser failed, was
  budget-skipped or rejected), today's rule applies (back to learning, reason
  ``no_diagnosis`` with the fallback named). Learner-side help (hints,
  priming, "don't know", assistance) is not a grading question: today's rule,
  reason ``learner_side``, at once, even while an earlier miss waits;
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
``grading_evidence``'s current rows name the unverified criteria. So a regrade
that changes whether an answer is a miss at all is still read live (Phase 6's
merged semantics); one that leaves it a miss does not reopen its decision.

Each miss's decision has a time (``MissVerdict.decided_at``): the deciding
diagnosis row, the hold, the wait deadline, or the answer itself. Learner-side help or
"I don't know this" recorded before an earlier miss's decision landed decides
the outcome, however that diagnosis reads when it lands, so a receipt does not
change after the fact.

PF-c is read from its own records (:func:`pfc_unverified_attempt_ids`):
``grading_evidence``'s current rows carry the unverified stamp, and the latest
blind grade record's ``assessed_shortfall`` says whether anything assessed fell
short.

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
from datetime import timedelta
import json
from typing import Any

from learnloop.algorithm_versions import DIAGNOSIS_SPLIT_VERSIONS, LEARNER_TEXT_GAP_VERSIONS, PLACEMENT_VERSIONS
from learnloop.attempts.reveal_ledger import production_admissibility
from learnloop.clock import FrozenClock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.field.types import LearnerPredictor
from learnloop.placement.rules import (
    CHECK_PASS,
    PFC_UNASSESSED_INTERPRETATION,
    PFC_UNASSESSED_INTERPRETATION_KEY,
    DIAGNOSIS_WAIT_DAYS,
    FALLBACK_BUDGET_SKIPPED,
    FALLBACK_DIAGNOSIS_FAILED,
    FALLBACK_DIAGNOSIS_UNAVAILABLE,
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
    REASON_LEARNER_SIDE,
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
    """Whether a queued live diagnosis can land now (``split_grading_active``).

    The post-attempt worker runs a live diagnosis only at a split version with
    ``diagnosis.split_enabled``; otherwise the job is held, so placement falls
    back to today's rule instead of waiting (owner decision 2026-10-12). The
    first serving build or worker pass that sees the switch off stamps every
    queued live diagnosis held (``Repository.hold_queued_live_diagnoses``,
    write-once), and a held miss stays decided by today's rule when the switch
    comes back on or its diagnosis lands later (Codex re-review F3). No miss
    waits longer than ``placement.rules.DIAGNOSIS_WAIT_DAYS``
    (:func:`load_miss_verdicts`).
    """

    config = vault.config
    if config.algorithms.algorithm_version not in DIAGNOSIS_SPLIT_VERSIONS:
        return False
    return bool(getattr(getattr(config, "diagnosis", None), "split_enabled", True))


def initial_probes_enabled(vault: LoadedVault) -> bool:
    """Whether state sync opens an opening diagnostic episode per new LO."""

    return not placement_active(vault) or bool(vault.config.placement.initial_probes)


#: The source of a created prerequisite's light commitment (learner-text gaps):
#: read as a decision whose delayed check is the created LO's seed item.
LEARNER_TEXT_GAP_SOURCE = "learner_text_gap"


def gap_commitments_active(vault: LoadedVault) -> bool:
    """Created prerequisites' light commitments are read (their creation switch on).

    A live change behind ``learner_text_gaps.create_prerequisites_enabled``,
    not version-gated: the commitments exist only for LOs the pipeline
    created, so off restores the predecessor's routing exactly.
    """

    section = getattr(vault.config, "learner_text_gaps", None)
    return bool(section is not None and section.enabled and section.create_prerequisites_enabled)


def gap_sooner_checks_active(vault: LoadedVault) -> bool:
    """``mvp-0.13``: sooner checks are read (kill switch ``sooner_check_enabled``)."""

    section = getattr(vault.config, "learner_text_gaps", None)
    return bool(
        section is not None
        and vault.config.algorithms.algorithm_version in LEARNER_TEXT_GAP_VERSIONS
        and section.enabled and section.sooner_check_enabled
    )


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
    #: kept reason (slip, item_contract, interaction_context, unassessed) for
    #: ``passed``; knowledge_gap, no_gap_attributed, learner_side or
    #: no_diagnosis for ``failed``; i_dont_know_this for ``returned``.
    resolution_reason: str | None = None
    #: The miss that decided it, as the diagnosis read it (the receipt).
    resolution: MissVerdict | None = None
    #: Misses before the due date the diagnosis did not attribute to a knowledge
    #: gap: the LO stayed assumed. ``(attempt id, reason)`` each.
    kept_answers: tuple[tuple[str, str], ...] = ()
    #: A miss whose diagnosis has not landed: the decision waits on it.
    awaiting_diagnosis_attempt_id: str | None = None
    #: mvp-0.13: the first review was brought forward by a learner-text gap
    #: (``learner_gap_check_advances``); the due date it replaced.
    advanced_from: str | None = None
    advance_id: str | None = None

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
    #: ``clean`` or the kept reason; for learning, knowledge_gap,
    #: no_gap_attributed, learner_side, no_diagnosis or i_dont_know_this. None
    #: while assumed.
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
    #: mvp-0.13: maintenance LOs whose next check a learner-text gap brought
    #: forward and that no answer has taken since it fell due (the advance row).
    gap_check_due_by_lo: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

    def due_gap_check_learning_object_ids(self, now_iso: str) -> frozenset[str]:
        """Maintenance LOs whose brought-forward check is due now."""

        return frozenset(
            lo for lo, advance in self.gap_check_due_by_lo.items()
            if str(advance["advanced_due"]) <= now_iso
            and lo in self.intent_by_lo and self.intent_by_lo[lo].intent == INTENT_MAINTENANCE
        )

    @property
    def advanced_learning_object_ids(self) -> frozenset[str]:
        """Open assumptions whose first review a learner-text gap brought forward."""

        return frozenset(a.learning_object_id for a in self.assumptions if a.is_open and a.advanced_from)

    @property
    def committed_learning_object_ids(self) -> frozenset[str]:
        """Open light commitments: prerequisites created from a learner's text."""

        return frozenset(
            a.learning_object_id for a in self.assumptions if a.is_open and a.source == LEARNER_TEXT_GAP_SOURCE
        )

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


def _latest_grading_supports(connection: Any, attempt_ids: Iterable[str]) -> dict[str, Mapping[str, Any]]:
    """Each attempt's latest blind grade record's ``grading_support``.

    The latest record is the grade that wrote the attempt's current PF-c rows
    (a regrade appends a superseding record beside its new evidence). A
    pre-170 database has no blind grades.
    """

    wanted = sorted({str(value) for value in attempt_ids if value})
    if not wanted or connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='blind_grade_records'"
    ).fetchone() is None:
        return {}
    supports: dict[str, Mapping[str, Any]] = {}
    for start in range(0, len(wanted), 500):
        chunk = wanted[start:start + 500]
        for attempt_id, record_json in connection.execute(
            "SELECT attempt_id, record_json FROM blind_grade_records "
            f"WHERE attempt_id IN ({','.join('?' for _ in chunk)}) ORDER BY attempt_id, created_at, id",
            chunk,
        ).fetchall():
            try:
                record = json.loads(record_json or "{}")
            except ValueError:
                record = {}
            support = record.get("grading_support") if isinstance(record, dict) else None
            supports[str(attempt_id)] = support if isinstance(support, Mapping) else {}
    return supports


def pfc_unverified_attempt_ids(connection: Any) -> frozenset[str]:
    """Attempts whose current grade placement reads as PF-c *unassessed*.

    Read from PF-c's own records, never from ``manual_review_reason``: since
    the PF-c unassessed rule (owner decision 2026-10-12) that reason is a
    non-blocking log, recorded only when it is the grade's sole review concern,
    so a PF-c grade may carry another reason, or none once a review is cleared.

    Each criterion's current evidence is its latest unsuperseded
    ``grading_evidence`` row in write order (a regrade appends rows and may
    leave the live grade's rows unsuperseded). An attempt qualifies when a
    current criterion carries the valid-alternative gate's
    ``negative_evidence_blocked`` stamp and nothing ASSESSED fell short:

    - rows written under the unassessed rule (the stamp names
      ``unverified_interpretation = unassessed``) are read with the gate's own
      verdict, ``grading_support.assessed_shortfall`` on the attempt's latest
      blind grade record (a below-full criterion that is not unverified, or an
      attribution the gate left in force: still a miss);
    - rows written before the rule (Slice 1 M2: an unmarked stamp, no
      ``assessed_shortfall``) keep M2's reading: no other current criterion is
      below its maximum. A verified criterion whose maximum cannot be read (no
      assessment contract on the attempt) is not counted as a located error.
    """

    evidence_columns = {row[1] for row in connection.execute("PRAGMA table_info(grading_evidence)").fetchall()}
    if not {"attribution_json", "assessment_contract_version_id", "superseded_at"} <= evidence_columns:
        return frozenset()
    candidates = [
        str(row[0])
        for row in connection.execute(
            "SELECT DISTINCT attempt_id FROM grading_evidence "
            "WHERE superseded_at IS NULL AND instr(attribution_json, ?) > 0 ORDER BY attempt_id",
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

    def stamp(row: Mapping[str, Any]) -> Mapping[str, Any] | None:
        try:
            attribution = json.loads(row.get("attribution_json") or "null")
        except ValueError:
            return None
        if isinstance(attribution, dict) and attribution.get("negative_evidence_blocked") == PFC_UNVERIFIED_BLOCK:
            return attribution
        return None

    stamped = {
        attempt_id: [value for row in rows.values() if (value := stamp(row)) is not None]
        for attempt_id, rows in current.items()
    }
    stamped = {attempt_id: values for attempt_id, values in stamped.items() if values}
    supports = _latest_grading_supports(connection, stamped)
    result: set[str] = set()
    pre_rule: list[str] = []
    for attempt_id, stamps in stamped.items():
        support = supports.get(attempt_id) or {}
        if (
            any(value.get(PFC_UNASSESSED_INTERPRETATION_KEY) == PFC_UNASSESSED_INTERPRETATION for value in stamps)
            and support.get("valid_alternative_gate_applied")
            and "assessed_shortfall" in support
        ):
            # Written under the unassessed rule: the gate's own verdict.
            if not support["assessed_shortfall"]:
                result.add(attempt_id)
        else:
            pre_rule.append(attempt_id)
    if not pre_rule:
        return frozenset(result)
    # Written before the rule (M2): a located error is a verified criterion
    # below its maximum.
    maxima = _criterion_maxima(connection, (cid for attempt_id in pre_rule for cid in contracts[attempt_id]))

    def maximum(attempt_id: str, criterion_id: str) -> float | None:
        values = {
            maxima[(contract_id, criterion_id)]
            for contract_id in contracts.get(attempt_id, ())
            if (contract_id, criterion_id) in maxima
        }
        return min(values) if values else None

    for attempt_id in pre_rule:
        located = any(
            (limit := maximum(attempt_id, criterion_id)) is not None
            and float(row["points_awarded"]) + 1e-9 < limit
            for criterion_id, row in current[attempt_id].items()
            if stamp(row) is None
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


def _wait_deadline(first_job_at: str | None) -> str | None:
    """The instant a miss stops waiting on its diagnosis (rules.DIAGNOSIS_WAIT_DAYS)."""

    started = parse_utc(first_job_at) if first_job_at else None
    if started is None:
        return None
    return utc_now_iso(FrozenClock(started + timedelta(days=DIAGNOSIS_WAIT_DAYS)))


def load_miss_verdicts(
    connection: Any,
    answers: Iterable[AnswerFacts],
    *,
    diagnosis_live: bool,
    now_iso: str,
) -> dict[str, MissVerdict]:
    """How the diagnosis decides each graded miss (owner decision 2026-10-12).

    A miss is decided once (Codex review F4, re-review F3), by the first of
    three events, each read from a row that does not change once written:

    - the attempt's FIRST live diagnosis that read the blind grade current
      when it landed (``Repository._diagnosis_concerns_grade``; a completed
      one must be in force at landing, ``Repository._diagnosis_in_force``):
      completed, its reading (:func:`placement.rules.diagnosis_reason`);
      failed, budget-skipped, rejected or not needed, today's rule saying
      which. A diagnosis of a grade a regrade had already superseded decides
      nothing;
    - the kill switch holding one of the miss's live diagnose jobs (the first
      ``payload.split_held_at``, write-once): today's rule
      (``split_disabled``), decided at the hold;
    - the wait deadline, ``DIAGNOSIS_WAIT_DAYS`` after the miss's first live
      diagnose job (its ``created_at``), once it has passed: today's rule
      (``diagnosis_unavailable``), decided at the deadline.

    A later regrade, ``diagnose retry``, re-queue, release (``last_error`` is
    never read) or switch toggle never reopens or changes a decided miss.
    Before any of them:

    - not blind-graded (a joint grade): no diagnosis can arrive, today's rule;
    - a live job still queued with the switch off (``diagnosis_live`` false)
      and no hold recorded yet: today's rule (``split_disabled``) as of
      ``now_iso``, so the kill switch applies at once; the next serving build
      or worker pass records the hold, which then decides it;
    - a live job queued (switch on) or leased (in flight): pending;
    - no live job queued: ``not_diagnosed``, with the answer (a blind grade
      means the split was on when it was graded).
    """

    wanted = sorted({a.attempt_id for a in answers if a.graded_miss})
    if not wanted:
        return {}
    if not all(_table_present(connection, name) for name in ("blind_grade_records", "attempt_diagnoses", "post_attempt_jobs")):
        return {
            attempt_id: MissVerdict(attempt_id, MISS_TO_LEARNING, REASON_NO_DIAGNOSIS, fallback=FALLBACK_NOT_BLIND_GRADED)
            for attempt_id in wanted
        }
    records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    diagnoses: dict[str, list[dict[str, Any]]] = defaultdict(list)
    jobs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for start in range(0, len(wanted), 500):
        chunk = wanted[start:start + 500]
        marks = ",".join("?" for _ in chunk)
        for row in _rows(
            connection,
            f"SELECT id, attempt_id, record_json, created_at FROM blind_grade_records WHERE attempt_id IN ({marks}) "
            "ORDER BY attempt_id, created_at, id",
            chunk,
        ):
            records[str(row["attempt_id"])].append(row)
        for row in _rows(
            connection,
            "SELECT id, attempt_id, blind_grade_record_id, status, proposal_json, error, created_at "
            f"FROM attempt_diagnoses WHERE mode = 'live' AND attempt_id IN ({marks}) "
            "ORDER BY attempt_id, created_at, id",
            chunk,
        ):
            diagnoses[str(row["attempt_id"])].append(row)
        for row in _rows(
            connection,
            "SELECT id, attempt_id, state, payload_json, created_at FROM post_attempt_jobs "
            f"WHERE kind = 'diagnose' AND attempt_id IN ({marks}) ORDER BY attempt_id, created_at, id",
            chunk,
        ):
            if str((_json(row["payload_json"], {}) or {}).get("mode") or "live") == "live":
                jobs[str(row["attempt_id"])].append(row)

    def grade_at(rows: Sequence[Mapping[str, Any]], order: tuple[str, str]) -> Mapping[str, Any] | None:
        current = None
        for row in rows:  # ordered by (created_at, id)
            if _order(row["created_at"], row["id"]) <= order:
                current = row
        return current

    verdicts: dict[str, MissVerdict] = {}
    for attempt_id in wanted:
        attempt_records = records.get(attempt_id, [])
        attempt_jobs = jobs.get(attempt_id, [])
        open_job = next((job for job in reversed(attempt_jobs) if job["state"] in ("queued", "leased")), None)
        latest_record = attempt_records[-1] if attempt_records else None

        def fallback(reason: str, *, diagnosis_id: str | None = None, decided_at: str | None = None,
                     decided_ref: str | None = None, record_id: str | None = None) -> MissVerdict:
            return MissVerdict(
                attempt_id, MISS_TO_LEARNING, REASON_NO_DIAGNOSIS, fallback=reason, diagnosis_id=diagnosis_id,
                blind_grade_record_id=record_id or (str(latest_record["id"]) if latest_record is not None else None),
                job_state=str(open_job["state"]) if open_job is not None else None,
                decided_at=decided_at, decided_ref=decided_ref,
            )

        if latest_record is None:
            verdicts[attempt_id] = fallback(FALLBACK_NOT_BLIND_GRADED)
            continue
        deadline = _wait_deadline(min((str(job["created_at"]) for job in attempt_jobs), default=None))
        deciding: Mapping[str, Any] | None = None
        deciding_record: Mapping[str, Any] | None = None
        for row in diagnoses.get(attempt_id, []):
            current = grade_at(attempt_records, _order(row["created_at"], row["id"]))
            current_id = str(current["id"]) if current is not None else None
            if Repository._diagnosis_concerns_grade(row["blind_grade_record_id"], current_id):
                deciding = row
                record_id = row["blind_grade_record_id"]
                deciding_record = next(
                    (r for r in attempt_records if str(r["id"]) == str(record_id)), current,
                ) if record_id is not None else current
                break
        # The first hold the switch put on one of the miss's live jobs
        # (``post_attempt_jobs.payload.split_held_at``, write-once).
        held = min(
            (
                (str(stamp), str(job["id"]))
                for job in attempt_jobs
                if (stamp := (_json(job["payload_json"], {}) or {}).get("split_held_at"))
            ),
            default=None,
        )
        # Whichever came first decides, once (Codex re-review F3): the deciding
        # diagnosis landing, the switch holding the job, or the wait deadline
        # (once it has passed).
        events: list[tuple[tuple[str, str], str]] = []
        if deciding is not None:
            events.append((_order(deciding["created_at"], deciding["id"]), "diagnosis"))
        if held is not None:
            events.append((held, "held"))
        if deadline is not None and (now_iso > deadline or any(order > (deadline, "") for order, _kind in events)):
            events.append(((deadline, ""), "deadline"))
        first = min(events)[1] if events else None
        if first == "deadline":
            # The miss stopped waiting before anything else decided it.
            verdicts[attempt_id] = fallback(FALLBACK_DIAGNOSIS_UNAVAILABLE, decided_at=deadline)
            continue
        if first == "held":
            # The kill switch held its diagnosis: today's rule, decided at the
            # hold. Turning the switch back on, a later release or the
            # diagnosis landing afterwards does not change it.
            assert held is not None
            verdicts[attempt_id] = fallback(FALLBACK_SPLIT_DISABLED, decided_at=held[0], decided_ref=held[1])
            continue
        if first == "diagnosis":
            assert deciding is not None
            decided = {"decided_at": str(deciding["created_at"]), "decided_ref": str(deciding["id"])}
            record_id = str(deciding_record["id"]) if deciding_record is not None else None
            current_id = record_id
            if Repository._diagnosis_in_force(deciding["status"], deciding["blind_grade_record_id"], current_id):
                proposal = _json(deciding["proposal_json"], {}) or {}
                grade = (_json(deciding_record["record_json"], {}) or {}) if deciding_record is not None else {}
                attributions = list(grade.get("error_attributions") or [])
                scopes = {
                    int(row.get("index", position)): str(row.get("validity_scope") or "unknown")
                    for position, row in enumerate(attributions) if isinstance(row, Mapping)
                }
                classes = {
                    int(event.get("event_index", -1)): str(event.get("causal_class") or "unknown")
                    for event in proposal.get("event_diagnoses") or [] if isinstance(event, Mapping)
                }
                # A fatal error no attribution names was never read by the
                # diagnosis (its events key on the attributions).
                named = {str(row.get("error_type")) for row in attributions if isinstance(row, Mapping)}
                unread = sorted({str(error) for error in grade.get("fatal_errors") or []} - named)
                reason = diagnosis_reason(scopes, classes, unread_fatal_errors=unread)
                verdicts[attempt_id] = MissVerdict(
                    attempt_id,
                    MISS_TO_LEARNING if reason not in KEPT_REASONS else MISS_KEPT,
                    reason,
                    diagnosis_id=str(deciding["id"]),
                    blind_grade_record_id=record_id,
                    events=tuple(
                        (index, scopes.get(index, "unknown"), classes.get(index))
                        for index in sorted(set(scopes) | set(classes))
                    ),
                    unread_fatal_errors=tuple(unread),
                    **decided,
                )
                continue
            status, error = str(deciding["status"]), str(deciding["error"] or "")
            if status == "skipped" and error == "budget":
                reason = FALLBACK_BUDGET_SKIPPED
            elif status == "skipped" and error == "not_needed":
                reason = FALLBACK_NOT_NEEDED
            elif status == "validation_rejected":
                reason = FALLBACK_REJECTED
            elif status == "failed":
                reason = FALLBACK_DIAGNOSIS_FAILED
            else:
                reason = FALLBACK_NOT_DIAGNOSED
            verdicts[attempt_id] = fallback(
                reason, diagnosis_id=str(deciding["id"]), record_id=record_id, **decided,
            )
            continue
        if open_job is not None:
            if not diagnosis_live and open_job["state"] == "queued":
                # The switch is off and nothing has recorded the hold yet (the
                # next serving build or worker pass does): today's rule, as of
                # now, so the kill switch applies at once.
                verdicts[attempt_id] = fallback(FALLBACK_SPLIT_DISABLED, decided_at=now_iso)
            else:
                # Waiting on the diagnosis (a leased job is in flight: it lands,
                # or the worker releases it and records the hold).
                verdicts[attempt_id] = MissVerdict(
                    attempt_id, MISS_PENDING, REASON_DIAGNOSIS_PENDING,
                    blind_grade_record_id=str(latest_record["id"]), job_state=str(open_job["state"]),
                )
            continue
        # No live job was queued for it (the grade needed no diagnosis): decided
        # with the answer. The switch plays no part: a blind grade means the
        # split was on when it was graded.
        verdicts[attempt_id] = fallback(FALLBACK_NOT_DIAGNOSED)
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


def _landed(verdict: MissVerdict, answer: AnswerFacts) -> tuple[str, str] | None:
    """When a miss's decision became known, in the durable order: None while
    it is pending; the answer itself when it was known at once (learner-side
    help, an unassessed or joint grade, no diagnosis queued)."""

    if verdict.outcome == MISS_PENDING:
        return None
    if verdict.decided_at is None:
        return _order(answer.created_at, answer.attempt_id)
    return (str(verdict.decided_at), str(verdict.decided_ref or ""))


def _learner_side_before(
    answers: Sequence[AnswerFacts],
    *,
    after: int,
    landed: tuple[str, str] | None,
    stop: tuple[str, str] | None = None,
) -> AnswerFacts | None:
    """The first answer after ``answers[after]`` with learner-side help that was
    recorded before the earlier miss's decision ``landed`` (and before ``stop``,
    a return). Learner-side help is today's rule at once (Codex review F8): it
    returns the LO without waiting on the earlier miss's diagnosis, and the
    decision stays with it however that diagnosis reads when it lands."""

    for later in answers[after + 1:]:
        order = _order(later.created_at, later.attempt_id)
        if (stop is not None and stop <= order) or (landed is not None and landed <= order):
            return None
        if not later.learner_side_clean:
            return later
    return None


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
        advanced_from=decision.get("advanced_from"),
        advance_id=decision.get("advance_id"),
    )
    decided = _order(base.created_at, base.id)
    returned = min(
        (
            r for r in returns
            if r.get("assumption_id") == base.id
            # A light commitment (learner-text gaps) is not an
            # assumption_decisions row, so "I don't know this" records no
            # assumption id for it: a later return on its LO closes it.
            or (
                base.source == LEARNER_TEXT_GAP_SOURCE and not r.get("assumption_id")
                and str(r.get("learning_object_id")) == base.learning_object_id
                and _order(r["created_at"], r["id"]) > decided
            )
        ),
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

    for index, answer in enumerate(answers):
        answer_order = _order(answer.created_at, answer.attempt_id)
        if answer_order <= decided_order:
            continue
        if returned_order is not None and returned_order <= answer_order:
            break
        verdict: MissVerdict | None = None
        if not answer.learner_clean:
            # A miss, early or on schedule (an unassessed PF-c grade included):
            # the diagnosis decides it (owner decision 2026-10-12), once.
            verdict = decide_miss(answer, graded)
            landed = _landed(verdict, answer)
            # While its decision had not landed, learner-side help or "I don't
            # know this" returned the LO without waiting on it.
            helped = _learner_side_before(answers, after=index, landed=landed, stop=returned_order)
            if helped is not None:
                return replace(
                    base, status="failed", resolved_at=helped.created_at, resolving_attempt_id=helped.attempt_id,
                    resolution_reason=REASON_LEARNER_SIDE,
                    resolution=MissVerdict(helped.attempt_id, MISS_TO_LEARNING, REASON_LEARNER_SIDE), **counts(),
                )
            if returned_order is not None and (landed is None or returned_order < landed):
                return replace(
                    base, status="returned", resolved_at=returned_at, resolution_reason="i_dont_know_this",
                    **counts(),
                )
            if verdict.outcome == MISS_PENDING:
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
    for index, answer in enumerate(later):
        if answer.learner_clean:
            continue
        verdict = decide_miss(answer, graded)
        helped = _learner_side_before(later, after=index, landed=_landed(verdict, answer))
        if helped is not None:
            # Learner-side help while this miss's diagnosis had not landed: a
            # lapse at once (Codex review F8).
            return LearningObjectIntent(
                learning_object_id, INTENT_LEARNING, helped.created_at, "missed_in_maintenance", decision.id,
                outcome_reason=REASON_LEARNER_SIDE,
                resolution=MissVerdict(helped.attempt_id, MISS_TO_LEARNING, REASON_LEARNER_SIDE),
                kept_misses=tuple(kept),
            )
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


def _commitment_decisions(connection: Any) -> list[dict[str, Any]]:
    """Created prerequisites' light commitments as decision rows (source
    ``learner_text_gap``): one delayed check, no predictor."""

    from learnloop.db.stores.learner_gaps import commitments

    return [
        {
            "id": str(row["id"]), "learning_object_id": str(row["learning_object_id"]),
            "source": LEARNER_TEXT_GAP_SOURCE, "trigger_kind": "learner_text_gap", "trigger_ref": row["gap_id"],
            "p": None, "q_used": None, "predictor": "none", "predictor_version": "none",
            "first_review_due": str(row["first_review_due"]), "quick_check_session_id": None,
            "algorithm_version": str(row["algorithm_version"]), "created_at": str(row["created_at"]),
        }
        for row in commitments(connection)
    ]


def _advance_decisions(connection: Any, decisions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """mvp-0.13: bring each assumption's first review forward to its earliest
    learner-text-gap advance; returns (decisions, maintenance advances)."""

    from learnloop.db.stores.learner_gaps import check_advances

    advances = check_advances(connection)
    by_assumption: dict[str, dict[str, Any]] = {}
    maintenance: list[dict[str, Any]] = []
    for advance in advances:
        if advance["intent"] == INTENT_MAINTENANCE:
            maintenance.append(advance)
            continue
        key = str(advance.get("assumption_id") or "")
        current = by_assumption.get(key)
        if current is None or str(advance["advanced_due"]) < str(current["advanced_due"]):
            by_assumption[key] = advance
    out = []
    for decision in decisions:
        advance = by_assumption.get(str(decision["id"]))
        if advance is not None and str(advance["advanced_due"]) < str(decision["first_review_due"]):
            decision = {**decision, "first_review_due": str(advance["advanced_due"]),
                        "advanced_from": str(decision["first_review_due"]), "advance_id": str(advance["id"])}
        out.append(decision)
    return out, maintenance


def _pending_maintenance_checks(
    advances: Sequence[Mapping[str, Any]],
    intents: Mapping[str, LearningObjectIntent],
    answers: Mapping[str, Sequence[AnswerFacts]],
) -> dict[str, Mapping[str, Any]]:
    """Per maintenance LO, its earliest advance written in this maintenance
    spell that no answer has taken since it fell due."""

    pending: dict[str, Mapping[str, Any]] = {}
    for advance in advances:
        lo = str(advance["learning_object_id"])
        intent = intents.get(lo)
        if intent is None or intent.intent != INTENT_MAINTENANCE or str(advance["created_at"]) < str(intent.since):
            continue
        due = str(advance["advanced_due"])
        if any(answer.created_at >= due for answer in answers.get(lo, ())):
            continue
        current = pending.get(lo)
        if current is None or due < str(current["advanced_due"]):
            pending[lo] = advance
    return pending


def load_placement_state_from_connection(
    connection: Any,
    *,
    active: bool,
    diagnosis_live: bool,
    now_iso: str,
    gap_commitments: bool = False,
    gap_checks: bool = False,
) -> PlacementState:
    """Placement state over one connection.

    ``diagnosis_live`` (:func:`diagnosis_can_arrive`) says whether a queued
    diagnosis can land now; when it cannot, a graded miss falls back to
    today's rule instead of waiting. ``now_iso`` bounds the wait
    (``rules.DIAGNOSIS_WAIT_DAYS``). Both are required (Codex review F9): a
    caller that forgot one would silently wait on held jobs, or forever.
    :func:`load_placement_state` reads both from the vault.

    Learner-text gaps: ``gap_commitments`` adds created prerequisites' light
    commitments (:func:`gap_commitments_active`); ``gap_checks`` applies
    mvp-0.13's sooner checks (:func:`gap_sooner_checks_active`). Both default
    off, so every other caller reads exactly the predecessor's state.
    """

    if not placement_tables_present(connection):
        return PlacementState(active=active)
    decisions = _rows(connection, "SELECT * FROM assumption_decisions ORDER BY created_at, id")
    if gap_commitments:
        decisions = sorted(
            [*decisions, *_commitment_decisions(connection)],
            key=lambda row: _order(row["created_at"], row["id"]),
        )
    maintenance_advances: list[dict[str, Any]] = []
    if gap_checks:
        decisions, maintenance_advances = _advance_decisions(connection, decisions)
    returns = _rows(connection, "SELECT * FROM assumption_returns ORDER BY created_at, id")
    los = {str(row["learning_object_id"]) for row in decisions} | {
        str(row["learning_object_id"]) for row in returns
    }
    answers = load_answers(connection, los) if los else {}
    graded = load_miss_verdicts(
        connection, (answer for rows in answers.values() for answer in rows),
        diagnosis_live=diagnosis_live, now_iso=now_iso,
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
        gap_check_due_by_lo=_pending_maintenance_checks(maintenance_advances, intents, answers),
    )


def load_placement_state(
    vault: LoadedVault, repository: Repository, *, now_iso: str | None = None,
) -> PlacementState:
    """Placement state for a vault; ``now_iso`` defaults to the wall clock."""

    with repository.connection() as connection:
        return load_placement_state_from_connection(
            connection, active=placement_active(vault), diagnosis_live=diagnosis_can_arrive(vault),
            now_iso=now_iso or utc_now_iso(), gap_commitments=gap_commitments_active(vault),
            gap_checks=gap_sooner_checks_active(vault),
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
