"""`learnloop recurrence`: Slice 2 T1 (M3) recurrence groups with authority.

* ``guard``: the same-answer/different-cause suite through the same-cause
  judge (paid; ``--dry-run`` first). Any false merge blocks ``learnloop
  upgrade --to mvp-0.11``.
* ``groups``: the current recurrence groups and review cases (no call).
* ``report``: the M3 signals report after 2-4 weeks (no call).
* ``bench``: B1 (Eedi) and B3 (vault replay) through the local runner until
  Phase 5a's ``learnloop embeddings compare`` merges (then ``--suite b1|b3``
  there runs the same suites).

The backlog judge is ``learnloop embeddings adjudicate --task same_cause
--backlog``.
"""

from __future__ import annotations

import json
import signal
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Iterator

import typer

from learnloop.ai.spend import SpendCaps
from learnloop.cli.receipts import bind_command_repository, bind_command_vault
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository

recurrence_app = typer.Typer(
    no_args_is_help=True,
    help="Slice 2 T1: recurrence groups, the same-cause guard, the M3 report and the B1/B3 benchmarks.",
)


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


def _load(vault: Path):
    if not (vault / "learnloop.toml").is_file():
        raise typer.BadParameter("--vault must name a vault containing learnloop.toml")
    loaded = load_vault(vault)
    bind_command_vault(loaded.root)
    return loaded


def _repository(loaded, *, read_only: bool):
    from learnloop.db.repositories import Repository

    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    if read_only:
        return Repository.attach(sqlite_path, read_only=True)
    repository = open_vault_repository(loaded.root, sqlite_path)
    bind_command_repository(repository)
    return repository


def _echo(payload: object, json_output: bool) -> None:
    typer.echo(json.dumps(payload, sort_keys=True, default=str, indent=None if json_output else 2))


def _caps(max_calls: int, max_retries: int, max_tokens: int, max_cost_usd: float) -> SpendCaps:
    return SpendCaps(
        max_candidates=max_calls, max_pairs=max_calls, max_retries=max_retries,
        max_calls=max_calls, max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd,
    )


_PRICE_HELP = "USD per million tokens for a metered judge route whose price is unknown (unknown prices fail closed)."


