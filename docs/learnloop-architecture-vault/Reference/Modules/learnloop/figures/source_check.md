---
title: "learnloop.figures.source_check"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/source_check.py"
source_paths:
  - "src/learnloop/figures/source_check.py"
source_commit: "7fd12e25ec8d644a7f73bd03a530e9a4ee9585d0"
source_commit_timestamp: "2026-11-02T19:40:18-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.figures.source_check module"
  - "src/learnloop/figures/source_check.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.source_check`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.source_check` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: Reader RW5c P1: step 3, "matches the book's equation (checked)" (spec_reader_rw5c_checked_labels_v1 §4-§6, §10).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py) |
| Source lines | 1042 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7fd12e25ec8d644a7f73bd03a530e9a4ee9585d0` |
| Commit timestamp | `2026-11-02T19:40:18-05:00` |

## Public API

- `enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/figures/source_check.py), line 87) — ``figures.checked_labels_enabled`` under ``figures.enabled``, as configured now.
- `recheck_key(vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 93) — A recheck's gate key (§6.7): it makes no model request, but stops at any switch change.
- `class Candidate` ([source](../../../../../../src/learnloop/figures/source_check.py), line 100) — One readable equation of an input span.
  - `key(self) -> str` (line 115; public)
- `class Check` ([source](../../../../../../src/learnloop/figures/source_check.py), line 120) — The result of one run of steps 3a-3e.
  - `book_elements(self) -> list[dict[str, Any]]` (line 135; public)
- `input_spans(row: Mapping[str, Any]) -> list[tuple[str, str, str]]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 143) — ``(extraction_id, span_id, claim_key)`` of a figure's own input spans: the spans that were sent to the author, as stored for every held-out recheck.
- `read_candidates(vault: Any, repository: Any, spans: Sequence[tuple[str, str, str]], *, persist: bool=True) -> tuple[list[Candidate], dict[str, int]]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 172) — The readable equations of the input spans in reading order, and how many were refused by each reason.
- `class Drawn` ([source](../../../../../../src/learnloop/figures/source_check.py), line 227) — A bare reference to a definition: an element that draws it, whole.
- `expand(node: G.Node, definitions: Mapping[str, G.Node], _seen: tuple[str, ...]=()) -> G.Node` ([source](../../../../../../src/learnloop/figures/source_check.py), line 237) — ``node`` with definitions written out (the compiler caps the result).
- `drawn_by_reference(compiled: S.CompiledFigure) -> dict[str, list[Drawn]]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 248) — Each definition's elements that draw it by bare reference: the expression is exactly ``Node(kind="name", text=d)``.
- `binding_problem(node: G.Node) -> str | None` ([source](../../../../../../src/learnloop/figures/source_check.py), line 284) — Why a definition's expansion cannot be checked (§6.1), as a closed reason.
- `to_json(node: G.Node) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 311)
- `controls(node: G.Node, symbols: Sequence[str]) -> list[G.Node]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 331) — §6.5: ``d + 1``, ``2·d`` and ``d`` with each free symbol ``s`` replaced by ``s + 1``: exact transformations, structural, tuning nothing.
- `quote_overlaps(quote: str, candidate: Candidate) -> bool` ([source](../../../../../../src/learnloop/figures/source_check.py), line 432) — Whether a quote ``quote_in`` verifies in this block overlaps this segment.
- `check_figure(vault: Any, repository: Any, compiled: S.CompiledFigure, *, spans: Sequence[tuple[str, str, str]], grounding: str | None, persist: bool=True, sandbox: Sandbox | None=None, sandbox_ready: Callable[[], bool] | None=None) -> Check` ([source](../../../../../../src/learnloop/figures/source_check.py), line 483) — Steps 3a-3e on one compiled grammar spec.
- `record(connection: Any, figure_id: str, check: Check, *, trigger: str, created_at: str) -> str` ([source](../../../../../../src/learnloop/figures/source_check.py), line 766) — One ``figure_source_checks`` row and its ``judgment_ledger`` verdict, in the caller's transaction (F6, G23i): either both commit or neither.
- `failed_check(compiled: S.CompiledFigure) -> Check` ([source](../../../../../../src/learnloop/figures/source_check.py), line 787) — A check that could not run: an honest row, certifying nothing (G23f).
- `stored_problems(found: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 793) — The difference a check row records, in code's words, for *rebuild*'s first attempt (§6.6).
- `grammar_row(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/figures/source_check.py), line 800) — Only grammar-tier figures are checked (§11.1, N-a): sketch, ``js_animation`` and ``manim`` keep *not checked against the book*.
- `current_row(repository: Any, figure_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/figures/source_check.py), line 807) — The newest check of a figure at the current certification version (the one shown).
- `recheck_due(found: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/figures/source_check.py), line 814) — No check at the current certification version; or the last found no sandbox (a machine that has one now can decide what that one could not).
- `recheck(vault: Any, repository: Any, row: Mapping[str, Any], *, live_vault: Callable[[], Any] | None=None, clock: Clock | None=None, dry_run: bool=False, sandbox: Sandbox | None=None, sandbox_ready: Callable[[], bool] | None=None) -> Check | None` ([source](../../../../../../src/learnloop/figures/source_check.py), line 827) — A stored grammar figure rechecked by code, with no model client (§10.4), admitted against the switch as it is now before the sandbox and before the write (§6.7).
- `coverage(vault: Any, repository: Any, *, dry_run: bool, withheld: Callable[[Mapping[str, Any]], bool], sandbox: Sandbox | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 875) — ``reader figure-checks --recheck``: every stored grammar figure rechecked by code, with no model client; ``dry_run`` writes nothing.
- `audit(repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 947) — ``reader figure-checks`` with no ``--recheck``: each element carrying the claim, from the ledger.
- `report_block(connection: Any, *, since: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 964) — The reader report's ``source_checks``: outcomes, reasons, elements, latency, and opens and "not right?" notes for figures with a ``book`` element and without (§12 item 4).
- `add_report_block(report: dict[str, Any], sqlite_path: Any, *, since: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 1002) — Put :func:`report_block` under the reader report's ``figures`` (``learnloop reader report`` calls it only with the switch on, so off the report is as before: G23g).

