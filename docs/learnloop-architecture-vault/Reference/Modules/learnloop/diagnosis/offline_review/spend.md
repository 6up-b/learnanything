---
title: "learnloop.diagnosis.offline_review.spend"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/offline_review/spend.py"
source_paths:
  - "src/learnloop/diagnosis/offline_review/spend.py"
source_commit: "3906ee6fb8a652159b2245fe15487b16b79f6d69"
source_commit_timestamp: "2026-10-13T16:44:43-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.offline_review"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.offline_review.spend module"
  - "src/learnloop/diagnosis/offline_review/spend.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-offline-review"
---

# `learnloop.diagnosis.offline_review.spend`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.offline_review.spend` exists within [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] to own the behavior summarized by its module contract: Compatibility exports for the shared AI spend adapter.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/offline_review/spend.py](../../../../../../../src/learnloop/diagnosis/offline_review/spend.py) |
| Source lines | 7 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `3906ee6fb8a652159b2245fe15487b16b79f6d69` |
| Commit timestamp | `2026-10-13T16:44:43-04:00` |

## Public API

No public top-level function or class definition is declared in this file.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `ReviewSpend`; statically calls `ReviewSpend`
- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `ReviewSpend`; statically calls `ReviewSpend`
- [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]] — imports `ReviewSpend`; statically calls `ReviewSpend`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `ReviewSpend`, `RouteInfo`; statically calls `ReviewSpend`, `RouteInfo`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `ReviewSpend`, `RouteInfo`; statically calls `ReviewSpend`, `RouteInfo`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `OUTPUT_ALLOWANCE`, `ReviewSpend`, `admitted_output_limit`, `is_subscription_client`; statically calls `ReviewSpend`, `admitted_output_limit`, `is_subscription_client`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `ReviewSpend`; statically calls `ReviewSpend`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `ReviewSpend`, `RouteInfo`; statically calls `ReviewSpend`, `RouteInfo`
- [[Reference/Modules/learnloop/diagnosis/recurrence/escalation|learnloop.diagnosis.recurrence.escalation]] — imports `ReviewSpend`; statically calls `ReviewSpend`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `ReviewSpend`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `ReviewSpend`; statically calls `ReviewSpend`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `KNOWN_PRICES_PER_MILLION`, `ReviewSpend`, `RouteInfo`; statically calls `ReviewSpend`, `RouteInfo`
- [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] — imports `ReviewSpend`; statically calls `ReviewSpend`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `ReviewSpend`, `RouteInfo`; statically calls `ReviewSpend`, `RouteInfo`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/review_spend|learnloop.ai.review_spend]] — imports `__all__`, `module`

### Platform and third-party dependencies

- Standard library: none imported directly
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]], [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]], [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]], [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] and 9 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnose_review_spend.py](../../../../../../../tests/test_diagnose_review_spend.py) — direct import
  - `test_the_route_allowance_is_enforced_when_the_profile_sets_no_limit`
- [tests/test_learner_text_gaps_rereview.py](../../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f3_a_failed_pair_backs_off_one_text_and_the_run_goes_on`
  - `test_rr_f5_a_commands_calls_do_not_count_toward_the_live_daily_cap`
- [tests/test_learner_text_gaps_review.py](../../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f2_a_refused_draft_is_deferred_not_logged_unmatched`
  - `test_f2_a_spend_stop_leaves_both_texts_queued_and_stops_the_run`
- [tests/test_notes_as_learner_text.py](../../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_c2b_a_note_and_an_ordinary_gap_share_the_gap_readers_route`
- [tests/test_output_budget.py](../../../../../../../tests/test_output_budget.py) — direct import
  - `test_no_retired_hard_coded_output_cap_remains`
  - `test_slice1_review_spend_admits_the_transports_truncation_retry_at_double`
  - `test_the_same_cause_judge_is_no_longer_held_to_600_tokens`
- [tests/test_t6_followup_review.py](../../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_a_route_override_cannot_exceed_the_profile_maximum`
  - `test_review_spend_reserves_the_transport_retry_at_its_doubled_allowance`

## Modification guidance

- Change spend policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/offline_review/spend.py](../../../../../../../src/learnloop/diagnosis/offline_review/spend.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
