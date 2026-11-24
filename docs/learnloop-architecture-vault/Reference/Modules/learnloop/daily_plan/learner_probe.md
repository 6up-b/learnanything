---
title: "learnloop.daily_plan.learner_probe"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/learner_probe.py"
source_paths:
  - "src/learnloop/daily_plan/learner_probe.py"
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
  - "learnloop.daily_plan.learner_probe module"
  - "src/learnloop/daily_plan/learner_probe.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.learner_probe`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.learner_probe` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The probe router's learner lane: the router decides whether the feedback screen offers the quick check.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/learner_probe.py](../../../../../../src/learnloop/daily_plan/learner_probe.py) |
| Source lines | 287 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `decide(vault: Any, repository: Any, *, misconception_id: str, session_id: str | None=None, clock: Clock | None=None) -> Any` ([source](../../../../../../src/learnloop/daily_plan/learner_probe.py), line 52) — The repair status after the router has decided the factor's probe (where it had to): read, decide once if ``pending``, read again.
- `diagnostic_payload(vault: Any, repository: Any, proposal: Any) -> DP.DiagnosticProbe | str` ([source](../../../../../../src/learnloop/daily_plan/learner_probe.py), line 102) — The probe's diagnostic payload, or why none can be built (a string): the locked set's hypotheses at its prior, each with its cause class; the instrument's channel or its typed absence; one repair option per repair class, covering the hypotheses mapped to it.
- `value(vault: Any, repository: Any, proposal: Any, *, now_iso: str, seed_identity: Mapping[str, Any]) -> tuple[Any, dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/learner_probe.py), line 149) — ``(valuation, record)``: :func:`evaluate_probe`'s valuation of the proposal's probe against repairing now, or ``(None, record)`` with the reason none could be made (no topic, no payload, an error).
- `information(valuation: Any) -> float` ([source](../../../../../../src/learnloop/daily_plan/learner_probe.py), line 191) — The probe's information value at the learned slopes: the policy after its answer against the prior's choice after the same probe (``evaluate_probe``'s ``values.information``; 0 when no result changes the choice).
- `decide_proposal(vault: Any, repository: Any, proposal: Any, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/learner_probe.py), line 200) — Decide the proposal's probe once and record it; returns the factor's decision id (an earlier one when a concurrent read recorded it first).

### Module constants

- `LOG` ([src/learnloop/daily_plan/learner_probe.py](../../../../../../src/learnloop/daily_plan/learner_probe.py), line 41)
- `POLICY` ([src/learnloop/daily_plan/learner_probe.py](../../../../../../src/learnloop/daily_plan/learner_probe.py), line 44)
- `OWNER_DECISIONS` ([src/learnloop/daily_plan/learner_probe.py](../../../../../../src/learnloop/daily_plan/learner_probe.py), line 47)
- `LLM_NOT_ASKED` ([src/learnloop/daily_plan/learner_probe.py](../../../../../../src/learnloop/daily_plan/learner_probe.py), line 49)

### Explicit exports

`__all__` declares:

- `LLM_NOT_ASKED`
- `OWNER_DECISIONS`
- `POLICY`
- `decide`
- `decide_proposal`
- `diagnostic_payload`
- `information`
- `value`

## Internal implementation anchors

- `_cause_class(repository: Any, hypothesis_id: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/learner_probe.py), line 68)
- `_channel(vault: Any, repository: Any, item: Any, hypothesis_set: Any, labels: list[str]) -> DP.Channel | DP.MissingChannel` ([source](../../../../../../src/learnloop/daily_plan/learner_probe.py), line 74)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `module`; statically calls `decide`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; calls `_local_date`, `current_weight`, `day_price`, `numeric_seed`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; calls `build`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BlockCandidate`, `PlanState`; calls `BlockCandidate`, `PlanState`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `causal_repair_status`; calls `causal_repair_status`
- [[Reference/Modules/learnloop/diagnosis/learner_probe_proposal|learnloop.diagnosis.learner_probe_proposal]] — imports `CHANNEL_SOURCE`, `PROBE_ACTION_REF`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `resolve_instrument`; calls `resolve_instrument`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `instrument_conditionals`; calls `instrument_conditionals`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `HypothesisSet`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `label_conditionals`; calls `label_conditionals`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/router/plan_log|learnloop.router.plan_log]] — imports `NO_PROBE_REF`, `PROBE_REF`, `log_learner_probe_decision`; calls `log_learner_probe_decision`
- [[Reference/Modules/learnloop/router_objective/assignments|learnloop.router_objective.assignments]] — imports `module`; calls `record_pending`
- [[Reference/Modules/learnloop/router_objective/choose|learnloop.router_objective.choose]] — imports `module`; calls `PostMissInputs`, `post_miss_choice`
- [[Reference/Modules/learnloop/router_objective/diagnostic_payload|learnloop.router_objective.diagnostic_payload]] — imports `module`; calls `Channel`, `DiagnosticProbe`, `Hypothesis`, `MissingChannel`, `RepairOption`
- [[Reference/Modules/learnloop/router_objective/diagnostic_value|learnloop.router_objective.diagnostic_value]] — imports `evaluate_probe`; calls `evaluate_probe`
- [[Reference/Modules/learnloop/router_objective/miss_cause|learnloop.router_objective.miss_cause]] — imports `CLASSES`
- [[Reference/Modules/learnloop/router_objective/mix|learnloop.router_objective.mix]] — imports `module`; calls `failure_rule_name`, `fallback_label`, `seed_for`
- [[Reference/Modules/learnloop/router_objective/probe_coin|learnloop.router_objective.probe_coin]] — imports `module`; calls `applies`, `flip`, `pending_assignment`, `seed_for`, `served_distribution`, `share`
- [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]] — imports `module`; calls `Action`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `failure_share_to_other_policy_on`; calls `failure_share_to_other_policy_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — direct import
- [tests/test_probe_router_learner_lane.py](../../../../../../tests/test_probe_router_learner_lane.py) — direct import
  - `test_a_learned_probe_is_an_option_of_the_mix_and_no_coin_is_flipped`
  - `test_the_valuation_prices_the_existing_instruments_channel`

## Modification guidance

- Make changes here when the responsibility remains learner probe within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/learner_probe.py](../../../../../../src/learnloop/daily_plan/learner_probe.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
