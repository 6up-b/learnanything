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
            "A record kind (facet, item, concept, facet_repair) or one recipe (facet/definition, "
            "facet/dossier_scope, item/stem, item/skeleton, concept/definition, ...); "
            "repeatable. Default: all vault recipes. Slice 1 adds hypothesis, misconception and attempt "
            "(attempt/divergence, for history_mode=hybrid), embedded only when named. Slice 2 T6 adds "
            "source_block (source_block/text: every source's current blocks), also only when named, "
            "and alone."
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
    """Embed facet definitions, dossier fields, item stems and PF-b skeletons, concept definitions and repairs.

    Reruns skip saved hashes, and a text already paid for under another record
    id (an ingest-time nomination, say) is reused, not bought again.

    Both embedding switches must be enabled for paid work. SIGINT/SIGTERM
    finishes and saves the current batch, then stops before the next request.
    Reports contain only counts, limits and model metadata, never vault text.
    """
    # Imported here: the vector store needs numpy, which no other command loads.
    from learnloop.diagnosis.split.embeddings import backfill_with_db_recipes
    from learnloop.ops.embedding_backfill import backfill_embeddings
    from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES

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
        selectors = tuple(record_kind or ())
        source_kinds = {name for recipe in SOURCE_RETRIEVAL_RECIPES.values()
                        for name in (recipe.name, recipe.record_kind)}
        source_selected = [value for value in selectors if value in source_kinds]
        if source_selected and len(source_selected) != len(selectors):
            raise ValueError("Select source_block on its own (its corpus has its own caps); "
                             "run the other recipes in a separate backfill.")
        with _cancellation() as stop:
            if source_selected:
                # Slice 2 T6: the source library is never in the default
                # backfill; it is embedded only when named.
                report = backfill_embeddings(
                    loaded, caps=caps, dry_run=dry_run, recipes=selectors,
                    batch_size=batch_size, price_per_million=price_per_million,
                    cancelled=stop.is_set, registry=SOURCE_RETRIEVAL_RECIPES,
                )
            else:
                report = backfill_with_db_recipes(
                    loaded, caps=caps, dry_run=dry_run,
                    recipes=selectors if record_kind else None,
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


@embeddings_app.command("nomination-report")
def embeddings_nomination_report(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root; use a fixtures-local copy.")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan the backfill the report needs; no client, migration or data changes.")] = False,
    stored_only: Annotated[bool, typer.Option("--stored-only", help="Skip the backfill; report from vectors already stored (no model calls).")] = False,
    batch_size: Annotated[int, typer.Option("--batch-size", min=1, max=256)] = 32,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 1_000,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 100,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 1_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 0.25,
    price_per_million: Annotated[float | None, typer.Option(
        "--price-per-million", min=0,
        help="Positive USD input-token estimate for an unknown/changed model price; still subject to cost cap.",
    )] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Slice 2 T5 report: embedding nomination recall on doctor-found duplicates.

    Backfills facet and concept definitions and facet repairs (paid, capped;
    both embedding switches must be on), then reports recall@k against the
    lexical review passes, candidate blocking cutoffs (recorded, never applied),
    the noise floor, embedding-only nominations, the repair-equivalence shadow
    and what ingest nominated. Nominations never merge anything.
    """
    from learnloop.ops.graph_nomination_report import nomination_report

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must name a vault containing learnloop.toml")
        if dry_run and stored_only:
            raise ValueError("--dry-run plans the backfill; --stored-only skips it. Pass one.")
        caps = SpendCaps(
            max_candidates=max_candidates, max_pairs=0,
            max_retries=max_retries, max_calls=max_calls,
            max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd,
        )
        loaded = load_vault(vault)
        if loaded.issues:
            raise ValueError(
                f"Vault has {len(loaded.issues)} validation issues; run doctor before reporting."
            )
        with _cancellation() as stop:
            report = nomination_report(
                loaded, caps=caps, dry_run=dry_run, stored_only=stored_only,
                batch_size=batch_size, price_per_million=price_per_million,
                cancelled=stop.is_set,
            )
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2))
    if report["status"] == "cancelled":
        raise typer.Exit(code=130)
    if report["status"] not in {"dry_run", "complete"}:
        raise typer.Exit(code=1)


@embeddings_app.command("compare")
def embeddings_compare(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root (routes, ledger, checkpoints); use a fixtures-local copy.")],
    suite: Annotated[str, typer.Option("--suite", help="Registered suite: b2 (isomorph/near-duplicate), valid_alternative, b1 (Eedi 2024 misconception retrieval), b3 (recurrence vault replay), source_retrieval (Slice 2 T6 report) or b4 (PDF page images vs text chunks).")],
    output_dir: Annotated[Path, typer.Option("--output", "--output-dir", help="Report and vector-cache directory (outside the vault).")] = Path("fixtures-local/reports/compare"),
    benchmark: Annotated[Path | None, typer.Option("--benchmark", help="Benchmark directory: manifest.json (source, version, licence) and pairs.jsonl (b2), or the Eedi train.csv and misconception_mapping.csv (b1).")] = None,
    model: Annotated[list[str] | None, typer.Option("--model", help="Embedding model id (OpenRouter); repeatable. Default: embedding.model.")] = None,
    dims: Annotated[list[int] | None, typer.Option("--dims", min=1, help="MRL dimension sweep; repeatable. Default: embedding.dimensions (b1: 1024, a width every candidate reaches).")] = None,
    view: Annotated[list[str] | None, typer.Option("--view", help="b2 views: stem, skeleton, fingerprint, judge; b1 views: raw, hypothesis. source_retrieval systems: substring, keyword, meaning, hybrid, hybrid_rewrite. b4 systems: text, image, keyword, hybrid. Repeatable. Default: all.")] = None,
    family: Annotated[list[str] | None, typer.Option("--family", help="valid_alternative: activity family id; repeatable.")] = None,
    target_recall: Annotated[float, typer.Option("--target-recall", min=0.5, max=1.0, help="Recall on positives that sets each blocking cutoff (b3: on confirmed matches, also top_k).")] = 0.95,
    max_cases: Annotated[int | None, typer.Option("--max-cases", min=1, help="b2: pairs; source_retrieval and b4: questions (default 40 and 30).")] = None,
    max_items: Annotated[int, typer.Option("--max-items", min=1, help="valid_alternative: family items to cover; b4: pages per PDF source in the corpus.")] = 20,
    alternatives: Annotated[int, typer.Option("--alternatives", min=1, max=6, help="valid_alternative: alternative traces per item.")] = 2,
    tier: Annotated[str | None, typer.Option("--tier", help="Run the PF roles at a [pf.scaling] tier (cheap or frontier); B2's judge view then measures that tier's judge on labelled pairs.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan calls and tokens; no client, request or write.")] = False,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 100,
    max_pairs: Annotated[int, typer.Option("--max-pairs", min=0)] = 2000,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 500,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 4_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 2.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="One owner price for metered LLM roles' input AND output tokens (USD per million): an upper bound when it is the output price. Prefer --input-price-per-million with --output-price-per-million. Codex roles estimate only.")] = None,
    embedding_price_per_million: Annotated[float | None, typer.Option("--embedding-price-per-million", min=0, help="Embedding input price for models without a built-in estimate.")] = None,
    input_price_per_million: Annotated[float | None, typer.Option("--input-price-per-million", min=0, help="Owner input-token price for metered LLM roles (USD per million); pass with --output-price-per-million instead of --price-per-million.")] = None,
    output_price_per_million: Annotated[float | None, typer.Option("--output-price-per-million", min=0, help="Owner output-token price for metered LLM roles (USD per million); pass with --input-price-per-million.")] = None,
    writer_output_tokens: Annotated[int | None, typer.Option("--writer-output-tokens", min=1, help="b1: the hypothesis writer's output budget per case (default: the output-budget policy's for the diagnosis route, ai.output_tokens 16384 unless overridden; a reasoning model's reasoning tokens count against it). Part of the writer's cache identity.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run one registered benchmark suite on the shared harness (B2 sets PF's blocking cutoffs).

    Slice 2 T1's B1 (Eedi 2024; its hypothesis writer is the
    recurrence_hypothesis_writer role on the diagnosis route) and B3 (the
    vault's labelled hypothesis pairs; prints the [recurrence] top_k and
    cutoff it would set) run here too; `learnloop recurrence bench` is an
    alias for these two suites.

    Writes aggregate-only JSON and Markdown reports named by content. Every
    verdict appends to judgment_ledger; replay never reads these reports.
    Spend reports lead with what the providers billed (``usage.billed``);
    ``usage.charged`` is the reservation-based cap accounting.
    """
    from learnloop.diagnosis.recurrence.benchmarks import register_suites as register_recurrence_suites
    from learnloop.ops.embedding_compare import SUITES, CompareRequest, run_compare
    from learnloop.ops.pf_calls import ROLE_TASKS
    from learnloop.source_retrieval.suites import register_suites as register_source_retrieval_suites

    # This command is the shared harness's composition root: every consumer
    # suite (Phase 5a's b2 and valid_alternative; Slice 2 T1's B1/B3; T6's
    # source_retrieval report and B4) joins `embedding_compare.SUITES`, and any
    # extra LLM role joins
    # `pf_calls.ROLE_TASKS`, here before run_compare, through the consumer's
    # `register_suites(SUITES, role_tasks=ROLE_TASKS)`. Registration lives here,
    # not in ops, because ops -> diagnosis (or source_retrieval) would be a new
    # import back-edge.
    register_recurrence_suites(SUITES, role_tasks=ROLE_TASKS)
    register_source_retrieval_suites(SUITES, role_tasks=ROLE_TASKS)
    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must name a vault containing learnloop.toml")
        loaded = load_vault(vault)
        request = CompareRequest(
            suite=suite, output_dir=output_dir, benchmark_dir=benchmark, models=tuple(model or ()),
            dims=tuple(dims or ()), views=tuple(view or ()), family_ids=tuple(family or ()),
            target_recall=target_recall, max_cases=max_cases, alternatives=alternatives,
            max_items=max_items, tier=tier, dry_run=dry_run, writer_output_tokens=writer_output_tokens,
        )
        caps = SpendCaps(
            max_candidates=max_candidates, max_pairs=max_pairs, max_retries=max_retries,
            max_calls=max_calls, max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd,
        )
        with _cancellation() as stop:
            report = run_compare(loaded, request=request, caps=caps, price_per_million=price_per_million,
                                 embedding_price_per_million=embedding_price_per_million,
                                 input_price_per_million=input_price_per_million,
                                 output_price_per_million=output_price_per_million,
                                 cancelled=stop.is_set)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    typer.echo(json.dumps(report, sort_keys=True, default=str, indent=None if json_output else 2))
    if report["status"] == "cancelled":
        raise typer.Exit(code=130)
    if report["status"] not in {"dry_run", "complete"}:
        raise typer.Exit(code=1)


