# LearnLoop refactor strategy v3

Phase A, job 2. **Status: for the owner's review. No step starts until the owner has seen it.** Written on `refactor/map` from the map `docs/reviews/architecture-map-2026-11-08.md` (base main `a525dbcef4`), with its claims checked against the code on Nov 9. Where the map was wrong it's corrected in place, and Appendix A lists each correction.

## Summary for the owner

The refactor has 66 small steps in eleven arcs. It can stop cleanly after any arc. Nothing starts until phone V4, instruct/handoff (IH), RE0 and the test-suite branch have landed.

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
- **You run some things yourself.** One read-only script over your vaults and one upgrade of each vault. The fresh backup for the acceptance test exists: `~/learnloop-backups/20261109-copy`, taken Nov 9 (owner approved; agents read backup-API copies of it, never the live vaults).
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
4. **TUI (C7):** decided, owner, Nov 9: it becomes a true alternative frontend with parity, rebuilt from the ground up as a feature stage after the refactor. The refactor moves only its dependency (C7a) and doesn't reroute code that the rebuild replaces.
5. **Collections (C7):** keep them. The build runs on one, so nothing replaces them. The UX stage can hide the word.
6. **`projects/` (C7):** decided, owner, Nov 9: keep it. It's not removed in the refactor, and it'll grow later as a subset of goals.
7. **31 CLI commands and `experiments/` (C7):** say which report tools you still use, and whether E1 is finished.
8. **Kill switches at or below the oldest tag (D7):** remove them, except any your vaults set.
9. **Router speed target (F2):** keep "Next right after feedback no worse than mvp-0.49", remeasured after IH's prefetch.
10. **The router as the only probe decider (G2):** owner confirmed the direction, Nov 9. An independent Fable review (§2.10, G2) kept it but changed two specifics, which the owner accepted, Nov 9: the post-miss probe stays at the post-feedback Next, and the router prices hypothesis discrimination first, accepting a longer simulation. The learner's narrowing enters by reweighting, never by removing (G2).
11. **AD into surprise (H2-H3):** this crosses firewall limits A2 and A12, so it needs your amendment after you've read the four-way replay.
12. **The table list (J1):** review it. No table is dropped without your answer.
13. **AD eta's unbounded growth:** I recommend a saturating form as its own successor after E5, not inside the refactor.

Settled since the map: RE2 is a firm step (owner, Nov 9) and RE0 lands before step 1. Not settled: RE1's placement (§2.1).

