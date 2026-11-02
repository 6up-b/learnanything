---
title: "learnloop.serve_eligibility"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/serve_eligibility.py"
source_paths:
  - "src/learnloop/serve_eligibility.py"
source_commit: "736469cba1c0ccbb91310959278230ba86d8378f"
source_commit_timestamp: "2026-10-25T21:13:50-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.serve_eligibility module"
  - "src/learnloop/serve_eligibility.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.serve_eligibility`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.serve_eligibility` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: One serve/administration eligibility decision (the "one eligibility decision" stage, ``docs/reviews/serve-eligibility-decision.md``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py) |
| Source lines | 1078 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `736469cba1c0ccbb91310959278230ba86d8378f` |
| Commit timestamp | `2026-10-25T21:13:50-04:00` |

## Public API

- `trace_hash(learner_answer_md: str | None) -> str` ([source](../../../../../src/learnloop/serve_eligibility.py), line 187) — The identity of a learner's whole trace (the answer and the volunteered line, as ``trace_evidence.compose_learner_trace`` composes them).
- `disclosure_identity(row: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../src/learnloop/serve_eligibility.py), line 194) — The structured identity a disclosure row carries, or None for any row that is not a well-formed current-version disclosure (legacy rows too).
- `is_own_disclosure(row: Mapping[str, Any], submission_id: str | None, learner_answer_md: str | None) -> bool` ([source](../../../../../src/learnloop/serve_eligibility.py), line 231) — Is ``row`` the disclosure of exactly this submission: the same retry key AND the hash of exactly this trace, each compared for equality (round 5, F1-2)?
- `attributable_disclosure_ids(rows: Iterable[Mapping[str, Any]], *, practice_item_id: str, submission_id: str | None, learner_answer_md: str | None) -> frozenset[str]` ([source](../../../../../src/learnloop/serve_eligibility.py), line 248) — THE disclosures attributable to one submission: the plain self-grade disclosure rows (``answer_display``) on the item itself whose identity is exactly this submission's retry key and trace (:func:`is_own_disclosure`).
- `attempt_submission(repository: Any, attempt_id: str | None, practice_item_id: str | None) -> tuple[str | None, str | None]` ([source](../../../../../src/learnloop/serve_eligibility.py), line 278) — ``(retry key, trace)`` of the committed attempt ``attempt_id`` on this item: the identity its own disclosure rows must match exactly; ``(None, None)`` without an id, or for an attempt on another item (no exemption).
- `class RevealRow` ([source](../../../../../src/learnloop/serve_eligibility.py), line 295) — One ``reveal_events`` row (every column the decision reads).
  - `routine(self) -> bool` (line 308; public)
  - `from_row(cls, row: Mapping[str, Any]) -> RevealRow` (line 312; public)
- `class FollowupTask` ([source](../../../../../src/learnloop/serve_eligibility.py), line 326) — One open (``pending`` or ``served``) follow-up task selecting the item.
  - `cold(self) -> bool` (line 337; public)
  - `unexpired(self, at: str) -> bool` (line 340; public)
  - `due(self, at: str) -> bool` (line 343; public)
  - `from_row(cls, row: Mapping[str, Any]) -> FollowupTask` (line 348; public)
- `class EligibilityInputs` ([source](../../../../../src/learnloop/serve_eligibility.py), line 360) — Everything the decision reads, as of one instant.
- `class EligibilityDecision` ([source](../../../../../src/learnloop/serve_eligibility.py), line 416) — What a path may do with the item now, and why (inspectable: callers log :meth:`record` where they already record serving decisions).
  - `serves(self) -> bool` (line 445; public) — Can the path serve the item as it asked?
  - `writes(self) -> bool` (line 451; public) — Does acting on the decision write anything (a re-time, a withdrawal)?
  - `record(self) -> dict[str, Any]` (line 456; public)
- `class SubmitExposure` ([source](../../../../../src/learnloop/serve_eligibility.py), line 495) — Submit's reading of the item's exposure at one instant.
- `submit_exposure(inputs: EligibilityInputs) -> SubmitExposure` ([source](../../../../../src/learnloop/serve_eligibility.py), line 509) — Submit's auto-prime total, exactly as ``Repository.total_reveal_amount`` computes it in SQL (and ``attempts.reveal_total_for_submission`` subtracts the draft's own disclosure), row for row: * the item's rows only; * a routine display counts by its coverage: stamped at or after `…
- `active_task(inputs: EligibilityInputs) -> FollowupTask | None` ([source](../../../../../src/learnloop/serve_eligibility.py), line 583) — The task submit answers: the first due, unexpired open task of ANY kind selecting the item (``Repository.active_followup_task_for_item``, its order).
- `cold_task_holds(inputs: EligibilityInputs, task: FollowupTask) -> list[tuple[RevealRow, str, str]]` ([source](../../../../../src/learnloop/serve_eligibility.py), line 594) — The serving holds on one cold task now, each ``(row, released_at, reason)``: the scheduler's deferral scope, the item or anywhere in its learning object.
- `decide(inputs: EligibilityInputs, request: str) -> EligibilityDecision` ([source](../../../../../src/learnloop/serve_eligibility.py), line 648) — THE decision.
- `gather(repository: Any, *, practice_item_id: str, learning_object_id: str | None, at: str, window_until: str | None=None, submission_id: str | None=None, learner_answer_md: str | None=None, declared_primed: bool=False, auto_primed: bool=False, hints_used: int=0, attempt_type: str | None=None, reveal_rows: Sequence[Mapping[str, Any]] | None=None, check_created_at: str | None=None) -> EligibilityInputs` ([source](../../../../../src/learnloop/serve_eligibility.py), line 846) — Read the decision's inputs for one item from ``repository``.
- `check_once_at_attempt(repository: Any, *, practice_item_id: str, learning_object_id: str | None, attempt_id: str, attempt_at: str, check_created_at: str | None) -> EligibilityDecision` ([source](../../../../../src/learnloop/serve_eligibility.py), line 900) — The ``CHECK_ONCE`` decision as it stood when an attempt was submitted (daily-loop DL2 Codex re-review F3): only an attempt the decision would have served cold can answer a "Check once".
- `help_converts_active(vault: Any) -> bool` ([source](../../../../../src/learnloop/serve_eligibility.py), line 956) — Reader CA2's one help rule (``ONE_ASK_ALGORITHM_VERSION``, ``mvp-0.34``): at that tag or later with ``ask.cold_help_converts`` on.
- `decision_active(vault: Any) -> bool` ([source](../../../../../src/learnloop/serve_eligibility.py), line 974) — Is the one eligibility decision live for ``vault`` (a ``LoadedVault``, duck-typed)?
- `pending_writes(decision: EligibilityDecision) -> dict[str, str | None]` ([source](../../../../../src/learnloop/serve_eligibility.py), line 992) — The decision's writes as one map, for a reader that must judge as if they were made without making them (the CLI's validation before it prompts, a dry run): task id -> its new ``not_before``, or None for a withdrawn task.
- `with_pending_writes(inputs: EligibilityInputs, writes: Mapping[str, str | None] | None) -> EligibilityInputs` ([source](../../../../../src/learnloop/serve_eligibility.py), line 1003) — ``inputs`` as they would read once ``writes`` (:func:`pending_writes`) were made: re-timed tasks pushed (monotone), withdrawn ones gone.
- `retime(repository: Any, decision: EligibilityDecision, *, clock: Any=None) -> None` ([source](../../../../../src/learnloop/serve_eligibility.py), line 1019) — Apply a decision's re-times (monotone pushes of ``not_before``; never the expiry, so an episode that keeps being revealed still censors at its original end).
- `log_decision(decision: EligibilityDecision, *, path: str) -> None` ([source](../../../../../src/learnloop/serve_eligibility.py), line 1028) — The decision's trace line, at the path that acted on it.

