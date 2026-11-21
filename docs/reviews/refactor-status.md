# Refactor status

- Arc E is closed (E1 to E6, its adversarial review and fix round, and the rows due at its close; E7 waits for the evidence packet spec). The UX journey audit has two parts ([ux-journey-audit.md](ux-journey-audit.md), [ux-journey-audit-2.md](ux-journey-audit-2.md)): the owner asked for its fixes on Nov 19; fix stages 1 to 4 and the waiting indicators the owner asked for are on main with UX-1; thirteen walks on the fixed application gave fifteen new defects (UX-13 to UX-27) and a re-ranked list of stages, of which "First questions arrive" is being built. Arc G: G1, the algorithm tag `mvp-0.61` (G3-1 with the evidence reading fixes and the forgetting-clock cases; the owner's Nov 19 choices), the G6 design, the protection surface matrix (G6.1), the fixes for the six defects it confirmed and the table of which set each surface reads (G6.2) are on main; G6.3 was stopped by the cost rule. Next in arc G: G2's behaviour step (its five preparing steps are on main; it waits for the owner's four decisions), then the rest of G6 (the surfaces the matrix does not drive, display accounting).
- On main: the rebuild fix as `mvp-0.60`; the whole `repositories.py` split (L2a–L2d); the L1b cycle cuts (largest import component 84); E1–E6 (the router's choice is a pure function, its job control and trace assembly are their own modules, the objective's terms are apart from the rollouts, and an action kind has one guard test and one how-to list); G3's measurement of the two diagnosis beliefs; S1, S2 and M1; the K5 review with its two high fixes; `replay.ledger_bounded` removed.
- After E: G1 and G3, then K6 and G6, then G2; G4 only if G3 finds disagreement. H1 and H2 follow. E7 is built once, as the evidence view of `docs/specs/spec_evidence_packets_v1.md`.
- The owner decided the three K5 questions on Nov 18 (a repair followed by ordinary practice and a passed cold check confirms the repair; a skip leaves the forgetting clock and an answered attempt without a review restarts it, the due date staying; a certificate probe keeps counting retention with ordinary practice). The owner still needs to decide: the K5-8 paths that do not follow the clock rule (they need a tag), I2's reads on the decision path, K2.4c part B, the CLI-only code for L3, the diagnosis questions for K9.4, K9.13 and K9.17, and the open questions in the two specs.
- Decide H3–H6 with the AD memory spec. Do K8 and K7 before the terminal app rebuild or MCP v2. L5, T2, T5 and Z run at the close.

The orchestrator updates this file in each landing commit. This snapshot is the landing of the first evening's step 4 (a first set of questions from the part read) and evidence packets' prediction snapshots (Nov 21), after `mvp-0.61`, and the owner's Nov 19 decisions (the fixes of the UX audit; the forgetting-clock cases and "no update" for exposed probe answers in `mvp-0.61`; waiting indicators).

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
| J2 | Drop the first approved family of tables | not started | — | — | Owner decided on 2026-11-20: drop the dead groups (a drop refuses a table that holds rows); `hypothesis_sets` is RAW_LEDGER (landed Nov 20, [owner-decisions-small-1.md](owner-decisions-small-1.md)) |
| J3 | Drop the next approved family of tables | waiting on | — | — | Owner decided on 2026-11-20: retired-but-read tables are dropped once the steps that own their readers have removed them |
| J4 | Drop the final approved family of tables | waiting on | — | — | Owner decided on 2026-11-20: as J3 |

## Arc D

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| D1 | Enforce the oldest supported tag at vault doors | landed | `1da959e7d7` | [refactor-d1.md](refactor-d1.md) | — |
| D2a | Run basic test vaults at the head tag | landed | `72ace2968a` | [refactor-d2a.md](refactor-d2a.md) | — |
| D2b | Move tests off old tags in passes | waiting on | — | [refactor-d2b4.md](refactor-d2b4.md) | Third old-tag pass |
| D2b part 1 | Retag shared fixtures and older successor test builders | landed | `16a9e3fd48` | [refactor-d2b.md](refactor-d2b.md) | — |
| D2b part 2a | Build the shared plan test vault at head | landed | `33c10723f2` | [refactor-d2b2.md](refactor-d2b2.md) | — |
| D2b part 2b | Move plan tests off old tags where possible | landed | `5f0d44269e` | [refactor-d2b3.md](refactor-d2b3.md) | — |
| D2b part 2c | Run the second pass over old-tag tests | landed | `6c114e2ae1` | [refactor-d2b4.md](refactor-d2b4.md) | — |
| D2b third pass | Review the remaining tests that name old tags | not started | — | [refactor-d2b4.md](refactor-d2b4.md) | — |
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
| D8 | Fix the four replay gaps pinned by tests | not started | — | — | — |
| D8 retired items | Replay retirement at the correct point in history | not started | — | — | — |
| D8 same-second grades | Preserve commit order for grades sharing a timestamp | not started | — | — | — |
| D8 claims | Re-anchor claims created after replay materializes state | not started | — | — | Design for re-anchoring |
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
| E9 | Rename misleading modules and move feature-owned files | not started | — | — | E1–E7 |

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
| I2 | Extract pure due queue ranking from persistence | not started | — | [refactor-i2.md](refactor-i2.md) | Owner decided on 2026-11-20: superset reads, two pure stages (I2a, I2b, I2c) |
| I2-1 | Split serving writes from due queue reads | landed | `e1df438a03` | [refactor-i2.md](refactor-i2.md) | — |

## Arc G

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| G1 | Extract probe facts and hard stops | landed | `df8a5961b6` | [refactor-g1.md](refactor-g1.md) | `probe_facts` (pure) and `probe_verdict`; `decide_probe` derived, byte-equal on recorded and synthetic inputs; FG1's verdict on zeros replaced by its absence with the reason; one resolver for the three fitted-knob scopes |
| G2 | Make the action router the probe decider | waiting on | — | [design](refactor-g2-design.md), [steps 1 to 3](refactor-g2a.md), [steps 4 and 5](refactor-g2b.md) | Owner decided on 2026-11-20: no probes until learned, plus a small randomized share (the share's size is owed); lands as `mvp-0.63` after the check-credit fix. The G3 rerun found the probe instrument cannot separate causes on the owner's cards (ledger G3-4): asked whether to bind the hypotheses first |
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
| H2 | Compare four ways to use difficulty in replay | not started | — | — | Owner decided on 2026-11-20: run H2 now; H3 to H6 are decided from its report |
| H3 | Retire scalar difficulty from mastery and surprise | waiting on | — | — | H2 and owner's call with the [AD memory spec](../specs/spec_ad_memory_v1.md) |
| H4 | Retire the model-estimated difficulty signal from AD | waiting on | — | — | Owner's call with the AD memory spec |
| H5 | Update exam strata, retrieval filters and authoring | waiting on | — | — | Owner's call with the AD memory spec |
| H6 | Remove scalar writers and DTOs, preserving hashes | waiting on | — | — | Owner's call with the AD memory spec |

## Arc Z

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| Z1 | Write and verify the modelling paper | waiting on | — | — | E5, arc G's belief decision and arc H |
| Z2 | Measure the refactor and report the savings | waiting on | — | — | Refactor close |
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
| K2.4c part B | Split oversized appends into checkpointed passes | not started | — | [refactor-k2.4c.md](refactor-k2.4c.md#part-b-splitting-an-oversized-append-design-only-not-built) | Owner decided on 2026-11-20: split, one neighbourhood per run, using cached tokens |
| K2.5 | Split normalization into named stages with one state | landed | `f623e525ac` | [refactor-k2.5.md](refactor-k2.5.md) | — |
| K2.6 | Share the judge heartbeat and lapse checks | landed | `ece7907885` | [refactor-k2.6.md](refactor-k2.6.md) | `judgment_claims.claim_heartbeat` replaces the two copied loops (it stops and joins its thread); a lapsed lease no longer commits (the paid answer is kept for the retry); service spend renews in each reservation's injected clock. Production −5 lines |
| K2.7 | Put each job type in one table row | not started | — | — | — |
| K2.8 | Give each source kind one definition | not started | — | — | — |
| K2.9 | Centralize extractor choice and consent checks | landed | this commit | [refactor-k2.9-10.md](refactor-k2.9-10.md) | `pdf_extractor_for` returns the extractor and the consent it needs; the import job asks it and raises the card, with the same words and order as before |
| K2.10 | Fold small fixes for conflicts, estimates and comments | landed in part | this commit | [refactor-k2.9-10.md](refactor-k2.9-10.md) | Conflict resolution writes its mapping, status and audit row in one guarded transaction (ledger K2-2 fixed); three stale comments corrected. Not done: one JSON token estimator: the three in use give different numbers (30,003, 30,003 and 5,003 tokens for one non-ASCII payload), and unifying them would move shard membership and with it manifests: it needs its own decision |
| K2.11 | Have desktop read ingest eligibility from the sidecar | not started | — | — | Due before the UX overhaul |
| K2.12 | Record why ingest made its key decisions | not started | — | — | — |
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
| K11 | Map the daily plan engine before moving code | not started | — | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | Owner decided on 2026-11-20: run the map now |

## Arc K: diagnosis

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| K9 | Map diagnosis and write its structure strategy | landed | `31787227e2` | [diagnosis strategy](k9-diagnosis-strategy-2026-11-14.md) | — |
| K9.0 | Investigate the planted-type simulation's robust probe path | landed | `ed96d1b9d0` | [refactor-k9.0.md](refactor-k9.0.md) | — |
| K9.0b | Correct the robust probe gate and instrument ranking | landed | `7bdec7edb5` | [refactor-k9.0b.md](refactor-k9.0b.md) | — |
| K9.1 | Settle block answers on a mid-check stop | landed | `55205863a2` | [refactor-adfix2.md](refactor-adfix2.md) | — |
| K9.2 | Explain why a check was withheld | landed | `4f5b325939` | [refactor-adfix2.md](refactor-adfix2.md) | — |
| K9.3 | Use an injected clock for primed-sibling ranking | landed | `ce11173c99` | [refactor-adfix2.md](refactor-adfix2.md) | — |
| K9.4 | Expire an untaken primed repair episode | not started | — | [ledger R1-2](refactor-bug-ledger.md) | Owner decided on 2026-11-20: an untaken episode ends at the item's next ordinary review |
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
| K9.13 | Separate episode posterior reads from its fold | waiting on | — | — | Owner decided on 2026-11-20: folded into G4 if G4 runs |
| K9.14 | Update the Diagnosis note to match code | landed | `1d3edadcfe` | [Diagnosis and Remediation](../learnloop-architecture-vault/Concepts/Diagnosis%20and%20Remediation.md) | — |
| K9.15 | Remove failure triage and its registry entries | landed | `be3cb2ac11` | [refactor-k9.15.md](refactor-k9.15.md) | — |
| K9.16 | Remove EVSI shadow selection and its panel | landed | `1fad9526bd` | [refactor-k9.16.md](refactor-k9.16.md) | — |
| K9.17 | Feed released holds and regrades into belief | waiting on | — | [ledger K9-3](refactor-bug-ledger.md) | Owner decided on 2026-11-20: folded into G4 if G4 runs |

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
| K10.10 | Share the presentation chain and shown set | not started | — | — | — |
| K10.11 | Record figure refusals, reuse and available tiers | waiting on | — | — | K10.10 |
| K10.12 | Record each attempt by a rich figure job | waiting on | — | — | K10.11 |
| K10.13 | Move attempt-host policy under the figures package | dropped | — | — | Owner ruled out figures on phone and MCP |
| K10.14 | Read shown state and labels from the server | not started | — | [ledger K10-5](refactor-bug-ledger.md) | Due before the UX overhaul |
| K10.15 | Write the Figures note and correct stale lines | landed | `53f330c743` | [Figures](../learnloop-architecture-vault/Concepts/Figures.md) | — (K10-4 fixed) |
| K10.16 | Retire the eight figure content switches | not started | — | — | The count is in (2026-11-20, backup copies): 28 stored figures in one vault across six prompt versions, none in the other two, no legacy `verified` row anywhere |
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
| L3 | Mark serving reach and enforce the tooling boundary | waiting on | — | — | Owner decided on 2026-11-20: the orchestrator produces the per-package list, the owner marks what stays |
| L4 | Review which learned models need pure cores | landed (review) | `53f330c743` | [refactor-l4-review.md](refactor-l4-review.md) | Six extraction steps, in the order L4.1 claim priors, L4.2 cause slopes, L4.3 the episode posterior, L4.4 lesson-weight replay inputs, L4.5 the AD slot and commission decision, L4.6 the tail's fit-and-record assembly: not started, each under the stop rule. Five reproducibility gaps in the ledger (L4-1 to L4-5) |
| L5 | Explain long functions that other steps missed | waiting on | — | — | Refactor close |
| L6 | Make each extracted core return its record | waiting on | — | — | E2 and later core extraction briefs |
| L6a | Return records from the already extracted cores | not started | — | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | Owner decided on 2026-11-20: approved; the due-queue half waits for I2's core |
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
| The first evening, finished | P19 to P24, F39 to F43: the build's wait in more than one line, what comes tomorrow, the quick check above the fold, a section's end, the chapter's figures beside the exercises that use them; UX-34 and UX-35 brought forward | not started | — | — | The owner: whether a section's end finishes it (UX-29); whether problems set by Ask become practice (F44) |
| Course setup, graded work and the practice exam (spec first) | P3, F8, F22: start from a goal, one course for a student's materials, graded work entry, sitting a stored practice exam | not started | — | — | — |
| A Goals place (spec first) | P2: all goals, deadline and scope edits, pause and resume, "Am I ready?" outside the Reader | not started | — | — | — |
| Lessons you can find, with the Teacher screens remade | F21, P12: resume a lesson, a lesson on the topic just missed, the Teacher screens | not started | — | — | The "teach me this" control on feedback waits for G2 |
| Load you can see and steer, for one or two courses (spec first) | P5, F29: the forecast, less or more, one budget split across courses | not started | — | — | — |
| Help shows what it gave away | P6 (owner's decision 2) on desktop and phone feedback; F24 | waiting on | — | — | The Decider's first stage; arc G |
| Progress in words and the jargon sweep | P10, F28 | not started | — | — | — |
| Web pages keep their equations | UX-11: a web page read into LearnLoop keeps every display equation, its headings' own words as titles and none of the page's furniture | landed | `5a7728283a` | [ux11-html-extraction.md](ux11-html-extraction.md) | New reads use extraction version 3; a page read before keeps its stored text and its card offers "Read it again" where equations are missing (a re-read re-pays the changed units' inventory later, so it is never automatic; marks are not carried: the new reading is held back until it is marked). Open: UX-34 (emphasis splits and glued paragraphs), UX-35 (figures and captions dropped), the chapter stays one section |
| The Reader redo | Search, margin cues, syntopic reading; UX-34 and UX-35 | not started | — | — | Its cue model is a backend step |
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

## Notebook activities (queued by the owner on Nov 20; track H and NA0 run beside the queue)

The spec is `docs/specs/spec_notebook_activities_v1.md` (an untracked draft in the owner's checkout on Nov 20). Track H is an owner-side authoring harness outside every serving path; NA0 is six disposable spikes whose short result records land here.

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| H1 | `learnloop notebook check PATH --scope structure --out DIR`: a marimo notebook parsed without being run; cells, what each defines and reads, duplicate definitions, cycles; the `notebook` extra (marimo 0.25.2, wigglystuff 0.6.0); an import contract keeps serving code from importing the harness | landed | this commit | [notebook-h1.md](notebook-h1.md) | — |
| H2 to H12 | The cell writer, cards and the example index, the contract and manifest checks, the sandboxed runtime, layout and theme checks, review routes, acceptance and promotion, the author loop, retrieval, the evaluation set, the review console | not started | — | — | H5 waits on spike NA0.2; H7's real calls and H8 wait on the owner's image route and cap |
| NA0.1 to NA0.6 | Packaging and the content-security policy; the server under the sandbox; runtime budgets; authoring yield; non-computable activities; the power calculation | not started | — | — | The owner: a scratch root outside the repository, real material, a session with the packaged app and the phone |

## Lesson check credit (ledger TV2-1; ahead of the teacher track)

The router credits each lesson offer's committed delayed check as a full practice dose with no minutes charged, whether or not the learner returns or a question exists. The design is `docs/specs/spec_teacher_v2.md` §7.4; the fix is its own algorithm tag.

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| Steps 1 to 4 | Today's pricing pinned by tests; the as-of statistics of planned checks with a one-trial seed; the availability predicate shared with `delayed_check_words` and the dry minutes; a new rollout path for typed checks that no live decision can reach | landed | this commit | [algorithm-check-credit-steps-1-4.md](algorithm-check-credit-steps-1-4.md) | — |
| Step 5 | A read-only report over stored lesson offers and their delayed checks (`scripts/check_credit_report.py`) | not started | this commit | — | — |
| Step 6 | Switch on at `mvp-0.62`: the offer builder attaches the sensors, the typed checks are priced, the inputs a later report needs are stored | not started | — | — | An explanation, from the value's components, of why the fix raises a lesson's value on the owner's present-day inputs (the report, 2026-11-20) |
| Step 7 | The record, the comparison on copies of the owner's vaults, the G2 design renumbered to `mvp-0.63` | waiting on | — | — | Step 6 |

## The first evening, finished (UX stage 2 of the journey audit's third part)

A first set of questions from the part read; a section's end finishes it; an honest build wait; what comes tomorrow; one OK for every model route. The owner's decisions of 2026-11-20 are in [ux-journey-audit-3.md](ux-journey-audit-3.md); each step has its own record.

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| Step 1 | One OK before every model route (UX-10): one acceptance record, no call before it, one sheet | landed | this commit | [first-evening-step-1.md](first-evening-step-1.md) | The phone cannot record the OK yet: it says to give it on the desktop and sends nothing |
| Step 2 | Which passages were seen (migration 256, two append-only tables) and the section's end as an observation; nothing reads them yet | landed | this commit | [first-evening-step-2.md](first-evening-step-2.md) | — |
| Step 3 | Question work owned per topic (migration 257, one claim per topic, the `topic_managed` stamp, topic-scoped checkpoints); old section jobs indexed and resumed unchanged; still triggered only by a section's finish | landed | this commit | [first-evening-step-3.md](first-evening-step-3.md) | — |
| Step 4 | A topic gets its questions once every passage it cites has been seen; Today says what is and is not ready | landed | this commit | [first-evening-step-4.md](first-evening-step-4.md) | A live-route walk is owed (the first step a walk can see); ledger UX-60 and UX-61 (a note's excerpt and the request's wording on a part-read request) |
| Step 5 | A section's end finishes it; the quick-check controls split (a successor tag); the phone's count observer (ledger UX-59) | waiting on | — | — | Step 4 |
| Step 6 | Typed build stages and a several-line wait | not started | — | — | — |
| Step 7 | A dated next-practice line at the session's end and on Today | not started | — | — | — |
| Step 8 | Wording and the held-question line | not started | — | — | — |
| Step 9 | Web-page paragraphs and figures (UX-34, UX-35) | not started | — | — | — |
| Step 10 | A second source is readable while the first is still being built (UX-54) | not started | — | — | — |
| Step 11 | Keep an Ask answer's problems as practice | waiting on | — | — | Its own persisted-meaning review |

## Evidence packets and AD memory, beside the refactor

The owner decided on 2026-11-20 that five slices are built beside the refactor and that the behaviour steps come at the end of the queue (`docs/specs/spec_evidence_packets_v1.md` §12). None of the five needs a migration or an algorithm tag.

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| EP0t | The evidence-time rules readers already use, named: one serializable cutoff value with seven presets, a census of 60 callers, an inventory of what can be reconstructed historically, and the pinned identity of a prediction target | landed | this commit | [ep0t-time-policies.md](ep0t-time-policies.md) | 25 availability-SQL readers fit no preset and are left as they are: the record's question 1 |
| EP0 | Attempt facts in one typed value and the named predicates over them, every caller's result unchanged | landed | this commit | [ep0-attempt-facts.md](ep0-attempt-facts.md) | Two discrepancies between readers are the owner's call (ledger EP0-1, EP0-2); 41 readers are named in the census but not moved (import contracts, the adaptive-difficulty guard, a frozen package cycle) |
| EPp | Prediction snapshots on new receipts (the cutoff honoured, the target's pinned identity, the outcome distribution with the threshold categories, parameter provenance); then repeat-presentation receipts and the receipt repairs | landed (part 1 of 3) | this commit | [epp-a-prediction-snapshots.md](epp-a-prediction-snapshots.md) | Part 2: receipts for repeat presentations. Part 3: the receipt repairs SR-2, SR-3 and EPp-1 |
| ADM0 | Pre-registered simulation and descriptive baseline | landed | this commit | [adm0-preregistration.md](adm0-preregistration.md), [adm0-simulation-report.md](adm0-simulation-report.md) | The simulation cannot select the decay's support or a warmth ladder, and slow-retention recovery is inadequate: questions for the owner before ADM2a; the count on the owner's backup copies is still owed |
| ADM1 | The predecessor's update and eligibility interface, and an unused memory fold | not started | — | — | — |

## Structured model answers: one shared contract check and one re-ask

The owner decided on 2026-11-20 that every structured model call gets one shared step: an answer that parses but fails a declared predicate is discarded and asked for once more, inside the caller's own budget. The design has 22 steps; adoption goes family by family in the order of learner-visible harm.

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| Step 0 | The shared module (`ai/structured_contracts.py`), its registered count of one recovery shared with the provider's schema repair, and inert hooks; no caller uses it | landed | this commit | [structured-contracts-step-0.md](structured-contracts-step-0.md) | — |
| Steps 1 to 5 | The five local fixes of Nov 20: three stay local (pinned by tests), the empty-build predicate is extracted, the follow-up question's re-ask moves onto the shared step | landed | this commit | [structured-contracts-steps-1-4.md](structured-contracts-steps-1-4.md), [structured-contracts-step-5.md](structured-contracts-step-5.md) | Step 5 amended step 0: the one re-ask counts contract re-asks only; a provider's schema repair keeps its own rule (one per attempt, admitted by the caller); transport retries are untouched |
| Steps 6 to 22 | Adoption by call-site family, starting with blank replies in live dialogue (tutor, teach-back, teacher) | waiting on | — | — | Steps 1 to 5; two owner questions (a strict rule for a second empty build; versions for predicates that change what counts as evidence) |

