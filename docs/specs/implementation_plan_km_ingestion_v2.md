# Implementation Plan: Knowledge Model + Source Ingestion v2

Audience: an engineer who has **not** worked in this repository. This plan explains the codebase you are walking into, then sequences the implementation of two coordinated specifications:

- `spec_knowledge_model.md` (rev 4) — "KM": canonical shared facets, criterion-level observations, capability-aware certification, read-side projections.
- `spec_source_ingestion_v2.md` (rev 7) — "ING": source library, Document IR, durable jobs, role-specific inventories, synthesis into study maps, provenance, append.

Read both specs before starting any milestone. This plan tells you *where* and *in what order*; the specs are normative for *what*. Where this plan and a spec disagree, the spec wins.

---

## Part 1 — Orientation: the codebase you're entering

### 1.1 What LearnLoop is

A local-first adaptive learning app. A user's data lives in a **vault**: a directory of YAML/Markdown files (subjects, concepts, Learning Objects, Practice Items, rubrics, notes, goals) plus one SQLite database (`state.sqlite`) holding derived learner state and event history. There is no server; AI features call a local Codex runtime through a typed client.

Three layers, one service core:

```
apps/learnloop-tauri/          React + TypeScript UI (terminal aesthetic), Tauri shell
  src/screens/*.tsx            one file per screen (TodayScreen, PracticeScreen, ...)
  src/api/client.ts, dto.ts    typed RPC client + DTO definitions (camelCase)
  src-tauri/src/commands.rs    Rust proxy commands → Python sidecar

src/learnloop_sidecar/         JSON-RPC sidecar (Python)
  handlers/*.py                one module per feature area; thin: parse → service → serialize
  ingest_jobs.py               CURRENT in-memory job manager (to be replaced by ING M2)

src/learnloop/                 the actual product (Python)
  services/*.py                ALL business logic lives here (~40 modules)
  db/repositories.py           ALL SQL lives here (one large module; no SQL elsewhere)
  vault/                       YAML loaders/writers/models/paths (ruamel.yaml, pydantic v2)
  codex/client.py              typed LLM client; methods discovered via getattr so providers degrade
  ingest/                      fetchers, detection, resolution (acquisition kinds)
  sim/                         simulation harness (synthetic students through the REAL pipeline)
  cli.py                       Typer CLI; CLI and sidecar call the SAME services
  config.py                    embedded default TOML + pydantic models; per-vault learnloop.toml

migrations/NNN_*.sql           sequential SQLite migrations (currently 001–031; 032+ is free)
fixtures/                      small real vaults used by tests (linear_algebra, arxiv, law, ...)
tests/                         ~1060 pytest tests; deterministic, no network, FrozenClock
```

Run everything with: `python -m pytest -q` (full suite), `npx tsc --noEmit` and `cargo check` for the frontend/shell.

### 1.2 The invariants you must not break

These are load-bearing across the entire codebase. Every milestone below is designed around them.

1. **Evidence, not mastery.** No service writes mastery/belief state directly. All belief change flows through `apply_attempt` (`services/attempts.py:778`), which persists an attempt + grading evidence and updates derived state in one transaction. If you find yourself writing a belief row from anywhere else, stop.
2. **Replay determinism.** `rebuild_derived_state` (`services/replay.py:99`) must reproduce byte-identical derived state from the event history. Anything time-dependent uses `clock.py` / FrozenClock. Anything algorithm-dependent is stamped with `algorithm_version` (vault-global config field; currently `mvp-0.6`). Old vaults replay **frozen** under their recorded version — new behavior activates only at `mvp-0.7`.
3. **The LLM never writes files.** All AI-authored content flows through `AuthoringProposal` → `proposed_patches`/`proposed_patch_items` (SQLite) → human/auto review → `apply_accepted_items` (`services/patches.py:47`) → controlled vault writer. Every Codex call has an `agent_runs` row; caching keys on `agent_runs.input_context_hash`.
4. **CLI and Tauri share services.** A feature is not done when the service works: it needs CLI JSON output, a sidecar handler, a Rust proxy command, DTO + client types, and (usually) a screen. New Rust commands require a **full app restart**, not a Vite reload (`client.ts` surfaces this as `stale_app_binary`).
5. **Migrations are append-only** and SQLite `CHECK` constraints can't be altered in place — changing one means the full `CREATE new → copy → drop → rename` dance (see `migrations/002` for the pattern).

