# Ingestion and synthesis strategy (K2, 2026-11-11)

Refactor arc K, step K2, job 2. It stands on the map `docs/reviews/k2-ingestion-map-2026-11-11.md` as corrected after the Codex check (ids KP, KD, KB, KM, KO, KF, KC, KN, KH, KX, KV are the map's). **Base: main `565aee8724`**, with K0 (`refactor/k0-identity-pins`, landing soon) assumed landed. **Status: for the owner's review.** Docs only.

## Summary for the owner

Ingestion works, and several of its parts are good. Its cost is that a few ideas are each built several times: two synthesis orchestrators, four cache layers keyed four ways, five job stores with four heartbeat loops, a source kind spread over seven places in the backend and six in the desktop. On top of that, what synthesis reads is chosen silently. You asked for larger-view structures that make it readable and easy to extend. This plan gets there in 5 bug fixes and 12 small structural steps.

**Fix first, because they cost money or data today (K3, five steps, before arc D ends):**

| | fixes | why now |
|---|---|---|
| K3.1 | synthesis reads the right inventory row, and says which | a new prompt, model or re-read is paid for, then ignored (KX3) |
| K3.2 | keep-ahead sends only the new chapters | input grows with every chapter read, quadratic over a book (KX1) |
| K3.3 | the collection build inventories and sends every unit it's missing | one cached unit hides a revision's new units (KM3) |
| K3.4 | the append call gets a checkpoint, a generation limit and a refusal before an over-ceiling input | a retry re-pays, and an over-budget answer fails the same way forever (KX2, KM4) |
| K3.5 | apply recovery never overwrites newer YAML, and runs at startup | a crash can leave a half-applied vault the app keeps using (KD2) |

**Then the structure (K2.1-K2.12, after arc D):**
- **One synthesis run.** Bootstrap and append become one orchestrator with two modes (K2.4), so an append inherits bootstrap's shards, checkpoints and invariants instead of re-learning them. `_normalize` becomes named stages over one state (K2.5).
- **One cache rule.** Every paid structured call goes through one checkpoint helper keyed on what it sends (K2.1). The outer caches defer to it (K2.2). The manifest becomes the record of what a run read, not a reuse key (K2.3).
- **One place per kind of change.** A source kind becomes one table row (K2.8), extractor choice one function (K2.9), a job type one row (K2.7). The desktop asks the backend instead of copying its rules (K2.11).
- **Why x and not y.** Decision records at the three ingest choices that are silent today: build scope, inventory row and auto-apply (K2.12).

**What you must decide** (§5): whether an append's new concepts, facets and LOs auto-apply (KX4; I recommend new creates, with Undo as the net). Whether an arXiv id reads the full paper (KD3; I recommend yes). When the legacy canonical lane retires (I recommend at the UX overhaul).

**What a change costs, today → after** (§6). Counted from real commits; the "after" column is an estimate.

| change | today (backend src / desktop) | after |
|---|---|---|
| a source type | 5 modules, 7 places / 6 tables | 1 table row + its IR builder, 1 test |
| an extractor | 17 src files (GLM-OCR, distinct) / 8 | the extractor, 1 selection line, 1 test |
| a synthesis pass | both orchestrators + 7 | 1 stage in 1 orchestrator, its contract, its route |
| a facet rule | 5-8 modules, both orchestrators when it touches synthesis | `authority.py` or `judge.py`, 1 test |

**Cost.** About 1.5-2 weeks of queue for K3 and K2 together, at the strategy's pace. That's an estimate.

## 1. Diagnosis, ranked by cost

| # | Problem | Evidence (map) | Steps |
|---|---|---|---|
| 1 | **Keep-ahead appends re-send the book; the append call is unbounded and uncheckpointed.** Money, and a whole-book build that can't finish. | KX1, KX2, KM4; `content/pipeline/add_source.py:1646-1667`, `content/pipeline/jobs.py:1989`, `content/synthesis/source_append.py:84`, `:249-250` | K3.2, K3.4, K2.4 |
| 2 | **Apply recovery can overwrite newer YAML and runs only under `doctor --fix-state`.** Data. | KD2; `content/proposals/apply_protocol.py:237-243`, `:342`, `:576` | K3.5 |
| 3 | **Synthesis inputs are chosen with weak identity:** the oldest inventory row, label-keyed outer caches, a manifest missing role overrides and edges, a collection append that skips units. Paid work ignored, wrong reuse, no trace. | KX3, KM1, KM2, KM3, KB1, KO1 | K3.1, K3.3, K2.2, K2.3, K2.12 |
| 4 | **Two orchestrators and a 1,081-line normalizer.** Every synthesis-wide change edits both orchestrators, and the append copy keeps diverging (items-off twice, instrument gates, the brief, KM6). | KP1, KP5, KH1, KM6 | K2.4, K2.5 |
| 5 | **Four cache layers keyed four ways; four paid call families uncheckpointed.** The manifest is provenance, cache key and reuse key at once. | KB3, KX5, KH4 | K2.1, K2.2, K2.3 |
| 6 | **The pieces a change touches are scattered:** 21 job types in one 5,852-line module, plus four parallel lists. A source kind lives in 7 backend places and 6 desktop tables. Extractor choice is split between `jobs.py` and the extractor package. | KP2, KB6, KH2, KN1 | K2.7, K2.8, K2.9 |
| 7 | **Five job stores and four heartbeat loops.** Two heartbeats are near-copies. Two users commit after a lapse. One store mixes clocks. | KB2 | K2.6 |
| 8 | **The desktop copies backend rules, and four disagree.** | KB4 | K2.11 |
| 9 | **The silent decisions:** auto-apply's reasons, persona fallback, D2 MINT, build scope's withholding. | KO1, KO2, KO4, KD5 | K2.12 |
| 10 | **Small but real:** non-atomic conflict resolution, three token estimators, dead fetch and detect modules, stale comments. | KM5, KB5, KN1, KN2, KC1 | K2.10, folded in |

## 2. Answers to §2.17's strategy questions

**One checkpoint helper for every structured call, versus today's mix?** Yes, for model-work checkpoints. `ai/execution.py` already has `content_key` and `model_settings`. What each site re-implements is the load-validate-discard-save cycle (`content/synthesis/source_unit_inventory.py:692-710`, `content/synthesis/source_set_synthesis.py:2953-2963`, `content/pipeline/source_ingestion.py:1072-1082`, `content/facet_identity/judge.py:760-835`, `content/pipeline/jobs.py:352-375`), and the key policy. The helper keys on purpose, rendered prompt, schema and model settings by default. A caller adds the output budget only where a truncated answer could validate. That is the judge's case, and it becomes the stated exception instead of a contradiction. GLM-OCR's key (file, pages, backend, models) stays its own: there is no prompt. It does use the helper's cycle. Six recipes become one helper and two key shapes (K2.1).

**The manifest as provenance only, with reuse revalidated?** Yes, once every paid call has a checkpoint (K2.1). Then "reuse" needs no run-level key. Re-running the orchestration hits every checkpoint, and gates, facet plan and apply run under today's code (K2.3). This removes the over-invalidation (task graph, algorithm version, budgets, config dumps) and the under-invalidation (inventory content, role overrides, edges, `revision_diff`, the brief, KX5, KM2, KM6) from the reuse path in one move. The manifest keeps recording, now with exact inputs: inventory row ids, role overrides, an edge hash, the resolved brief. A one-time re-pay of the calls that had no checkpoint (structuring, epigraphs) happens per subject at the first build after K2.3.

**Hashing only what each step reads?** Yes, through K0's identity views (`config/retired.py` `identity_view`, the judge's `manifest_identity`, `graph_nomination`'s `IDENTITY_CONFIG_FIELDS`) and the rendered prompt. A rendered prompt is exactly what the step reads. Once K2.3 lands, the manifest's snapshot hashes stop being keys, so whether they're too wide stops mattering for cost.

**Does `_normalize` split into named stages?** Yes. Its twelve stages are already marked by good comments (map §1.1). It becomes one module of stage functions in order over one explicit state object, with the same output (K2.5). It is not a class hierarchy or a per-item-kind plugin.

**One job and lease mechanism instead of four reimplementations?** Two, not one. The ingest drain (A) fails an expired job and waits for a person. The shared judge claims (B) let the next process take over. Both semantics are right for their work. The cost is the four heartbeat loops and the lapse and clock bugs, not the two semantics. B1 and B2 share one heartbeat; the lapse check and the spend clock are fixed (K2.6). Follow-up and phone jobs are outside K2 (K7).

**Can each boundary change alone?**

| boundary | today (map §3.1) | after |
|---|---|---|
| extraction → inventory | no: unit ids are per extraction, rows rebind silently | yes for prompts and models (K2.2 keys rows on the rendered prompt); unit renumbering on re-read stays a re-inventory, recorded |
| inventory → synthesis | no: oldest row, labels only | yes: one selection rule, row ids recorded (K3.1, K2.12) |
| synthesis → facet identity | partly: verdicts applied inside `_normalize` stages 4-6 | yes: one named stage consumes the plan (K2.5) |
| synthesis → apply | mostly | yes, and apply survives crashes (K3.5) |
| pipeline → retrieval | no: eight imports in `jobs.py` | yes: retrieval's job types are rows in their own module (K2.7) |
| desktop → sidecar | no: eight copied rules | yes: the sidecar returns eligibility, roles and bounds (K2.11) |

**How is a new source type, extractor, pass or facet rule added?** Counted in §6, before and after.

## 3. The steps

**Every step** follows §2.1 of `docs/specs/refactor_strategy_v3.md`:
- an Opus implementer in a worktree;
- targeted tests under the memory cap, `lint-imports`, `ruff check`, the vault validators, and `tests/test_identity_pins.py` (K0);
- the full suite per landing batch, and one Codex review per arc.

**Named proofs:**
- **P-fail:** a test that fails before the change.
- **P-pins:** K0's identity pins unchanged. Where a step moves an identity deliberately, the pins are regenerated in that commit with the reason.
- **P-golden:** proposal rows for a fixed fake model output, compared whole before and after.
- **P-spend:** the step records on a backup-API copy the model calls it saves or adds.

No step changes learner scoring, so none needs a successor tag. Each is a content or infrastructure change.

### 3.1 K3: the fixes that cost money or data today

These may land before arc D ends, each alone, each from a failing test. Order: K3.1 → (K3.2, K3.3) → K3.4; K3.5 is independent.

**K3.1. Synthesis reads the right inventory row** (S). KX3, KB7.
- **Problem:** `_best_inventory` takes the oldest row in the preferred profile by revision and unit id (`content/synthesis/source_set_synthesis.py:225-235`, copied at `content/synthesis/source_coverage.py:42-55`). A row for new text, a new prompt label or a new model is paid for and ignored. The entry is filed under the current extraction id (`content/synthesis/source_set_synthesis.py:397`).
- **Does:** one `best_inventory(rows, unit, *, semantic_hash, prompt_version, provider, model, profile)` in `content/synthesis/source_unit_inventory.py`. It prefers the current semantic hash, then the current prompt, provider and model, then newest; the profile rule stays. Both call sites use it. The entry carries the row's own extraction id and row id.
- **Files:** `source_unit_inventory.py`, `source_set_synthesis.py` (`_collect_inputs`), `source_coverage.py`, their tests.
- **Deletes:** the second `_best_inventory`.
- **Proof:**
  - P-fail: re-inventory a unit under a new prompt label, synthesize with a fake client, and assert the newer row reaches the prompt.
  - P-pins: no K0 pin has inventories, so expect no change.
  - P-spend: on a copy, count the units whose chosen row changes (expected near zero; the copies hold one same-hash pair).
- **Note:** for a vault with a stale row, the manifest's label moves, so that subject's next bootstrap is a new run. Pass checkpoints still hit for unchanged shards. **Vault:** none.

**K3.2. Keep-ahead appends only the new units** (S). KX1.
- **Problem:** the planner's build carries no unit or revision filter, so each append sends the chosen inventory of every unit built so far.
- **Does:** the planner already puts the chosen `unit_ids` into the build's `auto_build` payload (`content/pipeline/add_source.py:1628-1640`). `handle_append_synthesis` passes them as `new_unit_ids` (`content/pipeline/jobs.py:1989`). `_append` filters `new_inventories` by unit as well as revision (`content/synthesis/source_append.py:249-250`). The append scope records `new_unit_ids` only when given, so the RPC paths keep their bytes.
- **Files:** `jobs.py`, `source_append.py`, `tests/test_ux_phase1_auto_build.py` or a new test beside it.
- **Proof:**
  - P-fail: a two-build book with a recording fake client; the second append's prompt holds only the second build's inventories.
  - P-pins: the append scope is unchanged when no unit filter is given.
  - P-spend: on a copy with a two-build source, the second append's inventory tokens fall from about 3.7× to 1× its new units (map §7). The textbook projection is about 18× fewer input tokens over a book.

**K3.3. The collection build sends every missing unit** (S). KM3.
- **Problem:** `build_study_map` calls a member new only when its revision has no inventory at all (`learnloop_sidecar/handlers/ingest.py:1131-1138`). A partly inventoried revision gets no inventory jobs for its new units, and may be filtered out of the append.
- **Does:** newness is per unit. A unit without a current row is inventoried, and its revision and unit join the append filter (the K3.2 parameter).
- **Files:** `learnloop_sidecar/handlers/ingest.py`, `tests/test_sidecar_append.py`.
- **Proof:** P-fail: a member with one cached unit and two new ones; both new units are inventoried and reach the append. **Risk note:** today such a build quietly omits units. No spend is saved; coverage is gained.

**K3.4. The append call is bounded and checkpointed** (M). KX2, KM4, KB5.
- **Problem:** no per-call checkpoint, no request-level generation limit and no input ceiling. The output check runs after generation with an escaping estimator (`content/synthesis/source_append.py:84-93`, `:557-575`). A budget failure leaves the run rows `running` (`:476-477`).
- **Does:**
  - The append call and its span round get a model-work checkpoint: purpose, rendered prompt, schema, settings, no budget. This is the same key shape as `_synthesis_pass_key` (`content/synthesis/source_set_synthesis.py:2966`), reused, not copied.
  - They run under `generation_limit(append_output_tokens)`.
  - A preflight refuses, before paying, an input over a new `append_input_ceiling` default, with a typed, non-retryable error that the book card shows. With K3.2 that is rare; splitting an oversized append arrives with K2.4.
  - The `StudyMapError` arm finalizes the run rows.
  - `_output_tokens` uses bootstrap's non-escaping `_result_tokens`.
- **Files:** `source_append.py`, `config/schema.py` (one default), `config/template.py`, `tests/test_source_append.py`, generated config notes.
- **Proof:**
  - P-fail, three tests: a retry after a gate failure makes zero model calls; an over-budget answer is checkpointed and the retry doesn't re-pay; a budget failure leaves both run rows `failed`.
  - P-pins: a new default joins K0's goldens.
  - P-spend: each retry of a failed append costs zero calls instead of one or two.

**K3.5. Apply recovery is safe and automatic** (M). KD2.
- **Problem:**
  - Recovery writes an intent's post-image over whatever a file holds, never reading `pre_hash` (`content/proposals/apply_protocol.py:237-243`, `:342`).
  - Only `doctor --fix-state` runs it (`ops/doctor.py:1309-1345`), though the docstring says startup. The next accept ignores pending intents.
  - Recovery skips recalibration (W6). The maintenance action has no handler.
- **Does:**
  - `materialize_targets` writes a file only when it equals `pre_hash` or already equals `post_hash`. Otherwise the intent is marked `conflicted`, keeping the newer file, and surfaced.
  - The sidecar runs `recover_apply_intents` at bind, beside facet-action recovery (`learnloop_sidecar/context.py:208-211`). `apply_accepted_items` refuses while an intent is pending.
  - Recovery runs recalibration.
  - The maintenance action gets its handler, or is removed.
- **Files:** `apply_protocol.py`, `patches.py`, `learnloop_sidecar/context.py`, `ops/maintenance_feed.py` (and its handler), new apply-recovery tests. **`conflicted` needs a migration:** `apply_intents.status` is CHECKed to `pending`, `applied`, `rolled_back` (`migrations/044_provenance_manifests_apply_intents.sql:158-159`), so the step adds a table rebuild with the CLAUDE.md migration rules (table role, head fixture, references). If the owner wants no migration in K3, the fallback is to leave the intent `pending`, refuse accepts while it is, and surface it; the next migration-carrying step adds the status.
- **Proof:**
  - P-fail: an intent whose target file changed after the intent is not overwritten.
  - P-fail: a crash between two renames is completed at the next sidecar bind.
  - P-fail: an accept with a pending intent is refused.
  - The durability lane, since this is fsync and rename territory.
- **Risk note:** data, not money. **Vault:** Doctor Migrations and Recovery (`:108`), Content Pipeline.

### 3.2 K2: the structure (after arc D)

Order: K2.1 → K2.2 → K2.3 → K2.4 (a, b, c) → K2.5; K2.6-K2.11 are independent of that chain and of each other; K2.12 after K2.4. Each lands alone or in batches of up to four.

**K2.1. One checkpoint helper** (M). KB3.
- **Problem:** six model-work recipes, each with its own load-validate-discard-save cycle and key policy. Four paid call families have no checkpoint: structuring, persona fire, epigraphs, and append until K3.4.
- **Does:** `ai/execution.py` gets `checkpointed(repository, *, purpose, prompt, schema, settings, result_model, identity_extra=None, validate=None)`. Key: purpose, rendered prompt, schema and settings, plus `identity_extra` where a caller needs it (the judge's budget). It uses `content_key`, `model_settings` and the existing table. The inventory window, synthesis pass, legacy window, both judges and K3.4's append move onto it with **byte-identical keys**. Structuring, persona fire (`diagnosis/diagnostic_gate.py`) and epigraphs are added. GLM-OCR keeps its key and uses the cycle.
- **Deletes:** five private cycles (`_reusable_window_checkpoint`, `_checkpointed_pass`, `_checkpointed_window_proposal`, the judge's two, `_ModelCheckpoints`' body), the judge's "everywhere" comment.
- **Abstraction and why it pays:** one function replaces six copies, and makes "a new paid call" a one-line wrap.
- **Proof:** P-pins (K0 pins A13-A15, A20 and the judge keys) unchanged; P-fail: a retry after a structuring pass reuses it; `tests/test_model_work_checkpoints.py` passes. **Vault:** `Workflows/Import Canonical Sources.md:189`.

**K2.2. Outer caches defer to the rendered key** (M). KM1.
- **Problem:** inventory-artifact reuse (label, provider, model) and completed shards (label-keyed) answer before the rendered-prompt checkpoints. A prompt edit without a label bump, or a changed endpoint, silently reuses old output.
- **Does:**
  - An inventory row stores its first window's rendered key in `usage_json`. Reuse requires it to match. Rows without one keep today's label match, so nothing is orphaned.
  - The completed-shard key becomes the pass key of the shard's first pass. Old shard rows stop matching, at zero model calls, because the passes' rendered checkpoints still hit.
- **Files:** `source_unit_inventory.py`, `db/repositories.py` (reuse query), `source_set_synthesis.py`.
- **Proof:**
  - P-fail: edit an inventory prompt's text without bumping its label; the unit is re-inventoried.
  - P-fail: a shard reruns from its pass checkpoint with zero calls.
  - P-pins: the shard key pin is bumped deliberately.

**K2.3. The manifest records; checkpoints reuse** (M). KX5, KM2, KM6, KH4.
- **Problem:** the manifest hash is provenance, cache key and reuse key at once. It moves on any config or task-graph change and misses inputs that change outputs. An append reuse returns an unapplied proposal (`content/synthesis/source_append.py:322-327`).
- **Does:**
  - Remove the completed-run lookup from bootstrap and append (`_reusable_bootstrap_run`; `completed_agent_run_by_context` at `content/synthesis/source_append.py:322`). A repeat runs the orchestration, and every paid call hits its K2.1 checkpoint.
  - The manifest gains the exact inputs (inventory row ids and content hashes, per-unit role overrides, an edge hash, the resolved brief, `revision_diff`'s hash) and fills or drops `asset_hashes`, `extractor_versions` and `lock_fingerprint`.
  - Append resolves its brief and practice mode before the manifest, as bootstrap does (KM6), through one shared function.
- **Deletes:** the run-level reuse branches, three null fields if dropped, `agent_run_input_context_hash`'s role as a key (it stays a record).
- **Proof:**
  - P-fail: a role-override-only change produces a new proposal.
  - P-fail: an identical rerun makes zero calls to the checkpointed families and applies.
  - P-pins: the manifest pins (K0 A1-A4) are bumped deliberately, with the reason "provenance only".
  - P-spend: one structuring and one epigraph call per subject at its first build after landing, from pre-K2.1 runs.
- **Vault:** a "Synthesis identity and caches" concept note.

**K2.4. One synthesis run, two modes** (L, as three M steps). KP5, KH1, KX2's split.
- **Problem:** `_create_study_map` (251 lines) and `_append` (312) are one shape written twice. 12 of the 15 append commits since Oct 1 also changed bootstrap, and the append copy diverged repeatedly.
- **K2.4a, shared tail:** facet identity, normalize, the gates, instrument gates, persist, apply, the facet doctor and epigraphs become one function, used by both. The append's extra item kinds (provenance links, notation mappings) enter as its normalizer's additions, not as a second persist path.
- **K2.4b, shared head:** inputs, brief resolution (K2.3's), scope and manifest become one function with a mode.
- **K2.4c, append through the shard runner:** the append's new inventories go through `_run_synthesis`'s shard and pass machinery with the append prompt. An oversized append splits by new units into checkpointed passes, which replaces K3.4's refusal. The neighbourhood stays the append's context.
- **Files:** `source_set_synthesis.py`, `source_append.py` (shrinks to the append prompt, neighbourhood and normalizer additions), `content/pipeline/jobs.py` (the two handlers), their tests.
- **Deletes:** `_append`'s orchestration, its private gates and persist block.
- **Abstraction and why it pays:** none new; a `mode` argument. Every later synthesis change edits one orchestrator.
- **Proof:** P-golden for bootstrap and append on fixed fake outputs (rows, gate diagnostics, auto-apply ids), before and after each sub-step; P-pins; the existing append, bootstrap and auto-build tests. **Vault:** Build a Study Map (`:55`, `:60`).

**K2.5. `_normalize` in named stages** (M). KP1.
- **Problem:** twelve stages in one 1,081-line frame with about fifteen shared dicts and eleven closures (`content/synthesis/source_set_synthesis.py:659-1739`).
- **Does:** `content/synthesis/normalize.py` holds a `_NormalizeState` dataclass (the id maps, the rows, the diagnostics) and one function per stage, in the order the map lists. `normalize()` calls them in that order. The closures become functions over the state. The approach paragraph the map asked for opens the module.
- **Deletes:** the frame; the `unique()` closure becomes a state method.
- **Proof:** P-golden on the bootstrap and append fixtures; the facet identity and mint-gate tests; no function over 200 lines in the module. **Size:** M, because it's a move with one review.

**K2.6. One heartbeat and a lapse check for judge claims** (S). KB2.
- **Problem:** B1 and B2 run near-copied heartbeats (`content/authoring/source_exercise_import.py:781-806`, `source_retrieval/reading_paths.py:819-841`) and commit through `holds_claim` without `now` (`:820`, `:838`, `:919`). Service spend renews with wall time and reserves with the injected clock (`source_retrieval/service_spend.py:125`, `:194`).
- **Does:** `db/stores/judgment_claims.py` gets `claim_heartbeat(repository, claim, *, lease_seconds, interval)`, which both use. Both pass `now` at commit. Service spend renews with its injected clock.
- **Deletes:** two heartbeat bodies.
- **Proof:** P-fail: a lapsed but unclaimed lease no longer commits; P-fail: a spend lease under a fake clock renews in the clock's frame.
- **Note:** A (ingest) and B (claims) stay two mechanisms on purpose (§2).

**K2.7. A job type is one row** (M, as moves). KP2, KB6, KP6.
- **Problem:** 21 job types in `jobs.py` (5,852 lines) beside the host. What a type is lives in five lists: `DEFAULT_HANDLERS`, `APPLYING_JOB_TYPES`, `_QUEUE_AFFECTING_JOB_TYPES`, `_PARALLEL_JOB_TYPES` and the stale `KNOWN_JOB_TYPES`. `RunnerServices` holds 11 client factories.
- **Does:**
  - Handlers move beside their feature: import and extraction to `content/pipeline/import_jobs.py`; inventory and synthesis to `content/synthesis/jobs.py`; Reader and authoring handlers to `content/authoring/jobs.py`; retrieval's four to `source_retrieval/jobs.py`.
  - One `JOB_TYPES` table in `content/pipeline/job_types.py` gives each type its handler, `applies_vault`, `affects_queue`, `parallel` and client route.
  - `jobs.py` keeps the host.
- **Deletes:** `KNOWN_JOB_TYPES`, `KNOWN_WORKFLOW_TYPES`, the four lists. Client factories where a route name serves.
- **Abstraction and why it pays:** a plain table of rows replaces five lists and a per-type edit to three modules. It is not a registry: no discovery, no decorators.
- **Proof:** moves only, so the targeted suites of every moved handler pass; P-fail: a test that every handled type has exactly one row. **Vault:** Content Pipeline.

**K2.8. A source kind is one row** (M). KH2, KB4 (source kind), KN1, KN2.
- **Problem:** a kind lives in `ingest/resolution.py`, `default_fetch`, `_is_document`, `default_extract`, `default_extraction_identity` (`content/pipeline/jobs.py:96-660`), `_KIND_NOUN` (`content/pipeline/add_source.py:101-111`) and the legacy mapping. The desktop has six tables, two missing `image`. A test-only fetch module shares the live fetch's name.
- **Does:**
  - `ingest/source_kinds.py` holds `SOURCE_KINDS`: each category's fetch mode, document flag, IR builder, extraction identity, learner noun and file extensions. The four `jobs.py` functions and `_KIND_NOUN` read it.
  - `classify_ingest_source` returns the kind's display row, so the desktop's `detectKind` and `KIND_META` go, keeping only an offline guess.
  - The YouTube helpers move out of `ingest/fetchers.py`.
- **Deletes:** `ingest/fetchers.py`'s fetch path (about 300 lines), `ingest/detect.py`, `source_ingestion.detect_source_kind`, the desktop kind tables in `IngestScreen.tsx`, `dto.ts:3313`'s literal union (generated from the table), `useSourceFileDrop.ts` and `useGlobalAdd.ts`'s extension lists.
- **Proof:** P-fail: every category in `SourceCategory` has a row and an extension list the desktop accepts; the import tests per kind; vitest for the Add box.
- **Target:** a new kind is one row, its IR builder and one test.

**K2.9. Extractor choice in one place** (S). KH (extractor).
- **Problem:** the selection ladder is in `ingest/extractors/__init__.py:84-155`. The consent, upload-OK and image rules that decide whether a selected extractor may run are in `content/pipeline/jobs.py:260-312`.
- **Does:** `pdf_extractor_for` returns the extractor and the consent it needs. `jobs.py` asks and raises the card.
- **Proof:** the GLM-OCR consent tests; P-fail: an image without the upload OK raises the card from the one function.
- **Target:** a new extractor is its module, one ladder line and one test.

**K2.10. Small correctness and hygiene, folded** (S).
- Conflict resolution writes the mapping, the status and the audit row in one transaction, with `WHERE status='open'` (KM5; `content/proposals/conflict_resolution.py:49-80`).
- One JSON token estimator, non-escaping, used by `_shards`, the neighbourhood and append (KB5).
- The five contradicting comments are fixed (KC1).
- Proof: P-fail for the conflict crash window.

**K2.11. The desktop asks instead of copying** (M). KB4.
- **Problem:** at least eight backend rules are copied in the desktop, and four disagree: assessment roles, retry eligibility, the image kind, native page ranges.
- **Does:**
  - `get_ingest_batch` and `list_ingest_batches` return `can_retry_synthesis`, `can_repair` and their reasons from the host's own checks (`content/pipeline/jobs.py:5346-5383`).
  - A `get_source_roles` result carries the role list and authority matrix from `content/sources/role_authority.py`.
  - `BUDGET_BOUNDS` is read everywhere it's used. Page ranges are validated by the sidecar.
  - The `import_source` test is fixed.
  - The copies are deleted. Wording stays for the UX overhaul.
- **Files:** `learnloop_sidecar/handlers/ingest.py`, `IngestActivity.tsx`, `OutlineAndPlan.tsx`, `AddToCollection.tsx`, `IngestScreen.tsx`, `PageRangeSelector.tsx`, `dto.ts`.
- **Proof:** vitest per component; the RPC contract test; P-fail: a cancelled synthesis offers retry.

**K2.12. Why x and not y at the three silent ingest choices** (M). KO1, KO2, KO4, KD5.
- **Problem:** the inventory row, the build scope's withholding, and the auto-apply reasons are not stored. Persona fallback and D2 MINT are silent. Only one ADR-017 record exists in the area.
- **Does:** `provenance.DecisionRecord` through the existing `write_decision`, at five boundaries:
  - `ingest_build_scope`: chosen, withheld with the exam rule, skipped as built;
  - `ingest_inventory_choice`: the row per unit and the rule, one record per run with a detail row list;
  - `ingest_auto_apply`: per item, the `_auto_applies` condition that failed, or the gate's switch or Undo reason;
  - `persona_fallback`: when semantic grading failed;
  - the D2 summary: counts of MINT, ALIAS and ABSTAIN with the gate's reasons.
  The planner job id is the trace id through to the apply intent (§3.3 of the refactor strategy).
- **Proof:** P-fail per record; `learnloop why` answers "why does this concept need a look?" on a fixture. **Vault:** a note on the automatic build.

### 3.3 Placement

**K3.1-K3.5:** beside arc D, each landing alone when its test passes (the K3 rule). **K2.1-K2.12:** after arc D, per §2.17. K2.1-K2.5 are one chain. K2.6, K2.9 and K2.10 can fill gaps. K2.7 and K2.8 touch `jobs.py` heavily, so they don't run beside K2.4. K2.11 goes before the UX overhaul so the overhaul inherits one contract. Arc K's Codex review covers K3 as one batch and K2 as one.

## 4. What not to do

| Tempting | Why not |
|---|---|
| **One job framework for ingest, follow-ups, post-attempt and phone jobs** | Different processes, different expiry semantics (fail and wait versus take over versus requeue on boot), different owners. K2.6 removes the copies; the semantics stay. K7 looks at cross-process workers. |
| **A workflow engine or durable-execution library** | A new dependency and concept for a single-user app whose queue already fences writes. |
| **A plugin or registry per source kind, extractor or job type** | Plain tables (`SOURCE_KINDS`, `JOB_TYPES`) and a `match` do it; no discovery, no decorators. |
| **A class hierarchy for `_normalize`'s item kinds** | The stages share id maps; a hierarchy would hide them. One state, functions in order. |
| **Drop the manifest** | It's the record of why the curriculum changed, and the owner reads it. K2.3 makes it exact and takes away its key role. |
| **Hash whole config sections into any new identity** | K0's rule: an identity view or the rendered prompt. |
| **Re-extract or re-inventory existing sources to "fix" them** | Paid work, and nothing is wrong with most rows. K3.1 and K2.2 change what's chosen next time. |
| **Auto-apply append restructures, merges or notation** | The owner's call (KX4), and restructures can move evidence. |
| **Re-import existing arXiv sources automatically** | A new revision changes span ids; only a re-read the learner asks for. |
| **Delete the legacy canonical lane now** | The Ingest screen's legacy and exam modes use it; the owner's call (§5). |
| **Split `add_source.py` by section now** | It reads by section, and K2.7-K2.9 take out what other modules reach into. Revisit at Z2. |
| **Move retrieval's derived indexes out of the job host entirely** | They need its lease and lock; K2.7 only moves their handlers and rows. |
| **Polish the ingest screens' wording** | The UX overhaul. K2.11 changes contracts, not copy. |

## 5. Owner's decisions

1. **Auto-apply for an append's new coverage (KX4).**
   - **Today:** only provenance links apply, so every append leaves "N changes need a look". This contradicts UX §6.5 and the automatic build's promise.
   - **Recommended:** auto-apply new creates (concepts, facets, LOs and their items) that pass the gates and whose dependencies are in the same proposal. Restructures, merges into registered facets, notation mappings and conflicts stay in review, and the book's one-tap Undo stays the net. Each auto-apply decision is recorded (K2.12).
   - **If yes:** a small step after K3.2 (`content/synthesis/source_append.py` `_normalize_append`, the test's `_assert_build_applied` tightened).
2. **arXiv full text (KD3).**
   - **Today:** a bare id or an `/abs/` link reads the abstract page.
   - **Recommended:** resolve it to the HTML full text (`/html/<id>`), then the PDF, then the abstract, recorded in the extraction identity. This applies to new adds and learner-requested re-reads only. The full text is far more tokens per paper, and so more inventory spend; that is the point, but it is spend.
   - **If yes:** a row change in K2.8's table, or a small step before it.
3. **When the legacy canonical lane retires.**
   - **Today:** `legacy_ingest` and `exam_ingest` still serve the Ingest screen's legacy and exam modes and `learnloop ingest`.
   - **Recommended:** retire it at the UX overhaul, once exam seeding has an in-app path on the new lane, not inside K2.

## 6. Measures

Measured at K2's close with the same scripts as the map (AST sweep, `git show --name-only` on a scratch branch for sample changes).

**Size and shape**

| measure | today | target |
|---|---|---|
| functions over 200 lines in scope | 11; longest 1,081 | `_normalize`, `_append`, `_create_study_map`, `handle_inventory` out of the list; no new ones |
| synthesis orchestrators | 2 | 1 |
| cache layers keyed on labels | 3 (completed run, completed shard, inventory artifact) | 0: one rendered-key rule, the manifest a record |
| model-work checkpoint cycles | 6 private copies | 1 helper; 2 key shapes (prompt, file) |
| paid call families with no per-call checkpoint | 4 | 0 |
| heartbeat loops | 4 | 2 (ingest, judge claims) plus service spend's |
| lists that say what a job type is | 5 | 1 table |
| places that say what a source kind is | 7 backend, 6 desktop | 1 table; the desktop reads it |
| desktop copies of backend rules | 8, 4 disagreeing | 0 disagreeing; copies only for offline hints |
| ADR-017 records in the area | 1 | 6 |
| `jobs.py` lines | 5,852 | the host, under about 2,500 |
| function-local imports in the area | 394 of 917 | down; no fixed number |

**What a change costs** (backend src / desktop / tests, files edited)

| sample change | today (counted) | after (estimate) | where |
|---|---|---|---|
| a source type | audio: 11 / 0 / 8 distinct; image: in a 18 / 10 / 7 stage | 1-2 / 0 / 1 | `ingest/source_kinds.py`, the IR builder |
| an extractor | GLM-OCR: 17 / 8 / 5 distinct | 2-3 / 0-1 / 1 | its module, `ingest/extractors/__init__.py` |
| a synthesis pass | epigraphs 9 / 0 / 8; T5 18 / 0 / 6 | 3-4 / 0 / 1-2 | one stage in `source_set_synthesis.py`, its contract, its route |
| a facet rule | 8 / 0 / 7 (exam authority); 5 / 3 / 7 (span check) | 2-3 / 0 / 1-2 | `content/facet_identity/authority.py` or `judge.py` |
| a new synthesis input | 2 commits (T5, then the identity fix) | 1: it's in the rendered prompt or the manifest's record, never a key to remember | |
| a new job type | `jobs.py`, `runner.py`, up to 4 lists | its handler and 1 row | `content/pipeline/job_types.py` |

**Behaviour and spend**
- Keep-ahead append input over a two-build source: about 3.7× → 1× its new units (P-spend on a copy).
- A retry of a failed append, structuring, persona or epigraph call: 1-2 calls → 0.
- Apply crash between renames: the half-applied vault is completed at the next sidecar bind, and a changed file is never overwritten (P-fail).
- "Why does this concept need a look?", "which inventory did this run read?" and "why wasn't chapter 3 built?" are answered by `learnloop why` from stored rows.

## 7. The vault plan

Each step fixes the notes it touches; the full rewrite stays in the final docs stage (refactor strategy §5).

| note | action | step |
|---|---|---|
| `Workflows/Build a Study Map.md` | fix the Codex example (`:55`) and the bootstrap-or-append rule (`:60`) | K2.4 (or A4-style now) |
| `Concepts/Source Authority and Provenance.md` | drop `adjunct` (`:50`); qualify "reviewed application" (`:58`) | K2.11 |
| `Workflows/Import Canonical Sources.md` | add the cache layers to `:189`, then the single rule | K2.1, K2.2 |
| `Workflows/Doctor Migrations and Recovery.md` | recovery at bind, conflicts | K3.5 |
| `Architecture/Content Pipeline.md` | job types as rows, apply recovery | K2.7, K3.5 |
| new: "Add a Source and Automatic Builds" (workflow) | Add, the planner, consent and cost, inventory, bootstrap or append, keep-ahead, Undo | K3.2, K2.12 |
| new: "Synthesis Identity and Caches" (concept) | the record versus the checkpoints; what each hashes | K2.3 |
| new: "Facet Identity" (architecture) | groups, judges, merges, aliases, undo | K2.5 |

**Not verified** (inherited from the map): KX1's spend is projected; every K3 failure is code-traced and needs its fail-first test; K2.4's split of an oversized append and K2.2's "zero calls after the shard key moves" rest on reading the pass checkpoints, not running them.
