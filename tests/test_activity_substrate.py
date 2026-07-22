"""P0.1 activity lineage substrate (spec_p0_measurement_correctness §3.5-§3.8, §9.5)."""

from __future__ import annotations

import threading

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.services.activities import (
    Administration,
    SurfaceAlreadyReserved,
    append_observation,
    cancel_reservation,
    evaluate_held_out_eligibility,
    log_attempt_duration,
    open_administration,
    reserve_surface,
    resolve_legacy_item,
    retire_with_reason,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault

LO_ID = "lo_svd_definition"
CLOCK = FrozenClock(NOW)


def _add_item(root, item_id, *, prompt="Prompt.", stimulus=None, mode="short_answer"):
    payload = {
        "id": item_id,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": mode,
        "attempt_types_allowed": ["independent_attempt", "dont_know"],
        "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0},
        "prompt": prompt,
        "expected_answer": "Answer.",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
            "fatal_errors": [],
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    if stimulus is not None:
        payload["evidence_fingerprint"] = {"shared_stimulus_id": stimulus}
    upsert_practice_item(root, payload, clock=CLOCK)


@pytest.fixture
def env(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_item(root, "pi_a", prompt="Prompt A.")
    _add_item(root, "pi_b", prompt="Prompt B.")
    _add_item(root, "pi_stim_1", prompt="Stim prompt one.", stimulus="stim1")
    _add_item(root, "pi_stim_2", prompt="Stim prompt two (near-clone).", stimulus="stim1")
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    return vault, repo, paths


def _item(vault, item_id):
    return vault.practice_items[item_id]


# ---------------------------------------------------------------------------


def test_migration_created_substrate_tables_and_partial_indices(env):
    _, repo, _ = env
    with connect(repo.sqlite_path) as connection:
        names = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        indices = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
        }
    for table in (
        "activity_families",
        "activity_family_versions",
        "activity_cards",
        "activity_card_versions",
        "activity_surfaces",
        "activity_administrations",
        "activity_surface_reservations",
        "activity_exposure_events",
        "activity_observations",
        "activity_surface_lifecycle_events",
        "retirement_records",
        "interaction_events",
        "measurement_events",
    ):
        assert table in names
    assert "idx_activity_reservation_live_surface" in indices  # one live reservation
    assert "idx_activity_exposure_render_once" in indices  # expose-at-most-once


def test_resolve_legacy_item_is_deterministic_and_idempotent(env):
    vault, repo, _ = env
    item = _item(vault, "pi_a")
    first = resolve_legacy_item(vault, repo, item, purpose="practice", clock=CLOCK)
    second = resolve_legacy_item(vault, repo, item, purpose="practice", clock=CLOCK)
    assert first == second
    assert first.purpose == "practice"
    # A different purpose is a distinct card/family but the EXACT identical surface_hash.
    adapter = resolve_legacy_item(vault, repo, item, purpose="assessment", clock=CLOCK)
    assert adapter.surface_hash == first.surface_hash
    assert adapter.card_contract_hash != first.card_contract_hash
    assert adapter.family_id != first.family_id


def test_reserve_then_cancel_before_render_releases_unseen(env):
    vault, repo, _ = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    reservation = reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=CLOCK)
    status = cancel_reservation(repo, reservation.reservation_id, clock=CLOCK)
    assert status == "released_unseen"
    row = repo.fetch_reservation(reservation.reservation_id)
    assert row["status"] == "released_unseen"
    kinds = [event["kind"] for event in repo.surface_lifecycle_history(resolved.surface_id)]
    assert "release_unseen" in kinds
    surface = repo.fetch_surface(resolved.surface_id)
    assert evaluate_held_out_eligibility(repo, surface=surface, purpose="assessment").is_unseen


def test_cancel_after_render_does_not_restore_pristine(env):
    vault, repo, _ = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    reservation = reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=CLOCK)
    open_administration(repo, resolved=resolved, reservation=reservation, clock=CLOCK)
    status = cancel_reservation(repo, reservation.reservation_id, clock=CLOCK)
    assert status == "cancelled"
    surface = repo.fetch_surface(resolved.surface_id)
    eligibility = evaluate_held_out_eligibility(repo, surface=surface, purpose="assessment")
    assert not eligibility.is_unseen
    assert eligibility.reason == "exact_surface_collision"


