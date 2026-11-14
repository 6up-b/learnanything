---
title: "learnloop.diagnosis.text_gaps.actions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/text_gaps/actions.py"
source_paths:
  - "src/learnloop/diagnosis/text_gaps/actions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.text_gaps"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.text_gaps.actions module"
  - "src/learnloop/diagnosis/text_gaps/actions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-text-gaps"
---

# `learnloop.diagnosis.text_gaps.actions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.text_gaps.actions` exists within [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] to own the behavior summarized by its module contract: What a named gap does, each behind its own switch, each undoable by one tap.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/text_gaps/actions.py](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py) |
| Source lines | 650 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ActionOutcome` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 66)
- `day_start(now_iso: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 90)
- `prerequisite_graph(vault: LoadedVault, edges: Iterable[ConceptEdge] | None=None) -> dict[str, set[str]]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 97) — Concept -> concepts that build on it (``prerequisite`` edges and LO declarations).
- `edges_on_disk(vault: LoadedVault) -> list[ConceptEdge]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 114) — Every edge in ``concepts/relations.yaml`` as it is now, including the learner-text gap edges a switch keeps out of the loaded vault.
- `would_cycle(vault: LoadedVault, prerequisite_concept: str, dependent_concept: str, *, edges: Iterable[ConceptEdge] | None=None) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 124) — Would ``prerequisite -> dependent`` close a cycle (or point a concept at itself)?
- `declared_prerequisite(vault: LoadedVault, prerequisite_lo: str, dependent_lo: str) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 144)
- `edge_id_for(text: LearnerText, prerequisite_lo: str, dependent_lo: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 154) — The edge a learner text adds (deterministic: a retry finds it, F3).
- `add_prerequisite_edge(root: Path, vault: LoadedVault, *, prerequisite_lo: str, dependent_lo: str, text: LearnerText, rationale: str, clock: Clock | None=None, edge_id: str | None=None, origin: str='match') -> tuple[str | None, str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 160) — Write the edge; returns (edge id, status) with status ``added`` or why not.
- `delete_edge(root: Path, edge_id: str) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 208)
- `slug(text: str, *, limit: int=40) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 218)
- `creations_today(repository: Repository, *, now_iso: str) -> int` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 222) — Kept creations since today's UTC midnight (the daily cap counts these).
- `subject_for_creation(vault: LoadedVault, text: LearnerText) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 230) — The asking item's subject; never a new or an inferred one.
- `creation_ids(text: LearnerText, draft: Any, *, dependent_lo: str | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 242) — The concept, LO and edge ids a creation writes: derived from the text and the draft, so a retry of the same job names the same entities (F3).
- `write_created_prerequisite(root: Path, repository: Repository, *, draft: Any, subject_id: str, concept_id: str, learning_object_id: str, edge_id: str | None, dependent_lo: str | None, text: LearnerText, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 255) — Write the concept, the LO and (when there is an asking LO) the edge.
- `seed_from_question(root: Path, *, question_event_id: str, learning_object_id: str, tutor_client: Any, authoring_client: Any, clock: Clock | None=None) -> tuple[str | None, str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 319) — One practice item made from the question and the tutor's answer.
- `undo_creation(root: Path, repository: Repository, gap: Mapping[str, Any], *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 353) — The created LO goes dormant (its items are no longer served); its edge goes.
- `record_belief(vault: LoadedVault, repository: Repository, *, text: LearnerText, statement: str, matched: Mapping[str, Any] | None, clock: Clock | None=None) -> ActionOutcome` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 376) — A sighting on the matched entry, or a new holding-pen candidate.
- `not_this_belief(repository: Repository, gap: Mapping[str, Any], *, actor: str='learner', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 448) — "Not what I meant": a ``different`` verdict (``learner_card``, or ``owner``).
- `sooner_check_active(vault: LoadedVault) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 477)
- `advance_check(vault: LoadedVault, repository: Repository, *, learning_object_id: str, now_iso: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 482) — The advance row to write for a matched prerequisite, or None.
- `persist_check_advance(connection: Any, advance: Mapping[str, Any], *, gap_id: str, now_iso: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 524)
- `commitment_row(vault: LoadedVault, *, learning_object_id: str, practice_item_id: str | None, now_iso: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 528)
- `reversal_verdict(gap: Mapping[str, Any], reversal: str, *, actor: str, created_at: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 547) — The ``judgment_ledger`` row an undo is (F9): a ``no`` on ``prerequisite_needed``.
- `class UndoError(ValueError)` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 578)
- `reverse_gap(root: Path, repository: Repository, gap_id: str, reversal: str, *, actor: str='learner', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 582) — Apply one reversal (idempotent: a repeated tap changes nothing).

### Module constants

