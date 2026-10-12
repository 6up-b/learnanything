"""Opt-in embedding maintenance, with estimates before paid work."""
from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import signal
import threading
from typing import Annotated, Iterator

import typer

from learnloop.ai.spend import SpendCaps
from learnloop.vault.loader import load_vault


embeddings_app = typer.Typer(no_args_is_help=True, help="Opt-in, bounded embedding maintenance.")


@contextmanager
def _cancellation() -> Iterator[threading.Event]:
    stop = threading.Event()
    previous = {}
    if threading.current_thread() is threading.main_thread():
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, lambda *_: stop.set())
    try:
        yield stop
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


@embeddings_app.command("backfill")
def embeddings_backfill(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root; use a fixtures-local copy.")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate calls, tokens and cost; no client, migration or data changes.")] = False,
    record_kind: Annotated[list[str] | None, typer.Option(
        "--record-kind",
        help=(
            "A record kind (facet, item) or one recipe (facet/definition, item/stem); repeatable. "
            "Default: all vault recipes. Slice 1 adds hypothesis, misconception and attempt "
            "(attempt/divergence, for history_mode=hybrid), embedded only when named."
        ),
    )] = None,
    batch_size: Annotated[int, typer.Option("--batch-size", min=1, max=256)] = 32,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 100,
    max_pairs: Annotated[int, typer.Option("--max-pairs", min=0, help="Backfill uses no pairs.")] = 0,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 100,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 100_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option(
        "--price-per-million", min=0,
        help="Positive USD input-token estimate for an unknown/changed model price; still subject to cost cap.",
    )] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Embed canonical facet definitions and item stems; reruns skip saved hashes.

    Both embedding switches must be enabled for paid work. SIGINT/SIGTERM
    finishes and saves the current batch, then stops before the next request.
    Reports contain only counts, limits and model metadata, never vault text.
    """
    # Imported here: the vector store needs numpy, which no other command loads.
    from learnloop.diagnosis.split.embeddings import backfill_with_db_recipes

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must name a vault containing learnloop.toml")
        caps = SpendCaps(
            max_candidates=max_candidates, max_pairs=max_pairs,
            max_retries=max_retries, max_calls=max_calls,
            max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd,
        )
        loaded = load_vault(vault)
        if loaded.issues:
            raise ValueError(
                f"Vault has {len(loaded.issues)} validation issues; run doctor before embedding."
            )
        with _cancellation() as stop:
            report = backfill_with_db_recipes(
                loaded, caps=caps, dry_run=dry_run,
                recipes=tuple(record_kind) if record_kind else None,
                batch_size=batch_size, price_per_million=price_per_million,
                cancelled=stop.is_set,
            )
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    if json_output:
        typer.echo(json.dumps(report, sort_keys=True))
    else:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] == "cancelled":
        raise typer.Exit(code=130)
    if report["status"] not in {"dry_run", "complete"}:
        raise typer.Exit(code=1)
