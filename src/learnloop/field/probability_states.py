"""The ``state`` each ``llm_probability`` variant sends (field spec §7.2).

Both judges get the same state for a prediction; only the question wrapper
differs. Every variant is past-only by construction:

* **The cutoff** is the moment the attempt began, taken from timing recorded
  before grading: the submission's intent (written at the first draft save
  or at submission, always before the grader ran) minus the logged
  presentation-to-submission latency, minus a safety margin for the
  latency's whole-second rounding. ``practice_attempts.created_at`` is
  stamped after grading, so it never sets a cutoff. When an attempt has no
  such record (older attempts, other surfaces), its start cannot be
  established and **no history is shown at all**: not a window, not a card,
  not the incumbent's fitted numbers (review F1). Every record shown must be
  strictly before the cutoff, so nothing revealed after the attempt began
  (a hint, a tutor answer, a later diagnosis or grade) can appear.
* **The current attempt** contributes only its item: never its answer,
  outcome, hints, timing or the item's reference solution.
* **Historical content follows the harness's revision policy.** An ``exact``
  row renders its verified snapshot and the rubric frozen in its assessment
  contract; a ``reconstructed_current`` row (the explicit, labelled
  ``--legacy-fallback current_content``) renders today's content and says
  so; anything else renders no item text or rubric, and V3 omits it and
  counts it (review F3).

The variants:

* **V1, item only:** the item stem, its LO and facet names, and its
  difficulty prior (solver-panel difficulty when Phase 5a provides it,
  otherwise empirical or authored), exactly as the harness's frozen features
  carry it.
* **V2, right/wrong window:** V1 plus the last 25 graded interactions the
  harness itself observed before the cutoff, as (item, knowledge-component
  names, result), JevKT's format without its population statistics. A
  fractional rubric outcome renders as ``partial``.
* **V3, rich state:** V1 plus a ``LearnerStateCardV1``-style rendering
  restricted to the LO, its same-concept LOs and its one-hop prerequisites:
  the incumbent predictor's numbers and region statuses (fitted only on
  observations before the cutoff, review F2), recent attempts (answer
  excerpts, blind-grade fields, hint totals and tutor-question timing),
  typed prior hypotheses with their evidence for and against and the
  repairs tried, and tutor questions, under the router card's token budget
  (router spec §4, D8): older successes drop first, then older text
  excerpts, then older attempts; typed fields never drop. What LearnLoop
  does not record (ordinary hint timing) is named, not implied (review F5).
"""
from __future__ import annotations

from bisect import bisect_left
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
import math
import sqlite3
from typing import Any

from learnloop.clock import parse_utc
from learnloop.diagnosis.split.history import (
    AttemptRef, HistoryAttempt, HypothesisRecord, VaultHistoryStore, learning_object_neighborhood,
)
from learnloop.field.outcomes import borrowed_repository
from learnloop.field.types import AttemptRow
from learnloop.learner.assessment_contracts import rubric_from_contract
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric

STATE_VERSION = "llm-probability-state-v2"
VARIANTS = ("v1", "v2", "v3")
V2_WINDOW = 25
#: router.card_token_budget's default (router spec §4, D8): V3 uses the same.
CARD_TOKEN_BUDGET = 16_000
STEM_LIMIT = 1_500
HISTORY_STEM_LIMIT = 200
ANSWER_LIMIT = 600
QUOTE_LIMIT = 200
QUESTION_LIMIT = 300
STATEMENT_LIMIT = 300
#: V3's attempt list before budgeting; the budget usually binds first.
V3_MAX_ATTEMPTS = 60
#: Evidence references kept per hypothesis and direction (most recent first
#: to go is the oldest); the totals are always shown.
MAX_EVIDENCE_REFS = 4
#: Subtracted from (intent - latency): the client rounds latency to whole
#: seconds and the intent's clock is the sidecar's. An earlier cutoff only
#: hides more.
START_MARGIN_SECONDS = 2
#: Stated in V2 and V3 when the attempt's start cannot be established.
HISTORY_WITHHELD = (
    "This attempt's start time was not recorded before grading, so no earlier work, "
    "diagnoses or questions are shown: they could include material from after it began."
)
#: What LearnLoop does not record, so the judge never reads absence as zero.
NOT_RECORDED = (
    "the timing of ordinary hints (each attempt keeps only its total)",
)
_MISCONCEPTION_LIFECYCLE = {
    "active": "durable_active",
    "resolving": "durable_resolving",
    "resolved": "durable_resolved",
}
UNKNOWN_AS_OF = "unknown_as_of_this_attempt"


