---
title: "learnloop.cli.embeddings"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/embeddings.py"
source_paths:
  - "src/learnloop/cli/embeddings.py"
source_commit: "305e5301bbc88d25194ab01fde335cd70e33d262"
source_commit_timestamp: "2026-10-26T14:45:07-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.embeddings module"
  - "src/learnloop/cli/embeddings.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.embeddings`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.embeddings` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: Opt-in embedding maintenance, with estimates before paid work.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/embeddings.py](../../../../../../src/learnloop/cli/embeddings.py) |
| Source lines | 751 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `305e5301bbc88d25194ab01fde335cd70e33d262` |
| Commit timestamp | `2026-10-26T14:45:07-04:00` |

## Public API

- `embeddings_backfill(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root; use a fixtures-local copy.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate calls, tokens and cost; no client, migration or data changes.')]=False, record_kind: Annotated[list[str] | None, typer.Option('--record-kind', help="A record kind (facet, item, concept, facet_repair) or one recipe (facet/definition, facet/dossier_scope, item/stem, item/skeleton, concept/definition, ...); repeatable. Default: all vault recipes. Slice 1 adds hypothesis, misconception and attempt (attempt/divergence, for history_mode=hybrid), embedded only when named. Slice 2 T6 adds source_block (source_block/text: every source's current blocks), also only when named, and alone.")]=None, batch_size: Annotated[int, typer.Option('--batch-size', min=1, max=256)]=32, max_candidates: Annotated[int, typer.Option('--max-candidates', min=0)]=100, max_pairs: Annotated[int, typer.Option('--max-pairs', min=0, help='Backfill uses no pairs.')]=0, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=100, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=2, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=100000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='Positive USD input-token estimate for an unknown/changed model price; still subject to cost cap.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 35) — Embed facet definitions, dossier fields, item stems and PF-b skeletons, concept definitions and repairs.
- `embeddings_nomination_report(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root; use a fixtures-local copy.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan the backfill the report needs; no client, migration or data changes.')]=False, stored_only: Annotated[bool, typer.Option('--stored-only', help='Skip the backfill; report from vectors already stored (no model calls).')]=False, batch_size: Annotated[int, typer.Option('--batch-size', min=1, max=256)]=32, max_candidates: Annotated[int, typer.Option('--max-candidates', min=0)]=1000, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=100, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=2, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=1000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=0.25, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='Positive USD input-token estimate for an unknown/changed model price; still subject to cost cap.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 125) — Slice 2 T5 report: embedding nomination recall on doctor-found duplicates.
- `embeddings_compare(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root (routes, ledger, checkpoints); use a fixtures-local copy.')], suite: Annotated[str, typer.Option('--suite', help='Registered suite: b2 (isomorph/near-duplicate), valid_alternative, b1 (Eedi 2024 misconception retrieval), b3 (recurrence vault replay), source_retrieval (Slice 2 T6 report) or b4 (PDF page images vs text chunks).')], output_dir: Annotated[Path, typer.Option('--output', '--output-dir', help='Report and vector-cache directory (outside the vault).')]=Path('fixtures-local/reports/compare'), benchmark: Annotated[Path | None, typer.Option('--benchmark', help='Benchmark directory: manifest.json (source, version, licence) and pairs.jsonl (b2), or the Eedi train.csv and misconception_mapping.csv (b1).')]=None, model: Annotated[list[str] | None, typer.Option('--model', help='Embedding model id (OpenRouter); repeatable. Default: embedding.model.')]=None, dims: Annotated[list[int] | None, typer.Option('--dims', min=1, help='MRL dimension sweep; repeatable. Default: embedding.dimensions (b1: 1024, a width every candidate reaches).')]=None, view: Annotated[list[str] | None, typer.Option('--view', help='b2 views: stem, skeleton, fingerprint, judge; b1 views: raw, hypothesis. source_retrieval systems: substring, keyword, meaning, hybrid, hybrid_rewrite. b4 systems: text, image, keyword, hybrid. Repeatable. Default: all.')]=None, family: Annotated[list[str] | None, typer.Option('--family', help='valid_alternative: activity family id; repeatable.')]=None, target_recall: Annotated[float, typer.Option('--target-recall', min=0.5, max=1.0, help='Recall on positives that sets each blocking cutoff (b3: on confirmed matches, also top_k).')]=0.95, max_cases: Annotated[int | None, typer.Option('--max-cases', min=1, help='b2: pairs; source_retrieval and b4: questions (default 40 and 30).')]=None, max_items: Annotated[int, typer.Option('--max-items', min=1, help='valid_alternative: family items to cover; b4: pages per PDF source in the corpus.')]=20, alternatives: Annotated[int, typer.Option('--alternatives', min=1, max=6, help='valid_alternative: alternative traces per item.')]=2, tier: Annotated[str | None, typer.Option('--tier', help="Run the PF roles at a [pf.scaling] tier (cheap or frontier); B2's judge view then measures that tier's judge on labelled pairs.")]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan calls and tokens; no client, request or write.')]=False, max_candidates: Annotated[int, typer.Option('--max-candidates', min=0)]=100, max_pairs: Annotated[int, typer.Option('--max-pairs', min=0)]=2000, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=500, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=2, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=4000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=2.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help="One owner price for metered LLM roles' input AND output tokens (USD per million): an upper bound when it is the output price. Prefer --input-price-per-million with --output-price-per-million. Codex roles estimate only.")]=None, embedding_price_per_million: Annotated[float | None, typer.Option('--embedding-price-per-million', min=0, help='Embedding input price for models without a built-in estimate.')]=None, input_price_per_million: Annotated[float | None, typer.Option('--input-price-per-million', min=0, help='Owner input-token price for metered LLM roles (USD per million); pass with --output-price-per-million instead of --price-per-million.')]=None, output_price_per_million: Annotated[float | None, typer.Option('--output-price-per-million', min=0, help='Owner output-token price for metered LLM roles (USD per million); pass with --input-price-per-million.')]=None, writer_output_tokens: Annotated[int | None, typer.Option('--writer-output-tokens', min=1, help="b1: the hypothesis writer's output budget per case (default: the output-budget policy's for the diagnosis route, ai.output_tokens 16384 unless overridden; a reasoning model's reasoning tokens count against it). Part of the writer's cache identity.")]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 182) — Run one registered benchmark suite on the shared harness (B2 sets PF's blocking cutoffs).
- `embeddings_adjudicate(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root; use a fixtures-local copy first.')], task: Annotated[str, typer.Option('--task', help='The judgment_ledger task to adjudicate. Slice 2 T1: same_cause.')]='same_cause', backlog: Annotated[bool, typer.Option('--backlog', help='Judge the shortlisted pairs of the existing history (required).')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan pairs, vectors to embed and spend; no client, call or write.')]=False, max_pairs_to_judge: Annotated[int | None, typer.Option('--max-pairs-to-judge', min=1, help='Judge at most this many pairs this run (earliest first).')]=None, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=300, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=30, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=3000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='USD per million tokens for a metered route whose price is unknown (unknown prices fail closed).')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 268) — Embeddings shortlist, the judge decides: adjudicate a task's candidate pairs.
- `local_setup(data_root: Annotated[Path | None, typer.Option('--data-root', help='Default ~/.local/share/learnloop.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Show the paths, pins and disk check; start nothing.')]=False, download: Annotated[bool, typer.Option('--i-understand-this-downloads-33-gb', help='Required to create the env and download the model.')]=False, adopt_model_dir: Annotated[Path | None, typer.Option('--adopt-model-dir', help='Record an existing model directory (verified; nothing moved).')]=None, adopt_env_python: Annotated[Path | None, typer.Option('--adopt-env-python', help="Record an existing environment's interpreter (nothing moved).")]=None, skip_weight_digests: Annotated[bool, typer.Option('--skip-weight-digests', help='Check shard sizes only (the remote code is always hashed).')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 368) — Create the separate environment, download the pinned model and verify it (owner-run).
- `local_index(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], now: Annotated[bool, typer.Option('--now', help='Ignore the batch wait (embedding.local.index_batch_minutes).')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Count the owed windows; launch nothing.')]=False, data_root: Annotated[Path | None, typer.Option('--data-root')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 403) — Index every owed window (grouped and singleton) in ONE capped 9B worker batch.
- `local_profile(vault: Annotated[Path, typer.Option('--vault', help='A vault copy whose teaching text fills the windows.')], extraction_id: Annotated[str, typer.Option('--extraction-id', help='The source extraction to profile on.')], tokens: Annotated[list[int] | None, typer.Option('--tokens', help="Sizes by the model's own count (repeatable).")]=None, data_root: Annotated[Path | None, typer.Option('--data-root')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 427) — P0: the true 8,192-token profile (one metered worker; nothing indexed).
- `local_status(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], data_root: Annotated[Path | None, typer.Option('--data-root')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 451) — Per local space: cache rows, covered sources, epoch and canary status.
- `student_setup(adopt_base: Annotated[list[str] | None, typer.Option('--adopt-base', help='NAME=DIR: record a downloaded base in place (verified; nothing moved). Repeatable.')]=None, data_root: Annotated[Path | None, typer.Option('--data-root')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Show the pinned bases and paths; start nothing.')]=False, skip_weight_digests: Annotated[bool, typer.Option('--skip-weight-digests', help='Check weight sizes only (code and small files are always hashed).')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 475) — Record the two pinned 0.6B bases (pplx-embed-v1-0.6b primary, Qwen3-Embedding-0.6B second).
- `student_plan(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], bank: Annotated[Path | None, typer.Option('--bank', help=_BANK_HELP)]=None, data_root: Annotated[Path | None, typer.Option('--data-root')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 508) — The whole P2 dry run: questions, plan calls, teacher targets, the run schedule, GPU-hours.
- `student_generate(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], bank: Annotated[Path | None, typer.Option('--bank', help=_BANK_HELP)]=None, budget: Annotated[int, typer.Option('--budget', help='Training questions wanted at most (nested 2k/10k/50k).')]=50000, dry_run: Annotated[bool, typer.Option('--dry-run', help='Passages, calls, tokens and cost; send nothing.')]=False, data_root: Annotated[Path | None, typer.Option('--data-root')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 527) — Synthetic questions from permitted passages (route ai.routing.retrieval_query_generator).
- `student_targets(vault: Annotated[Path, typer.Option('--vault', help="Explicit vault root (its index's canaries are checked).")], bank: Annotated[Path | None, typer.Option('--bank', help=_BANK_HELP)]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Count owed questions; launch nothing.')]=False, data_root: Annotated[Path | None, typer.Option('--data-root')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 560) — The teacher's targets: ONE 9B worker batch in query mode (12G scope, GPU lock, P2 meter).
- `student_train(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], bank: Annotated[Path | None, typer.Option('--bank', help=_BANK_HELP)]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Show the next run of the schedule; launch nothing.')]=False, data_root: Annotated[Path | None, typer.Option('--data-root')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 580) — Run the schedule's NEXT training run (screen, recipes, learning curve, seeds); rerun until it says evaluate.
- `student_evaluate(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], bank: Annotated[Path | None, typer.Option('--bank', help='The labelled bank (private JSON/JSONL).')]=None, arm: Annotated[list[str] | None, typer.Option('--arm', help="NAME=FILE: an alternative's per-question outcomes (qwen, voyage, keyword), naming the comparison fingerprint --dry-run prints. Repeatable.")]=None, checkpoint: Annotated[str | None, typer.Option('--checkpoint', help="A completed run's checkpoint SHA-256 (default: the schedule's candidate, else the serving checkpoint).")]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Check the inputs; start nothing.')]=False, data_root: Annotated[Path | None, typer.Option('--data-root')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 600) — A checkpoint on the bank beside the teacher: RECOMMENDED when E[U(student)] >= each measured alternative (spec §9.3).
- `student_adopt(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], checkpoint: Annotated[str | None, typer.Option('--checkpoint', help="The evaluated checkpoint's SHA-256 (default: the latest evaluation's).")]=None, data_root: Annotated[Path | None, typer.Option('--data-root')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 651) — Adopt the evaluated student (the owner's verdict in judgment_ledger; it then serves).
- `student_reject(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], checkpoint: Annotated[str | None, typer.Option('--checkpoint', help="The evaluated checkpoint's SHA-256 (default: the latest evaluation's).")]=None, data_root: Annotated[Path | None, typer.Option('--data-root')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 664) — Decline the evaluated student (recorded; withdrawn if it serves).
- `student_revoke(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], data_root: Annotated[Path | None, typer.Option('--data-root')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 677) — Withdraw the adopted checkpoint (embedding.local.student = false is the switch for every vault).
- `student_status(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], data_root: Annotated[Path | None, typer.Option('--data-root')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 695) — Bases, questions, targets, runs, the P2 meter, the adoption and the teacher replay.
- `fallback_backfill(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root; use a fixtures-local copy.')], extraction_id: Annotated[list[str] | None, typer.Option('--extraction-id', help='Repeatable; default every current extraction.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Windows, requests and the dollar bound; send nothing.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 713) — Embed the Voyage fallback space's missing windows: the WHOLE command is one run, capped at embedding.fallback.max_cost_usd_per_run and admitted at the full price (the aggregate estimate and charge are reported).
- `fusion_refit(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 738) — Refit the fusion posterior from the feedback receipts (no model call).

### Module constants

- `_BANK_HELP` ([src/learnloop/cli/embeddings.py](../../../../../../src/learnloop/cli/embeddings.py), line 471)

## Internal implementation anchors

- `_cancellation() -> Iterator[threading.Event]` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 21)
- `_vault_and_repository(vault: Path, *, write: bool)` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 343)
- `_emit(report: dict, json_output: bool, ok: frozenset[str]) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 361)
- `_owner_choice(vault: Path, checkpoint: str | None, data_root: Path | None, json_output: bool, *, accept: bool) -> None` ([source](../../../../../../src/learnloop/cli/embeddings.py), line 638)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `embeddings_app`
- [[Reference/Modules/learnloop/cli/contamination|learnloop.cli.contamination]] — imports `_cancellation`; statically calls `_cancellation`
- [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]] — imports `_cancellation`; statically calls `_cancellation`
- [[Reference/Modules/learnloop/cli/facets|learnloop.cli.facets]] — imports `_cancellation`; statically calls `_cancellation`
- [[Reference/Modules/learnloop/cli/families|learnloop.cli.families]] — imports `_cancellation`; statically calls `_cancellation`
- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `_cancellation`; statically calls `_cancellation`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `_cancellation`; statically calls `_cancellation`
- [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]] — imports `_cancellation`; statically calls `_cancellation`
- [[Reference/Modules/learnloop/cli/pf|learnloop.cli.pf]] — imports `_cancellation`; statically calls `_cancellation`
- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `_cancellation`; statically calls `_cancellation`
- [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]] — imports `_cancellation`; statically calls `_cancellation`
- [[Reference/Modules/learnloop/cli/recurrence|learnloop.cli.recurrence]] — imports `embeddings_compare`; statically calls `embeddings_compare`
- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `_cancellation`; statically calls `_cancellation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]] — imports `bind_command_repository`, `bind_command_vault`; calls `bind_command_repository`, `bind_command_vault`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `run_backlog`; calls `run_backlog`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `register_suites`; calls `register_suites`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `backfill_with_db_recipes`; calls `backfill_with_db_recipes`
- [[Reference/Modules/learnloop/local_embeddings/fusion|learnloop.local_embeddings.fusion]] — imports `refit_posteriors`; calls `refit_posteriors`
- [[Reference/Modules/learnloop/local_embeddings/setup|learnloop.local_embeddings.setup]] — imports `run_setup`, `setup_plan`; calls `run_setup`, `setup_plan`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `backfill_embeddings`; calls `backfill_embeddings`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `CompareRequest`, `SUITES`, `run_compare`; calls `CompareRequest`, `run_compare`
- [[Reference/Modules/learnloop/ops/graph_nomination_report|learnloop.ops.graph_nomination_report]] — imports `nomination_report`; calls `nomination_report`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `ROLE_TASKS`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `current_extractions`; calls `current_extractions`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `backfill_fallback_run`; calls `backfill_fallback_run`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `coverage_report`, `run_local_index`, `run_profile`; calls `coverage_report`, `run_local_index`, `run_profile`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `context`, `evaluate`, `owner_choice`, `plan`, `revoke`, `run_next`, `run_targets`, `setup_bases`, `status`; calls `context`, `evaluate`, `owner_choice`, `plan`, `revoke`, `run_next`, `run_targets`, `setup_bases`, `status`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `SOURCE_RETRIEVAL_RECIPES`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `generate`; calls `generate`
- [[Reference/Modules/learnloop/source_retrieval/suites|learnloop.source_retrieval.suites]] — imports `register_suites`; calls `register_suites`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `pathlib`, `signal`, `threading`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]], [[Reference/Modules/learnloop/cli/contamination|learnloop.cli.contamination]], [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]], [[Reference/Modules/learnloop/cli/facets|learnloop.cli.facets]], [[Reference/Modules/learnloop/cli/families|learnloop.cli.families]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_facet_identity_ingest.py](../../../../../../tests/test_facet_identity_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_family_memory_projection.py](../../../../../../tests/test_family_memory_projection.py) — imports consumer [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]]
- [tests/test_field_signal_production_paths.py](../../../../../../tests/test_field_signal_production_paths.py) — imports consumer [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]]
- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — imports consumer [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]]
- [tests/test_interaction_signals.py](../../../../../../tests/test_interaction_signals.py) — imports consumer [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/embeddings.py](../../../../../../src/learnloop/cli/embeddings.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
