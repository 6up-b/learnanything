---
title: "learnloop.followup_run.marks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_run/marks.py"
source_paths:
  - "src/learnloop/followup_run/marks.py"
source_commit: "6c4406ba4abd68e81355794a10ee1946f37fa4c6"
source_commit_timestamp: "2026-11-04T20:45:22-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_run"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.followup_run.marks module"
  - "src/learnloop/followup_run/marks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-run"
---

# `learnloop.followup_run.marks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_run.marks` exists within [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] to own the behavior summarized by its module contract: What the screen reads and writes of a learner's marks (spec §7; spec_router_objective_v1 §4 row 6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_run/marks.py](../../../../../../src/learnloop/followup_run/marks.py) |
| Source lines | 353 |
| Owning package | [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6c4406ba4abd68e81355794a10ee1946f37fa4c6` |
| Commit timestamp | `2026-11-04T20:45:22-05:00` |

## Public API

- `class MarkRefused(ValueError)` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 47) — A mark that names nothing on this attempt's list, or a list that is still held.
- `class MarkableList` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 52) — One attempt's list of possible causes, in the order it is displayed.
  - `order(self) -> list[str]` (line 65; public)
- `claim_checked_ids_of(causal_feedback: Mapping[str, Any] | None) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 102) — The cause ids of a feedback bundle's ``causalFeedback`` (the camel-cased ``claim_checked_feedback`` the bundle already computed), as ``_claim_checked_ids`` reads them.
- `markable_list(vault: Any, repository: Repository, attempt_id: str, *, claim_checked_ids: Sequence[str] | None=None) -> MarkableList | None` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 109) — The attempt's list, or None with no concrete cause to mark.
- `view(vault: Any, repository: Repository, attempt_id: str, *, surface: str=SURFACE_FEEDBACK, claim_checked_ids: Sequence[str] | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 148) — What the panel shows for one attempt, or None: the switch is off, the list is held, or there is nothing to mark.
- `bundle_view(vault: Any, repository: Repository, attempt_id: str, *, claim_checked_ids: Sequence[str] | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 183) — §3 step 8: an answer to a generated probe shows the earlier miss's list, since that is what its answer was about.
- `record_exposure(vault: Any, repository: Repository, *, attempt_id: str, surface: str, hypothesis_version_ids: Sequence[str], shown_at: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 200) — One display, from the client's display event, in the order as displayed.
- `record_inspector_exposure(vault: Any, repository: Repository, attempt_id: str) -> str | None` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 250) — The inspector shows every cause of the attempt, held or not.
- `record_mark(vault: Any, repository: Repository, *, attempt_id: str, mark: str, hypothesis_version_id: str | None=None, free_text: str | None=None, surface: str=SURFACE_FEEDBACK, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 282) — Append one mark and return the panel's new read; None with the switch off.

### Module constants

- `SURFACE_FEEDBACK` ([src/learnloop/followup_run/marks.py](../../../../../../src/learnloop/followup_run/marks.py), line 36)
- `SURFACE_PROBE_FEEDBACK` ([src/learnloop/followup_run/marks.py](../../../../../../src/learnloop/followup_run/marks.py), line 37)
- `SURFACE_INSPECTOR` ([src/learnloop/followup_run/marks.py](../../../../../../src/learnloop/followup_run/marks.py), line 40)
- `LIST_SURFACES` ([src/learnloop/followup_run/marks.py](../../../../../../src/learnloop/followup_run/marks.py), line 42)
- `MARKS_SURFACES` ([src/learnloop/followup_run/marks.py](../../../../../../src/learnloop/followup_run/marks.py), line 43)
- `EXPOSURE_SURFACES` ([src/learnloop/followup_run/marks.py](../../../../../../src/learnloop/followup_run/marks.py), line 44)

### Explicit exports

`__all__` declares:

- `EXPOSURE_SURFACES`
- `LIST_SURFACES`
- `MARKS_SURFACES`
- `MarkRefused`
- `MarkableList`
- `SURFACE_FEEDBACK`
- `SURFACE_INSPECTOR`
- `SURFACE_PROBE_FEEDBACK`
- `bundle_view`
- `markable_list`
- `record_exposure`
- `record_inspector_exposure`
- `record_mark`
- `view`