### Module constants

- `AUTO_PRIME_REVEAL_THRESHOLD` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 81)
- `COLD_FOLLOWUP_TASK_KINDS` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 85)
- `POST_ATTEMPT_REVEAL_KINDS` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 89)
- `COLD_RETRIEVAL_DELAY` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 93)
- `UNKNOWN_RELEASE` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 97)
- `SUBMIT` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 102)
- `COLD_CHECK` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 104)
- `PROBE` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 106)
- `QUICK_CHECK` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 108)
- `CHECK_ONCE` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 112)
- `REQUESTS` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 114)
- `SERVE` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 116)
- `SERVE_AS_ORDINARY` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 117)
- `DEFER_UNTIL` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 118)
- `REFUSE` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 119)
- `ELIGIBLE` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 124)
- `NO_COLD_CHECK` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 126)
- `COLD_CHECK_ROUTINE_DISPLAY` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 129)
- `COLD_CHECK_REVEALED_SINCE_SCHEDULED` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 132)
- `COLD_CHECK_ANSWER_SHOWN` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 137)
- `COLD_CHECK_PRACTISED_SINCE_SCHEDULED` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 142)
- `COLD_CHECK_ASSISTED` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 144)
- `COLD_CHECK_PRIMED` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 146)
- `COLD_CHECK_AUTO_PRIMED` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 150)
- `COLD_CHECK_HELP_TAKEN` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 156)
- `PROBE_ITEM_ANSWER_SHOWN` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 159)
- `QUICK_CHECK_ANSWER_SHOWN` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 161)
- `CHECK_ONCE_ANSWER_SHOWN` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 166)
- `COLD_CHECK_REFUSAL` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 169)
- `SELF_GRADE_DISCLOSURE_BASIS` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 176)
- `DISCLOSURE_IDENTITY_VERSION` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 183)
- `DISCLOSURE_PREFIX` ([src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py), line 184)

