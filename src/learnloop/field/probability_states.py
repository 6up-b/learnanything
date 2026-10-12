"""The ``state`` each ``llm_probability`` variant sends (field spec §7.2).

Both judges get the same state for a prediction; only the question wrapper
differs. Every variant is past-only by construction:

* **The cutoff** is the moment the attempt began: ``created_at -
  latency_seconds`` when the latency was logged. Without one it is one second
  after the previous attempt in the vault (any type) was submitted, the
  latest moment the attempt can be proved not to have started yet. With no
  previous attempt and no latency, nothing is known to precede it, so no
  history is shown at all. Every record shown must be strictly before the
  cutoff, so nothing revealed after the attempt began (a hint, a tutor
  answer, a later diagnosis or grade) can appear.
* **The current attempt** contributes only its item: never its answer,
  outcome, hints, timing or the item's reference solution.

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
  the incumbent predictor's numbers and region statuses, recent attempts
  (answer excerpts and blind-grade fields), typed prior hypotheses, hints and
  tutor questions, under the router card's token budget (router spec §4,
  D8): older successes drop first, then older text excerpts, then older
  attempts; typed fields never drop.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
import math
import sqlite3
from typing import Any

from learnloop.clock import parse_utc
from learnloop.diagnosis.split.history import (
    AttemptRef, HistoryAttempt, VaultHistoryStore, learning_object_neighborhood,
)
from learnloop.field.outcomes import borrowed_repository
from learnloop.field.types import AttemptRow
from learnloop.vault.models import LoadedVault, PracticeItem

STATE_VERSION = "llm-probability-state-v1"
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
    ``observe`` before asking for this prediction. ``incumbent`` holds the
    active predictor's numbers computed from that same past.
    """

    position_key: str
    row: AttemptRow
    history: tuple[AttemptRow, ...]
    incumbent: Mapping[str, Any]


