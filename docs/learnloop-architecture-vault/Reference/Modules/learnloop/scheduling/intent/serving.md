---
title: "learnloop.scheduling.intent.serving"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/intent/serving.py"
source_paths:
  - "src/learnloop/scheduling/intent/serving.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling.intent"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.intent.serving module"
  - "src/learnloop/scheduling/intent/serving.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling-intent"
---

# `learnloop.scheduling.intent.serving`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.intent.serving` exists within [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] to own the behavior summarized by its module contract: What serving reads from intent (spec §5.2, §5.3, §6.1): one object per build.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/intent/serving.py](../../../../../../../src/learnloop/scheduling/intent/serving.py) |
| Source lines | 764 |
| Owning package | [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `on_your_own(row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 102) — An attempt that can answer a "Check once": one the activity policy does not count as assisted (``causal_activity_policy.attempt_counts_as_assisted``, the one classification the projection, the facet timeline and certification read: a primed attempt, one with hints, a hinted atte…
- `intent_enabled(config: Any) -> bool` ([source](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 118) — Is intent live for this config: at the successor (``mvp-0.29``) or a later tag, with ``intent.enabled`` on (DL2 Codex re-review F2)?
- `check_date(snapshot: CommitmentSnapshot, *, default_days: int) -> tuple[datetime, str]` ([source](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 129) — When a "Check once" comes due (RW6b's request: ``due_hint`` first).
- `class CheckState` ([source](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 151) — One pending "Check once".
  - `reserved(self) -> tuple[str, ...]` (line 181; public) — The refused candidates a live assessment reservation holds (F16).
  - `pending(self) -> bool` (line 193; public) — Due, unanswered and not replaced everywhere: the plan accounts for it, with no candidates (``no_candidates``) as with any (F21).
  - `servable(self) -> tuple[str, ...]` (line 200; public) — The candidates this check may serve now: the eligible ones; with none, nothing while a hold lasts; else the exposed ones, as practice.
  - `cold(self, item_id: str) -> bool` (line 212; public)
- `class IntentServing` ([source](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 217)
  - `bind_admission(self, admitted: Any) -> None` (line 244; public) — Split the due checks with this admission (``build_due_queue``'s own).
  - `checks(self) -> dict[str, CheckState]` (line 251; public)
  - `intent(self, item_id: str) -> ItemIntent` (line 278; public)
  - `check_for(self, item_id: str) -> CheckState | None` (line 285; public)
  - `withhold_reason(self, item_id: str) -> str | None` (line 291; public) — Why the build leaves this item out, or None (served as usual).
  - `is_check_candidate(self, item_id: str) -> bool` (line 319; public)
  - `_anchor(self, item_id: str) -> str | None` (line 323; internal)
  - `last_review_at(self, item_id: str, state: Any) -> str | None` (line 329; public) — The review that set ``due_at`` (the anchor), for the review-load interval (§6.3, F5); an item with no qualifying attempt (imported state) falls back to its ``last_attempt_at``, as DL1 reads it.
  - `effective(self, item_id: str, state: Any) -> EffectiveDue` (line 339; public) — §5.3's effective due (the stored ``due_at`` at 0.90 or with recall targets off).
  - `target_for(self, item_id: str) -> float` (line 360; public)
  - `fallbacks(self) -> dict[str, int]` (line 364; public)
  - `effective_due_or_none(self, item_id: str, state: Any) -> datetime | None` (line 367; public) — For ``_forgetting_risk``: an override only when it differs.
  - `due(self, item_id: str, state: Any) -> bool` (line 374; public)
  - `pushes(self, item_id: str, state: Any) -> bool` (line 378; public) — §6.1: an attempted item under Learn or Master that is not yet due.
  - `intent_control_request_commitments(self) -> tuple[str, ...]` (line 390; public) — Intent-control ``help_me_remember`` commitments: choosing Master or Keep on an item is not a request (§5.3).
  - `filter_requests(self, base: Sequence[str]) -> list[str]` (line 402; public) — The existing branches, minus excluded or pending items, plus every due check's candidates (trimmed to one per check after the sort).
  - `due_checks(self) -> list[CheckState]` (line 419; public) — Every due, unanswered, unreplaced check, servable or not (round 6, F20: a check with nothing to serve is accounted for, never dropped); selection reads each one's ``servable``.
  - `pick_checks(self, queue: Sequence[Any]) -> tuple[list[Any], list[str]]` (line 429; public) — One item per due check: the first (top-ranked) candidate in the built order; the other candidates leave this build.
  - `check_item_ids(self, item_ids: Iterable[str]) -> dict[str, CheckState]` (line 449; public) — The due checks' items among ``item_ids`` (the plan's pool), one per check: the first in the given order.
- `build_checks(resolution: Resolution, *, by_lo: Mapping[str, list[str]], item_los: Mapping[str, str], now: datetime, default_days: int, attempts_since: Any, cold_at: Any=None) -> tuple[dict[str, CheckState], Resolution]` ([source](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 480) — Every pending "Check once" with its date and the items it decides; answered ones are folded to ``satisfied`` in the returned resolution.
- `check_feasibility(item_id: str, gate: Any) -> Mapping[str, Any] | None` ([source](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 561) — THE "Check once" feasibility gate (DL2 fix round 6): why ``item_id`` can never be a check's item now, or None.
- `check_feasibility_of(gate: Any) -> Any` ([source](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 570)
- `split_check(check: CheckState, *, eligibility: Any=None, feasibility: Any=None, followup_gate: Any=None) -> CheckState` ([source](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 591) — A due, unanswered check's candidates split by the eligibility decision (``eligibility(item_id, check_created_at)``; None: every one eligible), among those the one check gate passes.
- `intent_serving(vault: Any, repository: Any, *, now: datetime, weights: tuple[float, ...] | None=None, force: bool=False) -> IntentServing | None` ([source](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 640) — The build's intent view, or None when intent changes nothing.

### Module constants

- `DATE_FROM_DUE_HINT` ([src/learnloop/scheduling/intent/serving.py](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 91)
- `DATE_FROM_DEFAULT` ([src/learnloop/scheduling/intent/serving.py](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 92)
- `DATE_FROM_PRACTICE` ([src/learnloop/scheduling/intent/serving.py](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 94)
- `_SERVE` ([src/learnloop/scheduling/intent/serving.py](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 98)
- `_SERVE_AS_ORDINARY` ([src/learnloop/scheduling/intent/serving.py](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 99)

### Explicit exports

`__all__` declares:

- `CheckState`
- `DATE_FROM_DEFAULT`
- `DATE_FROM_DUE_HINT`
- `DATE_FROM_PRACTICE`
- `IntentServing`
- `build_checks`
- `check_date`
- `intent_enabled`
- `intent_serving`
- `on_your_own`
- `check_feasibility`
- `split_check`

## Internal implementation anchors

- `_items_by_learning_object(vault: Any) -> tuple[dict[str, str], dict[str, list[str]]]` ([source](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 466)
- `_admission_only(admission: Any) -> Any` ([source](../../../../../../../src/learnloop/scheduling/intent/serving.py), line 574) — No gate (a view with no vault behind it): the admission alone.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `intent_serving`; statically calls `intent_serving`
- [[Reference/Modules/learnloop/daily_plan/headline|learnloop.daily_plan.headline]] — imports `intent_serving`; statically calls `intent_serving`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `intent_serving`; statically calls `intent_serving`
- [[Reference/Modules/learnloop/daily_plan/schedule_effects|learnloop.daily_plan.schedule_effects]] — imports `intent_serving`; statically calls `intent_serving`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `intent_serving`; statically calls `intent_serving`
- [[Reference/Modules/learnloop/intent/checks|learnloop.intent.checks]] — imports `CheckState`, `intent_serving`; statically calls `intent_serving`
- [[Reference/Modules/learnloop/intent/report|learnloop.intent.report]] — imports `intent_enabled`; statically calls `intent_enabled`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `intent_serving`; statically calls `intent_serving`
- [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]] — imports `intent_enabled`; statically calls `intent_enabled`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `INTENT_VERSIONS`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/stores/intent_reads|learnloop.db.stores.intent_reads]] — imports `module`; calls `attempts_since`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `attempt_counts_as_assisted`; calls `attempt_counts_as_assisted`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/intent/feasibility|learnloop.scheduling.intent.feasibility]] — imports `CheckGate`; calls `CheckGate`
- [[Reference/Modules/learnloop/scheduling/intent/followup_gate|learnloop.scheduling.intent.followup_gate]] — imports `followup_gate`; calls `followup_gate`
- [[Reference/Modules/learnloop/scheduling/intent/model|learnloop.scheduling.intent.model]] — imports `CommitmentSnapshot`
- [[Reference/Modules/learnloop/scheduling/intent/recall_targets|learnloop.scheduling.intent.recall_targets]] — imports `EffectiveDue`, `effective_due`, `load_anchors`; calls `EffectiveDue`, `effective_due`, `load_anchors`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `ItemIntent`, `Resolution`, `load_snapshots`; calls `Resolution`, `load_snapshots`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `check_admission`; calls `check_admission`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `module`; calls `check_once_at_attempt`, `decide`, `gather`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/headline|learnloop.daily_plan.headline]], [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]], [[Reference/Modules/learnloop/daily_plan/schedule_effects|learnloop.daily_plan.schedule_effects]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — direct import
- [tests/intent_fakes.py](../../../../../../../tests/intent_fakes.py) — direct import
- [tests/test_ad23_intent_compose.py](../../../../../../../tests/test_ad23_intent_compose.py) — direct import
  - `test_f2_ad_never_serves_an_item_intent_withholds`
  - `test_property_ad_never_serves_or_clears_what_the_incumbent_withholds`
  - `test_the_real_scheduler_lane_with_commitments`
- [tests/test_ad23_inversion.py](../../../../../../../tests/test_ad23_inversion.py) — direct import
  - `test_the_codes_vocabulary_covers_the_incumbents_reasons`
- [tests/test_ad23_pool_membership.py](../../../../../../../tests/test_ad23_pool_membership.py) — direct import
  - `test_h_a_due_check_once_leaves_ad_drawing`
- [tests/test_data_capture_codex_rereview.py](../../../../../../../tests/test_data_capture_codex_rereview.py) — direct import
- [tests/test_data_capture_codex_review.py](../../../../../../../tests/test_data_capture_codex_review.py) — direct import
- [tests/test_intent_codex_rereview.py](../../../../../../../tests/test_intent_codex_rereview.py) — direct import
  - `test_f2_below_the_tag_commitments_change_nothing_with_the_switch_on`
  - `test_f2_new_vaults_start_at_the_successor_with_intent_live`
  - `test_f2_the_gate_reads_the_version_and_the_switch`
- [tests/test_intent_fix_round4.py](../../../../../../../tests/test_intent_fix_round4.py) — direct import
  - `test_f13_every_contamination_class`
  - `test_f13_on_your_own_is_the_activity_policys_classification`
- [tests/test_intent_fix_round7.py](../../../../../../../tests/test_intent_fix_round7.py) — direct import
  - `test_f21_a_due_check_on_an_lo_with_no_items_is_recorded_as_no_candidates`
- [tests/test_intent_resolution.py](../../../../../../../tests/test_intent_resolution.py) — direct import
  - `test_check_dates_read_the_due_hint_then_the_default_delay`
- [tests/test_reader_followups.py](../../../../../../../tests/test_reader_followups.py) — direct import
  - `test_each_follow_up_is_a_test_me_later_commitment_with_its_provenance`
- [tests/test_reader_followups_review.py](../../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f2_an_automatic_follow_up_never_lands_in_a_scope_the_learner_chose`
- [tests/test_reader_followups_round4.py](../../../../../../../tests/test_reader_followups_round4.py) — direct import
- [tests/test_reader_rw6b_landing.py](../../../../../../../tests/test_reader_rw6b_landing.py) — direct import

## Modification guidance

- Change serving policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/intent/serving.py](../../../../../../../src/learnloop/scheduling/intent/serving.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
