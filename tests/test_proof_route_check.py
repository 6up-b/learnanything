"""The valid-alternative gate for proofs and explanations (successor mvp-0.17).

On an item an LLM reads as proof-like, each new blind grade is followed by an
independent re-derivation of the learner's route (another model where one is
configured). The deterministic gate restores a criterion the grader marked
down without locating an error when the check validates the route, records
one disputed on a located step unverified (PF-c's unassessed type; a question
only when the dispute turns on the learner's meaning), and flags a step the
grader accepted that the check refutes with a verbatim quote. Agreement and
disagreement go to judgment_ledger. Fakes only; no network.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    LEARNER_TEXT_GAP_ALGORITHM_VERSION,
    PROOF_ROUTE_CHECK_ALGORITHM_VERSION,
    PROOF_ROUTE_CHECK_VERSIONS,
    SUCCESSOR_CHAIN,
)
from learnloop.attempts.blind_grading import BlindErrorAttribution, BlindGradingProposal
from learnloop.attempts.ai_contracts import CriterionEvidence
from learnloop.attempts.grading import PROVISIONAL_PENDING_CLARIFICATION
from learnloop.attempts.grading_support import UNVERIFIED_REVIEW_REASON
from learnloop.attempts.proof_check import (
    CLARIFICATION_TRIGGER,
    ITEM_KIND_TASK,
    PROOF_ROUTE_REVIEW_REASON,
    ROUTE_CHECK_TASK,
    CriterionRouteVerdict,
    ItemKindReading,
    ProofRouteCheck,
    apply_proof_route_gate,
    item_kind_prompt,
    proof_check_active,
    proof_check_route,
    route_check_prompt,
)
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.diagnosis.split.jobs import diagnosis_status
from learnloop.substrate.canonical_projection import project_canonical_facet_state, unassessed_evidence_row
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import Rubric

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, append_config, split_vault, submit

VERSION = PROOF_ROUTE_CHECK_ALGORITHM_VERSION
ITEM = "pi_svd_compute_001"  # setup (2) + result (2)
#: A route the default fake grades 0/4: ``setup`` with no located error,
#: ``result`` with the located quote "Take the eigenvectors".
ALTERNATIVE = "Take the eigenvectors of A^T A for V, then U = A V Sigma^{-1}."
CLOCK = FrozenClock(datetime(2026, 11, 1, 12, 0, tzinfo=UTC))


class CheckerFake(ReviewFakeClient):
    """The independent checker: an item-kind reading and one route check."""

    def __init__(self, *, kind="proof", reasoning=True, verdicts=None, question=None,
                 reason="not_learner_resident", model="checker-model", **kwargs):
        super().__init__(model=model, **kwargs)
        self.kind, self.reasoning = kind, reasoning
        self.verdicts = verdicts or {}
        self.question, self.reason = question, reason

    def _proof_item_classification(self, request, context):
        assert "learner_answer_md" not in context  # the item alone
        return ItemKindReading(response_kind=self.kind, reasoning_is_graded=self.reasoning, rationale="fake")

    def _proof_route_check(self, request, context):
        # Blind to the grade and the reference: only the item, rubric and answer.
        assert set(context) <= {"prompt", "rubric_criteria", "learner_answer_md", "clarification_exchange"}
        return ProofRouteCheck(
            route_md="restated", step_checks_md="checked",
            criteria=[CriterionRouteVerdict(criterion_id=cid, **spec) for cid, spec in self.verdicts.items()],
            clarification_question_md=self.question, clarification_reason=self.reason,
        )


class LocatedGrader(ReviewFakeClient):
    """The default fake's 0/4 with its located error on ``result`` naming no
    facet, so the grade carries no review concern of its own."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        attributions = [
            row.model_copy(update={"target_evidence_families": [], "target_criterion_ids": ["result"]})
            for row in result.error_attributions
        ]
        return result.model_copy(update={"error_attributions": attributions})


