"""P0.3 (spec §4.3, §9.2/§9.3) under ruling A (2026-07-27): the non-superseded
``grading_evidence`` revisions are the single directional authority for
criterion outcomes; the interpretation channel carries confidence/mass only.
Covers the supersession contract (superseded rows inert, non-superseded rows
authoritative, attempt summary columns still caches), adjudication reversal
through the superseding-revision door + receipts, the append-only write
discipline, lineage ledger, activation receipt, and status-boundary
monotonicity."""

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
from learnloop.services.canonical_projection import (
    CANONICAL_PROJECTION_VERSION,
    project_canonical_facet_state,
)
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
# Ruling A (2026-07-27), replacing the §7.2 "grading_evidence is a cache"
# reading: the NON-SUPERSEDED grading_evidence revisions are the single
# directional authority; superseded revisions are inert history; the
# practice_attempts summary columns remain caches the rebuild ignores.
# ---------------------------------------------------------------------------


def test_ruling_a_superseded_rows_inert_nonsuperseded_rows_authoritative(tmp_path):
    """Ruling A: mutating a non-superseded ledger row is editing history, so the
    rebuilt projection MUST move; a superseded revision confers nothing; the
    attempt summary columns are still caches."""

    vault, repo = _p0_vault(tmp_path)
    result = _attempt(vault, repo)
    project_canonical_facet_state(vault, repo)
    before = _cells(repo)
    assert before

    # 1. The attempt summary columns stay caches: the mvp-0.8 projection reads
    #    administrations + interpretations + the evidence ledger, never these.
    with connect(repo.sqlite_path) as connection:
        connection.execute(
            """
            UPDATE practice_attempts
               SET rubric_score = 0, correctness = 0.0, grader_confidence = 0.0
             WHERE id = ?
            """,
            (result.attempt_id,),
        )
        connection.commit()
    project_canonical_facet_state(vault, repo)
    assert _cells(repo) == before

    # 2. Adjudicating down writes a superseding revision (the ruling's whole
    #    point), so the original full-credit rows become inert history.
    observation = repo.observation_by_attempt(result.attempt_id)
    raw = repo.raw_grade_events_for_observation(observation["id"])[0]
    adj = append_adjudication(
        repo,
        observation_id=observation["id"],
        administration_id=observation["administration_id"],
        reviewed_raw_event_ids=[raw["id"]],
        adjudicator_source="human_owner",
        resolved_class="other",
        vault=vault,
        clock=CLOCK,
    )
    assert adj["evidence_revision"]["status"] == "revised"
    project_canonical_facet_state(vault, repo)
    after_adjudication = _cells(repo)
    assert after_adjudication != before

    # 3. Superseded rows are inert: corrupting them changes nothing.
    with connect(repo.sqlite_path) as connection:
        n_superseded = connection.execute(
            "UPDATE grading_evidence SET points_awarded = 3.7 "
            "WHERE attempt_id = ? AND superseded_at IS NOT NULL",
            (result.attempt_id,),
        ).rowcount
        connection.commit()
    assert n_superseded > 0
    project_canonical_facet_state(vault, repo)
    assert _cells(repo) == after_adjudication

    # 4. Non-superseded rows are authoritative: mutating one IS editing history
    #    and the rebuild follows it. (This is why append-only-with-supersession
    #    is the table's write discipline, not a stylistic preference.)
    with connect(repo.sqlite_path) as connection:
        n_live = connection.execute(
            "UPDATE grading_evidence SET points_awarded = 4.0 "
            "WHERE attempt_id = ? AND superseded_at IS NULL",
            (result.attempt_id,),
        ).rowcount
        connection.commit()
    assert n_live > 0
    project_canonical_facet_state(vault, repo)
    assert _cells(repo) != after_adjudication


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

    # Adjudicate the coarse class down to `other` (a corrected verdict). Under
    # ruling A this writes a superseding grading_evidence revision — the ledger
    # is the directional authority — alongside the new interpretation head.
    adj = append_adjudication(
        repo,
        observation_id=observation["id"],
        administration_id=observation["administration_id"],
        reviewed_raw_event_ids=[raw["id"]],
        adjudicator_source="human_owner",
        resolved_class="other",
        vault=vault,
        clock=CLOCK,
    )
    assert adj["evidence_revision"]["status"] == "revised"
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

    # Current projection self-corrected: full-credit success collapses. This is
    # the ruling's exhibit inverted — before it, adjudicating DOWN raised the
    # banked credit (certainty jumped to 1.0 while direction still read the
    # original full-credit fractions).
    assert after != before
    total_after = sum(v[2] for v in after.values())
    total_before = sum(v[2] for v in before.values())
    assert total_after < total_before

    # The ledger tells the whole story: originals superseded (kept as history,
    # pointing at their successor), the revision adjudication-sourced tier 4.
    all_rows = repo.fetch_grading_evidence(result.attempt_id, include_superseded=True)
    superseded = [r for r in all_rows if r.superseded_at is not None]
    live = [r for r in all_rows if r.superseded_at is None]
    assert superseded and live
    revision_ids = set(adj["evidence_revision"]["evidence_ids"])
    assert {r.id for r in live} == revision_ids
    assert all(r.superseded_by_evidence_id in revision_ids for r in superseded)
    assert all(r.grader_tier == 4 for r in live)
    assert all(
        (r.local_grader_id or "").startswith("adjudication:human_owner") for r in live
    )

    # Both folds agree on the corrected direction (ruling A keeps one tape):
    # the learner-facing timeline's final banked value equals the ledger cell.
    from learnloop.services.facet_evidence_timeline import facet_evidence_timeline

    banked_by_facet: dict[str, float] = {}
    for cell in repo.facet_capability_evidence_all():
        banked_by_facet[cell.facet_id] = (
            banked_by_facet.get(cell.facet_id, 0.0) + cell.certification_credit
        )
    for facet, banked in banked_by_facet.items():
        series = facet_evidence_timeline(vault, repo, facet)
        final = series[-1].demonstrated if series else 0.0
        assert final == pytest.approx(banked, abs=1e-12)

    # Replay reproduces: a second rebuild is byte-identical.
    project_canonical_facet_state(vault, repo)
    assert _cells(repo) == after

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


