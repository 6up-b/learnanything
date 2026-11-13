---
title: "learnloop.learner.learner_profile"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/learner_profile.py"
source_paths:
  - "src/learnloop/learner/learner_profile.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.learner_profile module"
  - "src/learnloop/learner/learner_profile.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.learner_profile`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.learner_profile` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Per-vault learner profile: ``profile/learner.yaml`` + the init-wizard claim.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/learner_profile.py](../../../../../../src/learnloop/learner/learner_profile.py) |
| Source lines | 91 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `read_learner_profile(paths: VaultPaths) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/learner/learner_profile.py), line 30)
- `write_learner_profile(paths: VaultPaths, *, starting_level: str, level_note: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/learner_profile.py), line 45)
- `seed_global_learner_claim(repository, starting_level: str, *, keep_replaced: bool=False, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/learner/learner_profile.py), line 64) — Replace the init-wizard global claim with one for ``starting_level``.

### Module constants

- `LEARNER_PROFILE_SCHEMA_VERSION` ([src/learnloop/learner/learner_profile.py](../../../../../../src/learnloop/learner/learner_profile.py), line 27)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]] — imports `seed_global_learner_claim`, `write_learner_profile`; statically calls `seed_global_learner_claim`, `write_learner_profile`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `read_learner_profile`; statically calls `read_learner_profile`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `read_learner_profile`; statically calls `read_learner_profile`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `read_learner_profile`, `seed_global_learner_claim`, `write_learner_profile`; statically calls `read_learner_profile`, `seed_global_learner_claim`, `write_learner_profile`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/synthesis/brief|learnloop.content.synthesis.brief]] — imports `INIT_CLAIM_PSEUDO_COUNT`, `STARTING_LEVELS`, `STARTING_LEVEL_CLAIMS`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `write_yaml`; calls `read_yaml`, `write_yaml`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]], [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]], [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_learner_report_superseded.py](../../../../../../tests/test_learner_report_superseded.py) — direct import
  - `test_a_global_claim_made_after_materialization_rebuilds_to_live`
  - `test_a_new_starting_level_keeps_the_old_one_for_an_lo_first_practised_under_it`
- [tests/test_rerun_proposals.py](../../../../../../tests/test_rerun_proposals.py) — direct import
  - `test_an_append_resolves_its_brief_and_inherits_the_learners_level`

## Modification guidance

- Change learner profile policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/learner_profile.py](../../../../../../src/learnloop/learner/learner_profile.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
