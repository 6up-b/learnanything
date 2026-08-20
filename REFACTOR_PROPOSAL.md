# LearnLoop Deep Refactoring Proposal

**Snapshot:** 2026-08-17
**Base revision:** `62fd1f6` (one commit past the archaeology snapshot `d0f25b2`; the working-tree material the archaeology inspected — migration 156, `db/observation_ledger.py`, `canonical_projection_rollout.py`, sidecar transport tests — is now tracked)
**Companion document:** `ARCHITECTURE_ARCHAEOLOGY.md` (descriptive findings). This document is the design phase: it proposes the target architecture and a staged migration plan. **It does not implement anything.**
**Revision:** 2 (2026-08-17) — incorporates the verified outcome of an adversarial agent review of revision 1 and the owner's rebuild-from-attempts requirement (§R). What changed and what was rejected is recorded in the *Revision 2 Changelog* at the end; the second verification round is in §0.

---

## 0. Verification of load-bearing claims

Every archaeology claim that a design decision below depends on was re-verified against `62fd1f6` before being used. Results:

**Confirmed exactly as reported:**

- `SdkCodexClient` and `OpenAIChatProviderClient` implement a set-identical 22-operation structured surface, with the chat client adding two media operations (`run_media_transcription` at `ai/openai_chat.py:199`, `run_media_markdown` at `:218`) and the SDK client adding `interrupt()` (`codex/client.py:881`).
- All shared AI contracts live under `learnloop.codex`: 22 request contexts (`codex/client.py:98–610`), 102 wire models (`codex/schemas.py`), prompt text (`codex/prompts.py`, pure constants), and — importantly — the 22 **prompt builders live in `codex/client.py:1423–2200`**, not in `prompts.py`.
- `ai/openai_chat.py:22–66` imports 22 private underscore-prefixed prompt builders plus `_codex_output_schema` from `codex.client`, duplicating the operation→(builder, schema) dispatch that `SdkCodexClient` also hardcodes.
- Provider identity collapse: `SdkCodexClient.__init__` (`codex/client.py:866`) and `HttpCodexClient.__init__` (`:678`) overwrite `provider_name` with `"codex"` after `ai/codex_sdk.py:44/:53` set the profile name. All eight default task routes point at `codex_low`/`codex_medium` (`config.py:1589–1598`), so provenance stamped at `services/attempts.py:949`, `source_set_synthesis.py:1479`, etc. loses the effort tier.
- Six divergent provider-composition sites (`cli.py:1653–1743`, `learnloop_sidecar/handlers/ai_providers.py:19–131`, `tui/screens/feedback.py:272–311`, `services/startup.py:57–101`, `services/ingest_runner.py` ×4 regions, `learnloop_sidecar/ingest_jobs.py:986–1033`), with the CLI/TUI ignoring named `codex_low`/`codex_medium` profiles and `startup.py:82–84` silently skipping a configured non-Codex fallback.
- Three CLI commands are accidentally Codex-only: `depth edges-author` (`cli.py:473–474`), `depth backfill-rungs` (`cli.py:519–520`), `clarification retry` (`cli.py:3280–3281`) — the generic client implements all three needed operations.
- `auth_mode` has zero behavioral readers (7 occurrences, all write/copy/expose). `settings_store.py:57–67` whitelist omits `input_modalities`, silently disabling native media on settings-derived profiles.
- `[codex]` → `[ai.providers.codex]` normalization is one-directional (`config.py:1926–1997`); both representations are read.
- Dead config knobs confirmed by absence of any reader: `forecasts.default_horizon_days`, `probe.episode.self_graded_evidence_weight`, `recall_coverage.facet_recall_prior_pseudo_count`, `recall_coverage.coverage_epsilon` (the last appears only as a classification string literal in `parameter_registry.py:831`).
- `services/` = exactly 259 files; `__init__.py` is a one-line docstring; exactly 19 modules execute raw SQL; sidecar registers exactly 296 RPC methods and imports 137 service modules; the TUI is live (`cli.py:5576` → `tui/app.py`) and imports exactly 9 service modules.
- `db/repositories.py` = 25,883 lines, 1,010 `def`s, three lazy upward imports into services (`:14794`, `:24898` with an explicit cycle-acknowledging comment, `:25502`); `Repository.__init__` unconditionally applies migrations (`:699`).
- `db/connection.py` is 12 lines: foreign keys on, **no `busy_timeout`, no `journal_mode`**; `PRAGMA busy_timeout = 5000` is hand-re-issued at ~19 call sites inside `repositories.py`.
- `services/ingest.py::ingest_source` has exactly one importer: its own test file. `default_run_legacy_ingest` (`ingest_runner.py:980`) calls `source_ingestion.ingest_canonical_source` (`:1034`); the `exam_ingest` job type aliases the same handler (`:2672`).
- `services/pdf_extraction.py` (legacy one-shot, one production importer: `source_ingestion.py:25`) and `ingest/extractors/` (durable path, 1,474 lines) are two live parallel PDF-extraction implementations; `ingest/hashing.py:94` explicitly acknowledges the duplicated cache-key logic.
- Table candidates: `source_exam_profiles` CRUD (`repositories.py:18362/:18387`) has **zero** callers anywhere; `source_locator_schemes` API is used only by one dedicated test; `learner_theta` has only a generic `find_record` entry and a `debug_time` timestamp entry. All three are empty in every tracked fixture DB (eight fixtures, migration maxima 26→155).
- Dormant modules carry explicit firewalls: `kinship_feature.py:67` `LIVE_ACTIVATION_ENABLED = False` ("consulted by NOTHING"), `shadow_components.py` schema-enforced zero authority, `open_world_gate.py` "NOT implemented … gate NOT MET", `card_outcome_replay.py` test-only prototype, `intent_planner.py` shadow-only pinned by `tests/test_intent_planner.py:78`, `causal_diagnostic_selector.py` shadow-only.
- Owner decision to freeze old-vault compatibility verified verbatim (`spec_p1_shared_substrate.md:1150–1171`, untracked/ignored file), including "kept green, not extended" and "deleting those paths … is a future owner decision".
- `run_doctor()` constructs `Repository` unconditionally (`doctor.py:138`), so a plain doctor run migrates. `SidecarContext.load()` (`context.py:45–77`) migrates, binds/recovers ingest leases, syncs state, refreshes projections, schedules cold probes, and can launch the Codex HTTP service via startup maintenance (`codex/runtime.py:176–186` is a real `subprocess.Popen`).
- The pre-existing test failure is still present at HEAD: `tests/test_activity_backfill.py::test_backfill_populates_substrate_from_fixture` fails with `attempts_replayed == 16`, expected `70` (re-run 2026-08-17).

**Corrections to the archaeology (design below uses the corrected facts):**

- Private `activities._canonical_hash`/`_json` importers: **37 src modules** (plus one aliased use in `substrate_cutover.py:535–536`), not "20+". Zero test importers.
- `learnloop/ingest/` is **not** the durable queue. It is fetch/detect/extract/normalize only (no lease/job/batch concepts). The durable queue lives entirely in `services/ingest_runner.py` + `repositories.py`.
- `AIProviderClient` declares 4 operations **plus** `consume_usage` and identity attributes (`ai/client.py:18–46`).
- Newly found dead code: `AIProviderSelection.uses_legacy_codex` (`ai/routing.py:27–29`) has exactly one consumer, `cli.py::_use_ai_provider` (`:1657`), which itself has **zero callers** — both are unreachable.
- Migration head is now **156** (tracked); the next free number is **157**. Fixture DBs top out at 155, i.e. every fixture is one migration behind HEAD.
- The `[ingest.audio] provider="openrouter"` path (`ingest_runner.py:793–865`) hardcodes the profile name `"openrouter"`, re-derives its own API-key preflight, and reuses `[ingest.native].max_audio_mb` despite being independent of `[ingest.native]`.

**Second verification round (adversarial review of revision 1, verified claim-by-claim):**

- `db/repositories.py:23–28` imports `DocumentIR`/`DocumentBlock`/`DocumentUnit`/`DocumentAsset` from `learnloop.ingest.ir` and `detect_locator_scheme` from `learnloop.ingest.locators` at module level, plus a lazy `ExtractionHealth` import (~`:18045`). Absorbing `learnloop/ingest` into a domain package would therefore create the forbidden `db → domain` edge. Revision 1's `content/sources` absorption is withdrawn.
- **25** migration files contain `PRAGMA foreign_keys`; `migrations/153_variable_rubric_scales.sql` sets it OFF at line 6 and back ON at line 154. `PRAGMA foreign_keys` is a no-op inside an open transaction, so blanket per-script transaction wrapping is unsafe.
- The shipped template sets `[animation] enabled = true` and `[ai.providers.codex] reasoning_effort = "low"` — revision 1's example template flipped both. `PdfIngestConfig.engine` accepts `auto|marker|pypdf|native` (`config.py:1315`), not `datalab`. `AIProviderConfig.type` defaults to `"codex_sdk"` (`config.py:1516`).
- `recall_coverage.severity_examples` **is** consumed at runtime (`recall_calibration.py:133`) — revision 1's move-to-code disposition was wrong.
- Context ownership is not uniform: `MisconceptionMatchContext` is domain-owned (`services/misconceptions.py:77`) and `run_diagnostic_trials` takes `context: Any` (`codex/client.py:973`) — precedent for feature-owned operation contracts.
- Submission receipts live in the sidecar (`handlers/practice.py:632` `_cached_submission` + `repositories.py`), not in `attempts.py` (which only carries `submission_id`) — revision 1's receipt extraction rested on a wrong responsibility claim.
- `probe_robust.use_robust_probe` is true for mvp-0.8 **and its successors including 0.9**, imported at five sites in `probe_episodes` — it is the active probe path, not frozen glue. `p0_projection.record_reinterpretation_if_changed` appends live append-only events (`p0_projection.py:88`).
- Dynamic module references exist and degrade silently: `parameter_registry._resolve_module_constant` builds `learnloop.services.{module}` strings (`:1117`), `open_world_gate` probes `learnloop.services.robust_composition` by name (`:95`), and `scoreboard` resolves `learnloop.services.certification_cold_probe` via `import_module` with a comment stating a missing module becomes a `no_producer` refusal (`:1470`).
- `taxonomy_regrade.py` (active via CLI, `cli.py:6637` region) was missing from revision 1's migration map.
- `grade_diagnostic_fire` is a dormant duck-typed provider seam probed by `diagnostic_gate.py:255` and `persona_gate.py` (×4) but implemented by no client.
- `controller_store.py` imports `Repository`, `Clock`, `new_ulid`, and `activities._json` — evidence for exclusive family SQL ownership, not for connection-only stores.
- Entry points cross-import today: `cli.py` imports `learnloop_sidecar` at five-plus sites (`DurableIngestJobs` at `:2132`; `client_for_provider`/`runtime_for_provider` at `:6130/:6613/:6651/:7515`) and the TUI at one (`tui/screens/practice.py:94`). `sensitivity_certificates.py:126` lazily imports `learnloop.sim.sweep`.
- Rebuild machinery (third round, for §R): `learnloop rebuild-derived-state` (`cli.py:5215`) runs only the per-LO replay (`replay.py:109–158`), stamping a `derived_state_rebuilds` receipt with three named recalibration boundaries (`algorithm_version`, `CANONICAL_PROJECTION_VERSION`, content-addressed `coverage_denominator_version`); the activity substrate, projections, and probes have separate replayers with no umbrella; version sets are already centralized in `assessment_contracts.py:54–64`.

Review claims that failed verification are recorded, with evidence, in the Revision 2 Changelog.

---

## A. Target Architecture

### What changes, in one paragraph

The refactor replaces the two namespaces that currently say nothing about the system — `services` (259 flat modules) and `codex` (provider name owning provider-neutral contracts) — with the boundaries the archaeology showed already govern behavior. `learnloop.ai` becomes a small structured transport plus provider selection/composition; AI operations (context, prompt, result model) become feature-owned, and Codex demotes to one transport implementation. The 259 service modules move into eleven domain packages named in the code's own vocabulary (attempts, learner, scheduling, goals, diagnosis, curriculum, substrate, content, reader, tutor, ops), while `learnloop/ingest` stays as acquisition infrastructure (revision 2 — `db` decodes its IR contracts). One provider composition root replaces six divergent resolution paths, with **manual** (no provider) as a typed outcome. SQL ownership becomes exclusive *write* ownership per table family plus named cross-family read models — the pattern the codebase already invented on its own (`controller_store.py`, `db/observation_ledger.py`) — and `repositories.py` is decomposed structurally behind its existing facade. The generated `learnloop.toml` shrinks from ~681 lines / 214 numeric leaves to a ~60-line file of settings a user can actually decide, **preserving every shipped default**, with everything else remaining modeled, defaulted, and overridable. Init/open gains one shared bootstrap path, validation-before-writes, a schema-gated read-only doctor, and audit-driven migration hardening. Frozen old-vault compatibility gets a named home (`substrate/compat/`) matching the 2026-07-19 owner decision. And making large algorithmic changes cheap becomes a first-class workstream (§R): a table-role registry, one rebuild orchestrator over the existing replayers, replay-completeness and rebuild-equivalence invariants, and a shadow rebuild-and-diff for evaluating a candidate algorithm against the vault's own history.

### Why this is simpler than the current architecture

Counting concepts a developer must hold:

| Concept today | After |
|---|---|
| `services/` — a namespace that predicts nothing; you must know all 259 filenames | 11 domain packages whose names predict membership; `services` deleted |
| `codex` as the conceptual owner of contexts/schemas/prompts/errors, with `ai` importing backwards into it | `ai` owns transport/selection/errors; operation contracts live with their features; `codex` is `ai/providers/codex.py`; the `ai → codex → token_usage` cycle disappears |
| 6 provider-resolution implementations with 4 observable behavioral differences | 1 composition root (`ai.routing.ready_client_for_task`), with a typed `manual` outcome |
| 22 operations × 3 transports = 3 hand-maintained dispatch tables, plus `getattr` capability probing at 17 call sites | each operation defined once, feature-owned, over one `StructuredTransport.complete()`; parity by construction; `supports()` only for genuinely optional capabilities (media, interrupt, legacy HTTP) |
| 2 config representations of the Codex provider (`[codex]` + `[ai.providers.codex]`), synchronized one-way | 1 (`[ai.providers.codex]`); `[codex]` parsed-and-translated for old vaults only |
| 3 ingestion generations | 2 (gen-1 deleted; gen-2 explicitly frozen behind the durable queue) |
| 2 parallel PDF-extraction implementations | 1 (`ingest/extractors`), after a flagged consolidation |
| "Repository owns SQL" (stated) vs 19 raw-SQL services + 3 upward imports (actual) | One enforced rule: each table family has exactly one owning store; `db` never imports domains |
| Generated config ≠ effective config (349 explicit vs ~597 effective leaves) | Template = decisions; `learnloop config effective` shows the whole truth |
| Opening/inspecting a vault silently migrates, syncs, and can spawn a Codex process | Explicit `migrate` step at open; read-only doctor; provider probing only where AI work is actually requested |
| Private symbols as de facto APIs (37 importers of `activities._*`; 7 CLI/sidecar sites importing `_`-names) | Promoted public APIs; import-linter contract forbids new private cross-package imports |

Concepts deliberately **added** (each solves a demonstrated problem, cited): the structured transport with feature-owned operations (kills the triple dispatch, `ai/openai_chat.py:22–66` vs `codex/client.py:933–1170`, with cross-provider parity by construction), the composition root (kills the six variants and their four behavioral divergences), the store rule (already exists — this proposal only blesses and refines it), `substrate/compat` (makes the owner's freeze decision navigable instead of implicit), and the table-role registry (§R — replaces three partial hand-maintained table inventories: each replayer's implicit list, `goal_series` pruning, `debug_time`).

### What this refactor deliberately does not do

- No universal AI-provider framework. The capability surface is exactly what the repository demonstrates: 22 structured operations, 2 media operations, identity/usage, readiness, routing, and Codex-only interruption. Nothing speculative.
- No attempt to break the ~68-module deferred-import SCC in one campaign. The cycles are frozen into an explicit, enforced contract and ratcheted down opportunistically.
- No event-store rewrite, no change to the raw-ledger/projection split, no change to append-only trigger semantics.
- No sidecar protocol changes: all 296 RPC names, payloads, and error codes are invariant.
- No React/TypeScript restructuring beyond documentation (noted in §D as future work).
- No silent behavior changes. Every behavior change is enumerated (there are 14, listed in §O stage descriptions and summarized in §M).

---

## B. Proposed Package Tree

```
src/learnloop/
├── __init__.py, __main__.py
├── clock.py  ids.py  numeric.py  attempt_types.py    # primitives (unchanged)
│
├── config/                    # split of config.py (2,217 lines)
│   ├── schema.py              #   Pydantic models + defaults
│   ├── compat.py              #   legacy normalization ([codex]→profile, probe/error_impacts aliases)
│   ├── template.py            #   the (new, minimal) generated learnloop.toml text
│   └── loader.py              #   TOML/.env/environment loading
│
├── vault/                     # filesystem layout + YAML/Markdown I/O — pure scaffolding only (rev 2)
├── bootstrap.py               # NEW: application-level vault bootstrap shared by CLI init and sidecar
│                              #   create_vault (subject/learner/AI-inheritance orchestration imports
│                              #   domain code, so it lives above vault/)
│
├── db/                        # SQLite mechanics; never imports domain packages (ingest excepted, see below)
│   ├── connection.py          #   + centralized busy_timeout; read-only (mode=ro) attach variant
│   ├── migrate.py             #   + vault-level coordinator: vault lock + FK-pragma-audited transactions
│   ├── table_roles.py         #   NEW (§R): raw/derived/receipt/workflow/compat registry, CI-enforced
│   ├── repositories.py        #   shrinking facade; delegates to stores/; new attach() (no migration)
│   └── stores/                #   per-family write stores + named cross-family read models
│       └── observation_ledger.py   (existing module, relocated)
│
├── ingest/                    # acquisition infrastructure: IR, locators, hashing, fetchers, extractors
│                              #   STAYS top-level (rev 2): db/repositories.py:23 decodes its data
│                              #   contracts — a documented infra edge, not a domain dependency
│
├── ai/                        # structured transport + provider selection/composition (§E)
│   ├── transport.py           #   StructuredTransport protocol: complete(StructuredRequest) → WireModel
│   ├── contexts.py            #   landing zone (from codex/client.py:98–610); each domain adopts its
│   ├── schemas.py             #   own contexts/models/prompts during its Phase-4 move
│   ├── prompts.py             #   prompt text + builders (from codex/prompts.py + client.py:1423–2200)
│   ├── strict_schema.py       #   _codex_output_schema & helpers (from codex/client.py:2202–2467)
│   ├── errors.py              #   AIProviderUnavailable; InvalidOutput/Interrupted/TurnTimeout subclass it
│   ├── client.py              #   provider factory + ResolvedClient (incl. first-class `manual` outcome)
│   ├── routing.py             #   selection precedence + ready_client_for_task() composition root
│   ├── runtime.py             #   readiness reports (existing)
│   ├── usage.py               #   token accounting          (from token_usage.py; cycle broken)
│   ├── runs.py                #   agent-run provenance      (from services/agent_runs.py)
│   ├── multimodal.py          #   media contracts (existing)
│   └── providers/
│       ├── codex.py           #   SdkCodexClient as a transport + checkout/revision/SDK-probe runtime
│       │                      #     + the interrupt capability
│       ├── codex_http.py      #   LegacyHttpOperations adapter — only if the owner retains it
│       │                      #     (decision gates S1.2; it cannot implement complete())
│       ├── openai_chat.py     #   chat transport (existing, re-pointed at ai.* imports)
│       └── openrouter.py      #   OpenRouter specialization (existing)
│
├── attempts/                  # accept an interaction, grade it, append evidence   (~24 modules)
├── learner/                   # learner-state model: mastery, recall, claims, facet state (~25)
├── scheduling/                # what happens next: scheduler + controller + selection (~28)
├── goals/                     # goals, forecasts, certification, exams              (~14)
├── diagnosis/                 # probes, causal attribution, misconceptions, remediation (~45)
├── curriculum/                # commitments, blueprints, golden path, depth, ladder (~20)
├── substrate/                 # activity/card/surface identity + projections        (~15)
│   └── compat/                #   FROZEN old-vault machinery (2026-07-19 owner decision)
├── content/                   # sources in, content out                             (~40)
│   ├── sources/               #   source-facing services (outline/refs/deletion/health/provenance);
│   │                          #     IR/extractors stay in learnloop/ingest (rev 2)
│   ├── pipeline/              #   durable queue runner + job handlers (ingest_runner split)
│   ├── synthesis/             #   inventory, briefs, shards, gates, manifests
│   ├── proposals/             #   proposals, patches, apply protocol, conflict resolution
│   └── authoring/             #   item/exercise generation, authoring gates, persona gates
├── reader/                    # reader UX services, annotations, render views, source objects (~13)
├── tutor/                     # tutor Q&A, teach-back, question queue, promotions   (~7)
├── ops/                       # startup, doctor, maintenance, locks, upgrade, debug, settings (~7, trimmed rev 2)
│
├── cli/                       # split of cli.py (7,957 lines) by sub-app
├── tui/                       # unchanged
└── sim/                       # unchanged

src/learnloop_sidecar/         # unchanged structure; imports narrowed to public APIs
```

