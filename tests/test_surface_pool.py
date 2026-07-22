"""P2 PRACTICE track -- the rotating practice pool (spec_p2 §7.3, U-028, §12.4;
design B.7)."""

from __future__ import annotations

import pytest

from learnloop.db.repositories import Repository
from learnloop.services import familiarity as F
from learnloop.services import surface_pool as SP
from learnloop.services.activities import (
    ExposureCollisionAtRender,
    append_exposure,
    open_administration,
    reserve_surface,
    resolve_legacy_item,
)
from learnloop.services.golden_path_fixture import (
    EXEMPLAR_A,
    EXEMPLAR_B,
    HELD_OUT,
    build_golden_path_fixture,
    stub_pool_surfaces,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path / "vault"
    fx = build_golden_path_fixture(root)
    vault = load_vault(root)
    repo = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return vault, repo, fx


def _resolve(vault, repo, item_id, purpose):
    item = vault.practice_items[item_id]
    return resolve_legacy_item(vault, repo, item, purpose=purpose)


def _assemble_two(vault, repo, fx, *, admit=True):
    """A two-surface pool over EXEMPLAR_A / EXEMPLAR_B resolved as practice surfaces."""

    ra = _resolve(vault, repo, EXEMPLAR_A, "practice")
    rb = _resolve(vault, repo, EXEMPLAR_B, "practice")
    pool = SP.assemble_pool(
        repo, pool_slug="pool_two", blueprint_version_id=fx.blueprint_version_id,
        surfaces=[
            {"surface_slug": "surf_a", "angle": "setup_only"},
            {"surface_slug": "surf_b", "angle": "move_spotting"},
        ],
    )
    if admit:
        SP.admit_pool_surface(repo, pool_id=pool.pool_id, surface_slug="surf_a", surface_id=ra.surface_id)
        SP.admit_pool_surface(repo, pool_id=pool.pool_id, surface_slug="surf_b", surface_id=rb.surface_id)
    return pool, ra, rb


# ---------------------------------------------------------------------------
# U-028 admission provenance.
# ---------------------------------------------------------------------------

def test_pool_assembly_deterministic(fixture):
    vault, repo, fx = fixture
    stub = stub_pool_surfaces()
    p1 = SP.assemble_pool(repo, pool_slug=stub["pool_slug"], blueprint_version_id=fx.blueprint_version_id, surfaces=stub["surfaces"])
    p2 = SP.assemble_pool(repo, pool_slug=stub["pool_slug"], blueprint_version_id=fx.blueprint_version_id, surfaces=stub["surfaces"])
    assert p1.content_hash == p2.content_hash
    assert p1.pool_id == p2.pool_id
    assert p1.minted is True and p2.minted is False


def test_surfaces_enter_candidate_and_review_requires_admission(fixture):
    vault, repo, fx = fixture
    pool, _ra, _rb = _assemble_two(vault, repo, fx, admit=False)
    assert all(s.admission_status == "candidate" for s in pool.surfaces)
    with pytest.raises(SP.InvalidPool):
        SP.review_pool(repo, pool_id=pool.pool_id)
    ra = _resolve(vault, repo, EXEMPLAR_A, "practice")
    rb = _resolve(vault, repo, EXEMPLAR_B, "practice")
    SP.admit_pool_surface(repo, pool_id=pool.pool_id, surface_slug="surf_a", surface_id=ra.surface_id)
    SP.admit_pool_surface(repo, pool_id=pool.pool_id, surface_slug="surf_b", surface_id=rb.surface_id)
    reviewed = SP.review_pool(repo, pool_id=pool.pool_id)
    assert reviewed.status == "reviewed"
    kinds = [e["kind"] for e in repo.practice_pool_events_for(pool.pool_id)]
    assert kinds.count("admitted") == 2 and "reviewed" in kinds and "registered" in kinds


def test_unadmitted_candidate_is_never_served(fixture):
    vault, repo, fx = fixture
    pool, _ra, _rb = _assemble_two(vault, repo, fx, admit=False)
    selection = SP.next_practice_surface(repo, pool_id=pool.pool_id)
    # Nothing admitted -> nothing served (candidates never serve, U-028).
    assert selection.current is None and selection.fallback is True


# ---------------------------------------------------------------------------
# §12.4 role protection + assessment-reserve collision.
# ---------------------------------------------------------------------------

def test_purpose_specific_family_cannot_transition_roles(fixture):
    vault, repo, fx = fixture
    pool, _ra, _rb = _assemble_two(vault, repo, fx, admit=False)
    assessment = _resolve(vault, repo, HELD_OUT, "assessment")
    # An assessment-purpose surface can never be admitted into a practice pool (§12.4).
    with pytest.raises(SP.InvalidPool):
        SP.admit_pool_surface(repo, pool_id=pool.pool_id, surface_slug="surf_a", surface_id=assessment.surface_id)


def test_assessment_reserved_surface_is_refused_at_admission(fixture):
    vault, repo, fx = fixture
    pool, _ra, _rb = _assemble_two(vault, repo, fx, admit=False)
    # A practice surface that hard-collides (same surface_hash) with the reserved
    # assessment surface is refused before it enters the candidate set (§7.3).
    practice_heldout = _resolve(vault, repo, HELD_OUT, "practice")
    with pytest.raises(SP.InvalidPool):
        SP.admit_pool_surface(
            repo, pool_id=pool.pool_id, surface_slug="surf_a",
            surface_id=practice_heldout.surface_id,
            assessment_surface_id=fx.assessment_surface_id,
        )


# ---------------------------------------------------------------------------
# §7.3 rotation -- one current + one cached spare, lazy after warmth.
# ---------------------------------------------------------------------------

def test_current_plus_spare_cache_is_bounded(fixture):
    vault, repo, fx = fixture
    rc = _resolve(vault, repo, HELD_OUT, "practice")
    pool, _ra, _rb = _assemble_two(vault, repo, fx)
    SP.assemble_pool(repo, pool_slug="pool_two", blueprint_version_id=fx.blueprint_version_id,
                     surfaces=[{"surface_slug": "surf_c", "angle": "transfer"}])
    SP.admit_pool_surface(repo, pool_id=pool.pool_id, surface_slug="surf_c", surface_id=rc.surface_id)
    selection = SP.next_practice_surface(repo, pool_id=pool.pool_id)
    assert selection.current is not None
    # POOL_SPARE_CACHE == 1: exactly one spare cached beyond current, never the third.
    assert SP.POOL_SPARE_CACHE == 1
    assert selection.spare is not None
    assert selection.current.surface_id != selection.spare.surface_id


def test_lazy_rotation_fires_after_warmth(fixture):
    vault, repo, fx = fixture
    pool, ra, rb = _assemble_two(vault, repo, fx)
    # Front surface fresh -> served as current, no rotation.
    first = SP.next_practice_surface(repo, pool_id=pool.pool_id)
    assert first.current.surface_id == ra.surface_id and first.rotated is False
    # Warm the front surface past the rotation threshold -> rotate to the spare (§7.3).
    F.record_soft_features(repo, surface_id=ra.surface_id, features={"exposure_count": 5.0, "recency": 3.0})
    rotated = SP.next_practice_surface(repo, pool_id=pool.pool_id)
    assert rotated.rotated is True
    assert rotated.current.surface_id == rb.surface_id


def test_next_practice_surface_writes_served_and_rotated_ledger_events(fixture):
    """§7.3 (L2 regression): serving a surface appends a ``served`` pool event, and a
    rotation appends a ``rotated`` event too -- ``pool_status`` shows the history.

    Before the fix ``next_practice_surface`` wrote no ledger event, so the served /
    rotated rotation history was invisible to ``pool_status``."""

    vault, repo, fx = fixture
    pool, ra, rb = _assemble_two(vault, repo, fx)

    SP.next_practice_surface(repo, pool_id=pool.pool_id)
    kinds = [e["kind"] for e in SP.pool_status(repo, pool_id=pool.pool_id)["events"]]
    assert kinds.count("served") == 1
    assert "rotated" not in kinds  # no rotation on the first, fresh serve

    # Warm the front surface past threshold -> rotation fires -> both events land.
    F.record_soft_features(repo, surface_id=ra.surface_id, features={"exposure_count": 5.0, "recency": 3.0})
    rotated = SP.next_practice_surface(repo, pool_id=pool.pool_id)
    assert rotated.rotated is True
    events = SP.pool_status(repo, pool_id=pool.pool_id)["events"]
    kinds = [e["kind"] for e in events]
    assert kinds.count("served") == 2 and kinds.count("rotated") == 1
    # The served event carries the served surface's id + freshness flags.
    served_events = [e for e in events if e["kind"] == "served"]
    import json as _json
    detail = _json.loads(served_events[-1]["detail_json"])
    assert detail["surface"]["surface_id"] == rb.surface_id
    assert "fresh" in detail["surface"] and "warmth" in detail["surface"]


def test_familiar_practice_is_never_reported_fresh(fixture):
    vault, repo, fx = fixture
    pool, ra, _rb = _assemble_two(vault, repo, fx)
    # A surface with no fingerprint ledger is 'unknown', never fresh (§7.3).
    served = SP.next_practice_surface(repo, pool_id=pool.pool_id).current
    assert served.fresh is False and served.reduced_evidence is True
    # After a fingerprint + exposure it is 'warm' -> still never fresh.
    surface = repo.fetch_surface(ra.surface_id)
    F.record_memberships(repo, surface_id=ra.surface_id,
                         memberships=[{"namespace": "shared_stimulus", "value_hash": "vh_shared"}])
    append_exposure(repo, surface=surface, administration_id=None, kind="rendered", purpose="practice")
    fam = F.familiarity_projection_v1(repo, surface_id=ra.surface_id, purpose="practice")
    assert fam.exposure_status == "warm"
    # The now-warm surface is still never reported as fresh evidence.
    warm_served = SP.next_practice_surface(repo, pool_id=pool.pool_id, warmth_threshold=0.99).current
    assert warm_served.fresh is False


# ---------------------------------------------------------------------------
# §12.4 leakage -- practice exposure invalidates the assessment reserve.
# ---------------------------------------------------------------------------

def test_practice_exposure_invalidates_same_fingerprint_assessment_reserve(fixture):
    vault, repo, fx = fixture
    # Resolve an unreserved sibling under BOTH purposes: identical surface_hash /
    # fingerprint, distinct surface rows (shared ledger blocks manufactured novelty).
    practice = _resolve(vault, repo, EXEMPLAR_B, "practice")
    assessment = _resolve(vault, repo, EXEMPLAR_B, "assessment")
    assert practice.surface_id != assessment.surface_id
    assert practice.surface_hash == assessment.surface_hash

    # Administer the practice surface -> a rendered exposure lands in the ONE ledger.
    admin = SP.open_practice(repo, resolved=practice, goal_id="g_leak")
    assert admin.surface_id == practice.surface_id

    # The same-fingerprint assessment reserve is now refused BEFORE render (§8.1/§12.4).
    with pytest.raises(ExposureCollisionAtRender):
        reservation = reserve_surface(repo, surface_id=assessment.surface_id, purpose="assessment", goal_id="g_leak")
        open_administration(repo, resolved=assessment, reservation=reservation, goal_id="g_leak")


# ---------------------------------------------------------------------------
# §12.4 / §12.8 generator outage does not corrupt an in-flight response.
# ---------------------------------------------------------------------------

def test_generator_outage_does_not_block_in_flight_practice(fixture):
    vault, repo, fx = fixture
    pool, ra, _rb = _assemble_two(vault, repo, fx)
    # Enqueue a spare pre-mint but run NO worker (generator outage).
    request_id = SP.request_spare_mint(repo, card_version_id=ra.card_version_id, anchor_surface_id=ra.surface_id)
    assert request_id
    # The learner may still consolidate on an admitted familiar surface -- serving
    # never blocks on the pending mint (§12.4 generator outage, §12.8 off hot path).
    selection = SP.next_practice_surface(repo, pool_id=pool.pool_id)
    assert selection.current is not None
