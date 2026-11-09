---
title: "learnloop.hints.state"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/state.py"
source_paths:
  - "src/learnloop/hints/state.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.state module"
  - "src/learnloop/hints/state.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.state`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.state` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H2a: the typed state a hint is chosen and written from (spec §4.5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/state.py](../../../../../../src/learnloop/hints/state.py) |
| Source lines | 426 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class EarlierHint` ([source](../../../../../../src/learnloop/hints/state.py), line 48) — One help row of this attempt, as the chooser and writer read it.
  - `from_row(cls, row: Mapping[str, Any]) -> 'EarlierHint'` (line 75; public)
- `class HintState` ([source](../../../../../../src/learnloop/hints/state.py), line 96) — Everything a hint is chosen and written from; ``unread`` names the reads that failed (their fields are empty, never guessed).
  - `has_work(self) -> bool` (line 136; public)
  - `shown_hints(self) -> list[EarlierHint]` (line 140; public)
  - `map(self) -> dict[str, Any] | None` (line 144; public)
  - `authored_remaining(self, item: PracticeItem) -> list[int]` (line 147; public) — The item's authored hints not yet shown in this attempt (by the client's reveals or the service's own authored rows), in order.
  - `answered_discriminating_here(self) -> bool` (line 154; public) — A discriminating question was answered at this placement: on the practice screen, on this same work (its hash), since the placement is the draft's (§4.2 "one at a time").
  - `discriminate_answers(self) -> list[dict[str, Any]]` (line 162; public)
  - `decider_state(self) -> dict[str, Any]` (line 167; public) — The typed, short state the Decider reads (§4.5): never the draft's text, the reference solution or the map's states (§7.4).
  - `state_hash(self) -> str` (line 201; public)
  - `record(self) -> dict[str, Any]` (line 204; public)
- `work_digest(work_md: str) -> str` ([source](../../../../../../src/learnloop/hints/state.py), line 219)
- `checkpoint_draft(repository: Repository, session_id: str, practice_item_id: str) -> str | None` ([source](../../../../../../src/learnloop/hints/state.py), line 223) — The session checkpoint's draft of this item (saved within 350 ms of typing; the client flushes it before asking), or None.
- `assemble_state(vault: LoadedVault, repository: Repository, item: PracticeItem, *, session_id: str, submission_id: str, work_md: str | None, seconds_on_item: float | None=None, now_iso: str | None=None, map_record: dict[str, Any] | None=None, map_loaded: bool=False) -> HintState` ([source](../../../../../../src/learnloop/hints/state.py), line 242) — The hint state for one request (local reads only).
- `rivals_payload(rivals: Sequence[Rival]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/hints/state.py), line 413)

### Module constants

- `LOG` ([src/learnloop/hints/state.py](../../../../../../src/learnloop/hints/state.py), line 40)
- `STATE_VERSION` ([src/learnloop/hints/state.py](../../../../../../src/learnloop/hints/state.py), line 42)
- `RECENT_ATTEMPTS` ([src/learnloop/hints/state.py](../../../../../../src/learnloop/hints/state.py), line 44)

### Explicit exports

`__all__` declares:

- `EarlierHint`
- `HintState`
- `RECENT_ATTEMPTS`
- `STATE_VERSION`
- `assemble_state`
- `checkpoint_draft`
- `rivals_payload`
- `work_digest`

## Internal implementation anchors

