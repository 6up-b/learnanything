# K11 — Daily-plan engine map

## Summary for the owner

**Verified:** at `f4ccb20266cb4f9ba8981a3decad54b3783585a1`, `src/learnloop/daily_plan/engine.py` is **6,777 lines**. It contains nine functions over 100 lines, including two over the ratchet’s 200-line threshold. Its main responsibility is still the traversal: gathering a plan’s inputs, crossing a boundary, committing the choice, serving it, and folding subsequent activity back into the plan. Arc E mostly separated the chooser and objective underneath it. It did not extract this traversal. Evidence: `daily_plan/engine.py:1611–2160`, `daily_plan/engine.py:3086–3365`, `daily_plan/engine.py:3955–4108`, `daily_plan/engine.py:5327–5540`; `docs/reviews/refactor-status.md:97–112`.

**Named costs exist.** The strongest evidence is:

| ID | Cost | Finding |
|---|---|---|
| **K11-C1** | A record-construction failure changed the served choice. | **Verified, historical defect, fixed.** ER-8 records a failure after the draw escaping into the engine’s fallback. The current boundary still joins separately produced choice, trace, record and persistence results. `docs/reviews/refactor-bug-ledger.md:275`; `daily_plan/engine.py:2698–2746`; `daily_plan/objective_chooser.py:757–775`. |
| **K11-C2** | A job’s ownership crossed the plan, chooser and host lifetimes. | **Verified, historical defect, fixed.** The carry fix touched the engine and four other files. New-plan creation still owns a carry-stop call; host closure and job registration live elsewhere. `docs/reviews/refactor-bug-ledger.md:276`; `daily_plan/engine.py:2142`; git `24427cb66b`. |
| **K11-C3** | Tests depend on private traversal seams. | **Verified, current coupling.** There are 29 literal patch sites naming 18 private engine attributes, plus two dynamic patch sites that exercise engine names. A crash-between-writes test patches `_boundary`; a keyed-pick rollback test injects failure through `_serve`. `tests/test_daily_plan_review_regressions.py:766–787`; `tests/test_reader_rw4b_fix6.py:170–201`. |
| **K11-C4** | A caller cannot establish purity or absence of writes from the apparent phase boundary. | **Verified code; inferred maintenance cost.** `_feasibility` can invoke a database-reading staged source. `_reconcile_changes`, described as “unwritten,” mutates its input and can invoke persisted cold-check eligibility changes before `reconcile` opens its event transaction. `daily_plan/engine.py:2544–2590`, `daily_plan/engine.py:3979–4108`; `daily_plan/staged_frame.py:227–237`; `scheduling/scheduler.py:2047–2088`. |

These establish costs at particular boundaries. **They do not establish that moving the whole traversal into smaller files would reduce those costs.** No implementation steps or split design are proposed here.

## Scope and evidence

This is the map authorized by K11’s stop rule, not a refactor. The rule limits subsequent work to named costs; the strategy explicitly excludes a general traversal rewrite, registries and dependency-injection machinery. Evidence: `docs/reviews/refactor-strategy-v3-audit-2026-11-16.md:98–104`, `:161–164`; `docs/specs/refactor_strategy_v3.md:1068–1094`.

All source references below are at the tip above. Paths beginning with `daily_plan/`, `db/`, `router_objective/`, `scheduling/`, and similar package names omit `src/learnloop/`. Sidecar paths retain `src/learnloop_sidecar/`. Function ranges include signatures and docstrings; lengths are `end_lineno − lineno + 1`, matching the ratchet’s AST convention.

**Verified** means read in source, counted statically, or read in git. **Inferred** identifies an interpretation of that evidence. Historical test outcomes quoted from the ledger remain reported historical outcomes: no tests were run for this map.

The whole engine was read. Nearby interfaces and the relevant paths through its callers and callees were traced. Only source/document reads, static Python analysis and read-only git commands were used. No file changed.

## 1. Traversal, reads, writes and transactions

### Transaction vocabulary

**Verified:** `Repository.atomic()` begins `BEGIN IMMEDIATE` when it owns the transaction; nested atomic work uses savepoints. `connection()` reuses the pinned connection when one exists. `pinned()` alone is not a transaction. Consequently, the engine’s lexical `atomic()` blocks describe transaction boundaries only when the caller has not already supplied an outer transaction. Evidence: `db/repositories.py:353–446`.

The core plan store consists of `daily_plans`, `attention_blocks` and `attention_block_events`. A block’s items and state are reconstructed from its events. Evidence: `db/stores/daily_plans.py:50–215`; `daily_plan/engine.py:845–860`.

In the table:

- **Own atomic** means the phase opens an atomic scope, possibly a nested savepoint.
- **Caller connection** means the phase writes through a connection supplied by its caller.
- **No enclosing atomic** means there is no transaction covering the whole phase. Called services may open their own.
- The last column is **inferred**. “Yes” means the phase already has a name and usable existing arguments/results; it does not mean it is pure. “No” means the proposed phase is not independently bounded in the current code.

### Ordered path

The normal entry is `advance_with_context`; first creation enters `build_plan`, then rejoins the same boundary machinery. Subsequent calls reconcile before deciding or serving again. `serve=False` suppresses presentation of the step, **not** plan creation, reconciliation or boundary writes. Evidence: `daily_plan/engine.py:5327–5352`.

