---
title: "learnloop.content.proposals.required_method_override"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/proposals/required_method_override.py"
source_paths:
  - "src/learnloop/content/proposals/required_method_override.py"
source_commit: "7efb7664be3f2dd41be0568e28c27d8e3e3e3a32"
source_commit_timestamp: "2026-10-14T15:55:29-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.proposals"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.proposals.required_method_override module"
  - "src/learnloop/content/proposals/required_method_override.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-proposals"
---

# `learnloop.content.proposals.required_method_override`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.proposals.required_method_override` exists within [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] to own the behavior summarized by its module contract: The owner's change to an item's required method, through the proposal/confirm path.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/proposals/required_method_override.py](../../../../../../../src/learnloop/content/proposals/required_method_override.py) |
| Source lines | 273 |
| Owning package | [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7efb7664be3f2dd41be0568e28c27d8e3e3e3a32` |
| Commit timestamp | `2026-10-14T15:55:29-04:00` |

## Public API

- `override_payload(vault: LoadedVault, item_id: str, *, name: str | None=None, criterion_ids: Sequence[str]=(), clear: bool=False) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/required_method_override.py), line 63) — The update one override proposes (``payload``), with the field before (``from``) and after (``to``).
- `propose_required_method_override(vault: LoadedVault, repository: Repository, item_id: str, *, name: str | None=None, criterion_ids: Sequence[str]=(), clear: bool=False, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/required_method_override.py), line 124) — Persist the owner's override as one pending proposal; returns its id and change.
- `is_override_item(item: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/required_method_override.py), line 170) — Is this proposal item the owner's override (its audit, which only :func:`propose_required_method_override` writes)?
- `owner_verdict_side_effect(proposal_item_id: str, existing: Any, data: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/required_method_override.py), line 178) — The acceptance plan's write of the owner's verdict for one override.
- `owner_input_hash(row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/proposals/required_method_override.py), line 211) — What the owner decided on: a source statement's verdict answers the import judgment's own question (its statement and method), so a lookup of that question finds it; a generated item's verdict is the field.
- `record_owner_verdict(repository: Repository, row: Mapping[str, Any], created_at: str) -> str` ([source](../../../../../../../src/learnloop/content/proposals/required_method_override.py), line 226) — Append the owner's verdict (idempotent on the row's fixed id); returns its id.

### Module constants

- `PROPOSAL_PURPOSE` ([src/learnloop/content/proposals/required_method_override.py](../../../../../../../src/learnloop/content/proposals/required_method_override.py), line 50)
- `OVERRIDE_VERSION` ([src/learnloop/content/proposals/required_method_override.py](../../../../../../../src/learnloop/content/proposals/required_method_override.py), line 51)
- `OWNER_VERDICT_EFFECT` ([src/learnloop/content/proposals/required_method_override.py](../../../../../../../src/learnloop/content/proposals/required_method_override.py), line 53)
- `OWNER_REQUIRES` ([src/learnloop/content/proposals/required_method_override.py](../../../../../../../src/learnloop/content/proposals/required_method_override.py), line 55)
- `OWNER_NOT_REQUIRED` ([src/learnloop/content/proposals/required_method_override.py](../../../../../../../src/learnloop/content/proposals/required_method_override.py), line 56)

### Explicit exports

`__all__` declares:

- `OVERRIDE_VERSION`
- `OWNER_NOT_REQUIRED`
- `OWNER_REQUIRES`
- `OWNER_VERDICT_EFFECT`
- `PROPOSAL_PURPOSE`
- `is_override_item`
- `override_payload`
- `owner_input_hash`
- `owner_verdict_side_effect`
- `propose_required_method_override`
- `record_owner_verdict`

## Internal implementation anchors

- `_input_hash(payload: Any) -> str` ([source](../../../../../../../src/learnloop/content/proposals/required_method_override.py), line 59)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]] — imports `propose_required_method_override`; statically calls `propose_required_method_override`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `record_owner_verdict`; statically calls `record_owner_verdict`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `is_override_item`, `owner_verdict_side_effect`; statically calls `is_override_item`, `owner_verdict_side_effect`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `TASK`, `statement_input_hash`; calls `statement_input_hash`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `compute_target_hash`; calls `compute_target_hash`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `best_target`, `is_source_statement`, `method_targets`, `names_match`; calls `best_target`, `is_source_statement`, `method_targets`, `names_match`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]], [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]], [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_required_method_authority.py](../../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_the_override_refuses_unknown_criteria_and_a_clear_with_nothing_to_clear`
  - `test_the_owner_override_on_a_generated_item_changes_only_the_field`
  - `test_the_owner_overrides_a_source_decision_and_clears_it_through_proposals`
- [tests/test_required_method_reopened.py](../../../../../../../tests/test_required_method_reopened.py) — direct import
  - `test_f15_a_generated_items_new_prompt_is_stored_as_generated`
  - `test_f15_a_generated_update_renaming_the_method_changes_only_the_field`
  - `test_f16_a_generated_items_override_is_ledgered_and_the_write_is_idempotent`
  - `test_f16_an_accepted_override_appends_the_owners_verdict_superseding_the_judgment`
- [tests/test_required_method_round3.py](../../../../../../../tests/test_required_method_round3.py) — direct import
  - `test_f21_clearing_or_renaming_never_edits_the_statement`
- [tests/test_required_method_round3_review.py](../../../../../../../tests/test_required_method_round3_review.py) — direct import

## Modification guidance

- Change required method override policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/proposals/required_method_override.py](../../../../../../../src/learnloop/content/proposals/required_method_override.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
