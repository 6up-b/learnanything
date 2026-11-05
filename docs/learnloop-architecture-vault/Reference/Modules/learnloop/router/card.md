---
title: "learnloop.router.card"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/card.py"
source_paths:
  - "src/learnloop/router/card.py"
source_commit: "a1ba732a86f8c704cd6e6ee1071bf7a30ad3fb1a"
source_commit_timestamp: "2026-11-04T08:47:30-05:00"
source_worktree_state: "clean"
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
  - "learnloop.router.card module"
  - "src/learnloop/router/card.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router"
---

# `learnloop.router.card`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.card` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: Router R2a: ``LearnerStateCardV1``, the learner as one router decision sees it.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py) |
| Source lines | 648 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a1ba732a86f8c704cd6e6ee1071bf7a30ad3fb1a` |
| Commit timestamp | `2026-11-04T08:47:30-05:00` |

## Public API

- `canonical_json(value: Any) -> str` ([source](../../../../../../src/learnloop/router/card.py), line 74)
- `estimate_tokens(value: Any) -> int` ([source](../../../../../../src/learnloop/router/card.py), line 78) — UTF-8 bytes / 4, rounded up (the Slice 1 estimator the V3 renderer uses).
- `excerpt(text: Any, limit: int) -> str` ([source](../../../../../../src/learnloop/router/card.py), line 85)
- `class CardInputs` ([source](../../../../../../src/learnloop/router/card.py), line 91) — Everything the card renders, gathered and filtered by the caller.
- `class LearnerStateCard` ([source](../../../../../../src/learnloop/router/card.py), line 123)
  - `payload(self) -> dict[str, Any]` (line 131; public) — What the decision stores (``router_decision_payloads``, kind card).
- `render_text(card: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router/card.py), line 196) — The card's text sections (deterministic from the typed card).
- `build_card(inputs: CardInputs, *, token_budget: int=DEFAULT_TOKEN_BUDGET) -> LearnerStateCard` ([source](../../../../../../src/learnloop/router/card.py), line 526) — The card for one decision, within ``token_budget`` (deterministic).

### Module constants

- `CARD_VERSION` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 56)
- `PREDECESSOR_CARD_VERSION` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 58)
- `DEFAULT_TOKEN_BUDGET` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 60)
- `EXCERPT_LIMIT` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 61)
- `STEM_LIMIT` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 62)
- `STATEMENT_LIMIT` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 63)
- `TYPED_SECTIONS` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 68)
- `SUGGESTION_SECTION` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 300)
- `_SUGGESTION_WORDS` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 301)
- `AD_CARD_VERSION` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 384)
- `SUGGESTION_CARD_SUFFIX` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 389)
- `SUGGESTION_RELEASE_CARD_SUFFIX` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 393)
- `MARKS_SECTION` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 399)
- `MARKS_CARD_SUFFIX` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 400)
- `_MARKS_HEADING` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 401)
- `_METADATA_TRUNCATION_KEYS` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 433)
- `READER_SECTION` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 442)
- `_READER_LISTS` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 443)
- `_READER_OLDEST_FIRST` ([src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py), line 447)

### Explicit exports

`__all__` declares:

- `AD_CARD_VERSION`
- `CARD_VERSION`
- `MARKS_CARD_SUFFIX`
- `MARKS_SECTION`
- `SUGGESTION_CARD_SUFFIX`
- `SUGGESTION_RELEASE_CARD_SUFFIX`
- `SUGGESTION_SECTION`
- `PREDECESSOR_CARD_VERSION`
- `CardInputs`
- `DEFAULT_TOKEN_BUDGET`
- `LearnerStateCard`
- `TYPED_SECTIONS`
- `build_card`
- `canonical_json`
- `estimate_tokens`
- `excerpt`
- `render_text`

## Internal implementation anchors

