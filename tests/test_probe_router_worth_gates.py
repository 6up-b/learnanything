"""G2: downstream of the router's selection no worth gate decides a probe again (``docs/reviews/refactor-g2-design.md``
§2c, sites G to K; ``learnloop.diagnosis.probe_authority``).

At ``PROBE_ROUTER_ALGORITHM_VERSION`` a probe the router selected (its presentation pins the router's decision) is
served, answered, closes its block and is scheduled with every legacy worth function made to raise: the causal gate's
verdict, the general follow-up's value suppression, the episode value decision (the scheduler's admission, the serving
door's veto, a block's continuation, an episode's value stop), action equivalence and the robust gate. Its episode is
bounded by its count. A probe of any other origin keeps those gates, and below the tag nothing changes.
"""

from __future__ import annotations


import pytest

from learnloop.diagnosis import probe_completion
from learnloop.diagnosis import voi_stopping as voi
from learnloop.diagnosis.probe_authority import (
    router_pin,
    router_selected_presentation,
    router_selected_rows,
)
from learnloop.diagnosis.probe_episodes import router_selected_episode

from tests.probe_router_authority_helpers import PROBE_ITEM, TAG, call, divergent_factor
from tests.probe_router_owned_helpers import SECOND, answer_the_pin, selected, sentinels


def test_a_router_selected_probe_is_served_answered_and_ended_with_every_legacy_worth_gate_raising(tmp_path,
                                                                                                   monkeypatch):
    case = selected(tmp_path, monkeypatch)
    sentinels(monkeypatch)
    presentation_id, episode_id = case.offer["presentationId"], case.offer["episodeId"]
    result = answer_the_pin(case, monkeypatch)
    # The router decided one question: its answer closes the block, with no value decision on another.
    assert result.probe_block_end is not None
    after = case.repository.probe_episode(episode_id)
    # Completion read only evidence and the count: never a value stop, action equivalence or the robust gate; the
    # second instrument is left, so the episode continues.
    assert after.status == "in_progress" and after.completion_reason is None
    # Whether the second instrument is asked is the router's continuation decision: until its job has run, the door
    # commits nothing; then the router's pin (the coin here asks) is served, with no value veto, and the scheduler
    # makes no value decision on it.
    pending = call(case.ctx, "get_probe_contract", {"practiceItemId": SECOND, "sessionId": "sess"})
    assert (pending["active"], pending["reason"]) == (False, "router_decision_pending")
    case.ctx.post_attempt_worker.run_pending("probe_router")
    from learnloop.scheduling.scheduler import OfferTrace

    from tests.voi_stopping_helpers import _build

    trace = OfferTrace()
    _build(case.vault, case.repository, trace=trace)
    assert not [d for d in trace.voi_decisions if d["site"] == voi.SITE_PROBE_EPISODE]
    second = call(case.ctx, "get_probe_contract", {"practiceItemId": SECOND, "sessionId": "sess"})
    assert second["active"] is True, second
    assert router_selected_presentation(case.repository, case.repository.probe_presentation(second["presentationId"]))
    assert router_selected_presentation(case.repository, case.repository.probe_presentation(presentation_id))
    assert router_selected_episode(case.vault, case.repository, after)


def test_the_count_bounds_a_router_selected_episode_and_value_decides_none_of_it(tmp_path, monkeypatch):
    case = selected(tmp_path, monkeypatch)
    # The rows' pin names the router's decision made at the tag (authority is the decision row's).
    rows = [{"selection_components": {"causal_probe": {"router_decision_id": case.decision_id}}}]
    assert router_selected_rows(case.repository, rows)
    assert not probe_completion.value_decides_episode(case.vault, case.repository, rows)
    assert probe_completion.episode_maximum_binds(case.vault, case.repository, rows)
    episode = case.repository.probe_episode(case.offer["episodeId"])
    reason, body = __import__("learnloop.diagnosis.probe_presentations", fromlist=["x"]).probe_value_block_reason(
        case.vault, case.repository, episode, PROBE_ITEM, session_id="sess")
    assert (reason, body) == (None, None)


def test_a_probe_of_another_origin_keeps_its_gates(tmp_path, monkeypatch):
    case = selected(tmp_path, monkeypatch)
    legacy = [{"selection_components": {"causal_probe": {"decision_receipt_id": "r"}}}, {"selection_components": {}}]
    assert not router_pin(legacy[0]["selection_components"]) and not router_selected_rows(case.repository, legacy)
    assert probe_completion.value_decides_episode(case.vault, case.repository, legacy)


def test_below_the_tag_a_pinned_router_decision_is_no_dispatch(tmp_path, monkeypatch):
    case = divergent_factor(tmp_path, version=TAG)
    # A pin naming no decision the router made at its tag (here none at all) dispatches nothing.
    rows = [{"selection_components": {"causal_probe": {"router_decision_id": "d"}}}]
    assert not router_selected_rows(case.repository, rows)
    assert probe_completion.value_decides_episode(case.vault, case.repository, rows)
    with pytest.raises(AssertionError):
        sentinels(monkeypatch)
        voi.probe_episode_decision()
