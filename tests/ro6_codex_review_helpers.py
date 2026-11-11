"""What other test files use from ``tests/test_ro6_codex_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import stop_coin as SC
from learnloop.router_objective import tail_data as TD
from learnloop.router_objective import value as V


STOP = SC.STOP
CFG = SimpleNamespace(router_objective=SimpleNamespace(session_gap_minutes=30.0, residual_prior_sd=0.01,
                                                       residual_weight_prior_sd=1.0, evaluation_window_days=14))
FAR = "2100-01-01T00:00:00Z"


@pytest.fixture
def utc(monkeypatch):
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def _trace(*, q: dict[str, float], mu: dict[str, float] | None = None, chosen: str = "a", cutoff_days: float = 90.0,
           residual: dict[str, float] | None = None, past_trim: dict[str, float] | None = None,
           previous: dict | None = None, coin: dict | None = None, dated: list[dict] | None = None,
           terminal: float = 0.0, features: dict[str, list[float]] | None = None) -> dict:
    support = list(q)
    mu = mu or {ref: 1.0 / len(support) for ref in support}
    width = len(LT.NAMES)
    candidates = {ref: {"kind": "stop" if ref == STOP else "review", "minutes": 0.0 if ref == STOP else 5.0,
                        "sensors": {}, "terms": {"q": value, **({"past_trim": past_trim[ref]} if past_trim else {})}}
                  for ref, value in q.items()}
    frozen = {ref: {"features": (features or {}).get(ref) or [0.0] * width,
                    "v_residual": (residual or {}).get(ref, 0.0)} for ref in support}
    record = {"status": "applied", "features_version": LT.FEATURES_VERSION, "candidates": frozen,
              **({"previous": previous} if previous else {})}
    return {"candidates": candidates, "mixing": {"mu": mu, "chosen": chosen, "effective": {"numeric": 0.5},
                                                 "epsilon": 0.0, "seeds": {}},
            "versions": {"horizon_days": 90.0}, "cutoff_days": cutoff_days, "reference": {"terms": {"terminal": terminal}},
            "residual": record, "policies": {"numeric": {"choice": chosen}},
            **({"stop_coin": coin} if coin else {}), **({"goal_dates": {"uses": dated}} if dated else {})}


def _row(decision_id: str, created_at: str, *, closes: str | None = None) -> dict:
    return {"id": f"t-{decision_id}", "decision_id": decision_id, "created_at": created_at,
            "local_date": created_at[:10], "window_closes_at": closes, "algorithm_version": "mvp-0.49",
            "kappa0": 0.0, "remembered_minutes": 20.0, "llm_status": "answered", "numeric_status": "answered"}


def _logged(row: dict, trace: dict) -> TD.Logged:
    return TD._logged(None, row, trace, CFG, FAR, False)


def _quiet(monkeypatch, links: dict[str, str | None], *, exam: float | None = 1.0) -> None:
    """``transitions``' reads replaced: the chain's links, no checks, no attention cost, ``exam`` for every import."""

    class _NoChecks:  # RO6's landing (R4): transitions read RO5's checks through one ledger and its closures
        def __init__(self, _connection):
            pass

        def resolve(self, _closure):
            return []

        def completion(self, _closure):
            return {"rate": None}

    monkeypatch.setattr(TD, "_next_links", lambda _connection, ids: ({key: links.get(key) for key in ids}, {}))
    monkeypatch.setattr(TD.C, "Ledger", _NoChecks)
    monkeypatch.setattr(TD.C, "administered", lambda _connection: {})
    monkeypatch.setattr(TD.S, "_price_rows", lambda _connection: [])
    monkeypatch.setattr(TD.S, "_day_prices", lambda *_a, **_k: {})
    monkeypatch.setattr(TD.S, "window_cost", lambda *_a, **_k: 0.0)
    monkeypatch.setattr(TD, "_exam_result_known", lambda _connection, _config, _lo, _on, _at: exam)


def _value_inputs():
    from tests.ro4_value_helpers import _inputs

    return _inputs(topics=(V.Topic(lo="lo_a", eta_mean=0.4, eta_var=0.2, undated_density=0.2, practiced=True,
                                   stability=3.0, elapsed_days=2.0),
                           V.Topic(lo="lo_b", eta_mean=-0.3, eta_var=0.1, undated_density=0.1)),
                   horizon_days=6.0, return_gaps_days=(1.0, 2.0), stop_accept=(2.0, 2.0),
                   dated=(V.DatedUse("g", "lo_b", 3.5, 1.0),))


def _value_actions():
    return [V.Action(ref="a", kind=V.REVIEW, item_los=("lo_a",), minutes=5.0),
            V.Action(ref="p", kind=V.PROBE, item_los=("lo_b",), minutes=4.0),
            V.Action(ref="stop_for_today", kind=V.STOP)]
