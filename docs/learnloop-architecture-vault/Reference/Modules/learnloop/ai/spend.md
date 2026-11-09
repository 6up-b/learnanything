---
title: "learnloop.ai.spend"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/spend.py"
source_paths:
  - "src/learnloop/ai/spend.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.spend module"
  - "src/learnloop/ai/spend.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.spend`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.spend` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Finite, per-command admission for paid work (Slice A §5.6).

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/spend.py](../../../../../../src/learnloop/ai/spend.py) |
| Source lines | 656 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `is_subscription_transport(*, profile=None, client=None) -> bool` ([source](../../../../../../src/learnloop/ai/spend.py), line 71) — True for a route billed to the owner's ChatGPT subscription (Codex or the plan provider).
- `subscription_usage_estimate(event: Mapping[str, object], *, planned_tokens: int, price_per_token: float | None) -> dict[str, object]` ([source](../../../../../../src/learnloop/ai/spend.py), line 78) — A subscription receipt's ``usage_json`` estimate (``estimated_only``).
- `class SpendCaps` ([source](../../../../../../src/learnloop/ai/spend.py), line 107)
  - `__post_init__(self) -> None` (line 117; internal)
  - `as_dict(self) -> dict[str, int | float]` (line 123; public)
- `class SpendEstimate` ([source](../../../../../../src/learnloop/ai/spend.py), line 128)
  - `__post_init__(self) -> None` (line 136; internal)
- `class SpendLimitExceeded(ValueError)` ([source](../../../../../../src/learnloop/ai/spend.py), line 143) — The next request cannot be admitted under the declared caps.
- `class SpendCancelled(AIInterrupted)` ([source](../../../../../../src/learnloop/ai/spend.py), line 147) — Cancellation was observed before admitting another request.
- `class SpendBudget` ([source](../../../../../../src/learnloop/ai/spend.py), line 151)
  - `__init__(self, caps: SpendCaps, *, cancelled: Callable[[], bool] | None=None, subscription: bool=False) -> None` (line 152; internal)
  - `caps(self) -> SpendCaps` (line 166; public)
  - `subscription(self) -> bool` (line 170; public)
  - `used(self) -> SpendEstimate` (line 174; public)
  - `declared(self) -> dict[str, object]` (line 177; public) — The caps in force, as recorded on receipts' ``budget_json``.
  - `check(self, estimate: SpendEstimate) -> SpendEstimate` (line 188; public) — Check additional work without reserving it or making any calls.
  - `request(self, estimate: SpendEstimate, *, subscription_route: bool=False) -> Iterator[SpendCharge]` (line 212; public) — Reserve one physical attempt before entering the paid-call body.
- `class SpendCharge` ([source](../../../../../../src/learnloop/ai/spend.py), line 261) — An admitted attempt; reconciliation is monotonic and idempotent.
  - `__init__(self, budget: SpendBudget, estimate: SpendEstimate, *, envelopes: tuple[tuple[SpendEnvelope, object], ...]=(), subscription: bool | None=None) -> None` (line 264; internal)
  - `note_estimated_only(self, *, total_tokens: int, estimated_usd: float | None) -> None` (line 280; public) — A subscription attempt's estimated usage (cumulative, ``estimated_only``) for the active envelopes' reports.
  - `reconcile(self, *, total_tokens: int | None=None, estimated_usd: float | None=None) -> None` (line 294; public) — Supply cumulative actual usage for this attempt, not usage deltas.
- `class SpendEnvelope` ([source](../../../../../../src/learnloop/ai/spend.py), line 331) — A money bound shared by every ``SpendBudget`` admitted while it is active.
  - `__init__(self, name: str, max_usd: float, *, observed: Callable[[], float] | None=None) -> None` (line 344; internal)
  - `_total(self) -> Decimal` (line 356; internal)
  - `remaining(self) -> float` (line 361; public)
  - `reserve(self, usd: Decimal) -> object` (line 365; public) — Reserve ``usd`` before a request is sent; returns the reservation's handle (passed back to ``unreserve``, ``charge`` and ``settle``).
  - `reservation_ref(self, handle: object) -> str | None` (line 379; public) — A durable name for the reservation, recorded on the request's root receipt (``budget_json.envelope_reservations``) so a ledger that counts the reservation never counts the receipt again.
  - `unreserve(self, handle: object) -> None` (line 386; public) — Undo a reservation whose request was never sent (another envelope refused it).
  - `charge(self, usd: Decimal, handle: object=None) -> None` (line 395; public) — Usage above the reservation (reconciliation; never a refund).
  - `settle(self, handle: object, actual: Decimal | None=None) -> None` (line 404; public) — The request finished and its receipt is written (``actual``: its reconciled cost, when the provider reported one).
  - `note_estimated_only(self, tokens: int, usd: Decimal | None) -> None` (line 412; public)
  - `report(self) -> dict[str, object]` (line 420; public)