| Phase, in order | Implementing functions: range; length | Reads | Writes and transaction | One named module without a new concept? |
|---|---|---|---|---|
| **0. Prepare the application request** | Sidecar `_require`, `src/learnloop_sidecar/handlers/daily_plan.py:282–308`; `prepare_queue_build`, `src/learnloop_sidecar/handlers/queue.py:120–151`; policy construction, `daily_plan/policy.py:55–127` | Session ownership; loaded configuration; pending diagnoses, commitments and follow-ups; policy settings. | Preparation can settle answered checks and measurement states, and arrange background work. There is no transaction encompassing preparation and the engine traversal. Explicit writes receive an ownership-checking repository wrapper. | **Yes** for the existing application preparation function. Its side effects precede the engine and are not part of a single plan transaction. |
| **1. Find today’s plan or choose its initial budget** | `get_or_create_today`, `daily_plan/engine.py:1611–1634`; 24. `remembered_minutes`, `:880–891`; 12. `PlanEnv.gap`, `:804–813`; 10. | Local date and clock; previous `daily_plans`; recent session activity; plan and re-entry configuration. | Abandons earlier open plans in an atomic scope; otherwise returns today’s existing plan or calls the build path. | **Yes.** Existing `PlanEnv` and `PlanRecord` carry the inputs and result; date and re-entry reads remain effects. |
| **2. Gather and classify the pool** | `_classified_pool`, `:1191–1357`; 167. `_project_probe_admission`, `:1433–1538`; 106. `_pool_prefilter`, `:1360–1392`; 33. | Scheduler queue; item states and requests; intent commitments; scheduled/cold checks; open diagnosed problems; goals/deadlines; duration evidence from `practice_attempts` and block events; clock; VOI policy. | Produces `_Pool`, admission results and prefilter material; changes `env.last_trace` through `build_eligible`. No enclosing atomic. Scheduler/providers retain their own effects. | **Yes as an effectful gatherer.** A scheduler list, requests, probe budget and prefilter must remain the same build’s inputs. |
| **3. Admit new material, choose reading, divide minutes and assemble the plan** | `_prepare_plan`, `:1664–1857`; 194. `_select_checks`, `:1896–1972`; 77. | Pool; day’s existing plans; projected review load; remembered budget; intent; configuration; fresh reading/path choice; clock. Reading also reaches progress and curriculum/path services. | Builds `_Prepared`, including `split_json`, `admission_json` and the future plan row. Does not insert the plan. No enclosing atomic; reading memo state can change. | **Yes.** `_Prepared` already names the result. **Inferred obstacle to purity:** input collection and assembly are interleaved, with several time samples. |
| **4. Commit the plan container** | `build_plan`, `:2084–2160`; 77. `_empty_extension`, `:2072–2081`; 10. | Prepared result; competing plan creation for the same date; previous empty extension. | Atomic duplicate check, optional `with_insert`, and `daily_plans` insert at `:2132–2141`. Stops earlier plans’ carries after that scope; reloads; crosses the first boundary separately. | **Yes.** The existing result and callback suffice. Plan insertion and first-block insertion deliberately remain separate commits. |
| **5. Reconcile activity already recorded** | `reconcile`, `:3955–3976`; 22. `_reconcile_changes`, `:3979–4108`; 130. | `practice_attempts`; loaded item lifecycle; generated-probe closure/retirement; current intents; cold checks; reading history and fresh reading choice; clock. | Mutates the in-memory record while assembling `item_done`, `item_displaced` and `block_ended` events. Cold-check eligibility may write through its callee. Then `reconcile` atomically appends events and updates the reading split/status. | **No as a read/compute/write-independent phase today.** Its “compute changes” part already mutates and can persist. The whole reconciliation operation does have an existing name. |
| **6. Refresh the current context** | `_context`, `:2200–2272`; 73. `_live_context`, `:2370–2382`; 13. `_routine_holds`, `:2275–2292`; 18. | Refreshed pool; fixed plan universe; already planned items; admission; reading; routine holds; AD deferrals; dates and activity. | Builds `PoolContext`; no enclosing atomic. | **Yes.** The context already exists. Its consistency depends on which pool, plan and time samples produced it. |
| **7. Admit or defer newly ready follow-ups** | `_insert_followups`, `:4560–4670`; 111. `_place_followup_probes`, `:4692–4768`; 77. `_restrained_followups`, `:4830–4922`; 93. | Follow-up workflows; current block and remaining minutes; restraint gate; lesson competition; device; estimator and AD facts. | Can displace tail items, insert follow-ups or an offer, record refusal/defer decisions and update workflows. Writes occur in branch-specific atomic scopes; gate/model work is outside those writes. | **Yes for the existing placement operation.** It passes existing plan/pool/outcome values, but its decision and mutation branches are interwoven. |
| **8. Decide whether this call may cross a boundary** | `advance_with_context`, `:5339–5540`; 202. `open_workbench`, `:5291–5311`; 21. `_device_block`, `:5174–5194`; 21. | Open workbench; current block; held device work; pending stop; forced follow-ups; existing offer and whether it was shown. | Can skip an item, withdraw an offer and recurse, or return held/pending/done. Each mutation owns a short atomic scope; no traversal-wide transaction. | **No as a single independent decision phase.** It is the traversal loop: reads, writes, reloads and retries change the next branch’s inputs. |
| **9. Administer randomized checks before the action draw** | `_draw_randomized_checks`, `:3561–3589`; 29. `_randomized_check_block`, `:3609–3697`; 89. | Day/session assignment state; check mode; eligible pool; requested/follow-up items; clock. | Draws/places the day’s checks. If a check block is placed, atomically logs and persists it instead of running the ordinary choice. Accumulates failure records for the boundary. | **Yes.** This is already a named pre-choice operation. Its failure list and forced-item information are shared with the following boundary. |
| **10. Build offers, calculate feasibility and choose** | `_boundary`, `:3086–3365`; 280. `_forced_charges`, `:3049–3083`; 35. `_feasibility`, `:2544–2637`; 94. `decide`, `:2640–2746`; 107. | Plan ledger; context; policy/source; staged frame; lesson offer; follow-up contest; chooser’s database/configuration/job inputs; wall clock for provenance. | Before the block transaction, may build an offer and start/wait for model jobs. Produces a decision; no ordinary block write yet. | **No as one isolated pure phase.** The source can perform reads; offer construction and chooser jobs have lifetimes; feasibility, fallback and record notes are separate operations. |
| **11. Complete records and commit the chosen block** | `_note_for_records`, `:2817–2832`; 16. `_write_boundary_records`, `:2761–2780`; 20. `_persist_block`, `:2955–3046`; 92. Commit portion of `_boundary`, `:3304–3363`. | Chosen decision; forced workflows; trigger attempt and parent records; frozen measurement objective; decision-state material; competing boundary state. | In one atomic scope: rechecks boundary ownership; writes router decision, prefilter/state/trace links and decision records; supersedes offers; arranges applicable measurement commitments; inserts block/events. Forecast writes follow the commit. | **No as “record assembly” alone.** Record identity and linkage are completed across decision, logger and persistence phases. **Yes** for the existing block commit using its caller connection. |
| **12. Name and serve the next step** | `_item_step`, `:5041–5069`; 29. `_reading_step`, `:5072–5091`; 20. `_lesson_offer_step`, `:5094–5111`; 18. `_held_cold_check`, `:5838–5871`; 34. `_serve`, `:5961–6016`; 56. `_present`, `:5889–5958`; 70. | Chosen block/item; device filter; current cold-check eligibility; existing presentation; router decision and offer receipts; clock. | Serving atomically records starts/serves and a presentation. `_present` has its own savepoint so a non-strict presentation failure need not lose the surrounding serve. Eligibility can make separate writes before serving. | **Yes for step construction and for serving separately.** The current transaction/failure policy joins presentation and serve effects; moving a name alone would not separate those semantics. |
| **13. AD replacement or deferral on a serve** | `_ad_deferrals_cleared`, `:5714–5745`; 32. `_ad_slot_serve`, `:5748–5835`; 88. | AD material view; plan-owned membership facts; current deferrals; day’s plans; config and clock. | Outer atomic scope covers guarded decision and accepted plan effects. Nested atomic scopes allow refusal/rollback of an unacceptable AD result. Unavailability records describe fallback to the incumbent. | **Yes as the existing guarded operation.** The same transaction and acceptance check span AD and plan writes; they are not independent per-phase commits. |
| **14. Settle the current plan or close it** | `_close`, `:3863–3949`; 87. `_persist_receipt`, `:3818–3860`; 43. `_close_on_pending_stop`, `:5220–5228`; 9. `stop_today`, `:6700–6719`; 20. | Stop decision; held work; plan state; measurement objective; session response; clock. | Atomic stop receipt, associated decision records/measurement work and plan status update. A stop after held work can leave the plan open. Probe forecasts follow the stop commit. | **Yes.** Closure is already named. Its stop receipt is another boundary decision and shares the same logging/record obligations. |

