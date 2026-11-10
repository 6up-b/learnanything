---
title: Developer Map
aliases:
  - Developer MOC
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - docs/specs/ARCHITECTURE.md
  - tests/test_architecture.py
  - pyproject.toml
tags:
  - learnloop/development
  - moc
---

# Developer Map

## Start with the behavior, not the filename

| Change | Primary authority | Then inspect |
|---|---|---|
| scoring/evidence interpretation | [[Learning System]] and `attempts/` | [[Algorithm Versions and Reproducibility]], [[Attempt Processing]] |
| what to serve next | the plan engine (`daily_plan/engine.py`) and the router's choice (`daily_plan/objective_chooser.py`, `router_objective/`); `scheduling/` only builds the FSRS due queue (`scheduling/scheduler.py`, `build_due_queue`) | [[LearnLoop Pipeline Map]], the table below |
| provider or route | [[AI Architecture]] | `ai/routing.py`, provider profile config, parity tests |
| a structured AI operation | owning domain `ai_contracts.py` | [[ADR-002 Feature-owned structured AI contracts]] |
| new persistent state | [[State and Persistence]] | table role, write owner, migration, rebuild tests |
| source ingestion job | [[Content Pipeline]] | `content/pipeline/runner.py`, `jobs.py`, queue store |
| CLI command | `cli/` public domain API | help snapshot and adapter-independence tests |
| desktop screen or RPC | [[Desktop Architecture]] and [[Desktop Module Catalog]] | DTO, Rust command registration, sidecar method, serializer/RPC contract tests |
| compatibility behavior | `substrate/compat/` | fixture-backed explicit decision |

## Where to change what

The sample changes from the refactor strategy's success measures (`docs/specs/refactor_strategy_v3.md` §6), with where each lives in the code today and the plumbing it also costs today. Paths are under `src/learnloop/`. The refactor moves several of these; each step that does updates its row.

| Change | Where it lives today | Plumbing it also costs today |
|---|---|---|
| A threshold or default (the router's `timeout_seconds`) | its field in `config/schema.py` (`RouterConfig`) | 48 frozen digests (one per tag, mvp-0.57) in `config/template.py` (`DEFAULTS_SNAPSHOT_BY_ALGORITHM`), the test files that read them, one generated config note |
| A seed or prior | as a default, in `config/schema.py` | the same digests |
| A model route | `ai/routing.py` (task and operation names), the route's default in `config/schema.py` | the digests |
| A prompt | its own module, with its prompt version bumped | a golden for each switch-off parity test |
| A new table | a file in `migrations/`, its role in `db/table_roles.py` (a `DERIVED` table also needs a replayer in `substrate/rebuild_orchestrator.py`), its role in `adaptive_difficulty/protected_tables.py` (`ROLES`, `COLUMNS`) when an AD operation reads it, its store under `db/stores/` | the head fixture `fixtures/migration_head/` upgraded in place and its `README.md` (see `CLAUDE.md`), the generated database notes |
| A new algorithm tag | `algorithm_versions.py` (`SUCCESSOR_CHAIN`), a root `*_upgrade.py` module, the upgrade dispatch in `cli/app.py`; follow `docs/algorithm-change-playbook.md` | frozen `*_VERSIONS` sets and "latest" pins in the successor tests, the digests |
| What to serve next | `daily_plan/engine.py` (the plan), `daily_plan/objective_chooser.py` (`_decide_objective`: the draw, the coin, the trace) | |
| A term of the router's objective | `router_objective/value.py`: the objective is `_Ledger.q`, fed by the ledger's accumulators; `_terms` only reports the breakdown in the trace | a kill switch and a successor if the change moves a decision |
| The rule that mixes the LLM and numeric policies | `router_objective/mix.py` | |
| An action the router can choose | spread: `daily_plan/lesson_offer.py`, `daily_plan/types.py`, `records.py`, `view.py`, `daily_plan/objective_chooser.py` (its trace), `router/plan_log.py`, `requests.py`, `why.py` | about 20 files for a lesson-offer-shaped action |
| A sensor the router reads | `daily_plan/objective_inputs.py`, `daily_plan/router_card.py`, `router/card.py`, `router_objective/trace.py`, `decision_state.py`, `tail_data.py` | two destinations with no shared definition |
| A new signal to model contexts | each context builder separately: `diagnosis/split/context.py`, `tutor/tutor_qa.py`, `daily_plan/router_card.py`, `hints/service.py` | input hashes that include the context |
| A new step in a pipeline | the pipeline's own seam: [[Content Pipeline]] for ingest, [[LearnLoop Pipeline Map]] for grading, diagnosis and the plan | |

## Safe change sequence

1. Locate the concept authority and affected workflow.
2. Open relevant notes in [[Module Catalog]] and [[Database Catalog]].
3. Identify the executable oracle in **Important tests**.
4. Preserve package direction from [[Package Boundaries]].
5. If persisted meaning changes, follow [[Algorithm Versions and Reproducibility#Change protocol]].
6. Run focused tests, import contracts, architecture tests, and the full suite.

> [!failure] Common wrong turns
> - Adding provider-named methods instead of a feature-owned structured operation.
> - Writing raw SQL from a second owner.
> - Clearing a table because it “looks derived” without proving a lossless replay source.
> - Importing a private underscore name across a package boundary.
> - Making one adapter import another.
> - Reusing an algorithm version after changing persisted meaning.

## Oracles

- [[Testing and Invariants]]
- `tests/test_architecture.py`
- `tests/test_structured_transport_parity.py`
- `tests/test_provider_resolution_parity.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_attempt_write_order.py`
- `tests/test_cli_help_snapshot.py`
- `tests/test_sidecar_serializer_snapshot.py`
