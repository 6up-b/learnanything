---
title: "learnloop.source_retrieval.spaces"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/spaces.py"
source_paths:
  - "src/learnloop/source_retrieval/spaces.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.spaces module"
  - "src/learnloop/source_retrieval/spaces.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.spaces`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.spaces` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: The source-space resolver: the ONE new seam in ``search_spans`` (spec_local_contextual_retrieval_v1 §5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/spaces.py](../../../../../../src/learnloop/source_retrieval/spaces.py) |
| Source lines | 600 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class LocalQueryEncoder` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 67) — The protocol a P1c teacher session or a P2 student implements.
  - `encode(self, texts: Sequence[str], *, deadline: float | None=None) -> list[Sequence[float]]` (line 72; public)
- `resolver_active(config: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 112) — The resolver runs only when a new space is switched on (else today's path, untouched).
- `query_kind(*, roles: Sequence[str], context_text: str | None, rewritten: bool) -> str` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 119) — The query kind from existing features (§5.2): a role filter, a selection present (deictic), the conceptual rewrite, else a lookup.
- `class SpaceState` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 131)
  - `usable(self) -> bool` (line 148; public)
  - `list_key(self) -> str` (line 152; public) — The list's immutable identity in the fusion model (Codex review F12).
  - `describe(self) -> dict[str, Any]` (line 157; public)
- `class Resolution` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 165)
  - `contributing(self) -> list[str]` (line 194; public)
  - `queried(self) -> list[str]` (line 197; public) — The identities of the lists whose query answered (set by :func:`meaning_lists`).
  - `coverage(self) -> str` (line 203; public) — ``ready`` when every embeddable extraction in scope has a contributor that answered (Codex review F6: an assigned space whose query failed does not cover anything).
  - `describe(self) -> dict[str, Any]` (line 214; public)
