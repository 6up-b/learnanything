"""Pure placement rules (learner field §5.2): no store, model or vault access.

The fast-track predicate mirrors report 2's simulation (``field.evaluation``):
an LO's first answers must all be cold, unhinted, unprimed, unhelped and
full-marks, at least ``min_correct`` of them, with no help or confusion signal
on the LO (``field.signals.blocks_fast_track``, the one shared rule), and the
active predictor must give ``P(theta_L > theta_known) >= q``.

Every input a decision reads is a plain value here, so a stored receipt can be
replayed through :func:`fast_track_verdict` to recompute it (G8).

Independence is the existing rule, not a new one: ``placement.state`` asks
``attempts.reveal_ledger.production_admissibility`` (and any final coldness
receipt) for each answer it is about to count and stores the result on the
answer's facts. An answer whose independence was never evaluated is not clean:
the rule fails closed.

Grades are read as the Slice 1 split records them: a blind grade and a regrade
both land on the attempt row (a regrade in place), and PF-c's unverified
criteria are no failure evidence. An answer whose only shortfall is on
criteria the valid-alternative gate recorded unverified is *unassessed*
(:attr:`AnswerFacts.unassessed`): no failure evidence, skipped by fast-track
and the quick check, as the field's outcome view leaves it unmeasured until it
is reviewed. At the first review (and in maintenance) it keeps the topic, with
the reason ``unassessed`` (owner decision 2026-10-12, :func:`decide_miss`).

Misses on an assumed or maintained LO are decided by the diagnosis, not by
full marks (:func:`decide_miss`, :func:`diagnosis_reason`).
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from math import erf, isfinite, log, sqrt
from typing import Any

from learnloop.field.types import RegionEstimate

RULES_VERSION = "placement-rules-v3"

#: A graded answer that can count toward fast-track (or pass a first review):
#: an ordinary independent answer, a free-text answer, a diagnostic probe
#: administration or a held-out exam answer. Hinted, self-reported, imported,
#: walkthrough-reconstructed, dont-know and teach-back attempts never count.
CLEAN_ATTEMPT_TYPES = frozenset({"independent_attempt", "open_text", "diagnostic_probe", "exam_attempt"})
#: Recorded attempts that are not answers at all (no row in report 2 either).
IGNORED_ATTEMPT_TYPES = frozenset({"skip", "guided_walkthrough"})
#: Contamination classes in which instruction reached the attempt.
ASSISTED_CLASSES = frozenset({"repair_activity", "instructional_diagnostic"})
#: The ``negative_evidence_blocked`` reason PF-c's valid-alternative gate
#: persists on an unverified criterion's grading evidence. The same value as
#: ``substrate.canonical_projection.UNVERIFIED_CRITERION_BLOCK`` (pinned by a
#: test): placement may not import ``substrate``, which already imports it.
PFC_UNVERIFIED_BLOCK = "valid_alternative_unverified"
_FULL_MARKS = 1.0 - 1e-9


def theta_known(known_probability: float) -> float:
    """logit(known_probability), on the ability scale (field D6: logit(.75))."""

    return log(known_probability / (1.0 - known_probability))


@dataclass(frozen=True)
class AnswerFacts:
    """The facts of one recorded answer that placement reads, and nothing else."""

    attempt_id: str
    learning_object_id: str
    practice_item_id: str
    created_at: str
    attempt_type: str
    correctness: float | None
    hints_used: int
    primed: bool
    dont_know: bool
    manual_review: bool
    assisted_class: bool
    #: ``production_admissibility`` (plus any final coldness receipt) over the
    #: window that ends at this answer. ``None``: not evaluated, never clean.
    independent: bool | None = None
    independence_reason: str | None = None
    reveal_event_id: str | None = None
    #: Start of the window the independence check scanned (exclusive).
    independence_since: str | None = None
    #: PF-c (Slice 1 M2): the current grade falls short only on criteria the
    #: valid-alternative gate recorded unverified (the final answer verified;
    #: no error was located). Not a measurement until it is reviewed.
    grade_unverified: bool = False

    @property
    def learner_side_clean(self) -> bool:
        """No help on the learner's side, whatever the grade: a graded answer
        type with no hints, priming, "don't know" or assistance."""

        return (
            self.attempt_type in CLEAN_ATTEMPT_TYPES
            and self.hints_used == 0
            and not self.primed
            and not self.dont_know
            and not self.assisted_class
        )

    @property
    def learner_clean(self) -> bool:
        """Full marks with no help on the learner's side: no hints, priming,
        "don't know", assistance or manual-review flag, on a graded answer
        whose grade is verified (never a PF-c unverified one)."""

        return (
            self.learner_side_clean
            and self.correctness is not None
            and isfinite(self.correctness)
            and self.correctness >= _FULL_MARKS
            and not self.manual_review
            and not self.grade_unverified
        )

    @property
    def unassessed(self) -> bool:
        """A learner-clean answer whose grade is PF-c unverified: no failure
        evidence. It never counts toward (or blocks) fast-track and the quick
        check; at the first review it keeps the topic (:func:`decide_miss`)."""

        return self.grade_unverified and self.learner_side_clean

    @property
    def is_miss(self) -> bool:
        """An answer the learner did not answer cleanly. An unassessed answer is
        not one. Whether a miss returns an assumed or maintained LO to learning
        is decided by :func:`decide_miss` (the diagnosis), not by this flag."""

        return not self.learner_clean and not self.unassessed

    @property
    def graded_miss(self) -> bool:
        """A miss whose only problem is the grade: no help on the learner's
        side, but short of full marks (or flagged for review). The diagnosis
        decides what it means (owner decision 2026-10-12)."""

        return self.learner_side_clean and not self.learner_clean and not self.unassessed

    @property
    def clean_correct(self) -> bool:
        """Learner-clean and independent: what fast-track and a quick check count."""

        return self.learner_clean and self.independent is True

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "clean_correct": self.clean_correct}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> AnswerFacts:
        return cls(**{key: value[key] for key in cls.__dataclass_fields__ if key in value})


def answer_facts(
    row: Mapping[str, Any],
    *,
    contamination_class: str | None = None,
    grade_unverified: bool = False,
) -> AnswerFacts | None:
    """Facts of a ``practice_attempts`` row, or None for a non-answer (skip)."""

    attempt_type = str(row["attempt_type"])
    if attempt_type in IGNORED_ATTEMPT_TYPES:
        return None
    correctness = row.get("correctness")
    return AnswerFacts(
        attempt_id=str(row["id"]),
        learning_object_id=str(row["learning_object_id"]),
        practice_item_id=str(row["practice_item_id"]),
        created_at=str(row["created_at"]),
        attempt_type=attempt_type,
        correctness=None if correctness is None else float(correctness),
        hints_used=int(row.get("hints_used") or 0),
        primed=bool(row.get("primed")),
        dont_know=attempt_type == "dont_know" or bool(row.get("declared_dont_know")),
        manual_review=bool(row.get("manual_review")),
        assisted_class=contamination_class in ASSISTED_CLASSES,
        grade_unverified=grade_unverified,
    )


def known_probability(region: RegionEstimate | None, threshold: float) -> float | None:
    """P(theta_L > threshold) under a calibrated region; None when untested.

    The same arithmetic as report 2 (``field.evaluation._known_probability``).
    """

    if region is None or region.untested:
        return None
    if not isfinite(region.mean) or not isfinite(region.variance) or region.variance < 0:
        raise ValueError("invalid calibrated region uncertainty")
    if region.variance == 0:
        return float(region.mean > threshold)
    return (1 + erf((region.mean - threshold) / sqrt(2 * region.variance))) / 2


def interval_80(region: RegionEstimate | None) -> list[float] | None:
    """The central 80% interval of theta_L, in logits."""

    if region is None or region.untested:
        return None
    half = 1.2815515655446004 * sqrt(max(region.variance, 0.0))
    return [region.mean - half, region.mean + half]


@dataclass(frozen=True)
class FastTrackVerdict:
    fires: bool
    reason: str
    clean_answers: int
    p: float | None


def fast_track_verdict(
    answers: Iterable[AnswerFacts],
    *,
    blocking_signal_ids: Iterable[str],
    region: RegionEstimate | None,
    min_correct: int,
    q: float,
    known_threshold: float,
) -> FastTrackVerdict:
    """Field §5.2 fast-track on an LO's answers so far, in time order.

    Unassessed answers (PF-c unverified grades) are skipped: they neither count
    toward the minimum nor block, as the field leaves them unmeasured."""

    answers = tuple(answer for answer in answers if not answer.unassessed)
    if any(not answer.learner_clean for answer in answers):
        return FastTrackVerdict(False, "non_clean_answer", 0, None)
    if any(answer.independent is not True for answer in answers):
        # A clean-looking answer the independence rule rejects (a solution was
        # revealed on the item or its LO in its window) is not evidence of
        # knowing: it never counts toward fast-track or a quick check.
        return FastTrackVerdict(False, "not_independent", 0, None)
    if len(answers) < min_correct:
        return FastTrackVerdict(False, "too_few_answers", len(answers), None)
    if tuple(blocking_signal_ids):
        # Help before starting, a confusion question or a suspected leak on the
        # LO: it is taught, never fast-tracked on early answers (field §3.1).
        return FastTrackVerdict(False, "blocked_by_signal", len(answers), None)
    p = known_probability(region, known_threshold)
    if p is None:
        return FastTrackVerdict(False, "untested", len(answers), None)
    if p < q:
        return FastTrackVerdict(False, "below_threshold", len(answers), p)
    return FastTrackVerdict(True, "fires", len(answers), p)


CHECK_PASS = "pass"
CHECK_FAIL = "fail"
CHECK_INELIGIBLE = "ineligible"


def check_verdict(answer: AnswerFacts) -> str:
    """The first review is a normal cold item: the verdict on its grade alone.

    ``pass``: a clean full-marks answer that the independence rule admits (the
    complement of report 2's miss, ``outcome < 1``). ``fail``: anything the
    learner did not answer cleanly (partial marks, hints, priming, "don't
    know", assistance). ``ineligible``: a clean answer the independence rule
    rejects, or an unassessed one (a PF-c unverified grade). ``independence``
    must already be evaluated for the check's window.

    What a ``fail`` or an unassessed answer does to the LO is the diagnosis's
    call (:func:`decide_miss`, owner decision 2026-10-12): only a knowledge gap
    returns it to learning.
    """

    if answer.unassessed:
        return CHECK_INELIGIBLE
    if not answer.learner_clean:
        return CHECK_FAIL
    if answer.independent is not True:
        return CHECK_INELIGIBLE
    return CHECK_PASS


# -- misses on an assumed or maintained LO: decided by the diagnosis ----------
#
# Owner decision 2026-10-12 (Slice A Phase 6 open question 3): the first-review
# check and a lapse in maintenance are decided by the diagnosis, not by full
# marks. Sometimes the question does not make clear what the rubric expects of
# a perfect answer, so a miss can just mean the learner did not know it had to
# be stated explicitly.

#: What a miss does to the LO.
MISS_TO_LEARNING = "learning"  # back to learning (new items served again)
MISS_KEPT = "kept"  # stays assumed (early) or in maintenance, reason recorded
MISS_PENDING = "pending"  # the diagnosis has not landed: the decision waits

#: Why. A knowledge gap returns the LO to learning; the four kept reasons do not.
REASON_KNOWLEDGE_GAP = "knowledge_gap"
REASON_SLIP = "slip"
REASON_ITEM_CONTRACT = "item_contract"
REASON_UNASSESSED = "unassessed"
REASON_NO_GAP_ATTRIBUTED = "no_gap_attributed"
KEPT_REASONS = frozenset({REASON_SLIP, REASON_ITEM_CONTRACT, REASON_UNASSESSED, REASON_NO_GAP_ATTRIBUTED})
#: Today's rule (any miss returns the LO to learning), said so on the receipt:
#: no diagnosis can arrive (``fallback`` names why), or the learner asked for
#: help (hints, priming, "don't know", assistance): not a grading question.
REASON_NO_DIAGNOSIS = "no_diagnosis"
REASON_LEARNER_SIDE = "learner_side"
REASON_DIAGNOSIS_PENDING = "diagnosis_pending"
#: Why no diagnosis can arrive for a graded miss (``MissVerdict.fallback``).
FALLBACK_SPLIT_DISABLED = "split_disabled"
FALLBACK_NOT_BLIND_GRADED = "not_blind_graded"
FALLBACK_DIAGNOSIS_FAILED = "diagnosis_failed"
FALLBACK_BUDGET_SKIPPED = "diagnosis_budget_skipped"
FALLBACK_NOT_NEEDED = "diagnosis_not_needed"
FALLBACK_REJECTED = "diagnosis_rejected"
FALLBACK_NOT_DIAGNOSED = "not_diagnosed"
#: Blind-grade validity scopes that put the miss on the item, not the learner.
ITEM_CONTRACT_SCOPES = frozenset({"item_contract", "grader_interpretation"})


@dataclass(frozen=True)
class MissVerdict:
    """How one miss on an assumed or maintained LO was decided: the receipt.

    ``events`` holds what the decision read from the diagnosis in force:
    ``(attribution index, validity_scope, causal_class)`` per blind-grade error
    attribution (``causal_class`` is ``None`` where the diagnosis wrote no event).
    """

    attempt_id: str
    outcome: str  # learning | kept | pending
    reason: str
    fallback: str | None = None
    diagnosis_id: str | None = None
    blind_grade_record_id: str | None = None
    job_state: str | None = None
    events: tuple[tuple[int, str, str | None], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def diagnosis_reason(
    attribution_scopes: Mapping[int, str],
    event_classes: Mapping[int, str],
) -> str:
    """The diagnosis's reading of a graded miss (Slice 1 M2 vocabulary).

    A knowledge gap is ``causal_class = learner_state`` on a
    ``valid_measurement`` attribution: the only reading that returns the LO to
    learning. Otherwise an item-contract or grader-interpretation attribution
    names the item, a ``transient_execution`` class on a valid measurement a
    slip, and anything else (the diagnoser abstained, or wrote no event) is
    ``no_gap_attributed``.
    """

    indexes = sorted(set(attribution_scopes) | set(event_classes))
    pairs = [(attribution_scopes.get(i, "unknown"), event_classes.get(i, "unknown")) for i in indexes]
    if any(scope == "valid_measurement" and cls == "learner_state" for scope, cls in pairs):
        return REASON_KNOWLEDGE_GAP
    if any(scope in ITEM_CONTRACT_SCOPES for scope, _cls in pairs):
        return REASON_ITEM_CONTRACT
    if any(scope == "valid_measurement" and cls == "transient_execution" for scope, cls in pairs):
        return REASON_SLIP
    return REASON_NO_GAP_ATTRIBUTED


def decide_miss(answer: AnswerFacts, graded: Mapping[str, MissVerdict]) -> MissVerdict:
    """A miss (or an unassessed answer) on an assumed or maintained LO.

    ``graded`` holds the loaded verdict of every graded miss (``placement.state``
    reads the diagnosis in force, the job queue and the kill switch).
    """

    if answer.unassessed:
        return MissVerdict(answer.attempt_id, MISS_KEPT, REASON_UNASSESSED)
    if not answer.learner_side_clean:
        return MissVerdict(answer.attempt_id, MISS_TO_LEARNING, REASON_LEARNER_SIDE)
    verdict = graded.get(answer.attempt_id)
    if verdict is None:
        return MissVerdict(
            answer.attempt_id, MISS_TO_LEARNING, REASON_NO_DIAGNOSIS, fallback=FALLBACK_NOT_DIAGNOSED,
        )
    return verdict


def prerequisite_layers(
    learning_objects: Iterable[str],
    prerequisites: Mapping[str, Iterable[str]],
) -> dict[str, int]:
    """Longest-path depth over the prerequisite edges among ``learning_objects``.

    Layer 0 has no prerequisite in the set. An LO is placed one layer below its
    deepest prerequisite in the set. Cycles are broken at the back edge, so the
    result is total and deterministic (LOs are visited in sorted order).
    """

    members = sorted(set(learning_objects))
    member_set = set(members)
    layers: dict[str, int] = {}
    visiting: set[str] = set()

    def visit(node: str) -> int:
        if node in layers:
            return layers[node]
        visiting.add(node)
        depth = 0
        for parent in sorted(set(prerequisites.get(node, ())) & member_set):
            if parent == node or parent in visiting:
                continue
            depth = max(depth, visit(parent) + 1)
        visiting.discard(node)
        layers[node] = depth
        return depth

    for member in members:
        visit(member)
    return layers


def new_material_key(
    *,
    layer: int,
    taught_first: bool,
    predicted_success: float,
    practice_item_id: str,
) -> tuple[int, int, float, str]:
    """Prerequisites first, then LOs you asked about, then easiest first."""

    return (layer, 0 if taught_first else 1, -predicted_success, practice_item_id)
