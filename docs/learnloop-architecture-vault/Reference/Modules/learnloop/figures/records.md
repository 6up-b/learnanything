---
title: "learnloop.figures.records"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/records.py"
source_paths:
  - "src/learnloop/figures/records.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.records module"
  - "src/learnloop/figures/records.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.records`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.records` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: The figures' decision records (ADR-017, refactor B4): why a figure was built ahead of need or not, and why an author's attempt was kept or not.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py) |
| Source lines | 582 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `code(value: Any) -> str | None` ([source](../../../../../../src/learnloop/figures/records.py), line 164) — ``value`` when it is an id or a code constant (``provenance.check_no_prose``), else a short hash of it, so a ref that happens to hold text never carries the text and never drops the record.
- `number(value: Any, digits: int | None=None) -> float | None` ([source](../../../../../../src/learnloop/figures/records.py), line 176) — A finite float (rounded to ``digits`` when given), or None.
- `write_records(repository: Any, records: Iterable[provenance.DecisionRecord]) -> list[str | None]` ([source](../../../../../../src/learnloop/figures/records.py), line 190) — Write each record with its own short transaction (``write_decision``); never raises.
- `in_one_trace(records: Sequence[provenance.DecisionRecord]) -> list[provenance.DecisionRecord]` ([source](../../../../../../src/learnloop/figures/records.py), line 196) — The records under the current trace, or one trace born for all of them (outside every entry point each write would otherwise birth its own).
- `prebuild_record(row: Mapping[str, Any], decision: Any, model: Any, *, draw_index: int, seed: str | None, builds_left: int, render_left: float, on_mains: bool, plan_waiting: bool, expected_requests: float) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/figures/records.py), line 208) — The ``figure_prebuild`` record of one decided candidate (``row`` is its ledger row).
- `class FilterLog` ([source](../../../../../../src/learnloop/figures/records.py), line 269) — One filter pass's exclusions by rule (request keys), and what it kept.
  - `exclude(self, rule: str, candidate: Any) -> None` (line 277; public)
  - `record(self) -> provenance.DecisionRecord | None` (line 284; public) — The ``figure_prefetch_filter`` record, or None when nothing was excluded.
- `build_stop_record(rule: str, status: str, decision_id: str, *, waiting: Sequence[str]=(), error: BaseException | None=None, refusal: str | None=None) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/figures/records.py), line 305) — A ``figure_prebuild_stop`` record: the build of ``decision_id`` stopped (``deferred``: it and the queue after it wait for a later pass), passed over (``excluded``), refused or failed.
- `spec_problem(problems: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/figures/records.py), line 326) — A parser's problems as a code: a prediction's own problem, or the spec's.
- `sketch_problem(problems: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/figures/records.py), line 332)
- `class AuthorAttempts` ([source](../../../../../../src/learnloop/figures/records.py), line 347) — What each author attempt came to, noted as the loop runs (list appends only: nothing here can change the loop's control flow), and written as ``figure_author`` records when the build ends.
  - `start(self, number: int) -> None` (line 358; public)
  - `current(self) -> _Attempt | None` (line 362; public)
  - `end(self, rule: str, *, status: str | None=None, error: BaseException | None=None, problems: int | None=None) -> None` (line 365; public) — The current attempt's verdict: ``rule`` its code (a retry follows, or it was the last).
  - `extra(self, problem: str) -> None` (line 376; public)
  - `fact(self, **facts: Any) -> None` (line 380; public)
  - `records(self, *, request: Any, request_id: str | None, model: Any, outcome: Any=None, error: BaseException | None=None, job_id: str | None=None) -> list[provenance.DecisionRecord]` (line 384; public) — One record per attempt (one for the refusal when the build stopped before any).
  - `write(self, repository: Any, **kwargs: Any) -> None` (line 439; public) — :meth:`records`, written; never raises (a record never changes the build it describes).
- `request_record(request: Any, *, status: str, rule: str, request_id: str | None=None, figure_id: str | None=None, menu: Sequence[str]=(), absent: Mapping[str, str] | None=None, matched: str | None=None, gate: Any=None, error: BaseException | None=None) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/figures/records.py), line 472) — The ``figure_request`` record of one request: what it came to (``status``, ``rule``), the figure it took or stored, and the author's menu with each absent tier's code.
- `withheld_record(figure_id: str, rule: str, *, where: str) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/figures/records.py), line 505) — A ``figure_withheld`` record: ``figure_id`` was not shown (``rule``), at ``where`` (``delivery``, ``list``).
- `write_withheld_once(repository: Any, figure_id: str, rule: str, *, where: str) -> None` ([source](../../../../../../src/learnloop/figures/records.py), line 520) — Write :func:`withheld_record` once per vault, figure and rule in this process: the Reader's list is read every few seconds while a video builds, and one record says it as well as a hundred.
- `rich_stop_record(stop_code: str, *, retryable: bool, job_id: str | None, request_id: str | None, attempts: int) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/figures/records.py), line 535) — A ``figure_rich_stop`` record: the rich job ``job_id`` ended with no row, for ``stop_code`` (``rich.RichJobStopped``'s); ``deferred`` when it waits to be tried again (the plan's wait).

### Module constants

- `_LOG` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 47)
- `KIND_PREBUILD` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 49)
- `KIND_FILTER` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 50)
- `KIND_BUILD_STOP` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 51)
- `KIND_AUTHOR` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 52)
- `KIND_REQUEST` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 53)
- `KIND_WITHHELD` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 54)
- `KIND_RICH_AUTHOR` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 55)
- `KIND_RICH_STOP` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 56)
- `MAX_KEYS_PER_RULE` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 59)
- `FILTER_PROTECTION_UNAVAILABLE` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 62)
- `FILTER_DUPLICATE` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 63)
- `FILTER_OPEN_HORIZON` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 64)
- `FILTER_DECIDED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 65)
- `FILTER_NO_SPANS` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 66)
- `FILTER_SHOW_ME_OFF` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 67)
- `FILTER_WITHHELD` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 68)
- `FILTER_GROUNDING_WITHHELD` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 69)
- `FILTER_ITEM_PROTECTED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 70)
- `FILTER_ALREADY_BUILT` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 71)
- `STOP_FOREGROUND` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 74)
- `STOP_RICH_IN_FLIGHT` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 75)
- `STOP_OFF_MAINS` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 76)
- `STOP_AUTHOR_NOT_PLAN` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 77)
- `STOP_ITEM_PROTECTED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 78)
- `STOP_BUILT_ALREADY` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 79)
- `STOP_RENDER_MINUTES` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 80)
- `STOP_DAILY_BUILDS` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 81)
- `STOP_BUILD_REFUSED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 82)
- `STOP_BUILD_FAILED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 83)
- `STOP_RICH_JOB_RUNNING` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 84)
- `MODEL_FAILED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 88)
- `STATUS_INVALID` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 90)
- `TIER_REASON_MISSING` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 92)
- `LABEL_TEXT` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 94)
- `LABEL_TEXT_STRIPPED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 96)
- `PREDICTION_INVALID` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 98)
- `PREDICTION_DROPPED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 100)
- `SPEC_INVALID` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 102)
- `SKETCH_INVALID` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 104)
- `BRIEF_INVALID` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 106)
- `VERIFICATION_FAILED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 108)
- `SOURCE_DIFFERS` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 110)
- `QUICK_DROPPED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 112)
- `ACCEPTED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 114)
- `UNSUPPORTED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 115)
- `BUILD_ERROR` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 117)
- `INTERRUPTED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 119)
- `RICH_BRIEF_INVALID` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 123)
- `SCENE_INVALID` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 125)
- `CLAIM_FAILED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 127)
- `PACING_FAILED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 129)
- `RENDER_FAILED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 131)
- `RENDER_TIMEOUT` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 133)
- `RENDER_REPAIRED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 135)
- `REQUEST_REFUSED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 137)
- `RICH_ATTEMPT_CODES` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 138)
- `REQUEST_BUILT` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 143)
- `REQUEST_REUSED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 145)
- `REQUEST_RICH_STARTED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 147)
- `REQUEST_RICH_PENDING` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 148)
- `REUSE_MATCHES` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 152)
- `WITHHELD_AT_DELIVERY` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 154)
- `WITHHELD_PICK` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 155)
- `SPEC_UNPARSABLE` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 156)
- `_KEPT` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 158)
- `_AUTHOR_STATUSES` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 160)
- `_PREDICTION_PROBLEM` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 161)
- `_WITHHELD_GUARD` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 516)
- `_WITHHELD_SEEN` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 517)

### Explicit exports

`__all__` declares:

- `ACCEPTED`
- `AuthorAttempts`
- `BRIEF_INVALID`
- `FilterLog`
- `KIND_AUTHOR`
- `KIND_BUILD_STOP`
- `KIND_FILTER`
- `KIND_PREBUILD`
- `LABEL_TEXT`
- `MAX_KEYS_PER_RULE`
- `MODEL_FAILED`
- `PREDICTION_DROPPED`
- `PREDICTION_INVALID`
- `SOURCE_DIFFERS`
- `SPEC_INVALID`
- `STATUS_INVALID`
- `VERIFICATION_FAILED`
- `build_stop_record`
- `code`
- `in_one_trace`
- `number`
- `prebuild_record`
- `write_records`
- `KIND_REQUEST`
- `KIND_RICH_AUTHOR`
- `KIND_RICH_STOP`
- `KIND_WITHHELD`
- `REUSE_MATCHES`
- `RICH_ATTEMPT_CODES`
- `request_record`
- `rich_stop_record`
- `withheld_record`
- `write_withheld_once`

## Internal implementation anchors

- `_measurements(waits: Any) -> int` ([source](../../../../../../src/learnloop/figures/records.py), line 252) — The measured latencies behind W: the quick tiers share one sample (the author call's duration counts for grammar and sketch alike), each rich tier's are its own requests.
- `_posterior_draws() -> int` ([source](../../../../../../src/learnloop/figures/records.py), line 262)
- `class _Attempt` ([source](../../../../../../src/learnloop/figures/records.py), line 337)
- `_outcome(outcome: Any, error: BaseException | None) -> tuple[str | None, str | None, str]` ([source](../../../../../../src/learnloop/figures/records.py), line 451) — The stored (or reused) figure's id, a rich-only build's job id, and the build's result as a code.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/author_answer|learnloop.figures.author_answer]] — imports `module`; statically calls `sketch_problem`, `spec_problem`
- [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]] — imports `module`; statically calls `AuthorAttempts`, `code`, `in_one_trace`, `request_record`, `write_records`
- [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]] — imports `module`; statically calls `write_withheld_once`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `FilterLog`, `build_stop_record`, `in_one_trace`, `prebuild_record`, `write_records`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `module`; statically calls `AuthorAttempts`, `in_one_trace`, `rich_stop_record`, `write_records`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `in_one_trace`, `request_record`, `write_records`, `write_withheld_once`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `write_decision`; calls `write_decision`
- [[Reference/Modules/learnloop/figures/prefetch_model|learnloop.figures.prefetch_model]] — imports `POSTERIOR_DRAWS`, `QUICK_TIERS`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `DecisionRecord`, `check_no_prose`, `current_trace`, `new_trace_id`, `where`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `logging`, `math`, `re`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/author_answer|learnloop.figures.author_answer]], [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]], [[Reference/Modules/learnloop/figures/listing|learnloop.figures.listing]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_author_answer.py](../../../../../../tests/test_figure_author_answer.py) — direct import
  - `test_a_brief_that_does_not_parse_is_retried_with_its_problems`
  - `test_a_rich_answer_still_label_like_on_the_last_attempt_keeps_its_brief_without_that_text`
  - `test_a_sketch_that_does_not_parse_is_retried_and_ends_an_earlier_figure`
  - `test_a_spec_that_does_not_parse_is_retried_with_the_parsers_problems`
  - `test_a_status_no_menu_offers_has_its_rich_text_left_unread`
  - `test_a_status_off_the_menu_is_retried_uncounted_with_the_media_offered`
  - `test_a_v2_spec_is_judged_spec_and_a_status_outside_the_three_is_noted_and_read_as_a_spec`
  - `test_an_empty_tier_reason_is_retried_uncounted`
  - `test_label_like_text_is_retried_in_codes_words_then_stripped_on_the_last_attempt`
  - `test_with_the_panels_off_an_advanced_panel_is_a_parse_problem`
- [tests/test_figure_author_predictions.py](../../../../../../tests/test_figure_author_predictions.py) — direct import
  - `test_a_real_problem_still_gets_the_second_attempt_without_the_predictions_noise`
- [tests/test_figure_decision_records.py](../../../../../../tests/test_figure_decision_records.py) — direct import
  - `test_a_bad_prediction_drops_itself_and_says_so`
  - `test_a_failed_model_call_is_model_failed_with_its_exception_class`
  - `test_a_figure_stored_failed_keeps_both_attempts_problems`
  - `test_a_pass_that_excludes_nothing_writes_no_filter_record`
  - `test_a_queue_stopped_by_foreground_work_records_what_waits`
  - `test_a_refused_build_leaves_a_refused_record`
  - `test_a_refused_or_failed_prebuild_is_a_stop_record`
  - `test_a_rich_only_build_names_its_job_and_an_interrupted_build_its_error`
  - `test_an_author_status_no_menu_offers_is_recorded_as_other`
  - `test_attempt_one_problem_survives_an_accepted_second_attempt`
  - `test_deferred_and_capped_decisions_are_deferred_records`
  - `test_label_text_is_its_own_code`
  - `test_prebuilds_record_no_measured_latency_then_sampled_eu_positive_with_the_wait_and_seed`
  - `test_protection_exclusions_are_counted_by_rule_with_ten_keys`
  - `test_records_that_cannot_be_built_or_written_change_no_decision_build_or_prompt`
  - `test_the_recorded_seed_redraws_the_pass_exactly`
  - `test_unreadable_protection_cuts_the_whole_pass_and_says_so`
- [tests/test_figure_label_wording.py](../../../../../../tests/test_figure_label_wording.py) — direct import
  - `test_f1_a_spec_saying_it_matches_the_book_gets_the_repair_call`
- [tests/test_figure_request_records.py](../../../../../../tests/test_figure_request_records.py) — direct import
  - `test_a_built_figure_records_its_request_with_the_menu_and_the_absent_tiers`
  - `test_a_figure_a_concurrent_build_stored_is_reused_as_built_meanwhile`
  - `test_a_figure_withheld_at_delivery_is_recorded_once`
  - `test_a_listed_chain_whose_pick_is_withheld_is_recorded_once_per_figure`
  - `test_a_listed_figure_whose_spec_no_longer_parses_is_recorded_once`
  - `test_a_rich_only_build_is_deferred_with_its_job_started_then_pending`
  - `test_a_second_press_reuses_under_this_setting`
  - `test_every_code_is_staged`
  - `test_records_keep_ids_and_codes_only`
- [tests/test_figure_rich_attempt_records.py](../../../../../../tests/test_figure_rich_attempt_records.py) — direct import
  - `test_a_failed_render_and_its_repair_are_two_attempts`
  - `test_a_scene_out_of_pacing_is_repaired_by_the_second_attempt`
  - `test_a_second_request_refused_by_the_budget_is_its_own_attempt`
  - `test_a_stop_is_recorded_and_survives_the_requeue`
  - `test_a_stop_waiting_for_the_plan_is_deferred_with_its_attempt`
  - `test_a_video_that_lands_records_its_one_attempt_on_the_figure`
  - `test_attempt_ones_problem_survives_attempt_two`
  - `test_every_attempt_code_is_staged`
- [tests/test_figure_switch_predicates.py](../../../../../../tests/test_figure_switch_predicates.py) — direct import
- [tests/test_figure_wait_estimate.py](../../../../../../tests/test_figure_wait_estimate.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains records within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