def test_cancel_after_render_emits_no_release_unseen_lifecycle(env):
    """L8 (§4.5/§9.5): when a render has burned the surface, cancel must NOT emit a
    release_unseen lifecycle event -- the status guard + exposure re-check keep a
    lost-race cancel from spuriously restoring a burned surface to pristine."""

    vault, repo, _ = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    reservation = reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=CLOCK)
    open_administration(repo, resolved=resolved, reservation=reservation, clock=CLOCK)

    status = cancel_reservation(repo, reservation.reservation_id, clock=CLOCK)
    assert status == "cancelled"
    kinds = [event["kind"] for event in repo.surface_lifecycle_history(resolved.surface_id)]
    assert "release_unseen" not in kinds
    # The render already flipped the reservation to 'rendered'; cancel must not
    # clobber it back to a terminal cancel via the status guard.
    assert repo.fetch_reservation(reservation.reservation_id)["status"] == "rendered"


def test_render_is_the_burn_boundary(env):
    vault, repo, _ = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    admin = open_administration(repo, resolved=resolved, clock=CLOCK)
    assert isinstance(admin, Administration)
    # Regardless of any downstream outcome the surface is permanently ineligible.
    surface = repo.fetch_surface(resolved.surface_id)
    assert not evaluate_held_out_eligibility(repo, surface=surface, purpose="assessment").is_unseen
    rendered = [e for e in repo.exposures_for_surface(resolved.surface_id) if e["kind"] == "rendered"]
    assert len(rendered) == 1
    lifecycle = [e["kind"] for e in repo.surface_lifecycle_history(resolved.surface_id)]
    assert "expose" in lifecycle and "consume" in lifecycle  # assessment consumes


def test_concurrent_render_exposes_at_most_once(env):
    vault, repo, paths = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    reservation = reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=CLOCK)

    results: list[Administration] = []
    errors: list[Exception] = []
    barrier = threading.Barrier(2)

    def worker():
        try:
            local_repo = Repository(paths.sqlite_path)
            barrier.wait()
            results.append(
                open_administration(local_repo, resolved=resolved, reservation=reservation, clock=CLOCK)
            )
        except Exception as exc:  # pragma: no cover - surfaced via assert below
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors
    assert len(results) == 2
    # Exactly one rendered exposure, and both callers observe the same administration.
    rendered = [e for e in repo.exposures_for_surface(resolved.surface_id) if e["kind"] == "rendered"]
    assert len(rendered) == 1
    assert results[0].administration_id == results[1].administration_id
    assert results[0].already_open != results[1].already_open  # one winner, one loser


def test_ensure_activity_family_and_card_are_race_safe(env):
    """M1 (§3.5): concurrent ensure_activity_family / ensure_activity_card calls with
    the same authoring key converge on a single row -- the UNIQUE backstops
    (migration 070) turn the check-then-act race into an IntegrityError -> re-SELECT
    instead of a duplicate family/card.

    Before the fix (no UNIQUE index, plain SELECT-then-INSERT) two racers each
    passed the SELECT and inserted, minting two families and two cards."""

    _vault, _repo, paths = env
    family_ids: list[str] = []
    card_ids: list[str] = []
    errors: list[Exception] = []
    barrier = threading.Barrier(4)

    def worker():
        try:
            local = Repository(paths.sqlite_path)
            barrier.wait()
            fid = local.ensure_activity_family(
                purpose="practice", legacy_kind="practice_item", title="dup", clock=CLOCK
            )
            family_ids.append(fid)
            card_ids.append(local.ensure_activity_card(family_id=fid, clock=CLOCK))
        except Exception as exc:  # pragma: no cover - surfaced via assert
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, errors
    assert len(set(family_ids)) == 1  # exactly one family, no duplicate
    assert len(set(card_ids)) == 1  # exactly one card for that family
    with connect(paths.sqlite_path) as connection:
        n_fam = connection.execute(
            "SELECT COUNT(*) c FROM activity_families WHERE purpose='practice' "
            "AND legacy_kind='practice_item' AND title='dup'"
        ).fetchone()["c"]
        n_card = connection.execute(
            "SELECT COUNT(*) c FROM activity_cards WHERE family_id=?", (family_ids[0],)
        ).fetchone()["c"]
    assert n_fam == 1
    assert n_card == 1


def test_second_live_reservation_is_rejected(env):
    vault, repo, _ = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=CLOCK)
    with pytest.raises(SurfaceAlreadyReserved):
        reserve_surface(repo, surface_id=resolved.surface_id, purpose="assessment", clock=CLOCK)


