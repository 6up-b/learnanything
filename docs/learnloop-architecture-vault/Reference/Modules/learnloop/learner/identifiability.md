---
title: "learnloop.learner.identifiability"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/identifiability.py"
source_paths:
  - "src/learnloop/learner/identifiability.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.identifiability module"
  - "src/learnloop/learner/identifiability.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.identifiability`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.identifiability` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Assessment identifiability doctor (knowledge-model §11.3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/identifiability.py](../../../../../../src/learnloop/learner/identifiability.py) |
| Source lines | 1065 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ProposalView` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 42) — Normalized identifiability inputs extracted from a proposal or registry.
- `class IdentifiabilityFinding` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 67) — A structured non-identifiability finding routed to the gate + gen-needs.
  - `as_dict(self) -> dict[str, Any]` (line 79; public)
- `declared_facets(view: ProposalView) -> set[str]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 154) — Every facet this neighborhood declares — the standing measurement obligations.
- `class MeasurementRank` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 179) — §D1's published ratio: resolvable dimensions vs facets declared.
  - `rank_ratio(self) -> float | None` (line 199; public) — ``measurement_rank / facets_declared`` (§5.8.2 reports 14/39 = 0.36).
  - `as_dict(self) -> dict[str, Any]` (line 206; public)
- `measurement_rank(view: ProposalView) -> MeasurementRank` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 221) — Count independent measurement dimensions against facets declared (§D1).
- `analyze_identifiability(view: ProposalView) -> list[IdentifiabilityFinding]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 287)
- `build_proposal_view(*, facets: list[dict[str, Any]], criterion_targets: list[dict[str, Any]], recipe_components: list[dict[str, Any]], recipes: list[dict[str, Any]] | None=None, planted_profiles: list[dict[str, Any]] | None=None, criterion_fingerprints: dict[str, str] | None=None) -> ProposalView` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 648) — Build the normalized identifiability view from synthesis proposal parts.
- `build_registry_view(vault: 'LoadedVault', subject_id: str | None=None, *, misconception_records: list[Any] | None=None) -> ProposalView` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 686) — Build the identifiability view from a subject's persisted registry (§11.3).
- `calculate_registry_hash(view: ProposalView) -> str` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 871) — A stable hash of the identifiability-relevant registry neighborhood.
- `load_misconception_records(vault: 'LoadedVault', repository: Any, scoped_los: set[str]) -> list[Any]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 916)
- `graph_identifiability_report(vault: 'LoadedVault', repository: Any, *, subject_id: str | None=None, schedule_probes: bool=False, clock: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 950) — Run the §11.3 doctor over each subject's registry neighborhood.
- `schedule_discriminating_probes(repository: Any, subject_id: str, findings: list[IdentifiabilityFinding], *, clock: Any=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 1037) — Persist a discriminating probe / coarsen need per finding (§11.3).

## Internal implementation anchors

