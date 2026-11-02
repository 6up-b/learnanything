---
title: "learnloop.tutor.reader_modes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tutor/reader_modes.py"
source_paths:
  - "src/learnloop/tutor/reader_modes.py"
source_commit: "bdd511fa67095e92f3d2221bab84917b8d8cb137"
source_commit_timestamp: "2026-10-26T19:04:43-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.tutor"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.tutor.reader_modes module"
  - "src/learnloop/tutor/reader_modes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-tutor"
---

# `learnloop.tutor.reader_modes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.tutor.reader_modes` exists within [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] to own the behavior summarized by its module contract: Reader workbench RW1c: the Reader tutor's three answer modes (spec_reader_workbench_v1 §4.6).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tutor/reader_modes.py](../../../../../../src/learnloop/tutor/reader_modes.py) |
| Source lines | 765 |
| Owning package | [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `bdd511fa67095e92f3d2221bab84917b8d8cb137` |
| Commit timestamp | `2026-10-26T19:04:43-04:00` |

## Public API

- `class BoundAsk` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 62) — A Reader question a workbench session binds to a practice item, derived on the server and validated (``handlers.reader_tutor.bound_ask``).
  - `hint_equivalent(self, substantive: bool) -> bool` (line 104; public) — The bound row's hint flag, the one value stored and returned (R1).
