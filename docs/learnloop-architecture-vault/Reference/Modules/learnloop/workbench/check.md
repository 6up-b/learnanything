---
title: "learnloop.workbench.check"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/workbench/check.py"
source_paths:
  - "src/learnloop/workbench/check.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.workbench"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.workbench.check module"
  - "src/learnloop/workbench/check.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-workbench"
---

# `learnloop.workbench.check`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.workbench.check` exists within [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] to own the behavior summarized by its module contract: Reader workbench RW2b: "Check my work" (spec_reader_workbench_v1 §5.2, §5.3, §5.8, G9, G12, G38).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py) |
| Source lines | 851 |
| Owning package | [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `models_off() -> bool` ([source](../../../../../../src/learnloop/workbench/check.py), line 95)
- `class Transformation(WireModel)` ([source](../../../../../../src/learnloop/workbench/check.py), line 103)
- `class MapClaim(WireModel)` ([source](../../../../../../src/learnloop/workbench/check.py), line 120)
- `class StepCheck(WireModel)` ([source](../../../../../../src/learnloop/workbench/check.py), line 125)
- `class ErrorReading(WireModel)` ([source](../../../../../../src/learnloop/workbench/check.py), line 138)
- `class WorkbenchCheckOutputV1(WireModel)` ([source](../../../../../../src/learnloop/workbench/check.py), line 143)
- `build_prompt(item: Any, rubric: Any, steps: Sequence[hint_workbench.WorkbenchStep], map_record: Mapping[str, Any] | None, *, request_id: str) -> str` ([source](../../../../../../src/learnloop/workbench/check.py), line 178)
- `class CheckUnavailable(Exception)` ([source](../../../../../../src/learnloop/workbench/check.py), line 198) — The check cannot run (``reason``: ``unrouted`` | ``unpriced`` | ``capped`` | ``session_capped`` | ``unavailable`` | ``models_off``); ``message`` is the learner's line.
  - `__init__(self, reason: str, message: str) -> None` (line 203; internal)
- `daily_envelope(vault: Any, repository: Repository, *, clock: Clock | None=None) -> SharedDailyEnvelope` ([source](../../../../../../src/learnloop/workbench/check.py), line 209)
- `session_calls_on(connection: Any, workbench_session_id: str) -> int` ([source](../../../../../../src/learnloop/workbench/check.py), line 216) — The workbench's own calls for this problem so far, read on ``connection``: its checks' (and RW2c's comparisons') receipts and its bridge and worked-example searches (one row per search, written before it runs, found or not: fix round 1, F9).
- `session_calls(repository: Repository, workbench_session_id: str) -> int` ([source](../../../../../../src/learnloop/workbench/check.py), line 233) — The workbench's own calls for this problem so far (:func:`session_calls_on`).
- `class CheckRoute` ([source](../../../../../../src/learnloop/workbench/check.py), line 240) — The check's pinned route for one request.
  - `__init__(self, vault: Any, repository: Repository, *, client: Any | None, envelope: Any, workbench_session_id: str) -> None` (line 243; internal)
  - `subscription(self) -> bool` (line 255; public)
  - `problem(self) -> CheckUnavailable | None` (line 258; public)
  - `ask(self, prompt: str, *, assist_id: str, result_model: type[WireModel] | None=None, prompt_version: str=PROMPT_VERSION) -> Any` (line 277; public) — One call on the route.
  - `model(self) -> str | None` (line 304; public)
- `class CheckedSteps` ([source](../../../../../../src/learnloop/workbench/check.py), line 319) — A validated check: the verdicts by chain id, the first questionable step, the error-kind guess and its readings, what was dropped and why.
- `validate(output: WorkbenchCheckOutputV1, steps: Sequence[hint_workbench.WorkbenchStep], item: Any, *, map_record: Mapping[str, Any] | None, error_kind_enabled: bool, outcomes: Mapping[int, symbolic.SymbolicOutcome] | None=None, unbound: frozenset[int] | set[int]=frozenset()) -> CheckedSteps` ([source](../../../../../../src/learnloop/workbench/check.py), line 338) — The check as shown: every claim checked in code (module docstring).
- `claims_from(output: WorkbenchCheckOutputV1, steps: Sequence[hint_workbench.WorkbenchStep], *, problem_text: str='') -> list[symbolic.SymbolicClaim]` ([source](../../../../../../src/learnloop/workbench/check.py), line 479) — The declared transformations, indexed by step number, each carrying the step's own text to be parsed and checked (:func:`_claim`).
- `hint_claim_verifier(vault: Any, item: Any, *, sandbox_run: Callable[..., Any] | None=None, symbolic_now: Callable[[], bool] | None=None) -> Callable[[Sequence[Any], Any], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/workbench/check.py), line 509) — The check path for a hint's own claims (Reader §5.3 "hints are verified separately"; fix round 1, F14), handed to the hint service.
- `ledger_rows(output: WorkbenchCheckOutputV1, steps: Sequence[hint_workbench.WorkbenchStep], checked: CheckedSteps, claims: Sequence[symbolic.SymbolicClaim], outcomes: Mapping[int, symbolic.SymbolicOutcome], *, sandbox_ran: bool) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/check.py), line 575) — What the check appends to ``judgment_ledger`` (pure): one ``llm`` verdict per step the model judged, with what validation did to it and the verdict shown; one ``verifier`` verdict per declared transformation the sandbox ran (whether it was bound to the learner's step, F3).
- `steps_hash(steps: Sequence[hint_workbench.WorkbenchStep]) -> str` ([source](../../../../../../src/learnloop/workbench/check.py), line 634)
- `class CheckResult` ([source](../../../../../../src/learnloop/workbench/check.py), line 639)
- `last_check(repository: Repository, workbench_session_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/workbench/check.py), line 647) — The problem's last SHOWN check row, or None.
- `run_check(vault: Any, repository: Repository, *, workbench_session_id: str, submission_id: str, item: Any, steps: Sequence[hint_workbench.WorkbenchStep], client: Any | None=None, sandbox_run: Callable[..., Any] | None=None, clock: Clock | None=None, cancelled: Callable[[], bool] | None=None, symbolic_now: Callable[[], bool] | None=None) -> CheckResult` ([source](../../../../../../src/learnloop/workbench/check.py), line 656) — Check the steps; the row is written prepared (``shown = 0``) and shown when the workbench receives it.
- `check_view(row: Mapping[str, Any], steps: Sequence[hint_workbench.WorkbenchStep], *, symbolic_enabled: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/check.py), line 766) — What the workbench shows of a check (no map node or route: the map contains the solution and reaches the learner only through hints).

