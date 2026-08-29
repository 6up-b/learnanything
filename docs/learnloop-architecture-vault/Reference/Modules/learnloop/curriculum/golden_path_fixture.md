---
title: "learnloop.curriculum.golden_path_fixture"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/golden_path_fixture.py"
source_paths:
  - "src/learnloop/curriculum/golden_path_fixture.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.golden_path_fixture module"
  - "src/learnloop/curriculum/golden_path_fixture.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.golden_path_fixture`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.golden_path_fixture` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: P2 -- deterministic golden-path fixture bootstrap (spec_p2_narrow_golden_path §C, §12.7, §12.8).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py) |
| Source lines | 427 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `stub_blueprint(*, family_key: str=FAMILY_KEY, source_rev: str=SOURCE_REV, unit_id: str=UNIT_ID, exemplar_refs: tuple[str, ...]=(EXEMPLAR_A, EXEMPLAR_B), held_out_ref: str=HELD_OUT) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 61) — Deterministic TaskBlueprintVersion spec (§3.2 shape).
- `stub_depth_edge() -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 118) — One reviewed inside-envelope depth edge (§7.5).
- `stub_diagnostic_pack() -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 137) — Deterministic diagnostic-pack stub (§5.1, §C).
- `stub_pool_surfaces() -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 151) — Deterministic practice-pool stub (§7.3, U-028, §C).
- `class GoldenPathFixture` ([source](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 165)
  - `content_hashes(self) -> dict[str, str]` (line 176; public) — The timestamp/id-independent content identity of the fixture (§12.8).
  - `as_dict(self) -> dict[str, Any]` (line 184; public)
- `build_golden_path_fixture(root: Path, *, clock: Clock | None=None) -> GoldenPathFixture` ([source](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 342) — Deterministically build the P2 golden-path fixture vault and confirm the run.

### Module constants

- `FIX_NOW` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 38)
- `FIX_NOW_ISO` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 39)
- `ALGORITHM_VERSION` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 40)
- `SUBJECT_ID` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 42)
- `SUBJECT_TITLE` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 43)
- `SOURCE_REV` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 44)
- `UNIT_ID` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 45)
- `FAMILY_KEY` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 46)
- `GOAL_ID` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 47)
- `BLUEPRINT_SLUG` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 48)
- `CONCEPT_ID` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 49)
- `LO_ID` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 50)
- `EXEMPLAR_A` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 52)
- `EXEMPLAR_B` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 53)
- `HELD_OUT` ([src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 54)

## Internal implementation anchors

- `_practice_item(item_id: str, prompt: str, *, now_iso: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 196)
- `_seed_vault(root: Path, *, clock: Clock, now_iso: str) -> VaultPaths` ([source](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 232)
- `_pin_algorithm_version(root: Path, version: str) -> None` ([source](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 328)
- `_vault_item(vault: Any, item_id: str) -> Any` ([source](../../../../../../src/learnloop/curriculum/golden_path_fixture.py), line 423)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/goldenpath|learnloop.cli.goldenpath]] — imports `build_golden_path_fixture`; statically calls `build_golden_path_fixture`

### Repository tooling consumers

- [scripts/gen_goldenpath_fixtures.py](../../../../../../scripts/gen_goldenpath_fixtures.py); calls `build_golden_path_fixture`, `stub_depth_edge`, `stub_diagnostic_pack`, `stub_pool_surfaces`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `utc_now_iso`; calls `FrozenClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/golden_path_confirm|learnloop.curriculum.golden_path_confirm]] — imports `module`; calls `confirm_exemplar_and_start`
- [[Reference/Modules/learnloop/curriculum/task_blueprints|learnloop.curriculum.task_blueprints]] — imports `module`; calls `place_reading_question`, `register_blueprint_version`, `review_blueprint_version`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `resolve_legacy_item`; calls `resolve_legacy_item`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `add_subject`, `init_vault`, `load_vault`; calls `add_subject`, `init_vault`, `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `write_yaml`; calls `write_yaml`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/goldenpath|learnloop.cli.goldenpath]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
- [tests/test_diagnostic_pack.py](../../../../../../tests/test_diagnostic_pack.py) — direct import
  - `test_enter_baseline_composes_probe_episode_and_pins`
  - `test_pack_uses_only_stub_cards_within_2_to_4`
- [tests/test_failure_triage.py](../../../../../../tests/test_failure_triage.py) — direct import
  - `test_high_confidence_signature_takes_intended_route`
- [tests/test_failure_triage_causal_gate.py](../../../../../../tests/test_failure_triage_causal_gate.py) — direct import
  - `test_triage_records_tier_one_basis_on_the_result_and_the_event`
- [tests/test_golden_path_fixture.py](../../../../../../tests/test_golden_path_fixture.py) — direct import
  - `test_fixture_blueprint_is_active_after_confirmation`
  - `test_fixture_bootstrap_confirms_a_certifying_run`
  - `test_fixture_is_deterministic_across_two_builds`
  - `test_fixture_vault_is_mvp_0_8`
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_event_replay_equivalence_after_full_walk`
  - `test_fault_injection_diagnostic_baseline_boundary_yields_exactly_one`
  - `test_golden_path_ten_step_fixture_journey`
  - `test_misconception_planted_learner_takes_signature_route_and_repair_rung`
  - `test_starting_instruction_closes_measurement_segment_and_reentry_is_fresh`
- [tests/test_p2_leakage_suite.py](../../../../../../tests/test_p2_leakage_suite.py) — direct import
  - `test_diagnostic_exposure_consumes_cold_eligibility`
- [tests/test_pattern_ladder.py](../../../../../../tests/test_pattern_ladder.py) — direct import
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — direct import
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_golden_path_completes_with_reader_never_invoked`
- [tests/test_surface_pool.py](../../../../../../tests/test_surface_pool.py) — direct import
  - `test_assessment_reserved_surface_is_refused_at_admission`
  - `test_current_plus_spare_cache_is_bounded`
  - `test_pool_assembly_deterministic`
  - `test_practice_exposure_invalidates_same_fingerprint_assessment_reserve`
  - `test_purpose_specific_family_cannot_transition_roles`
  - `test_surfaces_enter_candidate_and_review_requires_admission`

## Modification guidance

- Change golden path fixture policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/golden_path_fixture.py](../../../../../../src/learnloop/curriculum/golden_path_fixture.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
