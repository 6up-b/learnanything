---
title: "learnloop.hints.maps"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/maps.py"
source_paths:
  - "src/learnloop/hints/maps.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.maps module"
  - "src/learnloop/hints/maps.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.maps`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.maps` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H1: the approach map and its validation in code (spec §4.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py) |
| Source lines | 898 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class MapNode(WireModel)` ([source](../../../../../../src/learnloop/hints/maps.py), line 71)
- `class MapEdge(WireModel)` ([source](../../../../../../src/learnloop/hints/maps.py), line 96)
- `class MapRoute(WireModel)` ([source](../../../../../../src/learnloop/hints/maps.py), line 104)
- `class ApproachMapV1(WireModel)` ([source](../../../../../../src/learnloop/hints/maps.py), line 116)
- `class MergeMatch(WireModel)` ([source](../../../../../../src/learnloop/hints/maps.py), line 127)
- `class MergeNewRoute(WireModel)` ([source](../../../../../../src/learnloop/hints/maps.py), line 133)
- `class LearnerRouteMergeV1(WireModel)` ([source](../../../../../../src/learnloop/hints/maps.py), line 143) — The merge's answer: each new correct attempt either took an existing route or opens a new one (origin ``learner:<attempt ids>``).
- `class MapContext` ([source](../../../../../../src/learnloop/hints/maps.py), line 152) — What a map is checked against: the item and its seeds.
- `class Validation` ([source](../../../../../../src/learnloop/hints/maps.py), line 171)
  - `as_dict(self) -> dict[str, Any]` (line 181; public)
- `leak_expressions(text: str) -> set[str]` ([source](../../../../../../src/learnloop/hints/maps.py), line 205) — The expressions of a leak node's state a label must not contain: its math segments, formulas and numbers (normalized, at least two characters).
- `number_tokens(text: str | None) -> list[str]` ([source](../../../../../../src/learnloop/hints/maps.py), line 310) — The standalone numbers of a text, whole: signed (``-4``), decimal or a whole fraction, whitespace removed and a leading ``+`` dropped.
- `normalize_math(text: str) -> str` ([source](../../../../../../src/learnloop/hints/maps.py), line 333) — The text with Unicode signs written ASCII, its math delimiters (``$…$``, ``\(…\)``, ``\[…\]``) and ``\left``/``\right`` removed and ``\frac{a}{b}`` written ``(a)/(b)``: the one form a state, a label, a structured value and the expected answer are compared in.
- `normalize_key(text: str | None) -> str` ([source](../../../../../../src/learnloop/hints/maps.py), line 353) — An answer or key in the shared form: normalised, whitespace and a leading ``+`` stripped.
- `answer_candidates(text: str) -> list[str]` ([source](../../../../../../src/learnloop/hints/maps.py), line 370) — The expressions a text states, in the shared form: the whole content of every math span (taken before its delimiters are stripped; fix round 3, R2), its standalone signed numbers and whole fractions, the value after each ``=``, and the whole text when it is a short expression.
- `structured_expression(text: str | None) -> str | None` ([source](../../../../../../src/learnloop/hints/maps.py), line 391) — A structured field (a node's ``value``, the goal's ``conclusion``) as an expression the guarded checker reads, or None: empty, prose, a quantity with a unit ("4 m"), an equation, or not parseable.
- `states_answer(text: str, key: str | None) -> bool` ([source](../../../../../../src/learnloop/hints/maps.py), line 410) — Whether ``text`` states an expression equivalent to the key, by the guarded answer checker on both sides in the shared form (best-effort prose detection; fix rounds 2 and 3).
- `norm(text: str | None) -> str` ([source](../../../../../../src/learnloop/hints/maps.py), line 440) — The answer as a comparable string (fix round 5): math delimiters, ``\text{}``, ``\mathrm{}``, ``\,`` and ``~`` stripped, Unicode superscripts written ``^n`` and Unicode signs ASCII, whitespace collapsed to single spaces and trimmed.
- `quantity_shaped(reference: str | None) -> bool` ([source](../../../../../../src/learnloop/hints/maps.py), line 453) — Whether ``norm(reference)`` is a number, whitespace, then a token starting with a non-digit (fix round 5).
- `structured_verdict(expression: str | None, unit: str | None, key: str) -> tuple[str, str]` ([source](../../../../../../src/learnloop/hints/maps.py), line 465) — ``(verified | mismatch | unverified, basis)`` for a structured ``conclusion`` (or ``value``) with its ``unit`` against the exact key (fix round 5).
- `value_states_answer(value: str | None, unit: str | None, key: str | None) -> bool` ([source](../../../../../../src/learnloop/hints/maps.py), line 495) — A structured ``value`` is a leak when the goal rules would verify it as the goal, or when ``norm(value)`` equals ``norm(key)`` (fix round 5; conservative).
- `gives_away(text: str, expected_answer: str | dict[str, Any], key: str | None=None) -> bool` ([source](../../../../../../src/learnloop/hints/maps.py), line 505) — Whether ``text`` contains or gives away the expected answer: the tutor's span-leak check against the whole answer and, where the answer has an exact key (a worked solution's final value), against the key; a lone-digit key, which the span check ignores, by its own number token; a…
- `label_leaks(label: str, expressions: Collection[str], expected_answer: str | dict[str, Any], *, public_text: str='') -> bool` ([source](../../../../../../src/learnloop/hints/maps.py), line 519)
- `exact_key(expected_answer: str | dict[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/hints/maps.py), line 542) — The expected answer's exact key: the answer itself when it is a short parseable expression (in the shared form when only that parses: ``$\frac{1}{4}$``), else the numeric conclusion a worked solution ends with (``answer_check``, on the text or its shared form), else None (a proo…
- `goal_agreement(conclusion: str, expected_answer: str | dict[str, Any], unit: str='') -> tuple[str, str]` ([source](../../../../../../src/learnloop/hints/maps.py), line 616) — ``(verified | unverified | mismatch, basis)``: the goal node's structured ``conclusion`` against the expected answer's exact key (§4.3; fix round 3, R1).
- `validate_map(candidate: ApproachMapV1, context: MapContext) -> Validation` ([source](../../../../../../src/learnloop/hints/maps.py), line 681) — Every rule of §4.3's "validation in code"; failures by reason.
- `apply_merge(current: ApproachMapV1, merge: LearnerRouteMergeV1, *, attempt_refs: Mapping[str, str]) -> tuple[ApproachMapV1, list[str], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/hints/maps.py), line 799) — The current map with the learner's new routes (§4.3 "approach mining").
- `route_counts(map_payload: Mapping[str, Any]) -> dict[str, int]` ([source](../../../../../../src/learnloop/hints/maps.py), line 857) — Routes by origin kind (reference, trace_contract, skeleton, source, model, learner).

### Module constants

- `MAP_SCHEMA_VERSION` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 43)
- `REASONS` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 46)
- `PLAIN_ORIGINS` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 68)
- `_MATH` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 193)
- `_NUMBER` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 196)
- `_FORMULA` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 198)
- `_LONE_DIGIT_KEY` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 222)
- `_MATH_SPAN` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 247)
- `_DELIMITERS` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 248)
- `_LEFT_RIGHT` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 249)
- `_FRAC` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 250)
- `_SIGNS` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 252)
- `_EQUALS` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 255)
- `_NUMBER_CANDIDATE` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 258)
- `_ATTACHED_LEFT` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 261)
- `_ATTACHED_RIGHT` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 262)
- `_PROSE_WORD` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 321)
- `_MATH_NAMES` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 322)
- `_SINGLE_SYMBOL` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 323)
- `_QUANTITY` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 325)
- `_CANDIDATE_CHARS` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 326)
- `_TEXT_MARKUP` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 429)
- `_SUPERSCRIPTS` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 430)
- `_SUPERSCRIPT_RUN` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 432)
- `_QUANTITY_SHAPED` ([src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py), line 435)

### Explicit exports

`__all__` declares:

- `MAP_SCHEMA_VERSION`
- `PLAIN_ORIGINS`
- `REASONS`
- `ApproachMapV1`
- `LearnerRouteMergeV1`
- `MapContext`
- `MapEdge`
- `MapNode`
- `MapRoute`
- `MergeMatch`
- `MergeNewRoute`
- `Validation`
- `answer_candidates`
- `apply_merge`
- `exact_key`
- `gives_away`
- `goal_agreement`
- `label_leaks`
- `leak_expressions`
- `normalize_key`
- `normalize_math`
- `route_counts`
- `norm`
- `number_tokens`
- `quantity_shaped`
- `states_answer`
- `structured_expression`
- `structured_verdict`
- `value_states_answer`
- `validate_map`

## Internal implementation anchors

- `_squash(text: str) -> str` ([source](../../../../../../src/learnloop/hints/maps.py), line 201)
- `_states_short_key(text: str, key: str | None) -> bool` ([source](../../../../../../src/learnloop/hints/maps.py), line 225) — Whether ``text`` states a lone-digit key as a number of its own (Codex review F1): "4" in "The count is 4" or "$x = 4$", never inside "14", "4.5", "3/4", "x_4" or "2^4".
- `_skip_left(text: str, index: int) -> int` ([source](../../../../../../src/learnloop/hints/maps.py), line 265) — The index of the first non-space character left of ``index`` (-1 if none).
- `_skip_right(text: str, index: int) -> int` ([source](../../../../../../src/learnloop/hints/maps.py), line 274)
- `_standalone(text: str, match: re.Match[str]) -> bool` ([source](../../../../../../src/learnloop/hints/maps.py), line 280) — Whether a number candidate is a number of its own (fix round 5, U4): a scan across ANY whitespace on both sides, never fixed-width lookbehinds.
- `_signs(text: str | None) -> str` ([source](../../../../../../src/learnloop/hints/maps.py), line 329)
- `_clean(expression: str) -> str` ([source](../../../../../../src/learnloop/hints/maps.py), line 346)
- `_cut_prose(expression: str) -> str` ([source](../../../../../../src/learnloop/hints/maps.py), line 359) — An expression up to the first prose word or clause break after it.
- `_with_unit(expression: str | None, unit: str | None) -> str` ([source](../../../../../../src/learnloop/hints/maps.py), line 460)
- `_equal(left: str, right: str) -> bool | None` ([source](../../../../../../src/learnloop/hints/maps.py), line 565)
- `_case_only(left: str, right: str) -> bool` ([source](../../../../../../src/learnloop/hints/maps.py), line 572) — Whether two expressions differ only in letter case, which answer_check's text shortcut (``casefold``) would call equal.
- `_structured_equal(left: str, right: str) -> bool | None` ([source](../../../../../../src/learnloop/hints/maps.py), line 580) — Case-sensitive mathematical equality for the structured map fields (fix round 6, C1): ``2X`` is never ``2x``.
- `_structured_differ(left: str, right: str) -> bool | None` ([source](../../../../../../src/learnloop/hints/maps.py), line 600) — The case-sensitive counterpart of ``answers_differ`` (C1).
- `_differ(left: str, right: str) -> bool | None` ([source](../../../../../../src/learnloop/hints/maps.py), line 609)
- `_has_cycle(node_ids: Sequence[str], edges: Sequence[MapEdge]) -> bool` ([source](../../../../../../src/learnloop/hints/maps.py), line 642)
- `_origin(origin: str, context: MapContext, reasons: list[str], details: list[dict[str, Any]], route_id: str) -> str` ([source](../../../../../../src/learnloop/hints/maps.py), line 660) — The stored origin (refs replaced by ids), recording an unknown one.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/contracts|learnloop.hints.contracts]] — imports `exact_key`, `gives_away`, `label_leaks`, `leak_expressions`, `number_tokens`; statically calls `exact_key`, `gives_away`, `label_leaks`, `leak_expressions`, `number_tokens`
- [[Reference/Modules/learnloop/hints/discriminating|learnloop.hints.discriminating]] — imports `norm`; statically calls `norm`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `ApproachMapV1`, `LearnerRouteMergeV1`, `MapContext`, `Validation`, `apply_merge`, `route_counts`, `validate_map`; statically calls `MapContext`, `apply_merge`, `route_counts`, `validate_map`
- [[Reference/Modules/learnloop/hints/map_report|learnloop.hints.map_report]] — imports `REASONS`, `route_counts`; statically calls `route_counts`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `exact_key`, `gives_away`; statically calls `exact_key`, `gives_away`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/attempts/answer_check|learnloop.attempts.answer_check]] — imports `answers_differ`, `answers_equal`, `parse_answer`, `reference_final_answer`, `safe_math_text`; calls `answers_differ`, `answers_equal`, `parse_answer`, `reference_final_answer`, `safe_math_text`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_leaks_expected`; calls `span_leaks_expected`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/contracts|learnloop.hints.contracts]], [[Reference/Modules/learnloop/hints/discriminating|learnloop.hints.discriminating]], [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]], [[Reference/Modules/learnloop/hints/map_report|learnloop.hints.map_report]], [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/approach_map_fakes.py](../../../../../../tests/approach_map_fakes.py) — direct import
- [tests/test_approach_maps.py](../../../../../../tests/test_approach_maps.py) — direct import
  - `test_a_build_stores_one_validated_version_with_its_receipt_and_verdict`
  - `test_c3_a_leading_dot_decimal_quantity_is_kept_whole`
  - `test_f1_a_single_digit_answer_marks_its_node_and_fails_a_label_that_states_it`
  - `test_f3_a_lapsed_claim_of_a_dead_process_is_taken_over_and_fences_its_commit`
  - `test_m1_a_single_symbol_answer_is_a_token_match_never_a_substring`
  - `test_m3_an_expired_claim_writes_no_judgment_and_stores_nothing`
  - `test_r1_the_builders_output_schema_requires_the_structured_fields`
  - `test_r3_a_close_while_a_write_waits_for_the_lock_lands_nothing`
  - `test_r5_a_denominator_after_any_whitespace_is_not_the_answer`
  - `test_u2_close_never_waits_past_its_bound_on_a_commit_held_by_a_reader`
  - `test_u4_a_spaced_sign_stays_attached`

## Modification guidance

- Make changes here when the responsibility remains maps within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/maps.py](../../../../../../src/learnloop/hints/maps.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
