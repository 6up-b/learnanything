---
title: "learnloop.adaptive_difficulty.spend"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/spend.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/spend.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.spend module"
  - "src/learnloop/adaptive_difficulty/spend.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.spend`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.spend` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: AD1's paid work under one daily cap (spec §11.4 ``daily_spend_cap_usd``; handoffs §0 rule 6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/spend.py](../../../../../../src/learnloop/adaptive_difficulty/spend.py) |
| Source lines | 46 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `models_off() -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/spend.py), line 33)
- `ad_envelope(vault: Any, repository: Any, *, clock: Clock | None=None) -> SharedDailyEnvelope` ([source](../../../../../../src/learnloop/adaptive_difficulty/spend.py), line 37)

### Module constants

- `ENVELOPE` ([src/learnloop/adaptive_difficulty/spend.py](../../../../../../src/learnloop/adaptive_difficulty/spend.py), line 23)
- `FORECAST_OWNER_KIND` ([src/learnloop/adaptive_difficulty/spend.py](../../../../../../src/learnloop/adaptive_difficulty/spend.py), line 25)
- `AUDIT_OWNER_KIND` ([src/learnloop/adaptive_difficulty/spend.py](../../../../../../src/learnloop/adaptive_difficulty/spend.py), line 26)
- `RELATEDNESS_OWNER_KIND` ([src/learnloop/adaptive_difficulty/spend.py](../../../../../../src/learnloop/adaptive_difficulty/spend.py), line 28)
- `OWNER_KINDS` ([src/learnloop/adaptive_difficulty/spend.py](../../../../../../src/learnloop/adaptive_difficulty/spend.py), line 29)
- `MODELS_ENV` ([src/learnloop/adaptive_difficulty/spend.py](../../../../../../src/learnloop/adaptive_difficulty/spend.py), line 30)

### Explicit exports

`__all__` declares:

- `AUDIT_OWNER_KIND`
- `ENVELOPE`
- `FORECAST_OWNER_KIND`
- `MODELS_ENV`
- `OWNER_KINDS`
- `RELATEDNESS_OWNER_KIND`
- `ad_envelope`
- `models_off`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `ad_envelope`; statically calls `ad_envelope`
- [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]] — imports `module`; statically calls `models_off`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `module`; statically calls `ad_envelope`, `models_off`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `module`; statically calls `ad_envelope`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `module`; statically calls `ad_envelope`, `models_off`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `module`; statically calls `ad_envelope`, `models_off`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness_jobs|learnloop.adaptive_difficulty.relatedness_jobs]] — imports `module`; statically calls `models_off`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `models_off`; statically calls `models_off`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `models_off`; statically calls `models_off`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SharedDailyEnvelope`, `midnight`; calls `SharedDailyEnvelope`, `midnight`

### Platform and third-party dependencies

- Standard library: `__future__`, `os`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]], [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_commission_queued_before_models_go_off_waits_and_resumes`
- [tests/test_ad23_owner_decisions.py](../../../../../../tests/test_ad23_owner_decisions.py) — direct import
  - `test_a_cancelled_commission_stays_cancelled_when_models_come_back_on`
  - `test_a_commission_waiting_on_models_stays_open_and_a_cancelled_one_expires`

## Modification guidance

- Make changes here when the responsibility remains spend within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/spend.py](../../../../../../src/learnloop/adaptive_difficulty/spend.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
