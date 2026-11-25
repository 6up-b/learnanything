---
title: "learnloop.daily_plan.probe_continuation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/probe_continuation.py"
source_paths:
  - "src/learnloop/daily_plan/probe_continuation.py"
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
  - "learnloop.daily_plan.probe_continuation module"
  - "src/learnloop/daily_plan/probe_continuation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.probe_continuation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.probe_continuation` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The probe router's continuation: one router decision per next observation of a router-owned episode.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/probe_continuation.py](../../../../../../src/learnloop/daily_plan/probe_continuation.py) |
| Source lines | 305 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ContinuationProposal` ([source](../../../../../../src/learnloop/daily_plan/probe_continuation.py), line 46) — What the valuation reads about one episode's next observation (``learner_probe.value``'s proposal shape).
  - `practice_item_id(self) -> str | None` (line 63; public)
  - `facts(self) -> dict[str, Any]` (line 67; public)
- `boundary(repository: Any, episode: Any) -> tuple[int, int] | None` ([source](../../../../../../src/learnloop/daily_plan/probe_continuation.py), line 88) — The episode's decision boundary ``(observations, redraw)`` when a decision is due there, else None: none yet at this count, or the last one asked a probe whose pin ended unanswered (expired, refused, invalidated).
- `requested(vault: Any, repository: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/probe_continuation.py), line 108) — The router-owned episodes waiting on a continuation decision, oldest first.
- `proposal(vault: Any, repository: Any, episode: Any) -> tuple[ContinuationProposal | None, Any, str | None]` ([source](../../../../../../src/learnloop/daily_plan/probe_continuation.py), line 129) — ``(proposal, the next eligible instrument, why none)`` for the episode's next observation: its top eligible instrument, on its posterior.
- `decide(vault: Any, repository: Any, request: Mapping[str, Any], *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/probe_continuation.py), line 164) — Decide one waiting episode's next observation and record it with what it serves (the pinned next presentation, or the episode's stop), all in one transaction.
- `run_pending(vault: Any, repository: Any, *, clock: Clock | None=None, max_jobs: int=100) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/probe_continuation.py), line 291) — The continuation job: decide each waiting episode once.

### Module constants

- `LOG` ([src/learnloop/daily_plan/probe_continuation.py](../../../../../../src/learnloop/daily_plan/probe_continuation.py), line 37)
- `POLICY` ([src/learnloop/daily_plan/probe_continuation.py](../../../../../../src/learnloop/daily_plan/probe_continuation.py), line 40)
- `UNIT` ([src/learnloop/daily_plan/probe_continuation.py](../../../../../../src/learnloop/daily_plan/probe_continuation.py), line 42)

### Explicit exports

`__all__` declares:

- `POLICY`
- `UNIT`
- `ContinuationProposal`
- `boundary`
- `decide`
- `proposal`
- `requested`
- `run_pending`

## Internal implementation anchors

- `_observations(repository: Any, episode_id: str) -> int` ([source](../../../../../../src/learnloop/daily_plan/probe_continuation.py), line 73)
- `_pins_of(repository: Any, episode_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/probe_continuation.py), line 77) — The episode's presentations by the router decision their pin names.
- `_still_waiting(repository: Any, valued: Any, at: tuple[int, int]) -> Any` ([source](../../../../../../src/learnloop/daily_plan/probe_continuation.py), line 277) — The episode as it stands now when it is still the boundary that was valued (in progress, the same state segment, no presentation standing, the same observation count and redraw), else None.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `module`; statically calls `requested`
- [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]] — imports `run_pending`; statically calls `run_pending`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `probe_router_on`; calls `probe_router_on`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]] — imports `module`; calls `draw`, `information`, `instrument_items`, `value`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `module`; calls `freeze_followup`, `record`
- [[Reference/Modules/learnloop/db/writer_fence|learnloop.db.writer_fence]] — imports `require_current`; calls `require_current`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `repair_classes_for_factor`, `resolve_orchestrator_parameters`; calls `repair_classes_for_factor`, `resolve_orchestrator_parameters`
- [[Reference/Modules/learnloop/diagnosis/causal_reads|learnloop.diagnosis.causal_reads]] — imports `probe_burden_minutes`; calls `probe_burden_minutes`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `stop_on_router_decision`; calls `stop_on_router_decision`
- [[Reference/Modules/learnloop/diagnosis/probe_completion|learnloop.diagnosis.probe_completion]] — imports `park_without_supply`; calls `park_without_supply`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `router_selected_episode`; calls `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `router_selected_episode`
- [[Reference/Modules/learnloop/diagnosis/probe_hard_stops|learnloop.diagnosis.probe_hard_stops]] — imports `causal_origin_factor`; calls `causal_origin_factor`
- [[Reference/Modules/learnloop/diagnosis/probe_presentations|learnloop.diagnosis.probe_presentations]] — imports `commit_presentation`; calls `commit_presentation`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/router/plan_log|learnloop.router.plan_log]] — imports `CONTINUATION_STOP_REF`, `PROBE_REF`, `log_probe_continuation_decision`, `probe_continuation_decisions`, `probe_continuation_receipt_key`; calls `log_probe_continuation_decision`, `probe_continuation_decisions`, `probe_continuation_receipt_key`
- [[Reference/Modules/learnloop/router_objective/assignments|learnloop.router_objective.assignments]] — imports `module`; calls `record_pending`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `logging`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probe_router_continuation.py](../../../../../../tests/test_probe_router_continuation.py) — direct import
  - `test_a_pin_that_ended_unanswered_opens_a_new_boundary`
  - `test_below_the_tag_no_episode_waits_on_the_router`
  - `test_the_continuation_answer_closes_its_block_by_its_pin_and_no_legacy_worth_gate_is_asked`
  - `test_the_router_decides_the_next_observation_once_with_its_exact_served_distribution`
- [tests/test_probe_router_episode_owner.py](../../../../../../tests/test_probe_router_episode_owner.py) — direct import
  - `test_a_stale_worker_commits_neither_arm_of_the_continuation`
  - `test_an_exposed_answer_on_the_last_instrument_parks_the_episode_with_one_supply_request`
  - `test_between_blocks_only_the_router_supplies_a_router_owned_episodes_next_question`
  - `test_the_job_never_overwrites_the_learners_stop_made_while_it_valued`

## Modification guidance

- Make changes here when the responsibility remains probe continuation within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/probe_continuation.py](../../../../../../src/learnloop/daily_plan/probe_continuation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