@embeddings_app.command("adjudicate")
def embeddings_adjudicate(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root; use a fixtures-local copy first.")],
    task: Annotated[str, typer.Option("--task", help="The judgment_ledger task to adjudicate. Slice 2 T1: same_cause.")] = "same_cause",
    backlog: Annotated[bool, typer.Option("--backlog", help="Judge the shortlisted pairs of the existing history (required).")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan pairs, vectors to embed and spend; no client, call or write.")] = False,
    max_pairs_to_judge: Annotated[int | None, typer.Option("--max-pairs-to-judge", min=1, help="Judge at most this many pairs this run (earliest first).")] = None,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 300,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 30,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 3_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option(
        "--price-per-million", min=0,
        help="USD per million tokens for a metered route whose price is unknown (unknown prices fail closed).",
    )] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Embeddings shortlist, the judge decides: adjudicate a task's candidate pairs.

    `--task same_cause --backlog` (Slice 2 T1 §3.1) embeds any hypothesis
    without a vector for embedding.model, shortlists each learner-state
    hypothesis's earlier in-scope neighbours (recurrence.top_k, and the B3
    cutoff when set), skips settled pairs and sends every other pair to the
    same-cause judge (ai.routing.same_cause_judge, unset: the diagnosis
    route). Verdicts go to judgment_ledger; groups are refreshed. Nothing is
    merged or rejected by score. Run --dry-run first.
    """

    from learnloop.cli.receipts import bind_command_repository, bind_command_vault
    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.recurrence.backlog import run_backlog
    from learnloop.vault.paths import VaultPaths
    from learnloop.vault.repository import open_vault_repository

    try:
        if task != "same_cause":
            raise ValueError(f"unknown task {task!r}: Slice 2 T1 registers same_cause")
        if not backlog:
            raise ValueError("pass --backlog: live pairs are judged inside the diagnosis job")
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must name a vault containing learnloop.toml")
        loaded = load_vault(vault)
        bind_command_vault(loaded.root)
        sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
        if dry_run:
            repository = Repository.attach(sqlite_path, read_only=True)
        else:
            repository = open_vault_repository(loaded.root, sqlite_path)
            bind_command_repository(repository)
        caps = SpendCaps(
            max_candidates=max_calls, max_pairs=max_calls, max_retries=max_retries,
            max_calls=max_calls, max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd,
        )
        with _cancellation() as stop:
            report = run_backlog(
                loaded, repository, caps=caps, price_per_million=price_per_million,
                max_pairs=max_pairs_to_judge, dry_run=dry_run, cancelled=stop.is_set,
            )
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    typer.echo(json.dumps(report, sort_keys=True, default=str, indent=None if json_output else 2))
    if report["status"] == "cancelled":
        raise typer.Exit(code=130)
    if report["status"] not in {"dry_run", "complete"}:
        raise typer.Exit(code=1)


# -- Local contextual retrieval P0/P1a/P1b (spec_local_contextual_retrieval_v1) -----------
local_app = typer.Typer(no_args_is_help=True, help="The local pplx v2 9B source space (owner-run, off by default).")
embeddings_app.add_typer(local_app, name="local")
fallback_app = typer.Typer(no_args_is_help=True, help="The hosted Voyage fallback source space (opt-in, capped).")
embeddings_app.add_typer(fallback_app, name="fallback")
fusion_app = typer.Typer(no_args_is_help=True, help="The learned fusion of source spaces (logged; seed weights serve).")
embeddings_app.add_typer(fusion_app, name="fusion")


def _vault_and_repository(vault: Path, *, write: bool):
    from learnloop.cli.receipts import bind_command_repository, bind_command_vault
    from learnloop.db.repositories import Repository
    from learnloop.vault.paths import VaultPaths
    from learnloop.vault.repository import open_vault_repository

    if not (vault / "learnloop.toml").is_file():
        raise ValueError("--vault must name a vault containing learnloop.toml")
    loaded = load_vault(vault)
    bind_command_vault(loaded.root)
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    if not write:
        return loaded, Repository.attach(sqlite_path, read_only=True)
    repository = open_vault_repository(loaded.root, sqlite_path)
    bind_command_repository(repository)
    return loaded, repository


def _emit(report: dict, json_output: bool, ok: frozenset[str]) -> None:
    typer.echo(json.dumps(report, sort_keys=True, default=str, indent=None if json_output else 2))
    if report.get("status") not in ok:
        raise typer.Exit(code=1)


@local_app.command("setup")
def local_setup(
    data_root: Annotated[Path | None, typer.Option("--data-root", help="Default ~/.local/share/learnloop.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show the paths, pins and disk check; start nothing.")] = False,
    download: Annotated[bool, typer.Option(
        "--i-understand-this-downloads-33-gb", help="Required to create the env and download the model.")] = False,
    adopt_model_dir: Annotated[Path | None, typer.Option(
        "--adopt-model-dir", help="Record an existing model directory (verified; nothing moved).")] = None,
    adopt_env_python: Annotated[Path | None, typer.Option(
        "--adopt-env-python", help="Record an existing environment's interpreter (nothing moved).")] = None,
    skip_weight_digests: Annotated[bool, typer.Option(
        "--skip-weight-digests", help="Check shard sizes only (the remote code is always hashed).")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create the separate environment, download the pinned model and verify it (owner-run).

    Only this command creates ~/.local/share/learnloop/{envs,models}. Then set
    embedding.local.enabled = true in the vault and run `embeddings local index`."""

    from learnloop.local_embeddings.setup import run_setup, setup_plan

    try:
        if dry_run:
            report = {"status": "dry_run", **setup_plan(data_root)}
        else:
            adopting = adopt_model_dir is not None
            if not adopting and not download:
                raise ValueError("pass --i-understand-this-downloads-33-gb (or --adopt-model-dir); run --dry-run first")
            report = run_setup(root=data_root, adopt_model_dir=adopt_model_dir, adopt_env_python=adopt_env_python,
                               verify_weights=not skip_weight_digests)
    except (ValueError, RuntimeError, OSError) as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"dry_run", "ready"}))


