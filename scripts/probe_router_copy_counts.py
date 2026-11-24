"""The probe router's landing on copies of the owner's vaults: counts only (``docs/reviews/algorithm-probe-router.md``,
"What the orchestrator must run on owner copies").

``counts COPY``: one JSON line of counts read from a backup-API copy (never a live vault), read-only (the database
opened ``mode=ro``, as ``scripts/probe_router_report.py`` opens it; nothing is written and no model is called):

- the vault's tag and whether the probe router is on;
- the automatic lane's ``plan_interrupt`` decisions on the daily plan, by chosen option and by who decided (the probe
  coin's own share among them);
- the learner lane's decisions (``surface = 'causal_repair'``), by chosen option, learned or not, and by how the
  option was served (the mix or the probe coin);
- the probe coin's assignments, by variant;
- the causal gate's receipts, by decision (``router_decides`` from the tag);
- probe presentations pinning a router decision, and probe episodes by status and completion reason.

``compare BEFORE.json AFTER.json``: the counts that moved between two runs, as ``{"key": [before, after]}``.

    uv run python scripts/probe_router_copy_counts.py counts "$COPY" > before.json
    uv run python scripts/probe_router_copy_counts.py compare before.json after.json

It prints counts and tags only: never an id, a learner's text or a path.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any


def _report():
    """The comparison report's module, for its read-only open (its dataclasses resolve through ``sys.modules``)."""

    name = "probe_router_report"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parent / "probe_router_report.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _tag(root: Path) -> str | None:
    toml = root / "learnloop.toml"
    if not toml.is_file():
        return None
    import tomllib

    data = tomllib.loads(toml.read_text(encoding="utf-8"))
    algorithms = data.get("algorithms") if isinstance(data.get("algorithms"), Mapping) else {}
    value = algorithms.get("algorithm_version")
    return str(value) if value else None


def _has(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (table,)).fetchone() is not None


def _loads(raw: Any) -> Any:
    try:
        return json.loads(raw) if raw else {}
    except (TypeError, ValueError):
        return {}


def _sorted(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def counts(root: Path) -> dict[str, Any]:
    from learnloop.algorithm_versions import PROBE_ROUTER_VERSIONS

    tag = _tag(root)
    out: dict[str, Any] = {"algorithm_version": tag, "probe_router_on": tag in PROBE_ROUTER_VERSIONS}
    connection = _report().open_read_only(root)
    try:
        if _has(connection, "router_decisions"):
            automatic: Counter = Counter()
            automatic_by: Counter = Counter()
            learner: Counter = Counter()
            learner_learned: Counter = Counter()
            learner_served_by: Counter = Counter()
            for row in connection.execute("SELECT surface, chosen_ref, detail_json FROM router_decisions "
                                          "WHERE decision_kind = 'plan_interrupt'"):
                detail = _loads(row["detail_json"])
                if row["surface"] == "causal_repair":
                    learner[row["chosen_ref"]] += 1
                    learner_learned[str(bool(detail.get("learned")))] += 1
                    learner_served_by["mixture" if detail.get("mixture") else
                                      "probe_coin" if detail.get("probe_coin") else "no_coin"] += 1
                else:
                    automatic[row["chosen_ref"]] += 1
                    coin = detail.get("probe_coin") or {}
                    automatic_by["probe_coin_asked" if coin.get("arm") == "ask_probe" else
                                 "probe_coin_policy" if coin else "no_coin"] += 1
            out.update(automatic_decisions_by_choice=_sorted(automatic), automatic_decisions_by_coin=_sorted(
                automatic_by), learner_decisions_by_choice=_sorted(learner),
                learner_decisions_learned=_sorted(learner_learned),
                learner_decisions_served_by=_sorted(learner_served_by))
        if _has(connection, "policy_experiment_assignments"):
            out["probe_coin_assignments_by_variant"] = _sorted(Counter(
                row[0] for row in connection.execute(
                    "SELECT variant FROM policy_experiment_assignments WHERE experiment_id = 'g2_probe_coin:v1'")))
        if _has(connection, "causal_probe_decision_receipts"):
            out["causal_receipts_by_decision"] = _sorted(Counter(
                row[0] for row in connection.execute("SELECT decision FROM causal_probe_decision_receipts")))
        if _has(connection, "probe_presentations"):
            pinned = 0
            for row in connection.execute("SELECT selection_components_json FROM probe_presentations"):
                pin = _loads(row[0]).get("causal_probe") or {}
                pinned += bool(isinstance(pin, Mapping) and pin.get("router_decision_id"))
            out["presentations_pinning_a_router_decision"] = pinned
        if _has(connection, "probe_episodes"):
            out["episodes_by_status"] = _sorted(Counter(
                row[0] for row in connection.execute("SELECT status FROM probe_episodes")))
            out["episodes_by_completion_reason"] = _sorted(Counter(
                str(row[0]) for row in connection.execute("SELECT completion_reason FROM probe_episodes")))
    finally:
        connection.close()
    return out


def _flat(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            out.update(_flat(item, f"{prefix}{key}."))
        return out
    return {prefix.rstrip("."): value}


def compare(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, list[Any]]:
    a, b = _flat(before), _flat(after)
    return {key: [a.get(key), b.get(key)] for key in sorted(set(a) | set(b)) if a.get(key) != b.get(key)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("counts")
    one.add_argument("copy", type=Path)
    two = commands.add_parser("compare")
    two.add_argument("before", type=Path)
    two.add_argument("after", type=Path)
    args = parser.parse_args(argv)
    if args.command == "counts":
        print(json.dumps(counts(args.copy), sort_keys=True))
    else:
        before = json.loads(args.before.read_text(encoding="utf-8"))
        after = json.loads(args.after.read_text(encoding="utf-8"))
        print(json.dumps(compare(before, after), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
