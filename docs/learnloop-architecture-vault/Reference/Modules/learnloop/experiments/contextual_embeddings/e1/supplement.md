---
title: "learnloop.experiments.contextual_embeddings.e1.supplement"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/e1/supplement.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/e1/supplement.py"
source_commit: "f33994399e9e5ec0063191972fdfc28c0e7c9487"
source_commit_timestamp: "2026-10-23T22:20:45-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings.e1"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.e1.supplement module"
  - "src/learnloop/experiments/contextual_embeddings/e1/supplement.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings-e1"
---

# `learnloop.experiments.contextual_embeddings.e1.supplement`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.e1.supplement` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] to own the behavior summarized by its module contract: Labels for the v2 arms' NEW candidates (spec §5.2 rules, E1's $5 plan).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/e1/supplement.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py) |
| Source lines | 345 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f33994399e9e5ec0063191972fdfc28c0e7c9487` |
| Commit timestamp | `2026-10-23T22:20:45-04:00` |

## Public API

- `class SupplementPass(WireModel)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 71)
- `class SupplementVerdict(WireModel)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 76)
- `class Supplement` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 83)
- `new_candidates(question: BankQuestion, labels: QuestionLabels | None, v2_rankings: Mapping[str, Mapping[str, Sequence[str]]], *, depth: int=e1_pins.SUPPLEMENT_DEPTH) -> list[str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 97) — Units in any v2 arm's top ``depth`` that E0's labels never judged.
- `judged_support(labels: QuestionLabels) -> list[str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 111)
- `label_supplement(question: BankQuestion, labels: QuestionLabels, candidates: Sequence[str], snapshot: CorpusSnapshot, caller: Any) -> Supplement` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 147) — Two blinded passes over the new candidates (see the module docstring).
- `needs_audit(item: Supplement) -> str | None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 177)
- `audit_plan(items: Sequence[Supplement], *, share: float=pins.AUDIT_SAMPLE_SHARE) -> dict[str, str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 187)
- `adjudicate_supplement(question: BankQuestion, labels: QuestionLabels, item: Supplement, snapshot: CorpusSnapshot, caller: Any) -> Supplement` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 200)
- `accept_agreed(item: Supplement) -> Supplement` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 249)
- `supplement_all(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], labels: Mapping[str, QuestionLabels], v2_rankings: Mapping[str, Mapping[str, Sequence[str]]], caller: Any) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 255) — Every question's new candidates labelled and audited; a stop keeps what was done (the rest stays unknown and is counted).
- `supplement_agreement(items: Sequence[Supplement] | Any) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 311)
- `merge(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], labels: Mapping[str, QuestionLabels], items: Mapping[str, Supplement]) -> dict[str, int]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 322) — Fold accepted supplementary labels into E0's (in place); returns counts.

### Module constants

- `SUPPORTING` ([src/learnloop/experiments/contextual_embeddings/e1/supplement.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 52)
- `SUPPLEMENT_RULE` ([src/learnloop/experiments/contextual_embeddings/e1/supplement.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 54)
- `SUPPLEMENT_INSTRUCTIONS` ([src/learnloop/experiments/contextual_embeddings/e1/supplement.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 61)
- `E1_ROLE_PINS` ([src/learnloop/experiments/contextual_embeddings/e1/supplement.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 64)

## Internal implementation anchors

- `_refs(prefix: str, units: Sequence[str]) -> dict[str, str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 115)
- `_prompt(title: str, version: str, instructions: str, question: BankQuestion, snapshot: CorpusSnapshot, judged: Mapping[str, str], candidates: Mapping[str, str], final: Mapping[str, str], extra: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 119)
- `_sets(chosen: Sequence[Sequence[str]], judged: Mapping[str, str], candidates: Mapping[str, str]) -> tuple[list[frozenset[str]], int]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py), line 132) — Well-formed new sets (known refs, no repeats, at least one candidate).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `E1_ROLE_PINS`, `Supplement`, `merge`, `new_candidates`, `supplement_all`; statically calls `Supplement`, `merge`, `new_candidates`, `supplement_all`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `BankQuestion`, `CandidateLabel`, `QuestionLabels`, `RELEVANCE_ORDER`, `RELEVANCE_RUBRIC`, `evidence_sets_from_labels`, `label_context`, `stable_order`; calls `evidence_sets_from_labels`, `label_context`, `stable_order`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0ProviderFailure`, `E0Stop`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `CorpusSnapshot`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/pins|learnloop.experiments.contextual_embeddings.e1.pins]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/metrics|learnloop.experiments.contextual_embeddings.metrics]] — imports `cohen_kappa`; calls `cohen_kappa`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e1_harness.py](../../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_the_whole_pilot_with_fakes`
- [tests/test_e1_supplement.py](../../../../../../../../tests/test_e1_supplement.py) — direct import
  - `test_a_set_without_a_new_candidate_or_with_a_background_member_is_malformed`
  - `test_an_unresolved_verdict_leaves_the_new_candidates_unknown`
  - `test_only_unjudged_units_in_a_v2_top_ten_are_new`
  - `test_passes_are_blinded_new_sets_are_audited_and_merged`
  - `test_the_e1_roles_are_e0s_metered_messages_api_pins_with_e1_prompt_versions`

## Modification guidance

- Make changes here when the responsibility remains supplement within learnloop.experiments.contextual_embeddings.e1; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/e1/supplement.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/supplement.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
