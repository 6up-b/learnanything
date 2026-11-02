---
title: "learnloop.daily_plan.estimates"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/estimates.py"
source_paths:
  - "src/learnloop/daily_plan/estimates.py"
source_commit: "e4435c67875576c6e237183479248778806cc4d7"
source_commit_timestamp: "2026-10-20T23:32:34-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.estimates module"
  - "src/learnloop/daily_plan/estimates.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.estimates`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.estimates` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Time estimates (``spec_daily_loop_v1.md`` §6.4, Q12).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/estimates.py](../../../../../../src/learnloop/daily_plan/estimates.py) |
| Source lines | 267 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e4435c67875576c6e237183479248778806cc4d7` |
| Commit timestamp | `2026-10-20T23:32:34-04:00` |

## Public API

- `class DurationEvidence` ([source](../../../../../../src/learnloop/daily_plan/estimates.py), line 48) — What the estimator reads, loaded once per plan decision.
- `class ItemEstimate` ([source](../../../../../../src/learnloop/daily_plan/estimates.py), line 60)
  - `as_dict(self) -> dict[str, Any]` (line 69; public)
- `winsorize_minutes(latency_seconds: float, cap_minutes: float) -> float` ([source](../../../../../../src/learnloop/daily_plan/estimates.py), line 81)
- `feedback_minutes(dwell: Sequence[float]) -> float` ([source](../../../../../../src/learnloop/daily_plan/estimates.py), line 85)
- `mode_prior(mode_latencies: Sequence[float], prior_minutes: float, *, k: float=PSEUDO_OBSERVATIONS) -> float` ([source](../../../../../../src/learnloop/daily_plan/estimates.py), line 91) — g: the practice-mode median shrunk toward the item prior.
- `answer_minutes(own_latencies: Sequence[float], g: float, *, k: float=PSEUDO_OBSERVATIONS) -> float` ([source](../../../../../../src/learnloop/daily_plan/estimates.py), line 102)
- `class Estimator` ([source](../../../../../../src/learnloop/daily_plan/estimates.py), line 110)
  - `feedback_minutes(self) -> float` (line 115; public)
  - `estimate(self, item_id: str, practice_mode: str | None, expected_minutes: float | None) -> ItemEstimate` (line 118; public)
  - `item_minutes(self, vault: Any, item_id: str) -> float` (line 138; public) — The item's planning estimate, as the plan stores it (4 decimals).
  - `reading_minutes(self, words_left: int) -> float` (line 149; public) — A reading block's estimate, as the plan stores it (4 decimals).
- `reading_minutes(words_left: int, words_per_minute: int) -> float` ([source](../../../../../../src/learnloop/daily_plan/estimates.py), line 155) — A reading block's estimate: the section's words left / reading pace (§6.4).
- `load_duration_evidence(repository: Any, *, latency_cap_minutes: float, attempt_rows: Any=None, event_visible: Any=None, event_rows: Any=None) -> DurationEvidence` ([source](../../../../../../src/learnloop/daily_plan/estimates.py), line 161) — Read own latencies (by item and by mode) and plan feedback dwell.

### Module constants

- `ESTIMATOR_VERSION` ([src/learnloop/daily_plan/estimates.py](../../../../../../src/learnloop/daily_plan/estimates.py), line 31)
- `ESTIMATE_DECIMALS` ([src/learnloop/daily_plan/estimates.py](../../../../../../src/learnloop/daily_plan/estimates.py), line 37)
- `PSEUDO_OBSERVATIONS` ([src/learnloop/daily_plan/estimates.py](../../../../../../src/learnloop/daily_plan/estimates.py), line 39)
- `FALLBACK_PRIOR_MINUTES` ([src/learnloop/daily_plan/estimates.py](../../../../../../src/learnloop/daily_plan/estimates.py), line 41)
- `DEFAULT_FEEDBACK_MINUTES` ([src/learnloop/daily_plan/estimates.py](../../../../../../src/learnloop/daily_plan/estimates.py), line 42)
- `FEEDBACK_MIN_OBSERVATIONS` ([src/learnloop/daily_plan/estimates.py](../../../../../../src/learnloop/daily_plan/estimates.py), line 43)
- `FEEDBACK_CAP_MINUTES` ([src/learnloop/daily_plan/estimates.py](../../../../../../src/learnloop/daily_plan/estimates.py), line 44)

### Explicit exports

`__all__` declares:

- `DEFAULT_FEEDBACK_MINUTES`
- `DurationEvidence`
- `ESTIMATE_DECIMALS`
- `ESTIMATOR_VERSION`
- `Estimator`
- `FALLBACK_PRIOR_MINUTES`
- `FEEDBACK_CAP_MINUTES`
- `FEEDBACK_MIN_OBSERVATIONS`
- `ItemEstimate`
- `PSEUDO_OBSERVATIONS`
- `answer_minutes`
- `feedback_minutes`
- `load_duration_evidence`
- `mode_prior`
- `reading_minutes`
- `winsorize_minutes`

## Internal implementation anchors

- `_feedback_dwell(connection: Any, *, event_visible: Any=None, event_rows: Any=None) -> list[float]` ([source](../../../../../../src/learnloop/daily_plan/estimates.py), line 210) — item_done -> the next item_served in the same plan, capped at five minutes.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `Estimator`, `load_duration_evidence`; statically calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `Estimator`, `load_duration_evidence`; statically calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]] — imports `Estimator`, `load_duration_evidence`; statically calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `Estimator`, `load_duration_evidence`; statically calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]] — imports `Estimator`, `load_duration_evidence`; statically calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `Estimator`, `load_duration_evidence`; statically calls `Estimator`, `load_duration_evidence`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]], [[Reference/Modules/learnloop/daily_plan/ad_slot|learnloop.daily_plan.ad_slot]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_feedback_dwell_skips_a_serve_withheld_with_its_presentation`
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f12_a_pick_after_the_plan_closed_adds_no_feedback_dwell`
- [tests/test_duration_estimates.py](../../../../../../tests/test_duration_estimates.py) — direct import
  - `test_feedback_dwell_needs_ten_observations_and_is_capped`
  - `test_latencies_are_winsorized_at_the_cap`
  - `test_loaded_evidence_reads_own_and_mode_latencies`
  - `test_no_history_falls_back_to_the_prior_then_three_minutes`
  - `test_reading_estimate_is_words_left_over_the_pace`
  - `test_shrinkage_moves_from_the_prior_toward_own_latencies`
  - `test_vault_items_carry_expected_minutes_into_the_estimate`
- [tests/test_source_exercise_rpcs.py](../../../../../../tests/test_source_exercise_rpcs.py) — direct import
  - `test_an_interactive_import_bounds_the_authored_drafts_own_duration`
  - `test_the_carried_duration_response_is_the_plan_estimate_of_the_authored_draft`

## Modification guidance

- Make changes here when the responsibility remains estimates within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/estimates.py](../../../../../../src/learnloop/daily_plan/estimates.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
