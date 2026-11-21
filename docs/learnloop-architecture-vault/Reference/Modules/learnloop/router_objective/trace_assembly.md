---
title: "learnloop.router_objective.trace_assembly"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/trace_assembly.py"
source_paths:
  - "src/learnloop/router_objective/trace_assembly.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.trace_assembly module"
  - "src/learnloop/router_objective/trace_assembly.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.trace_assembly`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.trace_assembly` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: The objective router's decision trace, assembled: what one decision read, valued and drew, so its terms and its probabilities recompute from the trace alone.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/trace_assembly.py](../../../../../../src/learnloop/router_objective/trace_assembly.py) |
| Source lines | 442 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `option_kind(ref: str, candidate: Any) -> str | None` ([source](../../../../../../src/learnloop/router_objective/trace_assembly.py), line 44) — Stop, a lesson offer or a block, from the option's own fields; None for a ref with no candidate.
- `option_label(kind: str | None, candidate: Any, titles: Mapping[str, str]) -> str | None` ([source](../../../../../../src/learnloop/router_objective/trace_assembly.py), line 54) — The option's plain label in the trace.
- `candidate_row(ref: str, candidate: Any, *, titles: Mapping[str, str], valued: Any, action: Any, numeric: Any, topic_by_lo: Mapping[str, Any], miss_cause: Mapping[str, Any] | None, miss_topics: Mapping[str, Any], llm: Any, llm_parsed: Any, v: float | None, stop_q: float | None, top: Any, residual_applied: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/trace_assembly.py), line 69) — One option's row: its label, the numeric policy's action and terms for it, the sensors those read, the LLM's forecast for it, and, for a lesson offer, the offer's own section (:func:`_offer_trace`).
- `goal_dates(numeric: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/trace_assembly.py), line 149) — RO5 §9 item 3's sensor input: each active dated goal's uses with the memory model's frozen forecast at the goal's date (``m⁰``, from the pre-action belief under the tail, the same number the policy comparison logs) and the goal's absolute ``due_at``, for every dated goal the rol…
- `failure_rule_field(to_other: bool) -> dict[str, str]` ([source](../../../../../../src/learnloop/router_objective/trace_assembly.py), line 229) — IH5: the failure rule a decision was drawn under, logged only where it is not staged's (a record without the key was drawn before the tag, or with the switch off, and replays under staged's rule: ``mix.recompute``).
- `decision_trace(*, support: Sequence[str], by_id: Mapping[str, Any], feasible: Sequence[Any], titles: Mapping[str, str], numeric: Any, llm: Any, decider: Any, staged_ref: str, weight: tuple[float, Mapping[str, Any]], effective: Mapping[str, float], pi: Mapping[str, float], drawn: Any, seed: str, config: Any, now_iso: str, guard: Mapping[str, Any], stop_in_support: bool, card_version: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/trace_assembly.py), line 236) — The trace's common part for one decision (a block boundary's or a mid-block one's): every option's row (:func:`candidate_row`), the numeric policy's evaluation, both policies, the mix and its draw, the evaluation's uses and window, and the versions it was valued under.
- `objective_trace(choice: Any, *, support: Sequence[str], by_id: Mapping[str, Any], feasible: Sequence[Any], titles: Mapping[str, str], numeric: Any, llm: Any, decider: Any, staged_ref: str, weight: tuple[float, Mapping[str, Any]], seed: str, config: Any, now_iso: str, card_version: str | None, policy_card: Mapping[str, Any], contested: str | None, read_carried_for: Callable[[], Sequence[Mapping[str, Any]]] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/trace_assembly.py), line 394) — A block boundary's trace, from its choice (``choose.Choice``) and what the chooser read for it: the numeric policy's answer, the two models' results, the weight, the mix's seed, the LLM's card (``policy_card``) and the IH2 contest's follow-up (``contested``).

### Module constants

- `MISS_CAUSE_SOURCE` ([src/learnloop/router_objective/trace_assembly.py](../../../../../../src/learnloop/router_objective/trace_assembly.py), line 39)

