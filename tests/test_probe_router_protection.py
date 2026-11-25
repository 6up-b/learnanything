"""The probe doors ask the session serve's exam verdict (G2-R21, G2-R22: the probe router's fix round 3).

Every door that picks or serves a probe instrument shows its item in the session, so it reads the ``session_serve`` row
of ``exam_material.SURFACE_SETS`` through the one verdict (``exam_material.serve_refusals``) before anything is
priced, reserved or marked served: instrument selection (``probe_episodes.item_refusals`` inside
``eligible_instruments``), the learner lane's offer and its reread (``candidate_unservable``), and the serve itself
(``serve_presentation``), which retires a pin that became protected. A protected item reads as an absent one.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.exam_protection_review_helpers import _problem_book, _with_exercise
from tests.probe_router_authority_helpers import PROBE_ITEM, call
from tests.probe_router_owned_helpers import SECOND, grading_ready, selected


def _hold_out(case, item_id: str = PROBE_ITEM) -> None:
    """Mark the passage ``item_id`` was made from held out for evaluation, after the pin (the owner's later mark)."""

    _problem_book(case.repository)
    _with_exercise(case.root, item_id, source_id="src_problems", extraction_id="ext_problems", span_id="s2")
    save_unit_selection(case.repository, "ext_problems", ["ex", "notes"],
                        exam_use_modes={"ex": "held_out_evaluation"})
    case.vault = load_vault(case.root)
    case.ctx.load(case.root)


def _presentation(case):
    return case.repository.probe_presentation(case.offer["presentationId"])


def _absent(vault, item_id: str):
    """The vault as if ``item_id`` were not in it (the absent copy a protected item must read as)."""

    return replace(vault, practice_items={key: value for key, value in vault.practice_items.items() if key != item_id})


def test_a_pin_held_out_after_it_was_accepted_is_never_marked_served_by_the_contract_request(tmp_path, monkeypatch):
    """The split request: the item request refuses the held-out item and the contract request, separately, must not
    mark its presentation served. It ends the pin unshown and answers why."""

    from learnloop_sidecar.errors import SidecarError

    case = selected(tmp_path, monkeypatch)
    _hold_out(case)
    grading_ready(monkeypatch)
    with pytest.raises(SidecarError) as refused:
        call(case.ctx, "get_practice_item", {"practiceItemId": PROBE_ITEM, "sessionId": "sess"})
    assert refused.value.code == "held_out_material"
    contract = call(case.ctx, "get_probe_contract", {"practiceItemId": PROBE_ITEM, "sessionId": "sess"})
    assert contract["active"] is False and contract["reason"] == "probe_item_protected"
    presentation = _presentation(case)
    assert presentation.status == "ended" and presentation.end_reason == "invalidated"
    assert presentation.served_at is None


def test_an_item_reserved_for_a_held_out_exam_is_never_served_as_a_probe(tmp_path, monkeypatch):
    case = selected(tmp_path, monkeypatch)
    monkeypatch.setattr(Repository, "reserved_exam_pool_item_ids", lambda _self: {PROBE_ITEM})
    grading_ready(monkeypatch)
    contract = call(case.ctx, "get_probe_contract", {"practiceItemId": PROBE_ITEM, "sessionId": "sess"})
    assert contract["active"] is False and contract["reason"] == "probe_item_protected"
    assert _presentation(case).served_at is None


def test_instrument_selection_reads_a_protected_item_as_an_absent_one(tmp_path, monkeypatch):
    from learnloop.diagnosis.probe_episodes import eligible_instruments

    case = selected(tmp_path, monkeypatch)
    episode = case.repository.probe_episode(_presentation(case).probe_episode_id)
    # The accepted pin reserves its episode for its own item: release it to ask what selection ranks.
    case.repository.end_probe_presentation(case.offer["presentationId"], end_reason="abandoned")
    before = [entry.item.id for entry in eligible_instruments(case.vault, case.repository, episode)]
    assert SECOND in before
    _hold_out(case, SECOND)
    protected = [entry.item.id for entry in eligible_instruments(case.vault, case.repository, episode)]
    absent = [entry.item.id for entry in eligible_instruments(_absent(case.vault, SECOND), case.repository, episode)]
    assert SECOND not in protected
    assert protected == absent


def test_the_learner_lanes_offer_never_names_a_protected_instrument(tmp_path, monkeypatch):
    """Protected after the selection: the status reads the selection void and acceptance pins nothing."""

    from learnloop.diagnosis.causal_orchestrator import candidate_unservable

    case = selected(tmp_path, monkeypatch)
    monkeypatch.setattr(Repository, "reserved_exam_pool_item_ids", lambda _self: {PROBE_ITEM})
    candidate = {"practice_item_id": PROBE_ITEM}
    assert candidate_unservable(case.vault, case.repository, candidate) == "probe_item_protected"