### 1.3 The current state the specs are fixing

- Facet belief is keyed `(learning_object_id, facet_id, practice_item_id)` in `evidence_facet_recall_state` (migration 007) — the same fact relearned under every LO. **Thirteen modules** read/write this table; the KM re-key is the single biggest change point.
- `criterion_facet_weights` are empty in all 92 fixture items; attribution runs through a lexical fallback (`services/recall_coverage.py:772`).
- Ingestion is one atomic call (`services/source_ingestion.py:130`, ~2,500 LOC): fetch → extract → register → LLM authoring → auto-apply, one source at a time. PDF extraction (`services/pdf_extraction.py`) flattens marker output to Markdown and its cache key omits the marker version (stale-cache bug).
- Ingest jobs are in-memory only (`learnloop_sidecar/ingest_jobs.py`); nothing survives restart. There is **no cross-process lock** and **no `identity_locks`/`can_apply` implementation** — the specs' lock machinery is new work, not a refactor.
- The Tauri IngestScreen is a thin single-source form; ProposalsScreen is item-by-item accept/reject with no dependency concept.

### 1.4 The dependency spine (memorize this)

```
ING M1 → M2 → M3 → [M3.5 v2-lite SHIP] ─┐
KM1 (parallel with M1–M3) ──────────────┼→ ING M4 → M5 ─┐
KM2 (needs KM1) ────────────────────────┴───────────────┼→ ING M6 → M7 [CORE SHIP]
                                                        │
KM3 (needs KM2, benefits from M6 fixtures) ─────────────┘→ KM4 → KM5 → M8 → restructure-with-history spec
```

Hard rules: **KM1 must be final before M4 freezes the inventory schema. KM2 must be live before M6 applies a learnable study map.** KM1–KM2 is the lock-sensitive window: no real-learner attempts may accrue against v2 content before KM2's state model exists. `algorithm_version` is vault-global, so mvp-0.7 activation is an atomic per-vault upgrade; fixture vaults are **recreated, not migrated**.

---

## Part 2 — Milestones