### Module constants

- `CERTIFICATION_VERSION` ([src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py), line 58)
- `LEDGER_TASK` ([src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py), line 59)
- `OUTCOMES` ([src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py), line 61)
- `REASONS` ([src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py), line 64)
- `SANDBOX_LIMITS` ([src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py), line 69)
- `PER_CHECK_SECONDS` ([src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py), line 70)
- `REJECTED_REASON` ([src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py), line 72)
- `_UNICODE_MATH` ([src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py), line 73)
- `_RESULTS` ([src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py), line 74)
- `HARNESS_SHA256` ([src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py), line 84)
- `_RECHECKING` ([src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py), line 823)
- `_RECHECKING_GUARD` ([src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py), line 824)

### Explicit exports

`__all__` declares:

- `add_report_block`
- `audit`
- `coverage`
- `CERTIFICATION_VERSION`
- `CHECKED`
- `Check`
- `DIFFERS`
- `HARNESS`
- `HARNESS_SHA256`
- `LEDGER_TASK`
- `NOT_CHECKABLE`
- `OUTCOMES`
- `REASONS`
- `REJECTED_REASON`
- `UNDECIDED`
- `check_figure`
- `controls`
- `current_row`
- `drawn_by_reference`
- `enabled`
- `failed_check`
- `grammar_row`
- `input_spans`
- `read_candidates`
- `recheck`
- `recheck_due`
- `recheck_key`
- `record`
- `stored_problems`

## Internal implementation anchors