def estimate_tokens(value: Any) -> int:
    """UTF-8 bytes / 4, rounded up: the Slice 1 context estimator."""

    text = value if isinstance(value, str) else canonical_json(value)
    return math.ceil(len(text.encode("utf-8")) / 4)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def state_hash(state: Any) -> str:
    return hashlib.sha256(canonical_json(state).encode("utf-8")).hexdigest()


def excerpt(text: str | None, limit: int) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def _instant(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return parse_utc(str(value))
    except (TypeError, ValueError):
        return None


def _result(outcome: float) -> str:
    if outcome >= 1.0 - 1e-9:
        return "correct"
    if outcome <= 1e-9:
        return "incorrect"
    return "partial"


@dataclass(frozen=True)
class PredictionPoint:
    """One harness prediction: the row, and what the harness observed before it.

    ``history`` holds exactly the rows the harness had handed every arm's
    ``observe`` before asking for this prediction (it keys the cache).
    ``incumbent`` holds the active predictor's numbers fitted only on the
    observations made before this attempt's cutoff.
    """

    position_key: str
    row: AttemptRow
    history: tuple[AttemptRow, ...]
    incumbent: Mapping[str, Any]


class StateRenderer:
    """Reads one read-only vault snapshot; renders deterministic states.

    ``rows`` are the harness's own attempt rows (``inputs["attempts"]``):
    their revision status decides which historical content V3 may show. The
    caller owns the connection and its transaction. Nothing is written.
    """

    def __init__(
        self, vault: LoadedVault, connection: sqlite3.Connection, *, rows: Iterable[AttemptRow] = (),
    ) -> None:
        self.vault = vault
        self.connection = connection
        self._rows: dict[str, AttemptRow] = {row.attempt_id: row for row in rows}
        self._attempts: dict[str, dict[str, Any]] = {}
        cursor = connection.execute(
            "SELECT a.id, a.practice_item_id, a.learning_object_id, a.created_at, a.latency_seconds, "
            "a.hints_used, i.created_at AS intent_at FROM practice_attempts a "
            "LEFT JOIN submission_intents i ON i.submission_id = a.submission_id "
            "AND i.practice_item_id = a.practice_item_id ORDER BY a.created_at, a.id"
        )
        names = [column[0] for column in cursor.description]
        for values in cursor:
            record = dict(zip(names, values))
            instant = _instant(record["created_at"])
            if instant is None:
                continue
            record["instant"] = instant
            self._attempts[str(record["id"])] = record
        self._snapshots: dict[str, PracticeItem | None] = {}
        self._contracts: dict[str, Rubric | None] = {}
        self._grading: tuple[dict[str, dict[str, float]], dict[str, set[Any]]] | None = None
        self._history: VaultHistoryStore | None = None
        self._questions: list[dict[str, Any]] | None = None
        self._mutable: tuple[
            dict[tuple[str, str], tuple[datetime | None, datetime | None]], dict[str, list[tuple[datetime, str]]],
        ] | None = None

    # -- cutoff ------------------------------------------------------------

    def cutoff(self, attempt_id: str) -> datetime | None:
        """The latest instant the attempt provably had not begun, or ``None``.

        Only timing written before grading counts: the submission intent
        (first draft save or the submit itself, both before the grader ran)
        minus the logged presentation-to-submission latency and a rounding
        margin. Completion times include grading and never set a cutoff.
        """

        record = self._attempts.get(attempt_id)
        if record is None:
            return None
        latency = record.get("latency_seconds")
        intent = _instant(record.get("intent_at"))
        if intent is None or isinstance(latency, bool) or not isinstance(latency, (int, float)):
            return None
        if not math.isfinite(latency) or latency < 0 or intent > record["instant"]:
            return None
        start = intent - timedelta(seconds=float(latency) + START_MARGIN_SECONDS)
        # Floored to whole seconds: an earlier cutoff only hides more.
        return start.replace(microsecond=0)

    # -- item content --------------------------------------------------------

    def _item(self, row: AttemptRow) -> PracticeItem | None:
        """The graded revision for an ``exact`` row; today's content only when labelled.

        Only ``reconstructed_current`` rows (the explicit, labelled fallback)
        reach today's content. An ``exact`` row whose snapshot cannot be
        verified, or an ``excluded`` row, renders no item at all.
        """

        if row.revision_status == "reconstructed_current":
            return self.vault.practice_items.get(row.features.item_id)
        digest = row.item_snapshot_hash
        if row.revision_status != "exact" or not digest:
            return None
        if digest not in self._snapshots:
            stored = self.connection.execute(
                "SELECT item_json FROM practice_item_snapshots WHERE content_hash=? AND practice_item_id=?",
                (digest, row.features.item_id),
            ).fetchone()
            item = None
            if stored is not None:
                raw = stored[0]
                if hashlib.sha256(raw.encode()).hexdigest() == digest:
                    item = PracticeItem.model_validate_json(raw)
            self._snapshots[digest] = item
        return self._snapshots[digest]

    def _grading_rows(self) -> tuple[dict[str, dict[str, float]], dict[str, set[Any]]]:
        """Per attempt: the latest surviving points per criterion and the contracts they cite."""

        if self._grading is None:
            points: dict[str, dict[str, float]] = {}
            contracts: dict[str, set[Any]] = {}
            for attempt_id, criterion_id, awarded, contract_id in self.connection.execute(
                "SELECT attempt_id, criterion_id, points_awarded, assessment_contract_version_id "
                "FROM grading_evidence WHERE superseded_at IS NULL "
                "ORDER BY attempt_id, COALESCE(grading_revision, -1), created_at, id"
            ):
                points.setdefault(str(attempt_id), {})[str(criterion_id)] = float(awarded or 0.0)
                contracts.setdefault(str(attempt_id), set()).add(contract_id)
            self._grading = (points, contracts)
        return self._grading

    def _rubric(self, row: AttemptRow) -> Rubric | None:
        """The rubric the revision policy allows: frozen for ``exact``, today's when labelled."""

        if row.revision_status == "reconstructed_current":
            item = self.vault.practice_items.get(row.features.item_id)
            return self.vault.rubric_for_item(item) if item is not None else None
        if row.revision_status != "exact":
            return None
        contract_ids = self._grading_rows()[1].get(row.attempt_id, set())
        if len(contract_ids) != 1 or None in contract_ids:
            return None
        contract_id = str(next(iter(contract_ids)))
        if contract_id not in self._contracts:
            stored = self.connection.execute(
                "SELECT contract_json FROM assessment_contract_versions WHERE id=? AND practice_item_id=?",
                (contract_id, row.features.item_id),
            ).fetchone()
            rubric = None
            if stored is not None:
                try:
                    rubric = rubric_from_contract(json.loads(stored[0]))
                except (TypeError, ValueError, KeyError):
                    rubric = None
            self._contracts[contract_id] = rubric
        return self._contracts[contract_id]

    def _lo_title(self, lo_id: str) -> str:
        lo = self.vault.learning_objects.get(lo_id)
        return lo.title if lo is not None else "an unnamed learning objective"

    def _facet_titles(self, item: PracticeItem | None) -> list[str]:
        titles = []
        for facet in (item.evidence_facets if item is not None else []):
            canonical = self.vault.canonical_facet_id(str(facet))
            entry = self.vault.evidence_facets.get(canonical)
            titles.append((entry.title if entry is not None and entry.title else canonical).strip())
        return list(dict.fromkeys(title for title in titles if title))

    def item_view(self, row: AttemptRow) -> dict[str, Any]:
        """V1's content: no reference solution, rubric, hints or answer."""

        item = self._item(row)
        f = row.features
        # LLM-estimated difficulty is never a point value (field §4.3): the
        # harness's b already falls back to the LO prior, and the estimate
        # itself is withheld rather than shown to another model.
        llm_estimated = f.difficulty_source.startswith("llm") or (
            item is not None and item.difficulty_source == "llm_estimate"
        )
        prior: dict[str, Any] = {
            "irt_difficulty_b": round(f.b, 4),
            "irt_discrimination_a": round(f.a, 4),
            "source": f.difficulty_source,
            "note": "Logit ability scale: higher b is harder; b near 0 is about 50% for an average learner.",
        }
        if llm_estimated:
            prior["note"] += " No measured or authored difficulty: b is the default prior."
        elif item is not None and item.difficulty is not None:
            prior[f"{item.difficulty_source or 'authored'}_difficulty_0_to_1"] = item.difficulty
        view: dict[str, Any] = {
            "stem": excerpt(item.prompt, STEM_LIMIT) if item is not None else "(item text unavailable)",
            "learning_objective": self._lo_title(f.lo_id),
            "facets": self._facet_titles(item),
            "difficulty_prior": prior,
        }
        if f.capability:
            view["capability"] = f.capability
        return view

    # -- variants ------------------------------------------------------------

    def render(self, variant: str, point: PredictionPoint) -> dict[str, Any]:
        if variant == "v1":
            return {"item": self.item_view(point.row)}
        if variant == "v2":
            state: dict[str, Any] = {"item": self.item_view(point.row), "recent_interactions": self._window(point)}
            if self.cutoff(point.row.attempt_id) is None:
                state["history_withheld"] = HISTORY_WITHHELD
            return state
        if variant == "v3":
            return {"item": self.item_view(point.row), "learner_state": self._card(point)}
        raise ValueError(f"Unknown llm_probability variant {variant!r}")

    def _before(self, value: str | None, cutoff: datetime | None) -> bool:
        instant = _instant(value)
        return cutoff is not None and instant is not None and instant < cutoff

    def _window(self, point: PredictionPoint) -> list[dict[str, Any]]:
        cutoff = self.cutoff(point.row.attempt_id)
        prior = [row for row in point.history if self._before(row.observed_at, cutoff)]
        window = []
        for row in prior[-V2_WINDOW:]:
            item = self._item(row)
            window.append({
                "item": excerpt(item.prompt, HISTORY_STEM_LIMIT) if item is not None else "(item text unavailable)",
                "knowledge_components": [self._lo_title(row.lo_id), *self._facet_titles(item)],
                "result": _result(row.outcome),
            })
        return window

    # -- V3 card ------------------------------------------------------------

    def _store(self) -> VaultHistoryStore:
        if self._history is None:
            self._history = VaultHistoryStore(self.vault, borrowed_repository(self.connection))
        return self._history

    def _scope(self, lo_id: str) -> dict[str, str]:
        """The LO, its same-concept LOs and its one-hop prerequisites."""

        hood = learning_object_neighborhood(self.vault, lo_id)
        scope = {lo_id: "target"}
        for other in hood.same_concept_ids:
            scope.setdefault(other, "same_concept")
        for other in hood.prerequisite_ids:
            scope.setdefault(other, "prerequisite")
        return scope

    def _question_rows(self) -> list[dict[str, Any]]:
        if self._questions is None:
            cursor = self.connection.execute(
                "SELECT id, context, practice_item_id, attempt_id, question_md, question_type, "
                "seconds_into_attempt, hints_used_before, created_at FROM question_events "
                "ORDER BY created_at, id"
            )
            names = [column[0] for column in cursor.description]
            self._questions = [dict(zip(names, row)) for row in cursor]
        return self._questions

    def _mutable_rows(self) -> tuple[
        dict[tuple[str, str], tuple[datetime | None, datetime | None]], dict[str, list[tuple[datetime, str]]],
    ]:
        """Mutable hypothesis rows' write times and misconception transitions."""

        if self._mutable is None:
            mutable: dict[tuple[str, str], tuple[datetime | None, datetime | None]] = {}
            for kind, table in (("misconception", "misconceptions"), ("unresolved_factor", "unresolved_cause_factors")):
                for identifier, created, updated in self.connection.execute(
                    f"SELECT id, created_at, updated_at FROM {table}"  # noqa: S608 - fixed table names
                ):
                    mutable[(kind, str(identifier))] = (_instant(created), _instant(updated))
            transitions: dict[str, list[tuple[datetime, str]]] = {}
            for identifier, status, at in self.connection.execute(
                "SELECT misconception_id, to_status, at FROM misconception_transition_events ORDER BY at, id"
            ):
                instant = _instant(at)
                if instant is not None:
                    transitions.setdefault(str(identifier), []).append((instant, str(status)))
            self._mutable = (mutable, transitions)
        return self._mutable

    def _status_as_of(self, record: HypothesisRecord, cutoff: datetime) -> str:
        """A hypothesis's lifecycle as it stood at the cutoff.

        Causal hypotheses are versioned, so the store's as-of view is exact.
        A misconception's status comes from its transition events before the
        cutoff; a mutable row last written at or after the cutoff with no such
        record is labelled unknown rather than shown with today's status.
        """

        if record.kind == "causal_hypothesis":
            return record.lifecycle
        mutable, transitions = self._mutable_rows()
        if record.kind == "misconception":
            earlier = [status for at, status in transitions.get(record.id, []) if at < cutoff]
            if earlier:
                return _MISCONCEPTION_LIFECYCLE.get(earlier[-1], earlier[-1])
        _created, updated = mutable.get((record.kind, record.id), (None, None))
        if updated is not None and updated < cutoff:
            return record.lifecycle
        return UNKNOWN_AS_OF

    def _card(self, point: PredictionPoint) -> dict[str, Any]:
        row = point.row
        cutoff = self.cutoff(row.attempt_id)
        scope = self._scope(row.lo_id)
        titles = {lo: self._lo_title(lo) for lo in scope}
        incumbent = dict(point.incumbent)
        regions = incumbent.pop("regions", {})
        statuses = []
        unknowns = []
        for lo, relation in scope.items():
            region = regions.get(lo)
            if region is None or region.get("untested", True):
                statuses.append({"learning_objective": titles[lo], "relation": relation, "status": "untested"})
                unknowns.append(f"never tested before this attempt: {titles[lo]}")
            else:
                statuses.append({
                    "learning_objective": titles[lo], "relation": relation, "status": "tested",
                    "ability_mean_logit": round(region["mean"], 3),
                    "ability_sd_logit": round(math.sqrt(max(0.0, region["variance"])), 3),
                    "information_in_prior_units": round(region["n_eff"], 3),
                })
        card: dict[str, Any] = {
            "scope": [{"learning_objective": titles[lo], "relation": relation} for lo, relation in scope.items()],
            "incumbent_predictor": incumbent,
            "status_by_learning_objective": statuses,
            "explicit_unknowns": unknowns,
            "recent_work": [],
            "open_hypotheses": [],
            "tutor_questions": [],
            "not_recorded": list(NOT_RECORDED),
            "omitted": {
                "older_successes": 0, "text_excerpts": 0, "older_attempts": 0, "tutor_questions": 0,
                "unverified_revision": 0,
            },
        }
        if cutoff is None:
            card["history_withheld"] = HISTORY_WITHHELD
            return _fit(card)
        store = self._store()
        candidates = [
            attempt for attempt in store.attempts_before(AttemptRef(row.attempt_id, row.observed_at), list(scope))
            if self._before(attempt.completed_at, cutoff) and attempt.attempt_id != row.attempt_id
        ]
        verified: list[tuple[HistoryAttempt, AttemptRow]] = []
        for attempt in candidates:
            history_row = self._rows.get(attempt.attempt_id)
            if history_row is None or history_row.revision_status not in {"exact", "reconstructed_current"}:
                card["omitted"]["unverified_revision"] += 1
                continue
            verified.append((attempt, history_row))
        dropped = max(0, len(verified) - V3_MAX_ATTEMPTS)
        card["omitted"]["older_attempts"] += dropped
        verified = verified[dropped:]
        refs = {attempt.attempt_id: f"w{index}" for index, (attempt, _row) in enumerate(verified, start=1)}
        questions = [
            question for question in self._question_rows()
            if question.get("attempt_id") != row.attempt_id  # asked during the predicted attempt
            and self._before(question.get("created_at"), cutoff)
        ]
        during: dict[str, list[dict[str, Any]]] = {}
        for question in questions:
            if question.get("attempt_id") in refs:
                during.setdefault(str(question["attempt_id"]), []).append({
                    "seconds_into_attempt": question.get("seconds_into_attempt"),
                    "hints_used_before": question.get("hints_used_before"),
                    "type": question.get("question_type") or "unclassified",
                })
        facets_by_attempt: dict[str, frozenset[str]] = {}
        for attempt, history_row in verified:
            item = self._item(history_row)
            rubric = self._rubric(history_row)
            points = self._grading_rows()[0].get(attempt.attempt_id, {})
            meta = self._attempts.get(attempt.attempt_id, {})
            hints = int(meta.get("hints_used") or 0)
            facets_by_attempt[attempt.attempt_id] = frozenset(
                self.vault.canonical_facet_id(str(facet)) for facet in (item.evidence_facets if item else [])
            ) | frozenset(attempt.target_facets)
            entry: dict[str, Any] = {
                "ref": refs[attempt.attempt_id],
                "days_before": _days(attempt.completed_at, cutoff),
                "learning_objective": titles.get(attempt.learning_object_id, "unmapped"),
                "relation": scope.get(attempt.learning_object_id, "other"),
                "attempt_type": attempt.attempt_type,
                "revision": history_row.revision_status,
                "item": (excerpt(item.prompt, HISTORY_STEM_LIMIT) or None) if item is not None else None,
                "answer": excerpt(attempt.learner_answer_md, ANSWER_LIMIT) or None,
                "blind_grade": {
                    "score": attempt.score,
                    "max_points": float(rubric.max_points) if rubric is not None else None,
                    "score_fraction": round(history_row.outcome, 3),
                    "failed_criteria": (
                        sorted(c.id for c in rubric.criteria if c.id in points and points[c.id] + 1e-9 < float(c.points))
                        if rubric is not None else None
                    ),
                    "error_types": list(attempt.error_types),
                    "first_divergence": [excerpt(q, QUOTE_LIMIT) for q in attempt.first_divergence_quotes],
                },
                "assisted": attempt.assisted,
                "primed": attempt.primed,
                "hints_used": hints,
                "_success": history_row.outcome >= 1.0 - 1e-9,
            }
            if history_row.revision_status == "reconstructed_current":
                entry["revision_note"] = "today's item text and rubric (no verified historical revision)"
            if attempt.attempt_id in during:
                entry["tutor_questions_during"] = during[attempt.attempt_id]
            card["recent_work"].append(entry)
        card["open_hypotheses"] = self._hypotheses(
            store, scope, titles, cutoff, verified, refs, facets_by_attempt,
        )
        attempt_ids = {attempt.attempt_id for attempt, _row in verified}
        items_in_scope = {
            item_id for item_id, item in self.vault.practice_items.items() if item.learning_object_id in scope
        }
        for question in questions:
            if question.get("practice_item_id") not in items_in_scope and question.get("attempt_id") not in attempt_ids:
                continue
            entry = {
                "days_before": _days(question.get("created_at"), cutoff),
                "type": question.get("question_type") or "unclassified",
                "context": question.get("context") or "",
                "question": excerpt(question.get("question_md"), QUESTION_LIMIT),
                "seconds_into_attempt": question.get("seconds_into_attempt"),
                "hints_used_before": question.get("hints_used_before"),
            }
            if question.get("attempt_id") in refs:
                entry["attempt_ref"] = refs[str(question["attempt_id"])]
            card["tutor_questions"].append(entry)
        return _fit(card)

    def _hypotheses(
        self, store: VaultHistoryStore, scope: Mapping[str, str], titles: Mapping[str, str], cutoff: datetime,
        verified: Sequence[tuple[HistoryAttempt, AttemptRow]], refs: Mapping[str, str],
        facets_by_attempt: Mapping[str, frozenset[str]],
    ) -> list[dict[str, Any]]:
        """Typed prior hypotheses as of the cutoff, each with its evidence.

        A record shows only when it was written, and its source attempt
        completed, strictly before the cutoff (the store's as-of rule).
        Evidence is read from the same verified attempts the card shows:
        **for** is the attempt it was diagnosed from plus later non-passes on
        the hypothesis's LO or target facets; **against** is later passes
        there. Repairs tried carry their cold verifications as of the cutoff.
        """

        reference = AttemptRef("", _iso(cutoff))
        repairs: dict[str, list[dict[str, Any]]] = {}
        for repair in store.repairs_before(reference, None):
            for hypothesis_id in repair.hypothesis_ids:
                repairs.setdefault(hypothesis_id, []).append({
                    "operator": repair.operator or "unnamed",
                    "cold_successes": repair.cold_successes,
                    "cold_failures": repair.cold_failures,
                })
        rendered = []
        for record in store.hypotheses_before(reference, list(scope)):
            source = store.attempt(record.source_attempt_id) if record.source_attempt_id else None
            targets = frozenset(record.target_facets)
            evidence_for: list[dict[str, Any]] = []
            evidence_against: list[dict[str, Any]] = []
            for attempt, history_row in verified:
                if source is None or attempt.attempt_id == source.attempt_id or attempt.key() <= source.key():
                    continue
                if attempt.learning_object_id != record.learning_object_id and not (
                    targets & facets_by_attempt.get(attempt.attempt_id, frozenset())
                ):
                    continue
                reference_entry: dict[str, Any] = {
                    "ref": refs[attempt.attempt_id], "days_before": _days(attempt.completed_at, cutoff),
                }
                if history_row.outcome >= 1.0 - 1e-9:
                    evidence_against.append({**reference_entry, "kind": "passed_later"})
                else:
                    evidence_for.append({
                        **reference_entry, "kind": "non_pass_later",
                        "first_divergence": [excerpt(q, QUOTE_LIMIT) for q in attempt.first_divergence_quotes][:2],
                    })
            source_view: dict[str, Any] | None = None
            if source is not None:
                source_view = {
                    "ref": refs.get(source.attempt_id),
                    "days_before": _days(source.completed_at, cutoff),
                    "learning_objective": titles.get(source.learning_object_id, "unmapped"),
                    "first_divergence": [excerpt(q, QUOTE_LIMIT) for q in source.first_divergence_quotes][:2],
                }
                if source_view["ref"] is None:
                    source_view["note"] = "not in recent work (out of scope or no verified revision)"
                evidence_for.insert(0, {
                    "ref": source_view["ref"], "days_before": source_view["days_before"], "kind": "diagnosed_from",
                })
            entry: dict[str, Any] = {
                "kind": record.kind,
                "learning_objective": titles.get(record.learning_object_id or "", "unmapped"),
                "statement": excerpt(record.statement, STATEMENT_LIMIT),
                "cause_scope": record.scope,
                "status": self._status_as_of(record, cutoff),
                "written_days_before": _days(record.last_updated, cutoff),
                "source_attempt": source_view,
                "evidence_for_total": len(evidence_for),
                "evidence_against_total": len(evidence_against),
                "evidence_for": _bounded(evidence_for, keep_first=source is not None),
                "evidence_against": _bounded(evidence_against),
                "repairs_tried": repairs.get(record.id, []),
            }
            rendered.append(entry)
        return rendered


def _iso(instant: datetime) -> str:
    """The vault's own timestamp form (whole seconds, ``Z``)."""

    return instant.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _days(value: str | None, cutoff: datetime | None) -> float | None:
    instant = _instant(value)
    if instant is None or cutoff is None:
        return None
    return round((cutoff - instant).total_seconds() / 86400, 2)


def _bounded(entries: list[dict[str, Any]], *, keep_first: bool = False) -> list[dict[str, Any]]:
    """The most recent references; the diagnosing attempt always stays."""

    if len(entries) <= MAX_EVIDENCE_REFS:
        return entries
    if keep_first:
        return [entries[0], *entries[-(MAX_EVIDENCE_REFS - 1):]]
    return entries[-MAX_EVIDENCE_REFS:]


def _strip_private(card: Mapping[str, Any]) -> dict[str, Any]:
    clean = dict(card)
    clean["recent_work"] = [{k: v for k, v in entry.items() if not k.startswith("_")} for entry in card["recent_work"]]
    return clean


def _fit(card: dict[str, Any], budget: int = CARD_TOKEN_BUDGET) -> dict[str, Any]:
    """Truncate to the card budget in the router spec's order; typed fields stay."""

    def size() -> int:
        return estimate_tokens(_strip_private(card))

    omitted = card["omitted"]
    work: list[dict[str, Any]] = card["recent_work"]
    # 1. Older successes first (the list is chronological, oldest first).
    while size() > budget:
        index = next((i for i, entry in enumerate(work) if entry["_success"]), None)
        if index is None:
            break
        work.pop(index)
        omitted["older_successes"] += 1
    # 2. Then older text excerpts: answers, then item stems, oldest first.
    for field in ("answer", "item"):
        for entry in work:
            if size() <= budget:
                break
            if entry.get(field):
                entry[field] = None
                omitted["text_excerpts"] += 1
    for question in card["tutor_questions"]:
        if size() <= budget:
            break
        if question.get("question"):
            question["question"] = None
            omitted["text_excerpts"] += 1
    # 3. Then whole older attempts and questions; typed fields never drop.
    while size() > budget and work:
        work.pop(0)
        omitted["older_attempts"] += 1
    while size() > budget and card["tutor_questions"]:
        card["tutor_questions"].pop(0)
        omitted["tutor_questions"] += 1
    return _strip_private(card)


def history_pairs(history: Sequence[AttemptRow]) -> list[tuple[str, float]]:
    return [(row.attempt_id, row.outcome) for row in history]


def start_index(times: Sequence[datetime], cutoff: datetime | None) -> int:
    """How many time-ordered observations precede ``cutoff`` strictly (0 if unknown)."""

    return 0 if cutoff is None else bisect_left(times, cutoff)


__all__ = [
    "CARD_TOKEN_BUDGET",
    "HISTORY_WITHHELD",
    "PredictionPoint",
    "START_MARGIN_SECONDS",
    "STATE_VERSION",
    "StateRenderer",
    "V2_WINDOW",
    "VARIANTS",
    "canonical_json",
    "estimate_tokens",
    "excerpt",
    "start_index",
    "state_hash",
]
