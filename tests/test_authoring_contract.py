"""The authoring response-mode / misconception contract (incident 01KYH9F2…).

A tutor-promoted item shipped with an A–D option list and a speculative
``misconception_consistent_answer`` keyed to no registered misconception. Both
defects were introduced by authoring: the prompt ladder recommended a mode the
deterministic gate bans, and nothing required the misconception pair to be
atomic. These tests pin the contract that closes the class:

* one response-mode vocabulary, stated once and interpolated into the prompt;
* ``misconception_consistent_answer`` requires a keyed rubric fatal error,
  as a repairable deterministic validation error;
* the mechanically-fixable gate failures are remediated (information-removing
  only) and re-judged inside the gate chain;
* the edit/refresh door reports the SAME gate errors as the generation door,
  so refreshing an unchanged failing payload can no longer clear it.
"""

from __future__ import annotations

import copy
from pathlib import Path

from learnloop.codex.prompts import (
    BANNED_RESPONSE_MODES,
    LOW_MASTERY_RESPONSE_MODES,
    TUTOR_PROMOTION_PROMPT,
    TUTOR_PROMOTION_PROMPT_VERSION,
)
from learnloop.db.repositories import Repository
from learnloop.services.authoring_gates import (
    GATE_REMEDIATION_AUDIT_KEY,
    SelectedResponseGate,
    build_instrument_gates,
    selected_response_reasons,
)
from learnloop.services.proposals import (
    _edited_payload_validation_errors,
    _instrument_gate_errors,
    _practice_item_metadata_errors,
)
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault

_SURFACE_ERROR = "selected_response_surface"
_DETECTOR_ERROR = "persona_gate: no_keyed_detector"
_ATOMIC_ERROR = "misconception_answer_requires_keyed_fatal_error"

# Scrubbed copy of the failing payload's load-bearing shape (proposal item
# 01KYH9F2WWE6Z5PBGRKGNEMYVY in the owner's vault): lettered options plus a
# trailing choose-instruction in the prompt, a lettered expected answer, a
# banned practice_mode, a populated misconception_consistent_answer, and one
# fatal error with no misconception_id.
_FAILING_PAYLOAD = {
    "id": "pi_tutor_promoted_transported_additive_identity_01",
    "learning_object_id": "lo_alpha",
    "practice_mode": "multiple_choice_with_explanation",
    "prompt": (
        "Let V be a set, let W be a vector space with zero vector 0_W, and let "
        "T:V→W be a bijection. Define addition on V by "
        "u⊕v=T⁻¹(T(u)+T(v)). An additive identity e∈V must "
        "satisfy v⊕e=v for every v∈V. What must T(e) be?\n\n"
        "A. T(e)=T(v)\nB. T(e)=0_W\nC. T(e)=-T(v)\nD. T(e)=T⁻¹(0_W)\n\n"
        "Choose one option and explain why."
    ),
    "expected_answer": "B. T(e)=0_W. Since T is injective, v⊕e=v for every v.",
    "misconception_consistent_answer": (
        "A learner may choose D by confusing e∈V with its image T(e)∈W."
    ),
    "evidence_facets": ["facet_alpha"],
    "evidence_weights": {"facet_alpha": 1.0},
    "grading_rubric": {
        "max_points": 4,
        "criteria": [
            {
                "id": "criterion_identify",
                "points": 4.0,
                "description": "States that T(e)=0_W.",
                "measurement_status": "direct",
            }
        ],
        "fatal_errors": [
            {
                "id": "fatal_use_ordinary_zero_without_transport",
                "description": "Uses an ordinary coordinate zero without applying T⁻¹.",
                "max_grade": 2,
            }
        ],
    },
    "criterion_facet_weights": {"criterion_identify": {"facet_alpha": 1.0}},
    "tags": ["tutor_promoted"],
}


