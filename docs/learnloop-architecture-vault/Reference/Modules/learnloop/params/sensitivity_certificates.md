---
title: "learnloop.params.sensitivity_certificates"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/params/sensitivity_certificates.py"
source_paths:
  - "src/learnloop/params/sensitivity_certificates.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.params"
layer: "domain"
concepts:
  - "Learning System"
  - "Configuration"
workflows:
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.params.sensitivity_certificates module"
  - "src/learnloop/params/sensitivity_certificates.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-params"
---

# `learnloop.params.sensitivity_certificates`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/params/_package|learnloop.params]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.params.sensitivity_certificates` exists within [[Reference/Modules/learnloop/params/_package|learnloop.params]] to own the behavior summarized by its module contract: P0.5 sensitivity certificates + promotion evidence (spec §6, U-022 v2, design §3).

The authoritative system-level explanation remains in [[Learning System]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/params/sensitivity_certificates.py](../../../../../../src/learnloop/params/sensitivity_certificates.py) |
| Source lines | 394 |
| Owning package | [[Reference/Modules/learnloop/params/_package|learnloop.params]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class Certificate` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 41)
  - `as_entry(self) -> dict[str, Any]` (line 52; public)
- `certificate_from_sweep_report(*, path: str, covered_value: Any, plausible_range: Mapping[str, Any], scenario: Mapping[str, Any], sweep_report: Any) -> Certificate` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 66) — Derive a certificate from a ``SweepReport``.
- `certify(*, path: str, covered_value: Any, low: float, high: float, vault_root: Path, profile: Any, work_dir: Path, scenario: Mapping[str, Any] | None=None, grid_points: int=5, days: int=12, items_per_day: int=4, seed: int=42) -> Certificate` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 108) — Run a fine value-grid sweep across ``[low, high]`` on the fixed scenario and build a certificate.
- `store_certificate(repository: Repository, certificate: Certificate, *, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 152)
- `class CoverageLinkOutcome` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 167) — Result of :func:`link_coverage_certificate`.
  - `__bool__(self) -> bool` (line 175; internal)
- `link_coverage_certificate(repository: Repository, certificate: Certificate, *, clock: Clock | None=None) -> CoverageLinkOutcome` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 179) — Link a stored COVERAGE certificate to its registry entry, satisfying the audit's coverage obligation for an ``active`` decision parameter (rule (a)).
- `class PromotionEvidence` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 213) — Sim-derived evidence that gates ``heuristic -> simulation_validated``.
  - `as_entry(self) -> dict[str, Any]` (line 234; public)
- `promotion_evidence_from_sweep_report(*, path: str, covered_value: Any, plausible_range: Mapping[str, Any], scenario: Mapping[str, Any], sweep_report: Any) -> PromotionEvidence` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 253) — Derive sim promotion evidence from a ``SweepReport`` (same flip-point rule as a coverage certificate; here the ``decision_stable`` verdict is the normative gate :func:`promote` enforces).
- `promotion_evidence_from_certificate(certificate: Certificate, *, source: str='sim') -> PromotionEvidence` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 275) — Wrap a coverage certificate as promotion evidence (U-022 v2: promotion evidence MAY wrap a coverage certificate).
- `store_promotion_evidence(repository: Repository, evidence: PromotionEvidence, *, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 295)
- `class PromotionOutcome` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 306) — Result of :func:`promote`.
  - `__bool__(self) -> bool` (line 313; internal)
- `promote(repository: Repository, evidence: PromotionEvidence, *, clock: Clock | None=None) -> PromotionOutcome` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 317) — Consume PROMOTION EVIDENCE and, when it covers the entry's current effective value AND proves the decision stable across the plausible range, promote status to ``simulation_validated`` (never further -- §6; ``live_calibrated`` still requires an activated real-outcome evidence ma…
- `class DeletionCandidateReport` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 361)
  - `as_dict(self) -> dict[str, Any]` (line 365; public)
- `classify_inert_parameters(paths_stable: Mapping[str, bool]) -> DeletionCandidateReport` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 372) — Class-asymmetric disposition of sweep-proven-inert parameters (§6/design §3).

## Internal implementation anchors

- `_value_grid(low: float, high: float, points: int, covered: Any) -> list[Any]` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 97)
- `_loads(value: str) -> Any` ([source](../../../../../../src/learnloop/params/sensitivity_certificates.py), line 354)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/registry|learnloop.cli.registry]] — imports `module`; statically calls `certify`, `link_coverage_certificate`, `promote`, `promotion_evidence_from_certificate`, `store_certificate`
- [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]] — imports `module`; statically calls `promote`, `promotion_evidence_from_sweep_report`
- [[Reference/Modules/learnloop/scheduling/shadow_components|learnloop.scheduling.shadow_components]] — imports `module`; statically calls `PromotionEvidence`, `store_promotion_evidence`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `REGISTRY`, `module`; calls `set_promotion_evidence_id`
- [[Reference/Modules/learnloop/sim/sweep|learnloop.sim.sweep]] — imports `SweepEntry`, `run_sweep`; calls `SweepEntry`, `run_sweep`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`; calls `canonical_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/registry|learnloop.cli.registry]], [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]], [[Reference/Modules/learnloop/scheduling/shadow_components|learnloop.scheduling.shadow_components]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_sensitivity_certificates.py](../../../../../../tests/test_sensitivity_certificates.py) — direct import
  - `test_certificate_is_stable_when_no_decision_flips`
  - `test_certificate_records_flip_points`
  - `test_coverage_certificate_with_flip_points_is_valid_coverage`
  - `test_inert_classification_is_class_asymmetric`
  - `test_link_coverage_certificate_never_changes_status`
  - `test_promote_refuses_decision_unstable_evidence`
  - `test_promote_requires_covering_evidence`
  - `test_stale_coverage_certificate_does_not_link`

## Modification guidance

- Make changes here when the responsibility remains sensitivity certificates within learnloop.params; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/params/sensitivity_certificates.py](../../../../../../src/learnloop/params/sensitivity_certificates.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
