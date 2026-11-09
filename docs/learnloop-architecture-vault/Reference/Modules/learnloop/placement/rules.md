---
title: "learnloop.placement.rules"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/placement/rules.py"
source_paths:
  - "src/learnloop/placement/rules.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.placement"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.placement.rules module"
  - "src/learnloop/placement/rules.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-placement"
---

# `learnloop.placement.rules`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.placement.rules` exists within [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] to own the behavior summarized by its module contract: Pure placement rules (learner field §5.2): no store, model or vault access.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py) |
| Source lines | 501 |
| Owning package | [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `theta_known(known_probability: float) -> float` ([source](../../../../../../src/learnloop/placement/rules.py), line 71) — logit(known_probability), on the ability scale (field D6: logit(.75)).
- `class AnswerFacts` ([source](../../../../../../src/learnloop/placement/rules.py), line 78) — The facts of one recorded answer that placement reads, and nothing else.
  - `learner_side_clean(self) -> bool` (line 105; public) — No help on the learner's side, whatever the grade: a graded answer type with no hints, priming, "don't know" or assistance.
  - `learner_clean(self) -> bool` (line 118; public) — Full marks with no help on the learner's side: no hints, priming, "don't know", assistance or manual-review flag, on a graded answer whose grade is verified (never a PF-c unverified one).
  - `unassessed(self) -> bool` (line 133; public) — A learner-clean answer whose grade is PF-c unverified: no failure evidence.
  - `is_miss(self) -> bool` (line 141; public) — An answer the learner did not answer cleanly.
  - `graded_miss(self) -> bool` (line 149; public) — A miss whose only problem is the grade: no help on the learner's side, but short of full marks (or flagged for review).
  - `clean_correct(self) -> bool` (line 157; public) — Learner-clean and independent: what fast-track and a quick check count.
  - `as_dict(self) -> dict[str, Any]` (line 162; public)
  - `from_dict(cls, value: Mapping[str, Any]) -> AnswerFacts` (line 166; public)
- `answer_facts(row: Mapping[str, Any], *, contamination_class: str | None=None, grade_unverified: bool=False) -> AnswerFacts | None` ([source](../../../../../../src/learnloop/placement/rules.py), line 170) — Facts of a ``practice_attempts`` row, or None for a non-answer (skip).
- `known_probability(region: RegionEstimate | None, threshold: float) -> float | None` ([source](../../../../../../src/learnloop/placement/rules.py), line 198) — P(theta_L > threshold) under a calibrated region; None when untested.
- `interval_80(region: RegionEstimate | None) -> list[float] | None` ([source](../../../../../../src/learnloop/placement/rules.py), line 213) — The central 80% interval of theta_L, in logits.
- `class FastTrackVerdict` ([source](../../../../../../src/learnloop/placement/rules.py), line 223)
- `fast_track_verdict(answers: Iterable[AnswerFacts], *, blocking_signal_ids: Iterable[str], region: RegionEstimate | None, min_correct: int, q: float, known_threshold: float) -> FastTrackVerdict` ([source](../../../../../../src/learnloop/placement/rules.py), line 230) — Field §5.2 fast-track on an LO's answers so far, in time order.
- `check_verdict(answer: AnswerFacts) -> str` ([source](../../../../../../src/learnloop/placement/rules.py), line 271) — The first review is a normal cold item: the verdict on its grade alone.
- `class MissVerdict` ([source](../../../../../../src/learnloop/placement/rules.py), line 352) — How one miss on an assumed or maintained LO was decided: the receipt.
  - `as_dict(self) -> dict[str, Any]` (line 387; public)
- `diagnosis_reason(attribution_scopes: Mapping[int, str], event_classes: Mapping[int, str], *, unread_fatal_errors: Iterable[str]=()) -> str` ([source](../../../../../../src/learnloop/placement/rules.py), line 403) — The diagnosis's reading of a graded miss (Slice 1 M2 vocabulary).
- `decide_miss(answer: AnswerFacts, graded: Mapping[str, MissVerdict]) -> MissVerdict` ([source](../../../../../../src/learnloop/placement/rules.py), line 439) — A miss (or an unassessed answer) on an assumed or maintained LO.
- `prerequisite_layers(learning_objects: Iterable[str], prerequisites: Mapping[str, Iterable[str]]) -> dict[str, int]` ([source](../../../../../../src/learnloop/placement/rules.py), line 458) — Longest-path depth over the prerequisite edges among ``learning_objects``.
- `new_material_key(*, layer: int, taught_first: bool, predicted_success: float, practice_item_id: str) -> tuple[int, int, float, str]` ([source](../../../../../../src/learnloop/placement/rules.py), line 492) — Prerequisites first, then LOs you asked about, then easiest first.

### Module constants

- `RULES_VERSION` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 45)
- `CLEAN_ATTEMPT_TYPES` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 51)
- `IGNORED_ATTEMPT_TYPES` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 53)
- `ASSISTED_CLASSES` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 55)
- `PFC_UNVERIFIED_BLOCK` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 60)
- `PFC_UNASSESSED_INTERPRETATION_KEY` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 66)
- `PFC_UNASSESSED_INTERPRETATION` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 67)
- `_FULL_MARKS` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 68)
- `CHECK_PASS` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 266)
- `CHECK_FAIL` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 267)
- `CHECK_INELIGIBLE` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 268)
- `MISS_TO_LEARNING` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 304)
- `MISS_KEPT` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 305)
- `MISS_PENDING` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 306)
- `REASON_KNOWLEDGE_GAP` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 316)
- `REASON_SLIP` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 317)
- `REASON_ITEM_CONTRACT` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 318)
- `REASON_INTERACTION_CONTEXT` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 319)
- `REASON_UNASSESSED` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 320)
- `REASON_NO_GAP_ATTRIBUTED` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 321)
- `KEPT_REASONS` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 322)
- `REASON_NO_DIAGNOSIS` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 327)
- `REASON_LEARNER_SIDE` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 328)
- `REASON_DIAGNOSIS_PENDING` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 329)
- `FALLBACK_SPLIT_DISABLED` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 331)
- `FALLBACK_NOT_BLIND_GRADED` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 332)
- `FALLBACK_DIAGNOSIS_FAILED` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 333)
- `FALLBACK_BUDGET_SKIPPED` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 334)
- `FALLBACK_NOT_NEEDED` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 335)
- `FALLBACK_REJECTED` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 336)
- `FALLBACK_NOT_DIAGNOSED` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 337)
- `FALLBACK_DIAGNOSIS_UNAVAILABLE` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 341)
- `DIAGNOSIS_WAIT_DAYS` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 346)
- `ITEM_CONTRACT_SCOPES` ([src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py), line 348)