@local_app.command("index")
def local_index(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root.")],
    now: Annotated[bool, typer.Option("--now", help="Ignore the batch wait (embedding.local.index_batch_minutes).")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Count the owed windows; launch nothing.")] = False,
    data_root: Annotated[Path | None, typer.Option("--data-root")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Index every owed window (grouped and singleton) in ONE capped 9B worker batch.

    The worker runs in its own systemd scope (MemoryMax=12G, swap 0) under the
    GPU and full-suite locks and refuses to start under the memory and GPU
    floors; waiting is not a failure."""

    from learnloop.source_retrieval.local_index import run_local_index

    try:
        loaded, repository = _vault_and_repository(vault, write=not dry_run)
        report = run_local_index(loaded, repository, root=data_root, force=now, dry_run=dry_run)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"complete", "dry_run", "waiting_for_gpu", "waiting_for_batch"}))


@local_app.command("profile")
def local_profile(
    vault: Annotated[Path, typer.Option("--vault", help="A vault copy whose teaching text fills the windows.")],
    extraction_id: Annotated[str, typer.Option("--extraction-id", help="The source extraction to profile on.")],
    tokens: Annotated[list[int] | None, typer.Option("--tokens", help="Sizes by the model's own count (repeatable).")] = None,
    data_root: Annotated[Path | None, typer.Option("--data-root")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """P0: the true 8,192-token profile (one metered worker; nothing indexed).

    Windows are fitted by the model's own tokenizer (E1's were estimates and
    reached 5,603 tokens). Teaching text only; aggregates only in the output."""

    from learnloop.source_retrieval.local_index import run_profile

    try:
        loaded, repository = _vault_and_repository(vault, write=False)
        report = run_profile(loaded, repository, extraction_id, root=data_root,
                             **({"sizes": tuple(tokens)} if tokens else {}))
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"complete"}))


@local_app.command("status")
def local_status(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root.")],
    data_root: Annotated[Path | None, typer.Option("--data-root")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Per local space: cache rows, covered sources, epoch and canary status."""

    from learnloop.source_retrieval.local_index import coverage_report

    try:
        loaded, repository = _vault_and_repository(vault, write=False)
        report = {"status": "ok", **coverage_report(loaded, repository, data_root)}
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"ok"}))


