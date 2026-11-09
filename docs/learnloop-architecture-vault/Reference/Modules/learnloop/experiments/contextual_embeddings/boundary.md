---
title: "learnloop.experiments.contextual_embeddings.boundary"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/boundary.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/boundary.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.boundary module"
  - "src/learnloop/experiments/contextual_embeddings/boundary.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.boundary`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.boundary` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: The E0 provider boundary: no provider message leaves an E0 path (fix round 4, High 8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/boundary.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py) |
| Source lines | 232 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `classify(exc: BaseException) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 42) — An allowlisted classification of a provider exception (never its text).
- `status_code(exc: BaseException) -> int | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 81)
- `request_id(exc: BaseException) -> str | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 94)
- `provider_failure(exc: BaseException) -> E0ProviderFailure` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 102) — The sanitized stand-in for a provider exception (raise it ``from None``).
- `safe_message(exc: BaseException) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 108) — What an E0 command may print for a failure: an E0 stop's own message (built from allowlisted parts), else the exception's type name only.
- `quiet_provider_logs() -> Iterator[None]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 151) — Sanitize provider log records at every handler while active (reentrant).
- `class CodexLockdownMissing(PermissionError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 180) — The Codex tool lockdown is not in force: no E0 paid run starts.
- `require_codex_lockdown() -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 184) — Refuse the paid run unless every Codex turn is the locked-down one (security lockdown 55063be64): ``learnloop.ai.providers.codex_lockdown`` must import, the Codex provider must use its ``TurnLockdown`` and approval path, and the isolated-turn overrides the provider launches ever…
- `class CodexRoleRemaining(PermissionError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 219) — An E0 role still bills a subscription (Codex) route: no paid run starts.
- `require_no_codex_roles(role_pins: Any=None) -> None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 223) — Re-plan 2026-10-22: E0 makes NO Codex call.

### Module constants

- `PROVIDER_LOGGERS` ([src/learnloop/experiments/contextual_embeddings/boundary.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 35)
- `CLASSIFICATIONS` ([src/learnloop/experiments/contextual_embeddings/boundary.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 36)
- `_SAFE_ID` ([src/learnloop/experiments/contextual_embeddings/boundary.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 38)
- `_SAFE_TEXT` ([src/learnloop/experiments/contextual_embeddings/boundary.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 39)
- `_FILTER` ([src/learnloop/experiments/contextual_embeddings/boundary.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 145)
- `_LOCK` ([src/learnloop/experiments/contextual_embeddings/boundary.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 146)
- `_ACTIVE` ([src/learnloop/experiments/contextual_embeddings/boundary.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 147)

## Internal implementation anchors

- `_chain(exc: BaseException) -> list[BaseException]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 72)
- `_looks_secret(text: str) -> bool` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 125) — A credential shape: a provider key prefix, a bearer token, or a long token.
- `class _Sanitize(logging.Filter)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py), line 132)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]] — imports `require_codex_lockdown`, `safe_message`; statically calls `require_codex_lockdown`, `safe_message`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `provider_failure`, `quiet_provider_logs`; statically calls `provider_failure`, `quiet_provider_logs`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `classify`, `quiet_provider_logs`, `require_codex_lockdown`, `require_no_codex_roles`, `safe_message`; statically calls `classify`, `quiet_provider_logs`, `require_codex_lockdown`, `require_no_codex_roles`, `safe_message`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `require_codex_lockdown`, `require_no_codex_roles`; statically calls `require_codex_lockdown`, `require_no_codex_roles`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `quiet_provider_logs`; statically calls `quiet_provider_logs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AITurnTimeout`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `module`; calls `isolated_turn_overrides`
- [[Reference/Modules/learnloop/ai/providers/codex_lockdown|learnloop.ai.providers.codex_lockdown]] — imports `module`; calls `disabled_features`, `lockdown_config_overrides`, `shell_environment_overrides`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0ProviderFailure`, `E0Stop`; calls `E0ProviderFailure`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `logging`, `pathlib`, `re`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_relabel_round.py](../../../../../../../tests/test_e0_relabel_round.py) — direct import
  - `test_the_paid_cli_passes_reuse_run_and_authorizes_on_the_cumulative_budget`
- [tests/test_e0_review_round4_followup.py](../../../../../../../tests/test_e0_review_round4_followup.py) — direct import
  - `test_the_lockdown_is_active_on_this_tree`
  - `test_the_paid_run_refuses_when_the_lockdown_is_not_importable`
- [tests/test_e0_review_round5.py](../../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_the_paid_preflight_passes_with_every_pin_verified_zero_codex_and_the_lockdown`
  - `test_the_paid_run_refuses_any_codex_role`

## Modification guidance

- Make changes here when the responsibility remains boundary within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/boundary.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/boundary.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