Removed as top-level concepts: `services/`, `codex/`, `token_usage.py`, and the `ai/prompts.py` + `ai/schemas.py` dead shims. `learnloop/ingest` **stays** top-level (revision 2): `db/repositories.py:23` decodes its IR contracts, so absorbing it into `content/` would create the forbidden `db → domain` edge.

Naming rules honored: no `utils`, `helpers`, `common`, `misc`, or `managers` packages. `ops/` is the one judgment call — revision 2 trims it to the coherent operational core (startup, doctor, maintenance feed, vault lock, vault upgrade, debug time, settings store) after the review's "dumping ground" objection; `scoreboard` and the parameter-governance modules have their placement reopened (§C), and evaluation harnesses are distributed to their owning domains. `sim/` is classified as an evaluation library importable by domains (`sensitivity_certificates.py:126` → `sim.sweep`), not an entry point.

---

## C. Module Migration Map

Format: `current path → proposed path`. All entries are `MOVE/RENAME` (purely structural) unless annotated. Annotations: **SPLIT** (module divides), **SEM** (accompanied by a deliberate semantic change, detailed in §O), **DEL** (deletion candidate, §L), **FROZEN** (moves into a compatibility area and must not be extended), ⚠ (placement decided at stage-execution time by the owning-spec rule — the module's own docstring cites its governing spec section; the executor confirms against actual imports before moving).

Because per-module prose for 259 modules would be unreadable, the required rationale (current responsibility, proposed responsibility, ownership improvement, callers affected, import consequences, structural-vs-semantic) is given **per target package**, with exceptions called out per module.

### → `learnloop/ai/` (from `codex/`, `ai/`, top level, `services/`)

*Why:* the contracts are LearnLoop-owned (identical 22-operation surface across providers proves it); the `codex` namespace encodes historical provider ownership. *Callers:* 48 src files import `learnloop.codex` today (30 in services), 21 import `learnloop.ai`; all migrate via re-export shims first, then mechanically. *Import consequences:* the `ai → codex` inversion and the `token_usage` cycle disappear. *Structural vs semantic:* moves are structural; §O Stage 1.3 lists the accompanying semantic fixes separately. *Revision 2:* `ai/` is the **landing zone** for contracts moved out of `codex`; each domain adopts its own contexts/prompts/wire models during its Phase-4 move (precedent: `MisconceptionMatchContext` already lives in `services/misconceptions.py:77`). `ai/` ends up owning only transport, selection, errors, usage, and shared wire machinery.

| Current | Proposed | Note |
|---|---|---|
| `codex/client.py:98–610` (22 contexts) | `ai/contexts.py` | SPLIT of client.py |
| `codex/client.py:612–651` (protocol, errors) | `ai/client.py`, `ai/errors.py` | SPLIT; errors renamed with aliases (SEM-free: aliases keep `except CodexUnavailable` working) |
| `codex/client.py:1423–2200` (22 prompt builders) | `ai/prompts.py` → owning features (Phase 4) | SPLIT; builders become public, then travel to the features that own them (S1.2 makes each operation a feature-owned function over the transport) |
| `codex/client.py:2202–2467` (strict schema) | `ai/strict_schema.py` | SPLIT |
| `codex/client.py:856–1421` (`SdkCodexClient`) | `ai/providers/codex.py` | |
| `codex/client.py:668–852` (`HttpCodexClient`) | `ai/providers/codex_http.py` | owner decision **before S1.2** (§K Q1): it cannot implement `complete()`, so it either dies or stays as an explicit `LegacyHttpOperations` adapter |
| `codex/runtime.py` | `ai/providers/codex.py` (merged) | genuinely Codex-specific |
| `codex/schemas.py` | `ai/schemas.py` | replaces the dead one-line shim |
| `codex/prompts.py` | `ai/prompts.py` (merged with builders) | replaces the dead three-line shim |
| `ai/prompts.py`, `ai/schemas.py` (shims) | — | DEL (zero importers, verified) |
| `ai/codex_sdk.py` | `ai/providers/codex.py` (merged) | SEM: identity-collapse fix and `misconception_match_path` fix land here (§O S1.3) |
| `ai/client.py`, `ai/routing.py`, `ai/runtime.py`, `ai/multimodal.py`, `ai/openai_chat.py`, `ai/openrouter.py` | same names / `ai/providers/…` | routing gains the composition root (SEM, §O S1.3) |
| `token_usage.py` | `ai/usage.py` | the blocking cycle is gone once contracts move |
| `services/agent_runs.py` | `ai/runs.py` | provider-independent run provenance |
| `codex/` package | — | DEL after a shim period (§O S1.6) |

### → `learnloop/attempts/` (~24 modules)

*Why:* one reason for change — accepting an interaction, deciding grading authority, appending evidence (archaeology cluster 1). *Callers:* CLI, TUI, sidecar, 114 test files for `attempts` alone. *Consequences:* private symbols consumed by CLI/sidecar (`_resolved_codex_grade`, `_row_to_clarification`) are promoted to public API in the same stage. *Structural* except the promotions.

`attempts`, `post_attempt`, `grading`, `grade_classifier`, `grade_resolution`, `grader_calibration`, `calibration_streams` ⚠, `regrade`, `clarification`, `outcome_schemas`, `observations`, `evidence`, `effective_observation`, `measurement_corrections`, `attempt_trace`, `trace_evidence`, `reveal_ledger`, `salience_firewall`, `surprise`, `ability_transition`, `coldness_receipt` ⚠, `error_taxonomy` → *(see diagnosis)*, `mastery_step_attribution` → *(see learner)*.

### → `learnloop/learner/` (~25 modules)

*Why:* the learner-state model — predicted ability, demonstrated evidence, claims, readiness — is the system's central deliberately-separated quantity set ("evidence, not mastery"). *Callers:* everything that reads state: scheduler, goals, sidecar serializers. *Structural.*

`mastery`, `mastery_step_attribution`, `recall_coverage`, `recall_calibration`, `facet_state_reader` (the version-aware read adapter; its legacy branch is FROZEN behavior), `facet_evidence_timeline`, `facet_diagnostics`, `learner_profile`, `learner_review_feed` ⚠, `hypothesis_claims`, `surfaced_beliefs`, `overconfidence`, `capability_grid`, `capability_mapping`, `identifiability`, `independence_audit`, `inference_precheck`, `residual_diagnostics`, `blueprint_projection` ⚠, `measurement_state`, `assessment_contracts` ⚠, `contract_reachability` ⚠, `session_learning_diff` ⚠, `calibration` ⚠, `familiarity` ⚠.

### → `learnloop/scheduling/` (~28 modules)

*Why:* selection authority is one domain even though two implementations share it; keeping legacy scheduler and staged controller in **one package** puts the cutover seam (`controller_cutover.py:46 STAGED_POLICY_LIVE_FOR_P2`, `scheduler.py:214–215` ownership exclusion, `staged_policy.py:486–512` refusal) inside a single boundary instead of across two. *Callers:* CLI/TUI/sidecar today surfaces, goals, exams. *Structural;* the dual-ownership invariant (§M) is pinned by `test_controller_cutover.py`.

`scheduler`, `staged_policy`, `state_signals`, `controller_actions`, `controller_cutover`, `controller_ownership`, `controller_snapshot`, `controller_store` (becomes the `controller_*`/`attention_*` table store under the §G SQL rule), `constraint_engine`, `interleaving`, `dispersion`, `randomization_layer`, `selection_rewards`, `predictive_targets`, `evsi`, `action_loss`, `intent_planner` (shadow), `shadow_components` (dormant), `prequential` (dormant), `kinship_feature` (dormant), `open_world_gate` (dormant gate), `progression` ⚠, `progression_policy` ⚠, `decay_pressure`, `short_session`, `reentry_adapter`, `reentry_summary`, `fsrs`, `fsrs_fitting`, `review_log`, `evaluation` ⚠ (calibration report over logged scheduling decisions).

### → `learnloop/goals/` (~14 modules)

*Why:* "has the goal been reached, and how do we prove it" — contracts, forecasts, certification, and the held-out exam machinery that certifies goals. *Structural.*

`goal_contracts`, `goal_projection`, `goal_pace`, `goal_certification`, `goal_intent`, `goal_series` (scratch-DB replay; never mutates live DB — verified `goal_series.py:292–335`), `forecast_ledger`, `certification`, `certification_cold_probe`, `receipt_contributions` ⚠, `exam_pool`, `exam_session`, `exam_readiness`, `exam_seeding`, `exam_calibration`. *(Note: `exam_profile.py` does **not** move here — it aggregates exam profiles from sources, spec_source_ingestion_v2 §7, and belongs to `content/synthesis`.)*

### → `learnloop/diagnosis/` (~45 modules)

*Why:* identify a learner-state hypothesis, commission discriminating evidence, choose/verify a repair (archaeology cluster 3). This is the densest part of the deferred-import SCC; co-locating it makes the cycle mostly package-internal. *Structural.*

`probes` (FROZEN legacy paths inside), `probe_audit`, `probe_blocks`, `probe_coverage`, `probe_dialogue`, `probe_episodes`, `probe_families`, `probe_hypotheses`, `probe_instance_generation`, `probe_lifecycle`, `probe_outcome_mapping`, `probe_remint`, `probe_robust` (**ACTIVE** — the current mvp-0.8/0.9 probe path; revision 2 reclassification, only the mvp-0.6/0.7 point path is frozen), `probe_targeting`, `robust_composition`, `calibration_sessions`, `causal_activity_policy`, `causal_attribution`, `causal_diagnostic_selector` (shadow), `causal_factor_deferral`, `causal_health`, `causal_migration` (FROZEN), `causal_orchestrator`, `causal_probe_coherence`, `causal_probe_commissioning`, `causal_selection_audit`, `diagnosis_adjudication`, `diagnostic_augmentation`, `diagnostic_gate`, `diagnostic_pack`, `diagnostic_surface_supply`, `misconceptions`, `missing_vocabulary`, `remediation`, `remediation_intake`, `repair_splice`, `guided_redo`, `failure_triage`, `followups`, `gate_score`, `gate_fit`, `signal_quantiles`, `predictive_eig` ⚠, `error_hunt`, `contrast_pairs`, `discrimination_profiles`, `error_taxonomy`, `error_taxonomy_map`, `taxonomy_regrade` (revision 2: was missing from the map; active via CLI), `longform_trace` ⚠.

### → `learnloop/curriculum/` (~20 modules)

*Why:* durable curricular contracts and structures — what should be learned, in what shape. *Structural.*

`commitments`, `commitment_arcs`, `task_blueprints`, `curriculum_locks`, `pattern_ladder`, `depth_rungs`, `depth_transition`, `depth_edge_authoring`, `rung_backfill` ⚠, `golden_path_assessment`, `golden_path_compose`, `golden_path_confirm`, `golden_path_fixture`, `golden_path_restoration`, `golden_path_run`, `integration_backfill` ⚠, `concepts` ⚠, `confusable_concepts` ⚠, `subject_registry` ⚠, `graph_edit_proposals` ⚠ (produces proposals but its domain is knowledge-map editing).

### → `learnloop/substrate/` (~15 modules + compat)

*Why:* the P1 shared activity/card/surface substrate is the system's identity layer; the compatibility subpackage gives the 2026-07-19 freeze decision a navigable home with a README stating "kept green, not extended — changes here require an explicit compatibility decision." *Callers:* `activities` has ~78 importing files; `state_sync` ~102. The 37 importers of `activities._canonical_hash`/`_json` are migrated to promoted public names (`canonical_hash`, `canonical_json`) in the same stage — that private API is already a package-wide contract in fact. *Structural + API promotion.*

Live: `activities`, `activity_patterns`, `administration_adapters`, `card_lineage`, `instrument_serving`, `surface_mint`, `surface_pool` ⚠, `canonical_projection`, `canonical_projection_rollout`, `replay` (the live rebuild engine — §R), `state_sync` (live reconciliation; its FSRS-placeholder role is already documented as superseded by `card_lineage` for new administrations), `p0_projection` (revision 2 reclassification: its cutover activation is compat-flavored but it appends **live** reinterpretation events — `p0_projection.py:88` — so it must not be labeled frozen).
FROZEN → `substrate/compat/`: `activity_backfill`, `substrate_cutover`, `card_outcome_replay` (dormant prototype), `vault_upgrade` ⚠ (or `ops`; it is the mvp-0.7 activation machinery, frozen).

### → `learnloop/content/` (~45 modules, five subpackages)

*Why:* one pipeline — external material in, gated proposals out — but with four genuinely different reasons for change (acquisition, orchestration, synthesis, application) plus authoring. This is the only domain that warrants subpackages; everything else stays flat. *Consequences (revision 2):* `learnloop/ingest/` is **not** absorbed — `db/repositories.py:23` imports its IR contracts at module level, so it stays top-level infrastructure; `content/sources/` holds only the service-level source modules. *Structural except:* the `ingest_runner` SPLIT (§O S4.8a) and the audio-route change (S4.8b); gen-1 deletion is S4.8c.

- `content/sources/`: `source_outline`, `source_refs`, `source_deletion`, `source_outcome_analytics`, `role_authority`, `extraction_health`, `block_health`, `provenance`, `math_text` ⚠, `pdf_extraction` (consolidation onto `learnloop/ingest/extractors` is a **flagged behavioral migration** — output format/cache identity may differ — not scheduled by this proposal).
- `content/pipeline/`: `ingest_runner` **SPLIT** into `runner.py` (lease/heartbeat/claim/retry/recovery — pure queue mechanics) and `jobs.py` (the 14+ domain handlers; provider/media resolution delegated to the §E composition root); `quick_add`, `build_plan`, `acquisition_preview`, `revision_refresh`, `source_ingestion` (FROZEN gen-2, still the implementation behind the durable `legacy_ingest`/`exam_ingest` jobs), `ingest` **DEL** (gen-1; sole importer is its own test).
- `content/synthesis/`: `source_unit_inventory`, `source_unit_selection`, `source_set_synthesis`, `synthesis_manifests`, `synthesis_gates`, `synthesis_eval`, `brief`, `append_neighborhood`, `source_append`, `source_coverage`, `coverage_rollup`, `study_map_diff`, `exam_profile`, `facet_candidates` ⚠, `facet_mint_gate`, `facet_doctor`.
- `content/proposals/`: `proposals`, `patches`, `apply_protocol`, `conflict_resolution`.
- `content/authoring/`: `item_authoring`, `exercise_authoring`, `practice_generation`, `practice_leakage`, `authoring_gates`, `persona_gate`, `persona_realism`, `contract_commissioning`, `conjunctive_items` ⚠, `laddered_stems` ⚠, `rung_variants` ⚠, `concept_animation` ⚠.

### → `learnloop/reader/` (~13) and `learnloop/tutor/` (~7)

*Why:* two user-facing features with distinct state and UI semantics (archaeology cluster 7); kept separate rather than merged because they share only the AI contracts. *Structural.*

Reader: `reader_authoring`, `reader_capture`, `reader_dialogue`, `reader_guidance`, `reader_progression`, `reader_quick_check`, `reader_requests`, `reader_restoration`, `annotations`, `span_view`, `source_render_views`, `source_objects`, `source_search`, `source_review` ⚠.
Tutor: `tutor_qa`, `teach_back`, `promotions`, `durable_promotion`, `question_signal`, `question_queue`.

### → `learnloop/ops/` (~7, trimmed in revision 2)

*Why:* operational integrity of a vault — diagnostics, maintenance, locking, upgrade, machine-local settings. Trimmed to this coherent core after the review's "dumping ground" objection; evaluation harnesses went to their owning domains (`synthesis_eval` → content, `exam_calibration` → goals, `evaluation` → scheduling, `persona_realism` → content/authoring). *Structural.*

`startup`, `doctor`, `maintenance_feed`, `vault_lock`, `debug_time`, `settings_store`, `vault_upgrade` (if not `substrate/compat`).

Placement reopened, decided at stage time: `scoreboard` (cross-domain read-only report — ops or a reporting home), and the parameter-governance trio `parameter_registry`, `sensitivity_certificates`, `fitted_params` (candidates: `learner`, `scheduling`, or a small `params/` grouping if the three prove cohesive; note `sensitivity_certificates.py:126` lazily imports `learnloop.sim.sweep`, which is why `sim` is classified as an evaluation library, §B).

### → `learnloop/cli/` (from `cli.py`, 7,957 lines)

*Why:* 146 commands / 18 sub-apps in one file, mixing parsing, presentation, composition, and workflow policy. SPLIT by existing sub-app boundaries (one module per sub-app; shared output helpers in `cli/render.py` — a named presentational concern, not a "utils"). Composition moves to the §E root. *Structural except* the three Codex-only commands (SEM, fixed in §O S1.3 before the split).

### Unmoved

`clock.py`, `ids.py`, `numeric.py`, `attempt_types.py`, `vault/*` (gains `bootstrap.py`), `db/connection.py`, `db/migrate.py`, `tui/*`, `sim/*`, `learnloop_sidecar/*` (imports re-pointed only), `apps/learnloop-tauri/*`.

⚠ tally: ~30 modules carry the placement-to-confirm marker (including the reopened `ops` governance modules). Rule at stage time: the module's governing spec citation (present in 200+ docstrings) plus its actual import fan-in decide; a wrong guess is a one-line move later, so this uncertainty is cheap and honest.

**Dynamic references (revision 2, move-critical):** `parameter_registry` constructs `learnloop.services.{module}` strings at runtime, `open_world_gate` probes service modules by name, and `scoreboard` resolves its producer via `import_module` — with a missing module silently becoming a `no_producer` refusal. These strings are first-class migration dependencies: S0.2 inventories them and adds functional discovery tests; every move stage updates them alongside imports.

---

## D. Large-Module Refactor Plan

Sizes re-measured at `62fd1f6`. The bar for splitting is a *genuine conceptual boundary with different reasons for change*; line count alone never qualifies.

| Module | Lines | Decision | Rationale |
|---|---|---|---|
| `db/repositories.py` | 25,883 | **SPLIT** (structural, staged) | Genuine boundaries: table families (the schema's own grouping). Mechanics: extract per-family store classes into `db/stores/<family>.py`; `Repository` becomes a facade composing them, so all ~1,010 methods keep their call signatures and zero callers churn per stage. The codebase already validated this pattern twice (`controller_store.py:1–6` — "Kept out of the 18k-line repositories.py"; `db/observation_ledger.py`). What stays: facade, `find_record`, connection pinning. What moves: family method groups + their `_decode_*` helpers. Testing: existing repository-touching tests already cover the surface; each extraction stage is behavior-preserving and runs the full suite. Stop-anywhere property: each extracted family is independently valuable; there is no obligation to finish all families. Revision 2 refinement: the rule is write-ownership *exclusivity*, not store purity or location — `controller_store.py` imports `Repository`/`Clock`/service helpers and remains a legitimate domain-side owner; named cross-family read models (`observation_ledger.py` deliberately joins six families) are a separate, sanctioned category. |
| `cli.py` | 7,957 | **SPLIT** | By existing sub-app boundaries (18 sub-apps). Presentation stays with each command; provider composition leaves for the §E root; the two private service imports (`cli.py:3236`, `:5755`) are replaced by promoted public APIs. Semantic changes are quarantined into S1.3 (three Codex-only commands) *before* the mechanical split so the move diff is inert. |
| `apps/learnloop-tauri/src/api/dto.ts` | 6,109 | **KEEP (defer)** | Out of Python-refactor scope. Recorded as future work: split by screen domain and add a generated-or-tested contract check against sidecar serializers. Doing it now would couple this refactor to the weakest-tested layer (no React test suite). |
| `services/attempts.py` | 3,305 | **KEEP** (revised in rev 2) | Revision 1 proposed extracting submission receipts — withdrawn: that rested on a wrong responsibility claim. Receipts live in the sidecar (`handlers/practice.py:632` `_cached_submission`) and `repositories.py`; `attempts.py` only carries `submission_id`. The `apply_attempt` ordering (receipt → grade → raw evidence → legacy+canonical state → post-attempt) is a load-bearing protocol and stays intact. The only permitted extraction is the provider-grading glue (context assembly + provenance stamping), and only if it separates without touching the ordering; default is keep whole. `_resolved_codex_grade` is promoted to a public name (two external importers today). Testing: 114 test files import `attempts`; the move stage runs them all plus the post-attempt pipeline tests. |
| `services/causal_orchestrator.py` | 3,301 | **KEEP** | Dense diagnostic protocol with append-only receipt semantics and shadow hooks. No intuitive internal boundary that would not cut through the orchestration ordering. Revisit only after the diagnosis package settles; a large cohesive module is preferable here. |
| `services/ingest_runner.py` | 3,198 | **SPLIT** | Three verified reasons for change in one file: queue mechanics (lease/heartbeat/claim/retry/stale recovery — `:2802` onward), 14+ domain job handlers (`handle_*`, dispatch table `:2671`), and provider/media resolution (four separate resolution regions). Queue mechanics → `content/pipeline/runner.py`; handlers → `content/pipeline/jobs.py` (one module first — further splitting only if it proves warranted); provider/media resolution → the §E composition root + `content/sources` media routing. Boundary: handlers receive a context object (already exists: `ctx.services`, `:203`); the runner knows job names, not domains. Testing: ingest queue/recovery tests are the invariant anchors; highest-churn module (34 commits) so this split has the best odds of paying for itself. |
| `services/probe_episodes.py` | 2,659 | **KEEP** | Adaptive-episode state machine; internally ordered (selection → presentation → observation → stopping). Cohesive. |
| `services/source_set_synthesis.py` | 2,642 | **PARTIALLY EXTRACT** | Manifest/identity logic and deterministic gates are already separate modules; extract only the provider-call plumbing (client resolution + `getattr` probing, `:1462`, `:2337`) onto the composition root and capability API. Shard orchestration stays. |
| `codex/client.py` | 2,467 | **SPLIT** | Five verified regions (§0) with five different reasons for change. The §B `ai/` layout is exactly this split. |
| `services/proposals.py` | 2,340 | **KEEP** | Write-ahead protocol; moves intact to `content/proposals/`. Splitting a recovery protocol is how partial-application bugs are born. |
| `config.py` | 2,217 | **SPLIT** | Four regions with different consumers: schema (everyone), template (init only), compat normalization (load only), env loading (load only). See §B `config/`. |
| `codex/schemas.py` | 2,149 | **KEEP** (move whole) | 104 wire models, one concern. |
| `services/source_ingestion.py` | 2,032 | **KEEP, FROZEN** | Gen-2 legacy generation still wired into the durable `legacy_ingest` job. Do not decompose code that is a candidate for retirement (§K); freeze and document instead. |
| `services/scheduler.py` | 1,708 | **KEEP** | Cutover-sensitive; shares the exposure ledger with the staged controller. Splitting risks the exactly-one-owner invariant for zero navigational gain once it lives in `scheduling/`. |
| `cli.py` upgrade/`vault_upgrade` paths | — | **KEEP, FROZEN** | Compatibility machinery under the owner freeze. |

---

## E. AI Provider Architecture

### The capability surface LearnLoop actually requires (derived, not assumed)

From verified call sites, LearnLoop needs exactly this from a provider:

1. **Structured operations** — accept a typed LearnLoop context, return a candidate validated against a LearnLoop wire model. There are exactly 22 today (§0 table). This is the core surface; both major transports implement all 22.
2. **Media operations** — audio→transcript and PDF→Markdown, used by native ingest when the routed profile declares the modality (`ingest.native` + `input_modalities`). Chat-family transports only.
3. **Identity and usage** — `provider_name` / `provider_type` / `model` on every client; accumulated token usage via `consume_usage`; agent-run provenance recording.
4. **Capability availability** — optional workflows must be able to ask "can this client do X" and degrade or refuse (17 verified `getattr` sites today).
5. **Selection and constrained fallback** — explicit > `LEARNLOOP_AI_PROVIDER` > task route > `ai.active_provider`; fallback suppressed for explicit/env selections (`ai/routing.py:39–53`). **Manual** (no provider) is a supported resolution outcome — grading already treats it as a synthetic mode (`learnloop_sidecar/handlers/ai_providers.py:16`) — and must stay first-class.
6. **Readiness** — a pre-flight report distinguishing not-configured / auth-required / unavailable / ready.
7. **Error discrimination** — unavailable vs invalid-output vs timeout vs interrupted, where callers observably branch on them.
8. **Locality of authority** — the provider never writes vault state; LearnLoop gates and persists. (Already an invariant; the architecture must not accidentally weaken it.)

Not requirements (present in no caller): streaming, provider-side conversation threads (Tutor continuity is reconstructed from stored transcripts), video, tool execution against the vault.

### Classification

**PROVIDER-INDEPENDENT** (owned by `learnloop.ai`) — *revised in revision 2* from a 22-method protocol to a transport, after the adversarial review's cohesion argument survived verification (domain-owned contexts already exist: `MisconceptionMatchContext` in `services/misconceptions.py:77`; `run_diagnostic_trials` takes `context: Any`):

- **`StructuredTransport`** — the entire provider protocol for structured work: `complete(request: StructuredRequest) → WireModel`, where the request carries purpose (the SDK's provenance/debug label), prompt, wire model, and timeout. Validation and the one-repair expectation are interface semantics; repair/retry mechanics stay per-transport (existing observable differences preserved, per the archaeology's invariants).
- **Feature-owned operations.** Each of the 22 operations becomes one plain function owned by its feature — context dataclass, prompt builder, wire model, and a single `complete()` call, colocated with the workflow that uses it. Parity across providers is **by construction**: any transport can execute any operation, so the triple-maintained dispatch (`codex/client.py:933–1170`, `openai_chat.py:133–197`, HTTP's eight) and the 22-symbol private import block disappear without a central registry. Adding an operation touches only its owning feature.
- **Capability checks shrink to the genuinely optional**: media operations, `interrupt`, and (if retained) the legacy HTTP adapter's 8-operation surface, via `supports()`. The 17 `getattr` probes for structured operations become unconditional-with-client; degradation remains only for the **manual**/no-client outcome and legacy HTTP. This is why the HTTP decision (§K Q1) gates the design stage.
- Errors: `AIProviderUnavailable` in `ai/errors.py`, with `AIInvalidOutput`, `AIInterrupted`, `AITurnTimeout` **subclassing it** — existing broad `except CodexUnavailable` behavior is preserved by construction (review-accepted refinement). The `Codex*` names remain as aliases until callers migrate; `ai/openai_chat.py` raising a Codex-named error today (`:311` etc.) is exactly the leak this fixes.
- Selection/routing (`ai/routing.py`, unchanged precedence) plus a new **composition root**: `ready_client_for_task(config, task, *, explicit=None, vault_root) → ResolvedClient(client | manual, selection, runtime_report, fallback)` — the sidecar's resolution semantics (`ai_providers.py:88–101`, the one variant that honors named profiles) become the single implementation, and **manual is a typed outcome, not an absence**. Also `ROUTE_FOR_OPERATION`: an in-code map documenting which operations inherit which route (source inventory/synthesis → `canonical_ingest`, promotion classification → `tutor_qa`, promotion content → `authoring`, …). Explicit inheritance instead of caller folklore; the route set grows by exactly one (`transcription`, §H) and no further.
- Strict-schema conversion (`ai/strict_schema.py`), readiness report shape (`ai/runtime.py`), usage (`ai/usage.py`), run provenance (`ai/runs.py`), multimodal content contracts (`ai/multimodal.py`).
- **Contract staging:** S1.1 still moves all contexts/schemas/prompts out of `codex` into `ai/` as one pure mechanical move (a single landing zone, shims intact); each domain then adopts its own operations during its Phase-4 move. `ai/` ends up owning only transport, selection, errors, usage, and shared wire machinery.

**CODEX IMPLEMENTATION** (`ai/providers/codex.py`):

- SDK transport: thread-per-call, vault-root working directory, wall-clock timeout state, interruption + forced close, billed-usage-on-timeout, structured-transport regeneration pre-pass, debug prompt/schema logging.
- Runtime: checkout path/revision pinning, `openai_codex` import probe, HTTP-service startup/health (`subprocess.Popen` at `codex/runtime.py:176–186`).
- Implements `StructuredTransport`; `interrupt` is its one extra declared capability.

**CODEX HTTP** (`ai/providers/codex_http.py`, §K owner decision — resolved *before* S1.2 in revision 2): endpoint-per-operation semantics mean it genuinely **cannot implement `complete()`**. If retained, it stays an explicitly-named `LegacyHttpOperations` adapter with its 8 operations behind `supports()` and no repair round (existing difference, preserved). If retired, structured-operation degradation collapses to the manual/no-client case only.

**OPENROUTER IMPLEMENTATION** (`ai/providers/openrouter.py`, subclassing the shared chat transport):

- Endpoint/key defaults, attribution headers, `reasoning.effort` payload (replacing the DeepSeek `thinking` dialect).
- Inherits from `openai_chat`: 429/5xx retry, one text-only repair, `json_object`/strict `json_schema` modes, native audio/PDF content parts.
- Implements `StructuredTransport`; media operations are available when the profile declares the modality (config-declared, never runtime-probed — the existing `multimodal.py` rule, kept).

**PROVIDER-SPECIFIC** (deliberately *not* normalized — no lowest-common-denominator pretence):

- Interruption (Codex SDK only). Callers that care check `supports("interrupt")`.
- Local checkout/revision/subscription auth (Codex only) — stays in the Codex provider config model (§H splits the profile schema by type so chat profiles stop carrying `checkout_path` et al.).
- Repair/retry/timeout mechanics differ per transport and remain observable behavior (invariant in the archaeology's list); the shared contract only promises "validated candidate or typed error."
- Native media availability is config-declared per profile (`input_modalities`), never runtime-probed — the existing `ai/multimodal.py` design, kept.

### What this is *not*

No plugin registry, no entry-points discovery, no abstract "Provider" base with speculative hooks, no per-operation config — and, as of revision 2, **no 22-method provider protocol and no central operation registry either**: the adversarial review demonstrated the transport shape is strictly fewer concepts, and its factual premises verified. Two concrete transports (Codex SDK, OpenAI-compatible chat) plus one thin specialization (OpenRouter) plus, if the owner retains it, one explicitly legacy adapter.

---

## F. Codex/OpenRouter Capability Matrix

Current state (verified) and target state. "Chat" = `OpenAIChatProviderClient` base; OpenRouter inherits unless noted.

| Capability / workflow | Codex SDK | Codex HTTP | OpenRouter (chat) | Current status | Target |
|---|---|---|---|---|---|
| 22 structured operations (authoring, canonical ingest, grading, tutor QA, teach-back ×2, misconception match, promotion analysis, diagnostic trials, probe instance/dialogue/family, reader presets, quick check, rung backfill, exercise authoring, depth edges, source inventory, source-set synthesis, concept graph, animation, append reconciliation) | ✅ all 22 | ⚠ 8 only | ✅ all 22 | Shared and working | Feature-owned operations over `StructuredTransport`; parity by construction; HTTP (if retained) declares its 8 via `supports()` |
| Structured-output validation + repair | ✅ regeneration + 1 repair | ❌ validate only | ✅ 1 repair | Differs by transport | Unchanged (provider-specific, documented) |
| Strict `json_schema` mode | ✅ (SDK schema) | n/a | ✅ optional; default `json_object` | Open-keyed maps erased under strict shape (`test_codex_output_schema.py`) | Unchanged; keep `json_object` default for OpenRouter; limitation documented |
| Native audio transcription | ❌ | ❌ | ✅ mp3/wav | Working, but **two** OpenRouter selection paths (`ingest_runner.py:646–676` routed vs `:793–865` hardcoded clone) | One resolution path via the new `transcription` route + config normalization of `[ingest.audio]` (own stage, S4.8b); other formats: **documented as unavailable** |
| Native whole-PDF → Markdown | ❌ | ❌ | ✅ | Working | Unchanged; page selection: **provider limitation, documented** |
| Task routing + constrained fallback | ✅ | ✅ | ✅ | 8 routes; other ops inherit implicitly in caller code | `ROUTE_FOR_OPERATION` makes inheritance explicit; 9 routes (revision 2 adds `transcription`) |
| Provider/model provenance on agent runs | ⚠ collapses to `"codex"` | ⚠ collapses | ✅ | Named Codex profiles lose identity (`codex/client.py:866`) | **Fixed** — profile name preserved (S1.3, behavior change, pinned by new test) |
| Token usage accounting | ✅ incl. billed failures | ✅ | ✅ pre-validation | Working | Unchanged |
| Readiness check | ✅ deep (checkout/SDK/HTTP health) | ✅ | ⚠ env-var presence only | Chat "ready" is weak; unused healthcheck hook exists (`ai/runtime.py:60`) | Keep env-var check as the default; **delete the never-used hook** unless S1.3 wires it — decided at stage time |
| In-flight interruption | ✅ | ❌ | ❌ | Codex-specific | Explicitly provider-specific via `supports("interrupt")` |
| Persistent provider threads | per-call threads | ❌ | ❌ | Not a LearnLoop requirement (Tutor replays stored context) | **Documented as not required** |
| Streaming | ❌ | ❌ | ❌ | Not implemented, no caller | **Not built** (YAGNI) |
| `depth edges-author` CLI | ✅ | — | ❌ *accidentally* | Coupled to Codex (`cli.py:473`) | **Fixed** — routed via composition root |
| `depth backfill-rungs` CLI | ✅ | — | ❌ *accidentally* | `cli.py:519` | **Fixed** |
| `clarification retry` CLI | ✅ | — | ❌ *accidentally* | `cli.py:3280` | **Fixed** |
| Startup deferred-regrade fallback | ✅ | ✅ | ⚠ skipped when primary is Codex-family and unready (`startup.py:82–84`) | Configured non-Codex fallback silently unused | **Fixed** — composition root fallback rules apply everywhere |
| Settings-derived profiles keep modalities | n/a | n/a | ❌ whitelist drops `input_modalities` (`settings_store.py:57–67`) | Selecting a model in Settings can disable native media | **Fixed** (S1.3) + regression test |
| Local checkout / subscription auth | ✅ | ✅ | n/a | Codex-specific | Stays in Codex provider config only (§H type split) |

Result after target: **any workflow the chat transport can execute runs on an OpenRouter key with no Codex path involved.** The only OpenRouter-excluded behaviors are genuine provider differences (interruption, checkout auth) — none of them gate a LearnLoop workflow; they only change ergonomics (no mid-call cancel).

**Scope of the parity claim (revision 2):** everything above is **code-path parity** — same operations, same contexts, same validation, pinned by tests against fakes. Live model/provider *semantic* parity (auth, model availability, structured-output quality, quota, modality behavior on real endpoints) is untested and stays on the deferred list (§N), as does the never-exercised chat healthcheck hook.

---

## Codex → AI Migration: dependency classification and order

Every meaningful dependency on `learnloop.codex` (48 src files), classified:

| Dependency | Sites | Classification | Disposition |
|---|---|---|---|
| Context/schema/prompt/error imports (`from learnloop.codex.client import GradingContext, …`, `codex.schemas`, `codex.prompts`) | ~30 service modules, `ai/client.py:7,14`, `ai/openai_chat.py:22–88`, TUI, sidecar, 55+ test files | **Rename/move only** | Re-pointed to `learnloop.ai.*`; shims keep old paths alive until the final deletion stage |
| The 22 private prompt-builder imports in `ai/openai_chat.py:22–66` | 1 file, 22 symbols | **Provider-independent functionality in the wrong namespace** | The import block disappears when each operation is defined once, feature-owned, over the transport (S1.2) |
| `_codex_output_schema` used by chat `json_schema` mode (`openai_chat.py:325–333`) | 1 | **Provider-independent** | → `ai/strict_schema.py` |
| `make_codex_client` / `CodexClient` construction | `cli.py:473,519,3280` (three commands), `cli.py:1653–1743`, `tui/screens/feedback.py:272–311`, `startup.py:61–78`, `ingest_runner.py` ×4, `ingest_jobs.py:986–1033` | **Accidental Codex coupling** (the generic client implements every needed operation) | All eight sites migrate to the composition root; behavioral fixes enumerated in S1.3 |
| `check_codex_runtime` readiness probing | same sites + `ai/runtime.py:71–87` | **Codex implementation detail** behind a shared report | Stays, relocated into `ai/providers/codex.py`; reached only through `ai.runtime` |
| `CodexConfig` / `[codex]` TOML | `config.py`, legacy callers above, `learnloop_sidecar/context.py:343` | **Behavior requiring redesign** (duplicate representation) | §H: typed provider profiles; `[codex]` becomes parse-and-translate compat |
| `token_usage.py` placement constraint (`token_usage.py:16–19`) | 1 | **Accidental coupling** (cycle artifact) | Cycle disappears when contracts move; file → `ai/usage.py` |
| `openai_codex` external package imports | `codex/client.py:1244–1246`, `codex/runtime.py:255` only | **Codex implementation detail** (already well isolated) | Move with the provider; nothing else changes |

Migration order (deliberately: decisions → abstraction → callers → providers → relocation → deletion; each is a separate reviewable stage in §O):

0. **Owner decisions first (revision 2)** — the HTTP adapter's fate (§K Q1) and provenance direction (§K Q2) are decided before any interface design lands: HTTP cannot implement `complete()`, so its retention determines whether a `LegacyHttpOperations` adapter exists at all.
1. **Abstraction establishment** — move contracts into `ai/` (landing zone) with `codex/*` re-export shims (imports keep working; diff is file moves plus one import line per shim).
2. **Transport + feature-owned operations** — `StructuredTransport.complete()` lands; each of the 22 operations becomes one feature-owned function (context + prompt + wire model + one `complete()` call); the 17 `getattr` probes for structured operations become unconditional-with-client (degradation remains only for manual/no-client and, if retained, the HTTP adapter via `supports()`).
3. **Caller migration** — composition root lands (with the typed `manual` outcome); all eight resolution sites and the three Codex-only CLI commands migrate; behavioral fixes are made here, test-pinned, and nowhere else.
4. **Provider relocation** — `SdkCodexClient` + runtime → `ai/providers/codex.py`; HTTP adapter → `ai/providers/codex_http.py`; `ai/codex_sdk.py` merged away.
5. **Deletion** — dead shims (`ai/prompts.py`, `ai/schemas.py` — zero importers today), then the `codex/` shim package once no imports remain (enforced by grep + import-linter).

There is **no** single enormous rename commit: at every stage both spellings work, and the tree flips only after callers are clean.

---

## G. `services` Reorganization: structure and dependency rules

The subpackage purposes, memberships, and coherence arguments are in §C. This section states the rules that make the move architectural rather than cosmetic — the archaeology is explicit that a file move alone would "preserve the same architecture under new paths."

### Does a top-level `services` package remain useful?

**No.** After the eleven domain packages exist, `services` names nothing: it is not a layer (it contained four kinds of code), not a domain, and not an ownership boundary. It is deleted in the final move stage. The *concept* it gestured at — "application behavior lives below entry points and above persistence" — survives as the dependency rules below, which are checkable, unlike a directory name.

### Dependency rules (enforced by import-linter from Stage 0.2)

Allowed, by layer:

1. **Primitives** (`clock`, `ids`, `numeric`, `attempt_types`): import nothing internal.
2. **Infrastructure** (`config`, `vault`, `db`, `ingest`, `ai`): may import primitives and each other downward (`vault → config, db`; `ai → config`; **`db → ingest` is a documented edge** — `repositories.py:23` decodes IR contracts); **`db` and `ai` may never import domain packages** (`db` violates this today at three verified sites).
3. **Domain packages** (the eleven, plus `sim` as an evaluation library at this level): may import primitives, infrastructure, and *other domains' public names*. Cross-domain imports of underscore-prefixed symbols are forbidden (37+7 violations today, all fixed by promotion during moves).
4. **Entry points/adapters** (`cli`, `tui`, `learnloop_sidecar`): may import domain public names and infrastructure; never underscore symbols; never each other. **Known current violations** (revision 2, verified): `cli.py` imports `learnloop_sidecar` at five-plus sites and the TUI at one. Four are the `ai_providers` helpers (`client_for_provider`/`runtime_for_provider`) that dissolve into the composition root (S1.3); the TUI's `ready_grading_provider` likewise; the remaining `DurableIngestJobs` import (`cli.py:2132`) is fixed by moving the shared job engine into `content/pipeline` (S4.8a).

Explicitly tolerated, by contract file rather than by silence:

- The **deferred-import SCC** (~68 modules across attempts/diagnosis/substrate/scheduling) is codified as an explicit allowlist of known cycles in the import-linter config, with a ratchet: the list may shrink, never grow. Function-local imports remain legal *only* for edges on that list; a new function-local cross-package import fails CI. This is honest about what the refactor does not fix while preventing regression.
- `attempts.post_attempt` is the sanctioned cross-domain orchestration point (it exists to dispatch obligations into diagnosis/scheduling/goals); its wide fan-out is by design, documented in the module.

### Inappropriate dependencies to remove (each is a §O stage or sub-stage)

| Violation | Evidence | Fix |
|---|---|---|
| `db → services` (3 lazy imports) | `repositories.py:14794, 24898, 25502` | Move the policy constants/lookups (`CAUSAL_ACTIVITY_POLICY_VERSION`, `policy_for_class`, `CANONICAL_STATE_VERSIONS`, `CONTAMINATION_PRECEDENCE`) into a `db`-legal location or pass them in as arguments; the classification-append and legacy-write-guard methods take policy as parameters |
| CLI/sidecar importing `_`-private service symbols | 7 sites (§0) | Promote the symbols in their new domain homes; forbid recurrence via linter |
| 37 importers of `activities._canonical_hash`/`_json` | verified list | Promote to `substrate.activities.canonical_hash/canonical_json` (S4.0) — the underscore is a fiction |
| Raw SQL in 19 services | verified list | Under the store rule (below), 6 of the 19 are *already conformant stores in the wrong directory* (`controller_store`, `controller_ownership`, `shadow_components`, `prequential`, `kinship_feature`, `open_world_gate` — all own their post-096 tables); they are renamed/relocated, not rewritten. The rest (`probe_episodes`, `source_append`, `reader_authoring`, `study_map_diff`, `scoreboard`, `goal_series`, `debug_time`, `activity_patterns`, `concepts`, `depth_edge_authoring`, `probe_audit`, `action_loss`, `ingest_runner`) migrate their SQL into their domain's store module during that domain's move stage — *opportunistically, not as a big-bang* |
| `Repository` as second application layer | 25,883 lines, 1,010 defs | §D split; SQL-ownership rule below |

### SQL ownership rule (replaces the broken "Repository owns SQL" spec statement)

> Every table family has exactly one module owning its **writes**. New tables get an owning store from day one (already de facto practice — `controller_store.py:1–6`, `db/observation_ledger.py`). Named **cross-family read models** (e.g. `observation_ledger`, which deliberately joins six families) are a separate, sanctioned category. Ownership means exclusivity, not location or purity (revision 2): extracted stores land in `db/stores/`; existing domain-side owners stay put — `controller_store` imports `Repository`, `Clock`, and service helpers and remains a legitimate family owner. `Repository` remains as a facade over extracted stores plus the not-yet-extracted remainder; no *new* methods are added to the remainder.

This is a smaller claim than the P1 spec's rule (`spec_p1_shared_substrate.md:723–725`) but, unlike it, matches reality and is enforceable: a CI check greps for SQL string literals outside `db/stores/` + registered domain stores.

---

## H. `learnloop.toml` Refactor Proposal

### Principle

The generated file should contain **only settings a user can meaningfully decide** at vault creation: where state lives, which algorithm generation the vault is on, which AI providers to use, and which optional external-facing features are on. Everything else stays modeled with defaults, overridable by adding the key, and inspectable via a new `learnloop config effective [--only-overrides]` command (small new CLI feature; it exists to make the template shrink honest — the effective policy remains visible without being copied into every vault).

Today's template: ~681 lines, ~68 sections, 214 numeric leaves (`config.py:12–692`), while five whole modeled families are silently absent. Target template: ~60 lines.

### Setting-by-setting decisions

Legend: decision applies to the *generated template*; "model" notes what happens to the Pydantic schema. Old keys never hard-fail: unknown/retired keys already parse permissively, and that stays.

| Setting / family | Decision | Detail |
|---|---|---|
| `schema_version` | **KEEP, bump to `2`** | Revision 2: the provider-union split and field retirements are schema evolution even with a tolerant loader. The loader accepts `1` indefinitely and normalizes. |
| `[storage] sqlite_path` | **KEEP** | Genuinely user-facing. |
| `[algorithms] algorithm_version` | **KEEP** | Template value `mvp-0.9`; omission still defaults to `mvp-0.6` (deliberate old-vault safety — invariant). Fix the stale `config.py:703` comment ("mvp-0.7"). The missing `upgrade` target for 0.9 is a product gap logged in §K, not silently patched here. |
| `[evidence.*]` (attempt types, coverage, blueprints, certification) | **DERIVE** (template) / KEEP (model) | Behavioral policy with sane defaults; hidden from template. |
| `[evidence.correlation]` | **DEPRECATE** | Generated empty today; overlaps `recall_coverage` discounts (staged architecture). Stop generating; keep parsing; §K investigation decides model removal. |
| `[scheduler]` + `[scheduler.surprise]` + `[scheduler.followup]` | **DERIVE** (template) / KEEP (model) | 28 numeric leaves of ranking policy. `short_session_minutes` is the only borderline user setting; it moves to the template's commented examples rather than being generated. |
| `[goals]`, `[hypothesis]`, `[mastery]`, `[mastery.irt]` | **DERIVE** / KEEP model | Hidden defaults. |
| `[forecasts] default_horizon_days` | **REMOVE** | Zero readers (verified). Consumed nowhere; existing vaults containing it: parsed-and-ignored (already permissive). Model field and `ForecastsConfig` deleted; no migration needed. |
| `[probe]` legacy root fields (`attempts_target_*`, `claim_skip_threshold`, `variance_convergence_threshold`) | **DEPRECATE** | Frozen replay still reads them for old vaults. Never generated again; parsing preserved indefinitely under the compatibility freeze. `probe.hypothesis_set_max_size` stays live (KEEP model). |
| `[probe.episode]` | DERIVE / KEEP model; **REMOVE** `self_graded_evidence_weight` | Field has zero readers while its siblings are read at `probe_episodes.py:1473,1991` — superseded wiring. Parse-and-ignore for old files. |
| `[probe.generation]/[dialogue]/[calibration]/[hierarchy]/[lifecycle]/[shadow]/[block]/[irt]/[self_tag]` | **DERIVE** / KEEP model | `probe.dialogue.max_turns`: **UNCERTAIN** — no conclusive hard-cap consumer; S6.1b investigates, then wires it or removes it. |
| `[recall_coverage]` | DERIVE / KEEP model; **REMOVE** `facet_recall_prior_pseudo_count`; `coverage_epsilon` → **UNCERTAIN** | `facet_recall_prior_pseudo_count` has zero readers. `coverage_epsilon` was REMOVE in revision 1; the review's counterpoint held — the spec describes a coverage floor that may be *unimplemented rather than obsolete* — so the owner investigation (S6.1b) decides wire-or-remove. `severity_examples` **stay modeled and overridable** (revision 1 was wrong to move them to code: `recall_calibration.py:133` consumes them at runtime); hidden from the template like the rest. |
| `[facet_diagnostic]`, `[practice_generation]`, `[rung_variants]`, `[trace_evidence]`, `[diagnostic_augmentation]` | **KEEP model** (already absent from template) | Their absence today proves hidden-defaults work fine. |
| `[misconceptions]`, `[exam_seeding]`, `[tutor_qa]`, `[tutor_promotion]`, `[teach_back]` | DERIVE / KEEP model | Hidden. |
| `[animation]` | **KEEP** `enabled` in template; DERIVE rest | `enabled` is a real user decision (spawns Manim). `manim_executable`, `venv_path`, `auto_provision_venv` are machine-local implementation details: modeled, hidden, documented in the template comment. |
| `[ingest]` core (`window_char_cap` etc.) | DERIVE / KEEP model | |
| `[ingest.pdf]` | **KEEP** `engine` in template; DERIVE rest | Engine choice (marker vs pypdf vs datalab) is a genuine capability/cost decision. Marker options etc. stay modeled. |
| `[ingest.audio]` | **CONSOLIDATE** + KEEP endpoint config | Revision 2 mechanism: a ninth task route, **`transcription`**, resolving through the standard profile machinery — which preserves the legitimate independent-model use case (a cheap transcription model different from the ingest model) as a profile rather than the hardcoded-clone branch (`ingest_runner.py:793–865`). Existing `[ingest.audio] provider="openrouter"` settings (model, timeout) are **config-normalized** into a synthesized profile + route at load, exactly like the `[codex]` normalization; endpoint-transcription settings stay as-is. **Behavior change**, own stage (S4.8b), characterization first — tests currently pin the audio-specific model/timeout and must keep passing through normalization. |
| `[ingest.native]` | **KEEP** in template | Opt-in external-data-flow switch — a real user decision. |
| `[ingest.budgets]`, `[ingest.providers.*]`, `[ingest.runner]` | DERIVE / KEEP model | `evidence_span_input_tokens`: **UNCERTAIN** — same investigation bucket as `max_turns`. |
| `[ai]` (`active_provider`, `fallback_provider`, `timeout_seconds`) | **KEEP** | Core user decision. |
| `[ai.providers.<name>]` | **KEEP** in template (seeded profiles); **RENAME/model split** | The permissive one-model-fits-all profile leaks Codex fields (`checkout_path`, `sdk_python_path`, seven endpoint paths, `auth_mode`) into chat profiles. Model becomes a discriminated union on `type` (`codex_sdk` | `http` | `openai_chat` | `openrouter`); unknown fields on old files remain tolerated, and old profiles **omitting `type` keep today's `codex_sdk` default** (`config.py:1516`) so normalization is behavior-identical. **REMOVE** `auth_mode` everywhere (zero behavioral readers): field deleted from both models, dropped from `context.py:343` DTO exposure, parse-and-ignore for old files. |
| `[ai.routing]` | **KEEP** (+1 route) | Nine routes — revision 2 adds `transcription` (empty by default: falls through to routed native ingest / endpoint transcription exactly as today). Operation inheritance becomes the in-code `ROUTE_FOR_OPERATION` map (§E). |
| `[codex]` | **DEPRECATE** | Stop generating. One-way normalization into `[ai.providers.codex]` is preserved for existing vaults; after S1.3 no runtime code reads `config.codex` directly (today's legacy readers all migrate to the composition root), so the section becomes pure input compatibility. Doctor gains a notice suggesting the one-line translation. Model removal is a distant, owner-gated step. |
| `[capabilities]`, `[locks]`, `[error_impacts]`, `[fitting.fsrs]` | DERIVE / KEEP model | Hidden; `error_impacts` validator-seeded defaults unchanged. |
| `[cross_lo_propagation]` | **DEPRECATE → REMOVE model** | Already retired (docstring `config.py:1629–1634`), doctor-warned (`doctor.py:195–230`), and asserted-empty by tests. Keep the doctor warning; replace the typed model with parse-and-ignore of the raw key. |

### Proposed generated `learnloop.toml`

```toml
schema_version = 2

[storage]
sqlite_path = "state.sqlite"

[algorithms]
algorithm_version = "mvp-0.9"

# ---------------------------------------------------------------------------
# AI providers. LearnLoop works without any provider (manual grading).
# Routing precedence: explicit flag > LEARNLOOP_AI_PROVIDER > task route > active_provider.
# ---------------------------------------------------------------------------
[ai]
active_provider = "codex"
fallback_provider = ""

[ai.providers.codex]
type = "codex_sdk"
model = "gpt-5.6-sol"
reasoning_effort = "low"   # current shipped default — changing it is a product decision, not a refactor
# checkout_path / revision / sdk_python_path: set if your Codex checkout is non-default.

[ai.providers.openrouter]
type = "openrouter"
model = "deepseek/deepseek-chat"
api_key_env = "OPENROUTER_API_KEY"
response_format = "json_object"
timeout_seconds = 180
# input_modalities = ["audio", "pdf"]   # declare to enable native media ingest

[ai.routing]
grading = "codex_low"
canonical_ingest = "codex_medium"
canonical_ingest_retry = "codex_medium"
authoring = "codex_medium"
tutor_qa = "codex_low"
teach_back = "codex_low"
rung_variant = "codex_low"
animation = "codex_medium"
transcription = ""       # optional dedicated transcription profile (rev 2); empty = today's behavior

[ingest]
[ingest.pdf]
engine = "auto"          # auto | marker | pypdf | native

[ingest.native]
enabled = false          # send audio/PDF bytes to the routed provider natively

[animation]
enabled = true           # current shipped default; every render still needs a per-generation consent click

# ---------------------------------------------------------------------------
# Everything else (evidence weights, scheduler policy, probe episodes, mastery
# model, tutor budgets, …) runs on built-in defaults. Inspect the full
# effective configuration with:  learnloop config effective
# Override any key by adding it here with the same TOML path.
# ---------------------------------------------------------------------------
```

(`codex_low`/`codex_medium` remain validator-seeded derived profiles, unchanged — but after S1.3 their identity survives into provenance.)

### Defaults reproducibility (revision 2)

A minimal file means omitted values track code defaults across upgrades. The review is right that this is a policy question, but the repository already has the governing convention: behavior-affecting algorithm changes require an `algorithm_version` bump (CLAUDE.md). Revision 2 makes that enforceable with a **defaults-snapshot test keyed by `algorithm_version`** — changing a behavior-affecting default without a version bump fails CI. Runtime "immutable default bundles" (the review's heavier alternative) are deliberately not built: the CI-time snapshot gives the same guarantee with zero new runtime concepts. Whether old vaults should be *hard-frozen* instead is owner question 8.

### Compatibility consequences

- Existing vaults: nothing breaks. Every removed/hidden key parses as before (permissive models); removed-with-prejudice keys (`auth_mode`, the dead knobs, `cross_lo_propagation`) become parse-and-ignore, which is indistinguishable from today's behavior since nothing read them. `[ingest.audio] provider="openrouter"` settings are normalized into a profile + `transcription` route automatically (S4.8b).
- The only translation users may want: `[codex]`-only vaults keep working via normalization; the doctor notice tells them the modern spelling.
- No config migration tool is needed. A `doctor` check listing "keys present in your file that no longer do anything" is added instead (cheap, honest, reversible).

---

## I. `learnloop init` Refactor Proposal

### Diagnosis (verified)

- `init_vault()` (`vault/loader.py:314–361`) is a good primitive: per-file guards, idempotent completion of partial scaffolds, config reloaded before DB placement, atomic fresh-DB publication. Keep it.
- Problems: CLI `init` is two unguarded statements (`cli.py:1746–1751`) that will scaffold into any populated directory; sidecar `create_vault` (`handlers/vault.py:33–105`) duplicates bootstrap policy (AI-settings inheritance, subject creation, learner profile/claim seeding) inside a transport handler; `starting_level` validation runs *after* scaffold + subject creation (`:122–126`), leaving a valid partial vault on error; the generated TOML is the 681-line dump; opening is implicitly writeful everywhere (`Repository.__init__:699`); plain doctor migrates (`doctor.py:138`).

### Target initialization flow

1. A top-level `learnloop/bootstrap.py` gains `create_vault(root, *, subject=None, starting_level=None, inherit_ai_from=None, clock)` — revision 2 location: it orchestrates learner-profile/claim seeding and AI inheritance, which import domain code, so it lives *above* `vault/` (which keeps only pure filesystem/DB scaffolding):
   - **Validate first** (path emptiness policy, `starting_level`, subject name) — before any write.
   - Then `init_vault(root)` (unchanged primitive, now writing the §H minimal template).
   - Then optional subject, learner profile, learner claim, AI-settings inheritance — the logic currently inlined in the sidecar handler, moved verbatim.
2. CLI `learnloop init` calls the same bootstrap. It gains the sidecar's guard: refuse a file or a populated non-vault directory unless `--force`. (**Behavior change**, deliberate: the current silent scaffold-into-anything is a footgun with no test pinning it — the archaeology lists the missing test as a gap, and §N adds the test for the *new* behavior.)
3. Sidecar `create_vault` becomes a thin validated call into the same bootstrap. Error surface (`invalid_path`, `vault_dir_not_empty`, `invalid_starting_level`) is unchanged, except `invalid_starting_level` now leaves **no** partial vault (**behavior change**, an unambiguous improvement; new test).
4. Opening (revision 2 — no churn): `Repository(path)` **keeps its current migrating semantics**, so the 100+ construction sites are untouched. A new `Repository.attach(path)` skips migration and opens read-only where wanted; doctor's plain mode and `goal_series`' scratch copies use it (the latter re-run migrations pointlessly on every checkpoint copy today). Plain `learnloop doctor` becomes *physically* read-only — SQLite URI `mode=ro`, no parent-directory creation (today's `connect()` does `mkdir`), schema version read first, and **every check gated on the tables it needs**: apply-intent recovery, for example, requires migration 044, and the review's pre-044 crash scenario is real. `doctor --fix-state` applies migrations (**behavior change**, listed; `doctor.py:423–424` already *claims* read-only behavior it doesn't have). A pre-044 fixture byte-identity test pins it.
5. Migration hardening (own stage, redesigned in revision 2): a **vault-level migration coordinator** receives both the vault root — the lock must come from `vault_lock`, because `storage.sqlite_path` is relocatable and cannot locate it — and the database path. Per-script transactions are applied only after a **per-migration audit**: 25 migration files contain `PRAGMA foreign_keys`, which is a no-op inside an open transaction, so FK-toggling scripts (e.g. 153) run un-wrapped and are validated with `PRAGMA foreign_key_check` afterwards; the rest get explicit transactions. Fresh-DB atomic publication is already correct and unchanged.

### Obsolete / duplicate / lazy-init findings

| Finding | Disposition |
|---|---|
| 681-line generated TOML | Replaced (§H); existing vaults untouched |
| Bootstrap duplicated between CLI and sidecar | Unified in top-level `learnloop/bootstrap.py` (app layer; `vault/` stays pure scaffolding) |
| `starting_level` validated after writes | Validation-first (behavior change, improvement) |
| `[codex]` section generated for new vaults | Stopped (§H) |
| `AGENTS.md`, `profile/goals.md` scaffolding | **KEEP** — guarded, cheap, and `goals.md` authority is an open owner question (§K); init is the wrong place to resolve it |
| Backup/session/export directories from old `spec.md` | Already absent by design (`test_init.py` asserts absence) — formally recorded in §K as ABANDONED spec surface, not re-added |
| Eager DB creation at init | **KEEP** — atomic fresh publication is the safest moment to build the DB; laziness would move failure to first use for zero benefit |
| Fixture/calibration generators using `init_vault` | Unchanged (shared primitive is the point) |

### User-visible behavior changes (complete list for this area)

1. `learnloop init` refuses populated non-vault directories without `--force`.
2. Invalid `starting_level` no longer leaves a partial vault.
3. New vaults get the minimal TOML (old vaults keep their files).
4. Plain `doctor` no longer migrates or creates the DB.
5. Two processes racing to open/migrate one vault now serialize on the vault lock instead of racing unprotected.

---

## J. `state.sqlite` Legacy Audit

Scope: all 251 user tables at migration 156, audited by family (the schema's own grouping); individually contested tables get their own rows. Readers/writers are summarized from the archaeology plus this proposal's re-verification; "fixtures" refers to the eight tracked fixture DBs (migration maxima 26, 26, 62, 109, 152, 152, 155, 155). Persistent-state standard applies throughout: **absence of queries is never, by itself, grounds for dropping a table.**

Trigger constraint (invariant for every stage): 62 triggers enforce append-only/no-update semantics on causal, reveal, measurement-correction, misconception-disposition, and audit tables. Any refactor that rewrites instead of appending fails at the schema — this is a feature, and §O stages treat it as a test oracle.

### Family classifications

| Family (tables) | Purpose | Readers/writers | Classification | Confidence |
|---|---|---|---|---|
| Migration/proposals/content/parameters (`schema_migrations`, `agent_runs`, `assessment_contract_versions`, `proposed_patch*`, `change_batches`, `content_events`, `apply_intents`, `maintenance_notices`, `parameter_*`, `fitted_parameters`, `item_parameter_state`, `derived_state_rebuilds`) | Schema ledger, AI-run provenance, proposal lifecycle, apply recovery, parameter governance | migrate/doctor, proposals/patches/apply_protocol, parameter_registry | **ACTIVE** | High |
| Attempts/grading/measurement (`practice_attempts`, `grading_evidence`, `error_events`, `attempt_*`, `outcome_schema*`, `grader_calibration_*`, `calibration_stream_samples`, `raw_grade_events`, `grade_interpretations`, `grade_adjudications`, `activity_administrations`, `activity_observations`, `measurement_events`, `measurement_contract_corrections`, `grading_clarification*`, `reveal_events`, `trace_exercised_facets`) | Raw evidence ledgers + authority pipeline. The old/new grade tables are **parallel generations representing different pipeline stages**, not duplicates | attempts/grading/replay/projections; heavy test coverage | **ACTIVE** (both generations) | High |
| Learner-state projections, canonical (`facet_recall_state`, `facet_capability_evidence`, `facet_merges`, `capability_residual_state`, `subject_identifiability_watermarks`, `learning_object_mastery`, `learner_claims`, `capability_aliases`, `practice_item_quality_state`, `intervention_needs`) | Current learner model | learner/scheduler/goals/sidecar | **ACTIVE** | High |
| Learner-state projections, legacy (`evidence_facet_recall_state`, `facet_uncertainty`) | Pre-canonical facet state | version-branched reads in `facet_state_reader`; old fixtures contain rows (26/62/109-level fixtures verified non-empty) | **LEGACY, actively preserved** — frozen by the 2026-07-19 owner decision | High |
| `practice_item_state` | Item scheduling state, historical seam | scheduler, goals, exams, sidecar serializers, doctor, state_sync | **ACTIVE historical seam** — not removable until `activity_card_state` fully replaces it (it has not) | High |
| `activity_card_state` | Successor card state | card_lineage/purpose adapters | **ACTIVE partial successor** | High |
| Probe, legacy (`lo_probe_state`, `hypothesis_sets`, `learner_state_beliefs`, `elicitation_events`) | Pre-redesign probe state | frozen replay; non-empty in all four old fixtures (verified) | **LEGACY, actively preserved** | High |
| Probe, current (`probe_episodes`, `probe_state_segments`, `probe_presentations`, `probe_observations`, `probe_family_*`, `probe_item_*`, `probe_regrade_checks`, `probe_generation_needs`, `diagnostic_surface_generation_needs`, `probe_calibration_sessions`, `probe_manipulation_audits`) | Redesigned adaptive probes | diagnosis modules, extensive tests | **ACTIVE** | High |
| Scheduling/sessions (`scheduler_*`, `decision_features`, `learning_outcome_labels`, `sessions`, `session_checkpoints`, `queue_state`, `followup_*`, `practice_pool*`) | Selection, sessions, follow-ups | scheduler/controller/sidecar | **ACTIVE** | High |
| Activity substrate (`activity_families/…/versions/authoring`, `activity_cards*`, `activity_surfaces*`, `activity_patterns*`, `card_lineage*`, `surface_fingerprint_memberships`, `soft_kinship_features`, `interaction_events`, `retirement_records`, `surface_mint_requests`, `activity_exposure_events`) | P1 identity layer + exposure ledger | substrate modules; the exposure ledger is the shared scheduler/controller seam | **ACTIVE** | High |
| Source/ingest/provenance (`source_artifacts`, `source_revisions`, `source_extraction_runs`, `source_document_*`, `source_span_reanchors`, `source_block_health`, `source_unit_selections`, `source_unit_inventories`, `entity_source_links`, `notation_mappings`, `source_conflict*`, `synthesis_*`, `ingest_batches`, `ingest_jobs`, `ingest_job_dependencies`, `source_exposure_events`) | Source IR, durable queue, synthesis identity | content modules | **ACTIVE** | High |
| Reader/source objects (`source_render_*`, `source_annotation*`, `source_objects*`, `canonical_mapping_proposals`, `reader_*`) | Reader feature state | reader modules | **ACTIVE** | High |
| Tutor/questions/remediation (`question_*`, `misconception*`, `item_misconception_discrimination`, `remediation_episodes`, `failure_triage_*`, `rung_variant_requests`) | Tutor and repair lifecycle | tutor/diagnosis modules | **ACTIVE** | High |
| Goals/exams/forecasts (`goal_contract_*`, `hypothesis_events`, `forecasts`, `exam_*`, `certification_cold_probe_outcomes`, `cold_measurement_*`) | Goal contracts and certification | goals modules | **ACTIVE** (note: `forecasts` *table* is active via `forecast_ledger.py`; only the config knob was dead) | High |
| Curriculum/golden path (`commitment*`, `depth_*`, `task_blueprint*`, `target_exemplars`, `progression_policy_versions`, `angle_inventories`, `family_evidence_cap_policies`, `lapse_episodes`, `p2_ladder_*`, `diagnostic_pack*`, `golden_path_*`) | Curricular contracts | curriculum modules | **ACTIVE** | High |
| Controller/experimentation (`controller_*`, `attention_*`, `policy_experiment_assignments`, `familiarity_kernel_*`, `shadow_component_events`, `composed_selector_telemetry_horizons`) | Staged controller + shadow telemetry | scheduling modules; several feature-gated | **ACTIVE or DORMANT by feature** — shadow tables have schema-enforced zero authority (`controller_shadow_predictions` CHECK) | High |
| Causal/measurement evaluation (`causal_*`, `coldness_receipts`, `diagnosis_adjudications`, `missing_vocabulary_notes`, `unresolved_cause_factors`, `discrimination_profile_matches`, `contrast_pair_servings`, `error_hunt_outcomes`, `persona_realism_runs`, `diagnostic_eval_*`, `diagnostic_augmentation_receipts`) | Append-only diagnostic audit trail | diagnosis modules; trigger-protected | **ACTIVE** | High |
| Remaining (`observation_templates`, `observation_events`, `concept_animations`) | Feature state | respective services | **ACTIVE** | Medium-high |

### Individually contested tables

| Table | Purpose (intent) | Readers | Writers | Migrations | Tests | Fixture/user data | Classification | Confidence |
|---|---|---|---|---|---|---|---|---|
| `source_exam_profiles` | Persist aggregated exam profiles per source (spec_source_ingestion_v2 §7) | none — `upsert_exam_profile`/`get_exam_profile` (`repositories.py:18362/:18387`) have **zero callers**; live code computes `aggregate_exam_profile()` in memory (`exam_profile.py:92`, consumed by `source_coverage.py`, `source_set_synthesis.py`) | none | `041` | none | Empty in all six fixtures that have it | **DORMANT/UNFINISHED or SUPERSEDED** (revision 2 softening: migration 041 describes a deterministic materialized profile cache with `profile_hash` identity — an unfinished persistence design is as plausible as supersession) | Medium |
| `source_locator_schemes` | Persist per-source locator scheme | `backfill_locator_schemes`/`locator_scheme` (`repositories.py:18097/:18127`) — sole caller is one dedicated test (`test_source_layer.py:344`) | test only | `032` | 1 (API), 1 (DDL presence) | Empty everywhere | **ABANDONED partial implementation** — live representation is the `locator_scheme` column on links + `detect_locator_scheme()` | Medium-high |
| `learner_theta` | Original global-ability design (old `spec.md`, heavy prose) | generic `find_record` entry (`repositories.py:16634`, bare `dict` decoder) and `debug_time` timestamp list only | none | `001` | none | Empty everywhere | **ABANDONED historical architecture** | Medium-high |

### Safe deprecation strategy for the three candidates

Persistent state gets a telemetry-first process (reordered in revision 2), never a code+schema simultaneous delete:

1. **Deprecation visibility first** (§O S6.1a): `doctor` gains a "deprecated tables" check that reports row counts for the three tables, run on the owner's real vaults before anything is detached. Expected: zero everywhere (all fixtures verified empty). If any real vault reports rows, stop and escalate — that would falsify the abandonment hypothesis.
2. **Code detachment** (§O S6.1c, only after step 1 is clean): delete the orphaned repository CRUD (`upsert_exam_profile`, `get_exam_profile`, `backfill_locator_schemes`, `locator_scheme`) and its one test; remove the `learner_theta` entries from `find_record` and `debug_time`. Tables untouched. Fully reversible.
3. **No schema drop.** Revision 1's "drop-if-empty, abort otherwise" migration is **withdrawn** — an aborting migration in the sequential chain would block every later migration and vault opening (review finding, accepted). Empty tables cost nothing and stay indefinitely. If reclamation is ever wanted, the mechanism is an archive-rename (`_archived_<name>`) in an ordinary, never-aborting migration, owner-gated, with export tooling first.

### Adjacent persistent-state findings (not table removals)

- **Migration mechanics**: incremental path lacks per-script transactions and any process lock (`migrate.py:52–66`; verified no `BEGIN` outside trigger bodies, no lock anywhere). Hardened in §O S2.5 — audit-driven in revision 2: 25 migration files contain `PRAGMA foreign_keys` (a no-op inside a transaction), so FK-toggling scripts get a non-wrapped path validated by `PRAGMA foreign_key_check`, and the coordinator takes the vault root so the lock comes from `vault_lock`, not from the relocatable db path. It still touches the most dangerous file in the repo and gets its own stage with new tests first.
- **`db/connection.py`** sets no `busy_timeout`; ~19 hand-issued `PRAGMA busy_timeout = 5000` calls inside `repositories.py` compensate unevenly. Centralize in `connect()` (S2.5). A `journal_mode=WAL` switch is **explicitly out of scope** — it changes on-disk file layout for every existing vault and deserves its own decision.
- **`sqlite_admin` escape hatch** opens its own connection **without** `PRAGMA foreign_keys` (`handlers/sqlite_admin.py:36–39`) while normal connections enforce it. It is a tested, deliberate feature; proposal: add the pragma to its connection (small behavior change — FK-violating manual edits start failing loudly; flagged for the owner in S6.1c since the point of the hatch is power).
- **`debug_time.py`** hardcodes a second 15-table schema inventory including `learner_theta`. It shrinks naturally in step 1 above; folding it into per-family stores is optional follow-on.
- **Backup/restore**: still nonexistent (old `spec.md` promise). Recorded as ABANDONED-or-future in §K; this refactor does not build it, but the state audit notes that `goal_series`' copy-to-scratch pattern (`goal_series.py:292–304`) is the natural seed for one.

This audit is the seed data for the table-role registry — see §R.

---

## R. Rebuild & Recalibration Workstream (revision 2 addition)

**Requirement (owner, 2026-08-17):** large algorithmic changes should be easy to make and to evaluate by rebuilding derived state from past attempts.

**What already exists (verified, §0 third round):** rebuild-from-raw is a founding capability. `learnloop rebuild-derived-state` (`cli.py:5215`) replays every learning object with persisted attempts and stamps a `derived_state_rebuilds` receipt carrying three named recalibration boundaries — `algorithm_version`, `CANONICAL_PROJECTION_VERSION`, and a content-addressed `coverage_denominator_version` (`replay.py:109–158`, whose comments explicitly frame projection changes as "one deliberate recalibration boundary rather than silently"). Raw ledgers retain what replay needs without re-calling providers (`raw_grade_events` keeps AI grades; reveal/coldness/hint discounts are recorded and replayable — an archaeology invariant). Version sets are centralized in `assessment_contracts.py:54–64` with a comment requiring set-membership checks. Scratch-copy replay is proven (`goal_series.py:292–304`, never mutating the live DB). And the dormant `card_outcome_replay.py` is an owner-commissioned event-sufficiency proof (U-015) that future models can be built from stored events with zero schema changes.

**Why large changes are hard anyway (verified gaps):**

1. **There is no single rebuild.** `rebuild_derived_state` runs only the per-LO mastery/facet replay; the activity substrate (`activity_backfill`), projections (`p0_projection`, `substrate_cutover`, `canonical_projection_rollout`), and probes (robust cutover) have separate replayers with no orchestrator and no declared table coverage. "Rebuild everything derived" is tribal knowledge.
2. **No table-role contract.** Which of the 251 tables are raw inputs, rebuildable projections, append-only receipts, or preserved workflow state is re-encoded partially in each replayer, in `goal_series` pruning, and in `debug_time`'s hand-list.
3. **The one completeness check is red at HEAD** (`test_activity_backfill`, 16 of 70 attempts replayed) and there is no general invariant behind it.
4. **No equivalence oracle.** Nothing asserts a same-version rebuild reproduces identical projections — which is also the missing safety net that would make an *intentional* change reviewable: the equivalence diff becomes the review artifact.
5. **The sanctioned big-change path is unmaintained**: `learnloop upgrade` cannot target 0.9, the version fresh vaults ship with.

**The workstream:**

- **R1 — Table-role registry** (`db/table_roles.py`). One declarative manifest classifying every table: `RAW_LEDGER` (replay input, never rebuilt), `DERIVED` (cleared + rebuilt, algorithm-version-tagged), `RECEIPT` (append-only, never rebuilt — matching the trigger enforcement), `WORKFLOW` (queues/sessions/leases, preserved), `COMPAT` (frozen). Seeded from the §J audit. CI check: a migration adding an unclassified table fails. `debug_time`'s hand-list and `goal_series`' pruning knowledge dissolve into it.
- **R2 — One rebuild orchestrator.** `rebuild-derived-state` becomes the umbrella invoking all *registered* replayers in dependency order (LO replay, activity backfill, projection rollout, …), each declaring which `DERIVED` families it owns. Registry cross-check: every `DERIVED` family has exactly one owning replayer — completeness made structural. One `derived_state_rebuilds` receipt, as today. **The one semantically risky piece:** existing replayers keep their current invocation points (vault open, upgrade, CLI) untouched; the umbrella is strictly additive.
- **R3 — Invariant tests.** Replay-completeness (every raw attempt accounted for across all registered replayers — the generalization of the currently-failing test) and rebuild-equivalence (same-version rebuild on a golden fixture reproduces identical projections). These double as the oracle protecting the Phase-4 moves of `replay`/`canonical_projection`/`substrate`.
- **R4 — Shadow rebuild + diff.** `learnloop rebuild --shadow [--set algorithms.algorithm_version=…]`: generalize the `goal_series` scratch-copy pattern — replay the whole history under a candidate algorithm/config on a copy and report the learner-state diff (mastery/facet/schedule deltas; `session_learning_diff`/`study_map_diff` are the in-repo diff precedents). This is what makes a large change cheap to *evaluate* before committing. Never touches the live DB (existing `goal_series` invariant, kept).
- **R5 — Version-boundary hygiene.** `assessment_contracts` documented as the single version-set authority; the mvp-0.9 `upgrade` target fixed (absorbs the §N gap item); an "algorithm change playbook" doc: bump version → registry says what rebuilds → shadow diff → equivalence test deliberately re-pinned → defaults-snapshot test (§H) re-pinned.

**Non-goals (YAGNI):** no event-sourcing rewrite; receipts and workflow state are never rebuilt (a rebuild that fabricates receipts would violate the trigger-enforced append-only semantics); no automatic downgrade; no promise that arbitrary future models are derivable from today's events — that is what the U-015 sufficiency-proof pattern exists for, per new model.

**Placement:** R1–R3 land immediately after Phase 0 and run in parallel with Phases 1–2 (they extend the baseline-repair theme; R3 blocks R2 and the substrate move S4.1); R4 follows R2; R5 folds into S6.1b/S7.1.

---

## K. Legacy Feature Report

| Item | Classification | Evidence | Current callers | Historical intent | Recommendation | Confidence | Risk if wrong |
|---|---|---|---|---|---|---|---|
| `services/ingest.py` (gen-1 ingestion) | **LEGACY** | Sole importer is `tests/test_ingest_service.py` (verified) | its own test | Original MVP note-writing ingest | **Delete** module + test (S4.8c) | High | Trivial — git-recoverable |
| `services/source_ingestion.py` (gen-2 one-shot) | **ACTIVE legacy architecture** | Durable `legacy_ingest`/`exam_ingest` jobs dispatch to it (`ingest_runner.py:980–1034`, `:2671–2672`) | ingest runner, tests | v2 spec describes legacy ingest as "wrap Quick Add" — implementation preserved gen-2 instead | **Keep, freeze, document** the spec divergence; retirement is an owner product decision | High | Breaking imports for vaults that still use legacy ingest paths |
| One-shot ingest cache identity (no provider/model/prompt in key) | **LEGACY behavior** | Archaeology; cache key fields verified | source_ingestion callers | Predates synthesis-manifest identity model | **Keep frozen** while gen-2 lives; do *not* silently change cache identity inside a refactor (behavior change); note as a known defect | High | Stale-proposal reuse continues (already today's behavior) |
| `services/pdf_extraction.py` vs `ingest/extractors/` | **DUPLICATE (transitional)** | Two live engines; `ingest/hashing.py:94` admits the mirroring; single production importer `source_ingestion.py:25` | source_ingestion; tests | Old one-shot vs durable generations | **Consolidate** onto `extractors` when gen-2 is next touched; until then co-locate both under `content/sources/` with the duplication documented | Medium-high | Cache/caption behavior drift in legacy path |
| `[probe]` legacy fields + `services/probes.py` legacy paths | **LEGACY, compatibility-active** | Frozen replay reads them; old fixtures carry `lo_probe_state` rows | replay, old vaults | Pre-redesign probes; freeze decision | **Keep frozen**; never generate the fields again (§H) | High | Old-vault replay breaks |
| Backfill/upgrade/projection compat (`activity_backfill`, `substrate_cutover`, `vault_upgrade`, `facet_state_reader` legacy branch, `causal_migration`) | **LEGACY, frozen by owner decision** | `spec_p1_shared_substrate.md:1150–1171` verbatim. Revision 2 removes two false positives: `probe_robust` is the **ACTIVE** mvp-0.8/0.9 probe path (`use_robust_probe`, five import sites in `probe_episodes`), and `p0_projection` is **mixed** — compat activation plus live reinterpretation appends (`p0_projection.py:88`) | vault open/upgrade/rebuild | Deliberate preservation | **Keep**, relocate frozen members to `substrate/compat/` with a README quoting the freeze decision; `probe_robust` → `diagnosis/` (active), `p0_projection` → `substrate/` (live) | High | Old-vault data reinterpreted or lost |
| Textual TUI | **ACTIVE** | `cli.py:5576` → `tui/app.py`; imports exactly 9 services; tested | `learnloop today` users | Pre-desktop surface | **Keep.** Retiring it is a product decision (owner question below); it costs one provider-resolution variant (fixed anyway by S1.3) and buys a terminal surface + test coverage | High | Removing a used surface |
| Legacy Codex HTTP adapter (`HttpCodexClient`, `[codex] provider="http"`, startup command machinery) | **ACTIVE compatibility; prevalence UNCERTAIN** | Reachable from both factories; configured; tested; only 8 ops, no repair | factories, tests | First-generation Codex integration | **Owner decision** (below). If no real vault uses HTTP mode: delete adapter + startup/health machinery + config fields in S6.3. Until decided: moves to `ai/providers/codex_http.py` untouched | High (reachability) / Low (usage) | Breaking a deployment mode the repo cannot see |
| `ai/prompts.py`, `ai/schemas.py` shims | **DEAD** | Zero importers repo-wide (verified) | none | Partial migration artifact | **Delete** (S1.1 replaces them with the real modules) | High | None found; external-consumer risk negligible for a local app |
| `[codex]` + `[ai.providers.codex]` dual representation | **DUPLICATE, both active** | One-way validator sync (`config.py:1926–1997`); legacy readers on `[codex]` | CLI/TUI/startup until S1.3 | Config-generation transition | **Consolidate**: S1.3 removes runtime readers; §H stops generation; parse-and-translate stays | High | Old vaults' `[codex]`-only files must keep working (they do) |
| `auth_mode` | **DEAD CONFIG** | 7 occurrences, zero behavioral reads (verified table in §0) | none | Presumed auth-mode switch never wired | **Delete** field, template lines, DTO exposure | High | None |
| `AIProviderSelection.uses_legacy_codex` + `cli._use_ai_provider` | **DEAD CODE** (new finding) | Property's only consumer is `_use_ai_provider` (`cli.py:1657`), which has zero callers | none | Superseded by `CODEX_PROVIDER_NAMES` branching | **Delete** both (S1.3) | High | None |
| Provider identity collapse to `"codex"` | **DEFECT (uncertain intent)** | `codex/client.py:866/:678` overwrite; archaeology uncertainty #4; no pinning test | all provenance stamping | Likely constructor-order accident | **Fix in S1.3** as an explicit behavior change with a provenance-pinning test; if the owner wants grouped provenance instead, pin *that* | Medium-high | Provenance rows change meaning either way — which is why it gets a test before the fix |
| Settings profile-copy drops `input_modalities` | **DEFECT** | `settings_store.py:57–67` whitelist vs `multimodal.py:65` check | settings → native media | Whitelist predates modalities | **Fix in S1.3** + regression test | High | Silent native-media disablement continues |
| `forecasts.default_horizon_days`, `probe.episode.self_graded_evidence_weight`, `recall_coverage.facet_recall_prior_pseudo_count` | **DEAD CONFIG** | Zero readers each (verified per-field) | none | Superseded wiring / never wired | **Delete** fields (§H) | High | None (parse-and-ignore covers old files) |
| `grade_diagnostic_fire` duck-typed provider seam | **DORMANT speculative seam** (revision 2 addition) | Probed by `diagnostic_gate.py:255` and `persona_gate.py` (×4, incl. the `:534` "semantic oracle" framing); implemented by no client | gates (probe only) | Planned semantic-oracle upgrade path for diagnostic gates | **Investigate** (S6.1b): wire into the transport design or delete the probes | High (existence) / Medium (intent) | Deleting a planned seam, or carrying dead probes |
| Dynamic `learnloop.services.*` module strings | **ACTIVE, move-critical** (revision 2 addition) | `parameter_registry._resolve_module_constant` (`:1117`), `open_world_gate:95`, `scoreboard:1470` (missing module silently → `no_producer`) | registries/gates/scoreboard | Deliberate revert-tolerant indirection | **Inventory + functional discovery tests before any move** (S0.2); update in every move stage | High | Silent feature-unavailable after package moves |
| `[cross_lo_propagation]` | **RETIRED CONFIG** | Docstring says retired; doctor warns; tests assert empty | doctor warning only | Old propagation design | **Keep warning; drop typed model** (S6.1c) | High | None |
| `probe.dialogue.max_turns`, `ingest.budgets.evidence_span_input_tokens`, `recall_coverage.coverage_epsilon` (revision 2: moved here from DEAD — the spec describes a coverage floor that may be *unimplemented* rather than obsolete, and `parameter_registry.py:831` registers it) | **UNCERTAIN** | No conclusive consumer found | unclear | Possibly reserved/missing wiring | **Investigate** in S6.1b, then wire or delete | Medium | Removing a setting whose specified behavior was meant to be built |
| `card_outcome_replay` | **DORMANT prototype** | Docstring: "proof that the projection is later buildable"; manifest `reads_live_tables: False`; test-only importers | 2 test files | U-015 deferred consumer, intentional | **Keep** in `substrate/compat/`, documented | High | Deleting the U-014 resume path |
| `intent_planner` | **ACTIVE SHADOW** | Scheduler invokes under flag (`scheduler.py:533–537`); shadow-only pinned by test | scheduler | KM §11.2 staged feature | **Keep** | High | — |
| `causal_diagnostic_selector` | **ACTIVE SHADOW** | Orchestrator calls, discards result (`causal_orchestrator.py:1488–1501`) | orchestrator | EVSI-2 staging | **Keep** | High | — |
| `kinship_feature` | **DORMANT (firewalled)** | `LIVE_ACTIVATION_ENABLED = False` (`:67`); "consulted by NOTHING" | sim certificate producer, parameter registry | U-026 descoped, dead-man switch by design | **Keep** — the firewall is the feature | High | Deleting an owner-descoped-but-planned component |
| `shadow_components` + `prequential` | **DORMANT (schema-firewalled)** | authority CHECK `('none')` in schema; docstrings | state_sync telemetry retirement | U-025 descoped | **Keep** | High | — |
| `open_world_gate` | **DORMANT planned gate** | "NOT implemented … gate NOT MET" docstring | one CLI inspection command | P4 §14.1 deferral, deliberately inspectable | **Keep** | High | — |
| `goals.md` alongside `goals.yaml`/SQL contracts | **UNCERTAIN** | Scaffold still creates it; consumers differ by workflow | mixed | Early human-readable authority | **Investigate** (owner question); keep scaffolding meanwhile | Medium | Deleting a file the owner reads |
| Full-vault backup/restore | **ABANDONED (spec surface)** | Old `spec.md` promises; `test_init.py` asserts directories absent; no implementation | none | Original storage design | **Document as not-implemented**; note `goal_series` scratch-copy as the seed if ever built | High | — |
| `find_record` 29-table probe | **ACTIVE (inelegant)** | `repositories.py:16625–16660` | debug/inspection | Generic lookup | **Keep**; remove `learner_theta` entry in S6.1c (after S6.1a is clean) | High | — |
| Sidecar `sqlite_admin` raw editor | **ACTIVE feature** | Tested as a feature (`test_sidecar_contract.py:1919`); no FK pragma | Library screen | Deliberate power-user hatch | **Keep**; propose FK pragma (owner-visible change, S6.1c) | High | Restricting a hatch the owner relies on |
| `apply_intents` recovery, vault lock, ingest leases | **ACTIVE protocols** | write-ahead + recovery tests | apply/ingest paths | Core reliability | **Keep untouched**; every stage that moves their modules is move-only | High | Partial content application |

**Open decisions required from the owner** (nothing below proceeds without an explicit answer):

1. Is any real vault using the legacy Codex **HTTP** adapter (`[codex] provider = "http"` or an `http`-type profile)? → gates deleting `codex_http` + startup/health machinery + 9 config fields.
2. Should named-profile provenance record `codex_low`/`codex_medium` (proposed) or keep collapsing to `codex`? → gates the S1.3 provenance fix direction.
3. Keep or retire the **TUI**? (This proposal assumes keep.)
4. Is `goals.md` still an authority you read/edit, or scaffold residue?
5. May `legacy_ingest` remain implemented by gen-2 `source_ingestion` indefinitely (proposed: yes, frozen), or should it be re-implemented as "wrap Quick Add" per the v2 spec (a behavior change this refactor will not smuggle in)?
6. Confirm the telemetry-first table deprecation (§J) may proceed through step 1 (doctor visibility) and, after a clean report, step 2 (code detachment); schema drops are withdrawn entirely (archive-rename at most, owner-gated).
7. Is **manual grading** a provider, a workflow mode, or the absence of a client? (The composition root models it as a typed outcome with today's semantics; confirm.)
8. Should omitted-config behavior be **frozen per `algorithm_version`** via the CI defaults-snapshot test only (proposed), or hard-frozen at vault creation via runtime default bundles (heavier, not proposed)?
9. Should audio transcription keep an **independently selected model** (proposed: yes, via the `transcription` route/profile) and its own consent semantics?
10. Is `doctor` expected to be database-read-only (proposed), or globally side-effect-free — which would additionally forbid any provider probing on its path?
11. Are `learnloop.services.*` / `learnloop.ingest.*` import paths used by anything outside this repository (scripts, notebooks)? Shims cover the transition either way; the answer only sets how long they live.

---

## L. Deletion Inventory

Ordered by evidence strength; each entry names its §O stage and the proof required before deletion.

**Safe now (dead by direct verification):**

| Candidate | Evidence | Stage |
|---|---|---|
| `ai/prompts.py`, `ai/schemas.py` shims | zero importers repo-wide | S1.1 |
| `AIProviderSelection.uses_legacy_codex`, `cli._use_ai_provider` | zero (transitive) callers | S1.3 |
| `auth_mode` (2 model fields, 2 template lines, 2 copy sites, 1 DTO exposure) | zero behavioral reads | S2.1 |
| `forecasts.default_horizon_days` + `ForecastsConfig` | zero readers | S2.1 |
| `probe.episode.self_graded_evidence_weight` | zero readers; siblings read | S2.1 |
| `recall_coverage.facet_recall_prior_pseudo_count` | zero readers | S2.1 (`coverage_epsilon` moved to the investigate bucket in revision 2) |
| `services/ingest.py` + `tests/test_ingest_service.py` | gen-1; sole importer is its own test | S4.8c |
| `repositories.py` exam-profile CRUD (`upsert_exam_profile`, `get_exam_profile`, `_decode_exam_profile`) | zero callers | S6.1c (after S6.1a telemetry is clean) |
| `repositories.py` locator-scheme API (`backfill_locator_schemes`, `locator_scheme`) + its single test | test-only | S6.1c (after S6.1a) |
| `learner_theta` entries in `find_record` + `debug_time` | generic references only | S6.1c (after S6.1a) |

**After a prerequisite stage completes:**

| Candidate | Prerequisite | Stage |
|---|---|---|
| Duplicated operation dispatch in `openai_chat.py` + `SdkCodexClient` (the 22×2 method bodies) | transport + feature-owned operations live | S1.2 |
| The 22-symbol private import block `openai_chat.py:22–66` | contracts moved | S1.2 |
| Six provider-resolution implementations (CLI, sidecar, TUI, startup, ingest_runner ×4 regions, ingest_jobs) | composition root live + parity tests green | S1.3 |
| `ai/codex_sdk.py` (bridge module) | providers relocated | S1.4 |
| `learnloop/codex/` shim package | grep + import-linter prove zero imports | S1.6 |
| `[codex]` generation + direct `config.codex` runtime readers | S1.3 caller migration | S2.1 |
| ~19 hand-issued `busy_timeout` pragmas in `repositories.py` | centralized in `connect()` | S2.5 |
| `_extract_audio_openrouter` hardcoded-profile branch (`ingest_runner.py:793–865`) | `transcription` route + config normalization live, characterization green | S4.8b |
| `services/` package (empty by then) | all domain moves complete | S4.11 |
| `services/pdf_extraction.py` | legacy path consolidated onto `extractors` | follow-on to S4.8, flagged behavior review |
| Unused `openai_chat_healthcheck` hook (`ai/runtime.py:60`) | S1.3 decides wire-or-delete | S1.3 |

**Owner-gated (§K questions):**

- `ai/providers/codex_http.py` + `[codex]` HTTP/startup/health config fields + `CodexStartupRunner` machinery (question 1).
- `cross_lo_propagation` typed model (keep doctor warning) — question implicit in §H, low stakes.
- Archive-renames — never drops, never aborting migrations (revision 2) — for `source_exam_profiles`, `source_locator_schemes`, `learner_theta` (question 6; parked after §J step 2).
- TUI retirement (question 3; **not** proposed).

**Explicitly not deletions**, despite superficial dormancy: `kinship_feature`, `shadow_components`, `prequential`, `open_world_gate`, `card_outcome_replay`, `intent_planner`, `causal_diagnostic_selector`, all `substrate/compat` machinery, legacy probe/facet tables and readers, `practice_item_state`, both grade-ledger generations, `HttpCodexClient` (pending question 1), `goals.md` (pending question 4).

---

## Alternatives Considered

For each consequential decision, the plausible options, and why the chosen one is the simplest that satisfies known requirements.

### 1. AI provider abstraction (decision revised in revision 2)

**Option A — revision 1's choice: named-method protocol + shared operation table + declared capabilities.** One protocol with 22 named `run_*` methods, a single `OPERATIONS` table, transports implementing `_execute`, `capabilities()` replacing `getattr`.
**Option B — revision 2's choice: small structured transport + feature-owned operations.** `StructuredTransport.complete(request) → WireModel`; each operation is one feature-owned function (context, prompt builder, wire model, one `complete()` call); `supports()` only for media/interrupt/legacy-HTTP.
**Option C — minimal move:** relocate `codex/*` unchanged; keep triple dispatch and `getattr` probing.

| Criterion | A | B | C |
|---|---|---|---|
| Provider protocol size | 24+ methods | 1–3 methods | unchanged |
| Parity across providers | asserted by a table + tests | **by construction** — any transport runs any operation | silently drifts (today's defect) |
| Where a new operation lands | table row + context/builder/model in `ai/` | entirely inside its owning feature | two transports + import block |
| Capability flags | required for all 22 ops (because of HTTP) | only media/interrupt/legacy-HTTP | implicit `getattr` |
| Domain cohesion | AI contracts centralized away from their domains | contracts live with the workflow that owns them (existing precedent: `MisconceptionMatchContext` is already domain-owned) | contracts stay Codex-owned |
| Type safety | full | full (the operation function is typed; only the transport boundary is generic) | full |
| Caller churn | 17 `getattr` sites → `supports()` | ~one rewrite per operation, in the service that already owns the call | zero |

Revision 1 chose A. The adversarial review argued B, and its factual premises survived verification: context ownership is not uniform, HTTP's endpoint semantics do not fit a prompt transport, and per-provider parity by construction eliminates the very drift A's table only *tests* for. B is strictly fewer concepts and is more consistent with this proposal's own domain-package thesis. **B**, with the HTTP adapter's fate decided first (it cannot implement `complete()`). C remains the fallback floor.

### 2. `services` reorganization

**Option A — chosen: eleven top-level domain packages; `services` deleted.**
**Option B — subpackages under `services/`** (`services/attempts/`, …): identical grouping, keeps the `services` prefix.
**Option C — leave flat; fix only boundaries** (SQL rule, private-API promotion, import-linter) without moving files.

B preserves a name that the archaeology showed means nothing — every import keeps a `services.` segment that carries zero information, and "is this a service?" remains an unanswerable question for new code. Cost of A over B is one extra path segment of churn in the same mechanical rename. C is the honest minimalist option and was seriously considered: it fixes the *dependency* problems at ~20% of the churn. It fails objective 1 (navigability): 259 flat modules stay unpredictable, and the freeze boundary (`substrate/compat`) stays invisible. Since moves are staged per-domain and each stage is independently shippable, A degrades gracefully into C if later stages are abandoned — which is the right risk profile. **A, with C as its built-in fallback.**

*Revision 2 note:* the adversarial review preferred B ("promote a feature to top level only when its boundary is proven"). Position held — with the review's underlying safety point adopted as an explicit gate: **a domain moves top-level only after its import-linter contract is clean**, which is exactly what the per-domain stages do. The review's own §7 assessment endorsed nearly every grouping; the residual dispute is only the information-free `services.` prefix. If the owner prefers B anyway, it is a one-parameter change to the move stages, not a different design.

### 3. `repositories.py` decomposition

**Option A — chosen: facade-preserving structural split into per-family stores; no caller churn; stop-anywhere.**
**Option B — full per-domain repository objects with caller migration** (`repo.probes.get_episode(...)`).
**Option C — leave intact; fix the three upward imports only.**

B rewrites ~1,010 method references across the codebase and couples persistence refactoring to every domain stage — the highest-risk shape for the lowest marginal benefit, since the facade already gives a stable seam. C is defensible (the file is huge but *works*), but it abandons the one split with genuinely obvious conceptual boundaries (table families — the schema's own grouping) and leaves the SQL-ownership rule unenforceable. A is what the codebase already started doing on its own (`controller_store`, `observation_ledger`). **A; C is the explicit stop-anywhere floor after the upward imports are fixed.**

### 4. Configuration architecture

**Option A — chosen: minimal generated template + full modeled defaults + `config effective` command; schema_version stays 1.**
**Option B — layered config files** (machine `defaults.toml` + vault `learnloop.toml` + generated `effective.toml` snapshot).
**Option C — keep the full dump but annotate it** (comments marking "advanced").

B introduces file-precedence rules — a whole new concept — to solve a display problem; it also makes "what does my vault do" depend on more files, not fewer. C keeps 681 lines of copied policy that silently diverges from code defaults on every upgrade (this divergence is precisely how the mvp-0.8/0.9 documentation drift happened). A holds effective policy in exactly one place (the models), makes overrides intentional, and needs one small read-only CLI command. **A.**

*Revision 2 addition — Option D: immutable default bundles keyed by `algorithm_version`* (the review's proposal for the omitted-defaults drift problem). Considered and rejected as runtime machinery for a policy question: the repo's existing convention (behavior changes require a version bump) plus a **CI defaults-snapshot test keyed by `algorithm_version`** (§H) gives the same guarantee with zero new runtime concepts. Two corrections from the same review are accepted into A: the template preserves every shipped default (revision 1's example flipped two), and `schema_version` bumps to 2. Hard freezing remains owner question 8.

### 5. Provider-config typing (sub-decision of 4)

**Chosen:** discriminated union on `type` (codex vs chat field sets), unknown fields tolerated. **Alternative:** keep the permissive superset. The superset is why chat profiles carry `checkout_path` and why `auth_mode` survived unread for so long; the union costs one Pydantic discriminator and removes a whole class of silently-meaningless config. Rejected middle ground (validation warnings on irrelevant fields) adds noise without removing the confusion.

---

## M. Refactor Risk Register

Ranked by (blast radius × likelihood). Every entry names its mitigation stage.

| # | Risk | Why it is dangerous | Mitigation |
|---|---|---|---|
| 1 | **Attempt/post-attempt ordering drift** during the attempts extraction or package move | Ordering (receipt → grade → raw evidence → legacy+canonical state → obligations) is load-bearing for learner state, replay, priming, idempotency; 114 test files assume it | S4.2 is move+extract only, zero logic edits; §N ordering characterization test added first; any diff touching `apply_attempt` body is rejected in review |
| 2 | **Hidden runtime ImportErrors and silent dynamic-reference breakage** during package moves | The SCC hides ~68 modules' edges inside function bodies; worse (revision 2, verified), `parameter_registry`/`open_world_gate`/`scoreboard` resolve `learnloop.services.*` names at runtime and a missing module silently becomes `no_producer`/feature-unavailable — no exception, no failing import | S0.2 adds an import-everything smoke test, the dynamic-reference inventory, and functional discovery tests **plus** the full suite per move stage; every move stage updates the inventory alongside imports |
| 3 | **Replay/projection semantics change** via `substrate/compat` moves | Frozen machinery guards old-vault data; the archaeology's №10 hotspot | Compat modules move verbatim (S4.1); the failing-at-HEAD backfill test is fixed *first* (S0.1) so regressions are visible; fixture-DB tests are the oracle |
| 4 | **Provider behavior changes beyond the fourteen declared ones** | Six resolution sites have four *known* divergences; collapsing them can surface unknown ones | S0.3 characterization tests capture current per-entry-point resolution before S1.3; every intended change is individually test-pinned; unintended diffs fail the parity suite |
| 5 | **Provenance meaning shift** from the identity fix | `agent_runs` rows before/after the fix stamp different provider names for the same profile | S1.3 records the cutover in the run row (provenance is append-only anyway); owner question 2 settles direction before implementation |
| 6 | **Migration-hardening bugs in `migrate.py`** | The one file where a bug corrupts every vault; revision 2 adds the specific hazard — 25 scripts contain `PRAGMA foreign_keys`, which silently no-ops inside a transaction, so blind wrapping breaks table-rebuild migrations | S2.5 lands *after* §N adds interruption/concurrency tests and *after* a per-migration audit; FK-toggling scripts bypass wrapping and validate via `foreign_key_check`; fresh-path code (already correct) is not touched; the coordinator takes the vault root so the lock uses the existing tested `vault_lock` |
| 7 | **Ingest queue regressions from the `ingest_runner` split** | Lease/heartbeat/retry bugs cause duplicate or lost jobs; highest-churn module | Revision 2 splits the stage: S4.8a is pure moves with the queue/recovery tests; the one semantic change (audio route) is S4.8b with its own characterization; `exam_ingest` alias preserved |
| 8 | **Apply-protocol partial application** if proposals modules are touched carelessly | Filesystem+SQLite write-ahead recovery | `content/proposals` modules are move-only in every stage; `test_apply_write_ahead.py` runs on each |
| 9 | **Sidecar contract breakage without Python test failures** | 296 RPCs, 6,109-line DTO file, no React tests | No handler signatures change in any stage; serializer imports are re-pointed only; `test_sidecar_contract.py` + desktop RPC tests run per stage; §N adds a serializer-shape snapshot test |
| 10 | **Config normalization regressions for old vaults** | `[codex]`-only vaults, probe/error-impact aliases, custom sqlite paths | S2.1 keeps every compat validator; §N adds an old-TOML corpus test (fixture TOMLs from the eight fixture vaults) |
| 11 | **Scheduler/controller double-scheduling or orphaned work** if the cutover seam is disturbed | Exactly-one-owner invariant | `scheduling/` stage is move-only; `test_controller_cutover.py` + ownership tests are the oracle; `STAGED_POLICY_LIVE_FOR_P2` untouched |
| 12 | **Fixture staleness** (all fixtures ≤155, HEAD at 156+) | Upgrade-path coverage quietly narrows | §N: regenerate or add one fixture at current head; keep old ones (they *are* the legacy coverage) |
| 13 | **Scope creep: refactor becomes rewrite** | 22-stage plans invite "while we're here" | Every stage lists allowed files and forbidden change types; behavior changes only in stages that declare them (fourteen total, enumerated) |
| 14 | **Rebuild orchestrator (R2) disturbs replayer timing** | The existing replayers run at different moments (vault open, upgrade, explicit CLI); unifying them could change *when* derived state changes | R2 is additive-only — existing invocation points untouched; the rebuild-equivalence test (R3) is written first and is the oracle |

The fourteen declared behavior changes (revision 2): three Codex-only CLI commands routed generically; startup non-Codex fallback honored; provenance identity preserved (direction per owner Q2); `input_modalities` copied; CLI init guard (`--force`); starting-level validation before writes; minimal template (new vaults only, shipped defaults preserved); doctor physically read-only (schema-gated); migration coordinator (vault lock + FK-audited per-script transactions); centralized busy_timeout; audio `transcription` route + `[ingest.audio]` normalization; structured-operation availability becomes unconditional-with-client (probing remains only for manual/no-client and legacy HTTP — behavior-equivalent, contract-visible); FK pragma on sqlite_admin (owner-gated); `Repository.attach()` addition (constructor semantics unchanged — no user-visible difference).

---

## N. Testing Requirements

Tests that must exist **before** the stage that depends on them. Derived from the archaeology's gap list, filtered to those this refactor actually needs (the full gap list remains valid as general debt).

| Test | Guards | Blocks stage |
|---|---|---|
| Fix `test_activity_backfill.py::test_backfill_populates_substrate_from_fixture` (16 ≠ 70 at HEAD) and restore a green, `/tmp`-safe full-suite run (route pytest tmp dirs to a large scratch volume via `tmp_path` config) | The entire plan needs a trustworthy baseline | **S0.1 blocks everything** |
| Import-everything smoke test (import all `learnloop.*` modules, including function-local import targets via a walk) + import-linter contracts (layer rules + frozen-cycle allowlist) | Deferred-import breakage; dependency ratchet | S0.2, blocks all moves |
| Cross-entry-point provider-resolution characterization: for a fixture config matrix (codex-only, named-profile-customized, openrouter-active, fallback-configured), record which provider/model/profile each of the six sites resolves | Makes S1.3's intended changes explicit diffs against pinned current behavior | S1.3 |
| Transport parity test: every feature-owned operation executes against SDK and chat transport fakes with matching context/model types; HTTP (if retained) declares exactly its 8 via `supports()` | Replaces silent drift between the three dispatch tables | S1.2 |
| Provenance pinning: named profile `codex_medium` → `agent_runs.provider_name == "codex_medium"` (direction per owner question 2) | Identity fix | S1.3 |
| `input_modalities` survives settings profile materialization | Whitelist fix | S1.3 |
| Degradation equivalence: the manual/no-client outcome (and the 8-op HTTP adapter, if retained) refuses/degrades exactly as `getattr` absence does today at the 17 sites | Behavior-equivalence of the capability contract | S1.2 |
| Old-TOML corpus: parse the eight fixture vaults' `learnloop.toml` + a `[codex]`-only synthetic file; assert normalized equivalence before/after S2.1 | Config compat | S2.1 |
| Minimal-template equivalence: fresh vault from new template produces identical effective config to fresh vault from old template (modulo §H removals) | Template shrink is display-only | S2.2 |
| CLI init guard: populated non-vault dir refused; `--force` works; rerun-completes-partial-scaffold still passes (`test_init.py`) | Init changes | S2.3 |
| Invalid `starting_level` leaves no partial vault (CLI and sidecar) | Bootstrap unification | S2.3 |
| Plain doctor is physically read-only (open DB read-only / assert file hash unchanged; pending migrations *reported*) | Doctor change | S2.4 |
| Migration interruption: kill mid-script on an existing vault → either fully applied+recorded or fully absent; rerun succeeds | Per-script transactions | S2.5 |
| Concurrent open/migrate: two processes race; one waits on the vault lock; ledger consistent | Migration lock | S2.5 |
| Attempt-ordering characterization: instrumented fake repository asserts write order receipt → grade → evidence → state → post-attempt for one canonical flow | Attempts extraction/move | S4.2 |
| Ingest queue invariants re-run (lease recovery, retry counts, dependency order, `exam_ingest` alias) after the runner split | Runner split | S4.8a |
| Routed-vs-`[ingest.audio]` resolution test + doctor-notice test for the normalization | Audio route | S4.8b |
| Sidecar serializer snapshot: golden JSON shapes for the highest-traffic DTOs (queue, practice, reader) | Import re-pointing can't silently change payloads | S4.x (all move stages touching sidecar imports) |
| Deprecated-table doctor check reports zero rows on all fixtures (and, decisively, on the owner's real vaults) | State deprecation step 1 (§J, telemetry-first) | S6.1a |
| One fixture vault at current migration head (regenerate `linear_algebra` or add a ninth) | Fixture staleness (risk 12) | S0.1 |
| mvp-0.9 upgrade-path fixture + decision on `upgrade` CLI target gap | Currently *no* upgrade path reaches the version fresh vaults ship with — product gap; test pins whatever the owner decides | S6.1b / R5 |
| Functional discovery tests for dynamic `learnloop.services.*` references (parameter registry constants, open-world gate conditions, scoreboard producer) | Silent feature-unavailable after moves (§M #2) | S0.2, blocks all moves |
| Manual (no-provider) outcome included in the provider-resolution characterization matrix | Composition root must not change manual-grading semantics | S0.3 |
| Defaults-snapshot keyed by `algorithm_version`: a behavior-affecting default change without a version bump fails CI | Omitted-config drift under the minimal template (§H) | S2.2 |
| Old-profile-without-`type` normalization: profiles omitting `type` still resolve as `codex_sdk` | Provider-union compatibility | S2.1 (corpus test extension) |
| Pre-044 fixture: plain doctor completes, reports pending migrations, leaves the DB byte-identical (no `apply_intents` crash) | Schema-gated read-only doctor | S2.4 |
| Audio-path characterization: `[ingest.audio] provider="openrouter"` model/timeout/consent pinned, then re-pinned through route normalization | Audio route migration | S4.8b |
| Replay-completeness invariant (every raw attempt accounted for across all registered replayers) + rebuild-equivalence golden test (same-version rebuild reproduces identical projections) | Workstream R; also the oracle for R2 and the Phase-4 moves of replay/projection modules | R3, blocks R2 and S4.1 |
| Shadow-rebuild isolation: `rebuild --shadow` leaves the live DB hash unchanged while producing a diff report | R4 | R4 |

Explicitly deferred (valid debt, not blocking this refactor): live-provider integration tests (all parity claims remain code-path parity until these exist), React component tests, Rust bridge tests, Windows vault-lock parity, backup/restore round-trip.

---

## O. Staged Implementation Plan

Conventions for every stage, stated once: the repository is functional and the full suite green at each stage boundary; each stage is one PR-sized, single-purpose diff; behavioral invariants (archaeology "Behavioral Invariants" section) hold unless the stage's **Behavior** field says otherwise; "full suite" means `uv run pytest` green plus the import smoke test; move stages permit `git mv`, import rewrites, shim files, and **dynamic-reference string updates** only — no logic edits. Every stage that declares a behavior change updates the affected documentation *in the same stage* (revision 2); S7.1 remains the final sweep. Stages within a phase are ordered; phases 2 and 3 can interleave with phase 4 where prerequisites allow, and **Phase R runs in parallel with Phases 1–2**.

### Phase 0 — Baseline

**S0.1 — Green, runnable baseline** (three separate reviewable changes — revision 2 split).
*S0.1a:* diagnose and fix (or, if the expectation is genuinely stale, explicitly re-pin with written justification) the `test_activity_backfill` 16-vs-70 failure — it may implicate production replay/admissibility code from `62fd1f6`; if so, that fix is its own commit with its own test. This failure is also §R gap 3, so its diagnosis feeds the completeness invariant. *S0.1b:* route pytest temp dirs off `/tmp`. *S0.1c:* add/regenerate one fixture at the current migration head (all eight tracked fixtures are ≤155; HEAD is 156). *Invariants:* no production behavior change outside a proven-buggy replay path. *Done when:* full suite green twice consecutively from a clean checkout.

**S0.2 — Architecture guardrails.**
*Objective:* make the dependency rules, module graph, and dynamic references enforceable before anything moves. *Files:* new `tests/test_architecture.py` (import-everything smoke), import-linter config codifying §G layers + the frozen-cycle allowlist, SQL-location check, and (revision 2) the **dynamic-reference inventory** — every runtime-constructed `learnloop.*` module string (`parameter_registry`, `open_world_gate`, `scoreboard`) — with functional discovery tests proving each registry/gate/producer actually resolves. *Prereqs:* S0.1. *Changes:* tooling only; the allowlist is generated from the current graph, so CI is green by construction. *Risks:* allowlist too coarse (ratchet becomes toothless) — mitigate by listing edges, not packages. *Done when:* CI fails on a synthetic new `db→services` import, on a new private cross-package import, and on a renamed module that a dynamic string still references.

**S0.3 — AI composition characterization.**
*Objective:* pin current provider-resolution behavior at all six sites before touching any of it. *Files:* new `tests/test_provider_resolution_parity.py` using the §N config matrix, **including the manual (no-provider) outcome** (revision 2). *Prereqs:* S0.1. *Changes:* tests only — they document today's divergences as *expected* (e.g. "CLI ignores named codex_medium profile: known"). *Done when:* the matrix runs all six resolution paths headlessly (no live providers) and pins their outputs.

**S0.4 — Owner decision packet** (revision 2 addition).
*Objective:* resolve the decisions that gate later design stages, before them. *Content:* §K questions — HTTP adapter fate (gates S1.2), provenance direction (gates S1.3), manual-grading semantics (gates S1.3), defaults-freezing preference (noted for S2.2), audio model/consent semantics (gates S4.8b), telemetry-first table-deprecation confirmation. *Done when:* answers recorded in this document's changelog.

### Phase R — Rebuild & recalibration (parallel track; design in §R)

**R1 — Table-role registry.** `DATABASE MIGRATION` (registry only, no schema change) `TESTING` — `db/table_roles.py` seeded from the §J audit; CI check for unclassified tables; `debug_time` and `goal_series` table knowledge re-pointed at it. *Prereqs:* S0.1. *Done when:* all 251 tables classified and CI fails on a synthetic migration adding an unregistered table.
**R2 — Rebuild orchestrator.** `ABSTRACTION CHANGE` — `rebuild-derived-state` invokes all registered replayers in dependency order; each replayer declares its owned `DERIVED` families; every other invocation point untouched (additive-only). *Prereqs:* R1, R3 tests written first. *Done when:* the registry cross-check passes (every `DERIVED` family has exactly one owning replayer) and the umbrella reproduces today's per-LO rebuild byte-identically on a fixture.
**R3 — Invariants.** `TESTING` — replay-completeness + rebuild-equivalence golden tests (§N). *Prereqs:* S0.1a (its diagnosis feeds this). Blocks R2 and S4.1.
**R4 — Shadow rebuild + diff.** `BEHAVIOR CHANGE` (new additive command) — `learnloop rebuild --shadow` generalizing the `goal_series` scratch pattern; learner-state diff report. *Prereqs:* R2. *Done when:* a shadow run on a fixture vault produces a diff report and the live DB hash is unchanged.
**R5 — Version hygiene.** Folds into S6.1b (mvp-0.9 upgrade target, playbook doc) and S7.1.

### Phase 1 — AI provider architecture

**S1.1 — Contracts move to `learnloop.ai`.** `MOVE/RENAME`
*Objective:* `ai` owns contexts, wire models, prompt text, prompt builders, strict-schema conversion, errors. *Files:* `codex/client.py` (regions a, e, e′ out), `codex/schemas.py`, `codex/prompts.py` → `ai/contexts.py`, `ai/schemas.py`, `ai/prompts.py`, `ai/strict_schema.py`, `ai/errors.py`; `codex/*` become re-export shims; delete the two dead `ai` shims first. *Prereqs:* S0.2. *Changes:* purely structural; error classes get their `AI*` names with `Codex*` aliases preserved. *Invariants:* every existing import path still resolves. *Tests:* full suite; import smoke. *Deletions:* `ai/prompts.py` + `ai/schemas.py` dead shims. *Risks:* pickling/module-path-sensitive code (none known; smoke test covers). *Done when:* `codex/schemas.py` is one re-export line and the suite is green.

**S1.2 — Structured transport + feature-owned operations.** `ABSTRACTION CHANGE` `DELETE` (redesigned in revision 2)
*Objective:* one provider protocol (`complete()`); each operation defined once, owned by its feature. *Files:* new `ai/transport.py`; `codex/client.py` (SDK client rebased onto the transport), `ai/openai_chat.py` rebased; each of the 22 operations becomes a function colocated with its owning service (interim home `ai/` until that domain's Phase-4 move); the 17 `getattr` sites simplified — structured-op probing becomes unconditional-with-client, degradation remains only for manual/no-client and (if retained) HTTP via `supports()`. *Prereqs:* S1.1, **S0.4's HTTP decision** — if HTTP is retained it becomes an explicit `LegacyHttpOperations` adapter; if retired, its config fields and startup machinery queue for S6.2. *Behavior:* none — §N parity + degradation-equivalence tests prove it; `AIInvalidOutput` subclasses the unavailable family so broad `except` blocks are unaffected. *Tests:* transport parity against SDK/chat fakes, degradation equivalence; full suite. *Deletions:* 22×2 duplicated method bodies; the 22-symbol private import block. *Risks:* per-operation subtleties hidden in the old bodies — the SDK `purpose=` strings and regeneration pre-pass become `StructuredRequest`/transport behavior, preserved and tested. *Done when:* adding a hypothetical 23rd operation touches only its owning feature.

**S1.3 — Composition root and the declared provider fixes.** `DEPENDENCY CHANGE` `BEHAVIOR CHANGE` `DELETE`
*Objective:* one resolution path; the six known defects fixed, each test-pinned. *Files:* `ai/routing.py` (+`ready_client_for_task`, `ROUTE_FOR_OPERATION`), `cli.py:1653–1743` + the three Codex-only commands, `learnloop_sidecar/handlers/ai_providers.py`, `tui/screens/feedback.py`, `services/startup.py`, `services/ingest_runner.py` (resolution regions only), `learnloop_sidecar/ingest_jobs.py`, `ai/codex_sdk.py` (identity fix), `services/settings_store.py` (whitelist fix). *Prereqs:* S0.3, S0.4 (provenance direction + manual semantics), S1.2. *Changes (behavior, each pinned):* (1) CLI/TUI honor named `codex_low`/`codex_medium` profiles; (2) startup honors non-Codex fallback; (3–5) `depth edges-author`, `depth backfill-rungs`, `clarification retry` route generically; (6) provenance keeps profile identity; (7) `input_modalities` copied; (8) resolution returns a typed **manual** outcome with today's semantics (pinned in S0.3). S0.3's characterization pins flip from "known divergence" to "unified"; decide wire-or-delete for the unused chat healthcheck hook. The four CLI→sidecar `ai_providers` imports and the TUI's one dissolve here. *Invariants:* selection precedence, fallback suppression for explicit/env, per-workflow refusal semantics. *Tests:* updated parity matrix (now asserting uniformity), provenance test, modalities test; full suite. *Deletions:* the six site-local resolution implementations; `uses_legacy_codex` + `_use_ai_provider`. *Risks:* №4/№5 in §M. *Done when:* `grep -rn "make_codex_client\|check_codex_runtime" src/ | grep -v ai/` returns nothing outside the composition root and providers.

**S1.4 — Provider relocation.** `MOVE/RENAME` *Files:* `SdkCodexClient` + `codex/runtime.py` → `ai/providers/codex.py`; `HttpCodexClient` → `ai/providers/codex_http.py`; `ai/codex_sdk.py` merged away; `ai/openai_chat.py`, `ai/openrouter.py` → `ai/providers/`. *Prereqs:* S1.3. *Behavior:* none. *Done when:* `codex/` contains only shims and `ai/` has no module importing `codex/`.

**S1.5 — `token_usage` and `agent_runs` relocation.** `MOVE/RENAME` *Files:* `token_usage.py` → `ai/usage.py` (delete the cycle-apology docstring — the cycle is gone), `services/agent_runs.py` → `ai/runs.py`; shims. *Prereqs:* S1.4. *Done when:* suite green; shims in place.

**S1.6 — Codex package deletion.** `DELETE` *Files:* migrate remaining `learnloop.codex` importers (mechanical rewrite; ~48 src + ~55 test files, mostly one-line), then delete `codex/`; `Codex*` error aliases remain in `ai/errors.py` one phase longer for test ergonomics, then drop. *Prereqs:* S1.4, S1.5. *Done when:* `grep -rn "learnloop.codex" src/ tests/` is empty and import-linter forbids the path.

### Phase 2 — Config, init, open

**S2.1 — Config schema honesty.** `CONFIG MIGRATION` `DELETE`
*Objective:* typed provider profiles; retire dead settings; stop generating `[codex]`. *Files:* `config.py` (or `config/` split done here if convenient — otherwise S2.2), `learnloop_sidecar/context.py:343`. *Prereqs:* S1.3 (no `config.codex` runtime readers remain), S1.6. *Changes (revision 2):* discriminated provider union — profiles omitting `type` keep the `codex_sdk` default; delete `auth_mode` + the **three** dead knobs (`coverage_epsilon` moved to S6.1b investigation; `severity_examples` stay modeled); `schema_version` → `2` with `1` accepted; `[codex]` parse-and-translate only; doctor notice for translated files. *Invariants:* every old-TOML corpus file normalizes to the same effective config (§N test, extended with a no-`type` profile). *Tests:* corpus test; full suite. *Risks:* №10. *Done when:* corpus test green; fresh template contains no `[codex]`.

**S2.2 — Minimal template + `learnloop config effective`.** `CONFIG MIGRATION` `SPLIT`
*Files:* `config.py` → `config/{schema,compat,template,loader}.py`; new CLI command; §H template (shipped defaults preserved exactly — revision 2). *Prereqs:* S2.1; S0.4's defaults-freezing answer noted. *Behavior:* new vaults only. *Tests:* template-equivalence test (§N — fresh vault from the new template produces an identical effective config); **defaults-snapshot test keyed by `algorithm_version`**; `test_init.py`. *Done when:* fresh vault TOML ≤ 80 lines and `config effective` round-trips the full model.

**S2.3 — Unified bootstrap.** `MERGE` `BEHAVIOR CHANGE`
*Files:* new top-level `learnloop/bootstrap.py` (revision 2 — app-level orchestration; `vault/` keeps pure scaffolding); `cli.py` init command; `learnloop_sidecar/handlers/vault.py`. *Prereqs:* S2.2. *Changes (behavior):* CLI populated-dir guard + `--force`; validation-before-writes for `starting_level` (all-or-nothing subject+level). Sidecar error codes unchanged. *Tests:* §N init tests; sidecar vault-creation tests; existing-config-untouched byte check. *Done when:* both entry points call one bootstrap function and the new tests pass.

**S2.4 — Read-only doctor via `Repository.attach`.** `ABSTRACTION CHANGE` `BEHAVIOR CHANGE` (redesigned in revision 2)
*Files:* `db/repositories.py` (new `attach()` classmethod only — the migrating constructor is **unchanged**, so the 100+ construction sites don't churn), `db/connection.py` (read-only `mode=ro` URI variant, no `mkdir`), `services/doctor.py` (schema version read first; every check gated on the tables it needs — `apply_intents` recovery requires migration 044), `services/goal_series.py` (scratch copies use `attach`). *Prereqs:* S0.2. *Changes:* plain doctor physically read-only, reports pending migrations; `--fix-state` migrates. *Tests:* §N read-only doctor + pre-044 byte-identity tests; full suite. *Done when:* plain doctor on an outdated pre-044 fixture completes, reports, and leaves the file byte-identical.

**S2.5 — Migration coordinator and connection hardening.** `BEHAVIOR CHANGE` `DATABASE MIGRATION` (mechanics, not schema; redesigned in revision 2)
*Files:* `db/migrate.py` (vault-level coordinator taking vault root + db path; lock via `vault_lock` — the db path is relocatable and cannot locate the lock), `db/connection.py` (`busy_timeout=5000`), `repositories.py` (delete ~19 ad-hoc pragmas). *Prereqs:* §N interruption + concurrency tests written first, **and a per-migration audit**: 25 scripts contain `PRAGMA foreign_keys` (a no-op inside a transaction) — FK-toggling scripts run un-wrapped and are validated with `PRAGMA foreign_key_check` afterwards; the rest get explicit per-script transactions. *Invariants:* fresh-path atomic publication untouched; applied-migration idempotency. *Risks:* №6 — highest care; smallest possible diff; audit results recorded in the stage PR. *Done when:* kill-mid-migration and two-process tests pass; no stray `busy_timeout` pragmas remain; `foreign_key_check` is clean on every fixture after a full upgrade.

### Phase 3 — Persistence boundary

**S3.1 — `db` stops importing domains.** `DEPENDENCY CHANGE`
*Files:* `repositories.py:14794, 24898, 25502` + the three enclosing methods; their callers pass policy constants/callables in. *Prereqs:* S0.2. *Tests:* causal-classification and legacy-write-guard tests. *Done when:* import-linter's `db → domains` rule has zero exemptions.

**S3.2…S3.n — Store extraction series.** `SPLIT` (one stage per family; suggested first four: observation ledgers, ingest queue, probe episodes, controller/attention re-home)
*Objective:* per-family stores under `db/stores/` (or the owning domain per §G), `Repository` delegating. *Prereqs:* S3.1. *Changes:* method bodies move verbatim; facade methods become one-line delegations; the family's `_decode_*` helpers travel along. *Invariants:* every public `Repository` method keeps signature and behavior. *Tests:* full suite per family. *Deletions:* none until a family's facade methods lose all callers (tracked, deleted opportunistically). *Stop-anywhere:* explicitly allowed; each extraction stands alone. *Done when (per stage):* family SQL exists in exactly one module.

### Phase 4 — Domain packages (each stage: `MOVE/RENAME` + API promotion; behavior changes only where declared)

Order chosen by fan-in (most-depended-on first, so later moves don't re-touch earlier packages):

**S4.0 — Substrate public API.** Promote `activities._canonical_hash/_json` → `canonical_hash/canonical_json`; rewrite the 37 importers + the alias use. *Done when:* no underscore imports of `activities` remain.
**S4.1 — `substrate/`** (incl. `compat/` with README quoting the freeze decision; `state_sync`, `replay`, `canonical_projection*` move here). *Tests:* replay/backfill/cutover suites. Risk №3.
**S4.2 — `attempts/`** — move-only (revision 2: the receipt extraction is withdrawn, §D; receipts live in the sidecar) plus promotion of `_resolved_codex_grade`, `_row_to_clarification`; the domain's operation contracts (grading contexts/models) travel with it per §E contract staging. *Prereq:* §N ordering characterization test. Risk №1.
**S4.3 — `learner/`.**
**S4.4 — `diagnosis/`** (largest move; two commits if needed: probes+causal, then remediation+followups). Promote the guided-redo/remediation privates used by sidecar (`feedback.py:658,663`, `remediation.py:12`).
**S4.5 — `scheduling/`** (incl. controller family; promote `_FOLLOWUP_REASONS`). *Tests:* scheduler golden + cutover. Risk №11.
**S4.6 — `goals/`.**
**S4.7 — `curriculum/`.**
**S4.8a — `content/` moves + runner split.** Move-only (revision 2 split): the content service modules move (IR/extractors **stay** in `learnloop/ingest`); `ingest_runner` splits into `pipeline/runner.py` (queue mechanics) and `pipeline/jobs.py` (handlers); `DurableIngestJobs` moves out of the sidecar into `content/pipeline` (fixing the CLI→sidecar import at `cli.py:2132`); `exam_ingest` alias preserved. *Tests:* full ingest queue/recovery suite. Risk №7.
**S4.8b — Audio `transcription` route.** `BEHAVIOR CHANGE` `CONFIG MIGRATION` — the ninth route + `[ingest.audio]` normalization (§H); the hardcoded-profile branch (`_extract_audio_openrouter`) deleted only after the §N characterization pins model/timeout/consent through the new path; doctor notice for translated config. *Prereqs:* S0.4 (audio semantics), S1.3, S4.8a.
**S4.8c — Gen-1 deletion.** `DELETE` — `services/ingest.py` + its test (sole importer). PDF-extractor consolidation remains a separately flagged behavioral migration, **not scheduled** by this proposal.
**S4.9 — `reader/` + `tutor/`.**
**S4.10 — `ops/`.**
**S4.11 — Delete `services/`.** `DELETE` *Done when:* the directory is gone, import-linter forbids `learnloop.services`, **the dynamic-reference inventory shows zero remaining `learnloop.services.*` strings**, and CLAUDE.md/docs are updated in the same commit (they reference the path).

### Phase 5 — Entry points

**S5.1 — `cli/` package split.** `SPLIT` One module per sub-app; `cli/render.py` for shared output; behavior byte-identical (`--help` snapshots as the test oracle). *Prereqs:* S1.3 (composition), phase 4 (import targets stable).
**S5.2 — Sidecar import narrowing.** `DEPENDENCY CHANGE` Re-point remaining private imports to promoted APIs (should be zero by now — this stage is the audit); add the serializer snapshot test if not already landed. *Done when:* import-linter's "adapters use public names only" rule has zero exemptions.

### Phase 6 — Legacy, state, decisions

**S6.1a — Deprecated-state telemetry.** `TESTING` `DATABASE MIGRATION` (doctor check only, no schema change) — the §J step-1 doctor row-count check for the three contested tables, run on the owner's real vaults **before** anything is detached.
**S6.1b — Investigations.** `TESTING` `DOCUMENTATION` — `probe.dialogue.max_turns`, `evidence_span_input_tokens`, `coverage_epsilon` (wire or delete, each with a one-line finding recorded in the changelog); `grade_diagnostic_fire` (wire into the transport design or delete the probes); mvp-0.9 upgrade-target gap resolved with the §N fixture (R5); `goals.md` disposition; algorithm-change playbook doc (R5).
**S6.1c — Dead-code batch.** `DELETE` — repository CRUD orphans, `learner_theta` references (only after S6.1a reports clean), `cross_lo_propagation` typed model (doctor warning kept), sqlite_admin FK pragma (owner-gated).
**S6.2 — Owner-gated deletions.** `DELETE` `CONFIG MIGRATION` Execute whichever of §K questions 1–6 the owner approved: HTTP adapter removal, provenance direction confirmation, `goals.md` disposition, table-drop parking confirmed.

### Phase 7 — Documentation

**S7.1 — Docs truth pass.** `DOCUMENTATION` README (`mvp-0.8` → current reality), `documentation.md`, CLAUDE.md (new tree, new commands), a top-level `ARCHITECTURE.md` with the §B tree + §G rules + a pointer to `substrate/compat`'s freeze README; stale comment `config.py:703`. *Done when:* grep for `mvp-0.8` in docs returns only historical notes.

### Classification summary (requirement 12)

| Change | Classification | Semantics |
|---|---|---|
| Contracts/providers/usage relocation (S1.1, S1.4, S1.5, S1.6) | MOVE/RENAME, DELETE | none |
| Transport + feature-owned operations (S1.2) | ABSTRACTION CHANGE, DELETE | none (parity-proven; error subclassing preserves `except` behavior) |
| Composition root + fixes (S1.3) | DEPENDENCY, BEHAVIOR, DELETE | 7 declared changes + typed manual outcome (behavior-preserving) |
| Rebuild workstream (R1–R4) | DATABASE (registry only), ABSTRACTION, TESTING, BEHAVIOR (R4: new additive command) | additive only; replayer invocation points untouched |
| Config typing + dead-setting removal (S2.1) | CONFIG MIGRATION, DELETE | none for old vaults |
| Template + config split (S2.2) | SPLIT, CONFIG MIGRATION, TESTING | new vaults only; shipped defaults preserved |
| Bootstrap unification (S2.3) | MERGE, BEHAVIOR | 2 declared changes |
| attach() + read-only doctor (S2.4) | ABSTRACTION, BEHAVIOR | 1 declared change |
| Migration coordinator + connection hardening (S2.5) | BEHAVIOR, DATABASE (mechanics) | 2 declared changes |
| db→domain import removal (S3.1) | DEPENDENCY CHANGE | none |
| Store extractions (S3.2+) | SPLIT | none |
| Domain moves (S4.x) | MOVE/RENAME + API promotion | none — the audio change lives in its own stage (S4.8b) |
| Audio `transcription` route (S4.8b) | BEHAVIOR, CONFIG MIGRATION | 1 declared change, characterized first |
| `services` deletion (S4.11) | DELETE | none |
| CLI split (S5.1) | SPLIT | none |
| Telemetry / investigations / dead code (S6.1a–c) | TESTING, DATABASE (doctor check only), DELETE, DOCUMENTATION | sqlite_admin FK pragma if approved |
| Owner-gated deletions (S6.2) | DELETE, CONFIG MIGRATION | per decision |
| Docs (S7.1) | DOCUMENTATION | none |

---

## Closing

The archaeology's closing assessment said the challenge is "identifying authority, transaction, replay, compatibility, and capability boundaries that already govern behavior despite being spread across directories." This proposal's entire content is making exactly those boundaries load-bearing in the package structure: the AI candidate/authority boundary becomes `ai/` vs the domains; the frozen-compatibility boundary becomes `substrate/compat/`; the SQL-authority boundary becomes the store rule; the selection-authority boundary becomes one `scheduling/` package containing its own cutover; the config truth boundary becomes template-vs-model. Nothing here is a new architecture — it is the existing architecture, given names, tests, and a deletion path for everything that stopped being true.

Sequencing risk is deliberately front-loaded into small, reversible stages: the plan survives being abandoned after any stage boundary, and the highest-value work (Phase 1, Phase R, S2.1) is also the earliest and least entangled.

---

## Revision 2 Changelog (2026-08-17)

Revision 2 incorporates two inputs: an adversarial agent review of revision 1 (every load-bearing claim re-verified against the repository before acceptance — §0 second round) and the owner's requirement that large algorithmic changes be easy to make and evaluate (§R).

### Accepted from the review (proposal changed)

- `learnloop/ingest` stays top-level infrastructure — `db/repositories.py:23` imports its IR contracts, so the `content/` absorption would have violated the proposal's own `db → domain` rule (§B, §C, §G).
- The AI layer is redesigned from a 22-method protocol + operation table to **`StructuredTransport` + feature-owned operations**, with parity by construction and `supports()` narrowed to media/interrupt/legacy-HTTP; the HTTP adapter's fate moves *before* the design stage because it cannot implement `complete()` (§E, §F, S1.2, Alternatives 1).
- Migration hardening redesigned: per-migration audit (25 scripts contain `PRAGMA foreign_keys`, a no-op inside transactions — FK-toggling scripts run un-wrapped and validate via `foreign_key_check`); a vault-level coordinator takes the vault root because the relocatable db path cannot locate the lock (§I, §J, S2.5).
- Read-only doctor redesigned: `mode=ro` URI, no directory creation, schema-version gating — the pre-044 `apply_intents` crash scenario is real (§I, S2.4). `Repository.attach()` is added instead of changing constructor semantics at 100+ sites.
- The template preserves every shipped default — revision 1's example flipped `animation.enabled` (true) and codex `reasoning_effort` (low) — and the omitted-defaults drift problem is answered with a CI defaults-snapshot test keyed by `algorithm_version` (§H). `schema_version` bumps to 2; the `pdf.engine` comment corrected to `native`; no-`type` profiles keep the `codex_sdk` default.
- The "drop-if-empty, abort otherwise" table migration is **withdrawn** — an aborting migration would block the sequential chain and vault opening; telemetry now precedes code detachment, and schema drops are replaced by (at most, owner-gated) archive-renames (§J, §L, S6.1).
- The `attempts.py` receipt extraction is withdrawn — receipts live in `handlers/practice.py:632` + `repositories.py`, not in `attempts.py` (§D, S4.2).
- `probe_robust` reclassified **ACTIVE** (the mvp-0.8/0.9 path) and `p0_projection` **mixed** (live reinterpretation appends) — both out of the frozen list (§C, §K).
- `severity_examples` stay modeled config (consumed at `recall_calibration.py:133`); `coverage_epsilon` moved from REMOVE to investigate (possibly unimplemented spec behavior, not dead) (§H, §K).
- Dynamic `learnloop.services.*` module strings (parameter registry, open-world gate, scoreboard — silent `no_producer` degradation) become first-class migration dependencies with functional tests (S0.2); `taxonomy_regrade` added to the map (diagnosis); `grade_diagnostic_fire` recorded as a dormant speculative seam (§K).
- Store rule refined: write-ownership *exclusivity* plus a sanctioned cross-family read-model category — not store purity or location; `controller_store`'s imports acknowledged (§G, §D).
- `ops/` trimmed to the operational core; parameter-governance and scoreboard placements reopened; `sim` classified as an evaluation library (§B, §C).
- Entry-point cross-imports acknowledged as current violations with concrete fixes: four `ai_providers` helper imports + the TUI's dissolve into the composition root (S1.3); `DurableIngestJobs` moves to `content/pipeline` (S4.8a) (§G).
- Manual grading modeled as a typed resolution outcome and added to the characterization matrix (§E, S0.3); `AIInvalidOutput` subclasses the unavailable family so existing `except` behavior is preserved (§E).
- Audio consolidation redesigned: a ninth `transcription` route + config normalization of `[ingest.audio]` (preserving the independent-model use case), in its own characterized stage S4.8b — no longer bundled with file moves.
- OpenRouter parity qualified as **code-path parity**; live semantic parity remains untested and deferred (§F, §N).
- Stage hygiene: S0.1, S4.8, and S6.1 split into separately reviewable changes; owner decisions front-loaded into S0.4; documentation updates required in-stage for every behavior change.

### Rejected after verification (proposal unchanged, with evidence)

- The review's migration citations use a nonexistent path (`src/learnloop/db/migrations/…`); migrations live at `migrations/`. Its substance was re-verified at the real path before any acceptance.
- "Existing and newly initialized vaults change behavior" from the template change — false for existing vaults: `write_default_config` (`config.py:2214–2217`) returns early if the file exists. Only new vaults see the template; the drift concern applies to future minimal-config vaults and is addressed by the snapshot test.
- "The target dependency graph cannot be implemented as stated" — half-true only: the db→ingest edge was a real violation (accepted); contracts-in-`ai/` created no `ai → domain` import (`codex/schemas.py` imports only pydantic/typing/`attempt_types`). The AI redesign was adopted on cohesion grounds, not implementability.
- "Eleven top-level packages in one migration" — the plan was already one-domain-per-stage; revision 2 only makes the promotion gate explicit (a domain moves after its import contract is clean).
- Dropping S0.2's early boundary enforcement — codifying the *current* graph with a ratchet is what makes later moves reviewable; it stays (and gains the dynamic-reference inventory).
- Keeping the `services/` prefix (review §13) — position held; the review's own §7 table endorses nearly every grouping, and the residual dispute is an information-free path segment. Owner may override as a one-parameter change.
- Runtime immutable-default bundles — rejected as runtime machinery for a policy question; the CI-time snapshot keyed by `algorithm_version` gives the same guarantee (Alternatives 4, Option D).
- Splitting `diagnosis` as "too broad" — the SCC evidence favors one package; splitting would put the densest cycle across boundaries. Internal subfolders may be used at stage time.

### Added

- Workstream §R (owner requirement): table-role registry (R1), rebuild orchestrator over the existing replayers (R2, additive-only), replay-completeness + rebuild-equivalence invariants (R3), shadow rebuild + diff (R4), version hygiene including the mvp-0.9 upgrade target and the algorithm-change playbook (R5). Owner questions 7–11 added to §K.

### Implementation decisions (2026-08-17)

The implementation request adopted the proposal's conservative defaults for
the previously open gates:

1. Retain the legacy HTTP adapter as an explicit optional capability.
2. Preserve named profile identity (`codex_low`, `codex_medium`, or another
   configured name) in provenance.
3. Keep the Textual TUI.
4. Keep scaffolding and support for `goals.md` pending a separate product
   decision.
5. Keep the gen-2 `source_ingestion` implementation behind the frozen
   `legacy_ingest`/`exam_ingest` queue aliases.
6. Add telemetry for contested tables, but perform no schema drops or archive
   renames in this refactor.
7. Model manual grading as a typed no-client resolution outcome with the
   existing workflow semantics.
8. Freeze omitted defaults per `algorithm_version` with a CI fingerprint; do
   not write a full runtime default bundle into each vault.
9. Preserve independently selected transcription models and the existing
   audio-specific consent behavior through the `transcription` route.
10. Make plain doctor physically database-read-only; provider diagnostics are
    reported only when explicitly requested by an AI workflow.
11. Complete the in-repository path migration and compatibility-shim period;
    no external consumer contract is inferred beyond the repository.

### S6.1 investigation findings (2026-08-17)

- `probe.dialogue.max_turns` had no runtime reader; it is retired from the typed
  model and generated template, while legacy TOML is accepted and ignored.
- `ingest.budgets.evidence_span_input_tokens` had no runtime reader; it is
  retired with the same parse-and-ignore compatibility behavior.
- `recall_coverage.coverage_epsilon` had no executable coverage-floor consumer;
  retaining the knob would imply behavior the implementation does not provide,
  so it is retired and accepted only as ignored legacy input.
- `grade_diagnostic_fire` is retained and implemented as the shared structured
  `grading` operation by the SDK and chat transports; diagnostic/persona gates
  preserve their manual/no-capability fallback.
- `goals.md` remains scaffolded and loadable as directed by decision 4; no
  authority migration is part of this refactor.
- The upgrade target is now `mvp-0.9`, with a fixture-backed `mvp-0.8` successor
  test and the algorithm-change playbook at `docs/algorithm-change-playbook.md`.

### Deprecated-state telemetry evidence (2026-08-17)

All ten repository fixture databases were inspected read-only.  Every present
`source_exam_profiles`, `source_locator_schemes`, and `learner_theta` table had
zero rows; older fixtures in which a table predates the migration were reported
as unavailable rather than treated as empty.  No owner production vault is
present in this checkout, so the doctor warning remains the required stop gate:
any nonzero production count must be escalated before further state retirement.

### S2.5 migration audit outcome (2026-08-17)

The implementation deliberately strengthens the proposal's initial
``foreign_keys=OFF`` exception.  FK-rebuild scripts disable enforcement before
``BEGIN IMMEDIATE``, execute their parsed statements and migration receipt in
one transaction, run ``foreign_key_check`` before commit, and restore
enforcement in ``finally``.  This avoids the partial/unreceipted state possible
with an unwrapped rebuild while preserving the required pragma ordering.  The
synthetic failure test and an injected interruption in the real migration 153
both prove body-and-receipt rollback plus FK restoration.