def test_feedback_before_response_yields_no_terminal_credit(env):
    vault, repo, _ = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    admin = open_administration(repo, resolved=resolved, feedback_condition="before_response", clock=CLOCK)
    observation_id = append_observation(
        repo,
        administration_id=admin.administration_id,
        surface_id=resolved.surface_id,
        purpose="assessment",
        feedback_condition="before_response",
        attempt_id="att_x",
        clock=CLOCK,
    )
    with connect(repo.sqlite_path) as connection:
        row = connection.execute(
            "SELECT evidence_eligibility, eligibility_reason FROM activity_observations WHERE id = ?",
            (observation_id,),
        ).fetchone()
    assert row["evidence_eligibility"] == "ineligible"
    assert row["eligibility_reason"] == "feedback_before_response"


def test_cross_purpose_exact_and_near_clone_block_unseen(env):
    vault, repo, _ = env
    # Exact: practice render of an item blocks a later assessment claim on the
    # identical surface_hash (the adapter shares the surface_hash).
    practice = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="practice", clock=CLOCK)
    open_administration(repo, resolved=practice, clock=CLOCK)  # practice render enters ledger
    adapter = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    surface = repo.fetch_surface(adapter.surface_id)
    exact = evaluate_held_out_eligibility(repo, surface=surface, purpose="assessment")
    assert not exact.is_unseen and exact.reason == "exact_surface_collision"

    # Near-clone: a diagnostic render of one stimulus sibling blocks an assessment
    # claim on the other sibling (shared fingerprint, different surface_hash).
    diag = resolve_legacy_item(vault, repo, _item(vault, "pi_stim_1"), purpose="diagnostic", clock=CLOCK)
    open_administration(repo, resolved=diag, clock=CLOCK)
    sibling = resolve_legacy_item(vault, repo, _item(vault, "pi_stim_2"), purpose="assessment", clock=CLOCK)
    assert sibling.surface_hash != diag.surface_hash
    assert sibling.fingerprint == diag.fingerprint
    sibling_surface = repo.fetch_surface(sibling.surface_id)
    near = evaluate_held_out_eligibility(repo, surface=sibling_surface, purpose="assessment")
    assert not near.is_unseen and near.reason == "near_clone_collision"


def test_retire_with_reason_records_and_preserves_evidence(env):
    vault, repo, _ = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="assessment", clock=CLOCK)
    admin = open_administration(repo, resolved=resolved, clock=CLOCK)
    # A surviving evidence proxy: an observation row that must NOT be deleted.
    observation_id = append_observation(
        repo,
        administration_id=admin.administration_id,
        surface_id=resolved.surface_id,
        purpose="assessment",
        attempt_id="att_keep",
        clock=CLOCK,
    )

    record_id = retire_with_reason(
        repo,
        scope="card",
        card_version_id=resolved.card_version_id,
        reason="knew_prompt_not_concept",
        provenance="learner_action",
        clock=CLOCK,
    )

    records = repo.retirement_records_for_card_version(resolved.card_version_id)
    assert len(records) == 1 and records[0]["id"] == record_id
    assert records[0]["reason"] == "knew_prompt_not_concept"
    assert records[0]["provenance"] == "learner_action"
    assert records[0]["lifecycle_event_id"] is not None
    assert records[0]["interaction_event_id"] is not None

    lifecycle = [e["kind"] for e in repo.surface_lifecycle_history(resolved.surface_id)]
    assert "retire" in lifecycle
    with connect(repo.sqlite_path) as connection:
        interaction = connection.execute(
            "SELECT * FROM interaction_events WHERE id = ?", (records[0]["interaction_event_id"],)
        ).fetchone()
        surviving = connection.execute(
            "SELECT COUNT(*) n FROM activity_observations WHERE id = ?", (observation_id,)
        ).fetchone()
    assert interaction["kind"] == "retirement_reason"
    assert surviving["n"] == 1  # evidence untouched (§3.7)


def test_interaction_event_written_for_attempt_duration(env):
    vault, repo, _ = env
    resolved = resolve_legacy_item(vault, repo, _item(vault, "pi_a"), purpose="practice", clock=CLOCK)
    admin = open_administration(repo, resolved=resolved, clock=CLOCK)
    event_id = log_attempt_duration(
        repo,
        administration_id=admin.administration_id,
        attempt_id="att_dur",
        duration_ms=42000,
        surface_id=resolved.surface_id,
        clock=CLOCK,
    )
    events = repo.interaction_events_for_attempt("att_dur")
    assert len(events) == 1
    assert events[0]["id"] == event_id
    assert events[0]["kind"] == "attempt_duration"
    assert events[0]["attempt_duration_ms"] == 42000
    assert events[0]["administration_id"] == admin.administration_id
