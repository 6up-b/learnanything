"""Deterministic fake model clients and vault seeding for PF-b tests.

One ``PFFake`` answers every PF role by its result model. It solves linear
equations ``ax + b = c`` itself, so panel agreement, sympy equivalence and
CAS checks run on real arithmetic. Stems containing ``AMBIGUOUS`` make the
panel disagree; ``NEARVARIANT`` makes the structure check say ``near``;
``RUBRICMISMATCH`` makes the rubric inapplicable.
"""
from __future__ import annotations

import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Any

from learnloop.ai.execution import report_call_usage
from learnloop.content.authoring import pf_contracts as C
from learnloop.db.repositories import Repository
from learnloop.substrate.families import apply_family
from learnloop.vault.loader import load_vault
from learnloop.vault.models import ActivityFamily
from learnloop.vault.writer import upsert_practice_item
from tests.helpers import create_basic_vault

NOW = "2026-10-12T12:00:00+00:00"

SYMPY_CHECK = (
    "import sympy\n"
    "def check(reference, answer):\n"
    "    try:\n"
    "        return sympy.simplify(sympy.sympify(reference) - sympy.sympify(answer)) == 0\n"
    "    except Exception:\n"
    "        return False\n"
)

LINEAR_PROGRAM = '''
import random, sympy

def generate(seed):
    rng = random.Random(seed)
    a = rng.randint(2, 9)
    b = rng.randint(1, 20)
    c = rng.randint(21, 40)
    x = sympy.Rational(c - b, a)
    return {
        "parameters": {"a": a, "b": b, "c": c},
        "stem": f"Solve {a}x + {b} = {c} for x.",
        "solution": f"Subtract {b} from both sides, then divide by {a}.",
        "final_answer": str(x),
        "checkpoints": ["isolate the x term", "divide by the coefficient"],
    }

def check(draw, answer):
    p = draw["parameters"]
    try:
        return sympy.simplify(sympy.sympify(answer) - sympy.Rational(p["c"] - p["b"], p["a"])) == 0
    except Exception:
        return False
'''

_LINEAR = re.compile(r"(\d+)\s*x\s*\+\s*(\d+)\s*=\s*(\d+)")


def solve_linear(stem: str) -> str | None:
    match = _LINEAR.search(stem)
    if not match:
        return None
    a, b, c = (int(group) for group in match.groups())
    value = Fraction(c - b, a)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _letters(text: str) -> str:
    return re.sub(r"\W", "", text.casefold())


def prompt_context(prompt: str) -> dict[str, Any]:
    return json.loads(prompt[prompt.index("{"):])["context"]


