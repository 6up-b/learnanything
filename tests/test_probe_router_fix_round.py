"""G2's fix round (``docs/reviews/algorithm-probe-router.md``, "Fix round"): each test failed on main before its fix.

G2-R1: authority comes from the decision itself. A probe pinned by a router decision made below the probe router's
tag keeps its predecessor treatment after the vault is upgraded, mid-episode and in replay; only a decision the row
says was made at the tag, and that asked the probe, owns its presentation.
G2-R7: a pin that no longer stands (ended unanswered, or under a lock the episode no longer holds) owns nothing.
"""

from __future__ import annotations

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.diagnosis import probe_completion
from learnloop.diagnosis.probe_episodes import router_selected_episode
from learnloop.diagnosis.probe_offer import accept_probe_offer
from learnloop.router.plan_log import PROBE_REF, log_learner_probe_decision
from learnloop.vault.loader import load_vault

from tests.helpers import _set_algorithm_version_at
from tests.ih2_lessons_compete_helpers import draw  # noqa: F401 - a fixture
from tests.probe_router_authority_helpers import CLOCK, TAG, divergent_factor

HEAD = LATEST_ALGORITHM_VERSION


def _pinned(tmp_path, *, decided_at: str):
    """A probe pinned on the learner lane by a router decision row stamped ``decided_at`` (the vault at that tag when
    it was drawn, as the automatic lane's decisions below the tag are), then the vault upgraded to the head."""

    case = divergent_factor(tmp_path, version=decided_at)
    with case.repository.atomic(), case.repository.connection() as connection:
        decision_id = log_learner_probe_decision(connection, {
            "factor_id": case.factor, "chosen_ref": PROBE_REF, "propensity": 0.2,
            "served_pi": {PROBE_REF: 0.2, "no_probe": 0.8}, "detail": {}, "config": case.vault.config})
    offer = accept_probe_offer(case.vault, case.repository, factor_id=case.factor, router_decision_id=decision_id,
                               clock=CLOCK)
    assert offer.accepted
    _set_algorithm_version_at(case.root, HEAD)
    case.vault = load_vault(case.root)
    presentation = case.repository.probe_presentation(offer.presentation_id)
    episode = case.repository.probe_episode(offer.episode_id)
    rows = [{"selection_components": presentation.selection_components}]
    return case, presentation, episode, rows


def test_r1_a_pin_drawn_below_the_tag_keeps_its_predecessor_gates_after_the_upgrade(tmp_path):
    case, _presentation, episode, rows = _pinned(tmp_path, decided_at=TAG)
    assert not router_selected_episode(case.vault, case.repository, episode)
    # Value still decides the episode, as it did when the probe was asked.
    assert probe_completion.value_decides_episode(case.vault, case.repository, rows)


def test_r1_a_pin_drawn_at_the_tag_is_the_routers(tmp_path):
    case, _presentation, episode, rows = _pinned(tmp_path, decided_at=HEAD)
    assert router_selected_episode(case.vault, case.repository, episode)
    assert not probe_completion.value_decides_episode(case.vault, case.repository, rows)


def test_r7_a_pin_ended_unanswered_owns_nothing(tmp_path):
    case, presentation, episode, _rows = _pinned(tmp_path, decided_at=HEAD)
    case.repository.end_probe_presentation(presentation.id, end_reason="invalidated", clock=CLOCK)
    assert not router_selected_episode(case.vault, case.repository, episode)


# -- G2-R2: one decision, one served arm, everywhere it is logged ------------------------------------------------------


def _lane(tmp_path, monkeypatch, draw, u: float):
    import json
    from types import SimpleNamespace

    from learnloop.followup_run import jobs
    from learnloop.plan_refs import LESSON_OFFER_PREFIX
    from learnloop.router_objective import probe_coin as PC

    from tests.followup_serve_helpers import AuthorFake
    from tests.ih2_lessons_compete_helpers import _author_refuses, _miss_env

    env, row = _miss_env(tmp_path, version=HEAD, toml='[router_objective]\nstop_coin = 0.2\ncheck_rate = "off"\n')
    _author_refuses(monkeypatch)
    monkeypatch.setattr(PC, "draw_uniform", lambda _seed: u)
    draw.prefer = (LESSON_OFFER_PREFIX,)
    clients = SimpleNamespace(author=AuthorFake(), authoring=None, runtime=env.policy.restraint.runtime)
    jobs._run_probe_lane(env.vault, env.repository, row, choice=SimpleNamespace(factor_id="f", hypothesis_ids=()),
                         clients=clients, clock=env.clock)
    with env.repository.connection() as connection:
        (decision,) = [dict(r) for r in connection.execute(
            "SELECT id, chosen_ref, propensity FROM router_decisions WHERE decision_kind = 'plan_interrupt'")]
        (trace,) = [dict(r) for r in connection.execute(
            "SELECT decision_id, chosen_ref, propensity, trace_json FROM router_objective_traces "
            "WHERE decision_kind = 'plan_interrupt'")]
    trace["trace"] = json.loads(trace.pop("trace_json"))
    return decision, trace


def test_r2_the_trace_names_the_probe_the_coin_asked_at_its_served_probability(tmp_path, monkeypatch, draw):
    import pytest

    from learnloop.daily_plan.router_chooser import INSERT_NOW

    decision, trace = _lane(tmp_path, monkeypatch, draw, 0.05)
    assert decision["chosen_ref"] == trace["chosen_ref"] == INSERT_NOW
    assert decision["propensity"] == pytest.approx(0.2) and trace["propensity"] == pytest.approx(0.2)
    assert trace["trace"]["mixing"]["drawn_chosen"].startswith("lesson_offer:")


def test_r2_on_the_policy_arm_the_trace_logs_the_served_probability_not_mu(tmp_path, monkeypatch, draw):
    import pytest

    decision, trace = _lane(tmp_path, monkeypatch, draw, 0.9)
    mu = trace["trace"]["mixing"]["mu"][decision["chosen_ref"]]
    assert decision["chosen_ref"] == trace["chosen_ref"] and decision["chosen_ref"].startswith("lesson_offer:")
    assert trace["propensity"] == pytest.approx(decision["propensity"]) == pytest.approx(0.8 * mu, abs=1e-6)
