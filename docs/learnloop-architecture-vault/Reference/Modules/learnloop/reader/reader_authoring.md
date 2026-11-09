---
title: "learnloop.reader.reader_authoring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_authoring.py"
source_paths:
  - "src/learnloop/reader/reader_authoring.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_authoring module"
  - "src/learnloop/reader/reader_authoring.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_authoring`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_authoring` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: P3 slice 3, step 8 -- learner Q+A authoring, formulation coach, and in-review maintenance (spec_p3_reader_integration §9, design B step 8).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_authoring.py](../../../../../../src/learnloop/reader/reader_authoring.py) |
| Source lines | 651 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class AuthoringError(ValueError)` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 55) — Domain error for the reader-authoring service.
- `author_qa(repository: Repository, *, question: str, answer: str, source_id: str | None=None, revision_id: str | None=None, annotation_id: str | None=None, subject_id: str | None=None, depth_preset: str='remember_key_ideas', client_idempotency_key: str | None=None, family_title: str | None=None, root: Path | None=None, learning_object_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 83) — Persist a learner-authored Q+A card + pinned surface under an explicit commitment, in ONE confirmation (§9.1).
- `reader_practice_item_id(commitment_id: str) -> str` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 199) — The stable practice-item id of a reader question's card (its commitment's).
- `adopt_reference_questions(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 290) — Adopt reference-only reader questions whose passage an active LO now cites.
- `mint_ai_sibling(repository: Repository, *, family_id: str, predecessor_card_version_id: str, question: str, answer: str, scheduler_algorithm_version: str='fsrs6', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 415) — Mint a NON-learner-authored sibling for transfer (§9.1 last line).
- `coach_lint(*, question: str, answer: str, level: str='expert') -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 461) — Non-blocking formulation lint (§9.2).
- `record_coach_response(repository: Repository, *, commitment_id: str | None, level: str, response: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 498) — Record the learner's accept/edit/dismiss of a coach suggestion for corpus analysis (§9.2) -- NOT a live learned policy.
- `maintain(repository: Repository, *, action: str, lineage_id: str | None=None, from_card_version_id: str | None=None, to_card_version_id: str | None=None, prev_contract: Mapping[str, Any] | None=None, new_contract: Mapping[str, Any] | None=None, into_lineage_id: str | None=None, merged_card_version_id: str | None=None, split_card_version_id: str | None=None, forked_card_version_id: str | None=None, commitment_id: str | None=None, policy: str | None=None, bounds: Mapping[str, Any] | None=None, reviewed_edges: Any=(), scheduler_algorithm_version: str='fsrs6', root: Path | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 534) — In-review maintenance verbs (§9.3), each routed through the LANDED P1 lineage classifier / commitment machinery.

### Module constants

- `AUTHORING_SCHEMA_VERSION` ([src/learnloop/reader/reader_authoring.py](../../../../../../src/learnloop/reader/reader_authoring.py), line 51)
- `COACH_LEVELS` ([src/learnloop/reader/reader_authoring.py](../../../../../../src/learnloop/reader/reader_authoring.py), line 52)
- `MAINTENANCE_ACTIONS` ([src/learnloop/reader/reader_authoring.py](../../../../../../src/learnloop/reader/reader_authoring.py), line 531)

## Internal implementation anchors

- `_learner_card_contract(*, question: str, answer: str, target_ref: str | None, authorship: str, source_id: str | None, revision_id: str | None, annotation_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 59) — The card contract preserving the learner's EXACT surface (§9.1).
- `_span_anchor(repository: Repository, subject_id: str | None) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 172) — ``span:<extraction>/<span>`` (the reader's subject for a passage) -> ids.
- `_practice_learning_object(vault: LoadedVault, repository: Repository, *, learning_object_id: str | None, anchor: tuple[str, str] | None) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 182) — The active Learning Object a written question is filed under: the learner's explicit choice, else the first (sorted) active LO whose provenance cites the passage's section -- the same span->LO resolution tutor promotions use.
- `_adopt_into_practice(root: Path, repository: Repository, *, commitment_id: str, question: str, answer: str, subject_id: str | None, source_id: str | None, learning_object_id: str | None, clock: Clock | None, mechanism: str='reader_author_qa') -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 206)
- `_retire_adopted_items(root: Path, repository: Repository, *, commitment_id: str, clock: Clock | None) -> list[str]` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 354) — Retire the practice items a reader question (``reader_authored_qa`` commitment) was adopted into.
- `_requested_by_another_commitment(repository: Repository, practice_item_id: str, *, commitment_id: str) -> bool` ([source](../../../../../../src/learnloop/reader/reader_authoring.py), line 385) — True when a different, unretired commitment's head still targets the item.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `adopt_reference_questions`; statically calls `adopt_reference_questions`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `author_qa`, `coach_lint`, `maintain`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `author_item`, `retire_item`; calls `author_item`, `retire_item`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `add_target`, `change_depth_envelope`, `change_depth_policy`, `create_commitment`, `resolve_head`, `retire`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `BLOCK_SPAN_V1`, `format_block_span`, `parse_block_span`; calls `format_block_span`, `parse_block_span`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`, `log_interaction_event`; calls `canonical_hash`, `canonical_json`, `log_interaction_event`
- [[Reference/Modules/learnloop/substrate/card_lineage|learnloop.substrate.card_lineage]] — imports `module`; calls `append_minor_successor`, `classify_edit`, `fork_card`, `merge_lineage`, `split_lineage`, `start_lineage`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `REFERENCE_ADOPTION_MECHANISM`, `learning_object_servable`; calls `learning_object_servable`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_daily_loop_reader_authored_practice.py](../../../../../../tests/test_daily_loop_reader_authored_practice.py) — direct import
- [tests/test_daily_loop_reader_retire.py](../../../../../../tests/test_daily_loop_reader_retire.py) — direct import
  - `test_retiring_a_reader_question_retires_its_practice_item`
  - `test_retiring_a_reference_only_question_retires_nothing_else`
