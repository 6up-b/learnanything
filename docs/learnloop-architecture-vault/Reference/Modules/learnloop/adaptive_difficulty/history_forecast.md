---
title: "learnloop.adaptive_difficulty.history_forecast"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/history_forecast.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/history_forecast.py"
source_commit: "8af1a25c40d715fd86ddaddf7e4191b6e7b30d4b"
source_commit_timestamp: "2026-11-05T00:29:18-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.adaptive_difficulty.history_forecast module"
  - "src/learnloop/adaptive_difficulty/history_forecast.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.history_forecast`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.history_forecast` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Router objective RO2: ``llm_history_v1``, the frontier LLM full-history forecaster (spec_router_objective_v1 §6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py) |
| Source lines | 559 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8af1a25c40d715fd86ddaddf7e4191b6e7b30d4b` |
| Commit timestamp | `2026-11-05T00:29:18-05:00` |

## Public API

- `class HistoryForecastV1(WireModel)` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 117) — The LLM's answer: four probabilities strictly between 0 and 1, and a short rationale.
- `forecaster_name(rung: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 127)
- `frozen_key(presentation_id: str, rung: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 131)
- `draw_key(presentation_id: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 135)
- `receipt_keys(presentation_id: str, rung: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 139) — The canonical receipt keys of one rung's call: ``now`` and ``cold_<L>``.
- `draw(presentation_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 149) — The seeded draw of the lower rung: the seed (a digest of the draw version and the presentation), ``u`` in [0, 1) and the rung of its third, each rung's propensity 1/3.
- `freeze_history_inputs(vault: Any, connection: Any, item: Any, *, presentation_id: str, served_at: str, view: Any) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 166) — In the serve transaction: the draw and the exact request inputs of its two rungs.
- `forecast_history_presentation(vault: Any, repository: Any, presentation_id: str, *, clients: Clients | None=None, clock: Clock | None=None, fence: Any=None, live_vault: Callable[[], Any] | None=None) -> list[ForecastOutcome]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 241) — ``llm_history_v1`` for one plan presentation: its frozen rungs, H3 first, each sent exactly as frozen.
- `prompt_for(state: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 304) — The request ``llm_history_v1`` sends for one frozen state (the audit's dry run plans it too).
- `call_tokens(route: Any, prompt: str) -> dict[str, int]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 525) — What one logical call on ``route`` is charged, as the paid path charges it (Codex review F5): the request is reserved at the route's own output budget (``route.output_tokens``, which :func:`sending.ask_llm` passes on), and its one allowed retry (``max_retries=1``: a provider fai…
- `expected_calls(vault: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 541) — What one eligible presentation costs (for the owner, before landing): two calls (H3 and the drawn rung), each the frozen card (at most ``history_card_token_budget`` bytes) plus the instructions in, and at most the route's output budget out (``ai.route_output_tokens.ad_forecast_l…

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 86)
- `FORECASTER` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 88)
- `CARD_VERSION` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 89)
- `PROMPT_VERSION` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 90)
- `DRAW_VERSION` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 91)
- `ANCHOR` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 92)
- `DRAWN` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 95)
- `LAGS` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 97)
- `RATIONALE_SENTENCES` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 99)
- `FROZEN_PREFIX` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 100)
- `NOW_EVENT` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 101)
- `COLD_EVENT` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 102)
- `LABEL` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 104)
- `QUESTION` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 111)
- `_ID` ([src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 339)

### Explicit exports

`__all__` declares:

- `ANCHOR`
- `CARD_VERSION`
- `COLD_EVENT`
- `DRAWN`
- `DRAW_VERSION`
- `FORECASTER`
- `HistoryForecastV1`
- `LABEL`
- `LAGS`
- `PROMPT_VERSION`
- `call_tokens`
- `draw`
- `draw_key`
- `expected_calls`
- `forecast_history_presentation`
- `forecaster_name`
- `freeze_history_inputs`
- `frozen_key`
- `prompt_for`
- `receipt_keys`

## Internal implementation anchors

- `_budget(vault: Any) -> int` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 161)
- `_frozen(connection: Any, presentation_id: str, rung: str) -> tuple[str, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 213) — ``(status, content)``: ``ok`` and the frozen inputs; ``withheld`` (frozen at another protection epoch or naming withheld material: expired, never sent); ``missing``.
- `_done(connection: Any, presentation_id: str, rung: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 235)
- `_skip_reason(exc: BaseException | None, why: str | None=None) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 317) — Why a forecast was not made, as a censoring reason.
- `_sentences(text: str) -> tuple[str, bool]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 334)
- `_validated(answer: Any) -> dict[str, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 342)
- `_ask(vault: Any, repository: Any, client: Any, *, prompt: str, owner_id: str, envelope: Any, send: SendGuard) -> tuple[Any, str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 352)
- `_receipts(*, presentation: Mapping[str, Any], content: Mapping[str, Any], drawn: Mapping[str, Any], rung: str, values: Mapping[str, float] | None, status: str, received: str, model: str | None, request_hash: str, rationale: Mapping[str, Any] | None, censor: str | None, suffix: str | None) -> list[ForecastReceipt]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 371)
- `_write(repository: Any, vault: Any, receipts: list[ForecastReceipt], *, created_at: str, payload_key: str, request: Any, response: Any, received: str, judged: Mapping[str, Any] | None, admit: Callable[[], None] | None) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 417) — One rung's payloads, its receipts and (accepted) their judgments, in one fenced transaction.
- `_forecast_rung(vault: Any, worker: Any, rung: str, presentation: Mapping[str, Any], content: Mapping[str, Any], drawn: Mapping[str, Any], *, clients: Clients, clock: Clock | None, send: SendGuard) -> ForecastOutcome` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py), line 453)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]] — imports `forecast_history_presentation`; statically calls `forecast_history_presentation`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]] — imports `module`; statically calls `_done`, `_forecast_rung`, `call_tokens`, `forecaster_name`, `prompt_for`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]] — imports `freeze_history_inputs`; statically calls `freeze_history_inputs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]] — imports `LeaseLost`, `ReceiptWriteFailed`, `claimed`, `history_key`; calls `claimed`, `history_key`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `item_revision`; calls `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `EVENT`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]] — imports `module`; calls `_size`, `build_sections`, `evidence_ids`, `rung_card`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `current_view`, `material_view`; calls `current_view`, `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`, `epoch_of`; calls `entry`, `epoch_of`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `Clients`, `ForecastOutcome`, `LLM_ROUTE`, `PURPOSE`, `_llm_client`, `_protected`, `_record_admission`, `_store_payloads`, `source_identity`; calls `Clients`, `ForecastOutcome`, `_llm_client`, `_protected`, `_record_admission`, `_store_payloads`, `source_identity`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `ProtectedContent`, `SendGuard`, `module`, `refusal_status`; calls `SendGuard`, `ask_llm`, `refusal_status`
- [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]] — imports `module`; calls `ad_envelope`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `LLM_HISTORY`, `outside_forecasters`; calls `outside_forecasters`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`; calls `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `module`; calls `has_table`, `insert_history_draw`, `insert_payload`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `METERED_REQUESTS_PER_CALL`, `estimated_call_tokens`, `plan_route`; calls `estimated_call_tokens`, `plan_route`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `ForecastReceipt`, `ITEM_UNASSISTED_SUCCESS`, `LO_COLD_AFTER_BLOCK`, `LO_COLD_SUCCESS`, `NO_BINDING`, `record_receipts`; calls `ForecastReceipt`, `record_receipts`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `logging`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]], [[Reference/Modules/learnloop/adaptive_difficulty/history_audit|learnloop.adaptive_difficulty.history_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/serve|learnloop.adaptive_difficulty.serve]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro2_history_forecaster.py](../../../../../../tests/test_ro2_history_forecaster.py) — direct import
  - `test_the_background_job_sends_each_rung_as_frozen_and_writes_receipts`
  - `test_the_serve_freezes_the_draw_and_two_rungs`
- [tests/test_ro2_history_protection.py](../../../../../../tests/test_ro2_history_protection.py) — direct import
  - `test_content_held_out_after_the_serve_is_never_sent`
- [tests/test_ro2_history_resolve.py](../../../../../../tests/test_ro2_history_resolve.py) — direct import
  - `test_the_dry_run_estimates_the_runs_own_output_budget_and_retry`

## Modification guidance

- Make changes here when the responsibility remains history forecast within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/history_forecast.py](../../../../../../src/learnloop/adaptive_difficulty/history_forecast.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
