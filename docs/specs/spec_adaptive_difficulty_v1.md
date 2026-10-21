# Adaptive difficulty and mastery: practice in the band, probes that discriminate, levels that mean something (v1)

**Status:** amended 2026-10-17 by the owner's D22 (self-check verdicts on in-passage questions enter the prediction as their own learned term; A12 limit 1 amended; §5.11, §10.4, §11, AD1/AD3 gates). Drafted 2026-10-14 at the owner's request, on branch `docs/adaptive-difficulty-spec` from main `4108e1ccd` (`mvp-0.24`); revised 2026-10-15 for the final Codex verify (F10) and the owner's direction of 2026-10-14 (practice targeting live before promotion, a per-subject time-to-usable target, certification never from an estimated difficulty, the first-attempt split as the primary score). Revised again 2026-10-15 on branch `docs/adaptive-ad3-live` from main `2be98cc43`, for the owner's decisions of that day: AD2 and AD3 ship and go live together, each behind its own kill switch (D3); AD1 starts after the diagnosis-input-provenance stage, and the subject-level estimate sets where new topics start (D18); topic relatedness and implication are a learned, vault-specific model (§5.10, D19); reading raises the predicted level (§5.11, D20). Revised a third time on 2026-10-15, on branch `docs/adaptive-reading-kinds` from main `37a2a7e5f`, for the owner's decision of that day: the reading-signal firewall exception is confirmed with its four limits (A12, D20; Q8 resolved); four kinds of discrete reading event each have their own learned weight with diminishing returns in dose (§5.11); the AD report gains a dose-and-burden analysis (§10.4); and a small randomized dose arm in the Reader identifies "how many" (§5.12, D21). Spec only: no code changes. Decision-ready: every owner decision in §15 has a recommended default, which is accepted unless the owner overrides it at its checkpoint (owner decision 2026-10-12). D3 and D15–D21 record the owner's direction and are decided (D21 on 2026-10-15: the dose arm runs live).

**Research appendix:** `docs/specs/research/adaptive_difficulty_sources_v1.md`. It holds the six research angles, every source with its verdict, the verification log, and the local measurement (appendix §4, summarized here in §3.3). Bracketed keys in this spec, such as `[watson2017]`, name rows of that appendix. Every external source cited here was opened at its primary record (DOI registry, arXiv abstract page, proceedings page or the paper itself) and its title and first author checked; anything that could not be verified was dropped.

**Relationship to other specs:**
- `spec_learner_field_v1.md`: this spec adds an arm family to its harness (§7.2), follows its constraints F1–F5, F7 and F8, and reuses its interaction signals (§3.1). Its switching rule (§7.4) is computed here as a monitor, not as a precondition for going live (D3). The owner's direction of 2026-10-15 supersedes, for this spec's subject view only, its F6 and D2 (no LLM relation graphs; cross-LO sharing only after held-out support) and its §11 deferrals of the facet-level graph field and `idea_hier_llm_prior`, under the safeguards of §5.10. The field spec records the supersession at those places.
- `spec_knowledge_model.md` §8.1, §8.3: the learned couplings of §5.10 are not semantic edges and are never written to the relations registry. KM §8.3's condition that cross-LO priors steer live decisions only after held-out support is superseded for the subject view by the same owner direction (A6). This revision does not edit the knowledge-model spec (§17, Q8).
- `spec_p3_reader_integration.md` §8.2, §15.4 (the reading-signal firewall): reading enters AD only as discrete learning opportunities in prediction and selection, never through the evidence chokepoint and never as a salience magnitude. The owner confirmed this exception on 2026-10-15 with four limits (A12, §5.11); the AD2+AD3 stage records it in the firewall module and adds its tested carve-out (§17, Q8).
- `spec_reader_workbench_v1.md` (RW1b's "let me try the next step" and "why does this step work", RW2c's logged passage draw) and `spec_reader_quick_check_producer.md` (the section quick checks): their answered prompts are one of the four reading kinds (§5.11), and the randomized dose arm offers one more of them, or one more worked example, at a section (§5.12).
- `spec_mcp_frontend_c1.md` §4.8: AD1 starts after its "diagnosis input provenance" stage lands (D18).
- `spec_action_router_v1.md` and `plan_router_r2_v1.md`: the router keeps choosing blocks; this spec chooses the item and its feature point inside a block, after the router's draw and only among items the chosen block admits, and logs exact propensities that compose with the router's (§10.1). It answers router §15.6 (exam and problem-set profiles seed difficulty and rigor).
- `spec_daily_loop_v1.md` §6: the plan container keeps its minutes, lanes, new-material admission and reconciliation. AD substitutes one admitted new-lane item for another inside a planned slot, within those rules (§10.1–10.2).
- `spec_measurement_efficiency_v1.md`: certification keeps its ledger, its caps and its delayed cold probe (§5.7); this spec records each credited observation's feature point beside the ledger, so a cell can be demonstrated *at a point* (§9).
- `spec_probe_eig_redesign.md`: probes keep their hypothesis EIG, value-of-information stopping and likelihood identity; this spec changes what goes into the conditionals of capability hypotheses, amending two of that spec's rules explicitly (§6.3), and how probe items are authored.
- `spec_storage_sync_v1.md` (on main at `2be98cc43`), §6.12 and requirement R13: the opt-in contribution export that n>1 priors would come from (§13).
- `docs/algorithm-change-playbook.md`: every serving change here is a successor with a kill switch (§11).

---

## 0. Summary

**The question.** When a learner answers easily, is that because they are skilled or because the item is trivial? A single response cannot tell. LearnLoop today mostly does not try. Its item difficulty is a number the authoring model writes after being told the band it should hit (§3, G1). The certification ledger gives the same credit to a heavily scaffolded item as to an exam-level one at the same capability (G4).

