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
| D4 | high | **Router speed target still unmet.** Next right after feedback stays above 2 s on the large copies (a pinned week on linear_algebra: median 2,676 ms, 16 of 21 above 2 s, against mvp-0.49's 2,250 ms and 25 of 30). The remainder is the numeric policy's per-draw arithmetic (about 468k draw-evaluator calls in about 34 profiled jobs), then SQLite reads (about 13 s of 110 s). After a 3 s dwell no Next is above 2 s on any copy. | `docs/reviews/router-speed2.md:376`, `:388`, `:437`; `src/learnloop/router_objective/value.py:1512` |
| D5 | medium | **R4's cost.** A pooled connection on which a PRAGMA with an argument ran is closed at release, and `PRAGMA table_info(t)` is such a PRAGMA. There are 53 `table_info` sites in 39 files, including the objective's own paths, so each column check inside a job throws away a pooled connection. Measured opens per job went from 5 to 17 after R1-R4. Column checks are themselves compatibility code for older schemas. | `src/learnloop/db/connection.py:310`; `docs/reviews/router-speed2-codex-review.md:259`; `src/learnloop/router_objective/scores.py:199`, `src/learnloop/router_objective/checks.py:563`, `src/learnloop/daily_plan/router_card.py:447` |
