"""What other test files use from ``tests/test_mobile_v2_review_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from dataclasses import replace

from learnloop.daily_plan import engine

from tests.mobile_host_helpers import rows


def _stop_past_held_work(monkeypatch):
    """The chooser draws a stop (with its propensity) at any boundary crossed while a block is open:
    only a device's step crosses one then."""

    real = engine.decide
    drawn = []

    def decide(record, context, policy, **kwargs):
        decision = real(record, context, policy, **kwargs)
        if record.current_block() is None or not decision.feasible:
            return decision
        drawn.append(record.id)
        stop = replace(decision.choice, candidate_id=engine.STOP_FOR_TODAY, propensity=0.25,
                       why="a forced stop at the phone's boundary")
        return replace(decision, choice=stop, candidate=None, stop_offered=True)

    monkeypatch.setattr(engine, "decide", decide)
    return drawn


def _stops(repository):
    return [json.loads(row["detail_json"]) for row in rows(
        repository, "SELECT detail_json FROM attention_block_events WHERE kind = 'block_chosen'")
        if json.loads(row["detail_json"]).get("stop_reason")]
