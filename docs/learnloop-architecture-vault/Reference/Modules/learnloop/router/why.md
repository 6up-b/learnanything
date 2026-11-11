---
title: "learnloop.router.why"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/why.py"
source_paths:
  - "src/learnloop/router/why.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router.why module"
  - "src/learnloop/router/why.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router"
---

# `learnloop.router.why`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.why` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: Router R2a: the learner-facing "why" of a plan block, in plain words.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py) |
| Source lines | 340 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `jargon_in(text: str) -> list[str]` ([source](../../../../../../src/learnloop/router/why.py), line 128) — The internal terms ``text`` shows, in deny-list order.
- `topic_phrase(titles: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/router/why.py), line 134) — "Eigenvalues", "Eigenvalues and Bases", "Eigenvalues and 2 more topics".
- `sentence(code: str, *, topic: str | None=None, section: str | None=None) -> str` ([source](../../../../../../src/learnloop/router/why.py), line 147) — The plain sentence for a reason code ("" for an unknown code).
- `stop_code(minutes_left: float, stop_offer_minutes: float) -> str` ([source](../../../../../../src/learnloop/router/why.py), line 162)
- `model_why(component: str, rule_sentence: str, *, option_count: int, rationale: str | None=None, rationale_shown: bool=False) -> tuple[str, str]` ([source](../../../../../../src/learnloop/router/why.py), line 202) — ``(why, why_kind)`` of a block the mixture chose, by the component that drew it.
- `objective_why(component: str, rule_sentence: str, *, option_count: int, rationale: str | None=None, rationale_shown: bool=False) -> tuple[str, str]` ([source](../../../../../../src/learnloop/router/why.py), line 236) — ``(why, why_kind)`` of a block the objective's mix chose (RO4), by the component that drew it: the LLM policy as the mixture's LLM; the numeric policy's estimate (``computed``); staged's rule and the floor as before.
- `rationale_guard(rationale: str | None, evidence_ids: Sequence[str], card_evidence_ids: Sequence[str] | set[str] | frozenset[str], *, max_sentences: int=3) -> str | None` ([source](../../../../../../src/learnloop/router/why.py), line 258) — Why the LLM's rationale may not be shown, or None when it may (plan §7 guards).
- `mixture_details(summary: Mapping[str, Any], *, propensity: Any, decision_ref: str | None) -> str` ([source](../../../../../../src/learnloop/router/why.py), line 287) — The ``details`` line of a block decided under the mixture: plain words, then the receipt.

### Module constants

- `WHY_VERSION` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 26)
- `SENTENCES` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 30)
- `DETAILS_STAGED` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 59)
- `DENY_PATTERNS` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 62)
- `MIXTURE_WHY_VERSION` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 169)
- `MODEL_MARK` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 171)
- `PICKED_BY_MODEL` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 173)
- `PICKED_TO_VARY` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 175)
- `DRAWN_DETAILS` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 178)
- `WEIGHED_DETAILS` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 184)
- `NOT_READY_DETAILS` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 185)
- `ONLY_RULE_DETAILS` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 186)
- `SINGLE_OPTION_DETAILS` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 187)
- `HIDDEN_RATIONALE_DETAILS` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 188)
- `MODEL_NAMES` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 189)
- `FALLBACK_REASONS` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 190)
- `FOLLOWUP_WAITS` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 199)
- `PICKED_BY_ESTIMATE` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 233)
- `_SENTENCE_END` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 254)
- `_PROBABILITY_TEXT` ([src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py), line 255)

### Explicit exports

`__all__` declares:

- `DENY_PATTERNS`
- `DETAILS_STAGED`
- `DRAWN_DETAILS`
- `FALLBACK_REASONS`
- `FOLLOWUP_WAITS`
- `MIXTURE_WHY_VERSION`
- `MODEL_MARK`
- `PICKED_BY_MODEL`
- `PICKED_TO_VARY`
- `SENTENCES`
- `WHY_VERSION`
- `jargon_in`
- `mixture_details`
- `model_why`
- `rationale_guard`
- `sentence`
- `stop_code`
- `objective_why`
- `PICKED_BY_ESTIMATE`
- `topic_phrase`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `objective_why`, `rationale_guard`, `sentence`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `module`; statically calls `model_why`, `rationale_guard`, `sentence`, `stop_code`
- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `module`; statically calls `sentence`, `stop_code`, `topic_phrase`
- [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] — imports `DETAILS_STAGED`, `mixture_details`; statically calls `mixture_details`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]], [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]], [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_the_why_names_the_path_and_stays_plain`
- [tests/test_ro5_landing.py](../../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r5_3_how_was_this_chosen_is_plain_words_with_no_stage_names_or_symbols`
- [tests/test_router_r2b_serving.py](../../../../../../tests/test_router_r2b_serving.py) — direct import
  - `test_a_drawn_llm_pick_shows_its_rationale_and_its_cited_answers`
  - `test_every_details_line_is_plain`
  - `test_every_mixture_why_is_plain`
  - `test_the_daily_guard_refuses_metered_calls_and_never_a_subscription_call`
  - `test_the_rationale_guard`
- [tests/test_router_why_copy.py](../../../../../../tests/test_router_why_copy.py) — direct import
  - `test_a_title_ending_in_its_own_mark_takes_no_extra_period`
  - `test_every_sentence_is_plain`
  - `test_every_why_the_staged_chooser_writes_on_a_plan_is_plain`
  - `test_reason_codes_follow_the_lane_and_its_items`
  - `test_the_deny_list_catches_the_internal_terms`
  - `test_the_details_line_is_plain`
  - `test_topic_phrases_name_one_two_or_many_topics`

## Modification guidance

- Make changes here when the responsibility remains why within learnloop.router; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router/why.py](../../../../../../src/learnloop/router/why.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
