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

The common changes, from the refactor strategy's success measures (`docs/specs/refactor_strategy_v3.md` §6): the files to edit, the test or golden that shows the change, and the note to update. Source paths are under `src/learnloop/`. The refactor moves several of these; each step that does updates its row.

| Change | Edit | The test or golden that shows it | Note to update |
|---|---|---|---|
| A threshold or default (the router's `timeout_seconds`) | its field in `config/schema.py` (`RouterConfig`) | one line of `tests/goldens/effective_defaults.toml`, rewritten by the golden test's write command; a direct assertion only where a test means "this key has this value" | the generated `Reference/Configuration/Fields/Config - <section>.md` (regenerate with `_scripts/db_generate_reference.py`) |
| A seed or prior | as a default, in `config/schema.py` | its golden line, as above | the generated config note, as above |
| A model route | `ai/routing.py` (task and operation names), the route's default in `config/schema.py` | its `ai.routing` golden line; `tests/test_provider_resolution_parity.py` | [[AI Architecture#Task routes]]; the generated `Config - ai.md` |
| A prompt | its own module, with its prompt version bumped | the prompt's own tests; the switch-off parity golden for that prompt only (`tests/fixtures/*_switch_off*.json`) | the feature's note, only if what the learner sees changes |
| Speed work with no version change | the slow module only | the draw-for-draw harness (P-draw in the strategy §2.1: fixed seed and draw count, fake LLM and Decider; `docs/reviews/router-speed2.md`, "Identity"), plus the stage's own equality tests (`tests/test_rofu_speed.py` is the model) | none, unless a module's public names change (its generated module note) |
| A new table | a file in `migrations/`, its role in `db/table_roles.py` (a `DERIVED` table also needs a replayer in `substrate/rebuild_orchestrator.py`), its role in `adaptive_difficulty/protected_tables.py` (`ROLES`, `COLUMNS`) when an AD operation reads it, its store under `db/stores/`; the head fixture `fixtures/migration_head/` upgraded in place and its `README.md` (see `CLAUDE.md`) | `tests/test_table_roles.py`, `tests/test_rebuild_orchestrator.py`, `tests/test_ad_protected_tables.py`; `tests/test_migrations.py::test_repository_carries_a_fixture_at_the_current_migration_head`; `_scripts/db_validate_reference.py` | the generated `Reference/Database/Tables/<table>.md` and [[Database Catalog]] (`_scripts/db_generate_reference.py`); [[State and Persistence]] for a new kind of state |
| A new algorithm tag | `algorithm_versions.py` (`SUCCESSOR_CHAIN`), a root `*_upgrade.py` module, the upgrade dispatch in `cli/app.py`; follow `docs/algorithm-change-playbook.md` | a new `tests/test_<stage>_successor.py` (`tests/test_ro6_successor.py` is the model); the frozen `*_VERSIONS` sets and "latest" pins in the older successor tests move too; the golden line of its kill switch | [[Algorithm Versions and Reproducibility]], [[Version Registry]] |
| What to serve next | `daily_plan/engine.py` (the plan), `daily_plan/objective_chooser.py` (`_decide_objective`: the draw, the coin, the trace) | `tests/test_daily_plan_build.py`, `tests/test_plan_determinism.py`, `tests/test_daily_plan_replay.py`; `tests/test_ro4_objective_serving.py` for the chooser | [[LearnLoop Pipeline Map#Daily plan, router and serving]], [[Scheduling and Selection]] |
| A term of the router's objective | `router_objective/value.py`: the objective is `_Ledger.q`, fed by the ledger's accumulators; `_terms` only reports the breakdown in the trace. A kill switch and a successor if the change moves a decision | `tests/test_ro4_value.py` | [[LearnLoop Pipeline Map#Daily plan, router and serving]] |
| The rule that mixes the LLM and numeric policies | `router_objective/mix.py` | `tests/test_ih5_successor.py` and `tests/test_ro4_objective_serving.py`, which call `effective_weights`, `mu`, `draw` and `recompute` | [[LearnLoop Pipeline Map#Daily plan, router and serving]] |
| An action the router can choose | spread: `daily_plan/lesson_offer.py`, `daily_plan/types.py`, `records.py`, `view.py`, `daily_plan/objective_chooser.py` (its trace), `router/plan_log.py`, `router/requests.py`, `router/why.py`; about 20 files for a lesson-offer-shaped action | `tests/test_ih2_lessons_compete.py` is the model (lessons as an action) | [[LearnLoop Pipeline Map#Daily plan, router and serving]] |
| A sensor the router reads | two destinations with no shared definition: `daily_plan/objective_inputs.py`, `daily_plan/router_card.py`, `router/card.py`, `router_objective/trace.py`, `router_objective/decision_state.py`, `router_objective/tail_data.py` | `tests/test_router_card.py`, `tests/test_ro0_rows9_13_decision_state.py`, `tests/test_ro6_tail_data.py` | [[LearnLoop Pipeline Map#Daily plan, router and serving]] |
| A new signal to model contexts | each context builder separately: `diagnosis/split/context.py`, `tutor/tutor_qa.py`, `daily_plan/router_card.py`, `hints/service.py`; the input hashes that include the context move with it | each builder's tests: `tests/test_diagnosis_context.py`, `tests/test_tutor_qa.py`, `tests/test_router_card.py` | the section of [[LearnLoop Pipeline Map]] that owns the builder |
| A new step in a pipeline | the pipeline's own seam | the pipeline's journey tests | [[Content Pipeline]] for ingest, [[LearnLoop Pipeline Map]] for grading, diagnosis and the plan |

Step A3 replaced the 48 frozen default digests (one per tag, through mvp-0.57) in `config/template.py` with `tests/goldens/effective_defaults.toml`. Before it, a default, a seed or a route also changed each digest and the test files that read them.

## Safe change sequence

1. Locate the concept authority and affected workflow.
2. Open relevant notes in [[Module Catalog]] and [[Database Catalog]].
3. Identify the executable oracle in **Important tests**.
4. Preserve package direction from [[Package Boundaries]].
5. If persisted meaning changes, follow [[Algorithm Versions and Reproducibility#Change protocol]].
6. Run the tests the change can affect (`scripts/affected_tests.py`, chosen from the import graph; it falls back to the whole suite for `tests/conftest.py`, `tests/helpers.py`, `pyproject.toml`, migrations and fixtures), import contracts (`uv run lint-imports --no-cache`), the bug-finding linter (`uv run ruff check`; its rules are `[tool.ruff.lint]` in `pyproject.toml`) and architecture tests. A finding is fixed, or kept with `# noqa: <code>  <reason>`. Each landing runs the whole suite minus `arc_close`; each arc's close runs `-m arc_close` (the pre-registered simulations and the long journeys). The commands are in `CLAUDE.md`.
7. After committing the source change, regenerate the references (`.venv/bin/python docs/learnloop-architecture-vault/_scripts/generate_all.py` runs the module, desktop and db generators; each records its own commit in [[Reference/_generated|Generated Reference Provenance]]), run the validators in [[Documentation Dashboard#Reproducible validation]], and commit every note that changes.

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