# -- Local retrieval P2: the query student (owner-run; nothing here runs by itself) ---------
student_app = typer.Typer(no_args_is_help=True, help="P2: the 0.6B query student (owner-run, dry run first).")
local_app.add_typer(student_app, name="student")
_BANK_HELP = "The frozen E0/E1 bank (private JSON/JSONL): the leakage guard; never in a prompt or a loss."


@student_app.command("setup")
def student_setup(
    adopt_base: Annotated[list[str] | None, typer.Option(
        "--adopt-base", help="NAME=DIR: record a downloaded base in place (verified; nothing moved). Repeatable.")] = None,
    data_root: Annotated[Path | None, typer.Option("--data-root")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show the pinned bases and paths; start nothing.")] = False,
    skip_weight_digests: Annotated[bool, typer.Option(
        "--skip-weight-digests", help="Check weight sizes only (code and small files are always hashed).")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record the two pinned 0.6B bases (pplx-embed-v1-0.6b primary, Qwen3-Embedding-0.6B second).

    Run after `embeddings local setup`. Without --adopt-base a missing base is
    downloaded at its pinned revision (about 1.2 and 2.4 GB) into the data root."""

    from learnloop.source_retrieval.query_student import setup_bases

    try:
        adopt = {}
        for item in adopt_base or []:
            name, _sep, directory = item.partition("=")
            if not directory:
                raise ValueError("--adopt-base takes NAME=DIR")
            adopt[name.strip()] = Path(directory).expanduser()
        unknown = sorted(set(adopt) - {"pplx-embed-v1-0.6b", "qwen3-embedding-0.6b"})
        if unknown:
            raise ValueError("unknown base(s): " + ", ".join(unknown))
        report = setup_bases(root=data_root, adopt=adopt, verify_weights=not skip_weight_digests, dry_run=dry_run)
    except (ValueError, OSError) as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"dry_run", "ready"}))


@student_app.command("plan")
def student_plan(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root.")],
    bank: Annotated[Path | None, typer.Option("--bank", help=_BANK_HELP)] = None,
    data_root: Annotated[Path | None, typer.Option("--data-root")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The whole P2 dry run: questions, plan calls, teacher targets, the run schedule, GPU-hours."""

    from learnloop.source_retrieval.query_student import plan

    try:
        loaded, repository = _vault_and_repository(vault, write=False)
        report = plan(loaded, repository, bank_path=bank, root=data_root)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"dry_run"}))