class FullCreditGrader(ReviewFakeClient):
    """Gives every criterion full points whatever the answer."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [
            row.model_copy(update={"points_awarded": 2.0}) for row in result.criterion_evidence
        ]
        return result.model_copy(update={
            "criterion_evidence": evidence, "rubric_score": 4, "error_attributions": [],
        })


@pytest.fixture
def checker(monkeypatch):
    holder: dict = {}

    def install(fake):
        holder["fake"] = fake
        monkeypatch.setattr(
            "learnloop.attempts.proof_check.resolve_check_client", lambda vault, route: holder["fake"]
        )
        return fake

    return install


def _support(repository, attempt_id):
    return repository.latest_blind_grade_record(attempt_id)["record"]["grading_support"]


def _judgments(repository, task):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = ? ORDER BY created_at, id", (task,)
        )]


# -- the version and the switch ---------------------------------------------------------


def test_the_route_check_is_the_latest_successor_and_keeps_every_predecessor():
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == VERSION == "mvp-0.17"
    assert SUCCESSOR_CHAIN[-2] == LEARNER_TEXT_GAP_ALGORITHM_VERSION
    assert PROOF_ROUTE_CHECK_VERSIONS == frozenset({VERSION})


def test_active_only_at_the_successor_with_the_switch_on(tmp_path):
    _paths, vault, _repository = split_vault(tmp_path / "on", version=VERSION, seed=False)
    assert proof_check_active(vault)
    _paths, older, _repository = split_vault(tmp_path / "old", version="mvp-0.16", seed=False)
    assert not proof_check_active(older)
    _paths, off, _repository = split_vault(
        tmp_path / "off", version=VERSION, config="[proof_check]\nenabled = false", seed=False,
    )
    assert not proof_check_active(off)


# -- the gate (pure) ---------------------------------------------------------------------


RUBRIC = Rubric.model_validate({
    "id": "r", "max_points": 4,
    "criteria": [{"id": "setup", "description": "Sets up", "points": 2},
                 {"id": "result", "description": "Concludes", "points": 2}],
})
ANSWER = "Let x be fixed. Then x squared is positive. So the claim holds."


def _proposal(points, attributions=(), fatal=()):
    return BlindGradingProposal(
        local_analysis_md="a", attempt_id="a1", practice_item_id="i",
        criterion_evidence=[CriterionEvidence(criterion_id=cid, points_awarded=p, evidence=f"grader on {cid}")
                            for cid, p in points.items()],
        rubric_score=int(sum(points.values())), fatal_errors=list(fatal),
        error_attributions=list(attributions), grader_confidence=0.9,
    )


def _attribution(criterion, quote):
    return BlindErrorAttribution(
        error_type="conceptual_slip", evidence="e", target_criterion_ids=[criterion],
        first_divergence={"anchor_kind": "span", "criterion_id": criterion, "quote": quote},
        validity_scope="valid_measurement",
    )


def _check(question=None, reason="not_learner_resident", **verdicts):
    return ProofRouteCheck(
        route_md="r", step_checks_md="s",
        criteria=[CriterionRouteVerdict(criterion_id=cid, **spec) for cid, spec in verdicts.items()],
        clarification_question_md=question, clarification_reason=reason,
    )


def test_an_unlocated_mark_down_on_a_validated_route_is_restored():
    gate = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 2.0}), rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "established", "reason_md": "fixing x is a valid start"},
                     result={"verdict": "established"}),
        checker_model="m2",
    )
    assert gate.restored == ("setup",) and gate.unverified == () and gate.flagged == ()
    rows = {row.criterion_id: row for row in gate.proposal.criterion_evidence}
    assert rows["setup"].points_awarded == 2.0
    assert "m2" in rows["setup"].evidence and "grader on setup" in rows["setup"].notes
    assert gate.assessed_shortfall is False
    assert gate.proposal.manual_review_recommended is False
    assert gate.outcomes == {"setup": "restored", "result": "agree_full"}


def test_a_located_error_the_check_finds_valid_is_disputed_and_unassessed():
    gate = apply_proof_route_gate(
        _proposal({"setup": 2.0, "result": 0.0}, [_attribution("result", "x squared is positive")]),
        rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(result={"verdict": "established"}, setup={"verdict": "established"}),
    )
    assert gate.unverified == ("result",) and gate.restored == ()
    assert gate.proposal.error_attributions[0].validity_scope == "grader_interpretation"
    assert gate.assessed_shortfall is False
    # A dispute about a written step is machine-resident: no question.
    assert gate.clarification is None
    assert gate.proposal.manual_review_recommended is True


def test_a_question_only_when_the_dispute_turns_on_the_learners_meaning():
    proposal = _proposal({"setup": 2.0, "result": 0.0}, [_attribution("result", "x squared is positive")])
    learner = apply_proof_route_gate(
        proposal, rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check("Is x real here?", "ambiguous_notation", result={"verdict": "established"}),
    )
    assert learner.clarification == {
        "question_md": "Is x real here?", "reason": "ambiguous_notation",
        "criterion_id": "result", "trigger": CLARIFICATION_TRIGGER,
    }
    machine = apply_proof_route_gate(
        proposal, rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check("Is the step valid?", "not_learner_resident", result={"verdict": "established"}),
    )
    assert machine.clarification is None
    answered = apply_proof_route_gate(
        proposal, rubric=RUBRIC, learner_answer_md=ANSWER, clarification_allowed=False,
        check=_check("Is x real here?", "ambiguous_notation", result={"verdict": "established"}),
    )
    assert answered.clarification is None and answered.unverified == ("result",)


def test_an_accepted_step_the_check_refutes_verbatim_is_flagged_never_silently():
    gate = apply_proof_route_gate(
        _proposal({"setup": 2.0, "result": 2.0}), rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(result={"verdict": "not_established", "invalid_step_quote": "x  squared is POSITIVE",
                             "error_kind": "false_claim", "reason_md": "zero squared is zero"}),
    )
    assert gate.flagged == ("result",)
    rows = {row.criterion_id: row for row in gate.proposal.criterion_evidence}
    assert rows["result"].points_awarded == 2.0  # the grade stands
    assert "x  squared is POSITIVE" in rows["result"].notes and "reviewed" in rows["result"].notes
    assert gate.proposal.manual_review_recommended is True
    # Without a verbatim quote the disagreement is recorded, not flagged.
    unlocated = apply_proof_route_gate(
        _proposal({"setup": 2.0, "result": 2.0}), rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(result={"verdict": "not_established", "invalid_step_quote": "not in the answer"}),
    )
    assert unlocated.flagged == () and unlocated.outcomes["result"] == "questioned_unlocated"
    assert not unlocated.applied


def test_off_a_divergent_route_agreement_and_cannot_tell_leave_the_grade_as_the_grader_gave_it():
    """The grader did not read the route as divergent (P1's trigger), so an
    abstention keeps its mark-down (review F1 scopes the located-error rule)."""

    proposal = _proposal({"setup": 0.0, "result": 2.0}, [_attribution("setup", "Let x be fixed")])
    gate = apply_proof_route_gate(
        proposal, rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "not_established"}, result={"verdict": "cannot_tell"}),
    )
    assert not gate.applied
    assert gate.proposal.criterion_evidence == proposal.criterion_evidence
    assert gate.outcomes == {"setup": "agree_shortfall", "result": "cannot_tell"}
    unlocated = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 2.0}), rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "cannot_tell"}),
    )
    assert not unlocated.applied and unlocated.assessed_shortfall is True


# -- review F1: P1's located-error rule on a divergent route ------------------------------


@pytest.mark.parametrize("setup_verdict", [
    {"verdict": "cannot_tell"},
    {"verdict": "not_established"},
    {"verdict": "not_established", "invalid_step_quote": "a step the learner never wrote"},
])
def test_p1_an_unlocated_mark_down_on_a_divergent_route_is_unassessed(setup_verdict):
    """The grader marks ``setup`` down without locating an error; the check
    abstains or refutes it without a verbatim quote. On a divergent route whose
    conclusion is not shown to differ, that is not negative evidence."""

    gate = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 2.0}), rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(setup=setup_verdict, result={"verdict": "established"}),
        final_answer_status="undecidable", divergent_route=True, checker_model="m2",
    )
    assert gate.unlocated == ("setup",) and gate.unverified == ("setup",)
    assert gate.outcomes["setup"] == "unlocated" and gate.applied
    assert gate.assessed_shortfall is False and gate.held_for_review is False
    rows = {row.criterion_id: row for row in gate.proposal.criterion_evidence}
    assert rows["setup"].points_awarded == 0.0  # unassessed, not restored
    assert "Not assessed" in rows["setup"].notes and "m2" in rows["setup"].notes


def test_p1_a_located_error_still_counts_from_either_judge():
    grader_located = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 2.0}, [_attribution("setup", "Let x be fixed")]),
        rubric=RUBRIC, learner_answer_md=ANSWER, check=_check(setup={"verdict": "cannot_tell"}),
        final_answer_status="undecidable", divergent_route=True,
    )
    assert grader_located.unverified == () and grader_located.assessed_shortfall is True
    assert grader_located.outcomes["setup"] == "cannot_tell" and not grader_located.applied
    checker_located = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 2.0}), rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "not_established", "invalid_step_quote": "let X be FIXED"}),
        final_answer_status="no_conclusion", divergent_route=True,
    )
    assert checker_located.unverified == () and checker_located.assessed_shortfall is True
    assert checker_located.outcomes["setup"] == "agree_shortfall"


def test_p1_applies_only_to_a_divergent_route_without_fatal_errors():
    for kwargs, fatal in (({"divergent_route": False, "final_answer_status": "undecidable"}, ()),
                          ({"divergent_route": True, "final_answer_status": "undecidable"}, ("wrong_statement",))):
        rubric = Rubric.model_validate({
            **RUBRIC.model_dump(mode="json"),
            "fatal_errors": [{"id": "wrong_statement", "description": "proves the wrong claim", "max_grade": 0}],
        })
        gate = apply_proof_route_gate(
            _proposal({"setup": 0.0, "result": 2.0}, fatal=fatal), rubric=rubric, learner_answer_md=ANSWER,
            check=_check(setup={"verdict": "cannot_tell"}), **kwargs,
        )
        assert gate.unverified == () and gate.assessed_shortfall is True and not gate.applied


def test_p1_nothing_assessed_and_nothing_validated_is_held_for_review():
    gate = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 0.0}), rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "cannot_tell"}, result={"verdict": "not_established"}),
        final_answer_status="no_conclusion", divergent_route=True,
    )
    assert gate.unlocated == ("setup", "result") and gate.held_for_review is True
    assert gate.proposal.manual_review_recommended is True
    assert all("Held for review" in row.notes for row in gate.proposal.criterion_evidence)
    # One criterion the check validates is not "nothing validated".
    validated = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 0.0}, [_attribution("result", "x squared is positive")]),
        rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "cannot_tell"}, result={"verdict": "established"}),
        final_answer_status="no_conclusion", divergent_route=True,
    )
    assert validated.unverified == ("result", "setup") and validated.held_for_review is False


def _whole_answer(quote=None):
    """An attribution naming no criterion (a whole-answer finding)."""

    return BlindErrorAttribution(
        error_type="conceptual_slip", evidence="the route does not prove the claim",
        target_evidence_families=["svd"], validity_scope="valid_measurement",
        first_divergence=(
            {"anchor_kind": "whole_answer", "criterion_id": "", "quote": quote} if quote else None
        ),
    )


def test_p1_an_unlocated_whole_answer_attribution_is_the_graders_interpretation():
    """Re-review F1: an attribution that names no criterion and locates no
    step never preserves a measured failure on its own, once the gate has
    left the mark-downs unassessed (PF-c rescopes it the same way)."""

    gate = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 0.0}, [_whole_answer()]), rubric=RUBRIC,
        learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "cannot_tell"}, result={"verdict": "not_established"}),
        final_answer_status="undecidable", divergent_route=True,
    )
    assert gate.unverified == ("result", "setup")
    assert [row.validity_scope for row in gate.proposal.error_attributions] == ["grader_interpretation"]
    assert gate.assessed_shortfall is False
    # A whole-answer error the grader located verbatim still counts.
    located = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 0.0}, [_whole_answer("x squared is positive")]),
        rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "cannot_tell"}, result={"verdict": "not_established"}),
        final_answer_status="undecidable", divergent_route=True,
    )
    assert [row.validity_scope for row in located.proposal.error_attributions] == ["valid_measurement"]
    assert located.assessed_shortfall is True
    # A restore refutes the grader's unlocated mark-down; an unlocated
    # whole-answer claim does not keep the full grade a measured failure.
    restored = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 2.0}, [_whole_answer()]), rubric=RUBRIC,
        learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "established"}, result={"verdict": "established"}),
    )
    assert restored.restored == ("setup",) and restored.assessed_shortfall is False
    assert [row.validity_scope for row in restored.proposal.error_attributions] == ["grader_interpretation"]
    # Where the gate changes nothing, the grader's attribution is untouched.
    untouched = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 2.0}, [_whole_answer()]), rubric=RUBRIC,
        learner_answer_md=ANSWER, check=_check(setup={"verdict": "not_established"}),
    )
    assert not untouched.applied and untouched.assessed_shortfall is True
    assert [row.validity_scope for row in untouched.proposal.error_attributions] == ["valid_measurement"]


def test_an_unvalidated_grade_with_nothing_assessed_is_not_credited():
    """Re-review F9: with no criterion assessed, the assessed fraction is 1
    only on a verified answer (PF-c). Unvalidated, the grade is the grader's
    own, provisional and held for review: no credit the answer never earned."""

    from learnloop.attempts.attempts import assessed_rubric_score

    points = {"setup": 0.0, "result": 1.0}
    every = ("setup", "result")
    assert assessed_rubric_score(RUBRIC, points, [], unassessed_criterion_ids=every) == 4
    assert assessed_rubric_score(
        RUBRIC, points, [], unassessed_criterion_ids=every, answer_validated=False,
    ) == 1
    # With something assessed the flag changes nothing.
    assert assessed_rubric_score(
        RUBRIC, points, [], unassessed_criterion_ids=("setup",), answer_validated=False,
    ) == assessed_rubric_score(RUBRIC, points, [], unassessed_criterion_ids=("setup",)) == 2


# -- review F2: the machine check outranks the checker -------------------------------------


def test_a_conclusion_that_differs_from_the_reference_is_never_restored_or_unassessed():
    restorable = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 0.0}, [_attribution("result", "x squared is positive")]),
        rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "established"}, result={"verdict": "established"},
                     question="Is x real?", reason="ambiguous_notation"),
        final_answer_status="differs_from_reference", divergent_route=True,
    )
    assert restorable.restored == () and restorable.disputed == () and restorable.unverified == ()
    assert restorable.outcomes == {"setup": "answer_differs", "result": "answer_differs"}
    assert restorable.clarification is None and not restorable.applied
    assert restorable.assessed_shortfall is True
    assert [row.points_awarded for row in restorable.proposal.criterion_evidence] == [0.0, 0.0]
    assert restorable.agreement == {"setup": "disagree", "result": "disagree"}
    unlocated = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 2.0}), rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "cannot_tell"}),
        final_answer_status="differs_from_reference", divergent_route=True,
    )
    assert unlocated.unverified == () and unlocated.assessed_shortfall is True
    # A flag never changes the grade, so it still stands.
    flagged = apply_proof_route_gate(
        _proposal({"setup": 2.0, "result": 2.0}), rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(result={"verdict": "not_established", "invalid_step_quote": "x squared is positive"}),
        final_answer_status="differs_from_reference", divergent_route=True,
    )
    assert flagged.flagged == ("result",)


def test_a_grade_with_fatal_errors_is_never_restored_and_a_dispute_is_flagged():
    rubric = Rubric.model_validate({
        **RUBRIC.model_dump(mode="json"),
        "fatal_errors": [{"id": "wrong_statement", "description": "proves the wrong claim", "max_grade": 0}],
    })
    gate = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 0.0}, fatal=["wrong_statement"]), rubric=rubric,
        learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "established"}, result={"verdict": "established"}),
    )
    assert gate.restored == () and gate.disputed_fatal is True and gate.assessed_shortfall is True


def test_attributions_on_restored_criteria_leave_the_grade_and_stay_on_the_record():
    gate = apply_proof_route_gate(
        _proposal({"setup": 0.0, "result": 2.0}, [_attribution("setup", "not a quote from the answer")]),
        rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(setup={"verdict": "established"}),
    )
    assert gate.restored == ("setup",)
    assert gate.proposal.error_attributions == []
    assert gate.withdrawn_attributions[0]["target_criterion_ids"] == ["setup"]


def test_the_reading_decides_which_items_are_checked():
    """The LLM's reading, not a word list: any kind whose rubric credits the
    learner's reasoning is checked (a computation crediting the working
    included); recall and labelling never are."""

    def reading(kind, graded):
        return ItemKindReading(response_kind=kind, reasoning_is_graded=graded)

    assert reading("proof", True).proof_like and reading("computation", True).proof_like
    assert not reading("proof", False).proof_like
    assert not reading("recall", True).proof_like and not reading("classification", True).proof_like


def test_prompts_withhold_the_reference_and_the_grade():
    from learnloop.vault.models import PracticeItem

    item = PracticeItem.model_validate({
        "id": "i", "learning_object_id": "lo", "practice_mode": "constructed_response",
        "prompt": "Prove that x^2 >= 0.", "expected_answer": "SECRET REFERENCE",
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
    })
    kind = item_kind_prompt(item, RUBRIC)
    check = route_check_prompt(item, RUBRIC, ANSWER)
    assert "SECRET REFERENCE" not in kind and "SECRET REFERENCE" not in check
    assert ANSWER not in kind and ANSWER in check
    assert "keyword" not in kind  # an LLM reading, not a word list


# -- routes ------------------------------------------------------------------------------------


def _set_route(root, key, value):
    path = root / "learnloop.toml"
    text = path.read_text(encoding="utf-8")
    assert text.count("[ai.routing]\n") == 1
    path.write_text(text.replace("[ai.routing]\n", f'[ai.routing]\n{key} = "{value}"\n', 1), encoding="utf-8")


def test_the_check_runs_on_a_route_with_another_model_where_one_is_configured(tmp_path):
    profiles = (
        '[ai.providers.other]\ntype = "openrouter"\nmodel = "anthropic/claude-haiku-5.5"\n'
        'api_key_env = "OPENROUTER_API_KEY"\n'
    )
    _paths, vault, _repository = split_vault(
        tmp_path / "v", version=VERSION, seed=False,
        config=profiles,
    )
    grader_model = vault.config.ai.providers["codex"].model
    same = proof_check_route(vault, grader_model=grader_model)
    assert same.independent is False and "grading route" in same.reason
    _set_route(vault.root, "diagnosis", "other")
    with_diagnoser = proof_check_route(load_vault(vault.root), grader_model=grader_model)
    assert (with_diagnoser.provider, with_diagnoser.independent) == ("other", True)
    assert with_diagnoser.reason == "ai.routing.diagnosis"


def test_an_explicit_route_wins(tmp_path):
    _paths, vault, _repository = split_vault(
        tmp_path / "v", version=VERSION, seed=False,
        config=('[ai.providers.judge]\ntype = "openrouter"\nmodel = "openai/gpt-6-luna"\n'
                'api_key_env = "OPENROUTER_API_KEY"\n'),
    )
    _set_route(vault.root, "proof_check", "judge")
    route = proof_check_route(load_vault(vault.root), grader_model="gpt-5.6-sol")
    assert (route.provider, route.model, route.independent) == ("judge", "openai/gpt-6-luna", True)


# -- live grades -----------------------------------------------------------------------------


def test_a_validated_alternative_route_is_restored_live(tmp_path, checker):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    fake = checker(CheckerFake(verdicts={
        "setup": {"verdict": "established", "reason_md": "V from A^T A is valid"},
        "result": {"verdict": "established"},
    }))
    result = submit(vault, repository, LocatedGrader(), answer=ALTERNATIVE)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    support = _support(repository, result.attempt_id)
    proof = support["proof_route_check"]
    assert proof["status"] == "checked" and proof["applied"] is True
    assert proof["restored_criterion_ids"] == ["setup"]
    assert proof["unverified_criterion_ids"] == ["result"]  # the grader located "Take the eigenvectors"
    assert proof["checker"]["model"] == "checker-model" and proof["checker"]["independent"] is True
    assert proof["item_kind"]["proof_like"] is True
    # setup restored (2/2); result unassessed: the grade is over setup alone.
    assert (attempt["rubric_score"], attempt["correctness"]) == (4, 1.0)
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert rows["setup"].points_awarded == 2.0 and rows["setup"].evidence.startswith("Restored: an independent check")
    assert unassessed_evidence_row(rows["result"].attribution_json)
    assert support["unverified_criterion_ids"] == ["result"]
    assert support["valid_alternative_gate"] == {"final_answer": False, "proof_route": True}
    assert support["assessed_shortfall"] is False
    assert attempt["manual_review_reason"] == UNVERIFIED_REVIEW_REASON
    assert diagnosis_status(repository, result.attempt_id)["status"] == "not_needed"
    # Agreement and disagreement go to judgment_ledger, with the item reading.
    [kind] = _judgments(repository, ITEM_KIND_TASK)
    assert kind["left_id"] == ITEM and json.loads(kind["verdict"])["proof_like"] is True
    [verdict] = _judgments(repository, ROUTE_CHECK_TASK)
    assert verdict["left_id"] == result.attempt_id and verdict["judge_model"] == "checker-model"
    assert json.loads(verdict["verdict"])["agreement"]["disagree"] == 2
    assert fake.calls == ["proof_item_classification", "proof_route_check"]


class DivergentUnlocatedGrader(ReviewFakeClient):
    """The default fake's 0 on every criterion, locating no error, on a route
    it reads as divergent from the reference (``route_check``)."""

    def _blind_grading(self, request, context):
        from learnloop.attempts.grading_support import RouteCheck

        result = super()._blind_grading(request, context)
        update = {"error_attributions": []}
        if hasattr(result, "route_check"):
            update["route_check"] = RouteCheck(divergent_route=True, rederivation_md="re-derived")
        return result.model_copy(update=update)


def test_p1_live_an_unlocated_mark_down_on_a_divergent_route_is_unassessed(tmp_path, checker):
    """Review F1 through the live door: ``setup`` validated (restored),
    ``result`` marked down with nothing located by either judge (unassessed)."""

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    checker(CheckerFake(verdicts={"setup": {"verdict": "established"}, "result": {"verdict": "cannot_tell"}}))
    result = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    proof = _support(repository, result.attempt_id)["proof_route_check"]
    assert proof["divergent_route"] is True and proof["final_answer_status"] == "undecidable"
    assert proof["restored_criterion_ids"] == ["setup"] and proof["unlocated_criterion_ids"] == ["result"]
    # Graded over setup alone (2/2): the unlocated shortfall is no evidence.
    assert (attempt["rubric_score"], attempt["correctness"]) == (4, 1.0)
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert unassessed_evidence_row(rows["result"].attribution_json)
    assert attempt["manual_review_reason"] == UNVERIFIED_REVIEW_REASON
    assert diagnosis_status(repository, result.attempt_id)["status"] == "not_needed"


def test_p1_live_nothing_located_and_nothing_validated_is_held_for_review(tmp_path, checker):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    checker(CheckerFake(verdicts={"setup": {"verdict": "cannot_tell"}, "result": {"verdict": "not_established"}}))
    result = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    proof = _support(repository, result.attempt_id)["proof_route_check"]
    assert proof["held_for_review"] is True
    assert sorted(proof["unlocated_criterion_ids"]) == ["result", "setup"]
    assert attempt["manual_review_reason"] == PROOF_ROUTE_REVIEW_REASON and attempt["manual_review"]


class WholeAnswerGrader(DivergentUnlocatedGrader):
    """``DivergentUnlocatedGrader`` plus one whole-answer attribution that
    names no criterion and quotes nothing."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        return result.model_copy(update={"error_attributions": [_whole_answer()]})