class PFFake:
    provider_name = "fake"

    def __init__(self, model: str = "fake-model", *, proposals: list[dict[str, Any]] | None = None,
                 program: str = LINEAR_PROGRAM, select_everything: bool = False,
                 provider_type: str | None = None) -> None:
        self.model = model
        self.proposals = proposals
        self.program = program
        self.select_everything = select_everything
        self.calls: list[Any] = []
        if provider_type is not None:
            self.provider_type = provider_type

    def supports(self, capability: str) -> bool:
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request):
        self.calls.append(request)
        report_call_usage({"input_tokens": 100, "output_tokens": 50, "resolved_model": self.model + "-resolved"})
        model = request.result_model
        context = prompt_context(request.prompt)
        if model is C.SkeletonResult:
            return C.SkeletonResult(techniques=["isolate the variable", "divide"], operations=["a -> b"],
                                    checkpoints=["isolate the x term", "divide by the coefficient"],
                                    summary="Linear equation.")
        if model is C.GeneratorProgramResult:
            return C.GeneratorProgramResult(program=self.program,
                                            checkpoints=["isolate the x term", "divide by the coefficient"],
                                            rationale="linear draws")
        if model is C.ProposalBatch:
            count = context["count"]
            items = self.proposals or default_proposals(self.model)
            return C.ProposalBatch(candidates=[C.ProposedCandidate(**item) for item in items[:count]])
        if model is C.PanelSolve and "question" in context:  # closed-book answer
            generic = "GENERIC" in context["question"]
            return C.PanelSolve(final_answer="the generic answer" if generic else "UNKNOWN",
                                answer_kind="text", work_summary="closed book")
        if model is C.SourceAnchoredBatch:
            text = context["passages"][0]["text"]
            quote = " ".join(text.split()[:7])
            items = [
                ("what", f"According to the source, what defines the focus? (variant {i})", quote, True, None)
                for i in range(2)
            ] + [
                ("why", "Why did the authors choose a directrix?", "the authors preferred elegance above all", True, None),
                ("what", "GENERIC: what is a parabola?", quote, True, None),
                ("method_does_not_apply", "When does the focus construction fail?", quote, True, None),
            ]
            return C.SourceAnchoredBatch(candidates=[
                C.SourceAnchoredCandidate(
                    cited_ref="s0", cited_quote=cited, stem=stem, solution="Read the cited span.",
                    answer="the generic answer" if "GENERIC" in stem else f"answer {index}",
                    item_kind=kind, source_specific=specific, counterexample=counter)
                for index, (kind, stem, cited, specific, counter) in enumerate(items)][:context["count"]])
        if model is C.PanelSolve:
            stem = context["problem"]
            answer = solve_linear(stem) or "UNSOLVABLE"
            if "AMBIGUOUS" in stem:
                answer = str(7 + context["solve_index"] + len(self.calls))
            return C.PanelSolve(final_answer=answer, answer_kind="numeric", work_summary="solved")
        if model is C.EquivalenceResult:
            from sympy import simplify, sympify

            reference = context["reference_final_answer"]
            try:
                sympify(reference)
                kind = "numeric"
            except Exception:
                kind = "text"
            agreements = []
            for entry in context["answers"]:
                try:
                    agreements.append(bool(simplify(sympify(reference) - sympify(entry["answer"])) == 0))
                except Exception:
                    agreements.append(entry["answer"].strip() == reference.strip())
            return C.EquivalenceResult(answer_kind=kind, agreements=agreements,
                                       sympy_check=SYMPY_CHECK if kind == "numeric" else None)
        if model is C.StructureVerdict:
            stem = context["candidate"]["stem"]
            relation = "near" if "NEARVARIANT" in stem else "isomorph"
            return C.StructureVerdict(relation=relation, checkpoint_sequence_preserved=relation == "isomorph",
                                      rubric_applies_verbatim="RUBRICMISMATCH" not in stem, rationale="checked")
        if model is C.FreshnessVerdict:
            stem = _letters(context["candidate"]["stem"])
            return C.FreshnessVerdict(comparisons=[
                C.FreshnessComparison(
                    ref=item["ref"],
                    verdict="same_surface" if _letters(item["prompt"]) == stem else "different",
                    rationale="compared")
                for item in context["comparisons"]])
        if model is C.SelectionVerdict:
            refs = [item["ref"] for item in context["candidates"]]
            selected = refs if self.select_everything else refs[:context["slots"]]
            if self.select_everything:
                selected = selected + ["c999"]
            return C.SelectionVerdict(ranking=refs, selected=selected, rationale="diverse")
        if model is C.PairwiseVerdict:
            return C.PairwiseVerdict(preferred="A", depth="A", accuracy="tie", rationale="A deeper")
        if model is C.ValidAlternativeTraces:
            answer = solve_linear(context["problem"]) or "5"
            return C.ValidAlternativeTraces(
                canonical=C.TraceVariant(trace="Subtract then divide.", final_answer=answer, route_note="canonical"),
                alternatives=[C.TraceVariant(trace="Divide every term first, then subtract.", final_answer=answer,
                                             route_note="divide first"),
                              C.TraceVariant(trace="Guess and check.", final_answer="999", route_note="wrong")])
        raise AssertionError(f"unexpected result model {model}")


