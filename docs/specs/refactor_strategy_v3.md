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

<!-- NEXT -->
