---
title: "learnloop.learner.surfaced_beliefs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/surfaced_beliefs.py"
source_paths:
  - "src/learnloop/learner/surfaced_beliefs.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.surfaced_beliefs module"
  - "src/learnloop/learner/surfaced_beliefs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.surfaced_beliefs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.surfaced_beliefs` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: A6: the system must be able to say it was wrong.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/surfaced_beliefs.py](../../../../../../src/learnloop/learner/surfaced_beliefs.py) |
| Source lines | 404 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SurfacedBeliefError(ValueError)` ([source](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 121)
- `class BeliefReference` ([source](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 126) — The belief a presented claim is about, normalized at capture time.
- `class SurfacedBeliefWithdrawal` ([source](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 134) — One learner-visible retraction of one belief the learner was shown.
  - `entry_id(self) -> str` (line 162; public)
- `resolve_belief_reference(claim_type: str, claim_ref: Any) -> BeliefReference | None` ([source](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 170) — Normalize (claim_type, claim_ref) into the belief the claim asserts.
- `mark_belief_surfaced(repository: Repository, *, belief_id: str, claim_text: str | None, surface: str, belief_kind: str='misconception', clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 209) — Flag a belief as shown on a surface that does not dispatch typed claims.
- `record_belief_withdrawal(repository: Repository, *, belief_id: str, reason: str, replacement_belief_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 250) — Withdraw a belief, with a reason from A6's four-value vocabulary.
- `typed_withdrawal_reason(disposition: str, reason: str | None) -> str` ([source](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 289) — Map a stored (disposition, reason) pair onto A6's four values.
- `surfaced_belief_corrections(repository: Repository) -> list[SurfacedBeliefWithdrawal]` ([source](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 334) — Every withdrawal the learner is owed, oldest first.

### Module constants

- `BELIEF_CLAIM_TYPES` ([src/learnloop/learner/surfaced_beliefs.py](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 45)
- `_BELIEF_ID_KEYS` ([src/learnloop/learner/surfaced_beliefs.py](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 54)
- `WITHDRAWAL_REASONS` ([src/learnloop/learner/surfaced_beliefs.py](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 71)
- `_DISPOSITION_FOR_REASON` ([src/learnloop/learner/surfaced_beliefs.py](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 81)
- `_LEGACY_REASON_ALIASES` ([src/learnloop/learner/surfaced_beliefs.py](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 94)
- `WITHDRAWAL_WORDING` ([src/learnloop/learner/surfaced_beliefs.py](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 102)
- `FEED_ENTRY_KIND` ([src/learnloop/learner/surfaced_beliefs.py](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 118)

## Internal implementation anchors

- `_withdrawal_statement(*, claim_text: str, withdrawal_reason: str, replacement_statement: str | None) -> str` ([source](../../../../../../src/learnloop/learner/surfaced_beliefs.py), line 309) — Name the claim, then withdraw it, then (only then) mention a successor.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `mark_belief_surfaced`; statically calls `mark_belief_surfaced`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `typed_withdrawal_reason`; statically calls `typed_withdrawal_reason`
- [[Reference/Modules/learnloop/learner/hypothesis_claims|learnloop.learner.hypothesis_claims]] — imports `resolve_belief_reference`; statically calls `resolve_belief_reference`
- [[Reference/Modules/learnloop/learner/independence_audit|learnloop.learner.independence_audit]] — imports `SurfacedBeliefError`, `record_belief_withdrawal`; statically calls `record_belief_withdrawal`
- [[Reference/Modules/learnloop/learner/learner_review_feed|learnloop.learner.learner_review_feed]] — imports `surfaced_belief_corrections`; statically calls `surfaced_belief_corrections`
- [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] — imports `record_belief_withdrawal`; statically calls `record_belief_withdrawal`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `surfaced_belief_corrections`; statically calls `surfaced_belief_corrections`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `mark_belief_surfaced`; statically calls `mark_belief_surfaced`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]], [[Reference/Modules/learnloop/learner/hypothesis_claims|learnloop.learner.hypothesis_claims]], [[Reference/Modules/learnloop/learner/independence_audit|learnloop.learner.independence_audit]], [[Reference/Modules/learnloop/learner/learner_review_feed|learnloop.learner.learner_review_feed]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_durable_promotion_arms.py](../../../../../../tests/test_durable_promotion_arms.py) — direct import
  - `test_an_overturning_verdict_withdraws_a_surfaced_belief_once`
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
  - `test_a_belief_never_surfaced_is_not_a_harmful_write`
  - `test_harmful_write_rate_counts_a_surfaced_then_withdrawn_belief`
  - `test_supersession_is_not_harm_and_is_reported_separately`
- [tests/test_surfaced_belief_corrections.py](../../../../../../tests/test_surfaced_belief_corrections.py) — direct import
  - `test_a_belief_cannot_supersede_itself`
  - `test_a_second_disposition_is_a_second_fact_not_a_re_narration`
  - `test_an_untyped_reason_is_refused`
  - `test_belief_reference_resolution_covers_the_shapes_in_production`
  - `test_each_reason_maps_to_its_own_stated_wording`
  - `test_mark_belief_surfaced_declines_to_flag_an_unquotable_claim`
  - `test_mark_belief_surfaced_is_idempotent_on_a_read_path`
  - `test_never_surfaced_belief_yields_no_correction`
  - `test_presented_but_never_visible_is_not_surfaced`
  - `test_repeated_presentation_keeps_the_first_wording_and_exposure`
  - `test_replacement_belief_is_not_itself_withdrawn`
  - `test_rereading_the_feed_never_duplicates_the_correction`
  - `test_structured_claim_ref_from_the_feedback_surface_still_joins`
  - `test_supersession_with_a_replacement_still_narrates_the_withdrawal`
  - `test_suppressed_card_was_authored_not_shown`
  - `test_surfaced_then_retired_yields_one_correction_in_the_shown_words`
  - `test_surfacing_after_the_withdrawal_does_not_retroactively_owe_an_apology`
  - `test_the_four_reasons_are_exactly_a6s_vocabulary`
  - `test_withdrawal_drops_the_belief_from_working_hypotheses`
  - `test_withdrawals_interleave_reverse_chronologically`

## Modification guidance

- Change surfaced beliefs policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/surfaced_beliefs.py](../../../../../../src/learnloop/learner/surfaced_beliefs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
