"""RD-retire parity, cold follow-ups (spec §21.1: "Unchanged (commitments), and hosted inline (§12.6)"): a Reader cold
follow-up is the same commitment on both surfaces. Due, it opens inline on the item Today would serve, cold; under
RW6b's serve-time gate (an exposure since its valuation) neither surface serves it as the check: inline it refuses
with nothing to serve, as Today holds it. No model is called; the serve is a stand-in for Today's own."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.instructional import reader_followups as RF
from learnloop.intent import inline_administration as IA
from learnloop.vault.loader import load_vault
from tests.reader_followups_helpers import FakeSearch, _candidate, _plan, _seeded

ITEM = "pi_svd_define_002"


def _noon(day: str) -> datetime:
    parsed = date.fromisoformat(day)
    return datetime(parsed.year, parsed.month, parsed.day, 12).astimezone().astimezone(UTC)


def _impression(repo, item_id: str, moment: datetime) -> None:
    from learnloop.db.stores.source_service import insert_impression

    with repo.connection() as connection:
        insert_impression(connection, id=f"imp_{item_id}", created_at=moment.isoformat().replace("+00:00", "Z"),
                          surface="reader", caller_kind="reader", caller_ref="elsewhere", proposal_id="pp_elsewhere",
                          candidate_kind="item", practice_item_id=item_id, extraction_id=None, span_ids=[],
                          shown_fields={}, session_id=None)
        connection.commit()


def _begin(root, repo, commitment_id: str, moment: datetime) -> dict:
    return IA.begin(load_vault(root), repo, request_id=f"req_{moment.timestamp():.0f}", commitment_id=commitment_id,
                    session_id="ps_1", visible={}, serve=lambda item_id: {"practiceItemId": item_id},
                    covered=lambda learning_object_ids: set(), clock=FrozenClock(moment))


def _planned(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    row = _plan(vault, repo, session, FakeSearch([_candidate(ITEM, 0.99, 0.01, 1.0)]))
    [followup_id] = row["followup_commitment_ids"]
    return vault, repo, followup_id, _noon(row["valuation"]["chosen"][0]["due_hint"])


def test_a_due_cold_follow_up_opens_inline_cold_on_the_item_today_would_serve(tmp_path):
    from learnloop.scheduling.intent.serving import intent_serving

    vault, repo, followup_id, moment = _planned(tmp_path)
    today = intent_serving(load_vault(vault.root), repo, now=moment, force=True).checks[followup_id]
    assert today.provenance.get("via") == RF.VIA and today.servable and today.cold(today.servable[0])
    opened = _begin(vault.root, repo, followup_id, moment)
    admin = opened["administration"]
    assert admin["commitment_id"] == followup_id
    assert admin["practice_item_id"] == today.servable[0]
    assert bool(admin["cold"]) is True


def test_rw6bs_gate_holds_the_follow_up_on_both_surfaces(tmp_path):
    from learnloop.scheduling.intent.serving import intent_serving

    vault, repo, followup_id, moment = _planned(tmp_path)
    _impression(repo, ITEM, moment - timedelta(hours=1))
    today = intent_serving(load_vault(vault.root), repo, now=moment, force=True).checks[followup_id]
    assert ITEM in today.held and not today.servable
    with pytest.raises(IA.InlineCheckError) as refused:
        _begin(vault.root, repo, followup_id, moment)
    assert refused.value.code == "nothing_to_serve"
