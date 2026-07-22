"""P1 step 6 -- namespaced hard groups, soft-kinship, familiarity_projection_v1
(§4.1, §4.2, §4.3, §9.3; standing rules 5 & 7; owner decision A.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import activities as A
from learnloop.services import familiarity as F

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _surface(repo, *, hash_suffix, purpose="practice"):
    family_id = repo.ensure_activity_family(purpose=purpose, legacy_kind=None, title=f"f-{hash_suffix}", clock=CLOCK)
    card_id = repo.ensure_activity_card(family_id=family_id, clock=CLOCK)
    contract = {"target": "svd", "capability": "retrieval"}
    cv = repo.ensure_activity_card_version(
        card_id=card_id, version=1, card_contract_hash=A._canonical_hash({**contract, "s": hash_suffix}),
        contract_json=A._json(contract), schema_version=1, clock=CLOCK,
    )
    return repo.ensure_activity_surface(
        card_version_id=cv, surface_hash=f"sh-{hash_suffix}", fingerprint=None, surface_json="{}", clock=CLOCK,
    )


def _expose(repo, surface_id, *, purpose="practice"):
    repo.append_exposure_event(
        surface_id=surface_id, administration_id=None, surface_hash=f"exp-{surface_id}",
        fingerprint=None, kind="rendered", purpose=purpose, consumes_unseen=False, clock=CLOCK,
    )


# --- §4.1: namespaces never collide ------------------------------------------

def test_equal_values_in_different_namespaces_do_not_collide(repo):
    a = _surface(repo, hash_suffix="a")
    b = _surface(repo, hash_suffix="b")
    F.record_memberships(repo, surface_id=a, memberships=[{"namespace": "source_example", "value_hash": "svd-1"}], clock=CLOCK)
    F.record_memberships(repo, surface_id=b, memberships=[{"namespace": "solution_recipe", "value_hash": "svd-1"}], clock=CLOCK)
    assert repo.surfaces_sharing_membership(namespace="source_example", value_hash="svd-1") == [a]
    assert repo.surfaces_sharing_membership(namespace="solution_recipe", value_hash="svd-1") == [b]


def test_all_hard_memberships_considered_not_just_first(repo):
    a = _surface(repo, hash_suffix="a")
    b = _surface(repo, hash_suffix="b")
    # a belongs to TWO hard groups; b shares only the second.
    F.record_memberships(repo, surface_id=a, memberships=[
        {"namespace": "shared_stimulus", "value_hash": "stim-1"},
        {"namespace": "verbatim_target", "value_hash": "vt-1"},
    ], clock=CLOCK)
    F.record_memberships(repo, surface_id=b, memberships=[{"namespace": "verbatim_target", "value_hash": "vt-1"}], clock=CLOCK)
    _expose(repo, b)
    fam = F.familiarity_projection_v1(repo, surface_id=a)
    namespaces = {c.namespace for c in fam.hard_collisions}
    assert "verbatim_target" in namespaces  # the shared group is found, not the first field only


# --- §4.1: missing fingerprint -> unknown, never novel -----------------------

def test_missing_fingerprint_is_unknown_not_novel(repo):
    a = _surface(repo, hash_suffix="a")
    fam = F.familiarity_projection_v1(repo, surface_id=a)
    assert fam.exposure_status == "unknown"


def test_fingerprinted_but_unseen_is_novel(repo):
    a = _surface(repo, hash_suffix="a")
    F.record_memberships(repo, surface_id=a, memberships=[{"namespace": "surface_hash", "value_hash": "h-a"}], clock=CLOCK)
    fam = F.familiarity_projection_v1(repo, surface_id=a)
    assert fam.exposure_status == "novel"


# --- §9.3: cross-LO/purpose exposure visibility ------------------------------

def test_exposure_under_one_purpose_warms_hard_sibling_under_another(repo):
    a = _surface(repo, hash_suffix="a", purpose="practice")
    b = _surface(repo, hash_suffix="b", purpose="assessment")
    for sid in (a, b):
        F.record_memberships(repo, surface_id=sid, memberships=[{"namespace": "shared_stimulus", "value_hash": "stim"}], clock=CLOCK)
    _expose(repo, a, purpose="practice")
    # b (assessment) is warm because its hard sibling a (practice) was shown.
    fam_b = F.familiarity_projection_v1(repo, surface_id=b, purpose="assessment")
    assert fam_b.exposure_status == "warm"
    assert fam_b.blocks_unseen_claim is True


def test_hard_collision_blocks_unseen_claim(repo):
    a = _surface(repo, hash_suffix="a")
    b = _surface(repo, hash_suffix="b")
    for sid in (a, b):
        F.record_memberships(repo, surface_id=sid, memberships=[{"namespace": "verbatim_target", "value_hash": "vt"}], clock=CLOCK)
    _expose(repo, a)
    assert F.familiarity_projection_v1(repo, surface_id=b).blocks_unseen_claim is True


# --- §4.2: monotonicity ------------------------------------------------------

def test_warmth_is_monotone_in_exposure_features():
    base = {"exposure_count": 1.0, "recency": 0.5}
    more = {"exposure_count": 3.0, "recency": 0.9}
    assert F.warmth_score(more) >= F.warmth_score(base)
    # Adding a feature never decreases warmth (non-negative coefficients).
    assert F.warmth_score({**base, "recipe_overlap": 1.0}) >= F.warmth_score(base)
    assert 0.0 <= F.warmth_score(more) < 1.0


# --- §4.3 + A.4: tight-kinship clustering / evidence cap ---------------------

def test_tight_kinship_single_linkage_caps_independent_groups(repo):
    # Three near-identical surfaces (high overlap) cluster into ONE group.
    ids = []
    for suffix in ("a", "b", "c"):
        s = _surface(repo, hash_suffix=suffix)
        F.record_soft_features(repo, surface_id=s, features={
            "target_facet_overlap": 1.0, "recipe_overlap": 1.0, "semantic_similarity": 1.0,
        }, clock=CLOCK)
        ids.append(s)
    grouping = F.evidence_cap_grouping(repo, surface_ids=ids)
    assert grouping.independent_group_count == 1
    assert sorted(grouping.clusters[0]) == sorted(ids)


def test_distant_surfaces_stay_separate_groups(repo):
    s1 = _surface(repo, hash_suffix="x")
    s2 = _surface(repo, hash_suffix="y")
    F.record_soft_features(repo, surface_id=s1, features={"target_facet_overlap": 1.0}, clock=CLOCK)
    F.record_soft_features(repo, surface_id=s2, features={"angle_proximity": 0.0}, clock=CLOCK)
    grouping = F.evidence_cap_grouping(repo, surface_ids=[s1, s2])
    assert grouping.independent_group_count == 2


def test_clustering_is_deterministic(repo):
    ids = []
    for suffix in ("a", "b", "c"):
        s = _surface(repo, hash_suffix=suffix)
        F.record_soft_features(repo, surface_id=s, features={"recipe_overlap": 1.0, "semantic_similarity": 1.0}, clock=CLOCK)
        ids.append(s)
    first = F.tight_kinship_clusters(repo, surface_ids=ids)
    second = F.tight_kinship_clusters(repo, surface_ids=list(reversed(ids)))
    assert first == second


# --- U-033: tutor exposure propagation ---------------------------------------

def test_tutor_exposure_propagation_warms_and_degrades(repo):
    a = _surface(repo, hash_suffix="a")
    b = _surface(repo, hash_suffix="b")
    F.record_memberships(repo, surface_id=a, memberships=[{"namespace": "source_example", "value_hash": "ex-1"}], clock=CLOCK)
    out = F.propagate_tutor_exposure(
        repo,
        explanation_fingerprints=[{"surface_id": a, "namespace": "source_example", "value_hash": "ex-1"}],
        plausibly_touched_surface_ids=[b], clock=CLOCK,
    )
    assert out["degraded_to_unknown"] == [b]
    # b degraded to unknown, never silently novel.
    memberships = repo.fingerprint_memberships_for_surface(b)
    assert any(m["status"] == "unknown" for m in memberships)


# --- standing rule 5: salience is never learner evidence ---------------------

def test_familiarity_result_has_no_correctness_field():
    fields = set(F.Familiarity.__dataclass_fields__)
    for forbidden in ("correctness", "mastery", "evidence_credit", "score"):
        assert forbidden not in fields
    assert "correctness" not in F.AFFECTS


def test_belief_update_modules_do_not_consume_familiarity_warmth():
    """Static guard (rule 5): NO belief-update / certification / projection module may
    import the familiarity projection as a learner-knowledge signal. B8 widens this
    beyond mastery.py to every belief module (evidence, certification, mastery,
    canonical_projection) -- warmth is exposure salience, never evidence of knowledge."""

    src = Path(__file__).resolve().parents[1] / "src" / "learnloop" / "services"
    belief_modules = ("evidence.py", "certification.py", "mastery.py", "canonical_projection.py")
    for module in belief_modules:
        text = (src / module).read_text(encoding="utf-8")
        assert "familiarity_projection_v1" not in text, module
        assert "from learnloop.services.familiarity" not in text, module
        assert "import familiarity" not in text, module
