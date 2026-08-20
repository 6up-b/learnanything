---
title: "learnloop.content.authoring.item_authoring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/item_authoring.py"
source_paths:
  - "src/learnloop/content/authoring/item_authoring.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.item_authoring` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: Learner-owned practice-item authoring: create, edit, retire, split.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/item_authoring.py](../../../../../../../src/learnloop/content/authoring/item_authoring.py) |
| Source lines | 382 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ItemAuthoringError(ValueError)` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 37) — Invalid learner authoring operation.
- `author_item(root: Path, repository: Repository, *, learning_object_id: str, prompt: str, expected_answer: str, practice_mode: str='short_answer', hints: Sequence[str] | None=None, evidence_facets: Sequence[str] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 89) — Create a learner-authored card under an existing Learning Object.
- `edit_item(root: Path, repository: Repository, *, practice_item_id: str, prompt: str | None=None, expected_answer: str | None=None, hints: Sequence[str] | None=None, reason: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 146) — Reword a card in place.
- `retire_item(root: Path, repository: Repository, *, practice_item_id: str, reason: str, note: str | None=None, clock: Clock | None=None, loaded_vault: LoadedVault | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 191) — Retire a card: never served again, all history kept.
- `split_item(root: Path, repository: Repository, *, practice_item_id: str, parts: Sequence[Mapping[str, str]], reason: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 290) — "This feels like it actually wants to be two questions": retire the original and author one card per part, provenance-linked to it.

### Module constants

- `_LOGGER` ([src/learnloop/content/authoring/item_authoring.py](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 32)
- `EDITABLE_FIELDS` ([src/learnloop/content/authoring/item_authoring.py](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 34)
- `RETIREMENT_REASONS` ([src/learnloop/content/authoring/item_authoring.py](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 44)

## Internal implementation anchors

- `_require_item(vault: LoadedVault, practice_item_id: str) -> PracticeItem` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 59)
- `_record(repository: Repository, *, kind: str, practice_item_id: str, detail: Mapping[str, Any], clock: Clock | None) -> None` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 66) — Provenance trail; failure never blocks the learner's edit.
- `_apply_difficulty_report(vault, repository: Repository, item, *, reason: str, clock: Clock | None=None) -> None` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 239) — A too_easy/too_hard retirement is a learner report about THEMSELVES, not only about the card.
- `_mirror_surface_retirement(repository: Repository, item: PracticeItem, *, reason: str, clock: Clock | None) -> None` ([source](../../../../../../../src/learnloop/content/authoring/item_authoring.py), line 343) — Retire existing substrate cards without minting anything on retirement.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/card|learnloop.cli.card]] — imports `ItemAuthoringError`, `author_item`, `edit_item`, `retire_item`; statically calls `author_item`, `edit_item`, `retire_item`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `ItemAuthoringError`, `author_item`, `edit_item`, `retire_item`, `split_item`; statically calls `author_item`, `edit_item`, `retire_item`, `split_item`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `default_capability_for`; calls `default_capability_for`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `reanchor_mastery_from_claim`; calls `reanchor_mastery_from_claim`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `retire_with_reason`; calls `retire_with_reason`
- [[Reference/Modules/learnloop/substrate/surface_mint|learnloop.substrate.surface_mint]] — imports `obsolete_mint_work_for_card_versions`; calls `obsolete_mint_work_for_card_versions`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `logging`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/card|learnloop.cli.card]], [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_item_authoring.py](../../../../../../../tests/test_item_authoring.py) — direct import
  - `test_author_item_creates_learner_card`
  - `test_author_item_validates`
  - `test_edit_item_rewords_in_place`
  - `test_retire_item_reuses_loaded_vault_and_clears_serving_backdoors`
  - `test_retire_item_stops_all_serving`
  - `test_split_item_retires_original_and_links_parts`
- [tests/test_sidecar_blueprint_picker.py](../../../../../../../tests/test_sidecar_blueprint_picker.py) — direct import

## Modification guidance

- Change item authoring policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/item_authoring.py](../../../../../../../src/learnloop/content/authoring/item_authoring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