class StateRenderer:
    """Reads one read-only vault snapshot; renders deterministic states.

    The caller owns the connection and its transaction. Nothing is written.
    """

    def __init__(self, vault: LoadedVault, connection: sqlite3.Connection) -> None:
        self.vault = vault
        self.connection = connection
        self._attempts: dict[str, dict[str, Any]] = {}
        self._order: list[tuple[datetime, str]] = []
        for row in connection.execute(
            "SELECT id, practice_item_id, learning_object_id, created_at, latency_seconds, "
            "hints_used FROM practice_attempts ORDER BY created_at, id"
        ):
            record = dict(row) if not isinstance(row, tuple) else dict(zip(
                ("id", "practice_item_id", "learning_object_id", "created_at", "latency_seconds", "hints_used"), row,
            ))
            instant = parse_utc(str(record["created_at"]))
            if instant is None:
                continue
            record["instant"] = instant
            self._attempts[str(record["id"])] = record
            self._order.append((instant, str(record["id"])))
        self._order.sort()
        self._snapshots: dict[str, PracticeItem | None] = {}
        self._history: VaultHistoryStore | None = None
        self._questions: list[dict[str, Any]] | None = None

    # -- cutoff ------------------------------------------------------------

    def cutoff(self, attempt_id: str) -> datetime | None:
        """The attempt's start, or the latest instant provably before it."""

        record = self._attempts.get(attempt_id)
        if record is None:
            return None
        latency = record.get("latency_seconds")
        if isinstance(latency, (int, float)) and not isinstance(latency, bool) and math.isfinite(latency) and latency >= 0:
            # Floored to whole seconds: an earlier cutoff only hides more.
            return (record["instant"] - timedelta(seconds=float(latency))).replace(microsecond=0)
        key = (record["instant"], attempt_id)
        previous = [instant for instant, other in self._order if (instant, other) < key and other != attempt_id]
        return (previous[-1] + timedelta(seconds=1)).replace(microsecond=0) if previous else None

    # -- item content --------------------------------------------------------

    def _item(self, row: AttemptRow) -> PracticeItem | None:
        """The graded revision for an ``exact`` row, else today's content.

        Only ``reconstructed_current`` rows (the explicit, labelled fallback)
        reach today's content; the harness never predicts ``excluded`` rows.
        """

        digest = row.item_snapshot_hash
        if row.revision_status == "exact" and digest:
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
            if self._snapshots[digest] is not None:
                return self._snapshots[digest]
        return self.vault.practice_items.get(row.features.item_id)

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
            return {"item": self.item_view(point.row), "recent_interactions": self._window(point)}
        if variant == "v3":
            return {"item": self.item_view(point.row), "learner_state": self._card(point)}
        raise ValueError(f"Unknown llm_probability variant {variant!r}")

    def _before(self, value: str | None, cutoff: datetime | None) -> bool:
        instant = parse_utc(value) if value else None
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
        attempts: list[HistoryAttempt] = []
        hypotheses: list[dict[str, Any]] = []
        questions: list[dict[str, Any]] = []
        if cutoff is not None:
            store = self._store()
            # Hypotheses must be written, and their source attempt submitted,
            # strictly before the cutoff (the store's as-of rule).
            reference = AttemptRef("", _iso(cutoff))
            attempts = [
                attempt for attempt in store.attempts_before(
                    AttemptRef(row.attempt_id, row.observed_at), list(scope),
                )
                if self._before(attempt.completed_at, cutoff) and attempt.attempt_id != row.attempt_id
            ][-V3_MAX_ATTEMPTS:]
            for record in store.hypotheses_before(reference, list(scope)):
                hypotheses.append({
                    "kind": record.kind,
                    "learning_objective": titles.get(record.learning_object_id or "", "unmapped"),
                    "statement": excerpt(record.statement, STATEMENT_LIMIT),
                    "status": record.lifecycle,
                    "validated_evidence_count": record.validated_evidence_count,
                })
            items_in_scope = {
                item_id for item_id, item in self.vault.practice_items.items() if item.learning_object_id in scope
            }
            attempt_ids = {attempt.attempt_id for attempt in attempts}
            for question in self._question_rows():
                if question.get("attempt_id") == row.attempt_id:
                    continue  # asked during the predicted attempt
                if not self._before(question.get("created_at"), cutoff):
                    continue
                if question.get("practice_item_id") not in items_in_scope and question.get("attempt_id") not in attempt_ids:
                    continue
                questions.append({
                    "days_before": _days(question.get("created_at"), cutoff),
                    "type": question.get("question_type") or "unclassified",
                    "context": question.get("context") or "",
                    "question": excerpt(question.get("question_md"), QUESTION_LIMIT),
                    "seconds_into_attempt": question.get("seconds_into_attempt"),
                    "hints_used_before": question.get("hints_used_before"),
                })
        work = []
        for attempt in attempts:
            meta = self._attempts.get(attempt.attempt_id, {})
            passed = attempt.score is not None and attempt.max_points and attempt.score + 1e-9 >= attempt.max_points
            work.append({
                "days_before": _days(attempt.completed_at, cutoff),
                "learning_objective": titles.get(attempt.learning_object_id, "unmapped"),
                "relation": scope.get(attempt.learning_object_id, "other"),
                "attempt_type": attempt.attempt_type,
                "item": excerpt(attempt.item_prompt, HISTORY_STEM_LIMIT) or None,
                "answer": excerpt(attempt.learner_answer_md, ANSWER_LIMIT) or None,
                "blind_grade": {
                    "score": attempt.score, "max_points": attempt.max_points,
                    "failed_criteria": list(attempt.failed_criteria),
                    "error_types": list(attempt.error_types),
                    "first_divergence": [excerpt(q, QUOTE_LIMIT) for q in attempt.first_divergence_quotes],
                },
                "assisted": attempt.assisted,
                "primed": attempt.primed,
                "hints_used": int(meta.get("hints_used") or 0),
                "_success": bool(passed),
            })
        card = {
            "scope": [{"learning_objective": titles[lo], "relation": relation} for lo, relation in scope.items()],
            "incumbent_predictor": incumbent,
            "status_by_learning_objective": statuses,
            "explicit_unknowns": unknowns,
            "recent_work": work,
            "open_hypotheses": hypotheses,
            "tutor_questions": questions,
            "omitted": {"older_successes": 0, "text_excerpts": 0, "older_attempts": 0, "tutor_questions": 0},
        }
        return _fit(card)


def _iso(instant: datetime) -> str:
    """The vault's own timestamp form (whole seconds, ``Z``)."""

    return instant.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _days(value: str | None, cutoff: datetime | None) -> float | None:
    instant = parse_utc(value) if value else None
    if instant is None or cutoff is None:
        return None
    return round((cutoff - instant).total_seconds() / 86400, 2)


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


__all__ = [
    "CARD_TOKEN_BUDGET",
    "PredictionPoint",
    "STATE_VERSION",
    "StateRenderer",
    "V2_WINDOW",
    "VARIANTS",
    "canonical_json",
    "estimate_tokens",
    "excerpt",
    "state_hash",
]
