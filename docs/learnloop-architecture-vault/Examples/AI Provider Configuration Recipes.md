---
title: AI Provider Configuration Recipes
aliases:
  - Provider Recipes
  - AI Config Examples
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/config/template.py
  - src/learnloop/config/loader.py
  - src/learnloop/ai/routing.py
  - src/learnloop/ai/runtime.py
  - tests/test_openai_chat_client.py
  - tests/test_ai_runtime.py
tags:
  - learnloop/example
  - learnloop/ai
  - learnloop/configuration
---

# AI Provider Configuration Recipes

Choose one recipe, then verify the exact profile. Provider semantics and the full precedence rule are authoritative at [[Configure AI Providers#Understand selection precedence]] and [[AI Architecture]].

## Generated Codex profile

Fresh vaults contain a `codex` provider profile. Inspect, do not duplicate it:

```bash
uv run learnloop config effective --json --vault "$VAULT"
uv run learnloop doctor --ai --ai-provider codex --json --vault "$VAULT"
```

Proceed only when `ai_runtime.ready` is `true` and the returned profile/model are the intended ones.

## OpenAI-compatible profile

Edit the existing `[ai]` and `[ai.routing]` values, and add the new `[ai.providers.deepseek_flash]` table. The combined result should contain the fragment below, with endpoint/model names changed to values actually supported by the service. Do **not** append duplicate `[ai]` or `[ai.routing]` table headers to the generated TOML.

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

In `$VAULT/.env`:

```dotenv
DEEPSEEK_API_KEY=replace-with-real-secret
```

> [!warning] Secret handling
> Keep `.env` out of commits, examples, bug reports, and Obsidian transclusions. `learnloop.toml` stores only the environment-variable name.

Verify:

```bash
uv run learnloop config effective --json --vault "$VAULT"
uv run learnloop doctor --ai \
  --ai-provider deepseek_flash \
  --json --vault "$VAULT"
```

If the key is missing, the expected status is `provider_auth_required`, not a generic vault failure.

## OpenRouter profile

Use provider type `openrouter`, a named `api_key_env` such as `OPENROUTER_API_KEY`, and the desired OpenRouter model. The generated template is the best current field reference:

```bash
rg -n 'openrouter|OPENROUTER_API_KEY' "$VAULT/learnloop.toml"
uv run learnloop doctor --ai --ai-provider openrouter --json --vault "$VAULT"
```

The second command explicitly tests this profile even when another route is active.

## Manual mode

For one process:

```bash
LEARNLOOP_AI_PROVIDER=manual \
  uv run learnloop doctor --ai --json --vault "$VAULT"
```

Verified state:

```json
{
  "ai_runtime": {
    "provider": "manual",
    "ready": false,
    "status": "provider_unavailable",
    "message": "Manual mode selected; AI is disabled for this workflow."
  }
}
```

This is expected. Follow [[Manual Attempt and State Inspection]] for an ordinary self-grade. Do not use it for held-out exams, qualifying diagnostics, or teach-back grading.

## Temporary explicit override

Commands that expose `--ai-provider` can test a profile without changing routes:

```bash
uv run learnloop synthesize <source-set-id> \
  --ai-provider codex --json --vault "$VAULT"
```

Because this is explicit, a configured fallback does not silently replace it. This makes verification reproducible.

## Final readiness checklist

- effective config shows the intended profile and route;
- credential is resolved without printing it;
- doctor reports the correct provider/model;
- required workflows are not routed to manual;
- a failed call leaves an inspectable `agent_runs` receipt as described in [[Process Model Output]].

^provider-recipe-checklist
