# LearnLoop architecture map (2026-11-08)

Phase A, job 1 of the refactor. It names problems and recommends nothing. **Base: `refactor/map` at main `a525dbcef4`** (router speed 2 landed), with Phone V4 and instruct/handoff read as diffs and marked `V4:` and `IH:`.

## Summary for the owner

LearnLoop is 1,268 Python files and 436,042 code lines (624,515 raw), up from about 291,000 code lines on Oct 15. Tests are 1,446 files. The schema has 396 tables and the chain has 45 tags. It works and its guards hold (43 import contracts kept, every vault validator passing). What's expensive is understanding and changing it.

**The five most costly findings:**

1. **"Why x and not y" stops at failures, exclusions and joins (§4).** No id links input to reasoning to behaviour. The records that exist can be excellent: `ad_selections` and the router objective's trace store alternatives and probabilities. But a chooser crash drops the models' answers with no log line (`src/learnloop/daily_plan/engine.py:2671`), a timeout leaves no payload, model calls precede their decision's id and join only through JSON, and most exclusions aren't recorded. None of your four real cases can be fully answered from stored rows. "Why pre-builds started after 12 skips" can only be reconstructed: there is no 12 in the code.
2. **Plumbing dwarfs the change (§9).** The 40 s timeout was 1 behaviour line, 46 digests and 12 test files. Router speed 2 touched 9 source files and 615 files in all, 593 of them generated notes. A new table renames a 48-file fixture and edits 68 pinned test files. A one-constant successor pins 36.
3. **The top layer isn't a layer yet (§3.3, §5).** Choosing, job control, seeds, trace assembly and the wall clock share `daily_plan/objective_chooser.py`, and the objective's form shares an 860-line class with the rollouts. Swapping the mixing rule touched 13 source files for 47 lines of rule, and adding an action touched 20. Six sites answer "should we probe?", and two belief updates over locked hypotheses can disagree with nothing reconciling them (§4.4).
4. **History costs more than it protects (§7.3, §11).** 40 root `*_upgrade.py` modules (replay imports none of them), 4,302 `mvp-0.N` literals, about 40 tag gates constant at any tag your vaults hold, and clones of the same upgrade helpers in about 20 modules. Tests that walk the chain from mvp-0.9 are the slowest family, 16% of test time, and grow with each tag. The whole suite took 59 minutes at `-n 8`.
5. **Persistence and imports defeat local reasoning (§1).** `Repository` has 943 methods and 406 importing modules. A 191-module import cycle spans 19 packages, and 2,944 of 9,257 import edges are hidden inside functions. Protection has one named authority and several other decision sites (B3).

**Also worth your attention:**
- **The old difficulty scalar reaches further than the brief's list, and part of that list is a different quantity (§7.2).** FSRS's D shares the name and the columns in migrations 001, 075 and 168, and it stays. The scalar also feeds AD's own `z_llm` signal, the content hash, exam strata and index filters.
- **Router speed target still unmet (D4).** Next right after feedback stays above 2 s on the large copies. The remainder is the numeric policy's per-draw arithmetic, then SQLite reads. R4 closes a pooled connection on each `PRAGMA table_info` (D5).
- **A privacy note in the vault is wrong (§8.1):** it says PDFs stay local, while `auto` uses a hosted service when a key is set. The vault's first hop describes August's system, and its validators pass anyway.
- **Two important tables are labelled COMPAT and are live (T1):** `practice_item_state` and `hypothesis_sets`.
- **For you to decide:** the TUI, collections and `projects/` (§7.4), AD eta's growth without an upper bound (§13), and the table list (§10), which proposes no drop.
- **A merge conflict waits at IH's landing (§12):** router speed 2 made `numeric_seed` required, and IH's new calls don't pass it.

**Deprecated inventory (§7.4):** 23 dead rows, plus 44 client methods with no caller and 64 unreferenced definitions; 7 superseded; 14 legacy-only; 3 owner-call. **Tables (§10):** 345 live, 26 derived and rebuildable, 24 retired but still read, 1 dead.

**Limits (§13):** all four real cases postdate the only permitted copy (Nov 3), so those answers come from code, not rows. Deep and shallow are size heuristics, reachability is by name, and several rows were read by outline only. No test or model was run.

## How to read this

**Severity** is what a finding costs understanding, debugging or changing the system. **High:** it regularly costs a stage real time, or hides a cause. **Medium:** it costs when you're in that area. **Low:** it's noise. Finding ids are stable: P (packages), D (data flow), B (boundaries), S and O (observability), F (functional core), C (comments), X and N (size), H (change cost), T (tables), Z (timing).

**Evidence** is `file:line`. A bare `:line` continues the file just before it. Every citation in the hand-written sections was machine-checked to exist, and its line text logged. A sample was read.

| § | Contents | Scope item |
|---|---|---|
| 1 | Packages, deep and shallow | Job 1.1 |
| 2 | Five journeys | Job 1.2 |
| 3 | Boundary crossings, sample changes | Job 1.3, Nov 5 item 6 |
| 4 | Decisions, inventory, Nov 3 items, real cases | Job 1.4, Nov 3 items 1-4, Nov 8 item 11 |
| 5 | Functional core | Job 1.5 |
| 6 | Comments | Job 1.6 |
| 7 | Size, difficulty scalar, deprecated inventory | Job 1.7, Nov 5 item 7, Nov 8 item 9 |
| 8 | Vault audit | Job 1.8 |
| 9 | Change cost | Nov 8 item 10 |
| 10 | Tables | Nov 8 item 12 |
| 11 | Timing | Nov 8 item 13 |
| 12, 13 | Landing dependencies, open findings, unverified | |
| A, B, C | Every module, every table, unreachable definitions | |

## 1. Packages and features

Sizes come from an AST and tokenizer sweep of the merged tip. "Code" means non-blank lines that aren't comments or docstrings. Appendix A classifies each of the 1,268 modules.

**Classes, by heuristic.** Each class is a rule over size and interface, not a reading of the module:
- **deep:** at least 250 code lines and at most 10 public names, or at least 400 code lines and at most one public name per 40 lines.
- **wide:** at least 30 public names, or at least 20 with under 20 lines per name.
- **shallow:** thin (at most 45 lines and 3 functions), re-export, or a helper with one importer and at most 80 lines.
- **init:** an `__init__.py` of at most 60 lines.
- **medium:** everything else.

**Totals.** 1,268 Python files, 624,515 raw lines, 436,042 code lines, 274,136 statements, 21,865 functions.
- Modules by class: 291 deep, 690 medium, 80 wide, 142 shallow, 65 init.
- Oct 15's audit counted 768 files and 375,115 raw lines in `src/learnloop` alone. That package now has 1,158 files.
- Frontends: `apps/learnloop-tauri/src` has 611 TS/TSX files and 181,532 lines; `apps/learnloop-mobile/src` has 67 and 8,504 (311 of the 678 together are test files, 60,488 lines).
- Tests: 1,446 Python files, 456,965 lines. Migrations: 237 files, 18,301 lines. Vault: 2,244 Markdown notes.

| package | owns | files | raw | code | stmts | funcs | deep | medium | wide | shallow | init |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| diagnosis | causal attribution, probes, episodes, VOI, blind split, text gaps, recurrence | 111 | 73,690 | 53,395 | 27,394 | 1,927 | 43 | 53 | 7 | 3 | 5 |
| content | source pipeline, synthesis, authoring, proposals | 85 | 59,577 | 42,349 | 26,326 | 1,981 | 24 | 42 | 9 | 4 | 6 |
| db | `Repository`, stores, connection, migration, table roles | 63 | 46,967 | 36,665 | 16,331 | 2,100 | 5 | 38 | 10 | 8 | 2 |
| learnloop_sidecar | desktop and phone RPC handlers | 93 | 39,270 | 26,222 | 18,076 | 1,428 | 9 | 54 | 9 | 20 | 1 |
| source_retrieval | search, Reader lookup, reading paths, coverage | 42 | 29,380 | 20,223 | 15,687 | 1,196 | 8 | 21 | 9 | 3 | 1 |
| cli | Typer commands | 57 | 19,596 | 15,605 | 9,071 | 551 | 10 | 31 | 1 | 15 | 0 |
| attempts | submit, grading, evidence application, regrade | 30 | 21,328 | 15,115 | 6,875 | 462 | 9 | 16 | 1 | 3 | 1 |
| daily_plan | plan engine, boundary, choosers, offers | 34 | 20,120 | 14,000 | 9,461 | 708 | 13 | 18 | 1 | 1 | 1 |
| figures | Show me, authoring, verification, pre-builds | 25 | 19,910 | 13,366 | 11,523 | 891 | 6 | 12 | 6 | 0 | 1 |
| adaptive_difficulty | latent eta, serving, reading, guard | 47 | 19,286 | 13,035 | 9,904 | 822 | 14 | 28 | 0 | 4 | 1 |
| scheduling | scheduler, FSRS, staged policy, controller | 47 | 17,795 | 11,875 | 7,004 | 575 | 7 | 32 | 1 | 5 | 2 |
| reader | Reader dialogue, reports, active reading | 28 | 16,098 | 11,227 | 6,435 | 513 | 11 | 15 | 1 | 0 | 1 |
| ops | doctor, vault upgrade, PF generation, contamination | 29 | 14,339 | 11,036 | 6,967 | 506 | 12 | 10 | 0 | 5 | 2 |
| ai | providers, routes, spend, transports | 44 | 16,171 | 10,751 | 7,467 | 691 | 8 | 22 | 4 | 7 | 3 |
| (root modules) | 40 `*_upgrade.py`, protection, eligibility, versions, switches | 74 | 18,749 | 10,289 | 8,014 | 638 | 2 | 50 | 2 | 19 | 1 |
| experiments | contextual embeddings harnesses | 36 | 14,245 | 9,876 | 8,063 | 653 | 1 | 27 | 4 | 1 | 3 |
| learner | mastery EKF, calibration, lesson weight | 27 | 12,437 | 8,607 | 4,813 | 392 | 7 | 17 | 0 | 2 | 1 |
| substrate | replay, rebuild, canonical projection, compat | 27 | 12,311 | 8,500 | 4,774 | 408 | 9 | 13 | 1 | 2 | 2 |
| evsi_calibration | EVSI reports | 17 | 10,548 | 7,773 | 5,687 | 463 | 9 | 6 | 0 | 1 | 1 |
| hints | adaptive hints | 19 | 10,476 | 7,037 | 5,249 | 420 | 5 | 12 | 1 | 0 | 1 |
| router_objective | objective value, mix, coin, checks, scores, learned tail | 31 | 10,073 | 6,730 | 5,511 | 417 | 2 | 26 | 0 | 2 | 1 |
| tutor | Ask and teach-back | 10 | 8,881 | 6,094 | 3,164 | 217 | 5 | 3 | 1 | 0 | 1 |
| curriculum | commitments, depth rungs, deliverables | 23 | 8,524 | 6,088 | 3,219 | 240 | 10 | 10 | 0 | 2 | 1 |
| instructional | valuation, tools | 18 | 8,067 | 5,641 | 4,359 | 299 | 2 | 10 | 2 | 3 | 1 |
| goals | contracts, exam pool, certification | 19 | 7,763 | 5,304 | 2,916 | 224 | 5 | 11 | 0 | 2 | 1 |
| field | success head, predictors | 18 | 7,082 | 5,144 | 3,611 | 286 | 8 | 6 | 0 | 3 | 1 |
| teacher | lessons, checks, briefs | 17 | 7,209 | 4,901 | 3,860 | 281 | 2 | 10 | 2 | 2 | 1 |
| ingest | detection, extractors | 22 | 6,544 | 4,504 | 3,399 | 250 | 4 | 15 | 0 | 2 | 1 |
| router | decision log, outcomes, mixture primitives, card | 12 | 6,362 | 4,470 | 2,799 | 215 | 6 | 2 | 2 | 1 | 1 |
| projects | project probes | 10 | 5,300 | 4,187 | 2,324 | 209 | 5 | 4 | 0 | 0 | 1 |
| sim | simulations | 13 | 5,432 | 4,093 | 2,626 | 208 | 4 | 6 | 1 | 1 | 1 |
| practice_index | item index | 14 | 5,154 | 3,940 | 2,697 | 185 | 3 | 8 | 0 | 2 | 1 |
| workbench | Work in Steps | 9 | 4,552 | 3,276 | 1,842 | 137 | 2 | 6 | 0 | 0 | 1 |
| config | schema, template, compat | 5 | 9,851 | 3,058 | 1,930 | 62 | 2 | 1 | 1 | 0 | 1 |
| params | parameter registry | 4 | 4,149 | 2,995 | 966 | 50 | 1 | 2 | 0 | 0 | 1 |
| vault | vault models, loader, writer | 14 | 4,782 | 2,968 | 2,265 | 199 | 3 | 6 | 1 | 3 | 1 |
| local_embeddings | local vector worker | 13 | 3,828 | 2,618 | 2,213 | 199 | 0 | 11 | 1 | 0 | 1 |
| placement | placement predictor and state | 9 | 3,644 | 2,472 | 1,504 | 137 | 2 | 4 | 0 | 2 | 1 |
| tui | Textual terminal app | 11 | 2,471 | 1,932 | 1,397 | 177 | 4 | 2 | 0 | 3 | 2 |
| followup_run | FG1 worker and gate | 10 | 2,652 | 1,883 | 1,369 | 102 | 4 | 5 | 0 | 0 | 1 |
| learnloop_mobile | phone host | 10 | 2,241 | 1,575 | 1,327 | 136 | 2 | 5 | 0 | 2 | 1 |
| remote | MCP views and sources | 7 | 1,553 | 1,037 | 746 | 54 | 2 | 3 | 0 | 1 | 1 |
| capture | phone capture jobs | 8 | 1,231 | 934 | 632 | 49 | 0 | 5 | 0 | 2 | 1 |
| intent | intent serving | 5 | 1,054 | 752 | 479 | 30 | 0 | 3 | 0 | 1 | 1 |
| followup_serve | workflow and queue | 6 | 1,129 | 689 | 560 | 64 | 0 | 3 | 1 | 1 | 1 |
| learnloop_mcp | MCP server | 6 | 926 | 675 | 524 | 34 | 0 | 1 | 1 | 3 | 1 |
| matching | matching | 5 | 1,001 | 649 | 436 | 32 | 0 | 4 | 0 | 0 | 1 |
| data_capture | capture reports | 4 | 767 | 487 | 340 | 47 | 1 | 1 | 0 | 1 | 1 |

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| P1 | high | One persistence class holds most of the schema's surface. `Repository` has 943 methods of its own plus 7 mixins, and 406 modules import its module, which has 23,691 code lines. It's classed "deep" only because the heuristic counts module-level names: its real interface is those methods. A reader can't tell from a call which feature owns a table. | `src/learnloop/db/repositories.py`; `src/learnloop/db/stores/` has 54 files beside it |
| P2 | high | The import graph has one strongly connected component of 191 modules across 19 packages (65 in diagnosis, 21 in scheduling, 17 in adaptive_difficulty), and 2,944 of 9,257 internal import edges sit inside functions, in 572 modules. Local reasoning stops at the edge of that component. | `pyproject.toml:1060` freezes the cycles under "Existing deferred cross-package cycles are frozen" with a long `ignore_imports` list |
| P3 | high | Five wide modules act as god modules: `cli/app.py` (4,601 code lines, 128 internal imports), `daily_plan/engine.py` (4,141 code, 5,978 raw), `content/pipeline/jobs.py` (4,116), `attempts/attempts.py` (4,063, 46 public names), `figures/service.py` (2,443, 76 public names). | Appendix A |
| P4 | high | 81 functions exceed 200 lines and 468 exceed 100. The longest are `_normalize` (1,081), `build_due_queue` (787) and `_compute_resolved_grade_application` (774). The last two decide what's served and what's learned. | `src/learnloop/content/synthesis/source_set_synthesis.py:658`, `src/learnloop/scheduling/scheduler.py:186`, `src/learnloop/attempts/attempts.py:4331` |
| P5 | medium | 40 root-level `*_upgrade.py` modules (8,215 lines) crowd the package root. It's the first place a new engineer looks, and half its files are one-time vault steps. | §7.3; `src/learnloop/cli/app.py:302` dispatches them by a long `if`/`elif` on the tag |
| P6 | medium | Two modules are called "card" and two are called "router" with different owners: `router/card.py` and `daily_plan/router_card.py`; `router/` (log and primitives), `router_objective/` (objective) and `daily_plan/router_*.py` (runtime and chooser). Names don't tell a reader where the router lives. | `src/learnloop/router/card.py:188`, `src/learnloop/daily_plan/router_card.py:551`, `src/learnloop/daily_plan/objective_chooser.py:45` |
| P7 | low | 142 modules are shallow. Most are CLI groups (15) and sidecar handler shims (20), where thinness costs little. The ones worth reading in Appendix A are the 19 at the package root. | Appendix A |

`config/schema.py` shows why the heuristic needs reading with care: it has 147 public classes, 5,133 raw lines and only 1,787 code lines, because much of the file is history in comments. Its effective keys number 1,185 (`docs/learnloop-architecture-vault/Reference/Configuration/Configuration Field Catalog.md:15`).

## 2. Data flow

The chains below are in call order. Lines marked `IH:` or `V4:` are in that branch's own file, because those stages haven't landed. Their code is mapped as if landed, except where §12 says it can't be.

The frontends reach Python through one hop: Tauri to stdio JSON-RPC to `src/learnloop_sidecar/server.py:55`.

### 2.1 Add a source, extract, read

| Step | Code | Persisted | Non-determinism or model |
|---|---|---|---|
| Enqueue | `src/learnloop_sidecar/handlers/ingest.py:266`, then `src/learnloop/content/pipeline/jobs.py:4686` | `ingest_batches`, `ingest_jobs` (`src/learnloop/db/stores/ingest_queue.py:124`, `:260`) | none |
| Hop to worker thread | `src/learnloop/content/pipeline/jobs.py:5457`, `:5487`; `src/learnloop/content/pipeline/runner.py:861`, `:977` | job lease and heartbeat | thread timing |
| Import job | `src/learnloop/content/pipeline/jobs.py:2068` | | fetched bytes (`:2115`) |
| Register revision | `src/learnloop/content/sources/source_library.py:33` | `source_artifacts`, `source_revisions` (`src/learnloop/db/repositories.py:19678`, `:19990`) | keyed by asset hash |
| Extract | `src/learnloop/content/pipeline/jobs.py:2168`, `:469` | `source_extraction_runs`, `source_document_units`, `source_document_blocks` (`src/learnloop/db/repositories.py:20298`) | extractor or model output, bounded by request-hash reuse; provider chosen at `src/learnloop/content/pipeline/jobs.py:261` |
| Later jobs | `src/learnloop/content/pipeline/jobs.py:2544`, `:2463`, `:2489`, `:1489`, `:1838` | vectors, inventory, synthesis | embedding and synthesis models |
| Read | `src/learnloop_sidecar/handlers/reader.py:561` | `source_render_views`, `source_render_block_crosswalk` (`src/learnloop/db/repositories.py:12879`, `:12944`) | background drain hop |

### 2.2 Plan, router decision, serve

| Step | Code | Persisted | Non-determinism or model |
|---|---|---|---|
| Handler | `src/learnloop_sidecar/handlers/daily_plan.py:327`, `:450`, `:195` | | blocking wait for diagnoses (`src/learnloop_sidecar/handlers/queue.py:305`) |
| Plan and pool | `src/learnloop/daily_plan/engine.py:4726`, `:1606`, `:2077`, `:1186` then `src/learnloop/scheduling/scheduler.py:186` | `daily_plans`, `attention_blocks`, `attention_block_events` (`src/learnloop/db/stores/daily_plans.py:56`, `:94`, `:128`) | exploration draw (`src/learnloop/scheduling/scheduler.py:2868`), skipped on staged plans |
| Boundary | `src/learnloop/daily_plan/engine.py:2839`, `:3113` then `src/learnloop/router_objective/checks.py:191` | check assignments | day seed (`src/learnloop/router_objective/checks.py:98`) |
| Frame | `src/learnloop/daily_plan/staged_frame.py:174`, `:320` | | none |
| Choose | `src/learnloop/daily_plan/objective_chooser.py:1181` | | boundary key includes the latest attempt (`:1225`) |
| Job hop | `src/learnloop/daily_plan/router_runtime.py:477`, then `src/learnloop/daily_plan/objective_chooser.py:660` | | daemon thread; model calls on `src/learnloop/daily_plan/router_runtime.py:556` (`router_decider`, advice only) and `:626` (`router_llm`) |
| Numeric policy | `src/learnloop/daily_plan/objective_chooser.py:442`, `src/learnloop/daily_plan/objective_inputs.py:645`, `src/learnloop/router_objective/tail_serve.py:122`, `src/learnloop/router_objective/value.py:1512` | | common random numbers from a seed (`src/learnloop/daily_plan/objective_chooser.py:144`); the draw count depends on the wall clock |
| Mix | `src/learnloop/daily_plan/objective_chooser.py:1331`, weight `:339`, decision id `:1371`, **mu drawn at `:1376`**; `src/learnloop/router_objective/mix.py:92` | | seed = hash(key, ULID) (`src/learnloop/router_objective/mix.py:111`), so not reproducible from the boundary alone; seed, u1 and u2 are logged |
| Stop coin | `src/learnloop/daily_plan/objective_chooser.py:1385`, `src/learnloop/router_objective/stop_coin.py:136` | assignments | own uniform |
| Persist | `src/learnloop/daily_plan/engine.py:2749`, `:965`, `src/learnloop/router/plan_log.py:488` | `router_decisions`, `router_decision_payloads` (`src/learnloop/db/stores/router.py:124`, `:271`), `router_objective_traces` (`src/learnloop/db/stores/router_objective.py:161`) | |
| Eligibility | `src/learnloop/daily_plan/engine.py:5069`, `src/learnloop/serve_eligibility.py:648` (pure), `:846` (reads) | | none |
| AD slot | `src/learnloop/daily_plan/engine.py:4983`, `src/learnloop/adaptive_difficulty/serving.py:181`, `src/learnloop/adaptive_difficulty/selection.py:174` | `ad_selections` | seed from block and slot |
| Serve | `src/learnloop/daily_plan/engine.py:5182`, `:5110` | `plan_presentations` (`src/learnloop/db/stores/plan_presentations.py:55`) | |

**The router's wait.**
- The default is 8 s on main (`src/learnloop/config/schema.py:4134`) and 40 s on `IH:src/learnloop/config/schema.py:4135`.
- `Prefetch.wait` waits on every component event, so a stalled advisory Decider also holds the serve (`src/learnloop/daily_plan/router_runtime.py:165`).
- After the wait, `Prefetch.results` marks anything unset as a timeout and ignores the late answer (`src/learnloop/daily_plan/router_runtime.py:173`).
- A failed policy's share goes to staged on main (`src/learnloop/router_objective/mix.py:38`) and to the other policy under IH5 (`IH:src/learnloop/router_objective/mix.py:54`).

**FG1 runs a second decision path on the worker.** `src/learnloop/followup_run/jobs.py:396`, `src/learnloop/followup_run/router.py:212`, `:179`, `src/learnloop/daily_plan/objective_chooser.py:1754`, `:1637`.

### 2.3 Attempt, blind grading, diagnosis, evidence, scheduling

| Step | Code | Persisted | Model |
|---|---|---|---|
| Submit | `src/learnloop_sidecar/handlers/practice.py:1344`, `:1362` | | |
| Blind plan | `src/learnloop/attempts/attempts.py:2161`, `:2331` | | |
| Grade | `src/learnloop/attempts/attempts.py:2367`, `src/learnloop/attempts/grading_support.py:1084`, `src/learnloop/attempts/blind_grading.py:687` | `blind_grade_records` (`src/learnloop/db/stores/diagnoses.py:125`) | purpose `blind_grading`, k samples, modal choice |
| Apply | `src/learnloop/attempts/attempts.py:3200`, `:3645`, `:4331` | | clock read at `:4356` |
| Mastery and memory | `src/learnloop/learner/mastery.py:924`; FSRS weights `src/learnloop/attempts/attempts.py:4732` | | |
| Write | `src/learnloop/attempts/attempts.py:3899`, `src/learnloop/db/repositories.py:5983` | attempt, evidence, surprise, `practice_item_state`, `learning_object_mastery` | |
| Project | `src/learnloop/attempts/attempts.py:3410`, `src/learnloop/substrate/canonical_projection.py:619` | `facet_recall_state`, `facet_capability_evidence` | |
| Queue | `src/learnloop/attempts/post_attempt.py:89` | `post_attempt_jobs` | |
| Worker hop | `src/learnloop_sidecar/post_attempt_worker.py:141` | | threads |
| Diagnose | `src/learnloop/diagnosis/split/jobs.py:682`, `:807`, `src/learnloop/diagnosis/split/diagnoser.py:102` | `attempt_diagnoses` (`src/learnloop/db/stores/diagnoses.py:250`) | route `diagnosis`; sampling arm from an attempt-id hash (`src/learnloop/diagnosis/split/prior_analysis.py:93`) |
| Apply diagnosis | `src/learnloop/diagnosis/split/jobs.py:1051` | recurrence, normalized attribution | escalation at `:1133` |
| Follow-up | `src/learnloop/diagnosis/split/jobs.py:670`, `src/learnloop/followup_serve/workflow.py:502`, `src/learnloop_sidecar/post_attempt_worker.py:219`, `src/learnloop/followup_run/jobs.py:70` | `followup_workflows` | one authoring call |
| Next schedule | `src/learnloop/scheduling/scheduler.py:186` | scheduler slates | seeded exploration |

Not traced: where router and AD outcomes are written after an attempt. They're replayed by `src/learnloop/substrate/rebuild_orchestrator.py:537` and `:595`, but the live write path wasn't followed.

### 2.4 Reader Ask, tutor context, answer

| Step | Code | Persisted | Model |
|---|---|---|---|
| Handler | `src/learnloop_sidecar/handlers/reader.py:140` | | |
| Adapter | `src/learnloop_sidecar/handlers/reader_tutor.py:182`, `:199`, `:286`; `src/learnloop/source_retrieval/reader_tutor.py:144`; `src/learnloop/reader_learner_state.py:179` | | |
| Dialogue | `src/learnloop/reader/reader_dialogue.py:537`, `:723` | | |
| Ask | `src/learnloop/tutor/tutor_qa.py:752` (727 lines) | `question_events`, `agent_runs` written before the call (`:1152`, `:1189`) | retrieval (`src/learnloop/tutor/reader_modes.py:557`, `src/learnloop/source_retrieval/find_sources.py:899`), route `source_rerank` when verifying; answer at `src/learnloop/tutor/tutor_qa.py:1205`, route `tutor_qa`; blocks the sidecar's request |
| After | `src/learnloop/tutor/tutor_qa.py:1269`, `:1358`, `:1418` | citations, reveal rows (`src/learnloop/attempts/reveal_ledger.py:173`), causal signals | |
| Tail | `src/learnloop_sidecar/handlers/reader_tutor.py:438` | exposure, gap job | hops |

`learner_context.py`, at 1,732 lines the largest root module, isn't on this path. Its importers are `remote/`, `teacher/guards.py` and `learnloop_mcp/server.py`, so the name misleads.

### 2.5 A chat (MCP) tool call, and how the phone differs

**MCP.** `src/learnloop_mcp/server.py:470`, `:442`, `:383`, then `src/learnloop/remote/runtime.py:99`, a secondary attach with no migrations or workers.
- Views run on a read-only attach (`src/learnloop/remote/runtime.py:166`).
- `learning_context` goes to `src/learnloop/learner_context.py:1602`, which reads through `TextGuard` (`:511`) and `withheld_items` (`src/learnloop/learner_protection.py:190`).
- `find_sources` goes to `src/learnloop/remote/sources.py:150`.
- Every call or rejection is recorded before it returns (`src/learnloop_mcp/server.py:364`, `src/learnloop/remote/telemetry.py:120`).

**Phone.**
- It dispatches the real sidecar handlers (`src/learnloop_mobile/runtime.py:250`) behind a default-deny allowlist (`src/learnloop_mobile/allowlist.py:123`).
- Long methods commit to `mobile_jobs` first (`src/learnloop/capture/jobs.py:119`).
- Diagnosis runs with the desktop closed (`src/learnloop_mobile/runtime.py:222`).
- Its protection comes from eligibility and, under Phone V4, `V4:src/learnloop/reader/phone_media.py:64`, not `learner_protection`'s `TextGuard`. This is one of the duplicated authorities in B3.

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| D1 | high | The plan path holds three kinds of randomness with different reproducibility: a day-seeded check draw, a ULID-salted mix draw and a clock-dependent number of numeric draws. Replaying a boundary needs stored values for the second and can't recover the third. | `src/learnloop/router_objective/checks.py:98`, `src/learnloop/router_objective/mix.py:111`, `src/learnloop/daily_plan/objective_chooser.py:442` |
| D2 | medium | "Next" has several blocking waits stacked up: diagnoses, then the router job, then all components including advisory ones. A learner-visible delay can't be attributed from one record. | `src/learnloop_sidecar/handlers/queue.py:305`, `src/learnloop/daily_plan/router_runtime.py:165` |
| D3 | medium | Two frontends reach the same domain code through different seams. MCP uses `remote/` and its own attach; the phone reuses sidecar handlers. Each has its own protection checks. | `src/learnloop/remote/runtime.py:99`, `src/learnloop_mobile/runtime.py:250` |
| D4 | high | **Router speed target still unmet.** Next right after feedback stays above 2 s on the large copies (a pinned week on linear_algebra: median 2,676 ms, 16 of 21 above 2 s, against mvp-0.49's 2,250 ms and 25 of 30). The remainder is the numeric policy's per-draw arithmetic (about 468k draw-evaluator calls in about 34 profiled jobs), then SQLite reads (about 13 s of 110 s). After a 3 s dwell no Next is above 2 s on any copy. | `docs/reviews/router-speed2.md:380`, `:388`, `:458`; `src/learnloop/router_objective/value.py:1512` |
| D5 | medium | **R4's cost.** A pooled connection on which a PRAGMA with an argument ran is closed at release, and `PRAGMA table_info(t)` is such a PRAGMA. There are 53 `table_info` sites in 39 files, including the objective's own paths, so each column check inside a job throws away a pooled connection. Measured opens per job went from 5 to 17 after R1-R4. Column checks are themselves compatibility code for older schemas. | `src/learnloop/db/connection.py:310`; `docs/reviews/router-speed2-codex-review.md:259`; `src/learnloop/router_objective/scores.py:199`, `src/learnloop/router_objective/checks.py:563`, `src/learnloop/daily_plan/router_card.py:447` |

## 3. Boundary crossings

### 3.1 Where policy lives

| Policy | Lives in | Can it change without touching unrelated subsystems? |
|---|---|---|
| Objective form | `src/learnloop/router_objective/value.py:1496` (term names), `:602` (an 860-line `_Model` holds both the objective's ledger and the rollouts) | Term names stay in one file. Changing a term usually isn't local (§3.3). |
| Mixing | `src/learnloop/router_objective/mix.py:38` | The rule is a 133-line leaf, but IH5 still touched 13 source files (§3.3). |
| Choosing a block | `src/learnloop/daily_plan/objective_chooser.py:1331` | No. It also holds the weight read, seed, coin, guard, trace assembly and carry registration. |
| Staged rule | `src/learnloop/scheduling/staged_policy.py:294`, `src/learnloop/daily_plan/staged_frame.py:174`, `src/learnloop/daily_plan/lanes.py:477` | Three modules, one named "legacy" though it's live. |
| Scheduling score | `src/learnloop/scheduling/scheduler.py:186` (787 lines) | No. Ranking, exploration, propensities and persistence share one function. |
| Memory | `src/learnloop/scheduling/fsrs.py`, and the objective's own `src/learnloop/router_objective/memory.py:287` | Two implementations of a review step exist by design: the live one and the rollouts'. |
| Mastery | `src/learnloop/learner/mastery.py:924` (pure) | Yes for the update, no for what feeds it (`src/learnloop/attempts/attempts.py:4331`). |
| Grading rules | `src/learnloop/attempts/grading.py:926` (725 lines), `src/learnloop/attempts/blind_grading.py:687`, `src/learnloop/held_grades.py:62` | Two validators, one per lane. |
| Protection | `src/learnloop/learner_protection.py:190`, `src/learnloop/serve_eligibility.py:648`, `src/learnloop/scheduling/serving_exclusions.py:131`, `src/learnloop/figures/prefetch.py:290`, `V4:src/learnloop/reader/phone_media.py:64`, `V4:src/learnloop/scheduling/device_eligibility.py:330` | No. See B3. |
| Spend | `src/learnloop/ai/spend.py:188`, `src/learnloop/daily_plan/router_runtime.py:396`, `src/learnloop/figure_admission.py:346` | Three admission styles with different records (§4). |
| Probe deciding | `src/learnloop/diagnosis/causal_probe_coherence.py:413`, `src/learnloop/followup_run/lanes.py:59`, the follow-up gate at `src/learnloop/daily_plan/objective_chooser.py:1754` | No. See §4.4. |

### 3.2 Crossings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| B1 | high | Lower modules import the objective, and the objective's switch module is imported everywhere. `router_objective_switches.py` is a 390-line root module imported by 30 modules, including evidence (`attempts/attempts.py`), replay and rebuild. It mixes kill switches with the availability predicate that AD's history reads. | `src/learnloop/attempts/attempts.py:4719`, `src/learnloop/adaptive_difficulty/history_card.py:57`, `src/learnloop/adaptive_difficulty/outside.py:93` |
| B2 | medium | Packages below or beside the router reach into its internals: the scheduling controller cutover reads `decision_state`, the teacher reads assignments and checks, and FG1's worker lazily imports the chooser's gate. Each of these imports is function-local, so no import-linter contract sees a new layer. | `src/learnloop/scheduling/controller_cutover.py:286`, `src/learnloop/teacher/episodes.py:163`, `src/learnloop/teacher/report.py:269`, `src/learnloop/followup_run/router.py:169` |
| B3 | high | Protection has one named authority and several other decision sites. `learner_protection` is the predicate for chat and teacher text. The plan uses eligibility and exclusions. Figures run their own candidate filter with several checks. The phone uses device eligibility and media rules. 27 source files call one of the withheld or protection reads. Phone V4's landing needed a ruling that protection "judges an Ask's complete stored provenance before any presentation switch", because the frontend's check had drifted. | `src/learnloop/learner_protection.py:190`, `src/learnloop/figures/prefetch.py:947`, `V4:src/learnloop/scheduling/device_eligibility.py:330`; commit `b1b08138a6` on `phone/v4-reader` |
| B4 | high | Registering one table takes four to six files: the migration, `db/table_roles.py`, `adaptive_difficulty/protected_tables.py`, `adaptive_difficulty/column_classes.py`, a store, and the reference. Registering one constant adds a `_reg_const` entry (400 in the registry). A guard test enforces each. These protect real invariants, but every feature pays for AD's table firewall and the parameter ledger. | `src/learnloop/db/table_roles.py:41`, `src/learnloop/adaptive_difficulty/protected_tables.py:33`, `src/learnloop/adaptive_difficulty/column_classes.py:90`, `src/learnloop/params/parameter_registry.py:1559` |
| B5 | medium | The dependency rules are hard to read as a whole: 43 contracts in `pyproject.toml`, with long lists of exceptions and a 251-line frozen-cycle contract. `allow_indirect_imports = true` appears throughout, so a contract says less than its name. | `pyproject.toml:1060`; `lint-imports --no-cache` reports 43 kept, 0 broken |
| B6 | medium | Duplicated causal and probe predicates exist: `resolve_cold_probe_parameters` and `resolve_causal_probe_parameters` (noted Oct 15), and FG1 re-calls `decide_probe` with hard-coded zero inputs for a log field. | `src/learnloop/goals/certification_cold_probe.py:248`, `src/learnloop/diagnosis/causal_probe_coherence.py:151`, `src/learnloop/followup_run/router.py:111` |
| B7 | medium | `daily_plan/engine.py` carries product policy inside its traversal. Offer withdrawal, forced items, the check draw and AD's fallback are all inline in `advance_with_context` and `_boundary`. | `src/learnloop/daily_plan/engine.py:4823`, `:3113`, `:4983` |
| B8 | medium | Performance switches leak into a learned model's identity. Serving switches are part of RO6's generator payload and the boundary key. `held_ad_link` and the two speed-2 switches changed no decision value, yet the landing needed `SEED_NEUTRAL_SWITCHES` so the numeric seed ignored them, and RO6's generator "changes once when the new code first serves (a change point)". | `src/learnloop/daily_plan/objective_chooser.py:144`, `:223`; `docs/reviews/router-speed2.md:27` |
| B9 | low | Two defaults for the same FSRS prior: 5.0 in the input builder and in `Topic`. | `src/learnloop/daily_plan/objective_inputs.py:719`, `src/learnloop/router_objective/value.py:262` |

### 3.3 Item 6: the files each sample change edits today

Each row is counted from a real commit where one exists. "Source" excludes `config/template.py`, whose snapshot lines are counted separately; these commits' test edits are in §9.

| Change | Real example | Source files | What must be edited today | Local today? |
|---|---|---:|---|---|
| Add a sensor | `4d995af688` (TE0: confidence into the router card and model contexts); `e133e961a7` (a lesson's minutes on the objective's clock) | 11; 7 | Reader of the fact; `daily_plan/router_card.py` and `router/card.py` for the LLM's card, or `daily_plan/objective_inputs.py` and `router_objective/value.py` (`Topic`, `Inputs`) for the numeric policy; then `router_objective/trace.py`, `decision_state.py`, `tail_data.py` if the learned tail reads it; AD's guard lists if it reads a protected table | No. A sensor has two destinations with no shared definition. |
| Change a term of the objective | `3d018ebf50` (R1), `8a19c2698b` (R9), `58b727566e` (R6), `0c448efaa7` (R11) | 3, 6, 4, 1 | Always `router_objective/value.py`; usually `daily_plan/objective_chooser.py`, `objective_inputs.py`, `router_objective_switches.py`, `config/schema.py`, `params/parameter_registry.py`; a defaults digest for a new switch | Only R11, which was a one-file correction. |
| Swap the mixing rule | `d602dc8472` (IH5, on `instruct/handoff`) | 13 | `router_objective/mix.py`; `objective_chooser.py`; `trace.py`, `objective_report.py`; `algorithm_versions.py`, a 223-line `failure_share_upgrade.py`, `cli/app.py`, `cli/runtime.py`, `learnloop_sidecar/context.py`, `activation_journal.py`; `router_objective_switches.py`, `config/schema.py`, `params/parameter_registry.py` | No. The rule is 47 changed lines of 422. The rest is successor plumbing (§9). |
| Add an action | `e4131322b0` (TE3b: lesson offers in the block's support) | 20 | `daily_plan/lesson_offer.py` (new), `engine.py`, `lesson_suggestion.py`, `objective_chooser.py`, `objective_inputs.py`, `policy.py`, `records.py`, `router_card.py`, `types.py`, `view.py`; `router/plan_log.py`, `requests.py`, `why.py`; `router_objective/value.py`, `trace.py`, `offer_report.py`; store, registry, CLI, sidecar context | No. An action has no module of its own to implement. |
| Change a seed (prior) | Prior value: `llm_weight_prior`, read at `src/learnloop/router_objective/weight.py:60`, behaves as the 40 s default does (§9). Random seed: `bc1ceab278` (R2) | 2 | The default in `config/schema.py`; 46 digests in `config/template.py`; each frozen-digest test (12 for the 40 s) | The value is one line. The plumbing isn't. |

**Leaks across the top layer**, from lower detail into the choice, or from the choice into lower modules:
1. Chooser and job control are one module: `ObjectiveChooser` subclasses `RouterChooser` and runs threads, deadlines, carries and traces beside the choice. `src/learnloop/daily_plan/objective_chooser.py:45`, `:660`, `:1173`.
2. The numeric policy's draw count depends on the clock inside the top layer. `src/learnloop/daily_plan/objective_chooser.py:442`.
3. Trace assembly in the chooser knows every action kind and term source. `src/learnloop/daily_plan/objective_chooser.py:1000` and the offer branch at `:949`.
4. `_Model` couples what's optimized to rollout mechanics, so the objective can't be read apart from the simulation. `src/learnloop/router_objective/value.py:602`.
5. `value.py` holds the AD link's inverse and the lesson curve. `src/learnloop/router_objective/value.py:123`, `:285`.
6. Serving switches enter identity (B8).
7. `decide_probe` and its verbs make a second top layer for one decision (§4.4). `src/learnloop/diagnosis/causal_probe_coherence.py:413`.
8. FG1's refusal keys reuse causal hard refusals, so the router's support depends on causal internals. `src/learnloop/followup_run/router.py:76`.
9. Lessons' offers are valued in the chooser, built in `lesson_offer`, and withdrawn in the engine. `src/learnloop/daily_plan/objective_chooser.py:949`, `src/learnloop/daily_plan/lesson_offer.py:235`, `src/learnloop/daily_plan/engine.py:4823`.
10. Attempts read a router-objective switch to decide whether the interval multiplier applies, so an evidence path depends on the router's successor tag. `src/learnloop/attempts/attempts.py:4719`.

## 4. Decision points and observability (Nov 8 item 11, Nov 3 items 1-4)

**Short answer: no single id links user input to reasoning to behaviour.** The only column of that name in the schema is `objective_trace_id` on lesson episodes (`migrations/247_lesson_episodes.sql:70`). The router, grading, diagnosis and figures each keep their own record. Some are very good: `ad_selections` and `router_objective_traces` store alternatives and probabilities. The gaps are at failures, exclusions and the joins between records.

### 4.1 Inventory

Key: **R** a persisted row, **L** a log line only, **M** memory only, **-** nothing. "Why-not" asks whether each alternative's loss or exclusion is stored with a named rule. Rows marked (o) were read by outline or grep only, not read through.

| Decision or step | Code | Chosen | Alternatives and scores | Why-not | Inputs as of | Model, version, seed | Outcome link | Gap |
|---|---|---|---|---|---|---|---|---|
| Plan block | `src/learnloop/daily_plan/engine.py:2667`, `src/learnloop/router/plan_log.py:330` | R | R candidates with propensity | R constraint key | hash only | R; seed only if sampled | R via presentations | Chooser crash loses all reasoning (S1) |
| Top-k support | `src/learnloop/daily_plan/router_chooser.py:130` | R | names only | R `filtered` | - | k | - | Non-support candidates are never valued |
| Mix draw, mu, floor | `src/learnloop/daily_plan/objective_chooser.py:1363`, `src/learnloop/router_objective/mix.py:92` | R | R distributions | R failed plus status | waited ms | R weights, u1, u2, seed | R | Configured wait isn't on the row |
| Failure share (IH5) | `IH:src/learnloop/router_objective/mix.py:54` | R | as above | `failure_rule` | as above | switch in key | - | An absent key means either pre-tag or switch off |
| Rollouts, numeric policy | `src/learnloop/daily_plan/objective_chooser.py:442`, `src/learnloop/router_objective/value.py:1512` | R trace | R terms, q, SE, draws | tie record | sources and versions | switches; **seed not written** | R | The seed's identity excludes switches and isn't stored (`src/learnloop/daily_plan/objective_chooser.py:144`). The held reading map is "as of first read" with no stamp |
| Stop coin | `src/learnloop/router_objective/stop_coin.py:136` | R | R mu | score note | availability frozen | R seed, u, rate | R | Ineligibility: no field |
| Randomized checks | `src/learnloop/router_objective/checks.py:191` | R | (o) | R `non_service_type` | sensors frozen | R day seed | R | Draw or place failure: L only (`src/learnloop/daily_plan/engine.py:3133`, `:3179`) |
| Plan fallback rule | `src/learnloop/daily_plan/engine.py:2671` | R | - | R reason | - | R | - | S1 |
| Lesson offer build | `src/learnloop/daily_plan/lesson_offer.py:235` | R | kept only if drawn (`:313`) | R `none:*` | quantized | R | R | Builder crash: L only (`src/learnloop/daily_plan/engine.py:2896`) |
| Offer withdrawal | `src/learnloop/daily_plan/engine.py:4823`, `src/learnloop/daily_plan/lesson_offer.py:370` | R | n/a | R `forced_items` | time | - | - | **The forced item, workflow and next decision aren't named** |
| Learner action (IH3) | `IH:src/learnloop/daily_plan/learner_action.py:235` | R | R offered, p | note | - | R | R | A failed lesson candidate vanishes with only a log line |
| VOI stop | `src/learnloop/diagnosis/voi_stopping.py:2176` (o) | R | in detail (o) | R | R posterior | R | - | Forecast logging failure: L only (`src/learnloop/diagnosis/voi_forecasting.py:173`) |
| Follow-up value | `src/learnloop/diagnosis/voi_stopping.py:2274` | R | R | R | - | R | - | No router decision id |
| Decider judgment | `src/learnloop/decider_judgments.py:231` | R | R in rationale | status word | hash only | R | - | `disabled` returns no row (`:255`). The exception text is dropped (`:279`) |
| Grading verdict | `src/learnloop/attempts/grading.py:1570` (o) | R | - | review reason | hash | R | R | Not traced in depth |
| Held grade | `src/learnloop/held_grades.py:62` | derived at read | - | M | - | - | R excluded from evidence | No decision row: the hold is a predicate |
| Diagnosis attribution | `src/learnloop/diagnosis/followups.py:995` (o) | R debug payload | R support scores | - | - | - | - | Replay rebuilds it. Hook failures: L only |
| Causal probe decision | `src/learnloop/diagnosis/causal_probe_coherence.py:413`, `src/learnloop/diagnosis/causal_orchestrator.py:1467` | R | verb only | R | R inputs | R deterministic | R pin | No router link. Shadow failure: L only (`:1507`) |
| Probe selection | `src/learnloop/diagnosis/probe_episodes.py:1612` (o) | R | target pairs, EIG | R end reason | R posterior | R | R | Rejected instruments not checked |
| FG1 gate | `src/learnloop/followup_run/router.py:179`, `src/learnloop/followup_run/lanes.py:59` | R | R arms | R refusal key | R | R | R bindings | A refused decision row: L only, behaviour still applies (`src/learnloop/db/stores/router.py:140`) |
| Follow-up serve | `src/learnloop/followup_serve/workflow.py:165` (o) | R events | - | R | R | - | R | The workflow row is mutable; events carry history |
| Learner protection | `src/learnloop/learner_protection.py:190` | M | - | M | - | - | - | A per-call read: no row of its own |
| Serve eligibility | `src/learnloop/serve_eligibility.py:648`, `src/learnloop/daily_plan/engine.py:5069` | L; R when displaced | - | displacement only | - | - | - | Ordinary serves leave only a log line |
| Serving exclusions | `src/learnloop/scheduling/serving_exclusions.py:131`, `src/learnloop/router/decisions.py:60` | R today offer | - | named or count only | hash | - | - | Only with offer trace. `src/learnloop/scheduling/scheduler.py:1343` `continue` has no reason |
| Prefilter | `src/learnloop/daily_plan/engine.py:977` | R | counts, hashes | R gates | R | R | - | Read failure: L. No decision row means no receipt |
| Device eligibility | `V4:src/learnloop/scheduling/device_eligibility.py:330` | reason code | - | R reason | - | - | - | Predicate failure fails closed, with no log |
| Router spend | `src/learnloop/daily_plan/router_runtime.py:396` | R on admit | - | R status | - | - | - | A refused request writes no call row |
| General spend | `src/learnloop/ai/spend.py:188` | varies | - | varies | - | - | - | A figure refusal raises and stores nothing (`src/learnloop/figures/service.py:2513`) |
| Re-read, alias | `src/learnloop/ingest/reanchor.py:41` (o) | M | ? | M | ? | ? | ? | Alias store not confirmed |
| AD selection | `src/learnloop/adaptive_difficulty/serving.py:181` | R | R support with p | R per failed check | R state hash | R seed, u | R | **The most complete mechanism found** |
| AD unavailable | `src/learnloop/daily_plan/engine.py:4930`, `:4947`, `:5032` | L | - | code in log | - | - | - | The incumbent serves, with no row. Denials go to a JSONL file (`src/learnloop/adaptive_difficulty/denial_log.py:98`) |
| AD generation | `src/learnloop/adaptive_difficulty/generation.py:173` (o) | R | - | - | - | R | R | Refusal: L only |
| Hint ladder | `src/learnloop/hints/chooser.py:301` | R | R probabilities | R status | R hash | R seed | (o) | Missing client: no row |
| Teacher lesson | `src/learnloop/teacher/service.py:1155` (o) | R turns, receipts | ? | ? | ? | R | ? | Not read through |
| Lesson check | `src/learnloop/teacher/checks.py:198` | R on success | - | R failed run | - | R | (o) | Attempt-level trace not checked |
| Figure author | `src/learnloop/figures/service.py:2496` | R | attempt 1's problems overwritten | R reason, capped | R hash | R | R predictions | "Bad prediction" isn't a typed field |
| Prediction salvage | `src/learnloop/figures/spec.py:804`, `:842` | R | - | R dropped (capped) | - | - | - | `_flat_change` repairs silently (S10) |
| Figure pre-build | `src/learnloop/figures/prefetch.py:1056`, `src/learnloop/figures/prefetch_model.py:459` | R | EU, propensity | **`Decision.reason` not stored** | digest only | **RNG unseeded** (`src/learnloop/figures/prefetch.py:1061`) | R | S7, S8 |
| Reader retrieval | `src/learnloop/source_retrieval/library.py` (o) | conditional | `matched_by` in response | - | - | - | conditional | Stored only when logging is on |
| Ingest routing | `src/learnloop/ingest/extractors/__init__.py:84` (o) | not checked | - | raises | - | - | - | No routing receipt seen |
| Curriculum path | `src/learnloop/daily_plan/engine.py:540` (o) | status on read | label | shown | fingerprint | - | - | Unreadable path: L and a status |
| FSRS, interval | `src/learnloop/attempts/attempts.py:4718` | R surprise row | - | - | - | switch | - | Rating and elapsed aren't frozen per attempt: they're re-derived |
| AI route fallback | `src/learnloop/ai/routing.py:700` (o) | M | - | - | - | call row shows actual provider | - | No fallback event row |
| Retries | `src/learnloop/ai/execution.py:364` | R parent call | - | error type | - | - | - | Linked by owner only |

### 4.2 The worst silent sites

| ID | Site | What's lost |
|---|---|---|
| S1 | `src/learnloop/daily_plan/engine.py:2671` | Any chooser exception, including a mixture error after the models answered, becomes `<error: Type>`. `router_record` is then `None`, so answers, trace and payloads are dropped. No log line. |
| S2 | `src/learnloop/daily_plan/router_runtime.py:173` | An unanswered component becomes a synthetic timeout with no model or request payload. No log line. |
| S3 | `src/learnloop/daily_plan/router_runtime.py:605`, `:695` | A provider failure stays in the result object. It persists only if a decision is drawn from that entry. |
| S4 | `src/learnloop/daily_plan/router_chooser.py:304`, `src/learnloop/daily_plan/engine.py:2667` | A read whose key changes before serving leaves receipts with no decision row. |
| S5 | `src/learnloop/daily_plan/router_runtime.py:490` | Prefetch entry eviction, no record. |
| S6 | `src/learnloop/daily_plan/router_chooser.py:342` | `card_error` goes on the record, but no persisting reader was found. |
| S7 | `src/learnloop/figures/prefetch.py:937`, `:947` | Early returns and a run of `continue` filters drop figure candidates with no row, including protection exclusions. |
| S8 | `src/learnloop/figures/prefetch_model.py:465`, `:469` | The reason string, including "no measured build latency", isn't stored. |
| S9 | `src/learnloop/figures/prefetch.py:1279` | Build stoppages go to in-memory notes. |
| S10 | `src/learnloop/figures/spec.py:842` | A shape repair leaves no note. |
| S11 | `src/learnloop/decider_judgments.py:255`, `:279` | A disabled Decider leaves no row; a failed call keeps no exception text. |
| S12 | `src/learnloop/router/decisions.py:100` | On a head mismatch, the offer is published unlogged. |
| S13 | `src/learnloop/db/stores/router.py:140`, `src/learnloop/daily_plan/engine.py:977` | A refused decision row is a log line while the behaviour still applies. |
| S14 | `src/learnloop/followup_run/router.py:127` | The logged causal check's failure becomes `{}`. |
| S15 | `src/learnloop/scheduling/scheduler.py:1343` | Candidates skipped with no reason. |

### 4.3 Partial provenance mechanisms and the breaks between them

| Mechanism | Grain | Differs by |
|---|---|---|
| `router_decisions`, `router_decision_payloads` | Decision | Broadest ledger. Payloads are pruned at 365 days (`src/learnloop/config/schema.py:4129`) |
| `router_objective_traces` | Objective decision | Absent below mvp-0.47 and for deterministic picks (`src/learnloop/cli/router.py:311`) |
| `router_outcomes` | Decision | Derived |
| `prefilter_receipts`, `decision_state_receipts`, `session_receipts`, `decision_objectives`, `decision_measurement_events` | Decision or session | Serving lanes, behind switches |
| `plan_presentations` | Served item | Link to attempts |
| `router_decision_bindings`, `followup_workflows`, `followup_workflow_events` | Workflow | FG1 only |
| `judgment_ledger` | Judgment | Keyed by entity and input hash, no decision id |
| `model_call_receipts`, `agent_runs` | Call or run | Free-text `owner_kind` and `owner_id` |
| `forecast_receipts`, `voi_forecasts` | Forecast | Free-text decision ref |
| `decision_features` | Decision type plus id | No foreign key, older |
| `followup_value_decisions` | Source attempt | No router id |
| `causal_probe_decision_receipts`, `causal_discriminating_observations` | Causal factor | Causal ids only |
| `ad_selections` | Slot | Links to `router_decision_id` |
| `figure_prefetch_decisions` | Candidate | Own ledger |
| `router_suggestion_responses` | Offer | Links to the decision |
| `scheduler_slates`, `scheduler_slate_candidates`, `scheduler_explanations` | Slate | Good alternatives and scores, but no exclusions (no exclusion or reason column) |
| `interaction_events` | Event | Not decisions |

**The closest chain.** FG1: `practice_attempts.id` to `followup_workflows.source_attempt_id` to `decision_id` to `router_decisions.id` to bindings to presentation to attempt to `router_outcomes`. For a plan: `router_decisions.id` from `plan_presentations.router_decision_id` from `practice_attempts.plan_presentation_id`.

**The breaks:**
1. A plan decision names no triggering attempt. The attempt is only hashed into the key (`src/learnloop/daily_plan/router_chooser.py:428`, `src/learnloop/daily_plan/objective_chooser.py:1225`).
2. Model calls happen before the decision's id exists (`src/learnloop/daily_plan/objective_chooser.py:1371`). Their receipts hold the boundary key, joined only through JSON. On a Nov 3 copy, a direct join on the decision id found none of the router's receipts, which confirms the break from data.
3. Pending reads have no id.
4. `decision_receipt_id` is overloaded: the learner lane passes a causal receipt id (`src/learnloop_sidecar/handlers/remediation.py:191`), FG1 passes a router decision id into the same field (`src/learnloop/followup_run/jobs.py:431`, `src/learnloop/followup_run/admission.py:417`).
5. Learner-lane probes have no router row at acceptance.
6. Follow-up value, judgments, decision features and pre-builds have no router column.

**The entry points today.**
- `learnloop why` takes a practice item only, covers the scheduler only, and runs `sync_vault_state` and `run_startup_maintenance` first, so it isn't a pure read (`src/learnloop/cli/app.py:2407`).
- `learnloop router trace` is read-only and good, but covers objective decisions only (`src/learnloop/cli/router.py:311`).
- `trace-evidence` covers evidence (`src/learnloop/cli/app.py:1841`).
- The learner-facing "why" is a sentence (`src/learnloop/router/why.py`).

### 4.4 Nov 3 items 1-4

**Item 1, deciding.** `decide_probe` has two call sites: authoritative on the repair lane (`src/learnloop/diagnosis/causal_orchestrator.py:1735`), and logged only with fixed zero inputs on FG1's lane (`src/learnloop/followup_run/router.py:111`, inputs at `:115`). `causal_repair_status` has four callers (`src/learnloop/diagnosis/followups.py:1066`, `src/learnloop/diagnosis/causal_orchestrator.py:2317`, `src/learnloop/diagnosis/remediation.py:154`, `src/learnloop_sidecar/handlers/remediation.py:170`). `accept_probe_offer` has two (`src/learnloop_sidecar/handlers/remediation.py:191`, `src/learnloop/followup_run/admission.py:417`).

| Question | Causal lane | Router or other |
|---|---|---|
| Probe at all | `probe_now` versus skip verbs | FG1 arms |
| When | Offered at feedback, no draw | `insert_now` versus `continue_current` |
| Worth the minutes | `skip_burden_exceeds_value` | Q-bar with minutes, `voi_stopping`, follow-up value |
| Session budget | `defer_session_budget` | Plan minutes, stop arm |
| Burden | `defer_recent_burden` | Coin and price, with no shared rule |
| Hard refusals | Preference, machine checks, episode conflict | The same functions (`src/learnloop/followup_run/router.py:76`) |
| Repair | `RemediationBlocked` holds repair (`src/learnloop/diagnosis/remediation.py:163`) | The router has no arm |

A sixth path picks probe versus practice (`src/learnloop/followup_run/lanes.py:59`), and scheduler EIG reads the episode posterior (`src/learnloop/scheduling/scheduler.py:2688`). **Sev: high.** Six sites answer "should we probe?".

**Item 2, measuring.** One record of each fact:

| Table | Written at | Facts that overlap | Unique |
|---|---|---|---|
| `causal_probe_decision_receipts` | `src/learnloop/diagnosis/causal_orchestrator.py:1467` | factor and attempt; EIG (`probe_presentations`, different computation); burden minutes (trace); preference events; candidate ids (`probe_presentations`); verb (router's observational field, value verdict) | Formula and EVSI provenance |
| `causal_discriminating_observations` | `src/learnloop/diagnosis/causal_orchestrator.py:2604`, `:2778` | attempt and presentation; features (`probe_observations`, grading evidence); independence (discount in `probe_observations`); support (diagnosis receipt) | Which prediction was confirmed |
| `causal_probe_preference_events` | `src/learnloop/diagnosis/causal_orchestrator.py:799` | The workflow's release reason | The statement |
| `causal_blind_prediction_bundles` | `src/learnloop/diagnosis/causal_probe_coherence.py:999` (not the orchestrator) | ids in `probe_presentations`; model in call rows | The predictions |
| `causal_cold_verifications` | `src/learnloop/diagnosis/causal_probe_coherence.py:1961` | attempts; success (attempt score versus threshold); delayed outcome (`router_outcomes` R_cold, a separate rule) | Capability and repair updates |
| `causal_cold_outcomes` | `src/learnloop/diagnosis/causal_orchestrator.py:3144`, `src/learnloop/diagnosis/remediation.py:780` | coldness receipts; `forecast_receipts`; `decision_measurement_events` vocabulary | Non-measured dispositions |

`decision_features`, `router_outcomes` and `forecast_receipts` share no row with the first table. **Sev: medium.** The overlap is by fact, not by row.

**Item 3, two belief updates.**

| | Episode posterior | Discriminating observation |
|---|---|---|
| Function | `src/learnloop/diagnosis/probe_episodes.py:1869`, `:2074` | `src/learnloop/diagnosis/causal_probe_coherence.py:1144`, `src/learnloop/diagnosis/causal_orchestrator.py:2488`, `:2642` |
| Rule | L_w = w·L + (1-w)·Σπ(h)L(h); π'(h) ∝ π(h)·L_w(h) | Exact key match to the pinned bundle; score 1 if matched, 0 for other measured; no prior or likelihood |
| Stored | `probe_observations` before and after; recomputed at each read | `support_scores`, `resolved_factor` |
| Read by | `src/learnloop/instructional/valuation.py:215`, `src/learnloop/scheduling/scheduler.py:2688`, `src/learnloop/source_retrieval/passage_cues.py:392`, others | below |

**They can disagree, and nothing reconciles them. Sev: high.**
- Different evidence models.
- Different sets: commissioning locks with support scores (`src/learnloop/diagnosis/causal_probe_commissioning.py:669`), while `enter_episode` locks again without them (`src/learnloop/diagnosis/probe_episodes.py:296`), and each insert mints a new id (`src/learnloop/db/repositories.py:7767`).
- Independence is a refusal in one and a discount in the other.
- Held grades are checked in the first (`src/learnloop/diagnosis/probe_episodes.py:1926`); no held check was seen in the second.

**Correction to the brief's list:** `instructional/valuation` reads the episode posterior, not the discriminating observations.

**Item 4, what logs can't replace.** These guarantees need rows written before the answer:
- bundles: `src/learnloop/diagnosis/causal_probe_coherence.py:999`, reached from `src/learnloop/diagnosis/causal_probe_commissioning.py:587` and `src/learnloop/followup_run/admission.py:354`, before acceptance at `:417`; migration 121 forces `generated_without_observation = 1`;
- the pin of ids: `src/learnloop/diagnosis/causal_orchestrator.py:2186`;
- the locked set: `src/learnloop/diagnosis/causal_probe_coherence.py:836`;
- the posterior at selection, in `probe_presentations`.

Readers of the discriminating observations:
- `src/learnloop/diagnosis/scoreboard.py:1328`
- `src/learnloop/diagnosis/failure_triage.py:439`
- `src/learnloop/diagnosis/causal_health.py:285`
- `src/learnloop/evsi_calibration/live_report.py:723`
- `src/learnloop/diagnosis/causal_factor_deferral.py:351`
- `src/learnloop/router_objective/picks.py:82`
- `src/learnloop/ops/capture_report.py:285`
- `src/learnloop/db/stores/hypothesis_marks.py:167`

### 4.5 The four real cases and a sample of past bugs

**All four real cases postdate the only permitted copy (Nov 3, mvp-0.43), so none could be tried against stored records.** The rows don't exist there. The Nov 3 copy also has no `router_objective_traces`, `prefilter_receipts` or `followup_workflows`. The answers below come from reading what the code stores, not from querying the events themselves. They're unverified against the real rows.

| Case | What the code stores | Answerable from stored data alone? |
|---|---|---|
| **Nov 7, router LLM answers discarded by the 8 s timeout** | `router_decisions`: `fallback`, null LLM model id, `detail_json.router.fallback_reasons.llm='timeout'`, `mixture.models.llm` with status `timeout`, error "no answer within the budget", `waited_ms`, `boundary_key`. `router_objective_traces`: `llm_status='timeout'`. No LLM payloads. `model_call_receipts`: owner = the boundary key, with `output_text` once the call finished. No log line. | **Partly.** That a timeout happened: yes. What the late answer said: only by a manual JSON join from the decision to the receipt. The 8 s isn't on the row. A read that deferred writes no decision. |
| **Nov 8, offer withdrawn with `forced_items`** | `router_suggestion_responses`: `expired`, `{withdrawn: forced_items, block_id}`. `attention_block_events`: `block_ended`, reason. The next decision's `detail.forced[]`. The workflow's rows for the probe. No log line. | **Partly.** The reason word: yes. Which probe forced it: only by time-ordering, because no id links them (`src/learnloop/daily_plan/lesson_offer.py:370`). |
| **Nov 8, figure stored failed for a bad prediction** | `interactive_figures`: `verification='failed'`, null spec, `verification_report_json.reason` (first problem, at most 300 chars), `structural` (at most 12), prompt version, model, input hash. `judgment_ledger`: verifier, `failed`. Call rows per attempt with raw output. | **Largely, by reading text.** "Bad prediction" isn't typed. Attempt 1's problems survive only in attempt 2's prompt, if input was kept (not checked for this route). |
| **Why automatic pre-builds started after 12 skips** | `figure_prefetch_decisions`: `skip` rows with null EU and propensity 0, then `build` rows with positive EU, and a posterior digest. | **No, only by reconstruction.** The owner's "never explained" stands. **No counter or threshold of 12 exists in the code**: there's no such constant in `src/learnloop/figures/prefetch.py`, `prefetch_ledger.py` or `prefetch_model.py`. From code: with no measured latency, every decision is a skip with reason "no measured build latency", and that reason isn't stored (`src/learnloop/figures/prefetch_model.py:465`). Once a press or a completed `figure_author` call is measured (`src/learnloop/figures/prefetch_ledger.py:241`), `waits` isn't `None`. With blocked minutes unmeasured, cost is 0, so EU = p_open·wait > 0 and every draw builds (`src/learnloop/figures/prefetch_model.py:448`). So "12" would be how many candidates were skipped before the first measurement, not a rule. That's a hypothesis from code, not checked against the rows. The filter `owner_kind NOT LIKE 'prefetch%'` may not exclude pre-builds, if their owner kind is the task name (`src/learnloop/figures/routes.py:552`); not verified. |

**Past bugs tried on the Nov 3 copies.** Only outcomes are given here. Counts are in the private file.

| Past bug or question | Tried | Outcome |
|---|---|---|
| Why was this item served? (the shape of `docs/reviews/daily-loop-bugs.md` bug 2) | From an attempt with a slate: `scheduler_slate_id`, then its `scheduler_slate_candidates` | **Answered for alternatives and scores:** every candidate has priority, reward, predicted correctness and components. **Not for exclusions:** no column names why an item never reached the slate, which was this bug's actual question. |
| "The scheduler offer does not belong to this item/session" (`docs/reviews/owner-capture-2026-10-25-fixes.md`, B4) | Looked for a stored rejection | **No.** It raises `ValueError` (`src/learnloop/db/repositories.py:19244`) and nothing stores the refusal. |
| "Choosing a help style changed nothing" (same review, B2: no Decider routed) | `help_assists.chooser`, `judgment_ledger` | **Not answerable on these copies:** they hold no such rows, and `decider_judgments` returns without a row when disabled (S11), so "no Decider routed" leaves no trace by construction. |
| A router decision that fell back to a rule | `router_decisions.fallback`, payloads, outcome on `probability` | **Partly.** The decision, candidates, seed, card, requests and outcome are present. Joining to its call rows by decision id finds none (break 2). The copy's failed call rows keep an error type but no message or output. |
| Grader tests failing at a date (`docs/reviews/fix-grader-date-nov1.md`) | n/a | **Can't be tried.** It's a test-only bug with no stored data. |

### 4.6 Findings

| ID | Sev | Finding |
|---|---|---|
| O1 | high | No common trace id, and the only joins from a model call to its decision go through JSON. |
| O2 | high | The failure paths are where records stop: S1, S2 and S3 lose exactly the cases the owner has had to debug. |
| O3 | high | Exclusions are mostly unrecorded outside AD's selection and the staged frame: S7, S15, and the scheduler's slate has no exclusion column. |
| O4 | medium | Inspection tools are per-subsystem, and `learnloop why` writes before it reads. |
| O5 | medium | Reasons are often free text or capped, so "why" needs a human reading. |
| O6 | medium | Storage-wise: payload pruning at 365 days means "why" on old decisions keeps only a hash. |

## 5. Functional core and imperative shell

**Already mostly clean.** These are pure, or close to it, by reading or by grep for DB, clock and client use:
- `src/learnloop/learner/mastery.py:924` (the EKF update)
- `src/learnloop/field/predictors.py`
- `src/learnloop/scheduling/fsrs.py`, `src/learnloop/scheduling/evsi.py`
- `src/learnloop/router_objective/mix.py:92`
- `src/learnloop/serve_eligibility.py:648`, with its reads split out at `:846`
- `src/learnloop/adaptive_difficulty/selection.py:174`
- `src/learnloop/router_objective/value.py:1512`, which takes an injected clock

The `voi_stopping` valuation looks clean in the functions listed, but wasn't fully read.

**Entangled:**

| ID | Sev | Function | What's mixed in | Cost |
|---|---|---|---|---|
| F1 | high | `src/learnloop/daily_plan/objective_chooser.py:1331` `_decide_objective` | DB reads (weight, availability), a shared-job lock, a ULID-derived seed, the mix draw, the coin, the guard, trace assembly and carry registration with a background thread | Tests must pin the seed through the runtime. There's no way to call "given these inputs, choose". |
| F2 | high | `src/learnloop/daily_plan/objective_chooser.py:442` `run_numeric` | DB build, a monotonic deadline, callbacks, a blocking wait on the LLM, ContextVar read caches and connection pooling | The number of draws, and so Q-bar, depends on wall clock. This is also where the speed target's remainder lives (D4). |
| F3 | high | `src/learnloop/attempts/attempts.py:4331` `_compute_resolved_grade_application` | Clock read (`:4356`), repository reads (`:4732`), the EKF, surprise, FSRS scheduling and record construction in 774 lines | The core learner-state step can't be tested without a repository. |
| F4 | high | `src/learnloop/scheduling/scheduler.py:186` `build_due_queue` | Ranking, seeded exploration, propensities, reconciliation writes and slate persistence behind `persist_explanations`, with a `SystemClock` default | IH's prefetch must pass `persist_explanations=False` on a read-only attach, so a read path has to know a write flag exists. |
| F5 | medium | `src/learnloop/adaptive_difficulty/serving.py:181` `decide_slot` | Reading sweep writes, snapshot read, scoring, draw, insert and commissioning in the caller's transaction | `selection.py` and `predict.py` are pure, but this is the only live composition. |
| F6 | medium | `src/learnloop/attempts/attempts.py:2331`, `src/learnloop/diagnosis/split/jobs.py:807` | Model calls, validation, spend guards, sampling arms and transactions | Grading orchestration can't be exercised without fakes at each seam. |
| F7 | medium | `src/learnloop/learner/mastery.py:293` | The EKF's prior depends on repository claim reads | A "pure" model has an impure start. |
| F8 | medium | `src/learnloop/router_objective/tail_serve.py:122` | Fits inside a DB connection scope | The learned tail can't be run apart from storage. |
| F9 | low | `src/learnloop/scheduling/staged_policy.py:747` | Snapshot persistence, EVSI ranking, randomization and shadow writes | Its docstring says it serves shadow and golden-path; its callers weren't enumerated. |
| F10 | low | `src/learnloop/daily_plan/engine.py:2620` | Docstring says "Pure", while `policy.chooser.choose` does DB, threads and models | The comment misleads. |

## 6. Comments

This section rests on counts and a sample, not a read of 35,795 comment lines. The counts are regex matches over comment text, so they overlap and are approximate.

| Measure | Count |
|---|---:|
| Comment lines in `src/` | 35,795 |
| ...naming a stage artifact (ruling, Codex, round, landing, F-number or R-number) | about 2,312 |
| ...naming a spec or section | about 2,819 |
| ...naming the owner | about 580 |
| ...with a "why" marker word (because, since, so that, otherwise, why) | about 2,712 |
| Lines mentioning "legacy" | 1,344, in 239 files |

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| C1 | medium | Many comments are change history, not explanation: they say which review round produced a line rather than what breaks without it. A reader needs the review file to get the reason. | `src/learnloop/daily_plan/engine.py:4826`, `:4828`; `src/learnloop/db/connection.py:310` |
| C2 | medium | `config/schema.py` and `config/template.py` carry their history inline. `schema.py` is 5,133 raw lines with 1,787 code lines. | `src/learnloop/config/schema.py:4134` and the surrounding notes |
| C3 | medium | Some names and comments are stale or misleading: `LegacyLanesSource` is live on every path; `decide` says "Pure" (F10); `learner_context` isn't the learner context of the Ask path (§2.4). | `src/learnloop/daily_plan/lanes.py:477`, `src/learnloop/daily_plan/engine.py:2620` |
| C4 | high | The longest functions are thinly explained relative to their size, and their comments cluster on special cases rather than the overall approach. Comment lines against length: `_status_for_factor` 36 of 512, `build_reader_report` 52 of 587, `author_exercises` 32 of 401, `upgrade` 2 of 401. | `src/learnloop/diagnosis/causal_orchestrator.py:1414`, `src/learnloop/reader/reader_report.py:344`, `src/learnloop/content/authoring/exercise_authoring.py:473`, `src/learnloop/cli/app.py:108` |
| C5 | low | Some comments do what the owner asked for, and are worth keeping as the model: the `mastery.py` docstring on the single seam for item parameters, and the ruling note on why a connection is closed. | `src/learnloop/learner/mastery.py:783`, `src/learnloop/db/connection.py:310` |

No systematic search was done for wrong comments. The count of why-less decisions isn't measured.

## 7. Size, onboarding and what could go (Nov 5 item 7, Nov 8 item 9)

### 7.1 The LOC audit, rerun at this tip

The Oct 15 audit's scripts weren't in its backup directory, and radon and vulture were fetched at the time. I didn't fetch anything, so this is a re-derivation, not the same tool run. Only the sizes below are comparable.

| Measure | Oct 15 | Now | Note |
|---|---:|---:|---|
| `src/learnloop` files | 768 | 1,158 | |
| `src/learnloop` raw lines | 375,115 | about 581,000 | |
| All four Python packages, code lines | about 291,000 | 436,042 | same definition of "code" |
| Functions over 200 lines | 62 | 81 | |
| Root `*_upgrade.py` | 12 (about 20 by the prompt) | 40, 8,215 lines | |
| `mvp-0.N` literals in `src` | about 2,000 | 4,302, in 220 files | |
| Version-gate sites | about 397 | about 401 (regex, narrower than before) | not strictly comparable |
| `*_active(` references | about 245 | 239 | |
| Exact structural clone groups, functions of at least 8 lines | 105 groups, 4,068 redundant lines | 157 groups, 7,696 redundant lines | 107 outside `db/`, 6,336 lines, led by the `*_upgrade.py` modules |
| Tests | 803 files, 252,861 lines | 1,446 files, 456,965 lines | |
| Migrations | 190 files | 237 files, 18,301 lines | |

**Not rerun:** the literal-versus-logic split (string literals and big tables), radon complexity and vulture. Name-based reachability (§7.4) replaces vulture.

**Clones.** The largest group is the upgrade steps: `_activate_as_writer` appears in 19 modules at 50 lines each, `_upgrade` in 21 at 43, `complete_interrupted_activation` in 20 at 43 (`src/learnloop/attempt_content_state_upgrade.py`).

### 7.2 Item 7: the old difficulty scalar

**First, a correction to the brief's list. Two different things share the name, and only one is the scalar.**
- **The scalar to retire** is `PracticeItem.difficulty` and `LearningObject.difficulty_prior` (0 to 1, authored or LLM-estimated): `src/learnloop/vault/models.py:362`.
- **FSRS's D is a different quantity, and it stays.** `practice_item_state.difficulty` (`migrations/001_initial.sql:206`), `activity_card_state.difficulty` (`migrations/075_card_lineage_state.sql:54`) and `family_memory_state.difficulty` (`migrations/168_activity_family_membership.sql:39`) are memory state. RO's rollouts read them (`src/learnloop/router_objective/decision_state.py:109`, `src/learnloop/daily_plan/objective_inputs.py:117`). The docstring at `src/learnloop/learner/mastery.py:766` says the scalar path never consults it.
- **Only one of the four named migrations stores the scalar's kind of number:** `pf_candidates.difficulty` (`migrations/174_pf_generation.sql:36`), from the solver panel.

The empirical-Bayes `item_parameter_state.b_mean` (migration 016) is the scalar's posterior, with the authored value as its prior mean (`src/learnloop/learner/mastery.py:783`).

**Readers:**

| Area | Code | What it does with it |
|---|---|---|
| Mastery and surprise: the map to `b` | `src/learnloop/learner/mastery.py:758`, `:783`, `:772` | `b = scale·(d − 0.5)·2`, clamped. The single seam for the EKF, surprise and prediction |
| Attempt application | `src/learnloop/attempts/attempts.py:4484`, `:4691` | `b`, priming shift, EB update |
| Delayed checks, lessons, probes | `src/learnloop/delayed_checks.py:95`, `src/learnloop/learner/lesson_weight.py:412`, `src/learnloop/daily_plan/lesson_suggestion.py:144`, `src/learnloop/diagnosis/probes.py:322` | `b` for predicted success |
| Field and placement | `src/learnloop/field/outcomes.py:636`, `src/learnloop/field/predictors.py:199`, `src/learnloop/field/probability_states.py:326`, `src/learnloop/field/success_head.py:229` | Baseline signal and exclusion of LLM-estimated values |
| Adaptive difficulty's own signals | `src/learnloop/adaptive_difficulty/forecasters.py:77`, `src/learnloop/adaptive_difficulty/serve_inputs.py:117`, `src/learnloop/adaptive_difficulty/replay.py:239`, `src/learnloop/adaptive_difficulty/data_check.py:120` | **AD reads the scalar as an input signal, `z_llm`.** Retiring it changes AD's replay |
| Goals and exams | `src/learnloop/goals/exam_pool.py:47` | Stratifies the pool |
| Practice index | `src/learnloop/practice_index/retrieval.py:292` | Min and max filters |
| Authoring | `src/learnloop/content/authoring/practice_generation.py:465`, `:1696`, `src/learnloop/content/authoring/rung_variants.py:100`, `src/learnloop/diagnosis/contrast_pairs.py:484`, `src/learnloop/substrate/surface_mint.py:205` | Band prompts, rung axes, mint bounds |
| Probes, re-mint, coherence | `src/learnloop/diagnosis/causal_probe_coherence.py:1352`, `src/learnloop/diagnosis/probe_remint.py:188` | Compared and copied |
| Tutor, teacher | `src/learnloop/tutor/promotions.py:1001`, `src/learnloop/tutor/teach_back.py:929`, `src/learnloop/teacher/actions.py:169`, `src/learnloop/instructional/tools.py:276` | Copied into new items and tools |
| Hash | `src/learnloop/vault/hashes.py:41`, `:55` | **Part of the content hash of an LO and an item.** Removing the field moves hashes unless handled |
| TUI | `src/learnloop/tui/screens/practice.py:557` | Display |
| Sidecar | `src/learnloop_sidecar/handlers/serializers.py:431`, `:556`, `src/learnloop_sidecar/handlers/facets.py:128`, `src/learnloop_sidecar/handlers/knowledge_map.py:170` | DTOs |
| Desktop | `apps/learnloop-tauri/src/screens/KnowledgeMapScreen.tsx:507`, `apps/learnloop-tauri/src/components/InspectorOverlay.tsx:405`, `:651`, `apps/learnloop-tauri/src/api/dto.ts:441` | Inspector and map |
| Phone | none found for the scalar in `apps/learnloop-mobile/src` | |

**Writers:**

| Area | Code |
|---|---|
| Authoring | `src/learnloop/content/authoring/exercise_authoring.py:817`, `src/learnloop/content/authoring/practice_generation.py:1696` |
| PF generation and publish | `src/learnloop/ops/pf_generation.py:487`, `src/learnloop/ops/pf_publish.py:169`, `src/learnloop/db/stores/pf.py:21` |
| Proposals | `src/learnloop/content/proposals/ai_contracts.py:206`, `:548` |
| Teach-back and re-mint | `src/learnloop/tutor/teach_back.py:929`, `src/learnloop/diagnosis/probe_remint.py:188` |
| Vault writer | `src/learnloop/vault/writer.py:89`, `:120` |
| Fixtures | `src/learnloop/curriculum/golden_path_fixture.py:208` |

**Config:** `src/learnloop/config/schema.py:155`, `:156`, `src/learnloop/config/template.py:222`. **Sims:** `src/learnloop/sim/runner.py:841`, `src/learnloop/sim/ad_synthetic.py`. **Tests:** 53 files name `item_irt_params` or `difficulty_from_prior`, and 166 mention the word `difficulty` at all, including FSRS's D and AD.

| ID | Sev | Finding |
|---|---|---|
| X1 | high | The seam is good: `resolve_item_irt_params` is one function. The reach isn't: the scalar also feeds AD's signal, the content hash, exam strata, authoring prompts and index filters. |
| X2 | high | `b` has callers that use `item_irt_params` directly and skip the EB posterior (`src/learnloop/diagnosis/probes.py:322`, `src/learnloop/daily_plan/lesson_suggestion.py:144`), so "the single seam" isn't single. |
| X3 | medium | The word is overloaded across FSRS's D, the scalar, the "desirable difficulty" band and adaptive difficulty, so a grep can't tell them apart. |

### 7.3 Item 9: upgrade modules and version gates. Are they dead?

**Replay doesn't need the upgrade modules. Upgrading an old vault does.** No `*_upgrade` module is imported by `substrate/`, `attempts/` or `db/`. Production importers are `src/learnloop/cli/app.py`, the next chain link, and two callers of `phone_probes_upgrade`.

| Modules | Tags | Needed by a vault at mvp-0.43 or later? |
|---|---|---|
| `src/learnloop/ops/vault_upgrade.py:83` onward | 0.7 to 0.11 | The functions, no. The helpers `UpgradeResult` and `rewrite_algorithm_version`, yes: 40 links import them |
| `src/learnloop/diagnosis/recurrence/upgrade.py:77` and stuck_prompt, daily_plan, probe_tie, learner_text_gap, proof_check, sources, route_rules, voi_stopping, decider, router_staged | 0.12 to 0.23 | No |
| router_mixture, method_explicit | 0.24, 0.25 | No |
| `src/learnloop/regrade_contract_upgrade.py` | 0.26 | The upgrade no; `publish_algorithm_version` yes (21 importers) |
| eligibility_decision, intent, ad_successor, workbench_field_signals, reading_path_plan | 0.27 to 0.32 | No |
| `src/learnloop/claim_fixes_upgrade.py` | 0.33 | The helper `write_activation_journal`, yes (21 importers) |
| replay_ledger, one_ask, superseded_claims, attempt_content_state, cold_retry_reschedule, reader_followups, deliverable_plan, teacher, help_fold_attach, lesson_suggestions | 0.34 to 0.43 | Only if an activation journal names that link. Unverified: a journal sits beside a database I may not open |
| data_capture, followup_serve, interval_factor, router_objective, router_calibration, router_learned_tail, router_followups, teacher_probes, lesson_opportunity, lesson_offers, phone_probes | 0.44 to 0.54 | Yes, until every vault is at the latest tag |

**Coupling any removal must handle:**
- Links import their predecessor at module top, and every version set is built from `SUCCESSOR_CHAIN` (`src/learnloop/algorithm_versions.py:880`). Old tag names are therefore also vocabulary for stored data (`src/learnloop/substrate/recurrence_groups.py:447`).
- Tests start from old tags: `fixtures/migration_head_250/learnloop.toml` is at mvp-0.6, and 30 test files mention it.
- The playbook requires the predecessor-to-successor path to be exercised.
- `src/learnloop/substrate/compat/substrate_cutover.py:3` records a July 19 owner decision that pre-mvp-0.8 vaults aren't migrated, yet `upgrade_to_mvp07` and `upgrade_to_mvp08` remain (`src/learnloop/cli/app.py:303`, `:305`).

**Does replay branch below mvp-0.43? Yes in code, but on the vault's current tag, not the row's tag.** On a vault at mvp-0.43 or later those branches are constant.
- 79 tests use `in` or `not in` on a set whose floor is at or below 0.43, plus a tuple form at `src/learnloop/field/outcomes.py:290`.
- About 40 are pure tag gates, whose else-branch can only run below the floor. Examples: `src/learnloop/substrate/canonical_projection.py:309`, `:652`; `src/learnloop/substrate/rebuild_orchestrator.py:443`; `src/learnloop/attempts/attempts.py:1430`, `:3607`, `:4526`; `src/learnloop/attempts/regrade.py:463`; `src/learnloop/ops/doctor.py:407`; `src/learnloop/learner/mastery.py:203`.
- About 38 pair the tag with a kill switch, so the off-branch stays reachable at any tag (`src/learnloop/daily_plan/engine.py:145`, `src/learnloop/daily_plan/policy.py:42`, `src/learnloop/attempts/attempts.py:1385`). The hand count of these two groups is approximate.
- 11 tests on sets with floors above 0.43 can still be false at 0.43 to 0.53, 6 of them in `src/learnloop/router_objective_switches.py`.
- `src/learnloop/substrate/shadow_rebuild.py:195` accepts `algorithms.algorithm_version=mvp-0.9`, so a shadow rebuild can be forced to a low tag.

**Row readers that stay live whatever the tag** (old rows are read by shape or per-record markers): `src/learnloop/substrate/canonical_projection.py:736`, `src/learnloop/attempts/attempts.py:1522`, `:1529`, `:1540`, `src/learnloop/substrate/recurrence_groups.py:447`, `src/learnloop/db/repositories.py:26949`. Pruning tags doesn't remove these, and `fixtures/mvp017_route_check_replay` pins one.

**Also unknown:** the tags of the retired vaults, since `~/learnloop-retired` wasn't opened. The Nov 3 copies are at mvp-0.43 and migration 238.

### 7.4 Item 9: the deprecated inventory

**Method and limits.**
- Static references only; nothing was executed. "Reach" is whether a learner can get to it.
- "Last" is a `git log -1` at file or directory level.
- Rows were swept with the three landing branches in view: no candidate becomes called on any branch, except that `update_session_checkpoint` wasn't re-checked.
- The name-based reachability scan in Appendix C over-approximates reach (any same-named definition counts), so what it calls unreachable is a strong candidate, and it isn't proof: dynamic dispatch by computed name is missed.

**Premises in the brief that didn't hold.** These are "checked and live":
- `LegacyLanesSource` builds candidates on the objective path (`src/learnloop/daily_plan/lanes.py:477`, `src/learnloop/daily_plan/staged_frame.py:401`).
- `remote/` is the live MCP connector.
- Collections are still in the UI, under Under-the-hood.
- `eval_command` exists twice: `src/learnloop/cli/ad.py:166` is decorated and live; only the `app.py` copy is dead.
- `scheduling/staged_policy`, `router/`, `router_objective/`, `params/`, `ingest/`, `matching/`, `placement/`, `intent/`, `practice_index/`, `hints/`, `workbench/`, `followup_run/`, `followup_serve/`, `one_ask`, Decider tier 1, field predictors and `diagnosis/` subpackages all have live importers.
- There are no orphan screens: every file in `apps/learnloop-tauri/src/screens` has a production importer.

#### DEAD (no production caller; no learner reach)

| Name | Kind | Where | Callers | Replacement | Last | Old vaults or rebuild |
|---|---|---|---|---|---|---|
| `eval_command` (undecorated copy) | utility | `src/learnloop/cli/app.py:4040` | 0 | `cli/field.py`, `cli/evaluation.py` | 0c63463ad4 Oct 12 | no |
| `card_outcome_replay` | module, 261 lines | `src/learnloop/substrate/compat/card_outcome_replay.py:1` | 0; 2 test files | none | b322ef2e9b Aug 20 | not imported by rebuild; ADR-012 froze it |
| `substrate_cutover` | module, 721 lines | `src/learnloop/substrate/compat/substrate_cutover.py:66` | 0 imports; path strings in `src/learnloop/params/parameter_registry.py:107`; 3 test files | canonical substrate | b322ef2e9b Aug 20 | not imported by rebuild; the registry names it |
| `causal_migration` | module, 121 lines | `src/learnloop/diagnosis/causal_migration.py:42` | 0; 1 test file | none named | b322ef2e9b Aug 20 | no import |
| `remediation_intake` | module, 34 lines | `src/learnloop/diagnosis/remediation_intake.py:1` | 0; 1 test file | none named | b322ef2e9b Aug 20 | no import |
| `prequential` | module, 276 lines, "DESCOPED, U-025" | `src/learnloop/scheduling/prequential.py:1` | 0 imports | none | b322ef2e9b Aug 20 | no import |
| `ad_gates` | module, 395 lines | `src/learnloop/sim/ad_gates.py:1` | 0; 1 test file | none named | 04d1b40e19 Nov 6 | no |
| `interval_width_viability` | module, 150 lines | `src/learnloop/sim/interval_width_viability.py:1` | 0; 1 test file | none named | b322ef2e9b Aug 20 | no |
| `progression_policy` | module | `src/learnloop/scheduling/progression_policy.py:1` | every def unreachable by name scan | none | not checked | not checked |
| `client_contract` | module, 74 lines | `src/learnloop_mobile/client_contract.py:1` | 0; 1 test file, may be a pin by design | - | 7b11b0d67c Nov 6 | no |
| Legacy HTTP transport | provider, 248 lines | `src/learnloop/ai/providers/codex_http.py:59` | Refused first at `src/learnloop/ai/client.py:82`; contradicts ADR-011's "retain" | chatgpt_plan | cfa028fa90 Oct 21 | replay doesn't read the provider |
| RPCs with no frontend caller: `curriculum.cover`, `curriculum.cover_job` | RPC | `src/learnloop_sidecar/handlers/correspondents.py:367`, `:413` | tests only | none in UI | 52756865db Nov 4 | no |
| `reader.followups_plan` | RPC | `src/learnloop_sidecar/handlers/reader_followups.py:221` | tests only | background `prepare_followups` | fe0ac0f01b Nov 1 | no |
| `get_practice_coverage` | RPC | `src/learnloop_sidecar/handlers/practice_index.py:144` | tests only | none in UI | 5b52ef1c7d Oct 13 | no |
| `list_vault_epigraphs` | RPC | `src/learnloop_sidecar/handlers/epigraphs.py:19` | tests only | none in UI | ee2e43120c Sep 3 | no |
| `source_outcomes` | RPC | `src/learnloop_sidecar/handlers/ingest.py:1241` | none | CLI `source-outcomes` | e63a81c080 Nov 1 | no |
| `rpc.health` | RPC | `src/learnloop_sidecar/handlers/app.py:96` | none | `rpc.ping` | 8d809ce7aa Oct 26 | no |
| Tauri commands with no TS string: `get_config`, `diagnostic_pack_assemble`, `_admit`, `_review`, `practice_pool_assemble` | command | `src/learnloop_sidecar/handlers/app.py:128`, `apps/learnloop-tauri/src-tauri/src/commands.rs` | 0 | - | - | no |
| Config keys read by nothing: `locks.facet_lock_mass`, `locks.facet_surface_groups` | config | `src/learnloop/config/schema.py:1788`, `:1801`, `:1802` | kept so snapshots don't move | live merge with undo | - | snapshot tripwire only |
| `merge_locked_facets` | config | `src/learnloop/config/schema.py:3639` | doctor warns only | as above | - | snapshot only |
| `discrimination_min`, `discrimination_max`, `plan.pre_questions` | config | `src/learnloop/config/schema.py:152`, `:153`, `:3937` | only the registry (`src/learnloop/params/parameter_registry.py:2904`, `:2957`) | none | - | snapshot only |
| `target_error_type` | config | `src/learnloop/config/schema.py:440`, `src/learnloop/config/template.py:721` | schema and template only | none | - | no |
| 44 client methods with no production TS caller | client API | `apps/learnloop-tauri/src/api/client.ts` | 42 RPCs have no UI path; `clear_session_checkpoint` and `get_attempt` stay allowlisted for the phone | listed below | - | no |

The 44, by name: **Reader (20)** `annotation_history`, `block_health`, `block_original_region` (less certain), `cancel_request`, `create_annotation`, `drain_requests`, `enqueue_request`, `followups`, `link_relation`, `maintain`, `outbox_status`, `prime`, `request_status`, `restore`, `review_source_object`, `routing_prior`, `shrink_envelope`, `span_learning_objects`, `translate_selection`, `workbench.get`. **Others (22, plus the two above):** `blueprint.register`, `compare_sources`, `curriculum.coverage_correct`, `curriculum.path`, `curriculum.ready`, `diagnostic.baseline_enter`, `diagnostic.boundary_view`, `diagnostic.pack_list`, `diagnostic.triage_override`, `export_claims`, `purge_claims`, `get_placement_state`, `get_recent_ingests`, `get_remediation`, `golden_path.boundary_diff`, `practice_pool.admit_surface`, `practice_pool.status`, `record_practice_usage`, `refresh_revision`, `reload_vault`, `set_goal_use_weight`, `start_inventory`. The check matches names as words, so dynamic `api[...]` access would be missed.

**Also dead by Oct 15's and this scan's leaf list** (64 top-level definitions, 614 lines, referenced nowhere): for example `reanchor_selection_to` (`src/learnloop/content/synthesis/source_unit_selection.py:511`), `repair_proposal_item_audit` (`src/learnloop/content/proposals/proposals.py:1300`), `log_affect_tap` (`src/learnloop/substrate/activities.py:980`), `index_legacy_note` (`src/learnloop/content/sources/source_library.py:147`), `_not_implemented_handler` (`src/learnloop/content/pipeline/jobs.py:2949`). A further 98 definitions, 2,754 lines, are referenced only from tests. Appendix C has the wider reachability list.

#### SUPERSEDED (replacement live, still reachable)

| Name | Kind | Where | Replacement | Last | Learner reach | Old vaults or rebuild |
|---|---|---|---|---|---|---|
| Model mixture, `RouterChooser` | feature | `src/learnloop/daily_plan/policy.py:53`, `src/learnloop/daily_plan/router_chooser.py:300`; the objective subclasses it (`src/learnloop/daily_plan/objective_chooser.py:45`) | `ObjectiveChooser` (`src/learnloop/daily_plan/policy.py:110`) | c11b6179c7 Nov 3 | Yes, if `router_objective.enabled=false` or tag below 0.47 | Serves vaults at 0.43 to 0.46; logged rows stay |
| `StagedChooser` (`router.mode="staged"`) | feature | `src/learnloop/daily_plan/policy.py:99` | objective | 49712bc6f1 Oct 25 | By config, or tag below 0.24 | none seen |
| Pre-eligibility cold lane and hold | code path | `src/learnloop/scheduling/scheduler.py:1831`, `:2018` | `serve_eligibility` | not checked | Only with `eligibility.enabled=false` | no |
| Classic shell and practice card | UI switch | `src/learnloop/config/schema.py:4488`, `apps/learnloop-tauri/src/app/shell.ts:5` | simple shell | 725ef0e14d Oct 22 | By `[ui]` config | no; "display and navigation only" |
| Codex provider | provider, 3,441 lines | `src/learnloop/ai/providers/codex.py:1`, `src/learnloop/ai/client.py:76` | chatgpt_plan T1 | 182e5c55a2 Oct 27; lockdown Nov 2 | Only with `ai.agent_harness_opt_in` | Replay reads `grading_source` only; old configs may name it |
| Codex in settings and shell | UI | `apps/learnloop-tauri/src/screens/SettingsScreen.tsx:211`, `apps/learnloop-tauri/src/app/App.tsx:737`, `apps/learnloop-tauri/src/components/CommandPalette.tsx:127` | ChatGPT sign-in, `apps/learnloop-tauri/src/components/ConnectAI.tsx:108` | not checked | Yes: fallback labels, palette | no. Goes with the UX stage's settings cleanup |
| Retired routes `field_llm_probability`, `proof_check` | config, feature | `src/learnloop/config/schema.py:1226`, `src/learnloop/cli/field.py:61` | V1 to V3 arms; own-route grader | not checked | no | Records replay from stored data |

#### LEGACY-ONLY

| Name | Kind | Where | Replacement | Last | Learner reach | Old vaults or rebuild |
|---|---|---|---|---|---|---|
| Golden Path UI | screen | `apps/learnloop-tauri/src/components/ui.tsx:13` (`SHOW_GOLDEN_PATH=false`), `apps/learnloop-tauri/src/app/App.tsx:1471`, `apps/learnloop-tauri/src/screens/GoldenPathScreen.tsx:1` | Today, Reader | c94882abe7 Oct 22 | No: compile-time off | Unknown; run tables not swept |
| Golden family RPCs (39) | RPC | `src/learnloop_sidecar/handlers/golden_path.py:34`, `src/learnloop_sidecar/handlers/ladder.py:63`, `src/learnloop_sidecar/handlers/diagnostic.py:141` | none | 2079aa1eb0 Nov 4 | No | `bridge_active` still routes `golden_path.advance` (`src/learnloop/daily_plan/policy.py:36`) |
| P4 controller, kinship, shadow components | feature | `src/learnloop/scheduling/kinship_feature.py:1` (DESCOPED, U-026), `src/learnloop/scheduling/shadow_components.py:1` (DESCOPED, U-025), `src/learnloop/scheduling/controller_cutover.py:1`, `src/learnloop/scheduling/controller_store.py:104` | staged policy, objective | b322ef2e9b Aug 20 | CLI group `controller` only | Tables retained (§10); production callers not fully traced. Unverified row |
| Pre-canonical projection | code path | `src/learnloop/substrate/canonical_projection.py:311`, `src/learnloop/db/repositories.py:26940` | P0 projection | not checked | No at 0.43 or later | The head fixture at mvp-0.6 uses it; a shadow override can reach it |
| `activity_backfill` | module | `src/learnloop/substrate/rebuild_orchestrator.py:311` | none | b322ef2e9b Aug 20 | Indirect | **Yes: rebuild imports it** |
| `LEGACY_DEFAULT_CONFIG_TEXT` | config, about 718 lines | `src/learnloop/config/template.py:19` | `src/learnloop/config/template.py:739` | not checked | no | No reader in `src`; 2 test files |
| `DEFAULTS_SNAPSHOT_BY_ALGORITHM` | config, about 3,300 lines | `src/learnloop/config/template.py:845` | - | 00d25c2f8d Nov 7 | no | Tripwire only: 0 readers in `src` beyond its own module's helpers, 48 test files. See §9 |
| `CodexConfig` view | config | `src/learnloop/config/compat.py:33` | `[ai.providers]` | 42ab0bc90d Oct 23 | With opt-in | no replay use |
| Normalized-only keys | config | `src/learnloop/config/compat.py:62`, `:113`, `:149`, `:161`, `:171` | canonical keys | same | no | Needed if any vault TOML still sets them. Unknown: live vault configs not opened |
| `lo_mastery_delta` | config | `src/learnloop/config/schema.py:1769` | "legacy compatibility" | - | no | snapshot |
| `experiments/` | package, 36 files, 14,245 raw lines | `src/learnloop/cli/experiments.py:33` | none in serving | 833cedd2ab Oct 26 | CLI only | no |
| `evsi_calibration/` | package, 17 files, 10,548 raw lines | `src/learnloop/cli/evsi.py:18`, `src/learnloop/teacher/report.py:253` | reports only | dc5302d98c Nov 6 | Reports only | no replay import |
| `sim/` | package, 13 files, 5,432 raw lines | `src/learnloop/cli/runtime.py:853`, `src/learnloop/params/sensitivity_certificates.py:126`, `src/learnloop/scheduling/kinship_feature.py:462` | - | 04d1b40e19 Nov 6 | CLI only | no |
| 31 top-level CLI commands with no README, vault-doc, frontend or script reference | CLI | `src/learnloop/cli/app.py:1841` for `trace-evidence`; names below | mostly reports | see `app.py` | If typed; `apps/learnloop-tauri/src/components/CommandPalette.tsx:164` delegates any name | no. Medium confidence: `docs/specs` and `docs/reviews` weren't counted, and some are the owner's report tools |
| Kill switches for tags at or below 0.43, 27 named | config | `src/learnloop/algorithm_versions.py:679` and the comment lines naming them | - | - | By config | Each off-branch keeps predecessor code alive at any tag. `replay.ledger_bounded` affects rebuild results (`src/learnloop/attempts/attempts.py:1378`). Which are "fully landed" is unverified |

The 31: `backfill-originals`, `select-units`, `maintenance-feed`, `reentry-summary`, `source-outcomes`, `resolve-conflict`, `synthesis-eval`, `repair-extraction`, `independence-audit`, `trace-evidence`, `facet-candidates`, `resolve-error`, `debug-advance`, `recall-calibration`, `misconception-gate-backfill`, `exam-calibration`, `probe-coverage`, `probe-instances`, `diagnostic-augmentation`, `persona-realism`, `diagnostic-eval`, `probe-audit`, `graph-identifiability`, `residual-diagnostics`, `probe-regrade`, `taxonomy-regrade-check`, `causal-selection-readiness`, `build-causal-taxonomy`, `correct-measurement`, `probe-families`, `probe-gate`.

The 27 switches: `placement.enabled`, `recurrence.enabled`, `stuck_prompt.enabled`, `plan.enabled`, `router.probe_tie_admission`, `learner_text_gaps.sooner_check_enabled`, `proof_check.enabled`, `source_service.source_first_needs`, `voi_stopping.enabled`, `diagnosis.probe_lane_reads_diagnosis`, `router.enabled`, `router.restraint`, `required_method.enabled`, `eligibility.enabled`, `intent.enabled`, `workbench.field_signals_enabled`, `reading_paths.plan_uses_path`, `mastery.claim_fixes_enabled`, `replay.ledger_bounded`, `ask.cold_help_converts`, `practice.attempt_keeps_content_state`, `practice.reschedule_cold_after_assist`, `followups.enabled`, `curriculum.plan_uses_path`, `teacher.enabled`, `hints.fold_follows_attach`, `diagnosis.split_enabled`.

#### OWNER-CALL (a learner reaches it; a replacement may not cover the journey)

| Name | Kind | Where | Replacement | Last | Why it's the owner's call |
|---|---|---|---|---|---|
| Textual TUI | feature, 11 files, 2,471 raw lines; a hard dependency | `src/learnloop/cli/app.py:4033`, `src/learnloop/app_launch.py:8`, `pyproject.toml:14` | Desktop, phone | 3c5f0cbca8 Oct 17 | Documented at `README.md:312`. Not at parity: "keeps the open queue: no plan view" (`pyproject.toml:425`) |
| Collections, source sets | feature | `src/learnloop/cli/source_set.py:5`, `apps/learnloop-tauri/src/components/AddToCollection.tsx:39`, `apps/learnloop-tauri/src/screens/IngestScreen.tsx:1066`, `src/learnloop_sidecar/handlers/ingest.py:530` | "Add" | e63a81c080 Nov 1 | UI copy says synthesis reads collections, and source-set rows are loaded |
| `projects/` | feature, 10 files, 5,300 raw lines | `src/learnloop/cli/project.py:24`, `src/learnloop/ops/startup.py:13`, `src/learnloop_sidecar/handlers/queue.py:22` | none | 12b1ea122b Oct 13 | CLI and a queue sweep; its store's independence is unverified |

**Counts:** 23 DEAD rows, plus 44 client methods and 64 leaf definitions; 7 SUPERSEDED; 14 LEGACY-ONLY; 3 OWNER-CALL. Rows that aren't dead carry a learner-reach or rebuild note. **Not swept:** `calibration_bundles/`, which has no `.py` reference in `src`, `scripts` or `tests`, and whose purpose wasn't read.

### 7.5 What a new engineer must learn today

Vault, observations versus projections, table roles, the successor chain, kill switches, defaults snapshots, the migration head fixture, AD's guard, blind grading, held grades, the plan engine and its boundary, the router's two policies, the mix and its logged propensities, FSRS and the rollouts' memory, the Decider, spend admission, protection and its five seams, and the three frontends.

| ID | Sev | Finding |
|---|---|---|
| N1 | high | The concept count is itself a cost. Several concepts exist only for history (successor chain below the owner's oldest tag, snapshots, compat roles). |
| N2 | medium | CLAUDE.md's suite time is stale: it says about 17 minutes serial, while the Nov 7 gate took 59 minutes at `-n 8` (§11). |

## 8. The documentation vault (input to later stages; no vault notes were written)

Vault notes are cited as `docs/learnloop-architecture-vault/...:line`. In this section's tables, "Note" paths are relative to that folder and `AV` means `src/learnloop/algorithm_versions.py`.

**Validators, run read-only at this tip:**

| Validator | Result |
|---|---|
| `validate_vault.py` | Passed: 2,244 notes, 56,963 links, 7,982 source paths |
| `db_validate_reference.py` | `errors: []` |
| `desktop_validate.py` | Passed: 324 of 324 TS and TSX, 6 of 6 Rust. It failed at 214c206ff1 (a missing `BookPassage.md`, stale workbench notes), and router speed 2's landing fixed that |
| `module_validate.py` | Passed: 1,251 of 1,251 modules |

**The validators pass while the hand-written notes are badly behind. They check links and coverage, not truth. Sev: high.**

**Stamps.** The head is mvp-0.54 and migration 250 (`src/learnloop/algorithm_versions.py:1187`).

| source_commit (date) | Commits behind | Stamp | Notes |
|---|---:|---|---|
| 62fd1f6404 (Aug 17) | about 3,844 | mvp-0.9 | Architecture Overview, Adapter, Content Pipeline, Package Boundaries, Vault Lifecycle; most Concepts; most Workflows; all Examples; Architecture, Developer, User Journey Maps; ADR-001 to 012; Design Decision Index; Refactor Status; Glossary; AI Operation Registry |
| 0622ea164f (Sep 23) | about 3,685 | mvp-0.9 | Home, AI Architecture, Desktop, Privacy, Testing; Attempt Processing, Learning System, Scheduling; Data and State Map; ADR-014 |
| fc697aab4b (Oct 13) | about 2,678 | mvp-0.27 | LearnLoop Pipeline Map, though its body was last changed Nov 2 |

`src/learnloop_mobile` and `src/learnloop_mcp` have no module notes, and `apps/learnloop-mobile` has no desktop notes.

### 8.1 Removed, renamed or superseded behaviour (the most costly)

| Note | Line | Claim | Evidence | Sev |
|---|---|---|---|---|
| Architecture Overview | 28 | A deterministic controller chooses; AI doesn't own policy | `src/learnloop/algorithm_versions.py:765`: a learned mix with an LLM policy | high |
| Architecture Overview | 68 | Layer table lacks daily_plan, router, router_objective, placement, adaptive_difficulty, teacher, followup_serve, figures, mobile, MCP | `pyproject.toml:706`, `:714` | high |
| AI Architecture | 93 | Four provider types | `src/learnloop/config/schema.py:1059`: eight | high |
| Content Pipeline; Import Canonical Sources; Privacy and Trust | 69; 81; 59 | PDFs are local Marker or pypdf | `src/learnloop/ingest/extractors/__init__.py:84`, `src/learnloop/ingest/extractors/glm_ocr.py:190`: `auto` uses a hosted service when a key is set. **A privacy statement is wrong** | high |
| State and Persistence; Data and State Map; ADR-003; Rebuild | 42, 52; 30, 61; 36; 87 | 259 tables, 10 derived | 395 and 26: `docs/learnloop-architecture-vault/Reference/Database/Database Catalog.md:30` | high |
| Algorithm Versions; Version Registry | 58; 32 | Ends at mvp-0.34; mvp-0.27 | `src/learnloop/algorithm_versions.py:1187` | high |
| Learning System; Scheduling and Selection; Attempt Processing; Diagnosis | 28; 28; 39; 34 | Deterministic selection; slate as the whole story; joint grading; burden-only stopping | `src/learnloop/algorithm_versions.py:26`, `:241`, `:298`, `:771` | high |
| Start a Learning Cycle; First Learning Session | 57; 81 | Choose energy and sleep, inspect the queue | `apps/learnloop-tauri/src/screens/StartScreen.tsx:1776`, `apps/learnloop-tauri/src/screens/TodayScreen.tsx:550` | high |
| Process Model Output | 39 | No blind-grading branch | `src/learnloop/algorithm_versions.py:26` | high |
| Adapter Architecture | 23, 33 | Three adapters that never import one another | `src/learnloop_mobile/runtime.py:208` | medium |
| Reader Tutor | 29 | `tutor_qa.reader_enabled = false` | `src/learnloop/config/schema.py:586`: `True` | medium |
| Reader to Practice | 36 | No `learnloop reader` CLI | `src/learnloop/cli/reader.py:1` | medium |
| Inspect Persistent State | 67 | Migration head 156 | `migrations/250_help_assists_phone_surface.sql:1` | medium |
| Initialize a Vault | 31, 97 | New vault at mvp-0.9; latest mvp-0.12 | `src/learnloop/algorithm_versions.py:1187` | medium |

### 8.2 Major features with no explanatory note

| Feature | Hand-written coverage | Sev |
|---|---|---|
| Router objective RO0-RO6 | **None** (`src/learnloop/router_objective/`) | high |
| Teacher TE0-TE3 | **None** (`src/learnloop/teacher/`) | high |
| Figures, Show me | **None** | high |
| Follow-up serve FG1 | **None** | high |
| Data capture | **None** | medium |
| Router speed | **None** | low |
| Phone | Pipeline Map:324 only, and it says capture only, which is wrong (`src/learnloop_mobile/allowlist.py:123`) | high |
| MCP frontend, `learner_protection` | One row in Adapter; the Pipeline Map | high |
| Adaptive difficulty | Algorithm Versions:54, a passing mention | high |
| Decider, chatgpt_plan, GLM-OCR, held grades, exam-protection identity | The Pipeline Map only | high |
| Re-read safety, span aliases, method-explicit, Reader workbench, S0 | Short mentions | medium |
| Plan determinism | Pipeline Map:231 | low |
| Coordinated migrations | **Covered** (State and Persistence:72, ADR-008) | none |

### 8.3 Maps against the data flow in §2

| Note | Line | Claim | Contradicting code | Sev |
|---|---|---|---|---|
| Architecture Map | 25, 27 | Adapters are CLI, TUI, sidecar; domains stop at August's | `pyproject.toml:706` | high |
| Developer Map | 27 | Next-item policy lives in `scheduling/` | `src/learnloop/daily_plan/objective_chooser.py:1173` | high |
| Pipeline Map | 8, 105, 348 | Latest is mvp-0.27 | `src/learnloop/algorithm_versions.py:1187` | high |
| Pipeline Map | 117, 213, 230 | Next block drawn from rule, Decider and LLM | `src/learnloop/router_objective/mix.py:38`: LLM and numeric, Decider as advice | high |
| Pipeline Map | 116, 211 | Finite minute budget | `src/learnloop/algorithm_versions.py:762` | high |
| Pipeline Map | 130, 302, 324 | Mobile is a capture host | `src/learnloop_mobile/host.py:1` | high |
| Pipeline Map | 118 | No lessons or follow-up generation at serve | `src/learnloop/algorithm_versions.py:657`, `:737` | high |
| System canvas | 3 | 14 nodes; no pipeline, router, plan, mobile or MCP; advertised at Home:23 | `src/learnloop/algorithm_versions.py:771` | high |
| Data and State Map | 61 | Head 165 | Migration 250 | high |
| User Journey Map | 25 | Init, import, build, learn | Reader, plan, phone and chat doors absent | medium |

### 8.4 ADRs

| ADR | Finding | Sev |
|---|---|---|
| ADR-014, 015 | Correctly marked in frontmatter, callout and index | none |
| ADR-005 | "Adapters don't import one another" was amended in code with no note (`src/learnloop_mobile/runtime.py:208`) | high |
| ADR-003 | Rule holds; "ten tables" is wrong | medium |
| ADR-011 | Says retain a narrow HTTP capability. The transport is refused at every entry (`src/learnloop/ai/client.py:82`). The code is dead and the ADR doesn't say so | medium |
| ADR-002, 013 | Decider's typed choices and GLM-OCR have no decision record | medium |
| ADR-001, 008, 009 | Stale counts or lists; principles intact | low |
| ADR-006, 010, 012 | Not superseded. ADR-010's production-telemetry report was never written, and §10's copies give that evidence now | low |
| Design Decision Index | Reflects only ADR-014's supersession. No ADR exists for router mixture or objective, teacher, phone, MCP, S0 or GLM-OCR | medium |

### 8.5 Examples, orphans, contradictions

**Examples.** Every `learnloop` subcommand and flag in `Examples/*.md` still exists (read, not run). Stale preconditions:
- First Vault Walkthrough:32 and 105, Deliberate Canonical Import:26, and Import Canonical Sources:48 use `research_on_learning.md` at the repo root, which is now at `docs/specs/research_on_learning.md`, so **the Examples route fails at the first import (high)**.
- Recovery and Rebuild Drill:28 and others assume an mvp-0.9 vault.
- Manual Attempt:28 needs owner-lane copies.

**Orphans.** None with zero inbound links, in the hand-written scope. These have only one link: ADR-004, 011, 013 and 016 (only the Index links ADR-016, not Learning System, Attempt Processing or Diagnosis), AI Operation Registry, Glossary, Documentation Dashboard, Status Legend, Tag Taxonomy.

**Contradictions between notes.**
- Latest algorithm: `mvp-0.12` (Initialize:97), `mvp-0.27` (Version Registry:32), `mvp-0.34` (Algorithm Versions:58).
- Migration head: 156, 165, 202, 250.
- Derived tables: 10 in four notes, 26 in the catalog.
- PDF extraction: Content Pipeline against Pipeline Map:148.
- Reader default and opt-out: Reader Tutor:29 and Reader to Practice:68 against Pipeline Map:191.
- CLI help surfaces: 168 and 171.

**First hop.** Home to Architecture Overview orients a new engineer to the August architecture. Home:21 and Overview:28 say deterministic policy picks the next action. Home:27 and Developer Map:27 send readers to Scheduling and Selection, which never mentions the plan or router. The Pipeline Map, the most current note, is one row on Home. The doors and packages from §1 are absent.

**Not checked:** generated note content; Desktop Architecture beyond part of it; the later parts of several workflows; Example runtime output (JSON shapes, `jq` keys, SQL columns); whether `intent_planner` is still shadow-only. The vault agent's line numbers in notes were read at 214c206ff1; router speed 2's landing changed one hand-written note and generated notes, so a few may be off by a little.

## 9. What a pipeline change costs (Nov 8 item 10)

Counted from git, comparing the commits named. **Digest and pin churn is separated from real edits.**

- "pin" is a test file where at least 90% of changed lines match a pin pattern (digest, hash, version tag, head number, `successor`). It's a heuristic and it undercounts: the 40 s test edits restore a value before a digest comparison, so they don't match and I counted them by hand.
- "snap" is `config/template.py`, nearly all snapshot digests.
- "gen" is the generated vault Reference; much of it is provenance stamps.

### 9.1 Single changes

| Change | Kind | Behaviour lines | Src | Snap | Tests real | Tests pin | Other |
|---|---|---|---:|---:|---:|---:|---|
| **40 s router timeout**, `8ea11df389` + `6d9be191ca` | threshold | **1** (`src/learnloop/config/schema.py:4134`) | 2 (one is a docstring) | 92 lines: 46 digests | 1 literal | **11 tests** restoring 8.0 before a frozen digest | 1 generated note, 1 spec, plus the new spec |
| Numeric seed, `bc1ceab278` | seed | small | 2 | 0 | not counted | 0 | |
| One-constant successor, `8d0cf22296` (TE3b (0)) | new tag | "one constant" | 9 | 101 lines | 12 | **36** | |
| IH5 failure share, `d602dc8472` | mixing rule | 47 lines in `mix.py` | 13 | 99 lines | 14 | **36** | |
| Prompt fix, `214c206ff1` | prompt | 128 lines | 6 | 0 | 1 | later: **1 golden**, `1975294a0c`. The full-suite gate caught it after the fix was on main ("main's own tip fails it", `docs/reviews/router-speed2.md:426`) | |
| New input to model contexts, `4d995af688` (TE0) | signal | 565 lines | 11, across hints, tutor, diagnosis, router | 0 | not split | 0 | |
| Feature indicator, `6681b88cea` (TE3b (3)) | signal | 130 lines | 5 | 0 | 1 | 0 | |
| Merge pins, `dab159b1d1` | pure plumbing | 0 | 0 | 0 | 1 | **13** ("the pins the merge's first pass missed (14 tests)") | |
| A new table, `53222a3c7f` + `2437f516e5` (IH3) | new table | about 830 lines | 10 | 95 lines | 2 | **68** | fixtures renamed and rebuilt: **48 files, 4,510 lines**; **481 generated notes**; 15 frontend files |

**For a one-line default:** 1 behaviour line, 46 digests, 12 test files. That's the owner's example, confirmed. The tests do `dumped["router"]["timeout_seconds"] = 8.0` before hashing, so each frozen test accumulates a growing preamble that undoes later defaults (`IH:tests/test_ro4_successor.py:90`).

**Why it happens.** 49 test files reference a frozen snapshot or digest. `DEFAULTS_SNAPSHOT_BY_ALGORITHM` holds one digest per tag (`src/learnloop/config/template.py:845`), and any default change moves all of them. A successor's tag literal lives in `tests/test_mvp024_upgrade.py` and others: 193 test files mention a recent tag or `LATEST`, and 70 files name the fixture head's path, while CLAUDE.md says 5 such paths. The bare number `250` appears 102 times in 51 test files, though not all of those are the head.

**Who else is hit.** Each merged branch inherits this: router speed 2 merged main and needed its own golden re-record, and TE3a's merge needed `dab159b1d1`.

### 9.2 Whole stages

| Stage | Files | Src | Frontend | Migr. | Tests real | Tests pin | Fixtures | Vault gen | Docs | Src lines |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RO5 (`5b2b56b0de`..`51fb2f745f`) | 655 | 32 | 0 | 0 | 19 | 35 | 0 | 562 | 5 | 3,979 |
| RO6 (`51fb2f745f`..`e7a7d7734f`) | 606 | 19 | 0 | 0 | 20 | 35 | 0 | 526 | 4 | 3,174 |
| TE2 (`516db1d862`..`23182034c6`) | 821 | 41 | 13 | 1 | 17 | 84 | 48 | 608 | 6 | 2,654 |
| TE3a (`64f7d1dc86`..`8b0738499d`) | 751 | 31 | 0 | 1 | 27 | 75 | 48 | 562 | 6 | 1,156 |
| Router speed 1 (`23ce859c16`..`8853cd6b74`) | 540 | 8 | 0 | 0 | 6 | 3 | 0 | 519 | 3 | 454 |
| Phone V1 (`1c12763372`..`23ce859c16`) | 103 | 7 | 66 | 0 | 2 | 0 | 0 | 25 | 3 | 270 |
| Phone V2 (`8853cd6b74`..`14b2ed09ab`) | 136 | 24 | 41 | 0 | 13 | 1 | 0 | 53 | 4 | 1,034 |
| TE3b (`14b2ed09ab`..`e9ceaf8d44`) | 686 | 40 | 8 | 0 | 19 | 36 | 0 | 576 | 5 | 1,884 |
| Phone V3 (`e9ceaf8d44`..`ccb6573987`) | 703 | 25 | 11 | 1 | 24 | 86 | 48 | 499 | 6 | 861 |
| Router speed 2 (`214c206ff1`..`a525dbcef4`) | 615 | 9 | 0 | 0 | 4 | 4 | 0 | 593 | 4 | 738 |
| Phone V4 (`5fe3a22558`..`phone/v4-reader`) | 150 | 22 | 51 | 0 | 9 | 1 | 0 | 61 | 4 | 1,857 |
| IH, so far (`880e76deca`..`instruct/handoff`) | 711 | 39 | 23 | 1 | 21 | 87 | 48 | 481 | 8 | 2,512 |

**Router speed 2 is the clearest case: 9 source files and 615 files in all, 593 of them generated vault notes, with no version change and no migration.** The landing commits say "provenance-only churn left out", which means the churn is frequent enough to need managing.

### 9.3 By kind of change

| Change | Today | Plumbing that isn't the change |
|---|---|---|
| A threshold or default | 1 line | 46 digests, 12 test files, a generated note |
| A new switch | `schema.py`, `template.py`, `router_objective_switches.py`, `parameter_registry.py`; the reference's leaf count (`bf84a858c9` edits "the two prose leaf counts 1182 -> 1183") | Digests; if a serving switch, RO6's generator payload and a seed exclusion (B8) |
| A prompt | 1 file plus a version bump | A golden for each switch-off parity test |
| A new signal to a model | A reader, then each context builder separately: 11 files for TE0 | Input hash changes where inputs are hashed. Protection lists if it reads a guarded table |
| A new table | Migration, roles, AD's two lists, store | The fixture renamed (48 files), 68 pinned tests, 481 generated notes |
| A new algorithm tag | Constant, upgrade module, CLI dispatch, sidecar context, journal | 36 pinned tests, 46 plus one digests |
| A new step in a pipeline | FG1 and IH2 each span many commits; not reduced to one number here | |
| A model route | **Not measured.** `src/learnloop/ai/routing.py:34` holds 74 task names and `:178` 90 operations. No recent commit changes one route alone, so I can't count it from history. The plan-first transport changed routes wholesale (`b60e146f05`, 87 files) | |

### Findings

| ID | Sev | Finding |
|---|---|---|
| H1 | high | Frozen digests make a one-line default a 20-file change, and this cost recurs at each merge, not only at the change. |
| H2 | high | Migration and successor bookkeeping is the largest single share of many stages: the head fixture (48 files per migration), 36 to 87 pinned test files and hundreds of generated notes. Router speed 2's review needs reading past 593 generated files. |
| H3 | medium | A new model input has no common path: each context builder is separate (`src/learnloop/diagnosis/split/context.py`, `src/learnloop/tutor/tutor_qa.py:2090`, `src/learnloop/daily_plan/router_card.py:551`, `src/learnloop/hints/service.py:775`). |
| H4 | medium | Goldens and digests detect a change after the fact, sometimes only at someone else's landing gate. |

## 10. The table inventory (Nov 8 item 12)

**This is a list for the owner's review. It proposes nothing to drop.**

Every table across `src/learnloop/db/table_roles.py` and the migrations is in Appendix B: its role class, first writer and reader with file:line, write and read caller packages, its replayer or upgrade, doctor or sync mention, the feature from its first migration, and a class.

**Private data isn't here.** Per-vault row counts, newest dates and database sizes are in `fixtures-local/refactor-map/table-counts.md`, which is gitignored and not committed. **Those copies are from Nov 3 (mvp-0.43, migration 238), so anything newer can't appear in them.**

**Method and limits.**
- Static AST scan of every string constant and f-string in `src`, with table-name constants resolved. Writers are `INSERT`, `REPLACE`, `UPDATE` and `DELETE`, or a mention in a `write`-named function.
- Callers are found by the name of the function holding the SQL. Generic names like `snapshot` are shown as `(generic-name)`, and the caller sets over-approximate.
- `(o)` caveat from §4 applies: classes were reviewed by hand only for the non-live rows. A "live" class means a production path can write it, not that it's used.
- Sync column: `state_sync.py` and files with `sync` in their path. I found no separate sync layer for tables (S0's sync is out of the schema's scope here).

**Counts.** 396 tables with a role, including IH3's `router_learner_preferences`. A further 53 names appear only as transient migration rebuilds (`*_new`, `*__NNN`) or were dropped; they aren't tables at head. FTS shadow tables are handled separately (`src/learnloop/db/table_roles.py:728`).

| Class | Tables |
|---|---:|
| live | 345 |
| derived and rebuildable | 26 |
| retired but still read | 24 |
| dead | 1 |

| Role | live | derived | retired | dead |
|---|---:|---:|---:|---:|
| RAW_LEDGER (166) | 155 | | 11 | |
| WORKFLOW (99) | 98 | | 1 | |
| RECEIPT (95) | 90 | | 5 | |
| DERIVED (26) | | 26 | | |
| COMPAT (10) | 2 | | 7 | 1 |

**Retired but still read (24), and why:**

| Group | Tables | Why |
|---|---|---|
| Role says COMPAT | `elicitation_events`, `evidence_facet_recall_state`, `facet_uncertainty`, `learner_state_beliefs`, `lo_probe_state`, `source_exam_profiles`, `source_locator_schemes` | Frozen seams. `facet_uncertainty` and `evidence_facet_recall_state` are written only on non-canonical vaults (`src/learnloop/attempts/attempts.py:3322`). The last two, with `learner_theta`, are doctor's deprecated list (`src/learnloop/ops/doctor.py:1218`). |
| P4 controller and kinship (DESCOPED) | `controller_constraint_manifests`, `controller_outcome_windows`, `controller_prequential_reports`, `familiarity_kernel_events`, `familiarity_kernel_features`, `familiarity_kernel_models`, `shadow_component_events`, `soft_kinship_features` | Writers unreachable by name scan; tests only (§7.4) |
| Authoring and pattern substrate | `activity_card_authoring`, `activity_family_authoring`, `activity_surface_authoring`, `activity_pattern_versions`, `activity_patterns` | Same |
| Others | `angle_inventories`, `causal_mechanism_taxonomy_retirements`, `family_evidence_cap_policies`, `progression_policy_versions` | Same |

**Dead (1):** `learner_theta`. It has no reader or writer in code except the deprecated-table checks (`src/learnloop/ops/doctor.py:1218`, `src/learnloop/ops/debug_time.py`).

**A class alone doesn't make these safe to drop:** rows can carry history. Each needs the checks in item 12, and ADR-010's gate applies to the doctor list.

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| T1 | high | Role and reality disagree for the two most important COMPAT tables. `practice_item_state` holds the live FSRS memory state that attempts write and the objective reads. `hypothesis_sets` holds the locked hypothesis sets the live probe paths write. "COMPAT" tells a reader these are frozen. | `src/learnloop/db/table_roles.py:489`, `:329`; `src/learnloop/daily_plan/objective_inputs.py:117`, `src/learnloop/diagnosis/causal_probe_coherence.py:836` |
| T2 | medium | Many live-class tables have no reader in production code, so they're write-only records. Appendix B flags them as `readers have no production caller`: `card_lineage_edges`, `controller_candidates`, `diagnostic_pack_events`, `goal_contract_drafts`, `measurement_events`, `probe_family_lifecycle_events`, `retirement_records`. Some are audit by design. | Appendix B |
| T3 | medium | Whole families serve features the deprecated inventory lists: the golden-path ladder (`p2_ladder_policies`, `p2_ladder_stages`, seeded by migration), diagnostic packs, surface mint, and the controller's remaining live tables. They stay "live" by code because a golden-path or `bridge_active` path can still reach them. | `src/learnloop/daily_plan/policy.py:36` |
| T4 | low | 396 tables is itself the understanding cost. AD's guard register classifies about 156 of them again, so those carry a second classification. | `src/learnloop/adaptive_difficulty/protected_tables.py:33` |

**Not done:** a per-table check of whether code readers tolerate a table's absence (the `_table(...)` and `table_present` guards suggest many do), and row-level history value. Only the `probability` copy was upgraded (to main's migration 250), to note migrated-but-empty; that list is in the private file.

## 11. Timing baseline (Nov 8 item 13)

**Source:** per-test durations in one existing junit file, the Nov 7 gate on router speed 2's branch at `5a9dae936f` (`gate_full.xml` in the landing's scratch). The suite wasn't run for this map, as instructed. Its command: `pytest -n 8 --dist worksteal` in a 10 GB scope, with the full-suite lock held.

| Measure | Value |
|---|---:|
| Wall clock | 3,562.5 s (59:22) |
| Test seconds (sum of per-test times) | 27,650 s |
| Tests | 30,327: 30,189 passed, 91 skipped, 47 xfailed |
| Median test | 0.039 s |
| 90th percentile | 1.85 s |
| 99th percentile | 9.5 s |
| Tests under 0.1 s | 16,022 |
| Top 10 tests | 1,869 s, 6.8% of test seconds |
| Top 100 | 8,016 s, 29% |
| Top 500 | 12,425 s, 45% |
| Top 1,000 | 14,893 s, 54% |

Sum divided by 8 workers is 3,456 s, close to the wall clock, so the wall clock is dominated by test CPU rather than idle workers.

A later gate log on the merged tree (Nov 8, `gate2_full.log`) reports about the same: 57:32 at `-n 8`. I read only its summary. No serial or durability baseline exists in these files beyond a durability count, so **item 13's serial, `-n 8` and durability comparison has a baseline only for `-n 8`**. CLAUDE.md's "about 17 minutes" doesn't match.

**Where the time goes, by rough filename family (these overlap):**

| Family | Test seconds | Share |
|---|---:|---:|
| `*successor*`, `*upgrade*` | 4,364 | 16% |
| Reader, `rw*` | 2,589 | 9% |
| Router, `ro*`, objective | 2,014 | 7% |
| AD | 1,957 | 7% |
| Sim, simulation | 1,316 | 5% |
| Mobile | 366 | 1% |

**Slowest files:**

| File | Seconds | Tests |
|---|---:|---:|
| `test_ad23_sim` | 734 | 56 |
| `test_recurrence_commands` | 699 | 47 |
| `test_reader_rw1c_review` | 553 | 342 |
| `test_e1_harness` | 552 | 13 |
| `test_rofu_weeks` | 467 | 2 |
| `test_followup_next_matrix` | 451 | 71 |
| `test_ad_protected_readings` | 432 | 154 |
| `test_mvp024_upgrade` | 404 | 14 |
| `test_mvp023_upgrade` | 385 | 13 |
| `test_method_explicit_upgrade` | 385 | 12 |
| `test_mvp022_upgrade` | 369 | 12 |
| `test_mvp020_upgrade` | 346 | 11 |
| `test_ro6_tail_data` | 340 | 7 |

**Slowest tests:** `test_two_weeks_before_and_after_the_batch` 282 s and 185 s, `test_a_few_weeks_on_a_copy_shaped_synthetic_vault` 227 s, and a run of tests that walk the chain from an old tag: `test_upgrade_to_mvp042_works_from_supported_versions[mvp-0.9]` 184 s, `...mvp039...` 163 s, `...mvp040...` 151 s, `...mvp037...` 147 s, `...mvp035...` 144 s, `...mvp036...` 140 s, `...mvp038...` 138 s. Each new successor tends to add another such test, and each walks a longer chain.

| ID | Sev | Finding |
|---|---|---|
| Z1 | high | The successor chain is the largest single family, and its worst tests grow with each new tag: walking from mvp-0.9 re-runs every link. |
| Z2 | medium | Half of test time is in about 1,000 of 30,327 tests, while over half of the tests take under 0.1 s. Any speed-up is in a few hundred tests and fixtures. |
| Z3 | low | junit attributes setup to a test, so `basic_vault_template`'s cost and `backup_database`'s synchronous writes (the owner's prior) can't be separated from this file. It needs part B2's profiling. |

## 12. What depends on the landing stages, and what isn't built

**Base.** Citations are against `refactor/map`, which was fast-forwarded to main `a525dbcef4` (router speed 2 landed) with this file as its only change. Phone V4 and instruct/handoff are read as diffs: `V4:` and `IH:` citations are in those branches' own files.

| Stage | Changes the map how | Depends on it |
|---|---|---|
| Router speed 2 (landed) | Held reading map within one job; pooled connections; `SEED_NEUTRAL_SWITCHES` | D4, D5, B8, F2 |
| Phone V4 (`phone/v4-reader`) | Phone Reader, `src/learnloop_mobile/media.py` on that branch, device eligibility with media, `reader_dialogue.ask_provenance`, no migration | B3, §2.5 |
| Instruct hand-off (`instruct/handoff`, WIP) | 40 s default, mvp-0.55, IH5's failure share, IH2's contest, IH3's learner action, migration 251, prefetch | §2.2, §3.3 mixing row, §4.1 |

**A conflict to resolve at IH's landing.** Router speed 2 made `numeric_seed` a required keyword on `_start_objective` and `seed` a required keyword on `_mixed` (`src/learnloop/daily_plan/objective_chooser.py:1304`, `:1576`). `instruct/handoff` adds calls that pass neither: `IH:src/learnloop/daily_plan/objective_chooser.py:1231` and `IH:src/learnloop/daily_plan/objective_chooser.py:1582`. **The numeric seed on those paths after landing isn't determined by either branch, so §2.2 can't be mapped there.** Sev: medium.

**Not built; where the map would change:**

| Stage | Where |
|---|---|
| Phone V5-V7 | §2.5, B3 (more phone surfaces), §8.2 |
| MCP C1b, C2 | §2.5 (chat writes and practice would end MCP's read-mostly stance), `learner_protection`'s role, §4 (a learner action with no plan decision) |
| TE4 | §3.3's add-an-action row, §4.1's teacher rows |

## 13. Open findings carried in, and what's unverified

**Carried in (owner's call):**
- **AD eta grows without an upper bound.** `η` grows by `γ` on every practice opportunity with no ceiling (`docs/reviews/router-followups-codex-review.md:145`, `:191`). Not re-derived here.
- **Router speed's unmet target:** D4, with R4's cost at D5.

**Unverified or incomplete:**
- Every "(o)" row in §4.1 was read by outline or grep only: grading, teacher, ingest, Reader retrieval internals, the alias store.
- The four real cases are from code, not rows (§4.5). The 12-skips explanation is a hypothesis.
- Deep, wide and shallow are size heuristics, not readings of 1,268 modules.
- Reachability is name-based. Dynamic dispatch can hide a caller, and same-named functions can hide a dead one.
- The table scan misses SQL built from variables other than module constants, and caller packages over-approximate.
- Vault owners' retired vault tags, live `learnloop.toml` contents and activation journals weren't opened, as the rules require, so "still needed by old vaults" rests on the Nov 3 copies and code.
- §7.1's literal split, radon and vulture weren't rerun. §6 is counts and a sample.
- A model route's change cost isn't measured (§9.3).
- Line numbers cited from the subagent sweeps were machine-checked to exist, and their text logged. I read a sample, not all. Lines in files the merge changed were re-derived with a diff and checked.
- No test was run for this map. No model was called.

## Appendix A: every module, classified

`~.` is `learnloop.`. Classes are the size heuristic from §1 (`s:` is shallow). Generated at this tip by an AST sweep.

| module | raw | code | public | fan-in | fan-out | longest fn | class |
|---|---:|---:|---:|---:|---:|---:|---|
| learnloop | 4 | 1 | 0 | 0 | 0 | 0 | init/re-export |
| ~.__main__ | 6 | 3 | 0 | 0 | 1 | 0 | s:thin |
| ~.activation_journal | 163 | 65 | 9 | 28 | 0 | 15 | medium |
| ~.ad_successor_upgrade | 120 | 63 | 1 | 2 | 11 | 47 | s:re-export |
| ~.adaptive_difficulty | 18 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.adaptive_difficulty.arms | 247 | 167 | 3 | 2 | 9 | 41 | medium |
| ~.adaptive_difficulty.backfill | 278 | 191 | 2 | 1 | 16 | 70 | medium |
| ~.adaptive_difficulty.background | 549 | 339 | 5 | 3 | 11 | 80 | deep |
| ~.adaptive_difficulty.claims | 232 | 108 | 10 | 5 | 6 | 38 | medium |
| ~.adaptive_difficulty.column_classes | 705 | 647 | 1 | 1 | 0 | 7 | deep |
| ~.adaptive_difficulty.data_check | 207 | 164 | 2 | 1 | 4 | 91 | medium |
| ~.adaptive_difficulty.denial_log | 307 | 172 | 8 | 3 | 0 | 60 | medium |
| ~.adaptive_difficulty.dose | 393 | 268 | 9 | 2 | 11 | 83 | deep |
| ~.adaptive_difficulty.dose_report | 458 | 334 | 16 | 3 | 3 | 53 | medium |
| ~.adaptive_difficulty.feature_audit | 551 | 406 | 8 | 11 | 20 | 102 | deep |
| ~.adaptive_difficulty.forecasters | 161 | 112 | 2 | 5 | 8 | 40 | medium |
| ~.adaptive_difficulty.generation | 465 | 276 | 11 | 5 | 14 | 73 | medium |
| ~.adaptive_difficulty.history_audit | 215 | 158 | 2 | 1 | 13 | 50 | medium |
| ~.adaptive_difficulty.history_card | 767 | 547 | 6 | 2 | 9 | 180 | deep |
| ~.adaptive_difficulty.history_forecast | 560 | 419 | 11 | 3 | 22 | 70 | medium |
| ~.adaptive_difficulty.history_resolve | 309 | 197 | 3 | 3 | 11 | 105 | medium |
| ~.adaptive_difficulty.lessons | 87 | 47 | 2 | 1 | 2 | 28 | s:one-caller helper |
| ~.adaptive_difficulty.logs | 24 | 10 | 1 | 12 | 0 | 7 | s:thin |
| ~.adaptive_difficulty.material_view | 1843 | 1151 | 7 | 24 | 23 | 60 | deep |
| ~.adaptive_difficulty.model | 764 | 539 | 21 | 11 | 2 | 45 | medium |
| ~.adaptive_difficulty.monitoring | 288 | 196 | 17 | 5 | 1 | 29 | medium |
| ~.adaptive_difficulty.operation | 797 | 480 | 17 | 28 | 11 | 71 | medium |
| ~.adaptive_difficulty.outcomes | 146 | 93 | 6 | 5 | 3 | 20 | medium |
| ~.adaptive_difficulty.outside | 794 | 547 | 12 | 6 | 25 | 79 | deep |
| ~.adaptive_difficulty.predict | 173 | 115 | 10 | 6 | 8 | 25 | medium |
| ~.adaptive_difficulty.priors | 364 | 248 | 9 | 16 | 0 | 36 | medium |
| ~.adaptive_difficulty.projection | 59 | 26 | 3 | 3 | 1 | 7 | medium |
| ~.adaptive_difficulty.protected_tables | 770 | 552 | 3 | 2 | 0 | 15 | deep |
| ~.adaptive_difficulty.protection | 132 | 63 | 5 | 5 | 3 | 20 | medium |
| ~.adaptive_difficulty.readiness | 366 | 236 | 7 | 10 | 7 | 55 | medium |
| ~.adaptive_difficulty.reading | 500 | 298 | 5 | 7 | 16 | 77 | deep |
| ~.adaptive_difficulty.reading_cache | 183 | 97 | 5 | 3 | 1 | 16 | medium |
| ~.adaptive_difficulty.relatedness | 859 | 613 | 28 | 6 | 19 | 100 | medium |
| ~.adaptive_difficulty.relatedness_jobs | 100 | 59 | 2 | 1 | 10 | 29 | s:one-caller helper |
| ~.adaptive_difficulty.replay | 991 | 742 | 18 | 12 | 18 | 251 | deep |
| ~.adaptive_difficulty.report | 797 | 599 | 7 | 2 | 16 | 80 | deep |
| ~.adaptive_difficulty.scoring | 383 | 279 | 6 | 5 | 10 | 102 | deep |
| ~.adaptive_difficulty.selection | 412 | 289 | 18 | 8 | 2 | 28 | medium |
| ~.adaptive_difficulty.sending | 397 | 184 | 7 | 6 | 8 | 31 | medium |
| ~.adaptive_difficulty.serve | 166 | 99 | 2 | 1 | 13 | 70 | medium |
| ~.adaptive_difficulty.serve_inputs | 318 | 214 | 6 | 3 | 8 | 39 | medium |
| ~.adaptive_difficulty.serving | 465 | 341 | 10 | 5 | 16 | 101 | deep |
| ~.adaptive_difficulty.spend | 47 | 21 | 2 | 9 | 2 | 6 | s:thin |
| ~.adaptive_difficulty.state | 408 | 282 | 3 | 4 | 2 | 52 | deep |
| ~.adaptive_difficulty.successor | 152 | 70 | 12 | 15 | 2 | 11 | medium |
| ~.adaptive_difficulty.switches | 79 | 40 | 6 | 17 | 0 | 9 | medium |
| ~.adf_numeric | 119 | 61 | 7 | 6 | 0 | 28 | medium |
| ~.ai | 40 | 25 | 0 | 0 | 0 | 8 | init/re-export |
| ~.ai.agent_harness | 73 | 34 | 6 | 5 | 2 | 7 | medium |
| ~.ai.agreement | 188 | 120 | 3 | 1 | 0 | 74 | medium |
| ~.ai.chatgpt_plan | 8 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.ai.chatgpt_plan.oauth | 582 | 418 | 23 | 4 | 0 | 65 | wide |
| ~.ai.chatgpt_plan.responses | 428 | 320 | 12 | 1 | 0 | 57 | medium |
| ~.ai.chatgpt_plan.routes | 44 | 28 | 1 | 4 | 3 | 31 | s:re-export |
| ~.ai.chatgpt_plan.session | 738 | 560 | 9 | 8 | 3 | 92 | deep |
| ~.ai.chatgpt_plan.store | 518 | 347 | 11 | 3 | 1 | 47 | medium |
| ~.ai.chatgpt_plan.workspace | 398 | 295 | 5 | 2 | 0 | 58 | deep |
| ~.ai.client | 125 | 84 | 3 | 8 | 14 | 54 | medium |
| ~.ai.decisions | 337 | 236 | 14 | 22 | 1 | 36 | medium |
| ~.ai.disclosures | 361 | 324 | 3 | 3 | 2 | 24 | deep |
| ~.ai.embedding | 55 | 26 | 3 | 10 | 0 | 14 | s:thin |
| ~.ai.errors | 63 | 33 | 7 | 111 | 0 | 12 | s:thin |
| ~.ai.execution | 435 | 259 | 24 | 129 | 1 | 49 | wide |
| ~.ai.isolation | 527 | 303 | 12 | 4 | 0 | 97 | medium |
| ~.ai.multimodal | 142 | 86 | 11 | 2 | 1 | 16 | medium |
| ~.ai.native_media | 161 | 107 | 4 | 4 | 2 | 69 | medium |
| ~.ai.output_budget | 238 | 116 | 5 | 26 | 3 | 24 | medium |
| ~.ai.plan_fallback | 901 | 508 | 42 | 34 | 1 | 28 | wide |
| ~.ai.providers | 7 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.ai.providers.chatgpt_plan | 664 | 481 | 5 | 3 | 13 | 65 | deep |
| ~.ai.providers.codex | 2117 | 1491 | 15 | 7 | 12 | 250 | deep |
| ~.ai.providers.codex_http | 249 | 179 | 2 | 2 | 8 | 90 | medium |
| ~.ai.providers.codex_lockdown | 1326 | 789 | 34 | 4 | 1 | 64 | wide |
| ~.ai.providers.decider | 317 | 228 | 7 | 6 | 5 | 45 | medium |
| ~.ai.providers.openai_chat | 733 | 496 | 3 | 3 | 9 | 60 | deep |
| ~.ai.providers.openai_embedding | 163 | 126 | 3 | 6 | 6 | 49 | medium |
| ~.ai.providers.openrouter | 44 | 23 | 1 | 2 | 1 | 12 | s:thin |
| ~.ai.providers.openrouter_catalog | 231 | 162 | 7 | 1 | 2 | 39 | medium |
| ~.ai.providers.openrouter_video | 335 | 258 | 8 | 2 | 4 | 46 | deep |
| ~.ai.providers.structured_output | 48 | 32 | 2 | 1 | 1 | 21 | s:thin |
| ~.ai.providers.voyage_contextual | 180 | 132 | 3 | 2 | 5 | 24 | medium |
| ~.ai.review_spend | 446 | 320 | 7 | 5 | 3 | 86 | deep |
| ~.ai.routing | 889 | 582 | 17 | 61 | 7 | 64 | medium |
| ~.ai.runs | 69 | 31 | 1 | 10 | 3 | 42 | s:re-export |
| ~.ai.runtime | 257 | 197 | 6 | 9 | 5 | 124 | medium |
| ~.ai.schemas | 210 | 92 | 10 | 73 | 0 | 16 | medium |
| ~.ai.spend | 657 | 417 | 13 | 122 | 2 | 47 | medium |
| ~.ai.strict_schema | 186 | 103 | 2 | 5 | 1 | 46 | medium |
| ~.ai.tool_requests | 54 | 26 | 3 | 1 | 1 | 0 | s:re-export |
| ~.ai.transport | 318 | 194 | 10 | 114 | 4 | 73 | medium |
| ~.ai.usage | 309 | 163 | 9 | 13 | 0 | 25 | medium |
| ~.algorithm_versions | 1188 | 148 | 1 | 86 | 0 | 4 | medium |
| ~.app_launch | 30 | 9 | 2 | 2 | 2 | 11 | s:thin |
| ~.attempt_content_state_upgrade | 295 | 157 | 2 | 2 | 13 | 50 | medium |
| ~.attempt_types | 70 | 46 | 2 | 8 | 0 | 9 | medium |
| ~.attempts | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.attempts.ability_transition | 40 | 29 | 1 | 2 | 2 | 33 | s:re-export |
| ~.attempts.ai_contracts | 638 | 437 | 19 | 13 | 3 | 22 | medium |
| ~.attempts.answer_check | 713 | 507 | 7 | 6 | 0 | 42 | deep |
| ~.attempts.attempt_trace | 184 | 142 | 4 | 1 | 5 | 85 | medium |
| ~.attempts.attempts | 5653 | 4063 | 46 | 37 | 59 | 774 | wide |
| ~.attempts.blind_grading | 784 | 610 | 17 | 13 | 8 | 73 | medium |
| ~.attempts.calibration_streams | 216 | 155 | 7 | 2 | 5 | 58 | medium |
| ~.attempts.clarification | 506 | 292 | 8 | 6 | 6 | 115 | deep |
| ~.attempts.coldness_receipt | 2145 | 1687 | 7 | 4 | 5 | 401 | deep |
| ~.attempts.completion_lock | 92 | 55 | 3 | 2 | 0 | 28 | medium |
| ~.attempts.effective_observation | 467 | 312 | 7 | 4 | 4 | 89 | deep |
| ~.attempts.evidence | 43 | 18 | 3 | 9 | 1 | 9 | s:thin |
| ~.attempts.grade_classifier | 174 | 103 | 9 | 3 | 0 | 49 | medium |
| ~.attempts.grade_resolution | 1242 | 960 | 10 | 6 | 15 | 258 | deep |
| ~.attempts.grader_calibration | 698 | 519 | 13 | 4 | 6 | 142 | medium |
| ~.attempts.grading | 2032 | 1556 | 23 | 35 | 15 | 725 | deep |
| ~.attempts.grading_admission | 55 | 25 | 3 | 5 | 0 | 9 | s:thin |
| ~.attempts.grading_support | 1273 | 809 | 26 | 7 | 12 | 138 | medium |
| ~.attempts.hint_fold | 402 | 200 | 9 | 2 | 3 | 72 | medium |
| ~.attempts.measurement_corrections | 279 | 228 | 3 | 1 | 10 | 175 | medium |
| ~.attempts.observations | 181 | 155 | 7 | 1 | 4 | 62 | medium |
| ~.attempts.outcome_schemas | 162 | 123 | 3 | 6 | 3 | 25 | medium |
| ~.attempts.post_attempt | 459 | 278 | 7 | 6 | 13 | 128 | deep |
| ~.attempts.regrade | 828 | 647 | 4 | 3 | 25 | 406 | deep |
| ~.attempts.reveal_ledger | 662 | 385 | 17 | 19 | 6 | 95 | medium |
| ~.attempts.salience_firewall | 379 | 204 | 7 | 17 | 1 | 73 | medium |
| ~.attempts.stuck | 507 | 329 | 10 | 14 | 4 | 48 | deep |
| ~.attempts.surprise | 163 | 144 | 5 | 1 | 5 | 80 | medium |
| ~.attempts.trace_evidence | 349 | 143 | 8 | 6 | 1 | 76 | medium |
| ~.bootstrap | 187 | 145 | 3 | 3 | 9 | 57 | medium |
| ~.capture | 55 | 51 | 0 | 8 | 6 | 0 | init/re-export |
| ~.capture.devices | 188 | 151 | 6 | 4 | 3 | 58 | medium |
| ~.capture.errors | 11 | 7 | 1 | 6 | 0 | 6 | s:thin |
| ~.capture.inbox | 397 | 320 | 12 | 2 | 5 | 81 | medium |
| ~.capture.jobs | 228 | 157 | 8 | 2 | 4 | 55 | medium |
| ~.capture.maintenance | 63 | 44 | 3 | 1 | 3 | 16 | s:thin |
| ~.capture.report | 185 | 131 | 3 | 1 | 1 | 85 | medium |
| ~.capture.routing | 104 | 73 | 4 | 2 | 3 | 28 | medium |
| ~.causal_activity_policy | 91 | 56 | 2 | 8 | 0 | 25 | medium |
| ~.claim_fixes_upgrade | 386 | 216 | 3 | 22 | 13 | 69 | medium |
| ~.cli | 111 | 104 | 0 | 0 | 49 | 0 | medium |
| ~.cli.ad | 252 | 182 | 6 | 1 | 13 | 59 | medium |
| ~.cli.ai | 603 | 495 | 7 | 1 | 20 | 198 | deep |
| ~.cli.ai_compare | 1205 | 872 | 11 | 1 | 23 | 124 | deep |
| ~.cli.app | 5541 | 4601 | 86 | 3 | 128 | 401 | wide |
| ~.cli.calibration | 71 | 50 | 2 | 1 | 4 | 30 | s:one-caller helper |
| ~.cli.card | 79 | 63 | 3 | 1 | 2 | 21 | s:one-caller helper |
| ~.cli.claims | 33 | 23 | 2 | 1 | 1 | 14 | s:thin |
| ~.cli.clarification | 144 | 105 | 4 | 1 | 3 | 38 | medium |
| ~.cli.config | 43 | 35 | 1 | 1 | 1 | 33 | s:thin |
| ~.cli.contamination | 147 | 116 | 2 | 1 | 7 | 58 | medium |
| ~.cli.contracts | 118 | 101 | 3 | 1 | 2 | 34 | medium |
| ~.cli.controller | 42 | 31 | 1 | 1 | 2 | 29 | s:thin |
| ~.cli.curriculum | 102 | 61 | 2 | 1 | 8 | 41 | s:one-caller helper |
| ~.cli.data | 220 | 179 | 5 | 1 | 10 | 23 | medium |
| ~.cli.data_capture | 55 | 41 | 1 | 1 | 7 | 31 | s:re-export |
| ~.cli.decider | 71 | 38 | 1 | 1 | 5 | 34 | s:re-export |
| ~.cli.depth | 156 | 122 | 7 | 1 | 3 | 29 | medium |
| ~.cli.diagnose | 793 | 634 | 10 | 1 | 18 | 159 | deep |
| ~.cli.diagnosis | 347 | 295 | 4 | 1 | 3 | 125 | deep |
| ~.cli.embeddings | 752 | 562 | 20 | 13 | 22 | 87 | medium |
| ~.cli.evaluation | 202 | 148 | 4 | 1 | 11 | 42 | medium |
| ~.cli.evsi | 293 | 242 | 4 | 1 | 10 | 107 | medium |
| ~.cli.exam | 203 | 182 | 4 | 1 | 4 | 116 | medium |
| ~.cli.experiments | 310 | 234 | 8 | 1 | 11 | 89 | medium |
| ~.cli.facets | 185 | 131 | 5 | 1 | 6 | 46 | medium |
| ~.cli.families | 108 | 86 | 2 | 1 | 7 | 48 | medium |
| ~.cli.field | 310 | 242 | 3 | 4 | 17 | 115 | medium |
| ~.cli.field_classification | 187 | 142 | 3 | 1 | 17 | 139 | medium |
| ~.cli.fit | 213 | 192 | 4 | 1 | 7 | 78 | medium |
| ~.cli.gaps | 191 | 134 | 4 | 1 | 14 | 47 | medium |
| ~.cli.goldenpath | 26 | 16 | 1 | 1 | 2 | 14 | s:thin |
| ~.cli.grading | 322 | 242 | 6 | 1 | 9 | 73 | medium |
| ~.cli.hints | 129 | 91 | 2 | 1 | 7 | 50 | medium |
| ~.cli.inbox | 29 | 21 | 1 | 1 | 2 | 19 | s:thin |
| ~.cli.ingest_batches | 91 | 79 | 4 | 1 | 2 | 28 | s:one-caller helper |
| ~.cli.mcp | 185 | 135 | 4 | 1 | 7 | 38 | medium |
| ~.cli.pf | 119 | 87 | 3 | 1 | 4 | 48 | medium |
| ~.cli.placement | 102 | 73 | 2 | 2 | 6 | 40 | medium |
| ~.cli.plan | 96 | 69 | 2 | 1 | 6 | 29 | s:one-caller helper |
| ~.cli.practice_index | 296 | 225 | 7 | 2 | 14 | 56 | medium |
| ~.cli.probability_arms | 440 | 326 | 7 | 3 | 19 | 79 | deep |
| ~.cli.project | 887 | 747 | 13 | 1 | 13 | 85 | deep |
| ~.cli.questions | 61 | 49 | 2 | 1 | 2 | 27 | s:one-caller helper |
| ~.cli.reader | 220 | 157 | 4 | 1 | 12 | 54 | medium |
| ~.cli.receipts | 146 | 84 | 5 | 9 | 6 | 27 | medium |
| ~.cli.recurrence | 240 | 161 | 4 | 1 | 9 | 52 | medium |
| ~.cli.registry | 295 | 239 | 6 | 1 | 4 | 83 | medium |
| ~.cli.render | 181 | 154 | 0 | 2 | 2 | 17 | medium |
| ~.cli.router | 519 | 410 | 6 | 1 | 23 | 93 | deep |
| ~.cli.runtime | 882 | 794 | 0 | 25 | 42 | 139 | deep |
| ~.cli.sim | 358 | 311 | 5 | 1 | 7 | 88 | deep |
| ~.cli.source_set | 117 | 93 | 5 | 1 | 3 | 43 | medium |
| ~.cli.sources | 415 | 328 | 9 | 1 | 19 | 55 | deep |
| ~.cli.success_head | 233 | 186 | 2 | 1 | 14 | 146 | medium |
| ~.cli.surfaces | 71 | 54 | 2 | 1 | 2 | 37 | s:one-caller helper |
| ~.cli.teacher | 49 | 31 | 1 | 1 | 4 | 24 | s:re-export |
| ~.clock | 42 | 28 | 5 | 445 | 0 | 8 | medium |
| ~.cold_retry_reschedule_upgrade | 292 | 157 | 2 | 2 | 13 | 50 | medium |
| ~.confidence_events | 369 | 216 | 14 | 6 | 3 | 67 | medium |
| ~.config | 7 | 4 | 0 | 70 | 4 | 0 | init/re-export |
| ~.config.compat | 324 | 255 | 7 | 4 | 1 | 109 | deep |
| ~.config.loader | 173 | 125 | 5 | 14 | 3 | 23 | medium |
| ~.config.schema | 5143 | 1789 | 147 | 38 | 1 | 87 | wide |
| ~.config.template | 4204 | 885 | 4 | 2 | 2 | 20 | deep |
| ~.content.authoring | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.content.authoring.ai_contracts | 455 | 361 | 12 | 5 | 4 | 6 | medium |
| ~.content.authoring.animation_media | 211 | 153 | 5 | 1 | 0 | 73 | medium |
| ~.content.authoring.authoring_gates | 436 | 275 | 6 | 8 | 3 | 71 | deep |
| ~.content.authoring.concept_animation | 1551 | 1128 | 29 | 5 | 10 | 217 | medium |
| ~.content.authoring.conjunctive_items | 322 | 115 | 7 | 4 | 3 | 36 | medium |
| ~.content.authoring.contract_commissioning | 524 | 306 | 7 | 3 | 5 | 79 | deep |
| ~.content.authoring.draft_validation | 114 | 68 | 2 | 2 | 1 | 50 | medium |
| ~.content.authoring.exercise_authoring | 964 | 675 | 8 | 2 | 19 | 401 | deep |
| ~.content.authoring.item_authoring | 454 | 335 | 6 | 4 | 13 | 72 | deep |
| ~.content.authoring.laddered_stems | 392 | 189 | 7 | 2 | 3 | 138 | medium |
| ~.content.authoring.persona_gate | 1630 | 933 | 21 | 5 | 8 | 114 | deep |
| ~.content.authoring.persona_realism | 320 | 264 | 5 | 3 | 2 | 98 | deep |
| ~.content.authoring.pf_contracts | 444 | 344 | 29 | 4 | 4 | 26 | wide |
| ~.content.authoring.pf_sandbox | 421 | 330 | 10 | 8 | 1 | 55 | deep |
| ~.content.authoring.practice_generation | 2439 | 1782 | 18 | 8 | 26 | 206 | deep |
| ~.content.authoring.practice_leakage | 484 | 289 | 15 | 16 | 7 | 77 | medium |
| ~.content.authoring.rung_variants | 893 | 707 | 6 | 2 | 18 | 231 | deep |
| ~.content.authoring.source_exercise_import | 1719 | 1250 | 25 | 7 | 35 | 241 | deep |
| ~.content.facet_identity | 12 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.content.facet_identity.actions | 2101 | 1373 | 36 | 13 | 18 | 150 | wide |
| ~.content.facet_identity.authority | 1406 | 841 | 33 | 5 | 14 | 128 | wide |
| ~.content.facet_identity.dedupe | 248 | 207 | 3 | 1 | 14 | 128 | medium |
| ~.content.facet_identity.grouping | 308 | 223 | 5 | 2 | 2 | 84 | medium |
| ~.content.facet_identity.judge | 1265 | 963 | 28 | 6 | 10 | 120 | medium |
| ~.content.facet_identity.plan | 469 | 373 | 5 | 2 | 6 | 146 | deep |
| ~.content.facet_identity.span_support | 138 | 73 | 3 | 2 | 5 | 41 | medium |
| ~.content.facet_identity.views | 195 | 135 | 3 | 4 | 0 | 51 | medium |
| ~.content.pipeline | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.content.pipeline.acquisition_preview | 272 | 213 | 3 | 2 | 8 | 64 | medium |
| ~.content.pipeline.add_source | 2773 | 1860 | 71 | 15 | 28 | 159 | wide |
| ~.content.pipeline.ai_contracts | 89 | 68 | 4 | 1 | 2 | 18 | s:re-export |
| ~.content.pipeline.build_plan | 376 | 291 | 6 | 4 | 3 | 82 | deep |
| ~.content.pipeline.exam_marking | 395 | 242 | 9 | 3 | 5 | 64 | medium |
| ~.content.pipeline.jobs | 5814 | 4116 | 42 | 6 | 63 | 238 | wide |
| ~.content.pipeline.quick_add | 491 | 369 | 6 | 3 | 12 | 118 | deep |
| ~.content.pipeline.reread | 666 | 436 | 22 | 5 | 12 | 67 | wide |
| ~.content.pipeline.revision_refresh | 231 | 164 | 2 | 1 | 12 | 67 | medium |
| ~.content.pipeline.runner | 1262 | 870 | 10 | 6 | 12 | 148 | deep |
| ~.content.pipeline.source_ingestion | 2218 | 1917 | 27 | 3 | 25 | 305 | deep |
| ~.content.proposals | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.content.proposals.ai_contracts | 912 | 674 | 30 | 10 | 4 | 26 | wide |
| ~.content.proposals.apply_protocol | 603 | 440 | 6 | 5 | 11 | 118 | deep |
| ~.content.proposals.conflict_resolution | 90 | 57 | 3 | 2 | 2 | 50 | medium |
| ~.content.proposals.method_phrasing | 1232 | 829 | 26 | 2 | 18 | 127 | medium |
| ~.content.proposals.method_statement_judge | 502 | 344 | 16 | 5 | 15 | 71 | medium |
| ~.content.proposals.patches | 1336 | 1039 | 7 | 11 | 21 | 106 | deep |
| ~.content.proposals.proposals | 2537 | 2020 | 28 | 13 | 21 | 121 | deep |
| ~.content.proposals.required_method_override | 274 | 194 | 6 | 3 | 8 | 59 | medium |
| ~.content.sources | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.content.sources.block_health | 147 | 99 | 2 | 2 | 1 | 69 | medium |
| ~.content.sources.exam_material | 1589 | 943 | 36 | 59 | 7 | 83 | wide |
| ~.content.sources.exercise_statements | 205 | 119 | 7 | 6 | 4 | 46 | medium |
| ~.content.sources.extraction_health | 197 | 137 | 3 | 1 | 1 | 33 | medium |
| ~.content.sources.front_matter | 31 | 14 | 1 | 2 | 0 | 8 | s:thin |
| ~.content.sources.math_text | 358 | 243 | 5 | 3 | 0 | 50 | medium |
| ~.content.sources.pdf_extraction | 274 | 181 | 3 | 1 | 5 | 31 | medium |
| ~.content.sources.provenance | 123 | 89 | 1 | 3 | 1 | 83 | medium |
| ~.content.sources.role_authority | 269 | 145 | 9 | 12 | 0 | 46 | medium |
| ~.content.sources.source_deletion | 338 | 240 | 6 | 1 | 5 | 74 | medium |
| ~.content.sources.source_library | 175 | 113 | 3 | 2 | 5 | 104 | medium |
| ~.content.sources.source_outcome_analytics | 280 | 215 | 4 | 3 | 2 | 152 | medium |
| ~.content.sources.source_outline | 293 | 198 | 9 | 34 | 5 | 58 | medium |
| ~.content.sources.source_refs | 243 | 188 | 3 | 3 | 0 | 79 | medium |
| ~.content.sources.span_aliases | 469 | 270 | 18 | 14 | 5 | 31 | medium |
| ~.content.synthesis | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.content.synthesis.ai_contracts | 1062 | 791 | 51 | 5 | 3 | 18 | wide |
| ~.content.synthesis.append_neighborhood | 543 | 406 | 4 | 1 | 3 | 147 | deep |
| ~.content.synthesis.brief | 141 | 81 | 3 | 7 | 0 | 29 | medium |
| ~.content.synthesis.coverage_rollup | 60 | 44 | 1 | 1 | 2 | 49 | s:re-export |
| ~.content.synthesis.exam_profile | 188 | 129 | 5 | 2 | 0 | 87 | medium |
| ~.content.synthesis.facet_candidates | 189 | 128 | 3 | 1 | 3 | 55 | medium |
| ~.content.synthesis.facet_doctor | 122 | 74 | 3 | 4 | 2 | 33 | medium |
| ~.content.synthesis.facet_mint_gate | 551 | 306 | 11 | 5 | 2 | 76 | medium |
| ~.content.synthesis.graph_nomination | 1071 | 799 | 13 | 9 | 12 | 120 | deep |
| ~.content.synthesis.source_append | 1070 | 788 | 5 | 4 | 24 | 311 | deep |
| ~.content.synthesis.source_coverage | 274 | 217 | 1 | 2 | 7 | 145 | medium |
| ~.content.synthesis.source_set_synthesis | 3810 | 2970 | 11 | 4 | 39 | 1081 | deep |
| ~.content.synthesis.source_unit_inventory | 936 | 699 | 18 | 5 | 12 | 167 | medium |
| ~.content.synthesis.source_unit_selection | 567 | 405 | 12 | 9 | 6 | 126 | medium |
| ~.content.synthesis.study_map_diff | 80 | 55 | 1 | 1 | 2 | 40 | s:one-caller helper |
| ~.content.synthesis.synthesis_eval | 303 | 228 | 5 | 1 | 3 | 119 | medium |
| ~.content.synthesis.synthesis_gates | 1045 | 785 | 7 | 9 | 2 | 84 | deep |
| ~.content.synthesis.synthesis_manifests | 214 | 138 | 8 | 2 | 3 | 56 | medium |
| ~.content.synthesis.vault_epigraphs | 362 | 277 | 6 | 2 | 6 | 79 | deep |
| ~.curriculum | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.curriculum.ai_contracts | 144 | 102 | 8 | 2 | 3 | 6 | medium |
| ~.curriculum.commitment_arcs | 435 | 315 | 11 | 2 | 6 | 90 | medium |
| ~.curriculum.commitments | 939 | 689 | 27 | 26 | 3 | 98 | medium |
| ~.curriculum.concepts | 471 | 425 | 3 | 1 | 8 | 79 | deep |
| ~.curriculum.confusable_concepts | 91 | 73 | 2 | 1 | 4 | 66 | s:re-export |
| ~.curriculum.curriculum_locks | 122 | 69 | 4 | 2 | 2 | 25 | medium |
| ~.curriculum.depth_edge_authoring | 579 | 453 | 8 | 1 | 10 | 142 | deep |
| ~.curriculum.depth_envelopes | 33 | 16 | 2 | 3 | 1 | 13 | s:thin |
| ~.curriculum.depth_rungs | 665 | 438 | 12 | 9 | 4 | 121 | medium |
| ~.curriculum.depth_transition | 290 | 201 | 3 | 3 | 8 | 193 | medium |
| ~.curriculum.golden_path_assessment | 437 | 298 | 8 | 3 | 6 | 151 | deep |
| ~.curriculum.golden_path_compose | 217 | 173 | 3 | 1 | 4 | 132 | medium |
| ~.curriculum.golden_path_confirm | 369 | 263 | 4 | 2 | 5 | 195 | deep |
| ~.curriculum.golden_path_fixture | 428 | 337 | 6 | 1 | 8 | 94 | deep |
| ~.curriculum.golden_path_restoration | 442 | 286 | 6 | 2 | 9 | 90 | deep |
| ~.curriculum.golden_path_run | 375 | 269 | 9 | 6 | 5 | 86 | deep |
| ~.curriculum.graph_edit_proposals | 676 | 501 | 6 | 2 | 11 | 74 | deep |
| ~.curriculum.integration_backfill | 624 | 361 | 10 | 2 | 11 | 90 | deep |
| ~.curriculum.pattern_ladder | 511 | 341 | 9 | 1 | 5 | 108 | deep |
| ~.curriculum.rung_backfill | 157 | 117 | 3 | 1 | 9 | 101 | medium |
| ~.curriculum.subject_registry | 219 | 148 | 3 | 1 | 8 | 78 | medium |
| ~.curriculum.task_blueprints | 298 | 213 | 9 | 2 | 3 | 39 | medium |
| ~.daily_plan | 14 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.daily_plan.ad_slot | 388 | 245 | 8 | 1 | 9 | 78 | medium |
| ~.daily_plan.admission | 252 | 181 | 8 | 4 | 1 | 78 | medium |
| ~.daily_plan.chooser | 78 | 56 | 2 | 4 | 1 | 36 | medium |
| ~.daily_plan.engine | 5978 | 4141 | 50 | 16 | 58 | 264 | wide |
| ~.daily_plan.estimates | 268 | 173 | 9 | 6 | 1 | 47 | medium |
| ~.daily_plan.headline | 225 | 159 | 4 | 4 | 8 | 43 | medium |
| ~.daily_plan.intent_cost | 112 | 80 | 4 | 1 | 8 | 43 | s:one-caller helper |
| ~.daily_plan.lanes | 672 | 472 | 10 | 3 | 2 | 106 | deep |
| ~.daily_plan.lesson_offer | 450 | 273 | 19 | 5 | 11 | 80 | medium |
| ~.daily_plan.lesson_suggestion | 670 | 431 | 10 | 6 | 20 | 108 | deep |
| ~.daily_plan.measurement | 621 | 421 | 8 | 4 | 12 | 110 | deep |
| ~.daily_plan.objective_card | 126 | 85 | 1 | 1 | 2 | 30 | medium |
| ~.daily_plan.objective_chooser | 1871 | 1387 | 10 | 3 | 22 | 192 | deep |
| ~.daily_plan.objective_inputs | 812 | 576 | 7 | 2 | 25 | 164 | deep |
| ~.daily_plan.policy | 175 | 104 | 5 | 8 | 11 | 70 | medium |
| ~.daily_plan.reading | 308 | 185 | 4 | 1 | 3 | 54 | medium |
| ~.daily_plan.reading_choice | 191 | 102 | 5 | 2 | 0 | 31 | medium |
| ~.daily_plan.records | 527 | 373 | 5 | 4 | 1 | 65 | deep |
| ~.daily_plan.reentry | 195 | 137 | 5 | 3 | 4 | 90 | medium |
| ~.daily_plan.report | 183 | 160 | 2 | 1 | 2 | 91 | medium |
| ~.daily_plan.router_card | 832 | 600 | 2 | 1 | 20 | 106 | deep |
| ~.daily_plan.router_chooser | 978 | 778 | 7 | 3 | 14 | 101 | deep |
| ~.daily_plan.router_reader | 725 | 481 | 4 | 1 | 11 | 64 | deep |
| ~.daily_plan.router_retrieval | 423 | 315 | 7 | 2 | 10 | 74 | deep |
| ~.daily_plan.router_runtime | 755 | 513 | 12 | 7 | 12 | 80 | deep |
| ~.daily_plan.router_teach_back | 305 | 205 | 7 | 2 | 8 | 78 | medium |
| ~.daily_plan.schedule_effects | 143 | 86 | 3 | 1 | 5 | 58 | medium |
| ~.daily_plan.slot_facts | 173 | 117 | 5 | 1 | 10 | 44 | medium |
| ~.daily_plan.slot_facts_schema | 258 | 190 | 7 | 3 | 0 | 91 | medium |
| ~.daily_plan.split | 316 | 239 | 7 | 2 | 1 | 78 | medium |
| ~.daily_plan.staged_frame | 483 | 314 | 6 | 4 | 9 | 54 | deep |
| ~.daily_plan.types | 242 | 135 | 8 | 15 | 0 | 13 | medium |
| ~.daily_plan.view | 371 | 286 | 6 | 2 | 9 | 122 | deep |
| ~.daily_plan_upgrade | 116 | 65 | 1 | 2 | 9 | 47 | s:re-export |
| ~.data_capture | 20 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.data_capture.gates | 40 | 18 | 3 | 19 | 1 | 7 | s:thin |
| ~.data_capture.prefilter | 375 | 277 | 10 | 5 | 3 | 55 | deep |
| ~.data_capture.reading_exposures | 332 | 192 | 8 | 6 | 8 | 23 | medium |
| ~.data_capture_upgrade | 282 | 157 | 2 | 2 | 13 | 50 | medium |
| ~.db | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.db.checkpoint | 82 | 47 | 2 | 3 | 1 | 38 | s:re-export |
| ~.db.connection | 388 | 237 | 7 | 180 | 1 | 32 | medium |
| ~.db.copies | 178 | 111 | 6 | 10 | 1 | 43 | medium |
| ~.db.migrate | 464 | 283 | 12 | 12 | 2 | 67 | medium |
| ~.db.repositories | 27943 | 23691 | 27 | 406 | 30 | 255 | deep |
| ~.db.scopes | 393 | 255 | 11 | 16 | 3 | 21 | medium |
| ~.db.storage | 189 | 136 | 8 | 1 | 0 | 22 | medium |
| ~.db.stores | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.db.stores.ad_receipts | 279 | 191 | 14 | 12 | 1 | 19 | medium |
| ~.db.stores.ad_serving | 517 | 352 | 29 | 12 | 3 | 60 | wide |
| ~.db.stores.answered_contracts | 75 | 49 | 1 | 5 | 0 | 44 | medium |
| ~.db.stores.approach_maps | 145 | 91 | 9 | 4 | 0 | 12 | medium |
| ~.db.stores.collection | 228 | 157 | 1 | 1 | 5 | 71 | medium |
| ~.db.stores.completion | 81 | 55 | 1 | 1 | 1 | 29 | s:one-caller helper |
| ~.db.stores.daily_plans | 356 | 246 | 15 | 9 | 0 | 54 | medium |
| ~.db.stores.data_capture | 261 | 183 | 16 | 5 | 2 | 32 | medium |
| ~.db.stores.deliverables | 175 | 112 | 15 | 3 | 0 | 13 | medium |
| ~.db.stores.diagnoses | 989 | 781 | 4 | 2 | 2 | 73 | deep |
| ~.db.stores.diagnosis_review | 393 | 336 | 9 | 5 | 0 | 33 | deep |
| ~.db.stores.embedding_vectors | 277 | 191 | 10 | 19 | 1 | 61 | medium |
| ~.db.stores.facet_identity | 328 | 235 | 12 | 4 | 0 | 32 | medium |
| ~.db.stores.families | 128 | 104 | 9 | 4 | 0 | 25 | medium |
| ~.db.stores.field | 32 | 21 | 2 | 2 | 0 | 10 | s:thin |
| ~.db.stores.field_signal_receipts | 52 | 31 | 3 | 1 | 0 | 11 | s:thin |
| ~.db.stores.figure_prefetch | 55 | 30 | 4 | 1 | 0 | 9 | s:one-caller helper |
| ~.db.stores.figures | 413 | 269 | 27 | 10 | 0 | 20 | wide |
| ~.db.stores.followup_serve | 379 | 251 | 32 | 7 | 1 | 22 | wide |
| ~.db.stores.followup_value | 72 | 45 | 3 | 1 | 1 | 18 | s:one-caller helper |
| ~.db.stores.forecast_receipts | 127 | 94 | 3 | 4 | 2 | 46 | medium |
| ~.db.stores.held_out_signals | 118 | 59 | 5 | 3 | 0 | 18 | medium |
| ~.db.stores.help_assists | 759 | 441 | 34 | 19 | 0 | 38 | wide |
| ~.db.stores.hypothesis_marks | 191 | 122 | 14 | 6 | 1 | 23 | medium |
| ~.db.stores.ingest_queue | 962 | 772 | 5 | 4 | 1 | 112 | deep |
| ~.db.stores.intent_reads | 180 | 138 | 8 | 3 | 0 | 25 | medium |
| ~.db.stores.judgment_claims | 201 | 135 | 8 | 7 | 1 | 45 | medium |
| ~.db.stores.judgments | 43 | 30 | 1 | 68 | 0 | 29 | s:re-export |
| ~.db.stores.learner_gaps | 421 | 309 | 22 | 12 | 2 | 35 | wide |
| ~.db.stores.learner_notes | 307 | 188 | 20 | 3 | 0 | 20 | wide |
| ~.db.stores.lessons | 313 | 231 | 21 | 10 | 2 | 29 | wide |
| ~.db.stores.library_asks | 146 | 88 | 10 | 3 | 0 | 17 | medium |
| ~.db.stores.model_calls | 143 | 89 | 4 | 3 | 3 | 32 | medium |
| ~.db.stores.observation_ledger | 300 | 237 | 3 | 3 | 0 | 133 | medium |
| ~.db.stores.pf | 220 | 156 | 13 | 6 | 0 | 31 | medium |
| ~.db.stores.placement | 102 | 73 | 6 | 2 | 0 | 17 | medium |
| ~.db.stores.plan_presentations | 146 | 94 | 7 | 4 | 1 | 29 | medium |
| ~.db.stores.practice_index | 382 | 284 | 21 | 17 | 1 | 39 | wide |
| ~.db.stores.reader_cue_links | 197 | 138 | 11 | 2 | 0 | 21 | medium |
| ~.db.stores.reader_digests | 152 | 95 | 9 | 4 | 0 | 16 | medium |
| ~.db.stores.reading_paths | 98 | 60 | 7 | 1 | 0 | 10 | s:one-caller helper |
| ~.db.stores.recurrence | 544 | 412 | 20 | 4 | 2 | 48 | medium |
| ~.db.stores.retrieval_spaces | 214 | 155 | 12 | 8 | 0 | 17 | medium |
| ~.db.stores.router | 336 | 211 | 10 | 6 | 1 | 98 | medium |
| ~.db.stores.router_objective | 267 | 186 | 14 | 19 | 0 | 23 | medium |
| ~.db.stores.router_suggestions | 258 | 168 | 18 | 7 | 1 | 26 | medium |
| ~.db.stores.section_coverage | 126 | 85 | 7 | 3 | 0 | 21 | medium |
| ~.db.stores.session_ownership | 364 | 226 | 2 | 3 | 2 | 84 | medium |
| ~.db.stores.source_block_fts | 578 | 386 | 30 | 40 | 0 | 33 | wide |
| ~.db.stores.source_service | 1918 | 1235 | 61 | 34 | 2 | 163 | wide |
| ~.db.stores.voi_forecasts | 112 | 87 | 3 | 4 | 2 | 44 | medium |
| ~.db.stores.workbench | 207 | 143 | 15 | 5 | 0 | 26 | medium |
| ~.db.stores.write_provenance | 859 | 565 | 24 | 18 | 2 | 52 | medium |
| ~.db.table_roles | 800 | 483 | 8 | 6 | 0 | 16 | deep |
| ~.decider_judgments | 429 | 264 | 11 | 22 | 9 | 56 | medium |
| ~.decider_upgrade | 116 | 57 | 1 | 2 | 9 | 46 | s:re-export |
| ~.delayed_checks | 170 | 108 | 7 | 4 | 7 | 28 | medium |
| ~.delayed_completion | 178 | 96 | 7 | 5 | 2 | 17 | medium |
| ~.deliverable_plan_upgrade | 294 | 157 | 2 | 2 | 13 | 50 | medium |
| ~.diagnosis | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.diagnosis.ai_contracts | 397 | 321 | 25 | 7 | 3 | 33 | wide |
| ~.diagnosis.calibration_sessions | 392 | 274 | 8 | 6 | 9 | 116 | deep |
| ~.diagnosis.causal_activity_policy | 424 | 228 | 9 | 10 | 3 | 56 | medium |
| ~.diagnosis.causal_attribution | 3782 | 2930 | 23 | 27 | 15 | 357 | deep |
| ~.diagnosis.causal_diagnostic_selector | 672 | 507 | 4 | 3 | 8 | 360 | deep |
| ~.diagnosis.causal_factor_deferral | 500 | 308 | 2 | 4 | 3 | 142 | deep |
| ~.diagnosis.causal_health | 360 | 255 | 3 | 2 | 3 | 156 | deep |
| ~.diagnosis.causal_migration | 122 | 94 | 2 | 0 | 3 | 80 | medium |
| ~.diagnosis.causal_orchestrator | 3422 | 2411 | 35 | 9 | 17 | 512 | wide |
| ~.diagnosis.causal_probe_coherence | 2011 | 1572 | 28 | 15 | 10 | 183 | deep |
| ~.diagnosis.causal_probe_commissioning | 795 | 546 | 8 | 2 | 4 | 342 | deep |
| ~.diagnosis.causal_selection_audit | 229 | 189 | 1 | 2 | 5 | 169 | medium |
| ~.diagnosis.contrast_pairs | 1044 | 611 | 18 | 5 | 10 | 155 | medium |
| ~.diagnosis.diagnosis_adjudication | 866 | 625 | 9 | 5 | 5 | 156 | deep |
| ~.diagnosis.diagnostic_augmentation | 1244 | 1019 | 16 | 6 | 13 | 176 | deep |
| ~.diagnosis.diagnostic_gate | 515 | 363 | 5 | 9 | 6 | 146 | deep |
| ~.diagnosis.diagnostic_pack | 541 | 379 | 14 | 3 | 5 | 88 | medium |
| ~.diagnosis.diagnostic_surface_supply | 495 | 301 | 7 | 2 | 12 | 108 | deep |
| ~.diagnosis.discrimination_profiles | 572 | 274 | 11 | 6 | 3 | 114 | medium |
| ~.diagnosis.error_hunt | 729 | 407 | 9 | 4 | 11 | 120 | deep |
| ~.diagnosis.error_taxonomy | 108 | 88 | 1 | 2 | 5 | 66 | medium |
| ~.diagnosis.error_taxonomy_map | 267 | 148 | 2 | 10 | 0 | 30 | medium |
| ~.diagnosis.failure_triage | 1055 | 751 | 8 | 1 | 6 | 142 | deep |
| ~.diagnosis.followups | 2614 | 2009 | 15 | 10 | 29 | 389 | deep |
| ~.diagnosis.forecast_receipts | 611 | 435 | 6 | 3 | 8 | 130 | deep |
| ~.diagnosis.gate_fit | 207 | 156 | 5 | 1 | 5 | 66 | medium |
| ~.diagnosis.gate_score | 338 | 235 | 6 | 3 | 4 | 52 | medium |
| ~.diagnosis.grading_hardcases | 931 | 662 | 10 | 1 | 16 | 224 | deep |
| ~.diagnosis.guided_redo | 355 | 218 | 6 | 5 | 6 | 82 | medium |
| ~.diagnosis.longform_trace | 277 | 190 | 7 | 1 | 0 | 80 | medium |
| ~.diagnosis.misconceptions | 1012 | 660 | 9 | 10 | 17 | 145 | deep |
| ~.diagnosis.missing_vocabulary | 466 | 333 | 6 | 4 | 5 | 79 | deep |
| ~.diagnosis.offline_review | 17 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.diagnosis.offline_review.decider_links | 84 | 51 | 2 | 1 | 3 | 35 | s:one-caller helper |
| ~.diagnosis.offline_review.judge | 377 | 272 | 28 | 5 | 3 | 34 | wide |
| ~.diagnosis.offline_review.links | 133 | 109 | 1 | 1 | 8 | 89 | medium |
| ~.diagnosis.offline_review.planted | 472 | 384 | 13 | 1 | 8 | 49 | medium |
| ~.diagnosis.offline_review.probes | 290 | 193 | 12 | 2 | 6 | 43 | medium |
| ~.diagnosis.offline_review.report | 1069 | 937 | 8 | 5 | 5 | 107 | deep |
| ~.diagnosis.offline_review.runner | 1979 | 1682 | 21 | 6 | 36 | 132 | deep |
| ~.diagnosis.offline_review.spend | 8 | 2 | 0 | 14 | 1 | 0 | s:thin |
| ~.diagnosis.offline_review.spot_check | 483 | 381 | 9 | 2 | 10 | 144 | deep |
| ~.diagnosis.predictive_eig | 232 | 170 | 4 | 1 | 4 | 86 | medium |
| ~.diagnosis.probe_audit | 728 | 562 | 13 | 3 | 7 | 117 | deep |
| ~.diagnosis.probe_blocks | 500 | 355 | 5 | 3 | 12 | 186 | deep |
| ~.diagnosis.probe_coverage | 175 | 144 | 1 | 1 | 4 | 140 | medium |
| ~.diagnosis.probe_dialogue | 465 | 362 | 8 | 1 | 15 | 165 | deep |
| ~.diagnosis.probe_episodes | 3652 | 2612 | 46 | 22 | 36 | 260 | wide |
| ~.diagnosis.probe_families | 1798 | 1455 | 25 | 17 | 3 | 101 | deep |
| ~.diagnosis.probe_hypotheses | 274 | 182 | 7 | 14 | 7 | 102 | medium |
| ~.diagnosis.probe_instance_generation | 1534 | 1190 | 18 | 11 | 16 | 195 | deep |
| ~.diagnosis.probe_lifecycle | 300 | 236 | 9 | 1 | 5 | 80 | medium |
| ~.diagnosis.probe_outcome_mapping | 179 | 98 | 5 | 2 | 2 | 23 | medium |
| ~.diagnosis.probe_remint | 327 | 183 | 5 | 1 | 8 | 102 | medium |
| ~.diagnosis.probe_robust | 310 | 207 | 9 | 5 | 10 | 43 | medium |
| ~.diagnosis.probe_targeting | 887 | 594 | 16 | 2 | 6 | 123 | medium |
| ~.diagnosis.probes | 1606 | 1203 | 23 | 16 | 7 | 137 | deep |
| ~.diagnosis.quick_check | 437 | 337 | 5 | 2 | 15 | 73 | deep |
| ~.diagnosis.recurrence | 15 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.diagnosis.recurrence.backlog | 281 | 225 | 4 | 4 | 15 | 82 | medium |
| ~.diagnosis.recurrence.benchmarks | 1380 | 1028 | 26 | 1 | 19 | 82 | medium |
| ~.diagnosis.recurrence.display | 84 | 44 | 5 | 5 | 0 | 16 | medium |
| ~.diagnosis.recurrence.escalation | 180 | 130 | 5 | 2 | 5 | 43 | medium |
| ~.diagnosis.recurrence.guard | 722 | 563 | 15 | 3 | 18 | 113 | medium |
| ~.diagnosis.recurrence.judging | 327 | 203 | 17 | 9 | 18 | 48 | medium |
| ~.diagnosis.recurrence.kind | 185 | 145 | 4 | 6 | 4 | 66 | medium |
| ~.diagnosis.recurrence.live | 531 | 401 | 5 | 1 | 19 | 118 | deep |
| ~.diagnosis.recurrence.report | 296 | 241 | 2 | 1 | 6 | 52 | medium |
| ~.diagnosis.recurrence.upgrade | 217 | 140 | 3 | 2 | 12 | 54 | medium |
| ~.diagnosis.remediation | 1485 | 1020 | 18 | 15 | 16 | 281 | deep |
| ~.diagnosis.remediation_intake | 35 | 22 | 1 | 0 | 1 | 22 | s:re-export |
| ~.diagnosis.repair_splice | 280 | 158 | 7 | 1 | 1 | 47 | medium |
| ~.diagnosis.robust_composition | 608 | 396 | 14 | 15 | 1 | 91 | medium |
| ~.diagnosis.scoreboard | 1834 | 1213 | 17 | 7 | 16 | 122 | deep |
| ~.diagnosis.signal_quantiles | 142 | 105 | 2 | 2 | 3 | 56 | medium |
| ~.diagnosis.split | 19 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.diagnosis.split.card | 483 | 373 | 8 | 3 | 12 | 72 | deep |
| ~.diagnosis.split.context | 1032 | 798 | 19 | 9 | 10 | 291 | deep |
| ~.diagnosis.split.contract | 351 | 262 | 16 | 5 | 8 | 21 | medium |
| ~.diagnosis.split.diagnoser | 251 | 197 | 3 | 3 | 11 | 140 | medium |
| ~.diagnosis.split.embeddings | 417 | 323 | 12 | 8 | 12 | 98 | medium |
| ~.diagnosis.split.figure_trace | 146 | 99 | 1 | 3 | 3 | 83 | medium |
| ~.diagnosis.split.history | 1428 | 1060 | 13 | 10 | 13 | 297 | deep |
| ~.diagnosis.split.jobs | 1722 | 1283 | 20 | 19 | 38 | 235 | deep |
| ~.diagnosis.split.legacy_view | 215 | 174 | 3 | 3 | 2 | 35 | medium |
| ~.diagnosis.split.live | 500 | 351 | 11 | 8 | 19 | 83 | medium |
| ~.diagnosis.split.pfc_report | 438 | 379 | 6 | 1 | 14 | 110 | deep |
| ~.diagnosis.split.prior_analysis | 190 | 116 | 6 | 3 | 3 | 50 | medium |
| ~.diagnosis.split.provenance | 620 | 378 | 16 | 4 | 2 | 63 | medium |
| ~.diagnosis.split.reports | 351 | 294 | 2 | 1 | 6 | 85 | deep |
| ~.diagnosis.split.retrieval | 401 | 319 | 7 | 5 | 6 | 86 | deep |
| ~.diagnosis.split.settings | 72 | 49 | 1 | 9 | 0 | 19 | medium |
| ~.diagnosis.split.snapshot | 381 | 324 | 4 | 2 | 5 | 115 | deep |
| ~.diagnosis.split.validation | 688 | 553 | 6 | 3 | 6 | 398 | deep |
| ~.diagnosis.split.workbench_trace | 121 | 86 | 1 | 4 | 2 | 68 | medium |
| ~.diagnosis.taxonomy_regrade | 121 | 85 | 1 | 1 | 6 | 79 | medium |
| ~.diagnosis.text_gaps | 4 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.diagnosis.text_gaps.actions | 656 | 446 | 25 | 4 | 21 | 66 | wide |
| ~.diagnosis.text_gaps.candidates | 288 | 214 | 6 | 2 | 10 | 81 | medium |
| ~.diagnosis.text_gaps.contract | 410 | 254 | 4 | 10 | 4 | 10 | deep |
| ~.diagnosis.text_gaps.jobs | 821 | 519 | 23 | 14 | 14 | 162 | medium |
| ~.diagnosis.text_gaps.judges | 533 | 391 | 19 | 4 | 19 | 67 | medium |
| ~.diagnosis.text_gaps.kinds | 204 | 155 | 6 | 2 | 6 | 20 | medium |
| ~.diagnosis.text_gaps.pipeline | 1204 | 828 | 10 | 2 | 23 | 93 | deep |
| ~.diagnosis.text_gaps.provenance | 414 | 249 | 9 | 3 | 4 | 40 | medium |
| ~.diagnosis.text_gaps.report | 299 | 225 | 6 | 1 | 8 | 71 | medium |
| ~.diagnosis.text_gaps.sources | 1224 | 844 | 39 | 4 | 13 | 71 | wide |
| ~.diagnosis.text_gaps.tier1 | 306 | 213 | 4 | 1 | 12 | 68 | medium |
| ~.diagnosis.voi_forecasting | 603 | 458 | 7 | 4 | 10 | 111 | deep |
| ~.diagnosis.voi_stopping | 2504 | 1662 | 32 | 8 | 13 | 211 | wide |
| ~.eligibility_decision_upgrade | 118 | 58 | 1 | 2 | 9 | 44 | s:re-export |
| ~.evsi_calibration | 31 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.evsi_calibration.artifacts | 44 | 22 | 1 | 1 | 0 | 22 | s:re-export |
| ~.evsi_calibration.compare | 1484 | 1096 | 15 | 1 | 2 | 88 | deep |
| ~.evsi_calibration.eedi | 334 | 256 | 6 | 9 | 0 | 56 | deep |
| ~.evsi_calibration.experiments | 535 | 420 | 6 | 3 | 11 | 224 | deep |
| ~.evsi_calibration.families | 954 | 662 | 17 | 2 | 4 | 58 | medium |
| ~.evsi_calibration.family_data | 290 | 203 | 8 | 2 | 2 | 52 | medium |
| ~.evsi_calibration.family_fit | 962 | 747 | 22 | 3 | 2 | 62 | medium |
| ~.evsi_calibration.forecast_report | 904 | 649 | 10 | 2 | 16 | 56 | deep |
| ~.evsi_calibration.live_report | 1125 | 787 | 6 | 2 | 14 | 128 | deep |
| ~.evsi_calibration.metrics | 279 | 213 | 10 | 4 | 1 | 50 | medium |
| ~.evsi_calibration.multifamily | 1301 | 1036 | 6 | 1 | 12 | 323 | deep |
| ~.evsi_calibration.multisim | 413 | 323 | 9 | 1 | 7 | 160 | deep |
| ~.evsi_calibration.policies | 566 | 345 | 13 | 5 | 4 | 46 | medium |
| ~.evsi_calibration.response_fit | 580 | 457 | 6 | 6 | 1 | 87 | deep |
| ~.evsi_calibration.simulate | 376 | 309 | 10 | 4 | 6 | 146 | deep |
| ~.evsi_calibration.world | 370 | 248 | 12 | 5 | 3 | 52 | medium |
| ~.experiments | 10 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.experiments.contextual_embeddings | 30 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.experiments.contextual_embeddings.adapters | 1152 | 791 | 29 | 8 | 4 | 71 | medium |
| ~.experiments.contextual_embeddings.answers | 191 | 137 | 7 | 1 | 5 | 39 | medium |
| ~.experiments.contextual_embeddings.anthropic_api | 387 | 246 | 9 | 1 | 5 | 42 | medium |
| ~.experiments.contextual_embeddings.bank | 1086 | 773 | 36 | 10 | 9 | 96 | wide |
| ~.experiments.contextual_embeddings.boundary | 233 | 152 | 10 | 5 | 5 | 33 | medium |
| ~.experiments.contextual_embeddings.budget | 773 | 501 | 19 | 14 | 2 | 55 | medium |
| ~.experiments.contextual_embeddings.callers | 629 | 421 | 15 | 6 | 10 | 87 | medium |
| ~.experiments.contextual_embeddings.corpus | 976 | 692 | 32 | 15 | 12 | 112 | wide |
| ~.experiments.contextual_embeddings.credentials | 115 | 63 | 5 | 4 | 0 | 28 | medium |
| ~.experiments.contextual_embeddings.delivery | 392 | 280 | 12 | 3 | 4 | 35 | medium |
| ~.experiments.contextual_embeddings.e1 | 27 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.experiments.contextual_embeddings.e1.decide | 137 | 100 | 2 | 1 | 3 | 80 | medium |
| ~.experiments.contextual_embeddings.e1.gpu_meter | 191 | 138 | 3 | 2 | 1 | 45 | medium |
| ~.experiments.contextual_embeddings.e1.ledger | 91 | 61 | 5 | 2 | 2 | 19 | medium |
| ~.experiments.contextual_embeddings.e1.local | 315 | 231 | 13 | 3 | 8 | 49 | medium |
| ~.experiments.contextual_embeddings.e1.pins | 261 | 150 | 4 | 8 | 1 | 18 | medium |
| ~.experiments.contextual_embeddings.e1.plan | 311 | 246 | 7 | 2 | 6 | 59 | medium |
| ~.experiments.contextual_embeddings.e1.replay | 514 | 358 | 20 | 3 | 16 | 47 | wide |
| ~.experiments.contextual_embeddings.e1.report | 52 | 42 | 1 | 1 | 1 | 28 | s:thin |
| ~.experiments.contextual_embeddings.e1.run | 486 | 375 | 17 | 1 | 20 | 71 | medium |
| ~.experiments.contextual_embeddings.e1.supplement | 346 | 268 | 13 | 1 | 8 | 54 | medium |
| ~.experiments.contextual_embeddings.e1.worker | 854 | 631 | 30 | 2 | 0 | 85 | wide |
| ~.experiments.contextual_embeddings.evaluate | 95 | 65 | 5 | 4 | 4 | 35 | medium |
| ~.experiments.contextual_embeddings.live | 271 | 169 | 7 | 3 | 15 | 111 | medium |
| ~.experiments.contextual_embeddings.metrics | 182 | 122 | 10 | 5 | 1 | 35 | medium |
| ~.experiments.contextual_embeddings.paid | 689 | 525 | 15 | 4 | 14 | 248 | medium |
| ~.experiments.contextual_embeddings.pins | 576 | 347 | 10 | 25 | 0 | 21 | deep |
| ~.experiments.contextual_embeddings.plan | 506 | 373 | 11 | 1 | 6 | 78 | medium |
| ~.experiments.contextual_embeddings.records | 110 | 64 | 1 | 3 | 6 | 18 | medium |
| ~.experiments.contextual_embeddings.report | 182 | 149 | 3 | 4 | 2 | 118 | medium |
| ~.experiments.contextual_embeddings.retrieval | 329 | 219 | 11 | 6 | 6 | 24 | medium |
| ~.experiments.contextual_embeddings.runner | 643 | 498 | 14 | 5 | 10 | 139 | medium |
| ~.experiments.contextual_embeddings.stop_rules | 191 | 133 | 7 | 3 | 1 | 34 | medium |
| ~.experiments.contextual_embeddings.system_arms | 912 | 556 | 17 | 2 | 25 | 113 | medium |
| ~.field | 21 | 17 | 0 | 0 | 1 | 0 | init/re-export |
| ~.field.answer_signals | 392 | 253 | 6 | 2 | 2 | 62 | deep |
| ~.field.classification | 233 | 186 | 2 | 1 | 6 | 161 | medium |
| ~.field.decider | 110 | 74 | 2 | 1 | 4 | 28 | s:one-caller helper |
| ~.field.evaluation | 837 | 663 | 7 | 5 | 10 | 362 | deep |
| ~.field.item_content | 175 | 131 | 3 | 1 | 6 | 74 | medium |
| ~.field.memory | 45 | 24 | 1 | 1 | 3 | 11 | s:one-caller helper |
| ~.field.outcomes | 916 | 692 | 13 | 6 | 23 | 277 | deep |
| ~.field.predictors | 560 | 451 | 8 | 8 | 4 | 71 | deep |
| ~.field.priors | 63 | 45 | 1 | 1 | 2 | 48 | s:re-export |
| ~.field.probability_arms | 211 | 137 | 7 | 5 | 1 | 27 | medium |
| ~.field.probability_prep | 676 | 517 | 12 | 1 | 14 | 222 | deep |
| ~.field.probability_states | 807 | 584 | 8 | 2 | 6 | 130 | deep |
| ~.field.signals | 625 | 403 | 10 | 6 | 6 | 224 | deep |
| ~.field.success_head | 502 | 363 | 7 | 3 | 3 | 31 | deep |
| ~.field.success_head_analysis | 313 | 232 | 2 | 1 | 2 | 75 | medium |
| ~.field.types | 238 | 156 | 10 | 18 | 0 | 11 | medium |
| ~.field.workbench_signals | 358 | 216 | 4 | 3 | 2 | 81 | medium |
| ~.figure_admission | 459 | 216 | 23 | 18 | 5 | 47 | wide |
| ~.figures | 29 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.figures.book_math | 1302 | 970 | 7 | 2 | 2 | 52 | deep |
| ~.figures.display_format | 127 | 86 | 2 | 3 | 0 | 35 | medium |
| ~.figures.elements | 604 | 427 | 11 | 2 | 4 | 86 | medium |
| ~.figures.foreground | 88 | 50 | 4 | 5 | 0 | 14 | medium |
| ~.figures.grammar | 821 | 558 | 17 | 9 | 0 | 79 | medium |
| ~.figures.help | 462 | 282 | 8 | 3 | 10 | 54 | deep |
| ~.figures.katex_tree | 185 | 107 | 2 | 2 | 1 | 21 | medium |
| ~.figures.labels | 321 | 171 | 6 | 3 | 1 | 21 | medium |
| ~.figures.learner_state | 465 | 284 | 10 | 3 | 8 | 49 | deep |
| ~.figures.manim_figure | 931 | 674 | 16 | 2 | 4 | 119 | deep |
| ~.figures.power | 318 | 195 | 9 | 5 | 1 | 49 | medium |
| ~.figures.prefetch | 1749 | 1172 | 35 | 1 | 30 | 73 | wide |
| ~.figures.prefetch_ledger | 466 | 309 | 21 | 4 | 3 | 46 | wide |
| ~.figures.prefetch_model | 504 | 310 | 15 | 2 | 1 | 26 | medium |
| ~.figures.rich | 1172 | 747 | 32 | 5 | 24 | 117 | wide |
| ~.figures.routes | 614 | 405 | 17 | 3 | 10 | 28 | medium |
| ~.figures.service | 3906 | 2443 | 76 | 10 | 38 | 271 | wide |
| ~.figures.sketch | 911 | 642 | 28 | 4 | 2 | 159 | medium |
| ~.figures.sketch_engine | 501 | 319 | 8 | 3 | 0 | 36 | deep |
| ~.figures.sketch_verify | 819 | 554 | 7 | 1 | 4 | 187 | deep |
| ~.figures.source_check | 1093 | 797 | 25 | 3 | 17 | 115 | medium |
| ~.figures.source_check_harness | 814 | 633 | 37 | 0 | 1 | 75 | wide |
| ~.figures.spec | 1240 | 916 | 46 | 7 | 1 | 71 | wide |
| ~.figures.verify | 468 | 315 | 13 | 4 | 2 | 35 | medium |
| ~.followup_run | 7 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.followup_run.admission | 435 | 331 | 10 | 2 | 16 | 98 | deep |
| ~.followup_run.authoring | 291 | 199 | 11 | 3 | 7 | 65 | medium |
| ~.followup_run.decision_view | 106 | 73 | 2 | 2 | 2 | 56 | medium |
| ~.followup_run.jobs | 497 | 362 | 8 | 4 | 21 | 101 | deep |
| ~.followup_run.lanes | 113 | 73 | 5 | 3 | 8 | 37 | medium |
| ~.followup_run.lesson_probe | 197 | 130 | 5 | 1 | 11 | 87 | medium |
| ~.followup_run.marks | 354 | 257 | 9 | 3 | 10 | 66 | deep |
| ~.followup_run.router | 358 | 260 | 10 | 2 | 18 | 74 | deep |
| ~.followup_run.serving | 294 | 198 | 12 | 6 | 12 | 50 | medium |
| ~.followup_serve | 7 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.followup_serve.gates | 55 | 22 | 3 | 23 | 1 | 9 | s:thin |
| ~.followup_serve.identity | 325 | 196 | 17 | 19 | 3 | 47 | medium |
| ~.followup_serve.marks | 133 | 75 | 7 | 7 | 1 | 24 | medium |
| ~.followup_serve.queue | 87 | 45 | 8 | 8 | 3 | 9 | medium |
| ~.followup_serve.workflow | 522 | 351 | 22 | 16 | 7 | 47 | wide |
| ~.followup_serve_upgrade | 278 | 157 | 2 | 2 | 13 | 50 | medium |
| ~.goals | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.goals.certification | 8 | 3 | 1 | 7 | 0 | 2 | s:thin |
| ~.goals.certification_cold_probe | 1963 | 1269 | 17 | 5 | 16 | 244 | deep |
| ~.goals.exam_calibration | 174 | 129 | 1 | 3 | 4 | 99 | medium |
| ~.goals.exam_pool | 595 | 344 | 7 | 6 | 16 | 166 | deep |
| ~.goals.exam_readiness | 246 | 165 | 3 | 2 | 5 | 135 | medium |
| ~.goals.exam_seeding | 468 | 363 | 10 | 2 | 7 | 178 | deep |
| ~.goals.exam_session | 916 | 641 | 10 | 3 | 13 | 114 | deep |
| ~.goals.forecast_ledger | 283 | 238 | 6 | 3 | 6 | 69 | medium |
| ~.goals.goal_certification | 329 | 193 | 8 | 12 | 6 | 89 | medium |
| ~.goals.goal_contracts | 936 | 674 | 24 | 11 | 8 | 150 | medium |
| ~.goals.goal_intent | 57 | 34 | 2 | 2 | 1 | 33 | s:re-export |
| ~.goals.goal_lo | 191 | 120 | 8 | 1 | 6 | 43 | medium |
| ~.goals.goal_pace | 101 | 72 | 2 | 2 | 4 | 52 | medium |
| ~.goals.goal_projection | 905 | 623 | 12 | 23 | 15 | 134 | deep |
| ~.goals.goal_series | 248 | 193 | 2 | 2 | 7 | 33 | medium |
| ~.goals.goal_series_store | 110 | 89 | 1 | 1 | 1 | 44 | medium |
| ~.goals.receipt_contributions | 132 | 94 | 3 | 2 | 1 | 72 | medium |
| ~.goals.use_weights | 99 | 60 | 4 | 4 | 1 | 25 | medium |
| ~.grading_epochs | 206 | 97 | 8 | 9 | 0 | 22 | medium |
| ~.held_grades | 285 | 163 | 9 | 50 | 1 | 68 | medium |
| ~.help_fold_attach_upgrade | 282 | 157 | 2 | 2 | 13 | 50 | medium |
| ~.hint_window | 121 | 44 | 4 | 3 | 0 | 14 | medium |
| ~.hints | 20 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.hints.chooser | 450 | 313 | 12 | 2 | 10 | 115 | medium |
| ~.hints.contracts | 546 | 355 | 16 | 4 | 3 | 128 | medium |
| ~.hints.discriminating | 260 | 150 | 10 | 3 | 3 | 30 | medium |
| ~.hints.kinds | 192 | 123 | 5 | 7 | 0 | 19 | medium |
| ~.hints.map_builder | 1641 | 1121 | 21 | 12 | 17 | 80 | deep |
| ~.hints.map_report | 113 | 93 | 1 | 1 | 7 | 77 | medium |
| ~.hints.map_seeds | 328 | 230 | 12 | 2 | 10 | 33 | medium |
| ~.hints.maps | 899 | 558 | 27 | 5 | 3 | 112 | medium |
| ~.hints.options | 206 | 129 | 4 | 3 | 2 | 77 | medium |
| ~.hints.outcome | 697 | 470 | 12 | 2 | 15 | 108 | medium |
| ~.hints.report | 827 | 559 | 2 | 1 | 5 | 391 | deep |
| ~.hints.report_adaptive | 338 | 246 | 11 | 3 | 0 | 60 | medium |
| ~.hints.report_workbench | 464 | 307 | 2 | 2 | 3 | 166 | deep |
| ~.hints.service | 1268 | 903 | 18 | 4 | 25 | 146 | deep |
| ~.hints.state | 427 | 308 | 6 | 5 | 10 | 52 | deep |
| ~.hints.telemetry | 203 | 129 | 8 | 1 | 4 | 45 | medium |
| ~.hints.workbench | 1189 | 754 | 37 | 5 | 14 | 70 | wide |
| ~.hints.writer | 408 | 289 | 11 | 4 | 6 | 76 | medium |
| ~.ids | 110 | 67 | 4 | 170 | 0 | 21 | medium |
| ~.ingest | 33 | 21 | 0 | 0 | 3 | 0 | init/re-export |
| ~.ingest.block_roles | 379 | 237 | 9 | 12 | 0 | 33 | medium |
| ~.ingest.detect | 14 | 4 | 1 | 1 | 1 | 8 | s:thin |
| ~.ingest.extractors | 212 | 150 | 6 | 4 | 7 | 60 | medium |
| ~.ingest.extractors.base | 177 | 119 | 5 | 6 | 2 | 93 | medium |
| ~.ingest.extractors.datalab | 206 | 159 | 3 | 1 | 3 | 44 | medium |
| ~.ingest.extractors.glm_ocr | 1526 | 1099 | 11 | 8 | 9 | 136 | deep |
| ~.ingest.extractors.glm_text_layer | 683 | 449 | 13 | 1 | 0 | 72 | medium |
| ~.ingest.extractors.marker | 409 | 281 | 5 | 3 | 5 | 80 | deep |
| ~.ingest.extractors.marker_worker | 484 | 311 | 2 | 2 | 2 | 56 | deep |
| ~.ingest.extractors.normalizers | 413 | 326 | 3 | 1 | 3 | 110 | deep |
| ~.ingest.extractors.pypdf | 193 | 135 | 3 | 4 | 3 | 80 | medium |
| ~.ingest.fetchers | 401 | 308 | 13 | 3 | 2 | 50 | medium |
| ~.ingest.hashing | 181 | 111 | 6 | 12 | 1 | 29 | medium |
| ~.ingest.ir | 397 | 247 | 12 | 18 | 0 | 55 | medium |
| ~.ingest.locators | 70 | 30 | 3 | 28 | 0 | 20 | s:thin |
| ~.ingest.models | 80 | 52 | 6 | 8 | 0 | 15 | medium |
| ~.ingest.originals | 111 | 58 | 6 | 10 | 1 | 25 | medium |
| ~.ingest.reanchor | 239 | 176 | 5 | 6 | 1 | 38 | medium |
| ~.ingest.resolution | 81 | 60 | 3 | 7 | 1 | 46 | medium |
| ~.ingest.transcription | 133 | 96 | 4 | 1 | 2 | 66 | medium |
| ~.ingest.transcripts | 122 | 75 | 3 | 2 | 0 | 36 | medium |
| ~.instructional | 14 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.instructional.discriminating | 231 | 166 | 3 | 2 | 8 | 106 | medium |
| ~.instructional.exercises | 324 | 237 | 7 | 4 | 9 | 75 | medium |
| ~.instructional.exposure | 392 | 292 | 6 | 4 | 17 | 93 | deep |
| ~.instructional.harvest | 319 | 255 | 4 | 1 | 16 | 97 | deep |
| ~.instructional.interventions | 516 | 394 | 11 | 10 | 13 | 68 | medium |
| ~.instructional.needs | 333 | 236 | 5 | 4 | 19 | 176 | medium |
| ~.instructional.offers | 59 | 33 | 1 | 1 | 3 | 31 | s:re-export |
| ~.instructional.policy | 183 | 111 | 8 | 14 | 7 | 34 | medium |
| ~.instructional.practice | 486 | 305 | 14 | 7 | 20 | 57 | medium |
| ~.instructional.reader_digest | 907 | 533 | 27 | 2 | 18 | 69 | wide |
| ~.instructional.reader_followups | 1909 | 1312 | 32 | 3 | 35 | 196 | wide |
| ~.instructional.screen | 224 | 174 | 7 | 3 | 14 | 90 | medium |
| ~.instructional.sources | 206 | 125 | 9 | 9 | 8 | 30 | medium |
| ~.instructional.tools | 690 | 537 | 19 | 5 | 18 | 89 | medium |
| ~.instructional.validation | 12 | 3 | 0 | 2 | 1 | 0 | s:thin |
| ~.instructional.valuation | 1204 | 898 | 26 | 6 | 16 | 143 | medium |
| ~.instructional.wiring | 58 | 30 | 2 | 7 | 4 | 29 | s:thin |
| ~.intent | 14 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.intent.checks | 273 | 169 | 6 | 6 | 4 | 33 | medium |
| ~.intent.control | 520 | 412 | 11 | 4 | 6 | 76 | medium |
| ~.intent.deadline | 172 | 113 | 2 | 1 | 10 | 91 | medium |
| ~.intent.report | 75 | 58 | 1 | 1 | 4 | 50 | s:re-export |
| ~.intent_upgrade | 120 | 60 | 1 | 2 | 9 | 44 | s:re-export |
| ~.interval_factor_upgrade | 265 | 149 | 2 | 2 | 13 | 52 | medium |
| ~.learner | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.learner.assessment_contracts | 253 | 180 | 5 | 25 | 7 | 101 | medium |
| ~.learner.blueprint_projection | 393 | 262 | 10 | 6 | 2 | 57 | deep |
| ~.learner.calibration | 111 | 80 | 2 | 1 | 2 | 61 | s:one-caller helper |
| ~.learner.capability_grid | 232 | 167 | 4 | 3 | 12 | 98 | medium |
| ~.learner.capability_mapping | 358 | 199 | 14 | 24 | 1 | 45 | medium |
| ~.learner.contract_reachability | 723 | 407 | 9 | 11 | 3 | 59 | deep |
| ~.learner.facet_diagnostics | 850 | 624 | 16 | 25 | 11 | 97 | medium |
| ~.learner.facet_evidence_timeline | 1262 | 862 | 14 | 6 | 16 | 211 | deep |
| ~.learner.facet_state_reader | 302 | 206 | 7 | 21 | 3 | 49 | medium |
| ~.learner.familiarity | 528 | 315 | 10 | 6 | 2 | 82 | deep |
| ~.learner.hypothesis_claims | 278 | 221 | 7 | 3 | 3 | 126 | medium |
| ~.learner.identifiability | 1066 | 766 | 12 | 9 | 1 | 127 | deep |
| ~.learner.independence_audit | 279 | 169 | 4 | 1 | 6 | 75 | medium |
| ~.learner.inference_precheck | 579 | 450 | 7 | 2 | 2 | 60 | deep |
| ~.learner.learner_profile | 92 | 58 | 3 | 4 | 4 | 28 | medium |
| ~.learner.learner_review_feed | 269 | 191 | 1 | 1 | 6 | 51 | medium |
| ~.learner.lesson_weight | 1099 | 742 | 22 | 10 | 6 | 76 | medium |
| ~.learner.mastery | 1052 | 668 | 26 | 42 | 7 | 73 | medium |
| ~.learner.mastery_step_attribution | 217 | 144 | 3 | 1 | 0 | 110 | medium |
| ~.learner.measurement_state | 122 | 30 | 2 | 3 | 0 | 41 | s:thin |
| ~.learner.overconfidence | 118 | 83 | 3 | 4 | 4 | 42 | medium |
| ~.learner.recall_calibration | 350 | 318 | 4 | 1 | 12 | 81 | deep |
| ~.learner.recall_coverage | 1027 | 856 | 22 | 11 | 12 | 103 | medium |
| ~.learner.residual_diagnostics | 310 | 244 | 1 | 1 | 6 | 50 | medium |
| ~.learner.session_learning_diff | 160 | 136 | 2 | 2 | 4 | 108 | medium |
| ~.learner.surfaced_beliefs | 405 | 229 | 8 | 8 | 2 | 71 | medium |
| ~.learner_context | 1733 | 1168 | 19 | 5 | 11 | 85 | deep |
| ~.learner_protection | 748 | 439 | 15 | 24 | 6 | 58 | medium |
| ~.learner_text_gap_upgrade | 134 | 75 | 1 | 2 | 9 | 53 | s:re-export |
| ~.lesson_offers_upgrade | 226 | 157 | 2 | 2 | 13 | 46 | medium |
| ~.lesson_opportunity_upgrade | 226 | 157 | 2 | 2 | 13 | 46 | medium |
| ~.lesson_suggestions_upgrade | 286 | 157 | 2 | 2 | 13 | 50 | medium |
| ~.local_embeddings | 12 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.local_embeddings.cache | 174 | 123 | 3 | 3 | 1 | 20 | medium |
| ~.local_embeddings.fusion | 561 | 343 | 16 | 5 | 1 | 49 | medium |
| ~.local_embeddings.gpu_meter | 193 | 141 | 3 | 3 | 1 | 45 | medium |
| ~.local_embeddings.identity | 58 | 28 | 4 | 3 | 1 | 7 | medium |
| ~.local_embeddings.launcher | 125 | 81 | 6 | 3 | 3 | 26 | medium |
| ~.local_embeddings.pins | 161 | 106 | 5 | 8 | 0 | 11 | medium |
| ~.local_embeddings.setup | 202 | 146 | 4 | 3 | 2 | 63 | medium |
| ~.local_embeddings.student_decision | 360 | 219 | 15 | 2 | 0 | 26 | medium |
| ~.local_embeddings.student_pins | 203 | 119 | 4 | 5 | 0 | 6 | medium |
| ~.local_embeddings.student_server | 343 | 241 | 11 | 1 | 2 | 42 | medium |
| ~.local_embeddings.student_trainer | 469 | 349 | 13 | 2 | 1 | 120 | medium |
| ~.local_embeddings.worker | 967 | 722 | 33 | 5 | 0 | 87 | wide |
| ~.matching | 34 | 22 | 0 | 0 | 4 | 0 | init/re-export |
| ~.matching.judge | 351 | 241 | 9 | 8 | 10 | 113 | medium |
| ~.matching.kinds | 116 | 54 | 3 | 9 | 0 | 7 | medium |
| ~.matching.shortlist | 304 | 206 | 10 | 6 | 2 | 63 | medium |
| ~.matching.union | 196 | 126 | 6 | 4 | 0 | 61 | medium |
| ~.method_explicit_upgrade | 121 | 58 | 1 | 2 | 9 | 45 | s:re-export |
| ~.migration_coordinator | 108 | 64 | 2 | 3 | 5 | 33 | medium |
| ~.numeric | 242 | 152 | 10 | 20 | 0 | 47 | medium |
| ~.one_ask_upgrade | 296 | 157 | 2 | 2 | 13 | 50 | medium |
| ~.ops | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.ops.capture_report | 632 | 506 | 8 | 1 | 13 | 88 | deep |
| ~.ops.contamination | 14 | 3 | 0 | 0 | 2 | 0 | init/re-export |
| ~.ops.contamination.decider | 58 | 34 | 2 | 1 | 5 | 22 | s:thin |
| ~.ops.contamination.detectors | 571 | 446 | 8 | 3 | 11 | 80 | deep |
| ~.ops.contamination.judge | 416 | 315 | 11 | 2 | 14 | 160 | medium |
| ~.ops.contamination.recipes | 147 | 100 | 4 | 4 | 6 | 22 | medium |
| ~.ops.contamination.report | 582 | 481 | 3 | 2 | 15 | 213 | deep |
| ~.ops.contamination.symbolic | 316 | 207 | 8 | 2 | 1 | 55 | medium |
| ~.ops.content_fixes | 196 | 133 | 1 | 1 | 3 | 111 | medium |
| ~.ops.debug_time | 76 | 61 | 3 | 1 | 3 | 24 | s:one-caller helper |
| ~.ops.debug_time_store | 49 | 34 | 2 | 1 | 1 | 17 | s:thin |
| ~.ops.doctor | 2909 | 2368 | 5 | 2 | 41 | 188 | deep |
| ~.ops.embedding_backfill | 387 | 301 | 3 | 13 | 13 | 228 | deep |
| ~.ops.embedding_compare | 900 | 710 | 20 | 3 | 15 | 121 | medium |
| ~.ops.family_proposals | 639 | 544 | 5 | 2 | 19 | 264 | deep |
| ~.ops.graph_nomination_report | 362 | 298 | 5 | 1 | 10 | 84 | deep |
| ~.ops.maintenance_feed | 515 | 364 | 5 | 3 | 6 | 82 | deep |
| ~.ops.pf_calls | 646 | 473 | 11 | 10 | 9 | 143 | deep |
| ~.ops.pf_generation | 2202 | 1790 | 10 | 2 | 26 | 170 | deep |
| ~.ops.pf_publish | 573 | 385 | 14 | 1 | 18 | 93 | medium |
| ~.ops.pf_reports | 643 | 494 | 5 | 1 | 13 | 60 | deep |
| ~.ops.pf_selection | 89 | 57 | 6 | 1 | 0 | 21 | s:one-caller helper |
| ~.ops.pf_verify | 293 | 196 | 7 | 2 | 4 | 81 | medium |
| ~.ops.plan_transport | 180 | 111 | 5 | 2 | 6 | 42 | medium |
| ~.ops.settings_store | 316 | 208 | 8 | 9 | 1 | 61 | medium |
| ~.ops.startup | 111 | 78 | 2 | 3 | 11 | 72 | medium |
| ~.ops.vault_lock | 4 | 1 | 0 | 2 | 1 | 0 | s:thin |
| ~.ops.vault_upgrade | 511 | 338 | 10 | 43 | 11 | 88 | deep |
| ~.outcome_contract | 214 | 88 | 5 | 31 | 0 | 39 | medium |
| ~.params | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.params.fitted_params | 125 | 66 | 4 | 24 | 2 | 26 | medium |
| ~.params.parameter_registry | 3627 | 2674 | 15 | 47 | 5 | 99 | deep |
| ~.params.sensitivity_certificates | 395 | 255 | 14 | 3 | 5 | 42 | medium |
| ~.phone_probes_upgrade | 224 | 157 | 2 | 3 | 13 | 46 | medium |
| ~.placement | 8 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.placement.claim_check | 72 | 30 | 1 | 1 | 4 | 26 | s:re-export |
| ~.placement.decisions | 754 | 600 | 13 | 4 | 13 | 100 | deep |
| ~.placement.field_receipts | 70 | 42 | 2 | 1 | 2 | 33 | s:thin |
| ~.placement.predictor | 181 | 125 | 3 | 8 | 4 | 35 | medium |
| ~.placement.report | 396 | 342 | 2 | 1 | 4 | 229 | deep |
| ~.placement.rules | 502 | 253 | 13 | 4 | 1 | 34 | medium |
| ~.placement.signals | 108 | 65 | 4 | 3 | 5 | 19 | medium |
| ~.placement.state | 1553 | 1015 | 26 | 33 | 10 | 219 | medium |
| ~.practice_index | 6 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.practice_index.admission | 154 | 101 | 1 | 2 | 8 | 36 | medium |
| ~.practice_index.catalog | 42 | 22 | 4 | 7 | 1 | 8 | medium |
| ~.practice_index.contracts | 98 | 53 | 10 | 3 | 1 | 0 | s:re-export |
| ~.practice_index.coverage | 93 | 70 | 3 | 3 | 5 | 41 | medium |
| ~.practice_index.dossiers | 580 | 482 | 8 | 2 | 18 | 125 | deep |
| ~.practice_index.evaluation | 898 | 757 | 7 | 3 | 19 | 137 | deep |
| ~.practice_index.listwise | 299 | 203 | 10 | 13 | 11 | 110 | medium |
| ~.practice_index.paid | 688 | 464 | 13 | 48 | 13 | 105 | medium |
| ~.practice_index.query_vectors | 243 | 188 | 8 | 8 | 11 | 101 | medium |
| ~.practice_index.retrieval | 1751 | 1384 | 26 | 12 | 25 | 344 | deep |
| ~.practice_index.text | 97 | 68 | 3 | 5 | 0 | 19 | medium |
| ~.practice_index.tool | 56 | 36 | 2 | 1 | 3 | 5 | s:re-export |
| ~.practice_index.usage | 149 | 112 | 3 | 4 | 6 | 35 | medium |
| ~.probe_tie_upgrade | 124 | 71 | 1 | 2 | 9 | 51 | s:re-export |
| ~.projects | 15 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.projects.ai_contracts | 228 | 168 | 13 | 2 | 2 | 6 | medium |
| ~.projects.ai_runtime | 507 | 370 | 9 | 2 | 10 | 111 | deep |
| ~.projects.capture | 1270 | 1045 | 23 | 5 | 8 | 102 | deep |
| ~.projects.experiment_store | 978 | 804 | 4 | 6 | 3 | 37 | deep |
| ~.projects.git | 142 | 96 | 7 | 3 | 0 | 34 | medium |
| ~.projects.hooks | 158 | 109 | 5 | 1 | 2 | 28 | medium |
| ~.projects.probes | 1197 | 951 | 27 | 1 | 10 | 84 | medium |
| ~.projects.redaction | 361 | 254 | 7 | 2 | 0 | 30 | deep |
| ~.projects.report | 444 | 390 | 4 | 1 | 5 | 174 | deep |
| ~.proof_check_upgrade | 142 | 78 | 1 | 2 | 9 | 54 | s:re-export |
| ~.reader | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.reader.active_reading | 157 | 94 | 6 | 1 | 5 | 32 | medium |
| ~.reader.ai_contracts | 233 | 187 | 10 | 2 | 2 | 6 | medium |
| ~.reader.annotations | 694 | 514 | 10 | 5 | 5 | 93 | deep |
| ~.reader.as_printed | 931 | 526 | 9 | 2 | 6 | 79 | deep |
| ~.reader.reader_authoring | 652 | 476 | 8 | 2 | 13 | 118 | deep |
| ~.reader.reader_capture | 465 | 345 | 6 | 2 | 7 | 111 | deep |
| ~.reader.reader_cues | 621 | 420 | 19 | 4 | 9 | 83 | medium |
| ~.reader.reader_dialogue | 1422 | 938 | 19 | 17 | 14 | 364 | deep |
| ~.reader.reader_guidance | 630 | 464 | 4 | 15 | 6 | 86 | deep |
| ~.reader.reader_inquiry | 456 | 306 | 5 | 1 | 8 | 50 | deep |
| ~.reader.reader_intent | 835 | 560 | 17 | 1 | 14 | 100 | medium |
| ~.reader.reader_observations | 317 | 225 | 7 | 2 | 3 | 47 | medium |
| ~.reader.reader_progression | 240 | 187 | 3 | 20 | 7 | 120 | medium |
| ~.reader.reader_quick_check | 1270 | 940 | 24 | 4 | 16 | 119 | medium |
| ~.reader.reader_report | 970 | 738 | 1 | 1 | 5 | 587 | deep |
| ~.reader.reader_requests | 787 | 564 | 14 | 4 | 8 | 124 | deep |
| ~.reader.reader_restoration | 179 | 121 | 3 | 1 | 7 | 96 | medium |
| ~.reader.reader_sessions | 246 | 159 | 10 | 6 | 1 | 31 | medium |
| ~.reader.recap | 917 | 635 | 15 | 7 | 13 | 140 | deep |
| ~.reader.source_identity | 308 | 200 | 10 | 2 | 0 | 44 | medium |
| ~.reader.source_objects | 530 | 374 | 15 | 6 | 7 | 120 | medium |
| ~.reader.source_render_views | 248 | 179 | 6 | 3 | 2 | 58 | medium |
| ~.reader.source_review | 252 | 200 | 1 | 1 | 3 | 51 | medium |
| ~.reader.source_roles | 516 | 338 | 15 | 8 | 8 | 79 | medium |
| ~.reader.source_search | 88 | 66 | 1 | 3 | 2 | 46 | medium |
| ~.reader.span_view | 494 | 371 | 4 | 9 | 4 | 106 | deep |
| ~.reader.workbench | 1638 | 1100 | 54 | 12 | 8 | 112 | wide |
| ~.reader_followups_upgrade | 280 | 157 | 2 | 2 | 13 | 50 | medium |
| ~.reader_learner_state | 283 | 186 | 4 | 1 | 6 | 69 | medium |
| ~.reading_path_plan_upgrade | 119 | 59 | 1 | 2 | 9 | 44 | s:re-export |
| ~.reading_sources | 336 | 250 | 4 | 5 | 3 | 45 | deep |
| ~.recurrence | 93 | 32 | 5 | 10 | 0 | 11 | medium |
| ~.regrade_contract_upgrade | 274 | 134 | 1 | 23 | 13 | 77 | medium |
| ~.remote | 18 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.remote.endpoint_token | 239 | 151 | 11 | 4 | 0 | 28 | medium |
| ~.remote.errors | 30 | 12 | 3 | 3 | 0 | 4 | s:thin |
| ~.remote.runtime | 205 | 118 | 5 | 3 | 9 | 18 | medium |
| ~.remote.sources | 429 | 284 | 4 | 1 | 20 | 84 | deep |
| ~.remote.telemetry | 240 | 171 | 6 | 4 | 4 | 59 | medium |
| ~.remote.views | 392 | 301 | 5 | 1 | 12 | 72 | deep |
| ~.replay_ledger_upgrade | 292 | 151 | 2 | 2 | 12 | 54 | medium |
| ~.reveal_coverage | 158 | 55 | 8 | 8 | 0 | 23 | medium |
| ~.route_rules_upgrade | 116 | 57 | 1 | 2 | 9 | 45 | s:re-export |
| ~.router | 10 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.router.agreement | 120 | 79 | 2 | 1 | 0 | 31 | s:one-caller helper |
| ~.router.card | 685 | 475 | 7 | 1 | 1 | 102 | deep |
| ~.router.decisions | 676 | 498 | 7 | 2 | 3 | 260 | deep |
| ~.router.first_delayed_success | 454 | 347 | 3 | 2 | 4 | 81 | deep |
| ~.router.lesson_suggestions | 631 | 369 | 21 | 2 | 2 | 32 | wide |
| ~.router.mixture | 258 | 160 | 12 | 9 | 0 | 23 | medium |
| ~.router.outcomes | 1490 | 1086 | 7 | 6 | 8 | 202 | deep |
| ~.router.plan_log | 807 | 591 | 7 | 3 | 4 | 236 | deep |
| ~.router.requests | 702 | 499 | 30 | 3 | 2 | 38 | wide |
| ~.router.suggestion_report | 164 | 112 | 2 | 1 | 0 | 71 | medium |
| ~.router.why | 365 | 254 | 9 | 5 | 0 | 30 | deep |
| ~.router_calibration_upgrade | 229 | 157 | 2 | 2 | 13 | 46 | medium |
| ~.router_followups_upgrade | 221 | 157 | 2 | 2 | 13 | 46 | medium |
| ~.router_learned_tail_upgrade | 226 | 157 | 2 | 2 | 13 | 46 | medium |
| ~.router_mixture_upgrade | 104 | 57 | 1 | 2 | 9 | 41 | s:re-export |
| ~.router_objective | 16 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.router_objective.ask_availability | 93 | 61 | 3 | 2 | 5 | 29 | medium |
| ~.router_objective.assignments | 118 | 70 | 5 | 6 | 2 | 21 | medium |
| ~.router_objective.calibration_report | 214 | 175 | 5 | 1 | 8 | 38 | medium |
| ~.router_objective.checks | 752 | 506 | 18 | 8 | 8 | 70 | medium |
| ~.router_objective.cold_timing | 66 | 42 | 2 | 1 | 0 | 11 | s:thin |
| ~.router_objective.combiner_data | 189 | 122 | 2 | 1 | 2 | 55 | medium |
| ~.router_objective.decision_state | 377 | 280 | 4 | 6 | 6 | 63 | deep |
| ~.router_objective.exposure | 138 | 91 | 5 | 12 | 2 | 20 | medium |
| ~.router_objective.forecast_resolve | 176 | 126 | 3 | 2 | 1 | 55 | medium |
| ~.router_objective.goal_lifecycle | 99 | 65 | 2 | 1 | 4 | 25 | s:one-caller helper |
| ~.router_objective.goal_read | 225 | 162 | 6 | 1 | 3 | 44 | medium |
| ~.router_objective.learned_tail | 789 | 507 | 24 | 3 | 0 | 68 | medium |
| ~.router_objective.memory | 324 | 202 | 8 | 3 | 0 | 51 | medium |
| ~.router_objective.mix | 134 | 81 | 9 | 1 | 1 | 17 | medium |
| ~.router_objective.objective_report | 236 | 177 | 2 | 1 | 4 | 96 | medium |
| ~.router_objective.offer_report | 127 | 100 | 3 | 1 | 0 | 48 | medium |
| ~.router_objective.picks | 145 | 108 | 3 | 3 | 2 | 76 | medium |
| ~.router_objective.price | 265 | 165 | 9 | 5 | 0 | 38 | medium |
| ~.router_objective.question_state | 176 | 126 | 1 | 1 | 1 | 45 | medium |
| ~.router_objective.report | 248 | 195 | 2 | 1 | 2 | 34 | medium |
| ~.router_objective.scores | 638 | 383 | 16 | 4 | 5 | 64 | medium |
| ~.router_objective.sessions | 273 | 194 | 5 | 2 | 4 | 29 | medium |
| ~.router_objective.stop_coin | 646 | 400 | 15 | 6 | 3 | 86 | medium |
| ~.router_objective.tail_data | 930 | 610 | 25 | 3 | 9 | 119 | medium |
| ~.router_objective.tail_report | 200 | 162 | 2 | 1 | 2 | 69 | medium |
| ~.router_objective.tail_serve | 328 | 181 | 15 | 1 | 4 | 52 | medium |
| ~.router_objective.trace | 196 | 140 | 3 | 5 | 2 | 79 | medium |
| ~.router_objective.trajectory | 105 | 71 | 1 | 2 | 0 | 4 | medium |
| ~.router_objective.value | 1652 | 1104 | 17 | 2 | 1 | 114 | deep |
| ~.router_objective.weight | 198 | 124 | 9 | 3 | 0 | 38 | medium |
| ~.router_objective_switches | 391 | 178 | 27 | 28 | 1 | 20 | wide |
| ~.router_objective_upgrade | 274 | 157 | 2 | 2 | 13 | 50 | medium |
| ~.router_staged_upgrade | 108 | 57 | 1 | 2 | 9 | 44 | s:re-export |
| ~.scheduling | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.scheduling.action_loss | 385 | 235 | 9 | 10 | 2 | 97 | medium |
| ~.scheduling.constraint_engine | 363 | 213 | 7 | 3 | 8 | 37 | medium |
| ~.scheduling.controller_actions | 75 | 46 | 2 | 5 | 0 | 10 | medium |
| ~.scheduling.controller_cutover | 654 | 439 | 8 | 1 | 15 | 98 | deep |
| ~.scheduling.controller_ownership | 426 | 255 | 16 | 4 | 5 | 55 | medium |
| ~.scheduling.controller_snapshot | 415 | 304 | 5 | 9 | 9 | 123 | deep |
| ~.scheduling.controller_store | 513 | 398 | 22 | 5 | 4 | 80 | wide |
| ~.scheduling.decay_pressure | 163 | 117 | 3 | 2 | 4 | 80 | medium |
| ~.scheduling.device_eligibility | 278 | 130 | 3 | 4 | 1 | 27 | medium |
| ~.scheduling.dispersion | 101 | 45 | 1 | 1 | 2 | 37 | s:re-export |
| ~.scheduling.evaluation | 601 | 492 | 6 | 1 | 11 | 104 | deep |
| ~.scheduling.evsi | 673 | 414 | 14 | 10 | 2 | 93 | medium |
| ~.scheduling.family_memory_model | 113 | 80 | 3 | 3 | 2 | 18 | medium |
| ~.scheduling.forecast_receipts | 328 | 192 | 7 | 13 | 3 | 67 | medium |
| ~.scheduling.frame_constraints | 302 | 207 | 10 | 2 | 6 | 87 | medium |
| ~.scheduling.fsrs | 157 | 126 | 11 | 28 | 1 | 21 | medium |
| ~.scheduling.fsrs_fitting | 215 | 161 | 4 | 1 | 3 | 92 | medium |
| ~.scheduling.intent | 9 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.scheduling.intent.feasibility | 214 | 141 | 2 | 1 | 5 | 40 | medium |
| ~.scheduling.intent.followup_gate | 264 | 146 | 6 | 2 | 5 | 83 | medium |
| ~.scheduling.intent.model | 149 | 99 | 3 | 8 | 0 | 8 | medium |
| ~.scheduling.intent.recall_targets | 151 | 87 | 6 | 5 | 4 | 24 | medium |
| ~.scheduling.intent.resolution | 336 | 248 | 7 | 8 | 2 | 68 | medium |
| ~.scheduling.intent.serving | 765 | 475 | 10 | 9 | 12 | 109 | deep |
| ~.scheduling.intent_planner | 109 | 63 | 3 | 1 | 1 | 35 | s:one-caller helper |
| ~.scheduling.interleaving | 85 | 43 | 1 | 1 | 2 | 41 | s:thin |
| ~.scheduling.kinship_feature | 527 | 341 | 11 | 1 | 7 | 80 | medium |
| ~.scheduling.open_world_gate | 217 | 153 | 3 | 1 | 2 | 20 | medium |
| ~.scheduling.predictive_targets | 166 | 112 | 4 | 1 | 1 | 64 | medium |
| ~.scheduling.prequential | 277 | 184 | 6 | 0 | 4 | 30 | medium |
| ~.scheduling.progression | 342 | 221 | 10 | 0 | 5 | 58 | medium |
| ~.scheduling.progression_policy | 104 | 51 | 4 | 1 | 3 | 18 | s:one-caller helper |
| ~.scheduling.randomization_layer | 422 | 265 | 12 | 5 | 5 | 49 | medium |
| ~.scheduling.reentry_adapter | 288 | 200 | 4 | 0 | 11 | 74 | medium |
| ~.scheduling.reentry_summary | 175 | 129 | 4 | 5 | 5 | 79 | medium |
| ~.scheduling.review_log | 161 | 97 | 5 | 3 | 7 | 66 | medium |
| ~.scheduling.scheduler | 3752 | 2569 | 17 | 19 | 42 | 787 | deep |
| ~.scheduling.selection_rewards | 625 | 493 | 10 | 5 | 8 | 131 | deep |
| ~.scheduling.serving_exclusions | 349 | 173 | 6 | 5 | 10 | 56 | medium |
| ~.scheduling.session_minutes | 92 | 43 | 4 | 3 | 1 | 18 | medium |
| ~.scheduling.shadow_components | 309 | 193 | 9 | 1 | 6 | 58 | medium |
| ~.scheduling.short_session | 118 | 66 | 2 | 0 | 6 | 48 | s:one-caller helper |
| ~.scheduling.staged_policy | 1049 | 761 | 10 | 9 | 14 | 291 | deep |
| ~.scheduling.state_signals | 218 | 126 | 6 | 2 | 5 | 40 | medium |
| ~.scheduling.unresolved_cost | 283 | 191 | 4 | 3 | 3 | 65 | medium |
| ~.scheduling.voi_forecasts | 475 | 351 | 14 | 8 | 5 | 60 | medium |
| ~.section_map | 382 | 258 | 12 | 5 | 3 | 63 | medium |
| ~.serve_eligibility | 1079 | 631 | 22 | 20 | 2 | 72 | medium |
| ~.sim | 21 | 10 | 0 | 0 | 3 | 0 | init/re-export |
| ~.sim.ad_gates | 396 | 318 | 12 | 0 | 5 | 48 | medium |
| ~.sim.ad_synthetic | 1290 | 979 | 36 | 1 | 12 | 133 | wide |
| ~.sim.diagnostic_validation | 499 | 401 | 5 | 1 | 14 | 122 | deep |
| ~.sim.grader_confusion | 338 | 225 | 6 | 1 | 1 | 82 | medium |
| ~.sim.interval_width_viability | 151 | 101 | 3 | 0 | 3 | 39 | medium |
| ~.sim.kinship_admission | 117 | 66 | 2 | 1 | 1 | 29 | s:one-caller helper |
| ~.sim.metrics | 373 | 290 | 2 | 1 | 6 | 52 | deep |
| ~.sim.offline_benchmarks | 194 | 143 | 4 | 1 | 2 | 57 | medium |
| ~.sim.profiles | 192 | 139 | 3 | 4 | 2 | 54 | medium |
| ~.sim.runner | 1082 | 868 | 8 | 6 | 27 | 189 | deep |
| ~.sim.student | 482 | 321 | 7 | 4 | 0 | 141 | deep |
| ~.sim.sweep | 297 | 232 | 5 | 3 | 3 | 86 | medium |
| ~.source_retrieval | 18 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.source_retrieval.b4 | 438 | 362 | 5 | 1 | 14 | 109 | deep |
| ~.source_retrieval.bench | 364 | 271 | 15 | 3 | 10 | 44 | medium |
| ~.source_retrieval.compare | 876 | 646 | 8 | 4 | 23 | 417 | deep |
| ~.source_retrieval.compare_scope | 547 | 392 | 11 | 1 | 11 | 102 | medium |
| ~.source_retrieval.contracts | 60 | 32 | 6 | 5 | 1 | 0 | s:re-export |
| ~.source_retrieval.corpus | 763 | 456 | 21 | 43 | 11 | 67 | medium |
| ~.source_retrieval.deliverable_path | 1963 | 1374 | 48 | 5 | 26 | 99 | wide |
| ~.source_retrieval.deliverables | 1654 | 1092 | 46 | 6 | 24 | 79 | wide |
| ~.source_retrieval.dense | 340 | 256 | 6 | 5 | 7 | 48 | deep |
| ~.source_retrieval.evaluation | 1087 | 845 | 9 | 1 | 20 | 254 | deep |
| ~.source_retrieval.fallback_space | 466 | 346 | 12 | 5 | 18 | 85 | medium |
| ~.source_retrieval.feedback | 228 | 147 | 8 | 10 | 6 | 48 | medium |
| ~.source_retrieval.find_sources | 940 | 677 | 18 | 15 | 27 | 226 | medium |
| ~.source_retrieval.kept_comparisons | 1591 | 1097 | 24 | 6 | 14 | 81 | deep |
| ~.source_retrieval.library | 284 | 190 | 5 | 3 | 17 | 92 | medium |
| ~.source_retrieval.library_ask | 1501 | 984 | 35 | 8 | 27 | 188 | wide |
| ~.source_retrieval.local_index | 495 | 359 | 16 | 6 | 16 | 97 | medium |
| ~.source_retrieval.note_gaps | 330 | 201 | 8 | 1 | 6 | 78 | medium |
| ~.source_retrieval.note_links | 1318 | 874 | 40 | 4 | 15 | 108 | wide |
| ~.source_retrieval.passage_cues | 1762 | 1235 | 31 | 4 | 33 | 125 | wide |
| ~.source_retrieval.policy | 126 | 73 | 4 | 23 | 0 | 16 | medium |
| ~.source_retrieval.queries | 244 | 166 | 10 | 13 | 11 | 51 | medium |
| ~.source_retrieval.query_student | 1556 | 1161 | 41 | 2 | 19 | 250 | wide |
| ~.source_retrieval.reader_tutor | 606 | 376 | 15 | 5 | 18 | 57 | medium |
| ~.source_retrieval.reading_paths | 1377 | 929 | 42 | 7 | 24 | 62 | wide |
| ~.source_retrieval.recipes | 200 | 123 | 8 | 16 | 7 | 26 | medium |
| ~.source_retrieval.role_labeller | 561 | 391 | 9 | 1 | 14 | 158 | deep |
| ~.source_retrieval.search | 608 | 427 | 5 | 11 | 14 | 242 | deep |
| ~.source_retrieval.section_coverage | 2319 | 1540 | 49 | 14 | 27 | 145 | wide |
| ~.source_retrieval.service_spend | 376 | 233 | 9 | 21 | 8 | 29 | medium |
| ~.source_retrieval.source_vectors | 320 | 217 | 9 | 5 | 19 | 49 | medium |
| ~.source_retrieval.spaces | 601 | 430 | 8 | 5 | 13 | 134 | deep |
| ~.source_retrieval.student_data | 622 | 423 | 30 | 3 | 12 | 119 | wide |
| ~.source_retrieval.student_encoder | 546 | 405 | 18 | 4 | 12 | 47 | medium |
| ~.source_retrieval.suggest | 152 | 110 | 2 | 2 | 9 | 46 | medium |
| ~.source_retrieval.suites | 31 | 17 | 1 | 1 | 3 | 10 | s:re-export |
| ~.source_retrieval.timing | 102 | 72 | 3 | 1 | 3 | 49 | s:one-caller helper |
| ~.source_retrieval.tutor | 557 | 349 | 11 | 7 | 17 | 78 | medium |
| ~.source_retrieval.vault_notes | 808 | 543 | 20 | 3 | 12 | 64 | medium |
| ~.source_retrieval.verify | 330 | 208 | 11 | 7 | 13 | 49 | medium |
| ~.source_retrieval.windows | 313 | 194 | 11 | 6 | 6 | 39 | medium |
| ~.sources_upgrade | 113 | 60 | 2 | 2 | 9 | 37 | medium |
| ~.stuck_prompt_upgrade | 114 | 61 | 1 | 2 | 9 | 45 | s:re-export |
| ~.substrate | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.substrate.activities | 1261 | 910 | 40 | 61 | 6 | 113 | wide |
| ~.substrate.activity_patterns | 660 | 477 | 19 | 5 | 3 | 66 | medium |
| ~.substrate.administration_adapters | 351 | 214 | 14 | 4 | 5 | 48 | medium |
| ~.substrate.canonical_projection | 1335 | 856 | 9 | 43 | 16 | 512 | deep |
| ~.substrate.canonical_projection_rollout | 269 | 145 | 3 | 1 | 7 | 72 | medium |
| ~.substrate.card_lineage | 376 | 245 | 9 | 4 | 3 | 54 | medium |
| ~.substrate.compat | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.substrate.compat.activity_backfill | 388 | 317 | 2 | 1 | 5 | 304 | deep |
| ~.substrate.compat.card_outcome_replay | 262 | 162 | 7 | 0 | 0 | 34 | medium |
| ~.substrate.compat.substrate_cutover | 722 | 485 | 13 | 0 | 7 | 179 | medium |
| ~.substrate.data_quality | 176 | 140 | 4 | 3 | 5 | 120 | medium |
| ~.substrate.dataset | 749 | 538 | 7 | 1 | 8 | 85 | deep |
| ~.substrate.families | 508 | 437 | 8 | 4 | 12 | 78 | deep |
| ~.substrate.family_memory | 73 | 52 | 1 | 1 | 5 | 46 | s:re-export |
| ~.substrate.instrument_serving | 116 | 16 | 2 | 18 | 0 | 26 | s:thin |
| ~.substrate.intervention_outcomes | 431 | 298 | 5 | 6 | 5 | 88 | deep |
| ~.substrate.item_fingerprints | 214 | 134 | 14 | 5 | 4 | 28 | medium |
| ~.substrate.model_usage | 339 | 249 | 4 | 1 | 2 | 41 | medium |
| ~.substrate.p0_projection | 129 | 91 | 3 | 41 | 6 | 43 | medium |
| ~.substrate.rebuild_orchestrator | 818 | 560 | 9 | 6 | 26 | 87 | deep |
| ~.substrate.recurrence_groups | 732 | 538 | 12 | 12 | 6 | 70 | deep |
| ~.substrate.replay | 537 | 344 | 5 | 8 | 10 | 109 | deep |
| ~.substrate.shadow_rebuild | 484 | 377 | 6 | 1 | 5 | 78 | deep |
| ~.substrate.state_sync | 293 | 187 | 4 | 17 | 12 | 99 | medium |
| ~.substrate.surface_mint | 561 | 360 | 14 | 2 | 4 | 111 | medium |
| ~.substrate.surface_pool | 523 | 368 | 15 | 1 | 5 | 56 | medium |
| ~.superseded_claims_upgrade | 287 | 157 | 2 | 2 | 13 | 50 | medium |
| ~.symbolic_view | 199 | 110 | 13 | 12 | 1 | 17 | medium |
| ~.teacher | 21 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.teacher.actions | 245 | 189 | 6 | 1 | 9 | 68 | medium |
| ~.teacher.brief | 884 | 620 | 15 | 7 | 17 | 96 | deep |
| ~.teacher.checks | 319 | 238 | 10 | 2 | 16 | 60 | medium |
| ~.teacher.contracts | 326 | 174 | 25 | 8 | 1 | 0 | wide |
| ~.teacher.delayed | 264 | 171 | 8 | 2 | 9 | 103 | medium |
| ~.teacher.doctrines | 39 | 17 | 3 | 2 | 0 | 7 | s:thin |
| ~.teacher.episodes | 585 | 380 | 25 | 4 | 6 | 35 | wide |
| ~.teacher.exposure | 40 | 17 | 1 | 2 | 1 | 18 | s:re-export |
| ~.teacher.guards | 284 | 158 | 15 | 2 | 5 | 23 | medium |
| ~.teacher.notes | 120 | 78 | 3 | 2 | 4 | 32 | medium |
| ~.teacher.probes | 507 | 346 | 15 | 2 | 15 | 83 | medium |
| ~.teacher.report | 323 | 248 | 2 | 1 | 6 | 57 | medium |
| ~.teacher.service | 2559 | 1854 | 16 | 3 | 33 | 115 | deep |
| ~.teacher.te2 | 180 | 100 | 11 | 6 | 5 | 22 | medium |
| ~.teacher.topics | 137 | 94 | 5 | 2 | 4 | 47 | medium |
| ~.teacher.visuals | 376 | 217 | 17 | 2 | 6 | 32 | medium |
| ~.teacher_probes_upgrade | 228 | 157 | 2 | 2 | 13 | 46 | medium |
| ~.teacher_upgrade | 286 | 157 | 2 | 2 | 13 | 50 | medium |
| ~.text_canon | 64 | 18 | 2 | 5 | 0 | 16 | s:thin |
| ~.tui | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.tui.app | 60 | 38 | 3 | 1 | 4 | 6 | s:one-caller helper |
| ~.tui.minutes_memory | 88 | 53 | 3 | 1 | 3 | 22 | s:one-caller helper |
| ~.tui.screens | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.tui.screens.feedback | 682 | 565 | 1 | 1 | 15 | 56 | deep |
| ~.tui.screens.practice | 617 | 483 | 1 | 1 | 14 | 50 | deep |
| ~.tui.screens.start | 387 | 306 | 3 | 1 | 6 | 60 | deep |
| ~.tui.screens.today | 423 | 349 | 2 | 2 | 6 | 39 | deep |
| ~.tui.state | 65 | 50 | 1 | 5 | 10 | 14 | medium |
| ~.tui.theme | 29 | 22 | 0 | 1 | 0 | 0 | s:thin |
| ~.tui.widgets | 116 | 66 | 6 | 5 | 0 | 9 | medium |
| ~.tutor | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.tutor.ai_contracts | 795 | 587 | 32 | 9 | 5 | 48 | wide |
| ~.tutor.context_delivery | 454 | 299 | 13 | 7 | 3 | 79 | medium |
| ~.tutor.durable_promotion | 683 | 348 | 5 | 5 | 8 | 87 | deep |
| ~.tutor.promotions | 1181 | 967 | 8 | 5 | 16 | 194 | deep |
| ~.tutor.question_queue | 243 | 175 | 4 | 4 | 4 | 125 | medium |
| ~.tutor.question_signal | 612 | 421 | 7 | 1 | 7 | 92 | deep |
| ~.tutor.reader_modes | 766 | 419 | 16 | 3 | 6 | 152 | medium |
| ~.tutor.teach_back | 1410 | 1083 | 19 | 6 | 16 | 148 | deep |
| ~.tutor.tutor_qa | 2735 | 1795 | 28 | 26 | 30 | 727 | deep |
| ~.vault | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.vault.embedding_recipes | 368 | 250 | 10 | 16 | 6 | 30 | deep |
| ~.vault.facet_fingerprint | 89 | 50 | 3 | 4 | 0 | 19 | medium |
| ~.vault.hashes | 124 | 86 | 9 | 22 | 2 | 20 | medium |
| ~.vault.lifecycle | 180 | 79 | 10 | 17 | 1 | 27 | medium |
| ~.vault.loader | 875 | 641 | 12 | 139 | 9 | 86 | deep |
| ~.vault.models | 1033 | 551 | 56 | 297 | 3 | 25 | wide |
| ~.vault.paths | 127 | 78 | 3 | 140 | 2 | 8 | medium |
| ~.vault.repository | 104 | 38 | 3 | 89 | 7 | 24 | s:thin |
| ~.vault.required_method | 876 | 467 | 23 | 50 | 0 | 75 | medium |
| ~.vault.scope_seal | 43 | 18 | 1 | 3 | 0 | 20 | s:thin |
| ~.vault.working_vault | 74 | 42 | 3 | 1 | 0 | 19 | s:thin |
| ~.vault.writer | 619 | 499 | 12 | 23 | 11 | 44 | deep |
| ~.vault.yaml_io | 268 | 169 | 8 | 25 | 0 | 67 | medium |
| ~.vault_lock | 237 | 142 | 7 | 45 | 0 | 71 | medium |
| ~.voi_stopping_upgrade | 122 | 57 | 1 | 2 | 9 | 45 | s:re-export |
| ~.workbench | 17 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| ~.workbench.bridge | 202 | 130 | 2 | 2 | 12 | 121 | medium |
| ~.workbench.check | 852 | 609 | 22 | 5 | 17 | 119 | medium |
| ~.workbench.compare_methods | 571 | 387 | 13 | 2 | 21 | 109 | medium |
| ~.workbench.help_outcomes | 796 | 532 | 8 | 1 | 9 | 236 | deep |
| ~.workbench.ladder | 418 | 276 | 16 | 4 | 13 | 61 | medium |
| ~.workbench.passage_draw | 280 | 172 | 12 | 4 | 8 | 52 | medium |
| ~.workbench.route_example | 343 | 223 | 9 | 4 | 16 | 136 | medium |
| ~.workbench.symbolic | 1073 | 947 | 4 | 1 | 1 | 46 | deep |
| ~.workbench_field_signals_upgrade | 119 | 59 | 1 | 2 | 9 | 44 | s:re-export |
| learnloop_mcp | 13 | 2 | 0 | 2 | 0 | 0 | init/re-export |
| learnloop_mcp.__main__ | 18 | 10 | 1 | 0 | 1 | 5 | s:thin |
| learnloop_mcp.cli | 59 | 38 | 1 | 2 | 5 | 33 | s:re-export |
| learnloop_mcp.hosts | 64 | 46 | 1 | 1 | 1 | 32 | s:one-caller helper |
| learnloop_mcp.http_app | 148 | 92 | 8 | 1 | 2 | 14 | medium |
| learnloop_mcp.server | 624 | 487 | 25 | 2 | 10 | 151 | wide |
| learnloop_mobile | 2 | 0 | 0 | 0 | 0 | 0 | init/re-export |
| learnloop_mobile.__main__ | 4 | 2 | 0 | 0 | 1 | 0 | s:thin |
| learnloop_mobile.adapter | 86 | 55 | 5 | 2 | 0 | 11 | medium |
| learnloop_mobile.allowlist | 274 | 147 | 7 | 4 | 0 | 15 | medium |
| learnloop_mobile.cli | 122 | 89 | 7 | 1 | 6 | 17 | medium |
| learnloop_mobile.client_contract | 75 | 41 | 4 | 0 | 1 | 19 | s:one-caller helper |
| learnloop_mobile.config | 77 | 48 | 4 | 3 | 1 | 8 | medium |
| learnloop_mobile.doctor | 297 | 229 | 5 | 1 | 8 | 113 | medium |
| learnloop_mobile.host | 648 | 516 | 9 | 1 | 9 | 103 | deep |
| learnloop_mobile.runtime | 656 | 448 | 4 | 1 | 12 | 31 | deep |
| learnloop_sidecar | 5 | 2 | 0 | 1 | 0 | 0 | init/re-export |
| learnloop_sidecar.__main__ | 22 | 12 | 1 | 0 | 3 | 7 | s:re-export |
| learnloop_sidecar.background_jobs | 143 | 70 | 2 | 10 | 2 | 16 | medium |
| learnloop_sidecar.context | 1381 | 888 | 11 | 77 | 53 | 167 | deep |
| learnloop_sidecar.dto | 44 | 30 | 5 | 78 | 0 | 10 | s:thin |
| learnloop_sidecar.errors | 57 | 43 | 3 | 77 | 0 | 15 | medium |
| learnloop_sidecar.exam_grading | 104 | 73 | 1 | 1 | 0 | 27 | s:one-caller helper |
| learnloop_sidecar.handlers | 79 | 77 | 0 | 1 | 74 | 0 | s:re-export |
| learnloop_sidecar.handlers.adaptive_difficulty | 193 | 114 | 8 | 1 | 9 | 25 | medium |
| learnloop_sidecar.handlers.adjudication | 509 | 357 | 7 | 1 | 10 | 137 | deep |
| learnloop_sidecar.handlers.ai_providers | 129 | 75 | 10 | 13 | 7 | 30 | medium |
| learnloop_sidecar.handlers.animation | 177 | 138 | 7 | 1 | 6 | 39 | medium |
| learnloop_sidecar.handlers.app | 198 | 129 | 12 | 1 | 6 | 22 | medium |
| learnloop_sidecar.handlers.as_printed | 148 | 90 | 5 | 1 | 11 | 23 | medium |
| learnloop_sidecar.handlers.calibration | 173 | 112 | 12 | 1 | 8 | 27 | medium |
| learnloop_sidecar.handlers.capture | 183 | 127 | 13 | 4 | 11 | 30 | medium |
| learnloop_sidecar.handlers.chatgpt_plan | 224 | 141 | 11 | 2 | 10 | 34 | medium |
| learnloop_sidecar.handlers.claims | 96 | 75 | 9 | 1 | 5 | 14 | s:one-caller helper |
| learnloop_sidecar.handlers.cli | 109 | 90 | 2 | 1 | 4 | 67 | medium |
| learnloop_sidecar.handlers.compare_scope | 138 | 80 | 5 | 2 | 10 | 37 | medium |
| learnloop_sidecar.handlers.correspondents | 647 | 402 | 20 | 2 | 19 | 75 | medium |
| learnloop_sidecar.handlers.daily_plan | 753 | 467 | 18 | 3 | 29 | 68 | medium |
| learnloop_sidecar.handlers.deliverables | 789 | 526 | 22 | 2 | 17 | 76 | medium |
| learnloop_sidecar.handlers.diagnosis_card | 84 | 54 | 4 | 1 | 8 | 29 | s:one-caller helper |
| learnloop_sidecar.handlers.diagnostic | 211 | 150 | 20 | 1 | 6 | 14 | wide |
| learnloop_sidecar.handlers.epigraphs | 48 | 31 | 2 | 1 | 3 | 16 | s:thin |
| learnloop_sidecar.handlers.exams | 571 | 455 | 8 | 1 | 17 | 62 | deep |
| learnloop_sidecar.handlers.facet_detail | 334 | 228 | 5 | 1 | 12 | 87 | medium |
| learnloop_sidecar.handlers.facet_identity | 87 | 54 | 6 | 1 | 5 | 22 | s:one-caller helper |
| learnloop_sidecar.handlers.facets | 172 | 108 | 1 | 1 | 6 | 141 | medium |
| learnloop_sidecar.handlers.feedback | 1275 | 850 | 28 | 1 | 36 | 100 | medium |
| learnloop_sidecar.handlers.figures | 1521 | 930 | 42 | 4 | 38 | 99 | wide |
| learnloop_sidecar.handlers.first_run | 491 | 324 | 10 | 1 | 19 | 129 | deep |
| learnloop_sidecar.handlers.followup | 138 | 86 | 9 | 1 | 9 | 22 | medium |
| learnloop_sidecar.handlers.goals | 723 | 554 | 21 | 4 | 20 | 115 | medium |
| learnloop_sidecar.handlers.golden_path | 327 | 241 | 18 | 1 | 13 | 52 | medium |
| learnloop_sidecar.handlers.golden_path_assessment | 191 | 139 | 11 | 1 | 8 | 44 | medium |
| learnloop_sidecar.handlers.graph | 87 | 69 | 1 | 1 | 4 | 75 | s:one-caller helper |
| learnloop_sidecar.handlers.graph_edit | 111 | 74 | 7 | 1 | 6 | 21 | s:one-caller helper |
| learnloop_sidecar.handlers.hints | 545 | 326 | 10 | 2 | 24 | 55 | deep |
| learnloop_sidecar.handlers.ingest | 1599 | 1153 | 77 | 4 | 34 | 108 | wide |
| learnloop_sidecar.handlers.inspector | 229 | 200 | 2 | 1 | 5 | 66 | medium |
| learnloop_sidecar.handlers.intent | 105 | 67 | 6 | 1 | 9 | 12 | s:one-caller helper |
| learnloop_sidecar.handlers.item_authoring | 299 | 217 | 15 | 2 | 11 | 31 | medium |
| learnloop_sidecar.handlers.item_text_neighbors | 126 | 73 | 3 | 1 | 5 | 47 | s:one-caller helper |
| learnloop_sidecar.handlers.kept_comparisons | 247 | 146 | 9 | 2 | 10 | 38 | medium |
| learnloop_sidecar.handlers.knowledge_map | 1023 | 730 | 5 | 1 | 19 | 222 | deep |
| learnloop_sidecar.handlers.knowledge_model | 99 | 69 | 6 | 1 | 8 | 32 | s:one-caller helper |
| learnloop_sidecar.handlers.ladder | 333 | 245 | 24 | 1 | 7 | 34 | wide |
| learnloop_sidecar.handlers.learner_gaps | 187 | 134 | 6 | 4 | 8 | 53 | medium |
| learnloop_sidecar.handlers.lesson | 356 | 201 | 17 | 1 | 15 | 54 | medium |
| learnloop_sidecar.handlers.library | 217 | 154 | 7 | 1 | 6 | 47 | medium |
| learnloop_sidecar.handlers.library_ask | 833 | 508 | 19 | 7 | 28 | 90 | medium |
| learnloop_sidecar.handlers.library_exercises | 511 | 306 | 12 | 3 | 18 | 78 | medium |
| learnloop_sidecar.handlers.measurement | 428 | 284 | 9 | 1 | 22 | 87 | deep |
| learnloop_sidecar.handlers.notes | 411 | 243 | 20 | 2 | 15 | 70 | wide |
| learnloop_sidecar.handlers.placement | 167 | 116 | 8 | 2 | 8 | 37 | medium |
| learnloop_sidecar.handlers.practice | 2275 | 1496 | 33 | 8 | 42 | 227 | wide |
| learnloop_sidecar.handlers.practice_index | 149 | 100 | 9 | 4 | 12 | 33 | medium |
| learnloop_sidecar.handlers.proposals | 329 | 225 | 11 | 2 | 8 | 50 | medium |
| learnloop_sidecar.handlers.provenance | 68 | 46 | 4 | 1 | 7 | 23 | s:one-caller helper |
| learnloop_sidecar.handlers.queue | 784 | 520 | 14 | 3 | 34 | 100 | medium |
| learnloop_sidecar.handlers.reader | 2630 | 1815 | 138 | 8 | 67 | 138 | wide |
| learnloop_sidecar.handlers.reader_cue_discovery | 622 | 397 | 11 | 2 | 16 | 79 | medium |
| learnloop_sidecar.handlers.reader_followups | 239 | 147 | 11 | 2 | 10 | 72 | medium |
| learnloop_sidecar.handlers.reader_intent | 633 | 448 | 20 | 2 | 20 | 58 | medium |
| learnloop_sidecar.handlers.reader_tutor | 472 | 270 | 15 | 1 | 17 | 84 | medium |
| learnloop_sidecar.handlers.reading_paths | 269 | 174 | 7 | 2 | 12 | 57 | medium |
| learnloop_sidecar.handlers.recap | 169 | 92 | 8 | 1 | 9 | 16 | medium |
| learnloop_sidecar.handlers.registry | 71 | 46 | 4 | 1 | 5 | 27 | s:one-caller helper |
| learnloop_sidecar.handlers.remediation | 305 | 199 | 12 | 1 | 11 | 38 | medium |
| learnloop_sidecar.handlers.review | 13 | 9 | 1 | 1 | 4 | 3 | s:re-export |
| learnloop_sidecar.handlers.router_objective | 88 | 61 | 4 | 1 | 11 | 33 | s:one-caller helper |
| learnloop_sidecar.handlers.serializers | 1634 | 1154 | 23 | 8 | 34 | 246 | deep |
| learnloop_sidecar.handlers.sessions | 1070 | 674 | 32 | 11 | 14 | 60 | wide |
| learnloop_sidecar.handlers.settings | 829 | 646 | 18 | 1 | 16 | 96 | medium |
| learnloop_sidecar.handlers.side_by_side | 109 | 54 | 4 | 2 | 10 | 35 | medium |
| learnloop_sidecar.handlers.source_service | 312 | 214 | 18 | 2 | 16 | 37 | medium |
| learnloop_sidecar.handlers.sqlite_admin | 294 | 215 | 12 | 1 | 4 | 53 | medium |
| learnloop_sidecar.handlers.teach_back | 561 | 396 | 8 | 3 | 16 | 105 | deep |
| learnloop_sidecar.handlers.tutor_qa | 969 | 695 | 19 | 4 | 30 | 197 | medium |
| learnloop_sidecar.handlers.vault | 122 | 69 | 5 | 1 | 9 | 36 | s:one-caller helper |
| learnloop_sidecar.handlers.workbench | 1400 | 874 | 32 | 4 | 31 | 113 | wide |
| learnloop_sidecar.handlers.workbench_help | 725 | 472 | 15 | 2 | 25 | 95 | medium |
| learnloop_sidecar.handlers.workbench_rw2c | 333 | 206 | 8 | 2 | 17 | 51 | medium |
| learnloop_sidecar.logging | 104 | 67 | 4 | 10 | 0 | 26 | medium |
| learnloop_sidecar.post_attempt_worker | 287 | 191 | 1 | 2 | 5 | 47 | medium |
| learnloop_sidecar.prefetch_runtime | 199 | 120 | 6 | 6 | 4 | 26 | medium |
| learnloop_sidecar.registry | 37 | 25 | 2 | 75 | 1 | 14 | s:thin |
| learnloop_sidecar.request_origin | 158 | 64 | 8 | 9 | 3 | 25 | medium |
| learnloop_sidecar.server | 319 | 228 | 1 | 2 | 12 | 78 | medium |
| learnloop_sidecar.serving | 248 | 141 | 8 | 6 | 9 | 65 | medium |
| learnloop_sidecar.source_identity | 57 | 35 | 1 | 5 | 2 | 41 | s:re-export |

## Appendix B: every table

Paths are relative to `src/learnloop/`. Sorted by class. Generated by the static scan in §10 and reviewed by hand for the non-live rows. No counts: those are private (§10). This is for the owner's review, and proposes no drop.

| table | role | class | writer (first) | reader (first) | write callers | read callers | replayer / other | feature (first migration) | flags |
|---|---|---|---|---|---|---|---|---|---|
| learner_theta | COMPAT | dead | - | - |  |  | doctor | 001_initial |  |
| activity_card_authoring | RAW_LEDGER | retired but still read | `db/repositories.py:23026` | `db/repositories.py:23069` | substrate | substrate |  | 074_activity_contract_extensions | every writer unreachable by name-reach; tests only |
| activity_family_authoring | RAW_LEDGER | retired but still read | `db/repositories.py:22958` | `db/repositories.py:23018` | substrate | substrate |  | 074_activity_contract_extensions | every writer unreachable by name-reach; tests only |
| activity_pattern_versions | RAW_LEDGER | retired but still read | `db/repositories.py:22790` | `db/repositories.py:22790` | substrate | curriculum,substrate |  | 073_activity_patterns_and_features | every writer unreachable by name-reach; tests only |
| activity_patterns | RAW_LEDGER | retired but still read | `db/repositories.py:22775` | `db/repositories.py:22775` | substrate | curriculum,substrate |  | 073_activity_patterns_and_features | every writer unreachable by name-reach; tests only |
| activity_surface_authoring | RAW_LEDGER | retired but still read | `db/repositories.py:23456` | `db/repositories.py:23506` | substrate | substrate |  | 077_familiarity_namespace | every writer unreachable by name-reach; tests only |
| angle_inventories | RAW_LEDGER | retired but still read | `db/repositories.py:23851` | `db/repositories.py:23874` |  | scheduling |  | 079_progression_and_lapse | writer has no production caller |
| causal_mechanism_taxonomy_retirements | RAW_LEDGER | retired but still read | `db/repositories.py:16202` | `db/repositories.py:16190` |  | cli,diagnosis |  | 133_causal_mechanism_repair_key | writer has no production caller |
| controller_constraint_manifests | RECEIPT | retired but still read | `scheduling/controller_store.py:104` | `scheduling/controller_store.py:104` |  |  |  | 096_controller_snapshots | writer has no production caller |
| controller_outcome_windows | WORKFLOW | retired but still read | `scheduling/controller_store.py:437` | `scheduling/controller_store.py:486` | scheduling | scheduling |  | 098_controller_randomization_and_outcomes | every writer unreachable by name-reach; tests only |
| controller_prequential_reports | RECEIPT | retired but still read | `scheduling/prequential.py:237` | `scheduling/prequential.py:237` | scheduling | scheduling |  | 100_kinship_kernel_and_shadow_components | every writer unreachable by name-reach; tests only |
| elicitation_events | COMPAT | retired but still read | `db/repositories.py:9406` | `db/repositories.py:9497` | scheduling | ops |  | 001_initial |  |
| evidence_facet_recall_state | COMPAT | retired but still read | `db/repositories.py:6084` | `db/repositories.py:2803` | db,goals,ops,substrate,tutor | adaptive_difficulty,attempts,content,db,goals,learner,ops,sim,substrat | doctor rebuild | 007_recall_coverage_interventions |  |
| facet_uncertainty | COMPAT | retired but still read | `db/repositories.py:6084` | `db/repositories.py:6084` | db,goals,substrate,tutor | attempts,db,goals,instructional,learner,substrate,tutor |  | 012_facet_diagnostic_state |  |
| familiarity_kernel_events | RECEIPT | retired but still read | `scheduling/kinship_feature.py:185` | `scheduling/kinship_feature.py:509` | scheduling | scheduling |  | 100_kinship_kernel_and_shadow_components | every writer unreachable by name-reach; tests only |
| familiarity_kernel_features | RECEIPT | retired but still read | `scheduling/kinship_feature.py:338` | `scheduling/kinship_feature.py:355` | scheduling | scheduling |  | 100_kinship_kernel_and_shadow_components | every writer unreachable by name-reach; tests only |
| familiarity_kernel_models | RAW_LEDGER | retired but still read | `scheduling/kinship_feature.py:185` | `scheduling/kinship_feature.py:185` | scheduling | attempts,curriculum,scheduling |  | 100_kinship_kernel_and_shadow_components | every writer unreachable by name-reach; tests only |
| family_evidence_cap_policies | RAW_LEDGER | retired but still read | `db/repositories.py:23882` | `db/repositories.py:23882` | scheduling | scheduling |  | 079_progression_and_lapse | every writer unreachable by name-reach; tests only |
| learner_state_beliefs | COMPAT | retired but still read | `db/repositories.py:9294` | `db/repositories.py:9294` | diagnosis | diagnosis |  | 001_initial |  |
| lo_probe_state | COMPAT | retired but still read | `db/repositories.py:7713` | `db/repositories.py:7693` | diagnosis | content,diagnosis,followup_run,followup_serve,learnloop_sidecar,substr | sync | 001_initial |  |
| progression_policy_versions | RAW_LEDGER | retired but still read | `db/repositories.py:22923` | `db/repositories.py:22923` | scheduling | scheduling,substrate |  | 074_activity_contract_extensions | every writer unreachable by name-reach; tests only |
| shadow_component_events | RECEIPT | retired but still read | `scheduling/shadow_components.py:222` | `scheduling/shadow_components.py:222` | scheduling | scheduling |  | 100_kinship_kernel_and_shadow_components | every writer unreachable by name-reach; tests only |
| soft_kinship_features | RAW_LEDGER | retired but still read | `db/repositories.py:23397` | `db/repositories.py:23397` | learner | learner,scheduling |  | 077_familiarity_namespace | every writer unreachable by name-reach; tests only |
| source_exam_profiles | COMPAT | retired but still read | `db/repositories.py:20881` | `db/repositories.py:20906` |  |  | doctor | 041_source_unit_inventories |  |
| source_locator_schemes | COMPAT | retired but still read | `db/repositories.py:20557` | `db/repositories.py:20557` |  | adaptive_difficulty,content,ingest,reader,teacher | doctor | 032_source_layer |  |
| activity_administrations | RAW_LEDGER | live | `db/repositories.py:12007` | `adaptive_difficulty/material_view.py:485` | compat,reader,scheduling,substrate | adaptive_difficulty,cli,compat,db,field,goals,reader,scheduling,substr |  | 065_activity_lineage_substrate |  |
| activity_card_state | RAW_LEDGER | live | `db/repositories.py:22464` | `db/repositories.py:23193` | compat,curriculum,substrate | compat,daily_plan,substrate | rebuild | 075_card_lineage_state |  |
| activity_card_versions | RAW_LEDGER | live | `db/repositories.py:11798` | `db/repositories.py:11798` | compat,reader,substrate | compat,curriculum,reader,substrate |  | 065_activity_lineage_substrate |  |
| activity_cards | RAW_LEDGER | live | `db/repositories.py:11763` | `db/repositories.py:11763` | compat,reader,substrate | compat,curriculum,ops,reader,substrate |  | 065_activity_lineage_substrate |  |
| activity_exposure_events | RAW_LEDGER | live | `db/repositories.py:12007` | `db/repositories.py:12007` | compat,scheduling,substrate | cli,compat,learner,scheduling,substrate |  | 065_activity_lineage_substrate |  |
| activity_families | RAW_LEDGER | live | `db/repositories.py:11682` | `db/repositories.py:11682` | compat,reader,substrate | compat,ops,reader,substrate |  | 065_activity_lineage_substrate |  |
| activity_family_membership_events | RAW_LEDGER | live | `db/stores/families.py:76` | `db/stores/families.py:76` | ops,substrate | ops,substrate |  | 168_activity_family_membership |  |
| activity_family_versions | RAW_LEDGER | live | `db/repositories.py:11733` | `db/repositories.py:11733` | compat,substrate | compat,substrate |  | 065_activity_lineage_substrate |  |
| activity_observations | RAW_LEDGER | live | `db/repositories.py:12206` | `adaptive_difficulty/material_view.py:485` | attempts,compat,substrate | adaptive_difficulty,attempts,cli,compat,db,field,goals,learnloop_sidec |  | 065_activity_lineage_substrate |  |
| activity_surface_lifecycle_events | RECEIPT | live | `db/repositories.py:12007` | `db/repositories.py:12007` | attempts,compat,curriculum,scheduling,substrate | cli,curriculum,scheduling,substrate |  | 065_activity_lineage_substrate |  |
| activity_surface_reservations | WORKFLOW | live | `db/repositories.py:11923` | `db/repositories.py:15385` | curriculum,scheduling,substrate | learner_protection,ops,reader,scheduling,substrate |  | 065_activity_lineage_substrate |  |
| activity_surfaces | RAW_LEDGER | live | `db/repositories.py:11873` | `db/repositories.py:11873` | compat,substrate | cli,compat,content,curriculum,learner_protection,learnloop_sidecar,ops |  | 065_activity_lineage_substrate |  |
| ad_commission_results | RECEIPT | live | - | `db/stores/ad_serving.py:137` |  | adaptive_difficulty,content |  | 214_adaptive_difficulty_serving |  |
| ad_coupling_versions | RECEIPT | live | `db/stores/ad_serving.py:381` | `db/stores/ad_serving.py:390` | adaptive_difficulty | adaptive_difficulty |  | 214_adaptive_difficulty_serving |  |
| ad_dose_offers | RAW_LEDGER | live | `db/stores/ad_serving.py:327` | `adaptive_difficulty/material_view.py:1181` | adaptive_difficulty | adaptive_difficulty |  | 214_adaptive_difficulty_serving |  |
| ad_history_forecast_draws | RECEIPT | live | `db/stores/ad_receipts.py:218` | - | adaptive_difficulty |  |  | 245_history_forecaster |  |
| ad_reading_opportunities | RECEIPT | live | `db/stores/ad_receipts.py:145` | `adaptive_difficulty/data_check.py:78` | adaptive_difficulty | adaptive_difficulty,algorithm_versions,attempts,cli,config,db,diagnosi |  | 213_adaptive_difficulty_receipts |  |
| ad_relatedness_runs | RECEIPT | live | - | `db/stores/ad_serving.py:357` |  | adaptive_difficulty,cli |  | 214_adaptive_difficulty_serving |  |
| ad_selections | RAW_LEDGER | live | `db/stores/ad_serving.py:76` | `db/stores/ad_serving.py:88` | adaptive_difficulty | (generic-name),adaptive_difficulty,content |  | 214_adaptive_difficulty_serving |  |
| agent_runs | RECEIPT | live | `db/repositories.py:11015` | `attempts/stuck.py:433` | ai,attempts,content,curriculum,diagnosis,teacher,tutor | attempts,content,diagnosis,field,goals,learnloop_sidecar,tutor |  | 001_initial |  |
| apply_intents | WORKFLOW | live | `db/repositories.py:21691` | `db/repositories.py:21742` | content | content,ops | doctor | 044_provenance_manifests_apply_intents |  |
| approach_maps | WORKFLOW | live | `db/stores/approach_maps.py:47` | `db/stores/approach_maps.py:28` | hints | curriculum,db,hints,reader,substrate,workbench |  | 211_approach_maps |  |
| assessment_contract_versions | RAW_LEDGER | live | `db/repositories.py:11419` | `learner_context.py:236` | learner | attempts,cli,compat,content,data_capture,db,diagnosis,evsi_calibration |  | 034_assessment_contract_snapshots |  |
| assumption_decisions | RECEIPT | live | `db/stores/placement.py:27` | `placement/decisions.py:322` | content,learnloop_sidecar,placement | cli,diagnosis,placement,scheduling,source_retrieval |  | 172_placement_assumptions |  |
| assumption_returns | RECEIPT | live | `db/stores/placement.py:35` | `daily_plan/router_card.py:752` | content,learnloop_sidecar,placement | cli,daily_plan,diagnosis,placement |  | 172_placement_assumptions |  |
| attempt_completion_work | WORKFLOW | live | `db/stores/completion.py:20` | `db/stores/completion.py:50` | attempts | attempts,followup_run,learnloop_sidecar,teacher |  | 159_attempt_completion_work |  |
| attempt_debug_payloads | RAW_LEDGER | live | `db/repositories.py:5983` | `db/repositories.py:6167` | attempts,diagnosis,substrate | adaptive_difficulty,attempts,cli,diagnosis,learner,learnloop_sidecar,s | rebuild | 007_recall_coverage_interventions |  |
| attempt_diagnoses | RAW_LEDGER | live | `db/stores/diagnoses.py:222` | `db/stores/diagnoses.py:302` | diagnosis | attempts,cli,db,diagnosis,hints,learner,learner_context,learnloop_side |  | 170_blind_grading_diagnosis_split |  |
| attempt_feedback_metadata | RAW_LEDGER | live | `db/repositories.py:1509` | `db/repositories.py:1570` | attempts,learnloop_sidecar | attempts,cli,diagnosis,experiments,field,figures,source_retrieval |  | 005_attempt_feedback_metadata |  |
| attempt_submission_receipts | RECEIPT | live | `db/repositories.py:1482` | `db/repositories.py:1470` | learnloop_sidecar | capture,learnloop_mobile,learnloop_sidecar |  | 053_attempt_submission_idempotency |  |
| attention_block_events | RECEIPT | live | `db/stores/daily_plans.py:113` | `daily_plan/engine.py:4587` | daily_plan,db,router_objective,scheduling | (generic-name),daily_plan,db,evsi_calibration,field,figures,learnloop_ |  | 096_controller_snapshots |  |
| attention_blocks | WORKFLOW | live | `db/stores/daily_plans.py:92` | `adaptive_difficulty/material_view.py:1236` | daily_plan,scheduling | adaptive_difficulty,daily_plan,evsi_calibration,field,figures,learner, | upgrade | 096_controller_snapshots |  |
| blind_grade_records | RAW_LEDGER | live | `db/stores/diagnoses.py:100` | `held_grades.py:62` | attempts | (generic-name),adaptive_difficulty,attempts,cli,db,diagnosis,evsi_cali |  | 170_blind_grading_diagnosis_split |  |
| calibration_stream_samples | RAW_LEDGER | live | `db/repositories.py:15273` | `db/repositories.py:15302` | attempts | attempts,cli |  | 066_grader_channel |  |
| canonical_mapping_proposals | WORKFLOW | live | `db/repositories.py:14445` | `db/repositories.py:14466` | reader | reader |  | 094_source_objects |  |
| capability_aliases | RAW_LEDGER | live | `db/repositories.py:22703` | `db/repositories.py:22703` | substrate | substrate |  | 073_activity_patterns_and_features |  |
| capture_inbox | RAW_LEDGER | live | `capture/inbox.py:102` | `capture/inbox.py:102` | capture,learnloop_mobile,learnloop_sidecar | capture,learnloop_mobile,learnloop_sidecar,source_retrieval |  | 171_mobile_capture |  |
| capture_routes | WORKFLOW | live | `capture/inbox.py:102` | `capture/inbox.py:214` | capture,learnloop_mobile,learnloop_sidecar | capture,learnloop_sidecar,source_retrieval |  | 171_mobile_capture |  |
| card_lineage_edges | RAW_LEDGER | live | `db/repositories.py:22464` | `db/repositories.py:23171` | curriculum,substrate | compat |  | 075_card_lineage_state | readers have no production caller |
| card_lineages | RAW_LEDGER | live | `db/repositories.py:22464` | `db/repositories.py:23129` | curriculum,substrate | compat,curriculum,reader,substrate |  | 075_card_lineage_state |  |
| causal_activity_classification_events | RAW_LEDGER | live | `db/repositories.py:16739` | `db/repositories.py:16739` | attempts,diagnosis | adaptive_difficulty,attempts,causal_activity_policy,diagnosis,evsi_cal |  | 122_causal_activity_events |  |
| causal_attribution_reports | RECEIPT | live | `db/repositories.py:18002` | `db/repositories.py:17758` | diagnosis | (generic-name),attempts,diagnosis,followup_run,followup_serve,hints,in |  | 115_causal_attribution_p0 |  |
| causal_blind_prediction_bundles | RECEIPT | live | `db/repositories.py:16391` | `db/repositories.py:16439` | diagnosis | diagnosis |  | 121_causal_probe_coherence |  |
| causal_cold_outcomes | RAW_LEDGER | live | `db/repositories.py:16996` | `db/repositories.py:17063` | diagnosis | db,diagnosis,evsi_calibration,learnloop_sidecar,substrate |  | 145_causal_cold_outcomes |  |
| causal_cold_verifications | RAW_LEDGER | live | `db/repositories.py:16898` | `learner_context.py:1148` | diagnosis | cli,diagnosis,evsi_calibration,experiments,field,figures,learner_conte |  | 121_causal_probe_coherence |  |
| causal_discriminating_observations | RAW_LEDGER | live | `db/repositories.py:17471` | `db/repositories.py:17566` | diagnosis | (generic-name),db,diagnosis,evsi_calibration,followup_serve,local_embe |  | 130_causal_discriminating_observations |  |
| causal_hypotheses | RAW_LEDGER | live | `db/repositories.py:15679` | `learner_context.py:1148` | diagnosis | (generic-name),cli,daily_plan,db,diagnosis,evsi_calibration,experiment |  | 118_causal_attribution_p1 |  |
| causal_machine_checks | RECEIPT | live | `db/repositories.py:25849` | `db/repositories.py:25903` | diagnosis | cli,db,diagnosis,learnloop_sidecar |  | 124_causal_probe_decisions |  |
| causal_mechanism_taxonomy_assignments | RAW_LEDGER | live | `db/repositories.py:16231` | `db/repositories.py:16312` | diagnosis | diagnosis |  | 119_causal_mechanism_taxonomy |  |
| causal_mechanism_taxonomy_versions | RAW_LEDGER | live | `db/repositories.py:16231` | `db/repositories.py:16231` | diagnosis | diagnosis |  | 119_causal_mechanism_taxonomy |  |
| causal_probe_candidate_events | RECEIPT | live | `db/repositories.py:16562` | `db/repositories.py:16653` | diagnosis,followup_serve | diagnosis,followup_serve |  | 121_causal_probe_coherence |  |
| causal_probe_candidates | WORKFLOW | live | `db/repositories.py:16562` | `db/repositories.py:16631` | diagnosis,followup_serve | diagnosis,followup_serve,learnloop_sidecar |  | 121_causal_probe_coherence |  |
| causal_probe_decision_receipts | RECEIPT | live | `db/repositories.py:25454` | `db/repositories.py:25556` | diagnosis | (generic-name),db,diagnosis,instructional,router_objective |  | 124_causal_probe_decisions |  |
| causal_probe_preference_events | RAW_LEDGER | live | `db/repositories.py:25756` | `db/repositories.py:25756` | diagnosis | diagnosis |  | 124_causal_probe_decisions |  |
| causal_repair_class_definitions | RAW_LEDGER | live | `db/repositories.py:16114` | `db/repositories.py:16163` | diagnosis | diagnosis |  | 133_causal_mechanism_repair_key |  |
| causal_shadow_selection_receipts | RECEIPT | live | `db/repositories.py:25604` | `db/repositories.py:25690` | diagnosis | db,diagnosis |  | 146_causal_shadow_selection |  |
| certification_cold_probe_outcomes | RAW_LEDGER | live | `db/repositories.py:17343` | `db/repositories.py:17446` | goals | db,goals |  | 139_certification_cold_probes |  |
| change_batches | WORKFLOW | live | `curriculum/concepts.py:394` | `db/repositories.py:18457` | content,curriculum | cli,content |  | 001_initial |  |
| cold_measurement_opportunities | RECEIPT | live | `db/repositories.py:3997` | `db/repositories.py:3997` | diagnosis,goals | diagnosis,goals |  | 151_cold_measurement_opportunities |  |
| cold_measurement_opportunity_decisions | RECEIPT | live | `db/repositories.py:3908` | `db/repositories.py:4068` | diagnosis,goals | diagnosis,goals |  | 151_cold_measurement_opportunities |  |
| coldness_receipts | RECEIPT | live | `db/repositories.py:17130` | `learner_context.py:1321` | attempts | attempts,diagnosis,field,goals,learnloop_sidecar,placement,router_obje |  | 149_coldness_receipts |  |
| commitment_arc_events | RECEIPT | live | `db/repositories.py:14615` | `db/repositories.py:14615` | curriculum | curriculum |  | 095_commitment_arcs |  |
| commitment_arc_versions | RAW_LEDGER | live | `db/repositories.py:14574` | `db/repositories.py:14574` | curriculum | curriculum |  | 095_commitment_arcs |  |
| commitment_arcs | RAW_LEDGER | live | `db/repositories.py:14561` | `db/repositories.py:14666` | adaptive_difficulty,content,curriculum | curriculum,reader |  | 095_commitment_arcs |  |
| commitment_events | RECEIPT | live | `db/repositories.py:22260` | `daily_plan/measurement.py:575` | curriculum,db,instructional | config,curriculum,daily_plan,instructional,learnloop_sidecar,practice_ |  | 072_commitments |  |
| commitment_target_versions | RAW_LEDGER | live | `db/repositories.py:22260` | `db/repositories.py:5393` | db | config,content,curriculum,daily_plan,intent,learnloop_sidecar,local_em |  | 072_commitments |  |
| commitment_versions | RAW_LEDGER | live | `db/repositories.py:22260` | `db/repositories.py:5393` | db | config,content,curriculum,daily_plan,instructional,intent,learnloop_si |  | 072_commitments |  |
| commitments | RAW_LEDGER | live | `db/repositories.py:22328` | `db/repositories.py:5393` | curriculum,daily_plan,instructional,intent,reader,source_retrieval,tea | (generic-name),config,content,curriculum,daily_plan,instructional,inte | upgrade | 072_commitments |  |
| composed_selector_telemetry_horizons | WORKFLOW | live | `scheduling/shadow_components.py:257` | `scheduling/shadow_components.py:257` | substrate | substrate |  | 100_kinship_kernel_and_shadow_components |  |
| concept_animations | RAW_LEDGER | live | `db/repositories.py:5631` | `db/repositories.py:5675` | content,learnloop_sidecar | ai,config,content,db,figures,learnloop_sidecar,params |  | 114_concept_animations |  |
| content_events | RAW_LEDGER | live | `curriculum/concepts.py:394` | `db/repositories.py:18445` | attempts,content,curriculum | cli,content |  | 001_initial |  |
| contrast_pair_servings | RECEIPT | live | `db/repositories.py:26309` | `db/repositories.py:26358` | diagnosis | diagnosis |  | 143_instrument_classes |  |
| controller_candidates | WORKFLOW | live | `scheduling/controller_store.py:221` | `scheduling/controller_store.py:311` | scheduling |  |  | 096_controller_snapshots | readers have no production caller |
| controller_decisions | RECEIPT | live | `scheduling/controller_store.py:221` | `evsi_calibration/live_report.py:363` | scheduling | data_capture,evsi_calibration,scheduling |  | 096_controller_snapshots |  |
| controller_ownership | WORKFLOW | live | `scheduling/controller_ownership.py:102` | `scheduling/controller_ownership.py:94` | scheduling | scheduling |  | 099_controller_ownership |  |
| controller_ownership_events | RECEIPT | live | `scheduling/controller_ownership.py:180` | `scheduling/controller_ownership.py:102` | scheduling | scheduling |  | 099_controller_ownership |  |
| controller_shadow_predictions | RECEIPT | live | `scheduling/controller_store.py:328` | `scheduling/controller_store.py:354` | scheduling | scheduling |  | 096_controller_snapshots |  |
| controller_snapshots | RECEIPT | live | `scheduling/controller_store.py:57` | `scheduling/controller_store.py:57` | scheduling | hints,scheduling |  | 096_controller_snapshots |  |
| daily_plans | WORKFLOW | live | `db/stores/daily_plans.py:50` | `daily_plan/engine.py:1606` | ai,daily_plan,db,teacher | daily_plan,figures,followup_run,router_objective,source_retrieval | upgrade | 180_daily_plans |  |
| decision_features | RECEIPT | live | `db/repositories.py:9440` | `attempts/attempts.py:1790` | diagnosis,scheduling,tutor | adaptive_difficulty,attempts,cli,content,data_capture,diagnosis,experi |  | 011_training_dataset_logging |  |
| decision_measurement_events | RECEIPT | live | `db/stores/data_capture.py:131` | `daily_plan/measurement.py:414` | daily_plan | (generic-name),attempts,daily_plan,db,ops,router,router_objective |  | 240_data_capture |  |
| decision_objectives | RECEIPT | live | `db/stores/data_capture.py:106` | `daily_plan/measurement.py:436` | daily_plan | (generic-name),cli,config,content,daily_plan,diagnosis,figure_admissio |  | 240_data_capture |  |
| decision_state_receipts | RECEIPT | live | `db/stores/router_objective.py:141` | `db/stores/router_objective.py:150` | router_objective | adaptive_difficulty,daily_plan,followup_run,learnloop_sidecar,params,r |  | 243_router_objective_receipts |  |
| deliverable_path_sections | WORKFLOW | live | `db/stores/deliverables.py:110` | `db/stores/deliverables.py:114` | source_retrieval | (generic-name),db,source_retrieval |  | 228_deliverable_curriculum |  |
| deliverable_scope_inputs | RAW_LEDGER | live | `db/stores/deliverables.py:60` | `db/stores/deliverables.py:64` | source_retrieval | (generic-name),db |  | 228_deliverable_curriculum |  |
| deliverable_scope_resolutions | WORKFLOW | live | `db/stores/deliverables.py:78` | `db/stores/deliverables.py:82` | source_retrieval | (generic-name),source_retrieval,teacher |  | 228_deliverable_curriculum |  |
| depth_edge_instances | RAW_LEDGER | live | `curriculum/depth_edge_authoring.py:402` | `db/repositories.py:22166` | cli,curriculum | cli,curriculum |  | 107_depth_edge_templates |  |
| depth_edge_template_versions | RAW_LEDGER | live | `db/repositories.py:22077` | `db/repositories.py:22100` | curriculum | cli,curriculum |  | 107_depth_edge_templates |  |
| depth_edge_templates | RAW_LEDGER | live | `db/repositories.py:22050` | `db/repositories.py:22063` | curriculum | cli,curriculum |  | 107_depth_edge_templates |  |
| depth_envelope_versions | RAW_LEDGER | live | `db/repositories.py:22003` | `db/repositories.py:22003` | curriculum | curriculum,scheduling |  | 072_commitments |  |
| depth_milestone_versions | RAW_LEDGER | live | `db/repositories.py:22227` | `db/repositories.py:22210` | curriculum | curriculum |  | 072_commitments |  |
| depth_policy_versions | RAW_LEDGER | live | `db/repositories.py:21981` | `db/repositories.py:21981` | curriculum | curriculum,scheduling |  | 072_commitments |  |
| derived_state_rebuilds | RECEIPT | live | `db/repositories.py:6955` | `attempt_content_state_upgrade.py:230` | attempts,compat,curriculum,substrate | cli,diagnosis,learner,ops,substrate,upgrade | doctor upgrade | 009_derived_state_rebuilds |  |
| diagnosis_adjudications | RAW_LEDGER | live | `db/repositories.py:26050` | `db/repositories.py:26110` | diagnosis | cli,content,diagnosis,goals,learnloop_sidecar,tutor |  | 126_diagnosis_adjudication |  |
| diagnosis_context_receipts | RECEIPT | live | `db/stores/diagnoses.py:222` | `db/stores/diagnoses.py:477` | diagnosis | attempts,diagnosis,substrate |  | 170_blind_grading_diagnosis_split |  |
| diagnosis_feedback | RAW_LEDGER | live | `db/stores/diagnoses.py:527` | `learner_context.py:1148` | diagnosis | diagnosis,learner_context,substrate |  | 170_blind_grading_diagnosis_split |  |
| diagnosis_wait_receipts | RECEIPT | live | `db/stores/diagnoses.py:608` | `db/stores/diagnoses.py:633` | learnloop_sidecar | diagnosis |  | 170_blind_grading_diagnosis_split |  |
| diagnosis_would_merge_log | RECEIPT | live | `db/stores/diagnoses.py:568` | `db/stores/diagnoses.py:595` | diagnosis | diagnosis |  | 170_blind_grading_diagnosis_split |  |
| diagnostic_augmentation_receipts | RECEIPT | live | `db/repositories.py:26723` | `db/repositories.py:26766` | attempts,diagnosis | attempts,db,diagnosis |  | 144_diagnostic_augmentation |  |
| diagnostic_eval_cases | RAW_LEDGER | live | `db/repositories.py:26616` | `db/repositories.py:26695` | diagnosis | diagnosis |  | 144_diagnostic_augmentation |  |
| diagnostic_eval_runs | RECEIPT | live | `db/repositories.py:26575` | `db/repositories.py:26685` | diagnosis | diagnosis |  | 144_diagnostic_augmentation |  |
| diagnostic_pack_cards | RAW_LEDGER | live | `db/repositories.py:24717` | `db/repositories.py:24717` | diagnosis | diagnosis |  | 083_diagnostic_pack_and_triage |  |
| diagnostic_pack_events | RECEIPT | live | `db/repositories.py:24673` | `db/repositories.py:24836` | diagnosis |  |  | 083_diagnostic_pack_and_triage | readers have no production caller |
| diagnostic_pack_pins | RAW_LEDGER | live | `db/repositories.py:24844` | `db/repositories.py:24844` | diagnosis | curriculum,diagnosis |  | 083_diagnostic_pack_and_triage |  |
| diagnostic_packs | RAW_LEDGER | live | `db/repositories.py:24673` | `db/repositories.py:24673` | diagnosis | curriculum,diagnosis,learnloop_sidecar,params |  | 083_diagnostic_pack_and_triage |  |
| diagnostic_surface_generation_needs | WORKFLOW | live | `db/repositories.py:8987` | `db/repositories.py:8987` | diagnosis | diagnosis |  | 147_diagnostic_surface_generation_needs |  |
| discrimination_profile_matches | RECEIPT | live | `db/repositories.py:26233` | `db/repositories.py:26283` | attempts | attempts,diagnosis,goals |  | 143_instrument_classes |  |
| embedding_spaces | WORKFLOW | live | `db/stores/retrieval_spaces.py:39` | `db/stores/retrieval_spaces.py:74` | source_retrieval | (generic-name) |  | 220_retrieval_spaces |  |
| embedding_vectors | WORKFLOW | live | `db/stores/embedding_vectors.py:104` | `daily_plan/router_retrieval.py:215` | content,diagnosis,ops,practice_index,router,source_retrieval | (generic-name),config,content,daily_plan,diagnosis,experiments,field,f |  | 166_embedding_substrate_and_judgments |  |
| entity_source_links | RAW_LEDGER | live | `db/repositories.py:20039` | `content/pipeline/reread.py:534` | adaptive_difficulty,content | (generic-name),content,figures,learnloop_sidecar,ops,source_retrieval, | doctor | 044_provenance_manifests_apply_intents |  |
| error_event_lineage | RAW_LEDGER | live | `db/stores/write_provenance.py:741` | `db/stores/write_provenance.py:769` | attempts | db,diagnosis |  | 205_write_provenance |  |
| error_events | RAW_LEDGER | live | `db/repositories.py:2565` | `db/repositories.py:2373` | attempts,cli,db,diagnosis,goals,substrate,tutor | (generic-name),attempts,cli,db,diagnosis,evsi_calibration,experiments, | doctor rebuild | 001_initial |  |
| error_hunt_outcomes | RECEIPT | live | `db/repositories.py:26381` | `db/repositories.py:26430` | diagnosis | diagnosis |  | 143_instrument_classes |  |
| exam_answers | RAW_LEDGER | live | `db/repositories.py:19593` | `db/repositories.py:19634` | goals | cli,followup_run,goals,learnloop_sidecar |  | 024_exam_session |  |
| exam_pool_items | WORKFLOW | live | `db/repositories.py:19399` | `db/repositories.py:19376` | goals | adaptive_difficulty,content,goals,learner_protection,learnloop_sidecar |  | 023_exam_pool |  |
| exam_predictions | RECEIPT | live | `db/repositories.py:19554` | `db/repositories.py:19578` | goals | goals |  | 024_exam_session |  |
| exam_sessions | WORKFLOW | live | `db/repositories.py:19468` | `db/repositories.py:19491` | goals | attempts,cli,goals,learnloop_sidecar |  | 024_exam_session |  |
| facet_dossiers | WORKFLOW | live | `db/stores/practice_index.py:60` | `db/stores/practice_index.py:49` | practice_index | practice_index,vault |  | 169_practice_index |  |
| facet_identity_actions | WORKFLOW | live | `db/stores/facet_identity.py:62` | `db/stores/facet_identity.py:95` | content | cli,content,curriculum,db,evsi_calibration,field,learnloop_sidecar | doctor | 183_facet_identity_actions |  |
| facet_merges | RAW_LEDGER | live | `db/repositories.py:6661` | `db/repositories.py:6638` | content | content,db,evsi_calibration,field,learner,learnloop_sidecar,ops,substr | doctor | 037_canonical_facet_state |  |
| facet_registry_saves | WORKFLOW | live | `db/stores/facet_identity.py:206` | `db/stores/facet_identity.py:222` | content | content |  | 197_facet_registry_saves |  |
| failure_triage_events | RECEIPT | live | `db/repositories.py:24911` | `db/repositories.py:24911` | diagnosis | diagnosis |  | 083_diagnostic_pack_and_triage |  |
| failure_triage_routes | RAW_LEDGER | live | migration seed | `db/repositories.py:24890` |  | diagnosis,scheduling |  | 083_diagnostic_pack_and_triage | seeded by migration |
| false_remediation_adjudications | RAW_LEDGER | live | `db/stores/collection.py:93` | - | cli |  |  | 162_false_remediation_adjudications |  |
| family_proposals | WORKFLOW | live | `db/stores/families.py:10` | `substrate/families.py:147` | substrate | cli,content,experiments,ops,practice_index |  | 168_activity_family_membership |  |
| field_signal_receipts | RECEIPT | live | `db/stores/field_signal_receipts.py:26` | `db/stores/field_signal_receipts.py:38` | db,placement,scheduling,teacher | (generic-name) | upgrade | 219_field_signal_receipts |  |
| figure_predictions | RAW_LEDGER | live | `db/stores/figures.py:311` | `daily_plan/router_reader.py:481` | figures | (generic-name),cli,daily_plan,db,diagnosis,figures,reader |  | 216_interactive_figures |  |
| figure_prefetch_decisions | RAW_LEDGER | live | `db/stores/figure_prefetch.py:21` | `figures/prefetch.py:861` | figures | (generic-name),db,figures,learnloop_sidecar,local_embeddings,source_re |  | 237_figure_prefetch |  |
| figure_requests | RAW_LEDGER | live | `db/stores/figures.py:174` | `figure_admission.py:101` | figures | (generic-name),cli,diagnosis,figures,source_retrieval |  | 224_figure_requests |  |
| figure_source_checks | RAW_LEDGER | live | `db/stores/figures.py:62` | `db/stores/figures.py:94` | figures | figures |  | 238_figure_source_checks |  |
| fitted_parameters | RAW_LEDGER | live | `db/repositories.py:7295` | `db/repositories.py:7343` | cli | cli,diagnosis,goals,params |  | 016_fitted_parameters |  |
| followup_generation_jobs | WORKFLOW | live | `db/stores/followup_serve.py:166` | `db/stores/followup_serve.py:181` | followup_run,followup_serve | followup_run,followup_serve |  | 241_followup_generate_serve |  |
| followup_ratings | RAW_LEDGER | live | `db/repositories.py:4409` | `db/repositories.py:4434` | learnloop_sidecar | diagnosis,learnloop_sidecar,scheduling |  | 017_followup_ratings |  |
| followup_tasks | WORKFLOW | live | `db/repositories.py:1358` | `db/repositories.py:4144` | content,diagnosis,goals,learnloop_sidecar,scheduling,serve_eligibility | attempts,daily_plan,diagnosis,evsi_calibration,goals,instructional,int | upgrade | 058_remediation_episodes |  |
| followup_value_decisions | RECEIPT | live | `db/stores/followup_value.py:31` | `db/stores/followup_value.py:31` | diagnosis | diagnosis,evsi_calibration | upgrade | 201_followup_value_decisions |  |
| followup_workflow_events | RECEIPT | live | `db/stores/followup_serve.py:149` | `db/stores/followup_serve.py:158` | followup_serve | followup_serve |  | 241_followup_generate_serve |  |
| followup_workflows | WORKFLOW | live | `db/stores/followup_serve.py:45` | `db/stores/followup_serve.py:29` | followup_run,followup_serve | (generic-name),followup_run,followup_serve,router_objective |  | 241_followup_generate_serve |  |
| forecast_receipts | RECEIPT | live | `adaptive_difficulty/serve.py:149` | `adaptive_difficulty/data_check.py:78` | db,decider_judgments,placement,reading_sources,scheduling,teacher | adaptive_difficulty,cli,db,diagnosis,evsi_calibration,field,learner,sc |  | 206_forecast_receipts |  |
| forecasts | WORKFLOW | live | `db/repositories.py:10768` | `db/repositories.py:10768` | db,goals,scheduling | (generic-name),db,evsi_calibration,goals,learner,scheduling | doctor | 057_forecast_ledger |  |
| generated_probe_burns | RAW_LEDGER | live | `db/stores/followup_serve.py:318` | `db/stores/followup_serve.py:274` | followup_serve | daily_plan,followup_serve |  | 241_followup_generate_serve |  |
| generated_probe_items | RAW_LEDGER | live | `db/stores/followup_serve.py:259` | `db/stores/followup_serve.py:269` | followup_serve | daily_plan,delayed_checks,diagnosis,followup_serve,goals,learnloop_sid |  | 241_followup_generate_serve |  |
| goal_contract_drafts | WORKFLOW | live | `db/repositories.py:12650` | `db/repositories.py:12683` | goals |  |  | 068_goal_terminal_contracts | readers have no production caller |
| goal_contract_heads | WORKFLOW | live | `db/repositories.py:12510` | `db/repositories.py:12510` | curriculum,goals | curriculum,diagnosis,goals | doctor | 068_goal_terminal_contracts |  |
| goal_contract_versions | RAW_LEDGER | live | `db/repositories.py:12510` | `db/repositories.py:12510` | curriculum,goals | cli,curriculum,goals,router | doctor | 068_goal_terminal_contracts |  |
| goal_lifecycle_events | RECEIPT | live | `db/stores/router_objective.py:210` | `db/stores/router_objective.py:231` | router_objective | router_objective |  | 243_router_objective_receipts |  |
| golden_path_artifacts | RECEIPT | live | `db/repositories.py:25358` | `db/repositories.py:25358` | curriculum,diagnosis,scheduling | curriculum,diagnosis,learnloop_sidecar,scheduling |  | 087_golden_path_artifacts |  |
| golden_path_run_events | RECEIPT | live | `db/repositories.py:24281` | `db/repositories.py:24570` | curriculum | curriculum |  | 082_golden_path_runs |  |
| golden_path_runs | WORKFLOW | live | `db/repositories.py:24281` | `db/repositories.py:24281` | curriculum | curriculum,diagnosis,learnloop_sidecar,reader,scheduling |  | 082_golden_path_runs |  |
| grade_adjudications | RAW_LEDGER | live | `db/repositories.py:15241` | `db/stores/observation_ledger.py:124` | attempts | adaptive_difficulty,db,field |  | 066_grader_channel |  |
| grade_interpretations | RAW_LEDGER | live | `db/repositories.py:15131` | `db/repositories.py:15177` | attempts | adaptive_difficulty,attempts,cli,compat,db,field,router_objective |  | 066_grader_channel |  |
| grader_calibration_alphas | RAW_LEDGER | live | `db/repositories.py:14878` | `db/repositories.py:14963` | attempts,diagnosis | attempts,diagnosis |  | 066_grader_channel |  |
| grader_calibration_models | RAW_LEDGER | live | `db/repositories.py:14878` | `db/repositories.py:14851` | attempts,diagnosis | attempts,curriculum,diagnosis |  | 066_grader_channel |  |
| grading_clarification_responses | RAW_LEDGER | live | `db/repositories.py:1965` | `db/repositories.py:1907` | attempts | attempts,cli,learnloop_sidecar,router_objective |  | 142_grading_clarifications |  |
| grading_clarifications | RAW_LEDGER | live | `db/repositories.py:1872` | `db/repositories.py:1907` | attempts | attempts,cli,learnloop_sidecar,router_objective |  | 142_grading_clarifications |  |
| grading_evidence | RAW_LEDGER | live | `db/repositories.py:2212` | `confidence_events.py:212` | attempts,db | (generic-name),adaptive_difficulty,attempts,cli,confidence_events,cont | rebuild | 001_initial |  |
| help_assists | RAW_LEDGER | live | `db/stores/help_assists.py:56` | `daily_plan/objective_inputs.py:473` | attempts,hints,learnloop_sidecar,teacher,workbench | (generic-name),algorithm_versions,attempts,cli,config,content,daily_pl | upgrade | 210_help_assists |  |
| hypothesis_events | RAW_LEDGER | live | `db/repositories.py:10308` | `capture/report.py:100` | learner | capture,diagnosis,learner,learnloop_mobile,learnloop_sidecar,tutor |  | 055_hypothesis_events |  |
| hypothesis_exposure_probe_links | RECEIPT | live | `db/stores/hypothesis_marks.py:75` | `db/stores/hypothesis_marks.py:36` | followup_serve | (generic-name),ops |  | 242_hypothesis_marks |  |
| hypothesis_list_exposures | RECEIPT | live | `db/stores/hypothesis_marks.py:61` | `db/stores/hypothesis_marks.py:36` | followup_run | (generic-name),followup_serve,ops |  | 242_hypothesis_marks |  |
| hypothesis_marks | RAW_LEDGER | live | `db/stores/hypothesis_marks.py:68` | `db/stores/hypothesis_marks.py:36` | followup_run | (generic-name),daily_plan,db,router |  | 242_hypothesis_marks |  |
| hypothesis_sets | COMPAT | live | `db/repositories.py:7767` | `db/repositories.py:7803` | diagnosis | diagnosis,followup_serve,instructional |  | 001_initial | role says COMPAT; written by the live probe commissioning and episode paths |
| ingest_batches | WORKFLOW | live | `db/stores/ingest_queue.py:107` | `db/stores/ingest_queue.py:45` | content | cli,content,db,learnloop_sidecar |  | 033_durable_ingest_jobs |  |
| ingest_job_dependencies | WORKFLOW | live | `db/stores/ingest_queue.py:279` | `db/stores/ingest_queue.py:339` | content | content |  | 033_durable_ingest_jobs |  |
| ingest_jobs | WORKFLOW | live | `db/stores/ingest_queue.py:217` | `db/stores/ingest_queue.py:36` | content,db | cli,content,db,figures,learnloop_sidecar,scheduling,source_retrieval |  | 033_durable_ingest_jobs |  |
| instructional_impressions | RAW_LEDGER | live | `db/stores/source_service.py:126` | `db/stores/source_service.py:148` | db,instructional,learnloop_sidecar | adaptive_difficulty,content,instructional,teacher |  | 187_source_service_callers |  |
| interaction_events | RAW_LEDGER | live | `db/repositories.py:12770` | `adaptive_difficulty/material_view.py:1181` | compat,content,diagnosis,reader,remote,substrate | adaptive_difficulty,ai,cli,daily_plan,field,figures,instructional,ops, |  | 065_activity_lineage_substrate |  |
| interactive_figures | WORKFLOW | live | `db/stores/figures.py:136` | `figure_admission.py:101` | figures | (generic-name),attempts,cli,config,content,curriculum,daily_plan,db,di |  | 216_interactive_figures |  |
| intervention_needs | WORKFLOW | live | `db/repositories.py:7482` | `db/repositories.py:5724` | content,diagnosis,instructional,router_objective,tutor | cli,content,diagnosis,followup_run,learnloop_sidecar,router_objective, |  | 007_recall_coverage_interventions |  |
| item_forecast_payloads | WORKFLOW | live | `db/stores/ad_receipts.py:205` | `db/stores/ad_receipts.py:234` | adaptive_difficulty | (generic-name),adaptive_difficulty |  | 213_adaptive_difficulty_receipts |  |
| item_misconception_discrimination | RAW_LEDGER | live | `db/repositories.py:3415` | `db/repositories.py:3457` | diagnosis | diagnosis |  | 025_misconception_registry |  |
| item_serve_inputs | RECEIPT | live | `adaptive_difficulty/serve.py:149` | `adaptive_difficulty/data_check.py:78` | adaptive_difficulty,decider_judgments,reading_sources | adaptive_difficulty,cli,daily_plan,diagnosis,field,router |  | 213_adaptive_difficulty_receipts |  |
| item_skeletons | WORKFLOW | live | `db/stores/pf.py:79` | `db/stores/pf.py:93` | ops | hints,ops,substrate,vault |  | 174_pf_generation |  |
| judgment_ledger | RAW_LEDGER | live | `db/stores/judgments.py:14` | `decider_judgments.py:289` | (generic-name) | (generic-name),adaptive_difficulty,attempts,capture,cli,content,daily_ | upgrade | 166_embedding_substrate_and_judgments |  |
| judgment_work_claims | WORKFLOW | live | `db/stores/judgment_claims.py:37` | `content/authoring/source_exercise_import.py:1537` | content,hints,matching,reader,source_retrieval | ai,capture,content,db,evsi_calibration,experiments,field,hints,instruc |  | 176_recurrence_groups |  |
| lapse_episodes | WORKFLOW | live | `db/repositories.py:23918` | `db/repositories.py:23945` | scheduling | scheduling |  | 079_progression_and_lapse |  |
| learner_claims | RAW_LEDGER | live | `db/repositories.py:5860` | `adaptive_difficulty/replay.py:332` | db,learner,sim,tutor | adaptive_difficulty,algorithm_versions,cli,config,daily_plan,db,field, | rebuild upgrade | 001_initial |  |
| learner_gap_check_advances | RECEIPT | live | `db/stores/learner_gaps.py:174` | `db/stores/learner_gaps.py:187` | diagnosis | placement | upgrade | 182_learner_text_gaps |  |
| learner_gap_commitments | RECEIPT | live | `db/stores/learner_gaps.py:193` | `db/stores/learner_gaps.py:206` | diagnosis | (generic-name) |  | 182_learner_text_gaps |  |
| learner_note_links | RAW_LEDGER | live | `db/stores/learner_notes.py:171` | `db/stores/learner_notes.py:175` | db,source_retrieval | (generic-name),db,source_retrieval,teacher |  | 229_learner_notes |  |
| learner_notes | RAW_LEDGER | live | `db/stores/learner_notes.py:58` | `db/stores/learner_notes.py:52` | source_retrieval | (generic-name),db,source_retrieval |  | 229_learner_notes |  |
| learner_text_gap_jobs | WORKFLOW | live | `db/stores/learner_gaps.py:222` | `db/stores/learner_gaps.py:222` | capture,diagnosis,learnloop_mobile | (generic-name),cli,diagnosis,learnloop_sidecar,teacher |  | 182_learner_text_gaps |  |
| learner_text_gap_reversals | RAW_LEDGER | live | `db/stores/learner_gaps.py:136` | `learner_context.py:1442` | diagnosis | (generic-name),cli,daily_plan,diagnosis,field,figures,instructional,le |  | 182_learner_text_gaps |  |
| learner_text_gaps | RAW_LEDGER | live | `db/stores/learner_gaps.py:67` | `learner_context.py:765` | diagnosis | (generic-name),daily_plan,diagnosis,field,hints,instructional,learner_ | upgrade | 182_learner_text_gaps |  |
| lesson_activity_intervals | RECEIPT | live | `db/stores/lessons.py:270` | `daily_plan/lesson_offer.py:135` | teacher | (generic-name),daily_plan,router_objective |  | 247_lesson_episodes |  |
| lesson_checks | RECEIPT | live | `db/stores/lessons.py:137` | `db/stores/lessons.py:152` | teacher | (generic-name),algorithm_versions,attempts,evsi_calibration,learner,sc | upgrade | 234_teacher_lessons |  |
| lesson_episodes | RECEIPT | live | `db/stores/lessons.py:232` | `db/stores/lessons.py:258` | teacher | (generic-name),evsi_calibration,teacher |  | 247_lesson_episodes |  |
| lesson_plans | RAW_LEDGER | live | `db/stores/lessons.py:120` | `db/stores/lessons.py:120` | daily_plan,db,teacher | (generic-name),daily_plan,db,teacher |  | 234_teacher_lessons |  |
| lesson_receipts | RECEIPT | live | `db/stores/lessons.py:162` | `adaptive_difficulty/lessons.py:56` | db,placement,scheduling,teacher | (generic-name),adaptive_difficulty,daily_plan |  | 234_teacher_lessons |  |
| lesson_turn_payloads | WORKFLOW | live | `db/stores/lessons.py:89` | `db/stores/lessons.py:105` | teacher | (generic-name) |  | 234_teacher_lessons |  |
| lesson_turns | RAW_LEDGER | live | `db/stores/lessons.py:89` | `db/stores/lessons.py:84` | teacher | (generic-name),db,diagnosis |  | 234_teacher_lessons |  |
| lessons | RAW_LEDGER | live | `db/stores/lessons.py:33` | `cli/router.py:207` | teacher | (generic-name),adaptive_difficulty,daily_plan,evsi_calibration,figures | upgrade | 234_teacher_lessons |  |
| library_asks | WORKFLOW | live | `db/stores/library_asks.py:25` | `db/stores/library_asks.py:48` | source_retrieval | cli,learnloop_sidecar,reader,source_retrieval |  | 209_library_asks |  |
| maintenance_notices | WORKFLOW | live | `db/repositories.py:21267` | `db/repositories.py:21267` | curriculum,diagnosis,ops | curriculum,diagnosis,learnloop_sidecar,ops |  | 051_maintenance_feed |  |
| measurement_contract_corrections | RAW_LEDGER | live | `db/repositories.py:11520` | `db/repositories.py:11580` | attempts | adaptive_difficulty,attempts,db,learnloop_sidecar,substrate |  | 116_measurement_contract_corrections |  |
| measurement_events | RAW_LEDGER | live | `db/repositories.py:12007` | `db/repositories.py:14732` | attempts,compat,scheduling,substrate | compat |  | 065_activity_lineage_substrate | readers have no production caller |
| misconception_candidates | WORKFLOW | live | `db/repositories.py:3177` | `learner_context.py:1056` | diagnosis,tutor | cli,diagnosis,evsi_calibration,experiments,field,figures,learner,learn |  | 047_compositional_misconceptions |  |
| misconception_disposition_events | RAW_LEDGER | live | `db/repositories.py:10576` | `learner_context.py:1056` | learner | (generic-name),content,diagnosis,evsi_calibration,figures,instructiona |  | 116_measurement_contract_corrections |  |
| misconception_transition_events | RECEIPT | live | `db/repositories.py:2585` | `db/repositories.py:2924` | diagnosis | diagnosis,field,learner |  | 056_misconception_transitions |  |
| misconceptions | WORKFLOW | live | `db/repositories.py:2585` | `learner_context.py:1056` | diagnosis | (generic-name),cli,content,daily_plan,diagnosis,evsi_calibration,exper | doctor rebuild upgrade | 025_misconception_registry |  |
| missing_vocabulary_notes | RAW_LEDGER | live | `db/repositories.py:16020` | `db/repositories.py:16078` | diagnosis | diagnosis |  | 134_missing_vocabulary_notes |  |
| mobile_devices | WORKFLOW | live | `capture/devices.py:65` | `capture/devices.py:133` | capture,learnloop_mobile | capture,learnloop_mobile,learnloop_sidecar |  | 171_mobile_capture |  |
| mobile_jobs | WORKFLOW | live | `capture/jobs.py:71` | `capture/jobs.py:54` | capture,db,diagnosis,learnloop_mobile | capture,learnloop_mobile,learnloop_sidecar |  | 239_mobile_jobs |  |
| mobile_pairing_attempts | WORKFLOW | live | `capture/devices.py:38` | `capture/devices.py:38` | capture,learnloop_mobile | capture,learnloop_mobile |  | 171_mobile_capture |  |
| mobile_pairing_guard | WORKFLOW | live | `capture/devices.py:38` | `capture/devices.py:65` | capture,learnloop_mobile | capture,learnloop_mobile |  | 171_mobile_capture |  |
| mobile_pairings | WORKFLOW | live | `capture/devices.py:38` | `capture/devices.py:38` | capture,learnloop_mobile | capture,learnloop_mobile |  | 171_mobile_capture |  |
| mobile_request_log | WORKFLOW | live | `capture/maintenance.py:24` | `capture/maintenance.py:24` | capture,learnloop_mobile | capture,learnloop_mobile |  | 171_mobile_capture |  |
| model_call_receipts | RECEIPT | live | `db/stores/model_calls.py:20` | `db/stores/ingest_queue.py:802` | (generic-name),hints | (generic-name),adaptive_difficulty,ai,cli,content,daily_plan,db,diagno |  | 160_model_call_receipts |  |
| model_work_checkpoints | WORKFLOW | live | `db/stores/model_calls.py:29` | `daily_plan/router_teach_back.py:243` | adaptive_difficulty,hints | adaptive_difficulty,content,daily_plan,field,hints,ops,practice_index, |  | 160_model_call_receipts |  |
| notation_mappings | RAW_LEDGER | live | `db/repositories.py:20039` | `db/repositories.py:21048` | adaptive_difficulty,content | content |  | 044_provenance_manifests_apply_intents |  |
| observation_events | RAW_LEDGER | live | `db/repositories.py:5823` | `db/repositories.py:5853` | attempts | ops |  | 001_initial |  |
| observation_templates | RAW_LEDGER | live | `db/repositories.py:5779` | `db/repositories.py:5806` | attempts | attempts,cli |  | 001_initial |  |
| outcome_schema_versions | RAW_LEDGER | live | `db/repositories.py:14772` | `db/repositories.py:14772` | attempts | attempts,substrate |  | 066_grader_channel |  |
| outcome_schemas | RAW_LEDGER | live | `db/repositories.py:14755` | `db/repositories.py:14755` | attempts | attempts,substrate |  | 066_grader_channel |  |
| p2_ladder_policies | RAW_LEDGER | live | migration seed | `db/repositories.py:25080` |  | curriculum |  | 084_pattern_ladder | seeded by migration |
| p2_ladder_stages | RAW_LEDGER | live | migration seed | `db/repositories.py:25089` |  | curriculum |  | 084_pattern_ladder | seeded by migration |
| parameter_bind_events | RECEIPT | live | `db/repositories.py:7145` | `db/repositories.py:7167` | params | params |  | 069_parameter_registry |  |
| parameter_registry | RAW_LEDGER | live | `db/repositories.py:7007` | `db/repositories.py:7058` | params | cli,params | upgrade | 069_parameter_registry |  |
| parameter_registry_manifests | RECEIPT | live | `db/repositories.py:7072` | `db/repositories.py:7072` | params | params |  | 069_parameter_registry |  |
| parameter_sensitivity_certificates | RECEIPT | live | `db/repositories.py:7111` | `db/repositories.py:7137` | params | params |  | 069_parameter_registry |  |
| passage_links | WORKFLOW | live | `db/stores/reader_cue_links.py:40` | `db/stores/reader_cue_links.py:40` | db,source_retrieval | db,reader,source_retrieval |  | 215_reader_discovered_cues |  |
| persona_realism_runs | RECEIPT | live | `db/repositories.py:26456` | `db/repositories.py:26507` | content | content,diagnosis |  | 144_diagnostic_augmentation |  |
| pf_candidates | WORKFLOW | live | `db/stores/pf.py:29` | `db/stores/pf.py:58` | ops | (generic-name),cli,ops |  | 174_pf_generation |  |
| placement_quick_check_items | WORKFLOW | live | `db/stores/placement.py:71` | `placement/decisions.py:546` | diagnosis,placement | diagnosis |  | 173_placement_quick_check_presentations |  |
| placement_quick_checks | WORKFLOW | live | `db/stores/placement.py:43` | `diagnosis/quick_check.py:88` | diagnosis,placement | diagnosis,placement |  | 172_placement_assumptions |  |
| plan_presentations | RAW_LEDGER | live | `db/stores/plan_presentations.py:39` | `adaptive_difficulty/material_view.py:1378` | daily_plan | (generic-name),adaptive_difficulty,daily_plan,db,evsi_calibration,lear |  | 202_router_staged_frame |  |
| plan_usage_pauses | RAW_LEDGER | live | `db/stores/figure_prefetch.py:43` | `figures/prefetch.py:990` | figures | adaptive_difficulty,ai,cli,config,content,curriculum,db,figures,learnl |  | 237_figure_prefetch |  |
| policy_experiment_assignments | RECEIPT | live | `db/stores/router_objective.py:223` | `daily_plan/objective_chooser.py:321` | router_objective,scheduling | (generic-name),daily_plan,ops | upgrade | 098_controller_randomization_and_outcomes |  |
| post_attempt_jobs | WORKFLOW | live | `db/stores/diagnoses.py:100` | `db/stores/diagnoses.py:446` | attempts,cli,diagnosis,placement,scheduling | (generic-name),cli,daily_plan,db,diagnosis,learnloop_sidecar,ops,place | doctor | 170_blind_grading_diagnosis_split |  |
| practice_attempts | RAW_LEDGER | live | `db/repositories.py:2262` | `confidence_events.py:240` | attempts,db,diagnosis,evsi_calibration | (generic-name),adaptive_difficulty,ai,algorithm_versions,attempts,capt | doctor rebuild upgrade | 001_initial |  |
| practice_eval_queries | WORKFLOW | live | `db/stores/practice_index.py:196` | `db/stores/practice_index.py:184` | practice_index | practice_index |  | 169_practice_index |  |
| practice_index_evaluations | RECEIPT | live | `db/stores/practice_index.py:210` | `db/stores/practice_index.py:222` | practice_index | cli,practice_index |  | 169_practice_index |  |
| practice_index_proposals | RECEIPT | live | `db/stores/practice_index.py:110` | `db/stores/practice_index.py:164` | practice_index | (generic-name),cli |  | 169_practice_index |  |
| practice_item_snapshots | RECEIPT | live | `db/repositories.py:9562` | `learner_context.py:236` | adaptive_difficulty,diagnosis,scheduling | (generic-name),adaptive_difficulty,attempts,cli,content,curriculum,dat |  | 164_item_snapshots_and_adjudication_fk |  |
| practice_item_state | COMPAT | live | `db/repositories.py:1198` | `delayed_checks.py:146` | content,db,diagnosis,followup_run,followup_serve,goals,learnloop_sidec | (generic-name),cli,daily_plan,goals,router_objective,substrate,teacher | doctor rebuild sync upgrade | 001_initial | role says COMPAT; it is the live FSRS memory state (written every attempt, read by the objective) |
| practice_pool_events | RECEIPT | live | `db/repositories.py:25119` | `db/repositories.py:25320` | substrate | substrate |  | 085_surface_pool |  |
| practice_pool_surfaces | RAW_LEDGER | live | `db/repositories.py:25163` | `db/repositories.py:25163` | substrate | substrate |  | 085_surface_pool |  |
| practice_pools | RAW_LEDGER | live | `db/repositories.py:25119` | `db/repositories.py:25119` | substrate | learnloop_sidecar,substrate |  | 085_surface_pool |  |
| prefilter_payloads | RECEIPT | live | `db/stores/data_capture.py:60` | `db/stores/data_capture.py:99` | data_capture,db | data_capture,ops |  | 240_data_capture |  |
| prefilter_receipts | RECEIPT | live | `db/stores/data_capture.py:60` | `db/stores/data_capture.py:94` | data_capture,db | data_capture,ops |  | 240_data_capture |  |
| probe_calibration_sessions | WORKFLOW | live | `db/repositories.py:9227` | `db/repositories.py:9264` | diagnosis,placement | diagnosis,placement |  | 029_probe_selection_and_calibration |  |
| probe_episodes | WORKFLOW | live | `db/repositories.py:7813` | `db/repositories.py:7878` | diagnosis,followup_serve,learnloop_sidecar,tui | attempts,cli,curriculum,daily_plan,diagnosis,followup_run,followup_ser | sync upgrade | 028_probe_episodes |  |
| probe_family_calibrations | RAW_LEDGER | live | `db/repositories.py:8638` | `db/repositories.py:8638` | diagnosis | diagnosis |  | 028_probe_episodes |  |
| probe_family_lifecycle_events | RECEIPT | live | `db/repositories.py:8469` | `db/repositories.py:8502` | diagnosis |  |  | 030_probe_pilot_and_policy | readers have no production caller |
| probe_family_templates | RAW_LEDGER | live | `db/repositories.py:8388` | `db/repositories.py:8411` | diagnosis,sim | diagnosis |  | 028_probe_episodes |  |
| probe_generation_needs | WORKFLOW | live | `db/repositories.py:8916` | `db/repositories.py:8916` | diagnosis | adaptive_difficulty,daily_plan,diagnosis,scheduling |  | 028_probe_episodes |  |
| probe_instrument_cards | RAW_LEDGER | live | `db/repositories.py:8522` | `db/repositories.py:8560` | diagnosis | compat,diagnosis |  | 028_probe_episodes |  |
| probe_item_calibrations | RAW_LEDGER | live | `db/repositories.py:8756` | `db/repositories.py:8756` | diagnosis | diagnosis |  | 030_probe_pilot_and_policy |  |
| probe_item_family_links | RAW_LEDGER | live | `db/repositories.py:8582` | `db/repositories.py:8618` | diagnosis,followup_run | adaptive_difficulty,diagnosis |  | 028_probe_episodes |  |
| probe_manipulation_audits | RECEIPT | live | `db/repositories.py:16498` | `db/repositories.py:16547` | diagnosis | diagnosis |  | 121_causal_probe_coherence |  |
| probe_observations | RAW_LEDGER | live | `db/repositories.py:8207` | `db/repositories.py:8257` | diagnosis | diagnosis,followup_serve,held_grades,learnloop_sidecar,placement,route |  | 028_probe_episodes |  |
| probe_presentations | RAW_LEDGER | live | `db/repositories.py:408` | `learner_protection.py:190` | db,diagnosis,followup_serve,learnloop_sidecar,scheduling | (generic-name),adaptive_difficulty,attempts,compat,confidence_events,c |  | 028_probe_episodes |  |
| probe_regrade_checks | RECEIPT | live | `db/repositories.py:8857` | `db/repositories.py:8893` | diagnosis | diagnosis |  | 030_probe_pilot_and_policy |  |
| probe_state_segments | WORKFLOW | live | `db/repositories.py:7983` | `db/repositories.py:7983` | diagnosis | diagnosis |  | 028_probe_episodes |  |
| proposed_patch_item_dependencies | WORKFLOW | live | `db/repositories.py:11195` | `db/repositories.py:11382` | content,curriculum,diagnosis | content |  | 035_proposal_dependencies |  |
| proposed_patch_items | WORKFLOW | live | `curriculum/concepts.py:337` | `content/pipeline/add_source.py:2538` | content,curriculum,diagnosis,learnloop_sidecar | cli,content,curriculum,db,diagnosis,learnloop_sidecar,ops,tutor | doctor | 001_initial |  |
| proposed_patches | WORKFLOW | live | `db/repositories.py:11195` | `db/repositories.py:11174` | content,curriculum,db,diagnosis | content,curriculum,diagnosis,learnloop_sidecar,ops | doctor | 001_initial |  |
| question_classifications | WORKFLOW | live | `db/stores/field.py:24` | `field/classification.py:61` | field | field |  | 167_learner_field_outcomes |  |
| question_events | RAW_LEDGER | live | `db/repositories.py:4474` | `learner_protection.py:600` | hints,learnloop_sidecar,reader,tutor | (generic-name),adaptive_difficulty,attempts,cli,daily_plan,diagnosis,f |  | 019_question_events |  |
| question_promotion_requests | WORKFLOW | live | `db/repositories.py:5252` | `db/repositories.py:5339` | content,learnloop_sidecar,tutor | content,learnloop_sidecar,tutor |  | 117_question_promotion_jobs_and_queue_revision |  |
| question_promotions | WORKFLOW | live | `db/repositories.py:5075` | `db/repositories.py:5202` | tutor | adaptive_difficulty,content,daily_plan,learnloop_sidecar,scheduling,tu |  | 027_question_promotions |  |
| queue_state | WORKFLOW | live | `db/repositories.py:5479` | `db/repositories.py:5469` | content,diagnosis,instructional,intent,learnloop_mobile,learnloop_side | content,diagnosis,instructional,intent,learnloop_mobile,learnloop_side |  | 117_question_promotion_jobs_and_queue_revision |  |
| raw_grade_events | RAW_LEDGER | live | `db/repositories.py:15041` | `db/repositories.py:15089` | attempts | attempts,cli,compat,field |  | 066_grader_channel |  |
| reader_authored_questions | WORKFLOW | live | `db/repositories.py:13869` | `db/repositories.py:13948` | adaptive_difficulty,content,reader | cli,content,diagnosis,learnloop_sidecar,reader |  | 105_reader_authored_questions |  |
| reader_background_requests | WORKFLOW | live | `db/repositories.py:13519` | `db/repositories.py:13608` | adaptive_difficulty,content,reader | content,learnloop_sidecar,reader |  | 093_reader_background_requests |  |
| reader_capture_outbox | WORKFLOW | live | `db/repositories.py:13338` | `db/repositories.py:13330` | adaptive_difficulty,content,reader | learnloop_sidecar,reader |  | 091_interaction_events_reader_envelope |  |
| reader_cue_impressions | RECEIPT | live | `db/stores/reader_cue_links.py:124` | `db/stores/reader_cue_links.py:142` | cli,db,instructional,learner,learnloop_sidecar,projects | adaptive_difficulty,db,instructional,learnloop_sidecar,practice_index, |  | 215_reader_discovered_cues |  |
| reader_path_depths | WORKFLOW | live | `db/stores/reading_paths.py:35` | `db/stores/reading_paths.py:41` | source_retrieval | reader,source_retrieval |  | 217_reader_reading_paths |  |
| reader_path_sections | WORKFLOW | live | `db/stores/reading_paths.py:48` | `db/stores/reading_paths.py:55` | source_retrieval | (generic-name),cli,db,reader,source_retrieval |  | 217_reader_reading_paths |  |
| reader_section_progress | WORKFLOW | live | `db/repositories.py:14015` | `daily_plan/engine.py:482` | adaptive_difficulty,content,learnloop_sidecar | content,daily_plan,data_capture,db,diagnosis,figures,learnloop_sidecar |  | 106_reader_section_progress |  |
| reader_session_digests | WORKFLOW | live | `db/stores/reader_digests.py:34` | `db/stores/reader_digests.py:109` | instructional | (generic-name),adaptive_difficulty,cli,content,daily_plan,db,experimen | upgrade | 227_reader_session_digests |  |
| reading_exposure_receipts | RECEIPT | live | `db/stores/data_capture.py:209` | `db/stores/data_capture.py:172` | data_capture | data_capture |  | 240_data_capture |  |
| recurrence_escalations | RECEIPT | live | `db/stores/recurrence.py:367` | `db/stores/recurrence.py:367` | diagnosis | db,diagnosis |  | 176_recurrence_groups |  |
| recurrence_guard_cases | RAW_LEDGER | live | `db/stores/recurrence.py:455` | `db/stores/recurrence.py:480` | diagnosis | db |  | 176_recurrence_groups |  |
| reference_key_checks | RAW_LEDGER | live | `db/stores/source_service.py:394` | `content/authoring/source_exercise_import.py:1387` | content,ops | content,db,learnloop_sidecar,ops |  | 188_source_exercise_imports |  |
| remediation_episodes | WORKFLOW | live | `db/repositories.py:3736` | `learner_context.py:1148` | diagnosis | adaptive_difficulty,attempts,confidence_events,content,daily_plan,diag |  | 058_remediation_episodes |  |
| retirement_records | RECEIPT | live | `db/repositories.py:12728` | `db/repositories.py:15455` | substrate |  |  | 065_activity_lineage_substrate | readers have no production caller |
| retrieval_feedback | RECEIPT | live | `db/stores/retrieval_spaces.py:87` | `db/stores/retrieval_spaces.py:105` | curriculum,source_retrieval,substrate | content,db,local_embeddings,source_retrieval | rebuild | 220_retrieval_spaces |  |
| retrieval_interventions | RAW_LEDGER | live | `db/stores/source_service.py:1051` | `db/stores/source_service.py:1087` | instructional | cli,config,diagnosis,hints,instructional,learner,learnloop_sidecar,rem |  | 193_retrieval_interventions |  |
| reveal_events | RAW_LEDGER | live | `db/repositories.py:4859` | `delayed_checks.py:29` | attempts,workbench | (generic-name),adaptive_difficulty,attempts,causal_activity_policy,con |  | 154_reveal_ledger |  |
| router_decision_bindings | RECEIPT | live | `db/stores/followup_serve.py:350` | `db/stores/followup_serve.py:363` | followup_run,followup_serve | router,router_objective |  | 241_followup_generate_serve |  |
| router_decision_payloads | WORKFLOW | live | `db/stores/router.py:261` | `cli/router.py:111` | router | cli,daily_plan,followup_run,learnloop_sidecar,router |  | 202_router_staged_frame |  |
| router_decisions | RAW_LEDGER | live | `db/stores/router.py:110` | `cli/router.py:111` | daily_plan,db,router | (generic-name),cli,confidence_events,config,daily_plan,db,diagnosis,ev | rebuild upgrade | 181_router_decisions |  |
| router_learner_preferences | RAW_LEDGER | live | - | - | daily_plan | router |  | 251_router_learner_preferences | IH3, migration 251, on instruct/handoff only |
| router_objective_traces | RECEIPT | live | `db/stores/router_objective.py:170` | `daily_plan/objective_chooser.py:251` | router_objective | (generic-name),adaptive_difficulty,daily_plan,field,learner_context,ro | upgrade | 246_router_objective_traces |  |
| router_suggestion_responses | RAW_LEDGER | live | `db/stores/router_suggestions.py:167` | `db/stores/router_suggestions.py:122` | daily_plan,projects | (generic-name),daily_plan,db,router,router_objective,teacher | upgrade | 236_router_lesson_suggestions |  |
| rung_variant_requests | WORKFLOW | live | `db/repositories.py:5500` | `db/repositories.py:5393` | content,learnloop_sidecar | adaptive_difficulty,content,daily_plan,db,learner,learnloop_sidecar,sc |  | 108_rung_variant_requests |  |
| scheduler_explanations | RECEIPT | live | `db/repositories.py:9510` | `db/repositories.py:9510` | scheduling | cli,learnloop_sidecar,scheduling |  | 001_initial |  |
| scheduler_offer_receipts | RECEIPT | live | `db/stores/collection.py:54` | `capture/report.py:100` | learnloop_sidecar | adaptive_difficulty,capture,daily_plan,learnloop_mobile,learnloop_side |  | 161_collection_contract |  |
| scheduler_slate_candidates | WORKFLOW | live | `db/repositories.py:9562` | `capture/report.py:100` | diagnosis,evsi_calibration,learnloop_sidecar,scheduling | (generic-name),adaptive_difficulty,capture,daily_plan,db,evsi_calibrat |  | 010_scheduler_training_logs |  |
| scheduler_slates | WORKFLOW | live | `db/repositories.py:9562` | `daily_plan/engine.py:5255` | diagnosis,evsi_calibration,learnloop_sidecar,scheduling | daily_plan,db,diagnosis,evsi_calibration,learnloop_sidecar,scheduling |  | 010_scheduler_training_logs |  |
| schema_migrations | RECEIPT | live | `db/migrate.py:286` | `db/migrate.py:123` | db | cli,db,experiments,learnloop_mobile,learnloop_sidecar,ops,remote |  | 001_initial |  |
| section_coverage | WORKFLOW | live | `db/stores/section_coverage.py:41` | `db/stores/data_capture.py:193` | (generic-name),source_retrieval | (generic-name),attempts,cli,config,content,data_capture,db,experiments |  | 222_section_coverage |  |
| session_checkpoints | WORKFLOW | live | `db/repositories.py:1358` | `db/repositories.py:1358` | content,learnloop_mobile,learnloop_sidecar,placement | content,daily_plan,db,hints,learnloop_mobile,learnloop_sidecar,placeme |  | 001_initial |  |
| session_handoffs | RECEIPT | live | `db/stores/session_ownership.py:341` | `db/stores/session_ownership.py:104` | db | learnloop_sidecar,router_objective |  | 226_session_ownership |  |
| session_receipts | RECEIPT | live | `db/stores/router_objective.py:127` | `daily_plan/objective_inputs.py:168` | router_objective | daily_plan,learnloop_sidecar,router_objective |  | 243_router_objective_receipts |  |
| sessions | WORKFLOW | live | `db/repositories.py:9816` | `capture/report.py:100` | db,learnloop_mobile,learnloop_sidecar | (generic-name),capture,daily_plan,db,diagnosis,learner,learnloop_mobil | upgrade | 001_initial |  |
| source_annotation_anchor_segments | RAW_LEDGER | live | `db/repositories.py:13248` | `db/repositories.py:13055` | db | learnloop_sidecar,reader,source_retrieval |  | 090_source_annotations |  |
| source_annotation_anchor_versions | RAW_LEDGER | live | `db/repositories.py:13248` | `db/repositories.py:13055` | adaptive_difficulty,content,db | diagnosis,field,ingest,learnloop_sidecar,reader,scheduling,source_retr |  | 090_source_annotations |  |
| source_annotation_events | RAW_LEDGER | live | `db/repositories.py:13118` | `db/repositories.py:13118` | reader | db,learnloop_sidecar,reader |  | 090_source_annotations |  |
| source_annotation_versions | RAW_LEDGER | live | `db/repositories.py:13220` | `db/repositories.py:13046` | adaptive_difficulty,content,db | db,learnloop_sidecar,reader,source_retrieval |  | 090_source_annotations |  |
| source_annotations | RAW_LEDGER | live | `db/repositories.py:13036` | `db/repositories.py:13055` | learnloop_sidecar,reader | adaptive_difficulty,content,learnloop_sidecar,reader,source_retrieval |  | 090_source_annotations |  |
| source_artifacts | RAW_LEDGER | live | `db/repositories.py:19659` | `db/repositories.py:19709` | adaptive_difficulty,content,learnloop_sidecar | adaptive_difficulty,cli,content,figures,intent,learner_context,learnlo | doctor | 032_source_layer |  |
| source_auto_build_state | WORKFLOW | live | `db/repositories.py:19743` | `db/repositories.py:19727` | adaptive_difficulty,content,db | content |  | 198_add_book_state |  |
| source_block_health | RAW_LEDGER | live | `db/repositories.py:12981` | `db/repositories.py:13017` | adaptive_difficulty,content,figures,learnloop_sidecar | figures,learnloop_sidecar,params,reader |  | 089_source_block_health |  |
| source_comparisons | WORKFLOW | live | `db/stores/source_service.py:861` | `db/stores/source_service.py:888` | source_retrieval | reader,source_retrieval |  | 189_source_comparisons |  |
| source_conflict_resolutions | RECEIPT | live | `db/repositories.py:21210` | `db/repositories.py:21249` | content,learnloop_sidecar | content |  | 051_maintenance_feed |  |
| source_conflicts | WORKFLOW | live | `db/repositories.py:21062` | `db/repositories.py:21115` | content,learnloop_sidecar | cli,content,learnloop_sidecar,ops |  | 044_provenance_manifests_apply_intents |  |
| source_document_assets | RAW_LEDGER | live | `db/repositories.py:20039` | `db/repositories.py:20298` | adaptive_difficulty,content | (generic-name),content |  | 032_source_layer |  |
| source_document_blocks | RAW_LEDGER | live | `db/repositories.py:20039` | `content/pipeline/add_source.py:154` | adaptive_difficulty,content,experiments | (generic-name),content,db,diagnosis,experiments,figure_admission,hints | doctor | 032_source_layer |  |
| source_document_units | RAW_LEDGER | live | `db/repositories.py:20039` | `content/pipeline/add_source.py:154` | adaptive_difficulty,content | (generic-name),content,diagnosis,experiments,instructional,learnloop_s |  | 032_source_layer |  |
| source_exercise_imports | WORKFLOW | live | `db/stores/source_service.py:291` | `content/authoring/source_exercise_import.py:1507` | content,instructional,learnloop_sidecar | (generic-name),content,diagnosis,instructional,learnloop_sidecar,reade |  | 188_source_exercise_imports |  |
| source_exposure_events | RAW_LEDGER | live | `db/repositories.py:4558` | `db/repositories.py:4602` | adaptive_difficulty,content,diagnosis,instructional,reader | adaptive_difficulty,attempts,content,db,diagnosis,instructional,learnl |  | 049_source_exposure_events |  |
| source_extraction_runs | WORKFLOW | live | `db/repositories.py:20210` | `adaptive_difficulty/material_view.py:838` | content | (generic-name),adaptive_difficulty,attempts,content,db,diagnosis,inten | doctor | 032_source_layer |  |
| source_held_out_signal_marks | RAW_LEDGER | live | `db/repositories.py:20039` | `content/sources/exam_material.py:661` | adaptive_difficulty,content,db,migration_coordinator,vault | content,db,migration_coordinator,vault |  | 204_source_held_out_signal_marks |  |
| source_object_citations | RAW_LEDGER | live | `db/repositories.py:14319` | `content/pipeline/reread.py:534` | adaptive_difficulty,content,reader | adaptive_difficulty,content,db,figures,ops,reader,source_retrieval | doctor | 094_source_objects |  |
| source_object_relations | RAW_LEDGER | live | `db/repositories.py:14409` | `db/repositories.py:14429` | adaptive_difficulty,content,reader | reader,source_retrieval |  | 094_source_objects |  |
| source_object_versions | RAW_LEDGER | live | `db/repositories.py:14319` | `content/sources/span_aliases.py:351` | reader | adaptive_difficulty,cli,content,db,figures,ops,reader,source_retrieval | doctor | 094_source_objects |  |
| source_objects | RAW_LEDGER | live | `db/repositories.py:14309` | `db/repositories.py:14373` | reader | adaptive_difficulty,content,learnloop_sidecar,reader,source_retrieval |  | 094_source_objects |  |
| source_render_block_crosswalk | RAW_LEDGER | live | `db/repositories.py:12936` | `db/repositories.py:12970` | adaptive_difficulty,content,reader | reader |  | 088_source_render_views |  |
| source_render_views | WORKFLOW | live | `db/repositories.py:12873` | `db/repositories.py:12913` | reader | adaptive_difficulty,content,reader |  | 088_source_render_views |  |
| source_revisions | RAW_LEDGER | live | `db/repositories.py:19975` | `adaptive_difficulty/material_view.py:838` | content | (generic-name),adaptive_difficulty,attempts,capture,cli,content,db,dia | doctor | 032_source_layer |  |
| source_service_spend | WORKFLOW | live | `db/stores/source_service.py:1548` | `db/stores/source_service.py:1329` | db,source_retrieval | db,source_retrieval |  | 194_source_service_spend |  |
| source_span_reanchors | RAW_LEDGER | live | `db/repositories.py:20039` | `db/repositories.py:20039` | adaptive_difficulty,content | adaptive_difficulty,content,learnloop_sidecar |  | 032_source_layer |  |
| source_tool_calls | RECEIPT | live | `db/stores/source_service.py:974` | `db/stores/source_service.py:1001` | instructional | instructional,learnloop_sidecar,reader,source_retrieval,teacher |  | 192_source_tool_calls |  |
| source_unit_inventories | RAW_LEDGER | live | `db/repositories.py:20039` | `adaptive_difficulty/data_check.py:177` | adaptive_difficulty,content | adaptive_difficulty,content,learnloop_sidecar |  | 041_source_unit_inventories |  |
| source_unit_selections | WORKFLOW | live | `db/repositories.py:20039` | `content/sources/exam_material.py:533` | adaptive_difficulty,content | cli,content,learnloop_sidecar |  | 040_source_unit_selections |  |
| submission_intents | RAW_LEDGER | live | `db/stores/collection.py:157` | `attempts/attempts.py:1790` | learnloop_sidecar | (generic-name),adaptive_difficulty,attempts,learnloop_sidecar |  | 161_collection_contract |  |
| surface_fingerprint_memberships | RAW_LEDGER | live | `db/repositories.py:23326` | `db/repositories.py:23326` | learner | learner,scheduling |  | 077_familiarity_namespace |  |
| surface_mint_requests | WORKFLOW | live | `db/repositories.py:23526` | `db/repositories.py:23526` | ops,substrate | ops,substrate |  | 078_surface_mint_jobs |  |
| synthesis_generation_needs | WORKFLOW | live | `db/repositories.py:9090` | `db/repositories.py:9090` | content,curriculum,learner | content,curriculum,diagnosis,learner |  | 045_synthesis_generation_needs |  |
| synthesis_manifests | RAW_LEDGER | live | `db/repositories.py:21405` | `content/pipeline/add_source.py:2538` | content | content,daily_plan |  | 044_provenance_manifests_apply_intents |  |
| synthesis_runs | WORKFLOW | live | `db/repositories.py:21479` | `content/pipeline/add_source.py:2538` | content | cli,content,daily_plan,learnloop_sidecar,ops |  | 044_provenance_manifests_apply_intents |  |
| synthesis_shard_results | RAW_LEDGER | live | `db/repositories.py:21581` | `db/repositories.py:21621` | content | content |  | 064_synthesis_shard_results |  |
| target_exemplars | RAW_LEDGER | live | `db/repositories.py:24027` | `db/repositories.py:24196` | curriculum | curriculum,learnloop_sidecar |  | 081_task_blueprints |  |
| task_blueprint_review_events | RECEIPT | live | `db/repositories.py:24027` | `db/repositories.py:24204` | curriculum | reader |  | 081_task_blueprints |  |
| task_blueprint_versions | RAW_LEDGER | live | `db/repositories.py:24027` | `db/repositories.py:24027` | curriculum | curriculum,diagnosis,learnloop_sidecar,reader |  | 081_task_blueprints |  |
| task_blueprints | RAW_LEDGER | live | `db/repositories.py:23998` | `db/repositories.py:23998` | curriculum | curriculum,reader |  | 081_task_blueprints |  |
| task_feature_schema_versions | RAW_LEDGER | live | `db/repositories.py:22739` | `db/repositories.py:22739` | substrate | content,curriculum,substrate |  | 073_activity_patterns_and_features |  |
| text_write_provenance | RAW_LEDGER | live | `db/stores/write_provenance.py:308` | `db/stores/write_provenance.py:356` | db,diagnosis | db,figures,followup_run,learner_context |  | 205_write_provenance |  |
| trace_exercised_facets | RAW_LEDGER | live | `db/repositories.py:2078` | `db/repositories.py:2128` | attempts | adaptive_difficulty,attempts,learner,learnloop_sidecar,substrate |  | 141_conjunctive_instruments |  |
| unresolved_cause_factors | WORKFLOW | live | `db/repositories.py:17626` | `learner_context.py:1235` | diagnosis,followup_run,followup_serve,substrate | (generic-name),adaptive_difficulty,attempts,cli,daily_plan,db,diagnosi |  | 034_assessment_contract_snapshots |  |
| vault_epigraphs | RAW_LEDGER | live | `db/repositories.py:14203` | `content/synthesis/vault_epigraphs.py:61` | content | content,learnloop_sidecar |  | 158_vault_epigraphs |  |
| voi_forecasts | RECEIPT | live | `db/stores/voi_forecasts.py:48` | `db/stores/voi_forecasts.py:42` | db,goals,scheduling | adaptive_difficulty,db,evsi_calibration,goals,scheduling,teacher |  | 184_voi_forecasts |  |
| workbench_sessions | WORKFLOW | live | `db/stores/workbench.py:88` | `db/stores/workbench.py:77` | reader | db,diagnosis,field,hints,instructional,learner,learnloop_sidecar,reade |  | 207_workbench |  |
| workbench_steps | RAW_LEDGER | live | `db/stores/workbench.py:198` | `db/stores/workbench.py:171` | reader | diagnosis,field,reader,source_retrieval,workbench |  | 207_workbench |  |
| ability_transition_events | DERIVED | derived and rebuildable | `db/repositories.py:6084` | `db/repositories.py:6084` | attempts,db,goals,substrate,tutor | attempts,goals,substrate,tutor | replay:learning_state | 008_ability_transition_events |  |
| ad_attempt_trace | DERIVED | derived and rebuildable | `db/stores/ad_serving.py:418` | `db/stores/ad_serving.py:459` | adaptive_difficulty | db | replay:adaptive_difficulty | 214_adaptive_difficulty_serving |  |
| ad_state | DERIVED | derived and rebuildable | `db/stores/ad_serving.py:407` | `db/stores/ad_serving.py:449` | adaptive_difficulty,learner,teacher | db | replay:adaptive_difficulty | 214_adaptive_difficulty_serving |  |
| attempt_surprise | DERIVED | derived and rebuildable | `db/repositories.py:5749` | `db/repositories.py:1790` | attempts,content,db,diagnosis,goals,substrate,tutor | attempts,cli,content,db,diagnosis,evsi_calibration,goals,learner,learn | replay:learning_state doctor | 001_initial |  |
| capability_residual_state | DERIVED | derived and rebuildable | - | `db/repositories.py:6578` |  | substrate | replay:canonical_projection | 050_capability_residual_and_identifiability |  |
| confidence_calibration_state | DERIVED | derived and rebuildable | `learner/lesson_weight.py:957` | - | adaptive_difficulty,db,teacher |  | replay:lesson_weight | 234_teacher_lessons |  |
| facet_capability_evidence | DERIVED | derived and rebuildable | - | `db/repositories.py:6362` |  | adaptive_difficulty,attempts,content,daily_plan,diagnosis,goals,hints, | replay:canonical_projection | 037_canonical_facet_state |  |
| facet_outcome_observations | DERIVED | derived and rebuildable | `db/stores/field.py:12` | `db/stores/field.py:12` | field | field | replay:field_outcomes | 167_learner_field_outcomes |  |
| facet_recall_state | DERIVED | derived and rebuildable | - | `db/repositories.py:6330` |  | content,goals,learner,learnloop_sidecar,ops,sim | replay:canonical_projection doctor | 037_canonical_facet_state |  |
| family_memory_state | DERIVED | derived and rebuildable | `substrate/family_memory.py:27` | `substrate/family_memory.py:27` | substrate | substrate | replay:family_memory | 168_activity_family_membership |  |
| hypothesis_recurrence_groups | DERIVED | derived and rebuildable | `db/stores/recurrence.py:56` | `learner_context.py:1148` | substrate | db,diagnosis,learner_context,recurrence,scheduling,substrate,tutor | replay:recurrence_groups | 176_recurrence_groups |  |
| hypothesis_recurrence_review | DERIVED | derived and rebuildable | `db/stores/recurrence.py:56` | `db/stores/recurrence.py:185` | substrate | db | replay:recurrence_groups | 176_recurrence_groups |  |
| hypothesis_recurrence_state | DERIVED | derived and rebuildable | `db/stores/recurrence.py:56` | `db/stores/recurrence.py:114` | substrate | cli,db,diagnosis,recurrence,substrate,tutor | replay:recurrence_groups | 176_recurrence_groups |  |
| item_fingerprints | DERIVED | derived and rebuildable | `db/stores/pf.py:112` | `db/stores/pf.py:112` | substrate | content,ops,substrate | replay:item_fingerprints | 174_pf_generation |  |
| item_forecast_scores | DERIVED | derived and rebuildable | `db/stores/ad_serving.py:433` | `db/stores/ad_serving.py:470` | adaptive_difficulty | db | replay:item_forecast_scores | 214_adaptive_difficulty_serving |  |
| item_parameter_state | DERIVED | derived and rebuildable | `db/repositories.py:6084` | `db/repositories.py:6084` | db,goals,substrate,tutor | adaptive_difficulty,attempts,delayed_checks,goals,placement,substrate, | replay:learning_state | 016_fitted_parameters |  |
| learning_object_mastery | DERIVED | derived and rebuildable | `db/repositories.py:1417` | `daily_plan/objective_inputs.py:129` | db,goals,learner,substrate,tutor,upgrade | (generic-name),adaptive_difficulty,daily_plan,diagnosis,goals,hints,le | replay:learning_state doctor | 001_initial |  |
| learning_outcome_labels | DERIVED | derived and rebuildable | `db/repositories.py:6167` | `db/repositories.py:6167` | attempts,db | attempts,scheduling | replay:learning_state | 010_scheduler_training_logs |  |
| lesson_weight_state | DERIVED | derived and rebuildable | `learner/lesson_weight.py:957` | - | adaptive_difficulty,db,teacher |  | replay:lesson_weight | 234_teacher_lessons |  |
| lesson_weight_trace | DERIVED | derived and rebuildable | `learner/lesson_weight.py:957` | - | adaptive_difficulty,db,teacher |  | replay:lesson_weight | 234_teacher_lessons |  |
| practice_item_quality_state | DERIVED | derived and rebuildable | `db/repositories.py:6084` | `db/repositories.py:6084` | db,goals,substrate,tutor | attempts,diagnosis,goals,learner,ops,scheduling,substrate,tutor | replay:learning_state doctor | 007_recall_coverage_interventions |  |
| retrieval_fusion_posteriors | DERIVED | derived and rebuildable | `db/stores/retrieval_spaces.py:164` | `db/stores/retrieval_spaces.py:164` | local_embeddings | content,local_embeddings,source_retrieval | replay:retrieval_fusion_posteriors | 220_retrieval_spaces |  |
| retrieval_intervention_outcomes | DERIVED | derived and rebuildable | `db/stores/source_service.py:1104` | `db/stores/source_service.py:1120` | db,substrate | (generic-name),substrate | replay:retrieval_intervention_outcomes | 193_retrieval_interventions |  |
| router_outcomes | DERIVED | derived and rebuildable | `db/stores/router.py:306` | `db/stores/router.py:306` | router | evsi_calibration,router,router_objective | replay:router_outcomes upgrade | 181_router_decisions |  |
| source_block_fts | DERIVED | derived and rebuildable | `db/stores/source_block_fts.py:128` | `db/stores/source_block_fts.py:75` | substrate | content,db,instructional,ops,source_retrieval,substrate | replay:source_block_fts doctor | 177_source_block_fts |  |
| subject_identifiability_watermarks | DERIVED | derived and rebuildable | `db/repositories.py:6612` | `db/repositories.py:6597` | ops,substrate | ops | replay:identifiability doctor | 050_capability_residual_and_identifiability |  |

## Appendix C: definitions no production path reaches by name

715 top-level functions and methods, 11,972 lines. Reachability starts from decorated CLI, sidecar, mobile, MCP and TUI functions, and from module-level references everywhere, and follows names, so any same-named definition keeps a function alive. **A candidate list, not proof:** a name built at run time isn't seen. `tests` is how many test files name it. This is the wider list behind §7.4.

| definition | lines | tests |
|---|---:|---:|
| `adaptive_difficulty/denial_log.py:129` denial_count | 4 | 5 |
| `adaptive_difficulty/dose.py:317` offer_withheld | 4 | 0 |
| `adaptive_difficulty/history_forecast.py:541` expected_calls | 12 | 1 |
| `adaptive_difficulty/model.py:680` rating_probabilities | 5 | 1 |
| `adaptive_difficulty/model.py:732` dose_increment | 5 | 3 |
| `adaptive_difficulty/priors.py:293` features_complete | 4 | 0 |
| `adaptive_difficulty/priors.py:299` prior_demand | 5 | 1 |
| `adaptive_difficulty/protection.py:118` protected_items | 7 | 1 |
| `adaptive_difficulty/protection.py:127` is_protected | 2 | 0 |
| `adaptive_difficulty/readiness.py:357` card_line | 5 | 0 |
| `ai/chatgpt_plan/oauth.py:226` redact_authorization_url | 7 | 0 |
| `ai/execution.py:45` withhold_receipt_input | 16 | 0 |
| `ai/plan_fallback.py:375` start_collecting | 6 | 0 |
| `ai/plan_fallback.py:717` command_grant | 25 | 2 |
| `ai/plan_fallback.py:778` grant_origin | 5 | 9 |
| `ai/providers/chatgpt_plan.py:196` ChatGPTPlanProviderClient.workspace_record | 14 | 2 |
| `ai/providers/codex.py:2105` make_codex_client | 12 | 1 |
| `ai/providers/codex_lockdown.py:1272` clear_check_cache | 5 | 4 |
| `ai/providers/openai_chat.py:194` _DeadlineNetworkStream.start_tls | 4 | 1 |
| `ai/providers/openai_chat.py:218` _DeadlineNetworkBackend.connect_tcp | 5 | 1 |
| `ai/providers/openai_chat.py:224` _DeadlineNetworkBackend.connect_unix_socket | 4 | 1 |
| `ai/providers/voyage_contextual.py:52` _NoRedirect.redirect_request | 2 | 2 |
| `ai/routing.py:459` provider_for_operation | 17 | 0 |
| `ai/schemas.py:132` AnswerSpanTargetRef.validate_offsets | 10 | 0 |
| `ai/schemas.py:206` CandidateCause.validate_statement | 4 | 0 |
| `ai/strict_schema.py:124` map_typed_schema_paths | 42 | 1 |
| `attempts/ai_contracts.py:39` FirstDivergence.validate_offsets | 14 | 0 |
| `attempts/ai_contracts.py:61` FacetContrast.validate_contrast | 6 | 0 |
| `attempts/ai_contracts.py:88` RepairedTrace.validate_minimal_edit | 6 | 0 |
| `attempts/ai_contracts.py:147` ErrorAttribution.validate_abstention | 4 | 0 |
| `attempts/ai_contracts.py:188` RepairSuggestion.validate_eliciting | 22 | 0 |
| `attempts/ai_contracts.py:301` DiscriminationProfileMatch.validate_match | 4 | 0 |
| `attempts/attempts.py:5561` _evidence_coverage | 2 | 0 |
| `attempts/attempts.py:5565` _hint_dampening | 3 | 0 |
| `attempts/blind_grading.py:180` BlindRepairedTrace.validate_minimal_edit | 6 | 0 |
| `attempts/blind_grading.py:206` BlindErrorAttribution.validate_abstention | 4 | 0 |
| `attempts/calibration_streams.py:166` record_error_intake_sample | 24 | 1 |
| `attempts/grade_resolution.py:337` response_certainty_lcb | 68 | 2 |
| `attempts/grade_resolution.py:642` quarantine_observation | 58 | 3 |
| `attempts/grader_calibration.py:393` ResolvedModel.marginal_confusion | 12 | 1 |
| `attempts/grader_calibration.py:646` validate_promotion | 27 | 1 |
| `attempts/grader_calibration.py:680` denominator_counts_from_samples | 18 | 1 |
| `capture/inbox.py:387` report_orphan_originals | 10 | 1 |
| `cli/app.py:4040` eval_command | 13 | 0 |
| `cli/runtime.py:328` _fallback_provider_for_task | 3 | 0 |
| `config/compat.py:62` discard_retired_provider_settings | 8 | 0 |
| `config/compat.py:72` normalize_provider_profile | 11 | 0 |
| `config/compat.py:85` normalize_ai_input | 13 | 0 |
| `config/compat.py:211` ai_provider_from_codex | 30 | 1 |
| `config/schema.py:1009` AIProviderConfig._discard_auth_mode | 4 | 0 |
| `config/schema.py:1192` ChatGPTPlanProviderConfig._api_or_loopback | 17 | 0 |
| `config/schema.py:1542` AIRoutingConfig._drop_retired_routes | 5 | 0 |
| `config/schema.py:1549` AIRoutingConfig._default_embedding_route | 5 | 0 |
| `config/schema.py:1625` AIConfig._normalize_provider_profiles | 4 | 0 |
| `config/schema.py:1632` AIConfig._known_route_budgets | 6 | 0 |
| `config/schema.py:1641` AIConfig._merge_route_efforts | 5 | 0 |
| `config/schema.py:1649` AIConfig._known_route_efforts | 9 | 0 |
| `config/schema.py:1660` _require_known_routes | 5 | 0 |
| `config/schema.py:1923` EvidenceConfig._merge_defaults | 8 | 0 |
| `config/schema.py:2117` RecurrenceBlockingCutoff._a_cosine | 5 | 0 |
| `config/schema.py:2171` RecurrenceConfig._cutoffs_name_models | 5 | 0 |
| `config/schema.py:3201` NotesConfig._drop_legacy_tend | 5 | 0 |
| `config/schema.py:3950` PlanConfig._shares_leave_room | 8 | 0 |
| `config/schema.py:3993` IntentConfig._targets_are_probabilities | 11 | 0 |
| `config/schema.py:4029` RouterWeights.validate_total | 4 | 0 |
| `config/schema.py:4148` RouterConfig.validate_floor | 4 | 0 |
| `config/schema.py:4337` RouterObjectiveConfig._mins_leave_room | 11 | 0 |
| `config/schema.py:4813` AdaptiveDifficultyConfig._ordered_band | 5 | 0 |
| `config/schema.py:4821` AdaptiveDifficultyConfig._forecasters_switch | 7 | 0 |
| `config/schema.py:4831` AdaptiveDifficultyConfig._canonical_forecasters | 3 | 0 |
| `config/schema.py:4925` LearnLoopConfig._normalize_legacy_input | 6 | 0 |
| `config/schema.py:4933` LearnLoopConfig._ensure_effective_defaults | 87 | 0 |
| `config/schema.py:5030` default_codex_provider | 25 | 0 |
| `config/schema.py:5057` default_chatgpt_plan_provider | 11 | 0 |
| `config/schema.py:5070` deepseek_flash_provider | 10 | 0 |
| `config/schema.py:5082` deepseek_pro_provider | 11 | 0 |
| `config/schema.py:5095` openrouter_haiku_provider | 9 | 0 |
| `config/schema.py:5117` openrouter_embedding_provider | 14 | 0 |
| `config/schema.py:5133` openrouter_decider_provider | 10 | 2 |
| `config/template.py:4160` effective_defaults_fingerprint | 20 | 11 |
| `config/template.py:4182` defaults_fingerprint_for_version | 11 | 48 |
| `content/authoring/authoring_gates.py:117` chain_gates | 8 | 0 |
| `content/authoring/conjunctive_items.py:214` partition_supporting_targets | 36 | 1 |
| `content/authoring/exercise_authoring.py:173` _anchor_statement | 6 | 0 |
| `content/authoring/laddered_stems.py:109` stem_column_for_item | 14 | 1 |
| `content/authoring/laddered_stems.py:125` stem_columns_for_surfaces | 24 | 0 |
| `content/authoring/practice_generation.py:1169` _blueprint_shaping | 25 | 0 |
| `content/authoring/practice_generation.py:1196` _cross_source_difficulty_lines | 19 | 0 |
| `content/authoring/practice_generation.py:1217` _cross_source_instructions | 54 | 0 |
| `content/authoring/practice_generation.py:1273` generate_cross_source_practice_proposal | 132 | 2 |
| `content/authoring/source_exercise_import.py:666` record_key_check | 9 | 0 |
| `content/facet_identity/actions.py:1290` registry_save_by_id | 3 | 1 |
| `content/facet_identity/views.py:174` comparable_entry | 12 | 0 |
| `content/pipeline/add_source.py:1307` built_unit_ids | 5 | 1 |
| `content/pipeline/add_source.py:1318` _source_work_active | 2 | 2 |
| `content/pipeline/add_source.py:2002` advance_reading_build | 15 | 3 |
| `content/pipeline/jobs.py:2949` _not_implemented_handler | 7 | 0 |
| `content/pipeline/jobs.py:4459` DurableIngestJobs.retry_reading_advances | 6 | 3 |
| `content/pipeline/jobs.py:4487` DurableIngestJobs._reading_sweep_loop | 12 | 2 |
| `content/pipeline/reread.py:146` has_completed_reading | 3 | 0 |
| `content/pipeline/source_ingestion.py:669` detect_source_kind | 7 | 2 |
| `content/pipeline/source_ingestion.py:1476` _HTMLMarkdownParser.handle_starttag | 32 | 0 |
| `content/pipeline/source_ingestion.py:1509` _HTMLMarkdownParser.handle_endtag | 20 | 0 |
| `content/pipeline/source_ingestion.py:1530` _HTMLMarkdownParser.handle_data | 11 | 0 |
| `content/proposals/ai_contracts.py:284` RubricPatchPayload.derive_max_points_from_criteria | 9 | 0 |
| `content/proposals/ai_contracts.py:339` TraceContractPayload.validate_trace_contract | 25 | 0 |
| `content/proposals/ai_contracts.py:735` AuthoringProposalItem.coerce_payload_by_item_type | 26 | 0 |
| `content/proposals/ai_contracts.py:763` AuthoringProposalItem.validate_target_rules | 10 | 0 |
| `content/proposals/proposals.py:353` diagnostic_target_from_need | 16 | 0 |
| `content/proposals/proposals.py:412` diagnostic_review_warnings | 15 | 1 |
| `content/proposals/proposals.py:604` build_diagnostic_authoring_context | 65 | 0 |
| `content/proposals/proposals.py:671` _diagnostic_proposal_item_row | 37 | 0 |
| `content/proposals/proposals.py:710` _gate_target_record | 15 | 0 |
| `content/proposals/proposals.py:727` _reopen_need_after_gate_failure | 24 | 0 |
| `content/proposals/proposals.py:753` generate_diagnostic_proposal | 121 | 2 |
| `content/proposals/proposals.py:1300` repair_proposal_item_audit | 45 | 0 |
| `content/sources/role_authority.py:207` can_authorize_assessment | 4 | 0 |
| `content/sources/source_library.py:147` index_legacy_note | 28 | 0 |
| `content/synthesis/ai_contracts.py:47` InventoryProcedureSignal.coerce_span_ids | 18 | 0 |
| `content/synthesis/append_neighborhood.py:149` _NewSignals.all_name_tokens | 5 | 0 |
| `content/synthesis/exam_profile.py:181` profile_hash | 7 | 2 |
| `content/synthesis/source_unit_inventory.py:266` _unit_heading | 7 | 0 |
| `content/synthesis/source_unit_selection.py:345` default_exam_use_modes | 8 | 1 |
| `content/synthesis/source_unit_selection.py:482` reanchor_selection | 27 | 1 |
| `content/synthesis/source_unit_selection.py:511` reanchor_selection_to | 56 | 0 |
| `content/synthesis/synthesis_gates.py:182` GateReport.gates_fired | 2 | 0 |
| `curriculum/commitment_arcs.py:199` advance_arc | 90 | 2 |
| `curriculum/commitment_arcs.py:308` resume_arc | 7 | 0 |
| `curriculum/commitments.py:496` remove_target | 26 | 1 |
| `curriculum/commitments.py:773` record_depth_transition_committed | 20 | 0 |
| `curriculum/commitments.py:795` attach_family | 8 | 0 |
| `curriculum/commitments.py:805` detach_family | 8 | 0 |
| `curriculum/commitments.py:858` load_commitment | 2 | 1 |
| `curriculum/depth_edge_authoring.py:100` append_template_version | 20 | 0 |
| `curriculum/golden_path_fixture.py:137` stub_diagnostic_pack | 12 | 1 |
| `curriculum/golden_path_fixture.py:151` stub_pool_surfaces | 11 | 1 |
| `curriculum/golden_path_run.py:162` next_feasible_action | 4 | 0 |
| `curriculum/golden_path_run.py:350` advance_canonical | 18 | 1 |
| `curriculum/task_blueprints.py:141` discover_exemplar_candidates | 27 | 0 |
| `curriculum/task_blueprints.py:232` activate_blueprint_version | 25 | 1 |
| `daily_plan/engine.py:960` unregister_plan_decision_logger | 3 | 2 |
| `daily_plan/lanes.py:101` register_scheduled_check_provider | 3 | 4 |
| `daily_plan/lanes.py:106` unregister_scheduled_check_provider | 3 | 4 |
| `daily_plan/records.py:505` day_items | 2 | 0 |
| `daily_plan/view.py:366` now_payload | 2 | 0 |
| `data_capture/prefilter.py:346` admission_probability | 10 | 2 |
| `data_capture/reading_exposures.py:119` _clear_mapping_cache | 4 | 1 |
| `db/migrate.py:95` upgrade_authority | 4 | 1 |
| `db/repositories.py:1449` Repository.insert_practice_attempt | 4 | 16 |
| `db/repositories.py:1846` Repository.insert_grading_evidence | 5 | 5 |
| `db/repositories.py:2212` Repository.supersede_self_grade_rows | 19 | 2 |
| `db/repositories.py:2302` Repository.record_deferred_regrade | 70 | 1 |
| `db/repositories.py:2780` Repository.active_misconception_facet_ids | 22 | 0 |
| `db/repositories.py:3470` Repository.discrimination_rows_for_item | 9 | 1 |
| `db/repositories.py:3480` Repository.discrimination_rows_for_misconceptions | 16 | 1 |
| `db/repositories.py:3577` Repository.insert_attempt_surprise | 4 | 1 |
| `db/repositories.py:3736` Repository.create_remediation_episode | 25 | 3 |
| `db/repositories.py:4127` Repository.cold_measurement_opportunity_decision | 16 | 3 |
| `db/repositories.py:4977` Repository.total_reveal_amount | 68 | 1 |
| `db/repositories.py:6578` Repository.capability_residual_states | 6 | 2 |
| `db/repositories.py:6759` Repository.upsert_facet_uncertainty_state | 4 | 4 |
| `db/repositories.py:6927` Repository.learning_outcome_labels_for_source | 11 | 1 |
| `db/repositories.py:7103` Repository.parameter_registry_manifest | 7 | 1 |
| `db/repositories.py:7404` Repository.upsert_item_parameter_state | 4 | 0 |
| `db/repositories.py:7583` Repository.update_intervention_need_diagnostic_focus | 25 | 0 |
| `db/repositories.py:7693` Repository.probe_states | 11 | 0 |
| `db/repositories.py:7713` Repository.upsert_probe_state | 53 | 3 |
| `db/repositories.py:8434` Repository.retire_probe_family_template | 8 | 0 |
| `db/repositories.py:9379` Repository.state_beliefs | 26 | 1 |
| `db/repositories.py:9804` Repository.latest_scheduler_explanations_by_session | 11 | 1 |
| `db/repositories.py:9967` Repository.daily_attempt_counts | 32 | 1 |
| `db/repositories.py:10257` Repository.grading_correction_count_between | 27 | 0 |
| `db/repositories.py:12206` Repository.write_administration_lineage_atomic | 186 | 0 |
| `db/repositories.py:12683` Repository.goal_contract_drafts_for_goal | 7 | 1 |
| `db/repositories.py:12927` Repository.latest_render_view_for_extraction | 8 | 0 |
| `db/repositories.py:13463` Repository.pending_capture_outbox | 8 | 1 |
| `db/repositories.py:13485` Repository.get_capture_outbox | 6 | 3 |
| `db/repositories.py:13980` Repository.selection_reader_authored_questions | 12 | 0 |
| `db/repositories.py:13993` Repository.inquiry_reader_authored_questions | 12 | 0 |
| `db/repositories.py:14436` Repository.relations_for_object | 8 | 1 |
| `db/repositories.py:14689` Repository.arcs_for_source | 7 | 0 |
| `db/repositories.py:14732` Repository.measurement_events_for_administration | 15 | 1 |
| `db/repositories.py:14956` Repository.fetch_calibration_model | 6 | 0 |
| `db/repositories.py:15400` Repository.fetch_surface_by_hash | 12 | 0 |
| `db/repositories.py:15455` Repository.retirement_records_for_surface | 7 | 1 |
| `db/repositories.py:15463` Repository.retirement_records_for_card_version | 12 | 1 |
| `db/repositories.py:15654` Repository.interaction_events_for_attempt | 7 | 2 |
| `db/repositories.py:16202` Repository.retire_causal_mechanism_taxonomy_version | 28 | 1 |
| `db/repositories.py:17231` Repository.coldness_receipts_for_task | 13 | 1 |
| `db/repositories.py:17245` Repository.coldness_receipt_for_verification | 9 | 1 |
| `db/repositories.py:18300` Repository.update_proposal_item_audit | 29 | 0 |
| `db/repositories.py:19923` Repository.due_reading_requests | 8 | 2 |
| `db/repositories.py:20462` Repository.insert_span_reanchor | 31 | 2 |
| `db/repositories.py:20494` Repository.span_reanchors_from | 7 | 1 |
| `db/repositories.py:20557` Repository.backfill_locator_schemes | 27 | 1 |
| `db/repositories.py:20670` Repository.unit_selections_for_revision | 7 | 0 |
| `db/repositories.py:20771` Repository.held_out_signal_marks | 10 | 2 |
| `db/repositories.py:20825` Repository.get_unit_inventory | 6 | 1 |
| `db/repositories.py:20881` Repository.upsert_exam_profile | 24 | 1 |
| `db/repositories.py:20906` Repository.get_exam_profile | 13 | 1 |
| `db/repositories.py:21350` Repository.live_maintenance_notice_keys | 6 | 0 |
| `db/repositories.py:21734` Repository.mark_apply_intent_rolled_back | 7 | 0 |
| `db/repositories.py:21742` Repository.apply_intent | 6 | 0 |
| `db/repositories.py:22775` Repository.ensure_activity_pattern | 14 | 0 |
| `db/repositories.py:22790` Repository.ensure_activity_pattern_version | 74 | 0 |
| `db/repositories.py:22865` Repository.set_activity_pattern_version_status | 9 | 0 |
| `db/repositories.py:22923` Repository.ensure_progression_policy_version | 27 | 0 |
| `db/repositories.py:22951` Repository.progression_policy_version | 6 | 0 |
| `db/repositories.py:22958` Repository.upsert_activity_family_authoring | 49 | 0 |
| `db/repositories.py:23008` Repository.set_activity_family_authoring_status | 9 | 0 |
| `db/repositories.py:23026` Repository.upsert_activity_card_authoring | 42 | 0 |
| `db/repositories.py:23077` Repository.activity_card_authoring_for_family | 7 | 0 |
| `db/repositories.py:23085` Repository.activity_family_authoring_purposes | 15 | 0 |
| `db/repositories.py:23101` Repository.activity_family_version_family_id | 6 | 0 |
| `db/repositories.py:23129` Repository.card_lineage | 6 | 6 |
| `db/repositories.py:23179` Repository.lineage_for_card_version | 13 | 1 |
| `db/repositories.py:23282` Repository.activity_administration | 6 | 1 |
| `db/repositories.py:23289` Repository.all_activity_administrations | 10 | 0 |
| `db/repositories.py:23397` Repository.upsert_soft_kinship_features | 36 | 1 |
| `db/repositories.py:23456` Repository.upsert_activity_surface_authoring | 49 | 1 |
| `db/repositories.py:23602` Repository.surface_mint_requests_for_card_version | 20 | 1 |
| `db/repositories.py:23623` Repository.claim_next_surface_mint_request | 65 | 0 |
| `db/repositories.py:23740` Repository.set_surface_mint_candidate | 37 | 0 |
| `db/repositories.py:23851` Repository.insert_angle_inventory | 22 | 1 |
| `db/repositories.py:23874` Repository.angle_inventories_for_family | 7 | 0 |
| `db/repositories.py:23882` Repository.ensure_family_evidence_cap_policy | 28 | 0 |
| `db/repositories.py:23911` Repository.family_evidence_cap_policy | 6 | 1 |
| `db/repositories.py:23918` Repository.open_lapse_episode | 26 | 2 |
| `db/repositories.py:23978` Repository.lapse_episodes_for_lineage | 15 | 0 |
| `db/repositories.py:24188` Repository.task_blueprint_versions_for | 7 | 1 |
| `db/repositories.py:24204` Repository.task_blueprint_review_events_for | 7 | 1 |
| `db/repositories.py:24544` Repository.golden_path_run_by_receipt | 6 | 0 |
| `db/repositories.py:24813` Repository.diagnostic_pack_by_slug | 6 | 0 |
| `db/repositories.py:24836` Repository.diagnostic_pack_events_for | 7 | 1 |
| `db/repositories.py:25297` Repository.practice_pool_by_slug | 6 | 0 |
| `db/repositories.py:25418` Repository.golden_path_artifacts_for | 15 | 4 |
| `db/repositories.py:26120` Repository.diagnosis_adjudications_for_attempt | 15 | 1 |
| `db/repositories.py:26446` Repository.error_hunt_outcome | 7 | 1 |
| `db/repositories.py:27884` _decode_exam_profile | 4 | 0 |
| `db/stores/ad_receipts.py:121` reading_opportunity_exists | 12 | 0 |
| `db/stores/ad_receipts.py:135` source_recorded | 8 | 0 |
| `db/stores/ad_receipts.py:180` latest_source_written_at | 5 | 0 |
| `db/stores/ad_serving.py:449` read_state | 8 | 1 |
| `db/stores/ad_serving.py:459` read_trace | 9 | 0 |
| `db/stores/ad_serving.py:470` read_scores | 7 | 0 |
| `db/stores/approach_maps.py:61` latest_map | 8 | 1 |
| `db/stores/approach_maps.py:114` map_exists | 7 | 2 |
| `db/stores/deliverables.py:71` goals_with_inputs | 3 | 0 |
| `db/stores/diagnoses.py:682` DiagnosisStoreMixin.post_attempt_job | 6 | 0 |
| `db/stores/facet_identity.py:222` registry_save_by_id | 3 | 1 |
| `db/stores/families.py:103` current_memberships | 7 | 1 |
| `db/stores/followup_serve.py:363` bindings_for_decision | 5 | 2 |
| `db/stores/followup_value.py:59` decisions_for_attempt | 10 | 0 |
| `db/stores/help_assists.py:516` workbench_window_ids | 4 | 0 |
| `db/stores/hypothesis_marks.py:140` exposures_for_attempt | 3 | 0 |
| `db/stores/ingest_queue.py:363` IngestQueueStoreMixin.ingest_job_dependents | 10 | 1 |
| `db/stores/ingest_queue.py:651` IngestQueueStoreMixin.delete_finished_ingest_batches | 50 | 2 |
| `db/stores/intent_reads.py:154` surprise_factors | 14 | 0 |
| `db/stores/learner_notes.py:76` latest_note | 4 | 0 |
| `db/stores/learner_notes.py:82` latest_notes | 13 | 0 |
| `db/stores/learner_notes.py:165` note_count | 2 | 0 |
| `db/stores/learner_notes.py:219` ai_rows_for_state | 4 | 0 |
| `db/stores/plan_presentations.py:120` presentations_for_controller_decision | 14 | 0 |
| `db/stores/practice_index.py:101` dossier_count | 4 | 0 |
| `db/stores/reader_cue_links.py:79` link_by_id | 4 | 0 |
| `db/stores/reader_digests.py:143` session_keys | 4 | 0 |
| `db/stores/router.py:333` router_outcome_rows | 3 | 0 |
| `db/stores/router_suggestions.py:160` response_for_lesson | 5 | 0 |
| `db/stores/source_block_fts.py:532` indexed_block_count | 8 | 0 |
| `db/stores/write_provenance.py:780` retired_error_event_ids | 14 | 1 |
| `db/stores/write_provenance.py:796` current_error_event_ids | 25 | 1 |
| `db/table_roles.py:763` registry_mismatch | 9 | 1 |
| `db/table_roles.py:774` assert_complete_registry | 12 | 1 |
| `diagnosis/causal_activity_policy.py:309` resolve_conflicting_classes | 14 | 1 |
| `diagnosis/causal_attribution.py:1580` hypothesis_mechanism_projection | 25 | 1 |
| `diagnosis/causal_migration.py:42` migrate_legacy_causal_basis | 80 | 1 |
| `diagnosis/causal_probe_coherence.py:337` parse_bundle_feature_rows | 6 | 1 |
| `diagnosis/causal_probe_coherence.py:571` rung_divergence_gate | 77 | 2 |
| `diagnosis/causal_probe_commissioning.py:762` sweep_probe_commissioning | 33 | 1 |
| `diagnosis/contrast_pairs.py:276` ContrastPairCommissionPlan.for_subject | 4 | 0 |
| `diagnosis/diagnostic_pack.py:184` reject_pack_card | 18 | 0 |
| `diagnosis/diagnostic_pack.py:228` activate_pack | 17 | 0 |
| `diagnosis/failure_triage.py:409` _decisive_reason | 18 | 1 |
| `diagnosis/followups.py:546` evaluate_negative_surprise_followup | 38 | 2 |
| `diagnosis/misconceptions.py:354` _surface_family_for_attempt | 9 | 0 |
| `diagnosis/offline_review/report.py:226` _passes | 5 | 1 |
| `diagnosis/probe_episodes.py:1664` plan_precommitted_block | 151 | 2 |
| `diagnosis/probe_episodes.py:3549` abandon_episode | 19 | 1 |
| `diagnosis/probe_instance_generation.py:1398` approve_probe_instance | 32 | 1 |
| `diagnosis/probe_lifecycle.py:263` retire_probe_instance | 26 | 2 |
| `diagnosis/probe_targeting.py:112` prerequisite_already_demonstrated | 9 | 0 |
| `diagnosis/probe_targeting.py:123` should_suppress_prerequisite_probe | 8 | 1 |
| `diagnosis/probe_targeting.py:451` repair_mapping_backfills | 26 | 2 |
| `diagnosis/probe_targeting.py:712` next_cause_set_instrument | 24 | 0 |
| `diagnosis/probe_targeting.py:741` integration_condition_target | 18 | 1 |
| `diagnosis/probe_targeting.py:764` probe_priority | 123 | 2 |
| `diagnosis/probes.py:40` parse_misconception_label | 14 | 1 |
| `diagnosis/probes.py:267` enter_probe | 45 | 7 |
| `diagnosis/probes.py:920` probe_eig_component | 16 | 1 |
| `diagnosis/probes.py:1331` current_hypothesis_set | 23 | 1 |
| `diagnosis/probes.py:1356` persist_probe_beliefs | 39 | 1 |
| `diagnosis/probes.py:1397` record_probe_attempt | 59 | 3 |
| `diagnosis/quick_check.py:175` is_quick_check | 2 | 0 |
| `diagnosis/recurrence/benchmarks.py:525` MisconceptionHypothesis._not_blank | 13 | 0 |
| `diagnosis/recurrence/benchmarks.py:1159` register_suites | 14 | 8 |
| `diagnosis/recurrence/benchmarks.py:1178` run_bench | 77 | 2 |
| `diagnosis/recurrence/benchmarks.py:1257` plan_admission | 67 | 0 |
| `diagnosis/recurrence/escalation.py:68` EscalatedRepair._eliciting_needs_a_question | 4 | 0 |
| `diagnosis/remediation_intake.py:13` classify_intake | 22 | 1 |
| `diagnosis/split/context.py:979` stable_prefix | 6 | 1 |
| `diagnosis/split/context.py:987` cacheable_prefix | 15 | 1 |
| `diagnosis/split/context.py:1004` facets_overlap | 2 | 0 |
| `diagnosis/split/contract.py:115` DiagnosisRepairSuggestion.validate_eliciting | 8 | 0 |
| `diagnosis/split/history.py:240` HistoryAttempt.failure_facets | 4 | 0 |
| `diagnosis/split/history.py:729` VaultHistoryStore.with_blind_grades | 7 | 1 |
| `diagnosis/split/history.py:1341` StaticHistoryStore.replace_attempt | 5 | 1 |
| `diagnosis/split/history.py:1408` with_blind_overlay | 2 | 0 |
| `diagnosis/split/jobs.py:237` pending_diagnosis_attempts | 7 | 0 |
| `diagnosis/split/live.py:456` diagnosis_for_attempt | 26 | 2 |
| `diagnosis/split/live.py:484` grader_mode_for | 2 | 0 |
| `diagnosis/split/settings.py:60` DiagnosisSettings.with_mode | 2 | 0 |
| `diagnosis/voi_stopping.py:2416` followup_receipts | 14 | 3 |
| `diagnosis/voi_stopping.py:2432` followup_receipt | 8 | 2 |
| `evsi_calibration/eedi.py:332` option_index | 2 | 0 |
| `evsi_calibration/families.py:774` NrmFamily.holder_rates | 2 | 0 |
| `evsi_calibration/metrics.py:277` quantile_names | 2 | 0 |
| `experiments/contextual_embeddings/adapters.py:219` NoRedirect.redirect_request | 2 | 2 |
| `experiments/contextual_embeddings/adapters.py:472` VectorStore.get_raw | 3 | 1 |
| `experiments/contextual_embeddings/anthropic_api.py:118` extract_json | 11 | 0 |
| `experiments/contextual_embeddings/bank.py:1075` reference_dependencies | 11 | 0 |
| `experiments/contextual_embeddings/corpus.py:880` CorpusSnapshot.unit_dependency | 4 | 2 |
| `experiments/contextual_embeddings/corpus.py:885` CorpusSnapshot.window_dependency | 7 | 1 |
| `experiments/contextual_embeddings/credentials.py:34` load_env_file | 11 | 1 |
| `experiments/contextual_embeddings/delivery.py:267` retrieved_d0 | 18 | 1 |
| `experiments/contextual_embeddings/e1/run.py:62` LayeredVectorStore.get_raw | 2 | 1 |
| `experiments/contextual_embeddings/e1/worker.py:164` disk_free_bytes | 3 | 0 |
| `experiments/contextual_embeddings/plan.py:370` embedding_documents | 9 | 0 |
| `field/answer_signals.py:326` AnswerSignalArm.snapshot_bytes | 6 | 4 |
| `field/predictors.py:355` LoGeneral.snapshot_bytes | 10 | 4 |
| `field/predictors.py:453` BetaPredictor.snapshot_bytes | 2 | 4 |
| `field/predictors.py:504` is_calibrated_predictor | 7 | 3 |
| `field/predictors.py:513` validate_active_predictor | 5 | 4 |
| `field/probability_arms.py:49` all_arm_names | 5 | 1 |
| `field/signals.py:612` confusion_blocks_fast_track | 13 | 4 |
| `figures/elements.py:109` schema_label_fields | 27 | 1 |
| `figures/power.py:121` reset_probe_cache | 5 | 1 |
| `figures/power.py:230` set_power_reader | 6 | 9 |
| `figures/rich.py:196` rich_on_menu | 2 | 0 |
| `figures/rich.py:1131` payload_digest | 2 | 0 |
| `figures/sketch_engine.py:121` artifact_digest | 2 | 1 |
| `figures/spec.py:360` CompiledFigure.shade_labels | 2 | 0 |
| `followup_serve/gates.py:46` effective_auto_generate_on_entry | 9 | 2 |
| `followup_serve/identity.py:312` replay_inactive_ids | 4 | 0 |
| `goals/goal_contracts.py:408` confirm_goal_contract | 65 | 3 |
| `goals/goal_contracts.py:475` _with_use_weight | 20 | 1 |
| `goals/goal_lo.py:156` undo_goal_lo | 19 | 1 |
| `goals/receipt_contributions.py:109` cap_observation_contributions | 23 | 0 |
| `hints/map_builder.py:975` build_map_inline | 11 | 1 |
| `hints/map_builder.py:1114` BackgroundBuilds.track | 3 | 29 |
| `hints/map_builder.py:1296` wait_for_background_builds | 10 | 5 |
| `hints/outcome.py:569` unplaced_attempts | 7 | 4 |
| `hints/writer.py:373` empty_output | 16 | 5 |
| `ingest/detect.py:6` detect_source_kind | 8 | 2 |
| `ingest/extractors/base.py:54` assign_span_semantic_hash | 4 | 0 |
| `ingest/extractors/glm_ocr.py:232` _NoRedirect.redirect_request | 3 | 2 |
| `ingest/extractors/glm_ocr.py:1258` _TableParser.handle_starttag | 18 | 0 |
| `ingest/extractors/glm_ocr.py:1277` _TableParser.handle_data | 3 | 0 |
| `ingest/extractors/glm_ocr.py:1281` _TableParser.handle_endtag | 4 | 0 |
| `ingest/extractors/glm_text_layer.py:168` read_text_layer | 19 | 0 |
| `ingest/extractors/glm_text_layer.py:240` _worker_main | 46 | 0 |
| `ingest/extractors/marker_worker.py:276` _worker_main | 28 | 0 |
| `ingest/extractors/marker_worker.py:306` _read_request | 14 | 0 |
| `ingest/extractors/marker_worker.py:322` _exit_with_parent | 17 | 0 |
| `ingest/extractors/marker_worker.py:341` _orphaned | 23 | 0 |
| `ingest/extractors/marker_worker.py:366` _contain_descendants | 13 | 0 |
| `ingest/extractors/marker_worker.py:381` _job_limit_information | 38 | 1 |
| `ingest/extractors/marker_worker.py:421` _assign_to_kill_on_close_job | 26 | 0 |
| `ingest/hashing.py:179` block_type_histogram | 2 | 0 |
| `instructional/interventions.py:321` record_offer_shown | 7 | 1 |
| `instructional/policy.py:161` check_named_ids | 8 | 0 |
| `instructional/practice.py:294` record_proposal_pick | 12 | 2 |
| `instructional/reader_followups.py:1871` now_utc | 2 | 0 |
| `instructional/valuation.py:1163` refuse_mixed_decision | 6 | 1 |
| `learner/capability_mapping.py:321` group_proliferation_flag | 18 | 1 |
| `learner/facet_evidence_timeline.py:1016` _observation_events | 14 | 2 |
| `learner/familiarity.py:133` record_soft_features | 15 | 5 |
| `learner/familiarity.py:359` _pairwise_warmth | 21 | 0 |
| `learner/familiarity.py:386` _stem_edge | 15 | 0 |
| `learner/familiarity.py:403` tight_kinship_clusters | 82 | 3 |
| `learner/familiarity.py:499` evidence_cap_grouping | 29 | 1 |
| `learner/lesson_weight.py:1014` mass_mismatches | 14 | 1 |
| `learner/recall_coverage.py:435` event_local_severity | 37 | 0 |
| `learner/recall_coverage.py:550` build_facet_recall_updates | 31 | 0 |
| `learner/recall_coverage.py:636` build_quality_state_update | 31 | 0 |
| `local_embeddings/worker.py:158` disk_free_bytes | 3 | 0 |
| `ops/settings_store.py:130` remove_config_paths | 48 | 1 |
| `params/sensitivity_certificates.py:253` promotion_evidence_from_sweep_report | 20 | 1 |
| `params/sensitivity_certificates.py:372` classify_inert_parameters | 23 | 1 |
| `placement/signals.py:97` taught_first_learning_objects | 11 | 2 |
| `practice_index/tool.py:48` run_find_practice_tool | 5 | 1 |
| `projects/ai_runtime.py:189` set_route_resolver | 3 | 0 |
| `projects/experiment_store.py:726` ProjectStore.response_for_probe | 6 | 1 |
| `reader/annotations.py:545` reanchor_annotations_for_source | 32 | 2 |
| `reader/reader_authoring.py:415` mint_ai_sibling | 40 | 2 |
| `reader/reader_authoring.py:498` record_coach_response | 27 | 1 |
| `reader/reader_capture.py:456` retry_outbox | 9 | 2 |
| `reader/reader_cues.py:129` step_down | 5 | 1 |
| `reader/reader_restoration.py:151` restore_before_response | 28 | 1 |
| `reader/source_roles.py:135` tolerate_roles | 9 | 0 |
| `reader/source_roles.py:151` tolerate_malformed_roles | 19 | 0 |
| `reader/source_roles.py:177` TolerantRoles._tolerate_roles | 2 | 0 |
| `reader/workbench.py:789` record_draft_handoff | 15 | 1 |
| `recurrence.py:60` is_group_key | 2 | 1 |
| `router_objective/price.py:230` choice_log_likelihood | 12 | 0 |
| `router_objective/price.py:244` grid_posterior | 14 | 1 |
| `router_objective/tail_data.py:919` is_finite | 2 | 0 |
| `router_objective/value.py:427` cutoff_for | 2 | 1 |
| `router_objective_switches.py:174` sensors_in_value_on | 5 | 1 |
| `scheduling/action_loss.py:162` LossTable.argmin_action_set | 7 | 1 |
| `scheduling/action_loss.py:379` raw_cell | 6 | 1 |
| `scheduling/controller_actions.py:61` is_action | 2 | 0 |
| `scheduling/controller_cutover.py:425` cross_seam_exposure_probe | 41 | 2 |
| `scheduling/controller_cutover.py:504` _gate_shadow_parity | 13 | 0 |
| `scheduling/controller_cutover.py:519` _gate_ownership_assignment | 12 | 0 |
| `scheduling/controller_cutover.py:533` _gate_staged_live | 25 | 0 |
| `scheduling/controller_cutover.py:560` _gate_affect_one_edge | 23 | 0 |
| `scheduling/controller_cutover.py:585` _gate_rollback | 12 | 0 |
| `scheduling/controller_cutover.py:599` run_cutover_gates | 55 | 2 |
| `scheduling/controller_ownership.py:73` is_p2_golden_path_commitment | 14 | 0 |
| `scheduling/controller_ownership.py:102` rebuild_ownership_head | 55 | 1 |
| `scheduling/controller_ownership.py:170` ownership_events | 8 | 1 |
| `scheduling/controller_ownership.py:271` assign_p2_run | 28 | 5 |
| `scheduling/controller_ownership.py:342` _commitment_refs | 12 | 0 |
| `scheduling/controller_store.py:104` upsert_constraint_manifest | 22 | 0 |
| `scheduling/controller_store.py:311` candidates_for_decision | 10 | 1 |
| `scheduling/controller_store.py:354` shadow_predictions_for_decision | 10 | 1 |
| `scheduling/controller_store.py:412` assignment_row | 6 | 0 |
| `scheduling/controller_store.py:420` assignments_for_experiment | 10 | 1 |
| `scheduling/controller_store.py:437` open_outcome_window | 30 | 2 |
| `scheduling/controller_store.py:469` resolve_outcome_window | 15 | 2 |
| `scheduling/controller_store.py:486` outcome_window_row | 6 | 1 |
| `scheduling/controller_store.py:494` outcome_windows_for_decision | 10 | 0 |
| `scheduling/controller_store.py:506` pending_outcome_windows | 7 | 0 |
| `scheduling/evsi.py:512` joint_conditionals | 20 | 1 |
| `scheduling/family_memory_model.py:107` FamilyMemory.snapshot_bytes | 6 | 4 |
| `scheduling/intent/resolution.py:303` Resolution.committed_item_ids | 2 | 0 |
| `scheduling/intent/resolution.py:317` intent_control_commitments | 2 | 0 |
| `scheduling/intent/resolution.py:321` rechosen | 4 | 0 |
| `scheduling/intent/serving.py:319` IntentServing.is_check_candidate | 3 | 1 |
| `scheduling/kinship_feature.py:123` _default_judge | 30 | 0 |
| `scheduling/kinship_feature.py:155` _features_for | 5 | 0 |
| `scheduling/kinship_feature.py:162` _hard_colliding | 16 | 0 |
| `scheduling/kinship_feature.py:185` ensure_model | 42 | 1 |
| `scheduling/kinship_feature.py:229` familiarity_kernel_content_hash | 7 | 0 |
| `scheduling/kinship_feature.py:256` score_kinship | 80 | 1 |
| `scheduling/kinship_feature.py:338` _cache_feature | 15 | 0 |
| `scheduling/kinship_feature.py:355` cached_feature | 14 | 0 |
| `scheduling/kinship_feature.py:389` consulted_discount | 33 | 1 |
| `scheduling/kinship_feature.py:439` run_admission_gate | 68 | 2 |
| `scheduling/kinship_feature.py:509` _append_kernel_event | 18 | 0 |
| `scheduling/predictive_targets.py:57` TargetSet.weight_of | 5 | 1 |
| `scheduling/predictive_targets.py:78` _matches_candidate | 4 | 0 |
| `scheduling/predictive_targets.py:84` build_target_set | 64 | 1 |
| `scheduling/predictive_targets.py:150` build_from_contract_version | 16 | 0 |
| `scheduling/prequential.py:90` _effective_sample | 5 | 0 |
| `scheduling/prequential.py:97` _metrics_body | 9 | 0 |
| `scheduling/prequential.py:113` _resolved_outcomes_by_decision | 10 | 0 |
| `scheduling/prequential.py:125` _component_predictions | 8 | 0 |
| `scheduling/prequential.py:135` _time_bucket | 7 | 0 |
| `scheduling/prequential.py:144` _pairs_for | 28 | 0 |
| `scheduling/prequential.py:174` _splits_body | 9 | 0 |
| `scheduling/prequential.py:185` component_report | 25 | 1 |
| `scheduling/prequential.py:212` composed_selector_report | 23 | 1 |
| `scheduling/prequential.py:237` _persist_report | 30 | 0 |
| `scheduling/prequential.py:269` reports_for | 8 | 1 |
| `scheduling/progression.py:77` _next_context | 9 | 0 |
| `scheduling/progression.py:88` _orthogonal_angle | 22 | 0 |
| `scheduling/progression.py:112` next_growth_activity | 43 | 1 |
| `scheduling/progression.py:161` default_cap_body | 8 | 0 |
| `scheduling/progression.py:171` ensure_default_evidence_cap_policy | 8 | 1 |
| `scheduling/progression.py:199` apply_evidence_cap | 58 | 2 |
| `scheduling/progression.py:263` _plus_days | 3 | 0 |
| `scheduling/progression.py:268` open_lapse_episode | 22 | 2 |
| `scheduling/progression.py:292` link_retry | 27 | 2 |
| `scheduling/progression.py:321` give_up | 10 | 1 |
| `scheduling/progression_policy.py:48` default_progression_policy_body | 16 | 0 |
| `scheduling/progression_policy.py:66` register_progression_policy | 18 | 0 |
| `scheduling/progression_policy.py:86` ensure_default_progression_policy | 9 | 2 |
| `scheduling/progression_policy.py:97` load_progression_policy | 7 | 0 |
| `scheduling/randomization_layer.py:239` micro_randomize | 39 | 1 |
| `scheduling/randomization_layer.py:280` commitment_parallel_assign | 36 | 1 |
| `scheduling/randomization_layer.py:351` open_outcome_window | 25 | 2 |
| `scheduling/reentry_adapter.py:125` classify_cells | 58 | 1 |
| `scheduling/reentry_adapter.py:185` _pinned_target | 16 | 0 |
| `scheduling/reentry_adapter.py:203` _goal_conditioned_priority | 9 | 0 |
| `scheduling/reentry_adapter.py:214` plan_reentry | 74 | 1 |
| `scheduling/shadow_components.py:71` ComponentPredictions.as_map | 6 | 0 |
| `scheduling/shadow_components.py:79` predict_components | 20 | 1 |
| `scheduling/shadow_components.py:101` record_shadow_predictions | 28 | 1 |
| `scheduling/shadow_components.py:146` promote_component | 58 | 1 |
| `scheduling/shadow_components.py:206` _margin_value_hash | 4 | 0 |
| `scheduling/shadow_components.py:212` promote_action_chooser | 8 | 1 |
| `scheduling/shadow_components.py:222` _append_component_event | 18 | 0 |
| `scheduling/shadow_components.py:242` component_events | 8 | 1 |
| `scheduling/shadow_components.py:257` open_composed_selector_horizon | 26 | 1 |
| `scheduling/short_session.py:70` plan_short_session | 48 | 1 |
| `sim/grader_confusion.py:76` load_confusion | 4 | 1 |
| `sim/grader_confusion.py:160` _instrument_rows | 7 | 0 |
| `sim/grader_confusion.py:169` _heuristic_channel | 17 | 0 |
| `sim/grader_confusion.py:188` _point_diagnosis | 10 | 0 |
| `sim/grader_confusion.py:200` run_planted_misgrade_acceptance | 82 | 1 |
| `sim/grader_confusion.py:284` _draw_from | 9 | 0 |
| `sim/grader_confusion.py:295` choose_prior_concentration_for_budget | 43 | 1 |
| `sim/interval_width_viability.py:82` _joint_alpha | 9 | 0 |
| `sim/interval_width_viability.py:93` _instrument_rows | 3 | 0 |
| `sim/interval_width_viability.py:98` _scenario_verdict | 12 | 0 |
| `sim/interval_width_viability.py:112` run_interval_width_viability | 39 | 1 |
| `sim/kinship_admission.py:42` _pair_discount | 8 | 0 |
| `sim/kinship_admission.py:88` run_admission_sim | 29 | 0 |
| `sim/metrics.py:95` canonical_facet_belief_mae | 46 | 1 |
| `sim/runner.py:184` SimReport.deterministic_dict | 6 | 4 |
| `sim/student.py:267` SyntheticStudent.truth_snapshot | 2 | 0 |
| `source_retrieval/corpus.py:293` assessment_spans | 4 | 0 |
| `source_retrieval/deliverable_path.py:1830` plan_refresh_route_problem | 11 | 2 |
| `source_retrieval/deliverables.py:341` _goals_path | 4 | 0 |
| `source_retrieval/deliverables.py:599` write_facet_scope | 12 | 0 |
| `source_retrieval/dense.py:334` record_keys | 2 | 0 |
| `source_retrieval/feedback.py:132` record_citations | 12 | 1 |
| `source_retrieval/kept_comparisons.py:1237` relation_lineage | 15 | 2 |
| `source_retrieval/kept_comparisons.py:1254` relation_head | 9 | 1 |
| `source_retrieval/library_ask.py:231` OrganizerRoleNote._tolerate_roles | 2 | 0 |
| `source_retrieval/library_ask.py:261` _tolerate_explorable | 8 | 0 |
| `source_retrieval/library_ask.py:278` OrganizerExplorableNote._tolerate | 2 | 0 |
| `source_retrieval/library_ask.py:292` OrganizerRoleExplorableNote._tolerate | 2 | 0 |
| `source_retrieval/library_ask.py:762` organizer_spent_today | 10 | 1 |
| `source_retrieval/passage_cues.py:872` CueJudgment._tolerate_roles | 2 | 0 |
| `source_retrieval/policy.py:98` assert_policy | 16 | 0 |
| `source_retrieval/reader_tutor.py:573` citation_dicts | 9 | 0 |
| `source_retrieval/recipes.py:176` scope_manifest | 5 | 1 |
| `source_retrieval/role_labeller.py:110` PassageRoles._tolerate_roles | 2 | 0 |
| `source_retrieval/section_coverage.py:699` CoverageJudgment._tolerate | 13 | 0 |
| `source_retrieval/suites.py:18` register_suites | 10 | 8 |
| `substrate/activities.py:607` render_assessment_with_replacement | 53 | 1 |
| `substrate/activities.py:742` append_lifecycle | 20 | 0 |
| `substrate/activities.py:956` log_attempt_duration | 22 | 2 |
| `substrate/activities.py:980` log_affect_tap | 29 | 0 |
| `substrate/activities.py:1057` author_family_version | 63 | 2 |
| `substrate/activities.py:1122` activate_family_version | 8 | 1 |
| `substrate/activities.py:1132` _validate_cross_purpose_links | 23 | 0 |
| `substrate/activities.py:1157` link_cross_purpose_families | 22 | 1 |
| `substrate/activities.py:1181` pin_card_authoring | 47 | 3 |
| `substrate/activities.py:1230` resolve_progression_policy | 16 | 1 |
| `substrate/activities.py:1248` inspect_angle_coverage | 13 | 1 |
| `substrate/activity_patterns.py:195` normalize_capabilities | 10 | 1 |
| `substrate/activity_patterns.py:265` _validate_pattern_fields | 21 | 0 |
| `substrate/activity_patterns.py:288` _pattern_content_hash | 27 | 0 |
| `substrate/activity_patterns.py:317` _fields_to_columns | 22 | 0 |
| `substrate/activity_patterns.py:341` register_pattern_version | 33 | 1 |
| `substrate/activity_patterns.py:376` review_pattern_version | 4 | 0 |
| `substrate/activity_patterns.py:382` activate_pattern_version | 4 | 0 |
| `substrate/activity_patterns.py:388` list_compatible_patterns | 22 | 1 |
| `substrate/activity_patterns.py:412` candidate_within_bounds | 25 | 1 |
| `substrate/activity_patterns.py:443` routing_metadata | 10 | 1 |
| `substrate/activity_patterns.py:466` evidence_semantics | 13 | 1 |
| `substrate/activity_patterns.py:485` _launch_pattern_defs | 66 | 0 |
| `substrate/activity_patterns.py:553` ensure_builtin_patterns | 16 | 2 |
| `substrate/activity_patterns.py:575` adapt_probe_template_to_pattern | 32 | 1 |
| `substrate/activity_patterns.py:658` load_pattern_version | 2 | 0 |
| `substrate/administration_adapters.py:93` Adapter.apply_scheduling | 16 | 1 |
| `substrate/administration_adapters.py:126` DiagnosticAdapter.update_episode | 9 | 1 |
| `substrate/administration_adapters.py:170` PracticeAdapter.apply_scheduling | 28 | 1 |
| `substrate/administration_adapters.py:233` resolve_adapter_for_administration | 7 | 0 |
| `substrate/administration_adapters.py:258` project_administration | 48 | 1 |
| `substrate/card_lineage.py:103` _normalized_components | 5 | 0 |
| `substrate/card_lineage.py:302` _rating | 2 | 0 |
| `substrate/card_lineage.py:306` replay_review_events | 14 | 0 |
| `substrate/card_lineage.py:322` rebuild_card_state | 54 | 1 |
| `substrate/compat/card_outcome_replay.py:72` outcome_class_for_response_posterior | 10 | 1 |
| `substrate/compat/card_outcome_replay.py:152` replay_card_outcome_counts | 34 | 2 |
| `substrate/compat/card_outcome_replay.py:188` _outcome_class_from_ledger | 14 | 0 |
| `substrate/compat/card_outcome_replay.py:204` replay_event_stream | 17 | 1 |
| `substrate/compat/card_outcome_replay.py:223` u014_resume_shape | 28 | 1 |
| `substrate/compat/substrate_cutover.py:66` purpose_adapters_live | 16 | 2 |
| `substrate/compat/substrate_cutover.py:84` scheduling_write_authority | 6 | 0 |
| `substrate/compat/substrate_cutover.py:98` reject_legacy_scheduling_write | 9 | 1 |
| `substrate/compat/substrate_cutover.py:109` guarded_legacy_scheduling_write | 39 | 1 |
| `substrate/compat/substrate_cutover.py:193` _existing_observation | 3 | 0 |
| `substrate/compat/substrate_cutover.py:198` submit_administration_response | 179 | 3 |
| `substrate/compat/substrate_cutover.py:379` _enqueue_rebuild | 11 | 0 |
| `substrate/compat/substrate_cutover.py:398` rebuild_deferred_projection | 53 | 1 |
| `substrate/compat/substrate_cutover.py:508` _gate_purpose_side_effects | 12 | 1 |
| `substrate/compat/substrate_cutover.py:522` _gate3_probe_lineage | 22 | 0 |
| `substrate/compat/substrate_cutover.py:546` _gate_new_scheduling_projection | 37 | 1 |
| `substrate/compat/substrate_cutover.py:585` _gate_legacy_writes_rejected | 34 | 0 |
| `substrate/compat/substrate_cutover.py:621` run_cutover_gates | 76 | 2 |
| `substrate/families.py:380` recover_family_operations | 4 | 1 |
| `substrate/surface_mint.py:115` request_candidates | 27 | 3 |
| `substrate/surface_mint.py:144` claim_next_mint_job | 21 | 3 |
| `substrate/surface_mint.py:171` _card_bounds | 8 | 0 |
| `substrate/surface_mint.py:181` _within_task_feature_bounds | 21 | 0 |
| `substrate/surface_mint.py:204` _within_difficulty_bounds | 10 | 0 |
| `substrate/surface_mint.py:216` run_all_gates | 111 | 1 |
| `substrate/surface_mint.py:329` _stale_lease_result | 9 | 0 |
| `substrate/surface_mint.py:340` process_mint_job | 49 | 2 |
| `substrate/surface_mint.py:391` _mark_surface_admitted | 14 | 0 |
| `substrate/surface_mint.py:407` admit_candidate | 48 | 1 |
| `substrate/surface_mint.py:457` reject_candidate | 17 | 0 |
| `substrate/surface_mint.py:476` fail_mint_job | 8 | 0 |
| `substrate/surface_pool.py:263` reject_pool_surface | 19 | 0 |
| `substrate/surface_pool.py:304` activate_pool | 11 | 0 |
| `substrate/surface_pool.py:432` request_spare_mint | 21 | 1 |
| `substrate/surface_pool.py:459` open_practice | 31 | 11 |
| `teacher/service.py:463` _family | 2 | 3 |
| `tui/app.py:40` LearnLoopApp.get_theme_variable_defaults | 5 | 1 |
| `tui/app.py:46` LearnLoopApp.on_mount | 3 | 1 |
| `tui/app.py:50` LearnLoopApp.get_default_screen | 6 | 0 |
| `tui/minutes_memory.py:63` save_chosen_minutes | 22 | 1 |
| `tui/screens/feedback.py:145` FeedbackScreen.on_mount | 15 | 1 |
| `tui/screens/feedback.py:162` FeedbackScreen.watch_surprise_direction | 2 | 0 |
| `tui/screens/feedback.py:165` FeedbackScreen.watch_graded | 2 | 0 |
| `tui/screens/feedback.py:168` FeedbackScreen.watch_has_errors | 2 | 0 |
| `tui/screens/feedback.py:185` FeedbackScreen.set_points | 4 | 3 |
| `tui/screens/feedback.py:190` FeedbackScreen.set_confidence | 4 | 3 |
| `tui/screens/feedback.py:195` FeedbackScreen.set_error_type | 4 | 0 |
| `tui/screens/feedback.py:200` FeedbackScreen.toggle_fatal | 9 | 1 |
| `tui/screens/feedback.py:257` FeedbackScreen.auto_submit_ai | 4 | 1 |
| `tui/screens/feedback.py:262` FeedbackScreen._auto_submit_ai | 46 | 0 |
| `tui/screens/feedback.py:312` FeedbackScreen.auto_submit_codex | 2 | 0 |
| `tui/screens/feedback.py:324` FeedbackScreen._ai_ready | 3 | 0 |
| `tui/screens/feedback.py:328` FeedbackScreen._provider_label | 3 | 0 |
| `tui/screens/feedback.py:426` FeedbackScreen._record_worked_answer_reveal | 18 | 0 |
| `tui/screens/feedback.py:640` FeedbackScreen._render_fatal_summary | 5 | 0 |
| `tui/screens/feedback.py:646` FeedbackScreen.return_to_today | 5 | 1 |
| `tui/screens/feedback.py:652` FeedbackScreen.action_submit | 2 | 1 |
| `tui/screens/feedback.py:655` FeedbackScreen.action_next | 8 | 1 |
| `tui/screens/feedback.py:664` FeedbackScreen.advance_to_next | 7 | 0 |
| `tui/screens/feedback.py:672` FeedbackScreen.action_back | 2 | 1 |
| `tui/screens/feedback.py:675` FeedbackScreen.on_button_pressed | 7 | 0 |
| `tui/screens/practice.py:208` PracticeScreen.on_mount | 3 | 1 |
| `tui/screens/practice.py:212` PracticeScreen.on_screen_resume | 2 | 0 |
| `tui/screens/practice.py:216` PracticeScreen.watch_hints_used | 5 | 0 |
| `tui/screens/practice.py:227` PracticeScreen.set_answer | 3 | 5 |
| `tui/screens/practice.py:231` PracticeScreen.reveal_hint | 11 | 1 |
| `tui/screens/practice.py:250` PracticeScreen.press_stuck | 10 | 0 |
| `tui/screens/practice.py:339` PracticeScreen.action_submit | 6 | 1 |
| `tui/screens/practice.py:346` PracticeScreen.action_hint | 2 | 0 |
| `tui/screens/practice.py:349` PracticeScreen.action_stop_diagnosing | 12 | 0 |
| `tui/screens/practice.py:362` PracticeScreen.action_dont_know | 5 | 0 |
| `tui/screens/practice.py:368` PracticeScreen.action_skip | 2 | 0 |
| `tui/screens/practice.py:371` PracticeScreen.action_back | 2 | 1 |
| `tui/screens/practice.py:375` PracticeScreen.on_text_area_changed | 2 | 0 |
| `tui/screens/practice.py:378` PracticeScreen.on_button_pressed | 4 | 0 |
| `tui/screens/practice.py:383` PracticeScreen._refresh_answer_meta | 5 | 0 |
| `tui/screens/practice.py:464` PracticeScreen._hints_content | 13 | 0 |
| `tui/screens/start.py:40` Torus.on_mount | 3 | 1 |
| `tui/screens/start.py:136` MinutesPicker.on_mount | 2 | 1 |
| `tui/screens/start.py:147` MinutesPicker.action_step | 2 | 0 |
| `tui/screens/start.py:150` MinutesPicker.on_click | 10 | 0 |
| `tui/screens/start.py:161` MinutesPicker.watch_index | 4 | 0 |
| `tui/screens/start.py:232` StartScreen.on_mount | 2 | 1 |
| `tui/screens/start.py:236` StartScreen.on_minutes_picker_changed | 2 | 0 |
| `tui/screens/start.py:239` StartScreen._refresh_mode | 2 | 0 |
| `tui/screens/start.py:252` StartScreen.begin_session | 15 | 12 |
| `tui/screens/start.py:268` StartScreen.action_begin | 2 | 0 |
| `tui/screens/start.py:271` StartScreen.on_button_pressed | 3 | 0 |
| `tui/screens/today.py:50` PracticeCard.on_click | 2 | 0 |
| `tui/screens/today.py:100` TodayScreen.on_mount | 2 | 1 |
| `tui/screens/today.py:103` TodayScreen.on_screen_resume | 8 | 0 |
| `tui/screens/today.py:113` TodayScreen.action_refresh | 4 | 0 |
| `tui/screens/today.py:118` TodayScreen.action_move | 5 | 0 |
| `tui/screens/today.py:124` TodayScreen.action_open_selected | 5 | 0 |
| `tui/screens/today.py:130` TodayScreen.action_quick_open | 6 | 0 |
| `tui/screens/today.py:137` TodayScreen.open_practice | 7 | 11 |
| `tui/screens/today.py:145` TodayScreen._practice_screen | 4 | 0 |
| `tui/screens/today.py:150` TodayScreen.on_practice_card_selected | 5 | 0 |
| `tui/screens/today.py:157` TodayScreen._render_queue | 39 | 0 |
| `tui/screens/today.py:197` TodayScreen._refresh_static_panels | 5 | 0 |
| `tui/screens/today.py:203` TodayScreen._grouped | 26 | 0 |
| `tui/screens/today.py:230` TodayScreen._mark_focused | 3 | 0 |
| `tui/screens/today.py:305` TodayScreen._card_content | 36 | 0 |
| `tui/screens/today.py:379` TodayScreen._due_offset | 5 | 0 |
| `tui/widgets.py:103` KeyBar.set_keys | 3 | 0 |
| `tutor/ai_contracts.py:246` ExplorableCitation._tolerate | 4 | 0 |
| `tutor/reader_modes.py:500` guard_thread | 6 | 1 |
| `tutor/tutor_qa.py:459` attempt_key_matches | 12 | 0 |
| `vault/hashes.py:28` learning_object_hash | 16 | 1 |
| `vault/hashes.py:88` concept_hash | 10 | 0 |
| `vault/hashes.py:100` concept_edge_hash | 15 | 0 |
| `vault/hashes.py:122` rubric_hash | 2 | 0 |
| `vault/models.py:53` GoalFacetScope.is_empty | 2 | 1 |
| `vault/models.py:97` Goal._convert_legacy_concept_anchors | 11 | 0 |
| `vault/models.py:153` SourceSetMember._omit_unrecorded_scope_reading | 7 | 0 |
| `vault/models.py:278` Rubric.derive_max_points_from_criteria | 18 | 0 |
| `vault/models.py:429` TraceContract.validate_trace_contract | 25 | 0 |
| `vault/models.py:662` FamilyReference._verified_check | 4 | 0 |
| `vault/models.py:850` PracticeItem._family_relationship | 6 | 0 |
| `vault/models.py:858` PracticeItem._omit_absent_family_fields | 6 | 0 |
| `vault/paths.py:82` VaultPaths.source_dir | 2 | 0 |
| `vault/paths.py:85` VaultPaths.source_markdown_path | 3 | 0 |
| `vault/paths.py:89` VaultPaths.source_revision_path | 3 | 0 |
| `vault/paths.py:97` VaultPaths.source_extraction_cache_dir | 3 | 0 |
| `vault/working_vault.py:32` mark_working_vault | 19 | 1 |
| `vault_lock.py:98` read_lock_holder | 9 | 3 |
| `src/learnloop_mcp/server.py:414` ToolCalls.record_rejected | 19 | 0 |
| `src/learnloop_mcp/server.py:442` LearnLoopServer.call_tool | 13 | 9 |
| `src/learnloop_mobile/doctor.py:27` read_unit_environment | 23 | 1 |
| `src/learnloop_mobile/doctor.py:52` _reaches_backend | 23 | 0 |
| `src/learnloop_mobile/doctor.py:77` _serve_configs | 7 | 0 |
| `src/learnloop_mobile/doctor.py:86` serve_checks | 33 | 1 |
| `src/learnloop_mobile/doctor.py:121` loopback_listener | 7 | 1 |
| `src/learnloop_mobile/doctor.py:130` _unit_readiness | 14 | 1 |
| `src/learnloop_mobile/doctor.py:146` policy_example | 19 | 1 |
| `src/learnloop_mobile/doctor.py:167` doctor | 113 | 66 |
| `src/learnloop_mobile/runtime.py:457` HostRuntime.owed_finishes | 3 | 1 |
| `src/learnloop_sidecar/handlers/serializers.py:94` scheduled_item_dto | 13 | 1 |