### Explicit exports

`__all__` declares:

- `AUTO_PRIME_REVEAL_THRESHOLD`
- `CHECK_ONCE`
- `CHECK_ONCE_ANSWER_SHOWN`
- `COLD_CHECK`
- `COLD_CHECK_ANSWER_SHOWN`
- `COLD_CHECK_AUTO_PRIMED`
- `COLD_CHECK_HELP_TAKEN`
- `COLD_CHECK_PRACTISED_SINCE_SCHEDULED`
- `COLD_FOLLOWUP_TASK_KINDS`
- `COLD_RETRIEVAL_DELAY`
- `DEFER_UNTIL`
- `EligibilityDecision`
- `EligibilityInputs`
- `FollowupTask`
- `PROBE`
- `QUICK_CHECK`
- `REFUSE`
- `RevealRow`
- `ROUTINE_DISPLAY_COVERAGE`
- `SERVE`
- `SERVE_AS_ORDINARY`
- `SUBMIT`
- `DISCLOSURE_IDENTITY_VERSION`
- `SELF_GRADE_DISCLOSURE_BASIS`
- `active_task`
- `attempt_submission`
- `attributable_disclosure_ids`
- `check_once_at_attempt`
- `cold_task_holds`
- `decide`
- `decision_active`
- `help_converts_active`
- `disclosure_identity`
- `gather`
- `is_own_disclosure`
- `log_decision`
- `pending_writes`
- `retime`
- `submit_exposure`
- `trace_hash`
- `with_pending_writes`

## Internal implementation anchors

