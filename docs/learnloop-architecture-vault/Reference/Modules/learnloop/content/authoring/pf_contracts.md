---
title: "learnloop.content.authoring.pf_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/pf_contracts.py"
source_paths:
  - "src/learnloop/content/authoring/pf_contracts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.pf_contracts module"
  - "src/learnloop/content/authoring/pf_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.pf_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.pf_contracts` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: Wire contracts and versioned prompts for every PF-b model role (Slice 2 §5.3-§5.6).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py) |
| Source lines | 443 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SkeletonResult(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 53)
- `class GeneratorProgramResult(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 60)
- `class ProposedCandidate(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 66)
- `class ProposalBatch(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 77)
- `class PanelSolve(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 81)
- `class EquivalenceResult(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 87)
- `class StructureVerdict(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 93)
- `class FreshnessComparison(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 100)
- `class FreshnessVerdict(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 106)
- `class SelectionVerdict(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 118)
- `class PairwiseVerdict(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 124)
- `class TraceVariant(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 131)
- `class SourceAnchoredCandidate(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 137) — Answer first: the cited span, then the answer it supports, then the question.
- `class SourceAnchoredBatch(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 150)
- `class SpanSupportVerdict(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 154) — The reference verifier's check that a cited span supports the item's key.
- `class ValidAlternativeTraces(WireModel)` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 168)
- `skeleton_prompt(*, prompt: str, expected_answer: Any) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 179)
- `generator_program_prompt(*, parent: Mapping[str, Any], family: Mapping[str, Any], skeleton: Mapping[str, Any], relation: str, previous_failure: str | None, attempt: int=0) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 222)
- `proposer_prompt(*, parent: Mapping[str, Any], family: Mapping[str, Any], skeleton: Mapping[str, Any], relation: str, count: int, generation_seed: str, single_shot: bool=False) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 250)
- `panel_solve_prompt(*, stem: str, solve_index: int) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 272)
- `equivalence_prompt(*, stem: str, reference: str, answers: list[str]) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 303)
- `structure_prompt(*, parent: Mapping[str, Any], candidate: Mapping[str, Any], declared_relation: str) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 321)
- `freshness_prompt(*, candidate: Mapping[str, Any], comparisons: list[Mapping[str, Any]]) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 336)
- `selection_prompt(*, family: Mapping[str, Any], survivors: list[Mapping[str, Any]], slots: int) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 348)
- `pairwise_prompt(*, a: Mapping[str, Any], b: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 361)
- `source_anchored_prompt(*, passages: list[Mapping[str, Any]], parent: Mapping[str, Any], family: Mapping[str, Any], count: int, generation_seed: str) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 372)
- `span_support_prompt(*, question: str, cited_span: str, reference_answer: str, explanation: str, item_kind: str) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 390)
- `closed_book_prompt(*, stem: str) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 408)
- `valid_alternative_prompt(*, prompt: str, reference: str, count: int) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 418)

### Module constants

- `SKELETON_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 21)
- `GENERATOR_PROGRAM_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 27)
- `PROPOSER_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 28)
- `SINGLE_SHOT_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 29)
- `PANEL_SOLVE_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 30)
- `EQUIVALENCE_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 31)
- `STRUCTURE_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 32)
- `FRESHNESS_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 33)
- `SELECTION_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 34)
- `PAIRWISE_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 35)
- `VALID_ALTERNATIVE_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 36)
- `SOURCE_ANCHORED_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 37)
- `CLOSED_BOOK_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 38)
- `SPAN_SUPPORT_PROMPT` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 39)
- `_SEED_INSTRUCTION` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 42)
- `_DATA_NOT_INSTRUCTIONS` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 47)
- `FRESHNESS_VERDICTS` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 113)
- `FRESHNESS_DUPLICATE_VERDICTS` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 115)
- `_PROGRAM_TEMPLATE` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 191)
- `_EQUIVALENCE_TEMPLATE` ([src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 283)

### Explicit exports

`__all__` declares:

- `EQUIVALENCE_PROMPT`
- `FRESHNESS_DUPLICATE_VERDICTS`
- `FRESHNESS_PROMPT`
- `FRESHNESS_VERDICTS`
- `GENERATOR_PROGRAM_PROMPT`
- `PAIRWISE_PROMPT`
- `PANEL_SOLVE_PROMPT`
- `PROPOSER_PROMPT`
- `SELECTION_PROMPT`
- `SINGLE_SHOT_PROMPT`
- `CLOSED_BOOK_PROMPT`
- `SKELETON_PROMPT`
- `SOURCE_ANCHORED_PROMPT`
- `STRUCTURE_PROMPT`
- `VALID_ALTERNATIVE_PROMPT`
- `SPAN_SUPPORT_PROMPT`
- `SourceAnchoredBatch`
- `SourceAnchoredCandidate`
- `SpanSupportVerdict`
- `span_support_prompt`
- `EquivalenceResult`
- `FreshnessComparison`
- `FreshnessVerdict`
- `GeneratorProgramResult`
- `PairwiseVerdict`
- `PanelSolve`
- `ProposalBatch`
- `ProposedCandidate`
- `SelectionVerdict`
- `SkeletonResult`
- `StructureVerdict`
- `TraceVariant`
- `ValidAlternativeTraces`
- `equivalence_prompt`
- `freshness_prompt`
- `generator_program_prompt`
- `pairwise_prompt`
- `closed_book_prompt`
- `panel_solve_prompt`
- `proposer_prompt`
- `selection_prompt`
- `skeleton_prompt`
- `source_anchored_prompt`
- `structure_prompt`
- `valid_alternative_prompt`

## Internal implementation anchors

- `_prompt(title: str, version: str, instructions: str, context: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/authoring/pf_contracts.py), line 173)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `module`; statically calls `equivalence_prompt`, `freshness_prompt`, `skeleton_prompt`, `valid_alternative_prompt`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `module`; statically calls `closed_book_prompt`, `equivalence_prompt`, `freshness_prompt`, `generator_program_prompt`, `panel_solve_prompt`, `proposer_prompt`, `selection_prompt`, `skeleton_prompt`, `source_anchored_prompt`, `span_support_prompt`, `structure_prompt`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `module`; statically calls `pairwise_prompt`
- [[Reference/Modules/learnloop/ops/pf_verify|learnloop.ops.pf_verify]] — imports `module`; statically calls `equivalence_prompt`, `panel_solve_prompt`, `span_support_prompt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/authoring/pf_sandbox|learnloop.content.authoring.pf_sandbox]] — imports `EQUIVALENCE_PROTOCOL`, `GENERATOR_PROTOCOL`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `REQUIRED_METHOD_VARIANT_GUIDANCE`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]], [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]], [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]], [[Reference/Modules/learnloop/ops/pf_verify|learnloop.ops.pf_verify]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/pf_fakes.py](../../../../../../../tests/pf_fakes.py) — direct import
- [tests/source_service_fakes.py](../../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_key_ladder_labels.py](../../../../../../../tests/test_key_ladder_labels.py) — direct import
- [tests/test_pf_generation.py](../../../../../../../tests/test_pf_generation.py) — direct import
  - `test_a_new_round_asks_the_proposers_again_with_its_own_generation_seed`
  - `test_a_program_that_fails_its_tests_is_retried_then_the_family_publishes_nothing`
  - `test_a_quote_check_without_its_span_support_verdict_is_never_verified`
  - `test_an_unrelated_or_contradicted_quote_never_verifies_a_reference`
  - `test_generator_path_writes_a_tested_program_and_publishes_cas_verified_draws`
  - `test_panel_difficulty_is_a_logit_offset_from_the_parent`
  - `test_panel_disagreement_is_never_published_even_by_an_eager_judge`
- [tests/test_pf_reports.py](../../../../../../../tests/test_pf_reports.py) — direct import
  - `test_each_scaling_tier_runs_its_own_program_writer_on_identical_inputs`
- [tests/test_pf_sandbox.py](../../../../../../../tests/test_pf_sandbox.py) — direct import
  - `test_the_prompt_templates_accept_their_own_tuple_answers`
- [tests/test_pf_verify_extraction_parity.py](../../../../../../../tests/test_pf_verify_extraction_parity.py) — direct import
- [tests/test_required_method_items.py](../../../../../../../tests/test_required_method_items.py) — direct import
  - `test_authoring_prompts_carry_the_rule_and_moved_their_versions`
- [tests/test_required_method_rereview.py](../../../../../../../tests/test_required_method_rereview.py) — direct import
  - `test_f14_the_generation_guidance_leaves_the_sentence_to_the_writer`

## Modification guidance

- Change pf contracts policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/pf_contracts.py](../../../../../../../src/learnloop/content/authoring/pf_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
