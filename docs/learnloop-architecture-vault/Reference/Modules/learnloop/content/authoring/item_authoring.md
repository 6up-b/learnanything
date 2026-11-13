---
title: "learnloop.content.authoring.item_authoring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/item_authoring.py"
source_paths:
  - "src/learnloop/content/authoring/item_authoring.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.item_authoring module"
  - "src/learnloop/content/authoring/item_authoring.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.item_authoring`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.item_authoring` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: Learner-owned practice-item authoring: create, edit, retire, split.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/item_authoring.py](../../../../../../../src/learnloop/content/authoring/item_authoring.py) |
| Source lines | 453 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ItemAuthoringError(ValueError)` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 38) — Invalid learner authoring operation.
- `validate_author_item(vault, *, learning_object_id: str, prompt: str, expected_answer: str) -> None` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 90) — Pure validation shared by preflight and the authoritative file write.
- `author_item(root: Path, repository: Repository, *, learning_object_id: str, prompt: str, expected_answer: str, practice_mode: str='short_answer', hints: Sequence[str] | None=None, evidence_facets: Sequence[str] | None=None, source_refs: Sequence[Mapping[str, Any]] | None=None, event_detail: Mapping[str, Any] | None=None, item_id: str | None=None, provenance_detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 100) — Create a learner-authored card under an existing Learning Object.
- `edit_item(root: Path, repository: Repository, *, practice_item_id: str, prompt: str | None=None, expected_answer: str | None=None, hints: Sequence[str] | None=None, reason: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 174) — Reword a card in place.
- `retire_item(root: Path, repository: Repository, *, practice_item_id: str, reason: str, note: str | None=None, clock: Clock | None=None, loaded_vault: LoadedVault | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 223) — Retire a card: never served again, all history kept.
- `split_item(root: Path, repository: Repository, *, practice_item_id: str, parts: Sequence[Mapping[str, str]], reason: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 361) — "This feels like it actually wants to be two questions": retire the original and author one card per part, provenance-linked to it.

### Module constants

- `_LOGGER` ([src/learnloop/content/authoring/item_authoring.py](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 33)
- `EDITABLE_FIELDS` ([src/learnloop/content/authoring/item_authoring.py](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 35)
- `RETIREMENT_REASONS` ([src/learnloop/content/authoring/item_authoring.py](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 45)

## Internal implementation anchors

- `_require_item(vault: LoadedVault, practice_item_id: str) -> PracticeItem` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 60)
- `_record(repository: Repository, *, kind: str, practice_item_id: str, detail: Mapping[str, Any], clock: Clock | None) -> None` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 67) — Provenance trail; failure never blocks the learner's edit.
- `_apply_placement_self_report(vault, repository: Repository, item, *, reason: str, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 285) — Learner field F2 (mvp-0.11): "too easy" also marks the item's LO assumed known (not tested), checked in its first review (spec §5.2, D5).
- `_apply_difficulty_report(vault, repository: Repository, item, *, reason: str, clock: Clock | None=None) -> None` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 317) — A too_easy/too_hard retirement is a learner report about THEMSELVES, not only about the card.
- `_mirror_surface_retirement(repository: Repository, item: PracticeItem, *, reason: str, clock: Clock | None) -> None` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 414) — Retire existing substrate cards without minting anything on retirement.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/card|learnloop.cli.card]] — imports `ItemAuthoringError`, `author_item`, `edit_item`, `retire_item`; statically calls `author_item`, `edit_item`, `retire_item`
- [[Reference/Modules/learnloop/reader/active_reading|learnloop.reader.active_reading]] — imports `retire_item`; statically calls `retire_item`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `author_item`, `retire_item`; statically calls `author_item`, `retire_item`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `ItemAuthoringError`, `author_item`, `edit_item`, `retire_item`, `split_item`, `validate_author_item`; statically calls `author_item`, `edit_item`, `retire_item`, `split_item`, `validate_author_item`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `default_capability_for`; calls `default_capability_for`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `replace_claim_and_reanchor`; calls `replace_claim_and_reanchor`
- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `record_self_report`; calls `record_self_report`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `placement_active`; calls `placement_active`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `retire_with_reason`; calls `retire_with_reason`
- [[Reference/Modules/learnloop/substrate/surface_mint|learnloop.substrate.surface_mint]] — imports `obsolete_mint_work_for_card_versions`; calls `obsolete_mint_work_for_card_versions`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `current_practice_item`, `upsert_practice_item`; calls `current_practice_item`, `upsert_practice_item`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `logging`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/card|learnloop.cli.card]], [[Reference/Modules/learnloop/reader/active_reading|learnloop.reader.active_reading]], [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]], [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reference_gate_imports_helpers.py](../../../../../../../tests/reference_gate_imports_helpers.py) — direct import
- [tests/test_activity_families.py](../../../../../../../tests/test_activity_families.py) — direct import
  - `test_learner_edit_during_family_publication_is_not_lost`
  - `test_retire_from_a_stale_snapshot_keeps_family_membership`
