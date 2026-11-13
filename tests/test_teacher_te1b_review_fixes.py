"""Teacher TE1b, Codex review fixes (docs/reviews/teacher-te1b-router-suggestions-codex-review.md).

F2 a Start whose lesson never opened stays recoverable; F3 the logged propensity matches the
target-specific outcome (a heterogeneous-target, zero-effect check); F4 an accepted alternative's
delayed check reaches its decision through the predeclared scope, and an unshown decision has its
outcome; F5 the learner's answers are preference lines on the router's learner card; F6 the
below-band reason is adaptive difficulty's out-of-band rule on ``P_band``, not the mastery model's
expected success; F7 the acceptance model keeps the gap since the last suggestion beyond one day.
Every model is a fake; no network.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.router import lesson_suggestions as LS
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml
from tests.teacher_fakes import TeacherFake, _item, clients, plan_turn
from tests.teacher_te1b_suggestions_helpers import T0, _clock, _decisions, _rows, _suggestion, _vault, no_network, shown  # noqa: F401
from tests.teacher_te1b_review_fixes_helpers import _card

NOW = "2026-11-02T09:00:00Z"


def _attempt(paths, repository, item: str, points: int, when) -> None:
    complete_self_graded_attempt(
        load_vault(paths.root), repository,
        AttemptDraft(practice_item_id=item, learner_answer_md="an answer", attempt_type="independent_attempt",
                     evidence_origin="human"),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=4), clock=when)


def _item_for(paths, lo: str) -> str:
    item = f"pi_fix_{lo}"
    write_yaml(paths.practice_item_path("linear-algebra", item), _item(item, lo, "State it.", "okapi lemur: it"))
    return item


def _outcome(repository, decision_id: str) -> dict:
    from learnloop.router.outcomes import derive_router_outcomes

    with repository.connection() as connection:
        (outcome,) = [o for o in derive_router_outcomes(connection, reader_exposures=None) if o["decision_id"] == decision_id]
    return outcome


# --- F2: a Start whose lesson never opened ---------------------------------------------------------


def test_a_start_interrupted_before_its_lesson_opened_stays_on_the_card(tmp_path, shown, no_network):
    """The response is recorded, the app stops before ``lesson.turn``: reopening Today offers that lesson
    under the id the response recorded, and once it opens the card is gone."""

    paths, repository = _vault(tmp_path)
    card = _suggestion(paths, repository, _clock())
    started = SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="accepted",
                         clock=_clock())
    lesson_id = started["lesson"]["lesson_id"]
    again = _suggestion(paths, repository, _clock(hours=2))
    assert again is not None and again["decision_id"] == card["decision_id"]
    assert again["pending_lesson"]["lesson_id"] == lesson_id and again["alternatives"] == []
    assert again["suggestion"]["ref"] == card["suggestion"]["ref"]
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", clients=clients(TeacherFake([plan_turn])),
                  origin="router", origin_ref=card["decision_id"], lesson_id=lesson_id, clock=_clock(hours=2))
    assert _suggestion(paths, repository, _clock(hours=3)) is None


def test_an_alternative_start_interrupted_keeps_the_alternative(tmp_path, shown):
    paths, repository = _vault(tmp_path)
    card = _suggestion(paths, repository, _clock())
    alternative = card["alternatives"][1]
    SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="chose_alternative",
               candidate_ref=alternative["ref"], clock=_clock())
    again = _suggestion(paths, repository, _clock(hours=1))
    assert again["suggestion"]["ref"] == alternative["ref"]
    assert again["pending_lesson"]["learning_object_ids"] == alternative["learning_object_ids"]


def test_a_provider_failure_before_the_lesson_is_saved_leaves_an_idempotent_open(tmp_path, shown, no_network):
    """The teacher's client fails before the lesson row is written: the error carries no saved lesson id (the
    screen repeats the open, never a resume of an id that names no lesson), the card still offers the Start,
    and the repeated open succeeds under the recorded id."""

    paths, repository = _vault(tmp_path)
    card = _suggestion(paths, repository, _clock())
    started = SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="accepted",
                         clock=_clock())
    lesson_id = started["lesson"]["lesson_id"]

    def unavailable():
        raise S.LessonError("teacher_unavailable", "The teacher's model isn't set up.")

    down = S.Clients(teacher=unavailable, grading=unavailable, grading_source="ai")
    with pytest.raises(S.LessonError) as failed:
        S.open_lesson(load_vault(paths.root), repository, entry="learning_object", clients=down, origin="router",
                      origin_ref=card["decision_id"], lesson_id=lesson_id, clock=_clock())
    assert failed.value.code == "teacher_unavailable"
    assert "lesson_id" not in (getattr(failed.value, "details", None) or {})
    assert _rows(repository, "SELECT id FROM lessons") == []
    assert _suggestion(paths, repository, _clock(hours=1))["pending_lesson"]["lesson_id"] == lesson_id
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                         clients=clients(TeacherFake([plan_turn])), origin="router", origin_ref=card["decision_id"],
                         lesson_id=lesson_id, clock=_clock(hours=1))
    assert view["lesson_id"] == lesson_id


# --- F3: the propensity of the target-specific outcome -------------------------------------------------


def _half_and_half(seed: str) -> LS.Target:
    """A target drawn half and half between ``lesson:a`` and ``lesson:b`` (the seed's first uniform)."""

    chosen = "lesson:a" if LS._uniforms(seed)[0] < 0.5 else "lesson:b"
    return LS.Target("test", chosen, {"lesson:a": 0.5, "lesson:b": 0.5}, {})


@pytest.mark.real_draws  # its subject is production's seed derivation: the default pin would measure the substituted seeds
def test_logged_propensities_give_no_effect_when_targets_differ_and_the_card_does_nothing():
    """Two candidates drawn half and half, shown at 0.9 and 0.1; the outcome is 1 on A and 0 on B whatever
    the arm (no lesson effect). Inverse-propensity means of each arm over the drawn target's outcome, with
    the row's logged propensity (``π(target) · P(arm | target)``), agree: no effect. The aggregate chance of
    no card (``Σ π (1 − P)``), the earlier propensity, shows a large spurious one."""

    a = LS.ScoredCandidate(LS.Candidate("lesson:a", ("a",), "new_goal", 0.5), 0.9, 1.0, 0.0)
    b = LS.ScoredCandidate(LS.Candidate("lesson:b", ("b",), "new_goal", 0.5), 0.1, 1.0, 0.0)
    outcome = {"lesson:a": 1.0, "lesson:b": 0.0}
    n = 6000
    shown_sum = unshown_sum = aggregate_sum = 0.0
    for index in range(n):
        seed = LS.seed_for(f"day{index}", "snapshot")
        result = LS.draw([a, b], target=_half_and_half(seed), seed=seed)
        y = outcome[result.drawn.candidate.ref]
        # Horvitz-Thompson over the target distribution: weight π(target) / logged propensity.
        weight = result.drawn.pi / result.propensity
        if result.shown:
            shown_sum += y * weight
        else:
            unshown_sum += y * weight
            aggregate_sum += y * result.drawn.pi / result.p_no_card
    shown_mean, unshown_mean, aggregate_mean = shown_sum / n, unshown_sum / n, aggregate_sum / n
    assert shown_mean == pytest.approx(0.5, abs=0.05) and unshown_mean == pytest.approx(0.5, abs=0.05)
    assert abs(shown_mean - unshown_mean) < 0.06
    assert abs(shown_mean - aggregate_mean) > 0.3  # the aggregate propensity's spurious effect


def test_the_draw_logs_the_joint_target_and_arm_probability():
    a = LS.ScoredCandidate(LS.Candidate("lesson:a", ("a",), "new_goal", 0.5), 0.7, 1.0, 0.0)
    b = LS.ScoredCandidate(LS.Candidate("lesson:b", ("b",), "new_goal", 0.5), 0.2, 1.0, -1.0)
    for index in range(40):
        seed = LS.seed_for(f"d{index}", "s")
        result = LS.draw([a, b], target=LS.mixture_target([a, b], weights={"staged": 1.0}, epsilon=0.02, seed=seed),
                         seed=seed)
        arm = result.drawn.p_accept if result.shown else 1.0 - result.drawn.p_accept
        assert result.arm_propensity == pytest.approx(arm)
        assert result.propensity == pytest.approx(result.drawn.pi * arm)
        assert result.scope[0] is result.drawn and len(result.scope) == 2


# --- F4: the predeclared scope's delayed checks ----------------------------------------------------------


def test_an_accepted_alternatives_delayed_check_reaches_its_decision(tmp_path, shown):
    """The card recommends A; the learner takes alternative B and passes B's cold check two days later: the
    decision's outcome records B's R_cold in its predeclared scope, marked taken. The ITT outcome stays A's
    (still pending): the acceptor's choice never replaces the target."""

    paths, repository = _vault(tmp_path)
    card = _suggestion(paths, repository, _clock())
    target = card["suggestion"]["learning_object_ids"][0]
    alternative = card["alternatives"][0]
    chosen = alternative["learning_object_ids"][0]
    item = _item_for(paths, chosen)
    SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="chose_alternative",
               candidate_ref=alternative["ref"], clock=_clock(hours=1))
    _attempt(paths, repository, item, 4, _clock(days=2))
    outcome = _outcome(repository, card["decision_id"])
    assert outcome["action_status"] == "taken" and outcome["target_learning_object_id"] == target
    assert outcome["r_cold_status"] == "pending" and outcome["s_status"] == "pending"
    detail = json.loads(outcome["detail_json"])
    assert detail["taken_learning_object_ids"] == [chosen]
    by_lo = {entry["learning_object_id"]: entry for entry in detail["scope"]}
    assert set(by_lo) == {target, *(lo for alt in card["alternatives"] for lo in alt["learning_object_ids"])}
    assert by_lo[chosen]["taken"] and by_lo[chosen]["role"] == "alternative"
    assert by_lo[chosen]["r_cold_status"] == "observed" and by_lo[chosen]["r_cold_value"] == 1.0
    assert not by_lo[target]["taken"] and by_lo[target]["role"] == "target"
    assert by_lo[target]["r_cold_status"] == "pending"


