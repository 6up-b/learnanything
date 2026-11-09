---
title: "learnloop.cli.sources"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/sources.py"
source_paths:
  - "src/learnloop/cli/sources.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.cli.sources module"
  - "src/learnloop/cli/sources.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.sources`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.sources` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop sources`: Slice 2 T6 source retrieval from the command line.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/sources.py](../../../../../../src/learnloop/cli/sources.py) |
| Source lines | 414 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `sources_search(query: Annotated[str, typer.Argument(help='What to find in the source library.')], vault: Annotated[Path, typer.Option('--vault', help='Vault root; use a fixtures-local copy for experiments.')], deep: Annotated[bool, typer.Option('--deep', help='Also search by meaning (stored source-block vectors; one cached, capped query embedding) and rewrite a conceptual question (route source_query_rewrite). Paid: dry-run first.')]=False, limit: Annotated[int, typer.Option('--limit', min=1, max=200)]=20, dry_run: Annotated[bool, typer.Option('--dry-run', help='Print the planned paid calls and their estimated cost; call and write nothing.')]=False, max_calls: Annotated[int, typer.Option('--max-calls', min=0, help="Cap on the deep search's paid requests (rewrite, its retry, query embedding).")]=3, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0, help="Cap on the deep search's estimated tokens (a rewrite reserves its full output budget, a truncation retry twice that).")]=120000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0.0, help="Cap on the deep search's estimated metered cost (USD).")]=0.25, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 56) — Search every reader-enabled source, as the reader's library search does.
- `sources_suggest_lo(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], extraction_id: Annotated[str, typer.Option('--extraction', help='Extraction id of the span.')], span_id: Annotated[str, typer.Option('--span', help='Span id.')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 109) — Provenance-linked LOs for a span, else labelled nearest-LO suggestions (no calls).
- `sources_report(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], since: Annotated[str | None, typer.Option('--since', help='Only questions asked at or after this ISO time.')]=None, spend_days: Annotated[int, typer.Option('--spend-days', min=0, max=366, help='Days of actual spend to show for the source service and for automatic book preparation (0: none).')]=7, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 133) — Tutor-span retrieval timing per step (p50/p90, over the soft deadline) and truncated answers, the source service's actual spend per day (receipt cost, reserved vs settled, largest operations), and automatic book preparation's per day under its daily guard (ingest.cost_pause.dail…
- `exercises_harvest(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, learning_object: Annotated[list[str] | None, typer.Option('--lo', help='Only facets of these LOs.')]=None, facet: Annotated[list[str] | None, typer.Option('--facet', help='Only these facets.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan only: no client, nothing written.')]=False, max_cost_usd: Annotated[float | None, typer.Option('--max-cost-usd', min=0.0, help='Stop once metered spend reaches this.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 253) — Import judged textbook exercises for thin facets, each key checked before writing.
- `exercises_verify(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, item: Annotated[list[str] | None, typer.Option('--item', help='Only these practice items.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan only: no client, nothing written.')]=False, max_cost_usd: Annotated[float | None, typer.Option('--max-cost-usd', min=0.0, help='Stop once metered spend reaches this.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 277) — Check imported exercises' answer keys whose current content is not verified.
- `sources_outcomes(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 299) — What retrieval showed or served, and what followed (associations, not causes; no model call).
- `sources_tools(json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 329) — Every source tool's declaration (name, description, JSON schema, model call).
- `sources_tool(name: Annotated[str, typer.Argument(help='find_practice, find_sources, compare_sources, find_facets or practice_availability.')], args: Annotated[str, typer.Option('--args', help="The tool's arguments as a JSON object.")]='{}', vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Validate and show the policy; run nothing.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 346) — Run one tool as an external agent (caller kind ``agent``, policy ``reading``).
- `sources_build_preview(source_id: Annotated[str, typer.Argument(help="The book's source id (src_...).")], vault: Annotated[Path, typer.Option('--vault', help='Vault root; use a fixtures-local copy for experiments.')], whole_book: Annotated[bool, typer.Option('--whole-book', help="Preview 'Build questions for the whole book'.")]=False, approved: Annotated[bool, typer.Option('--approved', help="Preview as if the learner pressed 'Build them'.")]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 390) — Dry run of an automatic question build for one book (UX Phase 1): what it would cover, the route, tokens, money and whether it would ask first or stop.

## Internal implementation anchors

- `_open(vault: Path, *, migrate: bool=True)` ([source](../../../../../../src/learnloop/cli/sources.py), line 37)
- `_echo_auto_build_spend(spend: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 190)
- `_echo_spend(spend: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 216)
- `_emit(report: dict[str, Any], json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 242)
- `_exit_for(report: dict[str, Any], ok: set[str]) -> None` ([source](../../../../../../src/learnloop/cli/sources.py), line 247)
- `_agent_injections(vault: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/sources.py), line 336)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `sources_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`; calls `SpendBudget`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `_repository`, `_root`; calls `_repository`, `_root`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `auto_build_spend_report`, `preview_auto_build`; calls `auto_build_spend_report`, `preview_auto_build`
- [[Reference/Modules/learnloop/daily_plan/estimates|learnloop.daily_plan.estimates]] — imports `Estimator`, `load_duration_evidence`; calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `harvest`, `verify`; calls `harvest`, `verify`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `outcomes_report`; calls `outcomes_report`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `caller_for`; calls `caller_for`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `ToolArgumentsInvalid`, `drop_unknown_ids`, `run_tool`, `tool_schemas`, `validate_arguments`; calls `drop_unknown_ids`, `run_tool`, `tool_schemas`, `validate_arguments`
- [[Reference/Modules/learnloop/instructional/wiring|learnloop.instructional.wiring]] — imports `find_practice_injections`; calls `find_practice_injections`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `planning_repository`; calls `planning_repository`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `IntentUnavailable`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `deep_search_caps`, `plan_library_search`, `search_library`; calls `deep_search_caps`, `plan_library_search`, `search_library`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `PolicyRefused`, `derive_policy`; calls `derive_policy`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `spend_report`; calls `spend_report`
- [[Reference/Modules/learnloop/source_retrieval/suggest|learnloop.source_retrieval.suggest]] — imports `suggest_learning_objects`; calls `suggest_learning_objects`
- [[Reference/Modules/learnloop/source_retrieval/timing|learnloop.source_retrieval.timing]] — imports `tutor_timing_report`; calls `tutor_timing_report`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `pathlib`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

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

1. Modify [src/learnloop/cli/sources.py](../../../../../../src/learnloop/cli/sources.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
