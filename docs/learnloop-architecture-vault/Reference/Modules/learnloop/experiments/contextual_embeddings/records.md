---
title: "learnloop.experiments.contextual_embeddings.records"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/records.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/records.py"
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
  - "learnloop.experiments.contextual_embeddings.records module"
  - "src/learnloop/experiments/contextual_embeddings/records.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.records`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.records` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: E0's experiment-owned repository: receipts and verdicts (spec §4.3, §6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/records.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/records.py) |
| Source lines | 109 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ExperimentRecords` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/records.py), line 36) — One copy's writable experiment repository (under fixtures-local only).
  - `__init__(self, root: Path) -> None` (line 39; internal)
  - `receipts(self, owner_id: str) -> Iterator[None]` (line 55; public) — Observe every model call in this context into this repository.
  - `judgment(self, *, task: str, left_id: str, right_kind: str | None, right_id: str | None, verdict: str, score: float | None, details: Mapping[str, Any], call: Any) -> str` (line 63; public)
  - `judgments(self, task: str | None=None) -> list[dict[str, Any]]` (line 82; public)
  - `completed_outputs(self, prompt: Any) -> list[str]` (line 91; public) — The output texts of this repository's COMPLETED receipts whose input is exactly ``prompt`` (by text or prompt hash), newest first: what a resume can recover a settled response from (fix round 4, Medium 11).
  - `receipt_count(self) -> int` (line 106; public)

### Module constants

- `OWNER_KIND` ([src/learnloop/experiments/contextual_embeddings/records.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/records.py), line 33)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `ExperimentRecords`; statically calls `ExperimentRecords`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `ExperimentRecords`; statically calls `ExperimentRecords`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `ExperimentRecords`; statically calls `ExperimentRecords`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `record_model_calls`; calls `content_key`, `record_model_calls`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `_inside_local_root`; calls `_inside_local_root`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `init_vault`, `load_vault`; calls `init_vault`, `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `hashlib`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f10_verdicts_enter_judgment_ledger_once`
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_m11_a_settled_response_is_recovered_from_the_receipts`

## Modification guidance

- Make changes here when the responsibility remains records within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/records.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/records.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