def test_an_unshown_decision_has_its_itt_outcome_over_the_same_scope(tmp_path, monkeypatch):
    monkeypatch.setattr(LS, "_uniforms", lambda seed: (0.5, 0.0, 0.999999))
    paths, repository = _vault(tmp_path)
    assert _suggestion(paths, repository, _clock()) is None
    (row,) = _decisions(repository)
    detail = json.loads(row["detail_json"])
    target = detail["drawn_learning_object_ids"][0]
    _attempt(paths, repository, _item_for(paths, target), 0, _clock(days=2))
    outcome = _outcome(repository, row["id"])
    assert outcome["action_status"] == "not_applicable" and outcome["target_learning_object_id"] == target
    assert outcome["r_cold_status"] == "observed" and outcome["r_cold_value"] == 0.0 and outcome["s_status"] == "final"
    out_detail = json.loads(outcome["detail_json"])
    assert out_detail["arm"] == "not_shown" and out_detail["response"] is None
    assert out_detail["taken_learning_object_ids"] == []
    assert [entry["ref"] for entry in out_detail["scope"]] == [entry["ref"] for entry in detail["target_scope"]]


# --- F5: preference lines on the router's learner card ---------------------------------------------------


def test_the_learners_answers_are_preference_lines_on_the_router_card(tmp_path, shown):
    from learnloop.router.card import CARD_VERSION, SUGGESTION_CARD_SUFFIX, SUGGESTION_SECTION
    from tests.ux_phase1_support import set_config

    paths, repository = _vault(tmp_path)
    before = _card(paths, repository, "2026-11-02T08:00:00Z")
    assert SUGGESTION_SECTION not in before.json["evidence_sections"] and before.card_version == CARD_VERSION
    card = _suggestion(paths, repository, _clock())
    title = card["suggestion"]["title"]
    SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="declined",
               clock=_clock(hours=1))
    after = _card(paths, repository, "2026-11-03T09:00:00Z")
    assert after.json["evidence_sections"][SUGGESTION_SECTION][0]["response"] == "declined"
    assert f"2026-11-02 not now on {title}" in after.text
    assert after.card_version == CARD_VERSION + SUGGESTION_CARD_SUFFIX
    # Outside the card's 7-day window the line is gone; with suggestions off the card is the predecessor's.
    assert SUGGESTION_SECTION not in _card(paths, repository, "2026-11-10T09:00:00Z").json["evidence_sections"]
    set_config(paths.root, {("router", "lesson_suggestions", "enabled"): False})
    off = _card(paths, repository, "2026-11-03T09:00:00Z")
    assert SUGGESTION_SECTION not in off.json["evidence_sections"] and off.card_version == CARD_VERSION