**Verified supporting read boundaries:** duration evidence is read in `daily_plan/estimates.py:161–225`; reading reaches synthesis manifests/runs and section progress in `daily_plan/reading.py:48–75`, `daily_plan/engine.py:477–492`; re-entry reads session activity in `daily_plan/reentry.py:40–61`. These are not all reads of the downstream scheduler, intent or curriculum packages.

### Alternate paths that do not fit a single forward traversal

| Path | Functions and size | Effects and transaction |
|---|---|---|
| **Read-only job prefetch** | `prefetch_boundary`, `daily_plan/engine.py:5567–5636`; 70. `_reconcile_view`, `:5543–5564`; 22. | **Verified:** re-walks reconciliation, pool building, follow-up checks, forced charges and offer construction to reach the same chooser key. Returns `needs_write` and other reasons where it cannot continue. Its safety boundary includes the caller’s read-only repository attachment and `start_only` policy, not just `serve=False`. `src/learnloop_sidecar/handlers/daily_plan.py:672–694`. |
| **Projection** | `simulate_blocks`, `daily_plan/engine.py:1982–2069`; 88. `project_blocks`, `daily_plan/view.py:39–63`. | **Verified:** projects against copied plan state and a projection policy; does not commit projected blocks. It still calls engine `decide`, whose provenance samples wall time. Purity of its returned `Decision` objects is therefore weaker than deterministic projected blocks. |
| **Learner picks** | `learner_pick`, `daily_plan/engine.py:6097–6269`; 173. `_pick_new_block`, `:6272–6362`; 91. `_keyed_pick_scope`, `:6072–6080`; 9. | **Verified:** handles an already planned item, a closed-plan receipt or a new block. A keyed pick wraps selection, serve, key and delivery callback in one atomic scope; unkeyed paths retain their individual scopes. Reads scheduler offer/slate receipts when linking the choice. |
| **Minutes and extensions** | `_resplit`, `:6417–6455`; 39. `set_minutes`, `:6458–6505`; 48. `keep_going`, `:6508–6525`; 18. `more_new`, `:6564–6621`; 58. | **Verified:** gathers refreshed inputs, changes the remaining split or builds an extension, and records overrides. Slow preparation precedes the relevant atomic update. `more_new` also simulates the tradeoff. |
| **Reading completion/progress** | `reading_ended`, `:6627–6639`; 13. `note_reading_progress`, `:6660–6697`; 38. | **Verified:** locates the plan’s current reading and records progress/end events; later reconciliation interprets them. The fresh-choice rule and its receipt/history checks also occupy `:4138–4418`. |

**Finding — inferred:** the traversal can be named, but the naming alone does not make its phases independent. Three forms of coupling recur: an in-memory `PlanRecord` modified between branches, an atomic scope covering several owners’ writes, and a record completed only after later identifiers or observations exist. Evidence: `daily_plan/engine.py:3304–3363`, `:3979–4108`, `:6072–6269`.

## 2. Size history: what grew after S0

### Reproduced sizes

**Verified by `git show <revision>:src/learnloop/daily_plan/engine.py`:**

| Revision | Lines |
|---|---:|
| Nov 8 map base `a525dbcef4` | 5,977 |
| S0 `a810f628d8` | 6,546 |
| Nov 16 audit’s stated base `250b0e16fe` | 6,788 |
| D7e file revision `128128b911` | 6,775 |
| This tip | **6,777** |

The audit’s numbers reproduce at its named base; the current file is **231 lines larger than S0**, and **11 lines smaller than the audit base**. The audit identifies its base and measurement method at `docs/reviews/refactor-strategy-v3-audit-2026-11-16.md:3–5`.

`git log --follow --numstat` finds **18 file-touching commits after S0**, totalling **369 additions and 138 deletions**. “Landing” below means one such git entry, not an entire merge batch.

### Added-line classification

The addition count is split into **code / comment-or-docstring-only / blank** lines. An inline comment on a code line counts as code. These are physical added-line counts, not claims that every added code line changes behavior.

| Landing | Added / deleted | Added code / comment / blank | What the addition consists of; current evidence |
|---|---:|---:|---|
| `52ecd640ca` — B2 | +51 / −4 | 34 / 10 / 7 | **Record machinery:** provenance imports, `Decision.seen`, chooser-failure capture, boundary-record construction/write, and stop-path plumbing. Adds a wall-clock observation. `daily_plan/engine.py:2389–2408`, `:2707–2710`, `:2749–2780`, `:3919–3922`. |
| `1ddf7c88ed` — B3 | +219 / −28 | 148 / 38 / 33 | **Record machinery:** trigger/parent lookup; forced-item and superseded-offer facts; failed-step collection; check-block, interrupt, AD-fallback and serve-eligibility records; withdrawal-parent propagation. Includes database reads, mutation of `Decision.seen`, failure handling and writes, not just assembly. `:2783–2854`, `:3700–3717`, `:4925–4938`, `:5694–5711`, `:5838–5871`. |
| `7ad0437811` — B8 | +24 / −5 | 14 / 6 / 4 | **Record machinery:** logger-failure records at block and interrupt boundaries. `:964–1019`, `:5030–5035`. |
| `c88c1595f2` — Arc B fix 5 | +5 / −2 | 3 / 2 / 0 | **Record semantics:** prefer the attempt captured by the chooser over an attempt committed while it waited. `:2768–2773`. |
| `375c0c00c3` — retrievability | +2 / −2 | 2 / 0 / 0 | Mechanical common-function import/call; not record assembly. `:115`, `:1568–1582`. |
| `701fe41f7e` — D6 gates | +8 / −16 | 1 / 7 / 0 | Floor-gate simplification and explanatory text; not record assembly. `:151–154`, `:203–232`. |
| `4d59c0a826` — split/shadow retirement | +4 / −14 | 1 / 3 / 0 | Gate simplification around the diagnosed-problem repair rule. `:1103–1109`. |
| `d794e6f1b0` — reading-path switch retirement | +9 / −14 | 3 / 6 / 0 | Reading-path gate and receipt-path simplification. `:203–217`, `:4138–4199`. |
| `0a61836d96` — curriculum switch retirement | +6 / −12 | 2 / 4 / 0 | Deliverable-path gate simplification. `:220–232`, `:243–257`. |
| `128128b911` — data-capture switch retirement | +4 / −6 | 3 / 1 / 0 | Removes serving-switch checks from current capture behavior; not a new record builder. `:118`, `:1360–1392`, `:3779–3797`. |
| `61c247b726` — E6 alternative | +7 / −7 | 7 / 0 / 0 | Shared offer predicate/ref bindings and replacements of local comparisons. `:117`, `:2895–2924`, `:3320–3341`. |
| `13fe961716` — ER-11 | +5 / −5 | 5 / 0 / 0 | Rebinds the predicate to the standard-library leaf and preserves candidate-vs-subtype meaning. `:117`; `plan_refs.py:1`. |
| `24427cb66b` — carry lifecycle | +14 / −0 | 7 / 3 / 4 | **Behavior/lifecycle:** stops previous-plan carries when a new plan commits. The initial helper was subsequently removed. Current call: `:2142`. |
| `9ade08f447` — ER-4/ER-8 | +3 / −1 | 2 / 1 / 0 | **Record-failure semantics:** preserves the chooser’s record-build failures while adding boundary failures. `:2817–2832`; `daily_plan/objective_chooser.py:757–775`. |
| `fae3920269` — router fix follow-up | +3 / −18 | 3 / 0 / 0 | Separates decision-failure notes and calls `stop_carries` directly, removing the engine helper. `:111`, `:2142`, `:2823–2829`. |
| `e0abdbe223` — effective posterior | +3 / −1 | 2 / 0 / 1 | **Behavior/evidence:** decision-state capture reads the effective episode posterior. `:3743–3768`. |
| `88d64cf8a0` — effective observations | +0 / −1 | 0 / 0 / 0 | Deletes an unused import; no added engine behavior. Current import block: `:43–122`. |
| `46de447004` — caller’s exclusion clock | +2 / −2 | 2 / 0 / 0 | **Behavior/time:** exclusion reads receive the caller’s `now`. `:415–446`, `:1550–1587`. |
| **Total** | **+369 / −138** | **239 / 81 / 49** | **Net +231.** |

