"""Adaptive difficulty AD2+AD3, fix round 7: the round-6 verify's F17 and F18
(docs/reviews/adaptive-difficulty-ad23-codex-review.md, verify 20261019-212940-fdjMvO).

* F17 (A8): landing reconciliation never reads a protected item (held-out material, an exam
  reservation): no ownership, no forecast, no receipt, and the commission stays open; with the
  predicate unavailable nothing is reconciled. The same omission is closed in generation
  targeting and the readiness cells;
* F18: ``features_match`` compares the one resolved (audited) mapping the receipt records and the
  forecast reads, never the item's stamp.

Fakes only: no network, no model call, no paid call.
"""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from learnloop.adaptive_difficulty import predict as PR
from learnloop.adaptive_difficulty import report as REP
from learnloop.adaptive_difficulty.generation import record_landed_commissions, rung_features
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import ad_serving
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import LO, ad23_vault, selections, set_item

ROUTER_OFF = "[router]\nenabled = false\n"


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _at(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _open_commission(tmp_path) -> tuple[Any, dict[str, Any]]:
    from tests.test_ad2_serving import _generation_prompt

    paths = ad23_vault(tmp_path, items=("pi_g1",), config=ROUTER_OFF)
    _generation_prompt(paths)
    (commission,) = selections(paths, kind="commission")
    return paths, commission


def _land(paths, item_id: str, features: dict[str, Any], at: datetime, capability: str) -> None:
    from tests.test_ad2_serving import _land as land

    land(paths, item_id, {**features, "tools": ["closed_book"]}, _iso(at), capability=capability)


def _reconcile(paths, now: datetime) -> list[str]:
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    with repository.atomic():
        return record_landed_commissions(vault, repository, repository.connection(), now=_iso(now))


def _results(paths) -> list[dict[str, Any]]:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return ad_serving.commission_results(connection)


def _open_ids(paths, now: datetime) -> list[str]:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return [str(row["id"]) for row in ad_serving.open_commissions(connection, now=_iso(now))]


def _reserve(monkeypatch, *item_ids: str) -> None:
    """An exam reservation (one of the two reasons the held-out predicate protects an item)."""

    monkeypatch.setattr(Repository, "reserved_exam_pool_item_ids", lambda _self: list(item_ids))


def _forecast_inputs(monkeypatch) -> list[str]:
    seen: list[str] = []
    real = PR.current_spec

    def spy(vault, connection, item, **kwargs):
        seen.append(str(item.id))
        return real(vault, connection, item, **kwargs)

    monkeypatch.setattr(PR, "current_spec", spy)
    return seen


# -- F17: reconciliation never reads protected material --------------------------------------------


def test_a_protected_landing_never_closes_forecasts_or_receipts_a_commission(tmp_path, monkeypatch):
    """F17 (the verify's case): A is open; an exam-protected item lands in A's cell; a later
    reconciliation (an unrelated serve's) writes no receipt, asks no forecast of it, and A stays
    open. Failed before: the protected item was forecast, receipted to A and closed it."""

    paths, a = _open_commission(tmp_path)
    drawn = _at(a["created_at"])
    _land(paths, "held_exam", rung_features(a["chosen_point"]), drawn + timedelta(hours=1), a["cell_capability"])
    _reserve(monkeypatch, "held_exam")
    seen = _forecast_inputs(monkeypatch)
    later = drawn + timedelta(hours=2)
    assert _reconcile(paths, later) == []
    assert _results(paths) == [] and "held_exam" not in seen
    assert _open_ids(paths, later) == [a["id"]]


def test_with_the_predicate_unavailable_nothing_is_reconciled(tmp_path, monkeypatch):
    """F17, fail closed: when the held-out predicate cannot be computed, reconciliation reads no
    item and writes nothing, even for an unprotected landing, and the commission stays open; once
    it can, the landing is receipted."""

    from learnloop.content.sources import exam_material

    paths, a = _open_commission(tmp_path)
    drawn = _at(a["created_at"])
    _land(paths, "pi_landed", rung_features(a["chosen_point"]), drawn + timedelta(hours=1), a["cell_capability"])
    real = exam_material.held_out_material

    def unavailable(*_args, **_kwargs):
        raise RuntimeError("held-out material unreadable")

    monkeypatch.setattr(exam_material, "held_out_material", unavailable)
    seen = _forecast_inputs(monkeypatch)
    later = drawn + timedelta(hours=2)
    assert _reconcile(paths, later) == [] and _results(paths) == [] and seen == []
    assert _open_ids(paths, later) == [a["id"]]
    monkeypatch.setattr(exam_material, "held_out_material", real)
    assert len(_reconcile(paths, later)) == 1
    assert [r["practice_item_id"] for r in _results(paths)] == ["pi_landed"]


def test_a_protected_item_never_steers_the_commissioned_cell_or_readiness(tmp_path, monkeypatch):
    """F17's audit (A8): generation targeting (the LO's commissioned facet) and the readiness
    cells read only unprotected items: a protected item weighing heavily on another facet moves
    neither."""

    from learnloop.adaptive_difficulty import readiness as RD
    from learnloop.adaptive_difficulty.generation import lo_cell_facet
    from learnloop.adaptive_difficulty.protection import protection

    paths = ad23_vault(tmp_path, items=("pi_c1", "pi_c2"), config=ROUTER_OFF)
    set_item(paths, "pi_c1", evidence_facets=["f_open"], evidence_weights={"f_open": 1.0})
    set_item(paths, "pi_c2", evidence_facets=["f_held"], evidence_weights={"f_held": 1.0})
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    capability = PR.capability(vault.practice_items["pi_c2"])
    _reserve(monkeypatch, "pi_c2")
    protected = protection(vault, repository)
    assert protected.covers(vault.practice_items["pi_c2"]) and not protected.covers(vault.practice_items["pi_c1"])
    assert lo_cell_facet(vault, LO, protected=protected) == "f_open"
    assert all(facet != "f_held" for facet, _cap, _subject in RD._cells(vault, LO, protected))  # noqa: SLF001
    assert ("f_open", capability) in {(f, c) for f, c, _s in RD._cells(vault, LO, protected)}  # noqa: SLF001


# -- F18: one resolved feature mapping per landing -------------------------------------------------


def _audit(monkeypatch, item_id: str, complexity: int) -> Any:
    """The item's canonical audit resolves ``complexity`` (whatever its stamp says)."""

    from learnloop.adaptive_difficulty import serve_inputs
    from learnloop.adaptive_difficulty.feature_audit import item_revision

    real = serve_inputs.canonical_audits
    state: dict[str, str] = {}

    def audits(connection, content_hash, *, as_of=None):
        found = dict(real(connection, content_hash, as_of=as_of))
        if content_hash == state.get("hash"):
            found["complexity"] = {"judgment_id": "j_audit", "value": str(complexity), "judge": "decider"}
        return found

    def bind(paths) -> None:
        state["hash"] = item_revision(load_vault(paths.root).practice_items[item_id])[0]

    monkeypatch.setattr(serve_inputs, "canonical_audits", audits)
    return bind


def _flip(value: Any) -> int:
    return 1 if value == 0 else 0


@pytest.mark.parametrize("case", ["stamped_on_audited_off", "stamped_off_audited_on"])
def test_features_match_reads_the_audited_features_the_receipt_records(tmp_path, monkeypatch, case):
    """F18: A asks complexity c. Stamped c but audited otherwise: the receipt records the audited
    value, ``features_match`` is 0 and the report counts one off-point landing. The inverse (stamped
    off the point, audited on it): ``features_match`` is 1. Failed before: the flag compared the
    stamp while the receipt recorded the audit."""

    paths, a = _open_commission(tmp_path)
    drawn = _at(a["created_at"])
    requested = rung_features(a["chosen_point"])
    asked = requested.get("complexity", 0)
    stamped = asked if case == "stamped_on_audited_off" else _flip(asked)
    audited = _flip(asked) if case == "stamped_on_audited_off" else asked
    _land(paths, "pi_audited", {**requested, "complexity": stamped}, drawn + timedelta(hours=1), a["cell_capability"])
    _audit(monkeypatch, "pi_audited", audited)(paths)
    assert len(_reconcile(paths, drawn + timedelta(hours=2))) == 1
    (result,) = _results(paths)
    assert result["selection_id"] == a["id"] and result["features"]["complexity"] == audited
    expected = 0 if case == "stamped_on_audited_off" else 1
    assert result["features_match"] == expected
    repository = Repository(paths.sqlite_path)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        report = REP.build(load_vault(paths.root), repository, connection, sensitivity=False)
    assert report["selection"]["commissions"]["off_point"] == 1 - expected
