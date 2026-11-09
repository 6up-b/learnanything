---
title: "learnloop.content.facet_identity.plan"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/facet_identity/plan.py"
source_paths:
  - "src/learnloop/content/facet_identity/plan.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.facet_identity"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.facet_identity.plan module"
  - "src/learnloop/content/facet_identity/plan.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-facet-identity"
---

# `learnloop.content.facet_identity.plan`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.facet_identity.plan` exists within [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] to own the behavior summarized by its module contract: The facet-identity plan of one synthesis or append run.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/facet_identity/plan.py](../../../../../../../src/learnloop/content/facet_identity/plan.py) |
| Source lines | 468 |
| Owning package | [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Retirement` ([source](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 52) — One candidate that is not minted, and where it goes.
- `class FacetIdentityPlan` ([source](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 70)
  - `in_run(self) -> dict[str, Retirement]` (line 80; public)
  - `attach(self) -> dict[str, Retirement]` (line 83; public)
  - `as_dict(self) -> dict[str, Any]` (line 86; public)
  - `from_dict(cls, data: Mapping[str, Any] | None) -> FacetIdentityPlan | None` (line 95; public)
  - `summary(self) -> dict[str, Any]` (line 110; public)
- `candidate_subject_id(payload: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 129) — A candidate's ledger subject: its content, so reruns ask the same question.
- `build_plan(synth: Any, *, vault: Any, repository: Any, run_id: str, nominator: Any=None, judge_client: Any=None, cancelled: Callable[[], bool] | None=None, attach_enabled: bool=True) -> FacetIdentityPlan | None` ([source](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 169) — Decide the run's facet identities.
- `ingest_dry_run(vault: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 429) — The facet-identity judge's part of a synthesis/append dry run (review F5).

### Module constants

- `PLAN_VERSION` ([src/learnloop/content/facet_identity/plan.py](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 46)
- `CANDIDATE_KIND` ([src/learnloop/content/facet_identity/plan.py](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 47)
- `FACET_KIND` ([src/learnloop/content/facet_identity/plan.py](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 48)

### Explicit exports

`__all__` declares:

- `CANDIDATE_KIND`
- `FACET_KIND`
- `FacetIdentityPlan`
- `PLAN_VERSION`
- `Retirement`
- `build_plan`
- `candidate_subject_id`
- `ingest_dry_run`

## Internal implementation anchors

- `_d(obj: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 123)
- `_concepts(synth: Any, vault: Any) -> tuple[dict[str, str], list[tuple[str, str]]]` ([source](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 138) — Concept titles (client and registry ids) and concept-graph edges.
- `_candidate_nodes(synth: Any) -> list[tuple[str, dict[str, Any], str | None]]` ([source](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 155)
- `_attach_requests(plan: FacetIdentityPlan, candidates: Sequence[tuple[str, dict[str, Any], str | None]], registered: Mapping[str, Any], *, titles: Mapping[str, str], nominator: Any, queries: Mapping[str, Any], settings: Any, member: Callable[..., Member], payload_by_client: Mapping[str, Mapping[str, Any]], registry_concept_of: Mapping[str, str] | None=None) -> list[Any]` ([source](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 317) — Groups of surviving candidates with the registered facets nominated for them.
- `_resolve_chains(plan: FacetIdentityPlan) -> None` ([source](../../../../../../../src/learnloop/content/facet_identity/plan.py), line 410) — A survivor that is itself retired forwards its retirees (never a cycle).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `ingest_dry_run`; statically calls `ingest_dry_run`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `FacetIdentityPlan`, `build_plan`, `ingest_dry_run`; statically calls `FacetIdentityPlan`, `build_plan`, `ingest_dry_run`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/content/facet_identity/grouping|learnloop.content.facet_identity.grouping]] — imports `FacetNode`, `neighbourhood_groups`; calls `FacetNode`, `neighbourhood_groups`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `GroupOutcome`, `Member`, `build_judge`, `build_request`, `caps_from_config`, `resolve_route`; calls `Member`, `build_judge`, `build_request`, `caps_from_config`, `resolve_route`
- [[Reference/Modules/learnloop/content/facet_identity/views|learnloop.content.facet_identity.views]] — imports `judge_view`, `union_payload`; calls `judge_view`, `union_payload`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `FACET_RECIPE`, `facet_query`; calls `facet_query`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `facet_tokens`, `jaccard`; calls `facet_tokens`, `jaccard`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_authority.py](../../../../../../../tests/test_facet_authority.py) — direct import
- [tests/test_facet_identity.py](../../../../../../../tests/test_facet_identity.py) — direct import
  - `test_an_undone_in_run_merge_stays_apart_when_the_run_is_planned_again`
  - `test_in_run_consolidation_of_the_regression_set`
  - `test_the_plan_is_off_with_the_kill_switch`
- [tests/test_facet_identity_composition.py](../../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_the_ledger_records_merged_pairs_and_shortlisted_different_pairs_only`
- [tests/test_facet_identity_ingest.py](../../../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_two_sets_on_one_in_run_survivor_are_one_action_that_undoes_both`

## Modification guidance

- Change plan policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/facet_identity/plan.py](../../../../../../../src/learnloop/content/facet_identity/plan.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