@student_app.command("generate")
def student_generate(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root.")],
    bank: Annotated[Path | None, typer.Option("--bank", help=_BANK_HELP)] = None,
    budget: Annotated[int, typer.Option("--budget", help="Training questions wanted at most (nested 2k/10k/50k).")] = 50_000,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Passages, calls, tokens and cost; send nothing.")] = False,
    data_root: Annotated[Path | None, typer.Option("--data-root")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Synthetic questions from permitted passages (route ai.routing.retrieval_query_generator).

    Background-quiet on the ChatGPT plan (GPT-6 Luna by default): a plan that
    is down is reported; LEARNLOOP_AI_FALLBACK=openrouter for this command asks
    for OpenRouter instead (metered, capped at
    embedding.local.student_generator_max_cost_usd)."""

    from learnloop.source_retrieval.query_student import context
    from learnloop.source_retrieval.student_data import generate

    try:
        loaded, repository = _vault_and_repository(vault, write=not dry_run)
        manifest, space, reason = context(loaded, data_root)
        if manifest is None:
            report = {"status": "disabled", "reason": reason}
        else:
            with _cancellation() as stop:
                report = generate(loaded, repository, space_id=space, bank_path=bank, data_root=data_root,
                                  budget=budget, dry_run=dry_run, cancelled=stop.is_set)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"dry_run", "complete"}))


@student_app.command("targets")
def student_targets(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root (its index's canaries are checked).")],
    bank: Annotated[Path | None, typer.Option("--bank", help=_BANK_HELP)] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Count owed questions; launch nothing.")] = False,
    data_root: Annotated[Path | None, typer.Option("--data-root")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The teacher's targets: ONE 9B worker batch in query mode (12G scope, GPU lock, P2 meter)."""

    from learnloop.source_retrieval.query_student import run_targets

    try:
        loaded, repository = _vault_and_repository(vault, write=False)
        report = run_targets(loaded, repository, bank_path=bank, root=data_root, dry_run=dry_run)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"dry_run", "complete", "waiting_for_gpu"}))


