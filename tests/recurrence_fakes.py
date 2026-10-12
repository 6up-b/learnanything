"""Deterministic fakes for Slice 2 T1: a diagnoser with chosen cause statements
and a same-cause judge. No network, no paid call."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from learnloop.ai.schemas import CandidateCause
from learnloop.db.stores.judgments import append_judgment
from learnloop.matching.judge import SameOrDifferent

from tests.diagnosis_fakes import ReviewFakeClient

Decide = Callable[[str, str], str]


def different(_left: str, _right: str) -> str:
    return "different"


def shares_word(word: str) -> Decide:
    """``same`` when both statements mention ``word``, else ``different``."""

    def decide(left: str, right: str) -> str:
        return "same" if word in left.lower() and word in right.lower() else "different"

    return decide


class StatementFake(ReviewFakeClient):
    """The M1 fake diagnoser, with the cause statement chosen by the answer text.

    ``statements`` maps a substring of the learner answer to the statement the
    diagnosis names (and its misconception statement). ``cite`` keeps the
    base fake's one pattern claim (it cites the first earlier failure, a
    validated citation). ``decide`` answers the same-cause judge.
    """

    def __init__(self, statements: Mapping[str, str], *, cite: bool = False, decide: Decide = different,
                 operators: Mapping[str, str] | None = None, escalation_operator: str = "elicit_rule",
                 on_diagnosis: Callable[[str], None] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.statements = dict(statements)
        self.cite = cite
        self.decide = decide
        #: answer substring -> the repair operator its diagnosis suggests.
        self.operators = dict(operators or {})
        #: The operator the escalated-repair request answers with (the
        #: default repeats the diagnoser's: a model ignoring the instruction).
        self.escalation_operator = escalation_operator
        #: Every escalated-repair request's context, in order.
        self.escalation_requests: list[dict[str, Any]] = []
        #: Called with the answer text on every diagnosis (e.g. to cancel a command).
        self.on_diagnosis = on_diagnosis
        self.judged: list[tuple[str, str]] = []

    def _operator(self, answer: str) -> str:
        for key, operator in self.operators.items():
            if key in answer:
                return operator
        return "elicit_rule"

    def _statement(self, answer: str) -> str:
        for key, statement in self.statements.items():
            if key in answer:
                return statement
        return "The learner misapplies the rule."

    def _diagnosis(self, request, context):
        result = super()._diagnosis(request, context)
        answer = str(context["current_attempt"]["learner_answer_md"])
        if self.on_diagnosis is not None:
            self.on_diagnosis(answer)
        statement = self._statement(answer)
        events = [
            event.model_copy(
                update={
                    "candidate_causes": [
                        CandidateCause(statement=statement, cause_scope="learner_state", prior_weight=2.0),
                        CandidateCause(statement="A slip while copying.", cause_scope="transient_execution", prior_weight=0.5),
                    ],
                    "misconception_statement": statement,
                }
            )
            for event in result.event_diagnoses
        ]
        repairs = [
            repair.model_copy(update={"operator": self._operator(answer), "eliciting_question": "What does the rule say?"})
            for repair in result.repair_suggestions
        ]
        return result.model_copy(
            update={
                "event_diagnoses": events,
                "pattern_claims": result.pattern_claims if self.cite else [],
                "repair_suggestions": repairs,
            }
        )

    def _same_cause_judgment(self, request, context):
        first, second = context["first"]["statement"], context["second"]["statement"]
        self.judged.append((first, second))
        return SameOrDifferent(verdict=self.decide(first, second), rationale="fake judgment")

    def _recurrence_escalation_repair(self, request, context):
        from learnloop.diagnosis.recurrence.escalation import EscalatedRepair

        self.escalation_requests.append(dict(context))
        operator = self.escalation_operator
        return EscalatedRepair(
            operator=operator,
            representation="worked contrast",
            practice_mode="contrast",
            rationale="Put the wrong and the right reasoning side by side.",
            eliciting_question="Which step differs?" if operator.startswith("elicit_") else None,
        )


class JudgeFake(ReviewFakeClient):
    """Only the same-cause judge."""

    def __init__(self, decide: Decide = different, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.decide = decide
        self.judged: list[tuple[str, str]] = []

    def _same_cause_judgment(self, request, context):
        first, second = context["first"]["statement"], context["second"]["statement"]
        self.judged.append((first, second))
        return SameOrDifferent(verdict=self.decide(first, second), rationale="fake judgment")


def record_verdict(repository, *, left: str, right: str, verdict: str, judge: str = "llm",
                   kind: str = "hypothesis", created_at: str | None = None) -> str:
    """Append one same_cause verdict directly (as an import or a judge would)."""

    with repository.atomic():
        return append_judgment(
            repository.connection(),
            task="same_cause",
            left_kind=kind,
            left_id=left,
            right_kind=kind,
            right_id=right,
            judge=judge,
            judge_model="fake-model" if judge in ("llm", "diagnoser") else None,
            prompt_version="test" if judge in ("llm", "diagnoser") else None,
            input_hash=f"{left}|{right}|{judge}|{verdict}",
            verdict=verdict,
            rationale="test",
            created_at=created_at,
        )


__all__ = ["JudgeFake", "StatementFake", "different", "record_verdict", "shares_word"]
