---
title: "learnloop.experiments.contextual_embeddings.e1.plan"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/e1/plan.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/e1/plan.py"
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
  - "learnloop.experiments.contextual_embeddings.e1.plan module"
  - "src/learnloop/experiments/contextual_embeddings/e1/plan.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings-e1"
---

# `learnloop.experiments.contextual_embeddings.e1.plan`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.e1.plan` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] to own the behavior summarized by its module contract: The E1 plan: inputs, the GPU-hours and dollar estimates, the plan id.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/e1/plan.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py) |
| Source lines | 310 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `manifest_inputs(e0_run_dir: Path) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 43) — Counts from E0's frozen manifests (read-only; no vault, no store).
- `import_inputs(layout: Any, replays: Sequence[Any]) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 91) — Counts from a verified import's replays (exact documents and queries).
- `e0_novelty(replayed: Any) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 129) — How often one of E0's contextual arms ranked, in its top 10, a unit no other replayed arm put in its top 20 (nor the writer's proposals): the expected new-candidate rate of one more contextual arm.
- `gpu_estimate(vaults: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 158)
- `money_estimate(vaults: Mapping[str, Mapping[str, Any]], gaps: Mapping[str, Mapping[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 180) — Expected and worst-case dollars: the supplementary labels and audits, the two model canaries, and any voyage-context-4 fill.
- `build_plan(inputs: Mapping[str, Any], *, keys: Mapping[str, str], prior: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 241)
- `render_markdown(plan: Mapping[str, Any]) -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 293)

### Module constants

- `_FRAME_TOKENS` ([src/learnloop/experiments/contextual_embeddings/e1/plan.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 29)
- `_QUESTION_TOKENS` ([src/learnloop/experiments/contextual_embeddings/e1/plan.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 31)
- `_CANDIDATE_OVERHEAD` ([src/learnloop/experiments/contextual_embeddings/e1/plan.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 33)
- `_SONNET` ([src/learnloop/experiments/contextual_embeddings/e1/plan.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 34)
- `_OPUS` ([src/learnloop/experiments/contextual_embeddings/e1/plan.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 35)
- `_VOYAGE` ([src/learnloop/experiments/contextual_embeddings/e1/plan.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 36)
- `NOVELTY_ARMS` ([src/learnloop/experiments/contextual_embeddings/e1/plan.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 126)

## Internal implementation anchors

- `_sha(value: Any) -> str` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 39)
- `_e0_block(state: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 80)
- `_call_usd(pin: Any, tokens_in: float, tokens_out: float) -> float` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py), line 175)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]] — imports `render_markdown`; statically calls `render_markdown`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `build_plan`, `import_inputs`, `manifest_inputs`, `module`; statically calls `_call_usd`, `build_plan`, `import_inputs`, `manifest_inputs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `unit_refs`; calls `unit_refs`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/ledger|learnloop.experiments.contextual_embeddings.e1.ledger]] — imports `budget_check`; calls `budget_check`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]] — imports `v2_documents`, `v2_space`; calls `v2_documents`, `v2_space`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/pins|learnloop.experiments.contextual_embeddings.e1.pins]] — imports `module`; calls `e1_pins_fingerprint`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `e0_run_state`, `question_texts`; calls `e0_run_state`, `question_texts`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`; calls `pins_fingerprint`, `token_estimate`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `math`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_e1_harness.py](../../../../../../../../tests/test_e1_harness.py) — imports consumer [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]]

## Modification guidance

- Make changes here when the responsibility remains plan within learnloop.experiments.contextual_embeddings.e1; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/e1/plan.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/plan.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