## Internal implementation anchors

- `_non_gap_reading(scope: str, causal_class: str) -> str | None` ([source](../../../../../../src/learnloop/placement/rules.py), line 391) — One attribution's positive non-gap reading, or None (no reading).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `AnswerFacts`, `RULES_VERSION`, `fast_track_verdict`, `interval_80`, `known_probability`, `theta_known`; statically calls `fast_track_verdict`, `interval_80`, `known_probability`, `theta_known`
- [[Reference/Modules/learnloop/placement/report|learnloop.placement.report]] — imports `RULES_VERSION`
- [[Reference/Modules/learnloop/placement/signals|learnloop.placement.signals]] — imports `AnswerFacts`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `AnswerFacts`, `CHECK_PASS`, `DIAGNOSIS_WAIT_DAYS`, `FALLBACK_BUDGET_SKIPPED`, `FALLBACK_DIAGNOSIS_FAILED`, `FALLBACK_DIAGNOSIS_UNAVAILABLE`, `FALLBACK_NOT_BLIND_GRADED`, `FALLBACK_NOT_DIAGNOSED`, `FALLBACK_NOT_NEEDED`, `FALLBACK_REJECTED`, `FALLBACK_SPLIT_DISABLED`, `KEPT_REASONS`, `MISS_KEPT`, `MISS_PENDING`, `MISS_TO_LEARNING`, `MissVerdict`, `PFC_UNASSESSED_INTERPRETATION`, `PFC_UNASSESSED_INTERPRETATION_KEY`, `PFC_UNVERIFIED_BLOCK`, `REASON_DIAGNOSIS_PENDING`, `REASON_LEARNER_SIDE`, `REASON_NO_DIAGNOSIS`, `answer_facts`, `check_verdict`, `decide_miss`, `diagnosis_reason`, `new_material_key`, `prerequisite_layers`; statically calls `MissVerdict`, `answer_facts`, `check_verdict`, `decide_miss`, `diagnosis_reason`, `new_material_key`, `prerequisite_layers`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `RegionEstimate`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]], [[Reference/Modules/learnloop/placement/report|learnloop.placement.report]], [[Reference/Modules/learnloop/placement/signals|learnloop.placement.signals]], [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
  - `test_fast_track_default_threshold_is_not_met_by_two_answers`
  - `test_fast_track_receipt_recomputes_its_decision`
- [tests/test_curriculum_c1_fix_round3.py](../../../../../../tests/test_curriculum_c1_fix_round3.py) — direct import
  - `test_m2_a_diagnosis_wait_running_out_invalidates_with_no_write`
- [tests/test_curriculum_c1_fix_round4.py](../../../../../../tests/test_curriculum_c1_fix_round4.py) — direct import
- [tests/test_lp_claim_fixes_rereview.py](../../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
  - `test_f9_a_miss_the_diagnosis_timeout_decides_carries_its_line_reopened_after_the_deadline`
- [tests/test_placement_diagnosis_decides.py](../../../../../../tests/test_placement_diagnosis_decides.py) — direct import
  - `test_a_diagnosis_that_never_lands_stops_holding_the_check`
  - `test_a_knowledge_gap_on_the_check_returns_the_lo_to_learning`
  - `test_a_miss_the_diagnosis_does_not_call_a_gap_keeps_the_topic_in_maintenance`
  - `test_learner_side_help_is_not_a_grading_question`
  - `test_no_gap_attributed_is_not_a_pass`
  - `test_the_diagnosis_reading_is_the_m2_vocabulary`
- [tests/test_placement_split_grades.py](../../../../../../tests/test_placement_split_grades.py) — direct import
  - `test_a_pfc_grade_with_another_review_reason_is_still_unassessed`
  - `test_rules_read_an_unverified_grade_as_unassessed`
  - `test_the_pinned_block_reason_is_pfcs`
- [tests/test_stuck_prompt_composition.py](../../../../../../tests/test_stuck_prompt_composition.py) — direct import
  - `test_an_empty_stuck_answer_on_an_assumed_topic_takes_todays_rule_at_once`

## Modification guidance

- Make changes here when the responsibility remains rules within learnloop.placement; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/placement/rules.py](../../../../../../src/learnloop/placement/rules.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
