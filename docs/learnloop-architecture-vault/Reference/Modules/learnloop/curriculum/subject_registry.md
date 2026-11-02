---
title: "learnloop.curriculum.subject_registry"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/subject_registry.py"
source_paths:
  - "src/learnloop/curriculum/subject_registry.py"
source_commit: "b59f5a1a88e2481769277ee7f9fc528968d2f5d2"
source_commit_timestamp: "2026-10-13T11:32:17-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.subject_registry module"
  - "src/learnloop/curriculum/subject_registry.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.subject_registry`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.subject_registry` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: Registry review (spec_source_ingestion_v2 §5.7; spec_knowledge_model §3.4, §12.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/subject_registry.py](../../../../../../src/learnloop/curriculum/subject_registry.py) |
| Source lines | 218 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b59f5a1a88e2481769277ee7f9fc528968d2f5d2` |
| Commit timestamp | `2026-10-13T11:32:17-04:00` |

## Public API

- `class RegistryReviewError(ValueError)` ([source](../../../../../../src/learnloop/curriculum/subject_registry.py), line 37)
  - `__init__(self, code: str, message: str) -> None` (line 38; internal)
- `build_subject_registry(vault, repository, subject_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/subject_registry.py), line 79) — Facet-contract cards + identifiability warnings (§5.7).
- `propose_facet_merge(vault, repository, *, subject_id: str, retired_facet_id: str, surviving_facet_id: str, rationale: str | None=None, need_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/subject_registry.py), line 141) — Merge ``retired_facet_id`` into ``surviving_facet_id`` now, with a one-tap undo.

## Internal implementation anchors

- `_facet_ids_for_subject(vault, subject_id: str) -> list[str]` ([source](../../../../../../src/learnloop/curriculum/subject_registry.py), line 43) — Canonical facet ids exercised by the subject's practice items, plus any facet whose provenance/contract lists the subject — deterministic, sorted.
- `_facet_card(facet) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/subject_registry.py), line 55)
- `_reword_confirms(vault, repository, subject_id: str, facet_ids: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/subject_registry.py), line 125) — Rewords waiting for the owner's confirm (owner, 2026-10-13) that this subject's review shows.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]] — imports `RegistryReviewError`, `build_subject_registry`, `propose_facet_merge`; statically calls `build_subject_registry`, `propose_facet_merge`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `HELD_BACK_NOTE`, `action_by_id`, `describe`, `merge_registered_facets`, `pending_reword_confirms`; calls `action_by_id`, `describe`, `merge_registered_facets`, `pending_reword_confirms`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `TASK`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `build_registry_view`, `measurement_rank`; calls `build_registry_view`, `measurement_rank`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_reword_confirm.py](../../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_registry_review_lists_a_pending_confirm_with_its_wording_and_sources`
- [tests/test_facet_reword_confirm_review.py](../../../../../../tests/test_facet_reword_confirm_review.py) — direct import
  - `test_a_pending_confirm_hides_a_sources_text_once_its_member_is_an_exam`
- [tests/test_subject_registry.py](../../../../../../tests/test_subject_registry.py) — direct import
  - `test_coarsen_acceptance_resolves_generation_need`
  - `test_propose_facet_merge_applies_live_and_records_the_owners_verdict`
  - `test_propose_facet_merge_rejects_self_merge`
  - `test_propose_facet_merge_still_holds_back_a_shared_graded_criterion`
  - `test_subject_registry_facet_contract_cards`
  - `test_the_owner_merges_a_facet_that_used_to_be_locked_and_can_undo_it`
  - `test_unknown_subject_raises`

## Modification guidance

- Change subject registry policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/subject_registry.py](../../../../../../src/learnloop/curriculum/subject_registry.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
