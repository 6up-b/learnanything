"""Serializer-level surfaces for the remediation redesign (slice 4).

These pin the three read-only facts the UI now renders, and — more importantly —
the separations they exist to preserve:

* ``cold_check_result`` appears only on the attempt that SPENT a cold check, and
  reports ``passed`` and ``claim`` as two facts rather than one.
* ``cold_check_pending`` is a facet state distinct from demonstrated credit, and
  clears the moment the unassisted check is answered.
* ``auto_primed`` is absent, not false-with-a-zero, when the reveal ledger did
  not force the reclassification.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AUTO_PRIME_REVEAL_THRESHOLD,
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.remediation import (
    prescribe_remediation,
    start_remediation_episode,
    start_remediation_treatment,
)
from learnloop.vault.loader import load_vault
from learnloop_sidecar.handlers.knowledge_map import (
    _cold_check_pending_learning_objects,
    _facet_field,
)
from learnloop_sidecar.handlers.serializers import feedback_bundle
from learnloop_sidecar.handlers.sessions import _session_cold_checks

from tests.helpers import (
    NOW,
    add_followup_item,
    create_basic_vault,
    seed_due_item,
    write_facets,
)

LO_ID = "lo_svd_definition"
ITEM = "pi_svd_define_001"


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    write_facets(paths, [{"id": "recall", "kind": "definition", "claim": "SVD factorization."}])
    seed_due_item(paths)
    add_followup_item(vault_root)  # so primed and cold items can differ
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    misconception_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Confuses SVD with eigendecomposition.",
        correction_statement="SVD applies to any matrix; eigendecomposition needs a square one.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.8,
        clock=FrozenClock(NOW),
    )
    return vault, repository, misconception_id


def _attempt(vault, repository, item_id, *, clock, primed=False):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="U Sigma V transpose.",
            attempt_type="independent_attempt",
            hints_used=0,
            primed=primed,
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=clock,
    )


def _drive_to_cold_scheduled(vault, repository, misconception_id):
    episode = start_remediation_episode(repository, misconception_id, clock=FrozenClock(NOW))
    prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(NOW))
    treatment = start_remediation_treatment(vault, repository, episode["id"], clock=FrozenClock(NOW))
    _attempt(vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True)
    return repository.remediation_episode(episode["id"]), treatment["cold_item_id"]


# ── cold_check_result ─────────────────────────────────────────────────────────


def test_cold_check_result_is_null_on_an_ordinary_attempt(tmp_path):
    vault, repository, _ = _setup(tmp_path)
    result = _attempt(vault, repository, ITEM, clock=FrozenClock(NOW))

    bundle = feedback_bundle(vault, repository, result.attempt_id)
    assert bundle["coldCheckResult"] is None


def test_cold_check_result_reports_the_span_and_the_claim(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    episode, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)

    due = FrozenClock(NOW + timedelta(days=1))
    cold = _attempt(vault, repository, cold_item, clock=due)

    bundle = feedback_bundle(vault, repository, cold.attempt_id)
    result = bundle["coldCheckResult"]
    assert result is not None
    # The episode span the banner narrates: repaired then, checked now.
    assert result["episodeId"] == episode["id"]
    assert result["instructedAt"] == episode["created_at"]
    assert result["checkedAt"]
    assert result["checkedAt"] > result["instructedAt"]
    # The misconception under repair is named in words, not as an id.
    assert result["caseKind"] == "misconception"
    assert result["caseRef"] == misconception_id
    assert "SVD" in result["caseSummary"]
    # `passed` and `claim` are separate facts, and `claim` never invents a
    # confirmation the recorded outcome did not license.
    assert isinstance(result["passed"], bool)
    assert result["claim"] in {
        "repair_confirmed",
        "escalated_unrepaired",
        "downgraded",
        "unmeasured",
    }
    if result["claim"] == "repair_confirmed":
        assert result["passed"] is True
        assert result["claimDowngradedReason"] is None
    if result["claimDowngradedReason"]:
        assert result["claim"] == "downgraded"


def test_the_primed_repair_attempt_gets_no_cold_check_result(tmp_path):
    """The instructed half of the episode must not announce a verdict: the
    banner belongs to the attempt that answered unaided, and showing it on the
    primed attempt would report a repair as verified by the help it was given."""

    vault, repository, misconception_id = _setup(tmp_path)
    episode = start_remediation_episode(repository, misconception_id, clock=FrozenClock(NOW))
    prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(NOW))
    treatment = start_remediation_treatment(vault, repository, episode["id"], clock=FrozenClock(NOW))
    primed = _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )

    bundle = feedback_bundle(vault, repository, primed.attempt_id)
    assert bundle["coldCheckResult"] is None


# ── cold_check_pending ────────────────────────────────────────────────────────


def test_cold_check_pending_learning_objects_clear_once_the_check_is_answered(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)

    pending = _cold_check_pending_learning_objects(vault, repository)
    assert LO_ID in pending

    _attempt(vault, repository, cold_item, clock=FrozenClock(NOW + timedelta(days=1)))
    assert LO_ID not in _cold_check_pending_learning_objects(vault, repository)


def test_facet_points_carry_cold_check_pending_without_touching_demonstrated(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    _drive_to_cold_scheduled(vault, repository, misconception_id)

    pending = _cold_check_pending_learning_objects(vault, repository)
    assert LO_ID in pending

    field = _facet_field(vault, repository)
    assert field["points"], "the seeded facet should register a point"
    for point in field["points"]:
        assert isinstance(point["cold_check_pending"], bool)
        # The flag is exactly the LO join, nothing more.
        assert point["cold_check_pending"] == bool(
            set(point["learning_object_ids"]) & pending
        )
        # And it is a separate channel: demonstrated mass stays whatever the
        # evidence ledger says, pending check or not.
        assert point["demonstrated_mass"] == pytest.approx(
            len(point["demonstrated_capabilities"]) / len(point["required_capabilities"])
            if point["required_capabilities"]
            else 0.0
        )


# ── session cold-check counts ─────────────────────────────────────────────────


def test_session_counts_cold_checks_answered_and_confirmed_separately(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)

    due = FrozenClock(NOW + timedelta(days=1))
    session_id = repository.create_session(clock=due)
    assert _session_cold_checks(repository, session_id) == {"completed": 0, "passed": 0}

    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=cold_item,
            learner_answer_md="U Sigma V transpose.",
            attempt_type="independent_attempt",
            hints_used=0,
            session_id=session_id,
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=due,
    )
    repository.end_session(session_id)

    counts = _session_cold_checks(repository, session_id)
    # Answered is what the session did; confirmed is what it earned. The first
    # never implies the second.
    assert counts["completed"] == 1
    assert counts["passed"] <= counts["completed"]


# ── auto_primed ───────────────────────────────────────────────────────────────


def test_auto_primed_is_absent_when_the_ledger_did_not_force_it(tmp_path):
    vault, repository, _ = _setup(tmp_path)
    result = _attempt(vault, repository, ITEM, clock=FrozenClock(NOW))

    bundle = feedback_bundle(vault, repository, result.attempt_id)
    assert bundle["autoPrimed"] is False
    assert bundle["autoPrimedRevealTotal"] is None


def test_auto_primed_reports_the_reveal_total_behind_the_reclassification(tmp_path):
    vault, repository, _ = _setup(tmp_path)
    amount = AUTO_PRIME_REVEAL_THRESHOLD + 0.05
    repository.insert_reveal_event(
        {
            "practice_item_id": ITEM,
            "learning_object_id": LO_ID,
            "source_kind": "tutor_answer",
            "amount": amount,
            "basis": "test",
        },
        clock=FrozenClock(NOW),
    )

    result = _attempt(vault, repository, ITEM, clock=FrozenClock(NOW + timedelta(minutes=1)))

    bundle = feedback_bundle(vault, repository, result.attempt_id)
    assert bundle["primed"] is True
    assert bundle["autoPrimed"] is True
    assert bundle["autoPrimedRevealTotal"] == pytest.approx(amount)
