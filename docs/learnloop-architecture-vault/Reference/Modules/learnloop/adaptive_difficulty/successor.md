---
title: "learnloop.adaptive_difficulty.successor"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/successor.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/successor.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.successor module"
  - "src/learnloop/adaptive_difficulty/successor.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.successor`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.successor` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The AD2+AD3 successor's gate and its six switches (spec_adaptive_difficulty_v1 §11.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/successor.py](../../../../../../src/learnloop/adaptive_difficulty/successor.py) |
| Source lines | 151 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `successor_active(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 44) — At the successor's tag or later, with the master switch on.
- `switch_on(config: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 51) — One of the six switches, read only at the tag (below it: off).
- `selection_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 59)
- `generation_contract_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 63)
- `subject_view_live(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 67) — Live decisions read the subject view (``promoted_predictor``).
- `coupling_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 73)
- `reading_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 77)
- `verdicts_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 81)
- `lesson_opportunities_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 88) — Teacher TE3a (spec_teacher_v1 rev 5 §14.2): lesson opportunities are swept, applied by the subject view and read by the objective's lesson interface.
- `dose_offers_on(config: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 101) — The Reader's dose arm (outside the successor; every version).
- `history_fallback(config: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 110) — How AD reads a historical attempt whose exact item revision was not saved (``adaptive_difficulty.history_fallback``; owner decision 2026-10-19): ``"current_content"`` (the default) reads it against today's item text, ``"exclude"`` leaves it out.
- `settings(config: Any) -> dict[str, bool]` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 123)

### Module constants

- `SUCCESSOR` ([src/learnloop/adaptive_difficulty/successor.py](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 34)
- `SWITCHES` ([src/learnloop/adaptive_difficulty/successor.py](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 35)
- `DOSE_SWITCH` ([src/learnloop/adaptive_difficulty/successor.py](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 37)
- `LESSON_SWITCH` ([src/learnloop/adaptive_difficulty/successor.py](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 85)
- `HISTORY_FALLBACKS` ([src/learnloop/adaptive_difficulty/successor.py](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 107)

### Explicit exports

`__all__` declares:

- `DOSE_SWITCH`
- `HISTORY_FALLBACKS`
- `LESSON_SWITCH`
- `SUCCESSOR`
- `SWITCHES`
- `coupling_on`
- `dose_offers_on`
- `generation_contract_on`
- `history_fallback`
- `lesson_opportunities_on`
- `reading_on`
- `selection_on`
- `settings`
- `subject_view_live`
- `successor_active`
- `switch_on`
- `verdicts_on`

## Internal implementation anchors

- `_section(config: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/successor.py), line 40)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]] — imports `history_fallback`; statically calls `history_fallback`
- [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]] — imports `dose_offers_on`; statically calls `dose_offers_on`
- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `generation_contract_on`, `successor_active`; statically calls `generation_contract_on`, `successor_active`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]] — imports `lesson_opportunities_on`; statically calls `lesson_opportunities_on`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `lesson_opportunities_on`; statically calls `lesson_opportunities_on`
- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `lesson_opportunities_on`, `subject_view_live`; statically calls `lesson_opportunities_on`, `subject_view_live`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `lesson_opportunities_on`; statically calls `lesson_opportunities_on`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `switch_on`; statically calls `switch_on`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness_jobs|learnloop.adaptive_difficulty.relatedness_jobs]] — imports `coupling_on`; statically calls `coupling_on`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `history_fallback`, `lesson_opportunities_on`, `successor_active`; statically calls `history_fallback`, `lesson_opportunities_on`, `successor_active`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `successor_active`; statically calls `successor_active`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `coupling_on`, `selection_on`, `subject_view_live`, `successor_active`; statically calls `coupling_on`, `selection_on`, `subject_view_live`, `successor_active`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `selection_on`; statically calls `selection_on`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `subject_view_live`; statically calls `subject_view_live`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `subject_view_live`; statically calls `subject_view_live`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `ad_enabled`; calls `ad_enabled`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `ADAPTIVE_DIFFICULTY_ALGORITHM_VERSION`, `ADAPTIVE_DIFFICULTY_VERSIONS`, `LESSON_OPPORTUNITY_VERSIONS`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]], [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]], [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]], [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]], [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_owner_decisions.py](../../../../../../tests/test_ad23_owner_decisions.py) — direct import
  - `test_the_owner_defaults_of_2026_10_19`
- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — direct import
  - `test_below_the_tag_every_switch_reads_off_whatever_the_config_says`
  - `test_new_vaults_start_at_the_successor_with_every_switch_on`
  - `test_the_switches_compose`
- [tests/test_ad_guard_offer_receipts.py](../../../../../../tests/test_ad_guard_offer_receipts.py) — direct import
  - `test_the_fix_changes_serving_on_the_affected_shape_and_the_switches_restore_the_refusal_state`
- [tests/test_te3a_successor.py](../../../../../../tests/test_te3a_successor.py) — direct import
  - `test_the_gate_reads_off_below_the_tag_switched_off_and_with_ad_off`
  - `test_the_switch_defaults_on_and_is_classified`
- [tests/test_teacher_te1b_review_fixes.py](../../../../../../tests/test_teacher_te1b_review_fixes.py) — direct import
  - `test_below_band_reads_adaptive_difficultys_posterior_not_the_mastery_model`

## Modification guidance

- Make changes here when the responsibility remains successor within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/successor.py](../../../../../../src/learnloop/adaptive_difficulty/successor.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
