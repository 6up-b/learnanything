---
title: "learnloop.config.template"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/template.py"
source_paths:
  - "src/learnloop/config/template.py"
source_commit: "224700d26fdc3e8a31cb6a4fa481efff3ef1d939"
source_commit_timestamp: "2026-11-09T04:50:36-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.config"
layer: "infrastructure"
concepts:
  - "Configuration"
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.config.template module"
  - "src/learnloop/config/template.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-config"
---

# `learnloop.config.template`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/config/_package|learnloop.config]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.config.template` exists within [[Reference/Modules/learnloop/config/_package|learnloop.config]] to own the behavior summarized by its module contract: Generated configuration text and the effective-defaults snapshot contract.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py) |
| Source lines | 4222 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `224700d26fdc3e8a31cb6a4fa481efff3ef1d939` |
| Commit timestamp | `2026-11-09T04:50:36-05:00` |

## Public API

- `default_config_text(algorithm_version: str=LATEST_ALGORITHM_VERSION) -> str` ([source](../../../../../../src/learnloop/config/template.py), line 822) — The decision-only template as a vault at ``algorithm_version`` holds it.
- `write_default_config(path: Path) -> None` ([source](../../../../../../src/learnloop/config/template.py), line 4171) — Write the decision-only template without replacing an existing file.
- `effective_defaults_fingerprint(config: LearnLoopConfig | None=None) -> str` ([source](../../../../../../src/learnloop/config/template.py), line 4179) — Content address of the complete effective defaults for a new vault.
- `defaults_fingerprint_for_version(algorithm_version: str) -> str` ([source](../../../../../../src/learnloop/config/template.py), line 4201) — The effective-defaults fingerprint of a new vault at ``algorithm_version``.

### Module constants

- `LEGACY_DEFAULT_CONFIG_TEXT` ([src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py), line 19)
- `_ALGORITHM_VERSION_PLACEHOLDER` ([src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py), line 737)
- `_DEFAULT_CONFIG_TEMPLATE` ([src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py), line 739)
- `DEFAULT_CONFIG_TEXT` ([src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py), line 836)
- `DEFAULTS_SNAPSHOT_BY_ALGORITHM` ([src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py), line 845)

### Explicit exports

`__all__` declares:

- `DEFAULT_CONFIG_TEXT`
- `DEFAULTS_SNAPSHOT_BY_ALGORITHM`
- `LEGACY_DEFAULT_CONFIG_TEXT`
- `default_config_text`
- `defaults_fingerprint_for_version`
- `effective_defaults_fingerprint`
- `write_default_config`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `module`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `write_default_config`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `LATEST_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `LearnLoopConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `pathlib`, `tomllib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/config/__init__|learnloop.config]], [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — direct import
  - `test_the_successor_is_the_next_link_with_its_defaults_snapshot`
- [tests/test_attempt_content_state_successor.py](../../../../../../tests/test_attempt_content_state_successor.py) — direct import
  - `test_mvp037_is_one_constant_after_mvp036`
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_mvp035_is_one_constant_after_mvp034_and_the_latest`
- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_mvp038_is_one_constant_after_mvp037`
- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_config_responsibilities_have_canonical_module_owners`
  - `test_every_recorded_version_keeps_its_defaults_snapshot`
  - `test_minimal_template_preserves_non_provider_effective_defaults`
  - `test_new_vaults_start_at_the_latest_algorithm_version`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_the_successor_is_one_constant_after_rw6bs_followups`
- [tests/test_data_capture_successor.py](../../../../../../tests/test_data_capture_successor.py) — direct import
  - `test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys`
- [tests/test_diagnosis_input_provenance.py](../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_f5_every_defaults_snapshot_records_the_switch_off`
- [tests/test_field_config.py](../../../../../../tests/test_field_config.py) — direct import
  - `test_offline_config_never_opens_dotenv_or_global_settings`
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_the_successor_vocabulary_is_one_constant_after_its_predecessor`
- [tests/test_followup_successor.py](../../../../../../tests/test_followup_successor.py) — direct import
  - `test_every_defaults_snapshot_is_recomputed`
  - `test_new_vaults_get_true_effectively_and_older_templates_stay_as_they_were`
- [tests/test_help_fold_attach_successor.py](../../../../../../tests/test_help_fold_attach_successor.py) — direct import
  - `test_mvp042_is_one_constant_after_mvp041_and_the_latest`
- [tests/test_ih5_successor.py](../../../../../../tests/test_ih5_successor.py) — direct import
  - `test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_key`
- [tests/test_intent_codex_rereview.py](../../../../../../tests/test_intent_codex_rereview.py) — direct import
  - `test_f2_the_chain_ends_at_the_intent_successor`
- [tests/test_learner_report_superseded.py](../../../../../../tests/test_learner_report_superseded.py) — direct import
  - `test_the_tag_is_one_constant_after_mvp035_and_the_latest`
- [tests/test_lp_claim_fixes.py](../../../../../../tests/test_lp_claim_fixes.py) — direct import
  - `test_the_successor_is_one_constant_after_its_predecessor`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_successor`