- `_harness_files() -> tuple[str, str]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 77)
- `_health(repository: Any, extraction_id: str, block: Any, ir: Any, *, persist: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 156) — The block's health as ``reader.block_health`` computes it: stored when computed, never assumed ok (``unknown`` is not ``ok``, §5.2).
- `_bare_exact(side: G.Node) -> bool` ([source](../../../../../../src/learnloop/figures/source_check.py), line 275)
- `_bare_name(side: G.Node) -> bool` ([source](../../../../../../src/learnloop/figures/source_check.py), line 280)
- `_substitute(node: G.Node, name: str, replacement: G.Node) -> G.Node` ([source](../../../../../../src/learnloop/figures/source_check.py), line 322)
- `_exact(value: float) -> str` ([source](../../../../../../src/learnloop/figures/source_check.py), line 343)
- `_assumptions(compiled: S.CompiledFigure, names: set[str], variable: str | None) -> dict[str, str]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 348) — §6.3 step 1: sign assumptions the sliders' ranges imply, so a proof holds across them.
- `_projected_grid(compiled: S.CompiledFigure, names: set[str]) -> list[dict[str, float]]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 366) — The parameter grid on the parameters a definition reads (the others cannot move it).
- `_samples(compiled: S.CompiledFigure, drawn: Drawn) -> list[float]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 376)
- `_display_payload(compiled: S.CompiledFigure, name: str, drawn: Drawn, grid: Sequence[Mapping[str, float]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 385) — What the figure shows at every displayed sample of every grid point: the evaluator's double formatted by the twin of ``formatValue`` (§6.4).
- `_squashed_map(text: str) -> tuple[str, list[int]]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 413) — ``verify.quote_in``'s whitespace-collapsed text, with each character's place in ``text``.
- `_point_words(value: Any) -> str` ([source](../../../../../../src/learnloop/figures/source_check.py), line 448) — An exact witness coordinate as its shortest decimal when it is one, else the exact fraction.
- `_witness_words(name: str, witness: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/figures/source_check.py), line 460) — The difference, in code's words, for the second attempt and the ledger (§6.6).
- `_count(reasons: dict[str, int], reason: str, amount: int=1) -> None` ([source](../../../../../../src/learnloop/figures/source_check.py), line 471)
- `_run_sandbox(payload: Mapping[str, Any], sandbox: Sandbox | None) -> pf_sandbox.SandboxResult` ([source](../../../../../../src/learnloop/figures/source_check.py), line 478)
- `_check(vault: Any, repository: Any, compiled: S.CompiledFigure, *, spans: Sequence[tuple[str, str, str]], grounding: str | None, persist: bool, sandbox: Sandbox | None, sandbox_ready: Callable[[], bool] | None) -> Check` ([source](../../../../../../src/learnloop/figures/source_check.py), line 496)
- `_across_blocks(quote: str, spans: Sequence[tuple[str, str, str]], repository: Any) -> bool` ([source](../../../../../../src/learnloop/figures/source_check.py), line 613) — §5.3: a quote that spans two blocks is never one candidate's pointer.
- `_difference_points(grid: Sequence[Mapping[str, float]], drawn: Drawn, compiled: S.CompiledFigure) -> list[dict[str, str]]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 625) — The exact points a difference is looked for at (§6.3 step 5): the grid crossed with the variable's displayed samples.
- `_decide_definition(entry: dict[str, Any], name: str, pairs: Sequence[tuple[Candidate, bool]], results: Mapping[tuple[str, str], Mapping[str, Any]], failure: str | None, drawn: Sequence[Drawn], book: dict[str, E.BookLabel], book_elements: dict[str, str], problems: list[str]) -> None` ([source](../../../../../../src/learnloop/figures/source_check.py), line 641) — §6.6's precedence over this definition's pairs.
- `_controls_verdict(answers: Any) -> str | None` ([source](../../../../../../src/learnloop/figures/source_check.py), line 708) — §6.5: None when every control was refused.
- `_provenance(candidate: Candidate) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 721)
- `_finished(compiled: S.CompiledFigure, definitions: list[dict[str, Any]], candidates: Sequence[Candidate], reasons: Mapping[str, int], outcome: str, sympy_version: str, *, book: Mapping[str, E.BookLabel] | None=None, book_elements: Mapping[str, str] | None=None, problems: Sequence[str]=()) -> Check` ([source](../../../../../../src/learnloop/figures/source_check.py), line 726)
- `_rationale(definitions: Sequence[Mapping[str, Any]], reasons: Mapping[str, int]) -> str` ([source](../../../../../../src/learnloop/figures/source_check.py), line 744) — Code text only, for the ledger: per definition its name, outcome, closed reason and a difference's witness.
- `_shown_rows(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 870)
- `_latency(durations: Sequence[int]) -> dict[str, int | None]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 915)
- `_audit_entries(row: Mapping[str, Any], definitions: Sequence[Mapping[str, Any]], elements: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/source_check.py), line 920) — Each element carrying the claim, for the owner's audit (§12 item 2): the book's equation as read, its page and the figure's definition, rendered.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]] — imports `add_report_block`, `module`; statically calls `add_report_block`, `audit`, `coverage`, `enabled`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `check_figure`, `current_row`, `enabled`, `failed_check`, `grammar_row`, `recheck_due`, `record`, `stored_problems`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `current_row`, `enabled`, `grammar_row`, `recheck`, `recheck_due`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/pf_sandbox|learnloop.content.authoring.pf_sandbox]] — imports `module`; calls `SandboxLimits`, `sandbox_available`
- [[Reference/Modules/learnloop/content/sources/block_health|learnloop.content.sources.block_health]] — imports `module`; calls `analyze_block_health`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`; calls `exam_material`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] — imports `module`; calls `figure_verdicts`, `has_source_checks`, `insert_source_check`, `latest_source_check`, `latest_source_checks`, `shown_figures`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `FiguresChanged`, `FiguresGate`, `checked_labels_enabled`, `figures_enabled`; calls `FiguresGate`, `checked_labels_enabled`, `figures_enabled`
- [[Reference/Modules/learnloop/figures/book_math|learnloop.figures.book_math]] — imports `module`; calls `binary64_exact`, `read_relation`, `segments`
- [[Reference/Modules/learnloop/figures/display_format|learnloop.figures.display_format]] — imports `module`; calls `format_value`, `js_string`
- [[Reference/Modules/learnloop/figures/elements|learnloop.figures.elements]] — imports `module`; calls `BookLabel`, `element_id`, `element_map`, `to_tex`
- [[Reference/Modules/learnloop/figures/grammar|learnloop.figures.grammar]] — imports `module`; calls `Node`, `evaluate`, `walk`
- [[Reference/Modules/learnloop/figures/spec|learnloop.figures.spec]] — imports `module`; calls `_num`, `bar_ks`, `expanded_free`, `parse_spec`, `plot_xs`
- [[Reference/Modules/learnloop/figures/verify|learnloop.figures.verify]] — imports `module`; calls `parameter_grid`, `quote_in`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `fractions`, `hashlib`, `json`, `pathlib`, `re`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rw5c_judgments.py](../../../../../../tests/test_rw5c_judgments.py) — direct import
  - `test_a_failure_between_the_two_inserts_leaves_neither`
  - `test_a_recheck_supersedes_the_previous_verdict_of_the_same_figure`
  - `test_the_rationale_is_code_text_only`
