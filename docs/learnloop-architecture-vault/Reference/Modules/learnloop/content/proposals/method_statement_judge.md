---
title: "learnloop.content.proposals.method_statement_judge"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/proposals/method_statement_judge.py"
source_paths:
  - "src/learnloop/content/proposals/method_statement_judge.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.proposals"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.proposals.method_statement_judge module"
  - "src/learnloop/content/proposals/method_statement_judge.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-proposals"
---

# `learnloop.content.proposals.method_statement_judge`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.proposals.method_statement_judge` exists within [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] to own the behavior summarized by its module contract: The one-time judgment on a statement that must not be rewritten (redesign 2026-10-14).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py) |
| Source lines | 501 |
| Owning package | [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `default_caps(calls: int=50) -> SpendCaps` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 125) — One run's bound: ``calls`` judgments and $0.25 (a Decider request costs about $0.00002; an LLM judgment about $0.001 at Haiku's price).
- `decider_state(question: Question, statement: str, method: str) -> str` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 153) — What the Decider reads (the statement verbatim).
- `decider_question(question: Question, method: str) -> Any` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 163)
- `class SourceStatementReading(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 169)
- `class VariantStemReading(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 174)
- `llm_prompt(question: Question, statement: str, method: str) -> str` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 182)
- `statement_input_hash(question: Question, statement: str, method: str) -> str` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 195) — The judged input: the question set, the statement verbatim and the method's name.
- `planned_tokens(question: Question, statement: str, method: str) -> int` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 202) — An upper bound on one judgment's tokens, from text alone (a dry run): the larger of the Decider's request and the LLM judge's prompt, schema and output allowance.
- `argmax(question: Question, probabilities: Mapping[str, float]) -> str` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 215) — The most probable option; a tie goes to the conservative one.
- `class StatementVerdict` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 227) — One judgment: the deciding option and its ledger row.
- `recorded_verdict(connection: Any, *, question: Question, subject_kind: str, subject_id: str, statement: str, method: str) -> StatementVerdict | None` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 240) — The verdict already recorded for this statement and method, if any.
- `class MethodStatementJudge` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 266) — A resolved judge (the Decider, or the LLM judge) with its own spend.
  - `__init__(self, kind: JudgeKind, client: Any, *, spend: ReviewSpend, provider: str | None=None) -> None` (line 269; internal)
  - `judge(self, repository: Repository, *, question: Question, subject_kind: str, subject_id: str, statement: str, method: str, owner: tuple[str, str], right: tuple[str, str] | None=None, clock: Clock | None=None) -> StatementVerdict` (line 286; public) — The verdict for this statement: reused when recorded, else asked once and ledgered.
- `resolve_statement_judge(vault: LoadedVault, *, clients: Any=None, price_per_million: float | None=None, caps: SpendCaps | None=None, budget_for: Callable[[str], Any] | None=None) -> MethodStatementJudge | None` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 372) — The Decider via its route, else the LLM judge on it; None when neither is ready.
- `class LazyStatementJudge` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 411) — Resolves the judge on first use (most writes never need one), once.
  - `__init__(self, resolve: Callable[[], MethodStatementJudge | None]) -> None` (line 414; internal)
  - `get(self) -> MethodStatementJudge | None` (line 420; public)
- `as_lazy(judge: Any) -> LazyStatementJudge` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 431)
- `source_judge(judge: Any, repository: Repository, *, subject_id: str, owner: tuple[str, str], clock: Clock | None=None, log: Callable[[str], None] | None=None) -> Callable[[str, str], SourceStatementDecision | None]` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 437) — The ``judge_source`` callback the writer check takes for one source statement (``learnloop.vault.required_method.normalize_required_method``): the one-time judgment, or None when no judge is ready or it refused or failed (``log`` hears why).

### Module constants