@student_app.command("train")
def student_train(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root.")],
    bank: Annotated[Path | None, typer.Option("--bank", help=_BANK_HELP)] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show the next run of the schedule; launch nothing.")] = False,
    data_root: Annotated[Path | None, typer.Option("--data-root")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run the schedule's NEXT training run (screen, recipes, learning curve, seeds); rerun until it says evaluate."""

    from learnloop.source_retrieval.query_student import run_next

    try:
        loaded, repository = _vault_and_repository(vault, write=False)
        report = run_next(loaded, repository, bank_path=bank, root=data_root, dry_run=dry_run)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"dry_run", "trained", "evaluate", "waiting_for_gpu"}))


@student_app.command("evaluate")
def student_evaluate(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root.")],
    bank: Annotated[Path | None, typer.Option("--bank", help="The labelled bank (private JSON/JSONL).")] = None,
    arm: Annotated[list[str] | None, typer.Option(
        "--arm", help="NAME=FILE: per-question outcomes of an alternative (qwen, voyage, keyword). Repeatable.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Check the inputs; start nothing.")] = False,
    data_root: Annotated[Path | None, typer.Option("--data-root")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The candidate on the bank beside the teacher; ADOPTED when E[U(student)] >= each alternative (spec §9.3)."""

    from learnloop.source_retrieval.query_student import evaluate

    try:
        arms = {}
        for item in arm or []:
            name, _sep, path = item.partition("=")
            if not path:
                raise ValueError("--arm takes NAME=FILE")
            arms[name.strip()] = Path(path).expanduser()
        loaded, repository = _vault_and_repository(vault, write=False)
        report = evaluate(loaded, repository, bank_path=bank, root=data_root, arms=arms, dry_run=dry_run)
    except (ValueError, RuntimeError, TimeoutError) as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"dry_run", "adopted", "not_adopted"}))


@student_app.command("revoke")
def student_revoke(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root.")],
    data_root: Annotated[Path | None, typer.Option("--data-root")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Withdraw the adopted checkpoint (embedding.local.student = false is the switch for every vault)."""

    from learnloop.source_retrieval.query_student import revoke

    try:
        loaded, _repository = _vault_and_repository(vault, write=False)
        report = revoke(loaded, root=data_root)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"revoked", "none"}))


