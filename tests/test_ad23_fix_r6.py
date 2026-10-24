"""Adaptive difficulty AD2+AD3, fix round 6: the round-5 verify's reopened F15 and its F16
(docs/reviews/adaptive-difficulty-ad23-codex-review.md, verify 20261019-205930-JA9yfv).

* F15: landing ownership is by cell and order only: the cell's latest commission at the landing
  owns the item and its receipt records the realized features, even off the requested point;
* F16: one owner per item, enforced by ``UNIQUE(practice_item_id)``; draws of one second are
  ordered by insertion, and the first attribution is final.

Fakes only: no network, no model call, no paid call.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from learnloop.adaptive_difficulty.generation import record_landed_commissions, rung_features
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import ad_serving
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import ad23_vault, selections

ROUTER_OFF = "[router]\nenabled = false\n"


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _at(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _first_commission(tmp_path) -> tuple[Any, dict[str, Any]]:
    from tests.test_ad2_serving import _generation_prompt

    paths = ad23_vault(tmp_path, items=("pi_g1",), config=ROUTER_OFF)
    _generation_prompt(paths)
    (commission,) = selections(paths, kind="commission")
    return paths, commission


def _draw(paths, like: dict[str, Any], *, key: str, created_at: str, point: dict[str, Any]) -> str:
    """Another commission for the same cell, written through the store (as a draw would)."""

    row = {name: like[name] for name in ("kind", "view", "learning_object_id", "cell_facet", "cell_capability",
                                         "mode", "support", "excluded", "constants", "seed", "u", "propensity",
                                         "empty_support", "state_hash", "versions", "algorithm_version",
                                         "protection_epoch")}
    row.update({"decision_key": key, "chosen_point": point, "chosen_item_id": None, "created_at": created_at})
    with closing(connect(paths.sqlite_path)) as connection:
        selection_id = ad_serving.insert_selection(connection, row)
        connection.commit()
    return selection_id


def _land(paths, item_id: str, point: dict[str, Any], at: str, capability: str) -> None:
    from tests.test_ad2_serving import _land as land

    land(paths, item_id, {**rung_features(point), "tools": ["closed_book"]}, at, capability=capability)


def _reconcile(paths, now: str) -> list[str]:
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    with repository.atomic():
        return record_landed_commissions(vault, repository, repository.connection(), now=now)


def _results(paths) -> list[dict[str, Any]]:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return ad_serving.commission_results(connection)


def _other_point(point: dict[str, Any]) -> dict[str, Any]:
    value = point.get("complexity", 0)
    return {**point, "complexity": 1 if value == 0 else 0}


def test_a_late_item_off_the_successors_point_is_the_successors_landing(tmp_path):
    """F15 (the verify's case): A asks for one point on day 0 and expires; B asks for another
    point (complexity differs) for the same cell on day 9; an item at A's point lands on day 10.
    Exactly one receipt, owned by B, records the item's realized features (A's point) and says they
    are not B's point. Failed before: A was superseded and B's point did not match, so the landed
    item got no receipt at all."""

    paths, a = _first_commission(tmp_path)
    drawn = _at(a["created_at"])
    b_point = _other_point(a["chosen_point"])
    b = _draw(paths, a, key="commission:late:b", created_at=_iso(drawn + timedelta(days=9)), point=b_point)
    _land(paths, "pi_late", a["chosen_point"], _iso(drawn + timedelta(days=10)), a["cell_capability"])
    assert len(_reconcile(paths, _iso(drawn + timedelta(days=10, hours=1)))) == 1
    (result,) = _results(paths)
    assert (result["selection_id"], result["practice_item_id"]) == (b, "pi_late")
    realized = rung_features(a["chosen_point"])
    assert all(result["features"].get(dim) == value for dim, value in realized.items())
    assert result["features"]["complexity"] != b_point["complexity"]
    assert result["features_match"] == 0 and result["landed_after_expiry"] == 0
    assert result["status"] in ("in_band", "realized_out_of_band")
    assert _reconcile(paths, _iso(drawn + timedelta(days=11))) == []
    assert len(_results(paths)) == 1


def test_one_owner_at_equal_timestamps_and_the_first_attribution_is_final(tmp_path):
    """F16 (the verify's same-second case): ``pi`` lands in the second of A's draw and is
    receipted to A; B is drawn for the same cell and point in that same second. Reconciliation,
    repeated and after a whole rebuild, leaves exactly one row, ``(A, pi)``; a second owner is
    refused by the table itself. Failed before: B also took ``pi``, ``[(A, pi), (B, pi)]``."""

    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths, a = _first_commission(tmp_path)
    second = a["created_at"]
    _land(paths, "pi", a["chosen_point"], second, a["cell_capability"])
    assert len(_reconcile(paths, second)) == 1
    b = _draw(paths, a, key="commission:same-second:b", created_at=second, point=a["chosen_point"])
    for _ in range(2):
        assert _reconcile(paths, second) == []
    rebuild_all_derived_state(load_vault(paths.root), Repository(paths.sqlite_path))
    assert _reconcile(paths, second) == []
    assert [(r["selection_id"], r["practice_item_id"]) for r in _results(paths)] == [(a["id"], "pi")]
    with closing(connect(paths.sqlite_path)) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            ad_serving.insert_commission_result(connection, {
                "selection_id": b, "practice_item_id": "pi", "p_bar": 0.7, "status": "in_band",
                "state_hash": "h", "created_at": second})


def test_draws_of_one_second_are_ordered_by_insertion(tmp_path):
    """F16: an item that lands in a second holding two draws of its cell belongs to the one
    inserted last (``(created_at, rowid)``), which is also the cell's open commission."""

    paths, a = _first_commission(tmp_path)
    second = _iso(_at(a["created_at"]) + timedelta(days=9))
    b = _draw(paths, a, key="commission:tie:b", created_at=second, point=a["chosen_point"])
    c = _draw(paths, a, key="commission:tie:c", created_at=second, point=_other_point(a["chosen_point"]))
    _land(paths, "pi_tie", a["chosen_point"], second, a["cell_capability"])
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert [str(r["id"]) for r in ad_serving.open_commissions(connection, now=second)] == [c]
    assert len(_reconcile(paths, second)) == 1
    (result,) = _results(paths)
    assert result["selection_id"] == c and result["selection_id"] != b and result["features_match"] == 0
