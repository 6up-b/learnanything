---
title: "learnloop.config.template"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/template.py"
source_paths:
  - "src/learnloop/config/template.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/config/_package|learnloop.config]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.config.template` exists within [[Reference/Modules/learnloop/config/_package|learnloop.config]] to own the behavior summarized by its module contract: The decision-only configuration template a new vault is written with.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py) |
| Source lines | 125 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `default_config_text(algorithm_version: str=LATEST_ALGORITHM_VERSION) -> str` ([source](../../../../../../src/learnloop/config/template.py), line 99) — The decision-only template as a vault at ``algorithm_version`` holds it.
- `write_default_config(path: Path) -> None` ([source](../../../../../../src/learnloop/config/template.py), line 113) — Write the decision-only template without replacing an existing file.

### Module constants

- `_ALGORITHM_VERSION_PLACEHOLDER` ([src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py), line 14)
- `_DEFAULT_CONFIG_TEMPLATE` ([src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py), line 16)
- `DEFAULT_CONFIG_TEXT` ([src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py), line 110)

### Explicit exports

`__all__` declares:

- `DEFAULT_CONFIG_TEXT`
- `default_config_text`
- `write_default_config`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `module`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `write_default_config`

### Repository tooling consumers

- [scripts/refactor_measures.py](../../../../../../scripts/refactor_measures.py)

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `LATEST_ALGORITHM_VERSION`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/config/__init__|learnloop.config]], [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_config_responsibilities_have_canonical_module_owners`
  - `test_new_vaults_start_at_the_latest_algorithm_version`
  - `test_the_template_renders_at_every_tag_by_its_label_alone`
- [tests/test_diagnosis_input_provenance.py](../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_f5_every_tag_defaults_the_switch_off`
- [tests/test_effective_defaults_golden.py](../../../../../../tests/test_effective_defaults_golden.py) — direct import
  - `test_every_tag_has_the_latest_defaults_apart_from_its_label`
- [tests/test_field_config.py](../../../../../../tests/test_field_config.py) — direct import
  - `test_offline_config_never_opens_dotenv_or_global_settings`
- [tests/test_followup_successor.py](../../../../../../tests/test_followup_successor.py) — direct import
  - `test_new_vaults_get_true_effectively_and_older_templates_stay_as_they_were`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_the_successors_kill_switch_defaults_on_and_its_judge_route_is_unset`
- [tests/test_mvp013_upgrade.py](../../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_the_successors_kill_switch_defaults_on`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_the_plan_successors_defaults`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_the_probe_tie_successors_switches_default_on`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_the_learner_text_gap_successors_defaults`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_the_route_check_successors_kill_switch_defaults_on`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_the_route_rules_successors_kill_switch_stays_and_its_route_is_retired`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
  - `test_the_voi_stopping_successors_defaults`
- [tests/test_pf_cli.py](../../../../../../tests/test_pf_cli.py) — direct import
  - `test_template_keeps_generation_off_and_caps_publication`
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — direct import
  - `test_every_tag_defaults_the_switch_on`
- [tests/test_reading_step_switch.py](../../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_every_tag_defaults_the_switch_on`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_the_successor_sets_no_cosine_cutoff_by_default`
- [tests/test_ro1_successor.py](../../../../../../tests/test_ro1_successor.py) — direct import
  - `test_the_factors_constants_stay_in_config`

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/config/template.py](../../../../../../src/learnloop/config/template.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
