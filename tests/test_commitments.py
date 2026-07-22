"""P1 step 1 -- durable commitments (spec_p1_shared_substrate §3.1, §3.2, §9.1)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import commitments as C

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _targets(ref="svd"):
    return [{"target_kind": "canonical_facet", "target_ref": ref, "role": "required"}]


def _create(repo, action="select_exemplar", **over):
    kwargs = dict(
        action=action,
        intent_text="remember the svd",
        targets=_targets(),
        depth_preset="remember_key_ideas",
        clock=CLOCK,
    )
    kwargs.update(over)
    return C.create_commitment(repo, **kwargs)


# --- §9.1 invariant 4: passive action cannot commit --------------------------

@pytest.mark.parametrize("action", ["highlight", "read", "ask", "shown_proposal", "browse"])
def test_passive_action_cannot_create_commitment(repo, action):
    with pytest.raises(C.PassiveActionCannotCommit):
        _create(repo, action=action)


@pytest.mark.parametrize(
    "action", ["help_me_remember", "test_me_later", "select_exemplar", "create_quest"]
)
def test_each_commit_action_creates(repo, action):
    commitment = _create(repo, action=action)
    assert commitment.created is True
    assert commitment.created_action == action
    assert commitment.head.version == 1
    # A depth policy/envelope is proposed at creation (§3.1).
    assert commitment.head.depth_policy_version_id is not None
    assert commitment.head.depth_envelope_version_id is not None


# --- idempotency + merge candidate (§3.1) ------------------------------------

def test_idempotent_on_client_key(repo):
    first = _create(repo, client_idempotency_key="k1")
    second = _create(repo, client_idempotency_key="k1")
    assert second.id == first.id
    assert second.created is False


def test_idempotency_key_race_yields_one_commitment(repo):
    # B6 regression. Pre-fix there was no DB backstop: two concurrent creates with the
    # same client key could both pass the service-level SELECT (each sees no existing
    # row) and INSERT two commitments. The migration-080 partial UNIQUE index + the
    # IntegrityError->re-load-winner path collapse them to exactly one.
    import threading

    # Warm the content-addressed shared depth policy/envelope version objects (an
    # unrelated commitment with a different key) so the race is purely on the
    # commitment idempotency key, not on the shared version-object upserts.
    _create(repo, client_idempotency_key="warm-up")

    results: list = []
    errors: list = []
    barrier = threading.Barrier(6)

    def _worker():
        try:
            barrier.wait()
            results.append(_create(repo, client_idempotency_key="race-key"))
        except Exception as exc:  # pragma: no cover - surfaced via assertion below
            errors.append(exc)

    threads = [threading.Thread(target=_worker) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert len({c.id for c in results}) == 1  # one winner id
    assert sum(1 for c in results if c.created) <= 1  # at most one reported the create
    rows = repo.commitment_versions_for(results[0].id)
    assert len({r["commitment_id"] for r in rows}) == 1
    with repo.connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS n FROM commitments WHERE idempotency_key = 'race-key'"
        ).fetchone()["n"]
    assert count == 1


def test_missing_key_returns_merge_candidate_not_silent_merge(repo):
    first = _create(repo)  # no client key
    second = _create(repo, intent_text="a differently worded intent")  # same target set/action
    assert second.id == first.id
    assert second.created is False
    assert second.merge_candidate is True
    # No second commitment was minted, and the differently-worded intent did NOT
    # overwrite the original head (no silent merge).
    assert C.resolve_head(repo, first.id).intent_text == "remember the svd"


def test_different_target_set_creates_distinct_commitment(repo):
    first = _create(repo)
    other = C.create_commitment(
        repo,
        action="select_exemplar",
        intent_text="remember qr",
        targets=[{"target_kind": "canonical_facet", "target_ref": "qr", "role": "required"}],
        depth_preset="remember_key_ideas",
        clock=CLOCK,
    )
    assert other.id != first.id
    assert other.created is True


# --- version append leaves prior bytes/hash unchanged (invariant 5) ----------

def test_version_append_preserves_prior_bytes(repo):
    commitment = _create(repo)
    v1 = commitment.head
    C.append_commitment_version(
        repo, commitment_id=commitment.id, intent_text="sharper intent",
        change_reason="reworded", clock=CLOCK,
    )
    versions = repo.commitment_versions_for(commitment.id)
    assert len(versions) == 2
    stored_v1 = next(v for v in versions if v["version"] == 1)
    assert stored_v1["id"] == v1.id
    assert stored_v1["version_hash"] == v1.version_hash
    assert stored_v1["intent_text"] == "remember the svd"
    head = C.resolve_head(repo, commitment.id)
    assert head.version == 2
    assert head.intent_text == "sharper intent"


# --- A.3: depth-policy/envelope change forces version bump --------------------

def test_depth_policy_change_forces_version_bump_and_typed_event(repo):
    commitment = _create(repo, action="help_me_remember")
    before = C.resolve_head(repo, commitment.id).version
    C.change_depth_policy(repo, commitment_id=commitment.id, policy="auto_within_envelope", clock=CLOCK)
    after = C.resolve_head(repo, commitment.id)
    assert after.version == before + 1
    kinds = [e["kind"] for e in repo.commitment_events_for(commitment.id)]
    assert "version_appended" in kinds
    assert "depth_policy_changed" in kinds


def test_depth_envelope_change_forces_version_bump(repo):
    commitment = _create(repo)
    before = C.resolve_head(repo, commitment.id).version
    C.change_depth_envelope(
        repo, commitment_id=commitment.id, bounds={"capabilities": ["retrieval"]},
        allow_widen=True, clock=CLOCK
    )
    after = C.resolve_head(repo, commitment.id)
    assert after.version == before + 1
    assert after.depth_envelope_version_id is not None
    kinds = [e["kind"] for e in repo.commitment_events_for(commitment.id)]
    assert "depth_envelope_changed" in kinds


def test_noop_depth_policy_change_short_circuits(repo):
    # B8 regression. Re-applying the SAME resolved policy version must not bump the
    # version or fire a typed event (A.3 fires only on a real change to the active id).
    commitment = _create(repo, action="help_me_remember")
    body = {"policy": "auto_within_envelope", "note": "same"}
    C.change_depth_policy(repo, commitment_id=commitment.id, policy="auto_within_envelope",
                          body=dict(body), clock=CLOCK)
    mid = C.resolve_head(repo, commitment.id)
    events_before = len(repo.commitment_events_for(commitment.id))
    # Identical policy + body -> identical content hash -> same version id -> no-op.
    head = C.change_depth_policy(repo, commitment_id=commitment.id, policy="auto_within_envelope",
                                 body=dict(body), clock=CLOCK)
    assert head.version == mid.version  # no bump
    assert head.id == mid.id
    assert len(repo.commitment_events_for(commitment.id)) == events_before  # no event


def test_noop_depth_envelope_change_short_circuits(repo):
    # B8 regression: identical envelope bounds/edges -> same envelope id -> no-op.
    commitment = _create(repo)
    C.change_depth_envelope(repo, commitment_id=commitment.id, bounds={"capabilities": ["retrieval"]},
                            allow_widen=True, clock=CLOCK)
    mid = C.resolve_head(repo, commitment.id)
    events_before = len(repo.commitment_events_for(commitment.id))
    head = C.change_depth_envelope(repo, commitment_id=commitment.id,
                                   bounds={"capabilities": ["retrieval"]}, clock=CLOCK)
    assert head.version == mid.version and head.id == mid.id
    assert len(repo.commitment_events_for(commitment.id)) == events_before


# --- milestone-reached does NOT bump the version (A.3) -----------------------

def test_milestone_reached_does_not_bump_version(repo):
    commitment = _create(repo)
    before = C.resolve_head(repo, commitment.id).version
    C.record_milestone_reached(repo, commitment_id=commitment.id, milestone_slug="m1", clock=CLOCK)
    assert C.resolve_head(repo, commitment.id).version == before
    kinds = [e["kind"] for e in repo.commitment_events_for(commitment.id)]
    assert "depth_milestone_reached" in kinds


# --- target removal appends successor, preserves mapped observations ---------

def test_target_removal_appends_successor(repo):
    commitment = _create(repo)
    C.add_target(
        repo, commitment_id=commitment.id,
        target={"target_kind": "canonical_facet", "target_ref": "qr", "role": "optional"},
        clock=CLOCK,
    )
    head = C.resolve_head(repo, commitment.id)
    assert len(head.targets) == 2
    C.remove_target(repo, commitment_id=commitment.id, target_ref="qr", clock=CLOCK)
    head2 = C.resolve_head(repo, commitment.id)
    assert {t.target_ref for t in head2.targets} == {"svd"}
    # The prior version's target rows are still stored (append-only; observations
    # mapped to the removed target are never deleted, §3.2).
    v2 = next(v for v in repo.commitment_versions_for(commitment.id) if v["version"] == 2)
    prior_targets = repo.commitment_targets_for_version(v2["id"])
    assert any(t["target_ref"] == "qr" for t in prior_targets)
    kinds = [e["kind"] for e in repo.commitment_events_for(commitment.id)]
    assert "target_removed" in kinds


# --- disposition projection incl. test_me_later -> satisfied (§3.1) ----------

def test_test_me_later_starts_pending_then_satisfied(repo):
    commitment = _create(repo, action="test_me_later", depth_preset="keep_in_touch")
    assert commitment.disposition == "one_check_pending"
    # A hold_at_target policy is the §10 launch default for test_me_later.
    result = C.satisfy_single_check(repo, commitment_id=commitment.id, clock=CLOCK)
    assert result == "satisfied"
    assert C.resolve_disposition(repo, commitment.id) == "satisfied"
    # Idempotent: satisfying again does not reopen an obligation.
    assert C.satisfy_single_check(repo, commitment_id=commitment.id, clock=CLOCK) == "satisfied"


def test_pause_resume_retire_disposition(repo):
    commitment = _create(repo, action="help_me_remember")
    assert commitment.disposition == "active"
    assert C.pause(repo, commitment_id=commitment.id, clock=CLOCK) == "paused"
    assert C.resume(repo, commitment_id=commitment.id, clock=CLOCK) == "active"
    assert C.retire(repo, commitment_id=commitment.id, clock=CLOCK) == "stopped"


def test_reference_only_disposition_change(repo):
    commitment = _create(repo)
    assert (
        C.change_disposition(repo, commitment_id=commitment.id, disposition="reference_only", clock=CLOCK)
        == "reference_only"
    )
