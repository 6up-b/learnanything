---
title: "learnloop.ops.plan_transport"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/plan_transport.py"
source_paths:
  - "src/learnloop/ops/plan_transport.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.plan_transport module"
  - "src/learnloop/ops/plan_transport.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.plan_transport`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.plan_transport` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: Plan-first transport T1: the vault settings that still pin the Codex harness.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/plan_transport.py](../../../../../../src/learnloop/ops/plan_transport.py) |
| Source lines | 179 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CodexPin` ([source](../../../../../../src/learnloop/ops/plan_transport.py), line 36) — One setting of ``learnloop.toml`` that names a Codex profile, and its rewrite.
  - `as_dict(self) -> dict[str, Any]` (line 44; public)
- `codex_pins(root: Path, config: LearnLoopConfig) -> list[CodexPin]` ([source](../../../../../../src/learnloop/ops/plan_transport.py), line 70) — Every setting written in ``root/learnloop.toml`` that names a Codex profile.
- `finding_message(pin: CodexPin) -> str` ([source](../../../../../../src/learnloop/ops/plan_transport.py), line 114)
- `metered_fallback_message(config: LearnLoopConfig) -> str | None` ([source](../../../../../../src/learnloop/ops/plan_transport.py), line 127) — Why ``ai.fallback_provider`` is not used while the ChatGPT plan serves, or ``None`` (review F1).
- `fix_codex_pins(root: Path, config: LearnLoopConfig, *, dry_run: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ops/plan_transport.py), line 160) — Rewrite every :func:`codex_pins` setting in place (comments and layout kept).

### Module constants

- `FINDING_CODE` ([src/learnloop/ops/plan_transport.py](../../../../../../src/learnloop/ops/plan_transport.py), line 32)
- `METERED_FALLBACK_CODE` ([src/learnloop/ops/plan_transport.py](../../../../../../src/learnloop/ops/plan_transport.py), line 124)

### Explicit exports

`__all__` declares:

- `CodexPin`
- `FINDING_CODE`
- `METERED_FALLBACK_CODE`
- `codex_pins`
- `finding_message`
- `fix_codex_pins`
- `metered_fallback_message`

## Internal implementation anchors

- `_is_codex(config: LearnLoopConfig, name: str) -> bool` ([source](../../../../../../src/learnloop/ops/plan_transport.py), line 48)
- `_plan_profile_for(config: LearnLoopConfig, name: str, task: str | None=None) -> str` ([source](../../../../../../src/learnloop/ops/plan_transport.py), line 52) — The plan profile of the same tier as Codex profile ``name`` (on route ``task``).
- `_plan_entries(config: LearnLoopConfig) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/ops/plan_transport.py), line 154)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `fix_codex_pins`; statically calls `fix_codex_pins`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `FINDING_CODE`, `METERED_FALLBACK_CODE`, `codex_pins`, `finding_message`, `metered_fallback_message`; statically calls `codex_pins`, `finding_message`, `metered_fallback_message`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/agent_harness|learnloop.ai.agent_harness]] — imports `is_agent_harness_profile`; calls `is_agent_harness_profile`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/routes|learnloop.ai.chatgpt_plan.routes]] — imports `plan_profiles`; calls `plan_profiles`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `MANUAL_PROVIDER`, `is_plan_profile`; calls `is_plan_profile`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `CHATGPT_LOW_PROVIDER`, `CHATGPT_MEDIUM_PROVIDER`, `CODEX_PROVIDER_NAMES`, `CODEX_TO_PLAN_PROFILE`, `LEGACY_CODEX_TASK_ROUTES`
- [[Reference/Modules/learnloop/ops/settings_store|learnloop.ops.settings_store]] — imports `apply_config_updates`; calls `apply_config_updates`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `tomllib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_doctor_reports_each_pinned_codex_setting_and_fix_rewrites_it`
  - `test_f1_a_configured_metered_fallback_provider_is_never_used_silently_for_a_plan_route`
  - `test_f5_doctor_fix_keeps_the_tier_of_a_legacy_codex_route_value`

## Modification guidance

- Make changes here when the responsibility remains plan transport within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/plan_transport.py](../../../../../../src/learnloop/ops/plan_transport.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