def test_p1_live_an_unlocated_whole_answer_attribution_queues_no_diagnosis(tmp_path, checker):
    """Re-review F1 through the live door: every criterion ends unassessed and
    the grader's unlocated whole-answer claim no longer keeps the attempt a
    measured failure (no diagnosis; the claim is the grader's interpretation)."""

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    checker(CheckerFake(verdicts={"setup": {"verdict": "cannot_tell"}, "result": {"verdict": "not_established"}}))
    result = submit(vault, repository, WholeAnswerGrader(), answer=ALTERNATIVE)
    support = _support(repository, result.attempt_id)
    assert sorted(support["proof_route_check"]["unlocated_criterion_ids"]) == ["result", "setup"]
    assert support["assessed_shortfall"] is False
    assert diagnosis_status(repository, result.attempt_id)["status"] == "not_needed"
    [attribution] = repository.latest_blind_grade_record(result.attempt_id)["record"]["error_attributions"]
    assert attribution["validity_scope"] == "grader_interpretation"


def _schedule(repository):
    state = repository.practice_item_state(ITEM)
    return (state.difficulty, state.stability, state.due_at)


def _first_scheduled_attempt(vault, repository, checker):
    """A validated attempt (both criteria restored: 4/4) that schedules the
    item, rebuilt once so the baseline schedule is replay's (a rebuild of the
    seeded vault alone moves this item's due date by minutes)."""

    checker(CheckerFake(verdicts={"setup": {"verdict": "established"}, "result": {"verdict": "established"}}))
    first = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE, when=CLOCK.now())
    assert repository.fetch_practice_attempt(first.attempt_id)["rubric_score"] == 4
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    return first


