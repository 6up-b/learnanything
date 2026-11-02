---
title: "learnloop.projects.probes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/projects/probes.py"
source_paths:
  - "src/learnloop/projects/probes.py"
source_commit: "debd86c0d24a1e4837b20b76aad6a47a8720f8b2"
source_commit_timestamp: "2026-10-13T00:18:31-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.projects"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.projects.probes module"
  - "src/learnloop/projects/probes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-projects"
---

# `learnloop.projects.probes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.projects.probes` exists within [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] to own the behavior summarized by its module contract: Delayed probes: generation, filters, selection, sealing, answers, grades (spec §5.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py) |
| Source lines | 1196 |
| Owning package | [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `debd86c0d24a1e4837b20b76aad6a47a8720f8b2` |
| Commit timestamp | `2026-10-13T00:18:31-04:00` |

## Public API

- `authoring_output_tokens(config: LearnLoopConfig | None=None) -> int` ([source](../../../../../../src/learnloop/projects/probes.py), line 85)
- `closed_book_output_tokens(questions: int, config: LearnLoopConfig | None=None) -> int` ([source](../../../../../../src/learnloop/projects/probes.py), line 89)
- `grading_output_tokens(items: int, config: LearnLoopConfig | None=None) -> int` ([source](../../../../../../src/learnloop/projects/probes.py), line 94)
- `class SealedProbeError(ValueError)` ([source](../../../../../../src/learnloop/projects/probes.py), line 99) — A probe is not due yet, not selected, or does not exist.
- `class ProbeStateError(ValueError)` ([source](../../../../../../src/learnloop/projects/probes.py), line 103) — The requested action does not apply to this probe or response.
- `class GenerationError(ValueError)` ([source](../../../../../../src/learnloop/projects/probes.py), line 107) — A generation stage failed for a reason whose message is safe to show.
- `safe_error(exc: BaseException) -> str` ([source](../../../../../../src/learnloop/projects/probes.py), line 111) — An error string that can never quote model output.
- `authoring_context(bundle: dict[str, Any], *, repo_name: str, config: LearnLoopConfig) -> ProbeAuthoringContext` ([source](../../../../../../src/learnloop/projects/probes.py), line 172)
- `added_lines(diff_text: str) -> set[int]` ([source](../../../../../../src/learnloop/projects/probes.py), line 236) — New-side line numbers this diff added.
- `class Validity` ([source](../../../../../../src/learnloop/projects/probes.py), line 260)
- `is_prose_document(path: str) -> bool` ([source](../../../../../../src/learnloop/projects/probes.py), line 312)
- `stated_reason(quote: str, source: str, reference_answer: str, *, span_lines: list[str]=(), path: str='', preceding: list[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/probes.py), line 380) — Whether a cited span itself states the reason a ``why`` reference gives.
- `validate_candidate(candidate: ProbeCandidate, bundle: dict[str, Any], *, agent_committed: bool) -> Validity` ([source](../../../../../../src/learnloop/projects/probes.py), line 412) — Deterministic checks: citations resolve and quotes are verbatim (§5.2).
- `grade_items(paid: PaidCalls, route: ProjectRoute, items: list[dict[str, Any]], *, diff_id: str | None, stage: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/probes.py), line 501) — Blind-grade ``items`` ({key, question, reference_answer, citations, answer}).
- `class GenerationReport` ([source](../../../../../../src/learnloop/projects/probes.py), line 557)
  - `as_dict(self) -> dict[str, Any]` (line 566; public)
