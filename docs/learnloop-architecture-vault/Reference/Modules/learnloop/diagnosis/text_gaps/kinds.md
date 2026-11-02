---
title: "learnloop.diagnosis.text_gaps.kinds"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/text_gaps/kinds.py"
source_paths:
  - "src/learnloop/diagnosis/text_gaps/kinds.py"
source_commit: "943e5a3c56b12babc2926150d93b8742cb8f8efc"
source_commit_timestamp: "2026-10-12T20:50:39-04:00"
source_worktree_state: "clean"
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
  - "learnloop.diagnosis.text_gaps.kinds module"
  - "src/learnloop/diagnosis/text_gaps/kinds.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-text-gaps"
---

# `learnloop.diagnosis.text_gaps.kinds`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.text_gaps.kinds` exists within [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] to own the behavior summarized by its module contract: The two match kinds learner-text gaps register on T1's shared matcher.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py) |
| Source lines | 203 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `943e5a3c56b12babc2926150d93b8742cb8f8efc` |
| Commit timestamp | `2026-10-12T20:50:39-04:00` |

## Public API

- `query_hash(field: str, text: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 111)
- `prerequisite_query_text(name: str, line: str | None) -> str` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 117)
- `prerequisite_query(text: LearnerText, name: str, line: str | None) -> Subject` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 121) — The named prerequisite as the query subject (``learner_gap`` in the ledger).
- `belief_query(text: LearnerText, statement: str) -> Subject` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 135)
- `learning_object_subject(vault: LoadedVault, learning_object_id: str, *, basis: str) -> Subject | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 146)
- `registry_subject(kind: str, record_id: str, statement: str, *, learning_object_id: str | None, basis: str) -> Subject | None` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 168) — A durable misconception (``kind='durable'``) or holding-pen candidate.

### Module constants

- `GAP_RECORD_KIND` ([src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 36)
- `PREREQUISITE_FIELD` ([src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 37)
- `BELIEF_FIELD` ([src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 38)
- `LO_RECIPE` ([src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 39)
- `QUERY_RECIPE_VERSION` ([src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 40)
- `_PREREQUISITE_QUESTION` ([src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 42)
- `_PREREQUISITE_GUIDANCE` ([src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 48)
- `_BELIEF_QUESTION` ([src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 54)
- `_BELIEF_GUIDANCE` ([src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 58)
- `SAME_PREREQUISITE` ([src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 70)
- `SAME_BELIEF` ([src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 90)

### Explicit exports

`__all__` declares:

- `BELIEF_FIELD`
- `GAP_RECORD_KIND`
- `LO_RECIPE`
- `PREREQUISITE_FIELD`
- `SAME_BELIEF`
- `SAME_PREREQUISITE`
- `belief_query`
- `learning_object_subject`
- `prerequisite_query`
- `prerequisite_query_text`
- `query_hash`
- `registry_subject`

## Internal implementation anchors

- `_render(subject: Subject) -> Mapping[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py), line 66)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]] — imports `SAME_BELIEF`, `SAME_PREREQUISITE`, `learning_object_subject`, `registry_subject`; statically calls `learning_object_subject`, `registry_subject`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `BELIEF_FIELD`, `PREREQUISITE_FIELD`, `SAME_BELIEF`, `SAME_PREREQUISITE`, `belief_query`, `prerequisite_query`; statically calls `belief_query`, `prerequisite_query`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `MISCONCEPTION_FIELD`, `MISCONCEPTION_KIND`, `misconception_record`; calls `misconception_record`
- [[Reference/Modules/learnloop/diagnosis/split/retrieval|learnloop.diagnosis.split.retrieval]] — imports `DOCUMENT_PREFIX`, `QUERY_PREFIX`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/contract|learnloop.diagnosis.text_gaps.contract]] — imports `JUDGE_ROUTE`, `LearnerText`, `SAME_BELIEF_TASK`, `SAME_PREREQUISITE_TASK`
- [[Reference/Modules/learnloop/matching/kinds|learnloop.matching.kinds]] — imports `MatchKind`, `Subject`; calls `MatchKind`, `Subject`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EMBEDDING_RECIPES`, `learning_object_statement_text`; calls `learning_object_statement_text`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]], [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_the_vault_wide_shortlist_ranks_stored_vectors_and_judges_decide`
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_a_predecessor_second_opinion_is_never_reused_as_the_tier1_verdict`
  - `test_a_tied_gap_pair_goes_to_the_llm`
  - `test_gap_pairs`
  - `test_gap_pairs_reuse_the_deciders_verdict_and_defer_on_a_stopped_fallback`

## Modification guidance

- Change kinds policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/text_gaps/kinds.py](../../../../../../../src/learnloop/diagnosis/text_gaps/kinds.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
