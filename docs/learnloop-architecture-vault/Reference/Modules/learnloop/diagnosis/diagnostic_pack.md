---
title: "learnloop.diagnosis.diagnostic_pack"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/diagnostic_pack.py"
source_paths:
  - "src/learnloop/diagnosis/diagnostic_pack.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.diagnostic_pack module"
  - "src/learnloop/diagnosis/diagnostic_pack.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.diagnostic_pack`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.diagnostic_pack` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: P2 DIAGNOSTIC track -- the pre-authored diagnostic pack + bounded baseline (spec_p2_narrow_golden_path §5.1, §5.2, §5.3, §12.2; design B.4; migration 083).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/diagnostic_pack.py](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py) |
| Source lines | 535 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class InvalidPack(Exception)` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 36) — A pack card cannot be admitted: it is out of the blueprint's bounds, or a plausible grader/likelihood perturbation would change the recommended repair without a disclosure/abstention path (§5.1).
- `class PackCard` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 43)
  - `as_dict(self) -> dict[str, Any]` (line 49; public)
- `class PackRecord` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 59)
  - `as_dict(self) -> dict[str, Any]` (line 68; public)
- `pack_content_hash(*, pack_slug: str, blueprint_version_id: str, cards: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 92) — The timestamp/id-independent content identity of a pack (§12.8 determinism).
- `assemble_pack(repository: Repository, *, pack_slug: str, blueprint_version_id: str, cards: Sequence[Mapping[str, Any]], clock: Clock | None=None) -> PackRecord` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 122) — Assemble a diagnostic pack from admitted-candidate diagnostic-purpose cards for a reviewed blueprint version (§5.1).
- `admit_pack_card(repository: Repository, *, pack_id: str, card_slug: str, checks: Mapping[str, Any] | None=None, author: str='owner', clock: Clock | None=None) -> PackRecord` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 162) — Owner admits one reviewed card into the pack (U-028).
- `reject_pack_card(repository: Repository, *, pack_id: str, card_slug: str, reason: str, author: str='owner', clock: Clock | None=None) -> PackRecord` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 184)
- `review_pack(repository: Repository, *, pack_id: str, checks: Mapping[str, Any] | None=None, author: str='owner', clock: Clock | None=None) -> PackRecord` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 204) — Owner marks the pack reviewed once every card is admitted (§5.1).
- `activate_pack(repository: Repository, *, pack_id: str, author: str='owner', clock: Clock | None=None) -> PackRecord` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 228)
- `clamp_visible_cap(requested: int | None=None) -> int` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 251)
- `pin_pack_to_run(repository: Repository, *, run_id: str, pack_id: str, goal_contract_version_id: str | None=None, visible_cap: int | None=None, probe_episode_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 258) — Pin exactly one reviewed pack to the run at diagnostic entry (§5.2).
- `enter_baseline(vault: Any, repository: Repository, *, run_id: str, learning_object_id: str, pack_id: str, visible_cap: int | None=None, clock: Clock | None=None, ai_client: object | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 292) — Open one bounded diagnostic episode for the run and pin the pack (§5.2).
- `boundary_view(repository: Repository, *, run_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 457) — Render only the facet x capability cells relevant to the target blueprint (§5.3), projected over the pinned baseline episode's P0/P1 evidence.
- `snapshot_baseline_boundary(repository: Repository, *, run_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 488) — Persist the baseline boundary view as a run artifact at diagnostic-segment close (§5.3 / §8.4).

### Module constants

- `PACK_SPEC_SCHEMA_VERSION` ([src/learnloop/diagnosis/diagnostic_pack.py](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 28)
- `BASELINE_VISIBLE_CAP` ([src/learnloop/diagnosis/diagnostic_pack.py](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 33)
- `BOUNDARY_CELL_STATES` ([src/learnloop/diagnosis/diagnostic_pack.py](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 343)

## Internal implementation anchors

- `_canonical_cards(cards: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 78)
- `_reject_unstable_repair(card: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 107) — §5.1 admission gate: reject a card whose recommended repair is unstable under plausible grader/likelihood perturbations unless it carries a disclosure/abstention path.
- `_recipe_cells(spec: Mapping[str, Any]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 348) — The ordered, de-duplicated (facet, capability) cells of the blueprint's solution recipes (§5.3).
- `_baseline_evidence_projection(repository: Repository, run: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[tuple[str, str], dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 372) — Project the pinned baseline episode's observations onto the recipe cells (§5.3).
- `_load_pack(repository: Repository, pack_id: str, *, minted: bool=True) -> PackRecord` ([source](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py), line 512)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]] — imports `module`; statically calls `boundary_view`
- [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]] — imports `module`; statically calls `snapshot_baseline_boundary`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]] — imports `module`; statically calls `_load_pack`, `admit_pack_card`, `assemble_pack`, `boundary_view`, `enter_baseline`, `review_pack`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/golden_path_assessment|learnloop.curriculum.golden_path_assessment]] — imports `DEMONSTRATED_CLAIM_CERTAINTY`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `module`; calls `enter_episode`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`; calls `canonical_hash`, `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]], [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]], [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnostic_pack.py](../../../../../../tests/test_diagnostic_pack.py) — direct import
  - `test_boundary_view_projects_blueprint_cells_as_untested`
  - `test_cards_enter_candidate_and_review_requires_admission`
  - `test_enter_baseline_composes_probe_episode_and_pins`
  - `test_pack_rejects_unstable_repair_without_disclosure`
  - `test_pack_rejects_wrong_card_count`
  - `test_pin_binds_pack_to_run_and_goal_contract_version`
  - `test_pin_requires_reviewed_pack`
  - `test_visible_cap_is_clamped_into_the_2_to_4_band`
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_event_replay_equivalence_after_full_walk`
  - `test_fault_injection_diagnostic_baseline_boundary_yields_exactly_one`
  - `test_golden_path_ten_step_fixture_journey`
  - `test_starting_instruction_closes_measurement_segment_and_reentry_is_fresh`
- [tests/test_p2_leakage_suite.py](../../../../../../tests/test_p2_leakage_suite.py) — direct import
  - `test_diagnostic_exposure_consumes_cold_eligibility`

## Modification guidance

- Change diagnostic pack policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/diagnostic_pack.py](../../../../../../src/learnloop/diagnosis/diagnostic_pack.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
