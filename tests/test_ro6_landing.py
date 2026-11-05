"""Router objective RO6's landing onto main: the orchestrator's rulings, each reproduced by a test.

* **R4**: a stop-coin draw that the waiting-follow-up rule superseded after the draw (the ledger logs the forced block
  deterministic; the coin's row and the trace keep the drawn arm and the coin's served candidate with its exact
  probability, as RO5's landing records) is used intent-to-treat: its contrast is by the assignment drawn, never by
  the action served.

Fakes only; no model request.
"""

from __future__ import annotations

import pytest

from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import tail_data as TD

from tests.test_ro6_codex_review import CFG, FAR, STOP, _logged, _row, _trace

RATE = 0.05


def _superseded(decision_id: str, created: str, arm: str, served: str, *, chosen: str | None = None) -> TD.Logged:
    """A forced draw whose block the waiting-follow-up rule replaced after the draw. The trace is frozen before the
    rule runs, so it carries the coin's arm and served candidate; ``chosen`` stands in for a record that named the
    action the learner was actually served (the follow-up block) instead."""

    coin = {"arm": arm, "rate": RATE, "served": served, "served_propensity": 0.5,
            "superseded_by": "forced:followup"}
    return _logged(_row(decision_id, created, closes="2026-10-15T10:00:00Z"),
                   _trace(q={STOP: 0.0, "a": 1.0}, chosen=chosen or served, residual={STOP: 0.0, "a": 0.5}, coin=coin))


def _contrasts(monkeypatch, rows: list[TD.Logged], returns: dict[str, float]):
    monkeypatch.setattr(TD, "_with_traces", lambda _connection, found: [dict(row.row) for row in found])
    monkeypatch.setattr(TD.S, "observed_returns",
                        lambda *_a, **_k: {key: (value, None) for key, value in returns.items()})
    return TD.contrasts(None, CFG, rows, at=FAR)


def test_r4_a_coin_draw_superseded_by_a_waiting_follow_up_is_used_intent_to_treat(monkeypatch):
    rows = [_superseded("d1", "2026-10-01T10:00:00Z", SC.OFFER_STOP, STOP),
            _superseded("d2", "2026-10-01T11:00:00Z", SC.PRESENT_NEXT, "a")]
    found, record = _contrasts(monkeypatch, rows, {"d1": 2.0, "d2": 3.0})
    by_id = {row.decision_id: row for row in found}
    assert record["status"] == "identified" and record["assigned"] == {SC.OFFER_STOP: 1, SC.PRESENT_NEXT: 1}
    # By the assignment drawn: offer stop +Ĝ/p, present next −Ĝ/p, each forced with P(forced) = 2p.
    assert by_id["d1"].realized == pytest.approx(2.0 / RATE) and by_id["d1"].forced
    assert by_id["d2"].realized == pytest.approx(-3.0 / RATE) and by_id["d2"].forced
    assert by_id["d1"].forced_probability == pytest.approx(2 * RATE)
    # Never by the action served: a record naming the follow-up block that was served gives the same contrasts.
    served = [_superseded("d1", "2026-10-01T10:00:00Z", SC.OFFER_STOP, STOP, chosen="a"),
              _superseded("d2", "2026-10-01T11:00:00Z", SC.PRESENT_NEXT, "a", chosen=STOP)]
    again, _record = _contrasts(monkeypatch, served, {"d1": 2.0, "d2": 3.0})
    assert [(row.decision_id, row.realized, row.tail, row.residual) for row in again] == \
        [(row.decision_id, row.realized, row.tail, row.residual) for row in found]