## Internal implementation anchors

- `_chosen_factor(repository: Repository, attempt_id: str, workflow: Mapping[str, Any] | None) -> tuple[str | None, tuple[str, ...]]` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 69) — The factor whose causes are listed, and those causes: the workflow's, whatever became of it (its probe tested those very versions), else the newest factor still open or resolved.
- `_claim_checked_ids(vault: Any, repository: Repository, attempt_id: str) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 88) — With no factor, exactly the causes the feedback's own overlay would show (it fails closed on a receipt that doesn't permit learner feedback).
- `_state(repository: Repository, listed: MarkableList) -> dict[str, Any]` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 143)
- `_readable_time(value: str | None) -> bool` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 263)
- `_exposure_refusal(repository: Repository, attempt_id: str, surface: str, ids: Sequence[str]) -> str | None` ([source](../../../../../../src/learnloop/followup_run/marks.py), line 270)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `bundle_view`, `claim_checked_ids_of`; statically calls `bundle_view`, `claim_checked_ids_of`
- [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]] — imports `MarkRefused`, `record_exposure`, `record_mark`; statically calls `record_exposure`, `record_mark`
- [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]] — imports `record_inspector_exposure`; statically calls `record_inspector_exposure`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/hypothesis_marks|learnloop.db.stores.hypothesis_marks]] — imports `module`; calls `insert_exposure`, `insert_mark`, `marks_for_attempt`, `present`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `claim_checked_feedback`; calls `claim_checked_feedback`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `diagnosis_status`; calls `diagnosis_status`
- [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] — imports `concrete_rivals`; calls `concrete_rivals`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `is_holding`, `source_of_probe_attempt`; calls `is_holding`, `source_of_probe_attempt`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `hypothesis_marks_on`; calls `hypothesis_marks_on`
- [[Reference/Modules/learnloop/followup_serve/marks|learnloop.followup_serve.marks]] — imports `module`; calls `display_order`, `latest_marks`, `probe_state`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; calls `attempt_workflow`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]], [[Reference/Modules/learnloop_sidecar/handlers/followup|learnloop_sidecar.handlers.followup]], [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_fg1c_codex_review.py](../../../../../../tests/test_followup_fg1c_codex_review.py) — direct import
  - `test_f1_only_the_causes_a_context_still_shows_are_folded`
- [tests/test_followup_fg1c_r1_exposure_independence.py](../../../../../../tests/test_followup_fg1c_r1_exposure_independence.py) — direct import
  - `test_every_surface_that_sends_a_display_event_reaches_it`
- [tests/test_followup_fg1d_panel_read.py](../../../../../../tests/test_followup_fg1d_panel_read.py) — direct import
  - `test_every_panel_is_byte_identical_to_the_recomputing_read`
  - `test_the_exposure_after_the_panel_is_the_one_the_recomputing_read_gives`
- [tests/test_hypothesis_marks.py](../../../../../../tests/test_hypothesis_marks.py) — direct import
  - `test_a_live_diagnosis_is_stored_by_its_id`
  - `test_a_marks_read_that_fails_costs_the_panel_and_not_the_feedback`
  - `test_a_practice_lane_miss_keeps_the_cards_tap`
  - `test_the_blind_grader_never_sees_marks_and_the_diagnoser_does`
  - `test_the_diagnoser_reads_only_marks_made_before_the_attempt_it_is_on`
  - `test_the_list_keeps_its_order_on_every_read_and_a_new_version_keeps_its_place`
  - `test_the_switch_off_keeps_the_diagnosers_context_as_it_was_whatever_rows_exist`
  - `test_with_no_causes_on_the_attempt_the_bundle_has_no_key`
- [tests/test_hypothesis_marks_context.py](../../../../../../tests/test_hypothesis_marks_context.py) — direct import
  - `test_the_report_measures_marks_against_delayed_performance`

## Modification guidance

- Make changes here when the responsibility remains marks within learnloop.followup_run; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_run/marks.py](../../../../../../src/learnloop/followup_run/marks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
