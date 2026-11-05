---
title: "learnloop.cli.ad"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/ad.py"
source_paths:
  - "src/learnloop/cli/ad.py"
source_commit: "8d1272482fc14d002b0c0671f74e5f37d2427af9"
source_commit_timestamp: "2026-11-04T21:28:27-05:00"
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
  - "learnloop.cli.ad module"
  - "src/learnloop/cli/ad.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.ad`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.ad` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop ad`: adaptive difficulty AD1's owner-run commands (spec §14 AD1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/ad.py](../../../../../../src/learnloop/cli/ad.py) |
| Source lines | 251 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8d1272482fc14d002b0c0671f74e5f37d2427af9` |
| Commit timestamp | `2026-11-04T21:28:27-05:00` |

## Public API

- `data_check_command(vault: Annotated[Path, typer.Option('--vault', help='Vault root (read-only; use a backup copy).')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/ad.py), line 40) — The spec's §3.3 tables, first-surface attempts per cell, coverage of latency, ratings and hint timing, exam units with and without a facet mapping, and historical attempts by revision status.
- `backfill_command(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], audit: Annotated[bool, typer.Option('--audit', help='Audit every active and every held item revision.')]=False, llm_v1: Annotated[bool, typer.Option('--llm-v1', help='Forecast the never-attempted items (llm_v1:item).')]=False, reading: Annotated[bool, typer.Option('--reading', help='Sweep the reading history (no model call).')]=False, limit: Annotated[int | None, typer.Option('--limit', min=1, help='At most this many audits / forecasts.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Print the plan and the estimate; call and write nothing.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/ad.py), line 63) — AD1's one-time backfills (--audit, --llm-v1, --reading).
- `forecast_audit_command(vault: Annotated[Path, typer.Option('--vault', help='Vault root (use a backup copy).')], mode: Annotated[str, typer.Option('--mode', help='permuted (paid: shuffled history) or prior-sweep (free).')], limit: Annotated[int | None, typer.Option('--limit', min=1, help='At most this many permuted calls.')]=None, run: Annotated[bool, typer.Option('--run', help='Send (paid). Without it: a dry run that calls and writes nothing.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/ad.py), line 94) — Router objective RO2's audit of llm_history_v1 on frozen inputs (spec §6.4): a permuted-history run and a prior-strength sweep.
- `report_command(vault: Annotated[Path, typer.Option('--vault', help='Vault root (read-only; use a backup copy).')], json_output: Annotated[bool, typer.Option('--json')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Print what the report would read; compute nothing.')]=False, sensitivity: Annotated[bool, typer.Option('--sensitivity/--no-sensitivity', help='Rerun with each feature-effect prior shifted ±1 sd.')]=True) -> None` ([source](../../../../../../src/learnloop/cli/ad.py), line 130) — The AD2/AD3 report (spec §10.4): scores with the first-attempt split first, field's rule as a monitor, confidence sequences, auto-flags, the honest lines, identifiability, time to usable, the dose arm and the dose-and-burden analysis.
- `eval_command(vault: Annotated[Path, typer.Option('--vault', help='Vault root (read-only; use a backup copy).')], arms: Annotated[str | None, typer.Option('--arms', help='Comma-separated arms (default: every §10.4 arm).')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/ad.py), line 166) — The §10.4 harness arms, scored prequentially (first-attempt split first).
- `relatedness_command(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], subject: Annotated[str | None, typer.Option('--subject', help='One subject (default: every subject).')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Print the plan and the estimate; call and write nothing.')]=False, adopt: Annotated[bool, typer.Option('--adopt', help='Adopt the proposals in force as the next coupling version.')]=False, shadow: Annotated[bool, typer.Option('--shadow', help='Print what adopting a later version would change; write nothing.')]=False, confirm_reinterpretation: Annotated[bool, typer.Option('--confirm-reinterpretation', help='Adopt a later coupling version after reading its --shadow report.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/ad.py), line 193) — The relatedness proposal's backfill per subject (spec §5.10): one LLM call per subject on ai.routing.llm_probability_llm, reading only the subject's LO and facet text, the concept graph and item stems (never learner data or held-out text), inside adaptive_difficulty.daily_spend_…

## Internal implementation anchors

- `_vault_root(vault: Path) -> None` ([source](../../../../../../src/learnloop/cli/ad.py), line 34)
- `_read_only(vault: Path) -> tuple` ([source](../../../../../../src/learnloop/cli/ad.py), line 119)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `ad_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]] — imports `module`; calls `prequential`
- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `backfill`, `llm_plan`; calls `backfill`, `llm_plan`
- [[Reference/Modules/learnloop/adaptive_difficulty/data_check|learnloop.adaptive_difficulty.data_check]] — imports `data_check`; calls `data_check`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]] — imports `plan_audit`, `run_audit`; calls `plan_audit`, `run_audit`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `module`; calls `adopt`, `coupling_on`, `focus`, `prompt`, `propose_subject`, `shadow_report`, `subject_inputs`, `subjects`, `touched_units`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; calls `load_events`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `SPLITS`, `arm_scores`, `build`, `render_markdown`; calls `arm_scores`, `build`, `render_markdown`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `module`; calls `relatedness_runs`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `planning_repository`; calls `planning_repository`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `pathlib`, `sqlite3`, `typing`
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

### Regeneration and review checklist

1. Modify [src/learnloop/cli/ad.py](../../../../../../src/learnloop/cli/ad.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
