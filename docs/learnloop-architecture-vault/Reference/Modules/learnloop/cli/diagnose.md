---
title: "learnloop.cli.diagnose"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/diagnose.py"
source_paths:
  - "src/learnloop/cli/diagnose.py"
source_commit: "299e8047568cbb422a63b6f8373056c028f488be"
source_commit_timestamp: "2026-10-15T16:01:49-04:00"
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
  - "learnloop.cli.diagnose module"
  - "src/learnloop/cli/diagnose.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.diagnose`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.diagnose` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop diagnose`: the Slice 1 M1 offline review of blind grading and diagnosis.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/diagnose.py](../../../../../../src/learnloop/cli/diagnose.py) |
| Source lines | 792 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `299e8047568cbb422a63b6f8373056c028f488be` |
| Commit timestamp | `2026-10-15T16:01:49-04:00` |

## Public API

- `diagnose_data_check(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 79) — Graded wrong answers available for the review (M1 needs about 40 across topics).
- `diagnose_run(ctx: typer.Context, vault: Annotated[Path, typer.Option('--vault', help='Vault root; its database is copied, never modified.')], run_dir: Annotated[Path | None, typer.Option('--run-dir', help='Run directory (default: <vault>/.learnloop/diagnose-runs/<id>). An existing one resumes.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Print the plan and cost estimate; no copy, no client, no calls.')]=False, sample_size: Annotated[int, typer.Option('--sample-size', min=0)]=40, seed: Annotated[int, typer.Option('--seed')]=20261012, arms: Annotated[str, typer.Option('--arms', help='Comma-separated subset of a,b,c,d,e.')]='a,b,c,d,e', attempt: Annotated[list[str] | None, typer.Option('--attempt', help='Diagnose these attempts instead of a sample (repeatable).')]=None, since: Annotated[str | None, typer.Option('--since', help='Only attempts at or after this ISO timestamp.')]=None, repeat_subset: Annotated[int, typer.Option('--repeat-subset', min=0, help='Targets repeated under (b) for the noise floor.')]=10, planted_per_shape: Annotated[int, typer.Option('--planted-per-shape', min=0)]=2, planted_manifest: Annotated[Path | None, typer.Option('--planted-manifest', help='Authored planted cases (JSON) instead of generated ones.')]=None, no_planted: Annotated[bool, typer.Option('--no-planted')]=False, no_sweep: Annotated[bool, typer.Option('--no-sweep', help='Skip the (d) context-length sweep on planted cases.')]=False, sweep_budget: Annotated[list[int] | None, typer.Option('--sweep-budget', help='Sweep budgets in tokens (repeatable; default 25000, 50000, 100000).')]=None, no_probes: Annotated[bool, typer.Option('--no-probes', help='Skip the E1 grader probes.')]=False, probe_items: Annotated[int, typer.Option('--probe-items', min=0)]=40, no_joint_repeat: Annotated[bool, typer.Option('--no-joint-repeat', help='Skip re-running the joint grader (E1 noise floor).')]=False, no_judge: Annotated[bool, typer.Option('--no-judge')]=False, full_budget: Annotated[int, typer.Option('--full-history-token-budget', min=1000)]=100000, history_error_limit: Annotated[int, typer.Option('--history-error-limit', min=0)]=6, history_success_limit: Annotated[int, typer.Option('--history-success-limit', min=0)]=4, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=2500, max_candidates: Annotated[int, typer.Option('--max-candidates', min=0)]=500, max_pairs: Annotated[int, typer.Option('--max-pairs', min=0)]=0, max_retries: Annotated[int, typer.Option('--max-retries', min=0, help='Metered routes: every transport retry and JSON repair is one (Codex physical requests are not bounded).')]=50, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0, help='Metered routes only; not enforced on the Codex subscription.')]=5000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0, help='Metered routes only; Codex cost is estimated_only.')]=5.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='Owner USD/million-token bound for metered chat routes with an unknown price.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 131) — Blind-grade a stratified sample, diagnose it under arms (a)-(e), judge, probe.
- `diagnose_report(run: Annotated[Path, typer.Option('--run', help='Run directory from `diagnose run`.')], vault: Annotated[Path | None, typer.Option('--vault', help='Vault root (enables criterion-level grader agreement).')]=None, out: Annotated[Path | None, typer.Option('--out', help='Markdown path (default <run>/report.md); e.g. docs/reviews/slice-1-m1-report.md.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 293) — Write the M1 report (aggregates only) plus report.json and the verdict export.
- `diagnose_review(run: Annotated[Path, typer.Option('--run', help='Run directory from `diagnose run`.')], vault: Annotated[Path, typer.Option('--vault', help='Vault root (arm (a) verdicts are recorded there).')], new_session: Annotated[bool, typer.Option('--new-session', help='Start over instead of resuming.')]=False, seed: Annotated[int, typer.Option('--seed')]=20261012, max_items: Annotated[int, typer.Option('--max-items', min=1, max=20)]=10) -> None` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 322) — The optional owner spot-check: ~10 items, under 15 minutes, every screen skippable.
- `diagnose_import_links(run: Annotated[Path, typer.Option('--run', help='Run directory from `diagnose run`.')], vault: Annotated[Path, typer.Option('--vault', help='Vault root whose judgment_ledger receives the rows.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Count what would be imported; write nothing.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 404) — Append the run's pattern-link verdicts (real attempts only) to judgment_ledger as same_cause rows.
- `diagnose_drain(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], attempt: Annotated[str | None, typer.Option('--attempt', help="Only this attempt's diagnosis (still in attempt order).")]=None, kind: Annotated[list[str] | None, typer.Option('--kind', help='diagnose and/or embed; repeatable. Default: both.')]=None, max_jobs: Annotated[int, typer.Option('--max-jobs', min=1)]=1000, dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan and estimate only: no client, no call, no write.')]=False, max_calls: Annotated[int, typer.Option('--max-calls', min=0, help=_MAX_CALLS_HELP)]=500, max_retries: Annotated[int, typer.Option('--max-retries', min=0, help=_MAX_RETRIES_HELP)]=50, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0, help=_MAX_TOKENS_HELP)]=5000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0, help=_MAX_COST_HELP)]=5.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help=_PRICE_HELP)]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 495) — Run queued post-attempt jobs (diagnoses in attempt order, then embeddings).
- `diagnose_retry(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], attempt: Annotated[str, typer.Option('--attempt', help='Attempt whose diagnosis runs again.')], run_now: Annotated[bool, typer.Option('--run/--queue-only', help='Run it now (default) or only queue it.')]=True, dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan and estimate only: nothing is queued or called.')]=False, max_calls: Annotated[int, typer.Option('--max-calls', min=0, help=_MAX_CALLS_HELP)]=5, max_retries: Annotated[int, typer.Option('--max-retries', min=0, help=_MAX_RETRIES_HELP)]=4, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0, help=_MAX_TOKENS_HELP)]=1000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0, help=_MAX_COST_HELP)]=2.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help=_PRICE_HELP)]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 570) — Retry a failed or skipped diagnosis, or re-diagnose (appends, supersedes).
- `diagnose_status(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], attempt: Annotated[str | None, typer.Option('--attempt', help='One attempt (default: queue counts).')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 649) — An attempt's diagnosis status, or the queue's job counts.
- `diagnose_m2_report(vault: Annotated[Path, typer.Option('--vault', help='Vault root (read only).')], out: Annotated[Path | None, typer.Option('--out', help='Markdown path, e.g. docs/reviews/slice-1-m2-report.md.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 666) — End-of-M2 report: E5 (shadow recurrence), E7 (operations), card signals.
- `diagnose_pfc_report(vault: Annotated[Path, typer.Option('--vault', help='Vault root; use a fixtures-local copy for trials.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan and estimate only: no client, no call, no write.')]=False, max_items: Annotated[int, typer.Option('--max-items', min=0)]=40, max_real: Annotated[int, typer.Option('--max-real', min=0)]=40, seed: Annotated[int, typer.Option('--seed')]=0, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=400, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=4, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=2000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=5.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='USD per million tokens for an unknown metered price.')]=None, no_ledger: Annotated[bool, typer.Option('--no-ledger', help='Do not append verdicts to judgment_ledger.')]=False, out: Annotated[Path | None, typer.Option('--out', help='Markdown path for the report.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 690) — PF-c before/after (E1-style): mvp-2.0 vs mvp-2.1 blind grading prompt.

### Module constants

- `_EXPERIMENT_PARAMETERS` ([src/learnloop/cli/diagnose.py](../../../../../../src/learnloop/cli/diagnose.py), line 95)
- `_DIAGNOSIS_KEYS` ([src/learnloop/cli/diagnose.py](../../../../../../src/learnloop/cli/diagnose.py), line 317)
- `_LINK_KEYS` ([src/learnloop/cli/diagnose.py](../../../../../../src/learnloop/cli/diagnose.py), line 318)
- `_MAX_CALLS_HELP` ([src/learnloop/cli/diagnose.py](../../../../../../src/learnloop/cli/diagnose.py), line 480)
- `_MAX_RETRIES_HELP` ([src/learnloop/cli/diagnose.py](../../../../../../src/learnloop/cli/diagnose.py), line 485)
- `_MAX_TOKENS_HELP` ([src/learnloop/cli/diagnose.py](../../../../../../src/learnloop/cli/diagnose.py), line 486)
- `_MAX_COST_HELP` ([src/learnloop/cli/diagnose.py](../../../../../../src/learnloop/cli/diagnose.py), line 490)
- `_PRICE_HELP` ([src/learnloop/cli/diagnose.py](../../../../../../src/learnloop/cli/diagnose.py), line 491)

### Explicit exports

`__all__` declares:

- `diagnose_app`

## Internal implementation anchors

- `_cancellation() -> Iterator[threading.Event]` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 36)
- `_load(vault: Path)` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 49) — Load the vault; validation issues are reported, not fatal.
- `_echo(payload: object, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 71)
- `_explicit_options(ctx: typer.Context) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 117) — The ReviewOptions fields the command line set on purpose (not defaults).
- `_live_repository(vault: Path)` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 434) — The vault and its migration-applied repository (M2 commands write).
- `_drain_caps(max_calls: int, max_retries: int, max_tokens: int, max_cost_usd: float) -> SpendCaps` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 443)
- `_plan_repository(vault: Path, dry_run: bool)` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 454) — A dry run only reads; a real run opens the vault for writing.
- `_outcome_rows(outcomes) -> list[dict]` ([source](../../../../../../src/learnloop/cli/diagnose.py), line 465)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `diagnose_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `WORKSPACE_PROFILE_TYPES`, `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]] — imports `bind_command_repository`, `bind_command_vault`; calls `bind_command_repository`, `bind_command_vault`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]] — imports `import_pattern_links`; calls `import_pattern_links`
- [[Reference/Modules/learnloop/diagnosis/offline_review/report|learnloop.diagnosis.offline_review.report]] — imports `offline_review_report`, `render_markdown`; calls `offline_review_report`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `DECIDER_ROUTE`, `ReviewClients`, `ReviewOptions`, `data_check`, `decider_route_profile`, `estimate_spend`, `plan_review`, `register_decider_route`, `resolve_review_clients`, `route_profiles`, `run_review`, `unavailable_arms`; calls `ReviewOptions`, `data_check`, `decider_route_profile`, `estimate_spend`, `plan_review`, `register_decider_route`, `resolve_review_clients`, `route_profiles`, `run_review`, `unavailable_arms`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `ReviewSpend`; calls `ReviewSpend`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]] — imports `advance_session`, `export_judgments`, `record_diagnosis_screen`, `record_grade_screen`, `record_links_screen`, `render_screen`, `start_or_resume_session`; calls `advance_session`, `export_judgments`, `record_diagnosis_screen`, `record_grade_screen`, `record_links_screen`, `render_screen`, `start_or_resume_session`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `DIAGNOSE_KIND`, `EMBED_KIND`, `command_spend`, `diagnosis_status`, `drain`, `enqueue_diagnosis`, `plan_diagnosis_jobs`, `plan_embed_jobs`, `plan_unqueued_diagnosis`; calls `command_spend`, `diagnosis_status`, `drain`, `enqueue_diagnosis`, `plan_diagnosis_jobs`, `plan_embed_jobs`, `plan_unqueued_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `needs_diagnosis`; calls `needs_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] — imports `estimate_pfc`, `plan_pfc`, `render_pfc_markdown`, `run_pfc`; calls `estimate_pfc`, `plan_pfc`, `render_pfc_markdown`, `run_pfc`
- [[Reference/Modules/learnloop/diagnosis/split/reports|learnloop.diagnosis.split.reports]] — imports `m2_report`, `render_markdown`; calls `m2_report`, `render_markdown`
- [[Reference/Modules/learnloop/diagnosis/split/settings|learnloop.diagnosis.split.settings]] — imports `DiagnosisSettings`; calls `DiagnosisSettings`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
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

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]].

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

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/diagnose.py](../../../../../../src/learnloop/cli/diagnose.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
