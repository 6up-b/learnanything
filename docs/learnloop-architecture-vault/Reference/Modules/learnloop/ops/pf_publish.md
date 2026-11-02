---
title: "learnloop.ops.pf_publish"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/pf_publish.py"
source_paths:
  - "src/learnloop/ops/pf_publish.py"
source_commit: "2d7c4948399efdc96c3c60d7379da37bc90a9e3d"
source_commit_timestamp: "2026-10-14T20:18:37-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.pf_publish module"
  - "src/learnloop/ops/pf_publish.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.pf_publish`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.pf_publish` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: Publish verified PF-b survivors into their family as ordinary items (Slice 2 §5.3).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/pf_publish.py](../../../../../../src/learnloop/ops/pf_publish.py) |
| Source lines | 572 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2d7c4948399efdc96c3c60d7379da37bc90a9e3d` |
| Commit timestamp | `2026-10-14T20:18:37-04:00` |

## Public API

- `class PublishRefused(ValueError)` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 76) — The candidate may not be published (unverified, disabled, wrong state).
- `class VariantContradictsRequiredMethod(PublishRefused)` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 80) — The one-time publication judgment found that the variant's stem prohibits or contradicts the parent's required method, while the parent's rubric (copied verbatim) grades use of it (review F10; redesign 2026-10-14): rejected, so a later run regenerates the variant.
- `class RequiredMethodUnjudged(PublishRefused)` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 87) — A variant of a parent with a required method has no recorded one-time judgment of its stem yet (no judge was ready, or it refused or failed): not published, never with an unchecked appended sentence.
- `utc_day_bounds(clock: Clock | None=None) -> tuple[str, str]` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 98)
- `remaining_publish_slots(vault: LoadedVault, repository: Repository, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 106)
- `published_item_id(candidate_id: str) -> str` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 114)
- `variant_method_verdict(connection: Any, row: Mapping[str, Any], parent: PracticeItem) -> str | None` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 118) — The one-time publication judgment recorded for this candidate's stem against the parent's required method (``consistent`` / ``contradicts``), or None (the parent requires none, or nothing is recorded yet).
- `build_item_payload(vault: LoadedVault, parent: PracticeItem, row: dict[str, Any], *, item_id: str, now_iso: str, method_verdict: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 132) — The published item's payload, copied from the parent's contract.
- `judged_inputs(vault: LoadedVault, parent: PracticeItem, family: ActivityFamily) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 231) — The parent/family revisions and effective rubric a family run is judged against.
- `stale_inputs(vault: LoadedVault, row: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 253) — The judged inputs that no longer hold (empty when the selection is current).
- `class StaleSelection(PublishRefused)` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 269) — The selection was judged against a parent or family that has since changed.
- `publish_candidate(vault: LoadedVault, repository: Repository, candidate_id: str, *, clock: Clock | None=None) -> tuple[LoadedVault, str]` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 273) — Publish one selected, verified candidate; idempotent after a crash.
- `judge_variant_stem(vault: LoadedVault, repository: Repository, row: Mapping[str, Any], method_judge: Any, *, owner: tuple[str, str], clock: Clock | None=None, strict: bool=False) -> str | None` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 479) — The one-time publication judgment of a variant's stem (redesign 2026-10-14): does it prohibit or contradict the parent's required method?
- `publish_selected(vault: LoadedVault, repository: Repository, candidate_ids: list[str], *, clock: Clock | None=None, method_judge: Any=None, judge_owner: tuple[str, str]=PUBLISH_JUDGE_OWNER) -> tuple[LoadedVault, dict[str, Any]]` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 526) — Publish in order while today's cap allows; the rest stay ``selected``.

### Module constants

- `_LOGGER` ([src/learnloop/ops/pf_publish.py](../../../../../../src/learnloop/ops/pf_publish.py), line 48)
- `PUBLISH_POLICY_VERSION` ([src/learnloop/ops/pf_publish.py](../../../../../../src/learnloop/ops/pf_publish.py), line 50)
- `JUDGED_INPUTS_VERSION` ([src/learnloop/ops/pf_publish.py](../../../../../../src/learnloop/ops/pf_publish.py), line 51)
- `_CONTRACT_FIELDS` ([src/learnloop/ops/pf_publish.py](../../../../../../src/learnloop/ops/pf_publish.py), line 53)
- `PF_TAG` ([src/learnloop/ops/pf_publish.py](../../../../../../src/learnloop/ops/pf_publish.py), line 59)
- `TRACE_RELATIONS` ([src/learnloop/ops/pf_publish.py](../../../../../../src/learnloop/ops/pf_publish.py), line 62)
- `PF_KEY_STATUS` ([src/learnloop/ops/pf_publish.py](../../../../../../src/learnloop/ops/pf_publish.py), line 68)
- `PUBLISH_JUDGE_OWNER` ([src/learnloop/ops/pf_publish.py](../../../../../../src/learnloop/ops/pf_publish.py), line 95)

### Explicit exports

`__all__` declares:

- `JUDGED_INPUTS_VERSION`
- `PF_TAG`
- `PUBLISH_JUDGE_OWNER`
- `PUBLISH_POLICY_VERSION`
- `TRACE_RELATIONS`
- `PublishRefused`
- `RequiredMethodUnjudged`
- `StaleSelection`
- `VariantContradictsRequiredMethod`
- `build_item_payload`
- `judge_variant_stem`
- `judged_inputs`
- `publish_candidate`
- `publish_selected`
- `published_item_id`
- `remaining_publish_slots`
- `stale_inputs`
- `utc_day_bounds`
- `variant_method_verdict`

## Internal implementation anchors

- `_contract_view(vault: LoadedVault, parent: PracticeItem) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 218) — What the judges compared against and what publication copies from the parent.
- `_publish_locked(vault: LoadedVault, repository: Repository, candidate_id: str, *, clock: Clock | None) -> tuple[LoadedVault, str]` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 289)
- `_record_variant_key_check(connection: Any, item: PracticeItem, row: Mapping[str, Any], *, now_iso: str, decision_id: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 384) — A published variant of a textbook exercise records PF's verification of it as a reference-key check bound to its own content (idempotent).
- `_refuse_stale(repository: Repository, row: Mapping[str, Any], changed: list[str], now_iso: str) -> None` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 417) — Ledger the refusal and retire the selection from the backlog (regenerate to retry).
- `_refuse_contradiction(repository: Repository, row: Mapping[str, Any], reason: str, now_iso: str) -> None` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 434) — Ledger the refusal and reject the candidate (re-review F10; regenerate to retry).
- `_check_ledger(row: dict[str, Any], verdicts: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 451) — Publication reads the authoritative verdicts (§5.8), never workflow JSON.
- `_initialize_scheduling(repository: Repository, item: PracticeItem, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/ops/pf_publish.py), line 470) — Fresh scheduling state, as the next state sync would derive it, only when absent.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `TRACE_RELATIONS`, `judge_variant_stem`, `judged_inputs`, `publish_selected`, `remaining_publish_slots`, `stale_inputs`; statically calls `judge_variant_stem`, `judged_inputs`, `publish_selected`, `remaining_publish_slots`, `stale_inputs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `CONTRADICTS`, `as_lazy`, `recorded_verdict`; calls `as_lazy`, `recorded_verdict`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/families|learnloop.db.stores.families]] — imports `append_membership`; calls `append_membership`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/pf|learnloop.db.stores.pf]] — imports `candidate`, `candidate_verdicts`, `published_count_between`, `update_candidate`, `verdict_survived`, `verdict_verified`; calls `candidate`, `candidate_verdicts`, `published_count_between`, `update_candidate`, `verdict_survived`, `verdict_verified`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `insert_key_check`, `reference_content_hash`; calls `insert_key_check`, `reference_content_hash`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `resolve_legacy_item`; calls `resolve_legacy_item`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/item_fingerprints|learnloop.substrate.item_fingerprints]] — imports `render_expected_answer`; calls `render_expected_answer`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `ActivityFamily`, `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `inherit_required_method`; calls `inherit_required_method`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_canonical_exercise_serialization.py](../../../../../../tests/test_canonical_exercise_serialization.py) — direct import
  - `test_a_pf_variant_of_a_textbook_exercise_points_at_it`
- [tests/test_pf_generation.py](../../../../../../tests/test_pf_generation.py) — direct import
  - `test_a_published_variant_of_a_textbook_exercise_keeps_its_own_verification`
  - `test_a_selection_whose_parent_contract_changed_is_never_published`
  - `test_an_unverified_candidate_cannot_be_published`
  - `test_publication_reads_the_ledger_so_forged_workflow_state_cannot_publish`
  - `test_publication_recovery_never_erases_scheduling_state`
- [tests/test_required_method_authority.py](../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_a_variant_payload_is_never_built_without_its_publication_judgment`
- [tests/test_required_method_items.py](../../../../../../tests/test_required_method_items.py) — direct import
  - `test_pf_publication_keeps_the_parents_required_method_and_states_it`

## Modification guidance

- Make changes here when the responsibility remains pf publish within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/pf_publish.py](../../../../../../src/learnloop/ops/pf_publish.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