### Explicit exports

`__all__` declares:

- `LESSON_OFFER_SUBTYPE`
- `MISS_CAUSE_SOURCE`
- `STOP_FOR_TODAY`
- `candidate_row`
- `decision_trace`
- `failure_rule_field`
- `goal_dates`
- `objective_trace`
- `option_kind`
- `option_label`

## Internal implementation anchors

- `_serving_switches(config: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/trace_assembly.py), line 131) — The trace's ``versions.serving_switches`` (landing ruling R8), or nothing below the batch's tag.
- `_score_note(config: Any) -> str` ([source](../../../../../../src/learnloop/router_objective/trace_assembly.py), line 140)
- `_offer_trace(candidate: Any, valued: Any, action: Any, inputs: Any, topic_by_lo: Mapping[str, Any], terms: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/trace_assembly.py), line 170) — Teacher TE3b (spec_teacher_v1 rev 5 §15.1a, "what the trace records"): for a lesson offer, its sensors (``P(accept)`` with its posterior mean and sd and the priors version, the reason, AD's ``p̄`` for the target, the lesson curve's moments and version or ``placeholder``, the les…

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `decision_trace`, `failure_rule_field`, `objective_trace`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/router/requests|learnloop.router.requests]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/ad_link|learnloop.router_objective.ad_link]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/check_replay|learnloop.router_objective.check_replay]] — imports `TRACE_KEY`
- [[Reference/Modules/learnloop/router_objective/choose|learnloop.router_objective.choose]] — imports `ANSWERED`, `NOT_READY`
- [[Reference/Modules/learnloop/router_objective/mix|learnloop.router_objective.mix]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/objective|learnloop.router_objective.objective]] — imports `module`; calls `paired_standard_error`
- [[Reference/Modules/learnloop/router_objective/preferences|learnloop.router_objective.preferences]] — imports `module`; calls `with_values`
- [[Reference/Modules/learnloop/router_objective/price|learnloop.router_objective.price]] — imports `module`; calls `guard_minutes`
- [[Reference/Modules/learnloop/router_objective/rollouts|learnloop.router_objective.rollouts]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]] — imports `module`; calls `candidate_terms`
- [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]] — imports `LESSON_OFFER_SUBTYPE`, `STOP_FOR_TODAY`, `module`; calls `is_offer_subtype`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `CHECKS_OFF`, `check_mode`, `failure_share_to_other_policy_on`, `followup_generator_switches`; calls `check_mode`, `failure_share_to_other_policy_on`, `followup_generator_switches`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_action_kinds_complete.py](../../../../../../tests/test_action_kinds_complete.py) — direct import
  - `test_a_plan_candidates_trace_label_and_reversibility`
  - `test_stops_trace_label_and_support`
- [tests/test_check_credit_activation.py](../../../../../../tests/test_check_credit_activation.py) — direct import
  - `test_both_tags_the_decisions_numeric_answer_and_its_trace`
- [tests/test_ih5_successor.py](../../../../../../tests/test_ih5_successor.py) — direct import
  - `test_switch_off_or_below_the_tag_the_mix_is_the_predecessors_exactly`
- [tests/test_objective_trace.py](../../../../../../tests/test_objective_trace.py) — direct import
  - `test_each_option_is_told_apart_by_its_own_fields_and_labelled`
  - `test_the_failure_rule_is_logged_only_where_it_is_not_stageds`
  - `test_the_names_it_repeats_are_the_plans`
  - `test_with_no_numeric_answer_the_trace_keeps_its_keys_in_order_and_each_row_its_own`
- [tests/test_ro5_codex_review.py](../../../../../../tests/test_ro5_codex_review.py) — direct import
  - `test_f7_the_trace_freezes_every_dated_goals_forecast_beyond_the_window`
- [tests/test_router_sampling_points.py](../../../../../../tests/test_router_sampling_points.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains trace assembly within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/trace_assembly.py](../../../../../../src/learnloop/router_objective/trace_assembly.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