def proposal(stem: str, answer: str | None = None) -> dict[str, Any]:
    return {"stem": stem, "solution": "Isolate x, then divide.", "final_answer": answer or solve_linear(stem) or "1",
            "answer_kind": "numeric", "change_note": "new numbers", "preserved_note": "same steps",
            "techniques": ["isolate the variable", "divide"],
            "checkpoints": ["isolate the x term", "divide by the coefficient"]}


_CONTAINERS = ("tank", "barrel", "flask", "basin", "vat", "jug", "cask")


def default_proposals(model: str) -> list[dict[str, Any]]:
    """Distinct per model, so different proposers never collide by accident."""
    seed = sum(map(ord, model))
    container = _CONTAINERS[seed % len(_CONTAINERS)]
    offset = seed % 5
    return [proposal(f"A {container} holds {3 + offset}x + {5 + index} = {30 + index} litres; solve for x.")
            for index in range(10)]


def enable_pf(root: Path, **settings: Any) -> None:
    config = root / "learnloop.toml"
    text = config.read_text(encoding="utf-8").replace("generation_enabled = false", "generation_enabled = true")
    for key, value in settings.items():
        line = f"{key} = {json.dumps(value) if isinstance(value, (str, list)) else value}"
        if re.search(rf"(?m)^{key} = .*$", text):
            text = re.sub(rf"(?m)^{key} = .*$", line, text, count=1)
        else:
            text = text.replace("[pf]\n", f"[pf]\n{line}\n", 1)
    config.write_text(text, encoding="utf-8")


def seed_pf_vault(root: Path, *, enabled: bool = True, extra_items: int = 0, **settings: Any):
    """A basic vault plus a quantitative parent item in an owner-authored family."""
    paths = create_basic_vault(root)
    if enabled:
        enable_pf(paths.root, **settings)
    upsert_practice_item(paths.root, {
        "schema_version": 1, "id": "pi_linear_001", "learning_object_id": "lo_svd_definition",
        "practice_mode": "short_answer", "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
        "prompt": "Solve 2x + 4 = 10 for x.", "expected_answer": "Final answer: 3\n\nSubtract 4, divide by 2.",
        "difficulty": 0.4,
        "grading_rubric": {"max_points": 2, "criteria": [
            {"id": "setup", "points": 1, "description": "Isolates the x term."},
            {"id": "answer", "points": 1, "description": "Correct value of x."}]},
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW, "updated_at": NOW,
    })
    for index in range(extra_items):
        upsert_practice_item(paths.root, {
            "schema_version": 1, "id": f"pi_extra_{index:03d}", "learning_object_id": "lo_svd_definition",
            "practice_mode": "short_answer", "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
            "prompt": f"Extra question {index} about matrices.", "expected_answer": "x",
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW, "updated_at": NOW,
        })
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    family = ActivityFamily(
        id="af_linear", learning_object_id="lo_svd_definition",
        idea_statement="Solve a one-step linear equation", retrieval_target="The value of x with work",
        created_at=NOW, updated_at=NOW,
    )
    apply_family(vault, repository, family, {"pi_linear_001": "same_target"}, proposal_id="pfp_test",
                 judge="owner", rationale="test family")
    return load_vault(paths.root), repository, paths


def clients(proposer_models=("fake-a", "fake-b"), **overrides: Any) -> dict[str, Any]:
    base = PFFake("fake-judge")
    result: dict[str, Any] = {
        "skeleton": base, "program": base, "single_shot": base, "source": base, "closed_book": base,
        "proposer": [PFFake(model) for model in proposer_models],
        "panel": [PFFake("fake-panel-1"), PFFake("fake-panel-2")],
        "equivalence": base, "structure": base, "freshness": base, "selection": base,
    }
    result.update(overrides)
    return result