- `TASK` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 76)
- `SOURCE_QUESTION_SET` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 78)
- `VARIANT_QUESTION_SET` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 79)
- `LLM_PROMPT_VERSION` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 81)
- `PURPOSE` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 82)
- `DECIDER_ROUTE` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 83)
- `SOURCE_OPTIONS` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 88)
- `VARIANT_OPTIONS` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 100)
- `CONSERVATIVE_ORDER` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 113)
- `OPTIONS` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 117)
- `QUESTION_SETS` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 118)
- `CONTRADICTS` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 119)
- `CONSISTENT` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 120)
- `LLM_OUTPUT_TOKENS` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 122)
- `READING_MODELS` ([src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 179)

### Explicit exports

`__all__` declares:

- `CONSERVATIVE_ORDER`
- `CONSISTENT`
- `CONTRADICTS`
- `DECIDER_ROUTE`
- `LLM_PROMPT_VERSION`
- `LazyStatementJudge`
- `MethodStatementJudge`
- `PURPOSE`
- `SOURCE_OPTIONS`
- `SOURCE_QUESTION_SET`
- `SOURCE_REQUIRES`
- `SourceStatementReading`
- `StatementVerdict`
- `TASK`
- `VARIANT_OPTIONS`
- `VARIANT_QUESTION_SET`
- `VariantStemReading`
- `argmax`
- `as_lazy`
- `decider_question`
- `decider_state`
- `default_caps`
- `llm_prompt`
- `planned_tokens`
- `recorded_verdict`
- `resolve_statement_judge`
- `source_judge`
- `statement_input_hash`

## Internal implementation anchors

- `_estimate_tokens(text: str) -> int` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 134) — An upper bound on ``text``'s input tokens: its UTF-8 bytes.
- `_instructions(question: Question, method: str) -> str` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 140)
- `_injected(clients: Any) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py), line 359) — Tests (and callers) may inject the judge: a Decider client (it has ``decide``), an LLM client, or a mapping ``{"decider": ..., "llm": ...}``.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `LazyStatementJudge`, `resolve_statement_judge`, `source_judge`; statically calls `LazyStatementJudge`, `resolve_statement_judge`, `source_judge`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `LazyStatementJudge`, `resolve_statement_judge`; statically calls `LazyStatementJudge`, `resolve_statement_judge`
- [[Reference/Modules/learnloop/content/proposals/required_method_override|learnloop.content.proposals.required_method_override]] — imports `TASK`, `statement_input_hash`; statically calls `statement_input_hash`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `LazyStatementJudge`, `planned_tokens`, `recorded_verdict`, `resolve_statement_judge`; statically calls `LazyStatementJudge`, `planned_tokens`, `recorded_verdict`, `resolve_statement_judge`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `CONTRADICTS`, `as_lazy`, `recorded_verdict`; statically calls `as_lazy`, `recorded_verdict`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`; calls `ChoiceQuestion`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `ROUTE`, `decider_profile_name`, `ready_profile_client`, `ready_writer`; calls `decider_profile_name`, `ready_profile_client`, `ready_writer`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `enabled`; calls `enabled`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `ReviewSpend`, `RouteInfo`; calls `ReviewSpend`, `RouteInfo`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `receipt_sink`; calls `receipt_sink`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `SOURCE_REQUIRES`, `SourceStatementDecision`, `required_method_instruction`; calls `SourceStatementDecision`, `required_method_instruction`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/content/proposals/required_method_override|learnloop.content.proposals.required_method_override]], [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]], [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_method_explicit_landing.py](../../../../../../../tests/test_method_explicit_landing.py) — direct import
  - `test_switched_off_the_llm_judge_decides_the_statement`
- [tests/test_required_method_authority.py](../../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_a_metered_llm_judge_without_a_price_is_refused_before_sending_and_decides_nothing`
  - `test_a_source_statement_keeps_the_field_only_by_the_judgment`
  - `test_a_source_statement_with_no_judge_keeps_no_requirement`
  - `test_an_import_keeps_the_field_exactly_when_the_one_time_judgment_says_requires`
  - `test_pf_judges_each_selected_variant_once_and_publication_reads_the_verdict`
  - `test_the_argmax_has_no_threshold_and_a_tie_is_conservative`
  - `test_the_judgment_is_made_once_ledgered_with_probabilities_and_the_argmax_decides`
  - `test_without_a_decider_the_llm_judge_decides_and_without_either_nothing_does`
- [tests/test_required_method_items.py](../../../../../../../tests/test_required_method_items.py) — direct import
  - `test_an_imported_exercise_keeps_a_required_method_only_by_its_one_time_judgment`
- [tests/test_required_method_reopened.py](../../../../../../../tests/test_required_method_reopened.py) — direct import
  - `test_f16_an_accepted_override_appends_the_owners_verdict_superseding_the_judgment`
- [tests/test_required_method_round3_rereview.py](../../../../../../../tests/test_required_method_round3_rereview.py) — direct import
  - `test_f9_the_resume_budgets_the_largest_judgment_estimates_not_the_longest_stems`
- [tests/test_required_method_round3_review.py](../../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f7_a_resume_is_estimated_from_the_persisted_unfinished_stem`

## Modification guidance

- Change method statement judge policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/proposals/method_statement_judge.py](../../../../../../../src/learnloop/content/proposals/method_statement_judge.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