- `_successful(entry: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/router/card.py), line 138)
- `_work_line(entry: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router/card.py), line 142)
- `_lo_line(lo_id: str, row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router/card.py), line 166)
- `_suggestion_lines(entries: Sequence[Mapping[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/router/card.py), line 310)
- `_topics(ids: Any, card: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router/card.py), line 320)
- `_reader_lines(reader: Mapping[str, Any], card: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/router/card.py), line 325) — Reader workbench RW6b part 2 (spec §9.2; router R2): the "Reader activity" section, typed facts in plain words.
- `_marks_lines(entries: Sequence[Mapping[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/router/card.py), line 404)
- `_card_version(inputs: CardInputs, evidence_sections: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../src/learnloop/router/card.py), line 414)
- `_drop_reader_entry(reader: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/router/card.py), line 451) — Remove one entry of the reader section, deterministically, counting it in the section's ``omitted`` (Codex re-review F9): the model-written narrative first, then one entry of the longest list (ties: the later list), its oldest end.
- `_assemble(inputs: CardInputs, work: list[dict[str, Any]], truncation: Mapping[str, Any], confidence: Mapping[str, Sequence[Mapping[str, Any]]] | None=None, confidence_dropped: int=0, *, limit: bool=True, notice: bool=True, evidence_sections: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/card.py), line 478)
- `_drop_oldest_event(confidence: dict[str, list[dict[str, Any]]]) -> bool` ([source](../../../../../../src/learnloop/router/card.py), line 514) — Remove the oldest 7-day confidence event of any topic (each list is newest first); False when none is left.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `CardInputs`, `EXCERPT_LIMIT`, `LearnerStateCard`, `MARKS_SECTION`, `STATEMENT_LIMIT`, `STEM_LIMIT`, `SUGGESTION_SECTION`, `build_card`, `excerpt`; statically calls `CardInputs`, `build_card`, `excerpt`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — direct import
  - `test_readiness_numbers_from_subject_view_with_untested_cells`
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f4_a_card_with_a_released_line_moves_its_version_and_te1bs_card_keeps_its_own`
- [tests/test_followups_batch6_te1b_card.py](../../../../../../tests/test_followups_batch6_te1b_card.py) — direct import
  - `test_a_declined_suggestion_keeps_its_not_now_line`
  - `test_a_reservation_the_app_set_aside_is_not_a_learner_answer`
  - `test_not_now_on_a_pending_card_is_its_own_line_after_the_start`
- [tests/test_hypothesis_marks_context.py](../../../../../../tests/test_hypothesis_marks_context.py) — direct import
  - `test_marks_on_protected_work_keep_the_mark_and_never_the_words`
  - `test_over_budget_the_marks_go_whole_and_the_version_follows`
  - `test_the_card_counts_the_latest_and_takes_back_what_was_cleared`
  - `test_the_card_reads_no_mark_from_after_its_own_decision`
  - `test_with_no_mark_the_card_is_what_it_was_and_a_mark_comes_attributed`
- [tests/test_mcp_c1a_landing.py](../../../../../../tests/test_mcp_c1a_landing.py) — direct import
  - `test_both_readers_render_the_pinned_question_with_its_frozen_method`
- [tests/test_method_explicit_landing.py](../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_the_card_shows_the_frozen_methods_sentence_whole_after_a_shortened_statement`
- [tests/test_router_card.py](../../../../../../tests/test_router_card.py) — direct import
  - `test_over_budget_older_successes_go_first_then_excerpts_then_attempts`
- [tests/test_router_reader_activity.py](../../../../../../tests/test_router_reader_activity.py) — direct import
  - `test_narration_switched_off_after_a_narrative_was_saved_shows_it_nowhere`
  - `test_nothing_to_say_leaves_the_predecessor_card_byte_for_byte`
  - `test_the_budget_trims_reader_entries_deterministically_and_says_so`
  - `test_the_card_copy_is_bounded_and_says_what_it_left_out`
  - `test_the_reader_section_fits_wherever_the_predecessor_card_fits`
  - `test_the_section_is_in_the_typed_card_its_text_and_its_hash`
- [tests/test_teacher_te0_confidence_events.py](../../../../../../tests/test_teacher_te0_confidence_events.py) — direct import
  - `test_card_parity_with_no_confidence_data_only_the_version_moves`
  - `test_the_card_carries_the_events_on_work_lines_and_in_the_seven_day_window`
  - `test_the_gathered_card_renders_taps_and_hedge_reads_as_events`
  - `test_the_gathered_card_without_confidence_data_has_no_confidence_fields`
- [tests/test_teacher_te0_fix_round2.py](../../../../../../tests/test_teacher_te0_fix_round2.py) — direct import
  - `test_the_card_fits_whenever_the_predecessor_fits_across_budgets_and_topic_sizes`
  - `test_the_card_never_exceeds_a_budget_the_predecessor_fits_eight_topics_at_1000`
  - `test_the_metadata_goes_only_after_every_event_and_the_limit_before_the_notice`
- [tests/test_teacher_te0_review_fixes.py](../../../../../../tests/test_teacher_te0_review_fixes.py) — direct import
  - `test_a_card_within_budget_states_no_omission`
  - `test_a_heavy_confidence_week_stays_within_the_card_budget_and_keeps_recent_work`
  - `test_switched_off_the_card_is_the_predecessors_card`
- [tests/test_teacher_te1b_review_fixes.py](../../../../../../tests/test_teacher_te1b_review_fixes.py) — direct import
  - `test_a_chosen_alternative_reads_as_a_choice_over_the_suggestion`
  - `test_the_learners_answers_are_preference_lines_on_the_router_card`

## Modification guidance

- Make changes here when the responsibility remains card within learnloop.router; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router/card.py](../../../../../../src/learnloop/router/card.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
