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
