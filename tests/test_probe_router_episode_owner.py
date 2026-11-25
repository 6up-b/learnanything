"""One owner of a probe episode's state (G2-R24 and on: the probe router's fix round 3).

A decision is validated against the episode as it is inside the write transaction, not as it was read before the
valuation: the continuation job cannot overwrite the learner's "Stop diagnosing and teach me", nor pin against an old
segment; a stale process (the vault upgraded while it had it open) commits neither arm of the continuation nor a first
acceptance's episode rows.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.daily_plan import learner_probe as LP
from learnloop.daily_plan import probe_continuation as PCN
from learnloop.db.writer_fence import WriterFenceRefusal
from learnloop.router.plan_log import PROBE_CONTINUATION_SURFACE
from learnloop.router_objective import probe_coin as PC

from tests.probe_router_authority_helpers import PROBE_ITEM, call, read_status, table_rows
from tests.probe_router_owned_helpers import answer_the_pin, selected

#: The tables a probe decision, its episode and its pin touch.
EPISODE_TABLES = ("probe_episodes", "probe_presentations", "probe_state_segments", "hypothesis_sets",
                  "router_decisions", "policy_experiment_assignments", "decision_objectives")


def _answered(tmp_path, monkeypatch, *, u: float):
    case = selected(tmp_path, monkeypatch)
    answer_the_pin(case, monkeypatch)
    case.episode_id = case.offer["episodeId"]
    monkeypatch.setattr(PC, "draw_uniform", lambda _seed: u)
    return case


def _continuations(case) -> list[dict]:
    return table_rows(case.repository, "router_decisions", "WHERE surface = ?", (PROBE_CONTINUATION_SURFACE,))


def _snapshot(repository) -> dict[str, list[dict]]:
    return {table: table_rows(repository, table) for table in EPISODE_TABLES}


def _upgraded_elsewhere(repository) -> None:
    """Another process activated a later tag: the fence row moves while this process stays bound to its own tag."""

    with closing(sqlite3.connect(repository.sqlite_path)) as connection:
        connection.execute("INSERT INTO writer_fence(id, algorithm_version, updated_at) VALUES (1, 'mvp-9.99', 'x') "
                           "ON CONFLICT(id) DO UPDATE SET algorithm_version = excluded.algorithm_version")
        connection.commit()


@pytest.mark.parametrize("u", [0.0, 0.9], ids=["ask", "stop"])
def test_the_job_never_overwrites_the_learners_stop_made_while_it_valued(tmp_path, monkeypatch, u):
    """The learner says "Stop diagnosing and teach me" while the job values the next observation: the job's commit
    finds the episode converted and records nothing, whichever arm it drew."""

    from learnloop.diagnosis.probe_controls import stop_diagnosing_and_teach

    case = _answered(tmp_path, monkeypatch, u=u)
    (request,) = PCN.requested(case.vault, case.repository)
    real = LP.value

    def valued_while_the_learner_stops(*args, **kwargs):
        out = real(*args, **kwargs)
        episode = case.repository.probe_episode(case.episode_id)
        assert stop_diagnosing_and_teach(case.vault, case.repository, episode.learning_object_id) is not None
        return out

    monkeypatch.setattr(LP, "value", valued_while_the_learner_stops)
    assert PCN.decide(case.vault, case.repository, request) is None
    episode = case.repository.probe_episode(case.episode_id)
    assert (episode.status, episode.completion_reason) == ("converted_to_tutoring", "converted_to_tutoring")
    assert _continuations(case) == []
    assert case.repository.active_probe_presentation(case.episode_id) is None


@pytest.mark.parametrize("u", [0.0, 0.9], ids=["ask", "stop"])
def test_a_stale_worker_commits_neither_arm_of_the_continuation(tmp_path, monkeypatch, u):
    case = _answered(tmp_path, monkeypatch, u=u)
    (request,) = PCN.requested(case.vault, case.repository)
    before = _snapshot(case.repository)
    _upgraded_elsewhere(case.repository)
    with pytest.raises(WriterFenceRefusal):
        PCN.decide(case.vault, case.repository, request)
    assert _snapshot(case.repository) == before


def test_a_stale_first_acceptance_writes_no_episode_lock_or_segment(tmp_path, monkeypatch):
    """With no episode open on the learning object, a stale process's acceptance enters none: the entry and the pin
    are one fenced transaction."""

    from tests.causal_orchestrator_helpers import _activate_probe_candidate, _add_probe_item, _seed_factor, _vault
    from tests.helpers import admit_probe_instrument_card, append_config_toml
    from tests.probe_router_authority_helpers import sidecar
    from tests.probe_router_owned_helpers import SECOND

    _vault_, repository, root = _vault(tmp_path, with_probe_item=True, version=LATEST_ALGORITHM_VERSION)
    _add_probe_item(root, item_id=SECOND, surface="second_contrast_surface")
    append_config_toml(root, "\n[router_objective]\nstop_coin = 0.2\n")
    factor, first, second = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM, SECOND))
    _activate_probe_candidate(repository, factor, first, second)
    monkeypatch.setattr(PC, "draw_uniform", lambda _seed: 0.0)
    ctx = sidecar(root)
    assert read_status(ctx, {"misconceptionId": first})["routerState"] == "selected"
    for episode in repository.list_probe_episodes(statuses=("in_progress", "pending_items")):
        repository.update_probe_episode_status(episode.id, status="abandoned")
    before = _snapshot(repository)
    _upgraded_elsewhere(repository)
    with pytest.raises(WriterFenceRefusal):
        call(ctx, "causal_probe_offer_action", {"factorId": factor})
    assert _snapshot(repository) == before



def test_a_rejected_teach_me_now_records_no_consent_on_any_factor(tmp_path):
    """A stale pair (cause A, an open factor of cause B): refused before anything is written, so B's quick check is
    not suppressed (G2-R35)."""

    from learnloop_sidecar.errors import SidecarError

    from tests.causal_orchestrator_helpers import _seed_factor, _vault
    from tests.probe_router_authority_helpers import count, sidecar

    _vault_, repository, root = _vault(tmp_path, with_probe_item=True, version=LATEST_ALGORITHM_VERSION)
    _factor_a, cause_a, _ = _seed_factor(repository, attempt_id="att_a")
    factor_b, _cause_b, _ = _seed_factor(repository, attempt_id="att_b")
    ctx = sidecar(root)
    before = (count(repository, "router_learner_preferences"), count(repository, "causal_probe_preference_events"))
    with pytest.raises(SidecarError) as refused:
        call(ctx, "causal_teach_me_now", {"misconceptionId": cause_a, "factorId": factor_b})
    assert refused.value.code == "invalid_request"
    assert (count(repository, "router_learner_preferences"),
            count(repository, "causal_probe_preference_events")) == before
