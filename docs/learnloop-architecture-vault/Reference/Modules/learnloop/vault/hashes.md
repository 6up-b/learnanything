---
title: "learnloop.vault.hashes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/hashes.py"
source_paths:
  - "src/learnloop/vault/hashes.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.hashes module"
  - "src/learnloop/vault/hashes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.hashes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps hashes behavior inside its owning package, [[Reference/Modules/learnloop/vault/_package|learnloop.vault]]. Its public surface centers on `content_hash`, `learning_object_hash`, `practice_item_hash`, `reference_content_hash`, `skeleton_content_hash`, `activity_family_hash`.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/hashes.py](../../../../../../src/learnloop/vault/hashes.py) |
| Source lines | 123 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `content_hash(fields: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/vault/hashes.py), line 23)
- `learning_object_hash(learning_object: LearningObject) -> str` ([source](../../../../../../src/learnloop/vault/hashes.py), line 28)
- `practice_item_hash(practice_item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/vault/hashes.py), line 46)
- `reference_content_hash(practice_item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/vault/hashes.py), line 68) — What an answer-key check verified (canonical sources S1, §7.3a): the prompt, the expected answer, the grading rubric and, when set, the required method (method-explicit-3 review F1).
- `skeleton_content_hash(prompt: str, expected_answer: str | dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/vault/hashes.py), line 77) — The item text a PF solution skeleton describes (``item_skeletons.content_hash``).
- `activity_family_hash(family: ActivityFamily) -> str` ([source](../../../../../../src/learnloop/vault/hashes.py), line 117) — Authored family content has its own revision hash, never the item hash.

## Internal implementation anchors

- `_plain(value: Any) -> Any` ([source](../../../../../../src/learnloop/vault/hashes.py), line 13)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `reference_content_hash`; statically calls `reference_content_hash`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `content_hash`; statically calls `content_hash`
- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]] — imports `practice_item_hash`, `skeleton_content_hash`; statically calls `practice_item_hash`, `skeleton_content_hash`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/hints/report|learnloop.hints.report]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/hints/telemetry|learnloop.hints.telemetry]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `reference_content_hash`; statically calls `reference_content_hash`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]] — imports `activity_family_hash`; statically calls `activity_family_hash`
- [[Reference/Modules/learnloop/substrate/item_fingerprints|learnloop.substrate.item_fingerprints]] — imports `practice_item_hash`, `skeleton_content_hash`; statically calls `practice_item_hash`, `skeleton_content_hash`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `skeleton_content_hash`; statically calls `skeleton_content_hash`
- [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `practice_item_hash`; statically calls `practice_item_hash`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `practice_item_hash`; statically calls `practice_item_hash`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `reference_content_hash`; calls `reference_content_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `ActivityFamily`, `Concept`, `ConceptEdge`, `LearningObject`, `PracticeItem`, `Rubric`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]], [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] and 17 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/approach_map_fakes.py](../../../../../../tests/approach_map_fakes.py) — direct import
- [tests/test_activity_families.py](../../../../../../tests/test_activity_families.py) — direct import
  - `test_absent_fields_are_byte_identical_to_pre_family_model`
- [tests/test_approach_maps.py](../../../../../../tests/test_approach_maps.py) — direct import
  - `test_a_build_stores_one_validated_version_with_its_receipt_and_verdict`
- [tests/test_attempt_content_state_race.py](../../../../../../tests/test_attempt_content_state_race.py) — direct import
  - `test_an_attempt_graded_before_an_editing_sync_keeps_the_edited_hash`
  - `test_an_attempt_on_an_item_with_no_row_inserts_the_whole_row`
- [tests/test_canonical_exercise_serialization.py](../../../../../../tests/test_canonical_exercise_serialization.py) — direct import
  - `test_round_trip_and_hash_independence`
- [tests/test_duration_estimates.py](../../../../../../tests/test_duration_estimates.py) — direct import
  - `test_expected_minutes_is_optional_omitted_when_null_and_outside_the_hash`
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_a_reveal_writes_one_authored_hint_row`
- [tests/test_irt_difficulty.py](../../../../../../tests/test_irt_difficulty.py) — direct import
  - `test_difficulty_source_is_excluded_from_content_hash`
- [tests/test_item_fingerprints.py](../../../../../../tests/test_item_fingerprints.py) — direct import
  - `test_skeletons_from_one_model_at_two_prompt_versions_rebuild_without_a_key_collision`
- [tests/test_pf_generation.py](../../../../../../tests/test_pf_generation.py) — direct import
  - `test_published_items_keep_scheduling_hashes_and_unfamilied_items_unchanged`
- [tests/test_pr4_superseded_claims_landing.py](../../../../../../tests/test_pr4_superseded_claims_landing.py) — direct import
  - `test_landing_i_a_too_easy_retirement_during_a_session`
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
- [tests/test_required_method_items.py](../../../../../../tests/test_required_method_items.py) — direct import
  - `test_an_item_without_a_required_method_serializes_and_hashes_as_before`
- [tests/test_required_method_rereview.py](../../../../../../tests/test_required_method_rereview.py) — direct import
- [tests/test_required_method_round3.py](../../../../../../tests/test_required_method_round3.py) — direct import
- [tests/test_source_exercise_import.py](../../../../../../tests/test_source_exercise_import.py) — direct import
  - `test_a_retried_written_import_restores_a_missing_check`
  - `test_items_without_a_canonical_exercise_serialize_byte_identically`
  - `test_recovery_never_binds_a_verdict_to_content_edited_before_the_commit`
  - `test_the_books_solution_writes_and_verifies_the_key`
- [tests/test_state_sync_scheduling_race.py](../../../../../../tests/test_state_sync_scheduling_race.py) — direct import
  - `test_an_attempt_from_a_second_process_survives_a_concurrent_content_sync`
  - `test_content_change_sync_keeps_an_attempt_committed_after_its_snapshot`
  - `test_creating_sync_keeps_a_row_an_attempt_inserted_after_its_snapshot`
  - `test_incremental_watch_refresh_keeps_an_attempt_committed_after_its_read`
- [tests/test_success_head_cli.py](../../../../../../tests/test_success_head_cli.py) — direct import
  - `test_loader_reads_phase_5a_skeletons_keyed_by_item_id`

## Modification guidance

- Make changes here when the responsibility remains hashes within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/hashes.py](../../../../../../src/learnloop/vault/hashes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
