---
title: "learnloop.experiments.contextual_embeddings.retrieval"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/retrieval.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/retrieval.py"
source_commit: "7e6020e02ac2ef32285a38ee94800039dd54c9d3"
source_commit_timestamp: "2026-10-23T17:26:11-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.retrieval module"
  - "src/learnloop/experiments/contextual_embeddings/retrieval.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.retrieval`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.retrieval` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: E0 retrieval arms R0-R5 (spec §5.4) over the common candidate units.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/retrieval.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py) |
| Source lines | 328 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7e6020e02ac2ef32285a38ee94800039dd54c9d3` |
| Commit timestamp | `2026-10-23T17:26:11-04:00` |

## Public API

- `preceding_text(snapshot: CorpusSnapshot, unit: CandidateUnit) -> tuple[str | None, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 68) — The preceding numbered label and up to ``PRECEDING_CHARS`` of the preceding unit, within the same extraction, section and policy segment.
- `recipe_text(snapshot: CorpusSnapshot, unit: CandidateUnit, recipe: str, headers: Mapping[str, str] | None=None) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 88)
- `document_vector_key(space_id: str, snapshot: CorpusSnapshot, units: Sequence[CandidateUnit], texts: Sequence[str]) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 114) — The spec's ``document_vector_key`` (§4.3): the space, the extraction revision, every context span and offset, the targets, the policy, and the exact texts (which carry any generated-context dependency).
- `documents_for(snapshot: CorpusSnapshot, encoding: str, recipe: str, space_id: str, headers: Mapping[str, str] | None=None) -> tuple[list[Document], dict[str, str]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 126) — The documents an arm encodes, and ``{chunk_id: unit_id}``.
- `exact_search(index: SpaceVectors, query: Sequence[float], *, query_encoder: str, top_k: int=pins.POOL_DEPTH, allowed: set[str] | None=None) -> list[tuple[str, float]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 153) — Ordinary cosine over normalized vectors, best first, ties by id.
- `class BM25` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 177) — Okapi BM25 (k1 1.2, b 0.75) over unit texts; ties by id.
  - `build(cls, texts: Mapping[str, str]) -> BM25` (line 186; public)
  - `search(self, query: str, top_k: int=pins.POOL_DEPTH) -> list[tuple[str, float]]` (line 190; public)
- `class GeneratedContext(WireModel)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 219)
- `class GeneratedContexts(WireModel)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 224)
- `context_prompt(snapshot: CorpusSnapshot, window: Window, targets: Sequence[str] | None=None) -> tuple[str, dict[str, str]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 233) — One prompt per window: its permitted units as the excerpt, one ref per unit.
- `generate_contexts(snapshot: CorpusSnapshot, caller: Any) -> tuple[dict[str, str], dict[str, int]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 282) — ``{unit_id: context}`` for every unit, one call per window; a missing or out-of-range context is counted (``stats``) and the unit is reported without an R3 vector rather than silently given another recipe.
- `units_from_blocks(snapshot: CorpusSnapshot, hits: Sequence[tuple[str, str]]) -> tuple[list[str], dict[str, int]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 308) — Production block hits mapped to the units that hold them (first occurrence), withheld or unmapped blocks dropped and counted.

### Module constants

- `PRECEDING_CHARS` ([src/learnloop/experiments/contextual_embeddings/retrieval.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 52)
- `CONTEXT_PROMPT_VERSION` ([src/learnloop/experiments/contextual_embeddings/retrieval.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 53)
- `CONTEXT_INSTRUCTIONS` ([src/learnloop/experiments/contextual_embeddings/retrieval.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 54)
- `_WORD` ([src/learnloop/experiments/contextual_embeddings/retrieval.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 169)
- `CONTEXT_SUBSET_INSTRUCTIONS` ([src/learnloop/experiments/contextual_embeddings/retrieval.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 229)
- `SPLIT_ON` ([src/learnloop/experiments/contextual_embeddings/retrieval.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 253)
- `SKIP_ON` ([src/learnloop/experiments/contextual_embeddings/retrieval.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 256)

## Internal implementation anchors

- `_sha(*parts: Any) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 61)
- `_terms(text: str) -> list[str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 172)
- `_window_contexts(snapshot: CorpusSnapshot, window: Window, caller: Any, targets: Sequence[str] | None, stats: dict[str, Any]) -> list[tuple[str, str]]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py), line 259)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `preceding_text`; statically calls `preceding_text`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]] — imports `documents_for`, `exact_search`; statically calls `documents_for`, `exact_search`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `generate_contexts`; statically calls `generate_contexts`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `BM25`, `documents_for`, `exact_search`, `generate_contexts`, `recipe_text`; statically calls `documents_for`, `exact_search`, `generate_contexts`, `recipe_text`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/plan|learnloop.experiments.contextual_embeddings.plan]] — imports `context_prompt`, `recipe_text`; statically calls `context_prompt`, `recipe_text`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `units_from_blocks`; statically calls `units_from_blocks`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]] — imports `Chunk`, `Document`, `SpaceVectors`, `assert_compatible`, `query_vector_key`; calls `Chunk`, `Document`, `assert_compatible`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0ProviderFailure`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `CandidateUnit`, `CorpusSnapshot`, `Window`, `alias`; calls `alias`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `math`, `re`, `typing`
- Third party: `numpy`, `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/plan|learnloop.experiments.contextual_embeddings.plan]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_adapters.py](../../../../../../../tests/test_e0_adapters.py) — direct import
  - `test_exact_search_ties_break_by_id`
  - `test_mixed_spaces_and_foreign_query_encoders_are_refused`
- [tests/test_e0_paid_fakes.py](../../../../../../../tests/test_e0_paid_fakes.py) — direct import
  - `test_the_live_caller_admits_each_physical_request_and_resumes_from_checkpoints`
- [tests/test_e0_relabel_round.py](../../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_the_earlier_ledgers_admissions_stay_visible_so_a_known_truncation_is_not_resent`
- [tests/test_e0_review_round8.py](../../../../../../../tests/test_e0_review_round8.py) — direct import
  - `test_a_request_known_truncated_at_the_same_bound_is_not_sent_again`
  - `test_a_single_ref_that_still_truncates_is_counted_missing_not_a_stop`
  - `test_a_truncated_window_is_split_until_every_unit_has_its_context`
  - `test_the_first_paid_runs_failure_marker_is_read_and_truncation_inferred_from_the_ledger`
- [tests/test_e1_harness.py](../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_the_replay_caller_serves_checkpoints_reproduces_failures_and_never_sends`

## Modification guidance

- Make changes here when the responsibility remains retrieval within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/retrieval.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/retrieval.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
