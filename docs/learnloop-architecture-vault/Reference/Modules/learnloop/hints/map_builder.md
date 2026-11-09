---
title: "learnloop.hints.map_builder"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/map_builder.py"
source_paths:
  - "src/learnloop/hints/map_builder.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.map_builder module"
  - "src/learnloop/hints/map_builder.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.map_builder`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.map_builder` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H1: building, merging and reading approach maps (spec §4.3, §4.3.1, §7.2-7.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py) |
| Source lines | 1640 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class MapOutcome` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 158) — What one build or merge did.
  - `as_dict(self) -> dict[str, Any]` (line 178; public)
- `maps_enabled(config: Any) -> bool` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 182)
- `maps_envelope(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> SharedDailyEnvelope` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 190) — ``hints.maps.max_daily_cost_usd`` as a durable, atomic daily cap in the vault's spend ledger (``source_service_spend``) under its own envelope: each metered map request reserves its estimate in one BEGIN IMMEDIATE transaction checking today's total plus the estimate against the…
- `maps_spend_today(vault: LoadedVault, connection: sqlite3.Connection, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 206) — Today's map spend as the cap counts it, with the cap and what remains.
- `current_map(vault: LoadedVault, repository: Repository, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 231) — The item's map for its current revision, or None.
- `build_prompt(seeds: MapSeeds, *, feedback: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 311)
- `merge_prompt(item: PracticeItem, current: Mapping[str, Any], attempts: Sequence[SeedAttempt], facet_ids: Sequence[str], *, feedback: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 342)
- `map_context(vault: LoadedVault, seeds: MapSeeds) -> MapContext` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 356)
- `claim_key(practice_item_id: str) -> str` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 699)
- `build_map(vault: LoadedVault, repository: Repository, practice_item_id: str, *, trigger: str, client: Any | None=None, clock: Clock | None=None, deadline: float | None=None, wait_seconds: float | None=0.0, find: Callable[..., Any] | None=None, fence: 'BuildFence | None'=None) -> MapOutcome` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 855) — Build and store the item's map unless its current revision has one.
- `build_map_inline(vault: LoadedVault, repository: Repository, practice_item_id: str, *, client: Any | None=None, clock: Clock | None=None, deadline: float | None=None, find: Callable[..., Any] | None=None) -> MapOutcome` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 975) — H2's entry when a hint finds no map (§4.3.1, row 2): build it now, in the same request, and store it.
- `class BuildFence` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1001) — One background build's ticket: the registry's vault generation when it was admitted.
  - `__init__(self, registry: 'BackgroundBuilds', generation: str) -> None` (line 1006; internal)
  - `live(self) -> bool` (line 1010; public)
  - `enter_commit(self) -> bool` (line 1013; public) — Under the registry's generation lock: still this generation?
  - `leave_commit(self) -> None` (line 1019; public)
- `class BackgroundBuilds` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1023) — The lifecycle of build-on-serve workers, owned by the sidecar (fix round 2, M4): a registry keyed to the loaded vault with a generation token.
  - `__init__(self, *, drain_seconds: float=DRAIN_SECONDS) -> None` (line 1037; internal)
  - `generation(self) -> str` (line 1051; public)
  - `_live(self, generation: str) -> bool` (line 1054; internal)
  - `_enter_commit(self, generation: str) -> bool` (line 1057; internal)
  - `_leave_commit(self) -> None` (line 1064; internal)
  - `committing(self) -> int` (line 1071; public)
  - `bind(self, sqlite_path: Any) -> None` (line 1075; public) — Key the registry to the loaded vault; a different vault (or a closed registry) closes the previous generation (draining it only if no close has drained it yet) and opens a new one.
  - `admit(self, sqlite_path: Any) -> BuildFence | None` (line 1088; public)
  - `launch(self, sqlite_path: Any, work: Callable[[BuildFence], Callable[[], None]], *, name: str) -> threading.Thread | None` (line 1094; public) — Admit, register and start one build atomically with :meth:`close` (fix round 3, R4): under the registry lock the build is refused once closed, and registered before it starts, so a close either refuses it or joins it.
  - `track(self, thread: threading.Thread) -> None` (line 1114; public)
  - `close(self, timeout: float | None=None) -> bool` (line 1118; public) — Stop admitting, cancel, and join for at most ``timeout`` seconds (default ``drain_seconds``; never hangs).
  - `running(self) -> int` (line 1157; public)
- `schedule_build_on_serve(vault: LoadedVault, sqlite_path: Any, practice_item_id: str, *, client: Any | None=None, clock: Clock | None=None, find: Callable[..., Any] | None=None, builds: BackgroundBuilds | None=None) -> threading.Thread | None` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1165) — Start a background build for a served item (``hints.maps.build_on_serve``).
- `schedule_merge_after_hint(vault: LoadedVault, sqlite_path: Any, practice_item_id: str, *, client: Any | None=None, clock: Clock | None=None, builds: BackgroundBuilds | None=None) -> threading.Thread | None` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1229) — Start the lazy learner-route merge after a hint is shown (§4.3.1 row 3; H2a review F9): background, never on the request path, so it may use the map route's Codex.
- `wait_for_background_builds(timeout: float=30.0) -> bool` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1296) — Join the background builds started so far, of every registry (tests; the sidecar's shutdown path closes its own registry, :meth:`BackgroundBuilds.close`).
- `new_learner_attempts(vault: LoadedVault, repository: Repository, practice_item_id: str) -> list[SeedAttempt]` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1322) — The learner's correct answers in the item's family the current map has not seen (§4.3.1 row 3: "the map predates the learner's latest correct answers"), newest first, at most ``MAX_ATTEMPTS``.
- `merge_learner_routes(vault: LoadedVault, repository: Repository, practice_item_id: str, *, client: Any | None=None, clock: Clock | None=None, deadline: float | None=None, fence: 'BuildFence | None'=None) -> MapOutcome` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1340) — Merge the learner's new correct routes into the item's map (lazy: H2 calls it after a hint is shown on an item whose map predates them, :func:`schedule_merge_after_hint`).
- `select_items(vault: LoadedVault, *, item_id: str | None=None, family_id: str | None=None, learning_object_id: str | None=None) -> list[PracticeItem]` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1479) — The active items one ``hints maps build`` selector names (all, without one).
- `plan_item(vault: LoadedVault, repository: Repository, item: PracticeItem, *, client: Any | None=None) -> MapOutcome` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1510) — A dry run for one item: is a map due, and what would the call cost?
- `backfill(vault: LoadedVault, repository: Repository, items: Iterable[PracticeItem], *, dry_run: bool, limit: int | None=None, client: Any | None=None, clock: Clock | None=None, find: Callable[..., Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1544) — ``learnloop hints maps build``: build the items without a current map.

### Module constants

- `LOG` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 131)
- `PROMPT_VERSION` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 133)
- `MERGE_PROMPT_VERSION` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 134)
- `ROUTE_TASK` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 135)
- `PURPOSE` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 136)
- `MERGE_PURPOSE` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 137)
- `OWNER_KIND` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 139)
- `ENVELOPE` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 140)
- `OUTCOME_OWNER_KIND` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 143)
- `ENVELOPE_OWNER_KINDS` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 144)
- `LEDGER_TASK` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 145)
- `BUILDS_ENV` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 149)
- `TRIGGERS` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 150)
- `_CAPS` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 154)
- `_INSTRUCTIONS` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 262)
- `_MERGE_INSTRUCTIONS` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 290)
- `_LOCKS` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 527)
- `_LOCKS_GUARD` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 528)
- `PROCESS_TOKEN` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 540)
- `CLAIM_TASK` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 541)
- `CLAIM_LEASE_SECONDS` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 544)
- `CLAIM_HEARTBEAT_SECONDS` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 545)
- `_CLAIM_POLL_SECONDS` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 546)
- `_INFLIGHT` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 992)
- `_INFLIGHT_GUARD` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 993)
- `_THREADS` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 994)
- `DRAIN_SECONDS` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 998)
- `_DEFAULT_BUILDS` ([src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py), line 1162)

