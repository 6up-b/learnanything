"""The intent view after its check split (``IntentServing.frozen``) and the teach-back site's value context read
nothing: a queue build asks both from values its shell read before."""

from __future__ import annotations

import pytest

from learnloop.diagnosis import voi_stopping as voi
from learnloop.scheduling.intent.serving import intent_serving
from learnloop.scheduling.scheduler import SchedulerSession, check_admission, read_due_queue

from tests.due_queue_helpers import CLOCK, SESSION, build_intent_targets_vault, build_rich_vault


def _no_reads(*_args, **_kwargs):
    raise AssertionError("the frozen view read the repository")


def test_the_frozen_view_answers_as_the_live_one_without_reading(tmp_path, monkeypatch):
    vault, repository = build_intent_targets_vault(tmp_path / "vault")
    now = CLOCK.now()
    live = intent_serving(vault, repository, now=now)
    live.bind_admission(check_admission(vault, repository, now=now, intent_view=live, reasons=True))
    states = repository.practice_item_states()
    item_ids = sorted(vault.practice_items)
    expected = {
        item_id: (
            live.withhold_reason(item_id),
            live.effective_due_or_none(item_id, states.get(item_id)),
            live.pushes(item_id, states.get(item_id)),
        )
        for item_id in item_ids
    }
    expected_checks = [(check.commitment_id, check.servable, check.refused) for check in live.due_checks()]
    frozen = live.frozen()
    assert all(
        getattr(frozen, name) is None
        for name in ("_eligibility", "_admission", "_admission_factory", "_gate_factory", "_followup_gate")
    )
    assert frozen._anchor_loader is None and frozen._anchors is not None, "the targets need the anchors: loaded"
    monkeypatch.setattr(repository, "connection", _no_reads)
    assert {
        item_id: (
            frozen.withhold_reason(item_id),
            frozen.effective_due_or_none(item_id, states.get(item_id)),
            frozen.pushes(item_id, states.get(item_id)),
        )
        for item_id in item_ids
    } == expected
    assert [(check.commitment_id, check.servable, check.refused) for check in frozen.due_checks()] == expected_checks
    assert any(due is not None for _reason, due, _push in expected.values()), "the vault reaches an effective due"


def test_the_teach_back_site_values_from_a_context_that_reads_nothing(tmp_path, monkeypatch):
    """The teach-back admission gets the build's loaded value context, whose repository raises; its admission and
    receipts are the ones a context reading the repository itself gives."""

    vault, repository = build_rich_vault(tmp_path / "vault")
    real = voi.greedy_information_admission
    valued: list[int] = []

    def checked(context, site, entries, **kwargs):
        if site == voi.SITE_TEACH_BACK:
            with pytest.raises(RuntimeError, match="read the repository"):
                context.repository.connection()
            admission = real(context, site, entries, **kwargs)
            reference = real(voi.VoiContext(vault, repository), site, entries, **kwargs)
            assert admission.admitted == reference.admitted
            assert [admission.receipt_for(entry.ref) for entry in entries] == [
                reference.receipt_for(entry.ref) for entry in entries
            ]
            valued.append(len(entries))
            return admission
        return real(context, site, entries, **kwargs)

    monkeypatch.setattr(voi, "greedy_information_admission", checked)
    read_due_queue(vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION))
    assert valued, "the build valued its teach-backs"


def test_a_frozen_view_not_asked_for_anchors_raises_rather_than_reads(tmp_path):
    """No anchored item foreseen (``anchors_for`` empty): the anchors stay unread, and an effective due that needs
    them raises instead of reading or answering without them."""

    vault, repository = build_intent_targets_vault(tmp_path / "vault")
    now = CLOCK.now()
    live = intent_serving(vault, repository, now=now)
    live.bind_admission(check_admission(vault, repository, now=now, intent_view=live, reasons=True))
    states = repository.practice_item_states()
    frozen = live.frozen(anchors_for=[])
    anchored = [item_id for item_id in sorted(vault.practice_items)
                if frozen.target_for(item_id) != 0.90 and getattr(states.get(item_id), "due_at", None)]
    assert anchored
    with pytest.raises(RuntimeError, match="anchors"):
        frozen.effective_due_or_none(anchored[0], states[anchored[0]])
