# LearnLoop refactor strategy v3

Phase A, job 2. **Status: for the owner's review. No step starts until the owner has seen it.** Written on `refactor/map` from the map `docs/reviews/architecture-map-2026-11-08.md` (base main `a525dbcef4`), with its claims checked against the code on Nov 9. Where the map was wrong it's corrected in place, and Appendix A lists each correction.

## Summary for the owner

The refactor has 62 small steps in eleven arcs. It can stop cleanly after any arc. Nothing starts until phone V4, instruct/handoff (IH), RE0 and the test-suite branch have landed.

**What gets smaller**

| What | Today | After | Confidence |
|---|---|---|---|
| Package | 624,515 raw lines, 1,268 files | about 5-9% fewer lines and 6-11% fewer files. Most of the package is live, so it won't shrink by half | estimate |
| Upgrade code | 42 modules, about 8,900 lines | one table, about 450 lines. The old chain stays in a git tag | high |
| `config/template.py` | 4,203 lines | about 450 | high |
| Upgrade and successor tests | 34 files, 8,808 lines, 16% of test time | about 1,000 lines, under 3% | estimate |
| Whole-suite test seconds | measured at step S0 | removals and plumbing alone take off about 15-25% | estimate |

**What a change costs, before and after**

| Change | Today | After |
|---|---|---|
| A one-line default (the 40 s timeout) | 1 behaviour line, 46 digests, 12 test files | 1 line, plus 1 line in a readable file of defaults |
| A new table | 68 pinned test files, a 24-file fixture rename, 481 generated notes | about 8 files |
| A router speed-up with no version change | 615 files | about 110 |
| Swap the mixing rule | 13 source files | 1 module and its test, plus one row if it's a new tag |
| Add an action to the router | 20 source files | about 3 |

**What you'll notice**

- **`learnloop why`.** One command answers why x was chosen and not y, from the latest decision, an attempt, a block or a figure. Your four real cases are its acceptance test.
- **Failures leave a record.** A chooser crash, a timeout, a discarded answer or an exclusion all do.
- **You run some things yourself.** One read-only script over your vaults, one upgrade of each vault, and a fresh backup for the acceptance test.
- **An old backup needs the tag.** Restoring one below the oldest supported tag means upgrading it with the tagged old code first.
- **Three changes affect learning behaviour, each with a report first and a kill switch.** Probes after a miss are decided by the router (G2), one belief over locked hypotheses (G4, only if the measurements call for it), and the old difficulty scalar goes (H3-H6).
- **Next gets faster after feedback,** if F1 and F2 meet the target.
- **Screens don't change.** That's the UX overhaul's job. Anything a removal takes from a settings screen is listed for it.

**What you must decide**

Before step 1:
1. **Approve the order and the gate rhythm.** I recommend the full suite and durability once per landing batch of 1-4 steps, not per step, which would be about 60 machine-hours. Steps that change persisted meaning always land alone.
2. **One serial baseline overnight,** and one at the end. At today's test seconds it's roughly 5-8 hours of your desktop.

When its step comes (recommendations and evidence in §2.13):

3. **Oldest supported tag (D1).** I recommend the tag every live vault holds at that point, expected mvp-0.55, with the chain kept at a git tag. It needs your read-only script's output for your live and retired vaults.
4. **TUI (C7):** remove it. It has no plan view and bypasses the router; desktop and phone cover the daily journey. The one thing lost is practice from a bare terminal.
5. **Collections (C7):** keep them. The build runs on one, so nothing replaces them. The UX stage can hide the word.
6. **`projects/` (C7):** remove it if nothing is enrolled, keep it if something is. Only you know which. `learnloop project status` answers it.
7. **31 CLI commands and `experiments/` (C7):** say which report tools you still use, and whether E1 is finished.
8. **Kill switches at or below the oldest tag (D7):** remove them, except any your vaults set.
9. **Router speed target (F2):** keep "Next right after feedback no worse than mvp-0.49", remeasured after IH's prefetch.
10. **The router as the only probe decider (G2):** confirm it. A probe after a miss then arrives at the next decision, not on the feedback screen.
11. **AD into surprise (H2-H3):** this crosses firewall limits A2 and A12, so it needs your amendment after you've read the four-way replay.
12. **The table list (J1):** review it. No table is dropped without your answer.
13. **AD eta's unbounded growth:** I recommend a saturating form as its own successor after E5, not inside the refactor.

Settled since the map: RE2 is a firm step (owner, Nov 9) and RE0 lands before step 1. Not settled: RE1's placement (§2.1).

**Cost.** Roughly the size of RO0-RO6, TE2-TE3 and phone V1-V4 together: 62 implementer runs, about 30 fix rounds, about 60 Codex reviews and about 20 full-suite landings, or about 5-8 weeks of queue if usage allows. This is an estimate, not a measurement (§2.15).

**Where to stop if you need to.** After arc A (4% of the cost; every later change is cheaper). After B4 (10%; your four cases are answerable). After arc C (27%; dead code gone). After arc D (47%; history gone, tests on the real path). §2.14 lists them all.

## How this document is laid out

| § | Contents | Job 2 output |
|---|---|---|
| 1 | Diagnosis, ranked | 1 |
| 2 | The ordered steps, cost, stopping points, owner's evidence | 2 |
| 3 | The decision record | 3 |
| 4 | What not to do | 4 |
| 5 | The vault plan | 5 |
| 6 | Success measures, including every sample change's target | 6 |
| A | Corrections to the map | |
| B | One record of each fact (Nov 3 items) | |

## 1. Diagnosis

Ranked by what each costs a stage or a debugging session. Ids are the map's.

| # | Problem | Evidence I checked myself | Arc |
|---|---|---|---|
| 1 | **Failures, exclusions and joins leave no answer to "why x and not y".** No id links input to reasoning to behaviour. | `daily_plan/engine.py:2671` turns any chooser exception into `<error: Type>` with no log and no message. `Prefetch.results` (`router_runtime.py:173`) writes a timeout with no payload. `objective_chooser.py:1371` mints the decision id after the model calls. `figures/prefetch_model.py:465`'s reason never reaches the row (`prefetch.py:1090`, no reason column), and `filter_candidates` (`prefetch.py:937`) drops candidates with a bare `continue`. O1-O3, S1-S15. | B |
| 2 | **The plumbing is larger than the change, and most of it isn't protecting anything.** | All 46 snapshot digests are computed from today's schema with only the tag replaced (`config/template.py:4182`), so they hold one bit between them. Nothing in `src` reads them. 499 of router speed 2's 593 generated notes changed only commit stamps. 3,070 of the 4,304 `mvp-0.N` literals are comments, 2,319 of them in `template.py`; 285 are in code. H1, H2. | A, D |
| 3 | **History is kept alive at a cost, and the test suite mostly checks it.** | No upgrade module is reachable from replay, even through function-local imports (proof in §2.5). Yet 90 tag gates exist, and 79 of them are constant at mvp-0.43 or later. **New finding:** `AlgorithmsConfig.algorithm_version` defaults to `mvp-0.6` (`config/schema.py:18`) and `create_basic_vault` pins it (`tests/helpers.py:79`). 437 test files use that vault, and 271 of them never mention a version. Much of the suite tests a path no vault of yours has. | D |
| 4 | **The router's top layer isn't a layer.** | `_decide_objective` (`objective_chooser.py:1331`) reads the DB, mints ids, seeds, draws, flips the coin, assembles the trace and registers a background carry. `_Model` (`value.py:602`) holds the objective's ledger and the rollouts together. F1, F2, §3.3. | E |
| 5 | **Six sites answer "should we probe?", and two belief updates can disagree.** | `decide_probe` is authoritative on one lane and called with hard-coded zeros on the other, as a log field (`followup_run/router.py:111`). §4.4 of the map. | G |
| 6 | **Dead and superseded code stays,** partly because it's hard to prove dead. | The name scan missed the parameter registry's `importlib` path (Appendix A), so some "dead" modules are imported at runtime. | C, D |
| 7 | **Router speed target unmet, and R4 costs connections.** | 54 `table_info` sites in 40 files each close a pooled connection (`db/connection.py:310`). Opens per job went from 5 to 17. Numeric arithmetic is the rest (`docs/reviews/router-speed2.md:388`). D4, D5. | F |
| 8 | **The two functions that decide what's served and what's learned can't be tested without a database.** | `_compute_resolved_grade_application` (774 lines), `build_due_queue` (787 lines, with a `persist_explanations` write flag on a read path). F3, F4. | I |
| 9 | **The old difficulty scalar reaches further than its name,** and shares that name with FSRS's D. | `learner/mastery.py:758`, `adaptive_difficulty/serve_inputs.py:117`, `vault/hashes.py:41`, `goals/exam_pool.py:47`. X1-X3. | H |
| 10 | **Protection has one named authority and several decision sites.** B3. | `learner_protection.py:190`, `figures/prefetch.py:947`, V4's device eligibility and media rules. | G |