- `_unique_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]` ([source](../../../../../src/learnloop/serve_eligibility.py), line 219) — Reject a JSON object that names a field twice (``json.loads`` would keep the last value, round 6): such an identity is malformed.
- `_iso(moment: datetime) -> str` ([source](../../../../../src/learnloop/serve_eligibility.py), line 477)
- `_parsed(value: str) -> datetime | None` ([source](../../../../../src/learnloop/serve_eligibility.py), line 481)
- `_plus(stamp: str, delta: timedelta) -> str | None` ([source](../../../../../src/learnloop/serve_eligibility.py), line 489)
- `_ids(rows: Iterable[RevealRow]) -> tuple[str, ...]` ([source](../../../../../src/learnloop/serve_eligibility.py), line 631)
- `_shown(rows: Sequence[RevealRow]) -> str` ([source](../../../../../src/learnloop/serve_eligibility.py), line 638) — "its answer was shown (tutor answer at …)" for a refusal.
- `_decide_submit(inputs: EligibilityInputs, exposure: SubmitExposure, base: dict[str, Any]) -> EligibilityDecision` ([source](../../../../../src/learnloop/serve_eligibility.py), line 685)
- `_decide_cold_check(inputs: EligibilityInputs, exposure: SubmitExposure, base: dict[str, Any]) -> EligibilityDecision` ([source](../../../../../src/learnloop/serve_eligibility.py), line 733)
- `_decide_check_once(inputs: EligibilityInputs, exposure: SubmitExposure, base: dict[str, Any]) -> EligibilityDecision` ([source](../../../../../src/learnloop/serve_eligibility.py), line 806) — A learner's "Check once" (daily-loop DL2) asks the cold check's question without a task: the same holds (:func:`cold_task_holds`, counted from the check's choice), the same standing exposure.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]] — imports `EligibilityInputs`, `RevealRow`, `submit_exposure`; statically calls `EligibilityInputs`, `submit_exposure`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `module`; statically calls `decide`, `decision_active`, `gather`, `help_converts_active`, `log_decision`, `submit_exposure`, `with_pending_writes`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `module`; statically calls `attempt_submission`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `module`; statically calls `decision_active`, `log_decision`, `pending_writes`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `module`; statically calls `decide`, `decision_active`, `gather`, `log_decision`
- [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] — imports `module`; statically calls `decide`, `decision_active`, `gather`, `log_decision`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `COLD_CHECK_HELP_TAKEN`, `module`; statically calls `help_converts_active`
- [[Reference/Modules/learnloop/intent/checks|learnloop.intent.checks]] — imports `help_converts_active`; statically calls `help_converts_active`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `help_converts_active`; statically calls `help_converts_active`
- [[Reference/Modules/learnloop/scheduling/intent/followup_gate|learnloop.scheduling.intent.followup_gate]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `module`; statically calls `check_once_at_attempt`, `decide`, `gather`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `module`; statically calls `EligibilityDecision`, `decide`, `decision_active`, `gather`, `log_decision`, `retime`
- [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]] — imports `AUTO_PRIME_REVEAL_THRESHOLD`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `AUTO_PRIME_REVEAL_THRESHOLD`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `help_converts_active`; statically calls `help_converts_active`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `module`; statically calls `decision_active`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `help_converts_active`; statically calls `help_converts_active`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `help_converts_active`; statically calls `help_converts_active`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `ELIGIBILITY_DECISION_VERSIONS`, `ONE_ASK_VERSIONS`
- [[Reference/Modules/learnloop/reveal_coverage|learnloop.reveal_coverage]] — imports `ROUTINE_DISPLAY_COVERAGE`, `is_routine_display`, `routine_covered_from`, `routine_released_at`, `routine_row_covers`; calls `is_routine_display`, `routine_covered_from`, `routine_released_at`, `routine_row_covers`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `json`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_cold_retry_reschedule.py](../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_help_on_a_due_cold_retry_schedules_one_fresh_retry_on_another_surface`
- [tests/test_compare_methods.py](../../../../../tests/test_compare_methods.py) — direct import
  - `test_the_reveal_makes_the_cold_lane_treat_the_family_as_revealed_and_primes_the_next_attempt`
- [tests/test_intent_orchestrator_rulings.py](../../../../../tests/test_intent_orchestrator_rulings.py) — direct import
  - `test_r2_one_attributable_disclosure_function`
- [tests/test_reader_ca2_one_ask.py](../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_the_predecessor_refuses_a_hinted_cold_check_and_the_successor_converts_it`
  - `test_the_rule_is_live_only_at_the_tag_with_its_switch`
  - `test_without_help_the_cold_rules_are_unchanged`
- [tests/test_reader_workbench_rw2a.py](../../../../../tests/test_reader_workbench_rw2a.py) — direct import
  - `test_a_workbench_submit_asks_the_same_eligibility_decision_as_every_submit`
- [tests/test_serve_eligibility.py](../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_a_learners_pick_of_a_cold_check_submit_would_prime_is_served_as_practice`
  - `test_every_serve_agrees_with_submit_at_the_same_instant`
  - `test_q33_the_bounded_window_also_bounds_the_last_attempt`
  - `test_submit_exposure_is_the_sql_total_row_for_row`
  - `test_submit_refusal_names_the_change_since_the_serve`
  - `test_the_12_9_reproduction_is_served_as_practice_and_its_check_withdrawn`
  - `test_the_cold_delay_is_the_remediation_delay_and_the_constants_are_one`
  - `test_the_queue_serves_a_cold_retry_submit_would_prime_as_practice_and_ends_it_honestly`
- [tests/test_serve_eligibility_review.py](../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_a_cold_check_on_a_direct_open_is_withdrawn_when_its_item_can_no_longer_take_it_cold`
  - `test_f1_the_decision_refuses_any_primed_draft_and_names_its_provenance`
  - `test_f2_a_certification_probe_whose_answer_was_shown_expires_unmeasured`
  - `test_f2_a_non_persisting_read_withdraws_nothing`
  - `test_f2_every_open_cold_check_on_an_item_whose_answer_stands_is_withdrawn`
  - `test_f3_a_cold_check_is_never_served_on_an_item_practised_since_it_was_set`
  - `test_f3_a_delayed_open_and_submit_after_a_withdrawing_build_are_plain_practice`
  - `test_f4_below_the_tag_or_switched_off_the_12_9_case_is_served_as_on_mvp_026`
  - `test_f4_new_vaults_start_at_the_successor_with_the_switch_on`
  - `test_f4_the_gate_reads_the_version_and_the_switch`
  - `test_f5_a_withdrawal_racing_a_consume_leaves_the_consume_time_disposition_free`

## Modification guidance

- Make changes here when the responsibility remains serve eligibility within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/serve_eligibility.py](../../../../../src/learnloop/serve_eligibility.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
