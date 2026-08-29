---
title: "learnloop.learner.facet_state_reader"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/facet_state_reader.py"
source_paths:
  - "src/learnloop/learner/facet_state_reader.py"
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
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.learner.facet_state_reader module"
  - "src/learnloop/learner/facet_state_reader.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.facet_state_reader`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.facet_state_reader` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: KM2b consumer re-key: canonical shared facet state read adapter (§7.1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/facet_state_reader.py](../../../../../../src/learnloop/learner/facet_state_reader.py) |
| Source lines | 301 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `is_canonical_state_vault(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 47) — True when this vault reads/writes canonical (mvp-0.7 or mvp-0.8) facet state.
- `resolve_canonical_facet(vault: LoadedVault, merge_map: dict[str, str], facet_id: str) -> str` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 57) — Resolve a facet id to its terminal canonical survivor (§7.1).
- `class CanonicalFacetStateReader` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 147) — Serves legacy-shaped per-LO facet states from canonical mvp-0.7 rows.
  - `__init__(self, vault: LoadedVault, repository: Repository) -> None` (line 155; internal)
  - `_resolve(self, facet_id: str) -> str` (line 180; internal)
  - `states_for_lo(self, learning_object_id: str) -> list[FacetRecallState]` (line 188; public)
  - `state_for_facet(self, learning_object_id: str, facet_id: str, practice_item_id: str | None=None) -> FacetRecallState | None` (line 216; public)
- `facet_states_by_lo(vault: LoadedVault, repository: Repository) -> dict[str, list[FacetRecallState]]` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 242) — ``{learning_object_id: [FacetRecallState, ...]}`` for every LO in the vault.
- `facet_recall_states_for_lo(vault: LoadedVault, repository: Repository, learning_object_id: str, *, reader: CanonicalFacetStateReader | None=None) -> list[FacetRecallState]` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 253)
- `facet_recall_state_for_lo(vault: LoadedVault, repository: Repository, learning_object_id: str, facet_id: str, practice_item_id: str | None=None, *, reader: CanonicalFacetStateReader | None=None) -> FacetRecallState | None` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 266)
- `facet_uncertainty_states_for_lo(vault: LoadedVault, repository: Repository, learning_object_id: str, *, statuses: tuple[str, ...] | None=None) -> list[FacetUncertaintyState]` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 281) — Per-LO facet uncertainty states (KM §7.1).

## Internal implementation anchors

- `_max_iso(a: str | None, b: str | None) -> str | None` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 75)
- `_min_iso(a: str | None, b: str | None) -> str | None` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 83)
- `_capability_scope(rows: Iterable[CanonicalFacetRecallState]) -> str` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 91)
- `_fold(rows: list[CanonicalFacetRecallState], *, learning_object_id: str, facet_id: str, practice_item_id: str | None) -> FacetRecallState` ([source](../../../../../../src/learnloop/learner/facet_state_reader.py), line 96) — Fold capability-sliced canonical rows into one legacy-shaped state.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `CanonicalFacetStateReader`, `is_canonical_state_vault`; statically calls `CanonicalFacetStateReader`, `is_canonical_state_vault`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `is_canonical_state_vault`; statically calls `is_canonical_state_vault`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `facet_recall_states_for_lo`; statically calls `facet_recall_states_for_lo`
- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `is_canonical_state_vault`, `resolve_canonical_facet`; statically calls `is_canonical_state_vault`, `resolve_canonical_facet`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `facet_recall_state_for_lo`, `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`; statically calls `facet_recall_state_for_lo`, `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `is_canonical_state_vault`; statically calls `is_canonical_state_vault`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `is_canonical_state_vault`; statically calls `is_canonical_state_vault`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `facet_recall_states_for_lo`; statically calls `facet_recall_states_for_lo`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `is_canonical_state_vault`; statically calls `is_canonical_state_vault`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `facet_states_by_lo`, `facet_uncertainty_states_for_lo`, `is_canonical_state_vault`; statically calls `facet_states_by_lo`, `facet_uncertainty_states_for_lo`, `is_canonical_state_vault`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `facet_recall_states_for_lo`, `is_canonical_state_vault`; statically calls `facet_recall_states_for_lo`, `is_canonical_state_vault`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`, `is_canonical_state_vault`; statically calls `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`, `is_canonical_state_vault`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `is_canonical_state_vault`, `resolve_canonical_facet`; statically calls `is_canonical_state_vault`, `resolve_canonical_facet`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `facet_recall_state_for_lo`; statically calls `facet_recall_state_for_lo`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `facet_recall_state_for_lo`; statically calls `facet_recall_state_for_lo`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `facet_states_by_lo`; statically calls `facet_states_by_lo`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `is_canonical_state_vault`; statically calls `is_canonical_state_vault`
- [[Reference/Modules/learnloop/tutor/question_signal|learnloop.tutor.question_signal]] — imports `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`; statically calls `facet_recall_states_for_lo`, `facet_uncertainty_states_for_lo`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `CanonicalFacetStateReader`, `facet_recall_states_for_lo`, `is_canonical_state_vault`, `resolve_canonical_facet`; statically calls `CanonicalFacetStateReader`, `facet_recall_states_for_lo`, `is_canonical_state_vault`, `resolve_canonical_facet`
- [[Reference/Modules/learnloop_sidecar/handlers/facets|learnloop_sidecar.handlers.facets]] — imports `is_canonical_state_vault`; statically calls `is_canonical_state_vault`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `is_canonical_state_vault`; statically calls `is_canonical_state_vault`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `CanonicalFacetRecallState`, `FacetRecallState`, `FacetUncertaintyState`, `Repository`; calls `FacetRecallState`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] and 16 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_km2b_consumer_rekey.py](../../../../../../tests/test_km2b_consumer_rekey.py) — direct import
  - `test_exam_attempt_moves_shared_parent_across_los`
  - `test_two_los_share_one_facet_parent_in_scheduler_view`

## Modification guidance

- Change facet state reader policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/facet_state_reader.py](../../../../../../src/learnloop/learner/facet_state_reader.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
