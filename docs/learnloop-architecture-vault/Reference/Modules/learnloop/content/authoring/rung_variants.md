---
title: "learnloop.content.authoring.rung_variants"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/rung_variants.py"
source_paths:
  - "src/learnloop/content/authoring/rung_variants.py"
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
  - "learnloop.content.authoring.rung_variants module"
  - "src/learnloop/content/authoring/rung_variants.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.rung_variants`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.rung_variants` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: Learner-initiated re-runging: easier/harder sibling variants of one item.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/rung_variants.py](../../../../../../../src/learnloop/content/authoring/rung_variants.py) |
| Source lines | 885 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class RungVariantError(ValueError)` ([source](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 49)
  - `__init__(self, code: str, message: str)` (line 50; internal)
- `audit_variant_direction(source_item: PracticeItem, payload: dict[str, Any], direction: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 89) — Direction-symmetric structural audit for sibling variants.
- `audit_variant_manipulation_contract(repository: Repository, source_item: PracticeItem, candidate_payload: dict[str, Any], *, adversarial_review: dict[str, Any] | None, generation_agent_run_id: str | None=None, reviewer_agent_run_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 235) — P2 shared diff audit for harder/easier/rung-shift siblings.
- `resolve_item_waypoint(vault: LoadedVault, repository: Repository, item: PracticeItem) -> str` ([source](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 293) — The default-trajectory waypoint this item most plausibly sits at.
- `request_rung_variant(vault: LoadedVault, repository: Repository, *, practice_item_id: str, direction: str, session_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 357) — Record a re-rung request and write its evidence package.
- `generate_rung_variant(root, client: Any, *, request_id: str, repository: Repository | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 560) — Author the requested variant: one grounded sibling item at the target waypoint, rung-gated, with deterministic facet/fingerprint/capability stamping.

### Module constants

- `DIRECTIONS` ([src/learnloop/content/authoring/rung_variants.py](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 55)
- `CLAIM_SOURCE` ([src/learnloop/content/authoring/rung_variants.py](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 57)
- `BEYOND_TRAJECTORY` ([src/learnloop/content/authoring/rung_variants.py](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 62)
- `_ORDERED_TASK_AXES` ([src/learnloop/content/authoring/rung_variants.py](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 64)

## Internal implementation anchors

- `_variant_kind(source_item: PracticeItem, rung: RungTarget, direction: str) -> str` ([source](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 268) — A rung whose demanded point moves against direction is a trajectory shift.
- `_target_rung(vault: LoadedVault, repository: Repository, item: PracticeItem, source_slug: str, direction: str) -> RungTarget` ([source](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 507)
- `_rebuild_rung(repository: Repository, request: dict[str, Any]) -> RungTarget` ([source](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 793)
- `_variant_instructions(plan: Any, source_item: PracticeItem, rung: RungTarget, request: dict[str, Any], extra: str | None) -> str` ([source](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 815)
- `_created_item_row(repository: Repository, patch_id: str) -> tuple[str, str] | None` ([source](../../../../../../../src/learnloop/content/authoring/rung_variants.py), line 876) — (proposal_row_id, practice_item_id) of the created variant, or None.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `RungVariantError`, `generate_rung_variant`; statically calls `generate_rung_variant`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `RungVariantError`, `request_rung_variant`; statically calls `request_rung_variant`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`; calls `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/authoring_gates|learnloop.content.authoring.authoring_gates]] — imports `build_instrument_gates`; calls `build_instrument_gates`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `PracticeExpansionError`, `PracticeExpansionPlan`, `_RungGate`, `build_practice_expansion_plan`; calls `PracticeExpansionPlan`, `_RungGate`, `build_practice_expansion_plan`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `accept_items`, `generate_authoring_proposal`; calls `accept_items`, `generate_authoring_proposal`
- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `RungTarget`, `adjacent_slug`, `rung_float_proxies`, `select_rung`, `trajectory_slugs`, `waypoint_rung`; calls `RungTarget`, `adjacent_slug`, `rung_float_proxies`, `select_rung`, `trajectory_slugs`, `waypoint_rung`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `audit_manipulation_contract`; calls `audit_manipulation_contract`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `default_capability_for`; calls `default_capability_for`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`, `reanchor_mastery_from_claim`; calls `display_mastery`, `reanchor_mastery_from_claim`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `sync_vault_state`; calls `sync_vault_state`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_attribution_p0.py](../../../../../../../tests/test_causal_attribution_p0.py) — direct import
  - `test_variant_direction_audit_is_symmetric`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_rung_variant_failed_result_fails_the_durable_job`

## Modification guidance

- Change rung variants policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/rung_variants.py](../../../../../../../src/learnloop/content/authoring/rung_variants.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