def test_a_chosen_alternative_reads_as_a_choice_over_the_suggestion():
    from learnloop.router.card import _suggestion_lines

    lines = _suggestion_lines([{"at": "2026-11-02T10:00:00Z", "response": "chose_alternative",
                                "topics": ["Inner products"], "instead_of": ["Determinants"]},
                               {"at": "2026-11-01T10:00:00Z", "response": "ignored", "topics": ["SVD"]},
                               {"at": "2026-10-31T10:00:00Z", "response": "accepted", "topics": ["Eigen"]}])
    assert lines[1:] == ["- 2026-11-02 chose a lesson on Inner products over Determinants",
                         "- 2026-11-01 no answer on SVD", "- 2026-10-31 started the suggested lesson on Eigen"]


# --- F6: below the band is adaptive difficulty's, on P_band ----------------------------------------------


def test_below_band_reads_adaptive_difficultys_posterior_not_the_mastery_model(tmp_path, monkeypatch):
    """Three attempted LOs the mastery model calls very hard (0.1, the old code's below-band for all three):
    AD predicts the learner below the band on lo_det only (lo_eigen is out of the band above it; lo_inner is
    likely in it), so only lo_det is a below-band candidate. With AD's subject view not live, none is."""

    import learnloop.adaptive_difficulty.readiness as readiness
    import learnloop.adaptive_difficulty.successor as successor

    paths, repository = _vault(tmp_path)
    for offset, (item, lo) in enumerate((("pi_det_1", "lo_det"), (None, "lo_eigen"), (None, "lo_inner"))):
        _attempt(paths, repository, item or _item_for(paths, lo), 4, _clock(days=-3 + offset * 0.1))
    monkeypatch.setattr(SG, "_predicted", lambda *args, **kwargs: 0.1)
    bands = {"lo_det": {"p_band": 0.1, "p_bar": 0.3, "below": True},
             "lo_eigen": {"p_band": 0.1, "p_bar": 0.95, "below": False},
             "lo_inner": {"p_band": 0.6, "p_bar": 0.72, "below": False}}

    def reasons() -> dict[str, str]:
        candidates, _excluded = SG.build_candidates(load_vault(paths.root), repository, now_iso=NOW)
        return {c.learning_object_ids[0]: c.reason for c in candidates if c.reason != "new_goal"}

    monkeypatch.setattr(successor, "subject_view_live", lambda config: False)
    assert reasons() == {}  # AD not live: no below-band reason, whatever the mastery model says
    monkeypatch.setattr(successor, "subject_view_live", lambda config: True)
    monkeypatch.setattr(readiness, "band_positions",
                        lambda vault, repository, los, **kw: {lo: bands[lo] for lo in los if lo in bands})
    assert reasons() == {"lo_det": "below_band"}
    candidates, _excluded = SG.build_candidates(load_vault(paths.root), repository, now_iso=NOW)
    (det,) = [c for c in candidates if c.learning_object_ids == ("lo_det",)]
    assert det.band == bands["lo_det"] and det.as_dict()["band"] == bands["lo_det"]


