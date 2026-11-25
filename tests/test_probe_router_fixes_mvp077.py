"""mvp-0.77, the probe router's fix round 3 (``docs/reviews/algorithm-mvp-0.77.md``): what changes at the tag, each
on both sides of it (below the tag every answer is mvp-0.76's)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    OUTCOME_FIXES_ALGORITHM_VERSION,
    PROBE_ROUTER_FIXES_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    probe_router_fixes_on,
)
from learnloop.config.schema import LearnLoopConfig

BEFORE = OUTCOME_FIXES_ALGORITHM_VERSION
AT = PROBE_ROUTER_FIXES_ALGORITHM_VERSION


def test_the_tag():
    assert AT == "mvp-0.77" == SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION and SUCCESSOR_CHAIN[-2] == BEFORE
    assert probe_router_fixes_on(AT) and not probe_router_fixes_on(BEFORE) and not probe_router_fixes_on(None)


def _config(tag: str, **router: float) -> LearnLoopConfig:
    config = LearnLoopConfig()
    return config.model_copy(update={
        "algorithms": config.algorithms.model_copy(update={"algorithm_version": tag}),
        "router": config.router.model_copy(update=router),
    })


# -- G2-R34 (finding 14): a learned draw logs exactly its served arm's share ------------------------------------------


@pytest.mark.parametrize(("tag", "exact"), [(BEFORE, False), (AT, True)])
def test_r34_a_learned_draw_with_a_tiny_floor_logs_the_exact_share_through_the_persisted_row(tag, exact, monkeypatch):
    """The permitted floor 5e-13 with both policies on the same arm: that arm's share is 1 - 5e-13 and the other arm
    keeps 5e-13. From the tag the persisted row logs that share; below it the chooser's 1e-12 tolerance rounded it to
    1 before the row builder saw it, while ``served_pi`` kept mass on the other arm."""

    from learnloop.daily_plan import learner_probe as LP
    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.diagnosis.learner_probe_proposal import PROBE_ACTION_REF
    from learnloop.router.plan_log import NO_PROBE_REF, PROBE_REF, build_learner_probe_decision

    vault = SimpleNamespace(config=_config(tag, epsilon_min=5e-13))
    monkeypatch.setattr(OC, "current_weight", lambda _repository, _config, at: (0.5, {"source": "test"}))
    valuation = SimpleNamespace(choice="not_" + PROBE_ACTION_REF, record={"values": {"information": 0.25}})
    served, propensity, served_pi, fields, _pending = LP.draw(
        vault, None, key="learner_probe:f", unit="learner_probe", valuation=valuation,
        now_iso="2026-10-12T12:00:00Z", probe_ref=PROBE_REF, other_ref=NO_PROBE_REF)
    assert served == NO_PROBE_REF and served_pi[PROBE_REF] == pytest.approx(5e-13)
    row = build_learner_probe_decision({"factor_id": "f", "chosen_ref": served, "propensity": propensity,
                                        "served_pi": served_pi, "detail": fields})
    if exact:
        assert row["propensity_kind"] == "exact" and propensity == row["propensity"] == served_pi[NO_PROBE_REF] < 1.0
    else:
        assert propensity == 1.0 and row["propensity"] == 1.0


def test_r34_a_draw_logs_1_only_when_no_other_option_has_mass():
    from learnloop.router import mixture as mx

    lone = mx.Draw(chosen="a", component="staged", propensity=1.0, pi={"a": 1.0, "b": 0.0}, u1=0.5, u2=0.5)
    near = mx.Draw(chosen="a", component="staged", propensity=1 - 5e-13, pi={"a": 1 - 5e-13, "b": 5e-13}, u1=0.5,
                   u2=0.5)
    assert lone.logged_propensity(True) == 1.0 and lone.logged_propensity(False) == 1.0
    assert near.logged_propensity(True) == 1 - 5e-13 and near.logged_propensity(False) == 1.0