def test_f9_a_held_grade_is_not_credited_and_leaves_the_schedule_as_it_was(tmp_path, checker):
    """Re-review F9: nothing assessed and nothing validated is not a verified
    answer. The grade is the grader's own (provisional, held for review), and
    the item's FSRS memory and due date stay as they were until a regrade or
    an adjudication settles it; the held grade is no prediction error either."""

    from datetime import timedelta

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _first_scheduled_attempt(vault, repository, checker)
    before = _schedule(repository)
    checker(CheckerFake(verdicts={"setup": {"verdict": "cannot_tell"}, "result": {"verdict": "not_established"}}))
    held = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (again)",
                  when=CLOCK.now() + timedelta(days=3))
    attempt = repository.fetch_practice_attempt(held.attempt_id)
    assert _support(repository, held.attempt_id)["proof_route_check"]["held_for_review"] is True
    # The grader's own 0/4, never the verified-answer 4/4.
    assert (attempt["rubric_score"], attempt["correctness"]) == (0, 0.0)
    assert attempt["manual_review_reason"] == PROOF_ROUTE_REVIEW_REASON
    assert _schedule(repository) == before
    assert held.surprise_direction == "none"
    surprise = repository.latest_attempt_surprise(held.attempt_id)
    assert surprise["surprise_direction"] == "none"
    # Follow-up work is scheduling too: its insertion is withheld, typed.
    assert any(action.endswith(":grade_held_for_review") for action in surprise["suppressed_actions"])
    # Nothing assessed: no evidence, no diagnosis, no follow-up inserted.
    rows = repository.fetch_grading_evidence(held.attempt_id)
    assert rows and all(unassessed_evidence_row(row.attribution_json) for row in rows)
    assert diagnosis_status(repository, held.attempt_id)["status"] == "not_needed"
    # Replay reproduces the hold from the record, without a model.
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _schedule(repository) == before
    assert repository.fetch_practice_attempt(held.attempt_id)["rubric_score"] == 0