@student_app.command("status")
def student_status(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root.")],
    data_root: Annotated[Path | None, typer.Option("--data-root")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Bases, questions, targets, runs, the P2 meter, the adoption and the teacher replay."""

    from learnloop.source_retrieval.query_student import status

    try:
        loaded, repository = _vault_and_repository(vault, write=False)
        report = {"status": "ok", **status(loaded, repository, root=data_root)}
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"ok"}))


@fallback_app.command("backfill")
def fallback_backfill(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root; use a fixtures-local copy.")],
    extraction_id: Annotated[list[str] | None, typer.Option(
        "--extraction-id", help="Repeatable; default every current extraction.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Windows, requests and the dollar bound; send nothing.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Embed the Voyage fallback space's missing windows: the WHOLE command is
    one run, capped at embedding.fallback.max_cost_usd_per_run and admitted
    at the full price (the aggregate estimate and charge are reported)."""

    from learnloop.source_retrieval.corpus import current_extractions
    from learnloop.source_retrieval.fallback_space import backfill_fallback_run

    try:
        loaded, repository = _vault_and_repository(vault, write=not dry_run)
        targets = list(extraction_id or sorted(current_extractions(repository)))
        with _cancellation() as stop:
            report = backfill_fallback_run(loaded, repository, targets, cancelled=stop.is_set, dry_run=dry_run)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"dry_run", "complete"}))


@fusion_app.command("refit")
def fusion_refit(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Refit the fusion posterior from the feedback receipts (no model call)."""

    from learnloop.local_embeddings.fusion import refit_posteriors

    try:
        loaded, repository = _vault_and_repository(vault, write=True)
        report = {"status": "complete", **refit_posteriors(loaded, repository)}
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, frozenset({"complete"}))
