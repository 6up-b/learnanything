"""Deterministic fakes for learner-text gaps: the judge/reader/drafter LLM, the
Decider, the tutor, and the promotion path's analysis + authoring. No network,
no paid call."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import json
from typing import Any

from learnloop.ai.decisions import ChoiceAnswer, DecisionResult, NoulAnswer
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.diagnosis.text_gaps.contract import NeededVerdict, PrerequisiteDraft
from learnloop.matching.judge import SameOrDifferent
from learnloop.tutor.ai_contracts import LearnerGap, PromotionAnalysis, TutorAnswer

from tests.structured_ai import StructuredClientFake


def _payload(prompt: str) -> dict[str, Any]:
    for chunk in reversed(prompt.split("\n\n")):
        try:
            value = json.loads(chunk)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    start = prompt.find("{")
    return json.loads(prompt[start:]) if start >= 0 else {}


def _text(view: Mapping[str, Any]) -> str:
    return " ".join(str(value) for value in view.values() if value).lower()


PairDecide = Callable[[str, str], str]


def word_match(*words: str) -> PairDecide:
    """``same`` when both sides mention every word, else ``different``."""

    def decide(first: str, second: str) -> str:
        return "same" if all(word in first and word in second for word in words) else "different"

    return decide


def always(verdict: str) -> PairDecide:
    return lambda _first, _second: verdict


class GapLLMFake:
    """The learner_gap_judge / reader / drafter LLM (structured, isolated)."""

    provider_name = "fake_gap_llm"
    # Billed like Codex (the subscription): no price needed, calls still capped.
    provider_type = "codex_sdk"
    model = "fake/gap-judge"

    def __init__(
        self,
        *,
        decide: PairDecide = always("different"),
        needed: str = "yes",
        reading: LearnerGap | None = None,
        draft: PrerequisiteDraft | None = None,
        fail: set[str] | None = None,
        proposal: AuthoringProposal | None = None,
    ) -> None:
        self.decide = decide
        self.proposal = proposal
        self.needed = needed
        self.reading = reading
        self.draft = draft or PrerequisiteDraft(
            concept_title="Eigenvectors", concept_description="Vectors a matrix only scales.",
            learning_object_title="Define an eigenvector",
            learning_object_statement="State what an eigenvector of a matrix is.",
            edge_rationale="Diagonalizing a matrix uses its eigenvectors.",
        )
        self.fail = set(fail or ())
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, TOOL_FREE, ISOLATED_TURN}

    def consume_usage(self):
        from learnloop.ai.usage import TokenUsage

        return TokenUsage()

    def complete(self, request: Any) -> Any:
        payload = _payload(request.prompt)
        self.calls.append((request.purpose, payload))
        if request.purpose in self.fail:
            raise RuntimeError(f"{request.purpose} failed")
        if request.purpose in ("learner_gap_same_prerequisite", "learner_gap_same_belief"):
            context = payload["context"]
            verdict = self.decide(_text(context["first"]), _text(context["second"]))
            return SameOrDifferent(verdict=verdict, rationale="fake judge")
        if request.purpose == "learner_gap_prerequisite_needed":
            return NeededVerdict(verdict=self.needed, rationale="the item builds on it")
        if request.purpose == "learner_gap_reading":
            return self.reading or LearnerGap(kind="none")
        if request.purpose == "learner_gap_prerequisite_draft":
            return self.draft
        if request.purpose == "authoring" and self.proposal is not None:
            # A real author writes the origin LO the promotion context names.
            import re

            found = re.search(r'origin_learning_object_id\\?": \\?"([^"\\]+)', request.prompt)
            data = self.proposal.model_dump(mode="json")
            if found:
                for item in data["items"]:
                    if item["item_type"] == "practice_item":
                        item["payload"]["learning_object_id"] = found.group(1)
            return AuthoringProposal.model_validate(data)
        raise AssertionError(f"unexpected purpose {request.purpose}")


class ChoiceDecider:
    """An in-process Decider double: picks an option per question by a rule."""

    provider_name = "fake_decider"
    provider_type = "decider"

    def __init__(self, *, kind: str = "none", pair: PairDecide = always("unsure"), needed: str = "yes",
                 model: str = "fake/decider") -> None:
        from learnloop.ai.execution import model_call, report_call_usage

        self._model_call, self._report = model_call, report_call_usage
        self.kind = kind
        self.pair = pair
        self.needed = needed
        self.model = model
        self.states: list[Any] = []

        class _Settings:
            price_per_million_input = 0.02

        self.settings = _Settings()

    def _choose(self, name: str, state: Any) -> str:
        if name == "kind":
            return self.kind
        if name == "needed":
            return self.needed
        payload = _payload(state) if isinstance(state, str) else {}
        context = payload.get("context") or {}
        if "first" in context:
            return self.pair(_text(context["first"]), _text(context["second"]))
        return "unsure"

    def decide(self, state, questions, *, purpose):
        self.states.append((purpose, state))
        answers = {}
        with self._model_call(self, purpose=purpose, prompt=json.dumps(state, sort_keys=True, default=str)):
            self._report({"input_tokens": 120, "output_tokens": 3, "cost": 0.0000024})
            for name, question in questions.items():
                options = list(getattr(question, "options", {}) or {})
                if not options:
                    answers[name] = NoulAnswer(0.5)
                    continue
                choice = self._choose(name, state)
                choice = choice if choice in options else options[0]
                rest = (1.0 - 0.9) / max(1, len(options) - 1)
                probabilities = {option: (0.9 if option == choice else rest) for option in options}
                if len(options) == 1:
                    probabilities = {choice: 1.0}
                answers[name] = ChoiceAnswer(choice=choice, probabilities=probabilities, confidence=0.9)
            return DecisionResult(answers=answers, model=self.model + "-dated", input_tokens=120, output_tokens=3,
                                  cost=0.0000024, response_id="r", provider="Fake")


class GapTutor(StructuredClientFake):
    """The tutor, answering with a named gap."""

    provider_name = "fake_tutor"
    # The tutor on Codex (the owner's default route): the seed's analysis call
    # is admitted on the tutor's route, a subscription one here.
    provider_type = "codex_sdk"
    model = "fake/tutor"

    def __init__(self, gap: LearnerGap | None, *, question_type: str = "prerequisite", answer_md: str = "Think it through.",
                 analysis: PromotionAnalysis | None = None, proposal: AuthoringProposal | None = None) -> None:
        self.gap = gap
        self.question_type = question_type
        self.answer_md = answer_md
        self.analysis = analysis or PromotionAnalysis(question_nature="core_recall")
        self.proposal = proposal
        self.contexts: list[Any] = []

    def run_tutor_qa(self, context):
        self.contexts.append(context)
        return TutorAnswer(answer_md=self.answer_md, question_type=self.question_type,
                           facets=list(context.candidate_facets), learner_gap=self.gap)

    def run_promotion_analysis(self, context):
        return self.analysis

    def run_authoring_proposal(self, context):
        if self.proposal is None:
            raise AssertionError("no authoring proposal configured")
        return self.proposal


def seed_proposal(item_id: str = "pi_ltg_seed_001") -> AuthoringProposal:
    """A valid one-item practice proposal (its LO is overwritten to the created one)."""

    return AuthoringProposal.model_validate({
        "summary": "Seed item for a prerequisite created from the learner's question.",
        "source_refs": [{"ref_type": "note", "ref_id": "note_la_source"}],
        "items": [{
            "client_item_id": "seed",
            "item_type": "practice_item",
            "operation": "create",
            "proposed_entity_id": item_id,
            "source_ref_ids": ["note_la_source"],
            "rationale": 'From the tutor question "What is an eigenvector?"',
            "review_route": "auto_apply",
            "audit": {"audit_type": "deterministic_validator", "status": "passed", "summary": "ok",
                      "validator_name": "short-answer-normalizer", "validator_version": "1"},
            "payload": {
                "learning_object_id": "placeholder",
                "subjects": None,
                "practice_mode": "short_answer",
                "attempt_types_allowed": ["independent_attempt"],
                "prompt": "What is an eigenvector of a matrix A?",
                "expected_answer": "A nonzero vector v with Av = lambda v.",
                "evidence_facets": ["recall"],
                "evidence_weights": {"recall": 1.0},
                "criterion_facet_weights": {"correctness": {"recall": 1.0}},
                "retrieval_demand": 0.8,
                "transfer_distance": 0.2,
                "scaffold_level": 0.0,
                "surface_family": "eigenvector-definition",
                "repair_targets": ["recall"],
                "grading_rubric": {"max_points": 4,
                                   "criteria": [{"id": "correctness", "points": 4, "description": "Defines it."}],
                                   "fatal_errors": []},
            },
        }],
    })