- `resolve_source_spaces(vault: LoadedVault, repository: Repository, scope: Scope, *, consumer: str, query_kind: str, deadline: float | None, qwen_index: Any, posteriors: Mapping[str, Mapping[str, Any]] | None=None, receipt_id: str='') -> Resolution` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 321) — The available spaces and their weights for one query, with every reason.
- `meaning_lists(vault: LoadedVault, repository: Repository, resolution: Resolution, texts: Mapping[str, str], *, qwen_index: Any, qwen_vectors: Callable[[], tuple[dict[str, np.ndarray], dict[str, Any]]], depth: Callable[[str], int], permit: Callable[[str], bool], owner_id: str, deadline: float | None, budget: Any | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 448) — Each contributing space's ranking per query text, and the fused lists.
- `space_ranks(per_space: Mapping[str, Mapping[str, Sequence[str]]], key: str='query', *, identities: Mapping[str, str] | None=None) -> dict[str, dict[str, int]]` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 584) — ``{record id: {list identity: rank}}`` in each space's ``key`` list (the fusion model's features); ``identities`` maps a space name to its list identity (Codex review F12), else the name is used.

### Module constants

- `QWEN` ([src/learnloop/source_retrieval/spaces.py](../../../../../../src/learnloop/source_retrieval/spaces.py), line 56)
- `LOCAL_GROUPED` ([src/learnloop/source_retrieval/spaces.py](../../../../../../src/learnloop/source_retrieval/spaces.py), line 57)
- `LOCAL_SINGLETON` ([src/learnloop/source_retrieval/spaces.py](../../../../../../src/learnloop/source_retrieval/spaces.py), line 58)
- `VOYAGE` ([src/learnloop/source_retrieval/spaces.py](../../../../../../src/learnloop/source_retrieval/spaces.py), line 59)
- `USABLE` ([src/learnloop/source_retrieval/spaces.py](../../../../../../src/learnloop/source_retrieval/spaces.py), line 60)
- `PAID_QUERY_SPACES` ([src/learnloop/source_retrieval/spaces.py](../../../../../../src/learnloop/source_retrieval/spaces.py), line 64)
- `LOCAL_QUERY_ENCODER` ([src/learnloop/source_retrieval/spaces.py](../../../../../../src/learnloop/source_retrieval/spaces.py), line 83)

### Explicit exports

`__all__` declares:

- `LOCAL_GROUPED`
- `LOCAL_QUERY_ENCODER`
- `LOCAL_SINGLETON`
- `LocalQueryEncoder`
- `PAID_QUERY_SPACES`
- `QWEN`
- `Resolution`
- `SpaceState`
- `VOYAGE`
- `meaning_lists`
- `query_kind`
- `resolve_source_spaces`
- `resolver_active`
- `space_ranks`

## Internal implementation anchors

- `_adopted_student(vault: LoadedVault) -> LocalQueryEncoder | None` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 76)
- `_encode(encoder: Any, texts: Sequence[str], *, deadline: float | None, receipt_id: str) -> list[Sequence[float]]` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 86) — A local encoder's vectors; the receipt goes to an encoder that queues the teacher replay.
- `_cold_start(encoder: Any, *, deadline: float | None, box_s: float, share: float) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 94) — ``(status, reason)`` when a not-yet-running student should not be waited for, else None.
- `_qwen_state(index: Any, price: float) -> SpaceState` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 224)
- `_contextual_vectors(read: Callable[[str, Mapping[str, Sequence[tuple[str, int]]]], dict[str, np.ndarray]], space_id: str, windows: Mapping[str, Sequence[Any]]) -> tuple[dict[str, dict[str, np.ndarray]], int]` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 234)
- `_local_states(vault: LoadedVault, repository: Repository, windows: Mapping[tuple[str, str], Sequence[Any]], known: Mapping[str, Mapping[str, Any]], *, deadline: float | None=None, share: float=0.0) -> dict[str, SpaceState]` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 251)
- `_voyage_state(vault: LoadedVault, repository: Repository, windows: Mapping[tuple[str, str], Sequence[Any]]) -> SpaceState` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 301)
- `_rank(vectors: Mapping[str, Mapping[str, np.ndarray]], extraction_ids: Sequence[str], query: np.ndarray, *, limit: int, allow: Callable[[str], bool]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/spaces.py), line 419) — Plain cosine over a contextual space's covered blocks (E1's transform), ties by record id.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `resolver_active`; statically calls `resolver_active`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `PAID_QUERY_SPACES`, `resolver_active`; statically calls `resolver_active`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `meaning_lists`, `query_kind`, `resolve_source_spaces`, `resolver_active`, `space_ranks`; statically calls `meaning_lists`, `query_kind`, `resolve_source_spaces`, `resolver_active`, `space_ranks`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `resolver_active`; statically calls `resolver_active`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `resolver_active`; statically calls `resolver_active`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/retrieval_spaces|learnloop.db.stores.retrieval_spaces]] — imports `fusion_posteriors`, `spaces`; calls `fusion_posteriors`, `spaces`
- [[Reference/Modules/learnloop/local_embeddings/cache|learnloop.local_embeddings.cache]] — imports `CacheUnreadable`, `VectorCache`, `cache_path`; calls `VectorCache`, `cache_path`
- [[Reference/Modules/learnloop/local_embeddings/fusion|learnloop.local_embeddings.fusion]] — imports `module`; calls `learned_weights`, `list_key`, `posterior_for`, `rng_seed`, `seed_weights`, `selection_propensity`, `thompson_weights`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `PRICES_PER_MILLION`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `Scope`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `module`; calls `fallback_client`, `fallback_reason`, `fallback_space`, `query_vectors`, `window_vectors`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `LIST_NAMES`, `local_reason`, `local_spaces`; calls `local_reason`, `local_spaces`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `block_record_id`, `split_record_id`; calls `block_record_id`, `split_record_id`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `adopted_encoder`; calls `adopted_encoder`
- [[Reference/Modules/learnloop/source_retrieval/windows|learnloop.source_retrieval.windows]] — imports `expected_keys`, `mean_vector`, `windows_by_extraction`; calls `expected_keys`, `mean_vector`, `windows_by_extraction`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `pathlib`, `time`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]], [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]], [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_a_student_that_misses_the_time_box_is_late_and_the_others_serve`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_the_local_space_reports_no_encoder_in_p1_and_serves_through_the_hook`

## Modification guidance

- Make changes here when the responsibility remains spaces within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/spaces.py](../../../../../../src/learnloop/source_retrieval/spaces.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
