"""Teacher TE1b: the Codex re-review's reopened findings (docs/reviews/teacher-te1b-router-suggestions-codex-review.md).

* F2: a Start whose lesson never opened is offered again on a later day (not only the same day), before
  any new draw, and goes once a lesson on its LOs opens.
* F5: the day's target is drawn the router's way (spec_teacher_v1 §15.1): ``router.mode = "mixture"`` is
  the router's own ``model_mixture`` with the configured weights and floor (the models not asked about
  lesson candidates, so their weight is the staged rule's, G7), and ``staged`` is the randomization
  layer's ``epsilon_tiebreak``.

Every model is a fake; no network.
"""

from __future__ import annotations

import json
import math

import pytest

from learnloop.daily_plan import lesson_suggestion as SG
from learnloop.router import lesson_suggestions as LS
from learnloop.router import mixture as mx
from learnloop.scheduling import randomization_layer as RL
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, clients, plan_turn
from tests.teacher_te1b_suggestions_helpers import _clock, _decisions, _suggestion, _vault, no_network, shown  # noqa: F401
from tests.ux_phase1_support import set_config


# --- F2: an accepted Start whose lesson never opened, across a day boundary ------------------------------


def test_a_start_left_unopened_overnight_is_offered_the_next_day(tmp_path, shown, no_network):
    """Start on day 0, the app stops before the lesson opens: the next day's Today offers that lesson under
    the recorded id (no new draw is logged while it holds the card), it opens, and the day then draws."""

    paths, repository = _vault(tmp_path)
    card = _suggestion(paths, repository, _clock())
    started = SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="accepted",
                         clock=_clock(hours=1))
    lesson_id = started["lesson"]["lesson_id"]
    for days in (1, 3):
        again = _suggestion(paths, repository, _clock(days=days))
        assert again is not None and again["decision_id"] == card["decision_id"], days
        assert again["pending_lesson"]["lesson_id"] == lesson_id and again["alternatives"] == []
        assert again["suggestion"]["ref"] == card["suggestion"]["ref"]
    assert [row["receipt_key"] for row in _decisions(repository)] == ["lesson_suggestion:2026-11-02"]
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", clients=clients(TeacherFake([plan_turn])),
                  origin="router", origin_ref=card["decision_id"], lesson_id=lesson_id, clock=_clock(days=3, hours=1))
    after = _suggestion(paths, repository, _clock(days=3, hours=2))
    assert after is None or after["decision_id"] != card["decision_id"]
    assert len(_decisions(repository)) == 2  # day 3's own decision, drawn once the lesson opened


def test_an_overnight_alternative_start_keeps_the_alternative(tmp_path, shown):
    paths, repository = _vault(tmp_path)
    card = _suggestion(paths, repository, _clock())
    alternative = card["alternatives"][0]
    SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="chose_alternative",
               candidate_ref=alternative["ref"], clock=_clock(hours=1))
    again = _suggestion(paths, repository, _clock(days=1))
    assert again["suggestion"]["ref"] == alternative["ref"]
    assert again["pending_lesson"]["learning_object_ids"] == alternative["learning_object_ids"]


def test_a_reserved_lesson_is_dropped_once_teach_me_opened_one_on_it(tmp_path, shown, no_network):
    """The learner opened a lesson on the same LO themselves ("Teach me"): the reservation is not offered
    again, and the next day draws its own card."""

    paths, repository = _vault(tmp_path)
    card = _suggestion(paths, repository, _clock())
    SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="accepted",
               clock=_clock(hours=1))
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object",
                  learning_object_ids=card["suggestion"]["learning_object_ids"],
                  clients=clients(TeacherFake([plan_turn])), clock=_clock(hours=2))
    assert _suggestion(paths, repository, _clock(hours=3)) is None
    later = _suggestion(paths, repository, _clock(days=1))
    assert later is None or later["pending_lesson"] is None
    assert len(_decisions(repository)) == 2


# --- F5: the target is the router's draw for its mode -----------------------------------------------------


def test_mixture_mode_draws_the_target_by_the_routers_model_mixture(tmp_path, shown):
    """Default ``router.mode = "mixture"``: the logged target record is the router's ``model_mixture``: the
    configured weights, the models not asked (their weight on the staged rule, G7), the staged pick the top
    value, the ``epsilon_min`` floor, and ``mixture.recompute`` gives back the logged ``pi``."""

    paths, repository = _vault(tmp_path)
    set_config(paths.root, {("router", "weights", "staged"): 0.5, ("router", "weights", "decider"): 0.25,
                            ("router", "weights", "llm"): 0.25})
    _suggestion(paths, repository, _clock())
    (row,) = _decisions(repository)
    detail = json.loads(row["detail_json"])
    target = detail["target"]
    assert detail["target_design"] == LS.TARGET_MIXTURE == "model_mixture" and row["design"] == LS.DESIGN
    assert target["configured_weights"] == {"staged": 0.5, "decider": 0.25, "llm": 0.25}
    assert target["effective_weights"] == {"staged": 1.0, "decider": 0.0, "llm": 0.0}
    assert target["models"] == {"decider": {"status": "not_asked"}, "llm": {"status": "not_asked"}}
    assert json.loads(row["mixture_weights_json"]) == target["effective_weights"]
    assert row["model_distributions_json"] is None and row["fallback"] is None  # no model answer, no failure
    candidates = json.loads(row["candidates_json"])
    assert target["support"] == [c["ref"] for c in candidates] and target["staged_ref"] == candidates[0]["ref"]
    assert candidates[0]["value"] == max(c["value"] for c in candidates)
    k, eps = len(candidates), 0.02
    for candidate in candidates:
        expected = (1 - k * eps) + eps if candidate["ref"] == target["staged_ref"] else eps
        assert candidate["pi"] == pytest.approx(expected)
    assert mx.recompute(target) == pytest.approx(detail["pi_drawn"])
    assert row["propensity"] == pytest.approx(detail["pi_drawn"] * detail["p_show_drawn"])


