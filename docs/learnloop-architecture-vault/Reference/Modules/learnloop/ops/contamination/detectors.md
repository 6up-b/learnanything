---
title: "learnloop.ops.contamination.detectors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/contamination/detectors.py"
source_paths:
  - "src/learnloop/ops/contamination/detectors.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops.contamination"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.contamination.detectors module"
  - "src/learnloop/ops/contamination/detectors.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops-contamination"
---

# `learnloop.ops.contamination.detectors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.contamination.detectors` exists within [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] to own the behavior summarized by its module contract: Shadow contamination candidates: the lexical floor, the symbolic check and stored vectors.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/contamination/detectors.py](../../../../../../../src/learnloop/ops/contamination/detectors.py) |
| Source lines | 570 |
| Owning package | [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Candidate` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 69)
  - `task(self) -> str` (line 88; public)
  - `question(self) -> tuple[str, str, str, str, str]` (line 92; public)
  - `note_embedding(self, *, query: str, score: float, rank: int) -> None` (line 95; public)
  - `signals(self) -> dict[str, Any]` (line 99; public)
- `class DetectorScan` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 114)
- `class StoredVectors` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 125) — Read-only vectors of one model and prefix.
  - `__init__(self, loaded: LoadedVault, sqlite_path: Path)` (line 128; internal)
  - `close(self) -> None` (line 145; public)
  - `manifest(self, recipe: str) -> dict[str, str]` (line 150; public)
  - `stored(self, recipe: str, manifest: Mapping[str, str]) -> set[str]` (line 154; public) — Record ids whose CURRENT content hash has a vector for this model.
  - `vector(self, recipe: str, record_id: str, content_hash: str | None) -> np.ndarray | None` (line 167; public)
  - `index(self, recipe: str) -> VectorIndex` (line 177; public)
- `class VectorIndex` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 193)
  - `usable(self) -> bool` (line 201; public)
  - `ranked(self, query: np.ndarray, *, candidate_ids: Collection[str] | None=None) -> list[EmbeddingMatch]` (line 204; public) — Mean-centred cosine over the complete current index, best first.
  - `describe(self) -> dict[str, Any]` (line 218; public)
- `top_k_with_ties(matches: list[EmbeddingMatch], k: int) -> list[tuple[int, EmbeddingMatch]]` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 223) — The best ``k`` by competition rank (1, 2, 2, 4): a tie at the boundary stays whole.
- `scan_exam_leakage(loaded: LoadedVault, repository: Repository, vectors: StoredVectors, *, top_k: int) -> DetectorScan` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 259)
- `scan_tutor_answer_leak(loaded: LoadedVault, repository: Repository, vectors: StoredVectors, *, top_k: int) -> DetectorScan` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 345)
- `scan_reader_reveal(loaded: LoadedVault, repository: Repository, vectors: StoredVectors, *, top_k: int) -> DetectorScan` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 484)

### Module constants

- `DETECTORS` ([src/learnloop/ops/contamination/detectors.py](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 60)
- `TASK_FOR_DETECTOR` ([src/learnloop/ops/contamination/detectors.py](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 61)
- `POSITIVE_VERDICT` ([src/learnloop/ops/contamination/detectors.py](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 62)
- `GENERATED_ORIGINS` ([src/learnloop/ops/contamination/detectors.py](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 64)
- `TASK_PREFIX` ([src/learnloop/ops/contamination/detectors.py](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 65)
- `SCANNERS` ([src/learnloop/ops/contamination/detectors.py](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 566)

## Internal implementation anchors

- `_embedding_block(index: VectorIndex, queries: Iterable[str], with_vectors: int, without: int) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 238)
- `_excerpt_rubric(item: PracticeItem) -> list[str]` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 254)
- `_next_attempt(repository: Repository, item_id: str, after: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 335)
- `_when(value: Any) -> datetime | None` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 415)
- `class _Reserve` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 426) — One surface and every assessment reservation it has held.
- `_surface_prompt(surface: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 461) — The reserve's own question text, without its expected answer.
- `_reserves(repository: Repository) -> dict[str, _Reserve]` ([source](../../../../../../../src/learnloop/ops/contamination/detectors.py), line 469)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/contamination|learnloop.cli.contamination]] — imports `DETECTORS`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `Candidate`, `POSITIVE_VERDICT`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `Candidate`, `DETECTORS`, `DetectorScan`, `POSITIVE_VERDICT`, `SCANNERS`, `StoredVectors`; statically calls `StoredVectors`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AUTO_PRIME_REVEAL_THRESHOLD`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `held_out_spans`, `inventory_for_texts`, `screen_practice_payload`; calls `held_out_spans`, `inventory_for_texts`, `screen_practice_payload`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `EmbeddingMatch`, `get_vector`, `retrieve`; calls `get_vector`, `retrieve`
- [[Reference/Modules/learnloop/ops/contamination/recipes|learnloop.ops.contamination.recipes]] — imports `CONTAMINATION_RECIPES`, `answered_question_events`, `assessment_reservations`, `expected_answer_text`; calls `answered_question_events`, `assessment_reservations`, `expected_answer_text`
- [[Reference/Modules/learnloop/ops/contamination/symbolic|learnloop.ops.contamination.symbolic]] — imports `SymbolicResult`, `symbolic_check`; calls `symbolic_check`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `lexical_reserve_reveal`, `surface_statement_text`; calls `lexical_reserve_reveal`, `surface_statement_text`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `evaluate_held_out_eligibility`; calls `evaluate_held_out_eligibility`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `answer_leak_overlap`; calls `answer_leak_overlap`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `pathlib`, `sqlite3`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/contamination|learnloop.cli.contamination]], [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]], [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_contamination`

## Modification guidance

- Make changes here when the responsibility remains detectors within learnloop.ops.contamination; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/contamination/detectors.py](../../../../../../../src/learnloop/ops/contamination/detectors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
