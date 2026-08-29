---
title: "learnloop.learner.learner_profile"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/learner_profile.py"
source_paths:
  - "src/learnloop/learner/learner_profile.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.learner_profile` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Per-vault learner profile: ``profile/learner.yaml`` + the init-wizard claim.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/learner_profile.py](../../../../../../src/learnloop/learner/learner_profile.py) |
| Source lines | 82 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `read_learner_profile(paths: VaultPaths) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/learner/learner_profile.py), line 27)
- `write_learner_profile(paths: VaultPaths, *, starting_level: str, level_note: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/learner_profile.py), line 42)
- `seed_global_learner_claim(repository, starting_level: str, *, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/learner/learner_profile.py), line 61) — Replace the init-wizard global claim with one for ``starting_level``.

### Module constants

- `LEARNER_PROFILE_SCHEMA_VERSION` ([src/learnloop/learner/learner_profile.py](../../../../../../src/learnloop/learner/learner_profile.py), line 24)

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

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_init.py](../../../../../../tests/test_init.py) — imports consumer [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]]
- [tests/test_quick_add.py](../../../../../../tests/test_quick_add.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]]
- [tests/test_exam_readiness_and_conflict.py](../../../../../../tests/test_exam_readiness_and_conflict.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]]
- [tests/test_facet_mint_gate.py](../../../../../../tests/test_facet_mint_gate.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]]
- [tests/test_ingest_instrument_gates.py](../../../../../../tests/test_ingest_instrument_gates.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]]
- [tests/test_inventory_merge_parallel.py](../../../../../../tests/test_inventory_merge_parallel.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]]
- [tests/test_maintenance_feed.py](../../../../../../tests/test_maintenance_feed.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]]
- [tests/test_practice_leakage.py](../../../../../../tests/test_practice_leakage.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]]
- [tests/test_revision_refresh.py](../../../../../../tests/test_revision_refresh.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]]
- [tests/test_source_append.py](../../../../../../tests/test_source_append.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]]
- [tests/test_source_outcome_analytics.py](../../../../../../tests/test_source_outcome_analytics.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]]
- [tests/test_source_set_synthesis.py](../../../../../../tests/test_source_set_synthesis.py) — imports consumer [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]]

## Modification guidance

- Change learner profile policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/learner_profile.py](../../../../../../src/learnloop/learner/learner_profile.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
