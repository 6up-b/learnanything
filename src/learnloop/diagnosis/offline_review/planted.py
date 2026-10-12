"""Planted learners with known truth (Slice 1 §12 S1.0).

Three shapes, each a whole synthetic learner whose past is constructed and
whose truth is known by construction:

* ``changed_cause`` - C4's revert control: earlier failures share cause A and a
  prior hypothesis says A; the diagnosed answer fails for a different cause B.
  The diagnoser should name B and say the cause changed.
* ``paraphrased_recurrence`` - the diagnosed answer repeats cause A, which
  earlier answers on OTHER items showed in different words; a distractor
  failure has an unrelated cause. The A answers should be cited, the
  distractor not.
* ``same_answer_different_cause`` - an earlier answer reached the same final
  answer through cause A; the diagnosed one gets there through cause B. The
  two must be kept apart.

A planted learner's history is isolated (:class:`StaticHistoryStore`): it never
mixes with the real learner's attempts, and the real learner's contexts never
see it. Ids are minted like real ids, so neither the diagnoser, the judge nor
the owner can tell a planted case from a real one.

Traces come from the ``diagnosis_generator`` route (one call per case) or from
an authored manifest; both pass the same structural validation.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Mapping, Sequence

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import OperationClient, execute_structured_operation, render_structured_prompt
from learnloop.attempts.grading import resolve_quote_anchor, resolved_rubric
from learnloop.diagnosis.split.history import (
    HistoryAttempt,
    HypothesisRecord,
    StaticHistoryStore,
    learning_object_neighborhood,
)
from learnloop.ids import new_ulid
from learnloop.substrate.canonical_projection import surface_group_id
from learnloop.vault.models import LoadedVault, PracticeItem

PLANTED_PROMPT_VERSION = "planted-scenario-v1"
SHAPES = ("changed_cause", "paraphrased_recurrence", "same_answer_different_cause")
#: A canonical builtin type: a bespoke label would reveal the case is planted.
_PLANTED_ERROR_TYPE = "conceptual_slip"


class PlantedAttemptDraft(WireModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,15}$")
    practice_item_id: str
    learner_answer_md: str
    outcome: Literal["fail", "pass"]
    cause: Literal["A", "B", "C", "none"]
    first_divergence_quote: str | None = Field(
        default=None,
        description="For a failure: text copied VERBATIM from learner_answer_md where it first goes wrong.",
    )
    final_answer: str | None = None


class PlantedScenarioDraft(WireModel):
    cause_a_statement: str
    cause_b_statement: str | None = None
    cause_c_statement: str | None = None
    history: list[PlantedAttemptDraft] = Field(default_factory=list)
    target: PlantedAttemptDraft


_SHAPE_RULES = {
    "changed_cause": (
        "Write a learner whose history is THREE failures caused by belief A, on at "
        "least two different items, then a TARGET failure caused by a different, "
        "plausible belief B. The target answer must be inconsistent with A: someone "
        "holding A would not have written it. cause_c_statement stays null."
    ),
    "paraphrased_recurrence": (
        "Write a learner whose history has TWO failures caused by belief A on two "
        "DIFFERENT items, expressed in different words and notation, ONE failure "
        "caused by an unrelated belief C, and ONE correct answer (outcome pass, "
        "cause none). The TARGET fails because of belief A again, on a third item "
        "where possible, worded differently again. cause_b_statement stays null."
    ),
    "same_answer_different_cause": (
        "Write a learner whose history has ONE failure caused by belief A that "
        "reaches a specific wrong final answer X. The TARGET reaches the SAME "
        "final answer X on the same item (or an item where X is also wrong), but "
        "through a different belief B, visible in the reasoning. Fill final_answer "
        "on both. cause_c_statement stays null."
    ),
}


def _scenario_prompt(shape: str, learning_object_id: str, items: Sequence[Mapping[str, Any]]) -> str:
    return render_structured_prompt(
        "learnloop planted learner scenario",
        PLANTED_PROMPT_VERSION,
        {
            "task": (
                "You write synthetic learner answers with a KNOWN cause, for testing a "
                "diagnostic system. Use only the listed practice items. Each answer "
                "must read like a real learner's written work (concise, the learner's "
                "own notation, no commentary about being synthetic, no mention of "
                "'belief A'). Every failure's first_divergence_quote must be copied "
                "verbatim from that answer. State each belief in learner-model terms "
                "(what the learner thinks is true). Use keys h1, h2, ... for history "
                "and t1 for the target. "
                + _SHAPE_RULES[shape]
            ),
            "context": {
                "shape": shape,
                "learning_object_id": learning_object_id,
                "items": list(items),
            },
        },
    )


@dataclass(frozen=True)
class PlantedAttempt:
    key: str
    attempt_id: str
    practice_item_id: str
    learner_answer_md: str
    completed_at: str
    failed: bool
    cause: str
    first_divergence_quote: str | None = None
    final_answer: str | None = None


@dataclass(frozen=True)
class PlantedCase:
    case_id: str
    shape: str
    learning_object_id: str
    history: tuple[PlantedAttempt, ...]
    target: PlantedAttempt
    causes: Mapping[str, str]
    prior_hypothesis_id: str | None = None
    source: str = "generated"

    @property
    def target_cause(self) -> str:
        return self.causes.get(self.target.cause, "")

    def expected_link_ids(self) -> tuple[str, ...]:
        if self.shape != "paraphrased_recurrence":
            return ()
        return tuple(
            attempt.attempt_id
            for attempt in self.history
            if attempt.failed and attempt.cause == self.target.cause
        )

    def forbidden_link_ids(self) -> tuple[str, ...]:
        return tuple(
            attempt.attempt_id
            for attempt in self.history
            if attempt.failed and attempt.cause != self.target.cause
        )

    def truth(self) -> dict[str, Any]:
        return {
            "shape": self.shape,
            "target_cause_label": self.target.cause,
            "target_cause": self.target_cause,
            "other_causes": {
                label: statement for label, statement in self.causes.items() if label != self.target.cause
            },
            "expected_link_attempt_ids": list(self.expected_link_ids()),
            "forbidden_link_attempt_ids": list(self.forbidden_link_ids()),
            "prior_hypothesis_id": self.prior_hypothesis_id,
        }

    def as_record(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "shape": self.shape,
            "learning_object_id": self.learning_object_id,
            "history": [asdict(attempt) for attempt in self.history],
            "target": asdict(self.target),
            "causes": dict(self.causes),
            "prior_hypothesis_id": self.prior_hypothesis_id,
            "source": self.source,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "PlantedCase":
        return cls(
            case_id=str(record["case_id"]),
            shape=str(record["shape"]),
            learning_object_id=str(record["learning_object_id"]),
            history=tuple(PlantedAttempt(**dict(row)) for row in record.get("history") or []),
            target=PlantedAttempt(**dict(record["target"])),
            causes=dict(record.get("causes") or {}),
            prior_hypothesis_id=record.get("prior_hypothesis_id"),
            source=str(record.get("source") or "generated"),
        )


class PlantedCaseInvalid(ValueError):
    pass


def _validate_draft(
    shape: str,
    draft: PlantedScenarioDraft,
    vault: LoadedVault,
    allowed_items: set[str],
) -> None:
    attempts = [*draft.history, draft.target]
    keys = [attempt.key for attempt in attempts]
    if len(set(keys)) != len(keys):
        raise PlantedCaseInvalid("duplicate attempt keys")
    for attempt in attempts:
        if attempt.practice_item_id not in allowed_items or attempt.practice_item_id not in vault.practice_items:
            raise PlantedCaseInvalid(f"unknown practice item {attempt.practice_item_id!r}")
        if not attempt.learner_answer_md.strip():
            raise PlantedCaseInvalid("empty planted answer")
        if attempt.outcome == "fail":
            if attempt.cause == "none":
                raise PlantedCaseInvalid("a planted failure needs a cause")
            quote = attempt.first_divergence_quote or ""
            if not quote.strip() or resolve_quote_anchor(attempt.learner_answer_md, quote).char_start is None:
                raise PlantedCaseInvalid("first_divergence_quote is not verbatim in the answer")
    if draft.target.outcome != "fail":
        raise PlantedCaseInvalid("the planted target must be a failure")
    failures = [attempt for attempt in draft.history if attempt.outcome == "fail"]
    if shape == "changed_cause":
        if draft.target.cause != "B" or not draft.cause_b_statement:
            raise PlantedCaseInvalid("changed_cause needs a target caused by B")
        if len([attempt for attempt in failures if attempt.cause == "A"]) < 2:
            raise PlantedCaseInvalid("changed_cause needs at least two A failures")
    elif shape == "paraphrased_recurrence":
        same = [attempt for attempt in failures if attempt.cause == "A"]
        if draft.target.cause != "A" or len(same) < 2:
            raise PlantedCaseInvalid("paraphrased_recurrence needs two A failures and an A target")
        if not any(attempt.cause == "C" for attempt in failures) or not draft.cause_c_statement:
            raise PlantedCaseInvalid("paraphrased_recurrence needs a C distractor")
    elif shape == "same_answer_different_cause":
        if draft.target.cause != "B" or not draft.cause_b_statement:
            raise PlantedCaseInvalid("same_answer_different_cause needs a B target")
        same_answer = [
            attempt for attempt in failures
            if attempt.cause == "A"
            and attempt.final_answer
            and draft.target.final_answer
            and " ".join(attempt.final_answer.split()).casefold() == " ".join(draft.target.final_answer.split()).casefold()
        ]
        if not same_answer:
            raise PlantedCaseInvalid("same_answer_different_cause needs an A failure with the same final answer")
    else:  # pragma: no cover - guarded by callers
        raise PlantedCaseInvalid(f"unknown shape {shape!r}")


def case_from_draft(
    shape: str,
    draft: PlantedScenarioDraft,
    *,
    vault: LoadedVault,
    learning_object_id: str,
    allowed_items: set[str],
    start: datetime,
    source: str = "generated",
) -> PlantedCase:
    """Validate a draft and mint real-looking ids and timestamps."""

    _validate_draft(shape, draft, vault, allowed_items)
    causes = {"A": draft.cause_a_statement}
    if draft.cause_b_statement:
        causes["B"] = draft.cause_b_statement
    if draft.cause_c_statement:
        causes["C"] = draft.cause_c_statement

    def planted(row: PlantedAttemptDraft, hours: int) -> PlantedAttempt:
        return PlantedAttempt(
            key=row.key,
            attempt_id=new_ulid(),
            practice_item_id=row.practice_item_id,
            learner_answer_md=row.learner_answer_md,
            completed_at=(start + timedelta(hours=hours)).isoformat().replace("+00:00", "Z"),
            failed=row.outcome == "fail",
            cause=row.cause,
            first_divergence_quote=row.first_divergence_quote,
            final_answer=row.final_answer,
        )

    history = tuple(planted(row, 24 * index) for index, row in enumerate(draft.history))
    target = planted(draft.target, 24 * (len(history) + 1))
    prior = new_ulid() if shape == "changed_cause" else None
    return PlantedCase(
        case_id=new_ulid(),
        shape=shape,
        learning_object_id=learning_object_id,
        history=history,
        target=target,
        causes=causes,
        prior_hypothesis_id=prior,
        source=source,
    )


def candidate_items(vault: LoadedVault, learning_object_id: str) -> list[PracticeItem]:
    """Items on the LO and its one-hop neighbours (cross-surface material)."""

    neighborhood = learning_object_neighborhood(vault, learning_object_id)
    wanted = set(neighborhood.all_ids())
    return sorted(
        (item for item in vault.practice_items.values() if item.learning_object_id in wanted),
        key=lambda item: (item.learning_object_id != learning_object_id, item.id),
    )


def _item_payload(vault: LoadedVault, item: PracticeItem) -> dict[str, Any]:
    rubric = resolved_rubric(vault, item)
    expected = item.expected_answer
    return {
        "practice_item_id": item.id,
        "learning_object_id": item.learning_object_id,
        "prompt": item.prompt,
        "expected_answer": expected if isinstance(expected, str) else json.dumps(expected, sort_keys=True),
        "rubric": [{"id": criterion.id, "points": criterion.points, "description": criterion.description} for criterion in rubric.criteria],
    }


def plantable_learning_objects(vault: LoadedVault, preferred: Sequence[str] = ()) -> list[str]:
    """LOs with at least two candidate items, preferred ones first."""

    eligible = [
        lo_id
        for lo_id in sorted(vault.learning_objects)
        if len(candidate_items(vault, lo_id)) >= 2
    ]
    first = [lo_id for lo_id in dict.fromkeys(preferred) if lo_id in eligible]
    return first + [lo_id for lo_id in eligible if lo_id not in first]


def scenario_request(vault: LoadedVault, shape: str, learning_object_id: str, *, max_items: int = 8) -> tuple[str, set[str]]:
    items = candidate_items(vault, learning_object_id)[:max_items]
    payload = [_item_payload(vault, item) for item in items]
    return _scenario_prompt(shape, learning_object_id, payload), {item.id for item in items}


def request_planted_scenario(client: OperationClient, prompt: str) -> PlantedScenarioDraft:
    return execute_structured_operation(
        client,
        purpose="diagnosis_planted_scenario",
        prompt=prompt,
        result_model=PlantedScenarioDraft,
    )


def cases_from_manifest(
    payload: Any,
    *,
    vault: LoadedVault,
    start: datetime,
) -> list[PlantedCase]:
    """Authored cases: ``[{"shape", "learning_object_id", "scenario": <draft>}]``."""

    rows = payload.get("cases") if isinstance(payload, Mapping) else payload
    if not isinstance(rows, list):
        raise ValueError("planted manifest must be a list or {'cases': [...]}")
    cases = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or set(row) - {"shape", "learning_object_id", "scenario"}:
            raise ValueError(f"planted manifest case {index} must have only shape, learning_object_id, scenario")
        shape = str(row.get("shape") or "")
        if shape not in SHAPES:
            raise ValueError(f"planted manifest case {index} has unknown shape {shape!r}")
        lo_id = str(row.get("learning_object_id") or "")
        if lo_id not in vault.learning_objects:
            raise ValueError(f"planted manifest case {index} names unknown LO {lo_id!r}")
        draft = PlantedScenarioDraft.model_validate(row.get("scenario"))
        allowed = {item.id for item in candidate_items(vault, lo_id)}
        cases.append(
            case_from_draft(
                shape, draft, vault=vault, learning_object_id=lo_id, allowed_items=allowed,
                start=start + timedelta(days=30 * index), source="manifest",
            )
        )
    return cases


def _history_attempt(vault: LoadedVault, attempt: PlantedAttempt) -> HistoryAttempt:
    """A planted past attempt, graded by construction (blind-equivalent)."""

    item = vault.practice_items[attempt.practice_item_id]
    rubric = resolved_rubric(vault, item)
    criteria = [criterion.id for criterion in rubric.criteria]
    facets = tuple(vault.canonical_facet_id(str(value)) for value in item.evidence_facets)
    return HistoryAttempt(
        attempt_id=attempt.attempt_id,
        learning_object_id=item.learning_object_id,
        practice_item_id=item.id,
        completed_at=attempt.completed_at,
        surface_group=surface_group_id(item),
        item_prompt=item.prompt,
        learner_answer_md=attempt.learner_answer_md,
        attempt_type="independent_attempt",
        score=0.0 if attempt.failed else float(rubric.max_points),
        max_points=float(rubric.max_points),
        failed_criteria=tuple(criteria) if attempt.failed else (),
        passed_criteria=() if attempt.failed else tuple(criteria),
        first_divergence_quotes=(attempt.first_divergence_quote,) if attempt.failed and attempt.first_divergence_quote else (),
        error_types=(_PLANTED_ERROR_TYPE,) if attempt.failed else (),
        target_facets=facets if attempt.failed else (),
        validity_scopes=("valid_measurement",) if attempt.failed else (),
        item_facets=facets,
        failed_criterion_facets=facets if attempt.failed else (),
        grader_mode="blind",
    )


def planted_history_store(vault: LoadedVault, case: PlantedCase) -> StaticHistoryStore:
    attempts = [_history_attempt(vault, attempt) for attempt in case.history]
    hypotheses: list[HypothesisRecord] = []
    if case.prior_hypothesis_id is not None:
        sources = [attempt for attempt in case.history if attempt.failed and attempt.cause == "A"]
        last = sources[-1] if sources else None
        hypotheses.append(
            HypothesisRecord(
                id=case.prior_hypothesis_id,
                kind="causal_hypothesis",
                statement=case.causes.get("A", ""),
                scope="learner_state",
                status="candidate",
                lifecycle="candidate",
                learning_object_id=case.learning_object_id,
                source_attempt_id=last.attempt_id if last else None,
                validated_evidence_count=len(sources),
                last_updated=last.completed_at if last else None,
                target_facets=attempts[-1].item_facets if attempts else (),
            )
        )
    return StaticHistoryStore(attempts=attempts, hypotheses=hypotheses)


def default_start() -> datetime:
    return datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)


__all__ = [
    "PLANTED_PROMPT_VERSION",
    "SHAPES",
    "PlantedAttempt",
    "PlantedAttemptDraft",
    "PlantedCase",
    "PlantedCaseInvalid",
    "PlantedScenarioDraft",
    "candidate_items",
    "case_from_draft",
    "cases_from_manifest",
    "default_start",
    "plantable_learning_objects",
    "planted_history_store",
    "request_planted_scenario",
    "scenario_request",
]
