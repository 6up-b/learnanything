---
title: "learnloop.curriculum.commitment_arcs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/commitment_arcs.py"
source_paths:
  - "src/learnloop/curriculum/commitment_arcs.py"
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
  - "learnloop.curriculum.commitment_arcs module"
  - "src/learnloop/curriculum/commitment_arcs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.commitment_arcs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.commitment_arcs` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: P3 slice 3, step 9 -- commitment arcs (spec_p3_reader_integration §10.1/§10.2, design B step 9).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/commitment_arcs.py](../../../../../../src/learnloop/curriculum/commitment_arcs.py) |
| Source lines | 454 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ArcError(ValueError)` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 47) — Domain error for the commitment-arc service.
- `create_arc(repository: Repository, *, commitment_id: str, source_id: str | None=None, stages: Sequence[str] | None=None, pattern_refs: Sequence[str] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 88) — Create an arc bound to a commitment.
- `project_arc(repository: Repository, *, arc_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 143) — Rebuildable arc-state head: a projection over memory time + arc time (§10.1).
- `preview_for_capture(*, action: str, depth_preset: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 202) — The provisional arc shown immediately after a commit (§10.2): the declared stage ladder + the default policy for the action.
- `advance_arc(repository: Repository, *, arc_id: str, stage: str, evidence_receipt: Mapping[str, Any], selected_edge_id: str | None=None, goal_id: str | None=None, proposed_contract_body: Mapping[str, Any] | None=None, fork_edit: Mapping[str, Any] | None=None, live_activation_enabled: bool | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 217) — Record an achieved stage and request EXACTLY ONE P1 automatic transition (§10.1/§10.2).
- `pause_arc(repository: Repository, *, arc_id: str, reason: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 311) — Pause the arc before the next administration: prevents an uncommitted transition and leaves the capture/arc intact (§15.6.1).
- `resume_arc(repository: Repository, *, arc_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 328)
- `set_depth_policy(repository: Repository, *, arc_id: str, policy: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 337) — Change the commitment's depth policy and re-pin the arc to the new policy version (§10.2).
- `shrink_envelope(repository: Repository, *, arc_id: str, bounds: Mapping[str, Any], reviewed_edges: Sequence[Mapping[str, Any]]=(), clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 354) — Shrink (reduce) the active envelope before the next administration.
- `offer_prime(repository: Repository, *, arc_id: str, question_ref: str, section: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 418) — Offer a learner question from section N as an opt-in prime before section N+1 (§10.3).
- `answer_prime(repository: Repository, *, arc_id: str, question_ref: str, gave_up: bool=False, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 438) — Record a prime answer (§10.3): heavily tempered / no cold credit; it may adjust a low-authority prior only, and can never satisfy delayed certification.

### Module constants

- `DEFAULT_STAGES` ([src/learnloop/curriculum/commitment_arcs.py](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 39)
- `ARC_SCHEMA_VERSION` ([src/learnloop/curriculum/commitment_arcs.py](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 44)
- `_ARC_EVENT_KINDS` ([src/learnloop/curriculum/commitment_arcs.py](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 411)

## Internal implementation anchors

- `_reviewed_edges(repository: Repository, envelope_version_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 51)
- `_stage_milestone_map(stages: Sequence[str], reviewed_edges: Sequence[Mapping[str, Any]]) -> dict[str, str]` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 62) — Map each arc stage to the reviewed depth-milestone edge whose ``predecessor_milestone`` names that stage, else fall back to positional order.
- `_resolve_policy(repository: Repository, policy_version_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 136)
- `_repin(repository: Repository, arc_id: str, head: C.CommitmentVersion, *, event: str, detail: Mapping[str, Any], clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/curriculum/commitment_arcs.py), line 378)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]] — imports `module`; statically calls `create_arc`, `preview_for_capture`, `project_arc`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `ArcError`, `answer_prime`, `create_arc`, `offer_prime`, `pause_arc`, `project_arc`, `set_depth_policy`, `shrink_envelope`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `change_depth_envelope`, `change_depth_policy`, `pause`, `record_milestone_reached`, `resolve_disposition`, `resolve_head`, `resume`
- [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]] — imports `module`; calls `commit_one_edge`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`; calls `canonical_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_commitment_arcs.py](../../../../../../tests/test_commitment_arcs.py) — direct import
  - `test_advance_is_idempotent_on_decision_receipt`
  - `test_arc_pins_depth_and_maps_stages`
  - `test_auto_within_envelope_activates_exactly_one_edge_and_prior_stays_reached`
  - `test_hold_and_suggest_never_auto_activate`
  - `test_material_fork_has_no_fsrs_or_certification_inheritance`
  - `test_pause_before_next_administration_prevents_transition`
  - `test_prime_is_salience_only_no_cold_credit`
  - `test_project_arc_rebuilds_deterministically`
  - `test_shrink_envelope_allowed_widen_requires_confirmed_successor`
  - `test_shrink_envelope_allows_genuine_contraction`
  - `test_shrink_envelope_rejects_widening`
- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — direct import
  - `test_arc_and_salience_heads_rebuild_deterministically`
  - `test_journey1_reading_first_session`

## Modification guidance

- Change commitment arcs policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/commitment_arcs.py](../../../../../../src/learnloop/curriculum/commitment_arcs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
