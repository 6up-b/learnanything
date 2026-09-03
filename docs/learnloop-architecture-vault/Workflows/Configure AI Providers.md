---
title: Configure AI Providers
aliases:
  - AI Readiness Workflow
  - Manual Provider Workflow
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/ai/routing.py
  - src/learnloop/ai/runtime.py
  - src/learnloop/config/loader.py
  - src/learnloop/config/schema.py
  - src/learnloop/config/template.py
  - src/learnloop/ops/doctor.py
  - tests/test_ai_runtime.py
  - tests/test_openai_chat_client.py
  - tests/test_provider_resolution_parity.py
tags:
  - learnloop/workflow
  - learnloop/ai
  - learnloop/configuration
---

# Configure AI Providers

Use this workflow to select a provider profile, store its credential outside versioned TOML, and test the exact route LearnLoop will use. The provider abstraction, transport contract, and failure taxonomy live in [[AI Architecture]]; this note only covers operator actions.

## 1. Inspect the effective configuration

```bash
VAULT="$HOME/LearnLoop/linear-algebra"
uv run learnloop config effective --json --vault "$VAULT"
uv run learnloop doctor --ai --json --vault "$VAULT"
```

The generated configuration normally selects the `codex` profile. A ready result contains an `ai_runtime` object with `ready: true`, `status: "ready"`, the resolved provider type, and model.

> [!info] Readiness is route-specific
> `doctor --ai` tests provider composition, authentication, and model configuration. It does not prove that a later answer will pass a feature validator. Grading, canonical ingestion, authoring, tutor, and teach-back can route to different profiles.

## Understand selection precedence

For a command that accepts `--ai-provider`, resolution is:

1. the explicit command option;
2. `LEARNLOOP_AI_PROVIDER` in the process environment;
3. the task entry in `[ai.routing]`;
4. `[ai].active_provider`.

An explicit command option or environment override is an intentional hard selection: LearnLoop does not silently replace it with the configured fallback. Otherwise, `fallback_provider` may be used when the normal selected provider is unavailable.

^provider-precedence

## 3. Choose one of three operating modes

### Generated Codex profile

Keep the default `[ai.providers.codex]` profile and check it directly:

```bash
uv run learnloop doctor --ai --ai-provider codex --json --vault "$VAULT"
```

### OpenAI-compatible or OpenRouter profile

Add a named profile and point individual tasks at it by editing the existing `[ai]` and `[ai.routing]` tables (never append duplicate TOML table headers). This minimal combined fragment is expanded in [[AI Provider Configuration Recipes]]:

```toml
[ai]
active_provider = "deepseek_flash"
fallback_provider = "manual"

[ai.providers.deepseek_flash]
type = "openai_chat"
base_url = "https://api.deepseek.com"
api_key_env = "DEEPSEEK_API_KEY"
model = "deepseek-v4-flash"
response_format = "json_object"
thinking = "disabled"

[ai.routing]
grading = "deepseek_flash"
canonical_ingest = "deepseek_flash"
authoring = "deepseek_flash"
tutor_qa = "deepseek_flash"
teach_back = "deepseek_flash"
```

Put the secret in the vault's uncommitted `.env`, not `learnloop.toml`:

```dotenv
DEEPSEEK_API_KEY=replace-with-real-secret
```

Credential precedence is the existing shell environment, then `<vault>/.env`, then `~/.config/learnloop/settings.env`. Existing shell values are never overwritten by an env file.

### Declare input modalities

A provider profile lists the media it accepts natively under `input_modalities` (values: `audio`, `pdf`, `image`, `video`); native ingestion trusts only this declaration, never a runtime probe, so extraction identity stays deterministic offline.

```toml
[ai.providers.openrouter_ingest]
type = "openrouter"
model = "google/gemini-2.5-pro"
input_modalities = ["audio", "pdf", "image"]
```

Settings → Ingestion → *model capabilities* edits the same list: OpenAI-compatible profiles get checkboxes; OpenRouter profiles get **detect**, which looks the model up in OpenRouter's public model catalog (`GET /api/v1/models`, cached for 24 h under the machine config dir) and offers to apply what it finds. Choosing a native PDF/audio path for an OpenRouter route that has no declaration adopts the cached catalog entry automatically, without a network call.

### Typed manual mode

Use the profile explicitly for a single ordinary attempt:

```bash
LEARNLOOP_AI_PROVIDER=manual \
  uv run learnloop doctor --ai --json --vault "$VAULT"
```

Expected runtime state is `provider_unavailable` with a message that manual mode disables AI. That does **not** make the vault unhealthy; it is the typed no-client path.

> [!warning] Manual-mode boundary
> Ordinary practice can accept explicit criterion scores and records `grading_source = self`. Qualifying diagnostics, held-out exam answers, and teach-back transcript grading require a ready model and fail closed instead of inventing evidence.

## 4. Test the route that matters

```bash
# Default/active route
uv run learnloop doctor --ai --json --vault "$VAULT"

# A named profile, without changing config
uv run learnloop doctor --ai --ai-provider openrouter --json --vault "$VAULT"
```

For an OpenRouter profile with no credential, expect `status: "provider_auth_required"` and the configured `api_key_env` name. Fix the environment, open a new process if necessary, and repeat the same command.

## 5. Verify per-feature behavior

- canonical synthesis: run `source-coverage` first, then `synthesize ... --ai-provider <profile>`; see [[Build a Study Map]].
- grading: submit one non-diagnostic item and inspect `grading_source`; see [[Process Model Output]].
- tutor and teach-back: open their desktop surfaces; see [[Tutor and Teach-Back Workflow]].
- manual grading: follow [[Manual Attempt and State Inspection]].

> [!failure] Common configuration trap
> A provider can be valid yet not selected. Run `config effective --json`, then compare the task's `[ai.routing]` entry with the precedence rule above. Do not debug the model named in `active_provider` when an environment override selected another profile.

## Observable state

Provider configuration is in `learnloop.toml`; credentials may be in `.env` or global settings. Every real model call creates an `agent_runs` receipt and later transitions it to completion or failure. Manual mode creates no model client.

## Related notes

- [[AI Architecture]]
- [[Configuration]]
- [[Process Model Output]]
- [[AI Provider Configuration Recipes]]