- `diffs_awaiting_generation(store: ProjectStore, *, due_by: str | None=None, config: LearnLoopConfig | None=None, include_failed: bool=False) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/projects/probes.py), line 578) — Diffs whose probes are not generated yet, optionally only those due by ``due_by``.
- `plan_generation(store: ProjectStore, vault_root: Path, config: LearnLoopConfig, diffs: list[dict[str, Any]]) -> list[PlannedCall]` ([source](../../../../../../src/learnloop/projects/probes.py), line 598) — The calls generation would make, from the stored bundles (no model calls).
- `plan_for_bundle(bundle: dict[str, Any], *, repo_name: str, config: LearnLoopConfig) -> list[PlannedCall]` ([source](../../../../../../src/learnloop/projects/probes.py), line 625) — Every call a not-yet-generated bundle needs (also for not-yet-captured ones).
- `generate_for_diff(store: ProjectStore, vault_root: Path, config: LearnLoopConfig, paid: PaidCalls, routes: dict[str, ProjectRoute], diff: dict[str, Any], *, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/projects/probes.py), line 841) — Run the remaining stages for one diff; returns its new probe status.
- `generate_probes(store: ProjectStore, vault_root: Path, config: LearnLoopConfig, paid: PaidCalls, routes: dict[str, ProjectRoute], diffs: list[dict[str, Any]], *, clock: Clock | None=None) -> GenerationReport` ([source](../../../../../../src/learnloop/projects/probes.py), line 865)
- `probe_header(store: ProjectStore, probe: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/probes.py), line 931) — What the owner sees with a due question: where it is from, never the answer.
- `due_probes(store: ProjectStore, *, clock: Clock | None=None, repo_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/projects/probes.py), line 951)
- `open_probe(store: ProjectStore, probe_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/probes.py), line 964) — The question text of a due probe (the only way a question is rendered).
- `record_response(store: ProjectStore, probe_id: str, *, kind: str, answer: str | None=None, declaration: str='unassisted', served_at: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/probes.py), line 971)
- `grade_responses(store: ProjectStore, paid: PaidCalls, route: ProjectRoute, *, response_ids: list[str] | None=None, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/projects/probes.py), line 1024) — Blind-grade pending answers one at a time; failures stay pending to retry.
- `contest_grade(store: ProjectStore, response_id: str, *, score: float, note: str='', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/probes.py), line 1114) — The owner's adjudication becomes the outcome of record; the grade is kept.
- `reveal(store: ProjectStore, response: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/probes.py), line 1151) — After answering: the reference, its citations, and honest rationale labels.

### Module constants

- `GRADING_ITEM_TOKENS_ESTIMATE` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 74)
- `CLOSED_BOOK_QUESTION_TOKENS_ESTIMATE` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 75)
- `PROMPT_OVERHEAD_TOKENS` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 76)
- `MAX_GENERATION_ATTEMPTS` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 77)
- `MAX_GRADE_ATTEMPTS` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 78)
- `GENERIC_VERDICTS` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 79)
- `RESPONSE_KINDS` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 80)
- `_HUNK_HEADER` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 81)
- `DECLARATIONS` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 82)
- `_COMMENT_START` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 273)
- `_TRAILING_COMMENT` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 274)
- `_REASON_CUES` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 275)
- `_STOPWORDS` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 280)
- `_WORD` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 286)
- `_PROSE_SUFFIXES` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 307)
- `_PROSE_NAMES` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 308)
- `_FENCE` ([src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py), line 309)

### Explicit exports

`__all__` declares:

- `DECLARATIONS`
- `GenerationReport`
- `ProbeStateError`
- `RESPONSE_KINDS`
- `SealedProbeError`
- `Validity`
- `added_lines`
- `authoring_context`
- `authoring_output_tokens`
- `closed_book_output_tokens`
- `grading_output_tokens`
- `contest_grade`
- `diffs_awaiting_generation`
- `due_probes`
- `generate_for_diff`
- `generate_probes`
- `grade_items`
- `grade_responses`
- `open_probe`
- `plan_for_bundle`
- `plan_generation`
- `probe_header`
- `record_response`
- `reveal`
- `stated_reason`
- `validate_candidate`

## Internal implementation anchors

- `_exclusive(lock_dir: Path, name: str) -> Iterator[bool]` ([source](../../../../../../src/learnloop/projects/probes.py), line 128) — A non-blocking cross-process lock in ``lock_dir`` (the store's directory).
- `_input_hash(payload: Any) -> str` ([source](../../../../../../src/learnloop/projects/probes.py), line 153)
- `_now(clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/projects/probes.py), line 159)
- `_sealed_until(diff: dict[str, Any], config: LearnLoopConfig) -> str` ([source](../../../../../../src/learnloop/projects/probes.py), line 163)
- `_disclosure_for_bundle(bundle: dict[str, Any], diff: dict[str, Any], repo: dict[str, Any], prompt: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/probes.py), line 206)
- `_evidence(citations: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/projects/probes.py), line 220)
- `_clean_quote(quote: str) -> str` ([source](../../../../../../src/learnloop/projects/probes.py), line 267)
- `_comment_text(lines: list[str], *, diff: bool=False) -> str` ([source](../../../../../../src/learnloop/projects/probes.py), line 289) — The comment parts of source lines (whole-line and trailing comments).
- `_unmarked(lines: Iterable[str], *, diff: bool) -> list[str]` ([source](../../../../../../src/learnloop/projects/probes.py), line 318)
- `_document_prose(quote: str, *, diff: bool, preceding: list[str]) -> str` ([source](../../../../../../src/learnloop/projects/probes.py), line 322) — A prose document's cited text, or "" when it sits in a fenced code block.
- `_prose(quote: str, source: str, span_lines: list[str]=(), *, path: str='', preceding: list[str]=()) -> str` ([source](../../../../../../src/learnloop/projects/probes.py), line 337) — The natural-language part of a cited span.
- `_terms(text: str) -> set[str]` ([source](../../../../../../src/learnloop/projects/probes.py), line 367)
- `_clamp(score: float) -> float` ([source](../../../../../../src/learnloop/projects/probes.py), line 549)
- `_plan_stages(authoring_input: int | None, candidates: int, closed_book: int, grading: int, *, config: LearnLoopConfig | None=None) -> list[PlannedCall]` ([source](../../../../../../src/learnloop/projects/probes.py), line 633)
- `_author(store: ProjectStore, vault_root: Path, config: LearnLoopConfig, paid: PaidCalls, route: ProjectRoute, diff: dict[str, Any], repo: dict[str, Any], clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/projects/probes.py), line 657)
- `_closed_book(store: ProjectStore, paid: PaidCalls, route: ProjectRoute, diff: dict[str, Any], probes: list[dict[str, Any]]) -> None` ([source](../../../../../../src/learnloop/projects/probes.py), line 732)
- `_closed_book_grades(store: ProjectStore, paid: PaidCalls, route: ProjectRoute, diff: dict[str, Any], probes: list[dict[str, Any]], clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/projects/probes.py), line 778)
- `_select(store: ProjectStore, config: LearnLoopConfig, diff: dict[str, Any], clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/projects/probes.py), line 830)
- `_generate_all(store: ProjectStore, vault_root: Path, config: LearnLoopConfig, paid: PaidCalls, routes: dict[str, ProjectRoute], diffs: list[dict[str, Any]], report: GenerationReport, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/projects/probes.py), line 892)
- `_require_due(store: ProjectStore, probe_id: str, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/probes.py), line 955)
- `_grade_pending(store: ProjectStore, paid: PaidCalls, route: ProjectRoute, pending: list[dict[str, Any]], clock: Clock | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/projects/probes.py), line 1053)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]] — imports `GRADING_ITEM_TOKENS_ESTIMATE`, `PROMPT_OVERHEAD_TOKENS`, `ProbeStateError`, `SealedProbeError`, `contest_grade`, `diffs_awaiting_generation`, `due_probes`, `generate_probes`, `grade_responses`, `grading_output_tokens`, `open_probe`, `plan_for_bundle`, `plan_generation`, `record_response`, `reveal`; statically calls `contest_grade`, `diffs_awaiting_generation`, `due_probes`, `generate_probes`, `grade_responses`, `grading_output_tokens`, `open_probe`, `plan_for_bundle`, `plan_generation`, `record_response`, `reveal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`, `AITurnTimeout`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `parse_utc`, `utc_now_iso`; calls `FrozenClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/projects/ai_contracts|learnloop.projects.ai_contracts]] — imports `CLOSED_BOOK_PROMPT_VERSION`, `CLOSED_BOOK_PURPOSE`, `ClosedBookAnswers`, `ClosedBookContext`, `PROBE_AUTHORING_PROMPT_VERSION`, `PROBE_AUTHORING_PURPOSE`, `PROBE_GRADING_PROMPT_VERSION`, `PROBE_GRADING_PURPOSE`, `PROBE_KINDS`, `ProbeAuthoringContext`, `ProbeCandidate`, `ProbeCandidates`, `ProbeGrades`, `ProbeGradingContext`, `closed_book_prompt`, `probe_authoring_prompt`, `probe_grading_prompt`; calls `ClosedBookContext`, `ProbeAuthoringContext`, `ProbeGradingContext`, `closed_book_prompt`, `probe_authoring_prompt`, `probe_grading_prompt`
- [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]] — imports `PaidCalls`, `PlannedCall`, `ProjectRoute`, `ROLE_TASK`; calls `PlannedCall`
- [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]] — imports `BundleIntegrityError`, `estimate_tokens`, `load_bundle`, `parse_hunks`; calls `estimate_tokens`, `load_bundle`, `parse_hunks`
- [[Reference/Modules/learnloop/projects/experiment_store|learnloop.projects.experiment_store]] — imports `ProjectStore`, `store_path`; calls `store_path`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `fcntl`, `hashlib`, `json`, `pathlib`, `random`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
  - `test_no_retired_hard_coded_output_cap_remains`
- [tests/test_project_atomicity.py](../../../../../../tests/test_project_atomicity.py) — direct import
  - `test_a_grade_never_persists_without_its_judgment`
  - `test_a_second_grader_waits_its_turn_instead_of_paying`
  - `test_an_adjudication_never_persists_without_its_judgment`
  - `test_an_unfair_tap_never_persists_without_its_judgment`
  - `test_interleaved_graders_leave_one_outcome_and_report_it`
- [tests/test_project_blindness.py](../../../../../../tests/test_project_blindness.py) — direct import
  - `test_rendered_prompts_carry_no_provenance_declaration_or_closed_book_origin`
- [tests/test_project_probes.py](../../../../../../tests/test_project_probes.py) — direct import
  - `test_a_concurrent_generation_run_is_refused_not_double_paid`
  - `test_answers_grades_and_contest`
  - `test_authoring_prompt_carries_numbered_lines`
  - `test_citations_must_resolve_and_quote_verbatim`
  - `test_errors_never_quote_model_output`
  - `test_grade_failures_stay_pending_then_fail`
  - `test_probes_are_sealed_until_due`
  - `test_redacted_lines_cannot_be_quoted`
  - `test_unselected_probes_are_never_served`
- [tests/test_project_report.py](../../../../../../tests/test_project_report.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains probes within learnloop.projects; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/projects/probes.py](../../../../../../src/learnloop/projects/probes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
