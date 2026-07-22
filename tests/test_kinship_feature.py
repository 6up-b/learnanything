"""P4 step 5 (descoped, U-026) -- the heuristic LLM-judged soft-kinship feature behind
its sim admission gate (spec_p4 §8, §16.4; design §B step 5, §F).

Covers the firewall (computed + logged, consulted by NOTHING -- even after admission,
throughout P4); no current-correctness input (16.4); out-of-scope -> P1 fallback, never
zero (§8.4); the kernel cannot override a hard collision (16.4); and the sim admission
gate promoting only to ``simulation_validated`` while emitting the U-022
promotion-evidence artifact through the registry machinery.
"""

from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import activities as A
from learnloop.services import familiarity
from learnloop.services import kinship_feature as kf
from learnloop.services import parameter_registry as pr
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)


@pytest.fixture
def wired(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    pr.refresh(vault, repo, clock=CLOCK)
    return vault, repo


def _seed_surface(repo, suffix, features, memberships=()):
    family_id = repo.ensure_activity_family(purpose="practice", legacy_kind=None,
                                            title=f"f-{suffix}", clock=CLOCK)
    card_id = repo.ensure_activity_card(family_id=family_id, clock=CLOCK)
    contract = {"target": "svd", "capability": "retrieval"}
    cv = repo.ensure_activity_card_version(
        card_id=card_id, version=1,
        card_contract_hash=A._canonical_hash({**contract, "s": suffix}),
        contract_json=A._json(contract), schema_version=1, clock=CLOCK,
    )
    surface_id = repo.ensure_activity_surface(
        card_version_id=cv, surface_hash=f"sh-{suffix}", fingerprint=None,
        surface_json="{}", clock=CLOCK,
    )
    familiarity.record_soft_features(repo, surface_id=surface_id, features=features, clock=CLOCK)
    for m in memberships:
        familiarity.record_memberships(repo, surface_id=surface_id, memberships=[m], clock=CLOCK)
    return surface_id


def test_feature_conditions_only_on_pre_administration_info(wired):
    _, repo = wired
    sa = _seed_surface(repo, "a", {"target_facet_overlap": 1.0, "recipe_overlap": 1.0})
    sb = _seed_surface(repo, "b", {"target_facet_overlap": 1.0, "recipe_overlap": 1.0})
    score = kf.score_kinship(repo, subject_surface_id=sa, kin_surface_id=sb, clock=CLOCK)
    assert score.in_scope
    # 16.4: current correctness is NOT a feature. No correctness/outcome key anywhere.
    blob = json.dumps(score.conditioned_on).lower()
    for banned in ("correct", "outcome", "response_grade", "is_correct"):
        assert banned not in blob
    assert score.conditioned_on["information_horizon"] == "pre_administration"


def test_firewall_feature_is_consulted_by_nothing_even_after_admission(wired):
    _, repo = wired
    sa = _seed_surface(repo, "a", {"target_facet_overlap": 1.0, "recipe_overlap": 1.0})
    sb = _seed_surface(repo, "b", {"target_facet_overlap": 1.0, "recipe_overlap": 1.0})
    model_id = kf.ensure_model(repo, clock=CLOCK)
    # A strongly warm pair -> the feature WOULD prefer a big discount if consulted.
    kf.score_kinship(repo, subject_surface_id=sa, kin_surface_id=sb,
                     model_id=model_id, clock=CLOCK)
    p1 = 0.9
    # Before admission: consulted value is exactly P1's conservative discount.
    assert kf.consulted_discount(
        repo, subject_surface_id=sa, kin_surface_id=sb,
        p1_conservative_discount=p1, model_id=model_id,
    ) == p1
    # Admit the model (simulation_validated). Firewall STILL holds throughout P4:
    # simulation_validated is shadow; LIVE_ACTIVATION_ENABLED is OFF (§8.4/§17).
    assert kf.run_admission_gate(repo, model_id=model_id, clock=CLOCK).admitted
    assert kf.is_admitted(repo, model_id=model_id)
    assert kf.LIVE_ACTIVATION_ENABLED is False
    assert kf.consulted_discount(
        repo, subject_surface_id=sa, kin_surface_id=sb,
        p1_conservative_discount=p1, model_id=model_id,
    ) == p1


def test_firewall_does_real_work_warm_pair_would_move_discount_if_enabled(wired, monkeypatch):
    # Audit L9: the firewall test must show the feature WOULD change the discount if the
    # (hypothetical) live activation were on -- otherwise "consulted by nothing" is vacuous.
    # Contrast the two paths on the SAME strongly-warm pair: production keeps P1 exactly
    # (firewall intact), while a monkeypatched LIVE_ACTIVATION_ENABLED yields a discount
    # strictly below P1 (the feature moves it). The production path is re-asserted intact
    # after the contrast.
    _, repo = wired
    sa = _seed_surface(repo, "a", {"target_facet_overlap": 1.0, "recipe_overlap": 1.0})
    sb = _seed_surface(repo, "b", {"target_facet_overlap": 1.0, "recipe_overlap": 1.0})
    model_id = kf.ensure_model(repo, clock=CLOCK)
    score = kf.score_kinship(repo, subject_surface_id=sa, kin_surface_id=sb,
                             model_id=model_id, clock=CLOCK)
    assert kf.run_admission_gate(repo, model_id=model_id, clock=CLOCK).admitted
    p1 = 0.9
    # The cached feature itself carries a discount below P1 for this warm pair.
    assert score.discount_lo < p1

    # Production firewall path: P1 exactly, regardless of the admitted feature.
    assert kf.consulted_discount(repo, subject_surface_id=sa, kin_surface_id=sb,
                                 p1_conservative_discount=p1, model_id=model_id) == p1

    # Hypothetically-enabled path (never on in P4): the feature moves the discount below P1.
    monkeypatch.setattr(kf, "LIVE_ACTIVATION_ENABLED", True)
    enabled = kf.consulted_discount(repo, subject_surface_id=sa, kin_surface_id=sb,
                                    p1_conservative_discount=p1, model_id=model_id)
    assert enabled < p1

    # Firewall re-asserted intact once the hypothetical flag is off again.
    monkeypatch.setattr(kf, "LIVE_ACTIVATION_ENABLED", False)
    assert kf.consulted_discount(repo, subject_surface_id=sa, kin_surface_id=sb,
                                 p1_conservative_discount=p1, model_id=model_id) == p1


def test_out_of_scope_falls_back_to_p1_never_zero(wired):
    _, repo = wired
    # No soft features recorded -> out of scope -> P1 conservative, never zero (§8.4).
    score = kf.score_kinship(
        repo, subject_surface_id="sX", kin_surface_id=None,
        p1_conservative_discount=0.9, clock=CLOCK,
    )
    assert not score.in_scope
    assert score.discount_lo == 0.9 and score.discount_hi == 0.9
    assert score.discount_lo > 0.0


def test_kernel_cannot_override_a_hard_collision(wired):
    _, repo = wired
    # Two surfaces in the SAME hard group (shared_stimulus) -> P1 authority, out of scope.
    ha = _seed_surface(repo, "ha", {"target_facet_overlap": 1.0},
                       memberships=[{"namespace": "shared_stimulus", "value_hash": "same"}])
    hb = _seed_surface(repo, "hb", {"target_facet_overlap": 1.0},
                       memberships=[{"namespace": "shared_stimulus", "value_hash": "same"}])
    score = kf.score_kinship(repo, subject_surface_id=ha, kin_surface_id=hb, clock=CLOCK)
    assert not score.in_scope
    assert score.artifact["out_of_scope"] == "hard_collision_is_p1_authority"


def test_admission_emits_u022_promotion_evidence_and_only_reaches_sim_validated(wired):
    _, repo = wired
    model_id = kf.ensure_model(repo, clock=CLOCK)
    outcome = kf.run_admission_gate(repo, model_id=model_id, clock=CLOCK)
    assert outcome.admitted and outcome.evidence_id
    # Status advanced only to simulation_validated (a sim cannot go further, §8.4).
    row = kf.model_row(repo, model_id)
    assert row["status"] == "simulation_validated"
    assert row["admission_evidence_id"] == outcome.evidence_id
    # The U-022 promotion-evidence artifact is a real registry certificate row, and it
    # promoted the admission-threshold parameter to simulation_validated.
    entry = repo.parameter_registry_entry(kf.ADMISSION_PARAM_PATH)
    assert entry["status"] == "simulation_validated"
    assert entry["promotion_evidence_id"] == outcome.evidence_id
    certs = repo.sensitivity_certificates_for_path(kf.ADMISSION_PARAM_PATH)
    assert any(c["id"] == outcome.evidence_id and c["decision_stable"] for c in certs)


def test_admission_refuses_when_feature_does_not_move_the_discount(wired):
    _, repo = wired
    model_id = kf.ensure_model(repo, clock=CLOCK)

    class _FlatSim:
        moves_discount_correctly = False
        results: list = []

        def as_dict(self):
            return {"moves_discount_correctly": False}

    outcome = kf.run_admission_gate(repo, model_id=model_id, sim_report=_FlatSim(), clock=CLOCK)
    assert not outcome.admitted
    assert outcome.reason == "feature_did_not_move_discount"
    assert kf.model_row(repo, model_id)["status"] == "shadow"


def test_null_kin_self_feature_is_deduped(wired):
    # Audit L2/D6: the subject-only (kin_surface_id IS NULL) feature must be cached at most
    # once per (model, subject). Pre-fix the table UNIQUE treated NULLs as distinct, so a
    # re-score duplicated the self feature; the partial unique index (migration 101) makes
    # INSERT OR REPLACE collapse it.
    _, repo = wired
    sa = _seed_surface(repo, "a", {"target_facet_overlap": 1.0, "recipe_overlap": 1.0})
    model_id = kf.ensure_model(repo, clock=CLOCK)
    kf.score_kinship(repo, subject_surface_id=sa, kin_surface_id=None, model_id=model_id, clock=CLOCK)
    kf.score_kinship(repo, subject_surface_id=sa, kin_surface_id=None, model_id=model_id, clock=CLOCK)
    with repo.connection() as conn:
        rows = conn.execute(
            "SELECT COUNT(*) AS n FROM familiarity_kernel_features "
            "WHERE model_id = ? AND subject_surface_id = ? AND kin_surface_id IS NULL",
            (model_id, sa),
        ).fetchone()
    assert rows["n"] == 1
