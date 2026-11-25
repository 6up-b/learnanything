"""Counts for the difficulty label's retirement (mvp-0.71) on a backup-API copy of a vault, before and after its upgrade.

``snapshot COPY --as-of T --out PRIVATE.json`` reads one copy (read only; the copy's databases are hashed before and
after and must not change) and writes its mastery, surprise rows, stored due dates and due queue at ``T`` to
``PRIVATE.json`` (values and ids: private, never tracked). Stdout is counts only: the surprise rows by
``prediction_source``, grade-time forecast receipts, AD's trained subject trace rows and those carrying the KL measure,
attempts carrying follow-up gate records, and the integrity line.

``compare BEFORE.json AFTER.json`` prints counts and summary statistics only: mastery rows changed with the mean and
max logit-mean shift, surprise rows whose direction changed (by transition), due dates moved, and the queue's
Spearman and top-10 overlap. The comparisons are ``scripts/difficulty_four_way.py``'s own functions, so the numbers
read as that script's arm (f) against arm (a).

Refuses a path under ``~/learnloop-vaults`` or ``~/learnloop-retired``. Makes no model call.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from contextlib import closing
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
GRADE_KIND = "item_unassisted_success_at_grade"


def _four_way() -> Any:
    spec = importlib.util.spec_from_file_location("difficulty_four_way_script", HERE / "difficulty_four_way.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


#: The prediction sources a surprise row may name; anything else is counted under ``other``.
SOURCES = ("serve_receipt", "grade_receipt", "mastery")
DIRECTIONS = ("positive", "negative", "none")
BELOW_THE_TAG = "none (below the tag)"


def _counts(sqlite_path: Path) -> dict[str, Any]:
    from learnloop.db.connection import connect

    with closing(connect(sqlite_path, read_only=True)) as connection:
        sources: Counter[str] = Counter({name: 0 for name in (*SOURCES, BELOW_THE_TAG, "other")})
        directions: Counter[str] = Counter({name: 0 for name in (*DIRECTIONS, "other")})
        gated = 0
        for dist, direction, triggered, suppressed, diagnostics in connection.execute(
                "SELECT predicted_score_dist_json, surprise_direction, triggered_actions_json, suppressed_actions_json, "
                "gate_diagnostics_json FROM attempt_surprise"):
            payload = json.loads(dist) if dist else {}
            source = payload.get("prediction_source")
            sources[BELOW_THE_TAG if source is None else source if source in SOURCES else "other"] += 1
            directions[direction if direction in DIRECTIONS else "other"] += 1
            # A gate record is any of the three: a normal no-trigger decision leaves only its diagnostics.
            gated += int(bool(json.loads(triggered or "[]") or json.loads(suppressed or "[]")
                              or json.loads(diagnostics or "{}")))
        receipts = int(connection.execute("SELECT COUNT(*) FROM forecast_receipts WHERE kind = ?",
                                          (GRADE_KIND,)).fetchone()[0])
        trained = with_kl = 0
        if connection.execute("SELECT 1 FROM sqlite_master WHERE name = 'ad_attempt_trace'").fetchone():
            for (detail,) in connection.execute(
                    "SELECT detail_json FROM ad_attempt_trace WHERE view = 'subject' AND information IS NOT NULL"):
                trained += 1
                with_kl += int("kl_observation" in json.loads(detail or "{}"))
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        foreign = len(connection.execute("PRAGMA foreign_key_check").fetchall())
    return {"surprise_by_source": dict(sorted(sources.items())), "surprise_directions": dict(sorted(directions.items())),
            "attempts_with_gate_records": gated, "grade_time_receipts": receipts,
            "ad_trained_subject_rows": trained, "ad_rows_with_kl": with_kl, "integrity_ok": integrity,
            "foreign_key_violations": foreign}


def _public_counts(counts: Any) -> dict[str, Any]:
    """The counts' public shape, rebuilt from typed fields and allow-listed keys only, whatever a file held."""

    def count_map(value: Any, keys: tuple[str, ...]) -> dict[str, int]:
        value = value if isinstance(value, dict) else {}
        return {key: int(value.get(key, 0)) for key in keys}

    counts = counts if isinstance(counts, dict) else {}
    return {"surprise_by_source": count_map(counts.get("surprise_by_source"), (*SOURCES, BELOW_THE_TAG, "other")),
            "surprise_directions": count_map(counts.get("surprise_directions"), (*DIRECTIONS, "other")),
            **{key: int(counts.get(key, 0)) for key in ("attempts_with_gate_records", "grade_time_receipts",
                                                         "ad_trained_subject_rows", "ad_rows_with_kl",
                                                         "foreign_key_violations")},
            "integrity_ok": counts.get("integrity_ok") is True}


