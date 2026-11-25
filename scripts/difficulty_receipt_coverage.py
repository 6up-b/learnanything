"""H3's owner-copy counts (``docs/reviews/refactor-h3-h6-design.md`` §10): read-only, counts only.

    uv run python scripts/difficulty_receipt_coverage.py <vault copy> [--out <report.json>]

Run it on a backup-API copy of a vault (``learnloop.db.copies.copy_tree_with_databases``), never on a live one (a
path under ``~/learnloop-vaults`` or ``~/learnloop-retired`` is refused). The database is opened read-only
(``mode=ro``, ``PRAGMA query_only``); the vault is loaded without its environment; the copy's databases are hashed
before and after, and a change fails the run. It prints one JSON object of counts: no id, no item text, no value
of any single row. ``--out`` writes the same JSON to a file outside the copy.

What it counts:

* **receipt coverage**: per attempt type, the attempts, those bound to a plan presentation, and those H3's surprise
  would read a serve-time AD receipt for (the rule of ``scripts/difficulty_four_way.py``'s
  :func:`receipt_predictions`), with the fallback reasons and the primed ones among the covered;
* **the dormant measured-difficulty path**: ``item_parameter_state`` rows;
* **exam pools**: unreleased reservations by ``difficulty_stratum``, and released ones;
* **the live gate's records on ``attempt_surprise``**: rows with triggered actions, suppressed actions, gate
  diagnostics, and queued follow-up actions not yet answered (what a whole-vault rebuild clears today: the design
  note's §3.3);
* **the label**: items by ``difficulty_source`` and with or without a ``difficulty``; learning objects with a
  ``difficulty_prior``;
* **config**: the four effective settings the design reads, and the algorithm version;
* **integrity**: ``PRAGMA integrity_check`` and the foreign-key violation count.

Zero model calls; nothing is written.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sqlite3
import sys
from collections import Counter
from collections.abc import Sequence
from contextlib import closing
from pathlib import Path
from typing import Any

REPORT_VERSION = "difficulty_receipt_coverage_v1"
FOUR_WAY = Path(__file__).resolve().with_name("difficulty_four_way.py")


def _four_way() -> Any:
    spec = importlib.util.spec_from_file_location("difficulty_four_way_for_coverage", FOUR_WAY)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _refuse_live_vault(root: Path) -> None:
    home = Path.home()
    for name in ("learnloop-vaults", "learnloop-retired"):
        try:
            root.resolve().relative_to((home / name).resolve())
        except ValueError:
            continue
        raise SystemExit(f"refusing a live vault under ~/{name}: run on a backup-API copy")


def _digests(root: Path) -> dict[str, str]:
    """SHA-256 of each database file and its ``-wal`` (a read-only open may create an empty one); ``-shm`` left out."""

    from learnloop.db.copies import is_companion_file_name, is_database_file_name

    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or is_companion_file_name(path.name) or not is_database_file_name(path.name):
            continue
        digest = hashlib.sha256()
        for part in (path, path.with_name(path.name + "-wal")):
            if part.is_file():
                digest.update(part.read_bytes())
        out[str(path.relative_to(root))] = digest.hexdigest()
    return out


def _read_only(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.execute("PRAGMA query_only = ON")
    return connection


def _table(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (name,)).fetchone() is not None


def _columns(connection: sqlite3.Connection, name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({name})")}


def receipt_coverage(connection: sqlite3.Connection, receipts: dict[str, Any]) -> dict[str, Any]:
    columns = _columns(connection, "practice_attempts")
    primed = "primed" if "primed" in columns else "0"
    bound = "plan_presentation_id" if "plan_presentation_id" in columns else "NULL"
    by_type: dict[str, Counter] = {}
    for attempt_id, attempt_type, is_primed, presentation in connection.execute(
            f"SELECT id, attempt_type, {primed}, {bound} FROM practice_attempts"):
        counts = by_type.setdefault(str(attempt_type or "unknown"), Counter())
        counts["attempts"] += 1
        counts["bound"] += presentation is not None
        entry = receipts.get(str(attempt_id))
        if entry is not None and entry.tier == "receipt":
            counts["with_receipt"] += 1
            counts["with_receipt_primed"] += bool(is_primed)
        else:
            counts[f"fallback:{entry.reason if entry is not None else 'unread'}"] += 1
    total = Counter()
    for counts in by_type.values():
        total.update(counts)
    return {"by_attempt_type": {k: dict(sorted(v.items())) for k, v in sorted(by_type.items())},
            "all": dict(sorted(total.items()))}


def _queued_item(action: Any) -> str | None:
    """The item a queued follow-up action names, as the scheduler's pending list parses it
    (``db.stores.remediation``: ``negative_surprise_followup:<item>``, ``intervention_followup:queued:<item>``)."""

    if not isinstance(action, str):
        return None
    if action.startswith("negative_surprise_followup:"):
        return action.split(":", 1)[1]
    if action.startswith("intervention_followup:queued:"):
        return action.split(":", 2)[2]
    return None


def gate_records(connection: sqlite3.Connection) -> dict[str, Any]:
    if not _table(connection, "attempt_surprise"):
        return {"available": False}
    columns = _columns(connection, "attempt_surprise")

    def nonempty(column: str, empty: str) -> int | None:
        if column not in columns:
            return None
        return connection.execute(f"SELECT count(*) FROM attempt_surprise WHERE {column} IS NOT NULL "
                                  f"AND {column} != ?", (empty,)).fetchone()[0]

    out: dict[str, Any] = {
        "available": True,
        "rows": connection.execute("SELECT count(*) FROM attempt_surprise").fetchone()[0],
        "with_triggered_actions": nonempty("triggered_actions_json", "[]"),
        "with_suppressed_actions": nonempty("suppressed_actions_json", "[]"),
        "with_gate_diagnostics": nonempty("gate_diagnostics_json", "null"),
    }
    # Queued follow-up actions with no later attempt on their item (the scheduler's legacy pending list).
    pending = 0
    if "triggered_actions_json" in columns:
        for actions, created_at in connection.execute(
                "SELECT triggered_actions_json, created_at FROM attempt_surprise "
                "WHERE triggered_actions_json IS NOT NULL AND triggered_actions_json != '[]'"):
            try:
                parsed = json.loads(actions)
            except ValueError:
                continue
            for action in parsed if isinstance(parsed, list) else ():
                item = _queued_item(action)
                if not item:
                    continue
                later = connection.execute("SELECT 1 FROM practice_attempts WHERE practice_item_id = ? "
                                           "AND created_at > ? LIMIT 1", (item, created_at)).fetchone()
                pending += later is None
    out["queued_actions_unanswered"] = pending
    if _table(connection, "followup_tasks"):
        out["followup_tasks"] = connection.execute("SELECT count(*) FROM followup_tasks").fetchone()[0]
    if _table(connection, "followup_ratings"):
        out["followup_ratings"] = connection.execute("SELECT count(*) FROM followup_ratings").fetchone()[0]
    return out


def exam_pools(connection: sqlite3.Connection) -> dict[str, Any]:
    if not _table(connection, "exam_pool_items"):
        return {"available": False}
    unreleased = {str(stratum): count for stratum, count in connection.execute(
        "SELECT coalesce(difficulty_stratum, 'null'), count(*) FROM exam_pool_items WHERE released_at IS NULL "
        "GROUP BY 1 ORDER BY 1")}
    return {"available": True, "unreleased_by_stratum": unreleased,
            "unreleased_goals": connection.execute(
                "SELECT count(DISTINCT goal_id) FROM exam_pool_items WHERE released_at IS NULL").fetchone()[0],
            "released": connection.execute(
                "SELECT count(*) FROM exam_pool_items WHERE released_at IS NOT NULL").fetchone()[0]}


def label_census(vault: Any) -> dict[str, Any]:
    items = list(vault.practice_items.values())
    los = list(vault.learning_objects.values())
    return {
        "items": len(items),
        "items_by_source": dict(sorted(Counter(str(i.difficulty_source or "none") for i in items).items())),
        "items_with_difficulty": sum(1 for i in items if i.difficulty is not None),
        "learning_objects": len(los),
        "learning_objects_with_prior": sum(1 for lo in los if getattr(lo, "difficulty_prior", None) is not None),
    }


def config_view(vault: Any) -> dict[str, Any]:
    irt = vault.config.mastery.irt
    return {
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "mastery.irt.eb_difficulty_enabled": bool(irt.eb_difficulty_enabled),
        "mastery.irt.difficulty_default": float(irt.difficulty_default),
        "mastery.irt.difficulty_from_prior": bool(irt.difficulty_from_prior),
        "scheduler.surprise.remove_interval_factor": bool(vault.config.scheduler.surprise.remove_interval_factor),
    }


def coverage(vault_copy: Path) -> dict[str, Any]:
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    vault_copy = Path(vault_copy).resolve()
    _refuse_live_vault(vault_copy)
    before = _digests(vault_copy)
    vault = load_vault(vault_copy, load_environment=False)
    database = VaultPaths(vault.root, vault.config).sqlite_path
    four_way = _four_way()
    with closing(_read_only(database)) as connection:
        receipts = four_way.receipt_predictions(connection)
        report = {
            "version": REPORT_VERSION,
            "config": config_view(vault),
            "label": label_census(vault),
            "receipt_coverage": receipt_coverage(connection, receipts),
            "item_parameter_state_rows": (connection.execute("SELECT count(*) FROM item_parameter_state").fetchone()[0]
                                          if _table(connection, "item_parameter_state") else None),
            "exam_pools": exam_pools(connection),
            "gate_records": gate_records(connection),
            "integrity_check": [row[0] for row in connection.execute("PRAGMA integrity_check")],
            "foreign_key_violations": len(connection.execute("PRAGMA foreign_key_check").fetchall()),
        }
    after = _digests(vault_copy)
    if after != before:
        raise RuntimeError("the copy's databases changed during a read-only count")
    report["input_databases_unchanged"] = True
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("vault_copy", type=Path, help="a backup-API copy of a vault (never a live vault)")
    parser.add_argument("--out", type=Path, default=None, help="also write the JSON here (outside the copy)")
    args = parser.parse_args(argv)
    if args.out is not None:
        try:
            args.out.resolve().relative_to(args.vault_copy.resolve())
        except ValueError:
            pass
        else:
            raise SystemExit("--out must be outside the vault copy: the input is never written")
    report = coverage(args.vault_copy)
    text = json.dumps(report, indent=1, sort_keys=True)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
