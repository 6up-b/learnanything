---
title: "learnloop.diagnosis.split.validation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/validation.py"
source_paths:
  - "src/learnloop/diagnosis/split/validation.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.validation module"
  - "src/learnloop/diagnosis/split/validation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.validation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.validation` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: Deterministic validators for ``DiagnosisProposal`` (Slice 1 §5.4, §5.5).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/validation.py](../../../../../../../src/learnloop/diagnosis/split/validation.py) |
| Source lines | 687 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `protected_targets(item: PracticeItem, rubric: Rubric, vault: LoadedVault, *, criterion_points: Mapping[str, float], facets: Iterable[str], criteria: Iterable[str]) -> tuple[frozenset[str], frozenset[str]]` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 77) — (protected facets, passed criteria) by the passed-target firewall.
- `local_support(statement: str, local_texts: Sequence[str]) -> float` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 112) — Share of the cause's content words present in the blind local reading.
- `class ValidatedCitation` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 123)
- `class ValidatedDiagnosis` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 134)
  - `unknown_id_count(self) -> int` (line 142; public)
  - `cited_attempt_ids(self) -> list[str]` (line 145; public)
  - `citations_as_dicts(self) -> list[dict[str, Any]]` (line 157; public)
- `validate_diagnosis_proposal(proposal: DiagnosisProposal, *, assembled: AssembledContext, current: CurrentAttempt, vault: LoadedVault, item: PracticeItem, rubric: Rubric, store: HistoryStore, snapshot_known: KnownIds | None=None) -> ValidatedDiagnosis` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 225) — Apply every §5.4 rule; return the surviving proposal and the report.
- `primary_cause(payload: Mapping[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 631) — (event, cause) with the highest stated prior weight; first on ties.

### Module constants

- `_WORD` ([src/learnloop/diagnosis/split/validation.py](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 52)
- `_STOPWORDS` ([src/learnloop/diagnosis/split/validation.py](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 53)
- `LOCAL_SUPPORT_THRESHOLD` ([src/learnloop/diagnosis/split/validation.py](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 63)
- `CAUSAL_CAUSE_SCOPES` ([src/learnloop/diagnosis/split/validation.py](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 201)

### Explicit exports

`__all__` declares:

- `LOCAL_SUPPORT_THRESHOLD`
- `ValidatedCitation`
- `ValidatedDiagnosis`
- `local_support`
- `primary_cause`
- `protected_targets`
- `validate_diagnosis_proposal`

## Internal implementation anchors

- `class _FacetProbe` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 67) — A stand-in attribution, so the grader's firewall rule decides protection.
- `_content_words(text: str) -> set[str]` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 104)
- `class _Report` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 172)
- `_trace_checkpoints(item: PracticeItem) -> dict[str, set[str]]` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 204) — Recipe id -> checkpoint ids of the item's AVAILABLE trace contract.
- `_facet_of(ref: Any) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 213)
- `_criterion_of(ref: Any) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 219)
- `_citation_invalid_reason(prior: HistoryAttempt, targets: set[str]) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 625) — S4: a valid non-pass on an overlapping target, judged per observation.
- `_anchoring(payload: Mapping[str, Any], grade: Mapping[str, Any], known: KnownIds) -> tuple[bool, dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/split/validation.py), line 646)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/offline_review/judge|learnloop.diagnosis.offline_review.judge]] — imports `primary_cause`; statically calls `primary_cause`
- [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]] — imports `primary_cause`; statically calls `primary_cause`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `validate_diagnosis_proposal`; statically calls `validate_diagnosis_proposal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `enforce_passed_target_firewall`, `resolve_quote_anchor`; calls `enforce_passed_target_firewall`, `resolve_quote_anchor`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `validate_repair_candidate`; calls `validate_repair_candidate`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `AssembledContext`, `CurrentAttempt`, `KnownIds`
- [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] — imports `CAUSE_REF_PREFIX`, `DiagnosisProposal`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `HistoryAttempt`, `HistoryStore`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/offline_review/judge|learnloop.diagnosis.offline_review.judge]], [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]], [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_contract.py](../../../../../../../tests/test_diagnosis_contract.py) — direct import
  - `test_anchoring_suspect_when_a_reused_hypothesis_lacks_local_support`
- [tests/test_pfc_unassessed_readers.py](../../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_later_diagnosis_cannot_cite_an_unassessed_shortfall_as_a_recurrence`

## Modification guidance

- Change validation policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/validation.py](../../../../../../../src/learnloop/diagnosis/split/validation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