def test_f9_a_regrade_keeps_a_hold_and_releases_it_once_validated(tmp_path, checker):
    from datetime import timedelta

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _first_scheduled_attempt(vault, repository, checker)
    before = _schedule(repository)
    checker(CheckerFake(verdicts={"setup": {"verdict": "cannot_tell"}, "result": {"verdict": "not_established"}}))
    held = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (again)",
                  when=CLOCK.now() + timedelta(days=3))
    # Still held after a regrade: the grader's grade, the schedule untouched.
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(held.attempt_id),
                    runtime=ReadyRuntime(), client=DivergentUnlocatedGrader(), grading_source="ai",
                    clock=FrozenClock(CLOCK.now() + timedelta(days=4)))
    assert repository.fetch_practice_attempt(held.attempt_id)["rubric_score"] == 0
    assert repository.latest_blind_grade_record(held.attempt_id)["record"]["grading_support"][
        "proof_route_check"]["held_for_review"] is True
    assert _schedule(repository) == before
    # The check validates the route on a later regrade: the hold is released,
    # the grade is credited and the review is applied.
    checker(CheckerFake(verdicts={"setup": {"verdict": "established"}, "result": {"verdict": "established"}}))
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(held.attempt_id),
                    runtime=ReadyRuntime(), client=DivergentUnlocatedGrader(), grading_source="ai",
                    clock=FrozenClock(CLOCK.now() + timedelta(days=5)))
    assert repository.fetch_practice_attempt(held.attempt_id)["rubric_score"] == 4
    assert repository.latest_blind_grade_record(held.attempt_id)["record"]["grading_support"][
        "proof_route_check"]["held_for_review"] is False
    assert _schedule(repository) != before


def test_f9_a_record_from_before_the_hold_replays_as_written():
    from learnloop.attempts.proof_check import is_held_for_review, record_held_for_review

    support = {"proof_route_check": {"status": "checked", "held_for_review": True,
                                     "version": "proof-route-check-v3"}}
    assert is_held_for_review(support)
    assert record_held_for_review({"record": {"grading_support": support}})
    support["proof_route_check"]["version"] = "proof-route-check-v2"
    assert not is_held_for_review(support)
    assert not is_held_for_review({"proof_route_check": {"status": "unavailable", "held_for_review": True}})
    assert not record_held_for_review(None)


def test_f9_an_adjudication_releases_a_hold_on_replay(tmp_path, checker):
    """An owner's adjudication writes assessed evidence over the held grade
    (Ruling A's revision), so the next replay schedules it like any grade."""

    from datetime import timedelta

    from learnloop.attempts.grade_resolution import append_adjudication_evidence_revision

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _first_scheduled_attempt(vault, repository, checker)
    before = _schedule(repository)
    checker(CheckerFake(verdicts={"setup": {"verdict": "cannot_tell"}, "result": {"verdict": "not_established"}}))
    held = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (again)",
                  when=CLOCK.now() + timedelta(days=3))
    assert _schedule(repository) == before
    revision = append_adjudication_evidence_revision(
        repository, attempt_id=held.attempt_id, resolved_fraction=1.0, adjudication_id="adj-f9",
        adjudicator_source="human_owner", rationale="the route is valid", vault=vault,
        clock=FrozenClock(CLOCK.now() + timedelta(days=4)),
    )
    assert revision["status"] == "revised"
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert repository.fetch_practice_attempt(held.attempt_id)["rubric_score"] == 4
    assert _schedule(repository) != before


