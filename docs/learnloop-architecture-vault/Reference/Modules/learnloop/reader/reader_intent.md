---
title: "learnloop.reader.reader_intent"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_intent.py"
source_paths:
  - "src/learnloop/reader/reader_intent.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_intent module"
  - "src/learnloop/reader/reader_intent.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_intent`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_intent` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader workbench RW1b: the intent box and its router (spec_reader_workbench_v1 §4.2, §4.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py) |
| Source lines | 834 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class IntentAction` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 119) — One palette action: its id, intention, words and effect.
  - `intention(self) -> str | None` (line 136; public)
  - `as_dict(self) -> dict[str, Any]` (line 139; public)
- `class Availability` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 263) — What exists when the box opens: the switches and landed phases.
  - `from_config(cls, config: Any, *, model: bool=True, notes: bool=False) -> 'Availability'` (line 289; public)
  - `allows(self, action: IntentAction) -> bool` (line 315; public)
- `available_actions(available: Availability) -> list[IntentAction]` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 333)
- `question_set_version(available: Availability) -> str` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 340) — The routing's question-set version: RW5d's while show me is on (the figure option's text differs), else RW1b's, so every other routing hashes as before.
- `palette(available: Availability) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 350) — The palette, grouped by intention; a group with nothing in it is absent.
- `choice_question(actions: Sequence[IntentAction]) -> ChoiceQuestion` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 363)
- `decider_state(text: str, quote: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 375)
- `class Routing` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 384) — One routing: what the Reader runs, and why.
  - `intention(self) -> str | None` (line 402; public)
  - `as_dict(self) -> dict[str, Any]` (line 406; public)
- `calls_today(repository: Any, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 436) — The route's Decider requests admitted since today's UTC midnight: its reserved allowance (a reservation is made before the request is sent, so failed and unfinished calls count; one given back unsent does not).
- `speculation_limit(config: Any) -> int` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 478) — How many of the day's requests speculation may use (80% of the cap).
- `speculation_room(config: Any, repository: Any, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 484) — Whether a speculative routing may be made now (switch on, under 80% of the day).
- `input_hash(text: str, quote: str, options: Sequence[str], *, question_set: str=QUESTION_SET_VERSION) -> str` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 493)
- `selection_key(extraction_id: str, span_ids: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 498)
- `route(root: Any, config: Any, repository: Any, *, text: str, quote: str, extraction_id: str, span_ids: Sequence[str], available: Availability, speculative: bool=False, client_factory: Callable[[], Any] | None=None, clock: Clock | None=None, routing_id: str | None=None) -> Routing` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 528) — Route one intent-box text to a palette action (spec §4.2).
- `record_fate(repository: Any, judgment_id: str, fate: str, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 669) — A speculative routing was used (Enter took it) or discarded (the text changed, the box closed): one superseding ``decider`` row with the fate in its rationale.
- `record_correction(repository: Any, judgment_id: str, chosen: str | None, *, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 696) — The learner's "change": the action they picked instead (or ``cancelled``), a ``learner_card`` row superseding the routing's head.
- `revert_capture(repository: Any, *, annotation_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 727) — Undo the capture a routed action made, because the learner pressed "change" (spec §4.2: "change cancels it"; Codex review of RW1b, F4): the annotation is tombstoned (a delete intent, never a hard delete), the commitment a commit preset created with it is retired, and its synthes…

### Module constants

- `ROUTE` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 75)
- `TASK` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 76)
- `RECEIPT_OWNER` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 77)
- `QUESTION_SET_VERSION` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 79)
- `SHOW_ME_QUESTION_SET_VERSION` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 82)
- `COMPARE_QUESTION_SET_SUFFIX` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 85)
- `QUESTION_NAME` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 86)
- `SPECULATION_SHARE` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 88)
- `TEXT_LIMIT` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 90)
- `QUOTE_LIMIT` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 91)
- `LEFT_KIND` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 94)
- `RIGHT_KIND` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 95)
- `ALLOWANCE_TASK` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 99)
- `ALLOWANCE_LEASE_SECONDS` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 100)
- `INTENTIONS` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 103)
- `GROUP_ORDER` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 104)
- `GROUP_LABELS` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 105)
- `FATES` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 115)
- `ACTIONS` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 161)
- `ACTIONS_BY_ID` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 251)
- `DEFAULT_ACTION` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 253)
- `ANCHOR_FREE_ACTIONS` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 256)
- `SHOW_ME_LABEL` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 324)
- `SHOW_ME_CLAUSE` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 325)
- `REVERTIBLE_EFFECTS` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 720)
- `REVERT_REASON` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 723)
- `_TERMINAL_REQUESTS` ([src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py), line 724)

### Explicit exports

`__all__` declares:

- `ACTIONS`
- `ANCHOR_FREE_ACTIONS`
- `ACTIONS_BY_ID`
- `Availability`
- `DEFAULT_ACTION`
- `FATES`
- `GROUP_ORDER`
- `INTENTIONS`
- `IntentAction`
- `QUESTION_SET_VERSION`
- `REVERTIBLE_EFFECTS`
- `ROUTE`
- `Routing`
- `SPECULATION_SHARE`
- `TASK`
- `available_actions`
- `question_set_version`
- `calls_today`
- `choice_question`
- `decider_state`
- `palette`
- `record_correction`
- `record_fate`
- `revert_capture`
- `route`
- `speculation_limit`
- `speculation_room`

## Internal implementation anchors

- `_ask(mode: str, label: str, describe: str) -> IntentAction` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 144)
- `_preset(preset: str, group: str, label: str, describe: str, *, model: bool=True) -> IntentAction` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 148)
- `_active(style: str, group: str, label: str, describe: str) -> IntentAction` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 152)
- `_show_me(action: IntentAction) -> IntentAction` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 328)
- `_day(clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 418)
- `_allowance_prefix(day: str) -> str` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 422)
- `_used(connection: Any, day: str) -> int` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 426)
- `_reserve(repository: Any, *, routing_id: str, limit: int, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 445) — Claim one request of the day's allowance, or None when ``limit`` is reached.
- `_settle_reservation(repository: Any, key: str, *, routing_id: str, judgment_id: str | None, sent: bool, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 464) — A request sent keeps its reservation (``done``, naming its ledger row); one refused before sending (the spend gate) gives it back.
- `_client(root: Any, config: Any) -> Any` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 502)
- `_append(repository: Any, routing: Routing, *, verdict: str, model: str, rationale: Mapping[str, Any], right_id: str, left_id: str | None=None, judge: str='decider', supersedes_id: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 512)
- `_row(repository: Any, judgment_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 630)
- `_head(repository: Any, row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 640) — The head of this routing's own chain: the root row, then each row that supersedes the one before (F3: never another routing's row, even one on the same words).
- `_rationale(raw: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_intent.py), line 661)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `module`; statically calls `Routing`, `palette`, `record_correction`, `record_fate`, `revert_capture`, `route`, `speculation_room`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`, `choice_probabilities`; calls `ChoiceQuestion`, `choice_probabilities`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_disposition`, `retire`
- [[Reference/Modules/learnloop/db/stores/judgment_claims|learnloop.db.stores.judgment_claims]] — imports `claim_work`, `complete_claim`, `release_claim`; calls `claim_work`, `complete_claim`, `release_claim`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `ask_decider`; calls `ask_decider`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `delete_intent_annotation`; calls `delete_intent_annotation`
- [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]] — imports `module`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `module`; calls `rebind_completed`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `math`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reader_intent_helpers.py](../../../../../../tests/reader_intent_helpers.py) — direct import
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
- [tests/test_reader_ca3_compare_anywhere.py](../../../../../../tests/test_reader_ca3_compare_anywhere.py) — direct import
  - `test_the_intent_question_set_moves_only_with_the_verb`
- [tests/test_reader_find_sources_callers.py](../../../../../../tests/test_reader_find_sources_callers.py) — direct import
  - `test_with_the_sources_spec_absent_the_library_ask_is_absent`
- [tests/test_reader_intent.py](../../../../../../tests/test_reader_intent.py) — direct import
  - `test_a_decider_that_cannot_answer_routes_to_ask`
  - `test_a_held_out_passage_is_never_routed`
  - `test_a_later_day_counts_its_own_calls`
  - `test_a_speculative_routings_fate_is_a_superseding_row`
  - `test_a_tie_names_no_action_and_routes_to_ask`
  - `test_an_empty_enter_asks_with_no_model_call`
  - `test_an_empty_enter_through_the_sidecar_writes_nothing`
  - `test_an_unready_route_is_never_a_chat_fallback`
  - `test_change_records_the_learners_correction`
  - `test_the_decider_picks_the_action_and_the_row_is_ledgered`
  - `test_the_options_are_only_the_actions_that_exist`
- [tests/test_reader_intentions.py](../../../../../../tests/test_reader_intentions.py) — direct import
  - `test_actions_of_phases_not_landed_are_absent`
  - `test_grouping_changes_no_presets_effect`
  - `test_nothing_in_todays_notes_palette_is_missing`
  - `test_rw4a_adds_orient_and_transfer_library_asks_only_with_its_switch`
  - `test_switches_remove_their_actions`
  - `test_the_box_routes_on_every_source_kind`
  - `test_the_notes_pane_offers_only_the_anchor_free_actions`
  - `test_the_palette_is_grouped_by_intention_with_mark_last`
  - `test_the_readers_test_fixture_is_the_sidecars_palette`