### Explicit exports

`__all__` declares:

- `BUILDS_ENV`
- `DRAIN_SECONDS`
- `ENVELOPE`
- `LEDGER_TASK`
- `MERGE_PROMPT_VERSION`
- `OWNER_KIND`
- `PROMPT_VERSION`
- `ROUTE_TASK`
- `BackgroundBuilds`
- `BuildFence`
- `MapOutcome`
- `backfill`
- `build_map`
- `build_map_inline`
- `build_prompt`
- `claim_key`
- `current_map`
- `map_context`
- `maps_enabled`
- `maps_envelope`
- `maps_spend_today`
- `merge_learner_routes`
- `merge_prompt`
- `new_learner_attempts`
- `plan_item`
- `schedule_build_on_serve`
- `schedule_merge_after_hint`
- `select_items`
- `wait_for_background_builds`

## Internal implementation anchors

- `_active_item(vault: LoadedVault, item_id: str) -> PracticeItem | None` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 226)
- `_revision_key(item_hash: str, structure: str) -> str` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 246)
- `_failed_before(connection: sqlite3.Connection, item_id: str, right_kind: str, right_id: str) -> bool` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 250)
- `_clip(text: str, limit: int) -> str` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 302)
- `_expected_text(expected: Any) -> str` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 307)
- `_route_client(vault: LoadedVault, route: PaidRoute) -> tuple[Any | None, str | None]` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 368) — The route's pinned client (patched by tests; never a silent fallback).
- `class _Unpriced(Exception)` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 374)
- `class _Caller` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 379)
- `_ledger(repository: Repository, *, item_id: str, right_kind: str, right_id: str, prompt: str, verdict: str, validation: Validation | None, extra_reasons: Sequence[str]=(), round_: int, trigger: str, clock: Clock | None, prompt_version: str=PROMPT_VERSION, claim: '_Claim | None'=None) -> None` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 444)
- `class _Stored` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 462) — What :func:`_store` did: ``stored`` (a new row), ``current`` (a build found its revision's map stored by another builder first) or ``stale`` (the claim was lost, or a merge's base is no longer the newest row).
- `_store(repository: Repository, *, item: PracticeItem, item_hash: str, structure: str, seeds_hash: str, seeds_record: Mapping[str, Any], validated: ApproachMapV1, validation: Validation, trigger: str, model: str | None, prompt_version: str, prompt: str, clock: Clock | None, claim: '_Claim | None', base_map_id: str | None=None, vault: LoadedVault | None=None) -> _Stored` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 472) — Insert the new version, fenced in the same BEGIN IMMEDIATE transaction (Codex review F3): only while ``claim`` is this worker's lease, unexpired (owner, epoch and expiry; fix round 2, M3) and its vault still loaded (M4); a build (``base_map_id`` None) only when no map of its rev…
- `_item_lock(sqlite_path: Any, item_id: str) -> threading.Lock` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 531)
- `class _Claim` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 550)
- `class _LeaseLost(Exception)` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 564) — The build's lease or vault is gone: stop without paying or writing more.
- `_holds(connection: sqlite3.Connection, claim: _Claim) -> bool` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 568) — Owner, epoch and expiry (fix round 2, M3), and the heartbeat's own signal.
- `_alive(repository: Repository, claim: _Claim) -> bool` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 576)
- `_require_live(repository: Repository, claim: _Claim) -> None` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 583)
- `_renew_live(repository: Repository, claim: _Claim) -> None` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 588) — Renew the claim's full lease now, while it is still this worker's and unexpired, or raise ``_LeaseLost`` (reader RW6b part 2, final verify F3).
- `_fenced_txn(repository: Repository, claim: _Claim | None, *, fence: 'BuildFence | None'=None, lease: bool=True) -> Iterator[sqlite3.Connection]` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 607) — One fenced write transaction (fix rounds 3 and 4).
- `class _FencedRepository` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 641) — The repository a build's paid calls write through: receipts and checkpoints are written in a :func:`_fenced_txn`, so they commit only while the build's lease and vault hold (fix rounds 2 and 3).
- `_lease_now() -> str` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 693) — Wall-clock time for leases: process liveness, never the vault's clock.
- `_try_claim(repository: Repository, item_id: str, fence: 'BuildFence | None'=None, *, key: str | None=None, task: str=CLAIM_TASK, producer: str=OWNER_KIND, lease_seconds: int=CLAIM_LEASE_SECONDS) -> _Claim | None` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 703)
- `_claim(repository: Repository, item_id: str, until: float | None, fence: 'BuildFence | None'=None, *, key: str | None=None, task: str=CLAIM_TASK, producer: str=OWNER_KIND, lease_seconds: int=CLAIM_LEASE_SECONDS) -> _Claim | None` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 720) — Claim the item's builds across processes, waiting until ``until`` (``time.monotonic()``; None: until claimed; a dead holder's lease lapses within ``CLAIM_LEASE_SECONDS``).
- `_release(repository: Repository, claim: _Claim) -> None` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 740)
- `_claimed(repository: Repository, item_id: str, until: float | None, *, fence: 'BuildFence | None'=None, key: str | None=None, task: str=CLAIM_TASK, producer: str=OWNER_KIND, lease_seconds: int=CLAIM_LEASE_SECONDS) -> Iterator[_Claim | None]` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 754) — Hold the item's durable claim for the block, renewing its lease while the block runs; yields None (and holds nothing) when another process has it.
- `_two_rounds(caller: _Caller, *, purpose: str, first_prompt: str, reprompt: Callable[[Mapping[str, Any]], str], result_model: type[BaseModel], check: Callable[[Any], tuple[Validation, list[str]]], ledger: Callable[..., None], metadata: Mapping[str, Any]) -> tuple[Validation | None, str, int, list[str]]` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 799) — Ask, validate, re-ask once with the reasons, validate; never a third time.
- `_paid(outcome: MapOutcome, caller: _Caller, body: Callable[[], MapOutcome]) -> MapOutcome` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 827) — Run ``body`` with the paid-call failures mapped to an outcome.
- `_settled_build(vault: LoadedVault, repository: Repository, item: PracticeItem, outcome: MapOutcome) -> bool` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 904) — True (``outcome`` set) when no build is due: the revision has a map, or a serve meets a revision whose build was not stored.
- `_build_claimed(vault: LoadedVault, repository: Repository, item: PracticeItem, outcome: MapOutcome, claim: _Claim, *, client: Any | None, clock: Clock | None, deadline: float | None, find: Callable[..., Any] | None) -> MapOutcome` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 924)
- `_route_kinds(value: ApproachMapV1) -> dict[str, int]` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 971)
- `_known_attempts(current: Mapping[str, Any]) -> set[str]` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1312) — The attempts the map has mined: those a route records (Codex review F4).
- `_settled_merge(vault: LoadedVault, repository: Repository, item: PracticeItem, outcome: MapOutcome) -> tuple[dict[str, Any], list[SeedAttempt]] | None` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1377) — ``(current map, new attempts)`` when a merge is due, else None with ``outcome`` set (no map, or nothing new).
- `_merge_claimed(vault: LoadedVault, repository: Repository, item: PracticeItem, outcome: MapOutcome, claim: _Claim, *, client: Any | None, clock: Clock | None, deadline: float | None) -> MapOutcome` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1393)
- `_planned_seeds(seeds: MapSeeds) -> MapSeeds` ([source](../../../../../../src/learnloop/hints/map_builder.py), line 1501) — The dry run's seeds: the worked examples counted at their cap.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]] — imports `BackgroundBuilds`; statically calls `BackgroundBuilds`
- [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]] — imports `module`; statically calls `_alive`, `_claimed`, `_fenced_txn`
- [[Reference/Modules/learnloop/cli/hints|learnloop.cli.hints]] — imports `backfill`, `select_items`; statically calls `backfill`, `select_items`
- [[Reference/Modules/learnloop/hints/map_report|learnloop.hints.map_report]] — imports `LEDGER_TASK`, `OWNER_KIND`, `maps_spend_today`; statically calls `maps_spend_today`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `module`; statically calls `_FencedRepository`, `_claimed`, `_fenced_txn`, `_require_live`, `maps_enabled`, `maps_envelope`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `current_map`; statically calls `current_map`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `current_map`; statically calls `current_map`
- [[Reference/Modules/learnloop/hints/workbench|learnloop.hints.workbench]] — imports `current_map`, `schedule_build_on_serve`; statically calls `current_map`, `schedule_build_on_serve`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `module`; statically calls `_LeaseLost`, `_claimed`, `_holds`, `_renew_live`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `BackgroundBuilds`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `schedule_merge_after_hint`; statically calls `schedule_merge_after_hint`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `schedule_build_on_serve`; statically calls `schedule_build_on_serve`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`; calls `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/approach_maps|learnloop.db.stores.approach_maps]] — imports `module`; calls `current_map`, `insert_map`, `next_version`
- [[Reference/Modules/learnloop/db/stores/judgment_claims|learnloop.db.stores.judgment_claims]] — imports `CLAIMED`, `claim_work`, `holds_claim`, `release_claim`, `renew_claim`; calls `claim_work`, `holds_claim`, `release_claim`, `renew_claim`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/model_calls|learnloop.db.stores.model_calls]] — imports `delete_checkpoint`, `finish_receipt`, `insert_checkpoint`; calls `delete_checkpoint`, `finish_receipt`, `insert_checkpoint`
- [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]] — imports `MAX_ATTEMPTS`, `MAX_SPANS`, `MapSeeds`, `SPAN_CHARS`, `SeedAttempt`, `SeedSpan`, `assemble_seeds`, `item_revision`, `item_side`, `qualifying_attempts`; calls `SeedAttempt`, `SeedSpan`, `assemble_seeds`, `item_revision`, `item_side`, `qualifying_attempts`
- [[Reference/Modules/learnloop/hints/maps|learnloop.hints.maps]] — imports `ApproachMapV1`, `LearnerRouteMergeV1`, `MapContext`, `Validation`, `apply_merge`, `route_counts`, `validate_map`; calls `MapContext`, `apply_merge`, `route_counts`, `validate_map`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `PaidRoute`, `estimated_call_tokens`, `plan_route`, `resolve_client`; calls `PaidCalls`, `estimated_call_tokens`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SharedDailyEnvelope`, `daily_accounting`, `midnight`; calls `SharedDailyEnvelope`, `daily_accounting`, `midnight`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `dataclasses`, `json`, `logging`, `os`, `pathlib`, `sqlite3`, `threading`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]], [[Reference/Modules/learnloop/adaptive_difficulty/claims|learnloop.adaptive_difficulty.claims]], [[Reference/Modules/learnloop/cli/hints|learnloop.cli.hints]], [[Reference/Modules/learnloop/hints/map_report|learnloop.hints.map_report]], [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/approach_map_fakes.py](../../../../../../tests/approach_map_fakes.py) — direct import
- [tests/hint_fakes.py](../../../../../../tests/hint_fakes.py) — direct import
- [tests/test_ad1_codex_review_fixes.py](../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
  - `test_a_vault_switch_fences_the_feature_audit`
  - `test_a_vault_switch_fences_the_outside_forecasters`
- [tests/test_ad1_fix_round4.py](../../../../../../tests/test_ad1_fix_round4.py) — direct import
- [tests/test_ad1_fix_round8.py](../../../../../../tests/test_ad1_fix_round8.py) — direct import
  - `test_any_failure_at_ads_start_receipt_stops_the_dispatch`
  - `test_the_item_forecasts_start_receipt_fails_closed_with_the_right_status`
- [tests/test_ad1_fix_round9.py](../../../../../../tests/test_ad1_fix_round9.py) — direct import
- [tests/test_ad1_outside_and_cli.py](../../../../../../tests/test_ad1_outside_and_cli.py) — direct import
  - `test_background_jobs_run_off_the_request_path_once_each`
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
- [tests/test_approach_map_boundaries.py](../../../../../../tests/test_approach_map_boundaries.py) — direct import
  - `test_grading_prompts_never_carry_or_read_a_stored_map`
- [tests/test_approach_map_replay.py](../../../../../../tests/test_approach_map_replay.py) — direct import
- [tests/test_approach_maps.py](../../../../../../tests/test_approach_maps.py) — direct import
  - `test_a_build_stores_one_validated_version_with_its_receipt_and_verdict`
  - `test_a_failing_or_raising_build_never_reaches_the_serve`
  - `test_a_merge_needs_a_map`
  - `test_a_merge_that_misplaces_an_answer_is_reasked_then_not_stored`
  - `test_a_metered_build_under_the_cap_reserves_and_settles_its_spend`
  - `test_a_read_only_open_builds_nothing`
  - `test_a_revised_item_or_changed_seeds_gets_a_new_row_never_an_update`
  - `test_a_serve_starts_one_background_build_and_never_waits_for_it`
  - `test_f3_a_lapsed_claim_of_a_dead_process_is_taken_over_and_fences_its_commit`
  - `test_f3_a_stale_merge_never_supersedes_a_newer_map`
  - `test_f3_the_durable_claim_keeps_a_second_worker_from_paying`
  - `test_f4_a_seeded_but_unrouted_attempt_is_merged_later`
  - `test_f4_every_seeded_solution_needs_exactly_one_route`
  - `test_f4_only_a_route_assignment_counts_as_mined`
  - `test_f5_an_inherited_rubric_change_is_a_new_revision`
  - `test_l1_a_thread_start_failure_leaves_no_in_flight_mark`
  - `test_m3_a_lapsed_lease_is_never_renewed_by_the_heartbeat`
  - `test_m3_a_lost_heartbeat_stops_the_build_before_its_reask`
  - `test_m3_a_takeover_while_awaiting_a_response_pays_writes_and_stores_nothing_more`
  - `test_m3_an_expired_claim_writes_no_judgment_and_stores_nothing`
  - `test_m3_holds_claim_checks_expiry_and_renewal_never_revives_a_lapsed_lease`
  - `test_m4_a_vault_switch_while_the_provider_is_slow_writes_nothing_to_either_vault`
  - `test_m4_shutdown_and_eof_drain_within_their_bound`
  - `test_m5_a_merge_after_a_revert_stores_a_new_version_of_that_revision`
  - `test_new_correct_answers_gain_a_matching_route_or_open_a_learner_route`
  - `test_r1_the_builders_output_schema_requires_the_structured_fields`
  - `test_r3_a_close_while_a_write_waits_for_the_lock_lands_nothing`
  - `test_r4_a_dropped_receipt_logs_its_call_id`
  - `test_r4_a_generation_is_drained_once`
  - `test_r4_launch_and_close_are_atomic`
  - `test_the_backfill_builds_selected_items_and_skips_current_ones`
  - `test_the_daily_cap_holds_on_metered_routes_and_says_so`
  - `test_the_dry_run_prints_the_estimate_and_writes_nothing`
  - `test_the_hints_report_shows_maps_failures_routes_and_spend`
  - `test_the_inline_build_builds_now_and_stores`
  - `test_the_inline_build_waits_for_a_build_in_flight_and_never_builds_twice`
  - `test_the_kill_switch_builds_nothing_and_reads_nothing`
  - `test_the_route_falls_back_to_the_active_provider_and_an_override_keeps_the_cap`
  - `test_u2_close_never_waits_past_its_bound_on_a_commit_held_by_a_reader`
  - `test_u3_an_expired_lease_is_never_released`
  - `test_without_an_injected_client_the_test_guard_starts_no_build`
  - `test_worked_examples_come_from_t6_under_the_item_bound_policy`
- [tests/test_chat_total_transport_deadline.py](../../../../../../tests/test_chat_total_transport_deadline.py) — direct import
  - `test_rw6b2_f3_the_narration_lease_is_the_enforced_bound_plus_the_claim_margin`
- [tests/test_hint_h2a_review.py](../../../../../../tests/test_hint_h2a_review.py) — direct import
  - `test_f9_a_shown_hint_schedules_the_lazy_learner_route_merge`
  - `test_f9_an_undelivered_hint_schedules_nothing`
  - `test_f9_the_merge_after_a_hint_obeys_the_maps_switches`
- [tests/test_hint_h2b_fix4.py](../../../../../../tests/test_hint_h2b_fix4.py) — direct import
  - `test_f14_reconcile_after_a_revision_never_judges_a_hint_against_the_new_map`
- [tests/test_hint_h2b_rereview.py](../../../../../../tests/test_hint_h2b_rereview.py) — direct import
  - `test_f8_the_bound_counts_placements_not_candidates`
  - `test_f8_unplaceable_candidates_never_starve_a_placeable_one`
- [tests/test_hint_h2b_review.py](../../../../../../tests/test_hint_h2b_review.py) — direct import
  - `test_f5_a_placement_interrupted_after_its_answer_was_checkpointed_is_not_paid_again`
  - `test_f5_a_placement_never_scheduled_is_resumed_when_the_vault_opens`
  - `test_f5_a_retry_answered_from_the_receipt_schedules_the_placement`
- [tests/test_hint_kill_switch.py](../../../../../../tests/test_hint_kill_switch.py) — direct import
  - `test_h2b_outcome_placement_follows_the_adaptive_kill_switch`
- [tests/test_hint_outcome.py](../../../../../../tests/test_hint_outcome.py) — direct import
  - `test_a_closed_registry_starts_nothing_and_a_dead_fence_writes_nothing`
  - `test_a_metered_route_needs_a_price_and_joins_the_maps_envelope`
  - `test_it_runs_in_the_background_after_submit_with_an_injected_client`
  - `test_no_call_in_tests_without_an_injected_client`
- [tests/test_narrative_rollback_overlap.py](../../../../../../tests/test_narrative_rollback_overlap.py) — direct import
  - `test_a_reader_arriving_after_the_claim_delays_the_narrative_by_the_lease_and_doesnt_lose_it`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
  - `test_the_background_build_launcher_never_uses_the_grant`
- [tests/test_reader_digest_narrative.py](../../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_a_holder_that_stops_renewing_is_taken_over_only_after_its_request_timed_out`
  - `test_the_narration_lease_outlives_the_routes_request_timeout`
- [tests/test_reader_rw6b_p2_landing.py](../../../../../../tests/test_reader_rw6b_p2_landing.py) — direct import
  - `test_iii_the_narration_claim_and_the_reading_path_claims_are_distinct_and_independent`
- [tests/test_workbench_check.py](../../../../../../tests/test_workbench_check.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains map builder within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/map_builder.py](../../../../../../src/learnloop/hints/map_builder.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
