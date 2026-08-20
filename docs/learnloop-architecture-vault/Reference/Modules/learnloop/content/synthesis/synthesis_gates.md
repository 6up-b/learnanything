---
title: "learnloop.content.synthesis.synthesis_gates"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/synthesis_gates.py"
source_paths:
  - "src/learnloop/content/synthesis/synthesis_gates.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.synthesis_gates module"
  - "src/learnloop/content/synthesis/synthesis_gates.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.synthesis_gates`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.synthesis_gates` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Deterministic synthesis quality gates (source-ingestion §8.7).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py) |
| Source lines | 930 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class GateDiagnostic` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 38)
  - `to_dict(self) -> dict[str, Any]` (line 45; public)
- `class ProvenanceRef` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 56) — A source span backing a proposed entity (§4.2/§8.5).
- `class GateItem` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 70)
  - `is_semantic(self) -> bool` (line 93; public)
  - `is_destructive(self) -> bool` (line 98; public)
  - `refs(self) -> tuple[str, ...]` (line 103; public)
- `class GateProposal` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 108)
- `class GateContext` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 117)
- `class GateReport` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 146)
  - `hard_fails(self) -> list[GateDiagnostic]` (line 150; public)
  - `reviews(self) -> list[GateDiagnostic]` (line 154; public)
  - `blocked(self) -> bool` (line 158; public) — True when any hard_fail is present — the proposal cannot be persisted.
  - `requires_review(self) -> bool` (line 164; public)
  - `gates_fired(self) -> set[str]` (line 167; public)
- `run_synthesis_gates(proposal: GateProposal, ctx: GateContext) -> GateReport` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 171) — Run every §8.7 gate and collect typed diagnostics.

### Module constants

- `SEMANTIC_AUTHORITY_ROLES` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 25)
- `ASSESSMENT_ONLY_ROLES` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 29)
- `_SEMANTIC_ITEM_TYPES` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 31)
- `_TOKEN_RE` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 32)
- `_ADDITIVE_ITEM_TYPES` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 695)
- `_GATES` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 824)

## Internal implementation anchors

- `_gate_span_resolution(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 185)
- `_gate_scope(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 208)
- `_gate_unit_id_validity(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 227)
- `_gate_conflict_disposition(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 252)
- `_gate_lock_guard(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 274)
- `_lock_reason_for(item: GateItem, ctx: GateContext) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 293) — Delegate to can_apply when a vault/repository is wired, else use the item's injected lock_reason.
- `_gate_adequate_provenance(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 313)
- `_has_semantic_authority(item: GateItem) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 335)
- `_gate_criterion_targets_dag(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 346)
- `_gate_recipe_validity(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 397)
- `_gate_dependency_closure(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 485)
- `_gate_exam_authority(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 516)
- `_gate_held_out_leakage(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 539)
- `_gate_token_truncation(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 560)
- `_gate_practice_exam_only(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 583)
- `_gate_duplicate_ids_dangling(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 604)
- `_endpoint_known(endpoint: str, proposal: GateProposal) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 650)
- `_gate_near_duplicate_facets(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 657)
- `_gate_append_vocabulary(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 700) — Append vocabulary gate (§10.2/§10.3).
- `_is_alias_only_facet_append(item: GateItem, ctx: GateContext) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 748) — Is this a D2 alias registration — provably additive, so append-legal?
- `_default_identifiability(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 783) — Degenerate identifiability check (SEAM for KM5's §11.3 doctor).
- `_criteria_of(item: GateItem) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 847)
- `_blueprints_of(item: GateItem) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 857)
- `_facet_tokens(payload: dict[str, Any]) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 864)
- `_facet_signature(payload: dict[str, Any]) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 869)
- `_text_tokens(text: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 877)
- `_jaccard(left: set[str], right: set[str]) -> float` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 881)
- `_first_cycle(graph: dict[str, Iterable[str]]) -> list[str] | None` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 902)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `GateDiagnostic`; statically calls `GateDiagnostic`
- [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]] — imports `facet_tokens`, `jaccard`; statically calls `facet_tokens`, `jaccard`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `GateItem`, `GateProposal`, `ProvenanceRef`, `run_synthesis_gates`; statically calls `GateItem`, `GateProposal`, `run_synthesis_gates`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `GateContext`, `GateDiagnostic`, `GateItem`, `GateProposal`, `ProvenanceRef`, `run_synthesis_gates`; statically calls `GateContext`, `GateDiagnostic`, `GateItem`, `GateProposal`, `ProvenanceRef`, `run_synthesis_gates`
- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `GateDiagnostic`; statically calls `GateDiagnostic`
- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `GateDiagnostic`; statically calls `GateDiagnostic`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `Operation`, `can_apply`; calls `Operation`, `can_apply`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]], [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]], [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_append_vocabulary_gate_rejects_mutation_outside_restructure`
- [tests/test_synthesis_gates.py](../../../../../../../tests/test_synthesis_gates.py) — direct import
  - `test_clean_proposal_passes_all_gates`
  - `test_each_gate_emits_typed_diagnostic`
  - `test_exam_authority_allows_manual_override`
  - `test_report_separates_hard_fail_and_review`

## Modification guidance

- Change synthesis gates policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