- `_round(value: Any) -> float | None` ([source](../../../../../../src/learnloop/hints/state.py), line 215)
- `_seconds_between(earlier: str | None, later: str) -> float | None` ([source](../../../../../../src/learnloop/hints/state.py), line 233)
- `_read_earlier(repository: Repository, state: HintState, submission_id: str) -> None` ([source](../../../../../../src/learnloop/hints/state.py), line 296)
- `_read_placement(vault: LoadedVault, repository: Repository, state: HintState, now: str) -> None` ([source](../../../../../../src/learnloop/hints/state.py), line 310)
- `_read_prediction(vault: LoadedVault, repository: Repository, item: PracticeItem, state: HintState, now: str) -> None` ([source](../../../../../../src/learnloop/hints/state.py), line 318)
- `_read_facets(repository: Repository, state: HintState) -> None` ([source](../../../../../../src/learnloop/hints/state.py), line 331)
- `_assisted(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/hints/state.py), line 350)
- `_read_attempts(repository: Repository, item: PracticeItem, state: HintState) -> None` ([source](../../../../../../src/learnloop/hints/state.py), line 355)
- `_read_map(vault: LoadedVault, repository: Repository, item: PracticeItem, state: HintState) -> None` ([source](../../../../../../src/learnloop/hints/state.py), line 370)
- `_read_route_preference(state: HintState) -> None` ([source](../../../../../../src/learnloop/hints/state.py), line 376)
- `_read_examples(vault: LoadedVault, repository: Repository, item: PracticeItem, state: HintState) -> None` ([source](../../../../../../src/learnloop/hints/state.py), line 386) — A worked example at hand: the map was seeded with the learner's own book's worked examples (T6's spans, consumed: their texts are read back locally, never retrieved again); another instance: a family sibling.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `HintState`
- [[Reference/Modules/learnloop/hints/options|learnloop.hints.options]] — imports `EarlierHint`, `HintState`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `EarlierHint`, `HintState`, `assemble_state`, `rivals_payload`; statically calls `assemble_state`, `rivals_payload`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `HintState`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `assemble_state`; statically calls `assemble_state`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `module`; calls `submission_assists`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`; calls `blocks_by_key`
- [[Reference/Modules/learnloop/hints/discriminating|learnloop.hints.discriminating]] — imports `Rival`, `open_rivals`; calls `open_rivals`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `current_map`; calls `current_map`
- [[Reference/Modules/learnloop/placement/predictor|learnloop.placement.predictor]] — imports `active_predictor`; calls `active_predictor`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `load_placement_state`; calls `load_placement_state`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]], [[Reference/Modules/learnloop/hints/options|learnloop.hints.options]], [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]], [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_hint_contracts.py](../../../../../../tests/test_hint_contracts.py) — direct import
  - `test_a_waypoint_that_misses_the_chosen_horizon_is_caught`
  - `test_no_waypoint_or_label_carries_a_leak_nodes_state`
- [tests/test_hint_discriminating.py](../../../../../../tests/test_hint_discriminating.py) — direct import
  - `test_offered_only_with_two_open_rivals`
  - `test_on_new_work_a_new_discriminating_question_may_be_offered`
- [tests/test_hint_h2a_review.py](../../../../../../tests/test_hint_h2a_review.py) — direct import
  - `test_f2_a_smaller_step_toward_a_far_waypoint_targets_the_adjacent_node_on_the_way`
  - `test_f3_a_checkpoint_after_the_first_questionable_point_is_refused`
  - `test_f3_repeated_text_is_placed_at_its_first_occurrence`
  - `test_f4_an_alternative_learner_route_is_not_swapped_for_another_alternative`
  - `test_f8_a_book_origin_on_an_unverified_passage_is_refused`
  - `test_f8_the_writer_is_told_its_passages_are_unverified`
- [tests/test_hint_h2a_review_round4.py](../../../../../../tests/test_hint_h2a_review_round4.py) — direct import
  - `test_r4_the_reference_route_rule_for_every_kind_and_no_map_unchanged`
- [tests/test_hint_kill_switch.py](../../../../../../tests/test_hint_kill_switch.py) — direct import
  - `test_h2b_set_help_style_writes_the_one_stored_preference_and_reloads`
- [tests/test_hint_replies.py](../../../../../../tests/test_hint_replies.py) — direct import
  - `test_learner_route_keeps_the_learners_route_and_never_targets_the_reference`
- [tests/test_hint_service.py](../../../../../../tests/test_hint_service.py) — direct import
  - `test_the_state_reads_the_draft_rivals_map_and_this_attempts_hints`
  - `test_with_no_draft_in_the_request_the_session_checkpoints_draft_is_read`

## Modification guidance

- Make changes here when the responsibility remains state within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/state.py](../../../../../../src/learnloop/hints/state.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
