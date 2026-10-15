# Stage "adaptive-difficulty-spec": adaptive difficulty and mastery, specified

**Branch:** `docs/adaptive-difficulty-spec` (base `4108e1ccd`, `main` at `mvp-0.24`, migration head 202).
**Date:** 2026-10-14; this record was added on 2026-10-15 in the Codex fix step (review finding F8), which found it missing.
**Deliverables:**
- `docs/specs/spec_adaptive_difficulty_v1.md`, "Adaptive difficulty and mastery: practice in the band, probes that discriminate, levels that mean something (v1)";
- `docs/specs/research/adaptive_difficulty_sources_v1.md`, its research appendix: method, the 121 verified sources with verdicts, the verification log and the local measurement.

This is a documentation stage, directed by the owner on 2026-10-14. No code, migration, config or test changed, and no paid API call was made. Codex research workers ran on the owner's ChatGPT subscription.

## What the spec contains

- **The current mechanism, with file:line (§3).** Item difficulty is the band the generator was told to hit, echoed back. Empirical difficulty is dark for a correct reason (θ and b confounded at n=1). The canonical prediction path and certification are blind to an item's feature point. There is no per-presentation forecast receipt.
- **The model (§5).** An explanatory-IRT likelihood over a dynamic, hierarchical per-(facet, capability) Gaussian state: a subject level, capability offsets and feature effects are shared, and facet and cell offsets refine as their evidence arrives. The item offset is integrated out, never estimated. §5.9 gives the arithmetic for the owner's target of a usable estimate within 10–15 answered questions per subject, and what sharing cannot buy. Outcomes are ordinal and help-adjusted, with unknown help timing and revealed answers censored. Updates are a deterministic assumed-density filter with zero model calls. §5.8 states what one learner's history cannot identify.
- **Selection (§6).** Practice maximizes the posterior probability of a 70–80% success chance, with exact logged propensities. It draws only inside a block the router already chose, over the items that block admits. By the owner's direction it serves from AD2, before any predictor promotion, reading each LO's own evidence until AD3. An item it cannot serve is deferred from the plan's pools until its blocking condition clears. Calibration is bounded to acceptable difficulty. Probes keep hypothesis EIG; AD5 composes capability hypotheses' success split from AD and freezes it in the probe snapshot.
- **Generation, audit, signals (§7).** The generator writes to a feature point and is no longer asked to hit a band. An independent Decider audit checks the features. Item-side signals enter the offset prior with learned weights. Serve inputs are frozen in a receipt.
- **Forecasts (§8).** Receipts are written before every attempt and scored by proper rules. Item-only forecasts are prepared with the pool; learner-conditioned forecasts compete as experts.
- **Levels (§9).** Credit is stored by feature point, read from declared or audited features, never from an estimated difficulty. Ladders are immutable and per goal. Requirements and certificates bind feature points, never level numbers. Exam and problem-set targets come from practice-available units only.
- **Supporting sections:** integration with the router, daily plan, Decider and harness (§10); successors, switches, tables and replay invariants (§11); the learner's view (§12); the n>1 path (§13); phases AD1–AD5 with fail-first tests (§14); owner decisions D1–D17 with recommended defaults, of which D3 and D15–D17 record the owner's direction and are decided (§15); deferrals with triggers (§16); open questions (§17); the agent prompt template (§18).

## What this stage did, and what it leaves for later

| | This stage (docs only) | Implementing phases (AD1–AD5) | Owner-run |
|---|---|---|---|
| Code, migrations, tests | None | Per §14, through the §18 prompt | — |
| Paid calls | None | Feature audit, outside forecasters, backfills; spend-capped, dry-run first | The AD1 backfills on the owner's copies |
| Measurements | §3.3, on backup-API copies of the three vaults *as committed at `4108e1ccd`* (two months stale), aggregates only | `learnloop ad data-check`, `learnloop ad report` | Both commands on copies of the current working vaults (Q1); reading the AD2 report; AD4's shadow rebuild |

## Method

- Read the code cited in §3.1 and the specs the spec touches, in this worktree at `4108e1ccd`.
- Ran six Codex research workers with live, unrestricted web search (appendix §1.1). Every source they returned was then verified by this stage at its primary record (appendix §1.2).
- Measured on backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) under the gitignored `fixtures-local/adaptive-difficulty/`, with the vaults loaded with `load_vault(..., load_environment=False)` and the databases opened read-only. No settings or key file and no working-vault database was read.

