"""P4 step 3 -- the staged policy's within-block selector upgraded to robust EVSI per
minute (spec_p4 §6.4, §16.1/§16.3). The selector ranks ONLY within the feasible set the
constraint engine gated; the policy stays shadow-mode.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import action_loss as AL
from learnloop.services import controller_actions as A
from learnloop.services import controller_snapshot as cs
from learnloop.services import controller_store as store
from learnloop.services import staged_policy as sp
from learnloop.services.scheduler import SchedulerSession
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)


@pytest.fixture
def wired(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    return vault, repo


def _session():
    return SchedulerSession(session_id="s1", available_minutes=15)


def _loss_table():
    return AL.build_loss_table(
        routes=[
            {"reason": "memory_lapse", "first_intervention": "reveal"},
            {"reason": "false_belief_or_confusion", "first_intervention": "contrast"},
        ],
        duration_overrides={"reveal": 2.0, "contrast": 4.0},
    )


_PRIOR = {"memory_lapse": 0.5, "false_belief_or_confusion": 0.5}
_SEP = {"memory_lapse": {"e1": 0.9, "e2": 0.1}, "false_belief_or_confusion": {"e1": 0.1, "e2": 0.9}}


def test_evsi_selector_ranks_only_within_feasible_set(wired):
    vault, repo = wired
    good = cs.Candidate(candidate_ref="good", active=True, purpose="diagnostic",
                        surface_hash="G1")
    dead = cs.Candidate(candidate_ref="dead", active=False, purpose="diagnostic",
                        surface_hash="D1")
    loss = _loss_table()
    diagnostic = sp.DiagnosticSelector(
        loss_table=loss,
        candidates={
            "good": {"members": [_SEP], "prior": _PRIOR, "expected_minutes": 0.5},
            # 'dead' carries an even stronger EVSI signal, but it is INFEASIBLE and can
            # never be resurrected by a score.
            "dead": {"members": [_SEP], "prior": _PRIOR, "expected_minutes": 0.1},
        },
    )
    res = sp.decide(
        vault, repo, _session(),
        signals=sp.StateSignals(decision_relevant_robust_value=0.9),
        candidates=[good, dead], diagnostic=diagnostic, clock=CLOCK,
    )
    assert res.trace["ranking_inputs"]["selector"] == "robust_evsi_per_minute"
    assert res.chosen_candidate_ref == "good"
    assert "dead" not in res.trace["feasible_set"]
    assert "dead" in res.trace["exclusions"]
    # The decision stays shadow mode.
    assert store.decision_row(repo, res.decision_id)["mode"] == "shadow"
    # The EVSI products are on the trace.
    assert res.trace["ranking_inputs"]["evsi"]["best_ref"] == "good"


def _tied_diagnostic(randomize=True):
    material = {"members": [_SEP], "prior": _PRIOR, "expected_minutes": 0.5}
    return sp.DiagnosticSelector(
        loss_table=_loss_table(),
        candidates={"a": dict(material), "b": dict(material)},
        randomize=randomize,
    )


def _tied_report():
    from learnloop.services.constraint_engine import FeasibilityReport

    a = cs.Candidate(candidate_ref="a", active=True, purpose="diagnostic", surface_hash="A")
    b = cs.Candidate(candidate_ref="b", active=True, purpose="diagnostic", surface_hash="B")
    return FeasibilityReport(feasible=[a, b], excluded=[], per_candidate={}, manifest_hash="m")


def test_epsilon_tiebreak_seed_is_decision_specific():
    # Audit M2/F4: two IDENTICAL-value candidates are exactly tied, so the ε tie-break
    # fires. The seed must be decision-specific -- two different decisions (snapshot
    # hashes) draw differently, and the same decision replayed draws identically. Pre-fix
    # the seed was a static "evsi_tiebreak" constant, so every decision drew the same
    # value (a hidden fixed bias in which tied candidate wins).
    report = _tied_report()
    diagnostic = _tied_diagnostic()
    _, _, _, _, a1 = sp._select_diagnostic(report, diagnostic, repository=None, clock=CLOCK, snapshot_hash="hashA")
    _, _, _, _, a1_replay = sp._select_diagnostic(report, diagnostic, repository=None, clock=CLOCK, snapshot_hash="hashA")
    _, _, _, _, a2 = sp._select_diagnostic(report, diagnostic, repository=None, clock=CLOCK, snapshot_hash="hashB")

    assert a1 is not None and a1["randomized"] is True
    assert a1["draw"] == a1_replay["draw"] and a1["seed"] == a1_replay["seed"]
    assert a2["seed"] != a1["seed"]
    assert a2["draw"] != a1["draw"]


def test_randomize_refuses_static_fallback_seed_without_snapshot():
    # Audit M2/F4: randomize with no snapshot hash and no explicit seed has no
    # decision-specific seed to derive -> refuse rather than silently fall back to a
    # static constant.
    report = _tied_report()
    diagnostic = _tied_diagnostic()
    with pytest.raises(ValueError):
        sp._select_diagnostic(report, diagnostic, repository=None, clock=CLOCK, snapshot_hash=None)


def test_evsi_stop_is_a_typed_stop_not_no_feasible_activity(wired):
    vault, repo = wired
    # A feasible question with negligible separating value + high minutes cost -> the LCB
    # stop rule fires; that is a typed stop, distinct from "no feasible activity".
    weak = {"memory_lapse": {"e1": 0.5, "e2": 0.5},
            "false_belief_or_confusion": {"e1": 0.5, "e2": 0.5}}
    cand = cs.Candidate(candidate_ref="weak", active=True, purpose="diagnostic", surface_hash="W1")
    diagnostic = sp.DiagnosticSelector(
        loss_table=_loss_table(),
        candidates={"weak": {"members": [weak], "prior": _PRIOR, "expected_minutes": 20.0}},
    )
    res = sp.decide(
        vault, repo, _session(),
        signals=sp.StateSignals(decision_relevant_robust_value=0.9),
        candidates=[cand], diagnostic=diagnostic, clock=CLOCK,
    )
    assert res.action == A.STOP
    assert res.stop_reason == A.STOP_NO_POSITIVE_ROBUST_VALUE
