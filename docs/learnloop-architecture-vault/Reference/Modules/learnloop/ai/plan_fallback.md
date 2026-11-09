---
title: "learnloop.ai.plan_fallback"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/plan_fallback.py"
source_paths:
  - "src/learnloop/ai/plan_fallback.py"
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
  - "learnloop.ai.plan_fallback module"
  - "src/learnloop/ai/plan_fallback.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.plan_fallback`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.plan_fallback` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Ask before using OpenRouter while the ChatGPT plan is unavailable.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py) |
| Source lines | 900 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `offer_profile(config: LearnLoopConfig) -> str | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 57) — The OpenRouter profile LearnLoop may offer, or ``None`` (no profile, wrong type, no key).
- `priced_by(*settings: str) -> Iterator[None]` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 116) — Resolve routes in this block for a feature held to its own price (re-review F2).
- `offer_blocker(config: LearnLoopConfig, task: str) -> str | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 142) — Why OpenRouter could not do ``task`` if the learner chose it, or ``None`` (review F2).
- `offer_sentence() -> str` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 165)
- `class OfferCollector` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 176)
  - `hint(self) -> dict[str, Any] | None` (line 199; public) — The typed hint for the adapter, or ``None`` when nothing was offered.
- `quiet() -> Iterator[None]` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 233) — Make no offer and honour no grant for routes resolved in this block; units made here have no origin.
- `offers_suppressed() -> bool` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 256) — True inside :func:`quiet` (either kind): routes resolved here make no offer.
- `collecting(origin: str | None=None, stamp: tuple[str, tuple[int, int]] | None=None) -> Iterator[OfferCollector]` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 267) — Collect the offers made while the block runs (one RPC, or one unit's work), as action ``origin``.
- `relay_hint(hint: dict[str, Any] | None, restore: Any=None) -> bool` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 313) — Offer again, in the current request, what a unit (a job, a batch) offered.
- `relay_job_offer(job: Any) -> None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 332) — Relay a finished job's offer on the first read that finds it, then forget it (review F8).
- `take_offer(collector: OfferCollector, current_vault: Any) -> tuple[dict[str, Any] | None, str | None]` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 345) — What one response may show: (the hint, its vault key), or (None, None).
- `start_collecting() -> OfferCollector` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 375) — Collect for the rest of this context (one CLI process).
- `current_hint() -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 383) — The hint of this context's collector (the CLI's JSON), without its unit list.
- `note_unavailable(task: str, profile: str, *, signed_out: bool=False) -> None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 393)
- `note_plan_route(task: str, profile: str) -> None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 400)
- `note_plan_failure(*, signed_out: bool=False) -> None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 406) — A plan request failed for availability; called by the plan client.
- `class GrantToken` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 478) — A unit's grant: the action it belongs to, in the epoch it was given (:func:`unit_token`).
  - `live(self, key: str) -> bool` (line 487; public)
- `class Offer` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 496) — One "Use OpenRouter instead" the dispatch showed: answering it grants ``origin``.
- `request(vault_root: Any, origin: str) -> Iterator[None]` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 526) — Serve one request of action ``origin`` on this thread (the sidecar's dispatch, per RPC).
- `unit_origin() -> str | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 541) — The action a unit of work created now belongs to: the request's, outside any job and any probe.
- `unit_token(vault_root: Any) -> GrantToken | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 549) — The token a unit created now carries (or the time-boxed check runs under).
- `note_unit(kind: str, unit_id: str) -> None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 575) — Record a unit created in this request, so its offer lists it (answering tokens it).
- `job_grant(token: GrantToken | None, origin: str | None=None, *, keep_collector: bool=False) -> Iterator[None]` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 584) — Run a unit's work on this thread under its token (``None``: none), as action ``origin``.
- `unit_stamp(vault_root: Any) -> tuple[str, tuple[int, int]] | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 604) — The vault and epoch a unit is created in (taken at its creation; round 5, Medium 1).
- `unit(token: GrantToken | None, origin: str | None, stamp: tuple[str, tuple[int, int]] | None) -> Iterator[OfferCollector]` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 615) — A unit's work (a sidecar job, a batch's job): :func:`job_grant`, and its own collector.
- `status_as(origin: str) -> Iterator[None]` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 635) — A status read of what action ``origin`` would use: no offer, and its grant counts (in a request).
- `remember_batch_grant(batch_id: str, token: GrantToken | None, origin: str | None=None, vault_root: Any=None) -> None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 647) — Keep a new batch's token, origin and creation stamp.
- `batch_grant(batch_id: str | None) -> GrantToken | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 661)
- `batch_origin(batch_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 666)
- `keep_batch_offer(batch_id: str, hint: dict[str, Any] | None) -> None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 671) — A batch's run met the unavailable plan: keep its offer for the next read that shows the batch.
- `batch_stamp(batch_id: str, vault_root: Any) -> tuple[str, tuple[int, int]] | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 679) — The vault and epoch the batch was created in (in memory), else now (a batch from before a restart).
- `relay_batch_offer(batch_id: str | None) -> bool` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 687) — Relay (once) the offer a batch kept, on a read that shows that batch.
- `relay_batch_offers(batch_ids: Iterable[str | None]) -> None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 708) — Relay the first pending offer among the batches a response shows (one offer per response).
- `command_grant(*, host: bool=False) -> Iterator[bool]` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 717) — The CLI's ``LEARNLOOP_AI_FALLBACK=openrouter``: the command's own grant, for this command only.
- `mint_offer(vault_root: Any, hint: dict[str, Any], origin: str, units: Iterable[tuple[str, str]]=()) -> str | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 744) — Record the offer one response shows; its id is what "Use OpenRouter instead" answers.
- `answer_offer(vault_root: Any, offer_id: str | None) -> Offer | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 759) — The learner chose "Use OpenRouter instead" on offer ``offer_id``: grant its action, token its units.
- `grant_origin(vault_root: Any, origin: str, tasks: Iterable[str]=()) -> None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 778) — Grant action ``origin`` on this vault for the session (``answer_offer``'s effect; tests use it).
- `revoke(vault_root: Any | None=None) -> None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 785) — Stop using OpenRouter: for one vault, or (``None``) for every vault.
- `revoke_all() -> None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 809)
- `granted_origins(vault_root: Any) -> list[str]` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 813)
- `granted_tasks(vault_root: Any) -> list[str]` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 818) — The tasks the answered offers named (display: Settings' "Stop using OpenRouter").
- `is_granted(task: str, vault_root: Any) -> bool` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 825) — Whether OpenRouter may serve ``task`` here (redesign D).

