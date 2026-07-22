"""P1 step 3 -- family/card contract extensions + progression policy
(spec_p1_shared_substrate §3.6, §3.7, §9.1)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import activities as A
from learnloop.services import activity_patterns as AP
from learnloop.services import progression_policy as PP

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


@pytest.fixture
def seeded(repo):
    patterns = AP.ensure_builtin_patterns(repo, clock=CLOCK)
    policy_id = PP.ensure_default_progression_policy(repo, clock=CLOCK)
    family_id = repo.ensure_activity_family(purpose="practice", legacy_kind=None, title="fam", clock=CLOCK)
    return repo, patterns, policy_id, family_id


def _author(repo, family_id, patterns, policy_id, *, version=1, purpose="practice"):
    return A.author_family_version(
        repo,
        family_id=family_id,
        version=version,
        authoring_purpose=purpose,
        family_spec={"stage": version},
        pattern_version_id=patterns["minimal_retrieval"].id,
        progression_policy_version_id=policy_id,
        angle_inventory={"axes": ["cue_direction", "response_form"]},
        coverage_targets={"cue_direction": 2},
        clock=CLOCK,
    )


# --- §5.1 staged authoring is idempotent + leaves a draft --------------------

def test_authoring_is_idempotent_and_starts_as_draft(seeded):
    repo, patterns, policy_id, family_id = seeded
    fvid = _author(repo, family_id, patterns, policy_id)
    fvid2 = _author(repo, family_id, patterns, policy_id)
    assert fvid == fvid2  # re-run yields the same family_version_id
    authoring = repo.activity_family_authoring(fvid)
    assert authoring["status"] == "draft"  # no schedulable partial before activation
    A.activate_family_version(repo, family_version_id=fvid)
    assert repo.activity_family_authoring(fvid)["status"] == "active"


# --- §3.6 resolve progression policy -----------------------------------------

def test_resolve_progression_policy(seeded):
    repo, patterns, policy_id, family_id = seeded
    fvid = _author(repo, family_id, patterns, policy_id)
    body = A.resolve_progression_policy(repo, fvid)
    assert body is not None
    assert body["sibling_success_shrinkage"] == PP.SIBLING_SUCCESS_SHRINKAGE
    assert body["angle_progression"] == "delayed_orthogonal"


def test_inspect_angle_coverage(seeded):
    repo, patterns, policy_id, family_id = seeded
    fvid = _author(repo, family_id, patterns, policy_id)
    coverage = A.inspect_angle_coverage(repo, fvid)
    assert coverage["angle_inventory"]["axes"] == ["cue_direction", "response_form"]
    assert coverage["coverage_targets"] == {"cue_direction": 2}


# --- §9.1 family purpose cannot change in place ------------------------------

def test_family_purpose_immutable_in_place(seeded):
    repo, patterns, policy_id, family_id = seeded
    _author(repo, family_id, patterns, policy_id, purpose="practice")
    # Re-authoring the SAME stable family under a different purpose is refused;
    # cross-purpose reuse must create a separately gated family (§1.1 invariant 2).
    with pytest.raises(A.FamilyPurposeImmutable):
        A.author_family_version(
            repo, family_id=family_id, version=2, authoring_purpose="assessment",
            family_spec={}, clock=CLOCK,
        )


# --- §9.1 a cross-purpose link never reuses the same activity identity --------

def test_cross_purpose_link_rejects_self_identity(seeded):
    repo, patterns, policy_id, family_id = seeded
    fvid = _author(repo, family_id, patterns, policy_id)
    with pytest.raises(A.CrossPurposeIdentityReuse):
        A.link_cross_purpose_families(
            repo, family_version_id=fvid,
            links=[{"link_kind": "practices_for", "target_family_id": family_id}],
            clock=CLOCK,
        )


def test_cross_purpose_link_to_other_family(seeded):
    repo, patterns, policy_id, family_id = seeded
    fvid = _author(repo, family_id, patterns, policy_id)
    diag_family = repo.ensure_activity_family(
        purpose="diagnostic", legacy_kind=None, title="diag", clock=CLOCK
    )
    links = A.link_cross_purpose_families(
        repo, family_version_id=fvid,
        links=[{"link_kind": "diagnoses_for", "target_family_id": diag_family}],
        clock=CLOCK,
    )
    assert links == [{"link_kind": "diagnoses_for", "target_family_id": diag_family}]
    with pytest.raises(A.InvalidAuthoring):
        A.link_cross_purpose_families(
            repo, family_version_id=fvid,
            links=[{"link_kind": "not_a_kind", "target_family_id": diag_family}],
            clock=CLOCK,
        )


# --- §3.7 card authoring side row keyed by immutable P0 card version ----------

def test_pin_card_authoring(seeded):
    repo, patterns, policy_id, family_id = seeded
    fvid = _author(repo, family_id, patterns, policy_id)
    card_id = repo.ensure_activity_card(family_id=family_id, clock=CLOCK)
    card_version_id = repo.ensure_activity_card_version(
        card_id=card_id, version=1, card_contract_hash="h1", contract_json="{}",
        schema_version=1, clock=CLOCK,
    )
    A.pin_card_authoring(
        repo, card_version_id=card_version_id, family_version_id=fvid,
        capability="retrieval", surface_policy="rotating",
        task_features={"complexity": 2}, angle_identity={"cue_direction": "forward"},
        clock=CLOCK,
    )
    row = repo.activity_card_authoring(card_version_id)
    assert row["capability"] == "retrieval"
    assert row["surface_policy"] == "rotating"
    # The immutable P0 card version row is untouched (side-table extension, A.1).
    with pytest.raises(A.InvalidAuthoring):
        A.pin_card_authoring(repo, card_version_id=card_version_id, capability="bogus")
    with pytest.raises(A.InvalidAuthoring):
        A.pin_card_authoring(repo, card_version_id=card_version_id, surface_policy="teleporting")


def test_progression_policy_is_content_addressed(repo):
    a = PP.ensure_default_progression_policy(repo, clock=CLOCK)
    b = PP.ensure_default_progression_policy(repo, clock=CLOCK)
    assert a == b  # idempotent, content-addressed
