"""What the owner's vaults hold that the refactor's removals touch (refactor strategy v3 §2.6 D1; steps C3, C4, D7).

Read-only. For each vault directory named on the command line it prints:

- the algorithm tag its ``learnloop.toml`` names, and the database's migration head;
- whether an activation journal (``<database>.claim-fixes-activation``) stands beside the database, and the two
  tags it names;
- which config keys the TOML sets that a removal step drops: C3's keys nothing reads, C4's Codex transport (a
  Codex provider named by a profile, a route or the active/fallback provider, ``ai.agent_harness_opt_in``, the
  retired routes, the legacy ``[codex]`` table), and D7's kill switches at or below mvp-0.55.

It prints tags, a migration number, booleans and key names: no values, no ids, no learner text. The database is
opened read-only (a ``file:...?mode=ro`` URI, with ``immutable=1`` on a WAL-mode database that has no ``-wal``, so
no companion file appears); nothing is written, migrated or checkpointed, and no journal mode is set. Standalone (it imports nothing from ``learnloop``), so it runs on a vault whatever its version:

    uv run python scripts/vault_report.py ~/learnloop-vaults/linear_algebra ~/learnloop-retired/law [--json]

Exit 0 when every vault was read; 1 when a directory has no readable ``learnloop.toml``.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import tomllib
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

TAG = re.compile(r"^mvp-\d+\.\d+$")
JOURNAL_SUFFIX = ".claim-fixes-activation"

#: C3: keys nothing reads (``*`` is any name under a table of named entries).
C3_KEYS = (
    "locks",
    "locks.facet_lock_mass",
    "locks.facet_surface_groups",
    "facet_identity.merge_locked_facets",
    "mastery.irt.discrimination_min",
    "mastery.irt.discrimination_max",
    "plan.pre_questions",
    "recall_coverage.severity_examples.*.target_error_type",
    "error_impacts.*.lo_mastery_delta",
)

#: C4: the Codex transport's provider names and profile types, and its keys.
CODEX_PROVIDER_NAMES = frozenset({"codex", "codex_low", "codex_medium", "codex_luna"})
CODEX_PROVIDER_TYPES = frozenset({"codex_sdk", "http", "codex_http", "http_adapter"})
C4_KEYS = (
    "ai.agent_harness_opt_in",
    "ai.routing.field_llm_probability",
    "ai.routing.proof_check",
)

#: D7: kill switches for tags at or below mvp-0.55, with the tag each serves past (the map's 27 named switches,
#: tagged mvp-0.43 or below, then mvp-0.43 to mvp-0.55 from ``algorithm_versions.py``). Which go is the owner's call.
D7_SWITCHES: dict[str, str] = {
    **dict.fromkeys((
        "placement.enabled", "recurrence.enabled", "stuck_prompt.enabled", "plan.enabled",
        "router.probe_tie_admission", "learner_text_gaps.sooner_check_enabled", "proof_check.enabled",
        "source_service.source_first_needs", "voi_stopping.enabled", "diagnosis.probe_lane_reads_diagnosis",
        "router.enabled", "router.restraint", "required_method.enabled", "eligibility.enabled", "intent.enabled",
        "workbench.field_signals_enabled", "reading_paths.plan_uses_path", "mastery.claim_fixes_enabled",
        "replay.ledger_bounded", "ask.cold_help_converts", "practice.attempt_keeps_content_state",
        "practice.reschedule_cold_after_assist", "followups.enabled", "curriculum.plan_uses_path",
        "teacher.enabled", "hints.fold_follows_attach", "diagnosis.split_enabled",
    ), "<= mvp-0.43"),
    "router.lesson_suggestions.enabled": "mvp-0.43",
    "data_capture.serving": "mvp-0.44",
    "followup.generate_and_serve": "mvp-0.45",
    "scheduler.surprise.remove_interval_factor": "mvp-0.46",
    "router_objective.available_at_reads": "mvp-0.46",
    "router_objective.self_report_not_validated": "mvp-0.46",
    "router_objective.enabled": "mvp-0.47",
    "router_objective.stop_coin": "mvp-0.48",
    "router_objective.check_rate": "mvp-0.48",
    "router_objective.pick_open_share": "mvp-0.48",
    "router_objective.fitted_models": "mvp-0.48",
    "router_objective.learned_tail": "mvp-0.49",
    **dict.fromkeys((
        "router_objective.combiner_trace_outcomes", "router_objective.merged_sessions",
        "router_objective.consistent_review_draw", "router_objective.monotone_combiner",
        "router_objective.ad_predictive_link", "router_objective.carried_in_prefetch",
        "router_objective.scope_extension",
    ), "mvp-0.50"),
    "teacher.probes": "mvp-0.51",
    "adaptive_difficulty.lesson_opportunities": "mvp-0.52",
    "router.lesson_suggestions.in_objective": "mvp-0.53",
    "router_objective.failure_share_to_other_policy": "mvp-0.55",
}


def _paths(table: Mapping[str, Any], prefix: str = "") -> Iterator[str]:
    """Every dotted key path the TOML sets (tables included), never a value."""

    for key, value in table.items():
        path = f"{prefix}{key}"
        yield path
        if isinstance(value, Mapping):
            yield from _paths(value, f"{path}.")


def _matches(pattern: str, path: str) -> bool:
    parts, wanted = path.split("."), pattern.split(".")
    return len(parts) == len(wanted) and all(w in ("*", p) for w, p in zip(wanted, parts, strict=True))


def _codex_keys(data: Mapping[str, Any]) -> list[str]:
    found: list[str] = []
    if isinstance(data.get("codex"), Mapping):
        found.append("codex")
        found.extend(f"codex.{key}" for key in data["codex"])
    ai = data.get("ai") if isinstance(data.get("ai"), Mapping) else {}
    providers = ai.get("providers") if isinstance(ai.get("providers"), Mapping) else {}
    codex_profiles = set(CODEX_PROVIDER_NAMES)
    for name, profile in providers.items():
        kind = profile.get("type") if isinstance(profile, Mapping) else None
        if name in CODEX_PROVIDER_NAMES or kind in CODEX_PROVIDER_TYPES:
            codex_profiles.add(name)
            found.append(f"ai.providers.{name}")
    for key in ("active_provider", "fallback_provider"):
        if ai.get(key) in codex_profiles:
            found.append(f"ai.{key}")
    routing = ai.get("routing") if isinstance(ai.get("routing"), Mapping) else {}
    found.extend(f"ai.routing.{task}" for task, route in routing.items() if route in codex_profiles)
    return found


def _database(root: Path, data: Mapping[str, Any]) -> Path:
    storage = data.get("storage") if isinstance(data.get("storage"), Mapping) else {}
    path = Path(str(storage.get("sqlite_path") or "state.sqlite"))
    return path if path.is_absolute() else root / path


def _read_only_uri(database: Path) -> str | None:
    """A read-only URI that leaves nothing new beside the database, or None when none can.

    A read-only open of a WAL-mode database creates (and leaves) empty ``-wal`` and ``-shm`` files when they are
    absent. With no ``-wal`` there is nothing uncheckpointed, so the main file is the whole database and
    ``immutable=1`` reads it with no companion file; with both present, a plain read-only open reads the WAL too."""

    uri = f"{database.resolve().as_uri()}?mode=ro"
    with open(database, "rb") as handle:
        header = handle.read(20)
    if len(header) < 20 or header[18] != 2:  # rollback journal (or not a database): a reader creates nothing
        return uri
    wal, shm = (database.with_name(database.name + suffix) for suffix in ("-wal", "-shm"))
    if not wal.exists():
        return uri + "&immutable=1"
    return uri if shm.exists() else None


def _migration_head(database: Path) -> int | str:
    if not database.is_file():
        return "no database"
    try:
        uri = _read_only_uri(database)
        if uri is None:
            return "not read (a -wal without its -shm: open the vault in the app once, then rerun)"
        connection = sqlite3.connect(uri, uri=True)
    except (OSError, sqlite3.Error) as exc:
        return f"unreadable ({type(exc).__name__})"
    try:
        row = connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
        return int(row[0]) if row and row[0] is not None else "no migrations"
    except sqlite3.Error as exc:
        return f"unreadable ({type(exc).__name__})"
    finally:
        connection.close()


def _journal(database: Path) -> dict[str, Any]:
    path = database.with_name(database.name + JOURNAL_SUFFIX)
    if not path.exists():
        return {"present": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        payload = {}
    tags = {key: payload.get(key) if isinstance(payload, dict) else None for key in ("predecessor", "target")}
    return {"present": True, **{key: value if isinstance(value, str) and TAG.match(value) else "unreadable"
                                 for key, value in tags.items()}}


def report(root: Path) -> dict[str, Any]:
    """One vault's report: tags, migration head, journal and the removal steps' keys it sets."""

    config = root / "learnloop.toml"
    try:
        data = tomllib.loads(config.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return {"vault": root.name, "error": f"no readable learnloop.toml ({type(exc).__name__})"}
    algorithms = data.get("algorithms") if isinstance(data.get("algorithms"), Mapping) else {}
    tag = algorithms.get("algorithm_version")
    database = _database(root, data)
    paths = list(_paths(data))
    return {
        "vault": root.name,
        "algorithm_version": tag if isinstance(tag, str) and TAG.match(tag) else "unset or unreadable",
        "migration_head": _migration_head(database),
        "activation_journal": _journal(database),
        "c3_keys": [path for path in paths if any(_matches(pattern, path) for pattern in C3_KEYS)],
        "c4_keys": [path for path in paths if path in C4_KEYS] + _codex_keys(data),
        "d7_switches": [f"{path} ({D7_SWITCHES[path]})" for path in paths if path in D7_SWITCHES],
    }


def _text(entry: Mapping[str, Any]) -> str:
    if "error" in entry:
        return f"{entry['vault']}: {entry['error']}"
    journal = entry["activation_journal"]
    lines = [
        f"{entry['vault']}:",
        f"  algorithm_version: {entry['algorithm_version']}",
        f"  migration head: {entry['migration_head']}",
        "  activation journal: " + (f"yes ({journal['predecessor']} -> {journal['target']})"
                                    if journal["present"] else "no"),
    ]
    for label, key in (("C3 keys set", "c3_keys"), ("C4 keys set", "c4_keys"), ("D7 switches set", "d7_switches")):
        lines.append(f"  {label}: " + (", ".join(entry[key]) if entry[key] else "none"))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("vaults", nargs="+", type=Path, help="vault directories (each holds learnloop.toml)")
    parser.add_argument("--json", action="store_true", help="print one JSON object per vault, in a list")
    args = parser.parse_args(argv)
    entries = [report(path.expanduser()) for path in args.vaults]
    print(json.dumps(entries, indent=2) if args.json else "\n\n".join(_text(entry) for entry in entries))
    return 1 if any("error" in entry for entry in entries) else 0


if __name__ == "__main__":
    sys.exit(main())