- [tests/test_mobile_v3_successor.py](../../../../../../tests/test_mobile_v3_successor.py) — direct import
  - `test_the_snapshot_is_recorded_and_differs_from_the_predecessors_by_the_tag_alone`
- [tests/test_mvp010_upgrade.py](../../../../../../tests/test_mvp010_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_successor`
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_placement_successor`
- [tests/test_mvp013_upgrade.py](../../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_successor`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_plan_successor`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_probe_tie_successor`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_learner_text_gap_successor`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_route_check_successor`
- [tests/test_mvp018_upgrade.py](../../../../../../tests/test_mvp018_upgrade.py) — direct import
  - `test_defaults_fingerprints_are_recorded_for_every_successor`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_route_rules_successor`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_every_successor`
- [tests/test_mvp022_upgrade.py](../../../../../../tests/test_mvp022_upgrade.py) — direct import
  - `test_defaults_fingerprints_are_recorded_for_every_successor`
- [tests/test_mvp023_upgrade.py](../../../../../../tests/test_mvp023_upgrade.py) — direct import
  - `test_defaults_fingerprints_are_recorded_for_every_successor`
- [tests/test_mvp024_upgrade.py](../../../../../../tests/test_mvp024_upgrade.py) — direct import
  - `test_defaults_fingerprints_are_recorded_for_every_successor`
- [tests/test_pf_cli.py](../../../../../../tests/test_pf_cli.py) — direct import
  - `test_template_keeps_generation_off_and_caps_publication`
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — direct import
  - `test_every_defaults_snapshot_records_the_switch_on`
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_the_successor_is_one_constant_after_rw2d`
- [tests/test_reader_ca2_one_ask.py](../../../../../../tests/test_reader_ca2_one_ask.py) — direct import
  - `test_the_successor_is_one_constant_after_rebuild_equivalence`
- [tests/test_reader_followups_successor.py](../../../../../../tests/test_reader_followups_successor.py) — direct import
  - `test_mvp039_is_one_constant_after_mvp038_and_the_latest`
- [tests/test_reading_step_switch.py](../../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_every_defaults_snapshot_records_the_switch_on`
- [tests/test_rebuild_equivalence_review.py](../../../../../../tests/test_rebuild_equivalence_review.py) — direct import
  - `test_the_successor_is_one_constant_after_its_predecessor_with_its_defaults_snapshot`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_defaults_fingerprint_is_recorded_for_the_successor`
- [tests/test_regrade_contract_successor.py](../../../../../../tests/test_regrade_contract_successor.py) — direct import
  - `test_its_defaults_fingerprint_is_recorded`
- [tests/test_ro1_successor.py](../../../../../../tests/test_ro1_successor.py) — direct import
  - `test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys`
  - `test_the_factors_constants_stay_in_config_with_their_note`
- [tests/test_ro4_successor.py](../../../../../../tests/test_ro4_successor.py) — direct import
  - `test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys`
- [tests/test_ro5_successor.py](../../../../../../tests/test_ro5_successor.py) — direct import
  - `test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys`
- [tests/test_ro6_successor.py](../../../../../../tests/test_ro6_successor.py) — direct import
  - `test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys`
- [tests/test_rofu_successor.py](../../../../../../tests/test_rofu_successor.py) — direct import
  - `test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys`
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_f4_the_successor_follows_regrade_contracts_and_keeps_every_predecessor`
- [tests/test_te3a_successor.py](../../../../../../tests/test_te3a_successor.py) — direct import
  - `test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_key`
- [tests/test_te3b_successor.py](../../../../../../tests/test_te3b_successor.py) — direct import
  - `test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_key`
- [tests/test_teacher_te1_successor.py](../../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_every_defaults_snapshot_drops_to_mains_value_without_the_teacher_keys`
- [tests/test_teacher_te1b_suggestions.py](../../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_every_defaults_snapshot_drops_to_te1s_value_without_the_suggestion_keys`
- [tests/test_teacher_te2_successor.py](../../../../../../tests/test_teacher_te2_successor.py) — direct import
  - `test_every_defaults_snapshot_is_recomputed_and_moves_only_by_the_new_keys`

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
