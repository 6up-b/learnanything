"""P1 step 8 -- angle progression, family evidence caps, lapse/retry episodes
(§4.3, §5.4, §5.5; §9.2, §9.3)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import activities as A
from learnloop.services import familiarity as F
from learnloop.services import progression as P
from learnloop.services import progression_policy as PP

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _family_version_with_policy(repo, *, coordinates):
    family_id = repo.ensure_activity_family(purpose="practice", legacy_kind=None, title="fam", clock=CLOCK)
    policy_id = PP.ensure_default_progression_policy(repo, clock=CLOCK)
    fv = A.author_family_version(
        repo, family_id=family_id, version=1, authoring_purpose="practice",
        family_spec={"title": "fam"}, progression_policy_version_id=policy_id, clock=CLOCK,
    )
    repo.insert_angle_inventory(family_version_id=fv, coordinates_json=A._json(coordinates), clock=CLOCK)
    return fv


def _surface(repo, *, suffix, features=None):
    family_id = repo.ensure_activity_family(purpose="practice", legacy_kind=None, title=f"f-{suffix}", clock=CLOCK)
    card_id = repo.ensure_activity_card(family_id=family_id, clock=CLOCK)
    cv = repo.ensure_activity_card_version(card_id=card_id, version=1,
        card_contract_hash=A._canonical_hash({"s": suffix}), contract_json="{}", schema_version=1, clock=CLOCK)
    sid = repo.ensure_activity_surface(card_version_id=cv, surface_hash=f"sh-{suffix}",
                                       fingerprint=None, surface_json="{}", clock=CLOCK)
    if features is not None:
        F.record_soft_features(repo, surface_id=sid, features=features, clock=CLOCK)
    return sid


# --- §5.4 orthogonal-next ------------------------------------------------------

def test_next_growth_activity_is_delayed_orthogonal_not_near_clone(repo):
    fv = _family_version_with_policy(repo, coordinates={
        "cue_direction": ["forward", "backward"],
        "representation": ["symbolic", "verbal"],
    })
    growth = P.next_growth_activity(repo, family_version_id=fv,
                                    current_angle={"cue_direction": "forward", "representation": "symbolic"},
                                    current_context="original")
    assert growth.angle_progression == "delayed_orthogonal"
    assert growth.changed_axis is not None  # advanced an orthogonal axis
    assert growth.next_angle != {"cue_direction": "forward", "representation": "symbolic"}
    assert not growth.is_near_clone
    assert growth.delay_days == PP.ORTHOGONAL_NEXT_DELAY_DAYS
    assert growth.context_fade_next == "altered_stripped_cold"


def test_sibling_propagation_never_marks_reviewed_or_grants_group(repo):
    fv = _family_version_with_policy(repo, coordinates={"cue_direction": ["forward", "backward"]})
    growth = P.next_growth_activity(repo, family_version_id=fv, current_angle={"cue_direction": "forward"})
    sib = growth.sibling_propagation
    assert sib["family_stage_prior_only"] is True
    assert sib["marks_sibling_reviewed"] is False
    assert sib["grants_independent_group"] is False
    assert 0 < sib["shrinkage"] < 1
    # B8: drive the actual (non-)write path, not just the descriptor. next_growth_activity
    # is pure w.r.t. sibling state -- computing the growth activity marks NO sibling
    # reviewed and grants NO independent evidence, so no card-state or exposure/review
    # rows exist afterward (the strongly-shrunk family-stage prior is applied by the
    # caller, never by this projection).
    with repo.connection() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM activity_card_state").fetchone()["n"] == 0
        assert conn.execute("SELECT COUNT(*) AS n FROM activity_exposure_events").fetchone()["n"] == 0


# --- §4.3 family evidence cap --------------------------------------------------

def test_tight_cluster_is_one_independent_group(repo):
    # Two strongly-kin surfaces (high shared warmth) collapse to ONE independent group;
    # variants from one family cannot certify by multiplying (§4.3).
    feats = {"target_facet_overlap": 3.0, "recipe_overlap": 3.0, "semantic_similarity": 3.0}
    a = _surface(repo, suffix="a", features=feats)
    b = _surface(repo, suffix="b", features=feats)
    cap = P.apply_evidence_cap(repo, surface_ids=[a, b])
    assert cap.independent_group_count == 1
    assert len(cap.clusters) == 1


def test_distant_surfaces_are_separate_groups(repo):
    a = _surface(repo, suffix="c", features={"target_facet_overlap": 0.0})
    b = _surface(repo, suffix="d", features={"target_facet_overlap": 0.0})
    cap = P.apply_evidence_cap(repo, surface_ids=[a, b])
    assert cap.independent_group_count == 2


def test_additional_administrations_add_diminishing_mass(repo):
    feats = {"target_facet_overlap": 3.0, "recipe_overlap": 3.0, "semantic_similarity": 3.0}
    two = [_surface(repo, suffix=f"e{i}", features=feats) for i in range(2)]
    cap_two = P.apply_evidence_cap(repo, surface_ids=two)
    six = two + [_surface(repo, suffix=f"g{i}", features=feats) for i in range(4)]
    cap_six = P.apply_evidence_cap(repo, surface_ids=six)
    # All one tight cluster; extra administrations add diminishing mass, never a new group.
    assert cap_two.independent_group_count == cap_six.independent_group_count == 1
    assert cap_six.effective_mass <= cap_six.max_effective_mass
    assert cap_two.effective_mass < cap_six.effective_mass < len(six)
    # The extra four administrations added far less than four units of mass.
    assert cap_six.effective_mass - cap_two.effective_mass < 1.0


def test_evidence_cap_reads_policy_row(repo):
    policy_id = P.ensure_default_evidence_cap_policy(repo, clock=CLOCK)
    assert repo.family_evidence_cap_policy(policy_id) is not None
    a = _surface(repo, suffix="f", features={"target_facet_overlap": 0.0})
    cap = P.apply_evidence_cap(repo, surface_ids=[a], cap_policy_id=policy_id)
    assert cap.max_effective_mass == P.MAX_EFFECTIVE_MASS_PER_CLUSTER


# --- §5.5 lapse + linked retry -------------------------------------------------

def test_lapse_retry_preserves_original_and_does_not_stack(repo):
    lineage = repo.create_card_lineage(clock=CLOCK)
    episode_id = P.open_lapse_episode(repo, card_lineage_id=lineage, opened_administration_id="adm-1", clock=CLOCK)
    ep = repo.lapse_episode(episode_id)
    assert ep["status"] == "open" and ep["followup_due_at"] is not None
    P.link_retry(repo, episode_id=episode_id, observation={"outcome": "wrong"}, derived_retrievability=0.3, clock=CLOCK)
    P.link_retry(repo, episode_id=episode_id, observation={"outcome": "partial"}, derived_retrievability=0.5, clock=CLOCK)
    ep = repo.lapse_episode(episode_id)
    import json
    retries = json.loads(ep["retry_observations_json"])
    assert len(retries) == 2  # linked, never overwriting the original failure
    assert ep["derived_retrievability"] == 0.5  # updated, not stacked into new evidence


def test_give_up_closes_and_preserves_retries(repo):
    lineage = repo.create_card_lineage(clock=CLOCK)
    episode_id = P.open_lapse_episode(repo, card_lineage_id=lineage, clock=CLOCK)
    P.link_retry(repo, episode_id=episode_id, observation={"outcome": "wrong"}, clock=CLOCK)
    ep = P.give_up(repo, episode_id=episode_id, clock=CLOCK)
    assert ep["status"] == "given_up" and ep["closed_at"] is not None
    import json
    assert len(json.loads(ep["retry_observations_json"])) == 1
    # A retry on a closed episode is a no-op (does not resurrect it).
    P.link_retry(repo, episode_id=episode_id, observation={"outcome": "again"}, clock=CLOCK)
    assert repo.lapse_episode(episode_id)["status"] == "given_up"