def test_band_positions_thresholds_p_band_and_reads_the_side_from_expected_success(monkeypatch):
    """``calibrate_below`` thresholds P_band (a probability of being in the band), never expected success; the
    side (below rather than above) is the nearest point's expected success against the band's lower edge."""

    import learnloop.adaptive_difficulty.material_view as material_view
    import learnloop.adaptive_difficulty.readiness as readiness
    from learnloop.adaptive_difficulty.selection import Scored

    section = SimpleNamespace(enabled=False, practice_band=(0.70, 0.80), overlap_band=(0.55, 0.90),
                              overlap_share=0.10, near_tie_margin=0.05, calibrate_below=0.25)
    vault = SimpleNamespace(config=SimpleNamespace(adaptive_difficulty=section))
    scored = {
        "below": [Scored("p1", 0.20, 0.60), Scored("p2", 0.05, 0.30)],      # out of band; even the easiest under it
        "above": [Scored("p1", 0.20, 0.90), Scored("p2", 0.05, 0.97)],      # out of band, over it
        "likely": [Scored("p1", 0.40, 0.60), Scored("p2", 0.05, 0.30)],     # p̄ under the band, P_band >= cut
        "easier": [Scored("p1", 0.20, 0.60), Scored("p2", 0.01, 0.92)],     # an easier point is over the band
        "untested": [Scored("p1", 0.20, 0.60), Scored("p2", 0.05, 0.30)],   # AD's A4: never a claim
    }
    observed = {("f", "cap")}
    monkeypatch.setattr(readiness, "subject_view_live", lambda config: True)
    monkeypatch.setattr(material_view, "material_view", lambda vault, repository, view=None: "view")
    monkeypatch.setattr(readiness.RP, "snapshot", lambda vault, repository, view=None: SimpleNamespace(
        subject="subject", observed_cells=observed))
    monkeypatch.setattr(readiness, "_main_cell",
                        lambda view, vault, lo: ("g" if lo == "untested" else "f", "cap", "subj"))
    monkeypatch.setattr(readiness.S, "commission_candidates", lambda capability: [{"point": 1}, {"point": 2}])
    monkeypatch.setattr(readiness.PR, "point_spec", lambda point, **kw: kw["learning_object_id"])
    monkeypatch.setattr(readiness.PR, "score", lambda view, specs, **kw: scored[specs[0]])
    out = readiness.band_positions(vault, object(), list(scored))
    assert out["below"]["below"] and out["below"]["p_band"] == 0.2 and out["below"]["p_bar"] == 0.6
    assert not out["above"]["below"] and not out["likely"]["below"] and not out["easier"]["below"]
    assert out["untested"]["untested"] and not out["untested"]["below"]
    assert out["likely"]["calibrate_below"] == 0.25 and out["likely"]["band"] == [0.7, 0.8]