def _row(payload: dict) -> dict:
    return {
        "id": "row1",
        "client_item_id": "item_1",
        "item_type": "practice_item",
        "operation": "create",
        "payload": copy.deepcopy(payload),
        "validation_status": "valid",
        "validation_errors": [],
        "_auto_apply": True,
    }


def _vault_and_repo(tmp_path: Path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    return vault, repository


# ---------------------------------------------------------------------------
# Prompt contract
# ---------------------------------------------------------------------------


def test_prompt_interpolates_the_shared_vocabulary() -> None:
    assert "__LOW_MASTERY_MODES__" not in TUTOR_PROMOTION_PROMPT
    assert "__BANNED_MODES__" not in TUTOR_PROMOTION_PROMPT
    for mode in LOW_MASTERY_RESPONSE_MODES:
        assert f"`{mode}`" in TUTOR_PROMOTION_PROMPT
    # Banned modes appear only inside the ban sentence, never as the ladder's
    # recommendation — the old drift recommended one in the LOW rung.
    ban_sentence = TUTOR_PROMOTION_PROMPT.split("BANNED", 1)[1]
    for mode in BANNED_RESPONSE_MODES:
        assert TUTOR_PROMOTION_PROMPT.count(f"`{mode}`") == ban_sentence.count(f"`{mode}`")
    assert "recognition/structure modes" not in TUTOR_PROMOTION_PROMPT
    assert "registered_misconceptions" in TUTOR_PROMOTION_PROMPT
    assert TUTOR_PROMOTION_PROMPT_VERSION != "mvp-0.1-tutor-promotion"


def test_ladder_and_ban_cannot_overlap() -> None:
    assert not set(BANNED_RESPONSE_MODES) & set(LOW_MASTERY_RESPONSE_MODES)


# ---------------------------------------------------------------------------
# Atomic misconception pair (deterministic validation error, both doors)
# ---------------------------------------------------------------------------


def test_misconception_answer_without_keyed_fatal_error_is_invalid(tmp_path: Path) -> None:
    vault, _ = _vault_and_repo(tmp_path)
    errors = _practice_item_metadata_errors(
        copy.deepcopy(_FAILING_PAYLOAD), vault, None, generated=False
    )
    assert _ATOMIC_ERROR in errors


def test_misconception_answer_with_keyed_fatal_error_is_valid(tmp_path: Path) -> None:
    vault, _ = _vault_and_repo(tmp_path)
    payload = copy.deepcopy(_FAILING_PAYLOAD)
    payload["grading_rubric"]["fatal_errors"][0]["misconception_id"] = "mc_transport_zero"
    errors = _practice_item_metadata_errors(payload, vault, None, generated=False)
    assert _ATOMIC_ERROR not in errors


def test_no_misconception_answer_owes_nothing(tmp_path: Path) -> None:
    vault, _ = _vault_and_repo(tmp_path)
    payload = copy.deepcopy(_FAILING_PAYLOAD)
    payload["misconception_consistent_answer"] = None
    errors = _practice_item_metadata_errors(payload, vault, None, generated=False)
    assert _ATOMIC_ERROR not in errors


# ---------------------------------------------------------------------------
# Mode-declaration ban (second deterministic channel)
# ---------------------------------------------------------------------------


def test_banned_practice_mode_is_a_violation_even_with_a_clean_prompt() -> None:
    payload = {
        "practice_mode": "multiple_choice",
        "prompt": "Explain why the transported identity is T⁻¹(0_W).",
        "expected_answer": "Because T(e) must be 0_W.",
    }
    row = _row(payload)
    gate = SelectedResponseGate()
    gate([row])
    assert row["validation_status"] == "invalid"
    assert _SURFACE_ERROR in row["validation_errors"]


# ---------------------------------------------------------------------------
# Generation door: gate → deterministic remediation → re-judge
# ---------------------------------------------------------------------------


def test_generation_door_remediates_the_incident_payload(tmp_path: Path) -> None:
    vault, repository = _vault_and_repo(tmp_path)
    row = _row(_FAILING_PAYLOAD)
    chain = build_instrument_gates(vault, repository)
    chain([row])

    audit = row["audit"][GATE_REMEDIATION_AUDIT_KEY]
    assert set(audit["cured_errors"]) >= {_SURFACE_ERROR, _DETECTOR_ERROR}

    payload = row["payload"]
    assert "A. T(e)=T(v)" not in payload["prompt"]
    assert "Choose one option" not in payload["prompt"]
    assert "What must T(e) be?" in payload["prompt"]
    assert payload["practice_mode"] == "short_answer"
    assert not payload["expected_answer"].startswith("B.")
    assert payload["misconception_consistent_answer"] is None
    assert selected_response_reasons(payload) == []

    # Mechanically altered content ships to review: never valid, never auto.
    assert row["validation_status"] == "warning"
    assert row["validation_errors"] == []
    assert row["_auto_apply"] is False

    # The pre-remediation verdicts stay visible for the reviewer.
    diagnostics = chain.diagnostics()
    assert any(d["gate"] == "selected_response_surface" for d in diagnostics)
    assert any(d["gate"] == "persona_gate" and d["severity"] == "hard_fail" for d in diagnostics)
    assert audit["pre_remediation"]["practice_mode"] == "multiple_choice_with_explanation"


def test_remediation_bails_when_the_stem_is_the_surface(tmp_path: Path) -> None:
    vault, repository = _vault_and_repo(tmp_path)
    payload = {
        "id": "pi_tf",
        "practice_mode": "short_answer",
        "prompt": "True or false: every vector space has a unique additive identity?",
        "expected_answer": "True; identities are unique.",
    }
    row = _row(payload)
    chain = build_instrument_gates(vault, repository)
    chain([row])
    assert row["validation_status"] == "invalid"
    assert _SURFACE_ERROR in row["validation_errors"]
    assert GATE_REMEDIATION_AUDIT_KEY not in (row.get("audit") or {})


# ---------------------------------------------------------------------------
# Refresh door: same authorities, report-only
# ---------------------------------------------------------------------------


def test_refresh_door_reports_the_same_errors_as_the_generation_door(tmp_path: Path) -> None:
    vault, repository = _vault_and_repo(tmp_path)
    item = {
        "item_type": "practice_item",
        "operation": "create",
        "target_entity_id": _FAILING_PAYLOAD["id"],
        "validation_errors": [],
    }
    errors = _edited_payload_validation_errors(
        item, copy.deepcopy(_FAILING_PAYLOAD), vault, repository=repository
    )
    assert _SURFACE_ERROR in errors
    assert _DETECTOR_ERROR in errors
    assert _ATOMIC_ERROR in errors


def test_refresh_door_passes_the_remediated_payload(tmp_path: Path) -> None:
    vault, repository = _vault_and_repo(tmp_path)
    row = _row(_FAILING_PAYLOAD)
    build_instrument_gates(vault, repository)([row])
    assert row["validation_errors"] == []

    gate_errors = _instrument_gate_errors(row["payload"], vault, repository)
    assert gate_errors == []
    metadata_errors = _practice_item_metadata_errors(
        dict(row["payload"]), vault, None, generated=False
    )
    assert _ATOMIC_ERROR not in metadata_errors


def test_refresh_door_never_remediates(tmp_path: Path) -> None:
    """The edit door reports; a human-edited payload is the human's to change."""

    vault, repository = _vault_and_repo(tmp_path)
    payload = copy.deepcopy(_FAILING_PAYLOAD)
    item = {
        "item_type": "practice_item",
        "operation": "create",
        "target_entity_id": payload["id"],
        "validation_errors": [],
    }
    before = copy.deepcopy(payload)
    _edited_payload_validation_errors(item, payload, vault, repository=repository)
    assert payload == before