### What is actually L6-related

**Verified:** the three record landings B2, B3 and B8 account for **294 of the 369 added lines**, and **257 net lines**. The other changes together reduce that net growth by 26 lines. Thus record work explains more than the entire net growth since S0.

**Inferred classification:** L6 concerns the decision-specific facts and rule coverage currently derived from a completed decision: failure classification, alternatives, chosen reason, forced-item facts, and interrupt/check outcomes. Current sites include `daily_plan/engine.py:2817–2854`, `:3700–3717`, `:4925–4938`, plus `daily_plan/boundary_records.py:136–223` and `daily_plan/plan_records.py:133–248`.

That does **not** make all 294 added lines movable core assembly. These additions also contain:

- Database lookup of trigger attempts, parent records and workflows: `daily_plan/engine.py:2783–2814`.
- Transaction-bound writes and links to IDs only known at commit: `:2761–2780`, `:3304–3363`.
- Exception containment and logging: `:2749–2758`, `:2844–2854`.
- Caller-to-caller propagation of withdrawal parents: `:5339–5344`, `:5470–5483`.

**Verified qualification:** L6’s wording is “a core returns its record,” but the current objective core returns `Choice`; its `DecisionRecord` is constructed afterward in `choose.decision_record`, guarded by `_built_record`. That is the ER-8 repair, not an unnoticed absence of the initial E2 design. Evidence: `docs/specs/refactor_strategy_v3.md:804–807`; `router_objective/choose.py:102–210`, `:307`; `daily_plan/objective_chooser.py:757–775`, `:1060`.

No exact “L6 would remove N engine lines” follows from the history without defining and proving a particular core boundary.

## 3. What arc E moved, and what remains

**Verified:** E1–E6 and the E review landed; E6 landed its smaller alternative. E7 is waiting, E7b was dropped, E8 deferred and E9 unstarted. `docs/reviews/refactor-status.md:97–112`.

| Landed step | What moved out | What still sits in the engine |
|---|---|---|
| **E1 — switches and availability** | Availability rules moved from `router_objective_switches` to `db/attempt_availability`; scheduler/projection switches received separate homes. This was not an engine extraction. `docs/reviews/refactor-e1.md:110–118`. | Plan/path/reading gates remain at `daily_plan/engine.py:151–232`; deterministic scheduler configuration at `:707–777`; exclusions, intent and duration readers are still selected by the engine. **Verified:** these are its call-site policy and gathering responsibilities, not copies of the extracted availability formula. |
| **E2 — pure objective choice** | The mixture/coin/rationale decision moved from `ObjectiveChooser` into `router_objective/choose.py:152–210`. Choice facts and record construction now share that module; record failure is guarded outside the draw. | Engine feasibility, forced-item charging, offered/invalid-choice checks, fallback and container `Decision` remain at `daily_plan/engine.py:2544–2746`, `:3049–3083`. **Inferred:** “the chooser is pure” does not describe this outer decision operation. |
| **E3 — jobs, clocks and seeds** | Job start/wait/publication/carry handling moved to `daily_plan/objective_job.py`; seed construction to `daily_plan/objective_seeds.py`. `docs/reviews/refactor-e3.md:131–190`. | The engine chooses when jobs may be reached, handles `DecisionPending`, and restarts traversal after boundary races. It also stops carries at new-plan creation. `daily_plan/engine.py:2142–2159`, `:2700–2703`, `:5420–5429`, `:5567–5636`. Wall time for boundary provenance remains at `:2710`. |
| **E4 — trace assembly** | Candidate rows and objective trace assembly moved from the chooser to `router_objective/trace_assembly.py:69–129`, `:236–421`; existing trace storage remained separate. `docs/reviews/refactor-e4.md:80–112`. | Engine block detail, `PlanBlockDecision`, prefilter/state linking, boundary records, interrupt records and stop records remain. `daily_plan/engine.py:901–1019`, `:3155–3209`, `:3304–3363`, `:3863–3949`, `:4960–5035`. **Verified:** trace assembly and container receipt assembly are different remaining responsibilities. |
| **E5 — objective versus rollouts** | `value.py` became `objective.py`, `rollouts.py`, `ad_link.py` and `types.py`. `docs/reviews/refactor-e5.md:142–161`. | Engine gathers/fixes the measurement objective, captures decision state, places checks and records forecasts. `daily_plan/engine.py:3561–3717`, `:3743–3815`. **Verified:** objective mathematics did not remain duplicated here; the remaining code joins its inputs and consequences to the plan. |
| **E6 — smaller alternative** | Shared offer predicate and refs, a completeness guard, and an action-addition inventory; the full action-module design stopped. ER-11 placed the shared refs in `plan_refs.py`. `docs/reviews/refactor-e6.md:231–264`; `docs/reviews/refactor-bug-ledger.md:278`. | Offer building/competition, withdrawal, replacement, placement and serving still branch through the engine. `daily_plan/engine.py:2895–2924`, `:3124–3136`, `:3257–3357`, `:3373–3550`, `:5460–5501`. These are action lifecycle branches, not remaining copies of the shared predicate. |
| **E review** | Repairs sampling order, record failure containment, carry ownership and predicate contracts. `docs/reviews/refactor-bug-ledger.md:271–278`. | Current boundary records still need the chooser’s captured attempt, later parent/workflow facts and separate decision/boundary failure collections. `daily_plan/engine.py:2768–2775`, `:2817–2832`. The new-plan carry hook remains at `:2142`. |

### Later modules are not evidence that the engine was split