- `_criteria_by_facet(view: ProposalView) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 92) — facet id -> set of observation signatures (correlation group or criterion id).
- `_measurement_signatures(view: ProposalView) -> dict[str, frozenset[str]]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 137) — facet id -> the set of observation units that can see it (§D1).
- `_primary_anchor_pairs(view: ProposalView) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 257) — (facet, capability) pairs that at least one criterion PRIMARILY observes.
- `_anchor_groups(view: ProposalView) -> dict[tuple[str, str], set[str]]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 271) — (facet, capability) -> correlation groups that PRIMARILY observe it.
- `_check_planted_profiles(view: ProposalView, seen_pairs: set[tuple[str, ...]]) -> list[IdentifiabilityFinding]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 413) — Check 3 — different planted profiles with equivalent ideal outcomes.
- `_recipe_observable_signatures(view: ProposalView) -> dict[str, dict[str, frozenset[str]]]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 461) — blueprint_id -> {recipe_id -> frozenset of discriminating criterion signatures}.
- `_check_alternative_recipes(view: ProposalView, seen_pairs: set[tuple[str, ...]]) -> list[IdentifiabilityFinding]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 492) — Check 5 — alternative recipes grading cannot distinguish.
- `_check_component_vs_integration(view: ProposalView, seen_pairs: set[tuple[str, ...]]) -> list[IdentifiabilityFinding]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 534) — Check 6 — component weakness vs integration weakness, identical signatures.
- `_check_single_representation(view: ProposalView, seen_pairs: set[tuple[str, ...]]) -> list[IdentifiabilityFinding]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 598) — Check 7 — all evidence from one representation / source example / testlet.
- `_item_fingerprint(item: Any) -> str | None` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 815) — A representation/source/testlet signature for check 7 (§6 fingerprint).
- `_planted_profiles_from_registry(vault: 'LoadedVault', subject_id: str | None, scoped_los: set[str], *, misconception_records: list[Any] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 830) — Compositional misconception records as planted profiles for check 3.
- `_bundle_findings(findings: list[IdentifiabilityFinding]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 930) — Group findings into unresolved bundles (never false facet-specific precision).
- `_count_by_check(findings: list[IdentifiabilityFinding]) -> dict[str, int]` ([source](../../../../../../src/learnloop/learner/identifiability.py), line 1029)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `graph_identifiability_report`; statically calls `graph_identifiability_report`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `analyze_identifiability`, `build_proposal_view`; statically calls `analyze_identifiability`, `build_proposal_view`
- [[Reference/Modules/learnloop/curriculum/subject_registry|learnloop.curriculum.subject_registry]] — imports `build_registry_view`, `measurement_rank`; statically calls `build_registry_view`, `measurement_rank`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `IdentifiabilityFinding`, `analyze_identifiability`, `build_registry_view`, `load_misconception_records`; statically calls `analyze_identifiability`, `build_registry_view`, `load_misconception_records`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `build_registry_view`, `measurement_rank`; statically calls `build_registry_view`, `measurement_rank`
- [[Reference/Modules/learnloop/learner/residual_diagnostics|learnloop.learner.residual_diagnostics]] — imports `analyze_identifiability`, `build_registry_view`; statically calls `analyze_identifiability`, `build_registry_view`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `analyze_identifiability`, `build_registry_view`, `calculate_registry_hash`, `schedule_discriminating_probes`; statically calls `analyze_identifiability`, `build_registry_view`, `calculate_registry_hash`, `schedule_discriminating_probes`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `graph_identifiability_report`; statically calls `graph_identifiability_report`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `analyze_identifiability`, `build_registry_view`; statically calls `analyze_identifiability`, `build_registry_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `recipe_components`; calls `recipe_components`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]], [[Reference/Modules/learnloop/curriculum/subject_registry|learnloop.curriculum.subject_registry]], [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]], [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contrast_pairs.py](../../../../../../tests/test_contrast_pairs.py) — direct import
  - `test_commissioning_turns_identifiability_findings_into_requests`
- [tests/test_identifiability_doctor.py](../../../../../../tests/test_identifiability_doctor.py) — direct import
  - `test_graph_identifiability_report_and_probe_scheduling`
  - `test_registry_view_flags_missing_anchor`
  - `test_seven_identifiability_warnings`
- [tests/test_measurement_rank.py](../../../../../../tests/test_measurement_rank.py) — direct import
  - `test_as_dict_publishes_the_rank_and_the_deficit`
  - `test_computing_the_rank_triggers_no_merge`
  - `test_criteria_and_items_are_distinct_observation_units`
  - `test_declared_facets_covers_every_standing_obligation`
  - `test_empty_view_abstains_rather_than_dividing_by_zero`
  - `test_graph_identifiability_report_publishes_the_rank`
  - `test_item_pool_observations_are_measurement_dimensions`
  - `test_partial_overlap_is_still_two_dimensions`
  - `test_rank_does_not_disturb_the_seven_checks`
  - `test_rank_equals_dimensions_when_signatures_are_distinct`
  - `test_rank_on_the_real_linear_algebra_fixture`
  - `test_registry_view_rank_counts_items_and_criteria`
  - `test_two_facets_sharing_an_observing_signature_are_one_dimension`
  - `test_unobserved_facet_contributes_no_dimension_and_the_deficit_is_split`
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
  - `test_measurement_rank_is_composed_from_identifiability`
  - `test_measurement_rank_is_unavailable_with_no_declared_facet`
- [tests/test_synthesis_identifiability.py](../../../../../../tests/test_synthesis_identifiability.py) — direct import
  - `test_capability_confounding_within_a_facet`
  - `test_duplicate_signature_distinct_repairs_generates_discriminator`
  - `test_duplicate_signature_identical_repairs_coarsens`
  - `test_identifiable_proposal_has_no_findings`
  - `test_missing_anchor_for_required_facet_capability`

## Modification guidance

- Change identifiability policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/identifiability.py](../../../../../../src/learnloop/learner/identifiability.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
