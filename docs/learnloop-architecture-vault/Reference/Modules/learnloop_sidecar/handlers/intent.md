---
title: "learnloop_sidecar.handlers.intent"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/intent.py"
source_paths:
  - "src/learnloop_sidecar/handlers/intent.py"
source_commit: "0fc6e3e96f73e725ecc0505e16fc9c79902a881c"
source_commit_timestamp: "2026-10-20T01:23:55-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.intent module"
  - "src/learnloop_sidecar/handlers/intent.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.intent`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.intent` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Daily-loop DL2 RPCs: the single intent control (spec §5.2) and deadlines (§5.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/intent.py](../../../../../../src/learnloop_sidecar/handlers/intent.py) |
| Source lines | 104 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0fc6e3e96f73e725ecc0505e16fc9c79902a881c` |
| Commit timestamp | `2026-10-20T01:23:55-04:00` |

## Public API

- `class IntentScopeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/intent.py), line 32)
- `class SetIntentInput(IntentScopeInput)` ([source](../../../../../../src/learnloop_sidecar/handlers/intent.py), line 37)
- `class SetIntentDeadlineInput(IntentScopeInput)` ([source](../../../../../../src/learnloop_sidecar/handlers/intent.py), line 41)
- `get_intent(ctx: SidecarContext, params: IntentScopeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/intent.py), line 65)
- `set_intent(ctx: SidecarContext, params: SetIntentInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/intent.py), line 77)
- `set_intent_deadline(ctx: SidecarContext, params: SetIntentDeadlineInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/intent.py), line 90)

### Module constants

- `INTENT_RPCS` ([src/learnloop_sidecar/handlers/intent.py](../../../../../../src/learnloop_sidecar/handlers/intent.py), line 29)

### Explicit exports

`__all__` declares:

- `INTENT_RPCS`

## Internal implementation anchors

- `_scope(params: IntentScopeInput) -> Scope` ([source](../../../../../../src/learnloop_sidecar/handlers/intent.py), line 45)
- `_describe(vault: Any, repository: Any, scope: Scope) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/intent.py), line 51)
- `_require_enabled(vault: Any) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/intent.py), line 55)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]] — imports `cost_function`; calls `cost_function`
- [[Reference/Modules/learnloop/intent/control|learnloop.intent.control]] — imports `IntentControlError`, `Scope`, `apply_choice`, `describe`; calls `Scope`, `apply_choice`, `describe`
- [[Reference/Modules/learnloop/intent/deadline|learnloop.intent.deadline]] — imports `set_deadline`; calls `set_deadline`
- [[Reference/Modules/learnloop/scheduling/intent/model|learnloop.scheduling.intent.model]] — imports `SCOPE_KINDS`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `intent_enabled`; calls `intent_enabled`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_intent_codex_rereview.py](../../../../../../tests/test_intent_codex_rereview.py) — direct import
  - `test_f2_the_intent_control_is_off_below_the_tag`
- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/intent.py](../../../../../../src/learnloop_sidecar/handlers/intent.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
