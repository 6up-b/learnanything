"""Teacher TE1's synthetic vault and its scripted teacher (spec_teacher_v1; no network, every model a fake).

``build_teacher_vault`` is curriculum C0b's deliverable vault (the book ``ext_book`` whose
chapter ``ch_eigen`` teaches ``lo_eigen`` and ``ch_det`` ``lo_det``; the exam-role source
``ext_exam`` whose question is :data:`EXAM_QUESTION`; the second book ``ext_lay`` with the
held-out unit carrying :data:`HELD_OUT_SENTINEL`) with ``lo_det`` a prerequisite of
``lo_eigen``, plus vault items on ``lo_eigen`` and ``lo_det`` with distinctive keys and one
exam-reserved item whose prompt and key carry :data:`RESERVED_SENTINEL`.

``TeacherFake`` plays the teacher from a script: each ``teacher_turn`` request pops the next
scripted turn (a mapping, or a callable given the request's context); it grades checks
through the learner-blind contract with configurable points. Every request's prompt is kept
(``prompts``) for the sentinel gates.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from learnloop.ai.transport import ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.ai.isolation import TOOL_FREE
from learnloop.db.repositories import Repository
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml
from tests.deliverable_fixtures import build_deliverable_vault
from tests.section_coverage_fixtures import HELD_OUT_SENTINEL
from tests.source_retrieval_fakes import EXAM_QUESTION
from tests.structured_ai import StructuredClientFake

RESERVED_SENTINEL = "RESERVEDSENTINEL the reserved exam eigenvalue is forty-two"
SENTINELS = (EXAM_QUESTION, HELD_OUT_SENTINEL, RESERVED_SENTINEL, "RESERVEDSENTINEL", "HELDOUTSENTINEL")
NOW = "2026-11-01T09:00:00Z"

#: Vault items with distinctive keys (no teaching text in the scripts shares their words).
ITEMS = {
    "pi_eig_1": ("lo_eigen", "Find the eigenvalues of [[2,0],[0,5]].", "quokka zebra marmot: two, five"),
    "pi_eig_2": ("lo_eigen", "Give an eigenvector of [[2,0],[0,5]] for its larger eigenvalue.",
                 "pangolin narwhal: vector (0, 1)"),
    "pi_eig_3": ("lo_eigen", "Is [[1,1],[0,1]] diagonalizable?", "axolotl wombat: no, single eigenvector"),
    "pi_det_1": ("lo_det", "Compute det [[1,2],[3,4]].", "capybara ocelot: minus two"),
    "pi_det_2": ("lo_det", "What happens to a determinant when two rows swap?", "tapir gecko: flips sign"),
}
RESERVED_ITEM = "pi_eig_reserved"


def _item(item_id: str, lo_id: str, prompt: str, answer: str) -> dict[str, Any]:
    return {
        "id": item_id, "learning_object_id": lo_id, "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt"], "evidence_facets": [], "prompt": prompt,
        "expected_answer": answer, "hints": [],
        "grading_rubric": {"max_points": 4, "criteria": [
            {"id": "correctness", "points": 4, "description": "Answer matches the expected answer in substance."}]},
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW, "updated_at": NOW,
    }


def build_teacher_vault(root: Path, *, config: str = "", reserved: bool = True,
                        version: str | None = None) -> tuple[VaultPaths, Repository]:
    from learnloop.algorithm_versions import TEACHER_ALGORITHM_VERSION
    from tests.helpers import set_algorithm_version

    paths, repository = build_deliverable_vault(root, config=config, prerequisite=True)
    set_algorithm_version(paths, version or TEACHER_ALGORITHM_VERSION)
    for item_id, (lo_id, prompt, answer) in ITEMS.items():
        write_yaml(paths.practice_item_path("linear-algebra", item_id), _item(item_id, lo_id, prompt, answer))
    if reserved:
        from learnloop.source_retrieval import deliverables as DL
        from learnloop.vault.loader import load_vault

        write_yaml(paths.practice_item_path("linear-algebra", RESERVED_ITEM),
                   _item(RESERVED_ITEM, "lo_eigen", f"{RESERVED_SENTINEL}: compute it.", RESERVED_SENTINEL))
        created = DL.create_deliverable(load_vault(paths.root), repository, "My midterm", exam=True)
        repository.insert_exam_pool_items([{"id": "epi_te1", "goal_id": created["goal_id"],
                                            "practice_item_id": RESERVED_ITEM,
                                            "reserved_at": "2026-10-30T00:00:00Z"}])
    return paths, repository


def context_of(prompt: str) -> dict[str, Any]:
    start = prompt.index("{", prompt.index("prompt_version"))
    return json.loads(prompt[start:])["context"]


Turn = Mapping[str, Any] | Callable[[dict[str, Any]], Mapping[str, Any]]


class TeacherFake(StructuredClientFake):
    """A scripted teacher and a blind grader (``points``: per criterion, default full marks)."""

    provider_name = "fake_teacher"
    provider_type = "fake"
    model = "fake-teacher-model"

    def __init__(self, turns: list[Turn] | None = None, *, points: Mapping[str, float] | None = None,
                 full: bool = True) -> None:
        self.turns = list(turns or [])
        self.points = dict(points or {})
        self.full = full
        self.prompts: list[tuple[str, str]] = []
        self.contexts: list[dict[str, Any]] = []
        self.grading_contexts: list[Any] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, TOOL_FREE, ISOLATED_TURN}

    def complete(self, request: Any) -> Any:
        self.prompts.append((request.purpose, request.prompt))
        if request.purpose == "teacher_turn":
            from learnloop.teacher.contracts import TeacherTurnV1

            context = context_of(request.prompt)
            self.contexts.append(context)
            if not self.turns:
                return TeacherTurnV1.model_validate({"message": "Let's pause here."})
            nxt = self.turns.pop(0)
            payload = nxt(context) if callable(nxt) else nxt
            return TeacherTurnV1.model_validate(dict(payload))
        return super().complete(request)

    def run_blind_grading_proposal(self, context: Any) -> Any:
        from learnloop.attempts.blind_grading import BlindGradingProposal

        self.grading_contexts.append(context)
        evidence = [{
            "criterion_id": criterion["id"],
            "points_awarded": self.points.get(criterion["id"], float(criterion["points"]) if self.full else 0.0),
            "evidence": "The answer states the fact.",
        } for criterion in context.rubric["criteria"]]
        total = int(round(sum(row["points_awarded"] for row in evidence)))
        return BlindGradingProposal.model_validate({
            "local_analysis_md": "Graded against the committed solution.", "attempt_id": context.attempt_id,
            "practice_item_id": context.practice_item_id, "criterion_evidence": evidence,
            "rubric_score": max(0, min(int(context.rubric.get("max_points", total)), total)),
            "grader_confidence": 0.9})

    def run_grading_proposal(self, context: Any) -> Any:
        from learnloop.attempts.ai_contracts import GradingProposal

        self.grading_contexts.append(context)
        evidence = [{"criterion_id": c["id"], "points_awarded": float(c["points"]) if self.full else 0.0,
                     "evidence": "The answer states the fact."} for c in context.rubric["criteria"]]
        return GradingProposal.model_validate({
            "attempt_id": context.attempt_id, "practice_item_id": context.practice_item_id,
            "criterion_evidence": evidence, "rubric_score": int(sum(e["points_awarded"] for e in evidence)),
            "grader_confidence": 0.9})

    def all_prompts(self) -> str:
        return "\n".join(prompt for _purpose, prompt in self.prompts)


def clients(fake: TeacherFake) -> Any:
    from learnloop.teacher.service import Clients

    return Clients(teacher=lambda: fake, grading=lambda: fake, grading_source="ai")


# --- scripted turns ------------------------------------------------------------------------


def plan_turn(context: dict[str, Any]) -> dict[str, Any]:
    """Store a two-node plan anchored at the first delivered passage, and present it."""

    passages = [p["alias"] for s in context["brief"]["sources"].get("sections", []) for p in s.get("passages", [])]
    anchor = passages[:1]
    return {
        "message": "Here is the map: first what an eigenvalue is, then how to find one. Shall we start?",
        "requests": [{"action": "write_plan", "plan": [
            {"id": "n1", "statement": "An eigenvalue scales its eigenvector.", "lo_id": "lo_eigen",
             "anchors": anchor, "premises": []},
            {"id": "n2", "statement": "Find eigenvalues as roots of the characteristic polynomial.",
             "lo_id": "lo_eigen", "anchors": anchor, "premises": ["n1"]},
        ]}],
    }


def check_turn(node: str = "n1", *, solution: str = "The roots of det(A - tI) = 0.",
               message: str = "Apply it to a new case.") -> dict[str, Any]:
    return {
        "message": message,
        "check": {"node": node, "question": "For a 2 by 2 matrix A, what equation gives its eigenvalues?",
                  "form": "free", "committed_solution": solution,
                  "rubric": [{"id": "char_poly", "fact": "the eigenvalues solve det(A - tI) = 0", "points": 2}],
                  "anchors": []},
        "requests": [{"action": "forecast", "forecast_kind": "lesson_check_correct", "node": node, "p": 0.75}],
    }


def landed_turn(node: str = "n1", p: float = 0.6) -> dict[str, Any]:
    return {"message": "That step landed.",
            "requests": [{"action": "forecast", "forecast_kind": "lesson_step_retained", "node": node, "p": p}]}


def landed_and_close_turn(node: str = "n1", p: float = 0.6) -> dict[str, Any]:
    """The step landed: forecast its retention, then close (one turn)."""

    return {"message": "That step landed. Retrieve later: eigenvalues solve det(A - tI) = 0.",
            "requests": [{"action": "forecast", "forecast_kind": "lesson_step_retained", "node": node, "p": p},
                         {"action": "close", "close_reason": "goal_reached",
                          "recap": "Retrieve later: eigenvalues solve det(A - tI) = 0."}]}


def close_turn(recap: str = "Retrieve later: eigenvalues solve det(A - tI) = 0.") -> dict[str, Any]:
    return {"message": "We're done for today.",
            "requests": [{"action": "close", "close_reason": "goal_reached", "recap": recap}]}


__all__ = [
    "EXAM_QUESTION",
    "HELD_OUT_SENTINEL",
    "ITEMS",
    "NOW",
    "RESERVED_ITEM",
    "SENTINELS",
    "TeacherFake",
    "build_teacher_vault",
    "check_turn",
    "clients",
    "close_turn",
    "context_of",
    "landed_and_close_turn",
    "landed_turn",
    "plan_turn",
]