### Module constants

- `ROUTE_TASK` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 70)
- `OWNER_KIND` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 71)
- `PROMPT_VERSION` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 72)
- `ENVELOPE` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 73)
- `ENVELOPE_OWNER_KINDS` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 75)
- `MODELS_ENV` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 78)
- `VERDICTS` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 79)
- `_CAPS` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 81)
- `STEP_CHARS` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 82)
- `MARKS` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 87)
- `METHOD_LABELS` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 90)
- `NEUTRAL_REASON` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 92)
- `_INSTRUCTIONS` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 155)
- `LEDGER_TASK` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 564)
- `LEDGER_TASK_SYMBOLIC` ([src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py), line 565)

### Explicit exports

`__all__` declares:

- `CheckResult`
- `CheckRoute`
- `CheckUnavailable`
- `CheckedSteps`
- `ENVELOPE`
- `LEDGER_TASK`
- `LEDGER_TASK_SYMBOLIC`
- `MARKS`
- `METHOD_LABELS`
- `MODELS_ENV`
- `OWNER_KIND`
- `PROMPT_VERSION`
- `ROUTE_TASK`
- `WorkbenchCheckOutputV1`
- `build_prompt`
- `check_view`
- `claims_from`
- `daily_envelope`
- `hint_claim_verifier`
- `last_check`
- `ledger_rows`
- `run_check`
- `session_calls`
- `session_calls_on`
- `steps_hash`
- `validate`

