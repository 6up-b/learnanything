---
title: "Environment and Machine Settings"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-17"
aliases:
  - "settings.env"
  - "AI defaults TOML"
  - "dotenv precedence"
source_paths:
  - "src/learnloop/config/loader.py"
  - "src/learnloop/ops/settings_store.py"
  - "src/learnloop/ai/routing.py"
  - "src/learnloop/ai/runtime.py"
  - "src/learnloop_sidecar/handlers/settings.py"
  - "tests/test_ai_runtime.py"
  - "tests/test_settings_store.py"
tags:
  - "learnloop/configuration/environment"
  - "learnloop/configuration/secrets"
  - "learnloop/status/active"
---

# Environment and Machine Settings

Machine-specific paths, secrets, and provider overrides live outside [[learnloop.toml]]. This keeps a portable vault free of credentials while allowing each process and machine to supply its own execution environment. ^machine-settings-purpose

## Precedence

1. Variables already present in the process environment.
2. `<vault>/.env`.
3. Machine-global `settings.env`.

The first value wins because `load_dotenv()` never overwrites a key already in `os.environ`. The vault dotenv is loaded before the global file.

## Global file locations

The base directory resolves as:

1. `LEARNLOOP_CONFIG_DIR`, if set;
2. otherwise `XDG_CONFIG_HOME/learnloop`;
3. otherwise `~/.config/learnloop`.

Files beneath that base:

- `settings.env` — machine secrets and paths;
- `ai_defaults.toml` — the explicit AI selection/profile subset inherited by future vaults.

`ai_defaults.toml` is not a second effective-config layer during ordinary loading. It is an initialization source: a new vault inherits its explicitly persisted non-Codex AI selection when no open-vault inheritance succeeds. See [[Initialization#AI-settings inheritance]].

## Dotenv grammar

The loader accepts blank lines, `#` comments, optional `export `, valid shell-style key names, simple quoted values, and inline comments. It does not perform shell expansion. The settings writer preserves unrelated lines, writes atomically, rejects newlines in values, and best-effort applies mode `0600`.

```dotenv
LEARNLOOP_CODEX_CHECKOUT_PATH=/absolute/path/to/codex
OPENROUTER_API_KEY=replace-with-secret
DEEPSEEK_API_KEY=replace-with-secret
LEARNLOOP_TRANSCRIPTION_API_KEY=replace-with-secret
```

> [!warning] A running process already owns its environment
> Reloading dotenv cannot overwrite an old in-process value. Settings handlers that change a secret also update `os.environ` immediately; otherwise a restart would be required.

## Important variables

| Variable | Function |
|---|---|
| `LEARNLOOP_AI_PROVIDER` | Provider selection override after an explicit CLI/provider flag and before task route/active provider |
| `LEARNLOOP_CODEX_CHECKOUT_PATH` | Machine override for Codex profiles' checkout path |
| `OPENROUTER_API_KEY` | Default OpenRouter secret |
| `DEEPSEEK_API_KEY` | Seeded DeepSeek-compatible profile secret |
| `OPENAI_API_KEY` | Default secret for generic OpenAI-compatible profiles when no `api_key_env` is supplied |
| `LEARNLOOP_TRANSCRIPTION_API_KEY` | Direct endpoint transcription secret |
| `LEARNLOOP_PDF_LLM_API_KEY` | Optional Marker/PDF LLM service secret |
| `LEARNLOOP_CONFIG_DIR` | Overrides the machine-global settings directory |
| `XDG_CONFIG_HOME` | Supplies the standard config root when no LearnLoop override exists |
| `LEARNLOOP_MARKER_PROVIDER` | Chooses local Marker or Datalab extraction |
| `DATALAB_API_KEY` | Datalab extraction secret |
| `LEARNLOOP_DATALAB_TIMEOUT_SECS` | Datalab request timeout override |

Desktop/sidecar process controls such as `LEARNLOOP_SIDECAR_LOG_LEVEL`, `LEARNLOOP_SIDECAR_DEBUG`, `LEARNLOOP_SIDECAR_DEBUG_LOG`, and `LEARNLOOP_SIDECAR_TIMEOUT_SECS` affect the adapter process rather than the typed vault configuration.

## Security and portability guidance

- Keep `.env` and `settings.env` out of source control.
- Store only environment-variable names such as `api_key_env` in TOML.
- Prefer global settings for secrets shared by vaults and vault `.env` only when a vault genuinely needs a different credential.
- Use a shell variable for one-off provider experiments.
- Run `learnloop doctor --ai --vault /path/to/vault` only when provider diagnostics are wanted; plain doctor stays provider-independent and database-read-only.

