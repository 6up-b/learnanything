---
title: "learnloop.instructional.practice"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/practice.py"
source_paths:
  - "src/learnloop/instructional/practice.py"
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
  - "learnloop.instructional.practice module"
  - "src/learnloop/instructional/practice.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.practice`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.practice` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: ``find_practice`` for real callers (spec_source_practice_and_probes_v1 §6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/practice.py](../../../../../../src/learnloop/instructional/practice.py) |
| Source lines | 485 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `service_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/instructional/practice.py), line 54)
- `constrain_for_caller(constraints: PracticeConstraints, caller: CallerContext | None) -> PracticeConstraints` ([source](../../../../../../src/learnloop/instructional/practice.py), line 58) — What the caller's context forbids, applied on top of the request.
- `propose_practice(vault: LoadedVault, repository: Repository, query: str, constraints: PracticeConstraints | Mapping[str, Any] | None, *, caller: CallerContext | None, origin: str='rpc', embedder: Any | None=None, rerank_client: Any | None=None, clock: Clock | None=None, **injected: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/practice.py), line 78) — ``find_practice`` under a server-derived caller context.
- `continuation_cursor(repository: Repository, proposal_id: str, *, caller: CallerContext | None, query: str, intent: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/practice.py), line 116) — The stored cursor that resumes an earlier search (Codex re-review F5).
- `record_proposal_impressions(vault: LoadedVault, repository: Repository, *, proposal_id: str, keys: Sequence[Mapping[str, Any]], surface: str, session_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/practice.py), line 162) — Record the proposals a surface rendered.
- `refuse_protected_pick(repository: Repository, practice_item_id: str, *, vault: LoadedVault | None=None) -> None` ([source](../../../../../../src/learnloop/instructional/practice.py), line 226) — A pick of an item reserved for a goal's held-out exam, or (with the vault) of an item made from held-out material, is refused before anything is recorded or served (ValueError), however old the proposal: the reservation or the mark may postdate it (exam protection, 2026-10-13, a…
- `record_proposal_selection(repository: Repository, *, proposal_id: str, practice_item_id: str, clock: Clock | None=None, vault: LoadedVault | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/practice.py), line 244) — The learner's selection of a proposed item: the ``practised`` usage signal (idempotent), recorded before serving so a bad proposal is refused before anything is served.
- `record_proposal_delivery(vault: LoadedVault, repository: Repository, selection: Mapping[str, Any], *, session_id: str | None=None, router_decision_id: str | None=None, exercise: Mapping[str, Any] | None=None, import_id: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/instructional/practice.py), line 276) — S5: the picked proposal was delivered (shown and served), after the serving path succeeded.
- `record_proposal_pick(repository: Repository, *, proposal_id: str, practice_item_id: str, clock: Clock | None=None, vault: LoadedVault | None=None, session_id: str | None=None, router_decision_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/practice.py), line 294) — Selection and delivery together, for a caller that has already served the item (the sidecar's pick records them on either side of serving).
- `proposed_exercise(repository: Repository, proposal_id: str, extraction_id: str, span_ids: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/practice.py), line 308) — The source-exercise entry a proposal proposed, or ValueError.
- `duration_response(estimator: Any, item_id: str, mode: str) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/instructional/practice.py), line 328) — The injected minutes estimator's evidence for a not-yet-authored item of ``mode``, as plain data the import job evaluates the AUTHORED draft against (Codex third pass F7: minutes computed with ``expected_minutes=None`` let a 20-minute draft pass a five-minute bound as 3.5).
- `interactive_import_request(vault: LoadedVault, repository: Repository, proposal_id: str, entry: Mapping[str, Any], *, estimator: Any | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/practice.py), line 358) — What a learner's pick of a textbook exercise was proposed for, as plain data the import job validates the authored draft against (Codex re-review F7).
- `record_exercise_pick(repository: Repository, *, proposal_id: str, entry: Mapping[str, Any], clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/instructional/practice.py), line 400) — The ``practised`` usage verdict for a picked textbook exercise (idempotent).
- `imported_exercise_selection(repository: Repository, *, proposal_id: str, import_id: str, practice_item_id: str, vault: LoadedVault | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/practice.py), line 423) — The selection behind serving an imported textbook exercise: its import must have come from this proposal and written this item (ValueError).

### Module constants

- `SHOWN_PROMPT_CHARS` ([src/learnloop/instructional/practice.py](../../../../../../src/learnloop/instructional/practice.py), line 47)
- `EXAM_RESERVED_PICK` ([src/learnloop/instructional/practice.py](../../../../../../src/learnloop/instructional/practice.py), line 222)
- `_DURATION_SAMPLES` ([src/learnloop/instructional/practice.py](../../../../../../src/learnloop/instructional/practice.py), line 325)

### Explicit exports

`__all__` declares:

- `EXAM_RESERVED_PICK`
- `SHOWN_PROMPT_CHARS`
- `constrain_for_caller`
- `continuation_cursor`
- `propose_practice`
- `record_proposal_impressions`
- `proposed_exercise`
- `imported_exercise_selection`
- `duration_response`
- `interactive_import_request`
- `record_exercise_pick`
- `record_proposal_delivery`
- `record_proposal_pick`
- `record_proposal_selection`
- `refuse_protected_pick`
- `service_enabled`

