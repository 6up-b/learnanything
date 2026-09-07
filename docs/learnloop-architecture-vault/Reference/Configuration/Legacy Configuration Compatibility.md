---
title: "Legacy Configuration Compatibility"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
config_schema_version: 2
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-17"
aliases:
  - "Config normalization"
  - "Schema v1 compatibility"
source_paths:
  - "src/learnloop/config/compat.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/config/loader.py"
  - "tests/test_config_refactor.py"
  - "tests/test_ai_config.py"
tags:
  - "learnloop/configuration/compatibility"
  - "learnloop/status/active"
---

# Legacy Configuration Compatibility

Legacy input is translated **one way** into the canonical typed model before runtime consumers see it. Canonical values win when both forms are present, normalization is idempotent, and retired values do not reappear in serialized effective configuration. ^compat-direction

## Accepted schema generations

`schema_version = 1` and `schema_version = 2` both validate. New vaults emit v2. Compatibility changes parsing, not the selected learning algorithm: an old file that omits `algorithms.algorithm_version` keeps the model's `mvp-0.6` legacy fallback until an explicit upgrade.

## Canonical translations

| Legacy input | Canonical result | Precedence |
|---|---|---|
| `[codex]` | `[ai.providers.codex]` typed as SDK or HTTP | Existing canonical provider wins |
| provider type `codex_http` / `http_adapter` | `type = "http"` | Normalized before union discrimination |
| provider type `openai_compatible` | `type = "openai_chat"` | Normalized before union discrimination |
| provider without `type` | `codex_sdk` | Preserves old custom Codex profiles |
| Codex model `gpt-5.5` | current default model/reasoning pair | Applies to canonical Codex alias normalization |
| AI route value `codex` | task-specific `codex_low` or `codex_medium` | Explicit modern route is unchanged |
| `error_impacts.*.max_sharpening` | `recall_coverage.max_error_sharpening` | Canonical destination wins |
| `[ingest.native] enabled = true` with `audio = true` | `[ingest.audio] mode = "native"` plus `[ingest.native] fallback_when_unavailable = true` (unless set) | An explicit `mode` wins; the fallback opt-in preserves the legacy gate's silent transcription when the routed model cannot take audio; the retired `pdf` flag is dropped because `[ingest.pdf] engine` is the only PDF authority |

## Legacy audio normalization

When `[ingest.audio] provider = "openrouter"` appears, loading synthesizes an `openrouter_transcription` provider from the audio model/timeout plus the base OpenRouter profile and routes `ai.routing.transcription` to it. An explicit canonical transcription route wins. Endpoint-style `openai_compatible` audio remains on the direct transcription path and creates no chat route.

This preserves independently selected transcription models without keeping a separate provider architecture. Provider execution is explained in [[AI Architecture]].

## Accepted and ignored retired keys

These values parse for old files but are removed before the runtime model is serialized:

- top-level `forecasts` and `cross_lo_propagation`;
- `probe.episode.self_graded_evidence_weight`;
- `probe.dialogue.max_turns`;
- `recall_coverage.facet_recall_prior_pseudo_count` and `coverage_epsilon`;
- `ingest.budgets.evidence_span_input_tokens`;
- `ingest.native.enabled`, `ingest.native.audio`, and `ingest.native.pdf` (translated as above, then removed);
- provider `auth_mode`.

> [!note] Parse-and-ignore is deliberate
> These knobs had no active behavioral reader or represented retired architecture. Keeping them as modeled fields would imply functionality that does not exist.

## Runtime compatibility views

`config.codex` remains a non-serialized property derived from `ai.providers.codex` for compatibility callers. Runtime code should not add new reads through this view; new provider behavior belongs to the canonical AI configuration and [[AI Architecture]].

## Modification guidance

- Add legacy handling only in `config/compat.py` or model pre-validation hooks that delegate there.
- Make transformations one-way and idempotent.
- Prefer canonical input when both old and new spellings are present.
- Add fixture-corpus equivalence coverage to `tests/test_config_refactor.py`.
- Do not silently change `algorithms.algorithm_version` during spelling normalization.