- `spend_envelopes(*envelopes: SpendEnvelope | None) -> Iterator[tuple[SpendEnvelope, ...]]` ([source](../../../../../../src/learnloop/ai/spend.py), line 439) — Activate envelopes for this context (added to any already active).
- `active_envelopes() -> tuple[SpendEnvelope, ...]` ([source](../../../../../../src/learnloop/ai/spend.py), line 454)
- `class RequestAdmission` ([source](../../../../../../src/learnloop/ai/spend.py), line 496) — One admitted physical request: what it reserved, priced at its route.
- `class MeteredRequestGate` ([source](../../../../../../src/learnloop/ai/spend.py), line 506) — Per-request admission for one unit of paid work (a job attempt).
  - `__init__(self, *, limit_usd: float | None, price_per_token: Callable[[str | None], float | None], is_subscription: Callable[[Any], bool], default_output_tokens: int=0, spent_before_usd: float=0.0, cancelled: Callable[[], bool] | None=None) -> None` (line 535; internal)
  - `spent_usd(self) -> float` (line 563; public)
  - `limit_usd(self) -> float | None` (line 568; public)
  - `estimate_tokens(self, client: Any, *, prompt: Any, budget: int | None) -> int` (line 571; public) — Input (from the request's text) plus the output ceiling.
  - `estimate_usd(self, client: Any, *, prompt: Any, budget: int | None) -> float` (line 589; public)
  - `admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> RequestAdmission | None` (line 595; public)
  - `settle(self, admission: RequestAdmission | None, usage: Mapping[str, Any]) -> None` (line 631; public)

### Module constants

- `_COUNTS` ([src/learnloop/ai/spend.py](../../../../../../src/learnloop/ai/spend.py), line 58)
- `SUBSCRIPTION_PROFILE_TYPES` ([src/learnloop/ai/spend.py](../../../../../../src/learnloop/ai/spend.py), line 63)
- `SUBSCRIPTION_CLIENT_TYPES` ([src/learnloop/ai/spend.py](../../../../../../src/learnloop/ai/spend.py), line 64)
- `SUBSCRIPTION_UNENFORCED_CAPS` ([src/learnloop/ai/spend.py](../../../../../../src/learnloop/ai/spend.py), line 65)
- `ESTIMATED_ONLY` ([src/learnloop/ai/spend.py](../../../../../../src/learnloop/ai/spend.py), line 66)
- `RESERVATIONS_KEY` ([src/learnloop/ai/spend.py](../../../../../../src/learnloop/ai/spend.py), line 68)
- `NO_RESERVATION` ([src/learnloop/ai/spend.py](../../../../../../src/learnloop/ai/spend.py), line 466)
- `_CHARS_PER_TOKEN` ([src/learnloop/ai/spend.py](../../../../../../src/learnloop/ai/spend.py), line 492)

## Internal implementation anchors

- `_count(name: str, value: int) -> None` ([source](../../../../../../src/learnloop/ai/spend.py), line 96)
- `_money(name: str, value: float) -> None` ([source](../../../../../../src/learnloop/ai/spend.py), line 101)
- `class _NoReservation` ([source](../../../../../../src/learnloop/ai/spend.py), line 458) — A subscription request's place in an envelope: nothing reserved, so nothing to settle (its usage is tallied ``estimated_only``).
- `_reserve_in(envelopes: tuple[SpendEnvelope, ...], estimate: SpendEstimate, *, subscription: bool) -> tuple[tuple[SpendEnvelope, object], ...]` ([source](../../../../../../src/learnloop/ai/spend.py), line 469) — Reserve a metered estimate in every envelope, all or none; returns each envelope with its reservation handle.
- `_reported_usd(usage: Mapping[str, Any], price_per_token: float) -> Decimal | None` ([source](../../../../../../src/learnloop/ai/spend.py), line 640) — What a finished request cost: the provider's cost, else its tokens at the price; ``None`` when it reported nothing (the reservation stands).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `SpendBudget`, `SpendCaps`; statically calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `SpendLimitExceeded`; statically calls `SpendLimitExceeded`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `SpendLimitExceeded`; statically calls `SpendLimitExceeded`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/adaptive_difficulty/sending|learnloop.adaptive_difficulty.sending]] — imports `SpendBudget`, `SpendCaps`, `spend_envelopes`; statically calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/ai/review_spend|learnloop.ai.review_spend]] — imports `SpendBudget`, `SpendCancelled`, `SpendCaps`, `SpendCharge`, `SpendEstimate`; statically calls `SpendBudget`, `SpendCancelled`, `SpendEstimate`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`, `is_subscription_transport`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`, `subscription_usage_estimate`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`, `is_subscription_transport`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `SUBSCRIPTION_PROFILE_TYPES`, `SpendCaps`, `SpendLimitExceeded`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/contamination|learnloop.cli.contamination]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]] — imports `SpendCaps`, `SpendLimitExceeded`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/families|learnloop.cli.families]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `SpendCaps`, `SpendEstimate`, `is_subscription_transport`; statically calls `SpendCaps`, `SpendEstimate`, `is_subscription_transport`
- [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/pf|learnloop.cli.pf]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`, `is_subscription_transport`
- [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/cli/recurrence|learnloop.cli.recurrence]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `SpendBudget`; statically calls `SpendBudget`
- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`
- [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendLimitExceeded`; statically calls `SpendBudget`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`, `subscription_usage_estimate`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`, `is_subscription_transport`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `MeteredRequestGate`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`; statically calls `MeteredRequestGate`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `is_subscription_transport`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `SpendCancelled`; statically calls `SpendCancelled`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`; statically calls `SpendCaps`, `SpendEstimate`, `is_subscription_transport`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `SpendLimitExceeded`, `is_subscription_transport`; statically calls `is_subscription_transport`
- [[Reference/Modules/learnloop/daily_plan/router_teach_back|learnloop.daily_plan.router_teach_back]] — imports `is_subscription_transport`; statically calls `is_subscription_transport`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `SpendCaps`, `SpendLimitExceeded`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `SpendCaps`, `is_subscription_transport`; statically calls `is_subscription_transport`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendEstimate`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `SUBSCRIPTION_PROFILE_TYPES`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendEstimate`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendEstimate`, `SpendLimitExceeded`
- [[Reference/Modules/learnloop/diagnosis/recurrence/escalation|learnloop.diagnosis.recurrence.escalation]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `SpendEstimate`; statically calls `SpendEstimate`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `SpendCaps`, `SpendLimitExceeded`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `SpendCaps`, `SpendLimitExceeded`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]] — imports `is_subscription_transport`; statically calls `is_subscription_transport`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `SpendEnvelope`, `SpendLimitExceeded`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `is_subscription_transport`; statically calls `is_subscription_transport`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `is_subscription_transport`; statically calls `is_subscription_transport`
- [[Reference/Modules/learnloop/field/classification|learnloop.field.classification]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `subscription_usage_estimate`; statically calls `SpendBudget`, `SpendEstimate`, `SpendLimitExceeded`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `subscription_usage_estimate`; statically calls `SpendBudget`, `SpendEstimate`, `SpendLimitExceeded`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `SpendBudget`, `SpendCaps`, `spend_envelopes`; statically calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]] — imports `is_subscription_transport`; statically calls `is_subscription_transport`
- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`; statically calls `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`; statically calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `SpendLimitExceeded`, `spend_envelopes`; statically calls `spend_envelopes`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `spend_envelopes`; statically calls `spend_envelopes`
- [[Reference/Modules/learnloop/hints/writer|learnloop.hints.writer]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`; statically calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] — imports `SpendCancelled`, `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `spend_envelopes`; statically calls `spend_envelopes`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`; statically calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `SpendLimitExceeded`, `spend_envelopes`; statically calls `spend_envelopes`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`; statically calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendEstimate`, `subscription_usage_estimate`; statically calls `SpendEstimate`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `is_subscription_transport`; statically calls `SpendBudget`, `is_subscription_transport`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendBudget`, `SpendEstimate`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendEstimate`, `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`, `subscription_usage_estimate`; statically calls `SpendBudget`, `SpendEstimate`, `is_subscription_transport`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/ops/graph_nomination_report|learnloop.ops.graph_nomination_report]] — imports `SpendCaps`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`, `subscription_usage_estimate`; statically calls `SpendBudget`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendEstimate`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`; statically calls `SpendBudget`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendBudget`, `SpendEstimate`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `SpendBudget`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendEstimate`, `SpendLimitExceeded`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `SpendBudget`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendEstimate`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`, `subscription_usage_estimate`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`, `is_subscription_transport`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `SpendBudget`; statically calls `SpendBudget`
- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `SpendLimitExceeded`; statically calls `SpendLimitExceeded`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`; statically calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/source_retrieval/compare_scope|learnloop.source_retrieval.compare_scope]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `is_subscription_transport`, `spend_envelopes`; statically calls `SpendBudget`, `SpendCaps`, `is_subscription_transport`, `spend_envelopes`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `SpendLimitExceeded`; statically calls `SpendLimitExceeded`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `SpendBudget`, `SpendCaps`; statically calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `SpendEstimate`, `SpendLimitExceeded`; statically calls `SpendLimitExceeded`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `spend_envelopes`; statically calls `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`; statically calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`; statically calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `SpendBudget`, `SpendCaps`; statically calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `SpendBudget`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `SpendBudget`, `SpendCaps`, `SpendEnvelope`, `active_envelopes`, `spend_envelopes`; statically calls `SpendBudget`, `SpendCaps`, `SpendEnvelope`, `active_envelopes`, `spend_envelopes`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SpendEnvelope`, `SpendLimitExceeded`, `spend_envelopes`; statically calls `SpendEnvelope`, `SpendLimitExceeded`, `spend_envelopes`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `SpendCaps`; statically calls `SpendCaps`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`; statically calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `MeteredRequestGate`, `SpendLimitExceeded`, `is_subscription_transport`; statically calls `is_subscription_transport`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `is_subscription_transport`; statically calls `is_subscription_transport`
- [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] — imports `SpendLimitExceeded`, `spend_envelopes`; statically calls `spend_envelopes`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`; statically calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `SpendLimitExceeded`, `spend_envelopes`; statically calls `spend_envelopes`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `SpendCancelled`; statically calls `SpendCancelled`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `is_subscription_transport`; statically calls `is_subscription_transport`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `declared_budgets`; calls `declared_budgets`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `decimal`, `json`, `math`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] and 117 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ai_tool_isolation.py](../../../../../../tests/test_ai_tool_isolation.py) — direct import
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iii_a_figure_grant_never_meters_an_ask_and_an_ask_grant_meters_it_under_the_cap`
  - `test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s`
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_billing_class_is_subscription`
- [tests/test_codex_tool_lockdown.py](../../../../../../tests/test_codex_tool_lockdown.py) — direct import
- [tests/test_contamination_report.py](../../../../../../tests/test_contamination_report.py) — direct import
  - `test_caps_admit_before_any_call`
  - `test_dry_run_changes_nothing_and_builds_no_client`
  - `test_embed_uses_the_phase_1_backfill_with_the_t4_registry`
  - `test_identical_answers_resume_without_reusing_the_other_pairs_verdict`
  - `test_provider_errors_retry_within_caps_and_are_never_echoed`
  - `test_the_report_carries_a_repeated_judgment_noise_floor_and_owner_audits`
  - `test_unknown_price_fails_closed_on_a_metered_route`
- [tests/test_diagnose_review.py](../../../../../../tests/test_diagnose_review.py) — direct import
  - `test_a_resume_refuses_a_changed_output_limit`
  - `test_over_budget_refuses_before_copying`
- [tests/test_diagnose_review_spend.py](../../../../../../tests/test_diagnose_review_spend.py) — direct import
  - `test_a_json_repair_is_a_second_admitted_request_on_a_metered_route`
  - `test_admitted_repairs_are_charged_and_capped_by_the_admitted_output`
  - `test_subscription_requests_still_stop_on_cancellation`
  - `test_subscription_routes_have_no_physical_request_bound`
  - `test_the_call_count_cap_still_stops_subscription_work`
  - `test_the_route_allowance_is_enforced_when_the_profile_sets_no_limit`
  - `test_transport_retries_are_admitted_too`
- [tests/test_diagnosis_embeddings.py](../../../../../../tests/test_diagnosis_embeddings.py) — direct import
  - `test_backfill_embeds_db_recipes_only_when_named`
- [tests/test_diagnosis_isolation.py](../../../../../../tests/test_diagnosis_isolation.py) — direct import
  - `test_a_review_refuses_a_grader_or_diagnoser_that_cannot_isolate`
- [tests/test_e0_budget.py](../../../../../../tests/test_e0_budget.py) — direct import
  - `test_the_ledger_is_a_spend_envelope_for_reused_production_paths`
- [tests/test_e0_review_round2.py](../../../../../../tests/test_e0_review_round2.py) — direct import
  - `test_f19_the_ledger_envelope_ignores_a_subscription_sentinel`
- [tests/test_embedding_backfill.py](../../../../../../tests/test_embedding_backfill.py) — direct import
  - `test_already_cancelled_never_constructs_client`
  - `test_backfill_is_batched_and_idempotent_with_receipts`
  - `test_caps_refuse_before_client_construction`
  - `test_dry_run_does_not_construct_client_or_change_database`
  - `test_failed_batch_keeps_successful_checkpoint_and_redacts_report`
  - `test_invalid_paid_response_keeps_the_report_and_is_not_retried`
  - `test_provider_failure_reports_sdk_class_without_its_message`
  - `test_real_embedding_transport_retry_is_bounded_and_receipted`
  - `test_retry_is_admitted_against_remaining_call_cap`
  - `test_retry_is_charged_and_keeps_candidates_unique`
  - `test_unknown_price_reason_names_the_remedy`
- [tests/test_embedding_compare.py](../../../../../../tests/test_embedding_compare.py) — direct import
  - `test_compare_dry_runs_estimate_cost_and_admit_the_whole_plan`
- [tests/test_facet_identity.py](../../../../../../tests/test_facet_identity.py) — direct import
  - `test_spend_caps_stop_the_judge_before_a_call`
  - `test_the_decider_asks_one_choice_question_per_pair`
- [tests/test_facet_identity_composition.py](../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_a_configured_decider_route_builds_the_decider_judge_without_a_call`
- [tests/test_family_proposals.py](../../../../../../tests/test_family_proposals.py) — direct import
  - `test_caps_admit_before_any_calls`
  - `test_codex_estimate_falls_back_to_input_plus_output_tokens`
  - `test_codex_route_dry_run_shows_an_estimate_without_a_price`
  - `test_codex_run_still_stops_a_runaway_at_the_call_cap`
  - `test_each_retry_spends_and_never_echoes_provider_error`
  - `test_fake_codex_run_succeeds_and_receipts_carry_estimated_only`
  - `test_metered_route_keeps_the_physical_request_bound_and_full_caps`
  - `test_route_availability_never_changes_preview_model`
  - `test_unknown_price_fails_closed_even_with_high_cap`
  - `test_unusable_verdict_without_retry_budget_is_ledgered_and_reasked`