- [tests/test_rw5c_labels.py](../../../../../../tests/test_rw5c_labels.py) — direct import
  - `test_a_sketch_view_has_no_elements_or_source_check`
- [tests/test_rw5c_recheck.py](../../../../../../tests/test_rw5c_recheck.py) — direct import
  - `test_a_certification_bump_rechecks_at_no_paid_cost`
  - `test_a_difference_found_at_recheck_gives_the_failed_state_with_rebuild`
  - `test_a_prebuilt_figure_nobody_pressed_for_that_differs_lists_nothing`
  - `test_a_recheck_with_the_switch_off_or_turned_off_before_its_write_writes_nothing`
  - `test_pressing_rebuild_calls_the_author_and_stores_a_new_version`
  - `test_rebuild_is_not_offered_with_revisions_off`
  - `test_section_figures_leave_a_rejected_figure_out`
- [tests/test_rw5c_source_check.py](../../../../../../tests/test_rw5c_source_check.py) — direct import
  - `test_a_block_that_is_not_ok_is_refused_with_its_reason`
  - `test_a_book_condition_on_a_parameter_is_undecided`
  - `test_a_cancelled_factor_is_never_checked_and_a_stated_one_differs_at_the_hole`
  - `test_a_check_that_blows_up_costs_the_figure_nothing_and_certifies_nothing`
  - `test_a_computed_exponent_never_hides_a_cancellation`
  - `test_a_degenerate_definition_or_a_symbol_that_cancels_breaks_the_controls`
  - `test_a_held_out_block_later_withholds_the_figure_and_its_check`
  - `test_a_model_quote_of_a_wrong_equation_widens_nothing`
  - `test_a_parameter_dependent_condition_that_differs_is_undecided_by_domain`
  - `test_a_positive_base_needs_no_condition`
  - `test_a_renamed_parameter_is_names_and_the_sandbox_is_not_asked`
  - `test_a_sandbox_that_raises_unavailable_checks_nothing`
  - `test_a_second_difference_is_not_shown`
  - `test_a_sketch_tier_is_never_checked`
  - `test_a_square_of_a_root_against_x_is_never_checked`
  - `test_a_stated_claim_proved_different_wins_over_an_unstated_match`
  - `test_a_stated_match_names_its_equation_and_an_unstated_match_needs_no_claim`
  - `test_a_timeout_or_a_failed_run_checks_nothing`
  - `test_a_withheld_span_is_never_read`
  - `test_an_answer_outside_the_closed_results_is_undecided`
  - `test_an_exact_condition_passes_and_name_against_name_is_undecided`
  - `test_an_inconclusive_control_is_never_checked`
  - `test_an_inexact_literal_is_not_checkable`
  - `test_an_inline_copy_is_not_a_bare_reference_and_gets_role_ai`
  - `test_catastrophic_floating_point_near_zero_is_display_disagrees`
  - `test_grounding_none_is_never_checked`
  - `test_no_bubblewrap_checks_nothing`
  - `test_one_definition_differing_withholds_every_book_role_on_the_figure`
  - `test_sigma_in_a_denominator_with_a_positive_slider_passes`
  - `test_the_flagship_density_is_checked_with_display_agreement_over_its_grid`
  - `test_the_half_density_with_a_stated_claim_differs_and_names_where`
  - `test_the_reverse_cancellation_differs_too`
  - `test_the_switch_off_at_the_store_writes_nothing`
  - `test_the_switch_off_between_the_sandbox_and_the_second_attempt_stops_the_build`
  - `test_two_definitions_get_per_element_roles`
  - `test_unicode_math_is_never_a_candidate`
- [tests/test_rw5c_switch_off.py](../../../../../../tests/test_rw5c_switch_off.py) — direct import
  - `test_nothing_reads_the_ledger_while_the_switch_is_off`

## Modification guidance

- Make changes here when the responsibility remains source check within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/source_check.py](../../../../../../src/learnloop/figures/source_check.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