- **Verified:** `next_practice.py` is a separate dated, read-only summary. It freezes a clock value, attaches a read-only repository and imports `engine.review_population`. The population reader remains in the engine at `:1550–1587`. `daily_plan/next_practice.py:61–89`; `docs/reviews/refactor-status.md:356–370`.
- **Verified:** `check_delivery.py` classifies lesson-receipt trials as of a supplied time and computes counts/posteriors. `check_inputs.py` shares availability and dry-duration inputs. They feed lesson-offer pricing, rather than replacing the engine’s randomized-check administration or presentation paths. `daily_plan/check_delivery.py:161–184`, `:378–427`; `daily_plan/check_inputs.py:65–155`; `daily_plan/lesson_offer.py:635–639`; `daily_plan/engine.py:3561–3717`, `:5231–5258`.
- **Verified:** `schedule_effects.py` also imports `review_population`. This is a second observer depending on an engine-owned reader. `daily_plan/schedule_effects.py:45–56`.
- **Verified:** the router objective package now owns choice, trace assembly and objective/rollout mathematics. The engine still decides when those operations run and which writes belong to their result. `daily_plan/engine.py:3086–3365`.

## 4. Decision purity

“Pure” here means no database, clock, mutable external state or effectful callback is consulted while computing the result. Reading an already supplied record or configuration object does not by itself make a function impure.

The classifications below concern the relevant decision families, not serialization helpers or SQL writers.

| Decision family | Database / clock while deciding? | Classification |
|---|---|---|
| Plan/path switches: `plan_active`, `reading_from_furthest_active`, `reading_step_rule`, `reading_path_plan_active`, `deliverable_plan_active`; `daily_plan/engine.py:151–232` | Configuration/version predicates; no DB or clock in these bodies. | **Verified:** pure given the loaded configuration and leaf predicates. |
| Request selection and budget arithmetic: `_select_requests`, `_request_candidate`, `_usable_probe_minutes`; `:1112–1188` | No DB/clock. | **Verified:** pure given arguments. |
| Availability of already planned probes: `_plan_availability`; `:1146–1174` | Examines the supplied plan/held set. | **Verified:** no environmental reads; returned predicate depends on those supplied objects. |
| New-material candidate ordering, intent projections and admission IDs: `new_material_candidates`, `admitted_new_material_ids`, `_intent_admission_order`, `_intent_views`; `:2427–2527` | No direct DB/clock; uses supplied intent/context values and methods. | **Verified:** value computation under the existing intent-view contract. Arbitrary replacement callbacks are not proven pure. |
| Check selection: `_select_checks`; `:1896–1972` | Supplied intent, pool and budget. | **Verified:** decision logic already separated from pool gathering. |
| Reading selection: `_reading_on_path`, `_deliverable_choice`, `_fresh_reading_checked`, `_reading_on_book_path`; `:243–393`, `:504–571` | Reads curriculum/path/current reading state, repository and loaded content. | **Verified:** effectful. **Inferred:** not one flat context away without specifying the downstream choice/read contracts. |
| Reading memo validity: `_fresh_reading_fingerprint`, `_remembered_fresh_reading`; `:415–474` | Clock/date, exclusions, diagnosis waits and database commit identity; mutable memo. | **Verified:** effectful, including cache state. `daily_plan/reading_choice.py:118–150`. |
| Pool classification and probe admission: `_classified_pool`, `_project_probe_admission`; `:1191–1538` | DB, clock, scheduler, intent and VOI services; nested classification samples `env.now()`. | **Verified:** effectful. **Inferred:** the classification arithmetic can consume captured facts; the whole gathering/VOI operation is not merely missing a context parameter. |
| Review load population: `review_population`; `:1550–1587` | Repository and loaded items; exclusion time. | **Verified:** reader, not pure. Its downstream `projected_review_load` receives `now` and value inputs. `daily_plan/admission.py:109–135`. |
| Plan preparation: `_prepare_plan`; `:1664–1857` | DB and multiple clock/config reads. | **Verified:** effectful composition. **Inferred:** its admission/split/row arithmetic is one captured build-input set away; preserving present read points is a separate obligation. |
| Feasibility: `_feasibility`; `:2544–2637` | No direct SQL/clock, but calls `policy.make_source(context)` and `source.candidates`. | **Verified:** pure only for a pure source. Production `StagedFrameFactory` calls `frame.material`, which can build from DB and clock. `daily_plan/staged_frame.py:194–200`, `:227–237`, `:390–410`. |
| Outer choice/fallback: `decide`; `:2640–2746` | Effectful source/chooser; unconditional evaluation of `wall_now()` for `setdefault`. | **Verified:** not pure even with a deterministic chooser, because returned provenance can vary with wall time. |
| Choice validation: `_malformed_choice`; `:2863–2878` | No DB/clock. | **Verified:** pure given the choice. |
| Forced charges and tail displacement: `_forced_charges`, `_displaceable`, `_displacement_plan`; `:3049–3083`, `:4437–4470` | Supplied plan/context/items. | **Verified:** no DB/clock in the calculation. Actual displacement is a separate effect at `:4515–4540`. |
| Offer/follow-up eligibility: `_lesson_already_competed`, `_followup_contest`, `_offer_may_interrupt`, `_pending_followups`; `:3384–3502`, `:4546–4557` | Mixed: plan/pool-only checks beside repository/config-dependent checks. | **Verified:** the whole family is not pure. **Inferred:** the local predicates are small once their lookup results are supplied; the gate itself can perform model work. |
| Reconciliation: `_reconcile_changes`; `:3979–4108` | DB, clock, current item/intent/path state. | **Verified:** also mutates plan items/blocks and may persist eligibility changes. More than a context object separates it from purity. |
| Reading history/reopening predicates: `_path_split_reopens`, `_bounded_moves`, `_choice_fields`, `_closed_for_want_of_path_reading`; `:4127–4135`, `:4299–4323`, `:4399–4418` | Supplied records/receipts. | **Verified:** no environmental reads. Their surrounding fresh-choice reconciliation is effectful. |
| Pending-stop and held-check predicates: `_stop_pending`, `_check_held`; `:5204–5217`, `:5261–5266` | Supplied record/device state. | **Verified:** local predicates. `_device_block` is broader: it can record a check deferral. `:5157–5194`. |
| Serving eligibility and AD acceptance: `_held_cold_check`, `_ad_slot_serve`; `:5748–5871` | DB, clock, AD view and plan membership. | **Verified:** decisions and persistence are composed here; not pure wrappers. |
| Learner pick, minute changes, extension and stopping: `learner_pick`, `set_minutes`, `keep_going`, `more_new`, `stop_today`; `:6097–6719` | Current DB state, clock and refreshed context. | **Verified:** application operations with branches and writes, not candidate pure cores as whole functions. |

**Finding — K11-C4:** the “Pure” label on `_feasibility` is too broad for the production policy. Likewise, “unwritten” on `_reconcile_changes` describes its returned event list, not all effects reachable during its execution. Neither finding proves a new user-visible defect. They establish that those signatures/docstrings are insufficient boundaries for isolated reasoning.

## 5. Every function over 100 lines

