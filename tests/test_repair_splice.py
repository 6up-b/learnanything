"""Deterministic repair splice: derived prefix, end-append separator, replay.

The exhibit these tests are cut from is a real graded exam answer
(``pi_what_makes_log_transport_strategy``): a 78-character answer whose
``preserve_refs`` quote covered only its first 40 characters, but whose
``learner_work_prefix`` claimed the whole thing — hedge included — and whose
end-append repair was then pasted straight onto the end of that hedge.
"""

from __future__ import annotations

from typing import Any

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.schemas import GradingProposal
from learnloop.services.grading import validate_codex_grading_proposal
from learnloop.services.repair_splice import (
    clause_boundaries,
    is_end_append,
    preserved_prefix_from_refs,
    snap_prefix_end,
    splice_repaired_answer,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_repair_splice_001"

# The live exhibit, verbatim.
ANSWER = "I know we need a transformation function but I'm not sure what to do from here"
PRESERVE_QUOTE = "I know we need a transformation function"
REGENERATED = (
    " Take L(x)=log x. Then L(x+y)=log(xy)=log x+log y=L(x)+L(y), so commutativity "
    "and associativity are inherited from ordinary addition."
)


def _item_payload() -> dict[str, Any]:
    return {
        "id": ITEM_ID,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": ["definition_recall"],
        "evidence_weights": {"definition_recall": 1.0},
        "prompt": "What makes the log transport strategy work?",
        "expected_answer": "Take L(x)=log x and check both transport identities.",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correct", "points": 4, "description": "Correct."}],
            "fatal_errors": [],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


@pytest.fixture()
def item(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    upsert_practice_item(vault_root, _item_payload(), clock=FrozenClock(NOW))
    vault = load_vault(vault_root)
    return vault, vault.practice_items[ITEM_ID]


def _proposal(
    *,
    learner_work_prefix: str,
    preserve_refs: list[dict[str, Any]] | None = None,
    insertion: dict[str, Any] | None = None,
    regenerated: str = REGENERATED,
    repaired_answer_md: str | None = None,
) -> GradingProposal:
    trace: dict[str, Any] = {
        "learner_work_prefix": learner_work_prefix,
        "minimal_edit": "Append the choice L(x)=log x and the transport identities.",
        "regenerated_work": regenerated,
        "repaired_answer_md": (
            repaired_answer_md
            if repaired_answer_md is not None
            else learner_work_prefix + regenerated
        ),
        "changed_latent_claims": ["The useful transformation is the logarithm."],
        "changed_checkpoint_ids": [],
    }
    if insertion is not None:
        trace["repair_insertion_point"] = insertion
    suggestion: dict[str, Any] = {
        "practice_mode": "guided_completion",
        "rationale": "Complete the method the learner already recognized.",
        "operator": "complete_log_transport",
        "repaired_trace": trace,
    }
    if preserve_refs is not None:
        suggestion["preserve_refs"] = preserve_refs
    return GradingProposal.model_validate(
        {
            "attempt_id": "att_repair_splice",
            "practice_item_id": ITEM_ID,
            "rubric_score": 1,
            "criterion_evidence": [],
            "fatal_errors": [],
            "error_attributions": [],
            "repair_suggestions": [suggestion],
            "grader_confidence": 0.9,
        }
    )


def _validate(vault, item, proposal, answer: str = ANSWER):
    return validate_codex_grading_proposal(
        proposal,
        attempt_id="att_repair_splice",
        item=item,
        vault=vault,
        learner_answer_md=answer,
    )


END_APPEND = {
    "anchor_kind": "missing_required_step",
    "criterion_id": "correct",
    "checkpoint_id": "select_logarithm",
}
ANSWER_SPAN_REF = {
    "kind": "answer_span",
    "quote": PRESERVE_QUOTE,
    "char_start": 0,
    "char_end": 40,
}


# ── Pure derivation ──────────────────────────────────────────────────────────


def test_preserve_span_snaps_to_the_clause_not_the_whole_answer():
    derived = preserved_prefix_from_refs(ANSWER, [ANSWER_SPAN_REF])
    assert derived is not None
    assert derived.text == PRESERVE_QUOTE
    assert (derived.declared_end, derived.snapped_end) == (40, 40)
    assert derived.basis == "derived_from_preserve_refs"


def test_span_ending_mid_clause_snaps_outward_to_the_clause_end():
    answer = "The determinant is zero, so the matrix is singular."
    # Span stops mid-clause on "determinant".
    derived = preserved_prefix_from_refs(
        answer,
        [{"kind": "answer_span", "quote": "The determinant", "char_start": 0, "char_end": 15}],
    )
    assert derived is not None
    assert derived.text == "The determinant is zero,"


def test_boundaries_never_fall_inside_a_token():
    answer = "The value is 3.5 and the count is 1,000 which settles it."
    for boundary in clause_boundaries(answer):
        assert boundary == len(answer) or answer[boundary].isspace()
    # No boundary splits "3.5" or "1,000".
    assert 15 not in clause_boundaries(answer)
    assert 36 not in clause_boundaries(answer)


def test_snap_falls_back_to_end_of_text_when_no_boundary_follows():
    answer = "I know we need something"
    assert snap_prefix_end(answer, 6) == len(answer)


def test_quote_only_preserve_ref_is_anchored_server_side():
    derived = preserved_prefix_from_refs(
        ANSWER, [{"kind": "answer_span", "quote": PRESERVE_QUOTE}]
    )
    assert derived is not None
    assert derived.text == PRESERVE_QUOTE


def test_non_answer_span_preserve_refs_derive_nothing():
    assert (
        preserved_prefix_from_refs(ANSWER, [{"kind": "criterion", "criterion_id": "correct"}])
        is None
    )


def test_end_append_detection_requires_an_explicit_insertion_point():
    assert is_end_append({}) is False
    assert is_end_append({"repair_insertion_point": END_APPEND}) is True
    assert (
        is_end_append(
            {
                "repair_insertion_point": {
                    "anchor_kind": "span",
                    "criterion_id": "correct",
                    "char_start": 3,
                    "char_end": 9,
                }
            }
        )
        is False
    )


def test_existing_paragraph_break_is_not_doubled():
    spliced = splice_repaired_answer("work\n\n", "the repair", end_append=True)
    assert spliced.repaired_answer_md == "work\n\nthe repair"
    assert spliced.join == "verbatim"


# ── Through the validator ────────────────────────────────────────────────────


def test_derived_prefix_truncates_the_hedge_and_records_an_audit_note(item):
    vault, practice_item = item
    validated = _validate(
        vault,
        practice_item,
        # The exhibit's own bug: the model declared the ENTIRE answer preserved.
        _proposal(
            learner_work_prefix=ANSWER,
            preserve_refs=[ANSWER_SPAN_REF],
            insertion=END_APPEND,
        ),
    )
    trace = validated.repair_suggestions[0]["repaired_trace"]

    assert trace["learner_work_prefix"] == PRESERVE_QUOTE
    assert "not sure what to do from here" not in trace["learner_work_prefix"]
    assert trace["prefix_basis"] == "derived_from_preserve_refs"
    assert trace["model_reported_learner_work_prefix"] == ANSWER
    # Auditable by construction survives the derivation.
    assert (
        trace["repaired_answer_md"]
        == trace["learner_work_prefix"] + trace["regenerated_work"]
    )

    events = [
        event
        for event in validated.attribution_audit_events
        if event.get("event") == "repair_prefix_derived"
    ]
    assert len(events) == 1
    assert events[0]["declared_span_end"] == 40
    assert events[0]["snapped_end"] == 40
    assert events[0]["model_reported_prefix_length"] == len(ANSWER)
    assert events[0]["derived_prefix_length"] == len(PRESERVE_QUOTE)


def test_prefix_disagreement_never_fails_the_grade(item):
    vault, practice_item = item
    # A prefix that is not even verbatim learner work: with preserve_refs the
    # server computes its own and grades on, rather than rejecting.
    validated = _validate(
        vault,
        practice_item,
        _proposal(
            learner_work_prefix="I know we need a TRANSFORMATION FUNCTION",
            preserve_refs=[ANSWER_SPAN_REF],
            insertion=END_APPEND,
        ),
    )
    trace = validated.repair_suggestions[0]["repaired_trace"]
    assert trace["learner_work_prefix"] == PRESERVE_QUOTE
    assert ANSWER.startswith(trace["learner_work_prefix"])


def test_end_append_gets_a_paragraph_break(item):
    vault, practice_item = item
    validated = _validate(
        vault,
        practice_item,
        _proposal(
            learner_work_prefix=ANSWER,
            preserve_refs=[ANSWER_SPAN_REF],
            insertion=END_APPEND,
        ),
    )
    trace = validated.repair_suggestions[0]["repaired_trace"]
    assert trace["repaired_answer_md"] == PRESERVE_QUOTE + "\n\n" + REGENERATED.lstrip()
    assert trace["splice_join"] == "paragraph_break_inserted"
    assert trace["model_reported_regenerated_work"] == REGENERATED
    assert any(
        event.get("event") == "repair_splice_separator_inserted"
        for event in validated.attribution_audit_events
    )


def test_no_preserve_refs_fallback_is_byte_identical(item):
    """Legacy shape: model-reported prefix, mid-work anchor, unchanged bytes."""

    vault, practice_item = item
    mid_work = {
        "anchor_kind": "span",
        "criterion_id": "correct",
        "quote": PRESERVE_QUOTE,
        "char_start": 0,
        "char_end": 40,
    }
    validated = _validate(
        vault,
        practice_item,
        _proposal(learner_work_prefix=ANSWER, insertion=mid_work),
    )
    trace = validated.repair_suggestions[0]["repaired_trace"]
    assert trace["learner_work_prefix"] == ANSWER
    assert trace["repaired_answer_md"] == ANSWER + REGENERATED
    assert trace["prefix_basis"] == "model_reported"
    assert "model_reported_learner_work_prefix" not in trace
    assert trace["splice_join"] == "verbatim"
    assert validated.attribution_audit_events == []


def test_mid_work_splice_with_offsets_is_unchanged(item):
    """Offsets on the anchor mean a real insertion — no separator, no rewrite."""

    vault, practice_item = item
    validated = _validate(
        vault,
        practice_item,
        _proposal(
            learner_work_prefix=PRESERVE_QUOTE,
            preserve_refs=[ANSWER_SPAN_REF],
            insertion={
                "anchor_kind": "span",
                "criterion_id": "correct",
                "quote": PRESERVE_QUOTE,
                "char_start": 0,
                "char_end": 40,
            },
        ),
    )
    trace = validated.repair_suggestions[0]["repaired_trace"]
    assert trace["learner_work_prefix"] == PRESERVE_QUOTE
    assert trace["repaired_answer_md"] == PRESERVE_QUOTE + REGENERATED
    assert trace["splice_join"] == "verbatim"
    # Model and server agreed, so nothing is reported.
    assert "model_reported_learner_work_prefix" not in trace
    assert validated.attribution_audit_events == []


def test_derivation_is_replay_stable(item):
    """Pure function of stored fields: a second pass reproduces it exactly."""

    vault, practice_item = item

    def once():
        validated = _validate(
            vault,
            practice_item,
            _proposal(
                learner_work_prefix=ANSWER,
                preserve_refs=[ANSWER_SPAN_REF],
                insertion=END_APPEND,
            ),
        )
        return validated.repair_suggestions[0]["repaired_trace"]

    assert once() == once()
