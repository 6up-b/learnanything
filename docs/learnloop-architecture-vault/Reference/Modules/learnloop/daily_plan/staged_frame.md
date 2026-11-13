---
title: "learnloop.daily_plan.staged_frame"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/staged_frame.py"
source_paths:
  - "src/learnloop/daily_plan/staged_frame.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.staged_frame module"
  - "src/learnloop/daily_plan/staged_frame.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.staged_frame`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.staged_frame` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router R2a: the staged frame on Today (``staged_frame_v1``) and its chooser (``staged_v1``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/staged_frame.py](../../../../../../src/learnloop/daily_plan/staged_frame.py) |
| Source lines | 482 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `reason_code(lane: str, items: Sequence[PoolItem], *, reading: bool=False, path_label: str | None=None) -> str` ([source](../../../../../../src/learnloop/daily_plan/staged_frame.py), line 111) — The plain-"why" code of a block (:data:`learnloop.router.why.SENTENCES`).
- `class FrameMaterial` ([source](../../../../../../src/learnloop/daily_plan/staged_frame.py), line 154) — What the constraint engine and the ladder read, for the items evaluated so far.
- `class StagedFrame` ([source](../../../../../../src/learnloop/daily_plan/staged_frame.py), line 174) — The frame's material for one plan env (one RPC): built at the first boundary from one bounded snapshot over the pool, rebuilt over the union only when a later pool holds an item it has not evaluated (a follow-up that appeared mid-plan).
  - `__init__(self, vault: Any, repository: Any, *, clock: Any=None, item_states: Any=None) -> None` (line 181; internal) — ``item_states``: a reader of the item states the frame's constraints read in place of the repository's (adaptive difficulty passes its material view's, fix round 12); None reads the repository, as the plan does.
  - `material(self, pool: Iterable[PoolItem]) -> FrameMaterial` (line 194; public)
  - `_cold_items(self) -> frozenset[str]` (line 204; internal) — Items an open cold follow-up holds (``instructional.policy.cold_administration_open``'s rule).
  - `_block(self, item: PoolItem, role: str) -> Any` (line 216; internal)
  - `_build(self, pool: Sequence[PoolItem]) -> FrameMaterial` (line 227; internal) — Mandatory feasibility first (``frame_constraints.evaluate_mandatory``, the evaluation the "Check once" gate shares: R2a review F2's fail-closed rules), then the annotations (open cold checks, the ladder), each read on its own.
  - `_ladder(self, snapshot: Any, pool: Sequence[PoolItem], reserved_items: frozenset[str]) -> dict[str, dict[str, Any]]` (line 275; internal) — Each LO's eligible P4 rungs from per-LO signals (annotation only, Q1).
- `class StagedFrameSource` ([source](../../../../../../src/learnloop/daily_plan/staged_frame.py), line 335) — ``staged_frame_v1``: DL1's packing over the staged-feasible pool, annotated.
  - `candidates(self, state: PlanState) -> list[BlockCandidate]` (line 345; public)
  - `_annotate(self, candidate: BlockCandidate) -> dict[str, Any]` (line 348; internal)
  - `decision_record(self) -> dict[str, Any]` (line 376; public)
- `class StagedFrameFactory` ([source](../../../../../../src/learnloop/daily_plan/staged_frame.py), line 390) — ``PlanPolicy.make_source`` for the staged frame: one :class:`StagedFrame` per env.
  - `__call__(self, context: Any) -> StagedFrameSource` (line 395; internal)
- `class StagedChooser` ([source](../../../../../../src/learnloop/daily_plan/staged_frame.py), line 421) — ``staged_v1``: lane_quota_v1 over the staged-feasible candidates (Q1), deterministic, with the plain "why" and the stored learner-state card.
  - `choose(self, state: PlanState, feasible: Sequence[BlockCandidate]) -> BlockChoice` (line 428; public)

### Module constants

- `_LOG` ([src/learnloop/daily_plan/staged_frame.py](../../../../../../src/learnloop/daily_plan/staged_frame.py), line 88)
- `SOURCE_NAME` ([src/learnloop/daily_plan/staged_frame.py](../../../../../../src/learnloop/daily_plan/staged_frame.py), line 90)
- `CHOOSER_NAME` ([src/learnloop/daily_plan/staged_frame.py](../../../../../../src/learnloop/daily_plan/staged_frame.py), line 91)
- `MODE` ([src/learnloop/daily_plan/staged_frame.py](../../../../../../src/learnloop/daily_plan/staged_frame.py), line 92)
- `_FALL_THROUGH_RULES` ([src/learnloop/daily_plan/staged_frame.py](../../../../../../src/learnloop/daily_plan/staged_frame.py), line 108)

### Explicit exports

`__all__` declares:

- `CHOOSER_NAME`
- `FRESH_EVIDENCE_CHECKS`
- `FRESH_EVIDENCE_MODES`
- `FrameMaterial`
- `MODE`
- `SOURCE_NAME`
- `StagedChooser`
- `StagedFrame`
- `StagedFrameFactory`
- `StagedFrameSource`
- `item_role`
- `reason_code`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `StagedChooser`; statically calls `StagedChooser`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `SOURCE_NAME`, `StagedChooser`, `StagedFrame`, `StagedFrameFactory`; statically calls `StagedChooser`, `StagedFrame`, `StagedFrameFactory`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `CardBuilder`, `StagedChooser`; statically calls `StagedChooser`
- [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]] — imports `StagedFrame`; statically calls `StagedFrame`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/daily_plan/chooser|learnloop.daily_plan.chooser]] — imports `LaneQuotaChooser`; calls `LaneQuotaChooser`
- [[Reference/Modules/learnloop/daily_plan/lanes|learnloop.daily_plan.lanes]] — imports `ASSUMED_CHECK_REASON`, `GAP_COMMITMENT_CHECK_REASON`, `GAP_SOONER_CHECK_REASON`, `LegacyLanesSource`, `PoolItem`; calls `LegacyLanesSource`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BLOCK_MAX_MINUTES`, `BlockCandidate`, `BlockChoice`, `LANE_ACTIONS`, `PlanState`, `STOP_OFFER_MINUTES`; calls `BlockChoice`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `ignored_opening_episode_ids`; calls `ignored_opening_episode_ids`
- [[Reference/Modules/learnloop/router/why|learnloop.router.why]] — imports `module`; calls `sentence`, `stop_code`, `topic_phrase`
- [[Reference/Modules/learnloop/scheduling/controller_actions|learnloop.scheduling.controller_actions]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/frame_constraints|learnloop.scheduling.frame_constraints]] — imports `CONSTRAINTS_UNAVAILABLE_KEY`, `FRESH_EVIDENCE_CHECKS`, `FRESH_EVIDENCE_MODES`, `ROLE_FRESH_EVIDENCE`, `ROLE_PRACTICE`, `attention_block`, `evaluate_mandatory`, `item_role`; calls `attention_block`, `evaluate_mandatory`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; calls `StateSignals`, `ladder_eligibility`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]], [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]], [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — direct import
  - `test_support_respects_constraints_reversibility_and_admission`
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_the_staged_pick_inside_the_objective_is_the_same_with_preferences_on_record`
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_the_why_names_the_path_and_stays_plain`
- [tests/test_router_g1_feasibility.py](../../../../../../tests/test_router_g1_feasibility.py) — direct import
  - `test_an_annotation_failure_keeps_every_refusal`
- [tests/test_router_why_copy.py](../../../../../../tests/test_router_why_copy.py) — direct import
  - `test_reason_codes_follow_the_lane_and_its_items`

## Modification guidance

- Make changes here when the responsibility remains staged frame within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/staged_frame.py](../../../../../../src/learnloop/daily_plan/staged_frame.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
