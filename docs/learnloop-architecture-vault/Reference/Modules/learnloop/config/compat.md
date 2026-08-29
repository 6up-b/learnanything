---
title: "learnloop.config.compat"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/compat.py"
source_paths:
  - "src/learnloop/config/compat.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.config"
layer: "infrastructure"
concepts:
  - "Configuration"
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.config.compat module"
  - "src/learnloop/config/compat.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-config"
---

# `learnloop.config.compat`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/config/_package|learnloop.config]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.config.compat` exists within [[Reference/Modules/learnloop/config/_package|learnloop.config]] to own the behavior summarized by its module contract: One-way normalization and runtime aliases for legacy configuration.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/compat.py](../../../../../../src/learnloop/config/compat.py) |
| Source lines | 303 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class CodexConfig(BaseModel)` ([source](../../../../../../src/learnloop/config/compat.py), line 33) — Deprecated runtime view over the canonical ``ai.providers.codex`` profile.
- `discard_retired_provider_settings(data: Any) -> Any` ([source](../../../../../../src/learnloop/config/compat.py), line 62) — Drop provider keys that were parsed historically but never consumed.
- `normalize_provider_profile(value: Any) -> Any` ([source](../../../../../../src/learnloop/config/compat.py), line 72) — Canonicalize provider type aliases before union discrimination.
- `normalize_ai_input(data: Any) -> Any` ([source](../../../../../../src/learnloop/config/compat.py), line 85) — Normalize every named provider while preserving non-mapping inputs.
- `normalize_config_input(data: Any) -> Any` ([source](../../../../../../src/learnloop/config/compat.py), line 100) — Translate accepted legacy shapes into the canonical schema input.
- `ai_provider_from_codex(config: CodexConfig) -> AIProviderConfig` ([source](../../../../../../src/learnloop/config/compat.py), line 191) — Translate the deprecated Codex runtime object to a typed profile.
- `codex_config_view(config: LearnLoopConfig) -> CodexConfig` ([source](../../../../../../src/learnloop/config/compat.py), line 223) — Build the non-serialized ``config.codex`` compatibility alias.

### Module constants

- `_PROVIDER_TYPE_ALIASES` ([src/learnloop/config/compat.py](../../../../../../src/learnloop/config/compat.py), line 26)

### Explicit exports

`__all__` declares:

- `CodexConfig`
- `ai_provider_from_codex`
- `codex_config_view`
- `discard_retired_provider_settings`
- `normalize_ai_input`
- `normalize_config_input`
- `normalize_provider_profile`

## Internal implementation anchors

- `_provider_profile_from_legacy_codex(value: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/config/compat.py), line 234)
- `_profile_from_legacy_openrouter_audio(audio: dict[str, Any], providers: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/config/compat.py), line 242)
- `_normalize_codex_aliases(ai: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/config/compat.py), line 265)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `module`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `normalize_config_input`; statically calls `normalize_config_input`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `CodexConfig`, `codex_config_view`, `discard_retired_provider_settings`, `normalize_ai_input`, `normalize_config_input`; statically calls `codex_config_view`, `discard_retired_provider_settings`, `normalize_ai_input`, `normalize_config_input`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `AIProviderConfig`, `AudioIngestConfig`, `CodexHTTPProviderConfig`, `CodexSDKProviderConfig`, `DEFAULT_CODEX_MODEL`, `DEFAULT_CODEX_REASONING_EFFORT`, `DEFAULT_CODEX_TASK_ROUTES`, `LEGACY_CODEX_MODEL`, `LearnLoopConfig`, `OPENROUTER_TRANSCRIPTION_PROVIDER`, `openrouter_provider`; calls `AudioIngestConfig`, `openrouter_provider`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/config/__init__|learnloop.config]], [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]], [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_config_responsibilities_have_canonical_module_owners`

## Modification guidance

- Change configuration behavior in the schema, loader, compatibility normalizer, or template owner that matches the concern; preserve one-way legacy normalization.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/config/compat.py](../../../../../../src/learnloop/config/compat.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
