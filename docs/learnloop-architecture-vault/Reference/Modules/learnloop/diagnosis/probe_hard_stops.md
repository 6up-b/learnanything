---
title: "learnloop.diagnosis.probe_hard_stops"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_hard_stops.py"
source_paths:
  - "src/learnloop/diagnosis/probe_hard_stops.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.probe_hard_stops module"
  - "src/learnloop/diagnosis/probe_hard_stops.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_hard_stops`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_hard_stops` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Learner probe preferences and conflicts with an already-open probe episode.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_hard_stops.py](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py) |
| Source lines | 172 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `record_learner_preference(repository: Repository, *, preference: str, factor_id: str | None=None, learning_object_id: str | None=None, session_id: str | None=None, source: str='learner_action', expires_at: str | None=None, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py), line 40)
- `learner_preference(repository: Repository, *, factor_id: str | None=None, learning_object_id: str | None=None, session_id: str | None=None) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py), line 77)
- `causal_origin(factor_id: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py), line 98) — An episode's origin string for a factor.
- `causal_origin_factor(origin: str) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py), line 104) — The factor a causal episode's origin names, or None (:func:`_causal_origin`).
- `episode_conflict_reason(repository: Repository, episode: ProbeEpisodeRecord | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py), line 111) — Why an already-open probe episode cannot host this causal probe.
- `standing_owned_pin(repository: Repository, episode_id: str) -> Any` ([source](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py), line 140) — The episode's standing presentation when a decision owns it (a follow-up workflow's pin, or a router decision's: an accepted learner-lane offer, a continuation), else None.
- `probe_episode_conflict(repository: Repository, *, factor_id: str, learning_object_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py), line 154) — The conflict that would make ``accept_probe_offer`` refuse, if any.

### Module constants

- `LEARNER_PREFERENCES` ([src/learnloop/diagnosis/probe_hard_stops.py](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py), line 25)
- `EPISODE_CONFLICT_REASON` ([src/learnloop/diagnosis/probe_hard_stops.py](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py), line 30)
- `EPISODE_CONFLICT_MESSAGE` ([src/learnloop/diagnosis/probe_hard_stops.py](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py), line 33)

## Internal implementation anchors

- `_causal_origin(factor_id: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py), line 94)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/probe_continuation|learnloop.daily_plan.probe_continuation]] — imports `causal_origin_factor`; statically calls `causal_origin_factor`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `EPISODE_CONFLICT_MESSAGE`, `learner_preference`, `probe_episode_conflict`; statically calls `learner_preference`, `probe_episode_conflict`
- [[Reference/Modules/learnloop/diagnosis/probe_offer|learnloop.diagnosis.probe_offer]] — imports `EPISODE_CONFLICT_REASON`, `_causal_origin`, `episode_conflict_reason`, `record_learner_preference`; statically calls `_causal_origin`, `episode_conflict_reason`, `record_learner_preference`
- [[Reference/Modules/learnloop/diagnosis/probe_presentations|learnloop.diagnosis.probe_presentations]] — imports `learner_preference`, `standing_owned_pin`; statically calls `learner_preference`, `standing_owned_pin`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `causal_origin_factor`; statically calls `causal_origin_factor`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `learner_preference`, `probe_episode_conflict`; statically calls `learner_preference`, `probe_episode_conflict`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `record_learner_preference`; statically calls `record_learner_preference`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/probes|learnloop.db.stores.probes]] — imports `ProbeEpisodeRecord`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `episode_has_observations`; calls `episode_has_observations`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/probe_continuation|learnloop.daily_plan.probe_continuation]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/probe_offer|learnloop.diagnosis.probe_offer]], [[Reference/Modules/learnloop/diagnosis/probe_presentations|learnloop.diagnosis.probe_presentations]], [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_not_now_persists_and_the_next_call_does_not_reoffer`
  - `test_teach_me_now_starts_the_repair_under_recorded_authorisation`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_causal_disambiguation_end_to_end_acceptance`
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
- [tests/test_followup_journey.py](../../../../../../tests/test_followup_journey.py) — direct import
  - `test_continue_without_it_retires_the_probe_and_next_goes_on`
- [tests/test_probe_episode_conflict_one_check.py](../../../../../../tests/test_probe_episode_conflict_one_check.py) — direct import
  - `test_an_open_foreign_episode_that_has_measured_refuses`
  - `test_an_unknown_learning_object_asks_nothing`
  - `test_the_factors_own_episode_is_no_conflict`
  - `test_the_follow_up_router_asks_the_same_check`
- [tests/test_probe_router_authority.py](../../../../../../tests/test_probe_router_authority.py) — direct import
  - `test_d_the_refusals_ask_preference_then_machine_checks_then_the_shared_episode_check`
- [tests/test_probe_router_episode_owner.py](../../../../../../tests/test_probe_router_episode_owner.py) — direct import
  - `test_a_second_factors_acceptance_never_relocks_the_episode_under_the_first_factors_standing_question`

## Modification guidance

- Change probe hard stops policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_hard_stops.py](../../../../../../src/learnloop/diagnosis/probe_hard_stops.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
