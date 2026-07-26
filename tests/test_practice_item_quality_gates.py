"""Item-quality gates on generated practice (selected-response ban, rung ladder).

Generation used to enter every cold Learning Object at a ``response: recognize``
waypoint, which the authoring model renders as multiple choice. For a goal like
"get good at proofs" that produced whole batches of "which outline describes a
coordinate proof? A/B/C — reply with the letter" items: they measure option
elimination rather than the capability the LO names, and because they are
authored easy the learner model already predicts success, so answering them
correctly moves the posterior by almost nothing.
"""

from __future__ import annotations

import pytest

from learnloop.services.depth_rungs import (
    DEFAULT_TRAJECTORY,
    resolve_waypoint_slug,
    trajectory_slugs,
)
from learnloop.services.practice_generation import _SelectedResponseGate


def _row(item_id: str, prompt: str) -> dict:
    return {
        "item_type": "practice_item",
        "operation": "create",
        "client_item_id": item_id,
        "payload": {"prompt": prompt},
    }


# Verbatim surfaces the generator actually shipped into fixtures/linear_algebra.
SELECTED_RESPONSE_PROMPTS = [
    pytest.param(
        "Which outline describes a coordinate proof of a vector identity in F^n? "
        "A. Compare an arbitrary kth coordinate using scalar laws, then conclude all "
        "coordinates agree. B. Draw the vectors and measure their angles. C. Check only "
        "the first coordinate. Reply with the letter.",
        id="lettered_options_reply_with_letter",
    ),
    pytest.param(
        "In the phrase “let u be a vector in V,” what does this assert about u? "
        "A. u is an axiom of V. B. u is an element of the vector space V. C. u must belong "
        "to the scalar field F. Reply with the letter",
        id="definition_recognition",
    ),
    pytest.param(
        "True or false: Naming a set alone is enough to specify a vector space; addition "
        "and scalar multiplication need not be given.",
        id="true_false",
    ),
    pytest.param(
        "Which of the following is the commutative law for vector addition?",
        id="which_of_the_following",
    ),
    pytest.param(
        "Select the correct associative law for vector addition.",
        id="select_the_correct",
    ),
]


@pytest.mark.parametrize("prompt", SELECTED_RESPONSE_PROMPTS)
def test_selected_response_surfaces_are_blocked(prompt):
    gate = _SelectedResponseGate()
    rows = [_row("pi_bad", prompt)]
    gate(rows)

    assert rows[0]["_auto_apply"] is False
    assert rows[0]["validation_status"] == "invalid"
    assert "selected_response_surface" in rows[0]["validation_errors"]
    assert gate.violations and "pi_bad" in gate.violations[0]


@pytest.mark.parametrize(
    "prompt",
    [
        "Prove that x+y=y+x for all x,y in F^n by comparing the kth coordinate.",
        "State the two operations a set must be equipped with to be a vector space.",
        "A proposed addition on V sometimes produces an output outside V. Name the "
        "vector-space requirement this violates and explain why.",
        # "A" as a bare article must not trip the lettered-option pattern.
        "A vector space over F requires closure. Derive closure for F^n.",
    ],
)
def test_constructed_response_surfaces_pass(prompt):
    gate = _SelectedResponseGate()
    rows = [_row("pi_good", prompt)]
    gate(rows)

    assert rows[0].get("_auto_apply") is None
    assert not gate.violations


def test_gate_leaves_other_row_types_alone():
    gate = _SelectedResponseGate()
    rows = [
        {
            "item_type": "learning_object",
            "operation": "create",
            "payload": {"prompt": "Which of the following? A. x B. y"},
        },
        # An update, not a create: the gate only screens newly authored items.
        {
            "item_type": "practice_item",
            "operation": "update",
            "payload": {"prompt": "True or false: this is an update."},
        },
    ]
    gate(rows)

    assert not gate.violations
    assert all(row.get("_auto_apply") is None for row in rows)


def test_default_trajectory_has_no_selected_response_waypoint():
    """No generation target may ask for a picked answer."""

    for waypoint in DEFAULT_TRAJECTORY:
        assert waypoint.features.get("response") != "recognize", (
            f"waypoint {waypoint.slug!r} targets a selected response"
        )


def test_cold_entry_waypoint_is_a_cued_constructed_response():
    entry = DEFAULT_TRAJECTORY[0]

    assert trajectory_slugs()[0] == entry.slug == "recall"
    assert entry.features["response"] == "short_constructed"
    # Low demand comes from the cue, not from supplying candidate answers.
    assert entry.features["scaffolding"] == "cue"


def test_retired_recognize_slug_still_resolves():
    """Stored rung-variant requests written before the waypoint was removed."""

    assert resolve_waypoint_slug("recognize") == "recall"
    assert resolve_waypoint_slug("select_method") == "select_method"


def test_trajectory_is_monotone_and_escalates():
    """A new learner must be able to climb, not sit on low-information items."""

    slugs = trajectory_slugs()
    assert slugs == ("recall", "interpret", "execute", "select_method")
    capabilities = [waypoint.capability for waypoint in DEFAULT_TRAJECTORY]
    assert capabilities == [
        "retrieval",
        "schema_interpretation",
        "procedure_execution",
        "method_selection",
    ]
