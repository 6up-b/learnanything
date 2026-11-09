---
title: "learnloop_sidecar.handlers.sessions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/sessions.py"
source_paths:
  - "src/learnloop_sidecar/handlers/sessions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop_sidecar.handlers.sessions module"
  - "src/learnloop_sidecar/handlers/sessions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.sessions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps sessions behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `SessionStartInput`, `SessionIdInput`, `AdoptSessionInput`, `SessionCheckpointInput`, `AskAvailabilityInput`, `record_ask_availability`, `start_session`, `adopt_session` and 24 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/sessions.py](../../../../../../src/learnloop_sidecar/handlers/sessions.py) |
| Source lines | 1069 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class SessionStartInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 24)
- `class SessionIdInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 36)
- `class AdoptSessionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 40)
- `class SessionCheckpointInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 46)
- `class AskAvailabilityInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 60)
- `record_ask_availability(ctx: SidecarContext, params: AskAvailabilityInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 68) — RO0 row 3 (spec_router_objective_v1 §4): the practice screen says Ask's availability changed on an item it shows (a diagnostic check's contract loaded, say).
- `start_session(ctx: SidecarContext, params: SessionStartInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 81)
- `adopt_session(ctx: SidecarContext, params: AdoptSessionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 117) — Move the open session to the request's device (§6.5), keeping its id, its checkpoint, its caps and its offer binding.
- `get_start_summary(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 146) — What Start shows before a session begins (daily-loop DL0).
- `get_session(ctx: SidecarContext, params: SessionIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 169)
- `update_session_checkpoint(ctx: SidecarContext, params: SessionCheckpointInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 178)
- `clear_session_checkpoint(ctx: SidecarContext, params: SessionIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 185)
- `class SessionEndInput(SessionIdInput)` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 192)
- `end_session(ctx: SidecarContext, params: SessionEndInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 199)
- `patch_checkpoint(repository, params: SessionCheckpointInput, *, device_id: str | None, plan_presentation_id: Any=_KEEP, self_grade_disclosure: Any=_KEEP, first_hint_progress: Any=_KEEP, hint_seen: Any=_KEEP, page_seen: Any=_KEEP, earlier_opened: Any=_KEEP) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 310) — Merge ``params`` into the session's checkpoint.
- `ownership_error(error: SessionOwnershipError) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 415) — The sidecar's form of a refused session operation (mobile PR-4).
- `owned_session_errors() -> Iterator[None]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 430)
- `require_owned_session(ctx: SidecarContext, repository, session_id: str, *, expected_generation: int | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 444) — The open session, if the request's device owns it (mobile PR-4, §6.5).
- `refuse_moved_session(ctx: SidecarContext, repository, session_id: str | None) -> Callable[[], None] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 531) — Mobile v2 §5.6 (PR-4's open list, mobile-m2a §3 item 9): a session-keyed write outside practice (a plan step, a tutor question, a lesson suggestion's answer) from a device that does not own the session is refused with ``session_moved``, as practice writes are.
- `phone_claim_owner(ctx: SidecarContext, repository, session_id: str | None, *, phone_probes: bool) -> Callable[[], None] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 578) — Mobile v2 V3 (Codex review of V3, F1): what a phone door checks in the transaction that burns a generated probe (``serving.refuse_generated_probe_door``'s ``owned``): the named session is this device's, or, for a sessionless door, no other device owns the open session (:func:`re…
- `draft_page_seen(practice: dict[str, Any] | None, submission_id: str | None) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 743) — Reader CA1: whether a saved draft records the original page opened before Submit under ``submission_id``.
- `draft_earlier_opened(checkpoint: dict[str, Any] | None, *, practice_item_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 767) — Whether the session's saved draft on ``practice_item_id`` opened an earlier attempt's help under its current retry key (Codex review F1).
- `draft_earlier_uncarried(checkpoint: dict[str, Any] | None, *, practice_item_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 775) — Whether the draft's opening is not marked carried yet (opened, and :func:`carry_earlier_opened` has not recorded the first problem it moved onto).
- `carry_earlier_opened(repository, session_id: str | None, *, practice_item_id: str, workbench_session_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 785) — Codex re-review F1: the practice screen hands its draft to the steps, so the opening's one hint moves onto the unfinished workbench, where it lives as a carried answer-box hint (``workbench_sessions.carried_hints``, durable whatever the session's later drafts or sessions).
- `draft_hint_seen(practice: dict[str, Any] | None, submission_id: str | None) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 815) — Whether a saved draft records a hint seen under ``submission_id``.
- `draft_first_hint_progress(practice: dict[str, Any] | None, submission_id: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 824) — The marker a saved draft holds for ``submission_id``, else None.
- `draft_plan_presentation(checkpoint: dict[str, Any] | None, *, practice_item_id: str, submission_id: str | None) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 836) — The presentation a saved draft named, when ``submission_id`` is that draft's retry key on ``practice_item_id`` (router R2a, review F5), else None.
- `checkpoint_plan_presentation(checkpoint: dict[str, Any] | None, *, practice_item_id: str) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 854) — The presentation the checkpoint's saved draft of ``practice_item_id`` answers, under the draft's own retry key, or None (mobile v2 J6; Codex re-review of V2, F5).
- `with_self_grade_disclosure(focus: dict[str, Any] | None, disclosure: dict[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 902) — Store (or, with None, drop) the frozen self-grade trace in the practice envelope.
- `draft_self_grade_disclosure(checkpoint: dict[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 927) — The trace a plain self-grade froze for the checkpoint's draft, or None.
- `settle_self_grade_disclosure(repository, checkpoint: dict[str, Any] | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 965) — The draft a plain self-grade showed a full answer for is done with: debit the reveal ledger (``reveal_ledger.record_self_grade_disclosure_reveal``).
- `clear_checkpoint(repository, session_id: str) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 995) — Clear the session's checkpoint, settling a self-grade disclosure first.

### Module constants

- `_ASSISTED_ATTEMPT_TYPES` ([src/learnloop_sidecar/handlers/sessions.py](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 241)
- `_KEEP` ([src/learnloop_sidecar/handlers/sessions.py](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 303)
- `KEEP_MARKER` ([src/learnloop_sidecar/handlers/sessions.py](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 305)
- `KEEP_HINT_SEEN` ([src/learnloop_sidecar/handlers/sessions.py](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 306)
- `KEEP_EARLIER_OPENED` ([src/learnloop_sidecar/handlers/sessions.py](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 307)
- `_MOVED_KEYS` ([src/learnloop_sidecar/handlers/sessions.py](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 471)
- `_SELF_GRADE_DISCLOSURE_KEY` ([src/learnloop_sidecar/handlers/sessions.py](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 899)

## Internal implementation anchors

- `_session_topics(vault, repository, session_id: str, demonstrated_attempt_ids) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 244) — The topics the session practised, each with how it went, in the ○ ◌ ● vocabulary (``docs/specs/ux_learnloop_v1.md`` §7.5, session end): * ``on_your_own`` (●): one of the topic's OWN answers in the session earned certification credit (the session diff's ``demonstrated_attempt_ids…
- `_patch_checkpoint_locked(repository, params: SessionCheckpointInput, *, plan_presentation_id: Any, self_grade_disclosure: Any, first_hint_progress: Any, hint_seen: Any, page_seen: Any, earlier_opened: Any) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 353)
- `_require_owned(repository, session_id: str, device_id: str | None, *, expected_generation: int | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 437)
- `_require_pinned(repository, pinned: tuple[str, int], device_id: str | None, current: dict[str, Any] | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 474) — Landing ruling R1: the session a phone's sessionless write pinned at its start, still open, still this device's at the generation pinned, and still the open session; ``session_moved`` otherwise, carrying the open session's owner (the pinned one's when none is open).
- `_pin_open_session(repository, device_id: str | None) -> Callable[[], None]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 504) — A phone's sessionless check, pinned now and run later (each call raises ``session_moved``).
- `_merged_value(existing: dict[str, Any], params: SessionCheckpointInput, fields: set[str], name: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 612)
- `_copy_mapping(value: dict[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 618)
- `_with_hints_used(focus: dict[str, Any] | None, hints_used: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 622)
- `_with_declared_stuck(focus: dict[str, Any] | None, declared_stuck: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 634) — Store whether the draft is a stuck answer in the practice envelope.
- `_with_plan_presentation_id(focus: dict[str, Any] | None, presentation_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 652) — Store the draft's daily-plan presentation in the practice envelope (router R2a; no schema change).
- `_with_first_hint_progress(focus: dict[str, Any] | None, marker: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 668) — Adaptive difficulty AD1 (§11.2): keep the draft's first-hint progress marker in the practice envelope with the retry key it was set under (no schema change), so a restored draft keeps it and another draft never inherits it.
- `_with_hint_seen(focus: dict[str, Any] | None, seen: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 686) — Adaptive difficulty AD1 fix round 5 (V4): keep "a hint was seen on this draft" in the practice envelope with the retry key it was set under (no schema change), so a draft restored without a first-hint marker knows the first hint's timing is unknown.
- `_with_keyed_flag(focus: dict[str, Any] | None, name: str, value: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 704) — A flag kept in the practice envelope under the retry key it was set under (Reader CA1's ``pageSeen``, as ``hintSeen``); anything but True clears it.
- `_with_earlier_opened(focus: dict[str, Any] | None, opened: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 721) — Reader CA2 (K6, Q2; Codex review F1): *earlier on this question* was opened before Submit on this draft, kept in the practice envelope with the retry key it was opened under (no schema change), so the one hint-equivalent it costs survives a restart and a move into steps: the sub…
- `_draft_earlier_marker(checkpoint: dict[str, Any] | None, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 753)
- `_with_submission_id(focus: dict[str, Any] | None, submission_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 866) — Store the current attempt's stable retry key in the practice envelope.
- `_kept_disclosure(focus: dict[str, Any] | None, current_item: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 916) — The envelope without a disclosure that no longer belongs to its draft (another item, or another retry key on the same item).
- `_session_cold_checks(repository, session_id: str) -> dict[str, int]` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 1002) — Repair cold checks this session spent, and how many of them passed.
- `_session_followups_queued(repository, session_id: str) -> int` ([source](../../../../../../src/learnloop_sidecar/handlers/sessions.py), line 1037)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `draft_earlier_opened`, `draft_first_hint_progress`, `draft_hint_seen`, `draft_page_seen`, `draft_self_grade_disclosure`; statically calls `draft_earlier_opened`, `draft_first_hint_progress`, `draft_hint_seen`, `draft_page_seen`, `draft_self_grade_disclosure`
- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `refuse_moved_session`; statically calls `refuse_moved_session`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `require_owned_session`; statically calls `require_owned_session`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `require_owned_session`; statically calls `require_owned_session`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `refuse_moved_session`; statically calls `refuse_moved_session`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `KEEP_EARLIER_OPENED`, `KEEP_HINT_SEEN`, `KEEP_MARKER`, `SessionCheckpointInput`, `checkpoint_plan_presentation`, `clear_checkpoint`, `draft_earlier_opened`, `draft_plan_presentation`, `draft_self_grade_disclosure`, `patch_checkpoint`, `phone_claim_owner`, `require_owned_session`, `settle_self_grade_disclosure`; statically calls `SessionCheckpointInput`, `checkpoint_plan_presentation`, `clear_checkpoint`, `draft_earlier_opened`, `draft_plan_presentation`, `draft_self_grade_disclosure`, `patch_checkpoint`, `phone_claim_owner`, `require_owned_session`, `settle_self_grade_disclosure`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `phone_claim_owner`; statically calls `phone_claim_owner`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `SessionCheckpointInput`, `patch_checkpoint`, `require_owned_session`; statically calls `SessionCheckpointInput`, `patch_checkpoint`, `require_owned_session`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `draft_earlier_opened`, `refuse_moved_session`; statically calls `draft_earlier_opened`, `refuse_moved_session`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `SessionStartInput`, `carry_earlier_opened`, `draft_earlier_opened`, `start_session`; statically calls `SessionStartInput`, `carry_earlier_opened`, `draft_earlier_opened`, `start_session`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `frozen_trace_hash`, `record_self_grade_disclosure_reveal`; calls `frozen_trace_hash`, `record_self_grade_disclosure_reveal`
- [[Reference/Modules/learnloop/db/stores/session_ownership|learnloop.db.stores.session_ownership]] — imports `SessionOwnershipError`; calls `SessionOwnershipError`
- [[Reference/Modules/learnloop/goals/forecast_ledger|learnloop.goals.forecast_ledger]] — imports `issue_goal_forecasts`, `resolve_due_forecasts`; calls `issue_goal_forecasts`, `resolve_due_forecasts`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_attempt_ids`; calls `held_attempt_ids`
- [[Reference/Modules/learnloop/learner/session_learning_diff|learnloop.learner.session_learning_diff]] — imports `session_learning_diff`; calls `session_learning_diff`
- [[Reference/Modules/learnloop/router_objective/ask_availability|learnloop.router_objective.ask_availability]] — imports `module`; calls `record_change`
- [[Reference/Modules/learnloop/router_objective/sessions|learnloop.router_objective.sessions]] — imports `module`; calls `record_availability`, `record_end`, `sweep_unreported`
- [[Reference/Modules/learnloop/scheduling/session_minutes|learnloop.scheduling.session_minutes]] — imports `MINUTE_PRESETS`, `minute_choices`, `remembered_session_minutes`; calls `minute_choices`, `remembered_session_minutes`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`, `session_snapshot`; calls `session_snapshot`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `EmptyParams`, `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]] — imports `host_mutation`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `origin_ineligibility`; calls `origin_ineligibility`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] and 6 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_session_ownership.py](../../../../../../tests/test_session_ownership.py) — direct import
  - `test_a_skip_never_clears_the_draft_of_a_device_that_adopted_while_the_queue_was_built`
  - `test_a_skip_refuses_a_session_that_moved_and_came_back_while_the_queue_was_built`
- [tests/test_sidecar_remediation_surfaces.py](../../../../../../tests/test_sidecar_remediation_surfaces.py) — direct import
  - `test_session_counts_cold_checks_answered_and_confirmed_separately`
- [tests/test_sidecar_teach_back.py](../../../../../../tests/test_sidecar_teach_back.py) — direct import
  - `test_sidecar_teach_back_finish_retry_returns_same_attempt`
  - `test_sidecar_teach_back_from_a_queue_offer_links_the_graded_attempt`
  - `test_sidecar_teach_back_resume_merges_pending_learner_answer`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/sessions.py](../../../../../../src/learnloop_sidecar/handlers/sessions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
