# Refactor status

- Arc E is closed (E1 to E6, its adversarial review and fix round, and the rows due at its close; E7 waits for the evidence packet spec). The UX journey audit's first wave is done ([ux-journey-audit.md](ux-journey-audit.md): five persona walks, ten defects UX-1 to UX-10 in the bug ledger, twelve proposed fix stages); the owner asked for its fixes on Nov 19, and fix stages 1 to 4 (the broken controls; math macros and the empty goal; Today explains itself; the phone's small fixes) are on main with UX-1; the walks are run again next, with a second wave. Arc G has started: G1 is on main (the facts about a probe are apart from the verdict; K9-9 closed with it). The algorithm tag `mvp-0.61` is on main (G3-1 with the evidence reading fixes and the forgetting-clock cases; the owner's Nov 19 choices). Next in arc G: G6 (its design, the protection surface matrix and the fixes for the six defects the matrix confirmed are on main; the structural steps G6.2 and G6.3 are next), then G2.
- On main: the rebuild fix as `mvp-0.60`; the whole `repositories.py` split (L2a–L2d); the L1b cycle cuts (largest import component 84); E1–E6 (the router's choice is a pure function, its job control and trace assembly are their own modules, the objective's terms are apart from the rollouts, and an action kind has one guard test and one how-to list); G3's measurement of the two diagnosis beliefs; S1, S2 and M1; the K5 review with its two high fixes; `replay.ledger_bounded` removed.
- After E: G1 and G3, then K6 and G6, then G2; G4 only if G3 finds disagreement. H1 and H2 follow. E7 is built once, as the evidence view of `docs/specs/spec_evidence_packets_v1.md`.
- The owner decided the three K5 questions on Nov 18 (a repair followed by ordinary practice and a passed cold check confirms the repair; a skip leaves the forgetting clock and an answered attempt without a review restarts it, the due date staying; a certificate probe keeps counting retention with ordinary practice). The owner still needs to decide: the K5-8 paths that do not follow the clock rule (they need a tag), I2's reads on the decision path, K2.4c part B, the CLI-only code for L3, the diagnosis questions for K9.4, K9.13 and K9.17, and the open questions in the two specs.
- Decide H3–H6 with the AD memory spec. Do K8 and K7 before the terminal app rebuild or MCP v2. L5, T2, T5 and Z run at the close.

The orchestrator updates this file in each landing commit. This snapshot is the landing of `mvp-0.61` on main `713a0efd08` (Nov 19) and the owner's Nov 19 decisions (the fixes of the UX audit; the forgetting-clock cases for `mvp-0.61`).

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
| J2 | Drop the first approved family of tables | waiting on | — | — | Owner's approval and removal of readers and writers |
| J3 | Drop the next approved family of tables | waiting on | — | — | Owner's approval and removal of readers and writers |
| J4 | Drop the final approved family of tables | waiting on | — | — | Owner's approval and removal of readers and writers |

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
| I2 | Extract pure due queue ranking from persistence | waiting on | — | [refactor-i2.md](refactor-i2.md) | Owner's call about reading more rows on the decision path |
| I2-1 | Split serving writes from due queue reads | landed | `e1df438a03` | [refactor-i2.md](refactor-i2.md) | — |

## Arc G

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| G1 | Extract probe facts and hard stops | landed | `df8a5961b6` | [refactor-g1.md](refactor-g1.md) | `probe_facts` (pure) and `probe_verdict`; `decide_probe` derived, byte-equal on recorded and synthetic inputs; FG1's verdict on zeros replaced by its absence with the reason; one resolver for the three fitted-knob scopes |
| G2 | Make the action router the probe decider | being built | — | [design](refactor-g2-design.md), [steps 1 to 3](refactor-g2a.md) | Steps 1 to 3 are on main (this commit): every door characterized (28 tests, three journey cases), the post-miss choice as a pure function (10,260 cases equal), the diagnostic proposal's reads as a value object. Next: the pure successor evaluator, unserved, and the comparison report; then the behaviour step alone as `mvp-0.62`, after the owner's four decisions (design, section 7) and the report |
| G3 | Measure disagreement between the two diagnosis beliefs | landed | `8804080fcf` | [refactor-g3.md](refactor-g3.md) | Result on the live arxiv vault: four real pairs, none with different causes, all four one-sided, three with an exposed answer counted at full weight by the episode posterior (ledger G3-1). |
| mvp-0.61 | The evidence reading fixes as an algorithm tag: an exposed probe answer updates no belief (G3-1), unassessed criteria (ER-2), a regrade's source and a zero confidence on replay (K5-11, K5-12), the certificate probe's abstention (K5-3), a variant request is no review (K5-8) | landed | this commit | [algorithm-mvp-0.61.md](algorithm-mvp-0.61.md) | Adversarial review and its fix round inside (ledger T61-1 to T61-5 fixed; G3-3 open). The owner chose the clock cases and "no update" on Nov 19. The owner upgrades each vault (`learnloop upgrade --vault <path>`): the record's last section says what moves |
| G4 | Unify beliefs when measured disagreements warrant it | waiting on | — | [refactor-g3.md](refactor-g3.md) | The narrow fix G3-1 is on main as `mvp-0.61`. The full step is decided with a rerun of G3 on the owner's upgraded vaults |
| G5 | Give each duplicated fact one owner | deferred | — | — | Owner's Nov 17 queue |
| G6 | Use one authority for each protection question | being built | — | [design](refactor-g6-design.md) | G6.1 and the six fixes (G6.4 to G6.9) are on main. Next: G6.2 (each surface names its set in one table), G6.3 (one final passage admission), the five surfaces the matrix does not drive yet (with G6-P4 and G6.10), the display accounting extraction. K6-10 to K6-13 are independent fixes in the same area; K5-5 to K5-7 and K6-1 need a priming successor (a tag) |
| G6.1 | Pin what every protection surface answers for every protected fixture | landed | `99cda9d0ce` | [refactor-g6.1.md](refactor-g6.1.md) | `tests/test_protection_surface_matrix.py`: 37 fixture rows, 51 of 56 surfaces driven through their production functions, 1,502 cells, 100 fault cells, 30 reach cells; six defects confirmed as strict xfails. Not driven: the book solution region, the phone's dose offer, the pinned tutor job per row, compare, held feedback. Eleven cells differed from the design, none a leak |
| G6.4 to G6.9 | Fix the six protection defects the matrix confirmed (G6-P1, P2, P3, P5, P6, P7) | landed | this commit | [refactor-g6-fixes-1.md](refactor-g6-fixes-1.md) | A finished pinned tutor answer is checked at every read; an earlier Reader answer that drew on since-held material is left out of the model's context; the question author never sees a protected neighbour and refuses a held-out selection in every spelling; an exam-reserved item's passage stays out of figure prebuilds; a kept answer naming no stored passage is refused. Open: G6-P4 (the phone's dose offer, not yet driven); an exam unit's heading beside a selected exercise under a one-span held-out signal |

## Arc H

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| H1 | Distinguish the old scalar from FSRS difficulty | waiting on | — | — | Arc G |
| H2 | Compare four ways to use difficulty in replay | waiting on | — | — | H1 |
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
| K2.4c part B | Split oversized appends into checkpointed passes | waiting on | — | [refactor-k2.4c.md](refactor-k2.4c.md#part-b-splitting-an-oversized-append-design-only-not-built) | Owner's call on splitting append |
| K2.5 | Split normalization into named stages with one state | landed | `f623e525ac` | [refactor-k2.5.md](refactor-k2.5.md) | — |
| K2.6 | Share the judge heartbeat and lapse checks | not started | — | — | — |
| K2.7 | Put each job type in one table row | not started | — | — | — |
| K2.8 | Give each source kind one definition | not started | — | — | — |
| K2.9 | Centralize extractor choice and consent checks | not started | — | — | — |
| K2.10 | Fold small fixes for conflicts, estimates and comments | not started | — | — | — |
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
| K11 | Map the daily plan engine before moving code | waiting on | — | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | Owner's call on placing the map before E2 |

## Arc K: diagnosis

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| K9 | Map diagnosis and write its structure strategy | landed | `31787227e2` | [diagnosis strategy](k9-diagnosis-strategy-2026-11-14.md) | — |
| K9.0 | Investigate the planted-type simulation's robust probe path | landed | `ed96d1b9d0` | [refactor-k9.0.md](refactor-k9.0.md) | — |
| K9.0b | Correct the robust probe gate and instrument ranking | landed | `7bdec7edb5` | [refactor-k9.0b.md](refactor-k9.0b.md) | — |
| K9.1 | Settle block answers on a mid-check stop | landed | `55205863a2` | [refactor-adfix2.md](refactor-adfix2.md) | — |
| K9.2 | Explain why a check was withheld | landed | `4f5b325939` | [refactor-adfix2.md](refactor-adfix2.md) | — |
| K9.3 | Use an injected clock for primed-sibling ranking | landed | `ce11173c99` | [refactor-adfix2.md](refactor-adfix2.md) | — |
| K9.4 | Expire an untaken primed repair episode | waiting on | — | [ledger R1-2](refactor-bug-ledger.md) | Owner's answer to K9 Q1 |
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
| K9.13 | Separate episode posterior reads from its fold | waiting on | — | — | Arc G and owner's answer to K9 Q2 |
| K9.14 | Update the Diagnosis note to match code | landed | `1d3edadcfe` | [Diagnosis and Remediation](../learnloop-architecture-vault/Concepts/Diagnosis%20and%20Remediation.md) | — |
| K9.15 | Remove failure triage and its registry entries | landed | `be3cb2ac11` | [refactor-k9.15.md](refactor-k9.15.md) | — |
| K9.16 | Remove EVSI shadow selection and its panel | landed | `1fad9526bd` | [refactor-k9.16.md](refactor-k9.16.md) | — |
| K9.17 | Feed released holds and regrades into belief | waiting on | — | [ledger K9-3](refactor-bug-ledger.md) | Arc G and owner's answer to K9 Q2 |

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
| K10.9 | Extract pure reading of the figure author's answer | not started | — | — | — |
| K10.10 | Share the presentation chain and shown set | waiting on | — | — | K10.9 |
| K10.11 | Record figure refusals, reuse and available tiers | waiting on | — | — | K10.10 |
| K10.12 | Record each attempt by a rich figure job | waiting on | — | — | K10.11 |
| K10.13 | Move attempt-host policy under the figures package | dropped | — | — | Owner ruled out figures on phone and MCP |
| K10.14 | Read shown state and labels from the server | not started | — | [ledger K10-5](refactor-bug-ledger.md) | Due before the UX overhaul |
| K10.15 | Write the Figures note and correct stale lines | landed | `53f330c743` | [Figures](../learnloop-architecture-vault/Concepts/Figures.md) | — (K10-4 fixed) |
| K10.16 | Retire the eight figure content switches | waiting on | — | — | Owner's count for removing legacy reuse reads |
| K10.17 | Remove the dormant JavaScript animation tier | not started | — | — | — |

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
| L3 | Mark serving reach and enforce the tooling boundary | waiting on | — | — | Owner's list of CLI-only code that stays |
| L4 | Review which learned models need pure cores | landed (review) | `53f330c743` | [refactor-l4-review.md](refactor-l4-review.md) | Six extraction steps, in the order L4.1 claim priors, L4.2 cause slopes, L4.3 the episode posterior, L4.4 lesson-weight replay inputs, L4.5 the AD slot and commission decision, L4.6 the tail's fit-and-record assembly: not started, each under the stop rule. Five reproducibility gaps in the ledger (L4-1 to L4-5) |
| L5 | Explain long functions that other steps missed | waiting on | — | — | Refactor close |
| L6 | Make each extracted core return its record | waiting on | — | — | E2 and later core extraction briefs |
| L6a | Return records from the already extracted cores | waiting on | — | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | Owner's approval and the I2 core |
| L7 | Move the support floor as vaults advance | landed | `1da959e7d7` | [refactor-d1.md](refactor-d1.md) | — |

## Tests and phase reviews

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| T1 | Stop test files importing one another | landed | `732fe09aaf` | [refactor-t1.md](refactor-t1.md) | — |
| T2 | Rename tests for the behavior they prove | waiting on | — | — | Documentation stage at the close |
| T3 | Pin seeded draws in tests by default | landed | `412cc63b4b` | [refactor-t3.md](refactor-t3.md) | — |
| T4 | Port private patches and ratchet their counts | waiting on | — | [ledger K9-8](refactor-bug-ledger.md) | Ratchet decision. Porting rule already applies. |
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
| Stage 5 | Course setup and graded work (spec first) | not started | — | — | — |
| Stage 6 | A Goals place (spec first) | not started | — | — | — |
| Stage 7 | Load you can see and steer | not started | — | — | — |
| Stage 8 | Progress in words and the jargon sweep | not started | — | — | — |
| Stage 9 | Settings cleared | not started | — | — | — |
| Stage 10 | Help that shows what it gave away | waiting on | — | — | G6 and the Decider's first stage; H1, H2 |
| Stage 11 | The Reader redo | not started | — | — | Its cue model is a backend step |
| Stage 12 | Teacher screens remade | waiting on | — | — | A walk that reaches lessons (second wave) |
| Second wave of walks | Lessons, the workbench and figures, the practice exam, the returner, the expert, own notes, the project learner, two courses | waiting on | — | — | Stages 1, 3 and 4 on main |

## Second audit

| Step | What | State | Landing commit | Record | Waits on |
|---|---|---|---|---|---|
| S1 | Keep one status table in the repository | landed | `31ce39ec3d` | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | — |
| S2 | Stop batches when cost per removal more than doubles | landed | `31ce39ec3d` | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | — |
| S3 | Reorder open lanes around cuts and reviews | landed | — | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | Applied as a reordering: L1 and L2 ran ahead of the interior splits. L4's review has no slot yet. |
| S4 | Name the next features and their prerequisites | waiting on | — | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | Owner's approval of the strategy edits |
| P1 | Record what evidence each model call saw | waiting on | — | [Nov 16 audit](refactor-strategy-v3-audit-2026-11-16.md#3-additions) | Owner's call on packet records before the evidence packet build |