**Verified static census.** “Direct call” means a syntactic call resolved through an engine import/alias in tracked test Python, including helpers. It does not count an entry point eventually reaching the function, or a saved function reference invoked under another variable.

| Function | Engine range | Lines | What it does | Direct test call? |
|---|---|---:|---|---|
| `_classified_pool` | `daily_plan/engine.py:1191–1357` | 167 | Builds the scheduler pool, applies requests/intent/probe admission, classifies lanes and captures prefilter facts. | **Yes:** `tests/test_placement_unevidenced_return.py:294`. |
| `_project_probe_admission` | `:1433–1538` | 106 | Supplies project-probe candidates, costs and constraints to VOI admission. | **Through a helper:** `tests/voi_stopping_helpers.py:234`. |
| `_prepare_plan` | `:1664–1857` | 194 | Chooses forced work, admission, reading and lane split, then assembles the plan row. | **Yes, three sites:** `tests/test_daily_plan_review_regressions.py:934`; `tests/test_data_capture_a2_measurement.py:331`, `:343`. |
| `decide` | `:2640–2746` | 107 | Computes feasible options, asks the chooser, validates its answer and applies fallback. | **Yes, 16 sites:** examples at `tests/test_block_chooser_interface.py:88–113`. |
| **`_boundary`** | **`:3086–3365`** | **280** | Administers checks or selects and commits the next ordinary/offer/stop boundary. | **No direct syntactic call found.** Patched in crash-recovery tests: `tests/test_daily_plan_review_regressions.py:779–782`, `:880–883`. |
| `_reconcile_changes` | `:3979–4108` | 130 | Folds attempts, ineligibility and reading changes into in-memory state and pending events. | **No direct call found.** |
| `_insert_followups` | `:4560–4670` | 111 | Finds newly ready follow-ups and routes placement, restraint, refusal or boundary forcing. | **No direct call found.** |
| **`advance_with_context`** | **`:5339–5540`** | **202** | Runs reconciliation, refresh, follow-up placement, boundary decisions and next-step serving. | **Yes, 11 sites:** examples at `tests/test_ad23_fix_r5.py:191`, `:218`; `tests/test_ad2_serving.py:626`. |
| `learner_pick` | `:6097–6269` | 173 | Serves an explicit pick through planned, closed-plan and new-block paths, including keyed retries. | **Yes, 26 sites:** examples at `tests/test_daily_plan_build.py:302`, `:318`. |

The engine contributes exactly **two** functions to `functions_over_200_lines`: `_boundary` and `advance_with_context`. The ratchet counts that metric and its member list at `tests/test_structure_ratchets.py:53–63`; its measurement uses AST function ranges in `scripts/refactor_measures.py:727–736`.

**Inferred:** the ratchet detects the largest two functions, but seven other long functions and the file’s many shorter lifecycle helpers remain outside that metric. Their existence alone is not a named change cost.

## 6. Callers, private reach and cycles

### Direct importers

**Verified static census:** **182 tracked Python files directly import the engine**:

- **19 production files:** 12 in `learnloop`, seven in `learnloop_sidecar`.
- **163 test-tree files:** 140 `test_*.py` files and 23 helper files.

This counts importing files, not import statements, runtime callers or unique functions. Function-local imports count.

| Production callers | Count | Engine names used/imported |
|---|---:|---|
| `src/learnloop_sidecar/handlers/daily_plan.py:34–53`, `:451`, `:499`, `:599`, `:718` | 1 | `PlanEnv`, `PlanInactiveError`, `PlanStillOpenError`, `advance_with_context`, `keep_going`, `learner_pick`, `more_new`, `picked_under`, `plan_active`, `plan_scheduler_session`, `prefetch_boundary`, `reading_ended`, `set_minutes`, `stop_today`, `intent_view`, `latest_today`, `get_or_create_today`. |
| Other sidecar handlers: `deliverables.py:358`, `notes.py:174`, `practice.py:426`, `queue.py:19`, `reader.py:2226` | 5 | `deliverable_plan_active`, `local_date`, `PlanEnv`, `open_randomized_check`, `plan_active`, `note_reading_progress`. |
| Phone reader: `src/learnloop_sidecar/phone_reader.py:71` | 1 | `PlanEnv`, `open_randomized_check`. The phone’s ordinary plan routes reach the shared handlers through its allowlist, rather than another direct engine import: `src/learnloop_mobile/allowlist.py:170`, `:314`. |
| CLI: `cli/plan.py:43`, `:73` | 1 | `load_records_from_connection`, `local_date`, `plan_active`. |
| `daily_plan/policy.py:29` | 1 | `DEFAULT_POLICY`, `PlanPolicy`, `plan_active`. |
| `daily_plan/view.py:18` | 1 | `PlanEnv`, `PlanPolicy`, `PoolContext`, `day_records`, `simulate_blocks`. |
| `daily_plan/lesson_suggestion.py:55` | 1 | `PlanEnv`, `latest_today`. |
| `daily_plan/next_practice.py:65`; `daily_plan/schedule_effects.py:48` | 2 | `review_population`. |
| `daily_plan/slot_facts.py:50` | 1 | `admitted_new_material_ids`. |
| `daily_plan/learner_action.py:37` | 1 | Module alias `E`; public plan loading/reconciliation and **13 private names**, listed below. |
| `followup_run/router.py:173`, `:231`, `:344`; `followup_run/serving.py:142` | 2 | `PlanEnv`, `get_or_create_today`, `plan_active`, `interrupt_offer`, `place_interrupt_offer`, `FOLLOWUP_GONE`, `followup_placement`, `latest_today`. |
| `figures/prefetch.py:647`; `remote/views.py:144` | 2 | `load_records`; the remote view also imports `PlanEnv`, `plan_active`. |

**Verified production private reach:** `learner_action` uses `_live_context`, `_feasibility`, `_device_detail`, `_decision_state`, `_close`, `_done_step`, `_reload`, `_persist_block`, `_event`, `_reading_step`, `_serve`, `_item_step`, `_standing_presentation`. These are candidate calculation, state capture, mutation and presentation services—not one incidental helper. Evidence: `daily_plan/learner_action.py:280–281`, `:358`, `:456`, `:500–565`, `:624–632`.

**Inferred:** engine internals already form an application interface for another module. A purely mechanical move would have to preserve that interface or change its consumer.

### Names reached by tests

**Verified:** the test imports cover:

- Environment/value types and constants: `PlanEnv`, `PlanPolicy`, `PoolContext`, `PlanBlockDecision`, `DEFAULT_POLICY`, the plan errors, origin/check/follow-up/reading/held-step constants.
- Main operations: `get_or_create_today`, `build_plan`, `advance`, `advance_with_context`, `reconcile`, `decide`, `simulate_blocks`, `learner_pick`, `set_minutes`, `keep_going`, `more_new`, `stop_today`, `note_reading_progress`, `open_randomized_check`, `open_workbench`, `interrupt_offer`, `followup_placement`.
- Readers/policy helpers: `load_records`, `day_records`, `latest_today`, `local_date`, `local_day_start_iso`, `plan_active`, `plan_scheduler_session`, `staged_plans_deterministic`, the reading/path gates, `intent_view`, `new_material_candidates`, `legacy_source`, `ro5_check_origin`, `picked_under`.
- Logger registration and private pool, reading, reconciliation, boundary, selection and serving helpers.