- `_SLUG` ([src/learnloop/diagnosis/text_gaps/actions.py](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 62)
- `REVERSALS` ([src/learnloop/diagnosis/text_gaps/actions.py](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 538)

### Explicit exports

`__all__` declares:

- `ActionOutcome`
- `REVERSALS`
- `UndoError`
- `add_prerequisite_edge`
- `advance_check`
- `commitment_row`
- `creation_ids`
- `creations_today`
- `day_start`
- `declared_prerequisite`
- `delete_edge`
- `edge_id_for`
- `edges_on_disk`
- `not_this_belief`
- `persist_check_advance`
- `prerequisite_graph`
- `record_belief`
- `reversal_verdict`
- `reverse_gap`
- `seed_from_question`
- `slug`
- `sooner_check_active`
- `subject_for_creation`
- `undo_creation`
- `would_cycle`
- `write_created_prerequisite`

## Internal implementation anchors

- `_iso(value) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 86)
- `_hash(*parts: Any) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 150)
- `_reversal_judge(actor: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py), line 444)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]] — imports `UndoError`, `reverse_gap`; statically calls `reverse_gap`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `module`; statically calls `ActionOutcome`, `add_prerequisite_edge`, `advance_check`, `commitment_row`, `creation_ids`, `creations_today`, `day_start`, `declared_prerequisite`, `edge_id_for`, `edges_on_disk`, `persist_check_advance`, `record_belief`, `seed_from_question`, `subject_for_creation`, `write_created_prerequisite`
- [[Reference/Modules/learnloop/goals/goal_lo|learnloop.goals.goal_lo]] — imports `module`; statically calls `_hash`, `creations_today`, `day_start`, `slug`
- [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]] — imports `UndoError`, `reverse_gap`; statically calls `reverse_gap`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `module`; calls `gap`, `insert_check_advance`, `insert_reversal`, `reversals`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `normalize_text`; calls `normalize_text`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]] — imports `created_today`; calls `created_today`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `LearnerText`, `NEEDED_TASK`, `PROVENANCE_MECHANISM`, `SAME_BELIEF_TASK`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/provenance|learnloop.diagnosis.text_gaps.provenance]] — imports `reading_record`; calls `reading_record`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `load_placement_state`, `placement_active`, `prerequisite_learning_objects`; calls `load_placement_state`, `placement_active`, `prerequisite_learning_objects`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `PromotionNoItemError`, `promote_tutor_question`; calls `promote_tutor_question`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `ConceptEdge`, `LoadedVault`, `RelationsFile`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `delete_concept_edge`, `upsert_concept`, `upsert_concept_edge`, `upsert_learning_object`; calls `delete_concept_edge`, `upsert_concept`, `upsert_concept_edge`, `upsert_learning_object`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`; calls `read_yaml`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]], [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]], [[Reference/Modules/learnloop/goals/goal_lo|learnloop.goals.goal_lo]], [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_input_provenance_helpers.py](../../../../../../../tests/diagnosis_input_provenance_helpers.py) — direct import
- [tests/mcp_world.py](../../../../../../../tests/mcp_world.py) — direct import
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
- [tests/test_followups_nov2_note_gap_unlinked.py](../../../../../../../tests/test_followups_nov2_note_gap_unlinked.py) — direct import
  - `test_unlinked_is_never_a_learners_manual_reversal`
- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_a_tutor_question_that_states_a_belief_reaches_the_holding_pen`
  - `test_an_edge_that_would_close_a_cycle_is_refused`
  - `test_an_undeclared_match_adds_an_edge_after_a_needed_yes_and_one_tap_undo_removes_it`
  - `test_undo_creation_puts_the_lo_away_and_removes_its_edge_and_commitment`
- [tests/test_learner_text_gaps_rereview.py](../../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f1_a_job_stopped_after_a_write_logs_the_write_as_failed_and_undoable`
  - `test_rr_f1_a_recorded_edge_is_finished_after_the_judges_the_chooser_and_the_switch_change`
  - `test_rr_f1_a_stuck_retry_finishes_the_recorded_creation_whatever_the_second_reading`
- [tests/test_learner_text_gaps_review.py](../../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f10_switching_edges_off_removes_their_effect_and_keeps_them_in_the_file`
  - `test_f10_the_cycle_is_rechecked_on_the_file_inside_the_lock`
  - `test_f3_a_creation_retried_after_a_failed_sync_writes_once_and_is_logged`
  - `test_f3_a_job_that_gives_up_after_writing_names_the_creation_and_the_owner_can_undo_it`
  - `test_f3_a_matched_edge_retried_after_a_failed_sync_is_recorded_and_undoable`
  - `test_f9_an_owner_not_what_i_meant_is_an_owner_verdict`
  - `test_f9_undoing_an_edge_or_a_creation_is_a_ledger_verdict`
- [tests/test_mcp_c1a_narrow.py](../../../../../../../tests/test_mcp_c1a_narrow.py) — direct import
  - `test_a_raw_generated_id_cannot_confirm_a_guessed_title`

## Modification guidance

- Change actions policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/text_gaps/actions.py](../../../../../../../src/learnloop/diagnosis/text_gaps/actions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