- `withhold(texts: Sequence[str], binding: BoundAsk | None, *, placeholders: Sequence[str] | None=None, already: Collection[int]=(), fixed: Collection[int]=()) -> set[int]` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 127) — The indexes of the model-written ``texts`` one model call carries to withhold under the binding.
- `withhold_for_call(slots: Sequence[Slot], binding: BoundAsk | None, *, placeholders: Mapping[str, str] | None=None, already: Mapping[str, Collection[int]] | None=None, fixed: Collection[str]=()) -> dict[str, set[int]]` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 166) — The withheld indexes, per slot, of ONE model call (fix round 7, R1).
- `fit_slots(learner: str, slots: Sequence[str], *, limit: int, join: str=' ') -> tuple[str, list[int]]` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 194) — A model-bound string of at most ``limit`` characters: the learner's own text, then WHOLE model-written ``slots``; ``(text, indexes of the slots in it)``.
- `whole_token_cut(text: str, limit: int) -> str` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 225) — ``text`` on one line within ``limit`` characters, cut only at a space where every group is closed (fix round 10, R1; fix round 11, R4): a token, a number or a LaTeX group is never split ("2/130" never becomes "2/13").
- `open_question_work(gaps: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 283) — The bridge's open-question lines for these gap statements (the first :data:`QUERY_GAPS`).
- `class BoundDelivery` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 309) — What a bound request delivers to its model calls, from ONE withheld set (fix round 7, R1).
  - `lookup_inputs(self) -> dict[str, Any]` (line 341; public)
- `plan_bound_delivery(binding: BoundAsk | None, *, thread: Sequence[Mapping[str, Any]], gaps: Sequence[Mapping[str, Any]]=(), misconceptions: Sequence[Any] | None=None, learner_work: Sequence[Mapping[str, Any]]=(), query_learner: str | None=None, query_limit: int | None=None, practice_question_limit: int | None=None) -> BoundDelivery` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 346) — Every model-written text a bound request delivers, withheld once (fix round 7, R1).
- `guard_thread(thread: Sequence[Mapping[str, Any]], binding: BoundAsk | None) -> tuple[list[dict[str, Any]], int]` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 500) — The thread alone (a call that carries no other model-written text, retrieval off): :func:`plan_bound_delivery`'s ``thread`` and how many earlier answers it left out.
- `class ReaderTutorRequest` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 509) — What the adapter hands ``tutor_qa.ask_question(reader_tutor=...)``.
- `run_retrieval(request: ReaderTutorRequest, inputs: Mapping[str, Any] | None=None) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 552) — The injected retrieval; any failure keeps today's delivery (retrieval is context).
- `deliver(reader_spans: Sequence[Mapping[str, Any]], retrieved: Sequence[Mapping[str, Any]], *, budget_tokens: int, withheld: Any=None) -> tuple[list[dict[str, Any]], dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 566) — The selection and its neighbours first, then each retrieved passage not already delivered, within the context budget (the citation allowlist keeps the selection first, §4.6).
- `verify_excerpt(excerpt: Any, spans: Sequence[Mapping[str, Any]], *, withheld: Any=None, item: Any=None) -> tuple[dict[str, Any] | None, str | None]` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 595) — ``(excerpt, None)`` when it quotes a passage the tutor was given, else ``(None, why)``.
- `finalize(answer: Any, spans: Sequence[Mapping[str, Any]], citations: list[dict[str, Any]], *, retrieval: Mapping[str, Any], request: ReaderTutorRequest, withheld: Any=None, item: Any=None) -> tuple[dict[str, Any], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 632) — The answer's modes and the citations shown: ``(view, citations)``.
- `displayed_text(answer_md: str | None, view: Mapping[str, Any] | None, *, excerpt: bool=True) -> str` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 719) — Everything a Reader answer shows as text: the explanation, the excerpt and the bridge.
- `delivery_receipt(receipt: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 732) — The delivery's receipt when it records something (a trim, a drop, a retrieved passage added).

### Module constants

- `ABSTENTION_LINE` ([src/learnloop/tutor/reader_modes.py](../../../../../../src/learnloop/tutor/reader_modes.py), line 41)
- `ALTERNATIVE_ABSTENTION_LINE` ([src/learnloop/tutor/reader_modes.py](../../../../../../src/learnloop/tutor/reader_modes.py), line 44)
- `MODES` ([src/learnloop/tutor/reader_modes.py](../../../../../../src/learnloop/tutor/reader_modes.py), line 47)
- `MIN_EXCERPT_CHARS` ([src/learnloop/tutor/reader_modes.py](../../../../../../src/learnloop/tutor/reader_modes.py), line 49)
- `MAX_EXCERPT_CHARS` ([src/learnloop/tutor/reader_modes.py](../../../../../../src/learnloop/tutor/reader_modes.py), line 51)
- `MAX_BRIDGE_CHARS` ([src/learnloop/tutor/reader_modes.py](../../../../../../src/learnloop/tutor/reader_modes.py), line 53)
- `EARLIER_ANSWER_LEFT_OUT` ([src/learnloop/tutor/reader_modes.py](../../../../../../src/learnloop/tutor/reader_modes.py), line 58)
- `_JOIN` ([src/learnloop/tutor/reader_modes.py](../../../../../../src/learnloop/tutor/reader_modes.py), line 124)
- `_MATH_GROUPS` ([src/learnloop/tutor/reader_modes.py](../../../../../../src/learnloop/tutor/reader_modes.py), line 222)
- `QUERY_GAPS` ([src/learnloop/tutor/reader_modes.py](../../../../../../src/learnloop/tutor/reader_modes.py), line 280)

### Explicit exports

`__all__` declares:

- `ABSTENTION_LINE`
- `ALTERNATIVE_ABSTENTION_LINE`
- `BoundAsk`
- `EARLIER_ANSWER_LEFT_OUT`
- `MAX_BRIDGE_CHARS`
- `MAX_EXCERPT_CHARS`
- `MIN_EXCERPT_CHARS`
- `MODES`
- `ReaderTutorRequest`
- `deliver`
- `delivery_receipt`
- `fit_slots`
- `displayed_text`
- `finalize`
- `BoundDelivery`
- `QUERY_GAPS`
- `guard_thread`
- `open_question_work`
- `plan_bound_delivery`
- `run_retrieval`
- `verify_excerpt`
- `whole_token_cut`
- `withhold`
- `withhold_for_call`

## Internal implementation anchors

- `_canonical_record(record: Any) -> Any` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 290) — A misconception record with its statement and correction canonical (the form the plan reads and the verification is sent, fix round 11).
- `_misconception_text(record: Any) -> str` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 301)
- `_normalized(text: str) -> str` ([source](../../../../../../src/learnloop/tutor/reader_modes.py), line 591)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `module`; statically calls `open_question_work`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `module`; statically calls `deliver`, `displayed_text`, `finalize`, `plan_bound_delivery`, `run_retrieval`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `BoundAsk`, `ReaderTutorRequest`; statically calls `BoundAsk`, `ReaderTutorRequest`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `GROUNDING_PASSAGES`
- [[Reference/Modules/learnloop/text_canon|learnloop.text_canon]] — imports `canonical`; calls `canonical`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `FIGURE_GOAL_CHARS`
- [[Reference/Modules/learnloop/tutor/context_delivery|learnloop.tutor.context_delivery]] — imports `apply_budget`, `notable`; calls `apply_budget`, `notable`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_leaks_expected`; calls `span_leaks_expected`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `fit_presented_prompt`; calls `fit_presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `types`, `typing`, `unicodedata`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]], [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]], [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_offers.py](../../../../../../tests/test_figure_offers.py) — direct import
  - `test_the_tutor_view_keeps_a_yes_only_on_a_block_it_cites`
- [tests/test_reader_ca2_one_ask.py](../../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_the_bound_cold_ask_follows_the_rule`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_cut_never_opens_a_group_it_does_not_close`
  - `test_a_placeholder_the_key_matches_is_replaced_by_nothing`
  - `test_a_whole_token_cut_never_splits_a_token_or_a_group`
  - `test_an_answer_split_across_earlier_turns_is_not_delivered_whole`
  - `test_an_earlier_answer_and_a_gap_are_withheld_as_one`
  - `test_an_earlier_answer_is_rechecked_under_the_binding`
  - `test_another_way_drops_a_repeated_excerpt_and_citation`
  - `test_every_sent_model_written_fragment_was_checked`
  - `test_no_bound_model_call_receives_item_text_from_outside_the_plan`
  - `test_the_excerpt_guard_catches_a_short_key`
  - `test_the_fixpoint_reads_the_rebuilt_call_again`
  - `test_the_learner_work_keeps_the_learners_own_steps`
  - `test_the_stem_is_never_withheld`
  - `test_the_verification_union_is_checked_after_fitting`
  - `test_the_verifys_display_math_case_is_cut_before_the_group`
- [tests/test_reader_tutor_retrieval.py](../../../../../../tests/test_reader_tutor_retrieval.py) — direct import
  - `test_another_way_with_nothing_new_says_so_honestly`
  - `test_when_verification_keeps_nothing_the_answer_abstains`

## Modification guidance

- Change reader modes policy here when tutor owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/tutor/reader_modes.py](../../../../../../src/learnloop/tutor/reader_modes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