## Gate

| Check | Result |
|---|---|
| Internal consistency | Author read-through, three read-only Codex reviews before commit (appendix §5), then the post-commit Codex review, its fix pass, the Codex re-review and its fix pass, then the final Codex verify and its fix pass with the owner's direction (`docs/reviews/adaptive-difficulty-spec-codex-review.md`) |
| Code citations | After the final fix pass: 200 `file:line` citations (179 after the re-review fix pass, 164 after the first), continuation citations on the same line included, extracted by script, plus two line-opening continuations read by hand; every one resolves to a unique tracked file with a valid range, and each cited line was printed and read against its claim. Symbol citations (`exam_pool.reserved_item_ids`, `PracticeItem.canonical_exercise`, `canonical_projection.surface_group_id`, `practice_attempts.plan_presentation_id`) and the migration head (202) checked by grep |
| External citations | 121 of 121 sources verified at the primary record; every key the spec cites is a row of the appendix (appendix §1.2, §5). No fix pass added an external source |
| `git diff --check` | Clean |
| Tests | None run: no code changed |
| Paid calls | None |

## Open questions

The spec's §17: current data on the working vaults (Q1, owner-run), generator compliance with feature points (Q2), unit-to-facet mappings for exam targets (Q3), rating timing (Q4), data volume for the monitoring (Q5, renamed on 2026-10-15), whether the band should move with session state (Q6), and, since the revision below, the relatedness proposal's quality (Q7) and the records outside the spec (Q8). Each has a default or a measurement path.

## Revision 2026-10-15 (owner)

**Branch:** `docs/adaptive-ad3-live`, from main `2be98cc43` (migration head 203). Docs only: no code, migration, config or test changed, and no paid API call was made.

**The owner's decisions, in the owner's words:**
- "Ok agreed": start AD1 after the diagnosis-provenance stage lands, and the subject-level estimate sets where new topics start from AD2.
- "I feel like AD3 should be tried with AD2/AD1 just with a kill switch. AD3 is important to be able to have some semblance of adapting quickly within the vault to a learner's skill increase (via the Reader or by doing practice, whatever it is) without having to do a bunch of questions. it can be pretty vault dependent based on how the topics are related and whether being able to answer a given question implies knowledge about which topics (and to what extent it implies knowledge for those topics). this should definitely be some sort of learned model over time, but these intrinsics/hyperparams would probably change with the vault's subject (so perhaps a frontier LLM with high level semantic reasoning within a learned head harness here would be alright). we can just test it out and see for now"

**What changed in the spec:**
1. **Phases (D3 rewritten, D18 added; §0, §1, A6, §5.6, §5.9, §6.1, §8.2–8.4, §9.5, §10.1, §10.4, §11.1, §11.4, §14, §16–§18).**
   - AD1 is unchanged and comes first, once the "diagnosis input provenance" stage (`spec_mcp_frontend_c1.md` §4.8) has landed.
   - AD2 and AD3 now ship and go live together as one algorithm successor, each part behind its own kill switch: `selection`, `generation_contract` and `promoted_predictor`, plus `learned_coupling` and `reading_opportunities` for the subject view's new parts.
   - The subject view steers live draws, AD5's composition and the readiness numbers from the tag, and a new topic starts from the subject-level estimate.
   - The former promotion rule (field §7.4 plus the never-seen-cell split and band-region reliability) is now computed every report as monitoring. Five auto-flags each recommend a switch, and the report and glass box say whether sharing is helping, hurting or can't tell yet.
   - Flipping `promoted_predictor` off restores the LO view exactly. Exact logged propensities are kept everywhere.
