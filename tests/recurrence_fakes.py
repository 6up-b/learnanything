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
                 escalation_reveal_budget: float = 0.0,
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
        self.escalation_reveal_budget = escalation_reveal_budget
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
            answer_reveal_budget=self.escalation_reveal_budget,
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


M1_CAUSE_A = "Believes the factors of an SVD commute, so V and U may swap places."
M1_CAUSE_B = "Forgets to transpose V because the example matrix happens to be symmetric."
M1_DIAGNOSER_B = "Leaves V untransposed, trusting that the example's symmetry makes the transpose unnecessary."


def write_m1_run(run_dir, *, run_id: str = "run-1", linked: bool = False, cited_only: bool = False,
                 mode: str = "full", recovered: bool = True, prompt_version: str | None = None) -> str:
    """A minimal M1 review run directory with ONE planted same-answer/different-cause
    case and one completed diagnosis of its B answer (Slice 1 S1.0).

    ``linked``: the diagnosis's VALIDATED citations include the A answer (a
    false merge on the citation path); ``cited_only``: it cites the A answer
    but the citation did not validate. ``recovered``: M1's planted-cause judge
    said the diagnosis named the target cause. Returns the guard case id.
    """

    import json
    import sqlite3
    from pathlib import Path

    from learnloop.db.stores.diagnosis_review import ensure_review_schema, insert_review_row
    from learnloop.diagnosis.split.settings import DIAGNOSIS_PROMPT_VERSION

    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.json").write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
    a_attempt, b_attempt = f"{run_id}-a", f"{run_id}-b"
    record = {
        "case_id": "planted-0", "shape": "same_answer_different_cause", "learning_object_id": "lo_svd_compute",
        "history": [{"key": "h1", "attempt_id": a_attempt, "practice_item_id": "pi_svd_compute_001",
                     "learner_answer_md": "U Sigma V", "completed_at": "2026-01-01T00:00:00Z", "failed": True,
                     "cause": "A", "first_divergence_quote": "V and U swap", "final_answer": "U Sigma V"}],
        "target": {"key": "t1", "attempt_id": b_attempt, "practice_item_id": "pi_svd_compute_001",
                   "learner_answer_md": "U Sigma V", "completed_at": "2026-01-03T00:00:00Z", "failed": True,
                   "cause": "B", "first_divergence_quote": "V is symmetric", "final_answer": "U Sigma V"},
        "causes": {"A": M1_CAUSE_A, "B": M1_CAUSE_B},
        "prior_hypothesis_id": None, "source": "manifest",
    }
    truth = {"shape": "same_answer_different_cause", "forbidden_link_attempt_ids": [a_attempt],
             "expected_link_attempt_ids": []}
    citation = {"attempt_id": a_attempt, "quote": "V and U swap", "claim_index": 0}
    proposal = {
        "event_diagnoses": [{"event_index": 0, "candidate_causes": [
            {"statement": M1_DIAGNOSER_B, "cause_scope": "learner_state", "prior_weight": 2.0},
            {"statement": "A slip while copying.", "cause_scope": "transient_execution", "prior_weight": 0.5},
        ]}],
        "pattern_claims": [{"hypothesis_ref": "cause:0:0", "relation": "same_mechanism", "cited": [citation]}]
        if (linked or cited_only) else [],
    }
    connection = sqlite3.connect(run_dir / "scratch.sqlite")
    try:
        ensure_review_schema(connection, run_id=run_id)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS judgment_ledger (id TEXT PRIMARY KEY, created_at TEXT, task TEXT, "
            "left_kind TEXT, left_id TEXT, verdict TEXT, rationale TEXT)"
        )
        insert_review_row(connection, "review_planted_cases", {
            "id": "planted-0", "run_id": run_id, "shape": "same_answer_different_cause", "target_attempt_id": b_attempt,
            "truth_json": truth, "history_json": record, "source": "manifest",
        })
        insert_review_row(connection, "review_targets", {
            "id": "target-0", "run_id": run_id, "kind": "planted", "attempt_id": b_attempt,
            "practice_item_id": "pi_svd_compute_001", "learning_object_id": "lo_svd_compute",
            "completed_at": "2026-01-03T00:00:00Z", "planted_case_id": "planted-0", "position": 0,
        })
        insert_review_row(connection, "review_diagnoses", {
            "id": "diagnosis-0", "run_id": run_id, "target_id": "target-0", "arm": "d", "mode": mode,
            "status": "completed", "provider": "fake", "model": "fake-diagnoser",
            "prompt_version": prompt_version or DIAGNOSIS_PROMPT_VERSION, "proposal_json": proposal,
            "validation_report_json": {},
        })
        insert_review_row(connection, "review_context_receipts", {
            "diagnosis_id": "diagnosis-0", "failure_attempt_ids_json": [a_attempt], "success_attempt_ids_json": [],
            "history_attempt_ids_json": [a_attempt], "hypothesis_ids_json": [], "registry_candidate_ids_json": [],
            "prerequisite_refs_json": [], "retrieval_json": {},
            "validated_citations_json": [citation] if linked else [],
        })
        if recovered:
            connection.execute(
                "INSERT INTO judgment_ledger (id, created_at, task, left_kind, left_id, verdict, rationale) "
                "VALUES ('pcm-0', '2026-01-04T00:00:00Z', 'planted_cause_match', 'review_diagnosis', 'diagnosis-0', "
                "'target_cause', '{}')"
            )
        connection.commit()
    finally:
        connection.close()
    return f"m1:{run_id}:planted-0"


__all__ = ["JudgeFake", "StatementFake", "different", "record_verdict", "shares_word", "write_m1_run"]
