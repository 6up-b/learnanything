---
title: "learnloop.diagnosis.recurrence.upgrade"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/recurrence/upgrade.py"
source_paths:
  - "src/learnloop/diagnosis/recurrence/upgrade.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.recurrence"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.diagnosis.recurrence.upgrade module"
  - "src/learnloop/diagnosis/recurrence/upgrade.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-recurrence"
---

# `learnloop.diagnosis.recurrence.upgrade`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.recurrence.upgrade` exists within [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] to own the behavior summarized by its module contract: ``learnloop upgrade --to mvp-0.12``: activate recurrence with authority (Slice 2 §3.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/recurrence/upgrade.py](../../../../../../../src/learnloop/diagnosis/recurrence/upgrade.py) |
| Source lines | 216 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `upgrade_to_mvp012(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/upgrade.py), line 77)
- `guard_findings(vault: LoadedVault, repository: Repository) -> tuple[list[str], dict[str, Any] | None]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/upgrade.py), line 133) — Why the guard has not passed for the configured judge (empty: it passed).
- `advisory_notes(problems: list[str], guard: dict[str, Any] | None) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/upgrade.py), line 195) — The guard's status for an upgrade it does not gate (owner, 2026-10-12).

### Module constants

- `LOG` ([src/learnloop/diagnosis/recurrence/upgrade.py](../../../../../../../src/learnloop/diagnosis/recurrence/upgrade.py), line 69)
- `_CHAINED_PREDECESSORS` ([src/learnloop/diagnosis/recurrence/upgrade.py](../../../../../../../src/learnloop/diagnosis/recurrence/upgrade.py), line 74)
- `M1_RUN_ADDS` ([src/learnloop/diagnosis/recurrence/upgrade.py](../../../../../../../src/learnloop/diagnosis/recurrence/upgrade.py), line 187)

### Explicit exports

`__all__` declares:

- `M1_RUN_ADDS`
- `advisory_notes`
- `guard_findings`
- `upgrade_to_mvp012`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `upgrade_to_mvp012`; statically calls `upgrade_to_mvp012`
- [[Reference/Modules/learnloop/stuck_prompt_upgrade|learnloop.stuck_prompt_upgrade]] — imports `upgrade_to_mvp012`; statically calls `upgrade_to_mvp012`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `DIAGNOSIS_SPLIT_ALGORITHM_VERSION`, `PLACEMENT_ALGORITHM_VERSION`, `RECURRENCE_GROUP_ALGORITHM_VERSION`, `REVEAL_LEDGER_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `configured_judge_model`, `guard_status`; calls `configured_judge_model`, `guard_status`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `settings_from_config`; calls `settings_from_config`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`, `upgrade_to_mvp011`; calls `UpgradeResult`, `rewrite_algorithm_version`, `upgrade_to_mvp011`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `freeze_manifest`, `refresh`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `activate_p0_projection`; calls `activate_p0_projection`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `activate_recurrence_groups`, `prepare_recurrence_groups`; calls `activate_recurrence_groups`, `prepare_recurrence_groups`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/stuck_prompt_upgrade|learnloop.stuck_prompt_upgrade]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_recurrence_commands.py](../../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_a_citation_that_did_not_validate_merges_nothing_and_is_reported`
  - `test_a_failing_guard_leaves_every_predecessor_where_it_was`
  - `test_a_failure_after_preparation_leaves_no_group_in_force`
  - `test_a_false_merge_blocks_the_switch_and_a_fixed_judge_reruns_through_the_guard`
  - `test_a_judge_route_without_a_model_is_advisory_too`
  - `test_a_registered_case_the_judge_never_saw_blocks_the_switch`
  - `test_a_validated_diagnoser_citation_of_the_planted_a_answer_blocks_the_switch`
  - `test_an_advisory_guard_reports_a_recorded_false_merge_and_still_upgrades`
  - `test_an_advisory_guard_that_passed_says_so`
  - `test_an_explicit_rerun_supersedes_the_same_models_false_merge`
  - `test_an_m1_case_from_a_run_is_required_and_its_false_merge_blocks_the_switch`
  - `test_guard_verdicts_from_another_judge_model_do_not_open_the_switch`
  - `test_require_guard_restores_the_refusal`
  - `test_the_advisory_upgrade_chains_without_a_guard_run`
  - `test_the_guard_is_advisory_by_default`
  - `test_the_guard_judges_the_diagnosers_own_statement_for_the_b_answer`
  - `test_the_head_fixture_predecessor_to_successor_path`
  - `test_the_judge_producer_is_model_and_effort_so_codex_tiers_never_share_a_guard_pass`
  - `test_the_switch_needs_an_m1_case_checked_in_the_live_history_mode`
  - `test_the_upgrade_accepts_the_chain_and_refuses_older_versions`
  - `test_the_upgrade_activates_its_prepared_groups_after_the_switch`
  - `test_the_upgrade_chains_from_each_predecessor`
  - `test_verdicts_split_across_two_models_do_not_pass_for_the_configured_one`

## Modification guidance

- Change upgrade policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/recurrence/upgrade.py](../../../../../../../src/learnloop/diagnosis/recurrence/upgrade.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
