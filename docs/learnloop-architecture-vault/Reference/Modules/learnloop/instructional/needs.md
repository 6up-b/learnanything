---
title: "learnloop.instructional.needs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/needs.py"
source_paths:
  - "src/learnloop/instructional/needs.py"
source_commit: "8e8f41d2ac4eb8b5ec5c23bef529c67de7ce38a7"
source_commit_timestamp: "2026-10-13T16:04:01-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.instructional"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.instructional.needs module"
  - "src/learnloop/instructional/needs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.needs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.needs` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: Source-first fulfilment of intervention needs (spec_source_practice_and_probes_v1 §8.5; S2b).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/needs.py](../../../../../../src/learnloop/instructional/needs.py) |
| Source lines | 332 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8e8f41d2ac4eb8b5ec5c23bef529c67de7ce38a7` |
| Commit timestamp | `2026-10-13T16:04:01-04:00` |

## Public API

- `source_first_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/instructional/needs.py), line 60)
- `need_intent(need: Mapping[str, Any], path: str) -> str` ([source](../../../../../../src/learnloop/instructional/needs.py), line 66)
- `fulfil_need_from_sources(vault: LoadedVault, repository: Repository, need: Mapping[str, Any], *, path: str, clients: Mapping[str, Any] | None=None, rerank_client: Any | None=None, estimator: Any | None=None, pending_decision: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/needs.py), line 91) — Try the sources for one need; ``{"outcome": fulfilled | stale | generate, ...}``.
- `live_repair_class(repository: Repository, *, attempt_id: str, factor_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/instructional/needs.py), line 269) — The repair class the causal path is running for this attempt, or None.
- `pending_causal_decision(vault: LoadedVault, repository: Repository, need: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/instructional/needs.py), line 293) — The need's attempt's open causal factor as a priced decision, or None.

### Module constants

- `PATHS` ([src/learnloop/instructional/needs.py](../../../../../../src/learnloop/instructional/needs.py), line 57)

### Explicit exports

`__all__` declares:

- `PATHS`
- `fulfil_need_from_sources`
- `live_repair_class`
- `need_intent`
- `pending_causal_decision`
- `source_first_active`

## Internal implementation anchors

- `_chooser_gate(vault: LoadedVault, repository: Repository, need: Mapping[str, Any])` ([source](../../../../../../src/learnloop/instructional/needs.py), line 73) — The follow-up chooser's own rule, applied to an authored draft.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `fulfil_need_from_sources`, `pending_causal_decision`, `source_first_active`; statically calls `fulfil_need_from_sources`, `pending_causal_decision`, `source_first_active`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `module`; statically calls `pending_causal_decision`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `fulfil_need_from_sources`, `source_first_active`; statically calls `fulfil_need_from_sources`, `source_first_active`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `SOURCE_FIRST_NEEDS_VERSIONS`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `import_source_exercise`; calls `import_source_exercise`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `import_row`, `update_import`; calls `import_row`, `update_import`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `misconception_discrimination`; calls `misconception_discrimination`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `diagnosis_receipt`, `selected_repair`; calls `diagnosis_receipt`, `selected_repair`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `build_hypothesis_set`; calls `build_hypothesis_set`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `persisted_screen`; calls `persisted_screen`
- [[Reference/Modules/learnloop/instructional/validation|learnloop.instructional.validation]] — imports `draft_validator`; calls `draft_validator`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `rank_listener`; calls `rank_listener`
- [[Reference/Modules/learnloop/instructional/wiring|learnloop.instructional.wiring]] — imports `disabled_reason`, `find_practice_injections`; calls `disabled_reason`, `find_practice_injections`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `PracticeConstraints`, `find_practice`; calls `PracticeConstraints`, `find_practice`
- [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] — imports `module`; calls `record_rank_feasible_forecast`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `teaching_scope`; calls `teaching_scope`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `service_spend`; calls `service_spend`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_priced_causal_decision_carries_the_live_repair_class`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f7_an_open_causal_factor_with_competing_repairs_is_a_decision_question`
- [tests/test_source_first_needs.py](../../../../../../tests/test_source_first_needs.py) — direct import
  - `test_a_need_resumes_its_search_before_it_goes_to_generation`
  - `test_below_the_tag_and_with_the_switch_off_nothing_runs`
  - `test_discriminate_drafts_must_pass_the_choosers_own_gate`
  - `test_the_primed_retry_adapter_tries_sources_before_generating`

## Modification guidance

- Make changes here when the responsibility remains needs within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/needs.py](../../../../../../src/learnloop/instructional/needs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
