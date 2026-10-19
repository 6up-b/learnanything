"""`learnloop hints`: the hint-use report (adaptive hints H0; spec §6.3) and
approach maps (H1; spec §4.3.1).

`hints report` is read-only: the database is opened read-only, never migrated,
and no model is called. The report carries ids, counts, shares and timings,
never learner text; H1 adds its `maps` section.

`hints maps build` is the owner's backfill: `--dry-run` opens the database
read-only, retrieves nothing, calls nothing, writes nothing and prints the
estimate; a real run builds the selected items' missing maps under
`hints.maps.max_daily_cost_usd` and says so when the day is capped.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

import typer

from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

hints_app = typer.Typer(no_args_is_help=True, help="Hints: the hint-use report and approach maps.")
maps_app = typer.Typer(no_args_is_help=True, help="Approach maps (H1): build the subgoal maps hints will use.")
hints_app.add_typer(maps_app, name="maps")

_RELATIVE = re.compile(r"^(\d+)([dh])$")
_SURFACES = ("practice", "workbench", "guided_redo", "tutor")


def _since(value: str | None, now: datetime) -> str | None:
    if value is None:
        return None
    match = _RELATIVE.match(value.strip())
    if match:
        amount, unit = int(match.group(1)), match.group(2)
        return (now - (timedelta(days=amount) if unit == "d" else timedelta(hours=amount))).isoformat()
    return value


@hints_app.command("report")
def hints_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    since: Annotated[
        str | None,
        typer.Option("--since", help="Only hints shown at or after this ISO time, or a span such as 7d or 24h."),
    ] = None,
    surface: Annotated[
        str | None,
        typer.Option("--surface", help="Only one surface: practice, workbench, guided_redo or tutor."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Hints by surface, kind and level (authored hints are the baseline): shown, items,
    sessions, timing, more help, the attempt's outcome and later independent success;
    "doesn't connect" by shortcut, outcome placements, the expertise-reversal split,
    help abuse and avoidance counts, and latency and cost per route. Read-only."""

    from learnloop.hints.report import build_hints_report, item_caps

    now = datetime.now(UTC)
    try:
        if surface is not None and surface not in _SURFACES:
            raise ValueError(f"--surface must be one of {', '.join(_SURFACES)}")
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        report = build_hints_report(
            path, since=_since(since, now), surface=surface, now=now,
            item_caps=item_caps(loaded.practice_items.values()),
        )
        report["hints"] = loaded.config.hints.model_dump(mode="json")
        if surface in (None, "workbench"):
            # Reader workbench RW2b: the checkpoint's workbench rows (absent
            # when the vault has none).
            from learnloop.hints.report_workbench import build_workbench_report

            block = build_workbench_report(path, since=_since(since, now), item_facets={
                item.id: [loaded.canonical_facet_id(str(facet)) for facet in item.evidence_facets]
                for item in loaded.practice_items.values()},
                symbolic_enabled=bool(loaded.config.workbench.symbolic_checks_enabled))
            if block is not None:
                report["workbench"] = block
        from learnloop.hints.map_report import build_maps_report

        report["maps"] = build_maps_report(loaded, path)
        typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc


@maps_app.command("build")
def maps_build(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    item: Annotated[str | None, typer.Option("--item", help="Only this practice item.")] = None,
    family: Annotated[str | None, typer.Option("--family", help="Only the items of this practice family.")] = None,
    lo: Annotated[str | None, typer.Option("--lo", help="Only the items of this learning object.")] = None,
    limit: Annotated[
        int | None, typer.Option("--limit", min=1, help="Build at most this many maps in this run.")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Print the plan and the estimate; retrieve, call and write nothing.")
    ] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Build approach maps for active items that have none for their current revision
    (all items, or one --item, --family or --lo). Run --dry-run first."""

    from learnloop.hints.map_builder import backfill, select_items
    from learnloop.practice_index.paid import planning_repository

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault)
        items = select_items(loaded, item_id=item, family_id=family, learning_object_id=lo)
        repository = planning_repository(VaultPaths(loaded.root, loaded.config), dry_run=dry_run)
        result = backfill(loaded, repository, items, dry_run=dry_run, limit=limit)
        typer.echo(json.dumps(result, sort_keys=True, indent=None if json_output else 2, default=str))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc
