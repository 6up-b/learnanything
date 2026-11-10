---
title: "learnloop.intent.control"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/intent/control.py"
source_paths:
  - "src/learnloop/intent/control.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.intent"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.intent.control module"
  - "src/learnloop/intent/control.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-intent"
---

# `learnloop.intent.control`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.intent.control` exists within [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] to own the behavior summarized by its module contract: The single intent control (spec §5.1, §5.2): choose, preview, apply.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/intent/control.py](../../../../../../src/learnloop/intent/control.py) |
| Source lines | 518 |
| Owning package | [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class IntentControlError(ValueError)` ([source](../../../../../../src/learnloop/intent/control.py), line 70) — A choice the control cannot apply (unknown scope, nothing to act on).
- `class Scope` ([source](../../../../../../src/learnloop/intent/control.py), line 75)
  - `as_dict(self) -> dict[str, str]` (line 79; public)
- `class ScopeContents` ([source](../../../../../../src/learnloop/intent/control.py), line 84) — What a scope covers: its LO targets (or its one item) and every item.
  - `targets(self) -> list[dict[str, str]]` (line 92; public)
- `scope_contents(vault: Any, repository: Any, scope: Scope) -> ScopeContents` ([source](../../../../../../src/learnloop/intent/control.py), line 101) — A subject or source fans out to its active LOs (§5.1).
- `own_commitments(snapshots: Sequence[CommitmentSnapshot], scope: Scope) -> list[CommitmentSnapshot]` ([source](../../../../../../src/learnloop/intent/control.py), line 163) — The control's commitments for exactly this scope, newest choice last.
- `class Preview` ([source](../../../../../../src/learnloop/intent/control.py), line 187)
  - `as_dict(self) -> dict[str, Any]` (line 201; public)
- `preview(vault: Any, repository: Any, scope: Scope, choice: str, *, clock: Clock | None=None, snapshots: Sequence[CommitmentSnapshot] | None=None, contents: ScopeContents | None=None, cost: CostFunction | None=None) -> Preview` ([source](../../../../../../src/learnloop/intent/control.py), line 269)
- `current_choice(vault: Any, repository: Any, contents: ScopeContents, snapshots: Sequence[CommitmentSnapshot]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/control.py), line 350) — What the scope is set to now: its own commitment's choice, else the resolved intent of an LO or item (a request or a broader choice).
- `describe(vault: Any, repository: Any, scope: Scope, *, clock: Clock | None=None, cost: CostFunction | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/control.py), line 389) — The control's whole view: the current setting and every choice's preview.
- `class Applied` ([source](../../../../../../src/learnloop/intent/control.py), line 420)
  - `as_dict(self) -> dict[str, Any]` (line 426; public)
- `apply_choice(vault: Any, repository: Any, scope: Scope, choice: str, *, clock: Clock | None=None) -> Applied` ([source](../../../../../../src/learnloop/intent/control.py), line 431) — Write the choice (§5.1): create or version the scope's own commitment, or re-dispose it; "Check once" creates a fresh ``test_me_later``.

### Module constants

- `CHOICE_DOES` ([src/learnloop/intent/control.py](../../../../../../src/learnloop/intent/control.py), line 41)
- `CHOICE_PHRASE` ([src/learnloop/intent/control.py](../../../../../../src/learnloop/intent/control.py), line 54)

### Explicit exports

`__all__` declares:

- `Applied`
- `CHOICE_DOES`
- `CostFunction`
- `IntentControlError`
- `Preview`
- `Scope`
- `ScopeContents`
- `apply_choice`
- `current_choice`
- `describe`
- `own_commitments`
- `preview`
- `scope_contents`

## Internal implementation anchors

- `_source_extractions(repository: Any, source_id_or_extraction: str) -> list[str]` ([source](../../../../../../src/learnloop/intent/control.py), line 144) — A source scope's readings: the extraction itself, or every reading of the source's current revision (the library card names the source).
- `_item_title(item: Any) -> str` ([source](../../../../../../src/learnloop/intent/control.py), line 157)
- `_all_snapshots(repository: Any) -> list[CommitmentSnapshot]` ([source](../../../../../../src/learnloop/intent/control.py), line 178)
- `_virtual(contents: ScopeContents, choice: str, own: Sequence[CommitmentSnapshot], *, now_iso: str) -> CommitmentSnapshot` ([source](../../../../../../src/learnloop/intent/control.py), line 216) — The choice as a virtual newest commitment (the very rule the queue uses).
- `_plural(count: int, word: str) -> str` ([source](../../../../../../src/learnloop/intent/control.py), line 257)
- `_subject_phrase(contents: ScopeContents) -> str` ([source](../../../../../../src/learnloop/intent/control.py), line 261)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]] — imports `CostFunction`
- [[Reference/Modules/learnloop/intent/deadline|learnloop.intent.deadline]] — imports `IntentControlError`, `Scope`, `own_commitments`, `scope_contents`; statically calls `IntentControlError`, `own_commitments`, `scope_contents`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `Scope`, `own_commitments`; statically calls `Scope`, `own_commitments`
- [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]] — imports `IntentControlError`, `Scope`, `apply_choice`, `describe`; statically calls `Scope`, `apply_choice`, `describe`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `append_commitment_version`, `change_disposition`, `create_commitment`, `resolve_head`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/reader/recap|learnloop.reader.recap]] — imports `source_learning_objects`; calls `source_learning_objects`
- [[Reference/Modules/learnloop/scheduling/intent/model|learnloop.scheduling.intent.model]] — imports `CHOICES`, `CHOICE_DISPOSITION`, `CHOICE_LABEL`, `CHOICE_PRESET`, `ChoiceStamp`, `CommitmentSnapshot`, `INTENT_CONTROL_VIA`, `choice_for`; calls `ChoiceStamp`, `CommitmentSnapshot`, `choice_for`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `ItemIntent`, `Resolution`, `load_snapshots`; calls `Resolution`, `load_snapshots`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]], [[Reference/Modules/learnloop/intent/deadline|learnloop.intent.deadline]], [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]], [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_fakes.py](../../../../../../tests/ad23_fakes.py) — direct import
- [tests/intent_fakes.py](../../../../../../tests/intent_fakes.py) — direct import
- [tests/test_ad23_intent_compose.py](../../../../../../tests/test_ad23_intent_compose.py) — direct import
  - `test_f1_a_commitment_never_turns_the_slot_draw_off`
  - `test_f2_ad_never_serves_an_item_intent_withholds`
  - `test_property_ad_never_serves_or_clears_what_the_incumbent_withholds`
  - `test_the_incumbent_hands_ad_only_verdicts`
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f7_a_pause_after_the_plan_drops_its_pending_reading`
  - `test_f7_a_source_reads_only_under_learn_or_master`
  - `test_f8_a_deadline_covers_its_own_los_not_others_on_the_same_concept`
  - `test_f9_a_crash_between_publishing_and_linking_is_recovered_without_an_orphan`
  - `test_f9_concurrent_writers_publish_one_goal_and_one_link`