@pytest.mark.real_draws  # its subject is production's seed derivation: the default pin would measure the substituted seeds
def test_the_mixture_floor_draws_a_non_staged_target_with_its_exact_propensity():
    a = LS.ScoredCandidate(LS.Candidate("lesson:a", ("a",), "new_goal", 0.2), 0.9, 0.8, math.log(0.72))
    b = LS.ScoredCandidate(LS.Candidate("lesson:b", ("b",), "new_goal", 0.5), 0.6, 0.5, math.log(0.30))
    c = LS.ScoredCandidate(LS.Candidate("lesson:c", ("c",), "new_goal", 0.5), 0.5, 0.5, math.log(0.25))
    weights = {"staged": 1 / 3, "decider": 1 / 3, "llm": 1 / 3}
    seen = {}
    for index in range(400):
        seed = LS.seed_for(f"d{index}", "s")
        target = LS.mixture_target([a, b, c], weights=weights, epsilon=0.05, seed=seed)
        result = LS.draw([a, b, c], target=target, seed=seed)
        seen[result.drawn.candidate.ref] = seen.get(result.drawn.candidate.ref, 0) + 1
        assert target.pi == pytest.approx({"lesson:a": 0.9, "lesson:b": 0.05, "lesson:c": 0.05})
        assert target.record["component"] in ("staged", "uniform")
        arm = result.drawn.p_accept if result.shown else 1 - result.drawn.p_accept
        assert result.propensity == pytest.approx(target.pi[result.drawn.candidate.ref] * arm)
    assert seen["lesson:a"] > 300 and seen.get("lesson:b", 0) > 0 and seen.get("lesson:c", 0) > 0


def test_staged_mode_draws_the_target_by_the_epsilon_tiebreak(tmp_path):
    """``router.mode = "staged"``: no mixture, the randomization layer's tie-break. The six goal LOs are
    near-tied (same reason, same prior), so the target is uniform over the tied set with that propensity."""

    paths, repository = _vault(tmp_path)
    set_config(paths.root, {("router", "mode"): "staged"})
    _suggestion(paths, repository, _clock())
    (row,) = _decisions(repository)
    detail = json.loads(row["detail_json"])
    target = detail["target"]
    assert detail["target_design"] == LS.TARGET_TIEBREAK == "epsilon_tiebreak" and row["mixture_weights_json"] is None
    candidates = json.loads(row["candidates_json"])
    values = [math.exp(c["value"]) for c in candidates]
    refs = [c["ref"] for c in candidates]
    expected_tied = RL.tied_set(refs, values) if RL.is_near_equivalent(values) else [refs[0]]
    assert target["tied"] == sorted(expected_tied) and detail["drawn_ref"] in expected_tied
    for candidate in candidates:
        expected = 1 / len(expected_tied) if candidate["ref"] in expected_tied else 0.0
        assert candidate["pi"] == pytest.approx(expected)
    assert detail["pi_drawn"] == pytest.approx(1 / len(expected_tied))


def test_the_staged_tiebreak_is_deterministic_without_a_near_tie():
    top = LS.ScoredCandidate(LS.Candidate("lesson:a", ("a",), "new_goal", 0.1), 0.9, 0.9, math.log(0.81))
    low = LS.ScoredCandidate(LS.Candidate("lesson:b", ("b",), "new_goal", 0.5), 0.4, 0.5, math.log(0.20))
    refs, values = ["lesson:a", "lesson:b"], [0.81, 0.20]
    assignment = RL.epsilon_tiebreak(None, experiment_id=LS.DECISION_KIND, refs=refs, values=values, seed="s")
    assert not assignment.near_equivalent and assignment.variant == "lesson:a"
    target = LS.tiebreak_target([top, low], chosen_ref=assignment.variant, tied=[assignment.variant],
                                margin=RL.EPSILON_TIE_MARGIN)
    assert target.pi == {"lesson:a": 1.0, "lesson:b": 0.0}
    result = LS.draw([top, low], target=target, seed=LS.seed_for("d", "s"))
    assert result.drawn.candidate.ref == "lesson:a"
    arm = 0.9 if result.shown else 0.1
    assert result.propensity == pytest.approx(arm)
    # The scope still names the other candidate (predeclared), though the tie-break gave it no mass.
    assert [s.candidate.ref for s in result.scope] == ["lesson:a", "lesson:b"]
