---
title: "learnloop.adaptive_difficulty.feature_audit"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/feature_audit.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/feature_audit.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.feature_audit module"
  - "src/learnloop/adaptive_difficulty/feature_audit.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.feature_audit`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.feature_audit` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The feature audit (spec_adaptive_difficulty_v1 §7.2, §10.3; AD1, switch ``feature_audit``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py) |
| Source lines | 550 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `item_revision(item: Any) -> tuple[str, str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 128) — ``(content_hash, item_json)``: the revision's ``practice_item_snapshots`` serialization.
- `audit_state(item: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 144) — What the audit reads: the stem and the reference answer, nothing else.
- `question_for(dimension: str) -> ChoiceQuestion` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 150)
- `class FeatureAuditV1(WireModel)` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 157) — The LLM judge's answer: one value per asked dimension (null: cannot tell).
- `llm_prompt(item: Any, dimensions: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 168)
- `class AuditOutcome` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 181) — One revision's audit run.
  - `as_dict(self) -> dict[str, Any]` (line 195; public)
- `canonical_audits(connection: Any, content_hash: str, *, as_of: str | None=None, version: str=VERSION) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 199) — Per dimension, the revision's canonical audit: the earliest answered judgment.
- `audit_revision(vault: Any, repository: Any, item: Any, *, decider_factory: Callable[[], Any] | None=None, llm_client: Any | None=None, clock: Clock | None=None, protected: Any=None, fence: Any=None, live_vault: Callable[[], Any] | None=None) -> AuditOutcome` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 268) — Audit one item revision: the dimensions it has no canonical audit for.

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 61)
- `TASK` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 63)
- `VERSION` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 64)
- `LEFT_KIND` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 65)
- `RIGHT_KIND` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 66)
- `LLM_ROUTE` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 68)
- `DECIDER_ROUTE` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 69)
- `SCHEMA` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 70)
- `DIMENSIONS` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 71)
- `VOCABULARY` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 74)
- `_DESCRIPTIONS` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 81)
- `_INSTRUCTIONS` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 115)
- `_PREAMBLE` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 122)
- `_CAPS` ([src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 125)

### Explicit exports

`__all__` declares:

- `AuditOutcome`
- `DIMENSIONS`
- `FeatureAuditV1`
- `LEFT_KIND`
- `RIGHT_KIND`
- `TASK`
- `VERSION`
- `VOCABULARY`
- `audit_revision`
- `audit_state`
- `canonical_audits`
- `item_revision`
- `llm_prompt`
- `question_for`

## Internal implementation anchors

- `_answer_text(item: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 139)
- `_append(repository: Any, *, content_hash: str, item_id: str, dimension: str, judge: str, verdict: str, model: str, input_hash: str, score: float | None, rationale: Mapping[str, Any], now: str, admit: Callable[[], None] | None=None) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 226)
- `_decider_client(vault: Any, factory: Callable[[], Any] | None) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 241)
- `_llm_client(vault: Any, client: Any | None) -> tuple[Any | None, str | None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 251)
- `_remaining(repository: Any, content_hash: str) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 261)
- `_audit(vault: Any, worker: Any, item: Any, item_json: str, content_hash: str, remaining: list[str], outcome: AuditOutcome, *, decider_factory: Callable[[], Any] | None, llm_client: Any | None, clock: Clock | None, send: SendGuard) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 339)
- `_llm_fallback(vault: Any, repository: Any, item: Any, dimensions: list[str], decider_rows: Mapping[str, tuple[str, str]], outcome: AuditOutcome, *, envelope: Any, client: Any | None, content_hash: str, clock: Clock | None, send: SendGuard) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py), line 443)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `DECIDER_ROUTE`, `DIMENSIONS`, `FeatureAuditV1`, `LLM_ROUTE`, `_CAPS`, `audit_revision`, `audit_state`, `canonical_audits`, `item_revision`, `llm_prompt`, `question_for`; statically calls `audit_revision`, `audit_state`, `canonical_audits`, `item_revision`, `llm_prompt`, `question_for`
- [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]] — imports `audit_revision`, `item_revision`; statically calls `audit_revision`, `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `item_revision`; statically calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `item_revision`; statically calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `item_revision`; statically calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `item_revision`; statically calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/predict|learnloop.adaptive_difficulty.predict]] — imports `item_revision`; statically calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `item_revision`; statically calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `canonical_audits`; statically calls `canonical_audits`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]] — imports `DIMENSIONS`, `canonical_audits`, `item_revision`; statically calls `canonical_audits`, `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `item_revision`; statically calls `item_revision`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]] — imports `LeaseLost`, `ReceiptWriteFailed`, `audit_key`, `claimed`; calls `audit_key`, `claimed`
- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `current_view`; calls `current_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`; calls `entry`
- [[Reference/Modules/learnloop/adaptive_difficulty/protection|learnloop.adaptive_difficulty.protection]] — imports `guard`; calls `guard`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `ProtectedContent`, `SendGuard`, `StaleSnapshot`, `module`, `refusal_status`; calls `SendGuard`, `ask_decider`, `ask_llm`, `refusal_status`
- [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]] — imports `module`; calls `ad_envelope`, `models_off`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `feature_audit_enabled`; calls `feature_audit_enabled`
- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`, `choice_probabilities`; calls `ChoiceQuestion`, `choice_probabilities`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `module`; calls `insert_item_snapshot`, `insert_payload`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `client_for`, `module`; calls `argmax`, `client_for`, `enabled`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`, `resolve_client`; calls `plan_route`, `resolve_client`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]], [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] and 6 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad1_codex_review_fixes.py](../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
  - `test_a_claim_held_by_another_process_is_skipped`
  - `test_a_revision_is_protected_by_its_own_source_even_under_an_ordinary_id`
  - `test_a_vault_switch_fences_the_feature_audit`
  - `test_historical_snapshots_of_held_out_material_are_never_audited`
- [tests/test_ad1_fix_round4.py](../../../../../../tests/test_ad1_fix_round4.py) — direct import
- [tests/test_ad1_fix_round5.py](../../../../../../tests/test_ad1_fix_round5.py) — direct import
- [tests/test_ad1_fix_round6.py](../../../../../../tests/test_ad1_fix_round6.py) — direct import
  - `test_a_revision_that_keeps_raising_never_starves_the_rest`
- [tests/test_ad1_fix_round7.py](../../../../../../tests/test_ad1_fix_round7.py) — direct import
  - `test_a_refused_decider_record_labels_the_decider_status`
- [tests/test_ad1_fix_round9.py](../../../../../../tests/test_ad1_fix_round9.py) — direct import
  - `test_a_stopped_decider_request_stops_the_audit`
- [tests/test_ad1_migration.py](../../../../../../tests/test_ad1_migration.py) — direct import
  - `test_a_served_revision_hashes_as_the_scheduler_snapshots_it`
- [tests/test_ad1_outside_and_cli.py](../../../../../../tests/test_ad1_outside_and_cli.py) — direct import
  - `test_the_feature_audit_respects_the_cap_and_falls_back_honestly`
- [tests/test_ad1_send_guard.py](../../../../../../tests/test_ad1_send_guard.py) — direct import
  - `test_a_revision_held_out_during_the_decider_request_refuses_the_llm_fallback`
  - `test_a_revision_held_out_inside_a_truncated_fallback_attempt_refuses_the_retry`
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_a_run_whose_quoted_revision_was_replaced_then_protected_is_not_used`
  - `test_a_saved_run_proposed_before_its_subject_was_protected_is_not_used`
  - `test_a_stale_run_never_answers_for_a_re_proposal`
- [tests/test_ad23_fix_r7.py](../../../../../../tests/test_ad23_fix_r7.py) — direct import
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_z_v1_calibration_never_reads_a_withheld_items_forecast`
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_frozen_serve_signals_trained_on_a_newly_protected_answer_are_not_replayed`
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_a_failed_decider_hands_every_dimension_to_the_llm`
  - `test_feature_audit_ledgered_with_fallback`
  - `test_serve_inputs_frozen_against_later_audit_and_edit`
  - `test_the_decider_switch_off_audits_with_the_llm_only`

## Modification guidance

- Make changes here when the responsibility remains feature audit within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/feature_audit.py](../../../../../../src/learnloop/adaptive_difficulty/feature_audit.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
