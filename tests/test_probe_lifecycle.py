"""Family-version lifecycle transitions (spec §9.7, Checkpoint 4.7)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.probe_families import (
    CONTRAST_CONFUSABLE_V1,
    ensure_builtin_families,
    record_real_observation_counts,
)
from learnloop.services.probe_lifecycle import (
    LifecycleTransitionError,
    apply_family_lifecycle_transition,
    evaluate_family_lifecycle,
    retire_probe_instance,
    revise_family_version,
)
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault

FAMILY = CONTRAST_CONFUSABLE_V1.id
VERSION = CONTRAST_CONFUSABLE_V1.version
GRADER = CONTRAST_CONFUSABLE_V1.grader_policy
CLOCK = FrozenClock(NOW)


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    ensure_builtin_families(repository, clock=CLOCK)
    return loaded, repository


def _feed_real_evidence(repository, *, times):
    for _ in range(times):
        record_real_observation_counts(
            repository,
            family_template_id=FAMILY,
            family_template_version=VERSION,
            posterior_after={"unfamiliar": 1.0},
            slot_map={"unfamiliar": "unfamiliar"},
            observed_outcome="unanswered",
            grader_version=GRADER,
            clock=CLOCK,
        )


def test_provisional_family_needs_evidence_before_trust(tmp_path):
    loaded, repository = _setup(tmp_path)
    assessment = evaluate_family_lifecycle(loaded, repository, FAMILY, VERSION)
    assert assessment.status == "provisional"
    assert assessment.recommendation == "insufficient_evidence"
    assert any("real-learner sample" in reason for reason in assessment.reasons)


def test_transitions_follow_the_allowed_graph(tmp_path):
    _loaded, repository = _setup(tmp_path)

    # provisional -> trusted is allowed; trusted -> trusted is a no-op error;
    # retired is terminal.
    apply_family_lifecycle_transition(
        repository, family_id=FAMILY, version=VERSION, to_status="trusted", reason={"forced": True}
    )
    assert repository.probe_family_template(FAMILY, VERSION).status == "trusted"
    with pytest.raises(LifecycleTransitionError):
        apply_family_lifecycle_transition(
            repository, family_id=FAMILY, version=VERSION, to_status="trusted"
        )
    apply_family_lifecycle_transition(
        repository, family_id=FAMILY, version=VERSION, to_status="retired"
    )
    record = repository.probe_family_template(FAMILY, VERSION)
    assert record.status == "retired"
    assert record.retired_at is not None
    with pytest.raises(LifecycleTransitionError):
        apply_family_lifecycle_transition(
            repository, family_id=FAMILY, version=VERSION, to_status="provisional"
        )

    events = repository.probe_family_lifecycle_events(FAMILY, VERSION)
    assert [(e["from_status"], e["to_status"]) for e in events] == [
        ("provisional", "trusted"),
        ("trusted", "retired"),
    ]
    assert events[0]["reason"] == {"forced": True}


def test_regrade_disagreement_recommends_retirement(tmp_path):
    loaded, repository = _setup(tmp_path)
    admit_probe_instrument_card(repository)
    _feed_real_evidence(repository, times=25)

    # Manufacture systematic grading disagreement without needing observations:
    # regrade checks are recorded directly against the family/grader scope.
    for index in range(6):
        repository.insert_probe_regrade_check(
            attempt_id=f"attempt_{index}",
            probe_family_template_id=FAMILY,
            probe_family_template_version=VERSION,
            grader_version=GRADER,
            original_outcome="correct_target_reason",
            regrade_outcome="confusable_signature",
            clock=CLOCK,
        )

    assessment = evaluate_family_lifecycle(loaded, repository, FAMILY, VERSION)
    assert assessment.recommendation == "retire"
    assert any("regrade agreement" in reason for reason in assessment.reasons)


def test_revision_creates_next_draft_version(tmp_path):
    _loaded, repository = _setup(tmp_path)
    new_version = revise_family_version(repository, FAMILY, clock=CLOCK)
    assert new_version == VERSION + 1

    revised = repository.probe_family_template(FAMILY, new_version)
    assert revised.status == "draft"
    assert revised.template["version"] == new_version
    # The old version is untouched: historical observations replay unchanged.
    assert repository.probe_family_template(FAMILY, VERSION).status == "provisional"
    events = repository.probe_family_lifecycle_events(FAMILY, new_version)
    assert events[-1]["reason"] == {"revised_from_version": VERSION}


def test_instance_retirement_deactivates_without_touching_history(tmp_path):
    _loaded, repository = _setup(tmp_path)
    admit_probe_instrument_card(repository)

    assert retire_probe_instance(repository, "pi_svd_define_001", reason="bad surface", clock=CLOCK)
    links = repository.probe_item_family_links("pi_svd_define_001")
    assert all(link.instance_metadata["review_status"] == "retired" for link in links)
    states = repository.practice_item_states()
    assert not states["pi_svd_define_001"].active
    # Unknown instance: nothing to retire.
    assert not retire_probe_instance(repository, "pi_nonexistent", clock=CLOCK)
