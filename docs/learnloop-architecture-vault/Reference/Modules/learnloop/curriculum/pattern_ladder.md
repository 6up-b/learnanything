---
title: "learnloop.curriculum.pattern_ladder"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/pattern_ladder.py"
source_paths:
  - "src/learnloop/curriculum/pattern_ladder.py"
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
  - "learnloop.curriculum.pattern_ladder module"
  - "src/learnloop/curriculum/pattern_ladder.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.pattern_ladder`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.pattern_ladder` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: P2 LEARNING track -- the nine-rung pattern ladder (7 ordinals) + stage transitions (spec_p2_narrow_golden_path §7.1, §7.2, §12.3; design B.6; migration 084).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/pattern_ladder.py](../../../../../../src/learnloop/curriculum/pattern_ladder.py) |
| Source lines | 510 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class LadderError(Exception)` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 60) — A ladder action references an unknown run / stage.
- `class LadderStage` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 65)
  - `as_dict(self) -> dict[str, Any]` (line 75; public)
- `active_ladder(repository: Repository, *, policy_slug: str='ladder_v1') -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 140) — The reviewable ladder policy + its ordered stage rows (migration 084 DATA).
- `select_rung(*, triage: Mapping[str, Any] | None=None, reason: str | None=None, demonstrated_capability: bool=False) -> LadderStage | None` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 154) — Pick the nearest useful rung from the diagnostic route (§7.1).
- `stage_evidence_effects(stage_key: str, *, eligible: bool=True, failed: bool=False) -> AA.AdministrationEffects` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 183) — Resolve the P1 administration adapter for a rung's IMMUTABLE purpose and return its evidence effects (§7.2).
- `class LadderAdvance` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 314)
  - `as_dict(self) -> dict[str, Any]` (line 325; public)
- `enter_ladder(repository: Repository, run_id: str, *, triage: Mapping[str, Any] | None=None, reason: str | None=None, demonstrated_capability: bool=False, idempotency_key: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 339) — Record the ladder ENTRY rung on the run's event stream (§7.1).
- `advance_stage(repository: Repository, run_id: str, *, from_stage: str, outcome: str, surface_id: str | None=None, scaffold_use: float | None=None, eligible: bool=True, evidence_ids: list[str] | None=None, idempotency_key: str | None=None, clock: Clock | None=None) -> LadderAdvance` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 367) — Apply the §7.2 exit contract for a rung.
- `ladder_status(repository: Repository, run_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 477) — The current ladder rung + climb history projected from the run event stream (§12.6 -- reproducible from events alone).

### Module constants

- `LADDER_POLICY_SCHEMA_VERSION` ([src/learnloop/curriculum/pattern_ladder.py](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 42)
- `REPEATED_FAILURE_REVIEW_N` ([src/learnloop/curriculum/pattern_ladder.py](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 47)
- `STAGE_DELAY_DAYS` ([src/learnloop/curriculum/pattern_ladder.py](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 52)
- `COMPLETION_SCAFFOLD_THRESHOLD` ([src/learnloop/curriculum/pattern_ladder.py](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 57)
- `LADDER_STAGES` ([src/learnloop/curriculum/pattern_ladder.py](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 91)
- `STAGE_BY_KEY` ([src/learnloop/curriculum/pattern_ladder.py](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 102)
- `_REPRESENTATIVE_BY_ORDINAL` ([src/learnloop/curriculum/pattern_ladder.py](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 106)
- `_REASON_ENTRY_RUNG` ([src/learnloop/curriculum/pattern_ladder.py](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 113)
- `_FAIL_OUTCOMES` ([src/learnloop/curriculum/pattern_ladder.py](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 126)

## Internal implementation anchors

- `_next_stage(stage: LadderStage) -> LadderStage | None` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 129) — The next rung on the forward climb (the representative at ordinal+1), or None when the ladder is complete (the run is then ready to assess).
- `_current_rung_key(events: list[Mapping[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 200)
- `_failed_surfaces(events: list[Mapping[str, Any]], *, stage: str | None=None) -> set[str]` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 213) — Distinct failed surfaces, filtered to ONE rung when ``stage`` is given (§7.2).
- `_record_rung(repository: Repository, run_id: str, stage: LadderStage, *, reason: str, idempotency_key: str, outcome: str | None=None, surface_id: str | None=None, scaffold_use: float | None=None, evidence_ids: list[str] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/pattern_ladder.py), line 239) — Record a rung on the run's event stream (design B.6).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]] — imports `module`; statically calls `active_ladder`, `advance_stage`, `enter_ladder`, `ladder_status`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]] — imports `module`; calls `_existing_event`, `advance`, `project_run`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_json`; calls `canonical_json`
- [[Reference/Modules/learnloop/substrate/administration_adapters|learnloop.substrate.administration_adapters]] — imports `module`; calls `resolve_adapter`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_capable_planted_learner_skips_instruction`
  - `test_event_replay_equivalence_after_full_walk`
  - `test_golden_path_ten_step_fixture_journey`
  - `test_misconception_planted_learner_takes_signature_route_and_repair_rung`
  - `test_planted_profiles_route_to_distinct_rungs`
- [tests/test_pattern_ladder.py](../../../../../../tests/test_pattern_ladder.py) — direct import
  - `test_capable_learner_skips_unnecessary_instruction`
  - `test_completion_records_scaffold_use`
  - `test_completion_scaffold_threshold_and_stage_delay_are_wired`
  - `test_entry_stage_is_set_by_the_triage_route`
  - `test_fault_and_ambiguous_reasons_open_no_rung`
  - `test_instructional_stages_mint_no_certification_and_no_lapse`
  - `test_kill_resume_mid_ladder_rebuilds_position_from_events`
  - `test_ladder_policy_data_matches_code_authority`
  - `test_ladder_walks_each_stage_to_ready_to_assess`
  - `test_method_selection_repair_uses_setup_not_procedure_repetition`
  - `test_one_fail_per_rung_while_climbing_never_triggers_review`
  - `test_practice_rung_is_practice_weighted_but_still_not_certifying`
  - `test_repeated_failure_counts_distinct_surfaces_only`
  - `test_repeated_varied_failures_terminate_into_needs_review`
  - `test_select_rung_maps_each_reason_to_nearest_useful_rung`

## Modification guidance

- Change pattern ladder policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/pattern_ladder.py](../../../../../../src/learnloop/curriculum/pattern_ladder.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