Representative import/call evidence: `tests/test_block_chooser_interface.py:88`; `tests/test_daily_plan_build.py:302`; `tests/test_daily_plan_review_regressions.py:934`; `tests/test_placement_unevidenced_return.py:294`. The exhaustive private-patch census follows; direct private reads/calls are broader than patches.

### Engine private patches counted by the ratchet’s method

The ratchet resolves import aliases and module re-exports, counts each patch call once, and separately admits audited dynamic calls. A loop is one site. Evidence: `scripts/refactor_measures.py:246–260`, `:336–395`.

**Verified literal sites: 29, targeting 18 private names in 18 files.**

| Private name | Sites | Evidence |
|---|---:|---|
| `_fresh_reading` | 1 | `tests/data_capture_a2_measurement_helpers.py:67` |
| `_deliverable_choice` | 1 | `tests/test_curriculum_c1_fix_round2.py:293` |
| `_exam_material` | 2 | Same file, `:368`, `:370` |
| `_fresh_reading_checked` | 4 | `tests/test_curriculum_c1_fix_round3.py:110`, `:144`; `tests/test_curriculum_c1_fix_round4.py:108`; `tests/test_reader_rw6b_p2_landing.py:93` |
| `_boundary` | 4 | `tests/test_daily_plan_review_regressions.py:779`, `:782`, `:880`, `:883` |
| `_checks_to_place` | 1 | `tests/test_forced_withdrawal_records.py:216` |
| `_open_cold_check_items` | 1 | Same file, `:336` |
| `_randomized_check_block` | 1 | `tests/test_ih2_lessons_compete.py:206` |
| `_followups_compete` | 1 | Same file, `:207` |
| `_lesson_already_competed` | 1 | `tests/test_ih2_offer_ceiling_and_unseen.py:271` |
| `_offer_may_interrupt` | 2 | `tests/test_ih2_one_open_offer.py:349`, `:354` |
| `_persist_block` | 1 | `tests/test_ih3_learner_preferences.py:186` |
| `_classified_pool` | 4 | `tests/test_mobile_v2_landing_fixes.py:53`; `tests/test_mobile_v2_rereview_fixes.py:142`; `tests/test_mobile_v2_review_fixes.py:234`, `:275` |
| `_resplit` | 1 | `tests/test_mobile_v2_landing_fixes.py:169` |
| `_prepare_plan` | 1 | `tests/test_mobile_v3_carried.py:71` |
| `_PLAN_DECISION_LOGGERS` | 1 | `tests/test_remaining_decision_records.py:87` |
| `_displacement_plan` | 1 | `tests/test_router_g4_restraint.py:108` |
| `_live_context` | 1 | `tests/test_voi_v2.py:257` |

**Verified dynamic sites:**

1. `tests/test_mobile_v2_plan.py:233–234` patches `_device_block`, `_device_item`, `_held_step`, `_note_check_deferral` in one loop, asserting that desktop requests never enter device-only branches.
2. `tests/test_reader_rw4b_fix6.py:170–180` is a shared dynamic failure helper. Its engine use at `:201` patches `_serve`; other invocations target other modules. It is one ratchet site, not an engine-exclusive site.

Together these are **31 patch sites touching the engine and 23 distinct private engine names**. The shared dynamic helper must not be counted again when summing a whole-repository per-module breakdown.

**K11-C3’s limit:** the tests demonstrate dependence on these seams. Static reading cannot prove that no alternative test could express the same condition.

### Import cycles

**Verified:** the engine participates in runtime import cycles, including function-local edges:

- `engine → policy → engine`: `daily_plan/engine.py:722`; `daily_plan/policy.py:29`.
- `engine → lesson_suggestion → engine`: `daily_plan/engine.py:5097`; `daily_plan/lesson_suggestion.py:55`.
- `engine → slot_facts → engine`: `daily_plan/engine.py:5718`; `daily_plan/slot_facts.py:50`.

These are concrete cycles at this tip, not merely historical architecture notes. Their local imports defer import execution; they do not remove graph edges. No claim is made here about the size of the full strongly connected component. The strategy expressly rules out attacking that component wholesale: `docs/specs/refactor_strategy_v3.md:1073`.

## 7. Last ten file-touching landings: change cost

**Verified counts:** each row counts all other files changed by that git commit, excluding the engine. Source/test/document categories are path categories. “Why” is read from the diff and current call sites; it is not a claim that all co-edits were caused by the engine.

| Commit | Other files | Composition | Why they changed |
|---|---:|---|---|
| `46de447004` | **17** | 6 source, 9 tests, 2 docs | Caller-time exclusions affected scheduler, admission, quick-check and objective-input readers as well as the engine. Tests cover those readers and expired checks. Current engine calls: `daily_plan/engine.py:415–446`, `:1550–1587`. **Inferred:** broad shared-rule cost, not engine-specific fan-out. |
| `88d64cf8a0` | **20** | 16 source, 4 tests/pins | Remaining observation readers moved to the effective view; tests and structure golden followed. Engine changed only by deleting an import. `daily_plan/engine.py:43–122`. **Verified:** its presence in the commit exaggerates its causal share. |
| `e0abdbe223` | **9** | 8 source, 1 test | Effective posterior reached offer/suggestion/card/input/episode/follow-up/decision-state readers. Engine state capture is one consumer. `daily_plan/engine.py:3743–3768`; test file `tests/test_evidence_reading.py`. |
| `fae3920269` | **3** | 2 source, 1 pin | Engine, `boundary_records` and `objective_chooser` coordinated failure-note keys and direct carry-stop wiring; structure golden updated. `daily_plan/engine.py:2142`, `:2817–2832`. |
| `9ade08f447` | **7** | 4 source, 3 tests | Chooser, pure choice, trace assembly and record builder repaired publication sampling and record-failure containment; tests cover choice, sampling points and failure records. `docs/reviews/refactor-bug-ledger.md:271`, `:275`. **K11-C1.** |
| `24427cb66b` | **4** | 3 source, 1 test | `objective_chooser`, `objective_job`, sidecar context and lifecycle tests joined engine plan creation in repairing carry ownership. `daily_plan/engine.py:2142`; `docs/reviews/refactor-bug-ledger.md:276`. **K11-C2.** |
| `13fe961716` | **27** | 25 source, 1 test, 1 project config | Shared refs/predicate moved to a leaf; consumers changed imports and call semantics; `test_plan_refs` checked the contract. `daily_plan/engine.py:117`; `docs/reviews/refactor-bug-ledger.md:278`. **Inferred:** vocabulary/import-boundary fan-out, not traversal-size cost. |
| `61c247b726` | **26** | 22 source, 1 test, 3 docs | E6 alternative unified offer checks/refs and added the completeness guard. Engine was one consumer among router, objective, storage and offer code. `daily_plan/engine.py:2895–2924`, `:3320–3341`; `docs/reviews/refactor-e6.md:297–385`. |
| `128128b911` | **40** | 16 source, 23 tests/pins, 1 doc | Retired `data_capture.serving`: config/retired identity handling, serving readers, successor-switch expectations and defaults/tests. `daily_plan/engine.py:118`, `:1360–1392`. **Inferred:** switch-retirement cost; not evidence for splitting the engine. |
| `0a61836d96` | **21** | 7 source, 13 tests/pins, 1 doc | Retired `curriculum.plan_uses_path`: config/retired fields, path consumers, defaults, successor/identity expectations and tests. `daily_plan/engine.py:220–232`. **Inferred:** shared configuration and pin cost. |

