---
title: "learnloop.projects.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/projects/ai_contracts.py"
source_paths:
  - "src/learnloop/projects/ai_contracts.py"
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
  - "learnloop.projects.ai_contracts module"
  - "src/learnloop/projects/ai_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-projects"
---

# `learnloop.projects.ai_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.projects.ai_contracts` exists within [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] to own the behavior summarized by its module contract: Structured AI contracts for delayed probes (spec §5.2, §7; gate G3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py) |
| Source lines | 227 |
| Owning package | [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ProbeAuthoringContext` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 35) — Item-side material only: the redacted bundle and the generation request.
- `class ClosedBookContext` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 46) — Questions only: no diff, no repo, no reference answers.
- `class ProbeGradingContext` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 53) — Questions, verified references with their quoted evidence, and answers.
- `class ProbeCitation(WireModel)` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 62)
- `class ProbeCandidate(WireModel)` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 71)
- `class ProbeCandidates(WireModel)` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 80)
- `class ClosedBookAnswer(WireModel)` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 84)
- `class ClosedBookAnswers(WireModel)` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 89)
- `class ProbeGrade(WireModel)` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 93)
- `class ProbeGrades(WireModel)` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 100)
- `probe_authoring_prompt(context: ProbeAuthoringContext) -> str` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 180)
- `closed_book_prompt(context: ClosedBookContext) -> str` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 188)
- `probe_grading_prompt(context: ProbeGradingContext) -> str` ([source](../../../../../../src/learnloop/projects/ai_contracts.py), line 196)

### Module constants

- `PROBE_KINDS` ([src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py), line 22)
- `CITATION_SOURCES` ([src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py), line 23)
- `PROBE_AUTHORING_PROMPT_VERSION` ([src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py), line 25)
- `CLOSED_BOOK_PROMPT_VERSION` ([src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py), line 26)
- `PROBE_GRADING_PROMPT_VERSION` ([src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py), line 27)
- `PROBE_AUTHORING_PURPOSE` ([src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py), line 29)
- `CLOSED_BOOK_PURPOSE` ([src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py), line 30)
- `PROBE_GRADING_PURPOSE` ([src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py), line 31)
- `BLIND_CONTEXTS` ([src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py), line 59)
- `PROBE_AUTHORING_PROMPT` ([src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py), line 104)
- `CLOSED_BOOK_PROMPT` ([src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py), line 151)
- `PROBE_GRADING_PROMPT` ([src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py), line 160)

### Explicit exports

`__all__` declares:

- `BLIND_CONTEXTS`
- `CITATION_SOURCES`
- `CLOSED_BOOK_PROMPT_VERSION`
- `CLOSED_BOOK_PURPOSE`
- `ClosedBookAnswer`
- `ClosedBookAnswers`
- `ClosedBookContext`
- `PROBE_AUTHORING_PROMPT_VERSION`
- `PROBE_AUTHORING_PURPOSE`
- `PROBE_GRADING_PROMPT_VERSION`
- `PROBE_GRADING_PURPOSE`
- `PROBE_KINDS`
- `ProbeAuthoringContext`
- `ProbeCandidate`
- `ProbeCandidates`
- `ProbeCitation`
- `ProbeGrade`
- `ProbeGrades`
- `ProbeGradingContext`
- `closed_book_prompt`
- `probe_authoring_prompt`
- `probe_grading_prompt`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]] — imports `CLOSED_BOOK_PROMPT_VERSION`, `CLOSED_BOOK_PURPOSE`, `ClosedBookAnswers`, `ClosedBookContext`, `PROBE_AUTHORING_PROMPT_VERSION`, `PROBE_AUTHORING_PURPOSE`, `PROBE_GRADING_PROMPT_VERSION`, `PROBE_GRADING_PURPOSE`, `PROBE_KINDS`, `ProbeAuthoringContext`, `ProbeCandidate`, `ProbeCandidates`, `ProbeGrades`, `ProbeGradingContext`, `closed_book_prompt`, `probe_authoring_prompt`, `probe_grading_prompt`; statically calls `ClosedBookContext`, `ProbeAuthoringContext`, `ProbeGradingContext`, `closed_book_prompt`, `probe_authoring_prompt`, `probe_grading_prompt`
- [[Reference/Modules/learnloop/projects/report|learnloop.projects.report]] — imports `CLOSED_BOOK_PROMPT_VERSION`, `PROBE_AUTHORING_PROMPT_VERSION`, `PROBE_GRADING_PROMPT_VERSION`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]], [[Reference/Modules/learnloop/projects/report|learnloop.projects.report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/project_support.py](../../../../../../tests/project_support.py) — direct import
- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/test_ai_tool_isolation.py](../../../../../../tests/test_ai_tool_isolation.py) — direct import
  - `test_a_confinable_agent_runs_inside_the_isolation`
  - `test_an_unconfinable_agent_is_refused_before_any_request`
  - `test_the_kill_switch_runs_unconfined_and_says_so`
- [tests/test_project_blindness.py](../../../../../../tests/test_project_blindness.py) — direct import
  - `test_context_dataclasses_have_no_field_for_arm_explanation_judge_or_provenance`
- [tests/test_project_cli.py](../../../../../../tests/test_project_cli.py) — direct import
  - `test_hidden_retries_are_admitted_only_against_max_retries`
  - `test_metered_calls_carry_their_admitted_output_limit`
  - `test_metered_output_limit_reaches_the_provider_request_and_its_repair`
- [tests/test_project_probes.py](../../../../../../tests/test_project_probes.py) — direct import
  - `test_a_cited_comment_must_state_the_proposed_reason`
  - `test_a_descriptive_commit_subject_is_not_a_reason`
  - `test_a_fenced_code_block_in_an_adr_is_still_code`
  - `test_a_plain_markdown_adr_paragraph_states_its_reason`
  - `test_a_rationale_flag_on_plain_code_is_not_a_stated_reason`
  - `test_answer_first_schema_and_prompt`
  - `test_authoring_prompt_carries_numbered_lines`
  - `test_citations_must_resolve_and_quote_verbatim`
  - `test_errors_never_quote_model_output`
  - `test_incomplete_closed_book_answers_never_pass_the_filter`
  - `test_model_returning_extra_candidates_is_capped`
  - `test_redacted_lines_cannot_be_quoted`

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/projects/ai_contracts.py](../../../../../../src/learnloop/projects/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
