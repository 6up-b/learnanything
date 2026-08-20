---
title: "learnloop.content.synthesis.facet_mint_gate"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/facet_mint_gate.py"
source_paths:
  - "src/learnloop/content/synthesis/facet_mint_gate.py"
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
  - "learnloop.content.synthesis.facet_mint_gate module"
  - "src/learnloop/content/synthesis/facet_mint_gate.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.facet_mint_gate`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.facet_mint_gate` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: D2: gate facet minting at ingest (plan item 5.4).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/facet_mint_gate.py](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py) |
| Source lines | 550 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class MintDisposition(StrEnum)` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 94) — What to do with one candidate facet.
- `class MintReason(StrEnum)` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 115) — Typed reason per disposition — closed, never a free-text rationale.
- `class NeighbourKind(StrEnum)` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 136) — How a pair came to be compared.
- `class Neighbour` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 163) — One nominated comparison, with why it was nominated and how close it is.
  - `as_dict(self) -> dict[str, Any]` (line 171; public)
- `class MintVerdict` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 181) — One candidate facet, judged under D2, with the evidence it was judged on.
  - `mints(self) -> bool` (line 203; public)
  - `as_dict(self) -> dict[str, Any]` (line 206; public)
- `class MintGateReport` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 221)
  - `minted(self) -> tuple[MintVerdict, ...]` (line 225; public)
  - `aliased(self) -> tuple[MintVerdict, ...]` (line 229; public)
  - `abstained(self) -> tuple[MintVerdict, ...]` (line 233; public)
  - `aliases(self) -> dict[str, list[str]]` (line 236; public) — target facet id -> candidate ids registered as its aliases.
  - `counts(self) -> dict[str, int]` (line 245; public)
  - `reason_counts(self) -> dict[str, int]` (line 251; public)
  - `summary(self) -> dict[str, Any]` (line 257; public)
  - `as_dict(self) -> dict[str, Any]` (line 265; public)
- `separable(candidate: Mapping[str, Any], neighbour: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 298) — D2 criterion 1: does some authorable item make the holders diverge?
- `distinct_repair(candidate: Mapping[str, Any], neighbour: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 309) — D2 criterion 2: does the candidate prescribe something the neighbour does not?
- `is_testable(candidate: Mapping[str, Any], neighbour: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 315) — Both criteria need both fields on both sides.
- `judge_facet_mints(candidates: Sequence[Mapping[str, Any]], *, registered: Sequence[Mapping[str, Any]]=(), near_duplicate_threshold: float=DEFAULT_NEAR_DUPLICATE_THRESHOLD) -> MintGateReport` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 386) — Judge every candidate facet under D2.
- `mint_diagnostic(verdict: MintVerdict) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 505) — The §8.7-shaped review diagnostic for one non-clean verdict, or ``None``.

### Module constants

- `DEFAULT_NEAR_DUPLICATE_THRESHOLD` ([src/learnloop/content/synthesis/facet_mint_gate.py](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 91)
- `_KIND_RANK` ([src/learnloop/content/synthesis/facet_mint_gate.py](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 155)
- `MINT_GATE` ([src/learnloop/content/synthesis/facet_mint_gate.py](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 502)

## Internal implementation anchors

- `_signatures(payload: Mapping[str, Any]) -> frozenset[str]` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 276) — The candidate's planted-persona answers, normalized (§3.0's harness).
- `_repairs(payload: Mapping[str, Any]) -> frozenset[str]` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 286)
- `_claim(payload: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 294)
- `_neighbours(candidate: Mapping[str, Any], pool: Sequence[tuple[str, Mapping[str, Any], bool]], *, near_duplicate_threshold: float) -> tuple[Neighbour, ...]` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 334) — Nominate every facet worth comparing ``candidate`` against, nearest first.
- `_judge_one(candidate: Mapping[str, Any], pool: Sequence[tuple[str, Mapping[str, Any], bool]], *, near_duplicate_threshold: float) -> MintVerdict` ([source](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py), line 421)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `MintDisposition`, `judge_facet_mints`; statically calls `judge_facet_mints`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `MintDisposition`, `judge_facet_mints`, `mint_diagnostic`; statically calls `judge_facet_mints`, `mint_diagnostic`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `judge_facet_mints`; statically calls `judge_facet_mints`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `facet_tokens`, `jaccard`; calls `facet_tokens`, `jaccard`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `normalize_answer`; calls `normalize_answer`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `enum`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_mint_gate.py](../../../../../../../tests/test_facet_mint_gate.py) — direct import
  - `test_a_candidate_with_no_neighbour_mints_unconditionally`
  - `test_a_non_separable_candidate_becomes_an_alias_not_a_mint`
  - `test_a_separable_candidate_with_a_distinct_repair_is_minted`
  - `test_aliases_never_chain_because_candidates_are_judged_in_order`
  - `test_counts_and_summary_cover_the_closed_vocabularies`
  - `test_distinct_repair_and_testability_are_independent_criteria`
  - `test_every_typed_reason_is_reachable`
  - `test_ingest_aliases_a_collapsing_candidate_into_a_registered_facet`
  - `test_same_repair_class_aliases_even_when_signatures_differ`
  - `test_separability_is_symmetric_so_a_subset_facet_is_a_collapse`
  - `test_untestable_candidate_abstains_and_is_not_born_reviewed`

## Modification guidance

- Change facet mint gate policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/facet_mint_gate.py](../../../../../../../src/learnloop/content/synthesis/facet_mint_gate.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