**Finding:** none of these counts can honestly be described as “N other files because the engine is 6,777 lines.” Two are stronger evidence of a costly engine boundary: record construction reaching fallback, and asynchronous carry ownership reaching new-plan creation. The others mostly measure shared semantics, vocabulary, or retirement obligations.

The strategy’s proof rules explain why identity and draw pins appear alongside structural work: unchanged served/persisted values, preserved draw behavior and identity bytes are explicit obligations. `docs/specs/refactor_strategy_v3.md:76–96`.

## 8. Named costs and non-findings

### K11-C1 — Choice, observation and record construction have different failure boundaries

**Verified:** ER-8’s record builder once raised after a draw; engine exception handling then served the rule fallback. The repair spans `9ade08f447` and `fae3920269`; the first touched eight files including the engine. Current code guards record construction separately and has a derivation path when the choice’s own record is missing. Evidence: `docs/reviews/refactor-bug-ledger.md:275`; `daily_plan/objective_chooser.py:757–775`; `daily_plan/boundary_records.py:152–165`; `daily_plan/engine.py:2698–2746`.

**Verified related constraint:** ER-4 shows why gathering everything earlier into one context is not automatically equivalent. Moving reads of asynchronously published cards, requests and carried values changed recorded evidence even though the served choice stayed the same. `docs/reviews/refactor-bug-ledger.md:271`.

**Inferred cost:** changes at this seam require reasoning about the draw, publication sampling, record construction and the engine’s fallback together. This is more specific than file size.

### K11-C2 — Carry ownership crosses lifecycle owners

**Verified:** ER-9 records three defects: listing a carry after starting it, failing to stop it on host close, and allowing a later session/plan trace to consume it. The fix touched the engine plus four other files. The current engine hook stops earlier-plan carries after a new plan commits. `docs/reviews/refactor-bug-ledger.md:276`; `daily_plan/engine.py:2132–2143`; git `24427cb66b`.

**Verified residual tradeoff:** the ledger says the last deferred valuation of a plan can remain censored across a new-plan transition. That is documented behavior of the fix, not a newly inferred bug.

**Inferred cost:** lifecycle changes cannot be assessed solely inside `objective_job` or solely inside `build_plan`; both ownership and publication sites matter.

### K11-C3 — Failure and branch tests reach private traversal names

**Verified:** §6 lists the actual sites. The clearest examples establish behavior around boundaries that public calls alone do not let the current tests interrupt:

- Crash after plan insertion but before first-block insertion: patch `_boundary`, then verify requested items survive recovery. `tests/test_daily_plan_review_regressions.py:766–787`.
- Failure inside a keyed pick’s serve: dynamic patch of `_serve`. `tests/test_reader_rw4b_fix6.py:170–201`.
- Assert that desktop calls never enter device-only handling: patch four private helpers in one loop. `tests/test_mobile_v2_plan.py:222–234`.

**Inferred cost:** moving or combining these helpers changes test plumbing even when the public result stays unchanged. The counts name that coupling; they do not establish that every patch is undesirable.

### K11-C4 — Effect boundaries require following callees

**Verified:** `_feasibility`’s source factory may build staged material using the repository and clock. `_reconcile_changes` can call `cold_check_serve_hold` with its default `persist=True`; that can apply retimes/withdrawals before the engine opens its own reconciliation transaction. It also updates `done_at`, `displaced_at` and `ended_at` on supplied objects. `daily_plan/engine.py:2590`, `:4044–4108`; `daily_plan/staged_frame.py:227–237`, `:395–398`; `scheduling/scheduler.py:1838–1859`, `:2047–2088`.

**Inferred cost:** proving a phase read-only, or choosing a consistent input snapshot for it, requires tracing its policy/service implementation. The existing context types do not by themselves prove that property.

### Findings that do not justify a step on this evidence

- **Verified:** nine long functions and 182 importer files describe reach and reading effort. Neither count measures a defect rate or the savings from a split. `daily_plan/engine.py:1191–1357`, `:3086–3365`; caller census in §6.
- **Verified:** the ledger’s ER-8 and ER-9 are fixed historical defects. They are evidence of seam costs, not open defects to fix again. `docs/reviews/refactor-bug-ledger.md:275–276`.
- **Verified:** E6 already measured and rejected its larger action-module design. Its stop-rule record is not authorization to repeat that design under K11. `docs/reviews/refactor-e6.md:231–264`.
- **Verified:** plain `serve=False` is a deciding path by contract, not an accidental violation of a read-only promise. The separate prefetch path has a read-only attachment contract. `daily_plan/engine.py:5327–5334`, `:5567–5576`.
- **Verified:** measurement settlement is partly outside the engine, in Today preparation and `measurement.settle`; it is not an omitted engine phase awaiting extraction. `src/learnloop_sidecar/handlers/queue.py:137–149`; `daily_plan/measurement.py:436–457`.

**Stop-rule result:** this map found named costs, particularly K11-C1 through K11-C3. It does not select a follow-on step or claim that a general file split pays for those costs.

## Not verified

- No tests, application code, model calls, network requests, database reads or vault reads were performed. No P-tests, P-shadow, P-draw, identity-pin or durability proof was run.
- Historical fixes and historical failing/passing tests are verified as statements in git and the ledger; their outcomes were not reproduced.
- The engine was read whole. Nearby interfaces and cited paths were traced; every implementation in every transitive scheduler, curriculum, diagnosis, AD, storage and router dependency was not audited.
- The read/write table names the engine’s main stores and observed downstream boundaries. It is not an exhaustive transitive SQL-table inventory.
- Import and direct-test-call counts are static. Dynamic imports, aliases passed through arbitrary helpers, runtime dispatch and indirect consumers can add reach. Only concrete import cycles were established; the full component was not recounted.
- The private-patch count follows the ratchet’s literal resolution and audited dynamic sites. The shared dynamic helper also patches other modules, so per-module counts are not additive without deduplication.
- Purity classifications assume ordinary supplied value objects and the cited implementations. Arbitrary injected callbacks can add effects.
- No claim is made about how often the costly paths occur, their latency, their runtime failure rate, or how much an implementation change would save.
- No complete semantic proof was made that a phase could move unchanged. The per-phase “yes/no” judgments describe current boundaries and obstacles; they are not a split design.
- No new learner-visible defect is established by the misleading purity/unwritten descriptions alone.