# --- F7: the gap since the last suggestion -------------------------------------------------------------


def test_the_spacing_feature_keeps_every_multi_day_gap():
    values = [LS.spacing_feature(days) for days in (0.0, 1.0, 7.0, 30.0)]
    assert values[1] == 0.0 and LS.spacing_feature(None) == 0.0  # the seeded cadence is the reference
    assert values == sorted(values) and len(set(values)) == 4
    assert all(abs(value) <= 0.5 for value in values)


def test_the_acceptance_model_learns_that_a_card_after_a_week_is_taken_and_daily_ones_are_not():
    def context(days: float) -> LS.Context:
        return LS.Context(local_hour=9.0, minutes_left=None, reentry=False, days_since_last=days)

    candidate = LS.Candidate("lesson:x", ("x",), "new_goal", None)
    state = LS.AcceptanceState()
    seeded = [state.p_accept(context(days), candidate) for days in (1.0, 7.0, 30.0)]
    assert seeded == pytest.approx([LS.LEGACY_DAILY_SHOW] * 3, abs=0.02)  # about one a day, whatever the gap
    for _ in range(25):
        state.observe(context(1.0), candidate, False)
        state.observe(context(7.0), candidate, True)
    daily, weekly, monthly = (state.p_accept(context(days), candidate) for days in (1.0, 7.0, 30.0))
    assert weekly > daily + 0.2  # the old feature gave these two exactly the same value
    assert monthly != pytest.approx(weekly, abs=1e-3)
