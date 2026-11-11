---
title: ADR-018 The Codex transport is retired
aliases:
  - Codex retired
  - Codex transport retired
status: active
doc_version: 1.0.0
implementation_version: mvp-0.58
decision_date: 2026-10-21
decision_status: accepted
supersedes: ADR-011 Retain legacy HTTP as a narrow capability
last_reviewed: 2026-11-10
source_commit: 88607cb3fe54de8670458338c0d199e0076e662f
source_commit_timestamp: "2026-11-10T19:50:49-05:00"
source_paths:
  - src/learnloop/ai/agent_harness.py
  - src/learnloop/ai/client.py
  - src/learnloop/ai/runtime.py
  - src/learnloop/config/compat.py
  - src/learnloop/ops/plan_transport.py
  - tests/test_codex_transport_retired.py
  - tests/test_plan_first_transport.py
  - tests/http_provider_double.py
  - docs/reviews/refactor-c4.md
tags:
  - learnloop/decision
  - learnloop/ai
  - learnloop/compatibility
---

# ADR-018 The Codex transport is retired

## Context

LearnLoop once served model calls through the Codex agent harness: the Codex SDK's app-server (`codex_sdk` profiles) and an endpoint-per-operation HTTP adapter in front of one (`http`, [[ADR-011 Retain legacy HTTP as a narrow capability]]). The harness runs tools, and four security reviews of its lockdown kept finding agent features to switch off. On 2026-10-21 the owner moved every serving route to LearnLoop's own tool-free ChatGPT-plan client (plan-first transport), kept Codex behind an explicit `ai.agent_harness_opt_in`, and decided to retire the Codex code afterwards.

## Decision

Delete the transport: `ai/providers/codex.py`, `codex_http.py` and `codex_lockdown.py`, the `CodexConfig` runtime view and the opt-in (refactor C4). The ChatGPT plan and OpenRouter are the serving transports.

What stays is what old data and old configs need:

- The `codex_sdk` and `http` profile types and the code-default `codex`, `codex_low`, `codex_medium` and `codex_luna` profiles, so an old `learnloop.toml` that names one still loads and reads as the refusal of `learnloop.ai.agent_harness` (client factory, readiness, routing, the desktop's provider list), never as "not configured". A Codex profile is never a fallback.
- `learnloop doctor` reports every setting that pins a Codex profile and `doctor --fix` moves it to the plan profile of the same tier.
- An old top-level `[codex]` table still loads to the same profile.
- Stored rows keep their labels: `grading_source = "codex"` is the label of model grading for every transport, and replay reads it, never the provider; receipts and agent runs that name a Codex provider still read and display.

## Consequences

- No serving transport runs tools. An import-linter contract (`nothing-imports-the-codex-sdk`) refuses a new import of the Codex SDK or its CLI.
- An `ai.agent_harness_opt_in = true` left in a config is ignored: Codex no longer serves even there.
- The end-to-end tests keep the HTTP adapter's client as their in-process model (`tests/http_provider_double.py`), installed by a fixture for one test at a time.

## Enforcement

`tests/test_codex_transport_retired.py` loads an old config naming Codex in every way and checks each entry's refusal, the legacy table's profile and that a Codex-graded attempt replays identically; `tests/test_plan_first_transport.py` checks that no task under any routing value, fallback or override resolves to Codex. See [[AI Architecture#Provider implementations]].
