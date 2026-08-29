"""P2 §4: the causal activity policy is ONE authority with a pinned matrix.

Every cell of the table in ``learnloop.diagnosis.causal_activity_policy``'s
docstring is
asserted here, including the deliberate divergence from spec §7 (a *pure*
diagnostic feeds neither FSRS nor certification, which §7 only mandates for an
*instructional* one). Changing a cell means editing this test and bumping
``CAUSAL_ACTIVITY_POLICY_VERSION`` — which is the point.
"""

from __future__ import annotations

import pytest

import learnloop.causal_activity_policy as policy_primitives
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.causal_activity_policy import (
    CAUSAL_ACTIVITY_POLICY_VERSION,
    CONTAMINATION_CLASSES,
    CONTAMINATION_PRECEDENCE,
    assess_near_clone,
    attempt_counts_as_assisted,
    classify_attempt_activity,
    near_clone_from_selection_components,
    policy_for_class,
    resolve_attempt_activity_policy,
    resolve_conflicting_classes,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, add_followup_item, create_basic_vault

CLOCK = FrozenClock(NOW)

# class -> (fsrs, certification, assisted, closes_pre_intervention_segment)
POLICY_MATRIX = {
    "pure_diagnostic": (False, False, False, False),
    "instructional_diagnostic": (False, False, True, True),
    "repair_activity": (False, False, True, False),
    "verification": (True, True, False, False),
}


def test_service_exports_share_the_dependency_neutral_policy_authority():
    assert policy_for_class is policy_primitives.policy_for_class
    assert CONTAMINATION_PRECEDENCE is policy_primitives.CONTAMINATION_PRECEDENCE
    assert CAUSAL_ACTIVITY_POLICY_VERSION == (
        policy_primitives.CAUSAL_ACTIVITY_POLICY_VERSION
    )


@pytest.mark.parametrize(
    "contamination_class,expected", sorted(POLICY_MATRIX.items())
)
def test_policy_matrix_cells_are_pinned(contamination_class, expected):
    fsrs, certification, assisted, closes = expected
    policy = policy_for_class(contamination_class)
    assert policy.eligible_for_fsrs is fsrs
    assert policy.eligible_for_certification is certification
    assert policy.counts_as_assisted is assisted
    assert policy.closes_pre_intervention_segment is closes
    assert policy.policy_version == CAUSAL_ACTIVITY_POLICY_VERSION


def test_matrix_covers_every_class_exactly():
    assert set(POLICY_MATRIX) == CONTAMINATION_CLASSES
    assert set(CONTAMINATION_PRECEDENCE) == CONTAMINATION_CLASSES
    assert len(CONTAMINATION_PRECEDENCE) == len(CONTAMINATION_CLASSES)


def test_pure_diagnostic_is_stricter_than_spec_section_7():
    """Documented divergence: §7 only bars the INSTRUCTIONAL diagnostic."""

    pure = policy_for_class("pure_diagnostic")
    assert pure.eligible_for_fsrs is False
    assert pure.eligible_for_certification is False
    # ...but it is NOT assisted and does NOT close the pre-intervention
    # segment: only instruction leaking into the measurement does that.
    assert pure.counts_as_assisted is False
    assert pure.closes_pre_intervention_segment is False


def test_near_clone_only_moves_the_verification_certification_cell():
    assert policy_for_class("verification", near_clone=True).eligible_for_certification is False
    assert policy_for_class("verification", near_clone=True).eligible_for_fsrs is True
    for contamination_class in CONTAMINATION_CLASSES:
        clean = policy_for_class(contamination_class)
        cloned = policy_for_class(contamination_class, near_clone=True)
        assert clean.eligible_for_fsrs is cloned.eligible_for_fsrs
        assert clean.counts_as_assisted is cloned.counts_as_assisted
        assert (
            clean.closes_pre_intervention_segment
            is cloned.closes_pre_intervention_segment
        )


def test_unknown_class_raises():
    with pytest.raises(ValueError, match="unknown contamination class"):
        policy_for_class("wishful_thinking")


@pytest.mark.parametrize(
    "attempt_type,primed,hints,expected_class",
    [
        ("practice", False, 0, "verification"),
        ("dont_know", False, 0, "verification"),
        ("hinted_attempt", False, 2, "verification"),
        ("practice", True, 0, "repair_activity"),
        ("diagnostic_probe", False, 0, "pure_diagnostic"),
        ("diagnostic_probe", False, 1, "instructional_diagnostic"),
        ("diagnostic_probe", True, 0, "instructional_diagnostic"),
    ],
)
def test_attempt_signals_pick_the_class(attempt_type, primed, hints, expected_class):
    policy = classify_attempt_activity(
        attempt_type=attempt_type, primed=primed, hints_used=hints
    )
    assert policy.contamination_class == expected_class


def test_legacy_assisted_types_stay_assisted_without_losing_fsrs():
    """A hinted practice review has always scheduled; P2 does not change that."""

    policy = classify_attempt_activity(attempt_type="hinted_attempt", hints_used=0)
    assert policy.contamination_class == "verification"
    assert policy.counts_as_assisted is True
    assert policy.eligible_for_fsrs is True
    # Assisted attempts certify nothing (§5.4/§6).
    assert policy.eligible_for_certification is False


@pytest.mark.parametrize(
    "attempt_type,primed,hints,assisted",
    [
        ("practice", False, 0, False),
        ("practice", False, 1, True),
        ("practice", True, 0, True),
        ("hinted_attempt", False, 0, True),
        ("guided_walkthrough", False, 0, True),
        ("reconstruction_after_walkthrough", False, 0, True),
        ("diagnostic_probe", False, 0, False),
        ("diagnostic_probe", False, 1, True),
        ("teach_back", False, 0, False),
    ],
)
def test_attempt_counts_as_assisted(attempt_type, primed, hints, assisted):
    assert (
        attempt_counts_as_assisted(
            attempt_type=attempt_type, primed=primed, hints_used=hints
        )
        is assisted
    )


def test_resolved_attempt_policy_separates_assistance_from_eligibility():
    pure_probe = resolve_attempt_activity_policy(attempt_type="diagnostic_probe")
    assert pure_probe.counts_as_assisted is False
    assert pure_probe.eligible_for_certification is False

    near_clone = resolve_attempt_activity_policy(
        attempt_type="independent_attempt",
        recorded={"contamination_class": "verification", "near_clone": True},
    )
    assert near_clone.counts_as_assisted is False
    assert near_clone.eligible_for_certification is False

    # A recorded lower-contamination fact cannot launder immutable priming.
    primed = resolve_attempt_activity_policy(
        attempt_type="independent_attempt",
        primed=True,
        recorded={"contamination_class": "verification", "near_clone": False},
    )
    assert primed.contamination_class == "repair_activity"
    assert primed.counts_as_assisted is True
    assert primed.eligible_for_certification is False


def test_explicit_class_overrides_the_signal_derivation():
    policy = classify_attempt_activity(
        attempt_type="practice",
        primed=True,
        hints_used=0,
        explicit_class="repair_activity",
    )
    assert policy.contamination_class == "repair_activity"


def test_resolve_conflicting_classes_is_most_contaminated_wins():
    assert resolve_conflicting_classes("verification", "repair_activity") == "repair_activity"
    assert resolve_conflicting_classes("repair_activity", "verification") == "repair_activity"
    assert (
        resolve_conflicting_classes("pure_diagnostic", "instructional_diagnostic")
        == "instructional_diagnostic"
    )
    assert resolve_conflicting_classes("verification", "verification") == "verification"
    with pytest.raises(ValueError):
        resolve_conflicting_classes("verification", "nonsense")


def test_precedence_order_is_total_and_ranked():
    ranked = [policy_for_class(name) for name in CONTAMINATION_PRECEDENCE]
    # Only the least contaminated class feeds retention/certification.
    assert [p.eligible_for_fsrs for p in ranked] == [False, False, False, True]


# ---------------------------------------------------------------------------
# near_clone (§4.3)
# ---------------------------------------------------------------------------


def test_near_clone_is_a_fingerprint_comparison_not_provenance(tmp_path):
    """Regression: being generated FROM a source item is not being a clone of it."""

    root = tmp_path / "vault"
    create_basic_vault(root)
    add_followup_item(root)
    vault = load_vault(root)
    item_ids = sorted(vault.practice_items)
    assert len(item_ids) >= 2
    first, second = item_ids[0], item_ids[1]

    same = assess_near_clone(
        vault, practice_item_id=first, source_practice_item_id=first
    )
    assert same.near_clone is True
    assert same.basis == "shared_surface_group"

    other = assess_near_clone(
        vault, practice_item_id=second, source_practice_item_id=first
    )
    from learnloop.substrate.canonical_projection import surface_group_id

    expected = surface_group_id(vault.practice_items[second]) == surface_group_id(
        vault.practice_items[first]
    )
    assert other.near_clone is expected
    assert other.basis in {"shared_surface_group", "distinct_surface_group"}


def test_near_clone_without_a_source_is_false(tmp_path):
    root = tmp_path / "vault"
    create_basic_vault(root)
    vault = load_vault(root)
    item_id = sorted(vault.practice_items)[0]
    assessment = assess_near_clone(
        vault, practice_item_id=item_id, source_practice_item_id=None
    )
    assert assessment.near_clone is False
    assert assessment.basis == "no_source_item"


def test_near_clone_fails_closed_but_audibly_when_unresolvable(tmp_path):
    root = tmp_path / "vault"
    create_basic_vault(root)
    vault = load_vault(root)
    item_id = sorted(vault.practice_items)[0]
    assessment = assess_near_clone(
        vault, practice_item_id=item_id, source_practice_item_id="pi_does_not_exist"
    )
    assert assessment.near_clone is True
    assert assessment.basis == "unknown"


def test_explicit_near_clone_declaration_wins(tmp_path):
    root = tmp_path / "vault"
    create_basic_vault(root)
    vault = load_vault(root)
    item_id = sorted(vault.practice_items)[0]
    assessment = near_clone_from_selection_components(
        vault,
        practice_item_id=item_id,
        selection_components={"near_clone": False, "source_practice_item_id": item_id},
    )
    assert assessment.near_clone is False
    assert assessment.basis == "explicit"


# ---------------------------------------------------------------------------
# Append-only event log (§4.2)
# ---------------------------------------------------------------------------


def test_conflicting_writers_never_raise_and_most_contaminated_wins(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    repository = Repository(paths.sqlite_path)

    first = repository.record_causal_activity_classification(
        attempt_id="att_1",
        contamination_class="pure_diagnostic",
        source="probe_presentation_observation",
        clock=CLOCK,
    )
    assert first["contamination_class"] == "pure_diagnostic"

    # A primed probe: apply_attempt also classifies it as a repair activity.
    second = repository.record_causal_activity_classification(
        attempt_id="att_1",
        contamination_class="repair_activity",
        source="apply_attempt.primed",
        clock=CLOCK,
    )
    assert second["contamination_class"] == "repair_activity"
    assert second["recorded_classes"] == ["repair_activity", "pure_diagnostic"]
    assert second["event_count"] == 2
    assert second["eligible_for_fsrs"] is False
    assert second["counts_as_assisted"] is True

    current = repository.causal_activity_classification("att_1")
    assert current["contamination_class"] == "repair_activity"


def test_restating_the_same_fact_is_idempotent(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    repository = Repository(paths.sqlite_path)

    for _ in range(3):
        repository.record_causal_activity_classification(
            attempt_id="att_replay",
            contamination_class="verification",
            source="cold_verification",
            clock=CLOCK,
        )
    assert len(repository.causal_activity_classification_events("att_replay")) == 1


def test_concurrent_classification_waits_then_appends_next_sequence(tmp_path):
    """A reserved writer lock prevents MAX(seq)+1 from dropping a writer."""

    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import sleep

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    repository = Repository(paths.sqlite_path)

    # Hold the first connection's write transaction open with seq=1 while a
    # second repository connection tries to append. The second writer must wait,
    # then re-read MAX after commit and use seq=2. Under the old deferred
    # SELECT + INSERT OR IGNORE implementation it could read 0 and either fail
    # its lock upgrade or silently lose its row on the seq uniqueness conflict.
    writer_a = repository.connection()
    writer_a.execute("BEGIN IMMEDIATE")
    writer_a.execute(
        """
        INSERT INTO causal_activity_classification_events(
          id, attempt_id, seq, contamination_class, near_clone,
          near_clone_basis, closes_pre_intervention_segment,
          eligible_for_fsrs, eligible_for_certification, source,
          policy_version, detail_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "event_a",
            "att_concurrent",
            1,
            "pure_diagnostic",
            0,
            "no_source_item",
            0,
            0,
            0,
            "writer_a",
            CAUSAL_ACTIVITY_POLICY_VERSION,
            "{}",
            NOW.isoformat().replace("+00:00", "Z"),
        ),
    )
    started = Event()

    def append_second():
        started.set()
        return repository.record_causal_activity_classification(
            attempt_id="att_concurrent",
            contamination_class="repair_activity",
            source="writer_b",
            clock=CLOCK,
        )

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(append_second)
            assert started.wait(timeout=1)
            sleep(0.05)
            assert not future.done()
            writer_a.commit()
            resolved = future.result(timeout=2)
    finally:
        if writer_a.in_transaction:
            writer_a.rollback()
        writer_a.close()

    assert resolved["contamination_class"] == "repair_activity"
    events = repository.causal_activity_classification_events("att_concurrent")
    assert [(event["seq"], event["source"]) for event in events] == [
        (1, "writer_a"),
        (2, "writer_b"),
    ]


def test_near_clone_fails_closed_across_conflicting_events(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    repository = Repository(paths.sqlite_path)

    repository.record_causal_activity_classification(
        attempt_id="att_clone",
        contamination_class="verification",
        near_clone=False,
        near_clone_basis="distinct_surface_group",
        source="writer_a",
        clock=CLOCK,
    )
    row = repository.record_causal_activity_classification(
        attempt_id="att_clone",
        contamination_class="verification",
        near_clone=True,
        near_clone_basis="shared_surface_group",
        source="writer_b",
        clock=CLOCK,
    )
    assert row["near_clone"] is True
    assert row["eligible_for_certification"] is False


def test_classification_events_are_append_only(tmp_path):
    import sqlite3

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    repository = Repository(paths.sqlite_path)
    repository.record_causal_activity_classification(
        attempt_id="att_frozen",
        contamination_class="verification",
        source="writer_a",
        clock=CLOCK,
    )
    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE causal_activity_classification_events "
                "SET contamination_class = 'pure_diagnostic'"
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "DELETE FROM causal_activity_classification_events"
            )


def test_missing_attempt_has_no_classification(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    repository = Repository(paths.sqlite_path)
    assert repository.causal_activity_classification("nope") is None


# ---------------------------------------------------------------------------
# Projection version bump (§4.4 replay warning)
# ---------------------------------------------------------------------------


def test_canonical_projection_version_change_is_a_recalibration_boundary(tmp_path):
    """A projection semantics change must not retro-change state silently."""

    from datetime import timedelta

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    repository = Repository(paths.sqlite_path)
    for offset, projection_version in (
        (0, "canonical_projection_v1"),
        (1, "canonical_projection_v1"),
        (2, "canonical_projection_v2_causal_activity"),
    ):
        repository.record_derived_state_rebuild(
            scope="full",
            learning_object_ids=["lo_svd_definition"],
            algorithm_version="mvp-0.8",
            rebuilt_learning_objects=1,
            replayed_attempts=1,
            canonical_projection_version=projection_version,
            clock=FrozenClock(NOW + timedelta(hours=offset)),
        )

    changes = repository.derived_state_rebuild_version_changes()
    # Two boundaries, not one: the FIRST rebuild also recomputed estimates the
    # learner had already seen (`replayed_attempts=1`) under a projection
    # version that was not previously on record, and a silent recompute is the
    # failure mode this feed exists to prevent. Its `previous_*` is None, which
    # is the truthful statement that nothing earlier was recorded.
    assert len(changes) == 2
    assert changes[0]["previous_canonical_projection_version"] is None
    assert changes[0]["canonical_projection_version"] == "canonical_projection_v1"
    assert changes[1]["algorithm_version"] == "mvp-0.8"
    assert changes[1]["previous_algorithm_version"] == "mvp-0.8"
    assert (
        changes[1]["canonical_projection_version"]
        == "canonical_projection_v2_causal_activity"
    )
    assert (
        changes[1]["previous_canonical_projection_version"]
        == "canonical_projection_v1"
    )


def test_rebuild_records_the_current_projection_version(tmp_path):
    from learnloop.substrate.canonical_projection import CANONICAL_PROJECTION_VERSION
    from learnloop.substrate.replay import rebuild_derived_state

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    rebuild_derived_state(vault, repository, clock=CLOCK)
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT canonical_projection_version FROM derived_state_rebuilds"
        ).fetchall()
    assert [row["canonical_projection_version"] for row in rows] == [
        CANONICAL_PROJECTION_VERSION
    ]