- [tests/test_field_signal_production_paths.py](../../../../../../tests/test_field_signal_production_paths.py) — direct import
- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — direct import
  - `test_e_the_figures_daily_budget_refusing_a_visual_leaves_the_lesson_open`
  - `test_e_the_visual_builder_decides_by_the_lesson_gate_alone`
- [tests/test_glm_ocr.py](../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_429_and_5xx_retry_with_their_own_admission_and_receipt`
  - `test_auto_falls_back_on_a_glm_failure_but_never_past_a_refusal`
  - `test_r2_f4_cancelling_stops_the_windows_not_yet_sent`
  - `test_spend_refusals_send_nothing_and_no_ok_sends_nothing`
  - `test_the_daily_gate_prices_glm_receipts_and_local_runs_cost_nothing`
- [tests/test_grading_hardcases.py](../../../../../../tests/test_grading_hardcases.py) — direct import
  - `test_a_dry_run_plans_the_grader_and_builds_no_client`
- [tests/test_graph_nomination.py](../../../../../../tests/test_graph_nomination.py) — direct import
  - `test_backfill_reuses_a_vector_paid_at_ingest_under_another_id`
- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — direct import
  - `test_backfill_after_apply_reuses_the_vectors_paid_at_ingest`
- [tests/test_graph_nomination_report.py](../../../../../../tests/test_graph_nomination_report.py) — direct import
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_the_hardcase_harness_plans_the_grader_at_its_routes_policy_budget`
  - `test_the_hardcase_harness_retries_a_truncated_grade_once_at_double`
- [tests/test_integration_daily_loop_field.py](../../../../../../tests/test_integration_daily_loop_field.py) — direct import
  - `test_retired_reader_card_is_never_a_family_candidate`
- [tests/test_interaction_signals.py](../../../../../../tests/test_interaction_signals.py) — direct import
  - `test_codex_classification_still_stops_at_the_call_cap`
  - `test_no_calls_or_writes_when_not_admitted`
- [tests/test_item_fingerprints.py](../../../../../../tests/test_item_fingerprints.py) — direct import
- [tests/test_learner_text_gaps_rereview.py](../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f2_a_refused_draft_is_deferred_not_logged_unmatched`
  - `test_f2_a_spend_stop_leaves_both_texts_queued_and_stops_the_run`
- [tests/test_marker_pdfium_worker.py](../../../../../../tests/test_marker_pdfium_worker.py) — direct import
  - `test_a_cancelled_import_stops_the_marker_worker`
  - `test_every_process_the_marker_worker_started_ends_with_its_reading`
- [tests/test_matching.py](../../../../../../tests/test_matching.py) — direct import
  - `test_a_spend_refusal_stops_the_batch_and_a_failure_skips_one_pair`
- [tests/test_notes_as_learner_text.py](../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_c2b_a_note_and_an_ordinary_gap_share_the_gap_readers_route`
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
  - `test_paid_calls_fail_on_a_second_truncation`
  - `test_paid_calls_retry_a_truncation_once_at_double_the_admitted_budget`
- [tests/test_pf_generation.py](../../../../../../tests/test_pf_generation.py) — direct import
  - `test_codex_routes_run_on_the_subscription_with_estimated_only_cost`
  - `test_metered_unknown_price_and_caps_fail_closed_before_any_call`
  - `test_seeding_writes_nothing_until_the_plan_is_admitted`
- [tests/test_pf_reports.py](../../../../../../tests/test_pf_reports.py) — direct import
  - `test_report_dry_runs_price_and_admit_the_blind_judge`
- [tests/test_practice_index_adapters.py](../../../../../../tests/test_practice_index_adapters.py) — direct import
  - `test_batch_dry_runs_never_migrate_an_older_rollback_database`
  - `test_cli_eval_dry_run_find_coverage_status_and_tool_spec`
- [tests/test_practice_index_dossiers.py](../../../../../../tests/test_practice_index_dossiers.py) — direct import
  - `test_call_caps_still_bind_a_subscription_route`
  - `test_reverting_sources_selects_the_matching_earlier_dossier`
- [tests/test_practice_index_evaluation.py](../../../../../../tests/test_practice_index_evaluation.py) — direct import
  - `test_caps_are_checked_against_the_whole_plan_first`
  - `test_switch_off_and_caps_stop_before_a_decision`
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_an_alternative_embedding_model_takes_an_explicit_price`
- [tests/test_practice_index_paid.py](../../../../../../tests/test_practice_index_paid.py) — direct import
- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — direct import
  - `test_decider_end_to_end_through_the_fake_endpoint`
  - `test_dry_run_and_caps_refuse_before_any_client_call_or_write`
  - `test_llm_judge_metered_route_is_isolated_bounded_and_ledgered`
  - `test_rate_limits_retry_within_caps_and_malformed_answers_fail_closed`
  - `test_resume_recovers_a_committed_verdict_instead_of_paying_again`
  - `test_rich_state_carries_hypothesis_evidence_and_help_timing_to_both_judges`
  - `test_scripted_decider_sees_identical_states_for_both_judges`
  - `test_subscription_llm_estimates_cost_ledgers_invalid_verdicts_and_resumes`
  - `test_switches_and_cache_location_are_enforced`
- [tests/test_project_atomicity.py](../../../../../../tests/test_project_atomicity.py) — direct import
- [tests/test_project_blindness.py](../../../../../../tests/test_project_blindness.py) — direct import
  - `test_rendered_prompts_carry_no_provenance_declaration_or_closed_book_origin`
- [tests/test_project_cli.py](../../../../../../tests/test_project_cli.py) — direct import
  - `test_hidden_retries_are_admitted_only_against_max_retries`
  - `test_metered_calls_carry_their_admitted_output_limit`
  - `test_metered_output_limit_reaches_the_provider_request_and_its_repair`
  - `test_metered_routes_fail_closed_without_a_price`
- [tests/test_project_probes.py](../../../../../../tests/test_project_probes.py) — direct import
- [tests/test_project_report.py](../../../../../../tests/test_project_report.py) — direct import
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_a_student_that_misses_the_time_box_is_late_and_the_others_serve`
  - `test_a_student_that_never_becomes_ready_is_late_within_the_time_box_never_a_hang`
  - `test_the_resolver_serves_the_adopted_student_and_never_waits_for_a_zero_weight_cold_start`
- [tests/test_reader_ca3_compare_anywhere.py](../../../../../../tests/test_reader_ca3_compare_anywhere.py) — direct import
  - `test_a_decider_that_cannot_answer_reads_nothing`
- [tests/test_reader_digest_narrative.py](../../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_a_narrative_written_meanwhile_never_supersedes_part_1s_plan`
  - `test_a_spend_stop_inside_the_call_is_capped`
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — direct import
  - `test_a_budget_stop_leaves_the_digest_incomplete_and_the_next_plan_re_asks`
  - `test_the_spend_envelopes_are_the_followups_and_the_services`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f5_an_unjudged_worked_example_is_refreshed_in_the_background_under_both_envelopes`
- [tests/test_reader_intent.py](../../../../../../tests/test_reader_intent.py) — direct import
  - `test_a_decider_that_cannot_answer_routes_to_ask`
- [tests/test_reader_rw2b_review.py](../../../../../../tests/test_reader_rw2b_review.py) — direct import
- [tests/test_reader_rw3b_review_fixes.py](../../../../../../tests/test_reader_rw3b_review_fixes.py) — direct import
  - `test_retrievals_metered_requests_reserve_under_the_cue_envelope`
- [tests/test_recurrence_benchmarks.py](../../../../../../tests/test_recurrence_benchmarks.py) — direct import
  - `test_b1_and_b3_run_through_the_real_phase_5a_harness_once_merged`
  - `test_b3_replays_the_vaults_labelled_pairs`
  - `test_malformed_writer_json_is_one_failed_case_under_tight_caps`
  - `test_the_b1_dry_run_prices_a_metered_writer_with_its_tokens`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_the_backlog_refuses_over_its_caps`
  - `test_the_guard_stops_at_its_call_cap`
- [tests/test_recurrence_live.py](../../../../../../tests/test_recurrence_live.py) — direct import
  - `test_a_cancelled_command_stops_the_judge`
  - `test_a_hidden_escalation_card_plans_no_escalated_repair`
  - `test_an_exhausted_command_budget_stops_the_judge`
  - `test_the_dry_run_plans_the_recurrence_work_on_the_same_caps`
  - `test_the_judge_runs_on_the_commands_budget_and_shows_in_its_summary`
- [tests/test_required_method_reopened.py](../../../../../../tests/test_required_method_reopened.py) — direct import
  - `test_f17_a_failed_judgment_leaves_the_job_retryable_and_a_rerun_resumes_without_regenerating`
- [tests/test_required_method_round3.py](../../../../../../tests/test_required_method_round3.py) — direct import
- [tests/test_required_method_round3_rereview.py](../../../../../../tests/test_required_method_round3_rereview.py) — direct import
  - `test_f9_the_resume_budgets_the_largest_judgment_estimates_not_the_longest_stems`
- [tests/test_required_method_round3_review.py](../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f7_a_resume_is_estimated_from_the_persisted_unfinished_stem`
- [tests/test_ro2_history_forecaster.py](../../../../../../tests/test_ro2_history_forecaster.py) — direct import
  - `test_a_skipped_forecast_is_censored_with_its_reason`
- [tests/test_router_r2c_retrieval.py](../../../../../../tests/test_router_r2c_retrieval.py) — direct import
  - `test_the_backfill_dry_runs_and_then_embeds_what_is_missing`
  - `test_the_backfill_is_held_to_its_money_cap`
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
  - `test_a_closed_contexts_job_has_its_next_physical_request_refused`
- [tests/test_source_retrieval_cli.py](../../../../../../tests/test_source_retrieval_cli.py) — direct import
  - `test_deep_search_caps_bound_the_paid_steps`
- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
- [tests/test_source_retrieval_rereview.py](../../../../../../tests/test_source_retrieval_rereview.py) — direct import
- [tests/test_source_retrieval_rereview_cost.py](../../../../../../tests/test_source_retrieval_rereview_cost.py) — direct import
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
- [tests/test_source_retrieval_suites.py](../../../../../../tests/test_source_retrieval_suites.py) — direct import
- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — direct import
- [tests/test_source_service_spend_accounting.py](../../../../../../tests/test_source_service_spend_accounting.py) — direct import
  - `test_a_finished_request_counts_its_reported_cost_once`
  - `test_a_released_reservation_cannot_start_its_request`
  - `test_a_request_settled_without_its_cost_counts_a_lower_reported_cost`
  - `test_a_request_settled_without_its_reported_cost_counts_its_receipt`
  - `test_concurrent_admission_counts_the_unreconciled_receipt`
  - `test_subscription_requests_are_never_refused_by_the_shared_daily_cap`
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
  - `test_a_settled_request_is_counted_once_not_by_its_receipt_and_its_reservation`
  - `test_an_envelope_is_shared_by_concurrent_workers`
  - `test_prior_receipts_and_reservations_in_flight_add_up_under_the_cap`
  - `test_subscription_requests_are_estimated_never_refused`
  - `test_the_daily_cap_is_shared_by_concurrent_processes`
  - `test_the_daily_guard_refuses_past_five_dollars`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_a_cli_budget_has_room_for_every_query_encoder_and_the_rewrite`
  - `test_the_fallback_query_spends_from_the_callers_budget_and_is_planned`
- [tests/test_sources_merge_composition.py](../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_a_subscription_route_reserves_nothing_in_a_spent_envelope`
- [tests/test_spend_controls.py](../../../../../../tests/test_spend_controls.py) — direct import
  - `test_a_budget_without_a_money_cap_never_refuses_dollars_but_keeps_its_counts`
  - `test_actual_usage_reconciles_upward_only_idempotently_and_preserves_paid_result`
  - `test_cancellation_stops_next_attempt_without_charge`
  - `test_caps_and_estimates_reject_invalid_numbers`
  - `test_counts_reject_fractional_values`
  - `test_decimal_dollar_boundary_does_not_fail_from_binary_float_addition`
  - `test_declared_caps_persist_on_real_receipt_for_success_and_failure`
  - `test_dry_run_is_nonmutating_and_does_not_emit_model_receipts`
  - `test_each_cap_exact_boundary_then_rejects_before_call`
  - `test_failed_attempt_actual_cost_overrun_stops_next_request`
  - `test_failed_attempt_and_retry_charge_calls_tokens_cost_without_duplicate_candidates`
  - `test_invalid_actual_usage_cannot_reduce_reservation`
  - `test_omitted_price_is_unknown_not_free`
  - `test_request_requires_one_physical_attempt`
  - `test_subscription_budget_estimates_only_and_keeps_count_caps`
  - `test_unknown_price_rejects_even_large_finite_cap_explicit_price_estimate_admits`
  - `test_zero_caps_and_zero_price_allow_no_paid_calls`
- [tests/test_t6_followup_composition.py](../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_pf_caller_prices_a_truncation_retry_at_its_doubled_output_budget`
- [tests/test_t6_followup_rereview.py](../../../../../../tests/test_t6_followup_rereview.py) — direct import
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_every_verification_attempt_is_admitted_under_the_shared_caps`
  - `test_insufficient_candidate_caps_fail_at_the_dry_run`
  - `test_paid_calls_fail_a_truncation_at_the_profile_maximum_without_another_request`
  - `test_paid_calls_reserve_and_record_the_real_increased_limit`
  - `test_project_calls_reserve_the_transport_retry_at_its_doubled_allowance`
  - `test_review_spend_reserves_the_transport_retry_at_its_doubled_allowance`
- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_a_review_resume_refuses_a_changed_decider_profile`
  - `test_contamination`
  - `test_contamination_one_routes_switch_restores_its_old_checkpoints_budget_check_and_ledger`
  - `test_decider_receipt_and_spend_ignore_llm_output_budget`
  - `test_field_question_classification`
  - `test_gap_pairs_reuse_the_deciders_verdict_and_defer_on_a_stopped_fallback`
  - `test_link_judgments`
  - `test_links_the_decider_answered_are_never_paid_for_again_when_the_fallback_failed`
  - `test_needed_is_the_deciders_and_its_refusal_falls_back`
  - `test_route_decision_fallback_and_switch`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
- [tests/test_ux_phase1_landing.py](../../../../../../tests/test_ux_phase1_landing.py) — direct import
  - `test_the_request_gate_works_without_a_money_limit`
- [tests/test_ux_phase1_review_fixes.py](../../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
  - `test_f2_rereview_a_transport_retry_is_refused_when_the_failed_attempt_used_the_room`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/spend.py](../../../../../../src/learnloop/ai/spend.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