- [tests/test_daily_loop_reference_adoption.py](../../../../../../tests/test_daily_loop_reference_adoption.py) — direct import
  - `test_a_parked_lo_citing_the_passage_does_not_adopt`
  - `test_a_retired_reference_question_is_never_adopted`
  - `test_adoption_kill_switch_restores_baseline_and_keeps_adopted_cards`
  - `test_reference_question_becomes_practice_once_an_lo_cites_its_passage`
- [tests/test_integration_daily_loop_field.py](../../../../../../tests/test_integration_daily_loop_field.py) — direct import
  - `test_retired_reader_card_is_never_a_family_candidate`
- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — direct import
  - `test_journey7_tutor_exchange_to_durable`
- [tests/test_reader_adoption_ownership.py](../../../../../../tests/test_reader_adoption_ownership.py) — direct import
  - `test_crash_before_the_link_reuses_the_commitments_own_card`
- [tests/test_reader_authoring.py](../../../../../../tests/test_reader_authoring.py) — direct import
  - `test_ai_sibling_never_impersonates_learner_authorship`
  - `test_coach_lint_is_dismissible_and_never_blocks`
  - `test_coach_response_is_corpus_only_salience`
  - `test_cosmetic_edit_retains_state_only_through_classifier`
  - `test_material_edit_forks_without_blind_transfer`
  - `test_qa_confirms_once_idempotently`
  - `test_qa_persists_verbatim_before_ai_and_pins_under_commitment`
  - `test_qa_requires_both_question_and_answer`
  - `test_retirement_preserves_commitment_and_evidence`
  - `test_split_merge_spawn_create_lineage`

## Modification guidance

- Change reader authoring policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_authoring.py](../../../../../../src/learnloop/reader/reader_authoring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