**Cost.** Roughly the size of RO0-RO6, TE2-TE3 and phone V1-V4 together: 66 implementer runs, one Codex review per arc rather than per step (owner, Nov 9), and about 20 full-suite landings, or about 3.5-6 weeks of queue if usage allows (revised from 5-8; uncalibrated). Arc D is the first committed goal (owner, Nov 9: "the biggest stepping stone"); the rest is decided there. This is an estimate, not a measurement (§2.15).

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
| 1 | **Failures, exclusions and joins leave no answer to "why x and not y".** No id links input to reasoning to behaviour. | `daily_plan/engine.py:2671` turns any chooser exception into `<error: Type>` with no log and no message. `Prefetch.results` (`router_runtime.py:173`) writes a timeout with no payload. `objective_chooser.py:1371` mints the decision id after the model calls. `figures/prefetch_model.py:465`'s reason never reaches the row (the row at `prefetch.py:1093` has no reason column), and `filter_candidates` (`prefetch.py:937`) drops candidates with a bare `continue`. O1-O3, S1-S15. | B |
| 2 | **The plumbing is larger than the change, and most of it isn't protecting anything.** | All 46 snapshot digests are computed from today's schema with only the tag replaced (`config/template.py:4182`), so they hold one bit between them. Nothing in `src` reads them. 499 of router speed 2's 593 generated notes changed only commit stamps. 3,070 of the 4,304 `mvp-0.N` literals are comments, 2,319 of them in `template.py`; 285 are in code. H1, H2. | A, D |
| 3 | **History is kept alive at a cost, and the test suite mostly checks it.** | No upgrade module is reachable from replay, even through function-local imports (proof in §2.5). Yet 90 tag gates exist, and 79 of them are constant at mvp-0.43 or later. **New finding:** `AlgorithmsConfig.algorithm_version` defaults to `mvp-0.6` (`config/schema.py:18`) and `create_basic_vault` pins it (`tests/helpers.py:79`). 437 test files use that vault, and 271 of them never mention a version. Much of the suite tests a path no vault of yours has. | D |
| 4 | **The router's top layer isn't a layer.** | `_decide_objective` (`objective_chooser.py:1331`) reads the DB, mints ids, seeds, draws, flips the coin, assembles the trace and registers a background carry. `_Model` (`value.py:602`) holds the objective's ledger and the rollouts together. F1, F2, §3.3. | E |
| 5 | **Six sites answer "should we probe?", and two belief updates can disagree.** | `decide_probe` is authoritative on one lane and called with hard-coded zeros on the other, as a log field (`followup_run/router.py:111`). §4.4 of the map. | G |
| 6 | **Dead and superseded code stays,** partly because it's hard to prove dead. | The name scan missed the parameter registry's `importlib` path (Appendix A), so some "dead" modules are imported at runtime. | C, D |
| 7 | **Router speed target unmet, and R4 costs connections.** | 54 `table_info` sites in 40 files each close a pooled connection (`db/connection.py:310`). Opens per job went from 5 to 17. Numeric arithmetic is the rest (`docs/reviews/router-speed2.md:388`). D4, D5. | F |
| 8 | **The two functions that decide what's served and what's learned can't be tested without a database.** | `_compute_resolved_grade_application` (774 lines), `build_due_queue` (787 lines, with a `persist_explanations` write flag on a read path). F3, F4. | I |
| 9 | **The old difficulty scalar reaches further than its name,** and shares that name with FSRS's D. | `learner/mastery.py:758`, `adaptive_difficulty/serve_inputs.py:117`, `vault/hashes.py:41`, `goals/exam_pool.py:47`. X1-X3. | H |
| 10 | **Protection is nine questions, each with its own authority, and surfaces read different sets.** B3, corrected by K1 (`docs/reviews/refactor-k1.md`). | The span-level authority is `content/sources/exam_material.py` (about 80 importer modules). `learner_protection.py:190` answers one question of the nine (a model's view of an item). Surfaces disagree on the set: all exam material, held-out only, or teaching-wider. The fail-closed metadata check runs in 4 readers. | K1, G |

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
- **Who:** an Opus implementer in a worktree, then the gate; a step's named proof and the gates are its check. At the end of each arc, one read-only Codex review (`gpt-6.1-sol`) of the arc's whole diff, with a fix round for what it finds, before the next arc starts (owner, Nov 9: per arc, not per step, because the reviews have caught meaningful gaps). Steps that change persisted meaning (G2, G4, H3-H6) still land alone. "Verify" names anything beyond that, and the owner only where stated. Nothing in this document is yet approved to run.
- **Gate per step:** targeted tests under the memory cap, `lint-imports`, `ruff check` (from A5), the vault validators, and the step's named proof.
- **Gate per landing batch:** the full suite and durability once, on the merged tree (owner decision 1).
- **Gate per arc:** one full `pytest --fresh-connections` run at each arc's close, about 55 minutes, because the fast lane reuses connections (`tests/connection_reuse.py`) and only this run shows what that hides; and from A6 on, the `arc_close` tests (pre-registered sims and long journeys), which landing gates leave out (owner, Nov 9).
- **Not in any gate (owner, Nov 9):** `openai_codex`. `test_the_real_sdk_has_the_seams_the_lockdown_replaces` keeps skipping there.
- **Comments:** when a step touches a function, it follows the convention below, and only there. No sweep.
- **Vault:** the step fixes each note it names, and any other note it finds it has made false. The large rewrite stays last (§5).
- **Deleting:** before deleting anything, its step 0 proves it again at that tip: no import (including function-local and `importlib`), no string dispatch (`METHOD_REGISTRY`, Typer decorators, `MODULE_INVENTORY`, `_reg_const`), no frontend or phone caller, no replay, rebuild or upgrade path. A claim that doesn't hold moves the row to the owner's list. It never gets deleted anyway.

**The comment convention (C1, C4).** A comment says what breaks without this line, or why the obvious approach is wrong. It doesn't name a review round, a ruling or a stage; those belong in the commit and `docs/reviews`. A function over 100 lines starts with two or three sentences on its approach. `learner/mastery.py:783` and the note at `db/connection.py:310` are the models, though the second should lose its ruling number.

**Proofs, named once:**
- **P-tests:** the targeted tests, plus the fail-first test where a bug or silent path is fixed.
- **P-shadow:** `learnloop rebuild --shadow --json` before and after on backup-API copies under `fixtures-local/`, with the semantic projection identical and `schedule_effects` empty. Copies come from a fresh backup when the owner supplies one. Until then, the Nov 3 copies upgraded to the head tag.
- **P-draw:** the router speed stages' draw-for-draw harness: mixture seed pinned, fixed draw count, fake LLM and Decider. LLM requests, gates, prompts and every table must match the base commit (`docs/reviews/router-speed2.md`, "Identity").
- **P-playbook:** all of `docs/algorithm-change-playbook.md`: a successor tag, a kill switch that serves the predecessor exactly, the upgrade row, table roles, replay tests, a shadow rebuild on copies with mastery, facet and scheduling deltas reported before landing, and the fixture path.

**Identity rules (owner, Nov 11; arc C's review).** A deletion proof that only follows imports and names can't see a config or model dump inside a hash: C3's removal of the unread `merge_locked_facets` moved canonical synthesis's cache key, so finished runs stopped being reused. From K0 on:
- every step's gate includes `tests/test_identity_pins.py` (each compared identity pinned at a fixed input, §2.17 K0);
- a retired config field goes into `config/retired.py`'s `RETIRED_FIELDS` in the commit that removes it, so identities keep their bytes;
- an identity that should move is bumped deliberately, under `docs/algorithm-change-playbook.md` if it changes persisted meaning, and the pins are regenerated in that commit with the reason in the landing note.

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
- **Proof:** read against `ingest/extractors/__init__.py:84`, by the implementer, with the check recorded.

**A5. A bug-finding linter in every gate** (M) `[IH] [RE0]`. Owner, Nov 9.
- **Problem:** nothing checks Python beyond `lint-imports`. A ruff 0.17 run on main (`a36da14a4a`, `src/` and `tests/`, rules `F,E9,B,UP,SIM,PLE,RUF100`) found 7 undefined names, one of them live: `diagnosis/probe_instance_generation.py:933` calls `LOG.warning` in the fail-closed branch of the reserved-question check, where `LOG` is undefined, so a failed read raises `NameError` instead of returning "nothing admitted". Also: 65 closures capturing a loop variable (17 in that same file), 238 `zip()` calls without `strict=`, 72 re-raises without `from`, about 600 auto-fixable items and 847 stale `noqa` comments. About 3,500 star-import warnings, mostly in `cli/app.py`, are noise.
- **Files:** `pyproject.toml` (`[tool.ruff]`, and ruff in the `dev` extra pinned to one version), the findings' files, CLAUDE.md's commands, the stage and landing gate lists.
- **Rules:** bug-finding only: pyflakes `F`, `E9`, bugbear `B`, `PLE`, `RUF100`, and the `UP`/`SIM` rules the implementer judges free of churn. No formatter and no naming, style or complexity rules: reformatting 620k lines would change nearly every line and collide with every branch in flight. Star imports in the CLI modules get a per-file ignore, not a rewrite.
- **Order:** (1) the `LOG` bug first, its own commit, with a test that fails before the fix, if it hasn't been fixed by then; (2) one mechanical commit of `ruff check --fix` (safe fixes only), with nothing else in it; (3) each remaining finding read and either fixed with a test, or kept with a `noqa` and a reason; `B023` and `B905` are read one by one, because each can be a real bug or deliberate; (4) `ruff check` joins every step's gate and every landing gate, beside `lint-imports`.
- **Types, later and per file:** modules that arcs E and I create or rewrite get strict type checking (one checker, chosen at E1), enforced per file. No whole-codebase typing.
- **Proof:** `ruff check` is clean on the tip; the mechanical commit changes no test outcome (targeted run of the files it touches, then the batch gate); every behaviour fix has its own test. **Vault:** Developer Map's commands.

**A6. A shorter gate without losing what it catches** (M). Owner, Nov 9: "sims should run at each arc's close instead of every landing".
- **Problem:** item 10. On main `a810f628d8` the full suite is 31,037 tests and 8,281 test seconds (about 17 min at `-n 8`). The slowest 1% (about 310 tests: simulations, multi-day journeys, router rollouts) take 3,617 s, 44%; `test_ad23_sim` alone 708 s. 20,289 tests take under 0.05 s each, 170 s in all, so deleting cheap tests saves nothing. The slowest single test (215 s) is the floor at any worker count, and workers are capped by memory (10 GB for 8 on a 30 GB machine), not by the 32 cores.
- **Does:** (1) an `arc_close` marker for the pre-registered statistical sims and the long journeys whose size is the point (`test_ad23_sim` at its pre-registered size, `test_evsi_multisim`, and others the step names with their seconds); the landing gate runs `-m "not arc_close"`, and the arc-close gate (beside the Codex review and the `--fresh-connections` run) runs them; plain `uv run pytest` still runs everything. (2) Each of the slowest ~300 remaining tests is measured and either shrunk (a week where two prove nothing more), split (the 215 s and 168 s ones), or kept, with the reason recorded; every assertion is kept. (3) Per-step gates run the tests the change can affect, chosen from the import graph, with the full suite still at every landing. (4) Whether 10-12 workers fit in memory, measured.
- **Files:** `pyproject.toml` (marker), `tests/conftest.py`, the tests it shrinks or splits, CLAUDE.md's commands, the stage and landing gate lists, `scripts/refactor_measures.py` if its timed lanes need the marker.
- **Proof:** every test still runs in one of the two gates (a collection check that the union is the whole suite); no assertion removed (diff review); the landing gate's time before and after with the same command; the arc-close lane passes. **Target:** the landing gate at about 8-10 min at `-n 8`, the per-step gate in 1-2 min. Below about 5 min it would have to drop the end-to-end journeys or replay checks, which is not the aim.

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
- **Proof:** §3.6's acceptance, on the owner's fresh backup. **Verify:** a fresh agent given only `why --json` output and the questions, no code, answers the four cases and the past-bug sample. **Vault:** Workflows gets one "Debug a decision" note; Reference regenerated.

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
- **Candidates:** `substrate/compat/substrate_cutover.py` (721; 2 entries), `scheduling/progression_policy.py` (103; 3), `scheduling/progression.py` (341; 3), `scheduling/reentry_adapter.py` (287; 2), `scheduling/predictive_targets.py` (165; 1), `scheduling/short_session.py` (117; in `MODULE_INVENTORY` with no `_reg_const` entry). `scheduling/open_world_gate.py`'s `_has_attrs` also imports modules by name, so step 0 reads its list.
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
- **Check:** `open_world_gate.py:134` imports `curriculum.golden_path_assessment` and `pattern_ladder` by name; `DoseOffer.tsx` and `ExemplarConfirmDialog.tsx` mention golden names; `bridge_active` also carries the `router.enabled` switch `router_active` needs, so its check moves, not goes. `test_p2_acceptance` goes only for what it uniquely proves.
- **Tables:** left in place for J1. **Proof:** vitest, P-tests. **Verify:** a grep for a learner route left, in the step's gate. **Vault:** User Journey Map.

**C6. P4 controller, kinship, shadow components** (M, conditional).
- **Problem:** the map marks the row unverified. `scheduling/controller_cutover.py` (653), `controller_store.py` (512), `kinship_feature.py` (526), `shadow_components.py` (308); DESCOPED U-025, U-026; CLI group `controller`; references from `staged_policy.py`, `randomization_layer.py`, `router/decisions.py`, `controller_snapshot.py`.
- **Step 0 decides:** what's actually reached on the plan path. `controller_snapshot` probably stays. Anything live stays and the row moves to the owner. If C5 removed the only caller of `controller_cutover`, it goes with its registry entry. **Proof:** P-draw, P-shadow.

**C7. What the owner chose** (M, conditional on decisions 4-7).
- **TUI, step C7a (S; owner, Nov 9: "the TUI has to probably be rebuilt from the ground up in order to have parity as a true alternative frontend"):** the old `src/learnloop/tui/` stays working and frozen, and no refactor step spends effort rerouting it, because the rebuild replaces it. Only `textual` moves from the core dependencies (`pyproject.toml:14`) to a `tui` extra, so the base install stops carrying it, and `learnloop today` says how to install the extra when it's missing. When a later refactor step changes something the old TUI imports, the step makes the smallest fix that keeps its tests passing. `tui-keeps-the-open-queue` (DL1) stays until the rebuild. **Proof:** the TUI's 16 test files pass; a test that the base install imports without `textual`. **Rebuild, not in this document:** a spec-first feature stage with the held work after the refactor: a top-level `src/learnloop_tui/` adapter beside `learnloop_mobile` and `learnloop_mcp`, with the desktop's main journeys including the plan and router, on the same application contracts as the phone. The old TUI and its tests are deleted when it lands.
- **`projects/`: kept (owner, Nov 9: "please keep it and do not remove it in the refactor").** No step deletes it, or its CLI, config, routes or tests. It stays working through the arcs: a step that changes something it imports makes the smallest fix that keeps its 16 test files passing. It's a standalone store, so J1's table list doesn't cover it. Building on it is a later feature stage (below).
- **`experiments/`, if E1 is finished:** 36 files, 14,245 lines; results stay in `docs/`.
- **CLI commands:** those the owner names.
- **Proof:** P-tests, CLI help snapshot. **Vault:** Adapter Architecture, Package Boundaries, README.

**J1. The table review list** (M; arc J's first step, run here because the removals above name the readers).
- **Problem:** item 12; T1-T4. 396 tables: 24 retired but still read, 1 dead.
- **Files:** `scripts/table_review.py`; private output under `fixtures-local/table-review/`; the tracked part is `docs/reviews/table-review-<date>.md`, names and code facts only.
- **Does:** for each table: role, row counts and newest date on fresh copies, DB file sizes, readers and writers at this tip, replayer or upgrade, feature, class, and whether readers tolerate its absence. It re-reads the COMPAT-labelled live tables (`practice_item_state`, `hypothesis_sets`) and corrects their role in `db/table_roles.py`: step 0 checks what each role changes in rebuild.
- **No table is decided here.** It lists; the owner answers. **Needs:** a fresh backup: `~/learnloop-backups/20261109-copy` (Nov 9, migration 250, mvp-0.54).

**Stopping point 4.**

### 2.6 Arc D: history

**What I proved.** An AST closure over every import, function-local included and `TYPE_CHECKING` excluded, starting from `substrate/rebuild_orchestrator`, `shadow_rebuild`, `canonical_projection`, `attempts/attempts`, `daily_plan/engine` and `ops/doctor`, reaches 485-579 modules and none of the 42 upgrade modules. The `importlib` paths in `src` are the registry's `MODULE_INVENTORY`, `valuation`'s named gaps, `open_world_gate`, the fetchers and the PF sandbox, and a scan for `_upgrade` strings finds none naming an upgrade. So replay doesn't import them.

**What they're still needed for:**
1. **The CLI's `upgrade`.** Every link is its next link's predecessor.
2. **Every writing open.** The CLI and sidecar install `phone_probes_upgrade.complete_interrupted_activation`, which hands a journal naming an earlier link down the chain, back to mvp-0.33. Without a journal it checks one path and returns.
3. **Helpers.** `UpgradeResult`, `rewrite_algorithm_version`, `publish_algorithm_version`, `write_activation_journal`, plus two constants that `learner/recall_calibration.py:16` imports.
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
- **Measured:** a random 40 of the 271 files, run with the pin changed by a scratch plugin (no source edited): baseline green on the failing files; at mvp-0.43, 11 of 441 tests failed, in 7 of the 40 files; at mvp-0.54, 14 failed, in at least 8. So expect very roughly 50 files and a few percent of their tests. The sample is small, and other files may be worse.
- **Files:** `config/schema.py:18`'s default (to the floor or a required field), `tests/helpers.py:21`, `:75-79`, the basic vault's facets (it's "the pre-KM2 contract"), `use_init_algorithm_version`, the failing tests.
- **Rule:** a failing test is fixed to assert the same behaviour on the real path, or, if it only ever described the old path, deleted with a line in the landing note. An assertion is never edited to whatever the code now says without reading why it differs. A difference is a finding.
- **Proof:** P-tests; the landing record lists every changed assertion and why. **Vault:** Testing.

**D2b. Tests that name old tags** (L) `[T]`.
- **Problem:** 190 test files name tags at or below mvp-0.42, 143 use `set_algorithm_version`. Some mean "the predecessor serves exactly": those go when their switch goes (D7). Others just needed a tag.
- **Does:** re-tags the second kind to the floor. Batch by directory of behaviour, not all at once. Split further if the review needs it.
- **Proof:** as D2a.

**D3. The upgrade table** (L) `[IH]`.
- **Problem:** Z1, P5, X-clones: `_activate_as_writer` in 19 modules, `_upgrade` in 21, `complete_interrupted_activation` in 20. By normalized AST, the 7 newest links (mvp-0.48 on) differ only in the name of their upgrade function, and most of the 14 before them in four or five small functions, which step 0 reads. `interval_factor` is a real exception (a whole-vault rebuild), and `replay_ledger`'s activation differs too; step 0 reads it. `cli/app.py:108` has a 180-line docstring and a 40-branch `if`. About 23 assertions pin `inspect.getsource(...)` to name the latest module.
- **Files:** new `ops/upgrades.py`; `algorithm_versions.py`; `cli/app.py`; `cli/runtime.py:138`; `learnloop_sidecar/context.py:810`; `activation_journal.py`; `learner/recall_calibration.py:16`; the tests.
- **Deletes:** all 42 modules (about 8,900 lines; `recurrence/upgrade.py` and `ops/vault_upgrade.py` included), about 400 lines of `cli/app.py`, most of 8,808 lines of tests, the chain-walking tests (Z1).
- **Adds:** one table: `Link(tag, activate)`, where `activate` is `idempotent_projection` or `whole_vault_rebuild`, or a function if a link needs one. It replaces 42 clones with one transaction, journal and publication. A successor adds a row.
- **Keeps, with tests:** refuses jumps, journal before publication and publication last, recovery after death at each point, idempotent re-run, an old config readable when preparation fails (playbook step 3 and 8), the AD guard's denial mark.
- **Proof:** the kept tests run parametrized over each link on one small fixture, instead of walking from mvp-0.9. A fresh-copy upgrade through the table gives the same projection as `pre-floor`'s code. **Vault:** Add ADR-018's table; Version Registry; playbook steps 3 and 8.
- **Target:** a new tag is 1 constant, 1 row, 1 test row.

**D4. Constant gates: attempts, mastery, grading** (L) `[IH] [RE0]`.
- **Problem:** with the floor enforced, a gate on a set that holds every tag at or above the floor has a dead else-branch. By AST against the real chain, 79 sites are constant at a floor of mvp-0.43, and all 90 sites (47 sets) at a floor at the head. (The map's "about 40 pure, 38 paired" isn't reproducible; my own syntactic split found only 10 paired, and it misses some, such as `daily_plan/policy.py:42`. Each site gets read.)
- **Files:** `attempts/` (17 sites), `learner/` (6), and `held_grades`-adjacent callers.
- **Deletes:** the gate and its else-branch. Where a gate pairs with a kill switch, only the tag half goes; the switch waits for D7.
- **Proof:** P-shadow identical on every copy, and P-tests at the head. **Vault:** Attempt Processing, Learning System where they state a removed branch.

**D5. Constant gates: substrate, rebuild, doctor** (L).
- **Files:** `substrate/` (13 sites, including `canonical_projection.py:309`, `:319`, `:652`, `:654`, `:712`, `:1175`), `rebuild_orchestrator.py:443`, `ops/doctor.py` (5), `db/repositories.py:26949`'s gate half, `substrate/compat/` once unused.
- **Deletes:** the pre-canonical projection path (LEGACY-ONLY row), `facet_uncertainty` and `evidence_facet_recall_state` writers (`attempts/attempts.py:3322`) if the path is their only one, for J1's list.
- **Keeps:** every row reader that reads by shape, and `activity_backfill` (`rebuild_orchestrator.py:311`: rebuild imports it). `fixtures/mvp017_route_check_replay` must still pass.
- **Proof:** P-shadow on all copies; the replay fixture; rebuild-equivalence tests. **Verify:** step 0 inventories every old-row reader, and a test reads a fixture row through each after the removal.

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
- **Identity (K0):** `tests/test_identity_pins.py` C3-C6 show what each removal does to the router seeds, `FOLLOWUP_SWITCHES` and RO6's generator key; per switch, keep its served value in the identity or fold the change into E8's one change point.

**D8. The pinned replay gaps** (L, one landing per gap; owner, Nov 9). `docs/reviews/test-suite-audit.md` §4 pins four gaps with eight strict xfails, each of which goes red when fixed:
- **Retired items (3, `test_rebuild_closed_row_answer`):** an item retired outside the attempt ledger has no time replay can apply it at, so replay sees it active. Needs closures as ledger events.
- **Same-second grades (1, `test_rebuild_equivalence_review`):** two grades of one LO committed in one second in reverse id order replay in id order. Needs a persisted commit sequence.
- **Claims that never re-anchor (2, `test_learner_report_superseded`):** made after materialization, they differ between live and replay. Design open.
- **Provenance F2, F3 (2, `test_diagnosis_input_provenance_landing`):** the reopened gaps, waiting on the one-capture-point follow-up.
- **Rule:** each fix that changes persisted meaning follows the algorithm-change playbook and lands alone, like G2. `test_rebuild_equivalence`'s three xfails below mvp-0.36 go with the old tags in D3, not here. The placement gap isn't here: it's being fixed separately with its own successor.
- **Proof:** each xfail removed, because the test now passes; P-shadow on the fresh backup. **Vault:** the replay notes each fix changes.

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
- **Problem:** D5. 54 `table_info` sites in 40 files each mark a pooled connection (`db/connection.py:310`), raising opens per job from 5 to 17. Many appear to guard schemas no open can have, since every writing open migrates and every other attach refuses a mismatch; step 0 reads each.
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
- **Independent review, Nov 9 (Fable; the owner accepted the direction; the cited code rechecked by the orchestrator except where noted):** the router stays the one decider, but as written this step has two faults.
  - **Timing.** The post-miss `Next` already is a router decision (`followup_run/router.py:179-209`). Moving the probe to a later boundary is the WAIT arm, which releases feedback and marks the probe exposed, so it can no longer settle the cause (`followup_run/jobs.py:411-412`; the card says so at `objective_chooser.py:1780-1783`). So the post-miss probe stays at that Next, with feedback held. Only the learner lane's feedback-screen offer changes (`FeedbackScreen.tsx:48`, `handlers/remediation.py:170-191`).
  - **Pricing.** The numeric policy values a probe as one binary ability result (`router_objective/value.py:886-925`), and on main FG1's stand-in is `action="practice"` (`router_chooser.py:851`), so hypothesis discrimination reaches only the LLM's card. With the LLM out, IH5 hands the share to a policy blind to it. So the shape is two-stage: the diagnostic layer proposes the candidate, asserts hard stops and supplies the structure of its value (locked set, P(result | h), repair per h, burden), and the router alone draws and logs the propensity, with `π_Q` branching per hypothesis. No threshold in the diagnostic layer. Owner, Nov 9: "the simulation work is fine if it takes a bit longer", so the speed target doesn't block this; G1 measures the branching's milliseconds and reports them. The owner also wants the learner to help narrow the hypothesis space. FG1 §7's constraints stand unless the owner changes them: causes stay hidden before the probe because they prime the answer, and the locked set can't shrink after it's locked, so narrowing reweights branches instead of removing hypotheses. Its form, owner, Nov 9: their own words before the probe, and prompted directly when the answer didn't say; *Show anyway* then marks, with the probe recorded as not independent; and marks after the probe, informing future misses. Not an always-shown list. Marks' weight is learned, from FG1's agreement report. Building the direct prompt and any new surface is a feature spec, not this step; G2 only reads what exists.
  - **Scope.** As written G2 doesn't reach "only decider": `followups.py:395`'s value suppression and `voi_stopping`'s continuation site also answer. Fix or name them here. `recent_diagnostic_limit = 2.0` (`causal_probe_coherence.py:103`) is a hand-set count rule that goes with the verdict; the gate's margins are 0.0 and its claim to be fitted is unverified.

**G3. Measure the disagreement** (S, read-only).
- **Problem:** Nov 3 item 3. Different evidence models, different locked sets (commissioning with support scores, `enter_episode` again without, `probe_episodes.py:296`; each insert a new id, `db/repositories.py:7767`), independence refused in one and discounted in the other, held grades checked in one.
- **Does:** a report comparing the two channels' resolved factor on every copy. It also tries the map's "no held check seen in the second" against the code. **Output:** counts, in the private file. **Decides:** whether G4 is worth doing.

**G4. One belief** (L, lands alone, conditional).
- **Recommendation:** the episode posterior can serve both, as it already has a prior and a likelihood. The discriminating observation stays as the record of which pre-registered prediction matched, and `enter_episode` reuses commissioning's locked set. Its `resolved_factor` for new rows then derives from the posterior, and old rows keep theirs.
- **If G3 shows they rarely disagree on real data,** skip the semantic change, keep a `doctor` warning when they do, and stop.
- **Proof:** P-playbook; readers listed above tested on old and new rows.

**G5. One record of each fact** (M, optional).
- **Does:** for each fact in Appendix B's table, one owner. New writes stop filling a duplicate only after its readers move to the owner. No table goes here, and rows stay. Skip anything that's only tidier.

**G6. Protection: one authority per question** (M) `[V4]`. Corrected by K1 (`docs/reviews/refactor-k1.md`, Nov 11).
- **Problem:** B3; D3. The map counted one named authority and several decision sites. K1 found nine questions: is a span exam material or held out; may it ground a model; may it become practice; routine serving; cold and exam independence; a model's view of an item; held grades; an item's own solution; what leaves the desktop. Each already has an authority. The drift is in which set each surface reads (all exam, held-out only, teaching-wider) and in the metadata gate, which only 4 readers ask (K1 §1-§2).
- **Files:** `content/sources/exam_material.py` (the span-level authority), `learner_protection.py:190` and `:159`, `source_retrieval/corpus.py:226`, `:446`, `source_retrieval/section_coverage.py:273`, `figures/service.py:554`, `:3377`, `figures/prefetch.py:315`, `:957`, `adaptive_difficulty/protection.py:86`, `reader/phone_media.py:64`, `:126`, `scheduling/device_eligibility.py:330`, `:395`, `scheduling/serving_exclusions.py:112`, `:131`, `instructional/practice.py:226`, `instructional/policy.py:33`, `learnloop_sidecar/serving.py:256`, `content/pipeline/jobs.py:2988`, `:3256`, `content/authoring/source_exercise_import.py:1202`, `remote/sources.py:63`, `:178-230`, `remote/views.py:344`.
- **Does:**
  - `exam_material` stays the one span-level authority, with its two sets named, and the metadata gate (`protection_issues`) moves inside it, so every caller fails closed on source sets that didn't load. That's K1's fix 1, if it hasn't landed by then.
  - Each surface names the set it reads in one place, so the deliberate differences are explicit and tested: the Reader's model contexts and the Reader import read held-out only (owner defaults §8 Q1 and Q3); teaching, figures and the phone read all exam; AD reads held-out plus reservations; the kill switch covers serving only.
  - `learner_protection` stays the item-level answer for model contexts, built on `exam_material`.
  - Ingest, synthesis and authoring keep calling `exam_material` directly. Routing them through `learner_protection` would change the Reader checks against the owner's defaults and adds nothing (K1 §5).
  - Serve eligibility and held grades stay separate: they answer other questions.
  - The frontend's measurement-integrity rules (the hint ladder, disclosure, deferral) are listed in the protection note, not moved. Serve payloads carrying the key are a known exception for the UX stage.
  - No new concept.
- **Proof:** the protection tests, and K1 §4's parity matrix: one synthetic vault with each fixture (an exam member with no marks, a rule-2 unit, held-out, held-back, ambiguous and signal marks, the item kinds, unreadable source sets, the switch off) × every surface's production predicate (Q2-Q6, the phone's and MCP's payloads), with each cell's expected answer pinned. Fail closed when a predicate raises. It includes every leak the phone, MCP and exam-protection reviews found, and K1's own. **Vault:** Privacy and Trust; a protection note naming the nine questions and each surface's set.

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
- **Identity (K0):** the commit that removes `mastery.irt.difficulty_from_prior` and `difficulty_prior_scale` puts both in `config/retired.py`'s `RETIRED_FIELDS` (they feed placement's `version_hash` and the field predictors; `tests/test_identity_pins.py` C1-C2 fail otherwise), and `PracticeItem.difficulty` and `difficulty_source` stay on the model (whole-item dumps A9, A19).

**Stopping point 9.** Don't stop between H3 and H6 unless the switch serves cleanly: mid-way, readers and writers disagree about what the field is for.

### 2.12 Arc J, the paper, and the close

**J2-J4. Approved drops** (M each, conditional).
- **Order:** only after that table's readers and writers are gone and the owner approved it. One migration per family: the P4 and kinship tables; the authoring and pattern substrate; the COMPAT list and `learner_theta`; the golden-path ladder and pack tables, if approved.
- **Each:** table roles, AD's lists, generated reference, P-shadow on copies, doctor, ADR-010's gate on the doctor list. The landing record names the owner's backup step and DB size before and after. With A2 it's now about 8 files.
- **No table is decided in this document.**

**Z1. The modelling paper** (L). Nov 6 item 8. `docs/paper/learnloop-models.tex` and `.bib`, describing the code at this tip. PDF built locally if a TeX install exists, not committed (G8). No install without asking. A read-only Codex pass on `gpt-6-astra` (owner, Nov 9) checks its equations against the code. No learner data or owner notes. It runs here, not earlier, because E5, G4 and H move what it describes.

**Z2. Close** (S). Rerun every §6 measure with `scripts/refactor_measures.py` and the S0 commands. Report seconds saved per removal. **Then:** later feature work (§2.16).

**Z3. Archive the old specs** (S). Owner, Nov 9: "Within the refactor after documentation is finished we should also archive all of the old specs." It runs after the documentation rewrite (§5's last stage, by Codex, after the UX overhaul), so it's the one step that waits past Z2; Z2's measures don't wait for it.
- **Problem:** `docs/specs` holds every spec since July, and as-built, superseded and live ones sit side by side.
- **Does:** moves every spec that's implemented and superseded, or abandoned, into `docs/specs/archive/`. It leaves the live ones (specs still being built, or still the reference for current behaviour), with a short index (`docs/specs/README.md`): each live spec, then each archived one with what superseded it.
- **Keeps:** links working. Every reference in `docs/`, the architecture vault, `CLAUDE.md`, tests and code comments is updated, and the vault validators run.
- **Owner:** reviews the live/archive list before the move.
- **Proof:** no broken link (a check script or `validate_vault.py`); nothing deleted, only moved (`git diff --stat -M` shows renames only, plus the index and the updated references).

### 2.13 Evidence for the owner's calls

| Row | Evidence | Recommendation |
|---|---|---|
| **TUI** | `learnloop today` is its one door (`cli/app.py:4033`), documented at `README.md:312`. A contract keeps it on the open queue with no plan view (`pyproject.toml:425`), so a session there never reaches the router, lessons or figures. 2,471 lines, 11 files, 16 test files, a hard `textual` dependency. Last behaviour change Oct 17. | **Decided, owner, Nov 9: rebuilt from the ground up as a true alternative frontend with parity,** a feature stage after the refactor. C7a only moves its dependency. |
| **Collections** | "Retired from UI" was the July plan, but the build still runs against a collection (`IngestScreen.tsx:474`), source-set rows are loaded (`handlers/ingest.py:530`), 43 `src` files use the name, and `source_set_synthesis.py` is built on it. Add to collection remains in `SourceLibrarySidebar` and `OutlineAndPlan`. | **Keep; it's an internal concept with no replacement.** The UX stage can hide the word and the Under-the-hood actions. |
| **`projects/`** | Not the Matuschak-style contextual learning: that idea became goals (a deliverable is a goal, `spec_deliverable_curriculum_v1` Q1). This package is `spec_project_understanding_v1`'s M1: delayed comprehension questions on agent-written code in enrolled repos. Standalone: `<vault>/projects/project_store.sqlite`, no table in `state.sqlite`. A git-only sweep runs at app start and plan build (`ops/startup.py:13`, `handlers/queue.py:22`) and returns at once if nothing is enrolled. 5,300 lines, 16 test files. Last change Oct 13. A directory listing of the Nov 3 backup copies shows no `projects/` folder, which suggests no use on those vaults, though I can't tell whether that backup would include it. No replacement exists. | **Decided, owner, Nov 9: keep.** Later, a subset of goals: quizzes on your own code and learning in context. |
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
| G6 | 83% | One probe decider; protection one authority per question (K1). |
| H6 | 92% | Scalar retired, reported first. |
| J, Z | 100% | Tables reviewed and dropped as approved; paper; final measures; old specs archived once the docs rewrite is done (Z3). |
| K (beside the arcs, §2.17) | +10-15% | The modules the Nov 8 map didn't read are mapped and given steps; compared identities are pinned; ingestion has a structure strategy. |

Each arc's steps also land one at a time, so an interruption mid-arc leaves a working system, with the exception noted at H.

### 2.15 Cost

| | Count | Rough size each | Total |
|---|---|---|---:|
| Small steps | 10 | 0.2-0.4M tokens | about 3M |
| Medium | 32 | 0.5-1M | about 24M |
| Large | 21 | 1.5-3M | about 46M |

About **45-90M Opus tokens including re-read context** (revised, owner, Nov 9: Codex reviews per arc, about 11 on the subscription, not per step, so most of the roughly 30 review-driven fix rounds go; each arc's review can still cost one, and so can a gate failure), and about 20 landing gates (about 1 h each, shrinking as the suite does) plus two serial baselines. **I have no per-stage usage figure to calibrate against,** so treat the token numbers as an order of magnitude. Calendar: main took 1-3 stages a day on recent days, so about 3.5-6 weeks of queue time with reviews per arc (revised from 5-8; an estimate). D2 and D5 carry the most uncertainty: the D2 sample is small, and D5's hidden old-row readers could add fix rounds. By share: S0 and A 4%, B 13%, C and J1 10%, D 20%, E 16%, F 5%, I 6%, G 9%, H 9%, J2-4 and Z 4%.

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
| Z3, the spec archive | Codex docs | Archives what the rewritten docs no longer cite as live |

### 2.17 Arc K: the modules the map didn't read (owner, Nov 11)

**Why.** After arc C, three read-only reviews (orchestrator scratch, copies under the session's `scratchpad-backup/`: `coverage-audit-2026-11-11.md`, `serialization-sweep-2026-11-11.md`, `ingestion-review-2026-11-11.md`) found that the Nov 8 map read several high-impact packages by outline only, or not at all, and that no arc plans a step for them:
- `content/pipeline`, `content/synthesis`, `content/sources`, `ingest`, `content/facet_identity` (zero mentions in the map), `content/proposals`: about 37,000 code lines between them, with the longest function in the code (`source_set_synthesis._normalize`, 1,081 lines);
- `source_retrieval` (20,000 lines), `diagnosis/text_gaps`, `ai/chatgpt_plan`, `learnloop_mobile`'s auth and `learnloop_mcp`;
- grading, regrade, coldness and certification were read only as far as B7 needed;
- B3 and G6's protection inventory never names the exam predicate, `content/sources/exam_material.py` ("THE predicate", 79 referencing files), the lexical leakage floor or the frontend's checks.

The map's methods were name- and import-based, so whole risk classes were invisible to it: config or model dumps inside compared hashes, seeds and cache keys (the sweep lists about 40 compared whole-dump sites); about 247 wall-clock reads outside the injected clock; more than 30 thread or lease spawns, with the phone host and the desktop running workers on one vault; YAML and SQLite dual writes; sandboxes that run model-written code.

**The owner's goals for arc K (Nov 11):** the same as §1's for the whole refactor (local reasoning, change locality, discoverability, few abstractions, economy, observability, small surgical steps). For ingestion specifically: "the same evaluation pipeline for deep modules as the prior refactor audit", looking for better larger-view structures that optimize for readability and ease of extension.

**Each review step** is read-only and runs the Nov 8 method scoped to its packages: job 1 maps (packages and deep or shallow modules with sizes; the journeys end to end with persistence, model calls and randomness; boundary crossings and duplicated predicates; decision points and what is recorded; functional core versus shell; comments; dead code and onboarding; the vault notes), and job 2 writes the strategy (diagnosis ranked by cost, ordered small steps each naming the problem, files, deletions, any abstraction and why it pays, and the proof; what not to do; vault plan; measures). Opus writes both; a read-only adversarial Codex pass (`gpt-6-astra`) checks the map's claims before the strategy uses them. The steps it produces are inserted into this document as sub-steps (K2.1, K2.2, ...), with the same per-step gates and per-arc Codex review.

**K0. Identity pins** (S-M). After arc C's close, before D.
- **Does:** `tests/identity_pins_helpers.py`, `tests/goldens/identities.toml`, `tests/test_identity_pins.py` (the design is the sweep's §3.1): every compared identity computed through its production path at a fixed input and pinned; failure messages say keep (`RETIRED_FIELDS`, `exclude_if`, an explicit identity view) or bump (playbook). Shape pins for every type whole-dumped into a compared identity (sweep §3.2), and an AST check that a new dump beside a hash, seed, manifest or structured prompt is registered or marked provenance-only (sweep §3.3).
- **Fixes now:** the synthesis manifest scope's other whole dumps (`graph_nomination`, prices, the `problem` text; sweep A2-A4), which share the consumer that arc C broke.
- **Before later arcs:** H6 must put `mastery.irt.difficulty_from_prior` and `difficulty_prior_scale` in `RETIRED_FIELDS` (they feed placement's `version_hash` and the field predictors, sweep C1-C2); D7's switch removals feed router seeds and RO6's generator key (sweep C3-C6): pin them before D7 and decide per switch whether to keep its served bytes or fold the change into E8.
- **Proof:** the pins pass at the tip; each fails when its source field is removed in a scratch edit.

**K1. Protection inventory** (S-M; review). Before G6.
- **Scope:** every predicate that withholds, protects or excludes: `exam_material` and its 30-odd importer modules (ingest, synthesis and authoring call it directly, not through `learner_protection`), the lexical leakage floor (`ops/contamination`, `practice_leakage`, `tutor_qa`, `reader_dialogue`), retrieval's protection filters (`source_retrieval/section_coverage.py`), the sidecar serializers and DTOs, and the frontend's own checks.
- **Questions:** which protection question each predicate answers; where two answer the same question differently; whether answer keys, rubrics or held-out text ever reach a screen and are hidden only there; what G6's parity test must add.
- **Output:** corrections to G6's inventory and steps.
- **Done** (Nov 11, `docs/reviews/refactor-k1.md`): G6 corrected above. No live leak. Fix before G6 (each from a failing test, with no successor):
  - **One metadata gate (K1 D1).** `exam_material` and its siblings fail open on a `source_sets.yaml` that fails validation or is caught empty: rules 1 and 2 vanish for the tutor, imports, figures and the phone. Only `learner_protection`, `learner_context`, `remote/views.py` and section coverage ask `protection_issues`. Move the check into the shared read, and write the file atomically.
  - **Practice the Reader makes from exam material (K1 D4), owner's call.** The Reader import passes non-held-out exam material (`jobs.py:3256`). The item is then served, but withheld from model contexts as exam material and treated as a reserved question. Recommended: keep §8 Q3's default, and don't withhold the learner's own item. `exam_material.py:101` changes to agree.
  - **Doors that miss a reservation (K1 R1, R2, R9, D6).** The session serve door ignores exam reservations (`learnloop_sidecar/serving.py:256`). MCP `find_sources` returns a diagnostic probe's own passage and assessment-lane passages (`remote/sources.py:63`). The inspector shows every hint of the item being answered, cold checks included, uncounted (`InspectorOverlay.tsx:482-505`). A remediation's cold item isn't reserved until its task exists (`instructional/policy.py:33`).
  - **Two docstrings (K1 D3, D8).** Rule 4's "no search hit" against the library search, and figures' all-exam set against the Reader's held-out set.

**K2. Ingestion and synthesis: deep map and structure strategy** (L; review, two jobs). Starts after arc C's close; read-only, so it can run beside arc D.
- **Scope:** `content/pipeline` (jobs, runner, leases, queue), `content/synthesis` (bootstrap, append, `_normalize`, manifests, inventory, coverage, graph nomination, facet mint gate), `content/sources`, `ingest` (extractors including hosted OCR, re-read, span aliases), `content/facet_identity` (judge, merges, aliases, authority), `content/proposals` (patches, write-ahead apply and recovery), the ingest and synthesis paths of `content/authoring`, `source_retrieval`'s ingest-side consumers, the sidecar ingest handlers and the desktop's `IngestScreen` and `OutlineAndPlan`.
- **Inputs:** the ingestion review's findings, to be confirmed or corrected by the map (keep-ahead appends re-send the whole book: `add_source.py:1646-1666` enqueues no `new_revision_ids`, `jobs.py:1989` passes `None`, `source_append.py:248` falls back to every revision; append has no checkpoint, input ceiling or output split; `_best_inventory` reads a unit's oldest inventory whatever its extraction, prompt or model; appends from chapter 3 on never auto-apply; the manifest hash serves as provenance, cache key and reuse key at once), and the Sep 6 ingestion review's open findings.
- **Strategy questions beyond §1's:** one checkpoint helper for every structured call versus today's mix; the manifest as provenance only, with reuse revalidated; hashing only what each step reads; whether `_normalize` splits into named stages; one job and lease mechanism instead of four reimplementations; where extraction, inventory, synthesis, identity and apply meet, and whether each boundary can change alone; how a new source type, extractor, synthesis pass or facet rule is added, counting files before and after.
- **Output:** the map, the strategy, and sub-steps K2.1... placed after arc D (or earlier where a step only fixes a bug that costs money today; see K3).
- **Done** (Nov 11): map `docs/reviews/k2-ingestion-map-2026-11-11.md` (corrected after a Codex check), strategy `docs/reviews/k2-ingestion-strategy-2026-11-11.md`. The sub-steps, after arc D, in this order (details, files and proofs in the strategy, §3.2):
  - **K2.1 One checkpoint helper** (M): every paid structured call through one cycle in `ai/execution.py`, keyed on what it sends; structuring, persona fire and epigraphs gain checkpoints; existing keys byte-identical (K0 pins).
  - **K2.2 Outer caches defer to the rendered key** (M): inventory reuse and completed shards stop answering on prompt labels (map KM1).
  - **K2.3 The manifest records; checkpoints reuse** (M): no run-level reuse lookup; the manifest gains exact inputs (inventory rows, role overrides, edges, resolved brief); append resolves its brief first (KX5, KM2, KM6). Manifest pins bumped deliberately.
  - **K2.4 One synthesis run, two modes** (L, as three M steps: shared tail, shared head, append through the shard runner): `source_append.py` shrinks to its prompt, neighbourhood and normalizer additions.
  - **K2.5 `_normalize` in named stages** (M): `content/synthesis/normalize.py`, one state, one function per stage, same rows.
  - **K2.6 One heartbeat for judge claims** (S): the two near-copied loops become one; commits check lapse; service spend renews on its clock.
  - **K2.7 A job type is one row** (M): handlers beside their feature, one `JOB_TYPES` table replacing five lists in `jobs.py` and `runner.py`.
  - **K2.8 A source kind is one row** (M): `ingest/source_kinds.py`; the desktop reads it; `ingest/fetchers.py`'s fetch path, `ingest/detect.py` and the desktop's kind tables go.
  - **K2.9 Extractor choice in one place** (S): `pdf_extractor_for` returns the extractor and its consent.
  - **K2.10 Small fixes, folded** (S): atomic conflict resolution, one token estimator, five stale comments.
  - **K2.11 The desktop asks instead of copying** (M): retry and repair eligibility, roles, bounds and page ranges from the sidecar; four disagreements gone. Before the UX overhaul.
  - **K2.12 Why x and not y at ingest** (M): decision records for build scope, inventory choice, auto-apply, persona fallback and the D2 summary.

**K3. Ingest fixes that cost money or data today** (confirmed by K2's map; each alone, from a failing test, no successor; beside arc D). Details in `docs/reviews/k2-ingestion-strategy-2026-11-11.md` §3.1.
- **K3.1 The right inventory row** (S): one `best_inventory` in `source_unit_inventory.py` preferring the current semantic hash, then prompt, provider and model, then newest; the coverage copy goes. Today a new prompt, model or re-read is paid for and ignored.
- **K3.2 Keep-ahead appends only the new units** (S): `jobs.py` passes the planner's chosen unit ids, and `source_append.py` filters by them. Input stops growing with every chapter read.
- **K3.3 The collection build sends every missing unit** (S): newness per unit in the sidecar's `build_study_map`, not "the revision has any inventory".
- **K3.4 The append call bounded and checkpointed** (M): a checkpoint, `generation_limit`, a refusal before an over-ceiling input, finalized run rows on a budget failure, the non-escaping estimator.
- **K3.5 Apply recovery safe and automatic** (M): never overwrite a file that changed since the intent (its `pre_hash`); recover at sidecar bind; refuse accepts while an intent is pending; recalibrate. A `conflicted` status needs a migration.
- **Owner's calls first:** auto-applying an append's new coverage (recommended: new creates, Undo as the net); arXiv ids reading the full paper (recommended); when the legacy canonical lane retires (recommended: the UX overhaul).

**K4. Other vault-content writers** (M; review). `diagnosis/text_gaps`, tutor promotions, teacher, `followup_run`, goals, authoring outside ingest: for each writer, content-hash lineage, authority (`check_meaning_write`), exam protection and undo; YAML and SQLite crash windows.

**K5. Grading, regrade, coldness and certification** (M; review). Before I1 and H3, which rewrite this code. The two validators (`attempts/grading.py`, `blind_grading.py`); whether a coldness `unknown` can pass; whether newer exposure channels (phone Reader, figures, teacher, MCP) reach `coldness_receipt._scan_exposures`; regrade, held grades and FSRS consistency; the four `qualifies_as_*` consumers.

**K6. Reader Ask and retrieval side effects** (L; review). After D, before G6. Which Ask outcomes change learner state or serving and whether they replay; retrieval's protection filters against K1's questions and sets (`docs/reviews/refactor-k1.md` §1); the identity of daily path refresh and coverage judgments; wall-clock reads in cache keys.

**K7. AI transport and network edges** (S + S; review). Before the MCP and phone feature stages. ChatGPT-plan token refresh races between the sidecar and the phone host; behaviour with the plan down; whether the route actually used after a fallback is recorded (B8 left it open); MCP's URL-as-credential and the phone bearer; cross-process workers on one vault.

**Order:** arc C close → K0 and K1 (parallel) → arc D, with K2 running beside it and K3.1-K3.5 landing beside it (K3.1 first, K3.5 independent) → K2.1-K2.12 (K2.1-K2.5 one chain; K2.11 before the UX overhaul) → E → F and I (K5 before I1) → K6 before G6 → G → H (K0's H6 rule) → J, Z. K4 and K7 fit wherever the queue has room. **Cost:** roughly 10-15% on top of §2.15 (an estimate), most of it K2.

## 3. The decision record

### 3.1 What it is

**One record, one trace id, one entry point.** A decision-producing function returns a `DecisionRecord`, and the imperative shell writes it. Rich domain rows stay where they are, because replay and the playbook depend on them, and the record points to them. For failures, exclusions and refusals, which have no domain row today, the record is the row.

It sits at meaningful boundaries: the inventory in §3.8, not every function. It never holds learner text or item text.

### 3.2 The shape

`decision_records`, role `RECEIPT` (append-only, never cleared by replay, never read by it):

| Column | What it holds |
|---|---|
| `id` | ULID; also the record's handle in `why` |
| `trace_id` | One learner-visible action and its background work (§3.3) |
| `parent_id` | The record that caused this one, possibly in an earlier trace |
| `kind` | `plan_block`, `model_answer`, `offer_withdrawn`, `slate`, `figure_prebuild`, `figure_author`, `grade`, ... (constants beside the code that writes them) |
| `status` | `chosen`, `fallback`, `excluded`, `withdrawn`, `timeout`, `discarded`, `failed`, `refused`, `deferred` |
| `subject_kind`, `subject_id` | `attempt`, `item`, `block`, `offer`, `figure`, `job`, so a learner-visible thing finds its records |
| `chosen_ref` | What won, or null |
| `decided_by` | The rule, policy or route: `lane_quota`, `mixture`, `router_llm`, `prefetch_eu_v1` |
| `rule` | Why: a named code (`chooser_error`, `forced_items`, `no_measured_latency`, `sampled_eu_positive`) |
| `alternatives_json` | `[{ref, p, score, lost_by}]`: each alternative, its score or probability, and the rule that excluded it. Capped at 50, with an overflow count per rule |
| `facts_json` | The inputs as of that moment that explain it, as numbers, ids and codes: `{timeout_s, waited_ms, p_open, wait_min, cost_min, waits_n}` |
| `versions_json` | Tag, policy or prompt version, model id, seed, and the switches that changed this decision |
| `detail_table`, `detail_id` | The rich row: `router_decisions`, `ad_selections`, `interactive_figures`, ... |
| `error_type`, `error_where` | On failure: the exception class and `module:function:line`. No message by default, following the owner's Oct 24 rule that a traceback can quote what the code read, so it goes to the log at DEBUG with the trace id (`daily_plan/engine.py:4935`'s pattern) |
| `created_at` | |

**What happened next** isn't a column. It's the next record whose `parent_id` is this one, the `detail` row's own outcome (`router_outcomes`), or a presentation and attempt reached from the subject.

**In Python:** `provenance.DecisionRecord` (frozen dataclass), `provenance.write(connection, record)`, `provenance.current_trace()`. A pure function returns the dataclass; it never writes. Writing joins the caller's transaction where there is one, otherwise it takes its own short one. A failed write logs a warning and never changes the decision.

### 3.3 The trace id

**Born** once per learner-visible action:
- sidecar: `learnloop_sidecar/server.py:_handle`, per RPC;
- phone: `learnloop_mobile/runtime.py:250`, which dispatches the same handlers;
- MCP: `learnloop_mcp/server.py:364`;
- CLI: the root callback.

**Carried** by a ContextVar. Threads already start in a copied context (`router_runtime.py:495`), so router jobs inherit it with no change.

**Across a queue:** enqueuing a job writes a `job_enqueued` record with the job id as subject; the worker looks it up and continues that trace. No job table changes. So submit, grade, diagnosis and follow-up generation share one trace.

**Across actions:** the next plan decision is a new trace, and its `parent_id` names the record of the attempt its key already depends on (`objective_chooser.py:1225`). That closes break 1.

**Model calls** get a real `model_call_receipts.trace_id` column, set from the ContextVar in `db/stores/model_calls.py:45`. That closes break 2 without moving the decision id, which feeds the mix's seed.

**Logs:** `learnloop_sidecar/logging.py:84`'s `log_event` adds the trace id, so logs join through it.

### 3.4 Replay and persisted meaning

Writing a record changes no replayed meaning, for these reasons, each with a test:
- no replay or rebuild code can reach the table (import closure and a SQL scan, in the style of the upgrade proof);
- the role is `RECEIPT`, so rebuild never clears it;
- AD's guard classifies it as not readable by AD;
- `model_call_receipts.trace_id` is nullable, and no projection reads it.

Old decisions keep their rows and get no backfilled records. `why` reads old rows through a small reader labelled "reconstructed" (§3.6).

### 3.5 The entry point

```
learnloop why [latest | <trace-id> | <record-id> | attempt:<id> | item:<id> | block:<id> | figure:<id>]
              [--kind k] [--first-build] [--payload] [--json] --vault V
```

- **Read-only:** `connect(path, read_only=True)`, no sync and no maintenance.
- **Answers,** for each decision: chosen; alternatives, each with score or probability and why it lost; the inputs as of then; who decided, with versions and seed; what happened next; anything discarded, including calls in the trace that finished late or have no decision (S4, S5 derive from this rather than from new writes).
- **`item:<id>`** keeps today's `why` question and adds exclusions.
- **`--payload`** reads the prompt and output through the existing receipts, on the desktop's CLI only.
- **The glass-box view** reads the same function through one RPC, `why.get`, which returns ids, numbers and codes, not payloads. The UX stage draws it. It isn't on the phone's allowlist.
- `learnloop router trace` and `trace-evidence` become views over the same reader.

### 3.6 The four real cases, and how they're tested

| Case | How it's answered | From |
|---|---|---|
| **Nov 7, router LLM answers discarded by the 8 s timeout** | `plan_block`: `facts.timeout_s = 8`, `facts.waited_ms`, the mix's alternatives. `model_answer`, `decided_by=router_llm`, `status=timeout`. Receipts with this `trace_id` finishing after the decision's `created_at`: `why` prints "answered N s late, discarded", with `--payload` showing the answer | B1, B2 |
| **Nov 8, offer withdrawn with `forced_items`** | `offer_withdrawn`, `rule=forced_items`, `parent_id` = the offer's `plan_block`, `alternatives` = the forced items, `facts` = their workflow and source attempt. The next `plan_block`'s `parent_id` = this record. Under IH2's switch the case becomes one contest decision showing both with their chances | B3 |
| **Nov 8, figure stored failed for a bad prediction** | One `figure_author` per attempt: `status`, `rule=prediction_invalid`, typed problem codes, prompt version, model; `detail` = the `interactive_figures` row. Since `214c206ff1` a bad prediction drops only itself: `rule=prediction_dropped` | B4 |
| **Why automatic pre-builds started after 12 skips** | `figure_prebuild` per candidate: `rule=no_measured_latency`, then `sampled_eu_positive`; `facts.waits_n`, `wait_min`, `cost_min`, `p_open`; versions with the seed. `why --kind figure_prebuild --first-build` shows the last skip, the first build, and the measurement that changed between them. My reading of the code (no 12 exists; every skip before the first measured latency; EU then positive with cost 0) is a hypothesis until rows confirm it | B4 |

**The honest limit.** Those four events happened before these records exist. No backup can make them answer from `decision_records`, and the Nov 3 copies predate them too. So there are two tests.

**1. Staged, runs in every suite (`tests/test_why_cases.py`).** Each case is staged with fake models and a synthetic vault: a slow LLM past the wait, then a late answer; a probe arriving while an offer waits; a figure author returning a bad prediction; a run of pre-build passes before and after the first measured latency. Each asserts the fields above from `why --json` alone.

**2. Real rows, on a fresh backup (`tests/test_why_real_cases.py`, marker `owner_vaults`).** It runs once the owner supplies a backup taken after Nov 8:

```
# the owner, or an agent with the owner's fresh backup path:
#   copy with learnloop.db.copies.copy_tree_with_databases into fixtures-local/why-cases/
LEARNLOOP_OWNER_VAULTS=$PWD/fixtures-local/why-cases \
  systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G \
  uv run pytest -m owner_vaults tests/test_why_real_cases.py -v
```

It finds, by date and shape, rows from Nov 7-8 on `arxiv_v2`, and asserts what `why`'s "reconstructed" reader can give from rows of that age:
- **Case 1:** a `router_decisions` row with LLM status `timeout`, and its receipt joined through `boundary_key`, output present or the reason it's absent.
- **Case 2:** the `expired` response with `forced_items`, plus the time-ordered next decision and workflow rows, labelled as inferred.
- **Case 3:** the `interactive_figures` row with `verification='failed'`, its reason and call rows.
- **Case 4:** the count of skip rows before the first non-skip per trigger kind, and the time of the first press or completed `figure_author` call. It reports whether that count is 12 and whether the first measurement falls between. If it doesn't, the hypothesis is wrong and the owner is told.

Failures print ids and field names only. Nothing from it goes in a tracked file.

**A later backup completes it:** after B4 has been live through a real timeout, withdrawal, figure failure and first build, the same test finds native records, and asserts they answer without the word "reconstructed".

**Verified by a reader without the code.** A fresh agent with no code access gets only `why --json` output and the four questions, plus the past-bug sample in §6, and writes the answers. The owner judges them.

### 3.7 Storage and protection

**Storage.** Rows are small: ids, numbers, capped lists. Exclusions are aggregated by rule, with counts and a few ids. Assume at most about 1 KB a row and about 30 rows per attempt cycle (this is an estimate; B6 measures it on a copy-shaped synthetic journey). `router.payload_retention_days` prunes `alternatives_json` and `facts_json` on old rows and keeps the row (migration 254, the arc B fix round: the no-update trigger allows only that, to fixed placeholders, on rows over a day old; startup maintenance runs it). If growth passes 5% of a vault's database per month, B6 tightens what it records by rule. Payloads aren't duplicated: the receipts already hold them.

**Protection and blindness.** The proportionate bar: a row holds no prose. A test checks that `facts_json`, `alternatives_json` and `rule` contain only numbers, ids and code constants, with item text planted in the fixture. No model context reads the table, and no grader context can, enforced as AD's guard is. `why.get` returns no payloads, and `--payload` reads only what the receipts already hold, on the owner's own desktop CLI. A trace therefore can't move protected text anywhere new.

### 3.8 Inventory: what has no record today, and where it's covered

Status after B8: every row below is either recorded or written down in ADR-017 with the rows that answer it instead ("B8: boundaries with no record, and why not"), so the inventory has no silent gap.

| Gap (map) | Debugging value | Step | Status |
|---|---|---|---|
| Chooser crash S1; timeout S2; provider failure S3; `card_error` S6 | Highest: cost the owner real time | B2 | Recorded (`plan_block`, `model_answer`) |
| Orphan calls S4; eviction S5 | High; derived at read, no write | B1, B2 | Derived by `why` (`discarded`, `unclaimed`) |
| Withdrawal; check draw or place failure; lesson builder crash; AD unavailable; head mismatch S12; eligibility on ordinary serves | High | B3 | Recorded (`offer_withdrawn`, failed children, `ad_slot`, `serve_eligibility`); a plain `SERVE` is its presentation row |
| Figure filter S7; reason S8; stoppages S9; salvage S10; author refusal; unseeded RNG | High | B4 | Recorded (`figure_prebuild`, `figure_prefetch_filter`, `figure_prebuild_stop`, `figure_author`); rich jobs' per-attempt codes are B8's open item |
| Disabled Decider and lost text S11; refused decision row S13; lost logged check S14; refused spend | Medium | B5, B8 | Recorded (`decider_judgment`, `router_decision_row`, `followup_gate`, `spend_admission`); B8 added S13's other half (a plan logger that raised) and the shared daily caps' and the lesson envelope's refusals. The other spend catchers keep their own rows (ADR-017) |
| Scheduler skip S15; slate exclusions; serving exclusions outside offers | High (daily-loop bug 2) | B6 | Recorded (`slate`); the quick check and `find_practice` are learner-initiated selectors whose exclusions `why item:<id>` re-derives (ADR-017) |
| Held grade; grading verdict; diagnosis attribution; follow-up value; VOI forecast failure; causal probe's router link; probe selection; AD generation refusal; hint ladder's missing client; `decision_receipt_id`'s overload | Medium to high; several read only by outline | B6, B7, B8 | Recorded (`grade`, `grade_held`, `diagnosis`, `followup_value`, `voi_forecast`, `probe_offer`, `probe_value`; B6 split the parameter). AD generation refusal and the missing hint client are answered by `ingest_jobs` and `help_assists` rows; B8 added `ad_commission_skip` where the job's result mislabelled a guard denial |
| Teacher lesson and check; Reader retrieval; ingest routing; route fallback; retries; re-read and alias; curriculum path; FSRS rating and elapsed; device eligibility's failure | Lower; read first, record or write down why not | B8 | Recorded: the lesson's `budget` close, the curriculum path's daily re-judgment (`curriculum_path_refresh`), the FSRS review on the grade (`facts.fsrs`). Written down in ADR-017 with the rows that answer them: the rest. Open: the route fallback on the receipt (a migration), ingest's primary-failure class |
| Background AD denials outside the plan's phases | Low; the JSONL counts them | B3, B8 | `ad_guard_denials.jsonl`, by the owner's 2026-10-21 decision (ADR-017) |
| Learner protection, a per-call read | Recorded only where it excludes something from a decision (B4, B6). Not per read | none alone | As stated |

**What it replaces.**
- **Kept:** `router_decisions` and payloads, `router_objective_traces`, `ad_selections` (the model for the shape), `judgment_ledger`, `plan_presentations`, the causal receipts and the other rows in the map's §4.3. They're ledgers with guarantees, and the playbook keeps them immutable.
- **Gone:** the JSON join from decision to receipt (new rows), free-text `owner_id` as the join, AD's JSONL denial log if nothing else reads it, in-memory build notes, `why`'s writes, and per-subsystem entry points as separate code.
- **Net concepts:** +1 table, +1 small module, +1 RPC; −4 entry points and −3 ad hoc logs. It's the one new concept this strategy adds, and it's justified because no existing mechanism can answer the owner's four cases.

**ADR-017** records all of this. **"Decision" isn't renamed everywhere;** `router_decisions` stays.

## 4. What not to do

| Tempting | Why not |
|---|---|
| **Split `Repository` into stores wholesale** | 943 methods, 406 importing modules: a very large diff that proves nothing and changes no decision. Dead methods go (C1), and a method moves to its store when a step touches it. |
| **Break the 191-module import cycle head-on** | The frozen-cycle contract records it honestly. Function-local imports are the cost, and removals, E1 and E5 cut edges where they pay. Re-measure at Z2; no separate arc. |
| **A policy, action or sensor registry; a plugin framework; dependency injection** | The owner ruled them out, and a plain `match` and small modules do it. E6 stops if it adds more than it removes. |
| **Make `decision_records` the system of record, or replace ledgers with it** | Raw ledgers and receipts are immutable by the playbook, and bundles must exist before the answer. A log can't replace them (Nov 3 item 4). |
| **Backfill records for old decisions** | A record written now would claim to know inputs nobody stored. `why` labels what it reconstructs instead. |
| **Trace spans, OpenTelemetry, a log store** | A new dependency and concept for a single-user desktop app. One table and a ContextVar answer the questions. |
| **A record at every function, or per protection read** | Storage, noise, and a false sense of coverage. The rule is meaningful boundaries, and an exclusion that affected a decision. |
| **Storing prompts or free text in records** | The receipts hold them under existing rules. A second copy is a new leak surface. |
| **Delete Appendix C's 715 definitions** | They're candidates from a name scan. Its misses include `importlib` and generators. Only re-proven rows go. |
| **Delete by tag without the floor, or remove old-row readers** | Replay reads old rows by shape at any tag. Pruning them breaks real history. D5's review hunts for exactly this. |
| **Prune below-floor branches before moving the test vault** | Most tests would lose their path while the real path stays less tested. D2 comes first. |
| **Squash the 237 migrations into one baseline** | Saves little reading, since nobody reads them in sequence, and it would break coordinated migrations and old-copy upgrades. |
| **Merge AD's two guard lists, or weaken them, to cheapen a new table** | They enforce a real firewall (B4). A2 makes the fixture cost go away; the guard keeps its cost. |
| **Untrack generated `Reference/`** | The owner reads it in Obsidian, and validators and the final docs stage use it. With stamps gone, what's left is real change. |
| **Reduce rollout draws or shorten the deadline to hit the speed target** | That changes decisions to win a number. |
| **Cache across jobs or add a read-cache layer for speed** | Router speed 2 already held reads within a job, and the remainder isn't there. F3 only if measured. |
| **Consolidate `router/`, `router_objective/` and `daily_plan/router_*` into one package first** | A rename doesn't help until E2-E6 say what's left. E9 renames only what misleads. |
| **Rename the FSRS `difficulty` columns** | A migration with no learner benefit. H1's guard test keeps the two apart. |
| **A separate comment sweep** | Touch it, fix it. A sweep is a large diff with nothing to test. |
| **Polish screens; rewrite settings** | The UX overhaul follows. This strategy only lists what removals affect. |
| **Test-speed infrastructure here** | It's on `tests/audit-speed`, by the owner's word. |
| **Rework `build_due_queue` or the engine's traversal beyond I2 and E6** | `daily_plan/engine.py` (5,978 lines) carries real policy. Taking out only the pieces with a named cost keeps review possible. |
| **Bound AD eta inside the refactor** | It's a modelling change for the owner, with its own successor. |

## 5. The vault plan

**Order (owner, Nov 8).** Job 1's audit is the input (§8 of the map). Each step fixes the notes it touches. The one full update is the last stage, by Codex, after the UX overhaul, so it describes the final screens. This overrides the older prompt's "first docs-only step". Only A4 runs early, for a wrong privacy statement.

**Each step's gate:** the four validators pass, and the notes named in its step are true. Validators check links and coverage, not truth (§8), so the review reads the notes it changed against the code.

**Inside the refactor:**

| Note | Change | Step |
|---|---|---|
| Content Pipeline, Import Canonical Sources, Privacy and Trust | Fix the privacy claim | A4 |
| Developer Map | Replace "next-item policy lives in scheduling" with §6's table | A4, then each arc |
| Generated `Reference/` | Lose per-note stamps; `_generated.md` | A1 |
| Inspect Persistent State, State and Persistence | Head path; head number by reference, not literal | A2 |
| Algorithm Versions and Reproducibility, Version Registry, playbook | Defaults file; floor; upgrade table | A3, D1, D3 |
| ADR-017 (new) | The decision record | B1 |
| ADR-018 (new) | The floor, the upgrade table, the kill-switch rule; supersedes the chain parts of the playbook | D1, D3, D7 |
| ADR-019 (new) | The router as one decider | G2 |
| "Debug a decision" workflow (new) | How to use `why` | B9 |
| ADR-005, ADR-011, ADR-012, ADR-003 | Mark as amended or superseded when the step makes it so | C4, D, C1 |
| AI Architecture | Provider table | C4 |
| Adapter Architecture, Package Boundaries, Testing | As removals land | C7, D2 |
| Router Objective (new, short) | Where the objective, rollouts, actions and sensors live | E5, E6, E7 |
| Attempt Processing, Learning System, Diagnosis, Scheduling and Selection | Each paragraph the step made false | D4, I1, I2, G1, G2, H |
| Refactor Status | Points to this strategy; deleted at the close | S0, Z2 |

**For the last stage (Codex, after the UX overhaul):**
- **Fix** everything in the map's §8.1, §8.3 and §8.5, re-checked then: the first hop (Home, Architecture Overview), Maps, Examples' stale preconditions (`research_on_learning.md`'s path).
- **Add** notes for §8.2's gaps, short and few: Teacher, Figures, Follow-up serve, Phone, MCP and protection, Adaptive difficulty, Decider and held grades. `learnloop_mobile`, `learnloop_mcp` and `apps/learnloop-mobile` get module and desktop notes.
- **Redraw:** Architecture Map, Data and State Map, Developer Map, User Journey Map, Pipeline Map, the canvas (or delete the canvas: it has 14 nodes and is linked once).
- **Merge or delete:** one-link notes (Glossary, Status Legend, Tag Taxonomy, Documentation Dashboard, AI Operation Registry) merged where they duplicate; workflows that describe removed paths deleted; ADR-001, 008, 009's stale counts replaced by references.
- **Mark:** Design Decision Index brought up to date, with new ADRs for the router objective, teacher, phone, MCP, S0, Decider and GLM-OCR as Codex finds them undecided on paper.
- **The onboarding path:** Home → Architecture Overview → the relevant Concept, Workflow and Map → the code. The gate: a new reader locates §6's sample changes from the vault alone.
- **Gates:** every validator, every file:line citation re-checked, every Example's commands dry-run on a scratch vault.

## 6. Success measures

Measured at S0 and Z2 with one script and the same commands.

**Size and rules**

| Measure | Map's baseline | Target |
|---|---|---|
| Python files, all packages | 1,268 | down 6-11% |
| Raw lines, code lines | 624,515; 436,042 | down 5-9% (the top of that range needs `experiments/` gone; `projects/` stays by the owner's decision, and the TUI stays until its rebuild, so this estimate may fall short) |
| Functions over 200 lines | 81 | down, no fixed number; `build_due_queue` and `_compute_resolved_grade_application` out of the list |
| Root `*_upgrade.py`; all upgrade modules | 40; 42 | 0; 1 table module |
| `Repository` methods | 943 | at least 58 fewer |
| `mvp-0.N` literals: code / docstring / comment | 285 / 949 / 3,070 | under 60 / under 300 / under 500 |
| Tag gates: constant at the floor / all | 79 at 0.43 / 90 | 0 / only tags above the floor |
| Kill switches at or below the floor | 27 named, at least | 0, except any the owner keeps |
| Import-linter contracts | 43 | lower, no fixed number; each kept contract readable |
| Removed list | | every removed feature named in Z2's report |
| Database size | private file | reported before and after each drop |

**What a change costs.** Files edited, counted on a scratch branch at Z2 with the same changes.

| Sample change | Today | Target | Where after |
|---|---|---|---|
| Threshold or default (40 s timeout) | 1 line, 46 digests, 12 test files, 1 note | 1 line; 1 golden line; at most 1 test literal; 1 note | `config/schema.py` |
| A new table | Migration, roles, AD's 2 lists, store; 24 files renamed; 68 pinned tests; 481 notes | Those 5; 2 fixture files; 0 pins; a handful of notes | |
| Speed work with no version (router speed 2) | 615 files (9 source, 593 notes) | about 110 at most; lower if per-module test lists go | |
| A new tag | 9 source files, 36 pinned tests, 101 digest lines | 1 constant, 1 table row, 1 test row, plus its switch | `algorithm_versions.py`, `ops/upgrades.py` |
| Add a sensor (objective) | 11, 7 files | `daily_plan/sensors.py` and its test | |
| Change an objective term | 3, 6, 4, 1 files | `router_objective/objective.py` and its test; a switch if it's a successor | |
| Swap the mixing rule | 13 files, 47 lines of rule | `mix.py` and its test; a new tag adds its row and switch | |
| Add an action | 20 files | `router_objective/actions.py`, its test, a trace label; plus a screen if it has one | |
| Change a seed or prior | 1 line, plus digest churn | As a default | `config/schema.py` |
| Prompt | 1 file and a version bump, plus goldens for each switch-off parity test | 1 file and bump; goldens only for that prompt | its module |
| New signal to model contexts (TE0) | 11 files | the signal's function, and one line in each builder that uses it | `learner_signals` |
| New step in a pipeline | not reducible to a number; FG1, IH2 | Developer Map names the seam; time-to-locate measures it | |
| A model route | not measured: no recent commit changed one alone | measure at S0 on a scratch branch; target: 1 default, 1 golden line | `config/schema.py`, `ai/routing.py` |

**Speed**

| Measure | Baseline | Target |
|---|---|---|
| Next right after feedback, large copies | Median 2,676 ms, 16 of 21 over 2 s, against mvp-0.49's 2,250 ms, 25 of 30 (a pinned week) | No worse than mvp-0.49's by the same method, after IH's prefetch |
| Connection opens per job | 17 | about 5 |
| Decision values at a fixed draw count | | Byte-identical across every speed step |

**Tests (item 13).** The test branch owns infrastructure and the "before" is S0's, because it lands first.

| Measure | Baseline | Target |
|---|---|---|
| Serial; `-n 8 --dist worksteal`; `-m durability` | S0 (Nov 7's `-n 8` was 59:22 before that branch) | Same commands at Z2. No fixed target; each removal reports its seconds |
| Upgrade and successor family | 4,364 test seconds, 16% (Nov 7) | under 3% |
| Tests run on the served path | 271 files default to mvp-0.6 | 0 |

The order: removals first (C1-C7, each with its tests), then D3 (the chain tests, the largest family), then D7 (predecessor-exact tests), then Z2. Nothing that a test proves is dropped without a named replacement, and each landing note says what still proves it. The test branch has already run by then, so a second usefulness pass over what's left is the owner's call at Z2, not a planned step.

**Inspectability**

| Measure | Target |
|---|---|
| The four real cases | `tests/test_why_cases.py` passes always; `tests/test_why_real_cases.py` passes on a fresh backup; the no-code reader answers |
| "The latest decision", "this attempt", "this block", "this figure" | `why` answers each with chosen, alternatives, losers' reasons, inputs, decider, versions, seed, next |
| Silent sites S1-S15 | Each has a fail-first test, or a line in ADR-017 saying why not |
| A decision with no record | B8's inventory lists none unexplained |

**Time to locate.** A fresh agent, given only a symptom, the vault and `why`, with minutes and files opened recorded at S0 and Z2:
1. "Dormant or resolved learning objects are still served" (`docs/reviews/daily-loop-bugs.md` §2).
2. "Choosing a help style changed nothing" (`docs/reviews/owner-capture-2026-10-25-fixes.md`, B2).
3. "The scheduler offer does not belong to this item/session" (same review, B4).
4. A router decision that fell back to a rule: which model failed and how.
5. "Where do I change the mixing rule, an objective term, a route, a threshold?"

**Docs (at the last stage).** Every validator passes, and no note describes behaviour that no longer exists.

## Appendix A: corrections to the map

Fixed in place in `docs/reviews/architecture-map-2026-11-08.md`, under its "Corrections" section and at each row. Everything here was checked against the code on Nov 9.

| # | Map said | Actually | Effect |
|---|---|---|---|
| 1 | A new table renames a 48-file fixture, 4,510 lines | **24 files:** 22 renamed unchanged, 2 changed. `--numstat --no-renames` counts each twice (2,261 + 2,249 lines) | A2's baseline |
| 2 | 70 files name the head's path | 68 test files (70 lines), plus 3 scripts: 71 files | A2 |
| 3 | 4,302 `mvp-0.N` literals (read as code) | By tokenizer, 4,304: **3,070 in comments, 2,319 of them in `template.py`; 949 in docstrings and multi-line strings; 285 in code strings** | The cost is mostly history in comments. A3 and D3 remove most |
| 4 | `substrate_cutover`: 0 imports, path strings only; DEAD | **Imported at runtime:** `MODULE_INVENTORY` and `_resolve_module_constant` (`params/parameter_registry.py:3150`) `importlib` it. The same goes for `progression_policy`, `progression`, `predictive_targets`, `reentry_adapter`, `shadow_components`, `kinship_feature`, `controller_cutover`. Deleting one without its entries breaks registry refresh | C1 and C2 split |
| 5 | `sim/ad_gates`: DEAD, 1 test file | **It's the library of `test_ad23_sim`, the suite's slowest file (734 s),** with `sim/ad_synthetic` (1,289 lines, not listed) | Not a removal; handed to test usefulness |
| 6 | `client_contract`: DEAD, "may be a pin by design" | A generator: `tests/test_mobile_phone_contract.py:49` writes and compares committed files with it. **Live as a tool** | Kept |
| 7 | Upgrade importers are `cli/app.py`, the next link and two callers; 40 modules | **42 modules** (40 at root, `ops/vault_upgrade`, `diagnosis/recurrence/upgrade`), and `learner/recall_calibration.py:16` imports `vault_upgrade`'s constants | D3 |
| 8 | "Replay imports none" | **Proven, and stronger:** none reachable by any import from 6 replay and serving roots. **But** every writing open in the CLI and sidecar installs the chain's completion, and a journal naming an old link walks it | D1, D3 |
| 9 | Tests start from old tags: the head fixture at mvp-0.6 | **Larger:** `AlgorithmsConfig`'s default and `create_basic_vault` are at mvp-0.6. 437 test files use that vault, 271 name no version. Not in the map | D2 is new |
| 10 | About 40 pure gates, about 38 paired | The 79 and 11 are confirmed by AST against the real chain (36 sets constant, 11 varying). The split isn't reproducible: a syntactic pass finds about 10 paired and misses some | D4-D6 read each |
| 11 | S1: answers, trace and payloads are dropped | Exact on the decision row, trace and payloads. The answers survive in `model_call_receipts` if the call finished; a fallback row with `chooser_error` is written. The exception's message is lost | B2 |
| 12 | 53 `table_info` sites in 39 files | 54 in 40 at this tip | Small |
| 13 | §7.4's DEAD rows don't list them | **Also unreachable by import from any entry:** `scheduling/progression`, `predictive_targets`, `reentry_adapter`, `short_session`, `sim/ad_synthetic`. Not orphans: `figures/source_check_harness.py` (read as text, `figures/source_check.py:90`), `ingest/detect.py` (re-exported) | C2 |
| 14 | §9 "48" in the stage table (TE2, TE3a, V3, IH) | Same double count | Rows annotated |

**Checked and held:** the 8 s and 40 s lines; `DEFAULTS_SNAPSHOT_BY_ALGORITHM` has no `src` reader; S2, S7 and S8 as described; `decide_probe`'s two sites; `figure_prefetch_decisions` has no reason column; `_flat_change` leaves no note; no 12 in the pre-build code; the scalar's readers I opened; 943 `Repository` methods; 43 contracts.

**Not re-checked:** every other row. §4.1's (o) rows stay unread until B7 and B8. Steps prove what they rest on when they run.

## Appendix B: one record of each fact (Nov 3 item 2)

The owner. A step moves a reader to it (G5), and a duplicate stops being written only after that. Rows stay. "Guarantee" means written before the answer, and it can't come from logs.

| Fact | One owner | Also held today | What happens |
|---|---|---|---|
| Predictions before the answer | `causal_blind_prediction_bundles` | ids in `probe_presentations` | Stays; guarantee |
| Locked hypotheses | `hypothesis_sets` | Second lock at `enter_episode` | Stays; guarantee; one lock if G4 goes ahead |
| Posterior at selection | `probe_presentations` | | Stays; guarantee |
| Which prediction matched | `causal_discriminating_observations` | Features in `probe_observations`, grading evidence | Stays; read by the 8 modules in §2.10 |
| Belief after an observation | `probe_observations` (episode posterior) | `support_scores`, `resolved_factor` | G3, G4 |
| Attempt, presentation | `practice_attempts`, `probe_presentations` | `causal_probe_decision_receipts`, observations | Join by id; stop copying only where nothing reads the copy |
| Whether to probe: formula and EVSI provenance | `causal_probe_decision_receipts` | Router's `observational` field | Stays; the verdict goes at G2, the facts stay |
| Burden minutes | Trace | Receipts | Trace |
| Learner's "Not now" | `causal_probe_preference_events` | Workflow's release reason | Statement stays there; the workflow names it |
| Cold outcome | `causal_cold_outcomes` for non-measured dispositions; `router_outcomes` R_cold, `causal_cold_verifications` | `forecast_receipts`, `decision_measurement_events` | **Two rules for "delayed outcome" exist (map §4.4).** G5 names one, or writes down why two |
| Why this choice | `decision_records`, pointing at the row above | | New; B7 |

`decision_features`, `router_outcomes` and `forecast_receipts` share no row with the receipts, so there's nothing to merge: the overlap is by fact only.

