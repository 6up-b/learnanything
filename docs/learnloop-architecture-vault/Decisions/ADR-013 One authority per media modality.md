---
title: ADR-013 One authority per media modality
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-09-02
decision_status: accepted
last_reviewed: 2026-09-02
source_paths:
  - src/learnloop/config/schema.py
  - src/learnloop/config/compat.py
  - src/learnloop/ai/native_media.py
  - src/learnloop/content/pipeline/jobs.py
  - src/learnloop_sidecar/handlers/settings.py
tags:
  - learnloop/decision
  - learnloop/ingest
  - learnloop/configuration
---

# ADR-013 One authority per media modality

## Context

Native PDF ingestion (sending the file to the routed chat provider) depended on four independent switches: the `[ingest.native]` master gate, its `pdf` flag, `[ingest.pdf] engine = "native"`, and the provider profile's `input_modalities`. The desktop exposed only the first, so the Settings toggle did nothing for PDFs, a per-run `native` engine was silently dropped, the legacy CLI path silently substituted a local engine, and PDF and audio failed differently (PDF fail-closed and retried forever, audio fell back silently).

## Decision

Each media modality has exactly one authority in its own table: `[ingest.pdf] engine` and `[ingest.audio] mode`. `[ingest.native]` keeps only shared limits (`max_pdf_mb`, `max_audio_mb`) and the `fallback_when_unavailable` opt-in; the retired gates are normalized one way in `config.compat`. Readiness ("can this modality go natively?") is one pure function in `learnloop.ai.native_media`, consumed by extraction identity, extraction, the sidecar settings payload, and enqueue-time checks. Capability is declared per profile (`input_modalities`), never probed at run time; OpenRouter's public model catalog may *propose* a declaration through the settings surface.

## Consequences

- An explicit native choice that cannot run fails loudly with a typed, non-retryable error (or, with the opt-in, takes the non-native path with a health flag) — for both modalities.
- The Settings screen shows the same readiness the import will apply, per modality, with the reason.
- Future modalities (image, video) add a `mode` beside their own settings and a readiness entry; nothing reintroduces a master gate.

## Alternatives considered

- Keep `[ingest.native]` as a gate with per-modality sub-tables: rejected because `engine = "native"` already existed as the PDF authority in the schema, DTOs, RPC params and CLI, and a second PDF switch was exactly the two-authority bug.
- Runtime capability probing: rejected because extraction identity must be deterministic and offline tests honest ([[AI Architecture]]).

## Enforcement

`tests/test_native_media_readiness.py`, the native blocks of `tests/test_ingest_runner.py`, `tests/test_settings_sidecar.py`, and `tests/test_config_refactor.py` (legacy-gate normalization).

## Related notes

- [[Content Pipeline]]
- [[Privacy and Trust Boundaries]]
- [[Legacy Configuration Compatibility]]
- [[Configure AI Providers]]
