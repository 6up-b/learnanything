# Refactor status

- Arc E is closed (E1 to E6, its adversarial review and fix round, and the rows due at its close; E7 waits for the evidence packet spec). The UX journey audit has two parts ([ux-journey-audit.md](ux-journey-audit.md), [ux-journey-audit-2.md](ux-journey-audit-2.md)): the owner asked for its fixes on Nov 19; fix stages 1 to 4 and the waiting indicators the owner asked for are on main with UX-1; thirteen walks on the fixed application gave fifteen new defects (UX-13 to UX-27) and a re-ranked list of stages, of which "First questions arrive" is being built. Arc G: G1, the algorithm tag `mvp-0.61` (G3-1 with the evidence reading fixes and the forgetting-clock cases; the owner's Nov 19 choices), the G6 design, the protection surface matrix (G6.1), the fixes for the six defects it confirmed and the table of which set each surface reads (G6.2) are on main; G6.3 was stopped by the cost rule. Next in arc G: G2's behaviour step (its five preparing steps are on main; it waits for the owner's four decisions), then the rest of G6 (the surfaces the matrix does not drive, display accounting).
- On main: the rebuild fix as `mvp-0.60`; the whole `repositories.py` split (L2a–L2d); the L1b cycle cuts (largest import component 84); E1–E6 (the router's choice is a pure function, its job control and trace assembly are their own modules, the objective's terms are apart from the rollouts, and an action kind has one guard test and one how-to list); G3's measurement of the two diagnosis beliefs; S1, S2 and M1; the K5 review with its two high fixes; `replay.ledger_bounded` removed.
- After E: G1 and G3, then K6 and G6, then G2; G4 only if G3 finds disagreement. H1 and H2 follow. E7 is built once, as the evidence view of `docs/specs/spec_evidence_packets_v1.md`.
- The owner decided the three K5 questions on Nov 18 (a repair followed by ordinary practice and a passed cold check confirms the repair; a skip leaves the forgetting clock and an answered attempt without a review restarts it, the due date staying; a certificate probe keeps counting retention with ordinary practice). The owner still needs to decide: the K5-8 paths that do not follow the clock rule (they need a tag), I2's reads on the decision path, K2.4c part B, the CLI-only code for L3, the diagnosis questions for K9.4, K9.13 and K9.17, and the open questions in the two specs.
- Decide H3–H6 with the AD memory spec. Do K8 and K7 before the terminal app rebuild or MCP v2. L5, T2, T5 and Z run at the close.

The orchestrator updates this file in each landing commit. This snapshot is the landing of `mvp-0.64` (K9.4: an untaken repair episode ends) (Nov 21), at `mvp-0.64`, and the owner's Nov 19 decisions (the fixes of the UX audit; the forgetting-clock cases and "no update" for exposed probe answers in `mvp-0.61`; waiting indicators).

## Baseline and arc A

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| S0 | Measure the baseline and refresh the map | landed | `7a2b108e16` | [refactor-baseline.md](refactor-baseline.md) | — |
| A1 | Remove per-note stamps from generated reference notes | landed | `1c0e9653c1` | [refactor-a1.md](refactor-a1.md) | — |
| A2 | Give the head test fixture a stable name | landed | `f52d13b937` | [refactor-a2.md](refactor-a2.md) | — |
| A3 | Replace frozen digests with one readable defaults file | landed | `00d1a77885` | [refactor-a3.md](refactor-a3.md) | — |
| A4 | Correct privacy guidance and refresh developer directions | landed | `9ce90f7e96` | [refactor-a4.md](refactor-a4.md) | — |
| A5 | Add bug-finding lint rules to every gate | landed | `14722beef0` | [refactor-a5.md](refactor-a5.md) | — |
| A6 | Shorten landing gates and move simulations to arc close | landed | `1fcce2517e` | [refactor-a6.md](refactor-a6.md) | — |

## Arc B

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| B1 | Add decision records, trace IDs and read-only why | landed | `0f309956e3` | [refactor-b1.md](refactor-b1.md) | — |
| B2 | Record router failures and their causes | landed | `52ecd640ca` | [refactor-b2.md](refactor-b2.md) | — |
| B3 | Record forced items, withdrawals and boundary failures | landed | `1ddf7c88ed` | [refactor-b3.md](refactor-b3.md) | — |
| B4 | Record figure builds, exclusions and author attempts | landed | `0ed4761bf0` | [refactor-b4.md](refactor-b4.md) | — |
| B5 | Record Decider refusals and spending refusals | landed | `45d56d6dc4` | [refactor-b5.md](refactor-b5.md) | — |
| B6 | Record scheduler slates and serving exclusions | landed | `ac370fb4f0` | [refactor-b6.md](refactor-b6.md) | — |
| B7 | Record the attempt chain and continue job traces | landed | `837a4e63bc` | [refactor-b7.md](refactor-b7.md) | — |
| B8 | Record the remaining high-value decision boundaries | landed | `7ad0437811` | [refactor-b8.md](refactor-b8.md) | — |
| B9 | Use one why reader and test real cases | landed | `a8b3ab6f68` | [refactor-b9.md](refactor-b9.md) | — |

## Arc C

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| C1 | Delete proven dead modules and leaf definitions | landed | `d728249360` | [refactor-c1.md](refactor-c1.md) | — |
| C2 | Remove dead modules with their registry entries | landed | `11c3bfaa2b` | [refactor-c2.md](refactor-c2.md) | — |
| C3 | Remove unused calls and unread config keys | landed | `c08fe44d94` | [refactor-c3.md](refactor-c3.md) | — |
| C4 | Retire the Codex transport and its configuration | landed | `f93a483ef7` | [refactor-c4.md](refactor-c4.md) | — |
| C5 | Remove Golden Path screens, RPCs and code | landed | `5ba0fded47` | [refactor-c5.md](refactor-c5.md) | — |
| C6 | Remove dead controller and kinship-era code | landed | `4857bd99ab` | [refactor-c6.md](refactor-c6.md) | — |
| C7 | Apply the owner's choices about conditional removals | landed | `2564375ac3` | [refactor-c7a.md](refactor-c7a.md) | — |
| C7a | Move the terminal UI dependency to an extra | landed | `2564375ac3` | [refactor-c7a.md](refactor-c7a.md) | — |

## Arc J

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| J1 | List candidate tables and correct their roles | landed | `f930ecb2cf` | [refactor-j1.md](refactor-j1.md) | — |
| J2 | Drop the first approved family of tables | landed | this commit | [refactor-j2.md](refactor-j2.md) | Five of group A's eleven dead tables are dropped (migration 260), behind a guard that refuses a vault where one holds a row. The other six wait: one is the parent of a retired-but-read table, five still have unreached code that a test runs. `hypothesis_sets` is RAW_LEDGER (landed Nov 20) |
| J3 | Drop the next approved family of tables | waiting on | — | — | Owner decided on 2026-11-20: retired-but-read tables are dropped once the steps that own their readers have removed them. Next family: the six left from group A with their unreached code and tests, and group F's `lapse_episodes`; the two `p2_ladder` tables hold rows seeded by migration 084 in every vault, so the guard would refuse them: the owner's call |
| J4 | Drop the final approved family of tables | waiting on | — | — | Owner decided on 2026-11-20: as J3 |

## Arc D

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| D1 | Enforce the oldest supported tag at vault doors | landed | `1da959e7d7` | [refactor-d1.md](refactor-d1.md) | — |
| D2a | Run basic test vaults at the head tag | landed | `72ace2968a` | [refactor-d2a.md](refactor-d2a.md) | — |
| D2b | Move tests off old tags in passes | waiting on | — | [refactor-d2b5.md](refactor-d2b5.md) | A fourth pass over `mixture_env`'s default and the config-written tags the third pass lists |
| D2b part 1 | Retag shared fixtures and older successor test builders | landed | `16a9e3fd48` | [refactor-d2b.md](refactor-d2b.md) | — |
| D2b part 2a | Build the shared plan test vault at head | landed | `33c10723f2` | [refactor-d2b2.md](refactor-d2b2.md) | — |
| D2b part 2b | Move plan tests off old tags where possible | landed | `5f0d44269e` | [refactor-d2b3.md](refactor-d2b3.md) | — |
| D2b part 2c | Run the second pass over old-tag tests | landed | `6c114e2ae1` | [refactor-d2b4.md](refactor-d2b4.md) | — |
| D2b third pass | Review the remaining tests that name old tags | landed | this commit | [refactor-d2b5.md](refactor-d2b5.md) | 450 test cases moved to the head (vaults below the head: 2,493 → 2,043); eleven builders now default to the head; row stamps kept as data. Left: 187 passing cases not moved (mostly through `mixture_env`'s default) and 247 whose tag comes from a hand-written config or copied fixture |
| D2b fourth pass | Tests off old algorithm tags where the tag is not the subject, fourth pass | landed | this commit | [refactor-d2b6.md](refactor-d2b6.md) | 368 cases moved in 84 files (2,071 to 1,705); tests and helpers only, no assertion changed. What is left is the tag as the subject, except 54 cases that pass at the head behind shared wrappers and 84 whose tag sits in a hand-written config or copied fixture: another pass would not pay |
| D3 | Replace the upgrade chain with one table | landed | `9eb0194c2c` | [refactor-d3.md](refactor-d3.md) | — |
| D4 | Remove constant attempt, mastery and grading gates | landed | `41387e1236` | [refactor-d4.md](refactor-d4.md) | — |
| D5 | Remove constant rebuild, projection and doctor gates | landed | `a4bd9f2b77` | [part 1](refactor-d5.md), [part 2](refactor-d5b.md) | — |
| D6 | Remove remaining constant gates and unused version sets | landed | `b4c8fbad98` | [refactor-d6.md](refactor-d6.md) | — |
| D7 | Retire eligible switches and record the kept groups | landed | `52bbf14de9` | [refactor-d7e.md](refactor-d7e.md) | Replay-read follow-up in batch 1 part 5 below |
| D7 inventory | List switches and their readers before removal | landed | `00bdf58da8` | [refactor-d7-inventory.md](refactor-d7-inventory.md) | — |
| D7.0 | Report vault switches and hold the version floor | landed | `3405215424` | [refactor-d7.0.md](refactor-d7.0.md) | — |
| D7 batch 1 part 1 | Retire teacher weights and five practice switches | landed | `72b771471a` | [refactor-d7a.md](refactor-d7a.md) | — |
| D7 batch 1 part 2 | Retire cold-help and stuck prompt switches | landed | `5c561264c7` | [refactor-d7a.md](refactor-d7a.md) | — |
| D7 batch 1 part 3 | Retire eligibility and its predecessor cold lane | landed | `1d122fee33` | [refactor-d7a.md](refactor-d7a.md) | — |
| D7 batch 1 part 4 | Retire diagnosis split and shadow switches | landed | `250b0e16fe` | [refactor-d7a.md](refactor-d7a.md) | — |
| D7 batch 1 part 5 | Retire bounded replay and claim fixes switches | landed | `06082c1b73` | [refactor-d7f.md](refactor-d7f.md) | — (`replay.ledger_bounded` removed; `mastery.claim_fixes_enabled` kept: its retirement moves an identity shape pin) |
| D7 batch 2 | Retire placement, follow-up and stopping switches | deferred | — | [refactor-d7-inventory.md](refactor-d7-inventory.md) | D7 closed. Simulation needs the switches. |
| D7 batch 3 part 1 | Retire seven Today switches and their old paths | landed | `52bbf14de9` | [refactor-d7e.md](refactor-d7e.md) | — |
| D7 batch 3 part 2 | Retire the lesson, teacher and data capture switches | landed | `52bbf14de9` | [refactor-d7e.md](refactor-d7e.md) | — |
| D7 batch 3 last group | Retire the plan, router and restraint switches | dropped | — | [refactor-d7e.md](refactor-d7e.md) | Owner kept all three, Nov 17 |
| D7 batch 4 | Retire router objective switches at the floor | deferred | — | [refactor-d7-inventory.md](refactor-d7-inventory.md) | Arc E opens their file |
| D8 | Fix the four replay gaps pinned by tests | in progress | — | — | One landing per gap, in the design's order: same-second grades, retired items, the mastery seed, provenance |
| D8 retired items | Replay retirement at the correct point in history | landed | this commit | [algorithm-mvp-0.66.md](algorithm-mvp-0.66.md) | mvp-0.66, migration 263: each live application records the facet set it read in `attempt_lifecycle_inputs`, and replay uses it. Attempts from before the tag carry a labelled reconstruction from the predecessor's own replay |
| D8 same-second grades | Preserve commit order for grades sharing a timestamp | landed | this commit | [algorithm-mvp-0.65.md](algorithm-mvp-0.65.md) | mvp-0.65, migration 261: each new application records its sequence in `attempt_application_order`, and every prefix reader breaks a same-second tie by it. Attempts recorded before the tag keep their old order, labelled unknown |
| D8 claims | Re-anchor claims created after replay materializes state | landed | this commit | [algorithm-mvp-0.67.md](algorithm-mvp-0.67.md) | mvp-0.67, migration 265: the claims a learning object's mastery was first seeded from are recorded in `mastery_seed_inputs` where its row is first persisted, and replay starts from them. A starting-level change still affects only topics created afterwards (the profile setter's contract). Topics from before the tag carry a labelled reconstruction |
| D8 provenance | Fix the two reopened input provenance gaps | waiting on | — | — | One capture point for diagnosis inputs |
| D close fix 1 | Fix arc close serving and test gaps | landed | `7131b464c5` | [refactor-adfix1.md](refactor-adfix1.md) | — |
| D close fix 2 | Fix diagnosis stops, clocks and vault switching | landed | `6fffbc20c8` | [refactor-adfix2.md](refactor-adfix2.md) | — |
| D close rebuild fix | Preserve adjudications and avoid duplicate rebuild history (D-36, D-52) | landed | `41c1d97469` | [refactor-adfix3.md](refactor-adfix3.md) | — (shipped as `mvp-0.60`, no kill switch) |

## Arc E

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| E1 | Split the router's switches from the availability rule and the projection switches | landed | `50e5b760e3` | [refactor-e1.md](refactor-e1.md) | — |
| E2 | Extract the chooser's pure decision function | landed | `2bc640bf05` | [refactor-e2.md](refactor-e2.md) | — |
| E3 | Move job control and clocks out of choice | landed | `13925e8bbf` | [refactor-e3.md](refactor-e3.md) | — |
| E4 | Move trace assembly out of the chooser | landed | `8eb1c94b4d` | [refactor-e4.md](refactor-e4.md) | — |
| E5 | Separate objective terms from rollout arithmetic | landed | `f8300a3f00` | [refactor-e5.md](refactor-e5.md) | — |
| E6 | Put each router action in one place | landed | `8804080fcf` | [refactor-e6.md](refactor-e6.md) | The stop rule stopped the full design at step 0. The alternative landed with a guard test, one offer predicate, one definition of the refs and a how-to list. |
| E review | Adversarial review of arc E and its fix round | landed | `2632be75e9` | [refactor-efix1.md](refactor-efix1.md), [refactor-efix2.md](refactor-efix2.md) | Eleven findings (ledger ER-1 to ER-11): nine fixed, ER-5 by design, ER-2 left for the next algorithm tag. E-1 and E-2 are fixed in the same gate ([refactor-e-close-fixes.md](refactor-e-close-fixes.md)) |
| E7 | Build the shared view of evidence once | waiting on | — | — | The [evidence packet spec](../specs/spec_evidence_packets_v1.md) |
| E7b | Move shared learner signals ahead of E7 | dropped | — | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | Folded into E7 by the Nov 17 decision |
| E8 | Remove performance switches from learned model identity | deferred | — | — | Goes with F2 (owner, Nov 17: F2 only if Next after feedback is slow) |
| E9 | Rename misleading modules and move feature-owned files | closed (no eligible move) | this commit | [refactor-e9.md](refactor-e9.md) | Step 0 measured every root module's importers: 35 of 37 are imported by more than one production package, and the two single-package cases (`reader_learner_state` into `reader`, `app_launch` into `cli`) would each break an import contract. Nothing moves; the root keeps its modules. Done by a Codex worker |

## Arc F and RE2

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| F1 | Remove redundant column checks on current schemas | landed | `2b161923e6` | [refactor-f1.md](refactor-f1.md) | — |
| RE2 | Use one FSRS function for retrievability | landed | `68c61b9f1a` | [refactor-re2.md](refactor-re2.md) | — |
| F2 | Profile and streamline numeric policy arithmetic | deferred | — | — | Slow Next after feedback. Needs E5 and E8. |
| F3 | Profile and reduce the costliest SQLite reads | deferred | — | — | Revisit if F2 misses its target |

## Arc I

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| I1 | Extract the pure core of grade application | landed | `67a5364df0` | [refactor-i1.md](refactor-i1.md) | — |
| I2 | Extract pure due queue ranking from persistence | landed | I2a-I2c | [refactor-i2.md](refactor-i2.md) | Owner decided on 2026-11-20: superset reads, two pure stages (I2a, I2b, I2c). I2-2 (the read build's follow-up marks) stays open to arc I's close |
| I2a | The due queue's admission reads are gathered once before its decisions; each probe episode's value decision is computed at its consult from gathered values, with no repository | landed | this commit | [refactor-i2a.md](refactor-i2a.md) | Reads are within one SELECT of base on every build but one: an episode whose only reachable item is held by a not-yet-due check still costs about 2.2 to 2.5 times base reads (0.07 s at 300 items). I2b removes it by filtering on intent's whole gate once intent is frozen |
| I2b | Intent's view is frozen after the check split, the one intent read left; the teach-back site's value context has no repository; probe episodes are gathered only when an item past every gate could reach them | landed | this commit | [refactor-i2b.md](refactor-i2b.md) | Every measured build reads what the base reads; the corner case I2a left (an episode reachable only through an item a not-yet-due check holds) is back to base reads |
| I2c | The two pure stages, the persist call, `serve_due_queue` and `read_due_queue` replacing the flag | landed | this commit | [refactor-i2c.md](refactor-i2c.md) | `admit_due` and `rank_due` over gathered reads and frozen inputs, one persist call, `build_due_queue` renamed `serve_due_queue` (the flag had already gone with I2-1). Serving builds read far less; two gate-heavy builds read up to 14% more (a superset by design). The shell is still one function over 200 lines |
| I2-1 | Split serving writes from due queue reads | landed | `e1df438a03` | [refactor-i2.md](refactor-i2.md) | — |

## Arc G

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| G1 | Extract probe facts and hard stops | landed | `df8a5961b6` | [refactor-g1.md](refactor-g1.md) | `probe_facts` (pure) and `probe_verdict`; `decide_probe` derived, byte-equal on recorded and synthetic inputs; FG1's verdict on zeros replaced by its absence with the reason; one resolver for the three fitted-knob scopes |
| G2 | Make the action router the probe decider | landed | this commit | [algorithm-probe-router.md](algorithm-probe-router.md) | The router decides probes on both lanes at the new tag: a probe whose information value is not learned leaves the mix, and a probe coin (the stop coin's rate, read through one function; own seed, own assignment row, exact served distribution) offers it; the causal status is a facts read; the worth gates G to K step aside for router-selected probes only. The lanes differ in one rule (repair classes still settle the learner lane's status); the design's one continuation decision is not built. Phase review owed |
| G3 | Measure disagreement between the two diagnosis beliefs | landed | `8804080fcf` | [refactor-g3.md](refactor-g3.md) | Result on the live arxiv vault: four real pairs, none with different causes, all four one-sided, three with an exposed answer counted at full weight by the episode posterior (ledger G3-1). |
| mvp-0.61 | The evidence reading fixes as an algorithm tag: an exposed probe answer updates no belief (G3-1), unassessed criteria (ER-2), a regrade's source and a zero confidence on replay (K5-11, K5-12), the certificate probe's abstention (K5-3), a variant request is no review (K5-8) | landed | `0f309a8687` | [algorithm-mvp-0.61.md](algorithm-mvp-0.61.md) | Adversarial review and its fix round inside (ledger T61-1 to T61-5 fixed; G3-3 open). The owner chose the clock cases and "no update" on Nov 19. The owner upgrades each vault (`learnloop upgrade --vault <path>`): the record's last section says what moves |
| G4 | Unify beliefs when measured disagreements warrant it | waiting on | — | [refactor-g3.md](refactor-g3.md) | The owner, from the rerun of 2026-11-20 ([refactor-g3.md](refactor-g3.md)): the two records never disagree about a cause because neither learns one (ledger G3-4); the rerun recommends the skip branch |
| G5 | Give each duplicated fact one owner | deferred | — | — | Owner's Nov 17 queue |
| G6 | Use one authority for each protection question | being built | — | [design](refactor-g6-design.md) | G6.1, the six fixes and G6.2 are on main; G6.3 was stopped by the cost rule. Left: the five surfaces the matrix does not drive yet (with G6-P4 and G6.10), the display accounting extraction, G6-P8. K6-10 to K6-13 are independent fixes in the same area; K5-5 to K5-7 and K6-1 need a priming successor (a tag) |
| G6.1 | Pin what every protection surface answers for every protected fixture | landed | `99cda9d0ce` | [refactor-g6.1.md](refactor-g6.1.md) | `tests/test_protection_surface_matrix.py`: 37 fixture rows, 51 of 56 surfaces driven through their production functions, 1,502 cells, 100 fault cells, 30 reach cells; six defects confirmed as strict xfails. Not driven: the book solution region, the phone's dose offer, the pinned tutor job per row, compare, held feedback. Eleven cells differed from the design, none a leak |
| G6.4 to G6.9 | Fix the six protection defects the matrix confirmed (G6-P1, P2, P3, P5, P6, P7) | landed | `713a0efd08` | [refactor-g6-fixes-1.md](refactor-g6-fixes-1.md) | A finished pinned tutor answer is checked at every read; an earlier Reader answer that drew on since-held material is left out of the model's context; the question author never sees a protected neighbour and refuses a held-out selection in every spelling; an exam-reserved item's passage stays out of figure prebuilds; a kept answer naming no stored passage is refused. Open: G6-P4 (the phone's dose offer, not yet driven); an exam unit's heading beside a selected exercise under a one-span held-out signal |
| G6.2 | Each protection surface names the set it reads in one table | landed | `5f35fa7ac8` | [refactor-g6.2-3.md](refactor-g6.2-3.md) | `exam_material.SURFACE_SETS` (all exam, held out, or no exam set), read through `surface_material` and `surface_exam_material`; `tests/test_protection_surface_sets.py` holds each row to the matrix. The matrix passed unchanged |
| G6.3 | One final passage-admission function | dropped | — | [refactor-g6.2-3.md](refactor-g6.2-3.md) | Stopped by the cost rule: the best case reached three of the exits, added about 23 lines and made no test simpler; the other exits differ in when they read, how they fail and which reason words they store. One asymmetry found on the way: ledger G6-P8 |

## Arc H

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| H1 | Distinguish the old scalar from FSRS difficulty | landed | `ece7907885` | [refactor-h1.md](refactor-h1.md) | Six callers read item parameters through the one seam (`resolve_item_irt_params`); a guard test (`tests/test_difficulty_kinds_apart.py`: 54 modules, 161 sites) fails on a crossing read; 24 caller cases give the same numbers. Left: the lesson weight's reconstruction (ledger L4-2). Found: H1-1 (the terminal app's scalar bar can show FSRS D; with H5) |
| H2 | Compare four ways to use difficulty in replay | landed | this commit | [difficulty-four-way.md](difficulty-four-way.md) | Run on copies of the owner's vaults on 2026-11-23; the numbers went to the owner. H3 to H6 wait on the owner's decision from them |
| H3 | Retire scalar difficulty from mastery and surprise | waiting on | — | — | H2 and owner's call with the [AD memory spec](../specs/spec_ad_memory_v1.md) |
| H4 | Retire the model-estimated difficulty signal from AD | waiting on | — | — | Owner's call with the AD memory spec |
| H5 | Update exam strata, retrieval filters and authoring | waiting on | — | — | Owner's call with the AD memory spec |
| H6 | Remove scalar writers and DTOs, preserving hashes | waiting on | — | — | Owner's call with the AD memory spec |

## Arc Z

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| Z1 | Write and verify the modelling paper | waiting on | — | — | E5, arc G's belief decision and arc H |
| Z2 | Measure the refactor and report the savings | waiting on | — | — | Refactor close |
| Documentation rewrite, part 1 | The hand-written vault notes of the finished arcs (A, B, C, I, most of D, E and K) checked against the code and rewritten: 61 notes checked, 94 stale claims, 44 rewritten, 1 marked superseded | landed | this commit | [docs-rewrite-audit.md](docs-rewrite-audit.md) | Started early by the owner (2026-11-23). Arcs G and H and the modelling paper follow at the close. Written by a Codex worker |
| Z3 | Archive superseded and abandoned specs after documentation | waiting on | — | — | Documentation rewrite and owner's archive review |

## Arc K: identity and protection

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| K0 | Pin compared identities through their production paths | landed | `2bc93d4d2b` | [refactor-k0.md](refactor-k0.md) | — |
| K1 | Inventory protection questions, authorities and reading sets | landed | `565aee8724` | [refactor-k1.md](refactor-k1.md) | — |
| K1 fixes | Fix metadata gates, reservation gaps and docstrings | landed | `412cc63b4b` | [refactor-k1-fixes.md](refactor-k1-fixes.md) | — |

## Arc K: ingestion

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| K2 | Map ingestion and write its structure strategy | landed | `d1c3ee7c78` | [ingestion strategy](k2-ingestion-strategy-2026-11-11.md) | — |
| K2.1 | Use one checkpoint helper for structured calls | landed | `9eb0194c2c` | [refactor-k2.1.md](refactor-k2.1.md) | — |
| K2.2 | Key inventory and shard reuse on rendered inputs | landed | `ff8b42530b` | [refactor-k2.2.md](refactor-k2.2.md) | — |
| K2.3 | Record exact manifest inputs and reuse checkpoints | landed | `6daf76d9cb` | [refactor-k2.3.md](refactor-k2.3.md) | — |
| K2.4 | Share the synthesis run between two modes | waiting on | — | [refactor-k2.4c.md](refactor-k2.4c.md) | Part B of K2.4c |
| K2.4a | Share normalization, gates, persistence and apply | landed | `fea17dccae` | [refactor-k2.4a.md](refactor-k2.4a.md) | — |
| K2.4b | Share synthesis inputs, scope and manifest resolution | landed | `cb8bcb9a7f` | [refactor-k2.4b.md](refactor-k2.4b.md) | — |
| K2.4c | Run append through the shared shard runner | waiting on | — | [refactor-k2.4c.md](refactor-k2.4c.md) | Part B |
| K2.4c part A | Drive append calls through the shard runner | landed | `2f35db5173` | [refactor-k2.4c.md](refactor-k2.4c.md) | — |
| K2.4c part B | Split oversized appends into checkpointed passes | landed | this commit | [refactor-k2.4c-part-b.md](refactor-k2.4c-part-b.md) | An append too large for one request is split, in reading order, into checkpointed passes of whole inventories; a crash resumes at the crashed pass and applies once; an append that fits is byte-identical to before; one inventory over the ceiling is still refused. No run-total ceiling: each pass is admitted separately under the existing spend admission and daily cap. K2-20 fixed in the same landing: three job types now bump the queue revision, which the phone's poll needed. Phase review (Codex Astra, 2026-11-23): nineteen findings across K2.7, K10.11, K10.12 and K2.4c part B, fixed in one round (ledger K-R1 to K-R19) |
| K2.5 | Split normalization into named stages with one state | landed | `f623e525ac` | [refactor-k2.5.md](refactor-k2.5.md) | — |
| K2.6 | Share the judge heartbeat and lapse checks | landed | `ece7907885` | [refactor-k2.6.md](refactor-k2.6.md) | `judgment_claims.claim_heartbeat` replaces the two copied loops (it stops and joins its thread); a lapsed lease no longer commits (the paid answer is kept for the retry); service spend renews in each reservation's injected clock. Production −5 lines |
| K2.7 | Put each job type in one table row | landed | this commit | [refactor-k2.7.md](refactor-k2.7.md) | The job module keeps the host (6,195 to about 2,100 lines); handlers moved beside their features, 134 definitions identical by AST check; one `JOB_TYPES` table of plain rows replaces five lists; the job contracts are a leaf module; modules in an import cycle fall from 221 to 219. K2-20 (three job types do not bump the queue revision) is queued; K2-21 and K2-22 are fixed. Phase review (Codex Astra, 2026-11-23): nineteen findings across K2.7, K10.11, K10.12 and K2.4c part B, fixed in one round (ledger K-R1 to K-R19) |
| K2.8 | Give each source kind one definition | landed | this commit | [refactor-k2-batch-eligibility-records.md](refactor-k2-batch-eligibility-records.md) | `ingest/source_kinds.py` is the table; the desktop's copy is generated from it; `ingest/fetchers.py` and `ingest/detect.py` deleted; every reader's answer unchanged on a fixed corpus |
| K2.9 | Centralize extractor choice and consent checks | landed | this commit | [refactor-k2.9-10.md](refactor-k2.9-10.md) | `pdf_extractor_for` returns the extractor and the consent it needs; the import job asks it and raises the card, with the same words and order as before |
| K2.10 | Fold small fixes for conflicts, estimates and comments | landed in part | this commit | [refactor-k2.9-10.md](refactor-k2.9-10.md) | Conflict resolution writes its mapping, status and audit row in one guarded transaction (ledger K2-2 fixed); three stale comments corrected. Not done: one JSON token estimator: the three in use give different numbers (30,003, 30,003 and 5,003 tokens for one non-ASCII payload), and unifying them would move shard membership and with it manifests: it needs its own decision |
| K2.11 | Have desktop read ingest eligibility from the sidecar | landed | this commit | [refactor-k2-batch-eligibility-records.md](refactor-k2-batch-eligibility-records.md) | Retry and reuse eligibility, source roles, budget bounds and page-range refusals come from the sidecar; of the four disagreements the backend was right in three, and neither copy in the fourth (roles that never define concepts) |
| K2.12 | Record why ingest made its key decisions | landed | this commit | [refactor-k2-batch-eligibility-records.md](refactor-k2-batch-eligibility-records.md) | Decision records for build scope, the inventory choice and auto-apply, under the planner's trace (`learnloop why <planner job id>`) |
| K3 | Fix ingestion defects that cost money or data | landed | `dcf1eb5301` | [refactor-k3.md](refactor-k3.md), [final fix](refactor-k3.5.md) | — |
| K3.1 | Choose the current inventory row for synthesis | landed | `46b13f53c7` | [refactor-k3.md](refactor-k3.md) | — |
| K3.2 | Keep appends scoped to newly inventoried units | landed | `a83beeee84` | [refactor-k3.md](refactor-k3.md) | — |
| K3.3 | Send every missing unit in collection builds | landed | `84d2614688` | [refactor-k3.md](refactor-k3.md) | — |
| K3.4 | Bound and checkpoint the synthesis append call | landed | `5302288318` | [refactor-k3.4.md](refactor-k3.4.md) | — |
| K3.5 | Recover interrupted applies without overwriting changed files | landed | `4f85aa885e` | [refactor-k3.5.md](refactor-k3.5.md) | — |

## Arc K: other reviews

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| K4 | Map writers outside the ingestion pipeline | deferred | — | — | Owner's Nov 17 queue |
| K5 | Review grading, regrade, coldness and certification | landed | `1b63838666` | [refactor-k5.md](refactor-k5.md) | Sixteen ledger rows (K5-1 to K5-16): K5-14 and K5-2 fixed (`2b2c2fb155`, [refactor-k5-fixes-1.md](refactor-k5-fixes-1.md)); K5-1, K5-9, K5-10, K5-13, K5-15 and K5-16 fixed (`cd39afc328`, [refactor-k5-fixes-2.md](refactor-k5-fixes-2.md)); holes the arc E review found in that batch: ER-1, ER-3 and ER-6 fixed and ER-2 left for the next algorithm tag (`fix/arc-e-review-grading`, [refactor-efix1.md](refactor-efix1.md)); K5-3's plain part, K5-8's exceptions, K5-11 and K5-12 go with the next algorithm tag; K5-5 to K5-7 with G6; K5-4 with the evidence packet spec |
| K6 | Map Reader Ask and retrieval side effects | landed | `99707376c7` | [refactor-k6.md](refactor-k6.md) | Fourteen ledger rows (K6-1 to K6-14, nine high). Fix round A landed K6-2 to K6-9 and K6-14 (`659772cde4`, [refactor-k6-fixes-a.md](refactor-k6-fixes-a.md)); K6-1 goes with the Decider's first stage and K6-10 to K6-13 with G6 |
| K7 | Review AI transport and network boundaries | deferred | — | — | Terminal app rebuild or MCP v2 |
| K8 | Review sidecar handlers as the application layer | deferred | — | — | Terminal app rebuild or MCP v2 |
| K11 | Map the daily plan engine before moving code | landed (map) | this commit | [k11-daily-plan-engine-map.md](k11-daily-plan-engine-map.md) | Four costs are named (K11-C1 to K11-C4); the map says they do not show that splitting the file would lower them. No step follows unless one is briefed against a named cost |

## Arc K: diagnosis

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| K9 | Map diagnosis and write its structure strategy | landed | `31787227e2` | [diagnosis strategy](k9-diagnosis-strategy-2026-11-14.md) | — |
| K9.0 | Investigate the planted-type simulation's robust probe path | landed | `ed96d1b9d0` | [refactor-k9.0.md](refactor-k9.0.md) | — |
| K9.0b | Correct the robust probe gate and instrument ranking | landed | `7bdec7edb5` | [refactor-k9.0b.md](refactor-k9.0b.md) | — |
| K9.1 | Settle block answers on a mid-check stop | landed | `55205863a2` | [refactor-adfix2.md](refactor-adfix2.md) | — |
| K9.2 | Explain why a check was withheld | landed | `4f5b325939` | [refactor-adfix2.md](refactor-adfix2.md) | — |
| K9.3 | Use an injected clock for primed-sibling ranking | landed | `ce11173c99` | [refactor-adfix2.md](refactor-adfix2.md) | — |
| K9.4 | Expire an untaken primed repair episode | landed | this commit | [algorithm-mvp-0.64.md](algorithm-mvp-0.64.md) | Tag `mvp-0.64`. "The item" is read as the missed question (the only item every such episode has): the owner was told and can change it |
| K9.5 | Pin diagnosis identities and golden its journeys | landed | `4874f304e8` | [part 1](refactor-k9.5a.md), [part 2](refactor-k9.5b.md) | — |
| K9.5 part 1 | Pin the diagnosis package's compared identities | landed | `9cb87cfa16` | [refactor-k9.5a.md](refactor-k9.5a.md) | — |
| K9.5 part 2 | Golden the diagnosis journeys before moving code | landed | `4874f304e8` | [refactor-k9.5b.md](refactor-k9.5b.md) | — |
| K9.6 | Extract causal reads and hard stop checks | landed | `3c713310a6` | [refactor-k9.6.md](refactor-k9.6.md) | — |
| K9.7 | Extract machine checks and cold verification | landed | `f719b52f58` | [refactor-k9.7.md](refactor-k9.7.md) | — |
| K9.8 | Extract discriminating observations and learner offer actions | landed | `0678b5309c` | [refactor-k9.8.md](refactor-k9.8.md) | — |
| K9.9 | Extract probe completion policy and stopping rules | landed | `ebdb550566` | [refactor-k9.9.md](refactor-k9.9.md) | — |
| K9.10 | Extract presentations and delete dead block planning | landed | `f104eabe79` | [refactor-k9.10.md](refactor-k9.10.md) | — |
| K9.11 | Extract probe evidence and learner controls | landed | `753b68eac4` | [refactor-k9.11.md](refactor-k9.11.md) | — |
| K9.12 | Record declined probe answers and failed hooks | landed | `8311e90261` | [refactor-k9.12.md](refactor-k9.12.md) | — |
| K9.13 | Separate episode posterior reads from its fold | landed | this commit | [refactor-k9.13-k9.17.md](refactor-k9.13-k9.17.md) | G4 is closed, so this ran alone: the posterior's gather and its pure fold are separate; 30 comparisons returned equal posteriors and the same SQL in the same order. Built by a Codex worker |
| K9.14 | Update the Diagnosis note to match code | landed | `1d3edadcfe` | [Diagnosis and Remediation](../learnloop-architecture-vault/Concepts/Diagnosis%20and%20Remediation.md) | — |
| K9.15 | Remove failure triage and its registry entries | landed | `be3cb2ac11` | [refactor-k9.15.md](refactor-k9.15.md) | — |
| K9.16 | Remove EVSI shadow selection and its panel | landed | `1fad9526bd` | [refactor-k9.16.md](refactor-k9.16.md) | — |
| K9.17 | Feed released holds and regrades into belief | designed | — | [refactor-k9.13-k9.17.md](refactor-k9.13-k9.17.md) | A persisted-meaning change (released holds and regrades change the posterior and the stored misconception marginals): it needs its own algorithm tag after the ones in flight |

## Arc K: figures

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| K10 | Map figures and write their structure strategy | landed | `92a871d915` | [figures strategy](k10-figures-strategy-2026-11-14.md) | — |
| K10.1 | Stop building when a figure request is cancelled | landed | `7f96c0a5c7` | [refactor-k10-bugs.md](refactor-k10-bugs.md) | — |
| K10.2 | Tell the Reader when figures are withheld | landed | `ffc1cd94c5` | [refactor-k10-bugs.md](refactor-k10-bugs.md) | — |
| K10.3 | Continue the request trace in video jobs | landed | `d327f4b130` | [refactor-k10-bugs.md](refactor-k10-bugs.md) | — |
| K10.4 | Pin figure identities and golden the build | landed | `15075cca37` | [refactor-k10.4.md](refactor-k10.4.md) | — |
| K10.5 | Give each figure switch one predicate | landed | `b562858238` | [refactor-k10.5-6.md](refactor-k10.5-6.md) | — |
| K10.6 | Centralize figure protection and cut its cycle | landed | `66cad2da41` | [refactor-k10.5-6.md](refactor-k10.5-6.md) | — |
| K10.7 | Extract figure request and grounding functions | landed | `8d775a4456` | [refactor-k10.7-8.md](refactor-k10.7-8.md) | — |
| K10.8 | Extract presentation, listing and predictions from build | landed | `150b14ae3e` | [refactor-k10.7-8.md](refactor-k10.7-8.md) | — |
| K10.9 | Extract pure reading of the figure author's answer | landed | `5f35fa7ac8` | [refactor-k10.9-17.md](refactor-k10.9-17.md) | `figures/author_answer.py` `read_answer` returns a verdict (retry, unsupported, spec, sketch, rich) with its record code; the loop went from 305 to 186 lines; 711 of 711 old-and-new loop pairs identical; the figure goldens and pins unchanged. Net +155 source lines, past the estimate: kept because the rules are now tested with literal answers and two whole-build tests became one call each |
| K10.10 | Share the presentation chain and shown set | landed | this commit | [refactor-k10-batch-shown-switches.md](refactor-k10-batch-shown-switches.md) | One chain for section figures, the shown set and drawable/shown checks; `LESSON_TIERS` and `ATTEMPT_HOST_TIERS` as the one constant each tier door reads |
| K10.11 | Record figure refusals, reuse and available tiers | landed | this commit | [refactor-k10.11-k10.12.md](refactor-k10.11-k10.12.md) | One `figure_request` record per request (refused with its code, built, reused with the key that matched, or deferred), the menu as a pure core with a code for each tier left off, the gate record's unit and hold code, `figure_withheld` once per figure. No migration: all in `decision_records`. K10-10 fixed. Phase review (Codex Astra, 2026-11-23): nineteen findings across K2.7, K10.11, K10.12 and K2.4c part B, fixed in one round (ledger K-R1 to K-R19) |
| K10.12 | Record each attempt by a rich figure job | landed | this commit | [refactor-k10.11-k10.12.md](refactor-k10.11-k10.12.md) | Each rich attempt is a `figure_rich_author` record through the same builder; a job that ends with no row writes `figure_rich_stop`, so a requeue no longer erases why it stopped. ADR-017's open item closed. Phase review (Codex Astra, 2026-11-23): nineteen findings across K2.7, K10.11, K10.12 and K2.4c part B, fixed in one round (ledger K-R1 to K-R19) |
| K10.13 | Move attempt-host policy under the figures package | dropped | — | — | Owner ruled out figures on phone and MCP |
| K10.14 | Read shown state and labels from the server | landed | this commit | [refactor-k10-batch-shown-switches.md](refactor-k10-batch-shown-switches.md), [ledger K10-5](refactor-bug-ledger.md) | The view carries `shown` and a closed `label_code`; the desktop's literal copies and its branch on the English label are gone |
| K10.15 | Write the Figures note and correct stale lines | landed | `53f330c743` | [Figures](../learnloop-architecture-vault/Concepts/Figures.md) | — (K10-4 fixed) |
| K10.16 | Retire the eight figure content switches | landed | this commit | [refactor-k10-batch-shown-switches.md](refactor-k10-batch-shown-switches.md) | Eight switches into `RETIRED_FIELDS`, every pinned identity's bytes kept, new builds' prompt version byte-identical. V1/V2 contracts and the sketch-off row stay for machines whose sketch engine cannot load; the reuse key's legacy alternates stay while stored figures use older prompt versions (count of 2026-11-20: 28 figures in one vault across six versions); the desktop's constant contract keys wait for the Reader work |
| K10.17 | Remove the dormant JavaScript animation tier | landed | `5f35fa7ac8` | [refactor-k10.9-17.md](refactor-k10.9-17.md) | 20 source lines in 7 files; no config field and no stored row ever named it; an answer with that status, which no menu offers, is now recorded as `other` |

## Measure and layout steps

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| M0 | Hold the structure measures in a golden | landed | `9042ca91f3` | [refactor-m0.md](refactor-m0.md) | — |
| M1 | Hold serving file sizes and golden JSON lines | landed | `31ce39ec3d` | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | — |
| L1 | Cut the import cycle at measured edges | waiting on | — | [refactor-l1b.md](refactor-l1b.md) | Arc G for the remaining knot |
| L1a | Cut two import edges with pure moves | landed | `572d40b9fa` | [refactor-l1a.md](refactor-l1a.md) | — |
| L1b | Cut three more edges and measure the component | landed | `914145d0b9` | [refactor-l1b.md](refactor-l1b.md) | — |
| L2 | Move repository methods into named store files | landed | `f243c960e1` | [pilot](refactor-l2a.md), [b](refactor-l2b.md), [c](refactor-l2c.md), [d](refactor-l2d.md) | — (`repositories.py` is a 3,025-line facade with 52 methods; 17 store files and `db/records.py`) |
| L2a | Pilot a store for reading request methods | landed | `400dfeb2be` | [refactor-l2a.md](refactor-l2a.md) | — |
| L2b | Split five store groups from the repository | landed | `914145d0b9` | [refactor-l2b.md](refactor-l2b.md) | — |
| L2c | Split attempt, grade and diagnostic store groups | landed | `f10dbf51ae` | [refactor-l2c.md](refactor-l2c.md) | — |
| L2d | Split content, scheduling and other repository groups | landed | `f243c960e1` | [refactor-l2d.md](refactor-l2d.md) | — |
| L3 | Mark serving reach and enforce the tooling boundary | waiting on | — | [l3-serving-reach-list.md](l3-serving-reach-list.md) | The owner marks the list (260 tooling-only modules, 98,157 lines; no serving-to-tooling import today). Then the import contract and the reach field |
| L4 | Review which learned models need pure cores | landed (review) | `53f330c743` | [refactor-l4-review.md](refactor-l4-review.md) | Six extraction steps, in the order L4.1 claim priors, L4.2 cause slopes, L4.3 the episode posterior, L4.4 lesson-weight replay inputs, L4.5 the AD slot and commission decision, L4.6 the tail's fit-and-record assembly: not started, each under the stop rule. Five reproducibility gaps in the ledger (L4-1 to L4-5) |
| L5 | Explain long functions that other steps missed | waiting on | — | — | Refactor close |
| L6 | Make each extracted core return its record | waiting on | — | — | E2 and later core extraction briefs |
| L6a | Return records from the already extracted cores | landed | this commit | [refactor-l6a.md](refactor-l6a.md) | The grade-application core and `rank_due` return their records with their results, and the callers write them where they did; every written record byte-identical; one staged why-case per rule code (13), found from the code by a test; L6 is now in the strategy's per-step rules |
| L7 | Move the support floor as vaults advance | landed | `1da959e7d7` | [refactor-d1.md](refactor-d1.md) | — |

## Tests and phase reviews

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| T1 | Stop test files importing one another | landed | `732fe09aaf` | [refactor-t1.md](refactor-t1.md) | — |
| T2 | Rename tests for the behavior they prove | waiting on | — | — | Documentation stage at the close |
| T3 | Pin seeded draws in tests by default | landed | `412cc63b4b` | [refactor-t3.md](refactor-t3.md) | — |
| T4 | Port private patches and ratchet their counts | landed | this commit | [owner-decisions-small-1.md](owner-decisions-small-1.md) | — |
| T5 | Merge stage-named tests and review slow tests and goldens | waiting on | — | — | Arc E and the refactor close |
| Phase 1 review | Review the first phase and land its fixes | landed | `04a0154c0d` | [refactor-phase-1-review.md](refactor-phase-1-review.md) | — |
| Phase 2 review | Review the second phase and land its fixes | waiting on | — | — | Arc D close |

## UX journey audit: fix stages

The stages are the audit's ([ux-journey-audit.md](ux-journey-audit.md) section 10). After a stage lands, the walks it came from are run again.

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| UX-1 | Question writing for a long web page fits its output budget | landed | `c67f1931ed` | [ledger UX-1](refactor-bug-ledger.md) | — |
| Stage 1 | Broken controls: the Ask send control, Keep going, a past exam's open, empty states as notices, "add it" with no subject, the phone's delivery line (UX-3 to UX-7, UX-9) | landed | `99d24e65f6` | [ux-fix-stage-1.md](ux-fix-stage-1.md) | The walks again |
| Stage 2 | A source's own math macros reach the renderers; one-line snippets show no raw TeX; the empty goal's report says what is true (UX-2, UX-8) | landed | `1147749960` | [ux-fix-stage-2.md](ux-fix-stage-2.md) | The walks again. UX-10 (the consent question) waits for the owner's ruling. Found on the way: UX-11 (display equations dropped by web-page extraction), UX-12 (macros in model-written text outside the Reader) |
| Stage 3 | Today explains itself: an empty or finished Today names its cause and carries one step, each duration is labelled for what it measures, the book card's "Give your OK", refusals said in place | landed | `99cda9d0ce` | [ux-fix-stage-3.md](ux-fix-stage-3.md) | The walks again. Left for the Reader redo: two Reader refusals. Today cannot yet say that the plan suggested stopping (the plan's stop reason is free text) |
| Stage 4 | Phone small fixes: capture says when it was sent, a look that didn't finish says nothing is needed, the Today tab always opens the plan with "Resume your answer", the phone's durations in the desktop's words | landed | `99cda9d0ce` | [ux-fix-stage-4.md](ux-fix-stage-4.md) | A phone walk. Not built: pairing at once after the scan (the page a scan opens is the host's own, `src/learnloop_mobile/static/pair.*`; the host would accept nothing new): stage 4b. The router's line on the phone's Today (F14) is the owner's call |
| Second wave of walks | Thirteen walks on the fixed application: five re-walks and eight new personas (lessons, the workbench, the practice exam, the returner, the expert, own notes, a project, two courses) | landed | `5f35fa7ac8` | [ux-journey-audit-2.md](ux-journey-audit-2.md) | Before and after for stages 1 to 4, fifteen new defects (UX-13 to UX-27), findings F20 to F30, the stages below re-ranked. Not walked: a passed goal date, a sat practice exam, the Decider and embedding routes |
| Waiting you can see | The owner's Nov 19 request: a waiting indicator from Today to the question, from the question to feedback, and where a model writes | landed | `5f35fa7ac8` | [ux-waiting.md](ux-waiting.md) | 48 waits listed, 32 covered on the desktop and the phone. Left: figures, question writing's progress amount, adding a source, the practice exam, the Reader's project scope |
| First questions arrive | A first document's questions are written and offered (UX-13; P11; UX-29; UX-31) | landed | `4566d93ae9`, `574ebc0d14`, `1119b97462`, `7d6dfe9f82`, `9cf7b07914`, `746335c4a0`, `dbae0d5f56`, `c7572bda76`, `0b1fcf13da`, `5aa25b9a66`, `496e9cb4d1`, `1f9c8de1b3`, this commit | [backend](ux13-first-questions.md), [Today](ux-first-questions-today.md), [a section finished early](ux31-section-done-before-build.md) | A source is prepared as it is read, and a section's questions are written only when the section is finished. On main: output ceilings and one automatic retry; Today says the truth for each state and offers the first questions with Begin; the desktop Reader's "Done with this section"; a section finished before its book is ready now waits and gets its questions once when the book's topics arrive (found by the third wave's walk on the live route). Found by the walks on the live route after that: the one call that wrote a section's questions for all its topics ran into the request deadline; it is now one saved call per topic, saved as it arrives (UX-33, [record](ux33-section-questions-in-parts.md)), and each topic's questions are applied as soon as they are ready, judged against what is already applied, with one bad topic failing alone (UX-37, [record](ux37-first-questions-first.md)). Today shows how far the writing is and offers the questions already there ([record](ux-first-questions-progress.md)). A background call on the plan route that is still delivering output is no longer cut by the total deadline: it stops when the stream is silent for the profile's timeout or at a twenty-minute ceiling, and a ceiling cut is not retried by itself (UX-39, [record](ux39-live-stream-deadline.md)). The amount on the writing line counts only the sections being written (UX-38). On the real route the model marked every written question for review, so none was applied: the prompt line now states the policy the code implements, and a topic held for review is no failed topic (UX-40, [record](ux40-section-questions-apply.md)). The build's own call could run away into endless whitespace where the prompt said to omit a key its schema requires: the prompt now writes the key as null, a structured answer that turns to whitespace is cut and sent again, and a failed stream's receipt says how much it delivered (UX-41, [record](ux41-runaway-whitespace.md)). A topic's questions were refused whole when the model left their ids empty: LearnLoop now names an unnamed create itself, and the repair turn says what was wrong (UX-42, [record](ux42-create-without-id.md)). A first build that came back with no topic was accepted as finished: it is now asked again once, a build that is still empty says so on Today and the Library card with Try again, and a later build writes the questions owed to sections already finished (UX-43, [record](ux43-empty-build.md)). On main `0b1fcf13da` a first-day persona answered its first practice question on the real route 8 min 18 s after adding a chapter. A follow-up question that came back empty failed outright: an answer that ignores its contract is now asked again once (UX-45, [record](ux45-followup-empty-question.md)). After the first answers Today counted questions already answered or kept for a later check, Begin reopened one and Next went back to Today: the count, Begin and Next now follow what can be asked now (UX-44, [record](ux44-begin-after-first-answers.md)). The question an open certification check keeps for its day is withheld from ordinary practice, as a repair's retry question is (UX-44b, [record](ux44b-reserved-check-question.md)). Still true: a first-day learner who does not finish a section gets no practice, and a web chapter is one section: the owner's call whether a first set comes from the part read. Open: UX-30 and UX-32 (labels that promise question writing a build does not do) |
| Broken controls, second round | UX-14 to UX-27: the lesson you can come back to, the two sentences stages 2 and 3 got wrong, a check that asks nothing, the workbench's first click and its hint failure's words, Begin on a lesson offer, the lesson reply that stays, tabs that leave a check; the Reader's scroll, the phone's review reasons, section names in words, display equations drawn, a formula quoted once | landed | `9a91561184` | [group A](ux-fix-round-2a.md), [group B](ux-fix-round-2b.md) | The walks again, in the real window for UX-15 and UX-19. Open: why the workbench's hint writer fails its own checks (UX-20, with the help stage); UX-28 (the phone shows a held grade's score) |
| Third wave of walks | Thirteen walks: the first-day chain on the real model route (ten walks, each after the fix the one before produced) and three re-walks; UX-47 to UX-57 drafted, findings F39 to F47, proposals P19 to P24, the stages re-ranked | landed | this commit | [ux-journey-audit-3.md](ux-journey-audit-3.md) | — |
| Broken controls, third round | UX-47 to UX-57 (a failed topic ranked above the writing, the redo's "What to fix" in system words, "(on your own)" after help, a typed note never saved, words typed to find an action saved as a note, "Nothing planned" above an offer, a failed quick check never said, a second source waiting silently, a rail control covered on its first click, Ask's chips naming a slug, a second copy of the same file) and the wording rows UX-30, UX-32, UX-44c | landed | `9658a9ce2f` (group A: UX-46 to UX-49, UX-52, UX-53), this commit (group B: UX-50, UX-51, UX-54 to UX-57, and the wording rows UX-30, UX-32, UX-44c, UX-52b) | [ux-fix-round-3a.md](ux-fix-round-3a.md), [ux-fix-round-3b.md](ux-fix-round-3b.md) | UX-48b waits on the owner; UX-54's queue order is left for the next stage; UX-58 (two load-sensitive desktop tests) is open |
| The first evening, finished | P19 to P24, F39 to F43: the build's wait in more than one line, what comes tomorrow, the quick check above the fold, a section's end, the chapter's figures beside the exercises that use them; UX-34 and UX-35 brought forward | landed (steps 1 to 8) | see the stage's own table below | [algorithm-mvp-0.63.md](algorithm-mvp-0.63.md) and the steps' records | Left: web-page paragraphs and figures (step 9), a second source readable during a build (step 10), keeping an Ask answer's problems as practice (step 11). Three live walks on 2026-11-21; a fourth (a section read to its end) is owed |
| Course setup, graded work and the practice exam (spec first) | P3, F8, F22: start from a goal, one course for a student's materials, graded work entry, sitting a stored practice exam | not started | — | — | — |
| A Goals place (spec first) | P2: all goals, deadline and scope edits, pause and resume, "Am I ready?" outside the Reader | not started | — | — | — |
| Lessons you can find, with the Teacher screens remade | F21, P12: resume a lesson, a lesson on the topic just missed, the Teacher screens | not started | — | — | The "teach me this" control on feedback waits for G2 |
| Load you can see and steer, for one or two courses (spec first) | P5, F29: the forecast, less or more, one budget split across courses | not started | — | — | — |
| Help shows what it gave away | P6 (owner's decision 2) on desktop and phone feedback; F24 | waiting on | — | — | The Decider's first stage; arc G |
| Progress in words and the jargon sweep | P10, F28 | not started | — | — | — |
| Web pages keep their equations | UX-11: a web page read into LearnLoop keeps every display equation, its headings' own words as titles and none of the page's furniture | landed | `5a7728283a` | [ux11-html-extraction.md](ux11-html-extraction.md) | New reads use extraction version 3; a page read before keeps its stored text and its card offers "Read it again" where equations are missing (a re-read re-pays the changed units' inventory later, so it is never automatic; marks are not carried: the new reading is held back until it is marked). Open: UX-34 (emphasis splits and glued paragraphs), UX-35 (figures and captions dropped), the chapter stays one section |
| The Reader redo | Search, margin cues, syntopic reading; UX-34 and UX-35. Now the Reader workbench v2 spec: see its own section below | not started | — | [spec_reader_workbench_v2.md](../specs/spec_reader_workbench_v2.md) | RD-spike and RD0 first |
| Own notes as sources (spec first) | F27: a notes folder or a deck as one source, links between notes, the learner's wording kept | not started | — | — | — |
| Settings cleared | F17 and the owner's Nov 8 item | not started | — | — | — |

## Second audit

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| S1 | Keep one status table in the repository | landed | `31ce39ec3d` | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | — |
| S2 | Stop batches when cost per removal more than doubles | landed | `31ce39ec3d` | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | — |
| S3 | Reorder open lanes around cuts and reviews | landed | — | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | Applied as a reordering: L1 and L2 ran ahead of the interior splits. L4's review has no slot yet. |
| S4 | Name the next features and their prerequisites | landed | this commit | [owner-decisions-small-1.md](owner-decisions-small-1.md) | — |
| P1 | Record what evidence each model call saw | waiting on | — | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | Owner decided on 2026-11-20: approved as EP2, before EP3 |

## Reader workbench v2 (the Reader redo; spec landed Nov 22)

The spec is `docs/specs/spec_reader_workbench_v2.md` (desks, the companion, scratchpads, the goal lens, inline checks, pen and ink, lesson and notebook windows). It is the UX audit's "Reader redo" stage, taken whole: it runs after the refactor's open steps as a UX stage, and its first two stages may run beside the refactor because they touch no serving path. Each stage lands from a clean worktree through the landing gate and the real-webview harness (spec §18.3), carries a review file with its mockup comparison (the mockups themselves are private and are never committed), and closes with a Codex Astra adversarial review and one fix round. No stage ships a kill switch. Decisions D1 to D16 (spec §20) are built on their recommended defaults unless the owner overrides one; D14 (alt with vertical scroll zooms the overview) and D1 (criticality marks per section) are asked first.

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| RD-spike | Disposable packaged-app spike on WebKitGTK: the zoom engine, blur, IndexedDB durability, embeds; no product code kept | paused | — | — | Paused by the owner on 2026-11-22, partway. Measured so far: IndexedDB kept every acknowledged write through 30 forced kills; zoom frames were far over the 20 ms budget (cost in drawing, not script), still being diagnosed |
| RD0 | Foundations: migrations for desks, windows, pads, block versions, anchors and receipts; the write protocol; the two derived span tables with replayers; `desk.*`, `pad.*`, `passage.union_range`, `companion.history`, `checks.due_for`; import fences | landed | `9a65a449d2`; fix round: this commit | [reader-rd0.md](reader-rd0.md) | Migration 262, no algorithm tag. The adversarial review's ten findings fixed in one round (ledger RD0-1 to RD0-10; migration 264). The client's local store waits for the spike's durability decision |
| RD1 | The desk shell, the window lifecycle and the key router; source and video windows extracted from the Reader; the old panels as windows | landed | `6d6815aa2e`; fix round: this commit | [reader-rd1.md](reader-rd1.md) | The adversarial review's twelve findings fixed in one round (ledger RD1-3 to RD1-14): a refused write no longer blocks the outbox, a conflict keeps unrelated work, one store per vault, pairing and focus never remount a Reader, paused windows are inert and start nothing. Built without a frame-budget gate (owner, 2026-11-23: performance is revisited once the workbench works and matches the mockup). Source and video windows host the Reader in a windowed mode until RD-retire; the old Reader stays the default with links both ways. Fonts bundled locally (OFL) |
| RD2 | The overview and gestures: the zoom engine with the commit-identity invariant, live miniatures, curved links, gather, the wheel router, the HUD, the laptop rail | landed | `86859cc636`; fix round: `e7bbdbed23` | [reader-rd2.md](reader-rd2.md) | No frame-budget gate (owner, 2026-11-23); the frame trace is recorded as information. Found and fixed RD2-1, a bug in RD1: paused windows kept rendering The adversarial review's fifteen findings fixed in one round (ledger RD2-2 to RD2-16): no window owns input in the overview, one transition generation guards every callback, the unvisited-desk, focus-mode and keyboard-navigation exits meet the commit-identity check, a drop at slot 0 lands there. |
| RD3a | The companion and search, backend: `companion.ask` as a polled, cancellable job with the model call outside the sidecar mutex; `search.everything` with lexical groups at once and meaning groups through a job | landed | this commit; fix round: this commit | [reader-rd3a.md](reader-rd3a.md) | Partial answer text is not streamed (no transport streams it yet); idempotency lasts as long as the sidecar. The adversarial review found one blocker, twelve major and seven minor findings across RD3; the backend ones are fixed in one round (ledger RD3-1 to RD3-19): a job belongs to one vault and one sidecar epoch, every search supersedes the one before, and the companion's context is written with its question |
| RD3b | The companion and search, frontend: the app-wide `Companion` (docks, tab, anchored summon, dissolve, hand-off, avoid, the pill), ask jobs through the central poller, history, claims that open beside, thread windows, diff proposals ready for pads; search with groups, the meaning job and insert mode | landed | this commit; fix round: this commit | [reader-rd3b.md](reader-rd3b.md) | Mounted on the desks only until the companion's ask covers Practice and Today; answers arrive whole (no transport streams text yet). The review's twelve frontend findings fixed in one round (ledger RD3-20 to RD3-31): the desk keys reach the desk while a selection is open, a question waits for the desk to be saved, polls stop with their window, stale searches are dropped, retry resends the request whole, history pages, and a quote is never cut inside a formula |
| RD4a | Scratchpads, backend: migration 266 (submissions, carried questions and their events, proposals, labels; `pad_text` gaps), mvp-0.68 (pad text becomes learner text through the gap job: quote-only pads emit nothing, corrections supersede, tombstones retract), `pad.submit_block`, carried questions and the drain, proposals from passage links | landed | this commit; fix round: this commit | [algorithm-mvp-0.68.md](algorithm-mvp-0.68.md), [reader-rd4a.md](reader-rd4a.md) | Carried questions feed neither the router nor the Teacher yet: the owner chooses how (record §5). Proposals from search and correspondents wait for RD5. The adversarial review found three blockers, twelve major and two minor findings across RD4; the backend ones are fixed in one round (ledger RD4-1 to RD4-7): a teach-back submission is reserved under a conversation id before the hand-off, a lifted block keeps its links and quote context, a stale edit can keep both versions, stack membership and the running pad are their own desk operations, and `passage.content` returns a passage's own words |
| RD4b | Scratchpads, frontend: sticky tabs, the running pad, the live editor, gutter marks and hover cards, two-way links, lift out, arrange and split, the pad menu, sketch blocks, submit, carried questions, the drain | landed | this commit; fix round: this commit | [reader-rd4b.md](reader-rd4b.md) | Built without a frame-budget gate. A new pad inside a stack is kept in the window's view until a desk op can change a stack's entries; a source's math macros in pad quotes wait for RD5's append path. The §13.4 LaTeX fixture passes in every container. The review's fifteen frontend findings fixed in one round (ledger RD4-20 to RD4-34): a click in the editor no longer reverts the draft, reconciling keeps edits queued meanwhile, a conflicting edit keeps both versions, one request per submission, the teach-back's question is shown, the running pad exists on every desk, back-links reopen closed sources, a paged carried list, and passage marks from the union read |
| RD6a | The goal lens, backend: `goal.band`, `goal.lens` and `goal.section_choice` over the real goal, path and coverage model (mapping states, highest-need aggregation, the why, path reasons, depth, empty states); the level rules as one pure function with a table test | landed | this commit; fix round: this commit | [reader-rd6a.md](reader-rd6a.md) | No migration and no algorithm tag: "read it anyway" is a learner verdict in the judgment ledger. The frontend half (the band, marks, dimming, callouts, the path view) follows. The adversarial review's two blockers, eight major and four minor findings across RD6 are fixed in one round (ledger RD6-1 to RD6-14): one server function masks everything about a learning objective whose check is due, in every goal; stale or unsettled coverage reads partial, never skippable |
| RD5 | Menus: `passage.promoted` with its judged job, `passage.knows`, the proposals RD4 deferred (backend); one context menu on every object with promoted rows and every verb wired, the pad menu through the same component, the shelf's running-pad list (frontend) | landed | this commit; fix round: this commit | [reader-rd5a.md](reader-rd5a.md), [reader-rd5b.md](reader-rd5b.md) | Promoted rows are ordered by the learner's own history, most recent first (an orchestrator default; a learned ranking is the follow-up and needs impressions stored). Make it practice from a pad line opens the prefilled form: no server draft. The adversarial review's two blockers, fifteen major and six minor findings are fixed in one round (ledger RD5-1 to RD5-8 and RD5-30 to RD5-50): exam and held-out material never reaches search, the judge, a row or a proposal; a retried menu starts no second job; a closed menu's late rows reach no other menu; Make it practice on an exercise shows its words first and the items made afterwards (a draft-then-admit step stays an owner option) |
| RD6b | The goal lens, frontend: the band, margin marks with the why card, dimming, callouts, the path view with stored overrides, depth, the goal switch, marks on transcripts, the video track, shelf rows and the minimap, the companion's goal line | landed | this commit; fix round: this commit | [reader-rd6b.md](reader-rd6b.md) | Colours, type and the five goal tokens equal the mockup in every goal state at both viewports (the visual reference's rd6 stage). The Teacher lesson row waits for lesson windows; inline checks are RD7. Fix round: this commit (a late lens reply lands only for the goal shown; the band re-reads when a check comes due; a source is "not needed" only when every section is known so) |
| RD9a | Lesson windows: `LessonView` extracted with the lesson screen unchanged; lessons as tabs in a desk's stack from every entry; review replay with no model call; the additions pad; `lesson.list`; the path view's lesson row | landed | this commit; fix round: this commit | [reader-rd9a.md](reader-rd9a.md) | Check hand-offs and Today's suggestion cards keep the lesson screen (they live outside the desks). The adversarial review's seven major and one minor findings are fixed in one round (ledger RD9a-1 to RD9a-8): one additions pad per lesson; a closed opening sends no second turn; a lesson's quick question is asked on the lesson screen, never in a desk window, until inline checks' guard exists (an interim) |
| RD-retire | The old Reader goes, every parity row demonstrated | not started | — | — | RD4, RD5, RD6, RD9a |
| RD7a | Inline checks and veils, backend (algorithm tag mvp-0.69, migration 270): `check.begin_inline` records the administration and its veil set before the prompt, `check.protect_more`, `check.expose`, `check.submit_inline` through the attempt service, `check.abandon_inline`, `check.open_inline` for a restart; one administration at a time, shared with Today | landed | this commit | [reader-rd7a.md](reader-rd7a.md), [algorithm-mvp-0.69.md](algorithm-mvp-0.69.md) | The owner's decisions (2026-11-23): opening a veil is a reveal sized by overlap with the answer key; every note-bearing surface is veiled by default; a second answer on the other surface is practice and ordinary evidence. The Decider's narrowing waits for the reveal adjudication judgment. Migration 270 also carries the video chapters' replace guard. Adversarial review owed |
| RD7b | Inline checks and veils, frontend: the closed marker with no cues, the check card, veils on every note-bearing surface with honest cost wording before opening, `check.protect_more` for windows that come into view, abandon, restart recovery, verbs that wait while a check is open | landed | this commit | [reader-rd7b.md](reader-rd7b.md) | Opening one of the learner's own notes during a check submits the answer as practice, because notes are never read to measure them (an interim the owner has still to confirm). A lesson's quick question stays on the lesson screen: letting it into a desk window needs a schema change. The answer box is a plain text area. Adversarial review of RD7 owed |
| RD8a (backend) | Pen and ink, backend: `ink_strokes` and `ink_transcriptions` (migration 267), `ink.save`, `ink.erase`, `ink.list`, the `erase_ink` pad op, `ink.transcribe` as a polled, cancellable job that renders strokes to an image and reads it through a paid route, a reading as the block's next version, a learner's correction never overwritten | landed | this commit; fix round: this commit | [reader-rd8a.md](reader-rd8a.md) | No algorithm tag. On the default plan route a reading is refused before anything is sent, because no plan route reads images yet (owner decision open). The help ladder for ink is not built: it needs more than a new surface value (owner decision open). The adversarial review's fourteen major and three minor findings across RD8a are fixed in one round (ledger RD8a-2 to RD8a-19; migration 269 closes a replacing-insert hole in the transcription guard): a reading becomes a line's words only while the strokes it read still stand; erased handwriting blanks its automatic transcription; a cancelled reading is not paid for twice |
| RD8a (frontend) | Pen mode: pen input (pressure, tilt, barrel erase, palm rejection), the recognizer on sources (underline, bracket, strike, margin note, lasso), plain ink kept on the page, handwritten pads and ink lines with their readings, corrections and refusal states | landed | this commit; fix round: this commit | [reader-rd8a.md](reader-rd8a.md) | Moved ahead of RD7 by the owner on 2026-11-23. Not tried on a real tablet. The veil waits for RD7. Fix round: this commit (marks restored from their words, not screen position; undo removes a pending mark for real; a margin note is one annotation and one reading, grouped by place) |
| RD8b | Freeform ink help (tag); the help ladder for ink | not started | — | — | The owner's decision on the ladder; the hint service's freeform context |
| RD9b | Notebooks in the workbench: the notebook frame and paper theme (B4), the packaged-app check on WebKitGTK (B5, passed), marimo cells in pads as one live group per pad (B6), a lesson notebook in a lesson window with commit points and held cells (B7) | landed | this commit; fix round: this commit | [notebook-frame-b4-b5.md](notebook-frame-b4-b5.md), [notebook-cells-b6.md](notebook-cells-b6.md), [notebook-lesson-b7.md](notebook-lesson-b7.md) | No production path authors a notebook lesson yet (the notebook activities' authoring track); a commit in a notebook lesson gates what is shown and writes no evidence. The adversarial review's blocker, eleven major and three minor findings are fixed in one round (ledger NBF-5 to NBF-19): the sandbox has no writable host path and every host file goes through one checked module; the secret path is out of process arguments; a stop never leaves a server running; notebooks need a systemd user scope; a restart runs the pad's current cells. Open (NBF-16, accepted for now): notebook code can release its own held cells, so held cells gate what is shown and must never hold protected values |
| RD9c | Lesson redo and amendment | not started | — | — | Teacher v2, RD9a |
| RD10 | Video and carried polish: follow-along through judged correspondents, suggested chapters as a judged job with stored decisions (migration 268), `alt+;` timestamps, carried questions resurfacing | landed | this commit; fix round: this commit | [reader-rd10.md](reader-rd10.md) | One new structured prompt (the chapters judge), pinned. An accepted chapter does not feed section coverage (owner decision open). The adversarial review's blocker, four major and five minor findings are fixed in one round (ledger RD10-1 to RD10-15): follow-along, chapters and lesson tabs go through the goal lens's protection while a check is due; a cancelled suggestion stores nothing. Four places a held topic can still be named are listed for the owner (RD10-12 to RD10-15) |

## Notebook activities (queued by the owner on Nov 20; track H and NA0 run beside the queue)

The spec is `docs/specs/spec_notebook_activities_v1.md` (an untracked draft in the owner's checkout on Nov 20). Track H is an owner-side authoring harness outside every serving path; NA0 is six disposable spikes whose short result records land here.

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| H1 | `learnloop notebook check PATH --scope structure --out DIR`: a marimo notebook parsed without being run; cells, what each defines and reads, duplicate definitions, cycles; the `notebook` extra (marimo 0.25.2, wigglystuff 0.6.0); an import contract keeps serving code from importing the harness | landed | this commit | [notebook-h1.md](notebook-h1.md) | — |
| H2 to H4 | The authoring harness's cell writer (deterministic marimo code with parse-back and held cells kept); capability cards generated from the installed pinned packages (136 cards: every public wigglystuff and `mo.ui` export has one) with the example index and one declarative entry per tool; static contract and manifest checks, each with a self-test that breaks it | landed | this commit | [notebook-h2-h4.md](notebook-h2-h4.md) | Started by the owner on 2026-11-23 with teacher v2. Built by a Codex worker; nothing is run or rendered here (H5). No model call |
| H5 to H12 | The sandboxed runtime for authoring, layout and theme checks, review routes, acceptance and promotion, the author loop, retrieval, the evaluation set, the review console | not started | — | — | H5 uses the notebook runtime that now exists; H7's real calls and H8 wait on the owner's image route and cap |
| NA0.2 | The gate: a native marimo server under the hardened sandbox behind an app view (no network, a read-only notebook, isolated sessions, crash recovery, the bridge) | landed (gate passed in headless Chromium) | this commit | [notebook-na0.2.md](notebook-na0.2.md) | Five changes to the design as written, all in the record |
| Notebook runtime B1 to B3 | The runtime as product code: one supervised, sandboxed marimo server per pad or lesson, vault- and epoch-scoped; the frame proxy (per-session port and secret path, token injection, the frame's narrow API allowlist, the content-security policy); `notebook.open`, `status`, `close`, `release`, `run_cells` | landed | this commit | [notebook-runtime-b1-b3.md](notebook-runtime-b1-b3.md) | Moved up by the owner on 2026-11-23. No migration. Six defaults are named settings the owner may change. Not verified in the packaged app (WebKitGTK): that check, the notebook frame, cells in pads and lesson notebooks follow |
| NA0.1, NA0.3 to NA0.6 | Packaging and the content-security policy; runtime budgets; authoring yield; non-computable activities; the power calculation | not started | — | — | The owner: real material, a session with the packaged app and the phone |

## Teacher v2 (started by the owner on 2026-11-23; spec `docs/specs/spec_teacher_v2.md` §14)

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| TE5 parts A and C | One turn schema with capability sets, the eight historical provider contracts kept byte for byte (no identity pin or golden moved); the teacher's `create_goal_lo` action through the existing resolver and goal-creation service, with the library lookup before a new topic | landed | this commit | [teacher-te5.md](teacher-te5.md) | Built by a Codex worker. Part C changed the lesson's schema and doctrine deliberately: the pins it moved are listed in the record |
| TE5 part B | Compaction (§4.3) | waiting on the owner | — | [teacher-te5.md](teacher-te5.md) | Its trigger needs a margin that exists nowhere: fixed from one dry-run lesson, or learned during each live lesson |
| TE5 part D (L4-2) | The tag on `lesson_weight` (proposed mvp-0.70) | waiting on the owner | — | [algorithm-mvp-0.70.md](algorithm-mvp-0.70.md) | Capture effective difficulty curves from now on and keep historical fits, or snapshot historical reconstructions before rebuilding |
| TE6 to TE10 | Generated retention and transfer checks; lesson checks to the diagnoser; open lessons, the lesson as a sequence, arcs and deliverables; notebook verbs; chat | not started | — | — | TE5; TE9 also the notebook authoring track; TE10 MCP v2 |

## Lesson check credit (ledger TV2-1; ahead of the teacher track)

The router credits each lesson offer's committed delayed check as a full practice dose with no minutes charged, whether or not the learner returns or a question exists. The design is `docs/specs/spec_teacher_v2.md` §7.4; the fix is its own algorithm tag.

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| Steps 1 to 4 | Today's pricing pinned by tests; the as-of statistics of planned checks with a one-trial seed; the availability predicate shared with `delayed_check_words` and the dry minutes; a new rollout path for typed checks that no live decision can reach | landed | this commit | [algorithm-check-credit-steps-1-4.md](algorithm-check-credit-steps-1-4.md) | — |
| Step 5 | A read-only report over stored lesson offers and their delayed checks (`scripts/check_credit_report.py`) | landed | `52b9edc050` | [algorithm-check-credit-step-5.md](algorithm-check-credit-step-5.md) | — |
| Step 6 | Switch on at `mvp-0.62`: the offer builder attaches the sensors, the typed checks are priced, the inputs a later report needs are stored | landed | this commit | [algorithm-mvp-0.62.md](algorithm-mvp-0.62.md) | Ledger TV2-2 is open: a topic's first graded attempt makes it start forgetting in the rollouts (the memory model's asymmetry between an unpractised and a practised topic); it needs a memory-model successor |
| Step 7 | The record, the comparison on copies of the owner's vaults, the G2 design renumbered to `mvp-0.63` | landed | this commit | [algorithm-mvp-0.62.md](algorithm-mvp-0.62.md) | The owner upgrades their vaults (`learnloop upgrade --vault <path>`); the G2 design is renumbered to `mvp-0.63` |

## The first evening, finished (UX stage 2 of the journey audit's third part)

A first set of questions from the part read; a section's end finishes it; an honest build wait; what comes tomorrow; one OK for every model route. The owner's decisions of 2026-11-20 are in [ux-journey-audit-3.md](ux-journey-audit-3.md); each step has its own record.

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| Step 1 | One OK before every model route (UX-10): one acceptance record, no call before it, one sheet | landed | this commit | [first-evening-step-1.md](first-evening-step-1.md) | The phone cannot record the OK yet: it says to give it on the desktop and sends nothing |
| Step 2 | Which passages were seen (migration 256, two append-only tables) and the section's end as an observation; nothing reads them yet | landed | this commit | [first-evening-step-2.md](first-evening-step-2.md), [ux62-seen-viewport.md](ux62-seen-viewport.md) | Fixed after a live walk (ledger UX-62): the desktop recorded only the passage under its reading marker; it now records every passage shown during the learner's own movement. The walk is to be rerun |
| Step 3 | Question work owned per topic (migration 257, one claim per topic, the `topic_managed` stamp, topic-scoped checkpoints); old section jobs indexed and resumed unchanged; still triggered only by a section's finish | landed | this commit | [first-evening-step-3.md](first-evening-step-3.md) | — |
| Step 4 | A topic gets its questions once every passage it cites has been seen; Today says what is and is not ready | landed | this commit | [first-evening-step-4.md](first-evening-step-4.md) | A live-route walk is owed (the first step a walk can see); ledger UX-60 and UX-61 (a note's excerpt and the request's wording on a part-read request) |
| Step 5 | A section's end finishes it; the quick-check controls split (a successor tag); the phone's count observer (ledger UX-59) | landed | this commit | [algorithm-mvp-0.63.md](algorithm-mvp-0.63.md) | Walked on the live route twice on 2026-11-21 (a section read to its end); the fixes from those walks: [ux-section-end-round.md](ux-section-end-round.md), ledger UX-70, UX-78 to UX-85. Open: UX-86 (closing the app stops a build until Retry: the owner was asked) |
| Step 6 | Typed build stages and a several-line wait | landed | this commit | [first-evening-step-6.md](first-evening-step-6.md) | A live-route walk is owed; an append build (a book added to a subject that already has a map) names no part |
| Step 7 | A dated next-practice line at the session's end and on Today | landed | this commit | [first-evening-step-7.md](first-evening-step-7.md) | A live-route walk is owed: the days named match the days the questions are offered |
| Step 8 | Wording and the held-question line | landed | this commit | [first-evening-step-8.md](first-evening-step-8.md) | Fixed after the third live walk ([ux-walk3-round.md](ux-walk3-round.md)): ledger UX-67, UX-68, UX-69, UX-75, UX-76, UX-77. The held line links nowhere until an answer-hidden review screen exists |
| Step 9 | Web-page paragraphs and figures (UX-34, UX-35) | not started | — | — | — |
| Step 10 | A second source is readable while the first is still being built (UX-54) | not started | — | — | — |
| Step 11 | Keep an Ask answer's problems as practice | waiting on | — | — | Its own persisted-meaning review |

## Evidence packets and AD memory, beside the refactor

The owner decided on 2026-11-20 that five slices are built beside the refactor and that the behaviour steps come at the end of the queue (`docs/specs/spec_evidence_packets_v1.md` §12). None of the five needs a migration or an algorithm tag.

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| EP0t | The evidence-time rules readers already use, named: one serializable cutoff value with seven presets, a census of 60 callers, an inventory of what can be reconstructed historically, and the pinned identity of a prediction target | landed | this commit | [ep0t-time-policies.md](ep0t-time-policies.md) | 25 availability-SQL readers fit no preset and are left as they are: the record's question 1 |
| EP0 | Attempt facts in one typed value and the named predicates over them, every caller's result unchanged | landed | this commit | [ep0-attempt-facts.md](ep0-attempt-facts.md) | Two discrepancies between readers are the owner's call (ledger EP0-1, EP0-2); 41 readers are named in the census but not moved (import contracts, the adaptive-difficulty guard, a frozen package cycle) |
| EPp | Prediction snapshots on new receipts (the cutoff honoured, the target's pinned identity, the outcome distribution with the threshold categories, parameter provenance); then repeat-presentation receipts and the receipt repairs | landed | this commit | [epp-a-prediction-snapshots.md](epp-a-prediction-snapshots.md), [epp-b-repeat-receipts.md](epp-b-repeat-receipts.md), [epp-c-receipt-repairs.md](epp-c-receipt-repairs.md) | Open: ledger EPp-1 part B (stop dropping a batch whose time is unreadable: needs its own successor tag; part A, the scorer, landed) and EPp-3 (the repeat capture's cost on the serve path). EPp-2 fixed (21 test helpers register the sidecar's handlers themselves) |
| ADM0 | Pre-registered simulation and descriptive baseline | landed | this commit | [adm0-preregistration.md](adm0-preregistration.md), [adm0-simulation-report.md](adm0-simulation-report.md) | The simulation cannot select the decay's support or a warmth ladder, and slow-retention recovery is inadequate: questions for the owner before ADM2a; the count on the owner's backup copies is still owed |
| ADM1 | The predecessor's update and eligibility interface, and an unused memory fold | not started | — | — | — |

## Structured model answers: one shared contract check and one re-ask

The owner decided on 2026-11-20 that every structured model call gets one shared step: an answer that parses but fails a declared predicate is discarded and asked for once more, inside the caller's own budget. The design has 22 steps; adoption goes family by family in the order of learner-visible harm.

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| Step 0 | The shared module (`ai/structured_contracts.py`), its registered count of one contract re-ask (a provider's schema repair keeps its own rule: amended by step 5), and inert hooks | landed | `3f42da228a` | [structured-contracts-step-0.md](structured-contracts-step-0.md) | — |
| Steps 1 to 5 | The five local fixes of Nov 20: three stay local (pinned by tests), the empty-build predicate is extracted, the follow-up question's re-ask moves onto the shared step | landed | this commit | [structured-contracts-steps-1-4.md](structured-contracts-steps-1-4.md), [structured-contracts-step-5.md](structured-contracts-step-5.md) | Step 5 amended step 0: the one re-ask counts contract re-asks only; a provider's schema repair keeps its own rule (one per attempt, admitted by the caller); transport retries are untouched |
| Steps 6 to 22 | Adoption by call-site family, starting with blank replies in live dialogue (tutor, teach-back, teacher) | landed (step 6, the teacher turn) | this commit | [structured-contracts-step-6.md](structured-contracts-step-6.md) | The tutor's reply and the teach-back question are not adopted: neither call has an admission for a second request (ledger SC-1, the owner's call). Step 7 (the first build) needs the owner's rule for a second empty build. Steps 8 to 22 not started |

