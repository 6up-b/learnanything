"""Shared setups for ``tests/test_probe_router_authority.py``: the sites that answer "should a probe be asked after
this miss?" and the rows each one writes, on the automatic follow-up lane and on the learner's repair lane.

``TAG`` is the tag these tests characterize: the probe router's predecessor (``probe_router_helpers``), where every
site here answers as it did before the router became the decider.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from learnloop.db.repositories import Repository

from tests.causal_orchestrator_helpers import CLOCK, PROBE_ITEM, _activate_probe_candidate, _seed_factor, _vault
from tests.helpers import admit_probe_instrument_card
from tests.probe_router_helpers import BEFORE_PROBE_ROUTER

TAG = BEFORE_PROBE_ROUTER


def count(repository: Repository, table: str, where: str = "", args: tuple[Any, ...] = ()) -> int:
    with repository.connection() as connection:
        return int(connection.execute(f'SELECT COUNT(*) FROM "{table}" {where}', args).fetchone()[0])


def table_rows(repository: Repository, table: str, where: str = "", args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(f'SELECT * FROM "{table}" {where} ORDER BY rowid', args)]


def receipts(repository: Repository, factor_id: str | None = None) -> list[dict[str, Any]]:
    """The causal gate's receipts (oldest first), all of them or one factor's."""

    if factor_id is None:
        return table_rows(repository, "causal_probe_decision_receipts")
    return table_rows(repository, "causal_probe_decision_receipts", "WHERE factor_id = ?", (factor_id,))


def divergent_factor(tmp_path, *, instrument: bool = True, first: str = "repair:recall",
                     second: str | None = "repair:method"):
    """The learner lane's case: two concrete causes needing ``first`` and ``second`` repairs plus the open arm; with
    ``instrument`` a reviewed, active discriminating probe for them. Returns a namespace of vault, repository, root,
    factor and the two hypothesis ids."""

    vault, repository, root = _vault(tmp_path, with_probe_item=instrument)
    factor, a, b = _seed_factor(repository, first_repair=first, second_repair=second)
    if instrument:
        admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
        _activate_probe_candidate(repository, factor, a, b)
    return SimpleNamespace(vault=vault, repository=repository, root=root, factor=factor, first=a, second=b)


def sidecar(root):
    """A sidecar context on the vault at ``root``, for calling handlers as the app does."""

    import learnloop_sidecar.handlers  # noqa: F401 - registers the handlers
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    ctx.load(root)
    ctx.post_attempt_worker.autostart = False
    return ctx


def call(ctx, name: str, params: dict[str, Any]) -> dict[str, Any]:
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def decision_records(repository: Repository, kind: str) -> list[dict[str, Any]]:
    """The ``decision_records`` of one kind, oldest first, their JSON fields read."""

    import json

    out = []
    for row in table_rows(repository, "decision_records", "WHERE kind = ?", (kind,)):
        for key in ("alternatives_json", "facts_json", "versions_json"):
            row[key.removesuffix("_json")] = json.loads(row.pop(key))
        out.append(row)
    return out


def router_rows(repository: Repository, kind: str = "plan_interrupt") -> list[dict[str, Any]]:
    import json

    out = []
    for row in table_rows(repository, "router_decisions", "WHERE decision_kind = ?", (kind,)):
        row["detail_json"] = json.loads(row["detail_json"] or "{}")
        out.append(row)
    return out


__all__ = ["CLOCK", "PROBE_ITEM", "TAG", "call", "count", "decision_records", "divergent_factor", "receipts",
           "router_rows", "sidecar", "table_rows"]
