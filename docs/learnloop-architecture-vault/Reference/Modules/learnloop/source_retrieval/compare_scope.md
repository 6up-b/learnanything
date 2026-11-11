---
title: "learnloop.source_retrieval.compare_scope"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/compare_scope.py"
source_paths:
  - "src/learnloop/source_retrieval/compare_scope.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.compare_scope module"
  - "src/learnloop/source_retrieval/compare_scope.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.compare_scope`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.compare_scope` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Reader CA3: reading the learner's words for a comparison (ux_reader_compare_ask_v1 §4.3, §4.4, §12.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py) |
| Source lines | 546 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Book` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 119) — One book the learner may name: its source, title and file name.
  - `as_dict(self) -> dict[str, Any]` (line 127; public)
- `library_books(vault: Any, repository: Any, scope: Any) -> list[Book]` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 143) — The books the comparison may read (``scope``'s sources), one per source, by title; a source that is exam material whole is never listed (its name is not a passage, but nothing of it can be compared).
- `word_spans(text: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 164) — The words' contiguous spans (the first ``MAX_SPAN_WORDS`` words), each once, edge punctuation trimmed: the options a topic or an unknown book name is chosen from, so either is always the learner's own words.
- `questions_for(mode: str, books: Sequence[Book], spans: Mapping[str, str], *, whole: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 190) — The reading's typed questions (one request).
- `decider_state(text: str, mode: str, current: Sequence[Book]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 228)
- `class Reading` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 240) — One reading of the learner's words: what it found, and why.
  - `as_dict(self) -> dict[str, Any]` (line 262; public)
- `calls_today(repository: Any, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 302) — The route's requests admitted since today's UTC midnight (reserved before sending, so failed and unfinished calls count).
- `books_key(books: Sequence[Book]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 350)
- `input_hash(text: str, mode: str, books: Sequence[Book], current: Sequence[Book]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 354)
- `read(root: Any, config: Any, repository: Any, *, text: str, books: Sequence[Book], mode: str='ask', current_source_ids: Sequence[str]=(), client_factory: Callable[[], Any] | None=None, clock: Clock | None=None, reading_id: str | None=None) -> Reading` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 375) — Read one pressed text of the ask box or the refine box (§4.3, §4.4).
- `record_correction(repository: Any, judgment_id: str, *, source_ids: Sequence[str] | None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 501) — The learner changed the reading: the books they compare instead (a chip removed with ``×``, one added with *+ add a book*), or ``None`` when they pressed *change* to reword it.

### Module constants

- `ROUTE` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 71)
- `TASK` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 72)
- `RECEIPT_OWNER` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 73)
- `QUESTION_SET_VERSION` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 74)
- `LEFT_KIND` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 77)
- `RIGHT_KIND` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 78)
- `ALLOWANCE_TASK` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 80)
- `ALLOWANCE_LEASE_SECONDS` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 81)
- `TEXT_LIMIT` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 83)
- `TITLE_LIMIT` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 84)
- `OTHER_QUESTIONS` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 87)
- `MAX_BOOKS` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 88)
- `MAX_SPAN_WORDS` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 89)
- `MODES` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 91)
- `INTENTS` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 92)
- `CHANGES` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 106)
- `WHOLE` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 114)
- `NONE` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 115)
- `_EDGE` ([src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 161)

### Explicit exports

`__all__` declares:

- `Book`
- `MAX_BOOKS`
- `MAX_SPAN_WORDS`
- `MODES`
- `QUESTION_SET_VERSION`
- `ROUTE`
- `Reading`
- `TASK`
- `calls_today`
- `decider_state`
- `library_books`
- `questions_for`
- `read`
- `record_correction`
- `word_spans`

## Internal implementation anchors

- `_file_name(repository: Any, source_id: str) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 131)
- `_book_question(book: Book) -> NoulQuestion` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 182)
- `_argmax(probabilities: Mapping[str, float]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 271)
- `_named(p_yes: float) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 279) — A book is named when P(yes) beats P(no): the argmax of its two answers.
- `_day(clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 285)
- `_prefix(day: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 289)
- `_used(connection: Any, day: str) -> int` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 293)
- `_reserve(repository: Any, *, reading_id: str, limit: int, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 310) — Claim one request of the day's allowance, or None at ``limit``: the count and the claim are one write transaction, so two readings can never both take the last one (the intent box's rule, Codex review of RW1b F2).
- `_settle(repository: Any, key: str, *, reading_id: str, judgment_id: str | None, sent: bool, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 329)
- `_client(root: Any, config: Any) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 340)
- `_append(repository: Any, reading: Reading, *, verdict: str, model: str, rationale: Mapping[str, Any], right_id: str, left_id: str | None=None, judge: str='decider', supersedes_id: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 359)
- `_row(repository: Any, judgment_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 479)
- `_head(repository: Any, judgment_id: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/compare_scope.py), line 487)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]] — imports `module`; statically calls `Reading`, `library_books`, `read`, `record_correction`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`, `MAX_CHOICE_OPTIONS`, `MAX_QUESTIONS`, `NoulQuestion`, `choice_probabilities`; calls `ChoiceQuestion`, `NoulQuestion`, `choice_probabilities`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`; calls `exam_material`
- [[Reference/Modules/learnloop/db/stores/judgment_claims|learnloop.db.stores.judgment_claims]] — imports `claim_work`, `complete_claim`, `release_claim`; calls `claim_work`, `complete_claim`, `release_claim`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `ask_decider`; calls `ask_decider`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `math`, `pathlib`, `re`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reader_ca3_compare_anywhere_helpers.py](../../../../../../tests/reader_ca3_compare_anywhere_helpers.py) — direct import
- [tests/test_curriculum_c0b_landing.py](../../../../../../tests/test_curriculum_c0b_landing.py) — direct import
  - `test_ii_compare_scope_and_the_scope_resolver_are_separate_routes`
  - `test_ii_compare_scopes_cap_does_not_stop_the_resolver`
  - `test_ii_curriculum_off_leaves_ca3_and_ca5a_as_with_no_deliverable`
  - `test_ii_the_curriculum_cap_does_not_stop_compare_scope`
- [tests/test_reader_ca3_compare_anywhere.py](../../../../../../tests/test_reader_ca3_compare_anywhere.py) — direct import
  - `test_a_reading_names_books_a_topic_and_an_unknown_name`
  - `test_the_days_cap_holds`
  - `test_the_learners_change_is_a_learner_card_row`
  - `test_word_spans_are_the_learners_words_within_the_apis_bound`

## Modification guidance

- Make changes here when the responsibility remains compare scope within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/compare_scope.py](../../../../../../src/learnloop/source_retrieval/compare_scope.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