2. **A learned, vault-specific relatedness and implication model (new §5.10, D19, R13; §5.2, §5.4, §5.5, §5.7, §5.8).**
   - **Shape:** a sparse soft Q-matrix (at most 3 loadings per item) and sparse LO couplings (at most 3 per LO), as extra shared terms in the hierarchy.
   - **Priors:** a frontier LLM proposes the prior means on the existing `ai.routing.llm_probability_llm` route, spend-capped and ledgered as `judgment_ledger` task `ad_relatedness`, and re-proposed when content changes. It reads the LO and facet text, the concept and prerequisite graph and item stems; it never reads learner data, held-out text or exam text.
   - **Learning:** the split and the coupling and implication strengths are learned per vault, by Bayesian model averaging over a 36-point a-priori grid (`ad_hyper_v1`) that includes zero coupling and zero implication.
   - **Safeguards:** sparsity, shrinkage, prediction-only influence, kill switches, and an auto-flag against uniform sharing on first attempts at never-seen topics.
   - **Supersession:** `spec_learner_field_v1.md` records it at F6, D2 and the two §11 rows.
3. **Reading as a learning opportunity (new §5.11, D20, A12).**
   - A section read, a passage viewed, a tutor exchange while reading and a worked example studied each raise the predicted level through a learned rate `γ_read[kind]`. They are frozen in a new receipt, `ad_reading_opportunities`, built in AD1.
   - Prediction only, never evidence, and no salience magnitude is read.
   - Scored on first attempts after reading, with an auto-flag.
4. **Fast adaptation without many questions (§5.9).**
   - New arithmetic shows what a coupling of strength `χ_C` buys a never-seen related topic. The own answers it needs before band mode fall from about 10 to about 6 at the grid's cap of 0.75, and the share of the related topic's deviation that moves its first prediction rises from 0.43 to 0.76.
   - Learning and reading transfer along couplings.
   - The honest limit: band mode on a topic's very first answer would need a correlation of about 0.95, which the grid never asserts.
   - New gate G-AD3-7 runs on synthetic vaults with known structure: related topics must adapt faster and unrelated ones must not be dragged.
5. **Consistency.**
   - New ids are A12, D18–D20, G-AD1-11, G-AD3-1 to G-AD3-10 (rewritten and extended) and Q7–Q8.
   - The migration head is updated to 203, and the storage-sync spec is noted as on main.
   - Exam protection (A8, now naming the relatedness proposal), held-out text never shown to any model, and frozen serve inputs (now with loadings) are unchanged in substance.

**Supporting files:**
- `docs/specs/research/adaptive_difficulty_sources_v1.md` gains §3 (g) with five sources: `[adams1997]`, `[chen2015q]`, `[culpepper2019]`, `[capstick2024]` and `[hoeting1999]`. Each was verified at its Crossref record or arXiv abstract page, with `[chen2015q]`'s abstract read at Europe PMC. That makes 126 in all.
- `docs/specs/spec_learner_field_v1.md` gains the supersession notes.

**Method.**
- **Code read at `2be98cc43`:** reader progress and its deletion path; section and span to LO mapping; span-view and reader-question ledgers; worked examples studied; the reading-signal firewall and its `apply_attempt` guard; router outcomes' exposure computation; the concept-graph model; field's `lo_general` registration; `judgment_ledger`'s schema; the AI routes.
- **Arithmetic:** the §5.9 coupled-case figures come from a linear-Gaussian computation in a local script (0.14 information per answer, no feature effects; its uncoupled case reproduces the spec's existing "about 10").
- **Records:** the "diagnosis input provenance" stage was identified from `spec_mcp_frontend_c1.md` §4.8 and `docs/reviews/mcp-c1a-narrow.md`.

**Gate.**

| Check | Result |
|---|---|
| Ids | Every D (D1–D20), A (A1–A12) and Q (Q1–Q8) the spec uses is defined. Every G id referenced is defined (by script) |
| Section references | Every in-spec § reference resolves to a heading (by script; the remaining matches point into other specs) |
| External citations | All 103 bracketed keys the spec cites are rows of the appendix (by script) |
| Code citations | The 24 `file:line` citations on changed lines, plus their continuation ranges, were re-checked at `2be98cc43`. Each resolves to a unique tracked file with a valid range, and each cited line was read against its claim |
| `git diff --check` | Clean |
| Tests | None run: no code changed |
| Paid calls | None |

**Left for the owner and the AD2/AD3 stage:**
- §17 Q8: dated notes in the knowledge-model spec (§8.3), the P3 reader spec (§8.2, §15.4) and the firewall module's docstring, scoped to AD's prediction-only use. This revision does not edit them.
- §17 Q7: the proposal's quality on real vaults is unknown until the successor runs; G-AD3-7 bounds the cost of a wrong proposal on synthetic vaults.