@recurrence_app.command("guard")
def recurrence_guard(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (a fixtures-local copy first).")],
    from_run: Annotated[Path | None, typer.Option("--from-run", help="Also judge an M1 review run's planted same-answer/different-cause cases.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Count the pairs and estimate the calls; no client, no call, no write.")] = False,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 60,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 20,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 400_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help=_PRICE_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run the same-answer/different-cause regression suite through the judge.

    Every planted pair is judged once per judge prompt version (reruns skip
    judged pairs); verdicts go to judgment_ledger on planted subjects, which
    never join the vault's groups. A false merge on any negative pair blocks
    `learnloop upgrade --to mvp-0.11`.
    """

    from learnloop.diagnosis.recurrence.guard import run_guard

    loaded = _load(vault)
    repository = _repository(loaded, read_only=dry_run)
    with _cancellation() as stop:
        report = run_guard(
            loaded, repository, caps=_caps(max_calls, max_retries, max_tokens, max_cost_usd),
            price_per_million=price_per_million, from_run=from_run, dry_run=dry_run, cancelled=stop.is_set,
        )
    _echo(report, json_output)
    if report["status"] not in {"dry_run", "complete"}:
        raise typer.Exit(code=1)
    result = report.get("result") or {}
    if result and not result.get("passed"):
        raise typer.Exit(code=2)


@recurrence_app.command("groups")
def recurrence_groups(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    reviews: Annotated[bool, typer.Option("--reviews/--no-reviews", help="Also list the review cases.")] = True,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The current recurrence groups (merged classes only) and review cases. No call."""

    loaded = _load(vault)
    repository = _repository(loaded, read_only=True)
    members = repository.recurrence_groups()
    groups: dict[str, list[dict]] = {}
    for row in members:
        groups.setdefault(str(row["group_key"]), []).append(row)
    payload = {
        "state": repository.recurrence_state(),
        "groups": [
            {
                "group_key": key,
                "classes": rows[0]["class_count"],
                "members": [
                    {key_: row[key_] for key_ in ("episode_key", "statement_normalized", "joined_by", "judge", "joined_by_ref")}
                    for row in rows
                ],
            }
            for key, rows in sorted(groups.items())
        ],
    }
    if reviews:
        payload["review_cases"] = repository.recurrence_review()
    _echo(payload, json_output)


@recurrence_app.command("report")
def recurrence_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    out: Annotated[Path | None, typer.Option("--out", help="Write the Markdown report here (JSON beside it).")] = None,
    audit_sample: Annotated[int, typer.Option("--audit-sample", min=0, max=200, help="Merged groups shown for the precision audit.")] = 10,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The M3 signals report (run after 2-4 weeks at mvp-0.11). No model or embedding call."""

    from learnloop.diagnosis.recurrence.report import m3_report, render_markdown

    loaded = _load(vault)
    repository = _repository(loaded, read_only=True)
    report = m3_report(loaded, repository, audit_sample=audit_sample)
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_markdown(report), encoding="utf-8")
        out.with_suffix(".json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    _echo(report if json_output or out is None else {"written": str(out)}, json_output)


@recurrence_app.command("bench")
def recurrence_bench(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (routes, receipts); use a fixtures-local copy.")],
    suite: Annotated[str, typer.Option("--suite", help="b1 (Eedi 2024) or b3 (vault replay).")],
    output_dir: Annotated[Path, typer.Option("--output", "--output-dir", help="Report and vector-cache directory (outside the vault).")] = Path("fixtures-local/reports/recurrence-bench"),
    benchmark: Annotated[Path | None, typer.Option("--benchmark", help="b1: directory with the Eedi train.csv, misconception_mapping.csv and a manifest.json.")] = None,
    model: Annotated[list[str] | None, typer.Option("--model", help="Embedding model id (OpenRouter); repeatable. b1 default: the five candidates; b3: embedding.model.")] = None,
    dims: Annotated[int, typer.Option("--dims", min=1, help="Common MRL width for every model compared.")] = 1024,
    view: Annotated[list[str] | None, typer.Option("--view", help="b1 query views: raw, hypothesis; repeatable. Default: both.")] = None,
    target_recall: Annotated[float, typer.Option("--target-recall", min=0.5, max=1.0, help="b3: recall on confirmed matches that sets the cutoff and top_k.")] = 0.95,
    max_cases: Annotated[int | None, typer.Option("--max-cases", min=1, help="b1: cases sampled (deterministically).")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan calls and tokens; no client, request or write.")] = False,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 2_000,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 50,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 10_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 2.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="Owner price for a metered hypothesis-writer route (b1).")] = None,
    embedding_price_per_million: Annotated[float | None, typer.Option("--embedding-price-per-million", min=0, help="Embedding input price for models without a built-in estimate.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run B1 or B3 (interim runner until Phase 5a's `embeddings compare` merges).

    B1's hypothesis writer uses the diagnosis route (Codex: estimated only);
    every embedding request is metered and admitted against the caps. Vectors
    are cached in the output directory, never in the vault. Reports are
    aggregate; B3 prints the recommended [recurrence] top_k and cutoff.
    """

    from learnloop.diagnosis.recurrence.benchmarks import BenchRequest, run_bench

    loaded = _load(vault)
    request = BenchRequest(
        suite=suite, output_dir=output_dir, benchmark_dir=benchmark, models=tuple(model or ()), dims=dims,
        views=tuple(view or ()), target_recall=target_recall, max_cases=max_cases, dry_run=dry_run,
    )
    caps = SpendCaps(
        max_candidates=max_calls, max_pairs=0, max_retries=max_retries, max_calls=max_calls,
        max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd,
    )
    try:
        with _cancellation() as stop:
            report = run_bench(
                loaded, request=request, caps=caps, price_per_million=price_per_million,
                embedding_price_per_million=embedding_price_per_million, cancelled=stop.is_set,
            )
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _echo(report, json_output)
    if report["status"] not in {"dry_run", "complete"}:
        raise typer.Exit(code=1)


__all__ = ["recurrence_app"]