- [tests/test_assumed_known.py](../../../../../../../tests/test_assumed_known.py) — direct import
  - `test_learner_placement_verdicts_append_to_the_judgment_ledger`
  - `test_too_easy_retirement_marks_the_lo_assumed_without_extra_writes`
- [tests/test_item_authoring.py](../../../../../../../tests/test_item_authoring.py) — direct import
  - `test_author_item_creates_learner_card`
  - `test_author_item_validates`
  - `test_edit_item_rewords_in_place`
  - `test_retire_item_reuses_loaded_vault_and_clears_serving_backdoors`
  - `test_retire_item_stops_all_serving`
  - `test_split_item_retires_original_and_links_parts`
- [tests/test_learner_report_superseded.py](../../../../../../../tests/test_learner_report_superseded.py) — direct import
  - `test_a_failure_between_the_replacement_and_its_re_anchor_leaves_the_earlier_report_in_force`
  - `test_a_replacement_from_another_process_whose_id_sorts_first_replays_after_the_claim_it_replaced`
  - `test_a_rung_variant_request_replaces_only_its_own_source_on_its_own_lo`
  - `test_a_second_too_easy_report_keeps_the_first_as_a_replaced_row_that_no_live_reader_reads`
  - `test_below_the_tag_the_seam_still_deletes_the_replaced_claim`
  - `test_random_attempts_and_learner_reports_rebuild_to_live`
  - `test_the_field_priors_read_only_the_claims_in_force`
  - `test_two_retirements_on_an_lo_without_attempts_rebuild_to_the_variance_the_replaced_one_left`
  - `test_two_writers_on_one_warm_lo_apply_their_reports_in_the_order_replay_reads`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
  - `test_f7_every_reanchoring_writer_records_its_point`
- [tests/test_pr4_superseded_claims_landing.py](../../../../../../../tests/test_pr4_superseded_claims_landing.py) — direct import
- [tests/test_reader_adoption_ownership.py](../../../../../../../tests/test_reader_adoption_ownership.py) — direct import
  - `test_an_independently_written_matching_card_is_not_captured`
- [tests/test_rebuild_closed_row_answer.py](../../../../../../../tests/test_rebuild_closed_row_answer.py) — direct import
  - `test_a_sibling_retired_after_the_last_answer_rebuilds_to_live`
  - `test_an_answer_after_a_sibling_was_retired_rebuilds_to_live`
- [tests/test_rebuild_equivalence.py](../../../../../../../tests/test_rebuild_equivalence.py) — direct import
  - `test_a_full_sync_after_a_rebuild_keeps_retired_items_retired`
  - `test_a_retired_item_stays_inactive_through_a_primary_load_and_a_rebuild`
  - `test_a_second_learner_report_on_an_lo_after_an_attempt_rebuilds_to_live`
  - `test_content_sync_nests_inside_a_rebuild_transaction_and_rolls_back_with_it`
  - `test_random_attempt_histories_rebuild_to_live_state_exactly`
  - `test_random_histories_with_claims_after_attempts_and_too_easy_retirements_rebuild_to_live`
- [tests/test_rebuild_equivalence_review.py](../../../../../../../tests/test_rebuild_equivalence_review.py) — direct import
- [tests/test_reference_check_binding.py](../../../../../../../tests/test_reference_check_binding.py) — direct import
  - `test_a_hints_only_edit_keeps_the_verification`
  - `test_a_late_background_check_never_verifies_an_edit`
  - `test_an_edited_prompt_or_key_is_unverified_until_rechecked`
- [tests/test_slate_record.py](../../../../../../../tests/test_slate_record.py) — direct import
- [tests/test_source_exercise_import.py](../../../../../../../tests/test_source_exercise_import.py) — direct import
  - `test_a_resumed_check_never_verifies_content_edited_since`
  - `test_recovery_never_binds_a_verdict_to_content_edited_before_the_commit`

## Modification guidance

- Change item authoring policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/item_authoring.py](../../../../../../../src/learnloop/content/authoring/item_authoring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
