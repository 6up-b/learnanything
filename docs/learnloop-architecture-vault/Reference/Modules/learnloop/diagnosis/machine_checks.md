---
title: "learnloop.diagnosis.machine_checks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/machine_checks.py"
source_paths:
  - "src/learnloop/diagnosis/machine_checks.py"
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
  - "learnloop.diagnosis.machine_checks module"
  - "src/learnloop/diagnosis/machine_checks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.machine_checks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.machine_checks` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Queue and discharge machine-side obligations before causal repair.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/machine_checks.py](../../../../../../src/learnloop/diagnosis/machine_checks.py) |
| Source lines | 363 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `backfill_obligation(targeting: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/machine_checks.py), line 48) — The typed backfill obligation for one classified cause set.
- `instrument_commissioning_obligation(targeting: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/machine_checks.py), line 83) — The typed obligation for a divergent factor with no instrument.
- `enqueue_backfill_obligation(repository: Repository, obligation: Mapping[str, Any], *, learning_object_id: str | None, source: str='causal_orchestrator', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/machine_checks.py), line 111) — Queue one typed obligation; idempotent on its content hash.
- `sweep_machine_checks(vault: LoadedVault, repository: Repository, learning_object_id: str, *, source: str='causal_orchestrator', clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/machine_checks.py), line 137) — Turn backfill obligations into queued machine checks, idempotently.
- `close_satisfied_backfills(repository: Repository, factor_id: str, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/diagnosis/machine_checks.py), line 287) — Close this factor's repair-mapping checks once it owes nothing.
- `resolve_machine_check(repository: Repository, check_id: str, *, resolution: Mapping[str, Any], status: str='resolved', clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/machine_checks.py), line 317) — Explicit discharge for a regrade / verifier / authoring agent.
- `pending_machine_checks_for_factor(repository: Repository, *, factor_id: str, learning_object_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/machine_checks.py), line 332) — Checks that must discharge before this factor may buy learner effort.

## Internal implementation anchors

- `_machine_check_id(obligation: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/diagnosis/machine_checks.py), line 34)
- `_close_orphan_checks(repository: Repository, learning_object_id: str, live: set[str], *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/machine_checks.py), line 259)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `resolve_machine_check`; statically calls `resolve_machine_check`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `backfill_obligation`, `close_satisfied_backfills`, `enqueue_backfill_obligation`, `pending_machine_checks_for_factor`; statically calls `backfill_obligation`, `close_satisfied_backfills`, `enqueue_backfill_obligation`, `pending_machine_checks_for_factor`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `sweep_machine_checks`; statically calls `sweep_machine_checks`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `pending_machine_checks_for_factor`; statically calls `pending_machine_checks_for_factor`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_cold_verification|learnloop.diagnosis.causal_cold_verification]] — imports `sweep_expired_cold_retries`; calls `sweep_expired_cold_retries`
- [[Reference/Modules/learnloop/diagnosis/causal_factor_deferral|learnloop.diagnosis.causal_factor_deferral]] — imports `sweep_promotion_blocking_factors`; calls `sweep_promotion_blocking_factors`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `candidate_has_current_blind_input_contract`; calls `candidate_has_current_blind_input_contract`
- [[Reference/Modules/learnloop/diagnosis/causal_reads|learnloop.diagnosis.causal_reads]] — imports `CAUSAL_ORCHESTRATOR_FORMULA_VERSION`, `MACHINE_CHECK_INSTRUMENT_COMMISSIONING`, `MACHINE_CHECK_REPAIR_MAPPING`, `PROBE_BLOCKING_MACHINE_CHECK_KINDS`, `SWEPT_MACHINE_CHECK_KINDS`
- [[Reference/Modules/learnloop/diagnosis/content_ids|learnloop.diagnosis.content_ids]] — imports `content_id`; calls `content_id`
- [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] — imports `classify_cause_set`; calls `classify_cause_set`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `end_untaken_episodes`; calls `end_untaken_episodes`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `RIVAL_CAUSES_FACTOR_VERSION`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_identity_helpers.py](../../../../../../tests/diagnosis_identity_helpers.py) — direct import
- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — direct import
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_a_stale_backfill_check_cannot_wedge_a_now_mapped_factor`
  - `test_live_attempt_queues_a_repair_mapping_backfill_that_self_closes`
- [tests/test_causal_probe_commissioning.py](../../../../../../tests/test_causal_probe_commissioning.py) — direct import
  - `test_sweep_machine_checks_queues_the_instrument_debt`
- [tests/test_followup_rival_factor.py](../../../../../../tests/test_followup_rival_factor.py) — direct import
  - `test_a_sweep_queues_no_mapping_this_factor_doesnt_need_and_a_retry_still_asks`
- [tests/test_probe_episode_conflict_one_check.py](../../../../../../tests/test_probe_episode_conflict_one_check.py) — direct import
  - `test_the_follow_up_router_asks_the_same_check`
- [tests/test_probe_router_authority.py](../../../../../../tests/test_probe_router_authority.py) — direct import
  - `test_d_a_pending_machine_check_refuses_before_the_router`
- [tests/test_untaken_repair_episode.py](../../../../../../tests/test_untaken_repair_episode.py) — direct import

## Modification guidance

- Change machine checks policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/machine_checks.py](../../../../../../src/learnloop/diagnosis/machine_checks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