- [tests/test_intent_fix_round4.py](../../../../../../tests/test_intent_fix_round4.py) — direct import
  - `test_f15_the_probe_contract_carries_the_diagnostic_variant`
- [tests/test_intent_fix_round5.py](../../../../../../tests/test_intent_fix_round5.py) — direct import
  - `test_f17_moving_a_deadline_after_a_depth_change_updates_the_goal_target`
  - `test_f17_moving_a_deadline_at_the_same_depth_keeps_its_target`
- [tests/test_intent_fix_round6.py](../../../../../../tests/test_intent_fix_round6.py) — direct import
- [tests/test_intent_fix_round7.py](../../../../../../tests/test_intent_fix_round7.py) — direct import
- [tests/test_intent_goal_deadline.py](../../../../../../tests/test_intent_goal_deadline.py) — direct import
  - `test_a_deadline_creates_a_learner_goal_linked_by_goal_id`
  - `test_a_deadline_needs_an_active_depth_setting`
  - `test_linking_a_deadline_does_not_move_the_choice_time`
  - `test_moving_the_deadline_updates_the_same_goal`
- [tests/test_intent_plan.py](../../../../../../tests/test_intent_plan.py) — direct import
  - `test_admission_takes_learn_first_and_keep_adds_no_new_material`
- [tests/test_intent_resolution.py](../../../../../../tests/test_intent_resolution.py) — direct import
  - `test_the_consequence_line_equals_the_resolved_result`
  - `test_the_consequence_line_names_what_it_replaces`
  - `test_the_projected_cost_follows_the_recall_target`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f2_an_automatic_follow_up_never_lands_in_a_scope_the_learner_chose`
  - `test_f2_creation_refuses_an_item_the_learner_committed_since_the_search`
- [tests/test_reading_paths.py](../../../../../../tests/test_reading_paths.py) — direct import
  - `test_dl2_intent_preselects_the_depth_and_the_newer_setting_wins_without_writing_dl2`
  - `test_each_dl2_choice_maps_onto_a_depth_or_asks`

## Modification guidance

- Make changes here when the responsibility remains control within learnloop.intent; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/intent/control.py](../../../../../../src/learnloop/intent/control.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