Each milestone lists: goal, main work items with file locations, schema changes, acceptance (pointing at the specs' §14/§16 verification lists), and pitfalls.

### Phase 0 — Groundwork (days, not weeks)

- Read both specs end-to-end; skim `documentation.md` and the July 2026 entries in the project memory/commit log.
- Baseline: full test suite green, `tsc`/`cargo check` clean, fixtures load (`learnloop doctor` on each `fixtures/*`).
- Commit the currently-uncommitted files (`ingest/resolution.py`, `learnloop_sidecar/ingest_jobs.py`, `tests/test_ingest_jobs.py`) — M1/M2 build on and eventually replace them.
- Reserve config blocks in `config.py`: `[ingest.budgets]`, `[ingest.providers.<name>]`, `[evidence.correlation]`, `[evidence.certification]`, `[evidence.blueprints]`, `[capabilities]`, `[locks]`. Empty-but-parsed now avoids churn later.

### ING M1 — Source layer (Track A)

**Goal:** immutable source identity (work → artifact → revision → extraction run) and the Document IR, with marker's structure preserved instead of flattened.

Work items:

1. **IR types** — new `src/learnloop/ingest/ir.py`: `DocumentBlock`, `DocumentUnit`, `DocumentAsset`, `ExtractionHealth` per ING §2.3. Pure dataclasses/pydantic; no extractor imports.
2. **Extractor providers** — new `src/learnloop/ingest/extractors/`: a `DocumentExtractor` protocol returning IR; `MarkerDocumentExtractor` (adapt the marker calls currently in `services/pdf_extraction.py`; keep marker behind a subprocess/adapter boundary — it's GPL-3.0, treat it as an optional user-installed provider from day one); `PyPdfDocumentExtractor` fallback; adapt the existing HTML/YouTube/text normalizers in `src/learnloop/ingest/fetchers.py` to emit trivial IR (units from headings/time ranges, no geometry).
3. **Migration 032** — `source_artifacts`, `source_revisions`, `source_extraction_runs` (with `extraction_request_hash`/`extraction_result_hash`, `UNIQUE(revision_id, extraction_request_hash)`), `source_document_units/blocks/assets`, `source_span_reanchors`. Schemas are in ING §2.3/§2.4 verbatim.
4. **Hash model** (ING §2.2) — request hash computable pre-execution (retry key); result hash on completion; per-unit `semantic_hash` with the specified normalization (strip markup, collapse whitespace, drop headers/footers, equations verbatim). Replace `pdf_extraction.py`'s `_cache_key` (it currently keys bytes+options only — the stale-cache bug ING §2.5 names).
5. **Vault-level `sources/` layout** — extend `vault/paths.py`; legacy `subjects/<id>/notes/` source notes stay readable in place; a small indexing pass registers legacy notes as artifact/revision rows without moving files (ING §13).
6. **Locator schemes** — declare `block_span_v1`; backfill migration stamps shape-detected schemes onto existing refs: `heading_path_v1` (`root/section-slug/p1`), `time_range_v1` (`t=a-b`), `arxiv_label_v1` (`thm:4.2`). Resolution code lives near `services/source_ingestion.py`'s `_locator_resolves`/`analyze_source_change` — those must keep working unchanged for legacy refs forever.
7. **Re-anchoring** — deterministic cross-run span re-anchor: exact content-hash wins only when unique; disambiguate by section/page/neighbors; ambiguous → `needs_reanchor`.
8. **Block-role hints** (ING §2.6) — deterministic classifier module, external to the marker adapter.

Acceptance: ING §14 rows 1–5 (identity, re-anchor, cache key, adapter contract, hash split). Pitfall: marker returns `FlatBlockOutput` from the *chunks renderer* — map ids/types/geometry/section hierarchy directly; do not re-derive structure from rendered markdown.

### ING M2 — Durable workflows (Track A)

**Goal:** repository-backed batches/jobs replacing the in-memory manager; work survives restarts.

Work items:

1. **Migration** — `ingest_batches`, `ingest_jobs`, `ingest_job_dependencies` (ING §6.2; `workflow_type`/`job_type` are app-validated open strings, NOT SQL CHECKs).
2. **Runner service** — new `services/ingest_runner.py`: leased sequential drain (`worker_id` + `heartbeat_at`), status vocabulary `queued|running|waiting_for_input|completed|failed|blocked|cancelled`, checkpoint ladder (`acquired → registered → extracted → inventoried → synthesized → proposed → applied`), retries keyed by the stage's idempotency hash, per-call `usage_json`.
3. **Worker hosts** — the sidecar hosts the drain loop while the app runs; the CLI drains foreground when no sidecar lease exists. Same lease; exactly one drains. Keep `learnloop_sidecar/ingest_jobs.py` as a thin compatibility wrapper that enqueues into the durable queue, then delete its subprocess machinery once parity tests pass.
4. **Sidecar/Tauri** — batch/job RPCs (start/get/list/cancel/resume), and the **Batch progress** + **Source library** screens (ING §5.7): card grid, checkpoint ladder, actual-vs-estimate token bars, `waiting_for_input` as actionable cards.

Acceptance: ING §14 queue-persistence and worker-host rows (restart survival, lease expiry → `interrupted`, dependency failure → `blocked`, no concurrent drain). Pitfall: `waiting_for_input` must hold **no** lease, or a question to the user blocks the whole queue.

### ING M3 — Outline, selection, budget planning (Track A)

**Goal:** users choose units and see costs before any pedagogical LLM call.

Work items: deterministic outline view over the IR (zero agent runs); unit-selection persistence with user boundary-overrides surviving re-extraction; acquisition preview + build plan (ING §8.6) with per-stage token estimates from `[ingest.budgets]`/provider limits; consent-gated extraction-repair flow ("Improve N difficult pages" → page-range repair run with `parent_extraction_id`); **Outline & unit selection** and **Build plan** screens.

### ING M3.5 — v2-lite (SHIP THIS)

Wire M1–M3 output into the *legacy* single-source synthesis (`services/source_ingestion.py` keeps building its markdown-chunk context from the IR's display rendering). Users get: better extraction, health/repair, durable queue, library, unit selection — while KM1/KM2 land. This is a named release; treat it as one (changelog, fixture smoke test, dogfood on a real textbook).

### KM1 — Semantic/task/observation contracts (Track B; parallel with M1–M3)

**Goal:** the vocabulary of the new knowledge model exists as validated schemas, doctor checks, and proposal plumbing — before any belief-state change.

Work items:

1. **facets.yaml schema_version 2** — extend `EvidenceFacet` in `vault/models.py` per KM §3.2 (kind, claim, pre/postconditions, examples, non_goals, error_signatures, instructional_repairs, aliases, status, version, `semantic_fingerprint`, provenance). Loader in `vault/loader.py` already resolves aliases (`canonical_facet_id`); extend, don't replace.
2. **Doctor** — fix the empty-registry skip (`services/doctor.py:588`): for mvp-0.7 vaults, facet-bearing items with an empty/non-covering registry are **errors**; legacy vaults keep warnings. Add contract-completeness checks.
3. **Candidate harvesting** — CLI `learnloop facet-candidates`: gather from unit inventories, LO summaries, rubric criteria, existing `evidence_facets`, fatal errors, misconception statements (KM §3.3). Similarity (lexical/MinHash) proposes review only.
4. **Blueprints/recipes** — LO YAML gains `blueprints:` with AND/OR recipes, capabilities, integration facets, requirement modality (KM §7.2/§8.2). Flat `evidence_facets` becomes a derived union for compatibility.
5. **Criterion targets** — rubric criteria gain `targets: [{facet, capability, role}]`, `depends_on` DAG, `correlation_group`, `recipe_ids` (KM §5.1). Ship the **mode→capability default mapping table** as data (used when recreating fixtures).
6. **Assessment contract snapshots** — migration: `assessment_contract_versions` + observation columns (`observation_id`, `grading_revision`, `assessment_contract_version_id`, `recipe_id`, `attribution_json`, `correlation_group`) added to/alongside `grading_evidence` (KM §5.2). Snapshot at item presentation; grading references the snapshot.
7. **Proposal dependency schema** — `proposed_patch_item_dependencies` + `dependency_status`; expand the closed `item_type`/`target_entity_type` CHECKs on `proposed_patch_items` (migration 001) **and** `content_events.entity_type` (migration 002) for `facet`, `task_blueprint`, `provenance_link`, `notation_mapping`, `source_conflict` — both need the SQLite table-rebuild dance.
8. **Generated-item gate** — reject unregistered facet ids on new items (mirror the existing probe-instance gate in `services/probe_instance_generation.py`).
9. **`can_apply()` skeleton** — new `services/curriculum_locks.py`: the single lock API (KM §12.1). At KM1 it computes locks from existing sources (attempts, goals, probes, misconceptions); the facet independence gate arrives with KM2's ledgers. `identity_locks()` is a read adapter over it.

Acceptance: KM §16 registry/recipe/observation rows that don't require new belief state. Pitfall: nothing in KM1 may change replay output for existing vaults — it is all schema, validation, and snapshots for *future* attempts.

### ING M4 — Source sets and role-specific inventories (needs KM1 final)

**Goal:** collections with pinned revisions and cached per-unit inventories whose schema encodes KM1's contracts.

Work items: `source_sets` YAML (membership owns role/scope/priority, pinned `revision_id`, unit `role_override` — ING §4.3) + loader/writer; `source_unit_inventories` table + cache identity (ING §7); role-aware inventory prompts as new `codex/client.py` methods (getattr-discovered, like `run_probe_instance_surfaces`) emitting the `SourceUnitInventory` contract with span-id citations; exam use modes (`held_out_evaluation | available_for_practice | blueprint_only`) + paper metadata (year/syllabus/weighting, same-family dedup); deterministic exam profile aggregation; coverage preview (ING §9.3, CLI first); **unknown roles fail closed for authority**.

Pitfall: `inventory_profile` is part of cache identity; a `combined` inventory may satisfy a narrower profile only when its schema version guarantees the fields. Get the UNIQUE key right the first time — it's the token-economics linchpin.

### ING M5 — Safety, provenance, dependency foundation

**Goal:** everything that must be true before an LLM builds curriculum at scale.

Work items:

1. **Vault mutation lock** — OS advisory file lock at `.learnloop/vault.lock` (flock-style, timeout, holder pid/purpose), taken by CLI and sidecar around accept-time critical sections. Nothing like this exists today.
2. **Write-ahead apply protocol** (ING §10.2) — rework `services/patches.py` acceptance: durable intent record in SQLite → staged fsynced temp YAML → atomic rename → mark applied; startup/doctor recovery completes or rolls back mid-flight intents; **process-kill tests at each boundary**.
3. **`entity_source_links`** table + writes from `apply_accepted_items` (ING §9.1); `notation_mappings`, `source_conflicts` tables.
4. **Synthesis gates** — new `services/synthesis_gates.py` implementing the ING §8.7 table (typed per-gate diagnostics; includes exam-authority, leakage, identifiability-hook, near-duplicate, token gates).
5. **Manifests** — `synthesis_manifests` + `synthesis_runs`; manifest hash becomes the `agent_runs.input_context_hash` cache seam.
6. Provenance/coverage services + `get_entity_provenance` sidecar + provenance panel.

### KM2 — Shared state + lineage (the big one; needs KM1)

**Goal:** belief state re-keys from per-LO to canonical facets, with capability ledgers and immutable observation lineage. This is the milestone that fixes the measured grind.

Work items:

1. **Migrations** — `facet_recall_state` (canonical id + `capability_key` + partial unique indexes), `facet_capability_evidence`, `facet_merges` (transitive, cycle-rejected at write), `unresolved_cause_factors` (KM §7.1/§5.2). Old `evidence_facet_recall_state` + `facet_uncertainty` stay read-only for frozen replay; `facet_uncertainty` re-keys to facet-only; `misconceptions` re-keys `target_facet`/`confused_with_facet` canonically.
2. **Write-path re-key** — `apply_attempt` → `recall_coverage.py` (`build_facet_recall_updates_from_prior` and friends) branch on `algorithm_version`: mvp-0.7 writes canonical rows via the KM §5.4 allocation rule (evidence_mass × criterion_share; roles 1.0/0.3; failure follows attribution distribution; unresolved → cause factor). First-error localization generalizes from `services/longform_trace.py` to all multi-facet items (KM §5.3).
3. **Consumer re-key** — the thirteen `evidence_facet_recall_state` readers: `recall_coverage`, `recall_calibration`, `goal_projection`, `facet_diagnostics`, `selection_rewards`, `scheduler`, `followups`, `practice_generation`, `exam_session`, `ability_transition`, `question_signal`, `attempts`, plus `repositories.py` SQL. Each gets a version-branched read (legacy vs canonical).
4. **Certification ledger** — derive `facet_capability_evidence` from observations (four-quantity rules, group budgets, attempt ceiling, group-proliferation flag — KM §5.4).
5. **Evidence fingerprints + vault-wide correlation lookup** (KM §6).
6. **Independence-gated locks live** — `can_apply` gains the §3.4 trigger (≥2 surface groups / `facet_lock_mass` / goal certified scope); pre-lock merge/split via `facet_merges`.
7. **Hand-authored fixture registries** — small facets.yaml v2 + blueprints for one or two fixture subjects (this resolves the KM2↔M6 circularity; canonical regeneration comes after M6).
8. **Sim harness re-key** — `sim/profiles.py` truth state and `runner._belief_mae` move to canonical facets; then run the KM §16 sim gates (shared-facet MAE and attempts-to-certify improve; no capability inflation, clone inflation, or blanket failure damage).
9. `algorithm_version: mvp-0.7` activation as an atomic vault upgrade; mixed-version vaults forbidden.

Pitfalls: replay must reproduce identically under BOTH versions — golden-replay tests on a legacy fixture and an mvp-0.7 fixture are the safety net. Never copy beta mass during merges; the merge map is resolved at read/replay time like aliases.

### ING M6 — Create study map (needs KM2 live)

**Goal:** the bootstrap journey end to end: brief → sharded synthesis → dependency-closed proposal → applied study map with facets/blueprints/criteria.

Work items: synthesis brief (+ optional Goal creation in the same flow); **Quick add** (one happy-path confirmation, small ToC-guided scope, queue priority, ready-subset build); `run_source_set_synthesis` codex method + span-request protocol (ING §8.5 — one bounded request round, untrusted-text delimiting); dependency-aware proposal application (closure accept/block under the vault lock); synthesis-time identifiability gate (discriminator-first, coarsen only when no distinguishing assessment exists); **synthesis quality eval harness** (hand-authored gold registry; facet precision/recall, over-fragmentation, duplicate rate, missing conditions, recipe validity, provenance accuracy, repair-distinctness — per prompt version); minimal **Open-in-source** viewer (PDF page + bbox, HTML anchor); bootstrap evidence refusal (no attempts against a partially-upgraded map); recreate fixture vaults canonically and diff against the hand-authored KM2 registries.

### KM3 — Projections and UX

**Goal:** Ready/Demonstrated/Next-gap becomes real, computed from blueprints over shared state.

Work items: blueprint likelihood projections (noisy-AND + guess floor + max-over-recipes; KM §9.2) in `selection_rewards.py`/`goal_projection.py`; capability/surface/integration certification for goals (KM §9.5 — goal DTOs already carry the dual-axis split, extend rather than replace); LO EKF (`services/mastery.py`) demoted to prediction-only calibration residual; **graph-prior correction** in `calibration_sessions.py` — zero non-prerequisite edges, respect direction, and **disable the live disagreement weighting** in `start_calibration_session` (lines ~229–231) so the signal is truly shadow; retire `cross_lo_propagation` config with migration warnings; anti-double-count test suite (KM §9.4, all six invariants); **Tauri re-key**: `FacetMasterySnapshot` DTO tree + radar/strata/terrain/well consumers move to canonical keys; ship the §9.6 deliverables — attempt trace view, unresolved-cause card, capability grid (diagnostic drill-down, one tap from Demonstrated), recipe tree, dual-encoded knowledge map, session narrative, evidence drawer with the **Demonstrated timeline** (non-monotone ledger fold; corrections render as visible events). The **Ready timeline overlay** follows immediately after KM3, goal-scoped, `algorithm_version`-segmented.

Display rule to enforce in review: ambient surfaces lead with Ready; goal/certification surfaces lead with Demonstrated; never one blended number.

### ING M7 — Update study map (CORE RELEASE with M6)

**Goal:** safe increments: add a source, select more units, adopt a new revision.

Work items: `append_source` + `run_append_reconciliation` with deterministic bounded affected-neighborhood selection (ING §10.1 — the linear-scaling gate in §14 is the acceptance test); specialized additive handlers (`provenance_link`, `notation_mapping`, `source_conflict` — auto-apply rules per §10.3); revision refresh diff/reconciliation; conflict + task-alignment review UI (side-by-side spans via the M6 viewer); **maintenance feed** with per-type aging policies; post-append near-duplicate facet doctor pass; **lightweight exam-readiness-by-task-family report** (blueprint distribution × facet-capability state, calibration overlays where practice-exam data exists).

### KM4 — Taxonomy + misconception composition

Mechanism taxonomy remap (KM §10.1 legacy mapping; it's a **grader contract** — bump `GRADING_PROMPT_VERSION`, update the signature matcher's fatal-id invariant, run a `probe-regrade`-style non-destructive check pass); compositional misconception records (mechanism + operation + target/confused facets); promotion discipline; contrast-probe parameterization from `target_facet`/`confused_with_facet`.

### KM5 — Diagnostic/scheduler integration

Full identifiability doctor (`learnloop graph-identifiability`, the seven warnings of KM §11.3) wired as the pre-first-practice check; unresolved-cause-set probe targeting (KM §11.1 priority order — feeds the Feedback screen's diagnostic card); **intent-first session composition in shadow mode** (log intents + rankings alongside live behavior; promotion requires held-out gains — the sim-sweep finding says membership/gating decides outcomes, so treat this with the same shadow discipline as the probe policies); capability residual activation (shrinkage thresholds are open calibration questions — ship behind config, default off); residual-dependence diagnostics.

### ING M8 + post-core

Cross-source practice generation with leakage controls; fully calibrated exam-readiness report; tutor citations via `entity_source_links` (click-through to Open-in-source); YouTube embedded player (needs the `youtube-nocookie.com` iframe origin allowed in Tauri CSP/capabilities — app restart category); figure-to-vision escalation; dual-pane span navigation; `source_exposure` instrumentation; provenance-outcome analytics. Then write the **restructure-with-history specification** — deliberately the first post-core spec, because locks accumulate monotonically and KM2's observation lineage was designed to make it possible.

---

## Part 3 — Cross-cutting practices

**Testing.** Follow the house pattern: service-level pytest per module (`tests/test_<module>.py`), sidecar contract tests (`test_sidecar_*.py`), fixture golden tests, and sim-harness gates for anything touching belief math. The specs' §14 (ING) and §16 (KM) verification lists are written to be translated 1:1 into test names — do that literally and check them off. Replay-identity tests (run `rebuild_derived_state` twice, diff) guard every KM milestone.

**Migrations.** Number sequentially from 032 as work lands (the specs' "032" is illustrative, not reserved). CHECK changes = table rebuild. Every migration gets a test in `tests/test_migrations.py` style: fresh DB and existing fixture DB both migrate.

**Prompts.** Every LLM contract (inventory, synthesis, grading, probe surfaces) is versioned (`*_PROMPT_VERSION`); changing one invalidates the relevant cache identity and, for grading, triggers a regrade-check pass. Source/inventory/span text is untrusted: delimit it, ignore embedded instructions, never let the model name file paths or arbitrary ids.

**Known gotchas (from hard experience in this repo):**

- `versioned()` in the sidecar camelizes recursively — never re-attach a snake_case payload to an already-versioned response.
- Frozen dataclasses (e.g. `AttemptResult`) need `dataclasses.replace`, not mutation.
- The Codex SDK cannot spawn from sandboxed/background shells — generation silently falls back (exit 0). Run LLM-dependent evals in a foreground shell.
- `sync_vault_state` force-reactivates items and auto-enters probe episodes — in tests, set up cards/registries **before** syncing; and it must NOT reactivate review-parked items.
- Sim gate trial counts must be ≥8 (Beta lower-bound math makes a perfect 5-trial run fail a 0.8 gate).
- Scheduler ranking weights are decision-inert; membership/gating decides outcomes. Don't burn time tuning weights — validate composition changes in the sim harness.

**Definition of done, per milestone:** spec verification rows pass as named tests; full suite green; `tsc` + `cargo check` clean; fixture vaults load through `doctor`; replay identity holds; CLI + sidecar + Tauri all expose the feature; and for shipping milestones (M3.5, M6+M7), a real-source dogfood run (one textbook PDF, one YouTube lecture, one past exam) completes the journey end to end.
