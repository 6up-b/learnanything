---
title: "learnloop.experiments.contextual_embeddings.stop_rules"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/stop_rules.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/stop_rules.py"
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
  - "learnloop.experiments.contextual_embeddings.stop_rules module"
  - "src/learnloop/experiments/contextual_embeddings/stop_rules.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.stop_rules`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.stop_rules` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: E0's stop rules S1-S4 (spec §7), computed from the results by code.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/stop_rules.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/stop_rules.py) |
| Source lines | 190 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `s1(*, kappa: float | None, unresolved_sets: int, extraction_failures: int, policy_failures: int, arm_completion: Mapping[str, float], incomplete_work: Mapping[str, int] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/stop_rules.py), line 17) — Labels and coverage: stop verdicts for kappa < 0.60, unresolved evidence sets, extraction/policy failures, materially incomplete arms, or planned work left undone (``incomplete_work``: seeds the writer never answered, questions never labelled, mandatory audits or planned answers…
- `s2(direct: Mapping[str, Mapping[str, Any] | None], *, latency_fits: Mapping[str, bool | None]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/stop_rules.py), line 53) — Direct reading for known-location tasks: D2/D3 minus D1 answer pass.
- `s3(*, context_gain: Mapping[str, Mapping[str, Any] | None], qwen_vs_hosted: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/stop_rules.py), line 86) — Cheap context: per hosted family, grouped minus singleton Complete Evidence@10; and the best Qwen contextual recipe minus the best hosted arm.
- `s4(*, finalist_vs_one_model: Mapping[str, Any] | None, answer_gain: Mapping[str, Any] | None, latency_ok: bool | None, independent_families: int, exploratory: bool=False) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/stop_rules.py), line 121) — Local experiment gate: the hosted finalist beats the best one-model arm by >= 5 points Complete Evidence@10 with a paired CI excluding 0, improves blind D1 answers, and no Reader latency regression.
- `decide(*, s1_inputs: Mapping[str, Any], s2_inputs: Mapping[str, Any], s3_inputs: Mapping[str, Any], s4_inputs: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/stop_rules.py), line 157) — All four rules.
- `incomplete_rules() -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/stop_rules.py), line 173) — The rules for a run with no results yet (a dry run or a budget stop).
- `summarize_decisions(decisions: Mapping[str, Any]) -> list[str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/stop_rules.py), line 180)

### Explicit exports

`__all__` declares:

- `decide`
- `incomplete_rules`
- `s1`
- `s2`
- `s3`
- `s4`
- `summarize_decisions`

## Internal implementation anchors

- `_lower(result: Mapping[str, Any] | None) -> float | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/stop_rules.py), line 47)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `incomplete_rules`; statically calls `incomplete_rules`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `decide`; statically calls `decide`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/report|learnloop.experiments.contextual_embeddings.report]] — imports `incomplete_rules`, `summarize_decisions`; statically calls `incomplete_rules`, `summarize_decisions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/report|learnloop.experiments.contextual_embeddings.report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_metrics_stop_rules.py](../../../../../../../tests/test_e0_metrics_stop_rules.py) — direct import
  - `test_an_unpinned_reader_latency_budget_fails_closed`
  - `test_s1_stops_verdicts_and_blocks_the_rest`
  - `test_s2_superior_noninferior_and_inconclusive`
  - `test_s3_context_gain_and_qwen_within_two_points`
  - `test_s4_needs_five_points_ci_answers_latency_and_power`
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_m14_s4_counts_only_the_paired_evidence_families_and_honours_exploratory`

## Modification guidance

- Make changes here when the responsibility remains stop rules within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/stop_rules.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/stop_rules.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
