---
title: "learnloop.intent.deadline"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/intent/deadline.py"
source_paths:
  - "src/learnloop/intent/deadline.py"
source_commit: "3240203723d79c44a6ee1c40f4303cbd4e061a1f"
source_commit_timestamp: "2026-10-20T13:30:13-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.intent"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.intent.deadline module"
  - "src/learnloop/intent/deadline.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-intent"
---

# `learnloop.intent.deadline`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.intent.deadline` exists within [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] to own the behavior summarized by its module contract: Goals as optional deadlines (spec §5.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/intent/deadline.py](../../../../../../src/learnloop/intent/deadline.py) |
| Source lines | 171 |
| Owning package | [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `3240203723d79c44a6ee1c40f4303cbd4e061a1f` |
| Commit timestamp | `2026-10-20T13:30:13-04:00` |

## Public API

- `goal_id_for(commitment_id: str) -> str` ([source](../../../../../../src/learnloop/intent/deadline.py), line 49) — The deadline goal's stable identity: one per commitment (F9).
- `set_deadline(vault: Any, repository: Any, scope: Scope, due_at: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/deadline.py), line 78) — Add or move the deadline of the scope's own depth commitment.

### Explicit exports

`__all__` declares:

- `goal_id_for`
- `set_deadline`

## Internal implementation anchors

- `_write_goals(path: Path, data: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/intent/deadline.py), line 55) — Publish ``goals.yaml`` whole: a temporary file, then an atomic replace, so a crash never leaves it half written.
- `_normalize_due(due_at: str) -> str` ([source](../../../../../../src/learnloop/intent/deadline.py), line 65)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]] — imports `set_deadline`; statically calls `set_deadline`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `append_commitment_version`
- [[Reference/Modules/learnloop/intent/control|learnloop.intent.control]] — imports `IntentControlError`, `Scope`, `own_commitments`, `scope_contents`; calls `IntentControlError`, `own_commitments`, `scope_contents`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `scope_facets`; calls `scope_facets`
- [[Reference/Modules/learnloop/scheduling/intent/model|learnloop.scheduling.intent.model]] — imports `CHOICE_LABEL`, `DEADLINE_CHANGE_REASON`, `choice_for`; calls `choice_for`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `load_snapshots`; calls `load_snapshots`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `yaml_to_string`; calls `read_yaml`, `yaml_to_string`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `os`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/intent|learnloop_sidecar.handlers.intent]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f8_a_deadline_covers_its_own_los_not_others_on_the_same_concept`
  - `test_f9_a_crash_between_publishing_and_linking_is_recovered_without_an_orphan`
  - `test_f9_concurrent_writers_publish_one_goal_and_one_link`
- [tests/test_intent_fix_round5.py](../../../../../../tests/test_intent_fix_round5.py) — direct import
  - `test_f17_moving_a_deadline_after_a_depth_change_updates_the_goal_target`
  - `test_f17_moving_a_deadline_at_the_same_depth_keeps_its_target`
- [tests/test_intent_goal_deadline.py](../../../../../../tests/test_intent_goal_deadline.py) — direct import
  - `test_a_deadline_creates_a_learner_goal_linked_by_goal_id`
  - `test_a_deadline_needs_an_active_depth_setting`
  - `test_linking_a_deadline_does_not_move_the_choice_time`
  - `test_moving_the_deadline_updates_the_same_goal`

## Modification guidance

- Make changes here when the responsibility remains deadline within learnloop.intent; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/intent/deadline.py](../../../../../../src/learnloop/intent/deadline.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