def snapshot(vault_copy: Path, *, as_of: str | None, out: Path) -> dict[str, Any]:
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    four_way = _four_way()
    four_way._refuse_live_vault(vault_copy)
    four_way.check_private_output(out, inputs=(vault_copy,))
    before = four_way._database_digests(vault_copy)
    vault = load_vault(vault_copy)
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    # Attached read only, without migrating: the copy is read as it stands.
    state = four_way.read_replayed(vault, Repository.attach(sqlite_path, read_only=True), as_of=four_way._as_of(as_of))
    counts = _counts(sqlite_path)
    if four_way._database_digests(vault_copy) != before:
        raise RuntimeError("the copy's databases changed while it was read")
    record = {"algorithm_version": vault.config.algorithms.algorithm_version, "as_of": as_of, "counts": counts,
              "state": state}
    four_way.write_private_output(out, json.dumps(record, sort_keys=True, default=str), inputs=(vault_copy,))
    return {"algorithm_version": _tag(record["algorithm_version"]), "mastery_rows": len(state["mastery"]),
            "surprise_rows": len(state["surprise"]),
            "queue_length": None if state["queue"] is None else len(state["queue"]), **_public_counts(counts)}


def _tag(value: Any) -> str:
    """A tag as printed: ``mvp-<n>.<n>`` or ``other``."""

    import re

    return value if isinstance(value, str) and re.fullmatch(r"mvp-\d+\.\d+", value) else "other"


def compare(before_path: Path, after_path: Path) -> dict[str, Any]:
    four_way = _four_way()
    before = json.loads(before_path.read_text(encoding="utf-8"))
    after = json.loads(after_path.read_text(encoding="utf-8"))
    base, arm = before["state"], after["state"]
    mastery = four_way.compare_mastery(base["mastery"], arm["mastery"])
    surprise = four_way.compare_surprise(base["surprise"], arm["surprise"])
    due = four_way.compare_due(base["due"], arm["due"])
    queue = four_way.compare_queue(base["queue"], arm["queue"], (10,))
    return {
        "from": _tag(before.get("algorithm_version")), "to": _tag(after.get("algorithm_version")),
        "mastery_changed": f"{mastery['changed']}/{mastery['rows']}",
        "mastery_delta_logit_mean": {k: mastery["delta_logit_mean"].get(k) for k in ("mean", "max", "min")}
        if mastery["delta_logit_mean"] else None,
        "surprise_changed": f"{surprise['changed']}/{surprise['rows']}",
        "surprise_direction_changed": surprise["direction_changed"],
        "surprise_direction_transitions": _transitions(surprise["direction_transitions"]),
        "due_items_moved": f"{due['practice_item_state']['moved']}/{due['practice_item_state']['rows']}",
        "queue_spearman": queue.get("spearman_common"),
        "queue_top10_overlap": (queue.get("top_k") or {}).get("10", {}).get("overlap"),
        "after_counts": _public_counts(after.get("counts")),
    }


def _transitions(found: Any) -> dict[str, int]:
    """Direction transitions keyed only by known directions (anything else under ``other``)."""

    out: dict[str, int] = {}
    for key, count in (found or {}).items():
        parts = str(key).split("->")
        known = len(parts) == 2 and all(part in DIRECTIONS for part in parts)
        name = str(key) if known else "other"
        out[name] = out.get(name, 0) + int(count)
    return dict(sorted(out.items()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("snapshot", help="read one copy; counts on stdout, values to --out")
    one.add_argument("vault_copy", type=Path)
    one.add_argument("--as-of", default=None, help="the instant the due queue is read at (one for every copy)")
    one.add_argument("--out", type=Path, required=True, help="the private JSON (values and ids), outside the copy")
    two = sub.add_parser("compare", help="two snapshots: counts and summary statistics on stdout")
    two.add_argument("before", type=Path)
    two.add_argument("after", type=Path)
    args = parser.parse_args(argv)
    if args.command == "snapshot":
        result = snapshot(args.vault_copy.resolve(), as_of=args.as_of, out=args.out)
    else:
        result = compare(args.before, args.after)
    print(json.dumps(result, sort_keys=True, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