- [tests/test_reader_rw1b_final_verify.py](../../../../../../tests/test_reader_rw1b_final_verify.py) — direct import
  - `test_f14_a_revert_after_an_undone_revert_converts_to_no_work`
  - `test_f14_revert_restore_revert_restore_converts`
  - `test_f14_revert_restore_revert_then_a_retried_conversion_enqueues_nothing`
  - `test_f16_a_running_revival_lands_on_the_reviving_capture`
  - `test_f16_a_same_instruction_revival_rebinds_to_the_reviving_capture`
  - `test_f16_captures_with_different_instructions_never_share_or_revive`
  - `test_f16_reverting_the_bound_capture_of_shared_work_rebinds_it`
- [tests/test_reader_rw1b_fix_round4.py](../../../../../../tests/test_reader_rw1b_fix_round4.py) — direct import
  - `test_a_revert_after_the_binding_read_still_maps_the_holder`
  - `test_a_revert_of_a_completed_request_nobody_else_holds_leaves_it`
  - `test_a_revert_of_a_completed_shared_request_moves_its_commitment_mapping`
  - `test_b_a_revert_after_the_stopped_check_moves_the_mapping`
  - `test_c_a_revival_during_landing_ends_mapped_to_the_reviving_capture`
  - `test_d_a_compatible_no_note_revival_keeps_its_exact_key`
  - `test_d_a_legacy_rekey_that_collides_takes_a_key_no_enqueue_computes`
  - `test_d_a_no_note_capture_never_revives_a_legacy_request_asking_something_else`
- [tests/test_reader_rw1b_rereview.py](../../../../../../tests/test_reader_rw1b_rereview.py) — direct import
  - `test_f14_a_capture_reverted_before_its_drain_enqueues_nothing`
  - `test_f14_a_failed_conversion_retried_after_the_revert_enqueues_nothing`
  - `test_f14_a_revert_racing_a_drain_waits_for_it_and_cancels_what_it_enqueued`
  - `test_f15_a_later_capture_keeps_running_work_its_revert_flagged`
  - `test_f15_a_later_capture_revives_cancelled_work`
  - `test_f15_reverting_the_original_capture_keeps_work_another_capture_holds`
  - `test_f15_reverting_the_sharing_capture_keeps_the_original_and_cancels_last`
- [tests/test_reader_rw1b_review.py](../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f2_an_unavailable_decider_spends_no_allowance`
  - `test_f2_two_routings_racing_for_the_last_call_admit_one`
  - `test_f2_two_speculations_racing_for_the_last_speculative_call_admit_one`
  - `test_f3_identical_routings_keep_their_own_fates_and_corrections`
- [tests/test_rw4_kill_switches.py](../../../../../../tests/test_rw4_kill_switches.py) — direct import
  - `test_every_rw4a_rpc_refuses_and_writes_nothing`

## Modification guidance

- Change reader intent policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_intent.py](../../../../../../src/learnloop/reader/reader_intent.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
