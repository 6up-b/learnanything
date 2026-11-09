---
title: "learnloop.cli.grading"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/grading.py"
source_paths:
  - "src/learnloop/cli/grading.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.grading module"
  - "src/learnloop/cli/grading.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.grading`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps grading behavior inside its owning package, [[Reference/Modules/learnloop/cli/_package|learnloop.cli]]. Its public surface centers on `grading_reviews`, `grading_adjudicate`, `grading_receipt`, `grading_hardcases`, `grading_method_phrasing`, `grading_required_method`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/grading.py](../../../../../../src/learnloop/cli/grading.py) |
| Source lines | 321 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `grading_reviews(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/grading.py), line 10) — List pending grade reviews, influence-ordered (§5).
- `grading_adjudicate(interpretation_id: Annotated[str, typer.Argument(help='Grade interpretation id (from `grading reviews`).')], resolved_class: Annotated[str | None, typer.Option('--resolved-class')]=None, source: Annotated[str, typer.Option('--source', help='human_owner|independent_expert|learner_clarification|deterministic_key')]='human_owner', rationale: Annotated[str | None, typer.Option('--rationale')]=None, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/grading.py), line 33) — Adjudicate one grade append-only (§4.4/§5): appends a new interpretation head, repoints the observation, emits measurement events, and rebuilds projections.
- `grading_receipt(attempt_id: Annotated[str, typer.Argument(help='Attempt id to trace.')], vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=True) -> None` ([source](../../../../../../src/learnloop/cli/grading.py), line 88) — The §5 measurement receipt: response -> raw grade -> interpretation -> projection, plus the calibration lineage.
- `grading_hardcases(vault: Annotated[Path, typer.Option('--vault', help='A backup-API copy of a vault (receipts and checkpoints are written there).')], route: Annotated[list[str], typer.Option('--route', help="A configured [ai.providers.*] profile to score as the grader; repeatable. Each is also scored along the production path (PF-c's gate and the own-route rule).")], cases: Annotated[Path | None, typer.Option('--cases', help='Gold-set JSON (default: fixtures/grading_hardcases/cases_v3.json).')]=None, ablations: Annotated[bool, typer.Option('--ablations', help='Grade under all four R2 arms: the reference shown or solve-first, crossed with the final-answer check shown to the grader or withheld (the gate still applies it). Default: the production arm only.')]=False, repeats: Annotated[int, typer.Option('--repeats', min=1, help='Fresh, separately identified repetitions of every call; 2 or more report a repeat-run noise floor.')]=1, output_dir: Annotated[Path, typer.Option('--output-dir', '--output', help='Report destination.')]=Path('fixtures-local/reports/grading-hardcases'), dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan calls, tokens and cost; build no client and send nothing.')]=False, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0, help='Cap on metered spend (reservations: each request reserves its full output budget).')]=3.0, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=200, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0, help="Cap on metered tokens (input plus reserved output; each request reserves its route's policy output budget, 16,384 by default).")]=4000000, max_retries: Annotated[int, typer.Option('--max-retries', min=0, help='Counted retries of a failed transport request.')]=4, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='One USD rate for input and output tokens (an upper bound). Metered routes need a price.')]=None, input_price_per_million: Annotated[float | None, typer.Option('--input-price-per-million', min=0)]=None, output_price_per_million: Annotated[float | None, typer.Option('--output-price-per-million', min=0)]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/grading.py), line 135) — Wrong-rejection and wrong-acceptance rates per judge route on hard cases.
- `grading_method_phrasing(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, judge: Annotated[str, typer.Option('--judge', help='auto (the Decider, else the LLM judge, else the heuristic: the first that is ready), decider, llm or heuristic.')]='auto', item: Annotated[list[str] | None, typer.Option('--item', help='Read only this practice item; repeatable. Default: every active item with its own rubric.')]=None, propose: Annotated[bool, typer.Option('--propose', help='Persist the repairs as one pending proposal (never auto-applied; review with `learnloop proposals`).')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help="Plan every request the run may send (the Decider's classification and the writer's rewrites, or the LLM judge's) with its estimated cost, and show the heuristic's flags; build no client and send nothing. Exits 1 when a metered route has no price.")]=False, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0, help='Cap on metered spend.')]=0.5, max_calls: Annotated[int | None, typer.Option('--max-calls', min=0, help='Cap on requests (default: two per item).')]=None, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help="USD per million tokens for a metered LLM judge or writer (an upper bound; without it their requests are refused); the Decider's listed price is known.")]=None, output_dir: Annotated[Path | None, typer.Option('--output-dir', help='Also write the JSON report here.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/grading.py), line 210) — Rubric criteria phrased by method, and their repair proposals.
- `grading_required_method(item_id: Annotated[str, typer.Argument(help='The practice item.')], method: Annotated[str | None, typer.Option('--method', help='The method its statement requires (its name, as the grader is shown it).')]=None, criterion: Annotated[list[str] | None, typer.Option('--criterion', help="A criterion that grades use of the method; repeatable (default: the current method's, when renaming it).")]=None, clear: Annotated[bool, typer.Option('--clear', help='The statement requires no method: clear the field.')]=False, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/grading.py), line 286) — Propose the owner's change to an item's required method (never auto-applied).

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `append_adjudication`; calls `append_adjudication`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `_cancellation`; calls `_cancellation`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `candidate_items`, `default_caps`, `run_method_phrasing`, `write_report`; calls `candidate_items`, `default_caps`, `run_method_phrasing`, `write_report`
- [[Reference/Modules/learnloop/content/proposals/required_method_override|learnloop.content.proposals.required_method_override]] — imports `propose_required_method_override`; calls `propose_required_method_override`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `ALL_ARMS`, `PRODUCTION_ARM`, `run_hardcases`, `write_report`; calls `run_hardcases`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `record_reinterpretation_if_changed`; calls `record_reinterpretation_if_changed`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
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

1. Modify [src/learnloop/cli/grading.py](../../../../../../src/learnloop/cli/grading.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