### Module constants

- `FALLBACK_KIND` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 50)
- `FALLBACK_ENV` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 52)
- `_OPENROUTER_TYPE` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 53)
- `_DEFAULT_KEY_ENV` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 54)
- `METERED_PRICE_SETTINGS` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 73)
- `PLAN_ONLY_TASKS` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 108)
- `_FEATURE_PRICES` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 112)
- `_COLLECTOR` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 225)
- `_QUIET` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 227)
- `_NO_OFFERS` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 229)
- `_GRANTS` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 436)
- `_EPOCH` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 438)
- `_GLOBAL` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 439)
- `_SEQ` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 440)
- `_OFFERS` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 442)
- `_BATCH_GRANTS` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 444)
- `_BATCH_ORIGIN` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 445)
- `_BATCH_OFFERS` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 446)
- `_BATCH_STAMP` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 447)
- `_GRANTS_LOCK` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 448)
- `_COMMAND_GRANT` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 450)
- `_REQUEST` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 452)
- `_JOB` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 454)
- `_STATUS_AS` ([src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py), line 457)

### Explicit exports

`__all__` declares:

- `FALLBACK_ENV`
- `FALLBACK_KIND`
- `METERED_PRICE_SETTINGS`
- `GrantToken`
- `Offer`
- `OfferCollector`
- `answer_offer`
- `batch_grant`
- `batch_origin`
- `collecting`
- `command_grant`
- `current_hint`
- `grant_origin`
- `granted_origins`
- `granted_tasks`
- `is_granted`
- `job_grant`
- `keep_batch_offer`
- `mint_offer`
- `note_plan_failure`
- `note_plan_route`
- `note_unavailable`
- `note_unit`
- `offer_blocker`
- `PLAN_ONLY_TASKS`
- `offer_profile`
- `offer_sentence`
- `offers_suppressed`
- `priced_by`
- `quiet`
- `batch_stamp`
- `relay_batch_offer`
- `relay_batch_offers`
- `take_offer`
- `unit_stamp`
- `relay_hint`
- `relay_job_offer`
- `remember_batch_grant`
- `request`
- `revoke`
- `revoke_all`
- `start_collecting`
- `status_as`
- `unit`
- `unit_origin`
- `unit_token`

## Internal implementation anchors