`Repository` (943 methods) and the 191-module import cycle are real costs (P1, P2), and I don't attack them head-on. §4 says why. Removals shrink both: 58 `Repository` methods have no other reference in `src` (702 lines, 39 of them used by tests), and 307 have exactly one other reference, so they move to their feature's store when a step touches them.

## 2. The steps

### 2.1 Before step 1, and the rules every step follows

**These land first, in this order, and each is assumed landed:** phone V4 (`phone/v4-reader`), instruct/handoff (`instruct/handoff`: mvp-0.55 and migration 251 are claimed; its spec's build order still has IH6, IH7 and IH4 after IH3), RE0 (`practice_attempts.active_seconds` and `attempt_cue_v1`; its migration follows 251), and the test-suite branch (`tests/audit-speed`). No tag or migration number below is claimed: `ls migrations/` and `SUCCESSOR_CHAIN` at each step give the next one.

**Marks.** `[V4]`, `[IH]` and `[RE0]` mean that branch changes files this step edits, so its step 0 re-reads them. `[T]` means the test branch's plumbing list feeds this step.

- **`[V4]`** touches `daily_plan/engine.py`, `db/repositories.py`, `reader/reader_dialogue.py`, `scheduling/device_eligibility.py`, `reader/phone_media.py`, sidecar handlers and `learnloop_mobile/`.
- **`[IH]`** touches `daily_plan/{engine,objective_chooser,objective_inputs,policy,router_chooser,router_runtime,lesson_offer,learner_action}.py`, `router_objective/{mix,trace,value,offer_report}.py`, `followup_run/`, `followup_serve/`, `router/plan_log.py`, `router/outcomes.py`, `cli/app.py`, `cli/runtime.py`, `config/`, `params/parameter_registry.py`, `activation_journal.py`, and adds `failure_share_upgrade.py`.
- **`[RE0]`** touches the attempt write path, `db/stores/router_objective.py`'s fill helper, the capture report, and the head fixture.
- **Not settled:** the RE spec's table also places RE1 before the refactor, "with IH3". The owner's Nov 9 word names only RE0, so I treat RE1 as not landed. If it lands first, it touches only `db/stores/workbench.py`'s `open_sessions`, the practice and workbench surfaces, and IH3's table. No step here depends on it.

**The test suite.** Infrastructure speed, flakes, the two owner-lane failures and usefulness are on `tests/audit-speed`, not here. This strategy keeps only what plumbing and removals do to the suite: version pins, frozen digests, the head fixture, generated notes, tests of removed features, and the default test vault (D2). That branch sends a plumbing list; S0 folds it into A2, A3, D2 and D3.

**Every step:**
- **Size:** one review-and-gate cycle.
- **Who:** an Opus implementer in a worktree, then a read-only Codex review of the diff, then the gate. "Verify" names anything beyond that, and the owner only where stated. Nothing in this document is yet approved to run.
- **Gate per step:** targeted tests under the memory cap, `lint-imports`, the vault validators, and the step's named proof.
- **Gate per landing batch:** the full suite and durability once, on the merged tree (owner decision 1).
- **Comments:** when a step touches a function, it follows the convention below, and only there. No sweep.
- **Vault:** the step fixes each note it names, and any other note it finds it has made false. The large rewrite stays last (§5).
- **Deleting:** before deleting anything, its step 0 proves it again at that tip: no import (including function-local and `importlib`), no string dispatch (`METHOD_REGISTRY`, Typer decorators, `MODULE_INVENTORY`, `_reg_const`), no frontend or phone caller, no replay, rebuild or upgrade path. A claim that doesn't hold moves the row to the owner's list. It never gets deleted anyway.

**The comment convention (C1, C4).** A comment says what breaks without this line, or why the obvious approach is wrong. It doesn't name a review round, a ruling or a stage; those belong in the commit and `docs/reviews`. A function over 100 lines starts with two or three sentences on its approach. `learner/mastery.py:783` and the note at `db/connection.py:310` are the models, though the second should lose its ruling number.

**Proofs, named once:**
- **P-tests:** the targeted tests, plus the fail-first test where a bug or silent path is fixed.
- **P-shadow:** `learnloop rebuild --shadow --json` before and after on backup-API copies under `fixtures-local/`, with the semantic projection identical and `schedule_effects` empty. Copies come from a fresh backup when the owner supplies one. Until then, the Nov 3 copies upgraded to the head tag.
- **P-draw:** the router speed stages' draw-for-draw harness: mixture seed pinned, fixed draw count, fake LLM and Decider. LLM requests, gates, prompts and every table must match the base commit (`docs/reviews/router-speed2.md`, "Identity").
- **P-playbook:** all of `docs/algorithm-change-playbook.md`: a successor tag, a kill switch that serves the predecessor exactly, the upgrade row, table roles, replay tests, a shadow rebuild on copies with mastery, facet and scheduling deltas reported before landing, and the fixture path.

**Environment rules for every step.** Scripts outside pytest run under an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No live or paid model calls. Copies only through `learnloop.db.copies`. Agents never open live vaults: the owner runs anything that reads them and pastes the output.

### 2.2 S0: re-baseline on the landed tip

**S0. Baselines and map refresh** (size M, plus machine time). No change to `src`.
- **Problem:** the map predates four landings, its `IH:` and `V4:` rows are from diffs, its §12 names an unresolved numeric-seed conflict at IH's landing, and item 13 has no serial or durability baseline.
- **Does:** reruns the map's sizes on the tip; re-derives the `IH:`, `V4:` and RE0 rows; confirms how IH's landing resolved `numeric_seed`; takes the plumbing list from `tests/audit-speed`; records serial, `-n 8 --dist worksteal` and `-m durability` times with the same commands the end measure will use (reusing that branch's numbers if they're from this tip); records every §6 measure, including time-to-locate.
- **Files:** `docs/reviews/refactor-baseline.md`, `scripts/refactor_measures.py` (one script, so S0 and Z2 measure the same way), map corrections.
- **Proof:** none needed. **Verify:** the Nov 7 figures (59:22, 27,650 test seconds) stay as history, not the "before", because the test branch moves them.

### 2.3 Arc A: stop taxing every later change

No behaviour changes, and every later step gets cheaper, so this comes first, even ahead of the silent failures. If B1 ran first, its new table would pay the full 68-file cost.

**A1. Generated notes stop churning** (S).
- **Problem:** H2. 499 of router speed 2's 593 generated notes changed only `source_commit`, `source_commit_timestamp`, `source_worktree_state` and their body rows.
- **Files:** `_scripts/{module,desktop,db}_generate.py`, `module_validate.py`, `desktop_validate.py`, `db_validate_reference.py`; `Reference/` regenerated once; `validate_vault.py`'s rule stays for hand-written notes.
- **Deletes:** the per-note stamps in generated notes. One `Reference/_generated.md` holds the commit they were generated at.
- **Adds:** nothing else. **Decide in step 0:** the remaining 94 were real changes, mostly config-field notes and per-module test lists. Drop the test lists too if they're the bulk.
- **Proof:** the validators pass; a regeneration on a clean tree gives an empty diff; regenerating after a one-line source change touches only that module's note. **Vault:** the notes on documentation generation.

**A2. A head fixture with a stable name** (M) `[IH] [RE0] [T]`.
- **Problem:** H2. Each migration renames 24 files (22 byte-identical) and edits 68 test files. 70 lines in 68 test files plus 3 scripts name the path; CLAUDE.md says 5.
- **Files:** `fixtures/migration_head_<N>/` to `fixtures/migration_head/`; `tests/helpers.py`; the 68 test files; `scripts/sanitize_migration_head_fixture.py`; `_scripts/db_generate_reference.py`, `db_validate_reference.py`; `tests/test_public_tip_guards.py`; `tests/test_tracked_fixture_databases.py`; `CLAUDE.md`; the fixture's `README.md`.
- **Deletes:** path literals, and pins like `max(applied_versions(HEAD)) == ... == 250` or `names[247] == ...`.
- **Adds:** two names in `tests/helpers.py`: `MIGRATION_HEAD_FIXTURE` and `migration_head()`, read from `migrations/`. They replace 70 literals.
- **Proof:** one test keeps the real check: the fixture's applied maximum equals the migrations' maximum. Pins of the form `[218, 219, ...]` become ranges to the head. The fixture stays in rollback mode. G8 still passes. **Vault:** Inspect Persistent State, State and Persistence.
- **Target:** a new migration changes `state.sqlite` and the README in the fixture, and no test pins.

**A3. One readable file of defaults** (M) `[IH] [T]`.
- **Problem:** H1, H4. 46 digests hold one bit. 49 test files reference a digest or snapshot, each with a growing preamble that undoes later defaults (`dumped["router"]["timeout_seconds"] = 8.0`).
- **Files:** `config/template.py`, `config/schema.py` (history comments), `algorithm_versions.py:877`, the 48-49 test files, `docs/algorithm-change-playbook.md` step 4.
- **Deletes:** `DEFAULTS_SNAPSHOT_BY_ALGORITHM` and `defaults_fingerprint_for_version` (no `src` reader; checked), `LEGACY_DEFAULT_CONFIG_TEXT` (no `src` reader, 2 test files; re-check them), every digest test and its preamble, and about 2,000 lines of history comments in `schema.py` plus 3,300 in `template.py`. A one-line "why" stays where one exists.
- **Adds:** `tests/goldens/effective_defaults.toml`: every effective key and value, sorted, generated by one helper and compared by one test. A changed default shows up as that line in review. This keeps the tripwire ("no silent default change") and replaces 46 hashes nobody can read.
- **Check:** a test that meant "this key has this value" keeps a direct assertion. `classify_config_path` tests stay.
- **Proof:** the effective config before and after is identical, compared whole. **Vault:** Algorithm Versions and Reproducibility, generated config notes.
- **Target:** the 40 s change is 1 schema line, 1 golden line, at most 1 test literal, and 1 generated note.

**A4. Correct what's dangerous now** (S).
- **Problem:** §8.1: the privacy note says PDFs stay local while `auto` uses a hosted service when a key is set. CLAUDE.md's suite time is stale (N2).
- **Files:** Content Pipeline, Import Canonical Sources, Privacy and Trust; `CLAUDE.md`; `README.md` if it repeats it; Developer Map gets a "where to change what" table from §6 (replacing its scheduler-first row).
- **Proof:** read against `ingest/extractors/__init__.py:84`. **Verify:** Codex, against the code.

**Stopping point 1.**

### 2.4 Arc B: why x and not y (item 11)

Design in §3. Order is by debugging value, with the map's silent failures first. Each step adds its `why` output and a test that stages the failure with fakes. None changes what's served: writing a record is never allowed to change a decision, and a record that fails to write logs a warning with the trace id and moves on.

**B1. The record, the trace id, the entry point** (L) `[IH] [V4]`.
- **Problem:** O1, O4; breaks 1-3 of §4.3.
- **Files:** `Decisions/ADR-017` (written first); new `src/learnloop/provenance.py` (a leaf, like `activation_journal`); one migration; `db/table_roles.py` (RECEIPT); AD's `protected_tables.py` and `column_classes.py`; `db/stores/provenance.py`; `ai/execution.py` and `record_model_event`; `learnloop_sidecar/server.py:55`, `logging.py:84`; `learnloop_mobile/runtime.py:250`; `learnloop_mcp/server.py:364`; CLI root; `cli/app.py:2407`.
- **Deletes:** `why`'s `sync_vault_state` and `run_startup_maintenance` calls (it becomes a pure read), and the JSON join for new rows.
- **Abstraction:** one dataclass, one table, one ContextVar, one read function. It replaces 4 entry points and the JSON join, and it's the only way the four cases become answerable (§3.6).
- **Proof:** P-tests; P-shadow (a new receipt changes nothing replayed; `decision_records` is unreachable from replay, by a test on the import closure and the SQL); P-draw. **Vault:** Add ADR-017; Inspect Persistent State.

**B2. Router failures** (M) `[IH]`. Case 1.
- **Problem:** S1, S2, S3, S5, S6.
- **Files:** `daily_plan/engine.py:2671`, `router_runtime.py:173`, `:605`, `:695`, `objective_chooser.py`, `router_chooser.py:342`.
- **Does:** a chooser crash writes `kind=plan_block, status=fallback, rule=chooser_error`, with the exception's type and location and each model's result summary. Each component gets a `model_answer` record, including `timeout`, with the configured wait. `why` lists any receipt in the trace that finished after the decision as discarded.
- **Deletes:** the misleading "Pure" on `decide` (F10). **Proof:** P-draw; fail-first tests for crash, timeout, late answer. **Vault:** Scheduling and Selection's router paragraph.

**B3. Forced items, withdrawals, boundary failures** (M) `[IH] [V4]`. Case 2.
- **Problem:** S12, the `forced_items` row, §4.1's check, offer and AD-unavailable rows, break 1.
- **Files:** `daily_plan/engine.py:4815-4832`, `:2896`, `:3133`, `:3179`, `:4930`, `:4947`, `:5032`, `lesson_offer.py:370`, `router/decisions.py:100`, `adaptive_difficulty/denial_log.py:98`, `serve_eligibility` caller at `engine.py:5069`.
- **Does:** `offer_withdrawn` names the forced items and their workflows, and the next decision's `parent_id` points to it. Plan decisions name their triggering attempt. AD denials move from the JSONL file to records, if nothing else reads the file.
- **Note:** IH2 removes this withdrawal when its switch is on (a contest decision replaces it; `WITHDRAWN_FORCED` stays for the switch's off path). **Proof:** P-draw. **Vault:** none beyond generated.

**B4. Figures** (M). Cases 3 and 4.
- **Problem:** S7, S8, S9, S10; `figures/service.py:2513`.
- **Files:** `figures/prefetch.py:937-960`, `:1056-1110`, `:1279`, `prefetch_model.py:465`, `service.py:2496-2560`, `spec.py:804-860`, `routes.py:552`.
- **Does:** a `figure_prebuild` record per decided candidate carries the rule, EU, propensity and measured-wait summary. A filter pass records its exclusions by rule, with counts and up to 10 keys, protection exclusions included. `figure_author` per attempt has typed problem codes (`prediction_invalid`, `status_invalid`, `label_text`, `model_failed`, `verification_failed`), so attempt 1's problems survive. The RNG's seed is drawn once and recorded, which changes nothing statistically.
- **Check in step 0:** whether `owner_kind NOT LIKE 'prefetch%'` excludes pre-builds (the map couldn't verify it). If it doesn't, that's a measurement bug: report it to the owner rather than fix it silently, since it changes EU.
- **Proof:** P-tests; a figure golden shows no change in prompts. **Vault:** none yet; figures have no note (§5).

**Stopping point 2.** The four cases answer from new rows.

**B5. Decider and spend refusals** (S) `[IH]`.
- **Problem:** S11, S13, S14; refused router requests leave no call row (`router_runtime.py:396`); `ai/spend.py:188`.
- **Files:** `decider_judgments.py:255`, `:279`, `db/stores/router.py:140`, `followup_run/router.py:127`, `router_runtime.py`, `figure_admission.py:346`.
- **Proof:** P-tests, including past bug B2 ("no Decider routed" now leaves a record).

**B6. Scheduler and serving exclusions** (M) `[IH]`.
- **Problem:** O3, S15, daily-loop bug 2's question, break 4 (`decision_receipt_id` overloaded).
- **Files:** `scheduling/scheduler.py:1343`, `:1831`, `scheduling/serving_exclusions.py:131`, `router/decisions.py:60`, `learnloop_sidecar/handlers/remediation.py:191`, `followup_run/admission.py:417`, `followup_run/jobs.py:431`.
- **Does:** one record per slate with exclusions counted by rule, and up to 10 ids per rule. Scheduler reads with `persist_explanations=False` write none, unless reached from a serve. The two meanings of `decision_receipt_id` get separate parameters. Existing rows keep their meaning.
- **Storage:** this is the largest writer; the step measures bytes per week on a synthetic copy-shaped journey. **Proof:** P-draw, P-shadow.

**B7. The attempt chain** (L) `[RE0]`.
- **Problem:** breaks 1, 5, 6; §4.1's grading, held grade, diagnosis, VOI, follow-up value and causal rows, several read by outline only.
- **Step 0 reads the (o) rows through:** `attempts/grading.py:1570`, `diagnosis/followups.py:995`, `diagnosis/voi_stopping.py:2176`, `diagnosis/probe_episodes.py:1612`, `followup_serve/workflow.py:165`, and traces where router and AD outcomes are written after an attempt (§2.3's open item).
- **Does:** the grade's trace carries through `post_attempt_jobs` and the diagnosis to the follow-up. A held grade gets a record when the hold first applies, while `held_grades.py:62` stays the predicate. Grading records carry ids, the verdict class and the versions, no answer text.
- **Proof:** P-shadow, and a blindness test: no grader context can read `decision_records`.

**B8. The rest, by value** (M, may stop early).
- **Scope:** teacher lessons and checks, Reader retrieval, ingest routing, AI route fallback, retries, re-read and alias resolution, curriculum path, FSRS rating and elapsed.
- **Rule:** read each first. Add a record where a real question can't be answered. For the rest, write down in ADR-017 why not. The goal is an inventory with no silent gap, not a record everywhere.

**B9. One entry point, acceptance** (M).
- **Files:** `learnloop_sidecar/handlers/why.py` (read-only RPC for the UX stage's glass-box view; not on the phone allowlist), `cli/router.py:311` and `cli/app.py:1841` become thin views over the same reader, `tests/test_why_cases.py`, `tests/test_why_real_cases.py`.
- **Proof:** §3.6's acceptance, on the owner's fresh backup. **Verify:** a Codex reader given only `why --json` output and the questions, no code, answers the four cases and the past-bug sample. **Vault:** Workflows gets one "Debug a decision" note; Reference regenerated.

**Stopping point 3.**

### 2.5 Arc C: delete what's proven dead

No change at any fixed input, and no learner reach except where stated. Each removes its tests first, so its seconds saved are recorded in the landing note. Settings screens that lose a backend are listed for the UX stage.

**C1. Dead modules with no registry tie** (M) `[T]`.
- **Deletes:** `diagnosis/causal_migration.py` (121 lines), `diagnosis/remediation_intake.py` (34), `substrate/compat/card_outcome_replay.py` (261), `scheduling/prequential.py` (276), `sim/interval_width_viability.py` (150), the undecorated `eval_command` (`cli/app.py:4040`), the 64 leaf definitions (614 lines), and 58 `Repository` methods (702 lines) after re-checking each. Their test files go with them (`test_causal_migration`, `test_interval_width_viability`, parts of `test_misconception_transitions_intake`, and so on).
- **Doesn't delete:** `client_contract` (a generator its test runs), `sim/ad_gates` and `sim/ad_synthetic` (the library of `test_ad23_sim`, the suite's slowest file, 734 s). Whether AD23's gates move to a marked lane is a test-usefulness question; it must be handed to `tests/audit-speed`, whose brief excludes the deprecated inventory (the map listed `ad_gates` there, wrongly).
- **Appendix C:** 715 definitions are candidates. Beyond the leaf list and the 98 test-only definitions (2,754 lines, deleted only when their test proves nothing else), a definition goes only if a step's own reader confirms it. This step doesn't work through the list.
- **Proof:** P-tests, `lint-imports`, the closure script from §2.8. **Vault:** module notes regenerated; ADR-012's froze-it note.

**C2. Registry-tied modules** (M).
- **Problem:** `MODULE_INVENTORY` (`params/parameter_registry.py:107`) imports these at `resolve_effective` through `importlib`, so "0 imports" was wrong. Deleting a module without its entry raises at registry refresh.
- **Candidates:** `substrate/compat/substrate_cutover.py` (721; 2 entries), `scheduling/progression_policy.py` (103; 3), `scheduling/progression.py` (341; 3), `scheduling/reentry_adapter.py` (287; 2), `scheduling/predictive_targets.py` (165; 1), `scheduling/short_session.py` (117; 0 entries, but named by `open_world_gate`'s `_has_attrs` check, to read).
- **Files:** those, `parameter_registry.py`, `open_world_gate.py`, `test_architecture.py`, `test_progression.py`, `test_activity_contract_extensions.py`, `test_laddered_stems.py`, `test_reentry_short_session.py`.
- **Check in step 0:** `refresh` loops over `decision_specs()` and leaves a removed spec's stored row in place, so it stays readable. Confirm `freeze_manifest` and `doctor` tolerate that. A removed decision parameter changes the next frozen manifest only.
- **Proof:** P-shadow; registry tests. **Vault:** generated.

**C3. Calls and keys nothing uses** (M) `[V4]`.
- **Deletes:** the map's RPC rows (`curriculum.cover_job`, `reader.followups_plan`, `get_practice_coverage`, `list_vault_epigraphs`, `source_outcomes`, `rpc.health`, and `curriculum.cover` once word-matched: a substring search hits `curriculum.coverage_correct`), the Tauri commands with no TS string, the 44 client methods except `clear_session_checkpoint` and `get_attempt` (allowlisted for the phone), and the config keys read by nothing (`locks.facet_lock_mass`, `locks.facet_surface_groups`, `merge_locked_facets`, `discrimination_min`, `discrimination_max`, `plan.pre_questions`, `target_error_type`, `lo_mastery_delta`).
- **Check:** unknown keys in an old TOML must stay harmless (`load_vault` on a config still setting each one). The owner's script (D1) prints any set in a real vault.
- **Proof:** vitest, `npm run typecheck`, the phone's contract test. **Vault:** Desktop notes regenerated.

**C4. The Codex transport** (M).
- **Problem:** ADR-011 says retain; the code refuses at every entry first. The owner decided on Oct 21 to retire it in T2.
- **Deletes:** `ai/providers/codex_http.py` (248), then `ai/providers/codex.py` (2,116) and what of `codex_lockdown.py` (1,325) only guards it, `CodexConfig` (`config/compat.py:33`), `ai.agent_harness_opt_in`, the retired routes (`field_llm_probability`, `proof_check`).
- **Check:** old configs naming a Codex provider must get the existing clear refusal, and the owner's script prints any. Replay reads `grading_source` only, so stored rows stay readable. Prove it by test.
- **UX list:** `SettingsScreen.tsx:211`, `App.tsx:737`, `CommandPalette.tsx:127`, fallback labels. **Vault:** AI Architecture's provider table; ADR-011 superseded.

**C5. Golden Path** (L, split if the review finds it large) `[IH]`.
- **Problem:** compile-time off (`SHOW_GOLDEN_PATH`), 39 RPCs, tables seeded by migration (T3), `bridge_active` (`daily_plan/policy.py:36`) still read by `router_active` and the handler.
- **Files:** `screens/GoldenPathScreen.tsx` (1,276), `components/goldenpath/`, `fixtures/goldenpath/`, `keymap.ts`, `App.tsx`; `handlers/golden_path.py`, `ladder.py`, `diagnostic.py` (check: some `diagnostic.*` may serve other screens); `daily_plan/policy.py`.
- **Check:** `DoseOffer.tsx` and `ExemplarConfirmDialog.tsx` mention golden names; `bridge_active` also carries the `router.enabled` switch `router_active` needs, so its check moves, not goes. `test_p2_acceptance` goes only for what it uniquely proves.
- **Tables:** left in place for J1. **Proof:** vitest, P-tests. **Verify:** Codex greps for a learner route left. **Vault:** User Journey Map.

**C6. P4 controller, kinship, shadow components** (M, conditional).
- **Problem:** the map marks the row unverified. `scheduling/controller_cutover.py` (653), `controller_store.py` (512), `kinship_feature.py` (526), `shadow_components.py` (308); DESCOPED U-025, U-026; CLI group `controller`; references from `staged_policy.py`, `randomization_layer.py`, `router/decisions.py`, `controller_snapshot.py`.
- **Step 0 decides:** what's actually reached on the plan path. `controller_snapshot` probably stays. Anything live stays and the row moves to the owner. If C5 removed the only caller of `controller_cutover`, it goes with its registry entry. **Proof:** P-draw, P-shadow.

**C7. What the owner chose** (M, conditional on decisions 4-7).
- **TUI, if removed:** `tui/` (2,471), `app_launch.py`'s launcher, `cli/app.py:4033`, `textual` from `pyproject.toml:14`, the `tui-keeps-the-open-queue` contract, 16 test files, `README.md:312` (`learnloop today`).
- **`projects/`, if removed:** the package (5,300), `cli/project.py`, `ops/startup.py:13`, `handlers/queue.py:22`, `[project]` config and routes, 16 test files.
- **`experiments/`, if E1 is finished:** 36 files, 14,245 lines; results stay in `docs/`.
- **CLI commands:** those the owner names.
- **Proof:** P-tests, CLI help snapshot. **Vault:** Adapter Architecture, Package Boundaries, README.

**J1. The table review list** (M; arc J's first step, run here because the removals above name the readers).
- **Problem:** item 12; T1-T4. 396 tables: 24 retired but still read, 1 dead.
- **Files:** `scripts/table_review.py`; private output under `fixtures-local/table-review/`; the tracked part is `docs/reviews/table-review-<date>.md`, names and code facts only.
- **Does:** for each table: role, row counts and newest date on fresh copies, DB file sizes, readers and writers at this tip, replayer or upgrade, feature, class, and whether readers tolerate its absence. It re-reads the COMPAT-labelled live tables (`practice_item_state`, `hypothesis_sets`) and corrects their role in `db/table_roles.py`: step 0 checks what each role changes in rebuild.
- **No table is decided here.** It lists; the owner answers. **Needs:** a fresh backup. Nov 3 predates everything since migration 238.

**Stopping point 4.**

### 2.6 Arc D: history

**What I proved.** An AST closure over every import, function-local included and `TYPE_CHECKING` excluded, starting from `substrate/rebuild_orchestrator`, `shadow_rebuild`, `canonical_projection`, `attempts/attempts`, `daily_plan/engine` and `ops/doctor`, reaches 485-579 modules and none of the 42 upgrade modules. The only `importlib` paths are the registry's `MODULE_INVENTORY`, `valuation`'s named gaps, `open_world_gate` and the fetchers, and none names an upgrade. So replay doesn't import them.

**What they're still needed for:**
1. **The CLI's `upgrade`.** Every link is its next link's predecessor.
2. **Every writing open.** The CLI and sidecar install `phone_probes_upgrade.complete_interrupted_activation`, which hands a journal naming an earlier link down the chain, back to mvp-0.33. Without a journal it checks one path and returns.
3. **Three helpers.** `UpgradeResult`, `rewrite_algorithm_version`, `publish_algorithm_version`, `write_activation_journal`, plus two constants that `learner/recall_calibration.py:16` imports.
4. **Old vaults.** The retired vaults' tags are unknown. A restore from an old backup needs an upgrade path.
5. **Tests.** 190 test files name a tag at or below mvp-0.42. 62 call an upgrade. 34 are upgrade or successor files.

**Not safe to prune by tag:** the row readers that read old rows by shape or marker stay whatever the tag (`substrate/canonical_projection.py:736`, `attempts/attempts.py:1522`, `:1529`, `:1540`, `substrate/recurrence_groups.py:447`, `db/repositories.py:26949`), and `fixtures/mvp017_route_check_replay` pins one.

**D1. The oldest supported tag** (M) `[IH]`. Owner's decision 3.
- **Before any code:** the owner runs `scripts/vault_report.py`, read-only and small, over live and retired vaults: each vault's tag, whether an activation journal stands beside its database, and which config keys it sets that C3, C4 or D7 would remove. It prints no learner data. The owner upgrades each live vault to the floor, which they must do for mvp-0.55 anyway.
- **Files:** `algorithm_versions.py` (`OLDEST_SUPPORTED`), the opener (`vault/repository.py`, `activation_journal.py`), `substrate/shadow_rebuild.py:195`, an annotated git tag `pre-floor` (the owner or orchestrator creates it; agents don't push).
- **Does:** a vault below the floor is refused at open, naming the tag and the two commands that upgrade it there. A journal naming a link below the floor is refused the same way. A shadow rebuild can no longer be forced below it. New `algorithm_version` default stays until D2.
- **Proof:** a Nov 3 copy, upgraded in a worktree at `pre-floor`, then opened, doctored and shadow-rebuilt on tip with no differences; a refusal test. **Verify:** owner confirms the retired-vault route is acceptable. **Vault:** ADR-018 (the floor), Algorithm Versions.

**D2a. The default test vault moves to the head** (L) `[T]`.
- **Problem:** finding 3 in §1. Basic-vault tests run the path below every real vault's tag, so later removals would delete what they test while leaving the real path untested.
- **Measured:** a random 40 of the 271 files, run with the pin changed by a scratch plugin (no source edited): baseline all green; at mvp-0.43, 11 of 441 tests failed in 5 files of the sample plus 2 in others (7 files); at mvp-0.54, 14 of 441. So expect very roughly 50-60 files and a few percent of their tests. This sample is small, and other files may be worse.
- **Files:** `config/schema.py:18`'s default (to the floor or a required field), `tests/helpers.py:21`, `:75-79`, the basic vault's facets (it's "the pre-KM2 contract"), `use_init_algorithm_version`, the failing tests.
- **Rule:** a failing test is fixed to assert the same behaviour on the real path, or, if it only ever described the old path, deleted with a line in the landing note. An assertion is never edited to whatever the code now says without reading why it differs. A difference is a finding.
- **Proof:** P-tests; the Codex review reads every changed assertion. **Vault:** Testing.

**D2b. Tests that name old tags** (L) `[T]`.
- **Problem:** 190 test files name tags at or below mvp-0.42, 143 use `set_algorithm_version`. Some mean "the predecessor serves exactly": those go when their switch goes (D7). Others just needed a tag.
- **Does:** re-tags the second kind to the floor. Batch by directory of behaviour, not all at once. Split further if the review needs it.
- **Proof:** as D2a.

**D3. The upgrade table** (L) `[IH]`.
- **Problem:** Z1, P5, X-clones: `_activate_as_writer` in 19 modules, `_upgrade` in 21, `complete_interrupted_activation` in 20. The 12 newest links differ only in the name of their upgrade function, and the ones behind them differ by little (checked by normalized AST). `interval_factor` is the real exception: a whole-vault rebuild. `cli/app.py:108` has a 180-line docstring and a 40-branch `if`. 23 tests pin `inspect.getsource(...)` to name the latest module.
- **Files:** new `ops/upgrades.py`; `algorithm_versions.py`; `cli/app.py`; `cli/runtime.py:138`; `learnloop_sidecar/context.py:810`; `activation_journal.py`; `learner/recall_calibration.py:16`; the tests.
- **Deletes:** all 42 modules (about 8,900 lines; `recurrence/upgrade.py` and `ops/vault_upgrade.py` included), about 400 lines of `cli/app.py`, most of 8,808 lines of tests, the chain-walking tests (Z1).
- **Adds:** one table: `Link(tag, activate)`, where `activate` is `idempotent_projection` or `whole_vault_rebuild`, or a function if a link needs one. It replaces 42 clones with one transaction, journal and publication. A successor adds a row.
- **Keeps, with tests:** refuses jumps, journal before publication and publication last, recovery after death at each point, idempotent re-run, an old config readable when preparation fails (playbook step 3 and 8), the AD guard's denial mark.
- **Proof:** the kept tests run parametrized over each link on one small fixture, instead of walking from mvp-0.9. A fresh-copy upgrade through the table gives the same projection as `pre-floor`'s code. **Vault:** Add ADR-018's table; Version Registry; playbook steps 3 and 8.
- **Target:** a new tag is 1 constant, 1 row, 1 test row.

**D4. Constant gates: attempts, mastery, grading** (L) `[IH] [RE0]`.
- **Problem:** with the floor enforced, a gate on a set that holds every tag at or above the floor has a dead else-branch. By AST against the real chain, 79 sites at floor mvp-0.43, and 90 at floor mvp-0.55, in 47 sets. (The map's "about 40 pure, 38 paired" isn't reproducible; my own syntactic split found only 10 paired, and it misses some, such as `daily_plan/policy.py:42`. Each site gets read.)
- **Files:** `attempts/` (17 sites), `learner/` (6), and `held_grades`-adjacent callers.
- **Deletes:** the gate and its else-branch. Where a gate pairs with a kill switch, only the tag half goes; the switch waits for D7.
- **Proof:** P-shadow identical on every copy, and P-tests at the head. **Vault:** Attempt Processing, Learning System where they state a removed branch.

**D5. Constant gates: substrate, rebuild, doctor** (L).
- **Files:** `substrate/` (13 sites, including `canonical_projection.py:309`, `:319`, `:652`, `:654`, `:712`, `:1175`), `rebuild_orchestrator.py:443`, `ops/doctor.py` (5), `db/repositories.py:26949`'s gate half, `substrate/compat/` once unused.
- **Deletes:** the pre-canonical projection path (LEGACY-ONLY row), `facet_uncertainty` and `evidence_facet_recall_state` writers (`attempts/attempts.py:3322`) if the path is their only one, for J1's list.
- **Keeps:** every row reader that reads by shape, and `activity_backfill` (`rebuild_orchestrator.py:311`: rebuild imports it). `fixtures/mvp017_route_check_replay` must still pass.
- **Proof:** P-shadow on all copies; the replay fixture; rebuild-equivalence tests. **Verify:** Codex specifically hunts for an old-row reader removed by mistake.

**D6. Constant gates: the rest, and the sets** (M) `[IH] [V4]`.
- **Files:** `daily_plan/` (8), `diagnosis/` (4), `placement/` (4), `field/`, `goals/`, `instructional/`, `content/proposals/`, `serve_eligibility.py`, `decider_judgments.py`.
- **Deletes:** every version set no gate uses, and tag constants except where stored data names them (`substrate/recurrence_groups.py:447`).
- **Proof:** P-draw, P-shadow. **Target:** `mvp-0.N` in code strings falls from 285 to under 60.

**D7. Kill switches at or below the floor** (L, in batches). Owner's decision 8.
- **Problem:** the 27 named switches, plus any from 0.44-0.55 the floor covers: each off-branch keeps predecessor code alive at any tag.
- **Rule proposed:** a switch goes when every vault is past its tag and no vault sets it. `replay.ledger_bounded` needs reading first (it affects rebuild results, `attempts/attempts.py:1378`).
- **Also goes:** the pre-eligibility cold lane and hold (`scheduling/scheduler.py:1831`, `:2018`), `RouterChooser`'s mixture path and `StagedChooser` if `router.mode` and the floor leave them unreachable, with their tests, "predecessor exactly" goldens and D2b's remaining tests.
- **Keeps:** every switch above the floor; the staged rule as the failure fallback.
- **Proof:** P-draw with switches at default; P-shadow. Removing a switch changes behaviour only for a vault that set it, and the owner's script shows none do. **Vault:** Config generated; ADR-018 states the rule.

**Stopping point 5.** The largest removal is done, and the tests run on the served path.

### 2.7 Arc E: the top layer (items 6 and 10; Nov 5)

**Target.** A short module says what's optimized and how the choice is made. Everything else (sensors, memory, rollouts, persistence, jobs, traces) sits beneath it. No registry or plugin; plain modules and small dataclasses. All steps here use P-draw at fixed draw counts, and P-shadow, and change no value.

**E1. Switches split** (S) `[IH]`.
- **Problem:** B1, leak 10. `router_objective_switches.py` (390 lines, 30 importers) mixes kill switches with AD's availability predicate; `attempts/attempts.py:4719` reads it.
- **Files:** that module, D7 having shrunk it, its importers. The availability predicate moves beside AD's reader; evidence paths stop importing a router module.

**E2. The choice, pure** (L) `[IH]`.
- **Problem:** F1. There's no way to call "given these inputs, choose".
- **Files:** new `router_objective/choose.py`: `choose(ChoiceInputs) -> Choice`, holding the failed-policy logic, effective weights, the draw, the coin, the why and the guard; `objective_chooser.py:1331-1490` becomes reads, then the call, then writes.
- **Abstraction:** one input dataclass and one result, which together remove the seed-pinning through the runtime in tests. The result carries the `DecisionRecord`.
- **Keeps:** IH5's failure share, IH2's contest, exact propensities, RO5's coin order (the mix's draw, then its own uniform).

**E3. Job control and the clock** (M) `[IH]`.
- **Problem:** F2, D1, leak 1, 2. Threads, deadlines, carries and `_await` share a module with the choice, and draw count depends on wall clock in a way only the job needs to know.
- **Files:** `daily_plan/objective_job.py` (from `_objective_job`, `run_numeric`'s scheduling half, carry helpers, `_drain_carry`), seeds into one small module (`numeric_seed`, mix seed, coin seed, with why each differs).
- **Removes:** `__import__("learnloop.clock", ...)` at `objective_chooser.py:1594`, `entry.__class__.__name__ == "_NoModels"` checks.
- **Keeps:** availability never depends on the LLM (F1 of RO4's review).

**E4. Trace assembly leaves the chooser** (M) `[IH]`.
- **Problem:** leak 3. `_trace` and `_offer_trace` know every action kind.
- **Files:** `router_objective/trace.py`, `objective_chooser.py:949-1170`. Each candidate supplies its own trace row.

**E5. The objective apart from the rollouts** (L) `[IH]`.
- **Problem:** leaks 4, 5; the "term" row of §3.3.
- **Files:** `router_objective/value.py` (1,651 lines) becomes `objective.py` (the terms, `_terms`, the ledger's meaning; readable in one sitting), `rollouts.py` (`_Model`, sessions, draws), `ad_link.py` (`AdLink`, `LessonCurve`). `Topic`, `Inputs`, `Action` go to `objective_inputs` types.
- **Proof:** `evaluate(...)` is byte-equal at fixed draws on recorded inputs, for every option combination. **Vault:** a new Router Objective note, short, for ADR-017's readers; the big write-up stays last.
- **Target:** change a term is `objective.py` and its test.

**E6. An action is one place** (L) `[IH]`.
- **Problem:** add-an-action touches 20 files; leak 9 (lessons valued in the chooser, built in `lesson_offer`, withdrawn in the engine).
- **Files:** `router_objective/actions.py` with one function per action kind: its candidate, its rollout step, its trace label, its reversibility. A plain `match`, not a registry. `daily_plan/{lesson_offer,types,records,view}.py`, `router/{plan_log,requests,why}.py`.
- **Limit:** engine traversal stays where it is, except offer withdrawal. Stop if it adds more than it removes, measured by the TE3b replay: count files for a lesson-offer-shaped addition on a scratch branch.
- **Serves:** TE4, RE3, RE5.

**E7. A sensor is one definition** (L) `[IH] [RE0]`.
- **Problem:** add-a-sensor has two destinations with no shared definition (11 and 7 files), and H3's builders.
- **Files:** `daily_plan/sensors.py`: named facts read at a boundary, `as_of` included. `router_card.py`, `router/card.py`, `objective_inputs.py`, `router_objective/{trace,decision_state,tail_data}.py` read from it. Then `learner_signals(connection, lo, at)` for the other context builders where a signal is shared (`diagnosis/split/context.py`, `tutor/tutor_qa.py:2090`, `hints/service.py:775`), each choosing by name.
- **Check:** input hashes that include the card must not move at the same inputs. **Abstraction:** two functions; they replace 11 edits for TE0-shaped changes.

**E8. Performance switches out of identity** (M).
- **Problem:** B8. `SEED_NEUTRAL_SWITCHES` exists because serving switches enter the numeric seed and RO6's generator.
- **Does:** the identity names only switches that change values. Since this moves RO6's generator id once, it's a recorded change point under P-playbook if the review finds it changes persisted meaning. It lands alone. Must precede F2, so speed work never touches a learned model's identity again.

**E9. Names** (S).
- **Problem:** P6, C3. Two `card` modules, `LegacyLanesSource` (live), `learner_context.py` (not the Ask path's context).
- **Does:** renames only. Packages stay. No consolidation of `router/` and `router_objective/`, unless the step finds it's a move of under 5 modules.

**Stopping point 6.** Objective and policy edits are local.

### 2.8 Arc F: speed (D4, D5)

Nothing here changes a value at a fixed draw count without the playbook. More draws fitting before a deadline is existing behaviour, as in both speed stages.

**F1. Column checks** (M).
- **Problem:** D5. 54 `table_info` sites in 40 files each mark a pooled connection (`db/connection.py:310`), raising opens per job from 5 to 17. Most guard schemas that no open can have, since every writing open migrates and every other attach refuses a mismatch.
- **Files:** those sites; `db/schema_facts.py` (one small helper, cached per head migration), used only by the sites that remain.
- **Deletes:** checks with no older schema to guard, after D1 (read each: some exist for test databases with partial schemas, and those tests move to the real schema). `db/stores/source_service.py` (5), `router_objective/scores.py` (2), `router_objective/checks.py:563`, `daily_plan/router_card.py:447` first.
- **Keeps:** R4's rule that a marked connection closes.
- **Proof:** opens per job measured back near 5; P-draw. **Depends:** D1.

**RE2. One retrievability function** (S). Owner, Nov 9; `spec_recognition_and_effort_v1.md` §6.
- **Problem:** `forgetting_curve` is called from 17 modules, 39 references beyond `scheduling/fsrs.py`, and `daily_plan/reentry.py:64`, `objective_inputs.py:419` and `router_objective/memory.py:274` define their own.
- **Files:** those; `scheduling/fsrs.py` gets one read function, scalar and vectorized, one definition.
- **Exempt:** `scheduling/fsrs_fitting.py`, `scheduling/evaluation.py`.
- **Abstraction:** none new: one function replaces several.
- **Proof:** replay identical on the head fixture; P-draw; decision latency no worse, measured; a test fails on a new direct `forgetting_curve` call outside the allowed modules. **Serves:** RE8. **Note:** runs before F2, which optimizes `memory.py`. If the sites differ in rounding or clamping, that's a finding, reported rather than silently unified.

**F2. The numeric policy's arithmetic** (L). Owner's decision 9.
- **Problem:** D4. About 468k draw-evaluator calls in about 34 jobs, tens of seconds of 110 s profiled.
- **Depends:** E5 (the arithmetic alone in `rollouts.py`), E8 (no identity knock-on), RE2.
- **Does:** profile on copies first, then vectorize or hold per-role values, each change proved byte-equal at fixed draws.
- **Target:** Next right after feedback no worse than mvp-0.49 on the large copies, by `docs/reviews/router-speed2.md`'s method and IH's prefetch in place. If unmet, it's reported, not forced with a shorter deadline or fewer draws.

**F3. SQLite reads** (M, only if F2 misses).
- **Problem:** about 394k `execute` calls, 13 s of 110 s. **Does:** re-profile and fix the top readers, with no new cache layer unless it's measured to matter.

### 2.9 Arc I: core and shell where it hurts

**I1. Grade application** (L) `[RE0] [IH]`.
- **Problem:** F3. `_compute_resolved_grade_application` (`attempts/attempts.py:4331`, 774 lines) reads the clock, repositories and config around the EKF, surprise and FSRS.
- **Does:** reads gather a `GradeInputs`; a pure function returns the application. Must precede H3, which changes `b` here. After D4 it's already smaller.
- **Proof:** P-shadow on all copies, byte-equal `surprise` rows on replay. **Vault:** Attempt Processing.

**I2. The due queue** (L) `[IH]`.
- **Problem:** F4. `build_due_queue` (`scheduling/scheduler.py:186`, 787 lines) ranks, draws, reconciles and persists, so IH's prefetch passes `persist_explanations=False` on a read path.
- **Does:** `rank_due(...)` pure, a separate persist call, the flag gone. The seeded exploration stays exact.
- **Proof:** P-draw, scheduler goldens, P-shadow.

**Stopping point 7.** Faster, and the two central functions are testable alone.

### 2.10 Arc G: one decider, one record of each fact, one belief, one protection

Nov 3 items 1-4; Appendix B holds the table. These guarantees stay whatever moves: prediction bundles written before the answer (`causal_probe_coherence.py:999`, migration 121's `generated_without_observation`), the pin of ids (`causal_orchestrator.py:2186`), the locked set before the answer (`:836`), the posterior at selection in `probe_presentations`, and the discriminating observations as inputs to `scoreboard`, `failure_triage`, `causal_health`, `evsi_calibration/live_report`, `causal_factor_deferral`, `router_objective/picks`, `ops/capture_report`, `hypothesis_marks`. Old rows stay readable. (`instructional/valuation` reads the episode posterior, not these.)

**G1. Facts, not a second decider** (M) `[IH]`.
- **Problem:** B6; §4.4. `decide_probe` mixes facts (gain, chance of changing the repair, burden, classes) with a verdict. FG1 calls it with zeros for a log field (`followup_run/router.py:111`), which reads like information and isn't (S14).
- **Does:** `probe_facts(...)` is pure and returns the facts and the hard stops. `decide_probe`'s verdict is one derived function over them, and still decides the repair lane until G2. FG1's fake-zero log goes. `resolve_cold_probe_parameters` and `resolve_causal_probe_parameters` merge if they don't differ. The router card can carry the facts.
- **Proof:** P-draw, P-shadow; existing causal tests unchanged. **Vault:** Diagnosis.

**G2. The router decides** (L, lands alone) `[IH]`. Owner's decision 10.
- **Problem:** Nov 3 item 1: six sites answer.
- **Does:** a probe on the repair lane becomes a candidate of the next decision, with `probe_facts` on its card; hard stops stay hard: machine checks, episode conflicts, the learner's "Not now". `RemediationBlocked`'s hold of repair becomes the candidate's reason to stand, and `decide_probe`'s verdict goes. `followup_run/lanes.py:59`'s rival count stays as the rule for which lane exists, since it's a fact about the factor, not a judgment of worth.
- **Scheduler EIG** (`scheduling/scheduler.py:2688`) stays as ranking for a staged fallback.
- **Proof:** P-playbook, with a successor and kill switch serving the predecessor exactly. Report: on copies, how often each path would have differed. **Verify:** owner reads the report. **Vault:** ADR-019.
- **Screens:** none redesigned. The existing feedback offer stays for the switch-off path; the UX stage decides how it reads.

**G3. Measure the disagreement** (S, read-only).
- **Problem:** Nov 3 item 3. Different evidence models, different locked sets (commissioning with support scores, `enter_episode` again without, `probe_episodes.py:296`; each insert a new id, `db/repositories.py:7767`), independence refused in one and discounted in the other, held grades checked in one.
- **Does:** a report comparing the two channels' resolved factor on every copy. It also tries the map's "no held check seen in the second" against the code. **Output:** counts, in the private file. **Decides:** whether G4 is worth doing.

**G4. One belief** (L, lands alone, conditional).
- **Recommendation:** the episode posterior can serve both, as it already has a prior and a likelihood. The discriminating observation stays as the record of which pre-registered prediction matched, and `enter_episode` reuses commissioning's locked set. Its `resolved_factor` for new rows then derives from the posterior, and old rows keep theirs.
- **If G3 shows they rarely disagree on real data,** skip the semantic change, keep a `doctor` warning when they do, and stop.
- **Proof:** P-playbook; readers listed above tested on old and new rows.

**G5. One record of each fact** (M, optional).
- **Does:** for each fact in Appendix B's table, one owner. New writes stop filling a duplicate only after its readers move to the owner. No table goes here, and rows stay. Skip anything that's only tidier.

**G6. Protection: one predicate** (M) `[V4]`.
- **Problem:** B3; D3. Figures, phone, plan and chat each carry their own checks. V4's landing needed a ruling because a check had drifted.
- **Files:** `learner_protection.py:190`, `figures/prefetch.py:947`, `scheduling/device_eligibility.py:330`, `reader/phone_media.py:64`, `scheduling/serving_exclusions.py:131`, the 27 callers.
- **Does:** each site asks `learner_protection` the "is this withheld" question, and adds only its own surface rule beside it. Fails closed everywhere. No new concept. The eligibility decision for serves stays separate, as it answers a different question.
- **Proof:** the protection tests; a parity test of every site on a protected fixture, before and after. **Verify:** Codex adversarially, on leaks only. **Vault:** Privacy and Trust; a note on protection.

**Stopping point 8.**

### 2.11 Arc H: the old difficulty scalar (item 7)

**Keep apart.** `practice_item_state.difficulty`, `activity_card_state.difficulty` and `family_memory_state.difficulty` are FSRS's D. They stay, and the rollouts read them. The scalar is `PracticeItem.difficulty`, `LearningObject.difficulty_prior` and `pf_candidates.difficulty`. Each use below is a persisted-meaning question.

**H1. Name them apart** (S).
- **Files:** `learner/mastery.py:758-800`, `diagnosis/probes.py:322`, `daily_plan/lesson_suggestion.py:144`, `learner/lesson_weight.py:412`, `delayed_checks.py:95`; one test that forbids the scalar path from reading FSRS's column and the reverse.
- **Does:** X2's direct callers go through the seam (`resolve_item_irt_params`). With `eb_difficulty_enabled = False` by default that changes no value; the test pins it.
- **Proof:** P-shadow.

**H2. The four-way replay, before anything changes** (M). Owner's decision 11.
- **Arms (spec_router_objective_v1 §11):** (a) today; (b) label off the mastery path (`mastery.irt.difficulty_from_prior=false`); (c) surprise from AD's item-conditioned predictive; (d) both.
- **Reports:** on copies, for each arm: mastery, surprise, due dates and the queue, plus AD scoring with `z_llm` out. No private numbers go in a tracked file.
- **Cold items:** where AD has no cell, its population-level predictive; if even that's absent, `b = difficulty_default` (0, "no label"). A structural value, never a hand-set one per item.
- **Firewall:** (c) has AD feed a stored surprise row, which A2 and A12 don't allow today (§11 says so). The owner rules on it with the report in hand. If no: surprise reads `b` from the EB posterior or the default, and (c) drops out.
- **Files:** `scripts/difficulty_four_way.py`, `docs/reviews/difficulty-four-way.md`. No `src` change. **Verify:** owner.

**H3. Mastery and surprise** (L, lands alone).
- **Does:** successor; below the tag or with the switch off, today's path. Readers: `mastery.py`'s seam, `attempts/attempts.py:4484`, `:4691`, delayed checks, lesson weight, lesson suggestion, probes, field baselines (`field/outcomes.py:636`, `predictors.py:199`, `probability_states.py:326`, `success_head.py:229`).
- **Proof:** P-playbook with the report from H2 on the final code. **Depends:** I1, H2.

**H4. AD's own signal** (M, lands alone).
- **Does:** an AD successor retires `z_llm` (`serve_inputs.py:117`, `forecasters.py:77`, `replay.py:239`, `data_check.py:120`). `llm_v3`'s outside forecast already carries a model's estimate as a receipt, so nothing new is needed. The replay reports AD's scoring with and without.
- **Proof:** P-playbook, AD's scoring report.

**H5. Exam strata, filters, authoring** (L, split per review).
- **Exam strata** (`goals/exam_pool.py:47`): the stratification changes which items enter a pool. Options: drop it, or stratify on AD's predictive frozen at pool build. Recommended: drop it, unless the replay shows pools losing their spread. The owner sees it in the report.
- **Index filters** (`practice_index/retrieval.py:292`): callers decide; likely removed.
- **Authoring** (`practice_generation.py:465`, `:1696`, `rung_variants.py:100`, `contrast_pairs.py:484`, `surface_mint.py:205`, `pf_generation.py:487`): band prompts move to AD's generation contract, which already needs no band. Rung "easier/harder" is a relation, not this number. Prompts bump their versions.
- **Copied values** (`teach_back.py:929`, `probe_remint.py:188`, `promotions.py:1001`, `teacher/actions.py:169`, `instructional/tools.py:276`, `causal_probe_coherence.py:1352`).
- **Proof:** P-playbook, where meaning moves; golden prompts updated knowingly.

**H6. Writers, DTOs, the hash** (M).
- **Does:** writers stop (`exercise_authoring.py:817`, proposals `ai_contracts.py:206`, `:548`, `vault/writer.py:89`, `:120`, `golden_path_fixture.py:208` if it survived, `pf_publish.py:169`, `db/stores/pf.py:21`). The model field stays optional and readable: old YAML still loads.
- **Content hash:** `vault/hashes.py:41`, `:55` keep hashing the stored value as written, so no existing item's hash moves, and a test pins that on the head fixture. This is the one reader that stays for good, labelled "frozen hash input".
- **DTOs:** `serializers.py:431`, `:556`, `facets.py:128`, `knowledge_map.py:170` go; `KnowledgeMapScreen.tsx:507`, `InspectorOverlay.tsx:405`, `:651`, `dto.ts:441` go or, if they'd redesign a screen, go on the UX list. Config keys `difficulty_from_prior`, `difficulty_prior_scale` go after their switch.
- **Columns:** `pf_candidates.difficulty` joins J's drop list if the owner approves. **Vault:** Learning System, Concepts.

**Stopping point 9.** Don't stop between H3 and H6 unless the switch serves cleanly: mid-way, readers and writers disagree about what the field is for.

### 2.12 Arc J, the paper, and the close

**J2-J4. Approved drops** (M each, conditional).
- **Order:** only after that table's readers and writers are gone and the owner approved it. One migration per family: the P4 and kinship tables; the authoring and pattern substrate; the COMPAT list and `learner_theta`; the golden-path ladder and pack tables, if approved.
- **Each:** table roles, AD's lists, generated reference, P-shadow on copies, doctor, ADR-010's gate on the doctor list. The landing record names the owner's backup step and DB size before and after. With A2 it's now about 8 files.
- **No table is decided in this document.**

**Z1. The modelling paper** (L). Nov 6 item 8. `docs/paper/learnloop-models.tex` and `.bib`, describing the code at this tip. PDF built locally if a TeX install exists, not committed (G8). No install without asking. A read-only Codex pass checks its equations against the code. No learner data or owner notes. It runs here, not earlier, because E5, G4 and H move what it describes.

**Z2. Close** (S). Rerun every §6 measure with `scripts/refactor_measures.py` and the S0 commands. Report seconds saved per removal. **Then:** later feature work (§2.16).

### 2.13 Evidence for the owner's calls

| Row | Evidence | Recommendation |
|---|---|---|
| **TUI** | `learnloop today` is its one door (`cli/app.py:4033`), documented at `README.md:312`. A contract keeps it on the open queue with no plan view (`pyproject.toml:425`), so a session there never reaches the router, lessons or figures. 2,471 lines, 11 files, 16 test files, a hard `textual` dependency. Last behaviour change Oct 17. | **Remove.** Desktop and phone cover the daily journey and much more. The one gap is a bare terminal over SSH. If you use that, keep it. |
| **Collections** | "Retired from UI" was the July plan, but the build still runs against a collection (`IngestScreen.tsx:474`), source-set rows are loaded (`handlers/ingest.py:530`), 43 `src` files use the name, and `source_set_synthesis.py` is built on it. Add to collection remains in `SourceLibrarySidebar` and `OutlineAndPlan`. | **Keep; it's an internal concept with no replacement.** The UX stage can hide the word and the Under-the-hood actions. |
| **`projects/`** | Standalone: `<vault>/projects/project_store.sqlite`, no table in `state.sqlite`. A git-only sweep runs at app start and plan build (`ops/startup.py:13`, `handlers/queue.py:22`) and returns at once if nothing is enrolled. 5,300 lines, 16 test files. Last change Oct 13. A directory listing of the Nov 3 backup copies shows no `projects/` folder, which suggests no use on those vaults, though I can't tell whether that backup would include it. No replacement exists. | **Remove if nothing is enrolled; keep otherwise.** It's well isolated, so keeping it costs little. Run `learnloop project status`. |
| **31 CLI commands, `experiments/`** | Listed at §7.4. `experiments/` is CLI-only, 14,245 lines, and you asked on Oct 21 for E1 to run. Some commands are your report tools. | Name what you use; the rest go. `experiments/` goes once E1 is finished. |

**Carried open findings.** AD eta's growth has no upper bound (`docs/reviews/router-followups-codex-review.md:145`): your call, and I recommend a saturating form as its own successor after E5, whose one-module objective makes it smaller. Router speed's unmet target: F1, F2.

### 2.14 Stopping points

| After | Cumulative cost | What's true if you stop here |
|---|---|---|
| A4 | 4% | Every later change costs far less: defaults, tables and speed work no longer touch dozens of files. Privacy note correct. |
| B4 | 10% | Your four real cases answer from `learnloop why` going forward. Failures leave records. |
| B9 | 17% | One entry point, with the inventory's gaps covered or written down. |
| C7 and J1 | 27% | Proven-dead code gone. You hold the table list. |
| D7 | 47% | Old tags gone, one upgrade table, tests on the served path, about 80% of the shrink done. **The natural place to stop if usage runs short.** |
| E9 | 63% | Objective, mixing, sensor and action changes are local. |
| F and I | 74% | Next faster where it can be; retrievability one function; grading and queue cores testable alone. |
| G6 | 83% | One probe decider; protection one predicate. |
| H6 | 92% | Scalar retired, reported first. |
| J, Z | 100% | Tables reviewed and dropped as approved; paper; final measures. |

Each arc's steps also land one at a time, so an interruption mid-arc leaves a working system, with the exception noted at H.

### 2.15 Cost

| | Count | Rough size each | Total |
|---|---|---|---:|
| Small steps | 9 | 0.2-0.4M tokens | about 3M |
| Medium | 32 | 0.5-1M | about 24M |
| Large | 21 | 1.5-3M | about 46M |

About **50-100M Opus tokens including re-read context,** plus about 60 Codex reviews on the subscription, and about 20 landing gates (about 1 h each, shrinking as the suite does) plus two serial baselines. **I have no per-stage usage figure to calibrate against,** so treat the token numbers as an order of magnitude. Calendar: main took 1-3 stages a day on recent days, so about 5-8 weeks of queue time. D2 and D5 carry the most uncertainty: the D2 sample is small, and D5's hidden old-row readers could add fix rounds. By share: S0 and A 4%, B 13%, C and J1 10%, D 20%, E 16%, F 5%, I 6%, G 9%, H 9%, J2-4 and Z 4%.

### 2.16 What builds on this

| Later work | Depends on | Why it's smaller |
|---|---|---|
| Phone V5-V7 | G6, B3 | One protection question, device exclusions recorded |
| MCP C1b, C2 | G6, B9 | Protection; a chat action gets a trace |
| TE4 | E6, E7 | An action in one place |
| Planned-evidence, nat-scale, `measured_loss` | E5, G1 | Terms and probe facts in one place; `VALUE_PER_NAT_MINUTES` stops deciding |
| RE3-RE8 | E6, RE2, I1 | New action kind; one read function for `S_eff`; RE7 is an `objective.py` term. RE's spec places RE3-RE8 between the refactor and the UX audit; the brief says beside the audit. Either works here. |
| UX audit and overhaul | C3-C5, B9 | Fewer backends; `why.get` for the glass-box view; the UX list this strategy collects |
| Codex docs, last | all | Describes the final screens |

<!-- NEXT -->
