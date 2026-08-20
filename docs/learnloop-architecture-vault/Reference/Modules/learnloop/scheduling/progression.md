---
title: "learnloop.scheduling.progression"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/progression.py"
source_paths:
  - "src/learnloop/scheduling/progression.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.progression module"
  - "src/learnloop/scheduling/progression.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.progression`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.progression` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P1 step 8 -- within-family angle progression, family evidence caps, and post-lapse linked retries (spec_p1_shared_substrate §4.3, §5.4, §5.5; owner decision A.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/progression.py](../../../../../../src/learnloop/scheduling/progression.py) |
| Source lines | 341 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class GrowthActivity` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 56)
  - `as_dict(self) -> dict[str, Any]` (line 65; public)
- `next_growth_activity(repository: Repository, *, family_version_id: str, current_angle: Mapping[str, Any] | None=None, current_context: str | None=None) -> GrowthActivity` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 112) — The §5.4 next growth activity after a success: a delayed orthogonal angle (never a near-clone), stepping the context fade, with strongly-shrunk sibling propagation that only touches the family-stage prior.
- `default_cap_body() -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 161)
- `ensure_default_evidence_cap_policy(repository: Repository, *, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 171)
- `class EvidenceCap` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 182)
  - `as_dict(self) -> dict[str, Any]` (line 189; public)
- `apply_evidence_cap(repository: Repository, *, surface_ids: Sequence[str], cap_policy_id: str | None=None, threshold: float | None=None, stem_columns: Mapping[str, tuple[str, str]] | None=None) -> EvidenceCap` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 199) — Cap independent evidence over a target x capability x angle neighborhood (§4.3).
- `open_lapse_episode(repository: Repository, *, card_lineage_id: str, opened_administration_id: str | None=None, learner_id: str='local', followup_days: int | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 268) — Open a durable lapse on a failed eligible practice administration (§5.5).
- `link_retry(repository: Repository, *, episode_id: str, observation: Mapping[str, Any], derived_retrievability: float | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 292) — Link a same-session retry to an OPEN lapse (§5.5).
- `give_up(repository: Repository, *, episode_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 321) — Close a lapse as ``given_up`` (§5.5).
- `recover(repository: Repository, *, episode_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 333) — Close a lapse as ``recovered`` (the next-day follow-up demonstrated recall).

### Module constants

- `MAX_EFFECTIVE_MASS_PER_CLUSTER` ([src/learnloop/scheduling/progression.py](../../../../../../src/learnloop/scheduling/progression.py), line 39)
- `DIMINISHING_MASS_DECAY` ([src/learnloop/scheduling/progression.py](../../../../../../src/learnloop/scheduling/progression.py), line 43)
- `POST_LAPSE_FOLLOWUP_DAYS` ([src/learnloop/scheduling/progression.py](../../../../../../src/learnloop/scheduling/progression.py), line 46)
- `DEFAULT_CAP_POLICY_SLUG` ([src/learnloop/scheduling/progression.py](../../../../../../src/learnloop/scheduling/progression.py), line 48)

## Internal implementation anchors

- `_next_context(fade: Sequence[str], current: str | None) -> str | None` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 77)
- `_orthogonal_angle(coordinates: Mapping[str, Any], current_angle: Mapping[str, Any]) -> tuple[dict[str, Any], str | None]` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 88) — Advance ONE orthogonal coordinate deterministically (sorted axis order): pick the first axis whose declared values offer something other than the current value, and step to the next distinct value.
- `_plus_days(iso: str, days: int) -> str` ([source](../../../../../../src/learnloop/scheduling/progression.py), line 263)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/familiarity|learnloop.learner.familiarity]] — imports `module`; calls `evidence_cap_grouping`
- [[Reference/Modules/learnloop/scheduling/progression_policy|learnloop.scheduling.progression_policy]] — imports `SIBLING_SUCCESS_SHRINKAGE`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`, `resolve_progression_policy`; calls `canonical_hash`, `canonical_json`, `resolve_progression_policy`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_journey6.py](../../../../../../tests/test_journey6.py) — direct import
  - `test_journey6_end_to_end_on_fresh_mvp08_vault`
- [tests/test_laddered_stems.py](../../../../../../tests/test_laddered_stems.py) — direct import
  - `test_different_stems_are_untouched_by_the_rule`
  - `test_same_column_co_clusters_even_when_the_features_are_cold`
  - `test_two_parts_at_different_capabilities_are_two_independent_groups`
  - `test_two_parts_at_one_capability_are_one_independent_group`
- [tests/test_progression.py](../../../../../../tests/test_progression.py) — direct import
  - `test_additional_administrations_add_diminishing_mass`
  - `test_distant_surfaces_are_separate_groups`
  - `test_evidence_cap_reads_policy_row`
  - `test_give_up_closes_and_preserves_retries`
  - `test_lapse_retry_preserves_original_and_does_not_stack`
  - `test_next_growth_activity_is_delayed_orthogonal_not_near_clone`
  - `test_sibling_propagation_never_marks_reviewed_or_grants_group`
  - `test_tight_cluster_is_one_independent_group`

## Modification guidance

- Change progression policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/progression.py](../../../../../../src/learnloop/scheduling/progression.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