@pytest.mark.parametrize("config", ["", "[diagnosis]\ngrading_support = false"])
def test_f2_live_the_checker_never_restores_a_wrong_final_answer(tmp_path, checker, config):
    """Review F2: "Name a prime." expects 2; the answer concludes 4. The grader
    gives 0 without locating an error and the checker calls the route valid:
    the deterministic check outranks it (with PF-c's policy on or off)."""

    class Unlocated(ReviewFakeClient):
        def _blind_grading(self, request, context):
            return super()._blind_grading(request, context).model_copy(update={"error_attributions": []})

    _paths, vault, repository = split_vault(tmp_path, version=VERSION, config=config)
    checker(CheckerFake(verdicts={"correctness": {"verdict": "established"}}))
    result = submit(vault, repository, Unlocated(), item_id="pi_unrelated_001",
                    answer="Four is the smallest even square, so the answer is 4.")
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert (attempt["rubric_score"], attempt["correctness"]) == (0, 0.0)
    proof = _support(repository, result.attempt_id)["proof_route_check"]
    assert proof["status"] == "checked" and proof["applied"] is False
    assert proof["final_answer_status"] == "differs_from_reference"
    assert proof["outcomes"] == {"correctness": "answer_differs"}
    assert proof["restored_criterion_ids"] == [] and proof["unverified_criterion_ids"] == []
    rows = repository.fetch_grading_evidence(result.attempt_id)
    assert [row.points_awarded for row in rows] == [0.0]
    assert not unassessed_evidence_row(rows[0].attribution_json)


def test_a_restore_alone_leaves_nothing_to_review(tmp_path, checker):
    class UnlocatedGrader(ReviewFakeClient):
        def _blind_grading(self, request, context):
            result = super()._blind_grading(request, context)
            return result.model_copy(update={"error_attributions": []})

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    checker(CheckerFake(verdicts={"setup": {"verdict": "established"}, "result": {"verdict": "established"}}))
    result = submit(vault, repository, UnlocatedGrader(), answer=ALTERNATIVE)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert (attempt["rubric_score"], attempt["correctness"]) == (4, 1.0)
    assert attempt["manual_review_reason"] is None and not attempt["manual_review"]
    support = _support(repository, result.attempt_id)
    assert support["proof_route_check"]["restored_criterion_ids"] == ["result", "setup"] or sorted(
        support["proof_route_check"]["restored_criterion_ids"]) == ["result", "setup"]
    assert support["unverified_criterion_ids"] == []
    assert diagnosis_status(repository, result.attempt_id)["status"] == "not_needed"


def test_a_dispute_on_the_learners_meaning_asks_one_question(tmp_path, checker):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    checker(CheckerFake(
        verdicts={"setup": {"verdict": "not_established"}, "result": {"verdict": "established"}},
        question="Does Sigma^{-1} mean the pseudo-inverse here?", reason="ambiguous_notation",
    ))
    result = submit(vault, repository, LocatedGrader(), answer=ALTERNATIVE)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["manual_review_reason"] == PROVISIONAL_PENDING_CLARIFICATION
    with repository.connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT * FROM grading_clarifications WHERE attempt_id = ?", (result.attempt_id,))]
    assert len(rows) == 1
    assert rows[0]["trigger"] == CLARIFICATION_TRIGGER and rows[0]["criterion_id"] == "result"
    assert rows[0]["reason"] == "ambiguous_notation"


def test_an_accepted_wrong_step_is_flagged_for_review(tmp_path, checker):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    checker(CheckerFake(verdicts={
        "setup": {"verdict": "established"},
        "result": {"verdict": "not_established", "invalid_step_quote": "U = A V Sigma^{-1}",
                   "error_kind": "unjustified_step", "reason_md": "Sigma may be singular"},
    }))
    result = submit(vault, repository, FullCreditGrader(), answer=ALTERNATIVE)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["rubric_score"] == 4  # never silently changed
    assert attempt["manual_review_reason"] == PROOF_ROUTE_REVIEW_REASON and attempt["manual_review"]
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert "U = A V Sigma^{-1}" in rows["result"].notes
    assert _support(repository, result.attempt_id)["proof_route_check"]["flagged_criterion_ids"] == ["result"]


def test_a_non_proof_item_is_read_once_and_never_checked(tmp_path, checker):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    fake = checker(CheckerFake(kind="computation", reasoning=False))
    first = submit(vault, repository, ReviewFakeClient(), answer=ALTERNATIVE)
    second = submit(vault, repository, ReviewFakeClient(), answer="U Sigma V^T")
    assert fake.calls == ["proof_item_classification"]  # cached per item content
    for attempt_id in (first.attempt_id, second.attempt_id):
        proof = _support(repository, attempt_id)["proof_route_check"]
        assert proof["status"] == "not_proof_like" and proof["applied"] is False
    assert _support(repository, second.attempt_id)["proof_route_check"]["item_kind"]["cached"] is True
    assert _judgments(repository, ROUTE_CHECK_TASK) == []


def test_an_unavailable_checker_leaves_the_graders_grade(tmp_path, checker, monkeypatch):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    monkeypatch.setattr("learnloop.attempts.proof_check.resolve_check_client", lambda vault, route: None)
    result = submit(vault, repository, ReviewFakeClient(), answer=ALTERNATIVE)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["rubric_score"] == 0
    proof = _support(repository, result.attempt_id)["proof_route_check"]
    assert proof["status"] == "unavailable" and proof["applied"] is False
    failing = CheckerFake(fail_purposes=("proof_route_check",))
    checker(failing)
    again = submit(vault, repository, ReviewFakeClient(), answer=ALTERNATIVE + " again")
    proof = _support(repository, again.attempt_id)["proof_route_check"]
    assert proof["status"] == "unavailable" and "AIProviderUnavailable" in proof["error"]
    assert repository.fetch_practice_attempt(again.attempt_id)["rubric_score"] == 0


@pytest.mark.parametrize("setup", ["kill_switch", "predecessor"])
def test_the_kill_switch_and_the_predecessor_grade_exactly_as_mvp016(tmp_path, checker, setup):
    """Off (or below mvp-0.17) nothing is called and the grade is mvp-0.16's."""

    if setup == "kill_switch":
        _paths, vault, repository = split_vault(tmp_path / "a", version=VERSION,
                                                config="[proof_check]\nenabled = false")
    else:
        _paths, vault, repository = split_vault(tmp_path / "a", version="mvp-0.16")
    _paths, baseline, baseline_repository = split_vault(tmp_path / "b", version="mvp-0.16")
    fake = checker(CheckerFake(verdicts={"setup": {"verdict": "established"}, "result": {"verdict": "established"}}))
    result = submit(vault, repository, ReviewFakeClient(), answer=ALTERNATIVE, when=CLOCK.now())
    reference = submit(baseline, baseline_repository, ReviewFakeClient(), answer=ALTERNATIVE, when=CLOCK.now())
    assert fake.calls == []
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    expected = baseline_repository.fetch_practice_attempt(reference.attempt_id)
    for column in ("rubric_score", "correctness", "manual_review_reason", "error_type"):
        assert attempt[column] == expected[column], column
    assert "proof_route_check" not in _support(repository, result.attempt_id)
    rows = [(r.criterion_id, r.points_awarded, r.attribution_json) for r in repository.fetch_grading_evidence(result.attempt_id)]
    ref = [(r.criterion_id, r.points_awarded, r.attribution_json)
           for r in baseline_repository.fetch_grading_evidence(reference.attempt_id)]
    assert rows == ref