- `_setting(config: LearnLoopConfig, dotted: str) -> Any` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 135)
- `_collector() -> OfferCollector | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 252)
- `_merge_into(collector: OfferCollector, hint: dict[str, Any] | None) -> None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 292)
- `_relay_into(collector: OfferCollector, hint: dict[str, Any] | None, restore: Any=None) -> bool` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 306)
- `_vault_key(vault_root: Any) -> str` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 460)
- `_here() -> int` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 464)
- `_epoch(key: str) -> tuple[int, int]` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 468)
- `_next() -> int` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 472)
- `_request_origin() -> str | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 507)
- `_job_here() -> tuple[str | None, 'GrantToken | None'] | None` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 514)
- `_in_job() -> bool` ([source](../../../../../../src/learnloop/ai/plan_fallback.py), line 521)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `module`; statically calls `quiet`
- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `note_plan_failure`; statically calls `note_plan_failure`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `module`; statically calls `is_granted`, `note_plan_route`, `note_unavailable`, `offer_blocker`, `offer_profile`, `offer_sentence`, `offers_suppressed`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `collecting`, `command_grant`; statically calls `collecting`, `command_grant`
- [[Reference/Modules/learnloop/cli/render|learnloop.cli.render]] — imports `current_hint`; statically calls `current_hint`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `module`; statically calls `job_grant`, `priced_by`, `unit_origin`, `unit_token`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `module`; statically calls `offer_profile`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`; statically calls `priced_by`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `module`; statically calls `batch_grant`, `batch_origin`, `batch_stamp`, `keep_batch_offer`, `note_unit`, `remember_batch_grant`, `unit`, `unit_origin`, `unit_token`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `module`; statically calls `quiet`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `quiet`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `quiet`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `quiet`; statically calls `quiet`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `module`; statically calls `is_granted`, `offer_blocker`, `offer_profile`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; statically calls `quiet`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; statically calls `quiet`
- [[Reference/Modules/learnloop/source_retrieval/student_data|learnloop.source_retrieval.student_data]] — imports `module`; statically calls `is_granted`, `quiet`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `module`, `quiet`; statically calls `quiet`, `revoke_all`
- [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]] — imports `module`; statically calls `answer_offer`, `granted_origins`, `granted_tasks`, `offer_profile`, `revoke`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `module`; statically calls `note_unit`, `relay_hint`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `module`; statically calls `note_unit`, `relay_hint`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `unit_origin`, `unit_token`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `module`; statically calls `status_as`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `module`; statically calls `note_unit`, `relay_job_offer`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `module`; statically calls `relay_batch_offer`, `relay_batch_offers`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `module`; statically calls `note_unit`, `relay_job_offer`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `module`; statically calls `quiet`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `priced_by`, `quiet`, `relay_batch_offer`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `module`; statically calls `note_unit`, `relay_job_offer`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `module`; statically calls `priced_by`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `module`; statically calls `note_unit`, `relay_hint`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `module`; statically calls `status_as`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `module`; statically calls `relay_batch_offer`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `module`; statically calls `collecting`, `mint_offer`, `relay_batch_offers`, `request`, `take_offer`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `os`, `pathlib`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]], [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]], [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/render|learnloop.cli.render]] and 29 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_t1_routes.py](../../../../../../tests/test_ad23_t1_routes.py) — direct import
  - `test_ads_routes_are_in_the_plan_first_table`
  - `test_inside_an_ad_operation_no_route_asks_and_no_grant_serves`
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iii_a_figure_grant_never_meters_an_ask_and_an_ask_grant_meters_it_under_the_cap`
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_usage_limit_mid_stream_pauses_the_plan_and_routes_fall_back`
- [tests/test_coverage_on_extract.py](../../../../../../tests/test_coverage_on_extract.py) — direct import
  - `test_the_job_runs_quiet_and_never_offers_openrouter`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_the_daily_refresh_rejudges_quietly_before_the_plan_is_built_once_a_day`
  - `test_with_the_plan_down_the_plan_falls_back_to_rw7b_says_stale_and_nothing_asks`
- [tests/test_figure_rich_job.py](../../../../../../tests/test_figure_rich_job.py) — direct import
  - `test_without_a_grant_a_plan_down_job_waits_and_asks_nothing`
- [tests/test_figure_rich_rpc.py](../../../../../../tests/test_figure_rich_rpc.py) — direct import
  - `test_a_granted_press_carries_its_token_and_action_to_the_rich_job`
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_the_build_job_belongs_to_figure_request_for_t1s_offer`
- [tests/test_notes_as_learner_text.py](../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_a_note_is_read_on_the_ordinary_routes_with_the_decider`
- [tests/test_notes_linked.py](../../../../../../tests/test_notes_linked.py) — direct import
  - `test_a_metered_route_needs_its_price_and_a_route_down_waits_quietly`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_background_jobs_offer_reaches_the_read_that_finds_it_done`
  - `test_a_plan_call_that_fails_for_availability_offers_openrouter_for_that_route`
  - `test_every_task_under_code_defaults_resolves_tool_free_and_never_codex`
  - `test_f1_a_configured_metered_fallback_provider_is_never_used_silently_for_a_plan_route`
  - `test_f2_openrouter_is_offered_only_when_the_feature_could_use_it`
  - `test_f3_the_question_build_asks_and_a_grant_serves_it_priced_as_metered`
  - `test_f4_grants_are_per_vault_per_offer_and_the_env_grant_is_the_cli_commands_only`
  - `test_f8_an_error_that_is_not_a_sidecar_error_keeps_the_offer`
  - `test_fix_l1_an_exercise_imports_own_authoring_route_is_held_to_its_price`
  - `test_fix_l1_the_rpc_gates_of_priced_features_offer_and_honour_no_grant_their_job_would_refuse`
  - `test_fix_l2_a_quiet_status_read_never_points_at_an_offer_it_did_not_make`
  - `test_rr_f1_the_connection_status_never_offers_and_shows_a_granted_build`
  - `test_rr_f2_a_feature_that_needs_its_own_price_is_not_served_by_another_features_grant`
  - `test_rr_f3_the_plan_status_lists_the_sessions_grants_for_a_lasting_stop`
  - `test_the_cli_json_carries_the_hint`
  - `test_unavailable_offers_openrouter_only_when_configured_and_sends_nothing_unasked`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
  - `test_a_grant_counts_only_in_the_learners_request_or_a_job_carrying_it`
  - `test_a_hint_job_started_in_the_request_carries_its_grant_and_a_background_one_does_not`
  - `test_a_manual_fallback_is_never_replaced_by_a_grant`
  - `test_an_ingest_batch_carries_the_grant_only_when_the_learner_enqueued_it`
  - `test_startup_recovery_of_import_key_checks_never_uses_the_grant`
  - `test_the_background_build_launcher_never_uses_the_grant`
  - `test_the_cli_commands_grant_is_its_own_threads_only`
  - `test_the_edit_recheck_never_uses_the_grant`
  - `test_the_imports_time_boxed_key_check_carries_its_requests_grant`
  - `test_the_reader_imports_background_key_check_never_uses_the_grant`
- [tests/test_plan_first_transport_offer_grants.py](../../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
  - `test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter`
  - `test_p2_a_relayed_offer_keeps_the_jobs_starting_method`
  - `test_p3_a_batch_asks_on_its_own_and_its_answer_tokens_it`
  - `test_p3_units_get_the_answered_offers_token_and_every_resume_keeps_it`
  - `test_p4_stop_kills_every_captured_token_even_after_a_new_yes`
  - `test_p5_scrolling_after_a_build_yes_queues_nothing_that_carries_a_grant`
  - `test_p7_rw5b_figures_ask_as_the_rpc_that_asked`
  - `test_s5_a_regrant_never_revives_a_token_a_waiting_worker_captured`
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — direct import
  - `test_m1_a_figure_jobs_delayed_poll_after_a_vault_switch_mints_nothing`
  - `test_m1_every_relay_path_keeps_its_units_vault_and_epoch`
  - `test_m2_a_batch_resumed_after_a_restart_asks_again_as_its_origin`
  - `test_m4_the_yes_is_the_builds_consent`
- [tests/test_plan_first_transport_paid_roles.py](../../../../../../tests/test_plan_first_transport_paid_roles.py) — direct import
  - `test_a_grant_routes_a_paid_role_to_openrouter_priced_as_metered_and_a_ready_plan_comes_first`
  - `test_every_paid_role_resolves_to_the_plan_and_asks_before_openrouter`
- [tests/test_plan_first_transport_today_quiet.py](../../../../../../tests/test_plan_first_transport_today_quiet.py) — direct import
  - `test_the_probe_pool_sweep_asks_nothing_and_honours_no_grant`
- [tests/test_section_coverage_rpcs.py](../../../../../../tests/test_section_coverage_rpcs.py) — direct import
  - `test_a_failed_job_relays_an_openrouter_offer_keyed_by_curriculum_cover`
- [tests/test_teacher_te1_successor.py](../../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_no_openrouter_offer_for_a_lesson_until_its_price_is_set`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/plan_fallback.py](../../../../../../src/learnloop/ai/plan_fallback.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
