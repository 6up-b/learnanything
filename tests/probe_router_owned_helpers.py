"""Shared setups for the probe router's router-owned episodes (``tests/test_probe_router_worth_gates.py``,
``tests/test_probe_router_continuation.py``): a learner-lane probe the router selected and the learner accepted, on a
learning object with a second instrument, and the legacy worth functions made to raise."""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.diagnosis import causal_orchestrator
from learnloop.diagnosis import followups
from learnloop.diagnosis import probe_blocks
from learnloop.diagnosis import probe_completion
from learnloop.diagnosis import probe_facts
from learnloop.diagnosis import voi_stopping as voi
from learnloop.router_objective import probe_coin as PC

from tests.causal_orchestrator_helpers import PROBE_ITEM
from tests.helpers import append_config_toml
from tests.probe_router_authority_helpers import call, read_status, sidecar

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


def sentinels(monkeypatch) -> None:
    for module, name in LEGACY_WORTH:
        def raiser(*_args, _name=f"{module.__name__}.{name}", **_kwargs):
            raise AssertionError(f"a legacy worth gate was asked about a router-selected probe: {_name}")

        monkeypatch.setattr(module, name, raiser)


#: A second instrument on the same card and learning object, so the episode has another probe to continue with.
SECOND = "pi_causal_probe_002"


def selected(tmp_path, monkeypatch, *, version: str = LATEST_ALGORITHM_VERSION):
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
    status = read_status(ctx, {"misconceptionId": case.first})
    assert status["routerState"] == "selected"
    offer = call(ctx, "causal_probe_offer_action", {"factorId": case.factor})["offer"]
    assert offer["accepted"] is True
    case.ctx, case.offer, case.decision_id = ctx, offer, status["routerDecisionId"]
    return case




def grading_ready(monkeypatch) -> None:
    """The serving door's grading provider, ready (no model is asked: nothing here grades)."""

    monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                        lambda *_a, **_k: ("fake", SimpleNamespace(ready=True), object()))


def answer_the_pin(case, monkeypatch, *, score: int = 0):
    """Serve the accepted pin through the sidecar's door and answer it: its block closes, the episode continues."""

    from tests.probe_block_end_helpers import _submit

    grading_ready(monkeypatch)
    served = call(case.ctx, "get_probe_contract", {"practiceItemId": PROBE_ITEM, "sessionId": "sess"})
    assert served["active"] is True and served["presentationId"] == case.offer["presentationId"]
    return _submit(case.vault, case.repository, item_id=PROBE_ITEM, presentation_id=case.offer["presentationId"],
                   score=score)