def test_adjudicating_up_raises_credit_and_unchanged_direction_skips(tmp_path):
    """Ruling A symmetry: an upward adjudication raises banked credit through
    the same superseding-revision door, and an adjudication that does not flip
    the leading class leaves the ledger untouched (typed skip)."""

    vault, repo = _p0_vault(tmp_path)
    result = _attempt(vault, repo, points=0, confidence=2)
    project_canonical_facet_state(vault, repo)
    before = _cells(repo)

    observation = repo.observation_by_attempt(result.attempt_id)
    raw = repo.raw_grade_events_for_observation(observation["id"])[0]
    adj = append_adjudication(
        repo,
        observation_id=observation["id"],
        administration_id=observation["administration_id"],
        reviewed_raw_event_ids=[raw["id"]],
        adjudicator_source="human_owner",
        resolved_class="success",
        vault=vault,
        clock=CLOCK,
    )
    assert adj["evidence_revision"]["status"] == "revised"
    project_canonical_facet_state(vault, repo)
    after = _cells(repo)
    total_after = sum(v[2] for v in after.values())
    total_before = sum(v[2] for v in before.values())
    assert total_after > total_before

    # Re-adjudicating to the same class flips nothing: the ledger already says
    # success, so the revision is skipped with a typed reason, and the previous
    # adjudication revision stays the live direction.
    live_before = {r.id for r in repo.fetch_grading_evidence(result.attempt_id)}
    raw2 = repo.raw_grade_events_for_observation(observation["id"])[0]
    adj2 = append_adjudication(
        repo,
        observation_id=observation["id"],
        administration_id=observation["administration_id"],
        reviewed_raw_event_ids=[raw2["id"]],
        adjudicator_source="human_owner",
        resolved_class="success",
        vault=vault,
        clock=CLOCK,
    )
    assert adj2["evidence_revision"]["status"] == "skipped_direction_unchanged"
    assert {r.id for r in repo.fetch_grading_evidence(result.attempt_id)} == live_before


def test_grading_evidence_write_discipline_is_append_only_with_supersession():
    """Ruling A's enforcement test: no repository write path may mutate a
    grading_evidence row's direction in place. Every UPDATE statement against
    the table must SET only the supersession bookkeeping columns — the ledger
    is append-only-with-supersession, because non-superseded rows ARE history.
    (Static source audit rather than DB triggers: the discipline currently
    holds by convention, and this test is what turns the convention into a
    contract.)"""

    import inspect
    import re as _re

    import learnloop.db.repositories as repositories_module

    source = inspect.getsource(repositories_module)
    allowed = {"superseded_at", "superseded_by_evidence_id"}
    updates = _re.findall(
        r"UPDATE grading_evidence\s+SET\s+(.*?)\s+WHERE", source, flags=_re.S
    )
    assert updates, "expected at least the supersession bookkeeping writers"
    for set_clause in updates:
        columns = {
            fragment.split("=")[0].strip()
            for fragment in set_clause.split(",")
            if "=" in fragment
        }
        assert columns <= allowed, (
            f"UPDATE grading_evidence touches non-supersession columns {columns - allowed}; "
            "direction changes must be superseding INSERTs (ruling A)"
        )


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
    assert latest["canonical_projection_version"] == CANONICAL_PROJECTION_VERSION
    assert latest["coverage_denominator_version"] is not None


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
