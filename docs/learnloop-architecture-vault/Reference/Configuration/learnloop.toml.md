---
title: "learnloop.toml"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
config_schema_version: 2
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-17"
aliases:
  - "Vault TOML"
  - "LearnLoop TOML"
source_paths:
  - "src/learnloop/config/template.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/config/loader.py"
  - "src/learnloop/vault/loader.py"
  - "tests/test_config_refactor.py"
  - "tests/test_init.py"
tags:
  - "learnloop/configuration/file"
  - "learnloop/configuration/schema-v2"
  - "learnloop/status/active"
---

# `learnloop.toml`

`learnloop.toml` is the required vault marker and the per-vault configuration file. [[Initialization]] writes it once and never overwrites an existing copy. Vault discovery walks upward until it finds this filename. ^toml-identity

## Generated template

```toml
schema_version = 2

[storage]
sqlite_path = "state.sqlite"

[algorithms]
algorithm_version = "mvp-0.9"

# AI is optional; an unavailable provider keeps today's manual workflow.
# Precedence: explicit flag > LEARNLOOP_AI_PROVIDER > task route > active provider.
[ai]
active_provider = "codex"
fallback_provider = ""

[ai.providers.codex]
type = "codex_sdk"
model = "gpt-5.6-sol"
reasoning_effort = "low"
# checkout_path / revision / sdk_python_path may be set for a non-default checkout.

[ai.providers.openrouter]
type = "openrouter"
model = "deepseek/deepseek-chat"
api_key_env = "OPENROUTER_API_KEY"
response_format = "json_object"
timeout_seconds = 180
# input_modalities = ["audio", "pdf"]

[ai.routing]
grading = "codex_low"
canonical_ingest = "codex_medium"
canonical_ingest_retry = "codex_medium"
authoring = "codex_medium"
tutor_qa = "codex_low"
teach_back = "codex_low"
rung_variant = "codex_low"
animation = "codex_medium"
transcription = ""

[ingest]
[ingest.pdf]
engine = "auto" # auto | marker | pypdf | native (send the PDF to the ingest model)

[animation]
enabled = true

# All other policy uses modeled defaults. Inspect it with:
#   learnloop config effective
# Override any modeled key by adding it under the same TOML path.
```

This is copied from `DEFAULT_CONFIG_TEXT`; the template is constrained to remain decision-only and under 80 lines by `tests/test_config_refactor.py`.

## Explicit decisions

| Path | New-vault value | Function |
|---|---|---|
| `schema_version` | `2` | Selects the canonical config shape |
| `storage.sqlite_path` | `state.sqlite` | Locates machine state relative to the vault root unless absolute |
| `algorithms.algorithm_version` | `mvp-0.9` | Selects current learning/projection semantics |
| `ai.active_provider` | `codex` | Default provider after explicit/env/task-route precedence |
| `ai.fallback_provider` | empty | No configured fallback profile |
| `ai.providers.codex.*` | SDK, GPT-5.6, low | Seed profile; see [[AI Architecture]] |
| `ai.providers.openrouter.*` | OpenRouter profile | Optional configured profile; secret is indirect |
| `ai.routing.*` | low/medium profiles | Per-workflow provider selection |
| `ingest.pdf.engine` | `auto` | PDF extraction choice; `native` sends the whole PDF to the ingest model (external data flow) |
| `ingest.audio.mode` | `transcription` | Audio path; `native` sends mp3/wav to the ingest model (external data flow) |
| `animation.enabled` | `true` | Makes animation available; each render still requires consent |

Every other current default is enumerated in [[Configuration Field Catalog]].

## Minimal overrides

Change only a scheduler value:

```toml
[scheduler]
short_session_minutes = 30
```

Select a different existing provider profile for grading:

```toml
[ai.routing]
grading = "deepseek_flash"
```

Move SQLite into a vault-relative data directory:

```toml
[storage]
sqlite_path = ".learnloop/data/state.sqlite"
```

> [!warning] Moving the path does not move an existing file
> Change management must deliberately relocate the database and preserve the vault-level lock identity. See [[Database#The live persistence path]].

## Editing and validation

The desktop settings store uses `tomlkit` to preserve comments and layout, writes a temporary sibling, and atomically replaces the file. Manual edits are supported; validate the result with:

```bash
learnloop config effective --vault /path/to/vault --json
learnloop doctor --vault /path/to/vault --json
```

Malformed TOML produces `ConfigLoadError` with path context. On Windows, Codex path errors additionally explain how TOML double-quoted backslashes become escapes; prefer forward slashes or single-quoted strings.

> [!danger] Never put secrets here
> Provider profiles store the **name** of an environment variable (`api_key_env`), not its value. Use [[Environment and Machine Settings]].