## Internal implementation anchors

- `_shown(text: str, limit: int) -> str` ([source](../../../../../../src/learnloop/instructional/practice.py), line 50)
- `_proposed_key(entry: Mapping[str, Any]) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/instructional/practice.py), line 146)
- `_requested_key(key: Mapping[str, Any]) -> tuple[str, ...] | None` ([source](../../../../../../src/learnloop/instructional/practice.py), line 153)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `continuation_cursor`, `propose_practice`; statically calls `continuation_cursor`, `propose_practice`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `continuation_cursor`, `propose_practice`; statically calls `continuation_cursor`, `propose_practice`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `imported_exercise_selection`, `record_proposal_delivery`, `record_proposal_selection`; statically calls `imported_exercise_selection`, `record_proposal_delivery`, `record_proposal_selection`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `proposed_exercise`; statically calls `proposed_exercise`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `propose_practice`, `service_enabled`; statically calls `propose_practice`, `service_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `propose_practice`, `service_enabled`; statically calls `propose_practice`, `service_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `interactive_import_request`, `proposed_exercise`, `record_exercise_pick`, `record_proposal_impressions`; statically calls `interactive_import_request`, `proposed_exercise`, `record_exercise_pick`, `record_proposal_impressions`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `EXAM_RESERVED_PICK`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `HELD_OUT_ITEM_REFUSAL`, `exam_reserved`, `held_out_item_ids`, `held_out_material`, `held_out_selection_active`; calls `exam_reserved`, `held_out_item_ids`, `held_out_material`, `held_out_selection_active`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `judgments_by_ids`, `proposal`; calls `judgments_by_ids`, `proposal`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `IMPRESSION_SURFACES`, `import_row`, `insert_impression`; calls `import_row`, `insert_impression`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `independent_check_eligibility`; calls `independent_check_eligibility`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `record_pick`; calls `record_pick`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `persisted_screen`; calls `persisted_screen`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `resolve_hypothesis_refs`; calls `resolve_hypothesis_refs`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `normalize_query`, `query_id`; calls `normalize_query`, `query_id`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `IntentUnavailable`, `PracticeConstraints`, `canonical_intent`, `find_practice`, `practice_modes`; calls `IntentUnavailable`, `canonical_intent`, `find_practice`, `practice_modes`
- [[Reference/Modules/learnloop/practice_index/usage|learnloop.practice_index.usage]] — imports `USAGE_TASK`, `record_practice_usage`; calls `record_practice_usage`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `CallerContext`, `PolicyRefused`, `derive_policy`; calls `PolicyRefused`, `derive_policy`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `service_spend`; calls `service_spend`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `fit_presented_prompt`; calls `fit_presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]], [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]], [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_discriminating_search.py](../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_a_pick_with_an_unjudged_worked_example_is_served_as_labelled_practice`
  - `test_an_earlier_impression_and_a_source_exposure_exclude`
  - `test_an_exposed_item_is_not_proposed_for_a_value_intent`
  - `test_the_discriminating_search_switch_refuses_value_intents`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_pick_of_an_item_reserved_since_its_proposal_is_refused_before_anything_is_recorded`
  - `test_an_exam_reserved_item_is_a_cold_administration_for_every_caller`
  - `test_an_import_rechecks_a_stale_proposal_before_any_paid_call`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_a_pick_of_an_item_marked_held_out_since_its_proposal_is_refused`
  - `test_with_the_switch_off_picks_and_session_serves_are_not_refused`
- [tests/test_proposal_impressions.py](../../../../../../tests/test_proposal_impressions.py) — direct import
  - `test_impressions_are_append_only`
  - `test_rendered_keys_are_recorded_from_the_receipt_and_unknown_keys_dropped`
  - `test_unknown_surface_and_proposal_are_refused`
- [tests/test_retrieval_interventions_write_points.py](../../../../../../tests/test_retrieval_interventions_write_points.py) — direct import
  - `test_a_pick_records_the_impressions_shown_before_it`
  - `test_a_value_intent_pick_keeps_both_verdicts`
  - `test_an_exercise_pick_and_a_need_served_are_source_exercise_rows`
- [tests/test_source_exercise_rpcs.py](../../../../../../tests/test_source_exercise_rpcs.py) — direct import
  - `test_an_imported_exercise_is_rechecked_for_independence_when_served`
  - `test_the_carried_duration_response_is_the_plan_estimate_of_the_authored_draft`
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
  - `test_an_ordinary_practice_request_respects_the_daily_cap`
- [tests/test_tutor_practice_request.py](../../../../../../tests/test_tutor_practice_request.py) — direct import
  - `test_a_cold_administration_proposes_nothing`
  - `test_the_caller_is_rederived_on_the_server_and_cannot_widen`
- [tests/test_valuation_calibration_fields.py](../../../../../../tests/test_valuation_calibration_fields.py) — direct import
  - `test_a_valued_pick_followed_by_an_attempt_records_hypothesis_movement`
  - `test_a_valued_pick_keeps_predicted_outcomes_regime_and_minutes`

## Modification guidance

- Make changes here when the responsibility remains practice within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/practice.py](../../../../../../src/learnloop/instructional/practice.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
