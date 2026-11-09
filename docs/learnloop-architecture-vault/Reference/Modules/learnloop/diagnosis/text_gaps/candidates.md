---
title: "learnloop.diagnosis.text_gaps.candidates"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/text_gaps/candidates.py"
source_paths:
  - "src/learnloop/diagnosis/text_gaps/candidates.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.text_gaps"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.text_gaps.candidates module"
  - "src/learnloop/diagnosis/text_gaps/candidates.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-text-gaps"
---

# `learnloop.diagnosis.text_gaps.candidates`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.text_gaps.candidates` exists within [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] to own the behavior summarized by its module contract: Which vault entries a named gap is judged against (grounded, then shortlisted).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/text_gaps/candidates.py](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py) |
| Source lines | 287 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Candidates` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py), line 57)
  - `summary(self) -> dict[str, Any]` (line 66; public)
  - `pairs(self, query: Subject) -> list[CandidatePair]` (line 75; public)
- `declared_prerequisites(vault: LoadedVault, anchors: Sequence[str]) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py), line 90)
- `created_today(repository: Repository, *, day_start: str) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py), line 99) — LOs this pipeline created since ``day_start`` and the learner kept.
- `lexical_rank(query_text: str, pool: Sequence[Subject], top_k: int) -> list[Subject]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py), line 117) — Token-overlap ranking (a fallback nominator only; the judge decides).
- `prerequisite_candidates(vault: LoadedVault, repository: Repository, text: LearnerText, *, query: Subject, query_vector: np.ndarray | None, model_id: str | None, top_k: int, limit: int, day_start: str) -> Candidates` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py), line 132)
- `belief_candidates(vault: LoadedVault, repository: Repository, text: LearnerText, *, query: Subject, query_vector: np.ndarray | None, model_id: str | None, top_k: int, limit: int) -> Candidates` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py), line 215)

### Module constants

- `_WORD` ([src/learnloop/diagnosis/text_gaps/candidates.py](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py), line 50)
- `_STOP` ([src/learnloop/diagnosis/text_gaps/candidates.py](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py), line 51)

### Explicit exports

`__all__` declares:

- `Candidates`
- `belief_candidates`
- `created_today`
- `declared_prerequisites`
- `lexical_rank`
- `prerequisite_candidates`

## Internal implementation anchors

- `_in_subject(vault: LoadedVault, learning_object_id: str, subject_id: str | None) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py), line 83)
- `_tokens(text: str) -> set[str]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py), line 113)
- `_registry_pool(vault: LoadedVault, repository: Repository, *, subject_id: str, exclude: set[str]) -> list[Subject]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py), line 260) — Every registry entry in the subject (durable beliefs and legacy holding-pen rows).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `created_today`; statically calls `created_today`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `belief_candidates`, `prerequisite_candidates`; statically calls `belief_candidates`, `prerequisite_candidates`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `gaps`, `reversals`; calls `gaps`, `reversals`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `_candidate_misconceptions`; calls `_candidate_misconceptions`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `LearnerText`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/kinds|learnloop.diagnosis.text_gaps.kinds]] — imports `SAME_BELIEF`, `SAME_PREREQUISITE`, `learning_object_subject`, `registry_subject`; calls `learning_object_subject`, `registry_subject`
- [[Reference/Modules/learnloop/matching/kinds|learnloop.matching.kinds]] — imports `Subject`
- [[Reference/Modules/learnloop/matching/shortlist|learnloop.matching.shortlist]] — imports `CandidatePair`, `shortlist_pairs`, `stored_vectors`; calls `CandidatePair`, `shortlist_pairs`, `stored_vectors`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `prerequisite_learning_objects`; calls `prerequisite_learning_objects`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `re`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]], [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/mcp_world.py](../../../../../../../tests/mcp_world.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]]
- [tests/test_diagnosis_input_provenance.py](../../../../../../../tests/test_diagnosis_input_provenance.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]]
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../../tests/test_diagnosis_input_provenance_landing.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]]
- [tests/test_followups_nov2_note_gap_unlinked.py](../../../../../../../tests/test_followups_nov2_note_gap_unlinked.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]]
- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]]
- [tests/test_learner_text_gaps_rereview.py](../../../../../../../tests/test_learner_text_gaps_rereview.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]]
- [tests/test_learner_text_gaps_review.py](../../../../../../../tests/test_learner_text_gaps_review.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]]
- [tests/test_mcp_c1a_narrow.py](../../../../../../../tests/test_mcp_c1a_narrow.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]]
- [tests/test_figures_codex_review.py](../../../../../../../tests/test_figures_codex_review.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]]
- [tests/test_figures_fix_round4.py](../../../../../../../tests/test_figures_fix_round4.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]]
- [tests/test_figures_scope_redesign.py](../../../../../../../tests/test_figures_scope_redesign.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]]
- [tests/test_hint_feedback_texts.py](../../../../../../../tests/test_hint_feedback_texts.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]]

## Modification guidance

- Change candidates policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/text_gaps/candidates.py](../../../../../../../src/learnloop/diagnosis/text_gaps/candidates.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
