---
title: "learnloop.content.authoring.authoring_gates"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/authoring_gates.py"
source_paths:
  - "src/learnloop/content/authoring/authoring_gates.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.authoring_gates module"
  - "src/learnloop/content/authoring/authoring_gates.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.authoring_gates`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.authoring_gates` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: One instrument-quality gate chain for every practice-item authoring lane.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/authoring_gates.py](../../../../../../../src/learnloop/content/authoring/authoring_gates.py) |
| Source lines | 435 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `selected_response_reasons(payload: dict[str, Any]) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 63) — Every reason this payload reads as a selected-response surface.
- `class SelectedResponseGate` ([source](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 85) — Deterministic ban on selected-response surfaces (multiple choice / T-F).
  - `__init__(self) -> None` (line 95; internal)
  - `__call__(self, rows: list[dict[str, Any]]) -> None` (line 98; internal)
- `chain_gates(*gates: RowGate) -> RowGate` ([source](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 117) — Run several row_transform gates over one proposal batch, in order.
- `remediate_instrument_gate_failures(rows: list[dict[str, Any]], *, persona_gate: PersonaGate) -> None` ([source](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 237) — Mechanically repair the two remediable gate failures, then re-judge.
- `class InstrumentGateChain` ([source](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 311) — The composed Stage-5.3/6 instrument gates, with named handles.
  - `__call__(self, rows: list[dict[str, Any]]) -> None` (line 325; internal)
  - `diagnostics(self) -> list[dict[str, Any]]` (line 335; public) — Gate outcomes in the synthesis lanes' ``gate_diagnostics`` shape.
- `build_instrument_gates(vault: Any, repository: Any | None=None, *, grading_client: Any=None, rung_gate: Any | None=None, difficulty_band_by_lo: dict[str, tuple[float, float]] | None=None, leading: Sequence[RowGate]=()) -> InstrumentGateChain` ([source](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 394) — The standard composition: leading → surface → rung → persona → pair.

### Module constants

- `SELECTED_RESPONSE_PATTERNS` ([src/learnloop/content/authoring/authoring_gates.py](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 52)
- `GATE_REMEDIATION_AUDIT_KEY` ([src/learnloop/content/authoring/authoring_gates.py](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 139)
- `_REMEDIABLE_SURFACE_ERROR` ([src/learnloop/content/authoring/authoring_gates.py](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 142)
- `_REMEDIABLE_DETECTOR_ERROR` ([src/learnloop/content/authoring/authoring_gates.py](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 143)
- `_REMEDIABLE_ATOMIC_ERROR` ([src/learnloop/content/authoring/authoring_gates.py](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 145)
- `_OPTION_LINE` ([src/learnloop/content/authoring/authoring_gates.py](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 147)
- `_OPTION_ANSWER_PREFIX` ([src/learnloop/content/authoring/authoring_gates.py](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 148)
- `_INSTRUCTION_LINE_PATTERNS` ([src/learnloop/content/authoring/authoring_gates.py](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 149)

## Internal implementation anchors

- `_strip_selected_response_surface(payload: dict[str, Any]) -> list[str] | None` ([source](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 152) — Remove the selected-response surface from ``payload`` in place.
- `_drop_unkeyed_misconception(payload: dict[str, Any]) -> list[str] | None` ([source](../../../../../../../src/learnloop/content/authoring/authoring_gates.py), line 218) — Drop a speculative diagnostic claim, demoting the item to plain practice.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `SELECTED_RESPONSE_PATTERNS`, `SelectedResponseGate`, `build_instrument_gates`, `chain_gates`; statically calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `build_instrument_gates`; statically calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `build_instrument_gates`; statically calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `selected_response_reasons`; statically calls `selected_response_reasons`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `build_instrument_gates`; statically calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `build_instrument_gates`; statically calls `build_instrument_gates`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `build_instrument_gates`; statically calls `build_instrument_gates`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `BANNED_RESPONSE_MODES`, `LOW_MASTERY_RESPONSE_MODES`
- [[Reference/Modules/learnloop/content/authoring/persona_gate|learnloop.content.authoring.persona_gate]] — imports `GateDecision`, `PersonaGate`, `_keyed_misconception_ids`; calls `PersonaGate`, `_keyed_misconception_ids`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `ContrastPairGate`; calls `ContrastPairGate`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]], [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]], [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]], [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_authoring_contract.py](../../../../../../../tests/test_authoring_contract.py) — direct import
  - `test_banned_practice_mode_is_a_violation_even_with_a_clean_prompt`
  - `test_generation_door_remediates_the_incident_payload`
  - `test_refresh_door_passes_the_remediated_payload`
  - `test_remediation_bails_when_the_stem_is_the_surface`

## Modification guidance

- Change authoring gates policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/authoring_gates.py](../../../../../../../src/learnloop/content/authoring/authoring_gates.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
