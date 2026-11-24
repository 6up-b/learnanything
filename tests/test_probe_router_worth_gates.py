"""G2: downstream of the router's selection no worth gate decides a probe again (``docs/reviews/refactor-g2-design.md``
§2c, sites G to K; ``learnloop.diagnosis.probe_authority``).

At ``PROBE_ROUTER_ALGORITHM_VERSION`` a probe the router selected (its presentation pins the router's decision) is
served, answered, closes its block and is scheduled with every legacy worth function made to raise: the causal gate's
verdict, the general follow-up's value suppression, the episode value decision (the scheduler's admission, the serving
door's veto, a block's continuation, an episode's value stop), action equivalence and the robust gate. Its episode is
bounded by its count. A probe of any other origin keeps those gates, and below the tag nothing changes.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.diagnosis import causal_orchestrator
from learnloop.diagnosis import followups
from learnloop.diagnosis import probe_blocks
from learnloop.diagnosis import probe_completion
from learnloop.diagnosis import probe_facts
from learnloop.diagnosis import voi_stopping as voi
from learnloop.diagnosis.probe_authority import (
    router_pin,
    router_selected_presentation,
    router_selected_rows,
)
from learnloop.diagnosis.probe_episodes import router_selected_episode
from learnloop.router_objective import probe_coin as PC

from tests.helpers import append_config_toml
from tests.probe_block_end_helpers import _submit
from tests.probe_router_authority_helpers import PROBE_ITEM, TAG, call, divergent_factor, sidecar

#: Every legacy function that answered "is this probe worth it?" downstream of a miss (sites B, G to K).
LEGACY_WORTH = (
    (causal_orchestrator, "decide_probe"),
    (probe_facts, "probe_verdict"),
    (followups, "_intervention_value"),
    (voi, "probe_episode_decision"),
    (probe_blocks, "_next_observation_does_not_pay"),
    (probe_completion, "_plausible_actions_agree"),
    (probe_completion, "_robust_completion_override"),
    (probe_completion, "_value_of_information_stop"),
)


def _sentinels(monkeypatch) -> None:
    for module, name in LEGACY_WORTH:
        def raiser(*_args, _name=f"{module.__name__}.{name}", **_kwargs):
            raise AssertionError(f"a legacy worth gate was asked about a router-selected probe: {_name}")

        monkeypatch.setattr(module, name, raiser)


#: A second instrument on the same card and learning object, so the episode has another probe to continue with.
SECOND = "pi_causal_probe_002"


def _selected(tmp_path, monkeypatch, *, version: str = LATEST_ALGORITHM_VERSION):
    """The learner lane's probe, selected by the router (the probe coin fixed to ask) and accepted, on a learning
    object with a second instrument left after it."""

    from learnloop.vault.loader import load_vault

    from tests.causal_orchestrator_helpers import _activate_probe_candidate, _add_probe_item, _seed_factor, _vault
    from tests.helpers import admit_probe_instrument_card

    _vault_, repository, root = _vault(tmp_path, with_probe_item=True, version=version)
    _add_probe_item(root, item_id=SECOND, surface="second_contrast_surface")
    append_config_toml(root, "\n[router_objective]\nstop_coin = 0.2\n")
    factor, first, second = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM, SECOND))
    _activate_probe_candidate(repository, factor, first, second)
    case = SimpleNamespace(vault=load_vault(root), repository=repository, root=root, factor=factor, first=first)
    monkeypatch.setattr(PC, "draw_uniform", lambda _seed: 0.0)
    ctx = sidecar(case.root)
    status = call(ctx, "causal_repair_status", {"misconceptionId": case.first})["repairStatus"]
    assert status["routerState"] == "selected"
    offer = call(ctx, "causal_probe_offer_action", {"factorId": case.factor})["offer"]
    assert offer["accepted"] is True
    case.ctx, case.offer = ctx, offer
    return case


def test_a_router_selected_probe_is_served_answered_and_ended_with_every_legacy_worth_gate_raising(tmp_path,
                                                                                                   monkeypatch):
    case = _selected(tmp_path, monkeypatch)
    _sentinels(monkeypatch)
    presentation_id, episode_id = case.offer["presentationId"], case.offer["episodeId"]
    monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                        lambda *_a, **_k: ("fake", SimpleNamespace(ready=True), object()))
    served = call(case.ctx, "get_probe_contract", {"practiceItemId": PROBE_ITEM, "sessionId": "sess"})
    assert served["active"] is True and served["presentationId"] == presentation_id
    result = _submit(case.vault, case.repository, item_id=PROBE_ITEM, presentation_id=presentation_id, score=0)
    # The router decided one question: its answer closes the block, with no value decision on another.
    assert result.probe_block_end is not None
    after = case.repository.probe_episode(episode_id)
    # Completion read only evidence and the count: never a value stop, action equivalence or the robust gate; the
    # second instrument is left, so the episode continues.
    assert after.status == "in_progress" and after.completion_reason is None
    # The scheduler ranks the second instrument without a value admission, and the serving door commits it without a
    # value veto.
    from learnloop.scheduling.scheduler import OfferTrace

    from tests.voi_stopping_helpers import _build

    trace = OfferTrace()
    _build(case.vault, case.repository, trace=trace)
    assert not [d for d in trace.voi_decisions if d["site"] == voi.SITE_PROBE_EPISODE]
    second = call(case.ctx, "get_probe_contract", {"practiceItemId": SECOND, "sessionId": "sess"})
    assert second["active"] is True, second
    assert router_selected_presentation(case.vault, case.repository.probe_presentation(presentation_id))
    assert router_selected_episode(case.vault, case.repository, after)


def test_the_count_bounds_a_router_selected_episode_and_value_decides_none_of_it(tmp_path, monkeypatch):
    case = _selected(tmp_path, monkeypatch)
    rows = [{"selection_components": {"causal_probe": {"router_decision_id": "d"}}}]
    assert router_selected_rows(case.vault, rows)
    assert not probe_completion.value_decides_episode(case.vault, case.repository, rows)
    assert probe_completion.episode_maximum_binds(case.vault, case.repository, rows)
    episode = case.repository.probe_episode(case.offer["episodeId"])
    reason, body = __import__("learnloop.diagnosis.probe_presentations", fromlist=["x"]).probe_value_block_reason(
        case.vault, case.repository, episode, PROBE_ITEM, session_id="sess")
    assert (reason, body) == (None, None)


def test_a_probe_of_another_origin_keeps_its_gates(tmp_path, monkeypatch):
    case = _selected(tmp_path, monkeypatch)
    legacy = [{"selection_components": {"causal_probe": {"decision_receipt_id": "r"}}}, {"selection_components": {}}]
    assert not router_pin(legacy[0]["selection_components"]) and not router_selected_rows(case.vault, legacy)
    assert probe_completion.value_decides_episode(case.vault, case.repository, legacy)


def test_below_the_tag_a_pinned_router_decision_is_no_dispatch(tmp_path, monkeypatch):
    case = divergent_factor(tmp_path, version=TAG)
    rows = [{"selection_components": {"causal_probe": {"router_decision_id": "d"}}}]
    assert not router_selected_rows(case.vault, rows)
    assert probe_completion.value_decides_episode(case.vault, case.repository, rows)
    with pytest.raises(AssertionError):
        _sentinels(monkeypatch)
        voi.probe_episode_decision()