## Internal implementation anchors

- `_squash(text: str) -> str` ([source](../../../../../../src/learnloop/workbench/check.py), line 314)
- `_leaks(text: str, item: Any) -> bool` ([source](../../../../../../src/learnloop/workbench/check.py), line 334)
- `_claim(index: int, transformation: Any, text: str, earlier: Sequence[hint_workbench.WorkbenchStep], problem_text: str, names_context: Sequence[str]=()) -> symbolic.SymbolicClaim` ([source](../../../../../../src/learnloop/workbench/check.py), line 459) — Fix round 3 (the orchestrator's ruling on F3): what is checked is ``text``, the learner's own writing, parsed from its LaTeX in the sandbox (:mod:`learnloop.workbench.symbolic`).
- `_switch_now(vault: Any, symbolic_now: Callable[[], bool] | None) -> bool` ([source](../../../../../../src/learnloop/workbench/check.py), line 496) — Fix round 13: ``workbench.symbolic_checks_enabled`` NOW: the caller's live reader (the sidecar's current vault, after any reload), else this vault's; an unreadable switch is off.
- `_step_of(entry: str) -> str | None` ([source](../../../../../../src/learnloop/workbench/check.py), line 568) — The step number a ``dropped`` entry names (``kind:3``, ``kind:3->1``).
- `_append_ledger(connection: Any, assist_id: str, rows: Sequence[Mapping[str, Any]], *, model: str | None, input_hash: str, created_at: str) -> None` ([source](../../../../../../src/learnloop/workbench/check.py), line 618)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] — imports `session_calls_on`; statically calls `session_calls_on`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `CheckRoute`, `CheckUnavailable`, `daily_envelope`; statically calls `CheckRoute`, `daily_envelope`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `session_calls_on`; statically calls `session_calls_on`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `module`; statically calls `check_view`, `daily_envelope`, `hint_claim_verifier`, `run_check`, `session_calls`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `module`; statically calls `daily_envelope`, `session_calls`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `call_labels`, `content_key`; calls `call_labels`, `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`; calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `module`; calls `insert_assist`, `workbench_rows`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `module`; calls `StepVerdict`, `WorkbenchHintContext`, `current_map_for`, `map_for_prompt`, `place_steps`, `text_leaks`, `verdict_from_record`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `PaidRoute`, `plan_route`, `resolve_client`; calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SharedDailyEnvelope`, `midnight`; calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `verdict_records`; calls `verdict_records`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/workbench/symbolic|learnloop.workbench.symbolic]] — imports `module`; calls `SymbolicClaim`, `run_checks`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `os`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]], [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]], [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rw2b_fix5.py](../../../../../../tests/test_reader_rw2b_fix5.py) — direct import
  - `test_item3_the_snapshot_and_the_check_view_carry_a_full_text_fingerprint`
- [tests/test_reader_rw2b_review.py](../../../../../../tests/test_reader_rw2b_review.py) — direct import
  - `test_f3r_a_hints_claim_about_part_of_a_side_is_the_models_reading`
  - `test_f9_the_search_runs_inside_the_workbench_envelope_and_a_spent_day_refuses_it`
- [tests/test_workbench_check.py](../../../../../../tests/test_workbench_check.py) — direct import
  - `test_a_check_runs_on_codex_with_its_cost_estimated_from_tokens`
  - `test_the_prompt_carries_the_steps_and_the_map_never_a_grader`
- [tests/test_workbench_passage_draw.py](../../../../../../tests/test_workbench_passage_draw.py) — direct import
  - `test_another_passage_is_a_learner_pick_one_click_away_and_no_call`
- [tests/test_workbench_route_example.py](../../../../../../tests/test_workbench_route_example.py) — direct import
  - `test_show_me_a_similar_example_is_one_of_the_problems_calls`

## Modification guidance

- Make changes here when the responsibility remains check within learnloop.workbench; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/workbench/check.py](../../../../../../src/learnloop/workbench/check.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