**The answer this spec builds.**
1. **Difficulty is a property of a feature point, learned from this learner's own history.** An item's difficulty is `b = (effect of its task features) + (an item offset with wide uncertainty)`. Feature effects are shared across items, so they can be learned from one learner (explanatory IRT, `[fischer1973]`, `[deboeck2008]`). The offset of a one-off item cannot be learned, so it is integrated out, never estimated (§5).
2. **The learner state is a posterior over ability per (facet, capability) cell, on the same scale as the feature ladder.** It is hierarchical: a subject level, capability offsets and feature effects are shared, and each facet and cell refines its own offset as evidence arrives, so answers anywhere in a subject inform every cell of it (§5.2). A learned, vault-specific relatedness model adds two sparse shared terms: which other topics answering an item implies knowledge of, and which topics are related. A frontier LLM proposes their prior means from the vault's content, and how far to trust them is learned from this vault's answers (§5.10). Reading counts as a learning opportunity that raises the predicted level, never as evidence. Four kinds of discrete reading event (reading a section or passage, a tutor exchange while reading, a worked example studied, an in-passage question answered) each have their own learned weight, with diminishing returns in how many occur before the next answer on the topic (§5.11). The AD report turns those weights into a dose-and-burden analysis: which active-reading practice improves cold retrieval most per minute, and how much of it is worth the time. Because a learner reads more when struggling, a small randomized dose arm in the Reader identifies "how many" (§5.12, §10.4). The state changes as the learner learns. Updates are deterministic and replayable, with zero model calls (§5.6). The target is a usable estimate within 10–15 answered questions per subject; §5.9 gives the arithmetic and what sharing and coupling can and cannot buy.
3. **Practice is chosen to land in the band.** Inside a block the router has already drawn, the rule serves, among the items that block admits, the one with the highest posterior probability that this learner's success chance lies in 70–80%. When no item in the cell can, it commissions one at the feature point most likely to. Near-ties and a small exploration share are randomized with exact, logged propensities (§6.1). The LLM writes a surface *at* the commissioned feature point and is no longer asked to hit a difficulty (§7). This serves from the AD2/AD3 successor with a-priori priors and reads the subject view from the start: band targeting corrects itself from the learner's outcomes (§6.1).
4. **Probes are chosen to discriminate.** They keep the existing hypothesis EIG and stopping rules. The item offset's uncertainty is folded into each hypothesis's predictions, and probe authoring targets feature points where hypotheses disagree, not a 45–55% band (§6.3).
5. **Every forecast is logged before the attempt and scored after it.** This covers the model in use, the incumbent, and outside forecasters (solver panel, an LLM given the item, an LLM and the Decider given the learner's history). Trust in each is learned from proper scores. Item-side signals enter the item-offset prior with learned weights. Forecasts that already read the learner's history compete as experts and are never folded in a second time (§8).
6. **Certification says "demonstrated up to level k".** Credit counts only from items at or above the level, judged by the features of the revision the learner answered and its audit, never by an estimated difficulty. The evidence is stored by feature point, not by level number. A level is always a level of one goal's ladder, and a requirement or certificate records the feature point it needs, so a new exam or milestone never changes what an existing one means. The features of practice-available exam and problem-set units define a goal's top level, "full mastery". Held-out exams are never served and never steer practice (§9).
7. **It ships in phases**, starting with logging that changes nothing served (AD1), once the diagnosis-input-provenance stage has landed. Practice in the band (AD2) and the subject view steering it live (AD3) then ship together as one successor, each part behind its own kill switch. Nothing waits for harness superiority: the harness keeps scoring the subject view against topic-only and uniform sharing, the report says honestly whether sharing is winning for this learner and vault, and auto-flags recommend a switch when it is not. Levels follow in AD4 and probe targeting in AD5. Each serving change is a successor with a kill switch (§14).

**The honest limits, stated once.** One learner's history cannot separate "skill rose" from "items at this feature level are easier than assumed" when feature levels rise in step with time. The design reduces the confound by randomizing feature points across time, reports it when it remains, and never presents a per-item difficulty as measured. And one learner's history can learn how strongly a vault's topics are related only in aggregate, never pair by pair; a never-seen topic still needs some of its own answers (§5.8, §5.9).

---

## 1. The owner's framing (binding) and what this spec takes from it

From the owner's request (2026-10-14):
- **A point difficulty is only an intermediate.** The deliverables are:
  1. **practice** items that improve the learner's skill, targeted at the desirable band (about 70–80% chance of success for *this* learner);
  2. **probes** that discriminate between live hypotheses, or elicit the most information for the next action.
- **Difficulty comes from this learner's traces:** history, cold and warm retrieval, hints, timing, optional ratings (easy / about right / hard, one tap, optional) and other variables. It does not come from an LLM labelling difficulty with no context.
- **Exam or problem-set questions can seed difficulty, best as the target** that defines "full mastery" where a vault has them. Held-out exam text is never served; only its features are used.

The direction agreed in conversation was evaluated against the research (§4.2). Most of it survives. Four parts change:
- the target becomes the expected response at a feature point (R1);
- the state becomes dynamic (R2);
- forecasts that already read the learner's history become competing experts rather than item-offset priors (R7);
- probes get their own objective, and calibration a bounded one (R4).

Later in the same conversation the owner directed four more points, binding and recorded as decided in §15:
- **Practice targeting goes live early (D3).** It serves without waiting for harness superiority, because band targeting corrects itself from outcomes (§6.1). On 2026-10-15 the owner extended this to the subject view (below).
- **A usable estimate within 10–15 answered questions per subject (D15).** This needs explicit sharing across cells (§5.2, §5.9).
- **Certification reads declared or audited features, never an estimated difficulty (D16, A11, §9).**
- **The first-attempt split is the primary score** for item-side signals and commissioned items (D17, §8.3).

On 2026-10-15 the owner directed four more points, binding and recorded as decided in §15:
- **AD1 starts after the diagnosis-input-provenance stage lands, and the subject-level estimate sets where new topics start** (D18). The owner's words: "Ok agreed".
- **AD3 goes live with AD2, behind a kill switch (D3).** "I feel like AD3 should be tried with AD2/AD1 just with a kill switch. AD3 is important to be able to have some semblance of adapting quickly within the vault to a learner's skill increase (via the Reader or by doing practice, whatever it is) without having to do a bunch of questions." The harness keeps scoring and reporting; it no longer gates (§10.4).
- **Relatedness and implication are a learned, vault-specific model (D19, §5.10).** "It can be pretty vault dependent based on how the topics are related and whether being able to answer a given question implies knowledge about which topics (and to what extent it implies knowledge for those topics). this should definitely be some sort of learned model over time, but these intrinsics/hyperparams would probably change with the vault's subject (so perhaps a frontier LLM with high level semantic reasoning within a learned head harness here would be alright). we can just test it out and see for now."
- **Reading and practice both raise the predicted level (D20, §5.11),** so a skill increase anywhere adapts related topics without many questions (§5.9).

Later on 2026-10-15 the owner confirmed the reading exception and refined it, binding and recorded in D20: "Confirming also the exception you scoped for the reading-signal firewall, except we should have each discrete event (maybe collate section read/passage view together for this) have its own weight, since then we can see whats the best way to read actively over time that best optimizes cold retrieval (like tutor exchanges while reading or studying worked examples, how many worked examples/in-passage questions should be done/asked to optimize for learning while minimzing friction and burden?)". This spec takes four things from it:
- **The exception is confirmed with its four limits** (A12): only discrete events; prediction and selection only, never evidence or certification; learned weights; its own kill switch and auto-flag.
- **Each kind of discrete event has its own learned weight** (§5.11): reading (a section read and a passage viewed, collated), a tutor exchange while reading, a worked example studied, and an in-passage question answered. Each weight shows diminishing returns in dose.
- **The goal is cold retrieval per minute, with little friction.** The AD report says which practice helps later retrieval most, how much of it is worth the learner's time, and what the Reader can do with that (§10.4).
- **"How many" needs randomization.** Observed doses are confounded by struggle, so a small randomized dose arm in the Reader identifies the effect of one more (§5.12). The owner decided it runs live (D21, 2026-10-15).

---

## 2. Standing constraints

| Id | Constraint | Source |
|---|---|---|
| A1 | **Derived and replayable.** Every posterior, score and level is rebuilt from ledgers, receipts and vault content, with zero LLM or embedding calls. | field F1; ADR-003 table roles |
| A2 | **Never evidence.** The model is a predictor. It never writes `grading_evidence`, mastery, facet recall, FSRS state or certification credit. Levels (§9) come from the observation ledger and the item's audited features, never from the posterior. The learned loadings and couplings (§5.10) and reading opportunities (§5.11) are predictions too: they never earn certification credit and never touch evidence. | field F2; `goal_certification.py:1-15`; owner 2026-10-15 |
| A3 | **Live changes through the playbook.** Each serving change is an immediate successor with a kill switch that restores the predecessor exactly, plus receipts. | playbook steps 1–8; field F3 |
| A4 | **Honest labels, generous defaults.** Untested, assumed, predicted and demonstrated are always distinguished; nothing predicted is shown as demonstrated (Ready vs Demonstrated, KM §9.6). | field F4; `exam_readiness.py:1-20` |
| A5 | **No point-fitted or hand-set hyperparameters; no hand-picked evidence weights.** Prior means and variances are set a priori and versioned (`ad_priors_v1`). Every effect that weighs an observation (feature effects, warmth, learning and reading rates, trust in each outside signal, rating and timing links) is latent state with such a prior, learned with uncertainty. So are the vault-level hyperparameters of sharing: how much is shared versus topic-specific, how strongly topics couple, and how strongly an answer implies knowledge of other topics. They are a posterior over an a-priori, versioned grid (`ad_hyper_v1`), learned per vault, never a fitted point value and never hand-set (§5.10). The few fixed measurement constants (§5.5) are versioned and swept in the harness. | field F5; owner 2026-10-14, 2026-10-15 |
| A6 | **Knowledge-model alignment, as the owner amended it on 2026-10-15.** No fixed propagation along authored edges (`prerequisite`, `part_of`, `related`, `analogous_to`, `confusable_with`): they are only inputs to the relatedness proposal (§5.10), whose influence is a learned, sparse, prediction-only coupling, never an edge in the registry. Sharing across LOs (the subject level, capability offsets, feature effects, learned couplings and loadings, and every other shared parameter learned from another LO's answers) steers live decisions from the AD2/AD3 successor on, without waiting for held-out support (D3, D19). This supersedes field F6, D2 and KM §8.3's held-out-support condition for this spec's subject view only, under §5.10's safeguards: sparsity, learned shrinkage, prediction-only influence, the kill switches and the auto-flags of §10.4. The harness keeps scoring the subject view against topic-only and uniform sharing. With `promoted_predictor` off, live decisions read the LO view (§5.6) exactly. | field F6, D2, §7.4; KM §8.1, §8.3; owner 2026-10-15 |
| A7 | **Biased sampling is declared.** Every served item records its serving origin. Every randomized choice logs seed and exact propensity before selection, the Reader's dose offers included (§5.12). | field F7; `randomization_layer.py:1-25` |
| A8 | **Exam protection.** Held-out exam and problem-set units are never served. They are never quoted to any AD prompt (generation, feature audit, forecasting, the relatedness proposal of §5.10). They never update learner state, and they never steer selection, generation or the ladder (router §15.6). Where the existing ingest inventory already gives them feature tuples, those tuples feed one evaluation-only report (§9.5).<br>*Recorded (AD2+AD3 fix round 8, Codex verify F19-F27):* **the boundary is one material view** (`adaptive_difficulty/material_view.py`). Every AD operation (a serve, a slot draw, a commission, landing reconciliation, generation targeting, the replay and its rebuilds, the report, the dose arm, a forecaster or calibration fit, the reading sweep, the relatedness proposal) asks the held-out predicate once and reads items, item facets and surface families, attempts (with latency), Reader questions, reading-opportunity receipts, plan presentations, reveals and forecast history only through it, each filtered by the held-out-material rule plus current exam reservations (`Protection.covers`). An attempt, reveal or receipt of a withheld item is invisible: it trains nothing, closes no reading window, takes no first surface and warms nothing; recorded reading receipts are revalidated against the current predicate. The protection is unconditional: it never reads `goals.held_out_selection` or any routine-serving switch. It fails closed: with the predicate unavailable the view is empty, a slot is served by the incumbent, generation takes the predecessor's target, the report discloses zero observations and why, and the dose arm draws nothing. `tests/test_ad23_material_view.py` fails when an AD module reads a raw item, attempt, question, receipt, presentation, reveal or snapshot reader (allowlist: the view, the predicate, `data_check`'s descriptive inventory and the background preparation queue's scheduling keys).<br>*Recorded (fix round 9, Codex verify of round 8):* **the contract is "protected == absent"** (`tests/test_ad23_contract.py`; the AST scan stays as a lint). On a vault holding every kind of protected material (held-out current items with sentinel stem, facet and surface family; a public item whose earlier answered revision is held out; protected answers with extreme latencies on shared LO, facet and family; a reveal; a commission result; a reading receipt; Reader questions citing a held-out span; a dose draw that offered one), every AD entry point (serves and the slot draw with its estimates, the serve hook, landing reconciliation, the replay and both rebuilds, the outside forecasters' prompt inputs, the commission draw and the commissioned generation request, the report, the dose arm, the reading sweep, the relatedness proposal, readiness and the router card, `ad report` and `ad eval`) writes and returns exactly what it does on a copy where that material does not exist, and no captured request quotes it. Filtering is at the source: an attempt is withheld when its current item or any revision it answered (its presentation's frozen revision, field's own revision resolution) is withheld, with its presentation; every derived quantity (field rows and their familiarity history through `load_attempt_rows(attempt_rows=...)`, AD's candidate duration estimates through `load_duration_evidence(attempt_rows=...)`, warmth, the dose moderator, practice minutes, history cards) is computed from the view's rows. The commissioned generation path reads the vault the view sees (`MaterialView.vault_view`) for contract and contrast reachability and the authoring context, and the serialized request is revalidated before it is sent (`CommissionedRequestGuard`); the commissioned target leaves out the incumbent's ability estimate. A landing of a withheld item closes no commission. One carve-out is recorded: AD1's `mastery_ekf` receipt records the incumbent's live mastery state verbatim (an exam answer is evidence there by design); it trains and selects nothing in AD and quotes no material.<br>*Recorded (the AD23 redesign, Option B + E1 + E2, 2026-10-21; supersedes the AST scan of round 8 and the contract's role of round 9):* **A8 holds by construction at the data sources.** Every AD entry point runs inside one guarded operation (`adaptive_difficulty/operation.py`). The operation computes the predicate once, and its **protection epoch** (a digest of the predicate's version, the held-out extractions and span keys, and the reserved exam items). It hands AD a projected vault (no withheld item or note, no facet only withheld material names, no provenance reference into withheld material) and a repository whose document-IR loader drops held-out blocks. While it is open, every SQLite connection to the vault carries an authorizer, which enforces four rules. A protected table (every column classified in `protected_tables.py`) is read only by the material view's rules, which withhold a row when any reference resolves to a withheld entity. The predicate's inputs are read only while it is computed. The incumbent's derived state is never read, but for the `mastery_ekf` carve-out; its serve-time constraints on a visible candidate are read in a named incumbent scope. Writes go to AD's own tables only. A refusal leaves AD unavailable for that operation and the incumbent serves (owner decision 2026-10-21): the denial is logged beside the database and counted in `learnloop ad report`, with no UI notice. The egress (a model request and its send guard's fresh re-reads) leaves the operation; incumbent maintenance and vault loads never run inside one. **E1 (owner decision 2026-10-21):** A8 ends at AD's commission target and the egress guard; the generator's internals are governed by the incumbent's exam protection, and the generation protections built in rounds 8-12 stay as built. **E2 (owner decision 2026-10-21):** one vault-wide epoch scopes every persisted artefact and cache computed from a projection. Relatedness runs are in force only at the epoch they were proposed under, so any protection change resets an adopted learned coupling until it is proposed and adopted again. A frozen outside-forecast state is sent only at its epoch, so a protection change expires pending background forecasts. The preparation cache and the replay and span-alias caches are keyed by the epoch. The contract is four tests (`test_ad_guard.py`, `test_ad_protected_tables.py`, `test_ad_projection.py`, `test_ad_epoch.py`), with one whole-pipeline differential kept as a smoke test (`test_ad23_contract.py`).<br>*Recorded (the AD23 redesign round 2, 2026-10-21):* the epoch digests everything the projection withholds (the material, the reservations, the protected items, the withheld revisions, notes and protected-only facets). Every AD artefact AD reads back (`protected_tables.EPOCH`) carries the epoch it was computed under and is read only at it: a row of another epoch, or one with no stamp, is never in force. Proposals are withheld by their effective payload's item before any expiry decision. A write reads only its own target and declared foreign keys. The first guard denial poisons its operation, so its output is discarded and the incumbent serves. | `exam_material.py:25-60`; ingestion §4.2, §8.5; router §15.5–15.6 |
| A9 | **Never blend.** AD's predictions change neither well depth nor the demonstrated beads. A level is a label beside them, never a second depth. | field F8; `apps/learnloop-tauri/src/screens/KnowledgeWellView.tsx:8-26` (one continuous quantity owns the geometry; Demonstrated is a discrete marker) |
| A10 | **Asking for help is never penalized in the record.** Hints change the outcome category of one observation (§5.3). They never reduce certification credit beyond the existing unassisted rule, and never write extra evidence. | field G13 |
| A11 | **Certification never reads an estimated difficulty.** Levels, requirement points, feature-qualified credit, certificates and the cold probe's item choice read only declared features (stamped on the answered revision, or written in a target or requirement) and audited features, the more conservative per dimension. They never read an estimated `b`: not AD's posterior, `β`, `α` or any `z` signal, not the learned loadings, couplings or reading terms (§5.10–5.11), not the item's `difficulty` label or `difficulty_source`, not a solver-panel rate, not empirical-Bayes `b`, not `resolve_item_irt_params` (§9). | owner 2026-10-14 (D16); A2 |
| A12 | **Reading is a learning opportunity, never evidence: a confirmed exception to the reading-signal firewall, with four limits.** The owner confirmed it on 2026-10-15 (D20).<br>1. **Only discrete events.** The listed kinds of §5.11 (reading, a tutor exchange while reading, a worked example studied, an in-passage question answered), each the fact that it happened, with a dose. No salience magnitude reaches AD's state, a draw or an offer: no dwell, scroll, highlight, skip, visibility segment, active time or answer text, and no salience projection. *(Amended 2026-10-17, D22:)* one typed value is admitted, the learner's self-check verdict (matches, partly or no) on an answered in-passage question, as its own learned term on the prediction (§5.11); it is a three-value judgment from `judgment_ledger`, not a magnitude, and limits 2–4 bind it as they bind the events. The dose-and-burden report reads the Reader's recorded visit minutes as a cost only, as the Reader report already does, and nothing it computes acts (§10.4).<br>2. **Prediction and selection only, never evidence or certification.** The events shift AD's *predicted* level and so its draws, forecasts and readiness numbers. They never pass the evidence chokepoint (`reject_salience`, wired into `attempts.apply_attempt`), and never write evidence, mastery, facet recall, FSRS, certification credit or levels.<br>3. **Learned weights.** Each kind's effect is latent state with a-priori, versioned priors, learned per vault, never hand-set (§5.5, §5.11).<br>4. **Its own kill switch and auto-flag.** `reading_opportunities` restores the subject view without reading exactly, and the reading auto-flag recommends it when reading predicts worse (§10.4). `reading_self_check` (D22) removes only the verdict term, restoring D20's behaviour exactly, with its own auto-flag.<br>The firewall's existing checks and tests stay. The AD2+AD3 stage updates the module's rule text and adds one narrow carve-out that admits only the listed kinds, with its own test (§5.11, G-AD3-13). | owner 2026-10-15 (D20); P3 reader spec §8.2, §15.4; `attempts/salience_firewall.py:1-24`; field §3.1 |

---

## 3. The current mechanism and its gaps

### 3.1 What exists (re-checked in this worktree at `4108e1ccd`)

- **Where item difficulty comes from.** Practice generation inverts the mastery channel's 2PL link at the learner's estimated ability. It turns the target success interval into a difficulty band (`content/authoring/practice_generation.py:2133-2149` `_difficulty_for_success`, `:2152-2182` `success_band_difficulty`, called at `:403-410`), with bands from config (`config/schema.py:398-399`: practice `(0.70, 0.85)`, probe `(0.45, 0.55)`). The authoring prompt then tells the model to "Calibrate each item's difficulty to its target's recommended_difficulty_band (~70-85% expected success) … and set difficulty and difficulty_source='llm_estimate' accordingly" (`practice_generation.py:1919`; also `practice_generation.py:1062`, `:1922`). For probes it says "Set difficulty within the recommended_difficulty_band: it lies on the learner's boundary (~50% expected success)" (`practice_generation.py:1984`).
- **How difficulty reaches the learner model.** `item_irt_params` maps the stored `difficulty ∈ [0,1]` to `b = 2.5·(2d − 1)` (`learner/mastery.py:356-378`). `resolve_item_irt_params` is "the single seam" through which the mastery EKF, surprise and prediction read it (`:381-397`). Primed attempts subtract a fixed `priming_b_offset = 2.0` (`config/schema.py:156-162`; `attempts/attempts.py:3402-3410`).
- **Empirical difficulty is dark.** An empirical-Bayes update of `b` exists (`mastery.py:400-447`) but ships disabled (`config/schema.py:163`). The config comment gives the reason: "theta and b are confounded at N=1" (`:150-155`). A monitor flags items with one-sided residuals after 5 attempts (`learner/calibration.py:1-7`, `:39-99`).
- **The solver panel.** For practice-family variants it sets a per-variant offset from the panel's solve rate *relative to the parent item's difficulty*, or 0.5 when the parent has none (`ops/pf_generation.py:183-198`). LLM self-labels are never requested there (`:37-42`).
- **Depth rungs.** A rung is one capability plus one task-feature point (`curriculum/depth_rungs.py:1-16`, schema `p1_launch@1`, `substrate/activity_patterns.py:71-89`). It is chosen by a mastery-band ladder with fixed cut points (`depth_rungs.py:228-307`) and an "optimism" step of one rung when evidence is thin (`:310-319`). A diagnosed hypothesis can override it (`:323-333`). The prompt is told that "Difficulty varies WITHIN the waypoint" (`practice_generation.py:1922`).
- **Prediction in serving.** On a canonical-state vault, an LO with blueprints predicts item success by a noisy-AND over component recall with slip and guess (`scheduling/selection_rewards.py:419-457` → `learner/blueprint_projection.py:370-392`). Item difficulty does not enter. Selection rewards an item by its fit to a target band per intent: practice `(0.55, 0.75)`, probe `(0.40, 0.60)`, repair `(0.75, 0.90)`, transfer `(0.60, 0.80)` (`selection_rewards.py:516-526`).
- **Certification.** Credit for one observation is its pseudo-mass if the observation is direct or embedded and unassisted, else zero (`learner/capability_mapping.py:246-266`). Credit accrues per `(facet, capability)` (`substrate/canonical_projection.py:920-950`). A cell is demonstrated at credit ≥ 1.0 (`goals/certification.py:1-7`; `goals/goal_certification.py:85-101`). A delayed cold probe per certified LO measures `false_certification_rate` (`goals/certification_cold_probe.py:1-40`; success at correctness ≥ 0.8, `:197`).
- **Learner difficulty reports.** An "easier/harder" request writes a self-graded `self_report` attempt at 0.3 evidence mass. It moves mastery, facet recall, the capability ledger and FSRS (`content/authoring/rung_variants.py:1-22`). A "too easy / too hard" retirement writes an LO claim at a fixed level (`content/authoring/item_authoring.py:317-365`).
- **Other signals.** `practice_attempts` records `hints_used`, `primed`, `latency_seconds` and a 1–5 pre-answer `answer_confidence` (`attempts.py:175`; mapping at `field/types.py:75`).
  - **Hints keep only their total.** Ordinary hints have no timing; the field's own judge is told so (`field/probability_states.py:98-101`). Only tutor questions log when help came (`question_events.attempt_progress`, `no_draft` or `draft_started`; read at `field/signals.py:351-359`).
  - **Latency is a time cost, never ability evidence.** It sizes the daily plan (`daily_plan/estimates.py:1-18`), the minutes of value-of-information stopping (`diagnosis/voi_stopping.py:421-449`) and the cost of an unresolved misconception (`scheduling/unresolved_cost.py:10-17`, `:131-145`). Probes log it as an observation feature only (`diagnosis/probe_episodes.py:2551-2560`).
- **Forecasts.** `attempt_surprise` holds a predicted score distribution but is DERIVED and recomputed (`db/table_roles.py:76`). Exams freeze item predictions (`goals/exam_calibration.py:1-15`). The field harness scores arms offline and prequentially (`spec_learner_field_v1.md` §7.2), and the T8 success-head arms are offline only (`field/success_head.py:1-15`). There is no per-presentation forecast receipt.
- **Exam profiles.** They carry task-family, capability, representation, format and point/time counts (`content/synthesis/exam_profile.py:57-80`), but no task-feature target.
- **Reading and relatedness inputs** (added 2026-10-15, checked at `2be98cc43`; the reading bullets re-checked, and in-passage questions and Reader timing added, at `37a2a7e5f`).
  - **Reading progress** is `reader_section_progress`, a WORKFLOW table (`db/table_roles.py:348`). Its `completed_at` is stamped once and never cleared (`db/repositories.py:13037-13038`), but its rows are deleted with their extraction (`delete_source_artifact`, `:18906`, at `:18960-18966`).
  - **Section and span to LO.** A section maps to the active LOs whose provenance cites its spans (`learning_objects_for_section`, `reader/reader_progression.py:66-79`); a span maps through its section (`learning_objects_for_span`, `:44-63`).
  - **Reading events.** Every span view appends a `source_exposure_events` row (`db/repositories.py:4115-4118`; RAW_LEDGER, `db/table_roles.py:414`). A tutor question asked while reading is a `question_events` row with context `reader` (`migrations/086_reader_dialogue.sql:62`; RAW_LEDGER, `db/table_roles.py:340`). Worked examples the learner was shown, or that sit in sections they read, are found by `studied_worked_examples` (`instructional/exposure.py:95-131`), which finds worked-example blocks by their role (`:104`).
  - **In-passage questions.** Two kinds exist, and neither writes an attempt today.
    - **Quick checks** are `reader_authored_questions` rows (WORKFLOW, `db/table_roles.py:345`), answered on the row (`answered_at`; `migrations/105_reader_authored_questions.sql:5-23`). RW1a added a scope, a `question_style` (`recall`, `next_step`, `why_step`, `assumptions`, `reconstruct`) and the learner's `self_check` (`matches`, `partly`, `no`). Answering stays formative: "no attempt, observation, mastery or FSRS row" (`migrations/185_reader_authored_question_scopes.sql:12-29`). RW1b's "let me try the next step" and "why does this step work?" write the `next_step` and `why_step` styles; the schema admits them, but the actions are not built at `37a2a7e5f`.
    - **Owner-placed reading questions** are instructional, source-visible administrations, "categorically ineligible for certification" (`reader/reader_dialogue.py:17-22`). Their answer is a `reader_answer_submitted` interaction event on the administration (`:963-990`), a kind the firewall stamps `salience_only` (`attempts/salience_firewall.py:40-68`). A formative reading answer "NEVER touches a posterior, FSRS state, or certification" (`reader/reader_dialogue.py:29-34`).
  - **Reader timing.** A Reader visit's close event carries its active seconds, which the Reader report sums into active minutes (`reader/reader_report.py:238-240`). Practice has `latency_seconds` and the plan's answer-minutes estimate (`daily_plan/estimates.py:1-18`).
  - **Router §15.2's covariate view is not built.** Router outcomes still compute the last exposure from attempts and reveals only (`router/outcomes.py:541-545`).
  - **The reading-signal firewall.** Reading signals carry authority class `salience_only`, and the evidence chokepoint rejects them: `reject_salience` is the first step of `apply_attempt` (`attempts/salience_firewall.py:1-24`; `attempts/attempts.py:2678-2683`). The module's standing rule says reading signals never enter "mastery, posterior, readiness, certification, or scheduling" (`attempts/salience_firewall.py:4-8`). It names "the ONE allowed downstream", proposal priority (`:23-24`, `proposal_priority_signal` at `:137-149`), and its test also checks statically that the belief modules never import it (`tests/test_salience_firewall.py:94-113`).
  - **The randomization layer** admits four designs (`scheduling/randomization_layer.py:57`) and reads proximal outcomes at the next spaced cold review (`:19-26`). A cold retrieval is one at least `COLD_RETRIEVAL_DELAY`, one day, after the last exposure (`diagnosis/remediation.py:31`).
  - **The concept graph.** Authored edges are `prerequisite`, `confusable_with`, `part_of` or `related` (`vault/models.py:171-178`), and an LO lists its prerequisites (`:330`). Knowledge-model §8.1 gives every relation type no direct learner-belief effect.
  - **Uniform sharing in the harness.** Field's `lo_general` is registered as a harness predictor (`field/predictors.py:510`).

### 3.2 Gaps

| Id | Gap | Consequence |
|---|---|---|
| G1 | **Difficulty is the requested band, echoed.** The model is told the band and asked to set `difficulty` inside it (`practice_generation.py:1919`). | The stored number mixes the learner estimate that produced the band with the model's view of the item. Feeding it back as `b` is circular. |
| G2 | **The one place difficulty is learned from outcomes is dark,** for a correct reason (θ and b confounded at n=1). | No mechanism learns anything about difficulty from this learner. |
| G3 | **The canonical prediction path is blind to item difficulty** (`blueprint_projection.py:370-392`). | A trivial item and a hard item on the same recipe get the same predicted success. The band fit in selection cannot tell them apart. |
| G4 | **Certification is blind to the item's feature point within a capability** (`capability_mapping.py:246-266`). | An unassisted success on a cued, near-recall item at `procedure_execution` earns the same credit as an exam-level one. This is "answered easily because the item is trivial". |
| G5 | **Four inconsistent target bands,** none logged as a forecast or checked against outcomes (`schema.py:398-399`; `selection_rewards.py:516-526`). | Generation aims at 70–85% while serving aims at 55–75% for the same intent. Nobody knows which is hit. |
| G6 | **Rung selection is a fixed threshold ladder** with a one-step optimism heuristic (`depth_rungs.py:228-319`). | There is no posterior, no information criterion and no propensity, so off-policy evaluation of rung choice is impossible. |
| G7 | **Learner reports are hand-weighted evidence** (0.3 mass; fixed claim levels) (`content/authoring/rung_variants.py:1-22`; `content/authoring/item_authoring.py:317-365`). | This conflicts with A5. A report counts as evidence with a weight nobody learned. |
| G8 | **No forecast receipt per presentation** (§3.1, Forecasts). | Trust in the solver panel or an LLM forecaster cannot be learned from live serving, only offline. |
| G9 | **Solver-panel difficulty is relative to a parent** whose own difficulty may be an LLM label (`pf_generation.py:183-198`). | The panel's information is a relative offset, which is right, but it is stored as an absolute number. |
| G10 | **Hints, priming and timing enter as fixed adjustments** (`priming_b_offset = 2.0` "provisional"; hint dampening `attempts.py:4461`). Latency is not evidence. | Ceiling effects go unaddressed. When most answers are correct, correctness alone says little about the margin, and the time taken or a rating could. |
| G11 | **No full-mastery target** (`exam_profile.py:57-80`). | The router §15.6 direction (exams seed rigor) has no level to aim at. |
| G12 | **The cited design doc does not exist.** `learner/mastery.py:1` and `learner/calibration.py:1` cite `spec_irt_difficulty.md`, which is not in `docs/`. | The IRT seam is undocumented. §5 of this spec documents its successor. |

### 3.3 Measurement on a backup copy (committed snapshot)

On backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of the three working vaults *as committed at `4108e1ccd`*. That snapshot is dated 2026-08-16 and is at `mvp-0.8`, so it is two months stale. Aggregates only; the method is in the appendix.

| Vault | Items | `difficulty_source` | Items with `task_features` | Graded attempts (excl. self-report) | Items attempted once / ≥2 | Full-credit share |
|---|---|---|---|---|---|---|
| `linear_algebra` | 99 | `llm_estimate` 97, `author` 2 | 96 | 62 | 47 / 7 | 0.74 |
| `probability` | 77 | `llm_estimate` 46, none 31 | 46 | 2 | — | — |
| `arxiv_v2` | 32 | `llm_estimate` 1, none 31 | 32 | 0 | — | — |

**`linear_algebra`, first unassisted and unprimed attempt per item vs its LLM `difficulty` label (n = 53):**
- Spearman ρ = **−0.60** overall (approximate 95% interval −0.75 to −0.39, Fisher z). Harder labels went with lower first-attempt correctness.
- Within capability, the residual correlation is **−0.42** (approximately −0.63 to −0.16).
- Per capability: retrieval −0.30 (n = 33), schema_interpretation −0.67 (n = 11), procedure_execution −0.30 (n = 5), method_selection −0.87 (n = 3).
- Coverage: latency on 18% of attempts, `answer_confidence` on 47%, hints on 3%, primed on 0%.

**What this says.**
- In this learner's own data, the echoed labels carried real ordinal information. That differs from the population result that LLM Easy/Medium/Hard labels predicted empirical difficulty at ρ = 0.06 `[an2026]`.
- The labels were written with the learner's band in context (G1), so part of what they encode is the learner estimate, not only the item.
- The data are one learner, two months old, mostly retrieval items, and near ceiling (74% full credit).
- Both readings point the same way: **neither trust nor discard the label; learn its weight** (§7.3, α_llm).
- The same measurement on the current working vaults was not run in this stage (§17, Q1). AD1's `learnloop ad data-check` reproduces it.

---

## 4. Research synthesis

Six Codex research workers with live, unrestricted web search covered six angles:
- (a) QUEST/QUEST+/Psi and Bayesian adaptive psychometrics;
- (b) Bayesian optimal experimental design;
- (c) explanatory IRT and item generation;
- (d) desirable difficulty, curriculum bandits and knowledge tracing;
- (e) LLM difficulty estimation and conditioned generation;
- (f) n=1 identifiability, pooling and forecast scoring.

121 sources were verified (appendix). Five more, for the relatedness model, were added and verified on 2026-10-15 (appendix §3 (g)), and nine more, for active-reading doses and randomized offers, later the same day (appendix §3 (h)). What follows is what they change.

### 4.1 Findings and the design changes they force

**R1. Target the family expected response at a feature point, not a point difficulty.**
- **Findings.**
  - Random-item IRT treats items as draws from a population and models unexplained item variation `[deboeck2008]`; LLTM with an error term does the same for feature-based difficulty `[janssen2004]`, `[fischer1973]`.
  - Item-cloning CAT chooses a family, then a random member `[glas2003]`.
  - The *family expected response function* summarizes "the probability of a correct response to an item randomly generated from an item family" `[sinharay2003]`.
  - Generating items during testing requires propagating item uncertainty into person estimates `[embretson1999]`.
  - On-the-fly generation is feasible, but imperfect equivalence within item models costs precision `[bejar2003]`.
- **Change.** The band applies to `p̄(x)`, the expected success over items generated at feature point `x` for this learner's state (§5.7). It does not apply to a point estimate for one item. The realized item is re-forecast before it is served (§7.4).

**R2. The learner changes during practice, so the state must be dynamic.**
- **Findings.**
  - QUEST/QUEST+/Psi assume a fixed observer `[watson1983]`, `[watson2017]`, `[kontsevich1999]`.
  - Work that measures perceptual learning makes the threshold trial-dependent `[zhang2019]`.
  - Dynamic IRT models growth as a state-space process `[wang2013]`, `[wilson2016]`.
  - Glicko propagates uncertainty for changing abilities `[glickman1999]`.
  - Adaptive training of a learning animal separates state estimation, learning dynamics and training utility `[bak2016]`.
- **Change.** Cell abilities carry a learning increment per graded opportunity and variance growth with time (§5.6). QUEST+ contributes its finite candidate enumeration and expected-utility selection, not its stationarity.

**R3. Nuisance parameters get "the attention they deserve, no more, no less".**
- **Findings.**
  - Psi-marginal keeps a joint posterior but selects stimuli by information gain on the parameters of interest only `[prins2013]`.
  - Lapses bias threshold and slope estimates `[wichmann2001]`, and freeing a lapse parameter alone does not remove the bias `[prins2012]`.
  - Adaptive designs induce small-sample bias, especially in slope `[kristensen2022]`.
- **Change.**
  - Feature effects, item offsets and outside-signal weights are nuisance for calibration selection (§6.2).
  - Lapse is a fixed small constant.
  - Slope (`a`) is fixed at 1 in v1; per-family slopes are deferred (§16).
  - Calibration of the whole adaptive loop is checked by simulation under the actual selection policy (AD2).

**R4. Practice and probes need different objectives; one POMDP could unify them, later.**
- **Findings.**
  - Bayesian design is expected utility, and different purposes need different utilities `[chaloner1995]`, `[rainforth2024]`.
  - Mutual information between competing models is the right probe objective `[cavagnaro2010]`, `[myung2013]`, `[cavagnaro2011]`, `[houlsby2011]`.
  - EVSI is right when the downstream decisions are known `[strong2015]`.
  - When the target is a prediction rather than all parameters, use targeted designs `[vanlier2012]` and expected predictive information gain `[bickfordsmith2023]`.
  - Teaching as a POMDP unifies diagnosis and instruction under one long-run objective `[rafferty2016]`.
  - A fixed weighted sum of information and band proximity has no principled exchange rate (worker b).
- **Change.**
  - Practice maximizes the posterior probability of being in the band (§6.1).
  - Probes keep hypothesis EIG and VOI stopping with item-offset uncertainty integrated (§6.3).
  - Calibration (when the posterior is too wide to target) maximizes information about the cell's ability, but only among items whose predicted success is acceptable (§6.2).
  - POMDP planning and amortized design policies `[foster2021]`, `[ivanova2021]` are deferred (§16).

**R5. The 70–80% band is a defensible engineering default, not a law.**
- **Findings.**
  - The "85% rule" is derived for gradient-descent learners on binary classification `[wilson2019]`.
  - Math Garden samples items at a mean success probability of .75 `[klinkenberg2011]`.
  - In a geography practice system, targets of 5–50% error showed easier questions better for short-term engagement and harder ones better for long-term engagement and learning `[papousek2016]`; see also `[papousek2015]`. That paper summarizes the Math Garden success-rate experiment as finding the easiest condition best for learning, mediated by the number of tasks solved `[jansen2013]`.
  - 50% is the information-optimal point for measurement, not learning `[eggen2006]`.
  - Desirable difficulties improve durable learning only while the learner can succeed with effort `[bjork2011]`.
- **Change.**
  - Keep the owner's 70–80% band.
  - Define success precisely (§5.3).
  - Evaluate by delayed cold outcomes, not immediate success (§10.4).
  - A band experiment is deferred with a trigger (§16).

**R6. What n=1 identifies.**
- **Findings.**
  - A response identifies an ability–difficulty *relationship*, not two quantities `[chen2021]`.
  - With unrestricted skill, `β' = β + v, θ'_t = θ_t + x_t·v` leaves every success probability unchanged (worker c).
  - Longitudinal designs need overlap and invariant anchors `[fu2016]`, `[le2026]`.
  - When an Elo system selects items adaptively from current ratings and updates item difficulties alongside abilities, the rating variance inflates artificially and the ratings do not converge `[bolsinova2025]`.
- **Change.** §5.8: the honest confound statement, randomized feature overlap, diagnostics, and no per-item difficulty presented as measured.

**R7. Outside estimates: item-side signals are priors; learner-conditioned forecasts are competing experts.**
- **Findings.**
  - Context-free LLM difficulty labels: ρ = 0.06 on 311 deployed questions `[an2026]`.
  - Systematic human–AI misalignment that model scale does not fix `[li2025]`.
  - Moderate ranking but systematic underestimation on 1,031 ENEM items `[brant2026]`.
  - Supervised text models barely beat a constant on USMLE difficulty: best RMSE 0.299 vs 0.311 for the baseline `[yaneva2024]`, `[bulut2024]`; see also the reviews `[benedetto2023]`, `[alkhuzaey2023]`.
  - Simulated solvers do better: up to r = 0.75/0.76/0.82 with NAEP when weaker models role-play classrooms `[acquaye2026]`; ρ up to 0.594 with floor and ceiling effects at the size extremes `[isophys2026]`. Model respondents have narrow ability distributions and are not humans `[liu2025]`, `[heyueya2024]`. Aligned simulators need human data `[scarlatos2025]`, `[hoyl2026]`.
  - History-conditioned LLM forecasting is plausible but unvalidated for this setting `[li2024fskt]`, `[srivastava2021]`, `[halawi2024]`.
  - Verbalized confidence needs recalibration `[tian2023]`, `[xiong2024]`.
  - Robust priors keep a vague component so conflict with history is survivable `[schmidli2014]`.
- **Change (to the agreed direction).**
  - Item-only signals (the LLM label, solver-panel offsets, an item-only LLM forecast, the item's source origin) enter the item-offset prior as a regression whose weights are latent and learned (§7.3).
  - A forecast that already read the learner's history (LLM or Decider given the card) is *not* folded into the item offset. Doing so would count the learner's history twice. It is logged, scored and weighted as a competing expert (§8.4).

**R8. Trust is learned from proper scores, and fit is not policy.**
- **Findings.**
  - Strictly proper scoring rules (log, Brier) separate calibration from sharpness `[gneiting2007]`.
  - Anytime-valid confidence sequences compare sequential forecasters without distributional assumptions `[choe2023]`.
  - Stacking `[yao2018]` and fixed-share expert weighting `[herbster1998]` combine forecasters chronologically.
  - Feature-rich logistic models are competitive with deep KT and should be checked for calibration `[gervet2020]`.
  - Fit statistics are a biased measure of a knowledge tracer's quality as a policy `[rachatasumrit2024]`.
- **Change.** §8.3–8.4, and serving gates and live monitoring that include decision-level checks (band-hit rate, delayed cold success, false certification), not only log loss (§10.4).

**R9. Observations beyond correctness.**
- **Findings.**
  - Partial credit improves knowledge-tracing prediction over binary outcomes `[wang2013pc]`.
  - Math Garden scores accuracy and response time together `[klinkenberg2011]`.
  - Response time with accuracy supports mastery stopping `[sapountzi2021]`.
  - Transparent feature models (LFA/AFM, PFA, DAS3H, LKT) share history across unique items through skill and context features `[cen2006]`, `[pavlik2009]`, `[choffin2019]`, `[pavlik2021]`.
  - Per-item KT parameters `[pardos2011]` need repeated items.
  - Elo is a cheap baseline `[pelanek2016]`.
- **Change.**
  - The outcome is ordinal: fail, partial or help-adjusted success, and unassisted success (§5.3).
  - Rating and timing are separate sub-arms that must earn activation; they are never counted as extra votes (§5.4).
  - KT-IDEM-style per-item parameters are rejected.

**R10. Generate to a specification, audit, then re-forecast.**
- **Findings.**
  - Cognitive design systems and item models ground features in solution processes `[embretson1998]`, `[embretson2001]`, `[gierl2012]`, `[gierl2013]`.
  - Controllable generation can hit observable task demands `[jiao2023]`, `[wang2023skillqg]`, `[bi2024]`, but controlled demand is not personal difficulty (worker e).
  - State-conditioned generation's headline target control was judged by a KT model, not by learners `[srivastava2021]`.
  - LLM-rated item features can fill an LLTM design matrix. In one small study (15 items, 1,452 responses), the best LLM's ratings recovered item difficulty at r = 0.89, against 0.33 for an expert consensus whose agreement was at or below chance on half the features. Ratings still need audits for zero variance and collinearity `[bediwy2026]`.
  - Generated items need human validation `[bhandari2024]`, `[zelikman2023]`.
- **Change.** §7: feature-point contract, an independent feature audit, item-side signals, re-forecast, and certification that uses the more conservative of stamped and audited features.

**R11. Bandits and level-set search lend ideas, not guarantees.**
- **Findings.** ZPDES picks activities by learning progress under expert constraints `[clement2015]`. Thresholding bandits `[locatelli2016]` and level-set estimation `[gotovos2013]` focus sampling near a threshold. All three assume stationary arms, and practice breaks that.
- **Change.** The overlap exploration of §6.1 borrows "sample near the boundary". Learning-progress bandits over families are deferred.

**R12. Pooling across learners comes later, robustly and privately.**
- **Findings.**
  - Hierarchical adaptive design builds priors from earlier participants `[kim2014]`.
  - Explanatory IRT eases person cold start `[park2019]`.
  - Individualized BKT separates student from skill parameters `[yudelson2016]`.
  - N-of-1 Bayesian models aggregate individuals hierarchically `[schmid2022]`.
  - Privacy: release item parameters under differential privacy and keep abilities local `[steiner2018]`; federated IRT with differential privacy `[zhou2025]`, `[hridi2026]`; user-level rather than item-level privacy `[liu2020]`; secure aggregation `[bonawitz2016]`.
- **Change.** §13's staged path, plus requirements on the contribution export.

**R13. Which topics an answer speaks to can be proposed by an expert, then learned (added 2026-10-15).**
- **Findings.**
  - Multidimensional Rasch-type models let one item measure several dimensions at once `[adams1997]`.
  - A diagnostic model's Q-matrix names the attributes each item requires, and it can be estimated from response data `[chen2015q]`. A fully Bayesian estimate can start from a prior built from expert knowledge, check which of the experts' attributes the data support, and find attributes they missed `[culpepper2019]`. Both learn from many examinees.
  - Learning-factor models count a practice opportunity for every skill an item's Q-matrix row names `[cen2006]`, `[pavlik2009]`.
  - An LLM can supply informative priors for a simple, interpretable predictive model; in the reported comparisons these priors reduced error with fewer labels than in-context prediction `[capstick2024]`.
  - Averaging models by their marginal likelihood accounts for model uncertainty, and improved out-of-sample prediction in the examples reviewed `[hoeting1999]`.
  - The learner-field spec rejected LLM relation graphs because propagating noisy facet attributions across a graph "would spread the attribution error" (field F6, D2).
- **Change.** The relatedness model of §5.10.
  - An LLM proposes the prior means of a sparse soft Q-matrix and sparse LO couplings. It reads the vault's content, never learner data.
  - How strongly to trust the proposal is learned per vault, by model averaging over an a-priori grid of hyperparameters.
  - Only vault-level strengths are learnable from one learner (§5.8).
  - Influence is prediction-only, behind sparsity, shrinkage, kill switches and an auto-flag.

**R14. Which active-reading practice helps later retrieval, how much, and how to tell (added 2026-10-15).**
- **Findings.**
  - **Delayed and immediate outcomes disagree.** Testing beat restudying prose on tests 2 days and 1 week later, while restudying won at 5 minutes and raised learners' confidence `[roediger2006]`. As R5 found for difficulty, immediate success misleads about durable learning.
  - **Questions in a text.** Adjunct questions have a strong effect on repeated test questions and a weaker one on related questions. Effect sizes depend, among other things, on the density of the questions and the text's length `[hamaker1986]`.
  - **Worked examples.** Studying worked examples took less time than solving and sped up later problems of the same structure, with fewer errors; both effects were specific to problems identical in structure `[sweller1985]`. Techniques that help inexperienced learners "can lose their effectiveness and even have negative consequences" for more experienced ones, the expertise reversal effect `[kalyuga2003]`. Students who learn well from worked examples generate many self-explanations while studying them `[chi1989]`.
  - **Diminishing returns.** DAS3H, following DASH, counts past practice per time window as `log(1 + count)`, which "induces diminishing returns of practice inside a given time window" `[choffin2019]`.
  - **Confounding.** With time-varying treatments, standard adjustment for confounding is biased when a confounder is itself affected by earlier treatment `[robins2000]`. Reading more because the last answers went badly, which reading then changes, is such a case.
  - **Randomizing at many decision points.** Micro-randomized trials randomize an intervention component at many decision points per person, and identify its proximal causal effects and their time-varying moderation `[klasnja2015]`. The moderated effect has a potential-outcomes definition suited to frequent treatment occasions, occasions when the person is not available, and moderators that past treatment influences `[boruvka2018]`.
  - **Offered is not taken.** When assignment is randomized but uptake is not, the instrumental-variable estimand is the average effect among compliers under stated assumptions, and otherwise only a ratio of intention-to-treat effects `[angrist1996]`.
- **Change.**
  - Four kinds of reading event, each with its own learned, saturating dose curve, exchangeable a priori so the data order them (§5.5, §5.11).
  - Their value is judged by cold outcomes and per minute of learner time, never by immediate success (§10.4).
  - A randomized dose arm offers one more worked example or in-passage question at a section, with exact logged propensities (§5.12). The report keeps the model's curves, which use every observation but are confounded, apart from the randomized offers' estimates, which are unbiased but slow, and labels each recommendation by which supports it (§10.4).

### 4.2 The agreed direction, item by item

| Agreed in conversation | Verdict | What changes |
|---|---|---|
| Explanatory IRT (LLTM): `b = f(features) + offset`, wide-variance offset | **Keep** | Add learned weights on item-side signals inside the offset (R7). Integrate the offset, never estimate it per item (R1, R6). |
| Per-item `b` unidentified at n=1, feature effects identifiable across items; state the confound honestly | **Keep, sharpen** | Identifiable only with feature–time overlap and a fixed scale. Randomized overlap and diagnostics (§5.8). |
| Per-(facet, capability) posterior over the learner's threshold on the feature ladder | **Keep, make dynamic and hierarchical** | Learning increment plus drift (R2). A shared subject level and capability offsets above facet and cell offsets, so a subject's answers inform all of its cells (§5.2, §5.5, §5.9). |
| QUEST+/Psi Bayesian adaptive choice: band for practice, information for calibration | **Keep, refine** | Practice maximizes `P(p ∈ band)`, not distance of a point estimate (R1, R4). Calibration maximizes psi-marginal information only among acceptable items (R3, §6.2). |
| LLM writes a surface *at* the chosen feature point | **Keep** | Add an independent feature audit and a re-forecast before serving (R10). |
| Every forecast logged before the attempt and scored | **Keep** | Receipts per presentation and a DERIVED scorer (§8). |
| Outside estimates (solver panel; LLM forecast *with* the learner card) enter as priors on the item offset | **Split** | Item-only signals → offset prior with learned weights. Forecasts that read the learner's history → competing experts, never offset priors (R7). |
| Observations: correctness, partial credit, cold/primed, hints, time, optional rating; weights learned, never hand-picked | **Keep** | Ordinal outcome. Hints change the outcome category; unknown hint timing is censored, never guessed. Cold vs warm (recent exposure to the LO in any channel) is a learned warmth shift. A primed attempt (the answer was in view) is never an unassisted success: revealed during the presentation, it enters only as "not an unassisted success", its correctness unused; exposed before it, it is excluded. Rating and timing are sub-arms with constrained, learned links that must earn activation (R9). |
| Probes target expected information gain between hypotheses, not the band | **Keep** | Item-offset uncertainty folded into the conditionals. Probe authoring stops using the 45–55% difficulty band (§6.3). |
| Certification "demonstrated up to rung k" from items at or above the rung; exam/pset defines the top rung; reconcile with the capability ledger | **Keep** | Credit is stored by feature point, from the more conservative of stamped and audited features; a rung is a point on one goal's immutable ladder. LO certification keeps its structure, with an entry-level floor and requirements stated as feature points. Full mastery is a separate label (§9). |
| n>1: pooled consented data supply population priors for feature effects and item offsets | **Keep** | Robust mixture priors, held-out learners *and* item families, learner-level privacy (R12, §13). |
| (2026-10-15) Topic relatedness and implication: a learned, vault-specific model with a frontier LLM's semantic prior | **Keep (owner)** | A sparse soft Q-matrix and sparse LO couplings with LLM-proposed prior means; strengths learned per vault; prediction-only; scored against uniform sharing and topic-only (R13, §5.10). |
| (2026-10-15) Reading raises the predicted level | **Keep (owner)** | A learning opportunity with its own learned rate, prediction-only, never evidence (§5.11). |
| (2026-10-15, confirmed) Each discrete reading event kind has its own weight, to learn which active reading best improves cold retrieval and how much of it | **Keep (owner), add randomization** | Four kinds with saturating, learned dose curves; a dose-and-burden analysis on cold outcomes per minute; a randomized dose arm, because observed doses are confounded by struggle (R14, §5.11–5.12, §10.4). |

---

## 5. The model

### 5.1 Units and notation

- **Cell** `c = (f, k)`: a canonical facet `f` and a capability `k ∈ {retrieval, schema_interpretation, procedure_execution, method_selection, coordination}`.
- **Subject** `j`: read as the field harness reads it. An attempt's subject is the one it recorded, the item's first subject (`practice_attempts.subject`, set from `vault.subjects_for_item`, `attempts/attempts.py:3296-3297`, `:3690`), or `default` when there is none (`field/outcomes.py:610`). A candidate's subject is its item's first subject; a feature point's is the first subject of the LO at hand.
- **Item** `i`:
  - capability `k_i`;
  - subject `j_i`;
  - facet weights `w_{i,f}` (normalized `evidence_weights`, falling back to equal weights over `evidence_facets`);
  - a **feature tuple** `x_i` on schema `p1_launch@1`: `complexity` 0–4, `transfer`, `scaffolding`, `span`, `response`, `tools`. The `representation` and `time` dimensions are not modelled in v1;
  - surface group `s_i` (`canonical_projection.surface_group_id`, `:246`);
  - item-side signals `z_i` (§7.3);
  - its LO `L(i)` (`learning_object_id`), and, in the subject view, its soft loadings `Q_{i,g}` onto facets `g` beyond its own (a soft Q-matrix row, §5.10).
- **LO** `L`: its facets `F(L)`; in the subject view, its coupled LOs `N(L)` with proposed strengths `C_{LM}` (§5.10).
- **Reading opportunity** `o`: an LO-scoped learning opportunity outside practice, of a kind `κ ∈ {reading, reader_tutor_exchange, worked_example, in_passage_question}` (`reading` collates a section read and a passage viewed), with a dose `D_{o,f} ∈ [0, 1]` for each facet it bears on. `n_{κ,f}` is the dose of kind `κ` that facet `f` has received since the last graded attempt on it (§5.11).
- **Attempt** `t` on item `i` at time `τ_t`:
  - correctness `y_t ∈ [0,1]`;
  - `hints_used`, and the help timing `h_t ∈ {none, before_work, after_work, unknown}` (§5.3);
  - whether the answer was revealed during the presentation (`primed`, §5.3);
  - warmth `w_t ∈ [0,1]`: recent exposure to the item's LO in any logged channel (§5.4);
  - `latency_seconds`;
  - optional rating `r_t ∈ {easy, about_right, hard}` (new, §12).

### 5.2 State

A Gaussian `N(μ, Σ)` (in the subject view, one per hyperparameter point `ξ`, mixed by a learned posterior; §5.10) over:
- **Cell abilities**, through an explicit hierarchy (owner direction 2026-10-14, as in field's `lo_general` and `lo_general+capability`): for an item or point of subject `j`, the ability on cell `(f, k)` is `θ_{f,k} = θ_{G,j} + θ_f + ψ_{j,k} + e_{f,k}`.
  - `θ_{G,j}`: the subject's **general level**, shared by every facet and capability of the subject (field's `θ_general`, one per subject).
  - `θ_f`: the facet's offset from that level, shared by the facet's capabilities.
  - `ψ_{j,k}`: a **capability offset** shared across the subject's facets (field's `δ_cap`); `ψ_{j,retrieval} ≡ 0` anchors the scale.
  - `e_{f,k}`: the cell's own offset.
  - So every answer in a subject informs `θ_{G,j}`, its capability's `ψ_{j,k}` and the feature effects `β`; every answer on a facet informs `θ_f`; only answers on the cell inform `e_{f,k}`. Each offset refines as its own evidence arrives. What the hierarchy can and cannot identify is in §5.8, and how much it speeds a usable estimate in §5.9.
  - State dimensions are created lazily, when a subject, facet or cell is first observed or first asked about. In the subject view, a new facet's topic-specific coordinates (`θ_f` and its `e_{f,k}`) are created coupled to the facets of its LO's coupled LOs (§5.10).
- **Learned relatedness (subject view only, §5.10).** Two sparse sets of extra shared terms:
  - **soft loadings:** each item's facet weights extend to a few facets beyond its own, so an answer informs, and is predicted by, the topics it implies knowledge of (§5.4);
  - **couplings:** the topic-specific parts of a few related LOs' facets are correlated a priori, so evidence and learning on one topic move its related topics.

  Their prior means come from an LLM's proposal for the vault; their strengths are the hyperparameters below.
- **Hyperparameters** `ξ = (σ_G², χ_C, χ_Q)`, per vault, in the subject view: the share of the cold-start variance in the subject level (how much is shared versus topic-specific), the coupling strength and the implication strength. They are latent: the subject view runs one filter per point of an a-priori grid and mixes them by a posterior learned from this vault's answers (§5.10). The LO view fixes `σ_G² = 1.5` and has no loadings or couplings.
- **Shared feature effects** `β`: cumulative increments per ordinal level of each feature dimension, plus contrasts for `response` and `tools`. The reference tuple `x_ref` (the default trajectory's `recall` waypoint: complexity 0, `same_context`, `short_constructed`, `cue`, `atomic`, `closed_book`) has demand 0, which anchors the location.
- **Item-signal weights** `α` (§7.3).
- **Learning increments:** `γ` per practice opportunity, and, in the subject view, each reading kind's dose-curve coefficients `γ_read[κ, m]`, a shared curve plus a deviation per kind (§5.11). **Warmth shift** `ζ`.
- **Sub-arm parameters**, present only when that sub-arm is on (§5.4), in unconstrained coordinates: rating `(c_1, d̃, ρ̃)`; timing `(ν, ω̃)`.

The item offset residual `ε_i` is *not* state. It is integrated out of every likelihood and prediction (R1).

### 5.3 Outcome categories (help-adjusted, ordinal)

One definition of success is shared with the certification cold probe (`certification_cold_probe.py:197`, success at correctness ≥ 0.8) and the partial threshold with the ledger (`canonical_projection.py:56`, `FAILURE_THRESHOLD = 0.40`):

**Help timing `h_t`.** Ordinary hints keep only their total today (§3.1), so timing is a per-attempt label with an explicit "unknown". A **help-equivalent question** is a practice-context tutor question during the presentation that field reads as help: `hint_equivalent` set, or a help type (`prerequisite`, `mechanism`, `clarification`, `strategy`) (`field/signals.py:217-221`, `:256-259`).
- `none`: `hints_used = 0` and no help-equivalent question;
- `before_work`: some help was **logged** before any work. That is a help-equivalent question logged with `attempt_progress = no_draft` or `seconds_into_attempt = 0` (field's own rule, `field/signals.py:351-359`), or, from AD1 on, ordinary hints with `first_hint_progress = no_draft` (§11.2);
- `after_work`: every source of help has its earliest event logged with work begun: `first_hint_progress = draft_started` when ordinary hints were used, and `attempt_progress = draft_started` on every help-equivalent question;
- `unknown`: anything else. That includes every ordinary hint recorded before AD1, a question with no progress marker, and a client that does not send `first_hint_progress`. **Missing timing is never read as "after work began".**

| Category `Y` | Condition |
|---|---|
| 2 **unassisted success** | `y ≥ 0.8`, `h_t = none`, not primed |
| 1 **partial, or success with help after work began** | `0.40 ≤ y < 0.8` with `h_t = none`, not primed; or `y ≥ 0.8` with `h_t = after_work`, not primed |
| 0 **fail** | not primed, and: `y < 0.40` with `h_t = none`; or `y < 0.8` with any help; or `h_t = before_work` (field §3.1's early-help cap); or an empty "I'm stuck" |
| `{0, 1}` **censored: not an unassisted success** | `y ≥ 0.8` with `h_t = unknown`, not primed; or any primed attempt, whatever its `y` and `h_t` |

Primed takes precedence over every other row, so each attempt has exactly one category.

**The forecast event and what counts as observed.** The event used everywhere (band, receipts, scoring and the update) is `Y = 2` on a first presentation that ends in a submitted, graded attempt. A future hint or reveal is never a forecast covariate.
- **The binary event is always observed** on a submitted attempt. Any help, or an answer revealed during the presentation, makes it 0, whatever the timing.
- **Censored categories** enter the update through `P(Y ≤ 1 | η) = 1 − P(Y ≥ 2 | η)`, and the ranked probability score skips them (§8.3). So training and scoring read the same event, and the model is never trained only on the presentations where the learner did not ask for help.
- **Primed attempts.** `primed` is set for a source-review retry and also, by `auto_primed_draft`, for any submission whose summed reveal amount on the item since its last attempt reaches `AUTO_PRIME_REVEAL_THRESHOLD = 0.35`, first attempts included (`attempts/attempts.py:149`, `:1937-1990`). AD splits them by when that sum was reached, using the same sum:
  - **Exposed before the presentation:** the item's reveal sum over `reveal_events` rows created before `served_at` already reaches the threshold. This is not a fresh first presentation. It is known at serve time, so the item is never in a draw's support (§6.1). A planned slot that holds it is served only as the predecessor serves it, with no draw (§6.1, step 0), and any receipt for it carries `pre_exposed = true`. Such presentations are excluded from the update and from scoring alike.
  - **Revealed during the presentation:** any other primed attempt with a bound presentation (the sum crossed the threshold after `served_at`, or the retry flow set the flag). The event did not occur. The attempt enters the update as the censored factor. Its correctness is never used, so revealed correctness is never ability evidence; only the fact that the learner needed the answer is.
  - **With no bound presentation,** the reveal's timing relative to serving is unknown, and the attempt is excluded from both.
- **Skipped or abandoned presentations** (no submission) have no outcome. They are right-censored in scoring and absent from training alike, so the estimand is explicitly "unassisted success, given an answer is submitted". The AD report gives the skip rate per forecast decile, so skips that concentrate where predictions are low are visible.
- Cold vs warm *without* the answer in view enters through the warmth covariate `w_t` (§5.4).

### 5.4 Likelihood

The linear predictor for attempt `t` on item `i`:

```
η_t = a · ( Σ_f w̃_{i,f} θ_{f,k_i}  −  β·φ(x_i)  −  α·z_i  −  ε_i )  +  ζ · w_t   =   ũ_tᵀ s  −  a·ε_i
ε_i ~ N(0, τ0²)        a = 1 (fixed in v1)
```

- `φ(x)` is the cumulative dummy coding of `x` relative to `x_ref`.
- **Extended facet weights `w̃` (the soft Q-matrix row).** In the LO view, and in the subject view at `χ_Q = 0`, `w̃_{i,f} = w_{i,f}`. In the subject view the item's proposed loadings `Q_{i,g}` (§5.10) take a share of its weight: `w̃_{i,f} = (1 − χ_Q·Q_i⁺)·w_{i,f}` on its own facets and `w̃_{i,g} = χ_Q·Q_{i,g}` on each loaded facet `g`, with `Q_i⁺ = Σ_g Q_{i,g} ≤ 1`. The loadings, like the item's features and signals, are the ones frozen at its serve (§7.5).
- `θ_{f,k_i}` is the §5.2 sum at the item's subject `j_i`, for every facet with `w̃_{i,f} > 0`. Because the extended weights still sum to 1, `θ_{G,j_i}` and `ψ_{j_i,k_i}` enter with coefficient `a`, which keeps the scale anchored.
- **The projection `ũ_t`.** Every state coordinate enters `η_t` linearly, warmth included: `ũ_t` has `a·w̃_{i,f}` on the cell abilities (so `a` on the subject level and the capability offset, `a·w̃_{i,f}` on each facet and cell offset), `−a·φ(x_i)` on `β`, `−a·z_i` on `α` and `w_t` on `ζ`. So `ζ`'s uncertainty and its covariances are carried through prediction and update like every other coordinate. Within one hyperparameter point `ξ` the loadings' coefficients are known numbers, so the projection stays linear (§5.10).
- **Warmth.** `w_t = exp(−Δh_t / h_w)`, with `h_w = 6` hours (a fixed, versioned constant swept by the harness), where `Δh_t` is the number of hours since the learner's last exposure to the item's LO in any logged channel. The channels are: an attempt on another item of the LO, a `reveal_events` row for the LO (`migrations/154_reveal_ledger.sql`), and reading and tutor events, read from the reading-opportunity receipt of §5.11 (router §15.2's covariate view, once built, reads the same). Warmth is the short-lived lift of recent exposure; the lasting part of reading is the learning increment of §5.11, learned separately. `w_t = 0` with no prior exposure. `w_t` is known when the item is served, so it is a valid forecast covariate. Its weight `ζ` is learned (router §15.2: "coldness is learned, not hard-coded").

Graded response, with guess floor `g_i = guess_floor_for_item` (`blueprint_projection.py:164`) and lapse `λ`:

```
P(Y ≥ 2 | η) = g_i + (1 − g_i − λ) · σ(η)
P(Y ≥ 1 | η) = g_i + (1 − g_i − λ) · σ(η + κ)
```

**Sub-arm likelihoods.** Each is a separate harness arm and is off in the base arm (§10.4).
- **`+rating`.** Ordinal logistic on the same predictor with its own link:
  - `P(r ≥ about_right) = σ(ρ·η − c_1)`;
  - `P(r = easy) = σ(ρ·η − c_2)`;
  - `ρ = exp(ρ̃)` and `c_2 = c_1 + exp(d̃)`, so `ρ > 0` and `c_1 < c_2` hold for every value of the latent coordinates `(c_1, d̃, ρ̃)`, and the category probabilities are always valid.
  - The rating is tapped after answering and before feedback (§12). It shares information with the outcome, so the arm earns activation only if it beats the base arm on held-out log loss. It is one factor of the attempt's joint likelihood (§5.6), never a free extra vote.
- **`+timing`.** For unassisted successes only, `log(ℓ_t / m̂_i) ~ N(ν − ω·η, σ_ℓ²)`.
  - `ω = exp(ω̃)`, with latent `(ν, ω̃)` and fixed `σ_ℓ`.
  - `ℓ_t` is `latency_seconds`. `m̂_i` is the plan estimator's `answer_minutes(item) × 60` (`daily_plan/estimates.py:1-18`), computed from latencies strictly before this attempt, with feedback dwell excluded.
  - Coverage is low today (18% of attempts in §3.3); the arm abstains where latency is missing.

All factors of one attempt (the outcome, and the rating and timing where present) share the same `η`, and so the same item residual `ε_i`. They form **one joint factor**, integrated over `ε_i` once (§5.6).

### 5.5 Priors (`ad_priors_v1`, a priori, versioned; field F5)

| Parameter | Prior | Basis |
|---|---|---|
| `θ_{G,j}` (subject level) | `N(0, σ_G²)` at the subject's creation. The subject view learns `σ_G² ∈ {0.75, 1.5, 2.25}` per vault (`ad_hyper_v1`, below); the LO view fixes `σ_G² = 1.5` | A share of the cold-start variance, so a subject's answers inform every cell of it. The three values are field's `lo_general` (0.75, with 2.25 per LO), half (1.5) and three quarters (2.25). The split used to be an a-priori assumption compared across harness arms; it is now learned from how far this vault's facets sit from their subject level (§5.8), and forecasts on never-seen items still test it (§5.9, D17) |
| `θ_f` (facet offset) | `N(0, (3.0 − σ_G²)/2)` at the facet's creation: 0.75 at `σ_G² = 1.5`. In the subject view a coupled facet's offset is created by regression on its coupled facets (§5.10), with this total variance | With the cell offset, the part of the prior that is the facet's and cell's own |
| **Claims** (re-anchoring, on the coordinates above) | Self-assessment claims **re-anchor a mean** at the claim's `created_at`, in the same ordered stream as attempts. The init wizard's global claim (`learner/learner_profile.py:61-80`, applied to every facet) re-anchors `θ_{G,j}`'s mean to `logit(claimed_level)`, for each subject with no eligible AD observation yet. A tutor gap declaration (`tutor/promotions.py:772-796`, applied to the facets or LO in scope) re-anchors `θ_f`'s mean so that the facet level `θ_{G,j} + θ_f` has mean `logit(claimed_level)`, for each facet in scope with no eligible observation yet. The re-anchored coordinate's variance is set to `max(current, its prior variance)`, so while the subject has no evidence every cell keeps its cold-start variance of 3.0, above today's `claim_prior_min_variance = 2.0` (`learner/mastery.py:172-201`; `config/schema.py:199-200`). Claims made after the first eligible observation of their scope are not read by AD. **Excluded:** claims written by easier/harder requests (`rung_variant_request`, `content/authoring/rung_variants.py:416-432`) and by too-easy/too-hard reports (`learner_report`, `content/authoring/item_authoring.py:317-365`), which AD does not read in v1 (D8). The EKF posterior is never used | A claim moves a mean and never shrinks a variance. A facet's variance can be lower than at its creation only because the subject level has learned from answers, never because of the claim. Applying claims at their own time means a later claim never seeds earlier observations. Claims are mutable rows, so a replaced claim's earlier version is not replayed (stated in the AD report) |
| `ψ_{j,k}` | schema_interpretation `N(−0.3, 0.5²)`, procedure_execution `N(−0.5, 0.5²)`, method_selection `N(−0.8, 0.5²)`, coordination `N(−1.2, 0.5²)`; retrieval ≡ 0; one set per subject | Ordering from capability dominance (measurement spec B1); magnitudes a priori. Field's `lo_general+capability` uses `N(0, 0.5²)`; the harness sweeps both |
| `e_{f,k}` | `N(0, (3.0 − σ_G²)/2)`: 0.75 at `σ_G² = 1.5`. Coupled like `θ_f` in the subject view (§5.10) | A fresh retrieval cell totals `σ_G²` + 2 × `(3.0 − σ_G²)/2` = 3.0 at every split, the cold-start variance (`schema.py` `cold_start_prior_logit_variance`); other capabilities add `ψ`'s 0.25 |
| **Hyperparameters** `ξ = (σ_G², χ_C, χ_Q)` (subject view; `ad_hyper_v1`) | Uniform over the grid `σ_G² ∈ {0.75, 1.5, 2.25}` × `χ_C ∈ {0, 0.25, 0.5, 0.75}` × `χ_Q ∈ {0, 0.25, 0.5}`: 36 points, each with prior weight 1/36 | Wide on purpose: zero coupling and zero implication carry a quarter and a third of the prior mass, so the learner's data can switch the proposal off (§5.10). The caps keep at least `1 − 0.75² ≈ 44%` of a topic's own variance and half of an item's weight on its own facets |
| `γ_read[κ, m]`, the dose-curve coefficients of each reading kind (subject view; §5.11), hierarchical: `γ_read[κ, m] = γ̄_m + δ_{κ,m}`, one set per vault | Shared curve: `γ̄_1 ~ N(0.10, 0.07²)` on the fast scale, `γ̄_2 ~ N(0.20, 0.10²)` on the slow scale. Each kind's deviation: `δ_{κ,1} ~ N(0, 0.07²)`, `δ_{κ,2} ~ N(0, 0.10²)`, for each of `reading`, `reader_tutor_exchange`, `worked_example`, `in_passage_question`. So each kind's coefficients have prior sd 0.10 and 0.14 | A priori, the first event of a kind raises the facet by about 0.11 logits (half a practice opportunity's `γ`, with sd 0.07), and a window's full saturating effect is about 0.3 (sd 0.17). The kinds are exchangeable a priori: the research orders them (testing beats restudy on delayed tests `[roediger2006]`; adjunct questions help `[hamaker1986]`; worked examples help novices and can reverse with expertise `[sweller1985]`, `[kalyuga2003]`) but gives no magnitude that transfers to this learner, so this vault's answers order them. The shared curve lets a rarely seen kind borrow from the others. Wide enough that a kind that does not predict a rise shrinks toward 0 |
| `λ_matched`, `λ_missed`, the self-check verdict term (subject view; §5.11, D22), one pair per vault | `N(0, 0.3²)` each, independent | Centred on 0 so an unlearned term changes nothing (D20's prediction exactly); the scale lets a vault learn a shift of a fraction of a logit per judged question. No hand-set asymmetry: the learner's data decides how much a *matches* and a *miss* are worth |
| `β` complexity, each step 0→1→2→3→4 | `N(0.5, 0.3²)` | Monotone ordering from the default trajectory; ~0.5 logit ≈ 10 points of success near 75% |
| `β` transfer, each step same_context→near→far→novel_combination | `N(0.5, 0.3²)` | Same |
| `β` scaffolding: cue→none `+`, cue→partial `−`, partial→worked `−` | `N(0.5, 0.3²)`, `N(−0.5, 0.3²)`, `N(−0.5, 0.3²)` | Less scaffolding is harder (`depth_rungs.py:41`) |
| `β` span, each step atomic→single_step→multi_step→whole_task | `N(0.4, 0.3²)` | Same |
| `β` response vs short_constructed | recognize `N(−0.7, 0.4²)`, long_constructed `N(0.3, 0.3²)`, structured_steps `N(0.3, 0.3²)`, performance `N(0.6, 0.4²)` | Selected response is easier and less informative (`depth_rungs.py:89-99`) |
| `β` tools: open_book/references vs closed_book | `N(−0.4, 0.3²)` | |
| `α_llm` (LLM label) | `N(0.2, 0.2²)` | Low prior trust (R7), above zero given §3.3 |
| `α_panel` (solver-panel relative offset) | `N(0.5, 0.3²)` | Moderate trust (R7) |
| `α_v1` (item-only LLM forecast, as a difficulty: `−logit p`) | `N(0.2, 0.2²)` | Low prior trust; learned |
| `α_origin` (generated vs canonical exercise) | `N(0, 0.5²)` | Neutral. This is the quantitative "surface gap" of router §15.5 |
| `γ` learning increment per graded first-surface opportunity in a cell | `N(0.2, 0.1²)` | Field `lo_general+practice` γ = 0.2 |
| `ζ` warmth shift (at `w_t = 1`) | `N(1.0, 0.5²)` | Half of today's `priming_b_offset` (2.0, an immediate re-read). Recent exposure in the session is weaker than a re-read |
| `+rating`: `ρ̃`, `c_1`, `d̃` | `N(log 0.5, 0.5²)`, `N(−1.0, 0.5²)`, `N(log 2.5, 0.3²)` | Rating is a noisy reading of the margin. Prior medians `ρ = 0.5`, `c_2 − c_1 = 2.5` |
| `+timing`: `ν`, `ω̃` | `N(0, 0.3²)`, `N(log 0.15, 0.6²)` | Faster when the margin is larger `[klinkenberg2011]`. Prior median `ω = 0.15` |
| **Fixed constants** (versioned, swept by the harness) | `a = 1`; `λ = 0.02`; `κ = 1.5`; `τ0 = 1.0`; `σ_ℓ = 0.6`; warmth decay `h_w = 6` h; drift `σ²_drift = 0.01`/day (`mastery.sigma2_drift`); relatedness sparsity: at most 3 loadings per item and 3 coupled LOs per LO (§5.10); reading dose-curve scales `h_1 = 1`, `h_2 = 4` events (§5.11) | Not learnable at n=1 without misleading precision (R3, R6). The sparsity caps are structural safeguards, not weights. The two dose scales fix a basis, not a shape: the learned coefficients on them set each kind's curve |

Cross-dimension correlations in the prior are zero except as implied by the hierarchy and, in the subject view, by the couplings (§5.10).

### 5.6 Update rule (deterministic assumed-density filtering)

Rows are processed in fixed order (`created_at`, `attempt_id`) in float64. Rebuild is byte-identical (G1 of field §7.1).

**Two views.** The same update runs over two sets of rows:
- The **subject view** reads every eligible row and every reading opportunity (§5.11), with the learned relatedness of §5.10. It runs one filter per hyperparameter point `ξ` of the `ad_hyper_v1` grid and mixes them by their learned weights (step 4). With `promoted_predictor` on, the default from the AD2/AD3 successor's tag, it is the view every live AD decision reads (§6.1, D3).
- The **LO view** of an LO `L` reads only the eligible rows on `L`'s items (each item has one `learning_object_id`), from `ad_priors_v1` at the fixed split `σ_G² = 1.5`, with no loadings, couplings or reading opportunities. Its shared terms (subject level, capability offsets, feature effects, `α`, `γ`, `ζ`) are learned from `L`'s answers alone, so its subject level acts as `L`'s level. It is the topic-only comparator the harness scores, and, with `promoted_predictor` off, the view every live AD decision about `L` reads, so no other LO's evidence steers it (A6).
- Both views are DERIVED, keyed by view in `ad_state` and `ad_attempt_trace` (§11.2), and rebuilt byte-identically.

Steps 1–6 run in each filter. Reading opportunities and the hyperparameter weights are subject-view steps.

1. **Eligibility.** A row updates the state only if it is all of the following:
   - a graded attempt of type `independent_attempt`, `open_text`, `diagnostic_probe` or `exam_attempt` (on reserved pool items, which are ordinary items);
   - the **first** graded attempt on its surface group `s_i` (repeat attempts on the same surface are FSRS's job, D10);
   - not held for review (`held_grades`);
   - not quarantined, unassessable or zero-mass;
   - from the current grading epoch;
   - with usable inputs: its frozen serve inputs, or a historical resolution whose status is not `excluded` (§7.5).

   Excluded: `self_report` rows, so that the rung-variant evidence package is not read twice (D8); presentations exposed before serving, and revealed attempts with no bound presentation (§5.3); `teach_back` in v1 (§16); and any held-out exam unit (A8). A primed attempt revealed *during* its presentation is not excluded: it enters as the censored factor (§5.3).
2. **Claims and reading.** An allowlisted claim (§5.5) whose `created_at` falls before this row re-anchors its mean first (`θ_{G,j}` for the global claim, `θ_f` for a gap declaration), if its scope has no eligible observation yet (mean-only; the variance never falls below the coordinate's prior). In the subject view, every reading opportunity ordered before this row (§5.11) applies its transition first.
3. **Propagate.** For each touched cell, add `σ²_drift · Δdays` (since that cell's last update) to `Var(e_{f,k})`. There is no mean decay; forgetting stays with FSRS (field §4.3, "Time").
4. **One joint factor per attempt.**
   - **Dependence.** The attempt's likelihood (the outcome category, and, where the active arm has them, the rating and the timing) depends on the state only through a low-dimensional vector `v_t`. It holds the linear projection `ũ_tᵀs` that forms `η_t` (warmth included, §5.4), plus the sub-arm link coordinates (`c_1, d̃, ρ̃`; `ν, ω̃`). That is at most six coordinates, and exactly one in the base arm.
   - **The shared residual.** The item residual `ε_i` enters every factor through the same `η_t`, so it is integrated **once**, inside the joint factor: `Z_t = E_{v_t, ε_i}[ L_Y(η_t) · L_r(η_t) · L_ℓ(η_t) ]`, with `η_t = ũ_tᵀs − a·ε_i`.
   - **Censored categories.** For a censored attempt (§5.3), `L_Y = P(Y ≤ 1 | η_t)`, and the rating and timing factors are omitted: help or a reveal came between the learner and the answer.
   - **Inputs.** `ũ_t` is built from the attempt's frozen features and signals (§7.5), never from the item as it stands at rebuild time.
   - **Quadrature.** `Z_t` and the posterior mean and covariance of `v_t` come from tensor Gauss–Hermite quadrature: 32 nodes on the `η` coordinate, with the `ε` variance `a²·τ0²` folded into it, and 5 nodes on each link coordinate. In the base arm this is the one-dimensional assumed-density update TrueSkill uses `[herbrich2006]`.
   - **Back-projection.** The full state is updated by linear-Gaussian back-projection from the moment-matched `v_t`: the rest of the state is regressed on `v_t` through `Σ`. This is the standard assumed-density-filter projection for a factor on a linear subspace.
   - **Why it matters.** Unlike today's EKF (`mastery.py:450+`), which linearizes at the prior mean, this is exact moment matching of a non-Gaussian likelihood, which matters at the ceiling. Correlated observations of one attempt enter once.
   - **Hyperparameter weights (subject view).** `Z_t(ξ)` is the attempt's marginal likelihood under the filter at point `ξ`, which the quadrature already computes. Each point's weight updates as `W_t(ξ) ∝ W_{t−1}(ξ) · Z_t(ξ)`, from the uniform prior of `ad_hyper_v1`. This is the Bayesian model average over the grid `[hoeting1999]`: exact for the grid, deterministic and replayable.
5. **Learn.** After the update, apply the learning transition `e_{f,k} ← e_{f,k} + w̃_{i,f}·γ` for each touched cell, its own and, in the subject view, its loaded ones (a practice opportunity for every topic the item draws on, as learning-factor models count it `[cen2006]`). In the subject view the increment also transfers along couplings: each coupled cell `(g, k)` that exists gains `corr₀(e_{f,k}, e_{g,k})·w̃_{i,f}·γ`, where `corr₀` is the a-priori correlation the coupling set (§5.10). Both are linear in the joint state, so the covariance propagates exactly. This is how the estimate tracks a moving threshold (§5.9).
   - **Reading windows.** In the subject view, every graded attempt other than `self_report` on an item that weighs on a facet (`w_{i,f} > 0`), eligible or not, closes that facet's reading-dose windows: each `n_{κ,f}` returns to 0 (§5.11). Ineligible rows only close windows; they update nothing else.
   - **One event, one increment.** An attempt that is itself an in-passage question (§5.11; its serving origin says so, A7) takes that kind's next dose-curve increment in place of `γ`, never both. Its outcome enters the update once, as any eligible attempt's does.
6. **Record.** The per-attempt trace (prior and posterior moments of `η`, predicted category probabilities, information gained, and, in the subject view, each point's `Z_t(ξ)` and weight) is written to the DERIVED trace (§11.2).

### 5.7 Predictive quantities

For cell `c` and a candidate feature point `x` (a not-yet-written item; `z = 0`), in the view the decision reads (§5.6, §6.1):
- **`p̄(x)`**: posterior predictive unassisted success, `E[g + (1 − g − λ)·σ(η)]` with `η ~ N(m(x), v(x))`. This is the family expected response `[sinharay2003]`. For a specific pool item, its own `z_i` enters `m`.
- **`p_θ(x)`**: the expected success *given* the epistemic state. The item residual `ε` is integrated and the state is held fixed. It is a monotone function `F_x` of the epistemic part `η_e = ũᵀs ~ N(m(x), v_e(x))`, `v_e = ũᵀΣũ`. The warmth at serve time sits inside `ũ` (§5.4).
- **`P_band(x)`** `= P(p_θ(x) ∈ [0.70, 0.80]) = Φ((F_x⁻¹(0.80) − m)/√v_e) − Φ((F_x⁻¹(0.70) − m)/√v_e)`. It is exact, because `F_x` is monotone.
  - `F_x` ranges over `(g, 1 − λ)`. A band edge outside that range makes its term 0 (below) or 1 (above); for example, a selected-response item with a guess floor above 0.70 can only reach the band from its lower edge.
  - The warmth `w_t` at the moment of serving enters through `ũ`, in both `m(x)` and `v_e(x)`.
- **`I_c(x)`**: psi-marginal information `I(θ_c; Y | x)` about the cell ability only, with every other state component treated as nuisance `[prins2013]`. Computed by two-level quadrature (outer over `θ_c`, inner over the conditional remainder plus `ε`).
- **`H(x)`**: hypothesis-conditional category probabilities for probes (§6.3).

**In the subject view** each quantity is the mixture over the hyperparameter points, weighted by `W(ξ)` (§5.6): `p̄` and `P_band` are exact weighted sums of the per-point values (a probability under a mixture is the weighted sum of the component probabilities), so propensities built from them stay exact; `I_c` treats `ξ` as one more nuisance, an outer sum over the grid. A not-yet-written item has no loadings, so a feature point's weights are the cell's own; a pool item uses its frozen loadings.

### 5.8 Identifiability: what one learner's history can and cannot say

**Can be identified** (given the scale fixed by `a = 1`, `ψ_{j,retrieval} = 0` and `x_ref`, and the location split fixed by the zero prior means of the facet and cell offsets):
- the ability on each observed cell (the §5.2 sum), and contrasts between cells;
- the subject level, as the part the observed facets share. It sharpens as more facets have answers; with one or two facets it stays close to its prior;
- each capability offset `ψ_{j,k}`, from facets observed both at `k` and at retrieval;
- the feature effects `β`, but only along directions of the design that vary independently: of each other, of the item-side signals, and of time within a cell. If two feature columns always move together (the default trajectory raises `complexity` and `transfer` in the same steps, `depth_rungs.py:101-122`), only their sum is identified, however well randomized the timing;
- the weights `α` on item-side signals, which are a regression across many items, subject to the same rank condition against the features;
- the learning increment `γ`, to the extent the same feature points recur;
- the vault-level hyperparameters of §5.10, each one number learned across many topics or items, under the assumption that the vault's topics are exchangeable given the proposal: the split `σ_G²`, from how far this vault's observed facets sit from their subject level; the coupling strength `χ_C`, from whether the facets the proposal couples sit closer together than the rest; the implication strength `χ_Q`, from whether items' outcomes follow the levels of the facets they load on. Each sharpens only as many topics have answers;
- each reading kind's dose curve (§5.11), from the change in success after reading, to the extent that reading is followed by answers on the same LO and that each kind's dose varies independently of the other kinds' and of struggle. A section read and the worked examples in it arrive together, and a learner reads more when struggling, so the randomized offers of §5.12 supply the independent variation.

**Cannot be identified:**
- the offset of a one-off item (its posterior is the prior plus one response's worth, and it is never shown or used as "measured" difficulty);
- between-learner variance;
- whether `β` is universal or this learner's;
- growth versus feature effects when features rise with time. If `x_t` is a function of `t`, then `(β + v, θ_t + x_t·v)` fits every observation equally well (R6);
- how an observed cell's ability divides between the subject level, the facet offset and the cell offset, beyond the sharing above. The data see sums, so that division is the prior's;
- how far a particular never-seen cell sits from what the shared terms and its couplings predict. The split and the coupling strength are learned for the vault as a whole (above), but a cell's own offset shows only in its own answers. Forecasts on never-seen items, field's first-attempt split, test the whole prediction (§8.3, D17). The subject view steers live decisions without waiting for that test (D3); the monitoring of §10.4 reports it and flags the subject view when it does worse than topic-only or uniform sharing;
- the strength of any one coupling or loading. One learner has one level per topic, so a single pair carries almost no information about its own correlation. Each pair and each loading keeps the proposal's value times the learned vault strength; a wrong pair is corrected, for prediction, only by its topic's own answers. Learning pairs one by one needs pooled data (§13);
- whether reading causes the rise it predicts, from observed reading alone. The learner chooses what to read and how much, often more when struggling, and struggle shows in later answers too `[robins2000]`. So the fitted curves are the rise in success that follows this learner's reading, not the causal effect of reading. Only the randomized offers of §5.12 identify a causal effect: that of *offering* one more worked example or in-passage question, and, through the offer, the effect among the occasions where the learner takes it, under the assumption that an offer works only by being taken `[angrist1996]`.

**The honest statement, shown in the AD report and in the glass-box view (not in the default UI).** "The estimated rise in your skill and the estimated hardness of each kind of question are conditional on two assumptions: that the hardness of a question kind is stable over time, and that generated questions really have the features they were asked for. Your answers alone cannot separate a rise in skill from questions at a level being easier than assumed. On something you have not practised yet, the first estimate leans on your other answers, on how related LearnLoop judges the topics to be, and on what you have read; your first answers there correct it."

**Design remedies:**
1. Randomized overlap: 10% of practice choices sample uniformly among items with acceptable predicted success, so feature level is not a function of time (§6.1). Commission candidates include one-step neighbours on a *single* dimension, so feature columns are varied one at a time and stop moving together.
2. Feature audits, so "the features it was asked for" is checked (§7.2).
3. The source-origin weight `α_origin`, so generated-vs-canonical differences are estimated, not absorbed into skill.

**Diagnostics** (AD report, every run):
- per-dimension correlation between served feature level and time, labelling `β` estimates "confounded" when `|r| > 0.6`;
- aliased directions: the eigenvectors of the data's contribution to the posterior precision of `(β, α)` with eigenvalue below 5% of the prior precision. Coefficients along them are labelled "prior-dependent";
- posterior contraction of each `β` relative to its prior;
- prior sensitivity: rerun with each prior mean shifted ±1 sd and report how many band decisions change;
- simulation recovery (AD2) under the actual policy versus a monotone policy;
- the hyperparameter posterior `W(ξ)` (§5.10), with each margin's contraction from its uniform prior, and each reading kind's dose curve with its contraction from the prior (§5.11).

### 5.9 How fast the estimate becomes usable (owner target, 2026-10-14)

**The target (D15).** A usable estimate within 10–15 answered questions per subject, not per cell. "Usable" means the practice draw can target the band: band mode engages (`max P_band ≥ calibrate_below`, §6.1 step 2; 0.35 as registered, 0.25 since the owner decision of 2026-10-19, below). On the model's scale that needs a posterior sd of about 0.74 logits at the served point, about ±11 points of success around 75%.

**The information arithmetic.**
- **At `a = 1`, with no item residual.** One answer near the threshold carries `p(1 − p)` units of Fisher information: about 0.19 at 75% and 0.25 at 50%. From a prior variance of about 3.0 logits², 12 well-chosen answers leave about ±0.6 logits, about ±12 points around 75%; 30 leave about ±0.4 logits, about ±7 points.
- **On the model's own scale.** The integrated item residual (`τ0 = 1`) and the lapse lower the information per answer to about 0.12 near 75% and 0.16 near 55% (where calibrate mode serves). They also flatten the success curve by the same factor, so the error *in points* barely moves: 12 answers leave ±0.67–0.75 logits, ±10–11 points; 30 leave ±0.44–0.50, ±7–8 points. In points this is close to the binomial limit `√(p(1 − p)/n)`, whatever the constants.
- **So band mode engages after about 10–13 answers that inform the quantity being served.** Calibrate mode's more informative items (§6.2) shorten that.

**"Per subject" needs sharing, and sharing has a limit.**
- Answers spread over a subject's cells inform a given cell only through what the cells share. §5.2 makes the sharing explicit: every answer in the subject informs `θ_{G,j}`, its capability's `ψ_{j,k}` and `β`; every answer on a facet informs `θ_f`; only the cell's own answers inform `e_{f,k}`.
- Live decisions read the subject view from the AD2/AD3 successor on (§5.6, D3), so the shared terms are learned from the whole subject and the target reads "per subject" from the start: a new topic starts from the subject-level estimate, not from the cold-start prior (D18). With `promoted_predictor` off, decisions fall back to the LO view, where the shared terms are learned from the slot's LO and the target reads "per LO".
- A cell's predictive variance is what remains of the shared terms' variance plus its own offsets'. No answer elsewhere reduces the second part without a coupling. A never-seen facet keeps at least `Var(θ_f) + Var(e_{f,k}) = 1.5` (sd 1.22) at the half split of `ad_priors_v1`. A never-seen facet could be band-ready on its first answer only if the prior put less than about 0.55 logits² in the facet and cell offsets together, that is, asserted that the learner's facets differ from their subject level by less than about ±0.74 logits. None of the three split values the subject view learns among does (§5.5), and no a-priori split could honestly.
- **What sharing buys, then.** These figures come from a linear-Gaussian approximation of §5.6, at 0.14 per answer, with `β` included, after 15 answers elsewhere in the subject:
  - Where the answers concentrate, 10–15 answers in the subject make the practised cells usable. They do concentrate, because a new-lane block stays on one LO (`daily_plan/lanes.py:444`).
  - A never-seen cell needs about 10 of its own answers at the half split, against 11 with no shared history or at the quarter split, and 6–8 at the three-quarter split.
  - Its first item is still pitched at the learner, not at the cold-start mean: its predicted mean comes from the shared terms, so calibrate mode serves an item of acceptable predicted success (§6.2) while the cell's own offset is learned.
- **The split is learned, and tested where it matters.** Field's `lo_general` puts a quarter of the variance in the shared level, `ad_priors_v1` puts half, and the third point puts three quarters. The subject view weighs the three by how this vault's facets spread around their subject level (§5.10). Forecasts on never-seen items still test the result. That is why field's first-attempt split is the primary score for the monitoring and its auto-flags, for item-side signals and for commissioned items (§8.3, D17).

**What a learned coupling buys a never-seen related topic (owner 2026-10-15).** A coupling of strength `χ_C` (the a-priori correlation that one full-strength proposed pair induces between two topics' own parts, §5.10) adds what uniform sharing cannot: part of a topic's own offset becomes predictable from a related topic. The figures below use the same linear-Gaussian approximation at 0.14 per answer, leaving out the feature effects (the uncoupled row still reproduces the "about 10" above), for the simplest case: 15 answers on one topic `L`, a never-seen topic `M` coupled to it at full proposed strength, the same capability, the half split. They were computed for this revision, not taken from a source.

| Coupling `χ_C` | Predictive variance of `M`'s cell | Own answers `M` needs before band mode | Share of `L`'s observed deviation from the prior that moves `M`'s first prediction |
|---|---|---|---|
| 0 (uniform sharing) | 2.35 | about 10 | 0.43 |
| 0.25 | 1.99 | about 9 | 0.54 |
| 0.5 | 1.54 | about 8 | 0.65 |
| 0.75 (the grid's cap) | 1.02 | about 6 | 0.76 |

`L`'s own estimate moves by 0.86 of the same deviation. At the three-quarter split and `χ_C = 0.75`, `M` needs about 3 answers of its own.

- **The mean moves first.** A learner who turns out 2 logits above the prior on `L` has `M`'s first item pitched about 1.5 logits higher at `χ_C = 0.75`, against 0.9 under uniform sharing, before any answer on `M`. Calibrate mode then serves an acceptable item there (§6.2), and band mode follows after the few own answers in the table.
- **Learning transfers along the coupling.** Every practice increment on `L` raises `M`'s predicted level by `corr₀ × γ` (§5.6 step 5). Ten opportunities on `L` at `γ = 0.2` raise `L` by 2.0 logits and, at `χ_C = 0.75`, `M` by 1.5, so `M`'s first questions are pitched higher with no warm-up questions. One strength governs both the level correlation and the transfer in v1; separating them is deferred (§16).
- **Implication works through the loadings.** An item on `L` that loads onto `M`'s facets (§5.10) informs `M` directly when answered, at weight `χ_Q·Q_{i,g}`, and practises it.
- **Reading works the same way.** A reading opportunity on `L` raises `L`'s facets by its kind's next dose-curve increment and coupled topics by `corr₀` times that, and lifts items elsewhere that load onto `L` (§5.11). The increments shrink as a kind's dose grows within a window, and a window's total per kind is bounded.
- **What this buys, plainly.** A skill increase seen in one topic, through practice or reading, moves the predictions for related topics through the learned couplings and loadings, so the next questions there are pitched higher without separate warm-up questions.
- **The honest limit.** A never-seen topic still needs some answers of its own for its own offset. After 15 answers on a related topic, band mode on its very first answer would need a correlation of at least 0.95 (0.88 after 30), and the grid stops at 0.75. Every topic keeps at least `1 − 0.75² ≈ 44%` of its own prior variance for its own answers to settle, on purpose. Where the vault's data say the proposal is wrong, `χ_C` moves toward 0 and the gain disappears with the risk (§5.10). G-AD3-7 checks both on synthetic vaults with known structure: related topics adapt faster, unrelated ones are not dragged (§14).

**What adds information per question.**
- **Partial credit.** The ordinal outcome (§5.3, `κ = 1.5`) adds about 9% near 55% and under 1% near 75%.
- **Help.** It is kept, never dropped. Early help is an observed fail, help after work began is a partial, and unknown timing is a censored non-success (§5.3). A design that kept only unassisted presentations would discard each of these.
- **Rating and timing.** Once their sub-arms earn activation (§5.4), they add at most about 0.06 and 0.04 per answer at their prior links: about +50% and +35% near 75%. Timing applies only to unassisted successes with a latency. Both share the item residual with the outcome in one joint factor, so together they add less than the sum.

**Learning moves the threshold.** Practice changes the learner. Field's `+practice` arm puts `γ` at about 0.2 logits per cold opportunity, about seven opportunities from 50% to 80%. The estimate tracks that moving threshold in three ways:
- **It anticipates.** After each update, the learning transition (§5.6 step 5) raises the touched cells by `E[γ]` before the next outcome is seen. So the next draw already aims at the higher threshold, and the selection steps up with the learner.
- **It learns the rate.** `γ` is shared latent state. A learner who learns faster than its prior mean produces successes above prediction. Those raise both the cell and `γ`, and every later step follows.
- **It never collapses.** `γ`'s remaining uncertainty and the daily drift act as process noise. Treating `Var(γ) = 0.01` as fresh noise at every opportunity holds a practised cell's steady-state sd near 0.5 logits (±8 points). Since `γ` is one coordinate learned from every cell, the real figure is lower.

*Finding at AD2+AD3 (2026-10-19; `docs/reviews/adaptive-difficulty-ad23.md` §3; not an amendment):* the last bullet's figure does not hold for the model as built. `γ` is one persistent latent coordinate, so its remaining uncertainty enters a practised cell's prediction as `t²·Var(γ | data)`, not as fresh noise per opportunity; in G-AD2-18's one-cell scenario the predictive sd at the best served point floors near 0.95 logits after 9-15 answers (0.64 with the learning transition off). Band mode needs `max P_band ≥ 0.35`, which needs an sd of at most 0.74 at a well-centred point, so band mode never engaged there and the draw stayed in calibrate mode. The owner's options are in the review.

**Owner decision 2026-10-19** (`docs/reviews/adaptive-difficulty-ad23.md` §3.4): "Merge with fixes, option 1 + option 2 + option 5 of §3.3. The successor merges with `selection` on, and the failing gates are kept as monitors: their strict xfails stay, with the figures. Lower `calibrate_below` to 0.25. Record it as a NEW, separately recorded pre-registration amendment, made after the reported results, with the reason. The earlier results stand as reported. Re-run `python -m learnloop.sim.ad_gates` and record the new G-AD2-18 figures beside the old ones. Don't change any other threshold. `learned_coupling` defaults to OFF until the owner has spot-checked the relatedness proposal. Update the defaults, the snapshots, the docs and the owner-run commands: show how to turn it on after adopting a coupling version." *Recorded:* `calibrate_below` is 0.25 (amendment A17 of the review's §1.9, made after the results, which stand as reported); at 0.25 band mode engages by the 15th answer for 66% of G-AD2-18's one-cell learners (0% at 0.35), and the gate still fails (band hits 16-30 0.105 against 0.35; the review's §3.4). `learned_coupling` is off by default (§11.4).

**Self-correction.** A wrong prior mean costs answers, not direction. A run of easy successes raises the estimate, and the next band draw steps up; failures step it down. The prior's variance (3.0 at a fresh cell, never shrunk by a claim) keeps the data in charge. After 12 answers, the prior carries about a sixth of the weight on the quantity they inform.

**The gates.** G-AD2-18 measures time-to-usable and the band-hit rate after 10–15 questions on synthetic learners; G-AD3-7 measures what the coupling buys and costs on synthetic vaults with known structure (§14).

### 5.10 Learned relatedness and implication (subject view; owner 2026-10-15, D19)

**What it answers.** Two questions, whose answers depend on the vault:
- which topics answering an item implies knowledge of, and how strongly;
- how related the vault's topics are.

The owner's direction: a learned model, whose hyperparameters change with the vault's subject, with "a frontier LLM with high level semantic reasoning within a learned head harness" supplying the semantic prior. The LLM proposes; this vault's answers decide how far to trust the proposal (R13).

**Shape: two sparse sets of extra shared terms in §5.2's hierarchy, in the subject view only.**
1. **Soft loadings (a soft Q-matrix).** Each item `i` may load onto at most 3 facets `g` of its subject outside its own, with proposed loadings `Q_{i,g} ∈ {0.25, 0.5, 1.0}` (weak, moderate, strong) and `Q_i⁺ = Σ_g Q_{i,g}` capped at 1. They extend the item's facet weights (§5.4): answering the item informs those facets' cells at its capability, and is predicted from them. Direction lives here: an item on a dependent topic may load onto its prerequisite's facets without the reverse.
2. **Couplings.** Each LO `L` may name at most 3 related LOs `M` of its subject, with proposed strengths `C_{LM} ∈ {0.25, 0.5, 1.0}`. A pair is coupled when either side names it, at the mean of the two sides' strengths (0 for a side that does not name it). A coupling correlates the topic-specific parts of the two LOs' facets: the facet offsets `θ_f`, and the cell offsets `e_{f,k}` at the same capability.
   - **Construction.** When the subject view creates a facet's topic-specific coordinate (`θ_g`, or `e_{g,k}`), it regresses it on the matching coordinates of the facets of its LO's coupled LOs that already exist: `θ_g = Σ_f b_{gf} θ_f` plus an independent own part. The weights spread each coupled LO's strength evenly over its existing facets, and are scaled so that the coupled part carries a share `χ_C² · min(1, Σ_L C_{LM})` of the coordinate's prior variance (§5.5); the own part carries the rest. The scaling reads the a-priori covariance of the regressors, which the replayer keeps beside the state, never their posterior.
   - **What that gives.** One full-strength pair induces an a-priori correlation `χ_C` between the two topics' own parts; `corr₀` denotes this a-priori correlation wherever the spec uses it. Because the new coordinate was untouched until created, creating it by regression on the current posterior gives exactly the posterior it would have had from the start, for every observation update. The joint prior is positive definite by construction, whatever the proposal.
   - **Learning transfers.** Learning and reading increments on a facet also reach its existing coupled facets, at `corr₀` times the increment (§5.6 step 5, §5.11).

The LO view has neither, and in the subject view `χ_C = χ_Q = 0` removes both exactly.

**Priors: a frontier LLM proposes the means (`ad-relatedness-v1`).**
- **What it reads, per subject:** the LOs' titles and summaries, the facets' titles and descriptions, the concept graph and prerequisites (`relations.yaml` edges, `vault/models.py:171-178`; `LearningObject.prerequisites`, `:330`), and the stems of the subject's items.
- **What it never reads:** learner data of any kind (attempts, grades, diagnoses, claims, ratings, reading or questions), any held-out or exam unit's text or any item derived from a held-out unit (A8), and any reference answer.
- **What it returns,** as typed structured output: per item, its loadings with a one-line rationale each; per LO, its related LOs with strengths and rationales. Anything that fails validation (an unknown id, a facet of another subject, a self-loading, more than three per unit) is dropped, and a unit left with no valid proposal has none: uniform sharing for it.
- **Where it runs.** A background job per subject on the field harness's existing frontier-LLM route, `ai.routing.llm_probability_llm` (empty means `ai.active_provider`; Codex on the owner's subscription is allowed), through the spend framework, inside `adaptive_difficulty.daily_spend_cap_usd`, dry-run first. It runs only while `learned_coupling` is on.
- **Ledger.** Each proposed loading and coupling appends one `judgment_ledger` row: task `ad_relatedness`, prompt version `ad-relatedness-v1`, judge `llm`; the item revision (by `content_hash`) or LO on the left; the facet or LO on the right; the strength as `score`; the rationale; and an `input_hash` over exactly what the job read. Replay reads these rows and never asks again (§11.3).
- **When.** A one-time backfill per subject at the AD2/AD3 successor's tag. After that, a re-proposal whenever the subject's content changes: an LO or facet added, retitled or redescribed, or a relation or prerequisite edited (couplings of the LOs touched); a new item revision (its loadings only). An unchanged `input_hash` is never re-asked.
- **As of.** The subject view is built under one coupling version. Adopting a version, the first at the successor's tag, applies the proposals then in force to the whole history, by one rebuild. After that, a proposal reaches only what did not exist yet: the loadings of a new item revision, frozen in its serve-input receipt (§7.5), and the couplings of a facet whose coordinates are created after it. Changing a coupling or loading of something that already exists is a reinterpretation: a new coupling version, adopted through the playbook with a shadow-rebuild report (§7.5, §11.1).

**Uncertainty and learning: the vault learns how far to trust the proposal.**
- **The hyperparameters are latent.** `ξ = (σ_G², χ_C, χ_Q)` says how much is shared versus topic-specific, how strongly topics couple, and how strongly an answer implies knowledge of other topics. It is learned per vault as hierarchical latent state, with the a-priori, versioned prior `ad_hyper_v1`, uniform over 36 grid points (§5.5). Nothing about it is hand-set (A5).
- **How it is learned.** The subject view runs one filter per grid point and weights them by their running marginal likelihood (§5.6 step 4), the Bayesian model average `[hoeting1999]`. Predictions, `P_band` and propensities read the mixture, so they stay exact (§5.7).
- **Learned shrinkage.** The grid contains `χ_C = 0` and `χ_Q = 0`, which are exactly uniform sharing. If the proposal does not predict this learner's answers, the weight moves there and the proposal stops steering. The prior is wide: zero carries a quarter of the prior mass for coupling and a third for implication.
- **Per pair, only the proposal.** One learner cannot identify one pair's strength (§5.8). Each pair and loading keeps the proposal's value times the learned vault strength, and a wrong pair is corrected, for prediction, by its topic's own answers. Learning pairs individually needs pooled data (§13).
- **Cost.** Each grid point is one filter over a state of tens to a few hundred coordinates: small. `ad_hyper_v1` is versioned, and the harness sweeps a finer grid (§10.4).

**What it changes, and what it never touches.**
- **Prediction only:** `p̄`, `P_band` and `I_c` in the subject view, and so the serve and commission draws, the forecasts, the readiness numbers and AD5's composed success `q_h`.
- **Never:** evidence, mastery, facet recall, FSRS, certification credit, levels or requirement points (A2, A11); an item's cell-pool membership, which stays its own facets (§6.1); the relations registry, to which nothing is written (KM §8.1, §8.4).

**Safeguards.** The learner-field spec rejected LLM relation graphs because "Propagating these outcomes across a graph would spread the attribution error" (field F6, D2). The owner superseded that deferral for this view on 2026-10-15, under these safeguards:
1. **Sparsity.** At most 3 loadings per item and 3 coupled LOs per LO. Influence reaches other topics only through these few terms, and weakens along chains as the product of strengths.
2. **Shrinkage.** The vault-level strengths are learned with zero in their support. Every topic keeps at least 44% of its own prior variance (`χ_C ≤ 0.75`), and every item at least half its weight on its own facets (`χ_Q ≤ 0.5`).
3. **Prediction-only influence, never certification credit.** As above; G-AD3-5 tests that evidence and certification are byte-identical under any proposal.
4. **Kill switches.** `learned_coupling = false` restores uniform sharing exactly: the subject view at its `χ_C = χ_Q = 0` points, with the split still learned, and no proposal calls. `promoted_predictor = false` restores the LO view exactly (§11.1).
5. **An auto-flag.** It fires when the coupled model predicts first attempts at never-seen topics worse than uniform sharing, and recommends `learned_coupling = false` (§10.4).
6. **No learner data in the structure.** The proposal never reads learner data, so a grading or attribution error cannot shape which topics are coupled. Such an error reaches only the directly loaded or coupled topics' terms, in proportion to the learned strengths.

**How it is scored.** In the learner-field harness, on field's first-attempt split (first attempts at never-seen LOs), against uniform sharing (field's `lo_general`, `field/predictors.py:510`, and AD's own `@subject_uniform`) and topic-only (`@lo`) (§10.4, D17).

**Protection resets a subject's learned coupling (AD2+AD3 fix round 12, Codex verify F38; owner-facing).** Each relatedness run records a fingerprint of its subject's protected material at proposal time: the protected item ids, revisions and sources in the subject's prompt context. When a subject's protection changes, every run proposed under the old protection stops being used, at `load_structure` and in the replay (no model call there). Its LO couplings and loadings both stop, and so do frozen loadings that name one of its judgments. *The consequence for the owner:* protecting material in a subject (or releasing it) resets that subject's learned coupling. AD then predicts there with no learned coupling until the owner re-proposes the subject's relatedness and adopts the new version. The next proposal re-asks every unit, because no run under the current protection answers for any of them. `learned_coupling` is off by default (owner decision 2026-10-19), so this affects only a vault that has turned it on and adopted a version.

### 5.11 Reading and other learning opportunities (subject view; owner 2026-10-15, D20)

**The idea.** A Reader session on an LO's sections is a learning opportunity, like a practice attempt. It raises the *predicted* level, so the next draws aim higher, exactly as the practice increment `γ` does (§5.6 step 5). It is never evidence (A12): the answers that follow confirm or correct the rise, as they do for practice. Each kind of reading event has its own learned weight, so the AD report can say which kinds of active reading help this learner's cold retrieval, and how much of each is worth the time (§10.4).

**The firewall exception, confirmed (owner 2026-10-15; A12).** Reading signals are salience-only, and the firewall's standing rule keeps them out of "mastery, posterior, readiness, certification, or scheduling" (§3.1). AD's predictor is a posterior, and its draws and readiness numbers are scheduling and readiness, so AD reads reading only under an exception. The owner confirmed it with four limits:
1. **Only discrete events:** the four kinds below, each the fact that something was read, viewed, explained, studied or answered, with a dose. No magnitude ever reaches the state, a draw or an offer: no dwell, scroll, highlight or skip count, no visibility segment, no active time, no answer text, and no output of the salience projector. The one typed value admitted is the self-check verdict, as D22's separate term (below). The report's cost side reads the Reader's recorded visit minutes, as the Reader report does, and nothing it computes acts (§10.4).
2. **Prediction and selection only, never evidence or certification:** the subject view's predictions, and so its draws, commissions, forecasts and readiness numbers. Never evidence, mastery, facet recall, FSRS, certification credit or levels.
3. **Learned weights:** each kind's dose curve is latent state with a-priori, versioned priors, learned per vault (§5.5, below). Nothing is hand-set.
4. **Its own kill switch and auto-flag:** `reading_opportunities` and the reading auto-flag (§10.4); for the verdict term, `reading_self_check` and its flag (D22).

**The carve-out (AD2+AD3 stage).** The stage updates the standing rule's text in `attempts/salience_firewall.py` (`:1-24`) to name this exception and its four limits. It adds one narrow function beside `proposal_priority_signal`, which is the module's one allowed downstream so far (`:137-149`): `learning_opportunity_events`, the only path from reading records to AD's state.
- **It admits exactly the sources in the table below,** and nothing else. No other entry of `READING_EVENT_KINDS` passes (`:40-68`; for example `reader_dwell`, `reader_span_visible`, `reader_scroll`, `reader_highlight`, `reader_question_skipped`), and no salience projection does (`:71-80`).
- **Its records** carry a kind and subkind, the source row's id and time, the LOs, facets and doses, and no magnitude field. They stay stamped `salience_only`, so `reject_salience` still refuses them at `apply_attempt`.
- **The firewall's tests stay.** Every existing test passes unchanged, and the belief modules still never import the module (`tests/test_salience_firewall.py:94-113`). A new test checks the allowlist (G-AD3-13).
- **One list.** AD1's sweep (below) records only these sources. The stage moves that list into the firewall module as the carve-out's allowlist, so the sweep and the carve-out read one list from then on.

**The four kinds, each with its own weight.** They are read from existing ledgers and the Reader's records (§3.1). Each source row yields at most one opportunity, of one kind, with one exception: a completed section is one `reading` event and also one `worked_example` event for each worked example in it (below).

| Kind | Sources: the carve-out's allowlist (subkind) | LOs and facets it bears on | Cap |
|---|---|---|---|
| `reading`: a section read and a passage viewed, collated | a section completed in the Reader: `reader_section_progress.completed_at`, stamped once (`section_read`); a span view in `source_exposure_events`, which covers the Guide's passages and passages the tutor cites, unless the span is a worked example (`passage_viewed`) | every LO whose provenance cites the section or span (`learning_objects_for_section`, `learning_objects_for_span`), dose 1 | a section once per section and LO; passage views one per LO per day |
| `reader_tutor_exchange` | an answered tutor question asked while reading: `question_events` with context `reader` or `library` (its answer mode) | its LO, or its facets where `facets_json` names them, dose 1 each | three per LO per day |
| `worked_example` | a worked-example block, found by its role, that the learner was shown (a span view of it) or that sits in a section they completed (`studied_worked_examples`) | the LO whose provenance cites it, dose 1 | once per example |
| `in_passage_question` | an in-passage question or active-reading prompt the learner answered: a `reader_authored_questions` row with `answered_at` set and style `recall`, `next_step`, `why_step` or `assumptions` (the style); an owner-placed reading question's `reader_answer_submitted` event on its administration (`owner_placed`) | the LOs of the question's section, or of its anchor span, dose 1 | once per question |

- **Doses.** A facet named directly takes dose 1. An opportunity that names only an LO spreads dose 1 evenly over the LO's facets. The caps keep repeated reading from counting as repeated learning, as field §3.1 caps signal mass. Within the caps, the dose curves below give diminishing returns.
- **A worked example is one kind, not two.** A span view of a worked-example block is a `worked_example`, not a `passage_viewed`. A completed section is one `reading` event, and each worked example in it is a `worked_example` event of its own: the prose and the examples are different things to have studied. Because the two arrive together, the randomized offers of §5.12 are what separate their weights.
- **What a kind leaves out.** `reconstruct` questions are not in-passage answers: they are escalated to practice items and served later as cold reconstructions, so AD reads them as attempts. Skipped or dismissed questions and unanswered prompts are not opportunities.
- **In-passage questions are opportunities, not evidence.** Today none writes an attempt (§3.1). Quick checks and RW1b's prompts are formative, and owner-placed questions are source-visible instructional administrations. AD never reads the learner's outcome class or answer text; it reads the self-check verdict only as D22's separate term (below), never as a grade. Where such a question is graded as an attempt, its evidence enters through the ordinary pipeline, and it is counted once:
  - an escalated question becomes a practice item, and its later attempt is a separate event that AD reads as it reads any attempt (§5.6);
  - a Reader surface that grades an in-passage answer as an attempt takes this kind's increment in place of `γ`, and its outcome enters the update once (§5.6 step 5).
- **RW1b is not built yet.** The `next_step` and `why_step` styles exist in the schema (§3.1). The kind counts them once the actions land.
- **The same channels as router §15.2.** These are the "reading, tutor" exposures router §15.2's covariate view names. That view is not built yet (§3.1), so AD derives them itself; the view can read the same receipt once it exists.

**Self-check verdicts (owner 2026-10-17; D22).** An in-passage question the learner answered and then judged against the revealed answer carries a verdict: *matches*, *partly* or *no*. The verdict is information about the topic, so it enters the prediction as its own learned term, beside the dose curves and separate from them.
- **The source.** The verdict's `judgment_ledger` row (task `reader_quick_check_self_check`, a `learner_card` verdict on the question and response, appended by `reader_quick_check._append_self_check_verdict`). It covers the section quick checks and RW1b's next-step, why-step and assumption prompts. Owner-placed reading questions have no verdict, and `reconstruct` questions are escalated to practice items as before. AD reads the ledger row through the carve-out. It never reads `ReaderObservationV1`, which stays `routing_only` (reader workbench G50).
- **Two classes:** `matched` (matches) and `missed` (partly or no). A question counts once: the first verdict written decides its class, and a later change, which appends a superseding row, is not read. A question answered without a verdict keeps only its D20 opportunity.
- **The term.** A verdict of class `v` on a question whose opportunity carries dose `D_f` on facet `f` sets `θ_f ← θ_f + λ_v·D_f`. Each existing coupled facet gains `corr₀(θ_f, θ_g)` times the same increment, and items elsewhere gain through their loadings, as for an opportunity. The increment is linear in `λ_v`, so the covariance propagates exactly.
- **Learned, with neutral priors.** `λ_matched` and `λ_missed` are latent state, learned per vault, with a-priori, versioned priors centred on 0 (`ad_priors_v1`, §5.5; `N(0, 0.3²)` logits). With no data the term is 0, so the prediction equals D20's exactly. `λ_missed` may become negative, so a miss can lower the predicted level. If verdicts don't predict later first attempts, both shrink toward 0.
- **Why the classes are asymmetric in expectation, but not in the prior.** A *partly* or *no* is a fairly reliable admission. A *matches* is judged with the expected answer showing and the book open, conditions that favour overclaiming. The prior stays symmetric, so the learner's own data says how much each class is worth.
- **What it never touches:** evidence, mastery, facet recall, FSRS, certification credit, levels and scheduling credit (A12 limits 2–4). No verdict passes the evidence chokepoint.
- **Self-check calibration in the AD report (§10.4).** Per class, the realized success of the next first attempt on the question's facets, against the predicted success with and without the term, with intervals. It says how well this learner's self-checks predict what they can do cold. It is read-only: nothing it computes acts.
- **Switch and flag.** `reading_self_check` (AD2/AD3 tag). Off removes the term and restores D20's prediction exactly, and the receipt rows are still written. It is moot when `reading_opportunities` or `promoted_predictor` is off. Its auto-flag recommends it off when `@subject` is worse than `@subject:noverdict` on first attempts after a verdict (§10.4).

**Frozen in a receipt.** `ad_reading_opportunities` (RECEIPT, append-only; §11.2) holds one row per (opportunity, LO): its kind and subkind, the source row's id and write time, the facets and doses as the mapping resolved them, the `ad_dose_offers` id when a randomized offer produced it (§5.12), the mapping version, and the authority class `salience_only`.
- **Written by a sweep.** At every serve, in the serve transaction and before its forecasts, a sweep records every opportunity whose source row was written since the last sweep. AD1's backfill sweeps the history once (§14).
  - *Amended at the AD1 Codex review (2026-10-18; `docs/reviews/adaptive-difficulty-ad1-codex-review.md`, F4):* a tutor exchange exists once its answer completes, so its source time is `question_events.answered_at` (migration 213, set once by the pending-to-answered update; a row written already answered keeps `created_at`), and every serve's sweep reads every answered exchange not yet recorded, however long ago it was asked. A question pending at a serve is never placed before it.
- **Why a receipt.** `reader_section_progress` is WORKFLOW and is deleted with its extraction, and the section-to-LO mapping depends on content that can change (§3.1).
- **Ordering.** Replay orders opportunities by their source row's write time. Every serve's sweep has already recorded everything written before it, so the state replay rebuilds is the state each serve saw (§7.3's rule for signals).
- **Switch.** The receipt is written under `forecast_receipts`, like AD's other receipts; `reading_opportunities` governs only whether the subject view applies it.

**The transition: one learned, saturating dose curve per kind.**
- **The curve.** The effect of kind `κ` on a facet, as a function of the dose `n` the facet has received in its current window, is

  ```
  g_κ(n) = γ_read[κ,1]·b_1(n) + γ_read[κ,2]·b_2(n),      b_m(n) = 1 − exp(−n / h_m),      h_1 = 1,  h_2 = 4
  ```

  The fast scale `h_1` says what the first event or two add, the slow scale `h_2` what several add. The scales are fixed, versioned constants (§5.5); the learned coefficients set each kind's shape.
- **The window.** A facet's window opens at its last graded attempt and closes at its next one (§5.6 step 5), so `n_{κ,f}` counts the dose of kind `κ` since the learner last answered on that facet. A curve thus says how much of a kind, before the next answer on the topic, adds to what the learner keeps. The dose-and-burden analysis reads it at a cold attempt (§10.4).
- **The transition.** An opportunity `o` of kind `κ` with dose `D = D_{o,f}` on facet `f` sets `θ_f ← θ_f + g_κ(n + D) − g_κ(n)`, then `n_{κ,f} ← n + D`.
  - Each existing coupled facet `g` gains `corr₀(θ_f, θ_g)` times the same increment (§5.10), and items elsewhere that load onto `f` gain through their loadings.
  - The increment is linear in the coefficients, with known numbers `b_m(n + D) − b_m(n)` as weights, so the covariance propagates exactly.
- **Diminishing returns, and a bound.** Each basis function rises with dose and flattens. With positive coefficients each further event of a kind adds less than the one before, as log counts do within a window in DAS3H `[choffin2019]`. Whatever the coefficients, a window's effect of one kind never exceeds `|γ_read[κ,1]| + |γ_read[κ,2]|`. A negative slow coefficient lets the data show a dose past which more of a kind does harm, as the expertise reversal effect describes for worked examples `[kalyuga2003]`.
- **Learned, hierarchically.** `γ_read[κ, m] = γ̄_m + δ_{κ,m}`: a shared curve, which every kind's events inform, plus a deviation per kind, which only that kind's events inform. All of it is latent state with the a-priori, versioned priors of §5.5, learned per vault from its answers, never hand-set (A5, A12). A kind after which success does not rise shrinks toward 0, and a rarely seen kind leans on the shared curve until its own events speak.
- **Warmth is separate.** The same events also feed the warmth covariate (§5.4), which carries the short-lived lift of recent exposure. The dose curves carry the lasting part, which is what a cold attempt measures.

**Where it reaches.** Like the couplings: the subject view's draws, commissions, forecasts, readiness numbers (with the untested rule, §9.5) and AD5's `q_h`. The LO view never reads it.

**What it never touches.** Evidence, mastery, facet recall, FSRS, certification credit and levels (A2, A12).
- AD reads its own receipt, through the carve-out, in its own replayer, and writes only DERIVED tables. No reading opportunity passes the evidence chokepoint (`reject_salience` in `apply_attempt`, §3.1).
- This keeps the P3 firewall's purpose: reading is never evidence (P3 §8.2, §15.4). It also keeps field §3.1's guard: signals may change routing and predictor state, never evidence.

**How it is scored.** By whether it improves predictions on first attempts after reading: the AD report scores the subject view against the same view with reading off (`@subject:noread`), on first attempts on an LO with a reading opportunity since its last answer, or since the start (§10.4). An auto-flag recommends `reading_opportunities = false` when reading predicts worse. What each kind is worth, per event and per minute, is the dose-and-burden analysis of §10.4.

### 5.12 How many: randomized dose offers in the Reader (owner 2026-10-15; D21)

**Why.** The curves of §5.11 are fitted to what the learner chose to read. A learner reads more, asks the tutor more and studies more examples when struggling, and that struggle also shows in the answers that follow (§5.8, `[robins2000]`). So the curves alone cannot say how many worked examples or in-passage questions to do. A small randomized arm in the Reader can. At a section it randomizes whether one *extra* worked example or in-passage question is offered, within a friction budget, with exact logged propensities (A7). It is a micro-randomized design: one learner, many decision points `[klasnja2015]`.

**The decision point.** A section boundary in the Reader where the existing quick-check conditions hold (anchor mode with section prompts on, `boundaryChecksAvailable`, `apps/learnloop-tauri/src/screens/ReaderScreen.tsx:326`), and also:
- the section maps to at least one LO (`learning_objects_for_section`);
- the cue density is not off, the Reader is not in skim mode, and the section is not the passage the learner was restored to (the Reader's restraint rules, `spec_reader_workbench_v1.md` §6.1);
- the friction budget has room (below).

**The variants.**
- **`none`:** the Reader exactly as it is.
- **`extra_worked_example`:** one more worked example on the section's LO, from the learner's sources and not yet studied. It comes from the sources spec's worked-example retrieval once that merges, and before that from a worked-example block, found by role (`instructional/exposure.py:104`), that the LO's provenance cites. No model writes one.
- **`extra_question`:** one more in-passage question on the section, from the existing quick-check producer within its caps. Once RW1b lands it is a `next_step` or `why_step` prompt on a derivation or worked example in the section; until then, or with none in the section, a `recall` question.

A variant whose content cannot be had at the decision (no unstudied example, no producer result in time) is infeasible. It leaves the support, the propensities renormalize over the feasible variants, and both facts are logged.

**The draw (`reading_dose_v1`).**
- **Propensity.** `π(v) = (1 − k·ε)·base(v) + ε` over the `k` feasible variants, with the floor `ε = dose_floor = 0.10`. The default base puts all its mass on `none`. So with both extras feasible, each extra is offered with probability 0.10 and the Reader is unchanged with probability 0.80. The floor holds whatever base the owner later adopts, so every variant keeps support.
- **Seed and log.** The seed is `seed_for(visit id, section id)`. The feasible variants, the base's version, every `π`, the seed and the chosen variant are appended to `ad_dose_offers` before anything is shown (A7).
- **Registration.** The draw is a sixth admissible design, `reading_dose`, in `scheduling/randomization_layer.py:57`. Like `model_mixture` and AD's `feature_overlap` (§10.1), it declares its own floor, which the dormant 0.05 floor never clips. Its outcomes join at the next spaced cold review, as the layer's do (`:19-26`).
- **Reversible, in the layer's sense.** An offer creates no commitment, reservation or schedule, and the learner can ignore it, so the layer's `grade_for` labels the arm `experimental` (`:98-109`). What an offer teaches persists. The dose curves count that carry-over, and the effect estimated below is that of one more offer given the offers and reading before it, which is why the dose already taken is its moderator.

**The friction budget.**
- One extra offer per section, and at most `dose_daily_offers = 3` a day.
- The offer is a LearnLoop element. It counts against the Reader's density budget and its one-mark-per-screenful rule. It never gates the text, never animates, and is dismissed with one key. A dismissal is never read as low ability.
- With the budget spent, or density off, no draw is made. The budget is a function of the logged offers, so which sections were eligible can be rebuilt.

**Uptake.** Delivery, uptake and dismissal append rows to the same ledger (`delivered`, `not_delivered`, `taken`, `dismissed`) and never change the draw's row. A taken extra becomes an ordinary reading opportunity of its kind (§5.11), with the offer's id on its receipt. How often offers are taken is open (§17, Q9).

**What it identifies.** The estimates are in the AD report (§10.4).
- **The outcome.** §5.3's event on the first graded attempt on an item of one of the section's LOs that comes at least one cold retrieval delay after the decision (one day, `diagnosis/remediation.py:31`), with no reveal of that item in between. Pending outcomes are right-censored.
- **The offer's effect.** For each extra variant against `none`: the effect of the offer on that outcome, averaged over the rest of the Reader as it ran. This is the proximal, moderated causal effect of a micro-randomized trial `[klasnja2015]`, `[boruvka2018]`, estimated with the logged propensities.
  - **Moderated by the dose already taken** of that kind in the window (0, 1, 2 or more). That is the randomized dose-response: the effect of one more, at each dose.
  - **Moderated by the predicted level band** at the decision, for the "helps when" lines of §10.4.
  - **Adjusted for precision** by the AD forecast fixed before the draw, which cannot bias a randomized comparison.
- **The effect of taking it.** An offer may be ignored. With the offer as an instrument, the effect on the occasions when the learner would take it is identified only if an offer works by being taken, never by being seen; otherwise the ratio has no causal reading `[angrist1996]`. The report labels it so.
- **Other offer policies.** Exact propensities let the report value policies with support in the arm, for example "offer an extra example while fewer than two were studied".

**The honest limit.** One learner's arm is slow. A planning illustration (iid, not a guarantee, as in §8.3): detecting a 10-point difference in cold success near 70%, at 80% power and two-sided 5%, needs about 300 outcomes of each extra variant. At the default floor, 100 eligible sections give about 10 offers of each. So at n=1 the arm resolves only large effects, and only after thousands of eligible sections. Until it does, the report says "can't tell yet" for it and labels the model's curves as observational (§10.4). Its rows are in the contribution export (§13), where pooled learners shorten that.

**Switch.** `reading_dose_offers` (D21). Off is today's Reader exactly: no draw, no offer, no row. It is independent of `reading_opportunities`. The arm changes what the Reader may offer, not any persisted meaning, like RW2c's passage draw (`spec_reader_workbench_v1.md` §5.10), so it needs no successor tag of its own. It ships with the AD2+AD3 stage (§14). An auto-flag recommends turning it off when the offers are a burden (§10.4).

---

## 6. Selection

### 6.1 Practice: land in the band

**Scope.** AD decides *which feature point and which item* for new material in a cell. *Which LO or facet to practise* is decided upstream (daily-plan lanes, router blocks, diagnosis repair).

AD makes two kinds of draw, logged separately: a **serve draw** over items that exist, and a **commission draw** over feature points to generate. Only the serve draw puts an item in front of the learner, so only its propensity enters off-policy evaluation of what was served.

**When it serves, and which state it reads (owner direction 2026-10-14 and 2026-10-15; D3).**
- Practice selection serves from the AD2/AD3 successor, behind its switch `selection`, with the a-priori priors of §5.5 and the honest uncertainty of §5.7. It waits for no harness result. A QUEST+-style band rule corrects itself from the learner's own outcomes even when its prior is off: a run of easy successes raises the estimate, and the next draw steps up (§5.9).
- Every draw about an LO `L`, serve or commission, reads the subject view (§5.6) while `promoted_predictor` is on, the default from the successor's tag. So the rest of the subject, the learned couplings and loadings (§5.10) and reading (§5.11) steer it, and a never-seen LO's first draw starts from the subject-level estimate (D18). With `promoted_predictor` off, every draw reads `L`'s LO view, exactly as a build without the subject view would (A6).
- The harness keeps scoring the subject view against the LO view and uniform sharing. It turns nothing on or off by itself; its auto-flags recommend a switch to the owner (§10.4).
- Whenever a draw randomizes, its propensity is exact and logged before the item is served (A7, step 4).

**The cell pool `P_c`.** An item is in cell `(f, k)` when `k_i = k` and `w_{i,f} > 0`.
- Every never-attempted, servable item in the cell, with its features and signals resolved as of now (§7.5).
- Excluded: exam-reserved items (`exam_pool.reserved_item_ids`), retired items, anything derived from a held-out unit, and items whose answer was exposed before serving (§5.3).
- Items authored above the depth envelope (`RungTarget.task_feature_bounds` "max") are excluded too. `coordination` items are served only behind a reviewed envelope (`depth_rungs.py:126-129`, `:176-182`).

**When AD draws, and over what: the slot support `S`.** AD never builds or reorders blocks (§10.1).
- The plan's source packs blocks exactly as its predecessor does, and the block is chosen exactly as today: by the router's draw, or, with the router off, by DL1's deterministic chooser (`daily_plan/policy.py:1-20`).
- A serve draw happens when a **slot** of the chosen block comes up to be served. A slot is a planned item with `new_admitted = true`: an ordinary never-attempted new-lane item the chooser planned, never a learner pick, a request, a follow-up or a scheduled check (`daily_plan/engine.py:1555-1557`). A new-lane block stays on one LO (`daily_plan/lanes.py:444`).
- The **candidates** of that draw are the slot item and every other never-attempted item of the slot item's LO, at the slot item's capability. The support `S` is the candidates that pass **every** check below at the moment of the draw.
- **The slot item gets no exemption.** Its block was admitted at a boundary. The frame evaluates items only there (`daily_plan/staged_frame.py:9-16`) and keeps that material for the whole request (`:194-211`). Before a serve, reconciliation re-checks only status and serving blocks (`daily_plan/engine.py:1925-1931`, run at `:2424`, before the serve at `:2484`). So a reservation, a cold check, a reveal or a constraint can change between the block's admission and its slot's serve. Every check is re-read at the draw, never taken from the admission or from the frame's cached material:
  0. **are still eligible:**
     - in `P_c` now, for some facet of the slot item, with its exclusions re-read (exam reservation, retirement, held-out derivation, pre-exposure, the depth envelope);
     - with no serving block (`vault/lifecycle.py:162-163`);
     - outside the exclusions that a selector outside the scheduler's timing honours. These are the routine exclusions, the item an open cold follow-up holds, and any item revealed within the cold retrieval delay (`scheduling/serving_exclusions.py:18-27`, `:84-86`). They are read as the quick check reads them (`diagnosis/quick_check.py:193-196`);
  1. **pass the admission the slot item passed.** Under the staged frame (router on): the constraint engine admits them in the block's attention action, re-evaluated against a fresh controller snapshot exactly as the frame evaluates items at a boundary, and they are reversible: no open cold check and no reserved assessment surface, the condition R2b's mixture already places on anything it draws (`staged_frame.py:42-52`, `:498-523`). With the router off: the predecessor's pool rules for the new lane, plus the same reversibility condition;
  2. are not planned in any of today's plans, this block included (for the slot item: in no slot but its own);
  3. **fit the block:** `est_minutes(i) ≤ est_minutes(slot item) + slack`, where `slack = max(0, min(BLOCK_MAX_MINUTES − the block's planned minutes, the plan's minutes_left, the new lane's minutes_left))` (`daily_plan/types.py:52`, `:79`, `:81`). So the block stays within 15 minutes and the plan within its budget (daily loop P1), and the slot item always fits;
  4. **add no admission load the plan did not grant:** `new_item_daily_cost(i) ≤ new_item_daily_cost(slot item)`, or the day's admitted load with `i` in place of the slot item stays within the ceiling (`daily_plan/admission.py:138-139`, `:142-201`). A one-for-one substitution leaves the count unchanged, and a slot that came in by the floor or the "more new material" override is never replaced by a costlier item.

  Checks 2–4 hold for the slot item by construction. Checks 0 and 1 are where it can fail.
- **A slot item that fails a check** is not in `S`, and AD draws among the other candidates. With none, `S` is empty (step 0 below). A slot item that passes, with no other candidate, is `S` alone and is served with `π = 1`.
- **With `selection = false`** none of this runs. The predecessor serves the planned item exactly as today (§10.2).
- **One transaction, no recomputation.** The support, the draw, its `ad_selections` row, any substitution and `item_served` are one transaction (`daily_plan/engine.py:2566-2599`). Nothing can change between the checks and the exposure, so a propensity is never recomputed after the draw and a drawn item is never refused afterwards. An item that fails a check is simply not in `S`.

**Serve rule (`ad_select_v1`):**
0. **Empty support.** If `S` is empty, AD makes no draw. The row records `empty_support` and each candidate's failed check.
   - **Pre-exposure only.** If the slot item failed only the pre-exposure check (§5.3), it is served as the predecessor serves it, with no draw: the row's mode is `predecessor` with `π_AD = 1`, and its receipts carry `pre_exposed = true`, so it neither trains nor is scored. So a pre-exposed item is never in a randomized support, and the learner still gets the item the plan chose.
   - **Otherwise** the slot is displaced with the container's existing event, `item_displaced`, with reason `ad_ineligible`. Its detail lists the slot item's failed checks, pre-exposure excepted. This is how reconciliation displaces an item that is no longer servable (`daily_plan/engine.py:1932-1936`), and the container's rules pick the next step.
   - **The displaced item is deferred until its blocking condition clears** (final verify F10). Displacement alone returns an item to the pool: `planned_ids()` drops displaced items (`daily_plan/records.py:247-250`), and a boundary's pool removes only planned and skipped items (`daily_plan/engine.py:1218-1230`). The scheduler does not apply the out-of-timing exclusions to ordinary items, so the next boundary could propose the same item, AD would displace it again, and the plan would loop without spending a minute. So:
     - **The exclusion set.** An item displaced with `ad_ineligible` joins the plan's exclusion set: `planned_ids()`, plus skipped items, plus active AD deferrals. The set is folded from the plan's own events (the `item_displaced` fold, `daily_plan/records.py:394-396`), so a rebuild reproduces it. It replaces the planned-and-skipped set wherever a pool source reads the plan: the boundary's context (`engine.py:1218-1230`), which the lane sources (`daily_plan/lanes.py:463`) and, with the router on, the staged frame (`daily_plan/staged_frame.py:548`) read; and the plan projection (`simulate_blocks`, `engine.py:1083`), which holds the set fixed. A later plan of the same day (`day_records`, `engine.py:310-311`) starts with the day's active deferrals. *Recorded (AD2+AD3, Codex verify F13):* the deferrals enter a pool only through the boundary's switch-aware context (`PoolContext.ad_deferred`: none with `selection` off, less what a boundary released); `PlanRecord.exclusion_ids()` holds only the planned and skipped items, and the projection adds the context's deferrals to it. With the kill switch off, Today's projection is the predecessor's.
     - **When it clears.** At each boundary, the deferral's failed checks are re-read with the functions the draw uses: check 0's sources, and check 1 on a fresh snapshot. The deferral clears when all of them pass, and the item rejoins the pool at that boundary. In practice:
       - a recent reveal clears once the item's latest reveal is older than the cold retrieval delay (one day, `diagnosis/remediation.py:31`);
       - an open cold follow-up's hold clears once that task closes, because the follow-up served the item or was cancelled;
       - an open cold check or a reserved surface clears once it closes or is released;
       - a constraint refusal clears once a fresh snapshot admits the item;
       - a serving block clears once it lifts;
       - an exam reservation, retirement, held-out derivation or envelope breach clears only if that fact changes.

       Pre-exposure is never a deferral reason, since alone it does not displace (above).
     - **Recorded.** The boundary's decision detail records the deferrals it applied and any it cleared, so each decision's pool can be reconstructed from its own row.
     - **Progress.** A deferred item is in no pool. The boundary chooses other work or, with none left, closes the plan as complete, as it does today when the pool runs out (`engine.py:1657-1662`). An item is displaced for ineligibility at most once per deferral, and a deferral clears only after something changes in the vault (time passing a delay, a task closing, a reservation released, a snapshot changing). So the plan cannot loop on the item. Test: G-AD2-31.
1. Compute `P_band(i)` and `p̄(i)` for every `i ∈ S`.
2. **Calibrate instead** if `max_{i∈S} P_band(i) < 0.35` (the posterior is too wide to target the band; typical in a new cell). Choose by §6.2.
3. Near-tie set `T = {i ∈ S : P_band(i) ≥ max P_band − 0.05}`. Overlap set `O = {i ∈ S : p̄(i) ∈ [0.55, 0.90]}`.
4. Draw with exact propensity `π(i) = (1 − q)·1[i∈T]/|T| + q·1[i∈O]/|O|`, with overlap share `q = 0.10`.
   - If `O` is empty, `q = 0` for this draw.
   - The seed is `seed_for(decision key)`, where the key is the block id and the slot's position.
   - The support, both scores, `π`, the seed and the chosen item are written to `ad_selections` in the serve transaction, **before** the item is served (A7).
5. **Substitution.** If the drawn item is not the slot item, an `item_substituted` block event records both items, both estimates and the `ad_selections` id. It is written in the same transaction, before `item_served`. The plan record's fold (`daily_plan/records.py:357-410`) replaces the slot's item and estimate with the drawn item's, so from then on the plan's planned minutes use the drawn estimate. The displaced slot item is unplanned and returns to the pool.

**Commission candidates `X_c` and rule.**
- `X_c`: the rungs of every ladder instance that applies to the cell (each active goal's ladder and the default ladder, §9.1) and their one-step neighbours on a single ordinal dimension, clipped to the depth envelope.
- A commission draw runs in two places, for the cell of the slot or LO at hand (its highest-weight facet, ties by facet id, at its capability):
  - at a serve draw, when the cell pool `P_c` (not the slot support) has no item with `P_band ≥ calibrate_below` (0.35 as registered; 0.25 since the owner decision of 2026-10-19, §5.9);
  - under `generation_contract`, wherever the existing generation path picks a waypoint for an LO (`select_rung`, `content/authoring/practice_generation.py:383-390`). That is how a cell whose pool is empty, and which so has no slot, gets new items.
- It uses the same rule as the serve draw: steps 1–4 over feature points with `z = 0`, with its own propensity, seed and `ad_selections` row (`kind = commission`).
- The chosen point is commissioned for generation (§7) and runs in the background. AD keeps at most one open commission per active cell.
  - **Owner decision 2026-10-19** (`docs/reviews/adaptive-difficulty-ad23-codex-review.md` open question 2, F5): "An unlanded commission (its generation failed or was rejected) EXPIRES 7 days after its job finished, so a fresh one can be drawn for that cell. Keep "at most one open per cell". A commission routed to review stays open while its item is in review. Add tests."
  - *Recorded (AD2+AD3):* a commission is open until a result lands (§7.4), it expires, or a later commission for its cell supersedes it (which the one-open rule allows only once it closed, so an expiry is never undone). It expires 7 days after its generation finished without landing: the job completed, failed (other than waiting on models that are off) or its batch was cancelled, or, if later, the last review decision on an item proposed for its LO since the draw. It stays open while its job has not run or waits on the models, and while such an item is in review (pending and not invalid). A commission the generation path drew for itself inside a durable job (a practice-expansion job) names that job (`ad_selections.generating_job_id`): its clock starts when that job finished, in any terminal state, and it stays open while the job is queued or running (Codex verify F14). If the job row is gone (deleted or pruned) the clock falls back to the draw; a commission drawn outside any job (a synchronous generation run) generated at the draw, so its clock starts there (`db/stores/ad_serving.open_commissions`). Expiry only closes a commission to new draws: a commission whose item landed gets its receipt whatever its expiry (§7.4, Codex verify F15).
- A commission changes only what can be served later. Its propensity is logged for completeness but never multiplied into a served item's weight.

**Why not Thompson sampling.**
- Sampling the joint state and picking the point nearest 0.75 explores in proportion to uncertainty (worker d).
- But its propensities need Monte Carlo over a ~20-dimensional Gaussian, so they are not exact.
- The rule above is exact, and its overlap share does the confound-breaking job.
- Thompson sampling is kept as a harness comparison (§10.4).


### 6.2 Calibration within acceptable difficulty

When the band cannot be targeted (always within the slot support `S` of §6.1):
- choose `i ∈ O` maximizing `I_c(i)` (§5.7), with near-ties (within 5% of the maximum information, relative) broken uniformly;
- if `O` is empty, choose the item of `S` whose `p̄` is nearest the interval `[0.55, 0.90]`, ties by item id;
- apply the same `q` overlap mixture and log it identically, with `mode = calibrate`.

**Why bounded.** Unbounded information would push toward 50% predicted success `[eggen2006]`. Bounding to `[0.55, 0.90]` keeps a cold learner from a run of failures (frictionless defaults) while still choosing the most informative acceptable item.

This replaces the "optimism step" heuristic (`depth_rungs.py:310-319`) when AD selection is on. The learner sees ordinary practice.

**Exam-target calibration.** When an exam/pset target exists (§9.5) and the goal's due date is within its horizon, `I_c` may be replaced by expected predictive information about success at the target points `[bickfordsmith2023]`. This is the same computation with the target tuples as prediction inputs. Off by default (D12).

### 6.3 Probes: discriminate

Probes keep their episode model, hypothesis sets, actual and predictive EIG (`diagnosis/probe_families.py:467-534`, `:536-620`), and value-of-information stopping (mvp-0.21). They also keep the probe spec's likelihood identity: candidate scoring and the posterior update use the same grader-composed conditionals, and the resolved snapshot is persisted with the presentation (`spec_probe_eig_redesign.md` §7.2, §9.3). Today that holds: `instrument_conditionals` composes the compiled rows with the grader channel (`probe_families.py:454-465`), the presentation stores `CompiledInstrument.snapshot()` (`:267-290`), and the update rebuilds the instrument from that snapshot (`diagnosis/probe_episodes.py:1828-1846`). AD5 adds one composition step *after* the grader channel, on the observed outcomes, and freezes its input in the same snapshot.

**Two probe-spec rules are amended, on purpose, under the AD5 successor only.** §7.2 requires the conditionals of admitted families to be compiled from the resolved card, and §9.3 says numbers change in exactly one place, the family Dirichlet posterior. For a *composed* slot (below), the card and its calibration keep every signature shape, and the success split comes from AD's frozen `q_h`. The identity rule (same conditionals for scoring and update) and the snapshot rule are kept exactly. With `probe_targeting = false`, both rules read as written.

**What AD5 changes in the conditionals (`ad_probe_compose_v1`).** AD supplies exactly one number per composed hypothesis slot: the probability `q_h(i)` that the learner, if `h` is true, gives an unassisted success on candidate `i`, **as graded**. AD learns `Y` from graded correctness and has no latent true response (§5.3–5.6). So `q_h` is the probability of an *observed* success, and grading error is already in it.
1. **Outcome-alphabet mapping.** The *success class* of an instrument is the outcome `classify_outcome` returns for an attempt at full rubric points (`probe_families.py:720-786`; for example `correct_target_reason`, `correct_strategy_complete`, or `high` for the legacy fallback). AD composes an instrument only when that class is exactly AD's event `Y = 2`. Two facts make it so:
   - a diagnostic block disables hints, the tutor, worked examples and answer reveal (`diagnosis/probe_episodes.py:70-77`), so a probe attempt is unassisted and unprimed;
   - correctness is `rubric_score / max_points` (`attempts/attempts.py:3295`), so with a rubric of at most 4 points, correctness ≥ 0.8 means full points.

   For any other rubric the rows stay exactly the card's, and the snapshot says `not_composed: rubric_points`.
2. **Row composition, on the observed outcomes.**
   - For a composed slot `h`, its **observed row** `G_h` is the compiled row `R_h` (true-outcome probabilities, after the family's Dirichlet calibration) composed with the family's grader channel, exactly as `instrument_conditionals` does today (`probe_families.py:454-465`).
   - Let `G_h(· | S)` and `G_h(· | S̄)` be `G_h` renormalized within the success class and within the other outcomes.
   - The composed row is `P(o | h, i) = q_h(i)·G_h(o | S) + (1 − q_h(i))·G_h(o | S̄)`. Its observed success probability is exactly `q_h(i)`, whatever the channel's reliability.
   - The card keeps its signatures (which wrong answer each hypothesis gives), and the channel keeps shaping how each is observed. AD replaces only the success split.
   - The ordinal table's floor (`negligible` = 0.01, `probe_families.py:28-34`) keeps both parts non-empty.
3. **Capability-hypothesis constraints.** A slot is composed only when its hypothesis is a constraint on cell abilities. "Below" and "at or above" a capability mean that the learner's success chance at that capability's entry point `e_k` (§9.1), with the item's facet weights and no warmth, is below 0.5 or at least 0.5:

   | Slot | Constraint |
   |---|---|
   | `unfamiliar` | retrieval below |
   | `recall_without_mechanism` | retrieval at or above; schema_interpretation below |
   | `procedure_without_selection` | procedure_execution at or above; method_selection below |
   | `robust_initial_grasp` | retrieval and the item's capability at or above |

   - `q_h(i)` is the posterior predictive success on `i` (the residual `ε` and the uncertainty of `β` and `α` integrated, §5.7) with the AD state conditioned on the constraint. The state is the view live decisions read (§6.1): the subject view while `promoted_predictor` is on, else the probe LO's view. The constraint truncates at most two linear functionals of the Gaussian state. The expectation is computed by deterministic quadrature over the truncated region, with the remainder conditional-Gaussian. If the constraint has probability below 1e-6 under the state, the slot is left uncomposed and the snapshot says so.
   - **Not composed:** `surface_only` and `schema_without_transfer` (transfer is a shared feature effect in v1, not a learner state AD can condition on), `other_or_unknown`, and every `misconception:*` and `confuses_with:*` slot. Their rows stay exactly the card's or the legacy fallback's, with their discrimination profiles and contrast pairs (`PracticeItem.discrimination_profiles`, `contrast_of`).
   - Card slot aliases (for example `surface_only` → `recall_without_mechanism` in the derivation family, `probe_families.py:1292-1294`) resolve before composition, so an aliased label reads its slot's composed row.
4. **Grader channel, applied once.** Uncomposed slots go through `compose_with_grader_channel` with the family's grader policy and reliability, exactly as today (§7.6 of the probe spec). A composed row is already observed and does not go through the channel again.
   - This is within the probe spec's own rule: evidence-strength fields "MUST either be explicitly post-grader quantities or be composed with this grader channel at runtime" (`spec_probe_eig_redesign.md` §7.6). `q_h` is a post-grader quantity. The card's signature shapes are still composed with the channel, as the probe spec's §7.2 requires.
   - Composing before the channel would apply grading error twice.
   - Take the contrast family: six outcomes (`probe_families.py:798-823`), reliability 0.90, so each other outcome receives 0.02 (`:59-62`, `:411-430`). There, `q_h = 0.80` would be observed as `0.90·0.80 + 0.02·0.20 = 0.724`. This composition keeps it at 0.80 (G-AD5-7).
5. **Calibration ownership.** The family and item Dirichlet counts (`probe_families.py:1722-1790`) keep accumulating as today and keep owning each slot's signature shapes. For a composed slot, only the within-class shapes `G_h(· | S)` and `G_h(· | S̄)` of the grader-composed calibrated row are used. The success split comes from AD alone, so it is never learned twice. This is the amendment stated above.
6. **The frozen snapshot.** When a candidate is scored, the composed instrument is built once. It is the instrument that candidate EIG and predictive EIG score, and it is the one `snapshot()` stores when the presentation commits.
   - The snapshot keeps the calibrated rows `R_h` as today and gains an `ad_composition` block. The block holds the composition version, the AD state hash and the priors version. Per slot, it holds `q_h` with the constraint and its probability, or the reason the slot was not composed.
   - `CompiledInstrument.from_snapshot` reads the block (`probe_families.py:291-300`), and `instrument_conditionals` applies it after the channel. So candidate scoring and the update compute the same composed rows from the same snapshot.
   - `compiled_likelihood_hash` covers the block when present (`probe_families.py:253-265`), and an instrument without one hashes exactly as today. So the probe audit's recomputation check covers `q_h` with no change (`diagnosis/probe_audit.py:311-320`).
   - The posterior update reads the snapshot, as today, and never recomputes `q_h` from a later AD state.
7. **Unchanged paths.** The incidental likelihoods of ordinary attempts (`probe_episodes.py:1884-1906`) and the legacy fallback's uncomposed slots keep today's `generic_bucket_marginals` (`diagnosis/probe_hypotheses.py:94-133`).

**Why this can lower or raise an item's EIG.** Integrating the residual inside each hypothesis computes EIG on the outcome distributions the learner will actually face, not on an idealized item. It also stops the acquisition rewarding information about an expendable item rather than the learner (worker b). This usually lowers an uncertain item's EIG, but not always: near saturation, noise can separate predictions. The test is agreement with a brute-force marginalized EIG, not monotonicity (G-AD5-2).

**Probe authoring targets discrimination, not difficulty.**
- The probe prompt's band instruction (`practice_generation.py:1984`) and the probe success band (`schema.py:399`) are retired under the AD5 successor.
- For capability hypotheses, the probe generator receives the feature point of `X_c` (§6.1) that maximizes the hypothesis EIG of the binary success event under the composed `q_h(x)` (with `z = 0`). For misconceptions it receives the discrimination-profile target.
- An item whose conditionals are identical across hypotheses already scores zero EIG whatever its difficulty (`probe_families.py:476-478`). AD5 keeps that rule and stops paying to author such items.

### 6.4 What is not AD's job

- **Block choice** stays with the router (staged rule, Decider, LLM, mixture; `router/mixture.py`).
- **Review timing of already-attempted items** stays with FSRS and the scheduler. AD does not reorder due reviews.
- **Repair after a diagnosis** stays with the diagnosis track, including the follow-ups it places and authors. The repair lane holds follow-ups and already-attempted items, never a new-material slot (`daily_plan/lanes.py:9-18`). A never-attempted item on a diagnosed LO is in the new lane, so AD's serve draw covers it as it covers any slot.
- **Selection-reward bands for due items** (`selection_rewards.py:516-526`) are unchanged.

---

## 7. Generation at a feature point

### 7.1 The contract to the generator (AD2/AD3 successor; switch `generation_contract`)

- The commissioned `RungTarget` carries `capability = k`, `task_features = x`, and `task_feature_bounds` with `max = x` on every dimension. The existing deterministic gate already rejects overshoot (`depth_rungs.py:204-208` point bounds; `validate_item_against_rung`, `:538-544`).
- The prompt **drops** every band instruction: `practice_generation.py:1062`, `:1919`, and the band clause of `:1922`. The waypoint clause ("NEVER change the waypoint") stays.
- It also drops the `recommended_difficulty_band` field from the target payload, and the band check `_check_difficulty_band` (`:1501-1537`).
- In their place: "Write the item so that it has exactly these features. Do not make it easier or harder than these features imply; difficulty is measured from the learner's answers. Separately, give your estimate `difficulty` in [0,1] of how hard this item is for a typical learner studying this topic. It is recorded as one weighted signal whose weight is learned from this learner's answers; it is not the item's difficulty."
- `difficulty_source = "llm_estimate"` stays on the item for the incumbent. Under AD it is only the signal `z_llm`.

### 7.2 Feature audit (AD1; switch `feature_audit`)

- After any item is generated or imported, one Tier-1-style Decider judgment per audited dimension (`complexity`, `transfer`, `scaffolding`, `span`, `response`) reads the item stem and reference answer only. It is never shown learner data or held-out text.
  - It answers a typed `ChoiceQuestion` over that dimension's vocabulary.
  - Argmax decides; a tie is no answer; the distribution is logged in `judgment_ledger` (task `ad_feature_audit`, version `ad-feature-audit-v1`), exactly as `decider_judgments.py:1-25` does.
  - Each judgment records the `content_hash` of the item revision it read (`practice_item_snapshots`, `migrations/164_item_snapshots_and_adjudication_fk.sql`). An edited item is a new revision and gets its own audit.
  - **The canonical audit** of a revision, per dimension and audit version, is the earliest judgment that answered. A later run of the same version never replaces it; a new audit version is a change of persisted meaning (§7.5).
  - On Decider failure, the existing LLM fallback runs and is recorded as such.
- **Backfill at AD1.** One owner-run pass, dry-run first and under the spend cap, audits every active item's current revision and every answered revision held in `practice_item_snapshots`. Without it, every existing item not already known below entry would stay "level pending" (§9.2) indefinitely.
- **Uses of the audited tuple `x̂_i`:**
  - AD's likelihood and predictions use `x̂_i` where the audit had answered *before the decision*, else the stamped `x_i`, as frozen at serve time (§7.5).
  - **Level credit (§9.2) uses the easier of `x_i` and `x̂_i` on every dimension**, from the answered revision and its canonical audit. An overclaimed feature can never raise a level.
  - The audit agreement rate per dimension is reported. Persistent disagreement is a generator finding, not a learner one.

### 7.3 Item-side signals and the offset prior

`z_i` is assembled from persisted values only, and **frozen per decision**:
- a selection or receipt uses exactly the signals whose `received_at` precedes it;
- an attempt's update uses the signals frozen at that attempt's serve time;
- the vector, each signal's receipt id and availability, and the `z_v1` recalibration version are written to the serve-input receipt (§7.5) and, for AD draws, to the `ad_selections` row. `ad_attempt_trace` repeats them for reading, but it is DERIVED and is not what freezes them.

A signal that arrives later is used only by later decisions and updates. It never changes an earlier state, selection or score. Together with the frozen features of §7.5, this is what lets replay reproduce history.

The signals:

| Signal | Value | Present when |
|---|---|---|
| `z_llm` | `2.5·(2d − 1)` from the item's own `difficulty` (the existing map, `mastery.py:377`) | `difficulty_source = "llm_estimate"` |
| `z_panel` | `logit(s_parent) − logit(s_item)`: the panel's relative offset, smoothed as in `pf_generation.py:190-197` | `difficulty_source = "solver_panel"` with the panel rates recorded |
| `z_v1` | `−logit(p_v1)`, where `p_v1` is an item-only LLM forecast of "probability a typical learner studying this topic answers correctly" (field V1 variant, no learner data), recalibrated on past items only. The sign makes it a difficulty, like the other signals | the item-scoped receipt, prepared with the pool before any serve (§8.1–8.2), was received before the serve |
| `z_origin` | 1 for generated items, 0 for canonical (textbook or problem-set) exercises (`PracticeItem.canonical_exercise`) | always |

`δ_i = α·z_i + ε_i`.

- The weights `α` are latent and shared (§5.5). Trust in each source is learned, and a useless source's weight shrinks toward 0 with no rule change. Whether a signal earns its place is judged first on field's first-attempt split, the forecasts on never-seen items that generation needs (§8.3, D17).
- A missing signal contributes 0.
- Because the regression sits beside the features `β`, it captures what a signal says *beyond* the item's features.

### 7.4 Re-forecast and the serve decision

- When a commissioned item lands, AD computes its own `p̄(i)` with its audited features and `z_i`.
  - If `p̄(i) ∈ [0.55, 0.90]`, it joins the cell's pool and is eligible.
  - If not, it still joins the pool (it may suit the learner later) but is not served for this commission.
  - Either way, an `ad_commission_results` receipt is appended, linked to the commission's `ad_selections` row. It records the item, `p̄(i)`, and in band or `realized_out_of_band`. The selection row is never mutated; the combined status is derived.
  - *Recorded (AD2+AD3, Codex verify F15):* landings are reconciled for every commission without a receipt, open, expired or superseded, at each fresh-item serve. An item belongs to the commission that was its cell's latest when it landed (drawn at or before it, with no later commission for the cell drawn before it), so no item is attributed twice. An item that landed after its commission expired is marked `landed_after_expiry`; the report counts it. *Round 6 (verify F15, F16):* ownership is by cell and order only, never by feature match: every active item that lands in a commissioned cell is owned by the cell's latest commission at its landing, and the receipt records the item's realized features and their re-forecast, with `features_match` saying whether they are the requested point. Draws are totally ordered by `(created_at, rowid)` (timestamps carry whole seconds); `UNIQUE(practice_item_id)` keeps one owner per item, and an item that already has a receipt is skipped, so the first attribution is final. *Round 7 (verify F17, F18):* reconciliation asks the held-out predicate (A8, `adaptive_difficulty.protection`) once and never reads a protected item: no ownership, forecast or receipt, so it never closes or supersedes a commission; with the predicate unavailable nothing is reconciled and the commissions stay open. `features_match` compares the same resolved (audited) mapping the receipt records and the re-forecast reads. The same predicate keeps protected items out of generation targeting (the LO's commissioned facet), the relatedness proposal's facet list, the readiness cells and router card fields, and the report's field comparators.
- The realized miss rate per feature point is a generator-quality metric. If it stays above 40% after AD2, generating several candidates per commission becomes the trigger in §16.
- A commissioned item's re-forecast is a forecast on a never-seen item, so it is scored first on field's first-attempt split (§8.3, D17).

### 7.5 Frozen serve inputs and historical attempts (AD1; switch `forecast_receipts`)

The features and signals an AD decision or update reads are fixed when the item is served. A later audit, re-audit, recalibration or item edit never rewrites them.

- **`item_serve_inputs`** (RECEIPT, append-only). One row per presentation of a never-attempted item, written in the serve transaction beside the in-process forecast receipts (§8.1). It holds:
  - the presentation reference and `practice_item_id`;
  - the served revision's `content_hash`, also written to `practice_item_snapshots` with `INSERT OR IGNORE` (migration 164);
  - the stamped tuple `x_i`; per audited dimension, the `judgment_ledger` id that had answered before the serve, or null; the resolved tuple AD reads (audit where answered, else stamped);
  - the signal vector `z_i` with each signal's receipt id and availability, and the `z_v1` recalibration version (§7.3);
  - `pre_exposed` (§5.3) and the resolution version `ad_feature_resolution_v1`;
  - from the AD2/AD3 successor on, the item revision's loadings in force at the serve (§5.10): each `judgment_ledger` id and value, and the coupling version.
- **Replay reads the receipt.** The update for an attempt uses exactly the row of the presentation it is bound to (the chain of §8.3).
- **Historical attempts** have no row: they predate AD1 or have no bound presentation. `ad_feature_resolution_v1` resolves them as of the attempt:
  - the answered revision follows the field's graded-revision rule (`spec_learner_field_v1.md` §3, "Historical revisions"; resolver `field/outcomes.py:154-233`): `exact` when the graded revision is found and matches; `reconstructed_current` only under `field.legacy_fallback = "current_content"`; otherwise `excluded`. Current content is never silently used;
    - **Owner decision 2026-10-19** (`docs/reviews/adaptive-difficulty-ad23.md` open question 4): "History fallback. AD reads historical attempts through the current-content fallback by default, so the owner's vaults start with usable history. First check what `field.legacy_fallback` controls beyond AD. If it affects anything outside AD (the field harness or other projections), DON'T change the field default. Add an AD-scoped setting, e.g. `adaptive_difficulty.history_fallback = "current_content"`, that AD's replay reads, and leave the field's default unchanged. Classify the new key in the parameter registry. Record what it means: historical attempts are read against today's item text where the exact revision wasn't saved." *Recorded (AD2+AD3):* `field.legacy_fallback` also drives the field harness (`learnloop field`, `success-head`, `eval`) and field's DERIVED facet-outcome view, so its default stays `"exclude"`. AD's replay and its report's comparators pass AD's own `adaptive_difficulty.history_fallback` (default `"current_content"`) to the same resolver: a historical attempt whose exact revision was not saved is read against today's item text (`reconstructed_current`); `"exclude"` leaves it out. The choice is explicit, in the config and in each attempt's resolution status, so current content is still never used silently;
  - from that revision: its stamped tuple, and its own `difficulty` for `z_llm`;
  - audits with `created_at` before the attempt (none exist before AD1), and no receipt-based signals.

  An attempt served before its subject's first coupling version was adopted (every historical attempt, and every receipt written during AD1) takes the loadings of the adopted version for its answered revision (§5.10, "As of").

  Each trace row carries `input_status` (`frozen`, `exact`, `reconstructed_current` or `excluded`). `excluded` attempts do not update the state. The AD report counts each status.
- **Reinterpretation is explicit.** Reading history with a new audit version, a new signal or a new resolution rule changes persisted meaning. It is a new `ad_feature_resolution` version, applied through the playbook with a shadow-rebuild report (§11.1), never a silent difference between two rebuilds.
- **Level credit reads differently, on purpose.** Certification describes the content the learner answered, not a decision taken before it. So an observation's level (§9.2) uses its answered revision and that revision's **canonical** audit (§7.2), whenever the audit landed. Until it lands, the readings already available bound the level from above. An observation whose stamped tuple is already below the entry point is level 0 for good. Any other is "level pending" and counts toward `e_k` only. The canonical audit is fixed once it exists, so the level resolves once and never changes after. An observation whose answered revision is `excluded` has no reading at all, and counts toward `e_k` only for good.

---

## 8. Forecasts: logging, scoring, trust

### 8.1 Receipts (AD1; switch `forecast_receipts`)

*Amended at AD1 (2026-10-18; `docs/reviews/adaptive-difficulty-ad1.md`):* `item_forecasts` is not a table of its own. Item forecasts are rows of kind `item_unassisted_success` in the `forecast_receipts` receipt family (migration 206, built for this by the saved-diagnosis-forecasts stage; owner-confirmed item 3 of `docs/reviews/diagnosis-forecast-receipts.md`): `scope` `presentation` (binding `plan_presentation`) or `item` (binding `first_presentation`, with `item_content_hash`), `created_at` as `issued_at`, `p` and optional `p_categories` in `forecast_json`, `received_at`, `status` and `algorithm_version` as below. Below, `item_forecasts` names these rows.

`item_forecasts` (RECEIPT, append-only), one row per (presentation, forecaster), or per (item revision, forecaster) for an item-only forecaster:
- **`scope`:** `presentation` or `item`;
- **presentation reference** (scope `presentation`): `plan_presentation_id`, `probe_presentation_id`, `scheduler_candidate_id`, or an exam session's pooled item (written when `start_exam` freezes its predictions, `goals/exam_session.py:1-12`);
- **item revision** (scope `item`): the revision's `content_hash`. An item-only forecast reads no learner data, so it is made once per revision, when the item is prepared for the pool, and never per presentation (§8.2);
- `practice_item_id`;
- `forecaster` and `forecaster_version` (hash of code, priors and config);
- `event = "unassisted_success"`;
- `p` and optional `p_categories`;
- `inputs_hash` and `inputs_as_of` (the snapshot the forecaster read);
- `issued_at`, `received_at`, `status` (`ok | failed | refused_spend`);
- `algorithm_version`.

**Validity rule.** A forecast is valid iff `inputs_as_of ≤ served_at`, whenever it arrives. So outside forecasters never sit on the critical path, and a late answer is still a true forecast *for scoring*. Whether it can also *inform* a decision is a separate rule: only a receipt received before the serve enters that serve's frozen inputs (§7.3, §7.5). An item-scoped receipt is scored against the item's first bound presentation. In-process forecasters (AD, the incumbent, `lo_general`) write their rows in the serve transaction, beside `plan_presentations` (plan R2 §5.2). Raw responses from paid forecasters go to `item_forecast_payloads` (WORKFLOW, pruned like `router_decision_payloads`); the receipt keeps the hash.

*Amended at the AD1 Codex review (2026-10-18; `docs/reviews/adaptive-difficulty-ad1-codex-review.md`, F2, F3, F8):* `inputs_as_of` is true only if the inputs are the ones the serve had. So the `llm_v3:*` request inputs (the served revision's item view and the history card with each earlier grade as it then stood) are frozen in the serve transaction, as an `item_forecast_payloads` request row, and the background job sends exactly those; a presentation without them (served while the forecasters were off, or whose first recording failed) is never forecast, and a reopened step's serve records nothing new. Every accepted outside forecast also appends one `judgment_ledger` row (task `ad_item_forecast`: model, prompt version, request hash, the receipt key), in its receipt's transaction.

### 8.2 Forecasters

| Forecaster | Reads | When on | Role |
|---|---|---|---|
| `ad_threshold@subject`, `ad_threshold@subject_uniform` and `ad_threshold@lo` (and sub-arms) | the AD state (§5): the subject view; the subject view restricted to its uniform-sharing points (`χ_C = χ_Q = 0`, renormalized, §5.10); the LO view (§5.6) | the AD2/AD3 successor onward, computed in-process at serve time | `@subject` drives practice selection and the readiness numbers with `promoted_predictor` on; `@lo` drives selection with it off (§6.1). The other two are scored as the comparators of §10.4: uniform sharing and topic-only |
| `mastery_ekf` (incumbent) | `resolve_item_irt_params` and the EKF | AD1 onward | Incumbent |
| `lo_general+composite` | field §4.3 | AD1 onward | Challenger |
| `solver_panel` | `difficulty_source = solver_panel` items: panel rate mapped through the item's `b` at the learner's incumbent ability | when present | Item-side signal and scored forecaster |
| `llm_v1:item` | item stem, LO and facet names (field V1) | AD1, switch `outside_forecasters`. Run once per item revision when it is prepared for the pool (after authoring or import and its feature audit, as a background job), and once as a backfill over the never-attempted items that exist at AD1. Never at presentation | Item-side signal `z_v1` after recalibration, which enters a serve only when received before it (§7.3); scored at the item's first presentation |
| `llm_v3:llm`, `llm_v3:decider` | field V3: item plus a `LearnerStateCardV1`-style card restricted to the LO and its prerequisites, plus similar past items with outcomes; Decider as a `noul` question | AD1, switch `outside_forecasters` (D4) | **Competing experts** (§8.4). Never an offset prior |

### 8.3 Scoring

- `item_forecast_scores` (DERIVED, one replayer) joins each valid receipt to its bound attempt through the exact chain `plan_presentations` → `practice_attempts.plan_presentation_id` (plan R2 §5.2). Unbound attempts fall back to the scheduler candidate, then the probe presentation; R1's session rule is never used.
- The outcome is the §5.3 event, read exactly as the update reads it.
  - Pending outcomes, and skipped or abandoned presentations, are right-censored, never failures.
  - Presentations with `pre_exposed = true` are not scored.
  - Any help, or a reveal during the presentation, makes the binary event 0.
- **Metrics per forecaster:**
  - log loss and Brier on the binary event;
  - ranked probability score on categories where given, over attempts whose category is fully observed (censored `{0, 1}` attempts are skipped);
  - the skip rate per forecast decile (§5.3);
  - reliability by decile and in the band region `[0.6, 0.9]`;
  - splits: field's first-attempt split (below), first surface in a never-seen cell vs later, capability, coldness, serving origin.
- **The primary split (owner direction 2026-10-14; D17).** Every presentation AD scores is a never-seen item, the first on its surface (§5.6). Field's first-attempt split (the first attempt on a never-seen LO, field §7.2) isolates the forecasts that rest only on shared terms and item-side information. Those are the forecasts generation needs. It is the primary score:
  - for the monitoring of the subject view and its auto-flags (§10.4);
  - for item-side signals: the weights `α` and each `z` signal (§7.3), the `+outside` arm, and the `llm_v1:item` and `solver_panel` forecasters;
  - for commissioned items' re-forecasts (§7.4).

  AD's never-seen-cell split is reported beside it, then all presentations.
- **Comparisons** between any two forecasters on the same presentations use anytime-valid confidence sequences on the score difference `[choe2023]`, so continuous monitoring is honest.
- **Planning illustration** (worker f; iid, not a guarantee): detecting a mean Brier advantage of 0.01 with score-difference sd 0.10 at 80% power needs about 784 outcomes. At n=1, comparisons resolve slowly by nature, which is one reason they monitor rather than gate (D3).

### 8.4 Learning trust

- **Item-side signals** earn trust through `α` inside the model (§7.3). This is Bayesian, so no separate weighting exists.
- **Learner-conditioned forecasters** (`llm_v3:*`, `lo_general`, `mastery_ekf`, `ad_threshold`) are combined in a DERIVED, reporting-only ensemble:
  - fixed-share exponential weights on Brier loss `[herbster1998]`, with learning rate 2 and share 0.05 (a priori);
  - chronological stacking `[yao2018]` as a second report.
- **The ensemble is never served** in this spec. Serving it would be a further successor, with its own trigger (§16).
- **What "trust" decides:**
  - nothing in serving by itself. The scores feed the AD report, the glass box and the auto-flags of §10.4, which recommend a switch to the owner. The subject view drives live decisions and readiness numbers from the AD2/AD3 successor on (D3);
  - whether the router's card shows an outside forecast (router §10, item 1).

---

## 9. Levels, certification and full mastery

**What certification reads: features, never an estimated difficulty (A11; owner direction 2026-10-14, D16).**
- Every input to a level, a requirement, a credit row, a certificate or the cold probe's item choice is a **feature point**: an answered revision's stamped tuple, its canonical audit (§7.2), or a point written in a target or requirement (§9.1, §9.4, §9.5). Where a stamped and an audited reading differ, the more conservative (easier) one counts (§9.2).
- No estimated difficulty enters, ever. That covers AD's posterior and its feature effects `β`, the signal weights `α` and every `z` signal (§7.3), the item's `difficulty` label and `difficulty_source`, solver-panel rates, empirical-Bayes `b` (`learner/mastery.py:400-447`) and `resolve_item_irt_params` (`:381-397`).
- An estimate may be wrong in a way one learner's answers cannot reveal (§5.8). A demonstration must not inherit that error.
- The rule holds with every AD switch on or off. G-AD4-13 tests it, and an import-linter contract forbids the certification and feature-credit code from importing AD's state or the IRT seam (§11.3).

### 9.1 Ladders: one per (target, capability), immutable (`ad_ladder_v1`, deterministic)

- **Ordered dimensions:** `scaffolding` (worked < partial < cue < none), `transfer`, `complexity`, `span`, response class (recognize < constructed < performance), `tools` (open < closed).
- **Entry point `e_k`:** the default-trajectory waypoint for capability `k` (`depth_rungs.py:101-122`). `coordination` has no entry without a reviewed envelope. It depends on `k` only, never on a goal.
- **A ladder instance** `L(k, t)` is a deterministic function of the capability `k` (so its entry `e_k`), a target point `t`, the feature schema (`p1_launch@1`) and the ladder version.
  - Its id is the hash of those four. Where the target came from (an exam profile hash, a milestone, the default) is recorded beside it for display and the glass box.
  - Instances are immutable. A new target makes a new instance; it never edits an old one.
- **Which target, per goal and cell.** A goal `g` reads, for a cell `c` in its scope, the target `t_{g,c}`, in order of precedence:
  1. the cell's exam/pset target (§9.5). It is the same for every goal: goals do not reference source sets yet (§16);
  2. else the goal's milestone target: the next reviewed milestone contract of the commitment that carries the goal (`goal_id` on the commitment head, `curriculum/commitments.py:186`; projected as in `depth_rungs.py:353-410`, `RungTarget.source = "milestone_edge"`). With several such commitments, the hardest point per dimension;
  3. else the **default target**: `e_k` stepped one level up in `complexity` and in `transfer`, bounded by the default trajectory. It depends on `k` only, so a cell outside every goal, or a goal with neither of the above, reads the **default ladder** of `k`.

  Any dimension where the target is easier than `e_k` is raised to `e_k`.
- **Walk:** from `e_k` to `t`, raising one dimension one level per rung in the fixed order above, cycling until every dimension reaches `t`. Rung 1 is `e_k`; rung `K` is `t`. Rung `r` of `L` is a feature point `L[r]`.
- **"Level k of K" always names a ladder instance.** Two goals sharing a cell can show different `K` and different levels. Both read the same evidence (§9.3), and neither changes it.

### 9.2 An observation's conservative tuple and its level on a ladder

- An observation's **conservative tuple** is the easier, per dimension, of the stamped features of the revision the learner answered and that revision's canonical audit (§7.2, §7.5).
- **Every reading is an upper bound.** The conservative tuple takes the easier reading on each dimension. So each reading available now bounds it from above: the stamped tuple, and each audited dimension whose canonical audit has answered. A reading that arrives later can only lower it. The observation's **bound** `u` is the easier, per dimension, of the readings available now.
- **Known below entry: level 0.** If `u` is easier than `e_k` on any ordered dimension, the observation has level 0 on every ladder. That holds now and after any audit, whether the audit is pending, has failed or has tied. Example: a retrieval item stamped `scaffolding = worked` is below retrieval's entry `cue`, whatever its audit will say.
- **Complete: its level.** When the stamped tuple exists and the canonical audit has answered on every audited dimension, `u` is the conservative tuple. Its **level on ladder `L`** is the largest `r` such that it is at least as hard as `L[r]` on every ordered dimension. Below rung 1 it has level 0.
- **Incomplete, and not known below entry: level 1 at most.** This is the legacy fallback, and it applies only where feature information is genuinely missing:
  - the audit is pending, or has failed or tied on some dimension (§7.2);
  - the item has no `task_features` (legacy);
  - the answered revision cannot be resolved (`excluded`, §7.5), so it has no reading at all.

  Such an observation gets level 1 if its capability is known (stamped, or `default_capability_for(practice_mode)`), and never more than level 1, on any ladder. It is labelled "level pending" while an audit can still complete it, and "level not rated" otherwise.
- **One resolution.** A level-pending observation resolves once. That happens when its canonical audit completes it, or earlier, when an answered dimension already shows it below entry.
  - Its level may rise. It may also fall to 0, if the audit reads the item below entry.
  - The canonical audit never changes afterwards (§7.2), so neither does the level.
  - Certification is derived on read. A certificate that rested on the provisional entry credit is re-derived, and a cold probe still pending for a certificate the LO no longer holds is handled exactly as today (§9.4).
  - The AD report counts provisional credits, and how many were later withdrawn.
  - Items are audited after generation or import (§7.2), and AD1's backfill covers existing ones, so an audit still pending when an item is answered is the exception.

### 9.3 The feature-qualified credit ledger (AD4 successor; switch `rung_certification`)

- **`facet_capability_feature_credit`** (DERIVED; owned by the replayer that owns `facet_capability_evidence`). One row per `(attempt, facet, capability)`:
  - the certification credit banked for that cell by exactly the existing rules: direct or embedded, unassisted, group budgets, repeat discounts and caps (`capability_mapping.py:246-288`; `canonical_projection.py:920-1030`), with its direct and embedded parts;
  - the observation's conservative tuple, or, while it is incomplete, its bound `u` and its status (pending, legacy or `excluded`, §9.2); the answered revision's `content_hash`; and the canonical audit ids.

  It stores no ladder and no level number, so no target change can rewrite it.
- **Demonstrated at a point.** A cell is *demonstrated at point `p`* when the credit of its observations whose conservative tuple is at least as hard as `p` on every ordered dimension sums to ≥ `DEMONSTRATED_CREDIT` (1.0, `certification.py:3`).
  - This is within-cell dominance, the feature-ladder analogue of capability dominance (measurement spec B1). There is no discount, because the observation dominates on every dimension. The basis is recorded.
  - Each row's credit is what the cell banked, so budgets and discounts computed over the whole cell are never relaxed for a harder subset. The sum is conservative by construction.
  - Embedded credit from capability dominance (B1) counts toward `e_k` only.
  - Incomplete observations (§9.2: an audit pending, failed or tied; legacy; `excluded`) count toward `e_k` only, unless they are known below entry.
  - Level-0 observations count toward no point at or above `e_k`. That includes observations known below entry while their audit is still missing.
- **"Demonstrated up to level k of `L`"** is the largest `k` such that the cell is demonstrated at `L[k]`. It is computed when read, for any ladder instance, and never stored as a bare number.
- **Never from the posterior, never from an estimated difficulty.** No level is ever derived from AD's state (A2), and no credit row, level or requirement reads an estimated `b` (A11, above). The posterior predicts; the ledger demonstrates.

### 9.4 Reconciliation with capability-matched certification

`lo_certification` (`goal_certification.py:275+`) keeps its structure: some recipe with every hard component demonstrated, plus integration evidence. Under AD4:
- **A component is demonstrated** when its `(facet, capability)` is demonstrated at its **requirement point** `p_req`. A requirement is a feature point, never a level number.
  - Default `p_req = e_k`, the entry point (D7). It is the same for every goal.
  - The only change for an LO with no declared requirement is that level-0 observations (heavily scaffolded, below the capability's entry point) stop counting. That is the "trivial item" fix.
- **A declared requirement** may set a harder point (owner decision D7). `p_req` is the hardest point, per dimension, of `e_k` and:
  - an optional `min_task_features` on a blueprint `RecipeComponent` (`vault/models.py:288-293`): a partial `p1_launch@1` tuple whose unspecified dimensions take `e_k`'s value; absent means `e_k`;
  - the next reviewed milestone contract (projected as in §9.1, precedence 2) of every active commitment with a target naming the LO or one of its facets, where the contract's capability is the component's.

  It reads no goal, so `lo_certification` stays a function of the LO, and two goals sharing an LO never see two certification states. Goal-specific targets show as levels of each goal's ladder, never as certification requirements.
- **Certificates bind their requirement points.** Certification is derived on read; there is no durable certificate table. A certificate's id is the content hash of (LO, blueprint, recipe, certified cells), snapshotted onto its cold-probe task and outcome row (`goals/certification_cold_probe.py:46-55`, `:334`). Under AD4 the hashed content also holds, per component, `p_req`, the schema and the ladder version. So:
  - a changed requirement (a revised blueprint, or a commitment moving to its next milestone) yields a new certificate id, never a reinterpreted old one;
  - a cold-probe verdict already recorded keeps the `p_req` of the certificate it judged; a probe still pending for a certificate the LO no longer holds is cancelled or `indeterminate` as `certificate_withdrawn`, exactly as today (`goals/certification_cold_probe.py:1360-1361`, `:1476-1490`);
  - an imported exam or a re-classified unit changes a goal's ladder and its "level k of K" (§9.5), never a requirement: exam targets are not certification requirements (D7).
- **The delayed cold probe** for a certificate is served on an item whose conservative tuple dominates the certificate's recorded `p_req` (`certification_cold_probe.py`). `false_certification_rate` is reported by the level of `p_req` on the default ladder of `k`, which is the same index for every goal, and by capability.
- **Exam pool stratification** moves from LLM-label strata (`exam_pool.py:42-55`) to levels of the exam goal's ladder instance, and records the instance id.
- **Kill switch** `rung_certification = false`: `facet_capability_evidence`, certification and the cold probe are byte-identical to the predecessor (G-AD4-4).
- **Upgrade.** Because a successor can reduce existing certificates on replay (level-0 items stop counting), the upgrade runs the playbook's shadow rebuild on copies and reports every certificate that would change before the version applies (playbook step 7).

### 9.5 Exam and problem-set targets: full mastery (AD4)

**Where target points come from.**
- The exam profile gains `target_feature_points`: per exam or problem-set unit, a `p1_launch@1` feature tuple.
- **Only units whose use mode is `blueprint_only` or `available_for_practice`** (`content/synthesis/source_unit_selection.py:333`) feed it, as router §15.6 requires for anything that steers generation or selection. Their text may be read, so the feature-audit judge classifies each one at ingest.
- Tuples are collapsed one vote per syllabus family (`exam_family_key`, `content/synthesis/exam_profile.py:35-54`).

**Mapping to cells.** A unit's points map to cells only by the unit's own facet mapping, at the unit's capability. A unit without a facet mapping feeds no target in v1. Spreading it over every facet of a goal would let one hard unit raise targets on unrelated facets, and goals do not yet reference the source sets their exams come from (`vault/models.py:136-139` names `source_set_ids` as a future goal field; no goal has it). Unmapped units are counted in the AD report and in `learnloop ad data-check` (Q3); using them at goal scope is deferred (§16).

**The target.** The cell's exam target `t_c` is the per-dimension 0.8-quantile of the cell's family-collapsed points from every practice-available unit (D12). Every goal whose scope holds the cell reads it first (§9.1). A new import or a re-classified unit gives a new `t_c` and so a new ladder instance. Requirements and certificates never read `t_c`, so they are unchanged (§9.4).

**Held-out units are evaluation only** (A8, D14).
- `held_out_evaluation` units are never served and never classified by an AD judge, and they never shape `t_c`, the ladder, selection or generation.
- Where the existing ingest inventory already records feature signals for them (as it records `held_out_task_families`, `exam_profile.py:64`), one evaluation report compares them with the ladder: "share of held-out exam tuples at or below the target level". A low share is an owner-visible finding ("practice aims below the exam") with no automatic action.
- The leakage gate (`content/authoring/practice_leakage.py`) is unchanged.

**Exam-session outcomes.**
- A goal's practice exam (`goals/exam_session.py:1-12`) serves reserved, never-practised pool items and freezes predictions before any answer is graded.
- Under AD, `start_exam` also writes an `item_forecasts` receipt per pooled item (§8.1), so exam-level calibration is scored on the same footing as the incumbent's frozen predictions.
- The answers then apply through the standard attempt pipeline, as today, and AD reads them like any first-surface attempt (§5.6).

**Two labels, never blended,** both per goal and cell, and both naming the ladder instance they read:
- **Full mastery (demonstrated):** the cell is demonstrated at `t_{g,c}`, the top rung of the goal's ladder (§9.3).
- **Ready for exam level (predicted):** `p̄(t_{g,c}) ≥ 0.8`, labelled as a prediction (KM §9.6; `exam_readiness.py:5-12`).
  - It needs a predictor that can predict at a feature point, which the incumbent cannot. It reads the subject view from the AD2/AD3 successor on (D3).
  - With `promoted_predictor` off, the line reads "exam level: not yet predicted". Demonstrated levels (AD4) do not depend on it.
  - **Untested stays untested.** A cell with no eligible answer of its own shows "untested" in place of the prediction, whatever the shared terms, couplings or reading predict (field F4 and §4.3: a region with no direct evidence is untested, whatever the inference says; A4). So sharing, a coupling or reading alone never shows "likely ready".

**Without practice-available exams or problem sets,** the top level is the milestone or default target, and "full mastery" is shown as "top level for this goal".

### 9.6 Ground truth

- The delayed cold probe stays the external check. `false_certification_rate` is reported per requirement level (on the default ladder of `k`, §9.4) and per capability.
- AD2 and AD4 add one metric: the **trivial-success rate**, the share of successes on items whose `p̄ > 0.95` at serve time. It falls when AD works. A high rate before AD is G4 measured.

---

## 10. Integration

### 10.1 Router mixture and exact propensities

- **Order.** The router picks a block with an exact propensity `π_router` (`router/mixture.py`); with the router off, DL1's chooser is deterministic and `π_router = 1`. Later, when a new-material slot of that block is served, AD draws the item with exact propensity `π_AD(i | block, slot, S)` (§6.1). AD never changes how blocks are packed or which candidates the router sees, so `π_router` means exactly what it means today.
- **The joint action.** What is logged is the pair (block, served item), with propensity `π_router(block) · π_AD(i | block, slot, S)`. It is the propensity of that pair, not the marginal probability of the item across blocks. Both factors are logged before exposure, so router R3's doubly-robust replay and an AD replay both have valid importance weights for pair-level policies. They evaluate serving policies *conditional on the pool that existed*. Alternative commissioning policies are not evaluable from these weights (§6.1).
- **Later decisions.** A substitution changes the block's planned minutes, and so the `minutes_left` the router reads at its next decision. That decision logs its own propensity on the state it saw, so the sequential factorization stays exact.
- AD registers its draw as a fifth admissible design, **`feature_overlap`**, in `scheduling/randomization_layer.py:57`. Like `model_mixture`, it declares its own floor (`q/|O|` on the overlap set), and the dormant 0.05 floor never clips it. Outcomes join at the next spaced cold review, as for the other designs (`randomization_layer.py:19-25`). The Reader's dose offers are a sixth, `reading_dose`, with their own floor (§5.12); they are drawn in the Reader, outside any block, so they never enter a pair propensity.
- **The router's card** (`LearnerStateCardV1`) gains, per LO, from the AD2/AD3 successor with `promoted_predictor` on: demonstrated level / K, `P_band` of the next point, and `p̄` at the target, with an "untested" mark on an LO with no eligible answer of its own (§9.5). These are readiness numbers from the subject view, and they steer the router's block choice across LOs. With `promoted_predictor` off, the card carries no AD fields. The card's version moves accordingly (plan R2 §3.6).

### 10.2 Daily-plan lanes

- Under AD2, each **new**-lane slot (`new_admitted`, §6.1) is served by AD's draw over its support, one draw per served slot. A slot whose support is empty is displaced, and its item is deferred from every pool of the day's plans until its blocking condition clears (§6.1, step 0). The exception is a slot whose item only pre-exposure ruled out: the predecessor serves it, with no draw. The lane's packing, order, minutes and admission are the predecessor's (`daily_plan/lanes.py:1-27`); the deferral only removes an item AD could not serve.
- **push** holds already-attempted items on goal frontiers, and **repair** holds follow-ups and already-attempted items. Neither has a new-material slot, so both are untouched (§6.4).
- **maintain** (due reviews and scheduled checks) is untouched.
- **Kill switch** `selection = false`: no draw, no substitution and no deferral; every slot serves its planned item, exactly as the predecessor.

### 10.3 The Decider

- **Feature audit** (§7.2): a Tier-1 judgment pattern on the existing `tier1_decider` route, with a `[decider_routes] ad_feature_audit` switch, live at AD1.
- **Forecaster** `llm_v3:decider` (§8.2): a `noul` question. It is scored only and never served (§8.4).
- **No new authority.** The Decider does not choose feature points or items. Its block-level role in the router is unchanged.

### 10.4 Field harness arms, going live, and monitoring

**Arms** added to `learnloop eval` (field §7.2). The base is scored in three views: `@subject` (the live subject view, §5.6), `@subject_uniform` (its uniform-sharing points, `χ_C = χ_Q = 0`, §5.10) and `@lo` (topic-only). The `@subject:` arms exist only in the subject view; the other arms are scored in the subject view and the LO view:
- `ad_threshold` (base);
- `ad_threshold@subject:noread`: the subject view with reading opportunities off (§5.11);
- `ad_threshold@subject:hyper_fixed`: the subject view at each single grid point, without learning `ξ`. Its uncoupled points at `σ_G² = 0.75` and `2.25` are the former split arms (`split_field`, `split_shared`). It shows what learning the hyperparameters buys over guessing them;
- `ad_threshold@subject:hyper_fine`: a finer grid (`σ_G²` in steps of 0.375, `χ_C` and `χ_Q` in steps of 0.125, same caps);
- `ad_threshold+rating` and `ad_threshold+timing`;
- `ad_threshold+outside` (adds `z_v1`; `z_llm`, `z_panel` and `z_origin` are in the base);
- `ad_threshold:grid` (QUEST+-exact grid for `θ_c` with shared parameters at their posterior means, to expose non-Gaussian error near the ceiling);
- `ad_threshold:ts` (Thompson-sampled selection, for the decision-level simulation only).

Field's own arms are the external comparators: `mastery_ekf` (the incumbent) and `lo_general` (uniform sharing, `field/predictors.py:510`). The harness replays history with the relatedness proposal current at the run. The proposal reads no learner data, so using it on past rows leaks nothing (§5.10).

Each arm's constants, and the thresholds of G-AD2-18, G-AD3-7 and G-AD3-11, are pre-registered in `docs/reviews/adaptive-difficulty-ad23.md` before the first replay on owner data, as T8 did (`field/success_head.py:14-15`).

**Going live: AD2 and AD3 together (owner direction 2026-10-14 and 2026-10-15; D3).** Practice selection and the subject view wait for no harness result. The AD2/AD3 successor serves `ad_threshold@subject` (§6.1) with the a-priori priors of §5.5 once two things hold:
- its gate passes (§14), including the simulations' decision-level checks (R8):
  - G-AD2-18: AD-selected practice lands in the band at least as often as the incumbent's waypoint choice, with a trivial-success rate no worse, and band mode engages within the time-to-usable target (§5.9);
  - G-AD3-7: on synthetic vaults with known structure, related topics adapt faster and unrelated ones are not dragged;
- the owner has read the AD2/AD3 report on a backup copy.

Its kill switches and the monitoring below guard it from then on.

**Monitoring and auto-flags (formerly the promotion rule).** Every report computes the harness's own rule (field §7.4) as written, as a monitor and never as a precondition:
- for `ad_threshold@subject` against `mastery_ekf`, against `@lo` (topic-only) and against `@subject_uniform` (uniform sharing): report 1's attempt-level log loss overall *and* on field's first-attempt split (the first attempt on a never-seen LO, the primary split, §8.3); the bootstrap interval at the margin fixed before the run (field D9); report 2's fast-track miss rate, recomputed with AD as the predictor;
- this spec's additions: a first-surface-in-a-never-seen-*cell* split (a new cell can belong to a seen LO), and the band-region reliability error.

Each first-attempt comparison also runs as an anytime-valid confidence sequence on the log-loss difference `[choe2023]`, so watching it continuously is honest.

**The honest line.** The AD report and the glass box say in plain words whether sharing is beating topic-only for this learner and vault: "helping", "hurting" or "can't tell yet", with the number of first attempts behind it. They say the same for the learned coupling against uniform sharing, and for reading against no reading.

**The dose-and-burden analysis (owner 2026-10-15; D20, D21).** The owner's goal: learn which active-reading practices best improve *cold retrieval*, and how much of each, while keeping friction and burden low. Every report has a section for it (`ad_dose_report_v1`), computed from the fitted reading curves of §5.11 and the randomized offers of §5.12. It is computed offline from the reading-on fit whatever `reading_opportunities` is set to, and it makes no model call.
- **Per kind, the gain per event.** For each of the four kinds, the gain in cold-retrieval success from one more event: the next step of its curve at dose 0 and at the learner's median dose. It is read at warmth 0 (the lasting part, §5.11), in points of unassisted success at the band's centre (75%), with a 90% interval from the posterior.
- **Per kind, the gain per minute.**
  - **Minutes per event** come from timing LearnLoop already records. A non-negative regression of each Reader visit's active minutes (`reader/reader_report.py:238-240`) on that visit's count of each kind, plus a constant for reading with no event, gives each kind's minutes per event; its interval is bootstrapped over visits.
  - **The practice reference row.** One more practice question on the same LOs: `γ`'s gain per opportunity, over the learner's answer minutes (`latency_seconds`, or the plan's estimate, `daily_plan/estimates.py:1-18`).
  - **Minutes stay in the report.** These timings are salience magnitudes, so they never enter the state, a dose, a draw or an offer (A12). That is why the recommendation below never acts by itself.
  - Events with no timing count toward the per-event figures only, and the report says how many there were.
- **The dose-response curve.** Each kind's `g_κ(n)` for `n = 0…10` events in a window, with its band. Then the **useful dose** `n*_κ`: the largest dose whose own event still adds at least the practice reference's gain per minute, by the posterior median, with an 80% interval. That threshold is stated, versioned and learned from the same state, not a constant: past `n*_κ`, another practice question would buy more cold retrieval per minute.
- **Two estimates, kept apart.**
  - The model's curves use every observation and are confounded by struggle (§5.8).
  - The randomized offers give the offer's effect and the dose-moderated effect of one more, unbiased but slow (§5.12).
  - Where both exist, the report shows them side by side and says whether they agree in sign.
- **"Helps when".** Moderators fixed in advance: the predicted level band at the event (below 50%, 50–80%, above 80%; expertise reversal `[kalyuga2003]`), a tutor exchange's answer mode, an in-passage question's style. A line appears only when a moderated contrast's interval excludes 0. It is labelled "tested by randomized offers" when the offers support it and "what preceded better recall for you" otherwise, never "what works".
- **Burden.** Per kind: minutes per event; for the offers, taken, dismissed and not delivered, per offer; and any cue-density change the learner made within a visit after an offer.
- **The plain recommendation.** One line per kind, from fixed templates over the fitted curves, with no model call. For example:
  - "Worked examples: about 2 per section before practice helped your later recall most per minute (tested by randomized offers)."
  - "Questions while reading: about 1 per section (what preceded better recall for you; not yet tested)."
  - "Tutor exchanges while reading helped when your predicted chance on the topic was below 50% (what preceded better recall for you)."

  "Per section" reads the window of §5.11: the dose on a topic before the learner next answers on it. A line reads "can't tell yet" when `n*_κ`'s interval spans more than 2 events or its minutes are unknown. The Reader shows these lines in the glass box ("What helps you", §12). The owner may adopt a useful dose as the dose arm's base policy (D21); nothing adopts it by itself.

The analysis is reported per vault, beside the AD report's other sections, and the glass box shows the learner's own lines.

**Auto-flags.** Each appears at the top of the report and in the glass box, with the switch it recommends:

| Flag | Fires when | Recommends |
|---|---|---|
| Sharing worse than topic-only | `@subject` is worse than `@lo` on first attempts at never-seen LOs, the confidence sequence excluding 0 | `promoted_predictor = false` |
| Coupling worse than uniform sharing | `@subject` is worse than `@subject_uniform` on first attempts at never-seen LOs, the confidence sequence excluding 0 | `learned_coupling = false` |
| Reading worse than no reading | `@subject` is worse than `@subject:noread` on first attempts after reading (§5.11), the confidence sequence excluding 0 | `reading_opportunities = false` |
| Verdicts worse than no verdicts | `@subject` is worse than `@subject:noverdict` on first attempts after a self-check verdict (§5.11, D22), the confidence sequence excluding 0 | `reading_self_check = false` |
| Readiness miscalibrated | the band-region reliability error of `@subject` exceeds 0.05 in two consecutive reports (a report is a window of 200 AD selections, recomputed from the prequential records; no report history is stored; owner decision 2026-10-19, below) | `promoted_predictor = false` |
| Band missed | realized success on AD-selected practice outside 0.60–0.88 over 200 selections | `selection = false` |
| Dose offers a burden | of the last 30 delivered extra offers (§5.12), at least 80% dismissed; or the learner lowered the cue density within a visit after an offer, three times in 14 days | `reading_dose_offers = false` |

**Owner decision 2026-10-19** (`docs/reviews/adaptive-difficulty-ad23-codex-review.md` open question 1, F8): "Readiness's "two consecutive reports" uses deterministic report windows (one per 200 AD selections), with no history table. Accepted as built; just record the decision." *Follow-up for a Reader stage:* the burden flag's density lowerings are matched to an offer's visit by time, because `cue_density_changed` events carry no `visit_id`; the Reader should send the visit with the preference change.

The owner flips a switch; code never edits the vault config. Each switch restores its predecessor exactly (§11.1).

**What `promoted_predictor` governs.** The switch keeps its name, though nothing is promoted any more:
- **(i) Readiness numbers.** The predictor whose numbers the learner sees as readiness: "Ready for exam level" and "likely ready" (§9.5, §12), and the router card's AD fields (§10.1).
- **(ii) The subject view in live decisions.** Practice and commission draws read the subject view instead of the LO view (§6.1), and so does AD5's probe composition (§6.3). That brings cross-LO sharing, the learned relatedness (§5.10) and reading (§5.11).

It never turns practice targeting on or off. Off restores the LO view and no AD readiness numbers, exactly. `learned_coupling` and `reading_opportunities` switch their parts of the subject view off, each exactly (§5.10, §5.11).

**Live monitoring (from the AD2/AD3 successor):**
- realized success on AD-selected practice (target 0.70–0.80);
- time to a usable estimate: answered questions per subject (and per LO with `promoted_predictor` off) until band mode engages, and the band-mode share of draws (§5.9);
- own answers each never-seen LO needed before band mode, split by whether it is coupled to a practised LO;
- delayed cold success (`R_cold`, router §15.2);
- `false_certification_rate`;
- minutes per demonstrated level;
- the dose arm: eligible sections, draws by variant, offers delivered, taken and dismissed, and matured cold outcomes per variant (§5.12).

These, the monitoring above and the dose-and-burden analysis are reported every 200 AD selections (`learnloop ad report`).

### 10.5 Probes, value of information and EVSI

§6.3. VOI stopping (mvp-0.21) and EVSI calibration (`evsi_calibration/`) are unchanged. AD5 changes only the conditionals they read and what is authored.

### 10.6 Exam protection

A8, §9.5. A test plants a sentinel string in a held-out unit. It asserts the sentinel reaches no AD prompt, receipt, payload, `ad_selections` row, audit input or `target_feature_points` entry, and that held-out units never change `t_c` (G-AD1-6, G-AD4-6).

### 10.7 Placement and "assumed known"

- **Placement is unchanged** (field §5.2): its sources (self-report, fast-track on early answers, an activated predictor, the quick check), and the first-review check that confirms an assumption.
  - That check stays in the maintain lane, whatever the item's attempt history (`daily_plan/lanes.py:6-8`), with placement's own item choice. This keeps §10.2's "maintain untouched" true.
  - Letting AD choose the check item at level ≥ 1, so that "assumed known" is checked at a level, is deferred (§16).
- **"Too easy / too hard" and "easier / harder" taps keep their existing effects** (D8). They happen after feedback, so they fail the rating contract (§5.4, a pre-feedback tap), and AD does not read them in v1. A separate post-feedback observation model is deferred (§16).

---

## 11. Replay, versioning, persistence

### 11.1 Successors and switches

| Phase | Successor? | Switch(es) under `[adaptive_difficulty]` (false = predecessor exactly) |
|---|---|---|
| AD1 measure and log (starts after the diagnosis-input-provenance stage lands, D18) | **No.** It adds receipts (forecasts, frozen serve inputs and reading opportunities), two nullable attempt columns (rating, first-hint progress) and audit judgments, but changes no persisted meaning and nothing served | `forecast_receipts`, `outside_forecasters`, `rating_tap`, `feature_audit` (Decider switch `ad_feature_audit`) |
| AD2 practice in the band | **Yes: one successor shared with AD3** (the next free tag at their joint merge). The offline harness and the `ad_threshold` receipts change nothing served; serve and commission draws, substitutions, deferrals and the generation contract do | `selection` (off: no draw, no substitution, no deferral), `generation_contract` (off: today's prompt and band check); receipts under `forecast_receipts` (shared with AD1) |
| AD3 the subject view live | **Yes: the same successor as AD2**, merged and live with it, waiting for no harness result (D3). The subject view steers live draws, AD5's composition and the readiness numbers from the tag | `promoted_predictor` (off: the LO view and no AD readiness numbers, exactly); `learned_coupling` (off: the subject view at its uniform-sharing points, with the split still learned, and no proposal calls, exactly); `reading_opportunities` (off: the subject view without reading transitions, exactly). Built in the same stage, outside the successor: `reading_dose_offers` (off: today's Reader exactly, with no draw, offer or row; §5.12) |
| AD4 levels and full mastery | **Yes** | `rung_certification` |
| AD5 probes that discriminate | **Yes** | `probe_targeting` |

- **One successor, six switches.** AD2 and AD3 are one algorithm successor with one tag, one upgrade function and one defaults snapshot. Each of its six switches restores its own part's predecessor exactly, and they compose: `promoted_predictor = false` makes `learned_coupling`, `reading_opportunities` and `reading_self_check` moot, `reading_opportunities = false` makes `reading_self_check` moot, and `selection = false` leaves the subject view computing receipts and readiness numbers while the predecessor serves every slot.
- **The dose arm is not part of the successor.** `reading_dose_offers` changes what the Reader may offer, not any persisted meaning, like RW2c's passage draw (§5.12). It ships in the AD2+AD3 stage with its own switch and composes with all five: its offers and their outcomes are logged whatever the others say.
- **Master switch.** `adaptive_difficulty.enabled = false` turns every AD behaviour off, logging included.
- **Version gating.** Successor gates follow the playbook: a serving change acts only at its tag or later (`algorithm_versions.successors_from`).
- **Upgrades.** Each upgrade function chains through the previous one, prepares the projection before the atomic version write, and leaves the prior version readable on failure (playbook step 3).
- **Defaults snapshots.** Each successor records one (playbook step 4).

### 11.2 Tables

| Table | Role | Contents | Rebuilt by |
|---|---|---|---|
| `practice_attempts.difficulty_rating` | RAW_LEDGER column (nullable) | `easy` / `about_right` / `hard`, tapped before feedback | — |
| `practice_attempts.first_hint_progress` | RAW_LEDGER column (nullable) | `no_draft` / `draft_started`: whether an answer had been started when the first ordinary hint was revealed (§5.3). The practice screen reads the same marker it already sends with tutor questions (`apps/learnloop-tauri/src/screens/PracticeScreen.tsx:284-285`) at the first hint reveal (`:619`), keeps it in the saved draft, and sends it on submit. Null on every earlier row, from clients that do not send it, and while `forecast_receipts` is off; null reads as `unknown` | — |
| `item_forecasts` | RECEIPT (append-only): rows of kind `item_unassisted_success` in `forecast_receipts` (migration 206), no table of its own (amended at AD1) | §8.1, with `scope` (`presentation` / `item`) | never cleared |
| `item_forecast_payloads` | WORKFLOW | raw outside-forecaster responses; pruned after `router.payload_retention_days` | — |
| `item_serve_inputs` | RECEIPT (append-only) | §7.5: per presentation of a never-attempted item, the served revision's hash, stamped and resolved features with audit ids, the signal vector with receipt ids, `pre_exposed`, the resolution version, and from the AD2/AD3 successor the loadings in force with their ledger ids and the coupling version | never cleared |
| `ad_reading_opportunities` | RECEIPT (append-only) | §5.11: per (reading opportunity, LO), the kind (`reading`, `reader_tutor_exchange`, `worked_example`, `in_passage_question`) and subkind, the source row's id and write time, the facets and doses as resolved, the `ad_dose_offers` id when an offer produced it, the mapping version, and the authority class `salience_only`; plus one verdict row per judged in-passage question (D22: kind `in_passage_question`, subkind `self_check:matched` or `self_check:missed`, the `judgment_ledger` row's id and write time as its source, the question's facets and doses); written by the serve-time sweep and AD1's one-time backfill | never cleared |
| `ad_dose_offers` | RAW_LEDGER (append-only) | §5.12: per eligible section draw, the visit, section and LOs, the feasible variants and why any was infeasible, the base policy's version, the floor, every `π`, the seed and the chosen variant, written before anything is shown; later rows for the same draw record `delivered`, `not_delivered`, `taken` or `dismissed`, and never change the draw's row | — |
| `judgment_ledger` rows, task `ad_feature_audit` | RAW_LEDGER (existing) | §7.2, with the audited revision's `content_hash` | — |
| `judgment_ledger` rows, task `ad_relatedness` | RAW_LEDGER (existing) | §5.10: one row per proposed loading (item revision → facet) or coupling (LO → LO), with strength, rationale, prompt version `ad-relatedness-v1` and input hash | — |
| `ad_relatedness_runs` | RECEIPT (append-only) | *Added at AD2+AD3 (2026-10-19):* one row per relatedness proposal run of a subject: the units it covered with each unit's fingerprint (an LO's text, facets, prerequisites and relations; an item revision's hash), the `judgment_ledger` ids it appended, its input hash and status. A re-proposal covers only the units whose fingerprint changed (§5.10 "When") | never cleared |
| `ad_coupling_versions` | RECEIPT (append-only) | *Added at AD2+AD3 (2026-10-19):* each adopted coupling version per subject (§5.10 "As of"): the runs in force at adoption, who adopted it and when. A later version is a reinterpretation, adopted only after its shadow report | never cleared |
| `ad_selections` | RAW_LEDGER (append-only) | decision id, `kind` (`serve` / `commission`), cell; for a serve draw, the block id, slot position and slot item; mode (`band` / `calibrate` / `predecessor`); the support (or commission candidates) with `P_band`, `p̄`, `I_c`, `π`, and each excluded candidate's failed check; seed; the chosen item (serve) or feature point (commission); `empty_support`; state hash; versions; for a commission the generation path drew inside a durable job, that job (`generating_job_id`, §6.1) | — |
| `item_substituted` block event | a new `kind` in the existing `attention_block_events` ledger (migration 096; `kind` is free text, so no migration) | §6.1 step 5: slot item, drawn item, both estimates, the `ad_selections` id; folded by `daily_plan/records.py:357-410` | — |
| `item_displaced` block event, reason `ad_ineligible` | the existing kind in `attention_block_events`; its detail is free JSON, so no migration | §6.1 step 0: the slot item's failed checks (pre-exposure excepted) and the `ad_selections` id. The plan record folds it into the plan's exclusion set as an AD deferral (`daily_plan/records.py:394-396` today keeps only the reason); each boundary's decision detail records the deferrals it applied and cleared | — |
| `ad_commission_results` | RECEIPT (append-only) | per landed commission: the `ad_selections` id, the generated item, its audited features, `p̄(i)`, in band or `realized_out_of_band`, `landed_after_expiry`, `features_match`; one row per item (§7.4) | never cleared |
| `ad_state` | DERIVED | current posterior per view (`subject`, or `lo:<id>`, §5.6): subject levels, facet and cell moments and shared parameters, sparse covariance; for the subject view, per grid point `ξ` with its weight `W(ξ)`, the a-priori covariance the coupling regression reads (§5.10), and the coupling version | AD replayer |
| `ad_attempt_trace` | DERIVED | per eligible attempt and view: prior and posterior `η` moments, category probabilities, information gained, `input_status` (§7.5), and, for the subject view, each point's `Z_t(ξ)` and weight | AD replayer |
| `item_forecast_scores` | DERIVED | §8.3 | forecast-score replayer |
| `facet_capability_feature_credit` | DERIVED | §9.3: per (attempt, facet, capability), banked credit and the conservative tuple; no level numbers | canonical-projection replayer (same owner as `facet_capability_evidence`) |

- Each new table is classified in `db/table_roles.py`. Each DERIVED table has exactly one registered replayer in `substrate/rebuild_orchestrator.py`, and both facts are tested (CLAUDE.md).
- Migrations take the next free numbers at implementation time. The head is 204 at `37a2a7e5f` (`migrations/204_source_held_out_signal_marks.sql`). The migration-head fixture is renamed and its five hard-coded paths and references regenerated, per CLAUDE.md.

### 11.3 Replay invariants

- **Zero model calls in replay.** The AD state is a pure function of the attempt ledger, the `item_serve_inputs`, `item_forecasts` and `ad_reading_opportunities` receipts, the `judgment_ledger` audit and relatedness rows, `practice_item_snapshots`, `ad_priors_v1` and `ad_hyper_v1`. Current vault content is read only for a historical attempt resolved `reconstructed_current` under the field's explicit fallback (§7.5). Outside forecasts and the relatedness proposal are read from their rows and never re-asked. The AD replayer reads `ad_reading_opportunities` only through the firewall's carve-out (§5.11). The dose-and-burden analysis is a function of the same inputs plus `ad_dose_offers` and the Reader visits' recorded timings (§10.4), and it too makes no model call.
- **Deterministic rebuilds.** Two rebuilds are byte-identical.
- **AD never touches evidence.** Mastery, facet recall, FSRS, `grading_evidence` and `facet_capability_evidence` are byte-identical with AD on vs off, under any relatedness proposal and any reading history (A2, A12). This is enforced by an import-linter contract forbidding the AD package from importing evidence writers. AD4's feature-credit ledger is the one exception: it is written by the canonical projection, not by AD.
- **Certification never reads an estimated difficulty (A11).** Credit rows, levels, requirement points, certificates and the cold probe's item choice are byte-identical under any change to AD's state (couplings, loadings and reading terms included), the item-side signals, the `difficulty` label, solver-panel rates or empirical-Bayes `b`. A second import-linter contract forbids the certification and feature-credit code from importing the AD package or `resolve_item_irt_params` (G-AD4-13).

### 11.4 Config (new section)

```toml
[adaptive_difficulty]
enabled = true
forecast_receipts = true
outside_forecasters = ["llm_v1:item", "llm_v3:llm", "llm_v3:decider"]   # D4; spend-capped
rating_tap = true
feature_audit = true
selection = true              # AD2/AD3 tag (one successor); waits for no harness result (D3)
generation_contract = true    # AD2/AD3 tag
promoted_predictor = true     # AD2/AD3 tag: the subject view steers live from the start (D3)
learned_coupling = false      # AD2/AD3 tag: loadings, couplings and their proposal (§5.10, D19); off until the owner adopts a coupling version (owner decision 2026-10-19)
reading_opportunities = true  # AD2/AD3 tag: reading raises the predicted level (§5.11, D20)
reading_self_check = true     # AD2/AD3 tag: self-check verdicts on in-passage questions as their own learned term (§5.11, D22)
reading_dose_offers = true    # AD2+AD3 stage, outside the successor: randomized dose offers in the Reader, live by owner decision (§5.12, D21)
dose_floor = 0.10             # per feasible variant (§5.12, D21); at most 1/3, so three feasible variants keep a proper distribution (amended at AD2+AD3)
dose_daily_offers = 3         # friction budget, beside one extra offer per section (§5.12)
rung_certification = true   # AD4 tag
probe_targeting = true      # AD5 tag
practice_band = [0.70, 0.80]
overlap_band = [0.55, 0.90]
overlap_share = 0.10
near_tie_margin = 0.05
calibrate_below = 0.25           # 0.35 as registered; amendment A17, owner decision 2026-10-19 (§5.9)
history_fallback = "current_content"   # AD's own reading of history without a saved revision (§7.5; owner decision 2026-10-19)
exam_target_quantile = 0.8
ready_threshold = 0.8
exam_target_calibration = false   # §6.2, D12
priors = "ad_priors_v1"
hyper = "ad_hyper_v1"             # the hyperparameter grid and its uniform prior (§5.10)
ladder = "ad_ladder_v1"
daily_spend_cap_usd = 0.50        # outside forecasters and the relatedness proposal on paid routes
```

**Owner decision 2026-10-19** (`docs/reviews/adaptive-difficulty-ad23.md` §3.4): "Merge with fixes, option 1 + option 2 + option 5 of §3.3. The successor merges with `selection` on, and the failing gates are kept as monitors: their strict xfails stay, with the figures. Lower `calibrate_below` to 0.25. Record it as a NEW, separately recorded pre-registration amendment, made after the reported results, with the reason. The earlier results stand as reported. Re-run `python -m learnloop.sim.ad_gates` and record the new G-AD2-18 figures beside the old ones. Don't change any other threshold. `learned_coupling` defaults to OFF until the owner has spot-checked the relatedness proposal. Update the defaults, the snapshots, the docs and the owner-run commands: show how to turn it on after adopting a coupling version."

**Owner decision 2026-10-19** (`docs/reviews/adaptive-difficulty-ad23.md` open question 4): "History fallback. AD reads historical attempts through the current-content fallback by default, so the owner's vaults start with usable history. First check what `field.legacy_fallback` controls beyond AD. If it affects anything outside AD (the field harness or other projections), DON'T change the field default. Add an AD-scoped setting, e.g. `adaptive_difficulty.history_fallback = "current_content"`, that AD's replay reads, and leave the field's default unchanged. Classify the new key in the parameter registry. Record what it means: historical attempts are read against today's item text where the exact revision wasn't saved."

*Recorded:* `learned_coupling` turns on only after the owner has run the relatedness proposal on a copy, spot-checked it and adopted a coupling version (`learnloop ad relatedness --adopt`); the proposal itself runs only with the switch on, so the owner sets it on the copy for the proposal and on the vault after adoption (the review's §8). `history_fallback` is classified in the parameter registry (decision, constraint).

---

## 12. What the learner sees (frictionless defaults)

- **Practice feels right, and nothing new is required.** There is no placement ceremony and no difficulty slider.
- **The optional one-tap rating.** Next to Submit: "Felt: easy · about right · hard".
  - It is not preselected and never required.
  - It is captured before feedback, beside the existing pre-answer confidence tap (`apps/learnloop-tauri/src/screens/PracticeScreen.tsx:211`).
  - It can be hidden for the session with one tap, and the choice is remembered (browser storage, per viewer).
- **"Why this item"** (one line, by the draw that chose it, like router §7.4):
  - band: "Picked to be challenging but doable for you (about a 3 in 4 chance)";
  - overlap: "A different kind of question, to keep LearnLoop's picture of you accurate";
  - calibrate: "A question to find your level here".
- **Levels on the map and the LO page:**
  - "Shown at level 2 of 4" (Demonstrated), on the ladder of the goal in view (§9.1); with no goal in view, the default ladder;
  - with an exam target: "Exam level: not yet shown · likely ready" (Ready, labelled as a prediction). The prediction reads the subject view; with `promoted_predictor` off the line reads "exam level: not yet predicted", and a cell with no answer of its own reads "untested" (§9.5).
  - Well depth and beads are unchanged by AD; the level is a label beside them (A9).
- **Now and then, one more thing to try at the end of a section** (the dose arm, §5.12). At most one per section and three a day, in the Reader's usual quiet style, dismissed with one key, never a gate on the text: "One more worked example on this? · Book A §3.4" or "A quick question on this section?". Most sections show nothing new. A dismissal costs nothing.
- **No jargon.** "Level", not rung; "chance", not probability.
- **Glass box on demand:**
  - the items behind each level, with dates;
  - the forecast numbers from each forecaster;
  - the feature point an item was written for, and the audit's reading of it;
  - which topics LearnLoop judges related to this one and which topics an item draws on, with the proposal's one-line reasons and how much this vault's answers have learned to trust them (§5.10);
  - what reading added to a prediction, by kind (§5.11);
  - **"What helps you"**: the dose-and-burden lines, for example "Worked examples: about 2 per section before practice helped your later recall most per minute", each labelled "tested by randomized offers" or "what preceded better recall for you", or "can't tell yet" (§10.4);
  - why an extra offer appeared: "Offered at random, to learn how much of this helps you" (§5.12);
  - whether sharing, the learned coupling and reading are helping, hurting, or can't tell yet, for this learner and vault, with any open auto-flag (§10.4);
  - the identifiability statement (§5.8).
- **Too easy / too hard / easier / harder** keep working as today (D8).

---

## 13. n>1: pooled priors from consented data

- **What pooling can supply.** Population priors for `β`, `ψ_{j,k}`, `α`, `γ`, the reading kinds' dose curves `γ_read` and `ζ`, the residual variance `τ0²` per generator family and version, the prior weights of the hyperparameter grid (§5.10), and the strengths of individual couplings and loadings on shared content (§5.8); and randomized dose estimates pooled over learners, which one learner's arm reaches only slowly (§5.12). These are exactly the quantities n=1 identifies weakly or not at all: one learner learns the split and the coupling strengths only in aggregate over a vault, and individual pairs not at all.
- **What stays local.** Personal cell abilities, always.
- **Staged path** (worker f, R12):
  1. **One learner (now).** A-priori priors, prior-predictive checks, sensitivity analysis and chronological scoring (§5.5, §8).
  2. **Opt-in pilot.**
     - Pool `β`, family residual variances, `γ`, `ζ` and `α` across consenting learners.
     - Validate on held-out learners *and* held-out item families.
     - Return the result as a versioned artefact (`ad_priors_v2`) through the playbook, like any change of persisted meaning (storage spec §6.12).
  3. **Transfer.** Robust mixture priors keep a vague component, so an unusual learner or a new generator escapes a misfitting population prior `[schmidli2014]`. Never count a learner's own history again through a pooled prior that includes it.
  4. **Private scale-up.**
     - Privacy at the learner level, not the item level `[liu2020]`.
     - Secure aggregation `[bonawitz2016]`.
     - Differentially private release of shared parameters with abilities kept local `[steiner2018]`, `[zhou2025]`.
- **Requirements this spec adds to the contribution export** (storage spec R13 / §6.12, phase S9). Structured fields only, no text:
  - audited and stamped feature tuples, and generator family and version;
  - `item_forecasts` (p values, forecaster ids and versions; payloads excluded);
  - `ad_selections` with propensities;
  - outcome categories (§5.3) with the help timing `h_t`, `primed` and `pre_exposed`;
  - optional ratings, and latency with the learner's own prior answer-time estimate beside it (§5.4), so the normalization can be rebuilt;
  - the relatedness proposal's structure (ids and strengths of loadings and couplings, never their rationales) and reading opportunities by kind, subkind and dose (§5.10–5.11);
  - `ad_dose_offers` with propensities, uptake and dismissal (§5.12), and minutes per visit, so the dose-and-burden analysis can be pooled.

  These keep pooled estimation of feature effects, couplings, reading curves and dose effects possible without a retrofit.
- **Trigger** (§16): the S9 export is built and at least 20 consenting learners have at least 200 first-surface attempts each.

---

## 14. Phases, gates and fail-first tests

Each test below is written first, and fails on today's code for the stated reason. All tests use fakes. The paid forecasters' interfaces are verified by the existing route tests and one dry-run.

### AD1: measure and log (no successor)

**Needs:** the "diagnosis input provenance" stage landed (`spec_mcp_frontend_c1.md` §4.8; D18).

**Builds:**
- migration: `item_forecasts` (with `scope`; *amended at AD1: kind `item_unassisted_success` rows of migration 206's `forecast_receipts`, so migration 213 adds no such table*), `item_forecast_payloads`, `item_serve_inputs`, `ad_reading_opportunities`, `practice_attempts.difficulty_rating`, `practice_attempts.first_hint_progress` (*and, amended at the AD1 Codex review, `question_events.answered_at`, §5.11*);
- table roles;
- the serve-input receipt (§7.5) and the in-process forecasters `mastery_ekf` and `lo_general+composite`, written in the serve transaction;
- outside forecasters behind `outside_forecasters`, spend-capped: `llm_v1:item` once per item revision when it is prepared for the pool, plus its one-time backfill; `llm_v3:*` asynchronously per presentation (§8.2);
- the feature audit (§7.2) and its owner-run backfill;
- the reading-opportunity sweep (§5.11) over the four kinds' listed sources only, at every serve and once as a backfill over the history, under `forecast_receipts`. No model call, and nothing reads the receipt until the AD2+AD3 stage adds the firewall carve-out;
- the rating tap (§12) and the first-hint progress marker (§11.2);
- `learnloop ad data-check`: the §3.3 tables on a backup copy, plus first-surface attempts per cell, coverage of latency, ratings and hint timing, exam units with and without a facet mapping (Q3), and historical attempts by revision status (§7.5).

**Gate:** G-AD1-1 to G-AD1-11.

| Id | Test (fails today because…) |
|---|---|
| G-AD1-1 | `test_forecast_receipt_written_in_serve_transaction`: serving a plan item writes one `item_forecasts` row per in-process forecaster in the same transaction as `plan_presentations`, with `inputs_as_of ≤ served_at` (no such table) |
| G-AD1-2 | `test_late_outside_forecast_is_valid_if_inputs_predate_serve` and `test_forecast_with_post_serve_inputs_is_invalid` (no validity rule) |
| G-AD1-3 | `test_rating_tap_optional_never_blocks_submit`: submit without a rating succeeds; the rating is stored only when tapped and only before feedback (no column) |
| G-AD1-4 | `test_feature_audit_ledgered_with_fallback`: Decider argmax per dimension, tie is no answer, LLM fallback recorded (no audit task) |
| G-AD1-5 | `test_ad1_switches_restore_predecessor`: all four switches false ⇒ no new rows, prompts byte-identical, no extra calls |
| G-AD1-6 | `test_held_out_sentinel_never_reaches_ad_inputs`: a sentinel in a held-out unit appears in no AD prompt, receipt, payload or audit input |
| G-AD1-7 | `test_replay_reads_receipts_zero_model_calls`: rebuild with model constructors forbidden |
| G-AD1-8 | `test_serve_inputs_frozen_against_later_audit_and_edit`: an audit that lands after the serve, a re-audit and an item edit change no `item_serve_inputs` row; the served revision is in `practice_item_snapshots` (no receipt today) |
| G-AD1-9 | `test_item_only_forecast_enters_inputs_only_if_received_before_serve`: an `llm_v1:item` receipt prepared with the pool appears in the first serve's `z_i`; one received after the serve is scored but absent from that serve's inputs (no item-scoped receipt today) |
| G-AD1-10 | `test_first_hint_progress_recorded_and_missing_is_null`: a first hint revealed with an empty answer stores `no_draft`, after typing `draft_started`; a restored draft keeps the marker; a client that sends none stores null (no column today; `field/probability_states.py:98-101`) |
| G-AD1-11 | `test_reading_opportunities_frozen_and_ordered_by_source_time` (no receipt today). Each listed source writes one receipt row per LO, inside the caps, with kind, subkind, doses, source id, source write time and the authority class `salience_only`: a completed section and a span view (`reading`), an answered reader tutor question, a worked example shown or in a completed section, an answered quick check of each in-passage style, and an answered owner-placed reading question. A span view of a worked-example block is a `worked_example` only. A `reconstruct` question, a skipped or dismissed question and an unanswered prompt write nothing. A source row written after a serve is never recorded by that serve's sweep and never changes that serve's state on replay. Deleting the extraction (`delete_source_artifact`) leaves the receipts. A judged in-passage question also writes one verdict row (D22), from its first `judgment_ledger` self-check verdict, as `self_check:matched` or `self_check:missed`; a later changed verdict writes nothing. No dwell, scroll, highlight, skip, visibility, active-time or answer value is read. With `forecast_receipts = false` no row is written |

### AD2: practice in the band (one successor with AD3; switches `selection`, `generation_contract`)

**Needs:** AD1 merged (its receipt tables). AD2 is built, merged and goes live together with AD3, as one successor (D3). It waits for no harness result: practice selection serves with a-priori priors and reads the subject view from the start (§6.1).

**Builds:**
- **The model.** The AD replayer in both views (`ad_state`, `ad_attempt_trace`, §5.6; the subject view's relatedness and reading are AD3's builds); in-process `ad_threshold@lo`, `@subject` and `@subject_uniform` receipts at serve time; arms in `learnloop eval` (§10.4); `learnloop ad report` (prequential metrics with the first-attempt split first, band-region reliability, identifiability diagnostics, sensitivity, time to a usable estimate); simulation recovery and time-to-usable runs on `sim/` synthetic learners with known `θ_t`, `β`, `γ`.
- **The serving.** `ad_selections` and `ad_commission_results`; the `feature_overlap` design; lane integration; serve and commission draws in the view `promoted_predictor` selects; AD deferrals in the plan's exclusion set (§6.1 step 0); the generation contract (§7.1); re-forecast (§7.4); "why this item".

**Gate:** G-AD2-1 to G-AD2-31 and AD3's G-AD3-1 to G-AD3-15, then the owner reads the AD2/AD3 report once on a backup copy (owner-run, field §7.3 style) before the successor merges.

**The model (offline):**

| Id | Test |
|---|---|
| G-AD2-1 | `test_trivial_success_barely_moves_ability` (**fail-first, the core question**): with `θ_c` posterior mean 1.0, an unassisted success on an item whose features put its demand at −3.0 moves the mean by < 0.02; a success at demand ≈ 1.0 moves it by ≥ 0.2; a failure on the trivial item moves it by ≥ 0.5 (no feature-based demand exists today; the canonical path is difficulty-blind, G3) |
| G-AD2-2 | `test_overclaimed_features_do_not_lower_demand_estimate`: audited features override stamped ones in the likelihood |
| G-AD2-3 | `test_rebuild_byte_identical` and `test_zero_model_calls` |
| G-AD2-4 | `test_ad_never_writes_evidence` (import-linter contract plus byte-identical evidence tables with AD on vs off) |
| G-AD2-5 | `test_self_report_and_held_grades_excluded`; `test_repeat_surface_attempts_excluded` |
| G-AD2-6 | `test_rating_subarm_off_is_identical_to_base` (no double counting) |
| G-AD2-7 | `test_confound_detected_under_monotone_schedule`: a simulated learner with true growth and **no** feature effect, served monotonically harder points, yields `β` labelled "confounded" by the diagnostic |
| G-AD2-8 | `test_feature_effects_recovered_under_overlap`: the same learner under `ad_select_v1` (`q = 0.10`, single-dimension commission neighbours) recovers each true `β` within 2 posterior sd in ≥ 90% of 200 seeds; directions aliased by design are reported "prior-dependent", not recovered |
| G-AD2-9 | `test_band_probability_exact`: `P_band` from §5.7 matches 10⁶-draw Monte Carlo within 1e-3, including band edges outside `F_x`'s range |
| G-AD2-10 | `test_joint_attempt_factor_integrates_residual_once`: with a rating and a timing present, the update matches brute-force joint integration over `ε_i` within 1e-6, and differs from the product of separately marginalized factors |
| G-AD2-11 | `test_link_parameters_always_valid`: for any values of `(c_1, d̃, ρ̃)`, rating category probabilities lie in [0,1] and sum to 1 |
| G-AD2-12 | `test_claims_applied_at_created_at_and_request_claims_excluded`: a claim never moves an attempt that precedes it; `rung_variant_request` and `learner_report` claims never enter the state |
| G-AD2-13 | `test_warmth_uses_only_pre_serve_exposures`: an exposure after the serve time never changes `w_t` or the receipt's `p` |
| G-AD2-14 | `test_help_and_reveal_are_censored_not_dropped` (**the estimand**): a simulated learner asks for help or reveals the answer more often the lower its ability. Over 200 seeds, AD's predicted unassisted-success rate matches the simulated rate within 2 posterior sd in ≥ 90%, while a variant that drops assisted attempts overestimates it. Changing the correctness of a revealed attempt never changes the update |
| G-AD2-15 | `test_unknown_hint_timing_never_read_as_after_work`: a success with ordinary hints and no marker, and one with a help-equivalent tutor question and no progress marker, both enter as censored `{0, 1}`; with `draft_started` they are category 1, with `no_draft` category 0 |
| G-AD2-16 | `test_replay_uses_frozen_inputs_and_explicit_history`: each attempt's factor is built from its `item_serve_inputs` row, never the current item; historical attempts resolve `exact`, `reconstructed_current` only under the field's fallback, else `excluded`, and `excluded` attempts never update |
| G-AD2-17 | `test_pre_exposed_presentation_excluded_from_update_and_scoring`: a reveal sum at the auto-prime threshold before `served_at` removes the item from `P_c`, sets `pre_exposed`, and the attempt neither updates nor is scored |
| G-AD2-18 | `test_time_to_usable_estimate_on_synthetic_learners` (**the owner's target**, §5.9; thresholds pre-registered with the arms). Setup: 200 synthetic learners per scenario from `sim/`, with true parameters drawn from `ad_priors_v1`, learning at their own `γ`, and item residuals at `τ0`. Pools hold items at every ladder point. Per answered question in the subject, the test records whether band mode engaged at the served point, and whether the draw was a band hit: the served item's true family-expected success (residual integrated) in [0.70, 0.80]. Pass conditions:<br>• **One LO, one cell** (every answer informs the served quantity, as in §5.9's arithmetic): band mode engages by the 15th answer for ≥ 80% of learners, and the band-hit rate over answers 16–30 is ≥ 0.35. The arithmetic gives about 0.45.<br>• **Wrong prior** (the true subject level 1.5 logits above or below the prior mean): the band-hit rate over answers 16–30 is ≥ 0.30, so the selection corrects itself.<br>• **The plan's flow** (one-LO blocks over three LOs and two capabilities, in the subject view, the live one): the band-hit rate over answers 16–30 is at least the incumbent waypoint ladder's (`depth_rungs.py:228-319`) and at least AD's with its updates switched off, and the trivial-success rate is no worse than the incumbent's.<br>The plan-flow results are reported for seen and never-seen cells separately (the first-attempt split), with the number of own answers each never-seen cell needed, and with the LO view's figures beside the subject view's |

**The serving (the AD2/AD3 successor):**

| Id | Test |
|---|---|
| G-AD2-19 | `test_propensity_recomputes_from_logged_row` and `test_seed_reproduces_draw` |
| G-AD2-20 | `test_generation_prompt_has_no_band_language_under_successor` (**fail-first**: `practice_generation.py:1919` contains the band instruction today) |
| G-AD2-21 | `test_selection_switch_off_restores_lane_order` (byte-identical plans on fixture copies) |
| G-AD2-22 | `test_exam_reserved_and_retired_items_never_selected`; `test_coordination_requires_envelope` |
| G-AD2-23 | `test_calibrate_mode_prefers_overlap_band`; `test_calibrate_with_empty_overlap_picks_nearest_to_band` |
| G-AD2-24 | `test_joint_propensity_logged_with_router_block` |
| G-AD2-25 | `test_commission_result_appended_never_mutates_selection`: an out-of-band landed item gets an `ad_commission_results` row and is not served for that commission |
| G-AD2-26 | `test_serve_propensity_is_over_existing_items`; `test_empty_overlap_sets_q_zero`; `test_empty_support_makes_no_draw_and_displaces`; `test_empty_pool_commissions_at_generation` |
| G-AD2-27 | `test_item_over_block_budget_not_in_support` (**fail-first**: no slot substitution exists today): an otherwise eligible item whose estimate exceeds the slot item's plus the block's, plan's or lane's slack is not in `S`; after any substitution the block is within 15 minutes and the plan within its budget |
| G-AD2-28 | `test_support_respects_constraints_reversibility_and_admission`: an item the constraint engine refuses, one holding an open cold check or a reserved surface, one planned elsewhere, and a costlier item for a floor-admitted slot are never in `S` |
| G-AD2-29 | `test_draw_after_block_choice_with_pair_propensity`: AD draws only at a `new_admitted` slot of the chosen block, inside the serve transaction; the logged pair propensity is `π_router · π_AD`; router candidates and `π_router` are byte-identical with AD on vs off; `item_substituted` folds into the plan record |
| G-AD2-30 | `test_support_rechecked_at_draw_slot_item_included` (**fail-first**: before a serve, reconciliation re-checks only status and serving blocks, `daily_plan/engine.py:1925-1931`). After a block is admitted and before its slot is served, the slot item becomes exam-reserved, gains an open cold follow-up, is revealed within the cold retrieval delay, reaches the pre-exposure threshold, or is refused on a fresh snapshot. The same is done, separately, to another candidate. None of them is in `S`. A slot item with no other candidate is displaced with `ad_ineligible`, except in the pre-exposure-only case, which is served with `mode = predecessor` and `π_AD = 1`. With `selection = false` the predecessor serves the planned item byte-identically |
| G-AD2-31 | `test_ineligible_displacement_defers_until_condition_clears` (**fail-first**, final verify F10: a displaced item returns to the pool, `daily_plan/records.py:247-250`, and the boundary pool removes only planned and skipped items, `daily_plan/engine.py:1223-1225`).<br>• **The verify's scenario.** `selection` on, router off. A five-minute, never-attempted ordinary item `a` is planned. Before it is served, it gets a partial reveal below the 0.35 auto-prime threshold, with no cold follow-up, and there are no substitutes.<br>• **No loop.** Step 0 displaces `a` once, with `ad_ineligible` and the failed check `recent_reveal`. Across 20 further advances, no block holds `a`, and with no other work the plan closes as complete. The projection never plans `a`, and a keep-going plan the same day excludes it. Rebuilding the plan record from its events gives the same exclusion set. The same holds with the router on.<br>• **Readmission.** With other work in the plan, `a` stays out while the reveal is within the delay, and rejoins the pool at the first boundary after it (fake clock), where AD may draw it. An item held by an open cold follow-up is readmitted once that task closes.<br>• **Switch off.** With `selection = false`, none of this happens and the predecessor serves `a` |

### AD3: the subject view live (one successor with AD2; switches `promoted_predictor`, `learned_coupling`, `reading_opportunities`, `reading_self_check`; outside the successor, `reading_dose_offers`)

**Needs:** AD1 merged. AD3 is built, merged and goes live together with AD2, as one successor (D3). No harness result is a precondition; the harness monitors it from the tag on (§10.4).

**Builds:**
- **The subject view live.** The subject view as the state of live decisions (§6.1, §6.3); the readiness numbers the learner sees ("Ready for exam level" and "likely ready", with the untested rule, §9.5, §12); the router card's AD fields (§10.1).
- **The learned relatedness (§5.10).**
  - The proposal job and its one-time backfill per subject: spend-capped, dry-run first, ledgered.
  - The loadings in the serve-input receipt.
  - The coupled construction and the transfer of increments.
  - The hyperparameter mixture over `ad_hyper_v1`.
- **Reading (§5.11).**
  - The firewall carve-out: the module's rule text updated to name the confirmed exception and its four limits, and `learning_opportunity_events` added as the only path from the receipt to AD's state, with the sweep's list moved into it. Every existing firewall test is unchanged.
  - The four kinds' dose curves, hierarchical over kinds, applied in the subject view, with reading windows closed by graded attempts (§5.6 step 5).
- **The randomized dose arm (§5.12), outside the successor, behind `reading_dose_offers`.** The `reading_dose` design in the randomization layer; `ad_dose_offers`; the section-boundary offer in the Reader (an extra worked example by retrieval, an extra question from the existing quick-check producer within its caps) inside the friction budget; uptake and dismissal rows.
- **The monitoring.** The comparators, confidence sequences, auto-flags and the honest line (§10.4); the dose-and-burden analysis with its plain recommendation lines (§10.4); the glass-box lines (§12).
- **Simulation.** Synthetic vaults with known structure in `sim/`, for G-AD3-6 and G-AD3-7, and synthetic readers with known per-kind effects, saturation and struggle-driven reading, for G-AD3-11 and G-AD3-14.

**Gate:** G-AD3-1 to G-AD3-15, with AD2's gate, before the owner reads the AD2/AD3 report.

| Id | Test |
|---|---|
| G-AD3-1 | `test_live_decisions_read_subject_view_and_switch_restores_lo_view` (**fail-first**: no AD state exists today). With `promoted_predictor` on, answers on another LO change an LO's `P_band`, `π` and commission point, and a never-seen LO's first draw reads the subject-level estimate (D18). With it off, answers on another LO change none of them (they still change `ad_threshold@subject`'s receipts), and draws and receipts are byte-identical to the same successor with the subject view absent |
| G-AD3-2 | `test_readiness_numbers_from_subject_view_with_untested_cells`: with the switch on, the exam line and the router card's AD fields appear, labelled as predictions. A cell with no eligible answer of its own shows "untested" whatever the shared terms, couplings or reading predict, so none of them alone ever shows "likely ready". With the switch off, the line reads "exam level: not yet predicted" and the card carries no AD fields |
| G-AD3-3 | `test_monitoring_applies_field_rule_as_monitor_never_gate`: the report computes field §7.4's rule for `@subject` against `mastery_ekf`, `@lo` and `@subject_uniform` (attempt-level log loss overall and on the first-attempt split, the bootstrap interval at the pre-registered margin, report 2's miss rate), plus the never-seen-cell split, band-region reliability and the confidence sequences. It states "helping", "hurting" or "can't tell yet" for sharing, coupling and reading. No outcome of the report changes any switch, config or served item |
| G-AD3-4 | `test_relatedness_proposal_reads_no_learner_or_held_out_data`: the job's input is exactly the subject's LO and facet text, the concept graph, prerequisites and item stems. A sentinel planted in an attempt, a grade, a diagnosis, a claim, a reading event, a tutor question, a reference answer, a held-out unit and an item derived from it reaches no prompt. Calls are spend-capped and dry-run first. Each loading and coupling is one `judgment_ledger` row. An unchanged input hash makes no call; a retitled LO or a new item revision re-proposes only what it touches. Invalid outputs (unknown ids, another subject's facet, self-loadings, over the caps) are dropped |
| G-AD3-5 | `test_coupling_is_prediction_only`: under any proposal, including an adversarial one that couples everything at full strength, `grading_evidence`, mastery, facet recall, FSRS, `facet_capability_evidence`, `facet_capability_feature_credit`, levels, requirement points, certificate ids and cell-pool membership are byte-identical to no proposal. The caps hold (3 per unit, `χ_C ≤ 0.75`, `χ_Q ≤ 0.5`). `learned_coupling = false` makes the subject view byte-identical to its `χ_C = χ_Q = 0` points and makes no proposal call |
| G-AD3-6 | `test_hyperparameters_learned_and_replayable`: the weights follow the running marginal likelihoods exactly; the joint prior stays positive definite under any proposal. On synthetic vaults generated at each grid point, with 300 first-surface answers over at least 10 LOs, the posterior puts at least half its weight on the generating point and its grid neighbours in ≥ 80% of seeds. Rebuilds are byte-identical with zero model calls. A proposal recorded after a coordinate's creation changes no earlier state, and a new coupling version applies only through its shadow rebuild |
| G-AD3-7 | `test_related_topics_adapt_faster_unrelated_not_dragged` (**the owner's target**, §5.9; thresholds pre-registered with the arms).<br>• **Setup.** 200 synthetic learners per scenario on synthetic vaults with known structure: 12 LOs in four clusters of three; a true topic correlation of 0.8 within a cluster and 0 across; true loadings of each dependent topic's items onto its prerequisite in the cluster; learners learning at their own `γ`. The proposal is simulated three ways: correct; noisy (half its pairs replaced by pairs across clusters); and wrong (every pair across clusters). Each learner first answers 15 questions on one LO, then meets its never-seen cluster mates and a never-seen LO of another cluster.<br>• **Related topics adapt faster** (correct proposal). On a never-seen cluster mate, band mode engages with at least 2 fewer own answers than under uniform sharing (`@subject_uniform`), by the median, and first-attempt log loss is lower than uniform sharing's with an interval excluding 0. The same holds after 15 opportunities of practice or 5 sections read on the first LO, with no answer on the mate.<br>• **Unrelated topics are not dragged** (all three proposals). On the never-seen LO of another cluster, first-attempt log loss is no worse than uniform sharing's by more than 0.02, and the band-hit rate over its own answers 1–15 is no lower than uniform sharing's by more than 0.03.<br>• **A wrong proposal shrinks.** Under the wrong proposal, the posterior weight on `χ_C = 0` reaches 0.5 within 100 first attempts at never-seen LOs in ≥ 80% of seeds, and the coupling auto-flag fires within 200 in ≥ 80% of seeds. Under the correct proposal, it fires in ≤ 5% |
| G-AD3-8 | `test_reading_raises_prediction_never_evidence`: each opportunity kind raises the predicted success of the LO's next draw by its next dose-curve increment, of items elsewhere that load on its facets, and of coupled topics by `corr₀` times it. A second event of a kind in the same window adds less than the first when both coefficients are positive, a graded attempt on the facet resets the window, and an in-passage answer graded as an attempt takes its kind's increment in place of `γ`, never both. Every evidence, mastery, facet-recall, FSRS and certification table is byte-identical with reading on vs off. No reading opportunity passes `apply_attempt`, and every existing test in `tests/test_salience_firewall.py` passes unchanged. On synthetic learners whose true level rises by 0.3 logits per section read, first-attempt log loss after reading is lower with reading on than off; with no true rise, the posterior mean of the `reading` kind's full effect falls below 0.05 and the reading auto-flag fires in ≤ 5% of seeds. `reading_opportunities = false` makes the subject view byte-identical to one with no reading transitions |
| G-AD3-9 | `test_auto_flags_recommend_and_never_act`: synthetic logs in which sharing, the coupling or reading predicts worse, or in which the dose offers are dismissed or followed by a lowered cue density, fire their flags, each with the switch §10.4 names, and in which nothing is worse fire none in ≥ 95% of seeds. No flag edits the vault config. Each switch off restores its part's predecessor byte-identically, and switches compose as §11.1 states |
| G-AD3-10 | `test_subject_view_mixture_keeps_propensities_exact`: `P_band` under the mixture matches 10⁶-draw Monte Carlo over `ξ` and the state within 1e-3; a draw's `π` recomputes from its logged row; the seed reproduces the draw |
| G-AD3-11 | `test_reading_kind_effects_and_saturation_recovered` (**the owner's question**; thresholds pre-registered with the arms).<br>• **Setup.** 200 synthetic readers per scenario from `sim/`. Each of the four kinds has its own true dose curve: different sizes, one saturating fast, one slowly, one with no effect, and, in one scenario, a worked-example curve that turns down past 3 per window (expertise reversal). Learners practise and read; the dose arm runs at its default floor and, separately, at a floor of 0.3.<br>• **Recovery.** For each kind, the fitted curve lies within 2 posterior sd of the true one at doses 1–5 in ≥ 90% of seeds, and the useful dose `n*_κ` is within one event of the true one in ≥ 80%. The no-effect kind's full effect has posterior mean below 0.05. The downturn is found (the curve's maximum before 5) in ≥ 80% of seeds.<br>• **Confounding.** In a scenario where learners read more after failures and reading has no true effect, the model's curve may show one. The randomized estimate of an offer's effect covers 0 at its nominal rate within ±5 points, and the report never labels that kind's line "tested by randomized offers" |
| G-AD3-12 | `test_dose_offer_propensities_exact` (**fail-first**: no dose arm exists today). Each draw's `π` recomputes exactly from its `ad_dose_offers` row: base, floor and feasible set. Every feasible variant has `π ≥ dose_floor` and the `π` sum to 1. An infeasible variant has no mass, and its reason is logged. The seed reproduces the draw, and over 10⁵ simulated draws each variant's frequency matches its `π` within 0.005. The row is written before the offer is shown, uptake and dismissal append rows without changing it, and the layer registers the `reading_dose` design with its own floor. The budget holds: at most one extra offer per section and `dose_daily_offers` a day, and no draw with the budget spent, density off or in skim mode. With `reading_dose_offers = false` the Reader is byte-identical and no row is written |
| G-AD3-13 | `test_firewall_carve_out_admits_only_listed_kinds` (**fail-first**: no carve-out exists today; it is added to `tests/test_salience_firewall.py` beside the unchanged tests). Parametrized over every `READING_EVENT_KINDS` entry, every `SALIENCE_PROJECTIONS` output and every source table: `learning_opportunity_events` admits exactly the listed sources of §5.11 and returns nothing for any other. No record it returns carries a magnitude field (dwell, active or idle seconds, scroll, highlight or revisit count, outcome class, answer text); the only typed value is D22's verdict class, read from `judgment_ledger` and never from `reader_authored_questions.response_md` or `ReaderObservationV1`. Every record stays stamped `salience_only`, so `reject_salience` and `apply_attempt` still refuse it. The belief modules still never import the firewall module, and the AD replayer reads the receipt only through the carve-out |
| G-AD3-14 | `test_dose_report_recommendation_follows_fitted_curves`. On synthetic fitted states with known curves and minutes, the report's useful dose is the dose at which the curve's marginal gain per minute, by posterior median, crosses the practice reference. The line reads "can't tell yet" exactly when `n*_κ`'s 80% interval spans more than 2 events or the kind's minutes are unknown. A "helps when" line appears only when its moderated contrast's interval excludes 0. The label is "tested by randomized offers" only when the arm's estimate agrees in sign with an interval excluding 0. Moving a curve moves its recommendation the same way. The lines come from fixed templates with no model call, and no recommendation changes a switch, the dose arm's base policy or any offer |
| G-AD3-15 | `test_self_check_verdict_shifts_prediction_never_evidence` (**fail-first**: no verdict term exists today; D22). (1) With `λ` at its prior mean the subject view's predictions equal D20's exactly. (2) A `missed` verdict with a learned negative `λ_missed` lowers the predicted success of the facet's next draw, of coupled facets by `corr₀` times the increment, and of loading items; a `matched` verdict with positive `λ_matched` raises it. (3) One question counts once: a changed verdict appends a ledger row and moves nothing. (4) No verdict reaches evidence, mastery, facet recall, FSRS, certification credit or levels, and `reject_salience` still refuses the receipt row. (5) `reading_self_check = false` gives predictions, draws and receipts byte-identical to D20's (the receipt rows still written), and the switch is moot under `reading_opportunities = false`. (6) Synthetic learners whose verdicts carry no signal shrink both `λ` toward 0 within the pre-registered tolerance, and learners whose misses predict cold failure recover a negative `λ_missed` |

### AD4: levels and full mastery (successor; switch `rung_certification`)

**Needs:** AD1 audits running (levels use audited features). It does **not** need AD2 or AD3: demonstrated levels come from the ledger, never from the predictor or any estimated difficulty (A11). The predicted "ready for exam level" line appears once the AD2/AD3 successor is live with `promoted_predictor` on (§9.5).

| Id | Test |
|---|---|
| G-AD4-1 | `test_level_2_not_demonstrated_by_level_1_successes` (**fail-first**: today any capability-matched success counts, G4) |
| G-AD4-2 | `test_level_uses_easier_of_stamped_and_audited` |
| G-AD4-3 | `test_level0_items_earn_no_certification_credit`; `test_legacy_items_capped_at_level_1` |
| G-AD4-4 | `test_switch_off_certification_byte_identical` |
| G-AD4-5 | `test_ready_and_demonstrated_never_blended` (vitest on the map and LO page) |
| G-AD4-6 | `test_exam_target_uses_practice_available_units_only`: `t_c` is unchanged when held-out units are added or removed; held-out tuples appear only in the evaluation report |
| G-AD4-7 | `test_cold_probe_served_at_certificate_requirement_point` |
| G-AD4-8 | Shadow rebuild on owner copies reports every certificate that changes (playbook step 7; owner-run) |
| G-AD4-9 | `test_two_goals_sharing_a_cell_read_their_own_ladders`: goals with different targets show different `K` and levels from the same feature-credit rows, and the shared LO has one certification state |
| G-AD4-10 | `test_target_revision_keeps_existing_certificate`: a new exam import or re-classified unit makes a new ladder instance and changes no requirement; a reached milestone makes a new certificate id; the earlier certificate's id, `p_req` and cold-probe verdict are unchanged |
| G-AD4-11 | `test_level_pending_until_canonical_audit`: an observation stamped at or above `e_k` counts toward `e_k` only until its revision's canonical audit lands. It is then counted once at its audited level, which may be 0. A later run of the same audit version changes nothing |
| G-AD4-12 | `test_known_below_entry_never_credited_while_audit_missing`. A retrieval item stamped `scaffolding = worked` earns no credit at `e_k` or above in three states: while its audit is pending, after the audit fails or ties on a dimension, and after it lands. A legacy item whose canonical audit reads below entry is level 0. Only observations with genuinely missing readings fall back to entry credit |
| G-AD4-13 | `test_certification_never_reads_estimated_difficulty` (**owner direction**, A11). Changing every estimated difficulty leaves `facet_capability_feature_credit`, levels, requirement points, certificate ids and the cold probe's item choice byte-identical. That covers AD's state in both views, `β`, `α`, every `z` signal, the item's `difficulty` and `difficulty_source`, solver-panel rates and empirical-Bayes `b`. Changing a stamped tuple or a canonical audit does move them. An import-linter contract forbids the certification and feature-credit modules from importing the AD package or `resolve_item_irt_params` |

### AD5: probes that discriminate (successor; switch `probe_targeting`)

| Id | Test |
|---|---|
| G-AD5-1 | `test_probe_prompt_has_no_difficulty_band_under_successor` (**fail-first**: `practice_generation.py:1984`) |
| G-AD5-2 | `test_eig_matches_marginalized_conditionals`: candidate EIG equals a brute-force computation over the residual and `β` uncertainty within 1e-6; identical conditionals give zero |
| G-AD5-3 | `test_capability_hypotheses_get_ad_conditionals` |
| G-AD5-4 | `test_switch_off_probe_selection_identical` |
| G-AD5-5 | `test_composed_snapshot_scores_and_updates_identically` (**end to end**): candidate EIG, the committed snapshot's `compiled_likelihood_hash` and the posterior update after the answer use the same composed rows; an AD state change after the commit changes no update; the probe audit's hash check passes |
| G-AD5-6 | `test_composition_scope`: a rubric above 4 points, misconception, `confuses_with`, `surface_only`, `schema_without_transfer` and `other_or_unknown` slots keep the card's rows exactly; an aliased label reads its slot's composed row; a constraint with probability below 1e-6 is left uncomposed and recorded |
| G-AD5-7 | `test_composed_success_marginal_survives_grader_channel` (**non-identity channel**). Under the contrast family's channel (six outcomes, reliability 0.90), a composed slot with `q_h = 0.80` has an observed success probability of 0.80 within 1e-12; composing before the channel would give 0.724. Its within-class shapes are those of the grader-composed calibrated row. An instrument with no composed slot has conditionals and `compiled_likelihood_hash` byte-identical to today's |

**Order.** AD1 starts once the "diagnosis input provenance" stage has landed (D18). AD2's replayer, AD3's relatedness model, the harness arms and the simulations can be built in parallel with AD1: they read existing ledgers and resolve attempts historically (§7.5) until AD1's receipts exist. Their serve-time receipts and serving write into AD1's tables, so AD2 and AD3 merge together, as one successor, after AD1. Nothing waits for a harness result (D3). AD4 can follow AD1 without waiting for AD2/AD3. AD5 follows AD2/AD3.

---

## 15. Owner decisions, with recommended defaults

| # | Decision | Recommended default |
|---|---|---|
| D1 | Practice band and what "success" means | `[0.70, 0.80]`; success = first unassisted response at correctness ≥ 0.8 (the cold probe's definition). The research supports a band in this region without fixing a number (R5) |
| D2 | Outcome categories (§5.3): help-adjusted success counts as "partial"; early help counts as fail; unknown help timing and answers revealed during the presentation are censored as "not an unassisted success" | Yes, aligned with field's hint arm (graded outcome by help depth). Training and scoring read the same event, so assisted presentations are never dropped from training |
| D3 | When AD serves, and what the subject view steers | **Decided by the owner (2026-10-14; revised 2026-10-15).**<br>• **One successor.** AD2 (practice in the band) and AD3 (the subject view live) ship together and go live together, under one algorithm successor. Each part has its own kill switch: `selection`, `generation_contract` and `promoted_predictor`, with `learned_coupling` and `reading_opportunities` for the subject view's parts (§5.10–5.11, §11.1).<br>• **The subject view steers from the start.** It drives live serve and commission draws, AD5's composition when AD5 lands, and the readiness numbers the learner sees, including where a new topic starts: the subject-level estimate (D18). It uses the a-priori priors of §5.5 and the honest uncertainty of §5.7. QUEST+-style band targeting corrects itself from the learner's outcomes even when its prior is off (§6.1, §5.9).<br>• **Guards.** The simulation gates, including the decision-level checks of G-AD2-18 (band hits at least the incumbent's, trivial successes no worse) and G-AD3-7 (related topics adapt faster, unrelated ones are not dragged); the kill switches; and the monitoring (§10.4).<br>• **The harness monitors, never gates.** It keeps scoring the subject view against the LO view (topic-only), uniform sharing and the incumbent, with field's first-attempt split primary (§8.3, D17). Field §7.4's rule and this spec's additions (the never-seen-cell split, band-region reliability) are computed as monitoring and auto-flag criteria, not as a precondition for going live. The AD report and the glass box say honestly whether sharing is beating topic-only for this learner and vault, and the auto-flags recommend the switch to flip when it is not (§10.4).<br>• **The switch restores exactly.** `promoted_predictor = false` restores the LO view: draws read each LO's own evidence, and no AD readiness numbers are shown.<br>• **Propensities.** Randomized draws keep exact, logged propensities (A7).<br>• **Supersedes** the 2026-10-14 version, under which the subject view and the readiness numbers waited for promotion by the harness rule, and the earlier default, under which selection itself waited |
| D4 | Live outside forecasters | On: the item-only LLM once per item revision when it is prepared for the pool, with a one-time backfill; the LLM with history (Codex on the subscription) and the Decider (OpenRouter, ~$0.50/day cap) per presentation. Learning trust needs hundreds of outcomes (§8.3), so collection should start early. Off the critical path |
| D5 | Rating tap placement | Beside Submit, before feedback; optional; hideable per session |
| D6 | Overlap exploration share | `q = 0.10` over items with `[0.55, 0.90]` predicted success |
| D7 | Required level for certification | The capability's entry point `e_k` (level 1 on every ladder), unless a commitment's milestone contract or a component's `min_task_features` sets a harder feature point (§9.4). Requirements are feature points, never level numbers. Full mastery is a separate label, never a certification requirement by default |
| D8 | Learner "easier/harder" and "too easy/too hard" | Keep today's owner-approved effects (self-report evidence package, claims). AD excludes the `self_report` rows and the claims these requests write (`rung_variant_request`, `learner_report`). It does not read the requests themselves in v1, because they come after feedback (§10.7). Nothing is counted twice. Replacing the 0.3-mass package is a separate decision (§16) |
| D9 | Feature-audit judge | Decider Tier-1 pattern, LLM fallback; certification uses the easier of stamped and audited features, never an estimated difficulty (D16) |
| D10 | AD observations | First graded attempt per surface group only; repeats stay FSRS's |
| D11 | Keep the generator's `difficulty` label | Yes, as signal `z_llm` with a learned weight (§3.3 shows it carried information here); never as the item's difficulty under AD |
| D12 | Exam target and exam-target calibration | Target = the per-dimension 0.8-quantile of family-collapsed tuples from practice-available exam/pset units; exam-target calibration (§6.2) off by default |
| D13 | Should the AD4 upgrade apply even if the shadow rebuild shows certificates changing? | Yes, after the owner reads the diff once. A certificate resting only on level-0 items was not a demonstration |
| D14 | Held-out exam features | Evaluation only. The target level comes from practice-available exam and problem-set units (router §15.6). Held-out tuples, where ingest already records them, feed only the coverage report (§9.5). The owner's 2026-10-14 framing ("only its features") is honoured without letting held-out units steer practice. Override: let held-out tuples define the *full-mastery label* (never the ladder, selection or generation), at the cost of a second target |
| D15 | Time to a usable estimate, and the sharing it needs | **Decided by the owner (2026-10-14; the split learned per vault since 2026-10-15):**<br>• **Target.** A usable estimate within 10–15 answered questions per subject, not per cell.<br>• **Sharing.** The model shares across cells through a subject level, capability offsets and feature effects, as field's `lo_general` and `+capability` do, and each facet and cell offset refines as its evidence arrives (§5.2). From 2026-10-15 it also shares through the learned couplings and loadings (§5.10, D19).<br>• **Gate.** G-AD2-18 measures the band-hit rate after 10–15 questions on synthetic learners; G-AD3-7 measures what coupling adds.<br>• **The prior split** is learned per vault among field's quarter, half and three quarters of the cold-start variance on the subject level (`ad_hyper_v1`, §5.5, §5.10). The LO view keeps the half split.<br>• **Honest limit (§5.9).** The target holds where the answers concentrate. A never-seen cell keeps part of its own offsets' prior variance and needs about 10 of its own answers to reach band mode under uniform sharing. A strong learned coupling to a well-practised topic shortens that, to about 6 at the grid's cap, but never to none. With `promoted_predictor` off, sharing is within an LO |
| D16 | What certification may read | **Decided by the owner (2026-10-14):** declared (stamped, or written in a target or requirement) and audited features only, the more conservative per dimension; never an estimated difficulty of any kind (A11, §9, G-AD4-13) |
| D17 | The primary scoring split | **Decided by the owner (2026-10-14):** field's first-attempt split (the first attempt on a never-seen LO), the forecasts on never-seen items that generation needs. It is the primary score for item-side signals and commissioned items (§7.3, §7.4, §8.3), and for the monitoring of the subject view, its couplings and reading, with their auto-flags (§10.4) |
| D18 | When AD1 starts, and where a new topic starts | **Decided by the owner (2026-10-15, "Ok agreed"):** AD1 starts after the "diagnosis input provenance" stage lands (`spec_mcp_frontend_c1.md` §4.8). From the AD2/AD3 successor on, a never-seen topic starts from the subject-level estimate (the subject view's shared terms, and its couplings, §5.10), never from the cold-start prior (§5.9, §6.1) |
| D19 | How the subject view relates topics | **Decided by the owner (2026-10-15):** a learned, vault-specific relatedness and implication model (§5.10).<br>• **Shape.** A sparse soft Q-matrix (which other facets answering an item implies knowledge of, and how strongly) and sparse LO couplings (each LO's few most related LOs), as extra shared terms in §5.2's hierarchy.<br>• **Priors.** A frontier LLM proposes their prior means per vault, from the LO and facet text, the concept and prerequisite graph and item stems. It never reads learner data, held-out text or exam text. It runs on an existing route under the spend cap, is ledgered in `judgment_ledger`, and is re-proposed when the vault's content changes.<br>• **Learning.** The hyperparameters (the shared versus topic-specific split, coupling and implication strength) are learned per vault as hierarchical latent state over the a-priori grid `ad_hyper_v1`, with wide uncertainty and zero in the support, so the learner's data can override the proposal.<br>• **Safeguards.** Sparsity, shrinkage, prediction-only influence (never certification credit), the kill switches and an auto-flag when the coupled model predicts first attempts worse than uniform sharing.<br>• **Scoring.** Against uniform sharing (`lo_general`, `@subject_uniform`) and topic-only (`@lo`) on first attempts at never-seen topics.<br>• **Supersedes** field F6, D2 and its §11 deferrals (the facet-level graph field, `idea_hier_llm_prior`) for this view only; the field spec records it |
| D20 | Reading as a learning opportunity, and the firewall exception | **Decided by the owner (2026-10-15), and confirmed later that day with per-kind weights:**<br>• **The exception is confirmed** with four limits (A12): only discrete events; prediction and selection only, never evidence or certification; learned weights; its own kill switch (`reading_opportunities`) and auto-flag (§10.4). The AD2+AD3 stage updates the rule text in `attempts/salience_firewall.py` and adds one narrow, tested carve-out that admits only the listed kinds (§5.11, G-AD3-13). Q8 is resolved.<br>• **Four kinds, each with its own learned weight** (§5.11): `reading` (a section read and a passage viewed, collated); `reader_tutor_exchange`; `worked_example`; and `in_passage_question` (RW1b's "let me try the next step" and "why does this step work", and the Reader's placed quick checks). An in-passage question graded as an attempt keeps its own evidence through the ordinary pipeline and takes its kind's increment in place of `γ`, so nothing is counted twice.<br>• **Diminishing returns in dose.** Each kind's effect is a saturating function of how many of that kind occurred before the next answer on the facet, with a-priori, versioned priors. The weights are hierarchical latent state learned per vault, never hand-set (§5.5).<br>• **Prediction only.** Reading shifts the *predicted* level, so the next draws aim higher, and is never evidence for mastery or certification (A2, A11, A12). It is scored by whether it improves first-attempt predictions after reading (§10.4).<br>• **The owner's goal.** The AD report's dose-and-burden analysis gives, per kind, the gain in cold-retrieval success per event and per minute with its uncertainty, the dose-response curve, the dose past which another event buys less than another practice question per minute, and a plain recommendation the Reader can show (§10.4).<br>• **Sources.** Existing reading records (`reader_section_progress`, `source_exposure_events`, reader tutor questions, worked examples studied, answered quick checks and owner-placed reading questions), frozen in a receipt, never a salience magnitude.<br>• **Supersedes** the morning's version, which had one linear rate per kind with section read and passage viewed apart, no in-passage kind, and the firewall note left open (Q8) |
| D21 | A live randomized dose arm in the Reader | **Decided by the owner (2026-10-15): live** ("For D21, lets have it live"), with the recommended floor and caps below; it ships on by default in the AD2+AD3 stage. The owner prefers live changes behind kill switches. At an eligible section boundary, one extra worked example or in-passage question is offered with probability `dose_floor = 0.10` each, and the Reader is otherwise unchanged; at most one extra offer per section and three a day; exact propensities logged before the offer (A7); its own switch `reading_dose_offers` and a burden auto-flag (§5.12, §10.4). The `none` arm is today's Reader, so the default withholds nothing that exists now. **Why a decision:** it is a live experiment in what the learner is offered, where the sources spec defers randomized designs between interventions and the workbench randomizes only among equally verified passages (`spec_reader_workbench_v1.md` §5.10). **Trade-off:** at the default floor, one learner's arm resolves only large effects, after thousands of eligible sections (§5.12); a larger floor buys speed with more offers. **Later:** the owner may adopt a recommended dose as the base policy; the floor keeps every variant in the support. **Override:** off, in which case the report keeps only the model's curves, labelled as observational |
| D22 | Self-check verdicts on in-passage questions | **Decided by the owner (2026-10-17), amending A12 limit 1 and D20** ("yes record that as a decision to amend a12 and add it to the adaptive difficulty scope"). The learner's matches / partly / no verdict on an answered in-passage question enters the subject view's prediction as its own learned term, `λ_matched` and `λ_missed`, with priors centred on 0 (§5.11). It is prediction and selection only: never evidence, mastery, facet recall, FSRS, certification credit, levels or scheduling credit. It is read from `judgment_ledger`, never from `ReaderObservationV1` (reader workbench G50 stands). AD1 freezes verdict rows in `ad_reading_opportunities`; the AD2+AD3 successor applies them under `reading_self_check`, with an auto-flag against `@subject:noverdict` and a self-check calibration section in the AD report (§10.4). **Why:** a *partly* or *no* is a fairly reliable admission of a gap and was being discarded; a *matches* is weak (judged with the answer shown and the book open), so the classes are learned separately per vault rather than hand-weighted. **Trade-off:** a little more state and one more switch; with few verdicts the term stays near 0 and changes nothing. **Unchanged:** RW1b records the verdict already (RW1a's `self_check` column and the ledger row), so no Reader change is needed. Missed answers still also reach learner-text gaps as `reader_formative` text |

---

## 16. Deferred, with triggers

| Deferred | Trigger |
|---|---|
| Per-family discrimination `a` | ≥ 3 generator families with ≥ 30 first-surface attempts each, and harness misfit in the slope (reliability-curve tilt) |
| Several candidates per commission, pick by re-forecast | Realized out-of-band rate > 40% over 100 commissions after AD2 |
| Grid or particle filter replacing ADF | `ad_threshold:grid` beats the base arm on band-region reliability with an interval excluding 0 |
| POMDP planning or amortized design policies `[rafferty2016]`, `[foster2021]` | A simulator validated against this learner's held-out data, and ≥ 1,000 AD decisions |
| LLM simulated-student panels as an item-side signal `[acquaye2026]` | A panel reaching ρ ≥ 0.5 against this learner's first-surface outcomes on ≥ 100 items |
| Band experiment: randomize the band centre by cell (0.70 / 0.75 / 0.85) and compare delayed cold success and minutes per level | ≥ 300 AD-selected practice attempts with matured `R_cold` |
| Per-capability bands | The band experiment shows a capability interaction |
| Reference anchor families (fresh instances of a stable family at a fixed point) | The confound diagnostic labels any `β` dimension "confounded" in two consecutive reports |
| Repeat-attempt observations in AD (a joint FSRS + AD arm) | The subject view has run live through two consecutive reports with no sharing flag, and the FSRS-plus-AD arm beats both in the harness |
| `teach_back` as an AD observation | A dialogue-to-outcome mapping validated in the harness (router §15.1 summaries exist) |
| Replace the 0.3-mass self-report package with rating-only evidence | Owner decision after AD2 shows `+rating` earning activation |
| Post-feedback request taps (easier/harder, too easy/too hard) as a separate, timestamped AD observation bound to their attempt | `+rating` earns activation, and ≥ 50 such taps exist |
| AD chooses placement's first-check item, restricted to level ≥ 1 | The subject view has run live through two consecutive reports with no sharing flag, and the placement assumption report shows first-check misses on items below the entry level |
| Serving the forecast ensemble (§8.4) | An ensemble beats the active predictor on log loss with an interval excluding 0 |
| Learning-progress bandit over families `[clement2015]` | Families with ≥ 5 recurring members per cell exist in a vault |
| `representation`, `time` and other `tools` dimensions | Items in a vault vary on them (data-check shows ≥ 2 levels with ≥ 20 items each) |
| Per-goal exam targets: a goal reads only the exam and problem-set units of its own source sets (§9.1, §9.5) | Goals gain `source_set_ids` (named as future in `vault/models.py:136-139`) and exam units record their source set |
| Exam units without a facet mapping feeding targets at goal scope (§9.5) | Per-goal exam targets exist, and data-check shows unmapped units are ≥ 25% of a goal's practice-available exam units |
| A joint model of help-seeking (asking for help or the answer as its own outcome, sharing `η`), as a harness arm against the censored factor of §5.3 | The AD report shows help or a reveal on ≥ 20% of first presentations over 200 of them |
| Pooled priors (§13) | The S9 export is built, and ≥ 20 consenting learners each have ≥ 200 first-surface attempts |
| Per-pair coupling and loading strengths learned from data, beyond the proposal times the vault strength (§5.8, §5.10) | Pooled priors exist (§13) for vaults with shared content |
| Separate strengths for the level correlation and for learning transfer along a coupling (one strength governs both in v1, §5.9) | The AD report shows first attempts on coupled topics after heavy practice elsewhere missing in one direction: a mean residual beyond ±0.1 logits over 100 such attempts |
| A learned head in place of the LLM proposal (an embedding or fine-tuned relatedness scorer) | Pooled data exist, or the coupling flag fires in two vaults whose proposals the owner judged sound |
| A finer or continuous hyperparameter posterior | The `:hyper_fine` arm beats the `ad_hyper_v1` grid on first attempts with an interval excluding 0 |
| Opportunity kinds beyond reading (a teach-back, a watched animation, a tutor explanation outside the Reader) as learning opportunities | Reading keeps its auto-flag clear through two consecutive reports, and the kind is logged with an LO mapping |
| Level-dependent reading effects in the state (a kind's curve that depends on the predicted level, the expertise reversal `[kalyuga2003]`), beyond the report's moderation lines | The dose arm's level-band moderation shows a contrast with an interval excluding 0 for some kind, in two consecutive reports |
| Subkind weights in the state (a style of in-passage question, a tutor answer mode, a section read apart from a passage view), beyond the report's moderation lines | The report's moderation for a subkind excludes 0 in two consecutive reports, with ≥ 100 events of each subkind |
| An adaptive offer policy (a bandit over the dose arm's variants, or offers that follow the useful dose automatically) | The dose arm has ≥ 300 matured cold outcomes per variant, the owner has adopted a base policy, and the offer's effect excludes 0 for some variant; the policy keeps the floor and reads no minutes or other salience magnitude |
| Federated or differentially private estimation | Pooled priors are computed anywhere other than the contributor's own machines |

---

## 17. Open questions

1. **Q1. Current data.** The §3.3 numbers come from the two-month-old committed snapshot. The same measurement on backup copies of the current working vaults was not run in this stage. AD1's `learnloop ad data-check` reproduces it on the owner's copies (owner-run). Until then, the label-weight prior `α_llm` (§5.5) rests on one stale vault.
2. **Q2. Generator compliance.** How often does the generator realize the requested feature point, by the audit's reading? Unknown until AD1 audits run. A low rate would make the feature model weak and push the "several candidates" trigger.
3. **Q3. Unit-to-facet mapping for exam targets.** How many exam units carry a facet mapping in the inventory? A unit without one feeds no target in v1 (§9.5); spreading it over a goal's facets is deferred (§16). Measured by AD1's data-check, which counts mapped and unmapped units.
4. **Q4. Rating timing.** Is a pre-feedback tap acceptable friction, or should the rating ride the existing post-feedback "too easy/too hard" controls (fewer taps, outcome-contaminated)? D5 recommends pre-feedback; the AD2 `+rating` arm will show whether it earns its place.
5. **Q5. Data volume for monitoring.** With about 10³ attempts a year and the §8.3 illustration, the harness comparisons may take months to resolve. Since the owner's direction of 2026-10-15 (D3), that delays no behaviour: the subject view, its couplings and reading steer from the start, a new LO starts from the subject-level estimate (D18), and the monitoring can only flag. Until a comparison resolves, the report says "can't tell yet" (§10.4).
6. **Q6. Motivation vs learning.** The research shows easier practice wins short-term engagement and harder practice wins learning `[papousek2016]`. Should the band move with the learner's session state (re-entry after a gap; frustration signals) before the band experiment reports? This spec keeps it fixed.
7. **Q7. Proposal quality.** How often does the relatedness proposal name couplings and loadings that this learner's answers support? Unknown until the AD2/AD3 successor runs. G-AD3-7 bounds the cost of a wrong proposal on synthetic vaults, the hyperparameter posterior shrinks it live, and the coupling flag catches what remains (§5.10, §10.4).
8. **Q8. Records outside this spec. Resolved 2026-10-15: the owner confirmed the firewall exception (D20). Recorded 2026-10-19 by the AD2+AD3 stage:** the firewall module's rule text names the exception and its four limits, `learning_opportunity_events` is its only path with the allowlist moved there (AD1's sweep reads the same list), G-AD3-13 tests it beside the unchanged tests, and dated notes are in `spec_knowledge_model.md` §8.3 and `spec_p3_reader_integration.md` §8.2 and §15.4. The supersessions here touch documents this revision does not edit: KM §8.3's held-out-support condition (A6), and the reading-signal firewall's standing rule, which names "posterior, readiness ... scheduling" (P3 §8.2, §15.4; `attempts/salience_firewall.py:4-8`). The AD2+AD3 stage updates the firewall module's rule text to name the confirmed exception and its four limits, and adds the narrow, tested carve-out of §5.11 (G-AD3-13), with every existing check and test unchanged. It also adds dated notes to the knowledge-model spec (§8.3) and the P3 reader spec (§8.2, §15.4), scoped to AD's prediction-and-selection use.
9. **Q9. Will the learner take the offers?** The dose arm identifies an offer's effect; the effect of what is offered shows only on occasions when the learner takes it (§5.12). If extra offers are mostly dismissed, the arm learns little and the burden flag fires. The AD report gives uptake per variant from the first week; a low uptake is a prompt to change the offer's wording or place, not the floor.

---

## 18. Agent prompt template (one per phase)

Fill in `<n>` (`1`, `23` for AD2 and AD3 together, `4` or `5`), the base commit and the worktree path. Give it to a fresh agent in the repo. The Codex review and fix steps follow `implementation_goal.md` §2. This spec stage itself was docs-only: it changed no code, ran no paid call, and its record is `docs/reviews/adaptive-difficulty-spec.md`. Everything below is for the implementing phases.

```text
You are implementing LearnLoop stage "adaptive-difficulty-ad<n>" (AD1 | AD2+AD3 | AD4 | AD5)
of docs/specs/spec_adaptive_difficulty_v1.md, in the worktree <path> on branch
adaptive-difficulty/ad<n> (base <commit>).

Read first: CLAUDE.md; docs/specs/implementation_handoffs.md §0 (standard rules and
invariants); docs/algorithm-change-playbook.md; the spec's §2 (standing constraints),
§3.1 (code truth; re-check every citation you rely on), §5 (model), §11 (successors,
switches, tables, replay invariants) and your phase's row in §14 with every section it
cites; db/table_roles.py. Then write a short plan (files, migrations, successor and kill
switches, spend caps and model routes, judgment_ledger writes, tests) to
docs/reviews/adaptive-difficulty-ad<n>.md and proceed.

Prerequisites (§14 "Order"): AD1 starts once the "diagnosis input provenance" stage has
landed (D18). AD2+AD3 can start from main, but its serve-time receipts and serving need
AD1's tables merged, and it merges as one successor only after its gate passes and the
owner has read its report; it waits for no harness result (D3). AD4 needs AD1 merged
(audits); AD5 needs AD2+AD3 merged. If yours is not met, stop and say so.

Build exactly your phase: its "Builds" list, its tests (each written first and failing
for the stated reason), its switches. AD1 changes nothing served. AD2+AD3 (one
successor), AD4 and AD5 are successors: each takes the next free mvp-0.N at merge, and
with a switch false its part is byte-identical to the predecessor. Live AD decisions read
the subject view with promoted_predictor on and the LO view with it off (A6, D3). Never
write evidence, mastery, FSRS or certification from AD's state, its couplings or reading
(A2, A12), and never let certification read an estimated difficulty (A11). AD2+AD3
updates the reading-signal firewall's rule text and adds only the carve-out of §5.11
(G-AD3-13), leaving every existing firewall check and test unchanged; its dose arm
(§5.12) ships behind reading_dose_offers and never reads a salience magnitude. AD2+AD3
pre-registers each arm's constants and the thresholds of G-AD2-18, G-AD3-7 and G-AD3-11
in docs/reviews/adaptive-difficulty-ad23.md before the first replay on owner data.

Paid routes: the feature audit on the existing tier1_decider route (the Decider,
perplexity/pplx-decider-v1.1-27b on OpenRouter) with its LLM fallback; llm_v1:item and
llm_v3:llm (Codex on the owner's subscription, recorded estimated_only); llm_v3:decider;
the relatedness proposal (AD2+AD3) on ai.routing.llm_probability_llm, which never reads
learner data or held-out text (§5.10). All go through the spend framework with --dry-run, inside
adaptive_difficulty.daily_spend_cap_usd, and append to judgment_ledger.

Hard rules:
- Work only in your worktree; never edit the main checkout; never commit changes to
  fixtures/linear_algebra, fixtures/probability or fixtures/arxiv_v2.
- Tests use fakes (tests/structured_ai.py StructuredClientFake; tests/helpers.py builders).
- Paid calls only on backup-API copies (learnloop.db.copies.copy_tree_with_databases) under
  fixtures-local/, dry-run first, inside caps; record calls and cost in your review file.
  Never read ~/.config/learnloop or any .env file; the app loads keys itself.
- Migrations from the next free number; classify tables (a DERIVED table has exactly one
  replayer); upgrade the head fixture (CLAUDE.md).
- Pin new or extended sidecar RPCs desktop-only in tests/test_mobile_allowlist.py.
- If the spec contradicts the code, record it in the review file and take the conservative
  option (switch off, no evidence writes) if work can continue, else stop.
- Don't merge, push, rebase onto other branches, or delete branches or worktrees.
- End every commit message with: Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

Done means: your phase's gate tests pass; uv sync --extra dev --extra mobile;
TMPDIR=<path>/fixtures-local/tmp uv run pytest -n auto; uv run pytest -m durability;
uv run lint-imports --no-cache; npm run typecheck && npm test if the app changed; the DB
reference generate and validate scripts if the schema changed; a shadow rebuild on a
fixtures-local copy for any successor; git diff --check. Owner-run commands (the AD1
backfills, the relatedness proposal's backfill, learnloop ad data-check and learnloop ad
report on the owner's copies, AD4's shadow rebuild) are listed in the review file, dry-run first, never run by you on the
working vaults.

Return: summary, final commit, review file path, gate results with pass counts, owner-run
commands, open questions.
```

---

*Related: `spec_learner_field_v1.md` · `spec_knowledge_model.md` §8 · `spec_p3_reader_integration.md` §8.2, §15.4 · `spec_reader_workbench_v1.md` §4.2, §5.10, §6.1 · `spec_reader_quick_check_producer.md` · `spec_mcp_frontend_c1.md` §4.8 · `spec_action_router_v1.md` §15.2, §15.5–15.6 · `plan_router_r2_v1.md` §5 · `spec_measurement_efficiency_v1.md` §3–5 · `spec_probe_eig_redesign.md` §2.3, §7 · `spec_storage_sync_v1.md` §6.12 · `docs/algorithm-change-playbook.md` · research appendix `docs/specs/research/adaptive_difficulty_sources_v1.md`*