# -- review F3: the reading and the check are planned and admitted --------------------------


class AdmissionLog:
    """A command guard that records each admission and may refuse one route."""

    def __init__(self, deny_route=None):
        self.calls, self.deny_route = [], deny_route

    def __call__(self, purpose, prompt, *, route="grading", client=None):
        from contextlib import nullcontext

        from learnloop.ai.spend import SpendLimitExceeded

        self.calls.append((purpose, route, getattr(client, "model", None)))
        if route == self.deny_route:
            raise SpendLimitExceeded(f"{route} refused")
        return nullcontext()


def test_the_reading_and_the_check_are_admitted_on_their_own_route(tmp_path, checker):
    from learnloop.attempts.grading_admission import grading_admission

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    checker(CheckerFake(verdicts={"setup": {"verdict": "established"}, "result": {"verdict": "established"}}))
    log = AdmissionLog()
    with grading_admission(log):
        submit(vault, repository, ReviewFakeClient(), answer=ALTERNATIVE, pipeline=False)
    assert log.calls == [
        ("blind_grading", "grading", None),
        ("proof_item_classification", "proof_check", "checker-model"),
        ("proof_route_check", "proof_check", "checker-model"),
    ]


def test_a_refused_check_stops_the_grade_and_is_never_sent(tmp_path, checker):
    from learnloop.ai.spend import SpendLimitExceeded
    from learnloop.attempts.grading_admission import grading_admission

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    fake = checker(CheckerFake(verdicts={"setup": {"verdict": "established"}}))
    before = {row["id"] for row in repository.list_attempt_history()}
    with grading_admission(AdmissionLog(deny_route="proof_check")), pytest.raises(SpendLimitExceeded):
        submit(vault, repository, ReviewFakeClient(), answer=ALTERNATIVE, pipeline=False)
    assert fake.calls == []
    assert {row["id"] for row in repository.list_attempt_history()} == before


def _cli_attempt(monkeypatch, root, client, *args):
    from typer.testing import CliRunner

    import learnloop.cli as cli_module
    from learnloop.cli.app import app

    monkeypatch.setattr(cli_module, "_ready_provider_for_task", lambda *_a, **_k: ("fake", ReadyRuntime(), client))
    return CliRunner().invoke(app, [
        "attempt", ITEM, *args, "--criterion-points", "setup=0,result=0", "--json", "--no-diagnose",
        "--vault", str(root),
    ])


METERED_JUDGE = (
    '[ai.providers.judge]\ntype = "openrouter"\nmodel = "openai/gpt-6-luna"\n'
    'api_key_env = "OPENROUTER_API_KEY"\n'
)


def test_cli_dry_run_plans_the_route_check_with_the_grade(tmp_path, monkeypatch, checker):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    fake = checker(CheckerFake())
    result = _cli_attempt(monkeypatch, vault.root, ReviewFakeClient(), "--answer", ALTERNATIVE, "--dry-run")
    assert result.exit_code == 0, result.output
    grading = json.loads(result.output)["grading"]
    assert grading["calls"] == 1 and grading["admissible"] is True
    proof = grading["proof_check"]
    assert proof["calls"] == 2 and proof["estimated_input_tokens"] > 100  # read + check (upper bound)
    assert proof["route"]["billing"] == "subscription"
    assert grading["total_estimate"]["calls"] == 3
    assert fake.calls == []
    # The caps cover the grade and the check together.
    capped = _cli_attempt(monkeypatch, vault.root, ReviewFakeClient(), "--answer", ALTERNATIVE, "--dry-run",
                          "--max-calls", "2")
    assert capped.exit_code == 1 and "calls exceeds max_calls" in json.loads(capped.output)["grading"]["reason"]
    # A metered checker route with no price is not admissible, and says so.
    _set_route(vault.root, "proof_check", "judge")
    (vault.root / "learnloop.toml").write_text(
        (vault.root / "learnloop.toml").read_text(encoding="utf-8") + "\n" + METERED_JUDGE, encoding="utf-8")
    metered = _cli_attempt(monkeypatch, vault.root, ReviewFakeClient(), "--answer", ALTERNATIVE, "--dry-run")
    assert metered.exit_code == 1, metered.output
    plan = json.loads(metered.output)["grading"]
    assert plan["proof_check"]["route"]["billing"] == "metered" and plan["admissible"] is False
    assert "price" in plan["reason"].lower()


def _metered_vault(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION, config=METERED_JUDGE)
    _set_route(vault.root, "proof_check", "judge")
    return load_vault(vault.root), repository


def test_cli_a_metered_check_without_a_price_is_refused_before_any_call(tmp_path, monkeypatch, checker):
    vault, repository = _metered_vault(tmp_path)
    fake = checker(CheckerFake(provider_type="openai_compatible", model="openai/gpt-6-luna"))
    grader = ReviewFakeClient()  # the subscription grader
    before = {row["id"] for row in repository.list_attempt_history()}
    result = _cli_attempt(monkeypatch, vault.root, grader, "--answer", ALTERNATIVE)
    assert result.exit_code == 1, result.output
    assert json.loads(result.output)["status"] == "over_budget"
    assert grader.calls == [] and fake.calls == []  # nothing was sent, not even the grade
    assert {row["id"] for row in repository.list_attempt_history()} == before


def test_cli_admits_and_meters_the_check_on_its_route(tmp_path, monkeypatch, checker):
    vault, repository = _metered_vault(tmp_path)
    fake = checker(CheckerFake(
        provider_type="openai_compatible", model="openai/gpt-6-luna",
        verdicts={"setup": {"verdict": "established"}, "result": {"verdict": "established"}},
    ))
    result = _cli_attempt(monkeypatch, vault.root, ReviewFakeClient(), "--answer", ALTERNATIVE,
                          "--price-per-million", "2.0")
    assert result.exit_code == 0, result.output
    spend = json.loads(result.output)["spend"]
    assert fake.calls == ["proof_item_classification", "proof_route_check"]
    assert spend["charged"]["calls"] == 3  # the grade and both check calls
    route = spend["routes"]["proof_check"]
    assert route["billing"] == "metered" and route["calls"] == 2 and route["input_tokens"] > 0
    assert spend["charged"]["metered_total_tokens"] > 0 and spend["charged"]["metered_estimated_usd"] > 0
    assert spend["routes"]["grading"]["billing"] == "subscription"


# -- review F4: a checked grade has its own calibration identity ------------------------------


