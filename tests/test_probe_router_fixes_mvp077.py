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


# -- G2-R25 (finding 5): a head a standing router pin forces is logged with probability 1 -----------------------------


def _pinned_continuation(tmp_path, monkeypatch, tag: str):
    """A router-owned episode whose continuation pinned the second instrument (the probe coin asks), and a Today
    session beside it."""

    from learnloop.router_objective import probe_coin as PC

    from tests.probe_router_owned_helpers import SECOND, answer_the_pin, selected

    case = selected(tmp_path, monkeypatch, version=tag)
    answer_the_pin(case, monkeypatch)
    monkeypatch.setattr(PC, "draw_uniform", lambda _seed: 0.0)
    case.ctx.post_attempt_worker.run_pending("probe_router")
    standing = case.repository.active_probe_presentation(case.offer["episodeId"])
    assert standing is not None and standing.practice_item_id == SECOND
    case.session_id = case.repository.create_session(energy=None, sleep_quality=None, available_minutes=20,
                                                      notes_md_path=None)
    return case


def _near_ties(monkeypatch, *, explored: bool) -> None:
    """Every other candidate is a near-tie of the greedy head at rate 0.5; the seeded roll explores or not. Today
    serves the list's head (as with the plan off, or on a phone)."""

    from learnloop.scheduling import scheduler
    from learnloop_sidecar.handlers import queue as queue_handler

    monkeypatch.setattr(queue_handler, "today_head_served", lambda _vault: True)

    def support(queue, session, config):
        if session.session_id is None or len(queue) < 2:
            return None
        return 0.5, list(queue[1:])

    monkeypatch.setattr(scheduler, "_exploration_support", support)
    monkeypatch.setattr(scheduler, "_exploration_draws", lambda *_args: (0.1 if explored else 0.9, 0.0))


def _today_offer(repository) -> dict | None:
    with repository.connection() as connection:
        row = connection.execute("SELECT * FROM router_decisions WHERE decision_kind = 'today_offer' "
                                 "ORDER BY created_at DESC, id DESC").fetchone()
    return dict(row) if row is not None else None


@pytest.mark.parametrize("explored", [False, True], ids=["greedy", "explored"])
def test_r25_a_forced_head_is_published_with_its_decision_and_probability_1_from_the_tag(tmp_path, monkeypatch,
                                                                                         explored):
    from tests.probe_router_authority_helpers import call
    from tests.probe_router_owned_helpers import SECOND

    case = _pinned_continuation(tmp_path, monkeypatch, AT)
    _near_ties(monkeypatch, explored=explored)
    queue = call(case.ctx, "get_today_queue", {"sessionId": case.session_id})
    served = [item["practiceItemId"] for section in queue["sections"] for item in section["items"]]
    assert served[0] == SECOND
    decision = _today_offer(case.repository)
    assert decision is not None, "the offer is published with its decision"
    assert decision["chosen_practice_item_id"] == SECOND
    assert (decision["propensity"], decision["propensity_kind"]) == (1.0, "deterministic")


@pytest.mark.parametrize("explored", [False, True], ids=["greedy", "explored"])
def test_r25_below_the_tag_the_forced_head_was_recomposed_without_its_pin(tmp_path, monkeypatch, explored):
    """mvp-0.76's: the probability calculation recomposed each near-tie outcome without the pin's promotion, so the
    forced head either logged less than 1 or mismatched and went out without a decision."""

    from tests.probe_router_authority_helpers import call
    from tests.probe_router_owned_helpers import SECOND

    case = _pinned_continuation(tmp_path, monkeypatch, BEFORE)
    _near_ties(monkeypatch, explored=explored)
    queue = call(case.ctx, "get_today_queue", {"sessionId": case.session_id})
    served = [item["practiceItemId"] for section in queue["sections"] for item in section["items"]]
    assert served[0] == SECOND
    decision = _today_offer(case.repository)
    if explored:
        assert decision is None  # the recomposed head was the explored one: published without a decision
    else:
        assert decision["chosen_practice_item_id"] == SECOND and decision["propensity"] == 0.5


# -- G2-R33 (finding 13, decided: option (a)): the probe ranking reads expected information over the observed posterior


@pytest.mark.parametrize("tag", [BEFORE, AT])
def test_r33_an_observed_family_is_ranked_on_its_information_not_a_hand_set_multiplier(tmp_path, monkeypatch, tag):
    """After one observation of family F, the hypothesis-information fallback values F's next instrument at 0.40 and
    another family's at 0.30. Below the tag the 0.6 multiplier made 0.40 rank as 0.24 and lose; from it the ranking
    is the information itself (computed over the observed posterior) and its basis is recorded with the instrument."""

    from dataclasses import replace

    from learnloop.diagnosis import probe_episodes as PE
    from learnloop.diagnosis.probe_episodes import OBSERVED_POSTERIOR_RANKING, enter_episode, eligible_instruments
    from learnloop.diagnosis.probe_presentations import commit_presentation, serve_presentation
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    from tests.helpers import set_algorithm_version
    from tests.probe_block_end_helpers import _submit
    from tests.probe_policy_helpers import CLOCK, ITEM_2, ITEM_3, ITEM_ID, LO_ID, _setup

    loaded, repository = _setup(tmp_path, items=(ITEM_ID, ITEM_2, ITEM_3))
    set_algorithm_version(VaultPaths(loaded.root, loaded.config), tag)
    loaded = load_vault(loaded.root)
    real_resolve = PE.resolve_instrument
    item_of: dict[int, str] = {}

    def resolve(vault, repository_, item, hypothesis_set):
        resolved = real_resolve(vault, repository_, item, hypothesis_set)
        if resolved is None:
            return None
        instrument, slot_map = resolved
        if item.id == ITEM_3:
            instrument = replace(instrument, family_template_id="another_family")
        item_of[id(instrument)] = item.id
        return instrument, slot_map

    information = {ITEM_ID: 0.5, ITEM_2: 0.40, ITEM_3: 0.30}
    monkeypatch.setattr(PE, "resolve_instrument", resolve)
    monkeypatch.setattr(PE, "instrument_expected_information_gain",
                        lambda _belief, instrument, _slot_map: information[item_of[id(instrument)]])
    # The hypothesis-information fallback: no adequate predictive target set.
    monkeypatch.setattr(PE, "instrument_predictive_information_gain", lambda *_args: SimpleNamespace(
        eig_nats=0.0, prior_predictive_entropy=0.0, target_count=0))
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    first = next(entry for entry in eligible_instruments(loaded, repository, episode) if entry.item.id == ITEM_ID)
    presentation = commit_presentation(loaded, repository, episode, first, clock=CLOCK)
    serve_presentation(repository, presentation.id, vault=loaded, clock=CLOCK)
    _submit(loaded, repository, item_id=ITEM_ID, presentation_id=presentation.id, score=2)
    after = eligible_instruments(loaded, repository, repository.probe_episode(episode.id))
    assert [entry.selection_objective for entry in after] == ["hypothesis_eig", "hypothesis_eig"]
    ranked = [entry.item.id for entry in after]
    if tag == AT:
        assert ranked == [ITEM_2, ITEM_3]
        assert all(entry.redundancy_penalty == 1.0 for entry in after)
        assert after[0].selection_components()["ranking_basis"] == OBSERVED_POSTERIOR_RANKING
    else:
        assert ranked == [ITEM_3, ITEM_2]
        assert "ranking_basis" not in after[0].selection_components()
