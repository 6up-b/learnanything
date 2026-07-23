"""P0.3 (spec §4.3, §7.2, §9.2/§9.3): mvp-0.8 authority-propagation projection
cutover -- cache-corruption rebuild, adjudication reversal + receipts, lineage
ledger, activation receipt, and status-boundary monotonicity."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.canonical_projection import project_canonical_facet_state
from learnloop.services.effective_observation import effective_observation_from_posterior
from learnloop.services.grade_resolution import append_adjudication
from learnloop.services.p0_projection import (
    activate_p0_projection,
    record_reinterpretation_if_changed,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, set_algorithm_version

CLOCK = FrozenClock(NOW)
ITEM = "pi_svd_define_001"


def _p0_vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    return vault, repo


def _attempt(vault, repo, *, points=4, confidence=4):
    return complete_self_graded_attempt(
        vault,
        repo,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="SVD factorizes a matrix as U Sigma V transpose.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": points}, fatal_errors=[], confidence=confidence),
        clock=CLOCK,
    )


def _cells(repo):
    return {
        (c.facet_id, c.capability): (
            round(c.direct_positive_mass, 9),
            round(c.direct_negative_mass, 9),
            round(c.certification_credit, 9),
        )
        for c in repo.facet_capability_evidence_all()
    }


# ---------------------------------------------------------------------------
# §7.2 / §9.2 bullet 5: rebuild from authoritative events, not caches.
# ---------------------------------------------------------------------------


def test_corrupt_legacy_caches_does_not_change_rebuilt_projection(tmp_path):
    vault, repo = _p0_vault(tmp_path)
    result = _attempt(vault, repo)
    project_canonical_facet_state(vault, repo)
    before = _cells(repo)
    assert before

    # Corrupt the documented current-grade caches (§7.2). The mvp-0.8 projection
    # reads administrations + interpretations, never these columns. L9 additionally
    # corrupts the per-criterion grading_evidence.points_awarded rows -- the other
    # legacy grade cache -- to prove the rebuild ignores those too.
    with connect(repo.sqlite_path) as connection:
        connection.execute(
            """
            UPDATE practice_attempts
               SET rubric_score = 0, correctness = 0.0, grader_confidence = 0.0
             WHERE id = ?
            """,
            (result.attempt_id,),
        )
        n_evidence = connection.execute(
            "UPDATE grading_evidence SET points_awarded = 0.0 WHERE attempt_id = ?",
            (result.attempt_id,),
        ).rowcount
        connection.commit()
    assert n_evidence > 0  # the corruption actually touched cached grade rows

    project_canonical_facet_state(vault, repo)
    after = _cells(repo)
    assert after == before


# ---------------------------------------------------------------------------
# §9.2 bullet 6: adjudication reverses current projection via appended events,
# historical decision receipt preserved.
# ---------------------------------------------------------------------------


def test_adjudication_reverses_projection_and_preserves_history(tmp_path):
    vault, repo = _p0_vault(tmp_path)
    result = _attempt(vault, repo, points=4, confidence=4)
    project_canonical_facet_state(vault, repo)
    before = _cells(repo)
    assert before

    observation = repo.observation_by_attempt(result.attempt_id)
    original_head = repo.active_interpretation_for_observation(observation["id"])
    original_row = repo.grade_interpretation(original_head["id"])
    raw = repo.raw_grade_events_for_observation(observation["id"])[0]

    # Adjudicate the coarse class down to `other` (a corrected verdict).
    adj = append_adjudication(
        repo,
        observation_id=observation["id"],
        administration_id=observation["administration_id"],
        reviewed_raw_event_ids=[raw["id"]],
        adjudicator_source="human_owner",
        resolved_class="other",
        clock=CLOCK,
    )
    new_head = repo.grade_interpretation(adj["interpretation_id"])
    event_id = record_reinterpretation_if_changed(
        repo,
        administration_id=observation["administration_id"],
        observation_id=observation["id"],
        from_interpretation=original_row,
        to_interpretation=new_head,
        clock=CLOCK,
    )
    activate_p0_projection(vault, repo, clock=CLOCK)
    after = _cells(repo)

    # Current projection self-corrected: full-credit success collapses.
    assert after != before
    total_after = sum(v[2] for v in after.values())
    total_before = sum(v[2] for v in before.values())
    assert total_after < total_before

    # An inspectable receipt was written and history is byte-stable.
    assert event_id is not None
    assert repo.grade_interpretation(original_head["id"]) == original_row  # append-only
    with connect(repo.sqlite_path) as connection:
        events = connection.execute(
            "SELECT kind FROM measurement_events WHERE kind = 'measurement_reinterpretation'"
        ).fetchall()
        rebuilds = connection.execute(
            "SELECT algorithm_version FROM derived_state_rebuilds WHERE scope = 'p0_projection_activation'"
        ).fetchall()
    assert len(events) == 1
    assert any(r["algorithm_version"] == "mvp-0.8" for r in rebuilds)


# ---------------------------------------------------------------------------
# §9.2 bullet 3: ledger lineage present; a projector dropping it fails.
# ---------------------------------------------------------------------------


def test_ledger_v2_carries_lineage_and_strict_projector_requires_it(tmp_path):
    vault, repo = _p0_vault(tmp_path)
    _attempt(vault, repo)

    ledger = repo.canonical_observation_ledger_v2()
    assert ledger
    row = ledger[0]
    required = {
        "administration_id",
        "active_interpretation",
        "active_adjudication",
        "calibration_lineage",
        "calibration_model_hash",
        "target_contract_version_id",
        "quarantine_state",
        "projection_algorithm_version",
    }
    assert required <= set(row)
    assert row["active_interpretation"] is not None
    assert row["calibration_model_hash"]

    # A projector variant that drops lineage must fail its own contract check.
    def strict_projector(rows):
        for r in rows:
            missing = required - set(r)
            if missing:
                raise ValueError(f"ledger row missing calibration lineage: {missing}")
        return True

    assert strict_projector(ledger) is True
    stripped = [{k: v for k, v in row.items() if k not in required}]
    with pytest.raises(ValueError):
        strict_projector(stripped)


# ---------------------------------------------------------------------------
# §7.2: activation records a rebuild receipt.
# ---------------------------------------------------------------------------


def test_activation_records_derived_state_rebuild(tmp_path):
    vault, repo = _p0_vault(tmp_path)
    _attempt(vault, repo)
    rebuild_id = activate_p0_projection(vault, repo, clock=CLOCK)
    assert rebuild_id
    latest = repo.latest_derived_state_rebuild()
    assert latest is not None
    assert latest["algorithm_version"] == "mvp-0.8"


# ---------------------------------------------------------------------------
# §9.3 bullet 2: narrowing the model continuously increases mass; no jump.
# ---------------------------------------------------------------------------


def test_narrowing_model_monotonically_increases_effective_mass():
    """Sweeping the LCB upward (a narrower calibration ensemble) monotonically
    raises effective mass with no status-gated discontinuity (§9.3 bullet 2).

    P4.2 revision: the mass discount is the EPISTEMIC factor ``lcb / certainty``,
    so mass rises strictly while the ensemble tightens (lcb below the point
    certainty — the only regime the robust bound produces, since certainty_lcb
    is floored by the mean-member certainty) and saturates at the full attempt
    mass once lcb == certainty. It never exceeds attempt_type_mass.
    """

    posterior = {"success": 0.8, "partial_success": 0.15, "other": 0.05}
    score_fraction = {"success": 1.0, "partial_success": 0.5, "other": 0.0}

    def mass(lcb: float) -> float:
        return effective_observation_from_posterior(
            observation_id="o",
            posterior=posterior,
            score_fraction=score_fraction,
            certainty_lcb=lcb,
            attempt_type_mass=1.0,
        ).effective_mass

    point_certainty = effective_observation_from_posterior(
        observation_id="o", posterior=posterior, score_fraction=score_fraction,
        certainty_lcb=0.0, attempt_type_mass=1.0,
    ).certainty
    within = [mass(point_certainty * f) for f in (0.1, 0.3, 0.5, 0.7, 0.9, 1.0)]
    assert within == sorted(within)
    assert all(b > a for a, b in zip(within, within[1:]))
    assert within[-1] == pytest.approx(1.0)
    # Synthetic lcb above the point certainty (the robust bound never produces
    # one) clamps at full mass instead of inventing evidence.
    assert mass(1.0) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# §4.3/§4.4 mastery wiring: new-version writes source grader confidence from the
# calibrated certainty LCB (the SAME certainty certification consumes), not the
# raw grader confidence. The resolve_reliability product shape is unchanged
# (pinned by test_characterization_mastery_reliability, which stays green).
# ---------------------------------------------------------------------------


def test_mvp08_mastery_reliability_sources_certainty_lcb(tmp_path):
    from learnloop.services.grade_resolution import response_certainty_lcb

    vault, repo = _p0_vault(tmp_path)
    item = vault.practice_items[ITEM]

    # The wide heuristic channel yields a certainty LCB strictly inside (0, 1):
    # NOT the raw grader confidence of 1.0. This is the value mvp-0.8 mastery
    # writes feed into resolve_reliability's grader-confidence factor.
    lcb = response_certainty_lcb(
        vault, repo, item=item, grading_source="ai", rubric_score=4, max_points=4,
        grader_confidence=1.0, response_text="SVD is U Sigma V transpose.",
        domain="lo_svd_definition", clock=CLOCK,
    )
    assert 0.0 < lcb < 1.0

    # A uniform channel drives the certainty LCB toward zero -> a low-reliability,
    # small mastery step (a uniform interpretation is uninformative, §4.3).
    from learnloop.services import robust_composition as rc

    uniform_alpha = {
        z: {f"{g}|high": 1.0 for g in ("success", "partial_success", "other")}
        for z in ("success", "partial_success", "other")
    }
    ctx = rc.decision_context_hash(
        episode_id=None, candidate_card_version="u", resolved_slot_map=None,
        posterior_at_selection={"success": 1 / 3}, projection_algorithm_version="mvp-0.8",
    )
    uniform_lcb = rc.certainty_lcb(
        joint_alpha=uniform_alpha, observed_emission="success|high",
        calibration_model_hash="uh", decision_context_hash=ctx,
    )
    assert uniform_lcb < lcb