def _identity(repository, attempt_id):
    record = repository.latest_blind_grade_record(attempt_id)["record"]
    return record["calibration_prompt_version"], repository.latest_raw_grade_identity(attempt_id)[0]


def test_a_checked_grade_is_calibrated_under_its_own_identity(tmp_path, checker):
    from learnloop.attempts.grading_support import REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION as BASE
    from learnloop.attempts.proof_check import PROOF_CHECK_VERSION, ROUTE_CHECK_PROMPT_VERSION

    _paths, vault, repository = split_vault(tmp_path / "v", version=VERSION)
    verdicts = {"setup": {"verdict": "established"}, "result": {"verdict": "established"}}
    checker(CheckerFake(verdicts=verdicts))
    checked = submit(vault, repository, ReviewFakeClient(), answer=ALTERNATIVE)
    expected = f"{BASE}+{PROOF_CHECK_VERSION}:{ROUTE_CHECK_PROMPT_VERSION}@checker-model"
    # The blind record (what replay reads) and the raw grade event agree.
    assert _identity(repository, checked.attempt_id) == (expected, expected)
    # Another checker model is another measurement process.
    checker(CheckerFake(verdicts=verdicts, model="other-checker"))
    other = submit(vault, repository, ReviewFakeClient(), answer=ALTERNATIVE + " (2)")
    assert _identity(repository, other.attempt_id)[0] == expected.replace("checker-model", "other-checker")
    # A grade the grader produced alone keeps the predecessor identity.
    reader = CheckerFake(kind="computation", reasoning=False, model="reader-model")
    _paths, plain_vault, plain_repository = split_vault(tmp_path / "plain", version=VERSION)
    checker(reader)
    plain = submit(plain_vault, plain_repository, ReviewFakeClient(), answer=ALTERNATIVE)
    assert _identity(plain_repository, plain.attempt_id) == (BASE, BASE)
    for setup, kwargs in (("kill_switch", {"version": VERSION, "config": "[proof_check]\nenabled = false"}),
                          ("predecessor", {"version": "mvp-0.16"})):
        _paths, off_vault, off_repository = split_vault(tmp_path / setup, **kwargs)
        checker(CheckerFake(verdicts=verdicts))
        off = submit(off_vault, off_repository, ReviewFakeClient(), answer=ALTERNATIVE)
        assert _identity(off_repository, off.attempt_id) == (BASE, BASE), setup


def test_a_regrade_records_the_identity_of_the_grade_it_produced(tmp_path, checker):
    from learnloop.attempts.attempts import replay_grader_identity
    from learnloop.attempts.grading_support import REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION as BASE

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    checker(None)  # no ready checker: the grader's grade alone, base identity
    result = submit(vault, repository, ReviewFakeClient(), answer=ALTERNATIVE)
    assert _support(repository, result.attempt_id)["proof_route_check"]["status"] == "unavailable"
    assert _identity(repository, result.attempt_id) == (BASE, BASE)
    # The checker is back; the regrade is checked and says so.
    checker(CheckerFake(verdicts={"setup": {"verdict": "established"}, "result": {"verdict": "established"}}))
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=ReviewFakeClient(),
                    grading_source="ai", clock=CLOCK)
    record_identity, raw_identity = _identity(repository, result.attempt_id)
    assert record_identity.startswith(BASE + "+proof-route-check-") and raw_identity == record_identity
    blind = repository.latest_blind_grade_record(result.attempt_id)
    assert replay_grader_identity(repository, result.attempt_id, blind)[0] == record_identity


# -- regrade and replay ------------------------------------------------------------------------


def test_a_regrade_checks_again_and_supersedes_the_verdict(tmp_path, checker):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    checker(CheckerFake(verdicts={"setup": {"verdict": "established"}, "result": {"verdict": "established"}}))
    result = submit(vault, repository, ReviewFakeClient(), answer=ALTERNATIVE)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    regrade_attempt(vault, repository, attempt, runtime=ReadyRuntime(), client=ReviewFakeClient(),
                    grading_source="ai", clock=CLOCK)
    verdicts = _judgments(repository, ROUTE_CHECK_TASK)
    assert len(verdicts) == 2 and verdicts[1]["supersedes_id"] == verdicts[0]["id"]
    regraded = repository.fetch_practice_attempt(result.attempt_id)
    assert (regraded["rubric_score"], regraded["correctness"]) == (4, 1.0)
    record = repository.latest_blind_grade_record(result.attempt_id)["record"]
    assert record["regrade"] is True
    assert record["grading_support"]["proof_route_check"]["restored_criterion_ids"] == ["setup"]
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert rows["setup"].points_awarded == 2.0
    assert unassessed_evidence_row(rows["result"].attribution_json)


def _projection(repository):
    return sorted(
        (cell.facet_id, cell.capability, round(cell.direct_positive_mass, 12),
         round(cell.direct_negative_mass, 12), round(cell.certification_credit, 12))
        for cell in repository.facet_capability_evidence_all()
    )


def test_replay_reproduces_route_checked_grades_without_a_model(tmp_path, checker, monkeypatch):
    """Same-version rebuild equivalence: replay reads the records as written
    and never calls the checker (playbook item 6)."""

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    checker(CheckerFake(verdicts={"setup": {"verdict": "established"}, "result": {"verdict": "established"}}))
    submit(vault, repository, ReviewFakeClient(), answer=ALTERNATIVE)
    flagged = CheckerFake(verdicts={"result": {"verdict": "not_established",
                                               "invalid_step_quote": "U = A V Sigma^{-1}"}})
    checker(flagged)
    submit(vault, repository, FullCreditGrader(), answer=ALTERNATIVE + " (second)")
    project_canonical_facet_state(vault, repository)
    before = _projection(repository)
    monkeypatch.setattr(
        "learnloop.attempts.proof_check.resolve_check_client",
        lambda vault, route: pytest.fail("replay must not call the checker"),
    )
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    first = _projection(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert first == _projection(repository) == before


# -- the migration -------------------------------------------------------------------------------


def test_migration_186_widens_the_trigger_and_keeps_every_clarification(tmp_path):
    from learnloop.db.copies import copy_tree_with_databases
    from learnloop.db.migrate import discover_migrations

    head = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_186"
    root = tmp_path / "head"
    copy_tree_with_databases(head, root)
    assert max(m.version for m in discover_migrations()) == 186
    with connect(root / "state.sqlite") as connection:
        sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'grading_clarifications'").fetchone()[0]
        assert "'route_check_disagreement'" in sql
        triggers = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'grading_clarifications'")}
        assert triggers == {"grading_clarifications_no_update"}
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_pf_c_outcomes_alone_are_not_this_gates():
    """A criterion PF-c already recorded unverified, which the check neither
    validates nor disputes, stays unverified, and this gate did not apply."""

    gate = apply_proof_route_gate(
        _proposal({"setup": 2.0, "result": 0.0}), rubric=RUBRIC, learner_answer_md=ANSWER,
        check=_check(result={"verdict": "not_established"}), unverified_before=["result"],
    )
    assert gate.unverified == ("result",) and gate.disputed == () and not gate.applied
