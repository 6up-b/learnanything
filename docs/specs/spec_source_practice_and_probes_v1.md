# Canonical sources as a shared instructional service: practice, probes and explanations from the learner's sources (v1)

**Status:** draft for owner review (2026-10-12), revised 2026-10-13 after the Codex review and its re-review (`docs/reviews/sources-spec-codex-review.md`: F1–F10, then F2 and F8 reopened and F11–F13). A backend track on its own branch (`sources/canonical-practice`), started on the owner's direction of 2026-10-12: "build the router and sources path as its own backend track now". The Reader workbench spec (`docs/specs/spec_reader_workbench_v1.md`, branch `docs/reader-workbench-spec`) owns every Reader surface and consumes this track. This track builds no Reader UI.

**Source.** Round 3 of the owner's design dialogue, `docs/brainstorming/Improving Reader's design.md` lines 1088–1461. The file is committed on `docs/reader-workbench-spec` at `2d08581e` and is byte-identical to the untracked copy on `main`. This spec also takes the retrieval parts of rounds 1–2 (lines 242–262, 337–427, 820–877). The coverage audit `docs/reviews/reader-dialogue-coverage.md` (same branch, `8deb75be`) classified round 3's ideas as its rows 86–115 and proposed restorations RS1–RS10. This spec takes over RS1 (every step), RS4, RS6, RS7 and the backend half of RS8, and gives every round-3 idea a disposition (§12): built, narrowed with a reason, or deferred with a trigger.

**Owner decisions in force (2026-10-12):**
- The recommended defaults recorded in each spec are accepted. The owner may override any of them at its checkpoint (§18 lists this spec's).
- Codex on the owner's ChatGPT subscription may run every paid LLM role, with no bound on physical requests. Its cost is estimated from token usage (`estimated_only`; Slice A plan §5 rule 6).
- The Decider is `perplexity/pplx-decider-v1.1-27b` on OpenRouter.
- Frictionless defaults: honest labels and generous defaults; live changes behind kill switches; no shadow stages by default.

**Standing owner preferences applied here:**
- LLM judgment over hand-picked constants. Embeddings shortlist and judges decide; no cosine cutoff is hand-set.
- **No artificial count caps.** Value of information decides how many: EIG over rival hypotheses, and EVSI for the next decision. The plan's minutes and the spend caps bound everything.
- Learner text over skip buttons.
- Replay makes zero model calls. Every paid batch command has `--dry-run` and spend caps. Calls leave receipts, and every verdict goes to `judgment_ledger`.
- Eval roles use strong, cheap models: Claude Haiku 5.5 or GPT-6 Luna via OpenRouter, or the ChatGPT-plan provider (now on `main`). Never `gpt-4.1-mini`.

**Relationship to other specs:**

| Spec | Relationship |
|---|---|
| `spec_embedding_consumers_v1.md` | T6 (§9, built) is the only retrieval substrate: `search_spans`, the scopes, `verify_spans`. Phase 5b's `find_practice` (§5.9) and its listwise judge are extended here, not duplicated. PF (§5.1–§5.4) supplies the family contract and the verifier. R1–R6 hold |
| `spec_reader_workbench_v1.md` | Consumes this track. RW4a's library ask and compare, RW4b's exercise fallback, RW6b's follow-ups and any RW4c the Reader revision adds are UI over the functions built here. One shared contract for `find_sources` and `compare_sources` (§9.1, §9.4): the Reader's §7.2 signature, policies and RW4e role filter (checked at `df23187e`) are its base, and this spec adds the intents. The value-of-information adapter that RW6b's §9.3 needs is built once (§8.3) |
| `spec_action_router_v1.md` | §15.3 sketched "canonical sources as a retrieval tool for the router". S4 builds that tool interface and the tutor's use of it now. R2 wiring stays deferred, with a trigger that supersedes §15.3's (§10.6). Item selection within a block stays with P4's selectors and `find_practice` (router §1) |
| `spec_daily_loop_v1.md`; `daily_loop_frictionless_defaults.md` | DL3's "Practice on…" box (§6.9) calls S0's RPC. DL1's learner picks are the serving path for proposals. DL2's "Check once" serves the dated checks RW6b creates from S2's valuations. C3 ("an unverified solution never certifies anything"): S1 shares DL3's attempt-time certification gate (DL §4.4) for imported exercises' keys (§7.3a) |
| `decision_value_and_commissioning_spec_v1.md` | EVSI (§6.4), the likelihood arms (§6.2), the result translation (§6.5), invariants 4–6, the repair-linked cold-outcome chain (§4.3) and repair effectiveness (§5.3). S5's outcome states follow §4.3. S2 and the Reader's RW6b are `rank_feasible`'s first live consumers, whichever merges first; a verdict licenses learner effort only from a likelihood regime that §6.2 allows to (§8.3.3) |
| `spec_slice_a_practice_and_field_v1.md` | Phase 5a's PF-b verifier and sandbox. Phase 5b's practice index |
| `spec_p3_reader_integration.md` | Invariants 6 (reading is not evidence), 9 (authorship is never laundered) and 10 (cold means no source cue) hold everywhere here |
| `spec_blind_grading_diagnosis_split_v1.md` | The grader stays blind. Retrieval never enters `BlindGradingContext`. Misconception targets are read from the diagnoser's overlay, never from raw grader rows |

**Citation convention.** Every `file:line` was re-checked in this worktree at `57d31c63` (again on 2026-10-13 for the review and re-review revisions; the branch changes no code) (`main`: migration head 180, latest algorithm `mvp-0.14`, the ChatGPT-plan provider merged). Python paths are relative to `src/learnloop/` (sidecar paths, which start with `learnloop_sidecar/`, to `src/`), frontend paths to `apps/learnloop-tauri/src/`, and migrations and docs to the repo root. A bare `:n` refers to the file cited just before it. Unmerged work is named by its branch. "Brainstorm L*n*" means line *n* of the dialogue file.

---

## 0. Thesis

The dialogue ends on the question this track answers (brainstorm L1455–1457): *"Given what this learner is trying to accomplish, what they have already demonstrated, and where their understanding remains uncertain, which existing piece of instructional material is most likely to help them progress—and how should it be used?"*

LearnLoop already has every part needed to answer it, but the parts don't meet:
- **`find_practice`** searches the vault's practice items in natural language, under typed constraints, and proposes without serving. Nothing in the app calls it (§3.2 item 1).
- **T6** retrieves source passages for the tutor and the library. It treats exercises and solutions only as things to exclude (`source_retrieval/corpus.py:158`, `:327`).
- **`import_exercises`** turns a textbook exercise into a practice item with a verbatim stem. It runs only when the learner selects the exercise in the Reader, and the AI-completed answer key is never checked (`content/authoring/exercise_authoring.py:241`, `:352`, `:540`).
- **PF-b** can verify an answer key with a solver panel and a sandboxed sympy check, but only inside its own generation run (`ops/pf_generation.py:1027`).
- **The probe EIG and EVSI machinery** values questions against rival hypotheses. Nobody has asked it about source material, and EVSI runs only in shadow (`diagnosis/causal_orchestrator.py:1493`).
- **Misconceptions** store the sources that correct them, and nothing reads them (`diagnosis/misconceptions.py:504`).

**This track joins them into one service.** The learner's sources become an instructional substrate with four operations:
- `find_practice`: practice items and textbook exercises;
- `find_sources`: passages for an instructional intent;
- `compare_sources`: syntopic retrieval;
- `find_facets`: the registry lookup router §15.3 asked for.

The tutor calls them now and the router will at R2, both through one typed tool interface. The Reader calls them through its own UI.

Five rules from the dialogue carry the design:
1. **Selection stays separate from retrieval** (brainstorm L1171–1205). Retrieval finds eligible candidates. Value of information and the existing serving paths decide what the learner gets. A tool proposes; it never administers.
2. **Don't eliminate cards; change what they represent** (L1131–1169). The family or card is the capability. A surface can be the verbatim textbook exercise, a generated variant or another verified presentation. A source exercise still needs a competency mapping, a checked key and an exposure check before it can stand as an independent test.
3. **The caller's context decides what may be retrieved** (L1358–1380). Contamination of independent assessment is the biggest risk. The policy comes from the server-side context of the call, never from a model's arguments.
4. **Source-authored, AI-written and learner-written content stay apart** (L1282). Every result carries its source and revision identity. "Checked" appears only after a check that is not an LLM.
5. **Retrieval joins the evidence loop** (L1382–1406), as a record of what was shown or served and what happened next. Reports read it; serving does not, until a randomized comparison exists.

---

## 1. Scope

**In scope (v1).** Six phases (seven builds, since S2 has two); sizes and order are in §15.
- **S0. `find_practice` gets real callers.** The tutor's "Practice this" offers, the daily plan's learner picks, and the Reader's and DL3's boxes, all through the same RPC. A proposal reaches the learner only through an existing serving path. What is displayed is recorded as an impression, apart from what was merely retrieved (§6.5).
- **S1. Textbook exercises as practice candidates (RW4c).**
  - A source-exercise arm in `find_practice`.
  - Import through `import_exercises`, keeping the verbatim stem.
  - The AI-completed key checked by a verifier ladder built from PF-b, with honest labels.
  - Certification follows the key: attempts on an unverified key schedule and teach but never certify (C3), through DL3's attempt-time gate. A check verifies only the exact stem, key and rubric it checked, so an edit needs a fresh check. This one part of S1 is an algorithm successor (§7.3a).
  - Attachment as a surface of a matching practice family.
  - Items that point at their canonical source exercise.
- **S2. Discriminating search**, in two phases.
  - **S2a:** `PracticeConstraints` gains `intent` (`practice` | `discriminate` | `retention` | `remediate`), `target_hypotheses` and the dialogue's typed filters. Candidates are valued by EIG over the learner's rival hypotheses, and by EVSI where a decision is pending, through one valuation input whose likelihood regime says what a verdict may license (§8.3). There is no count cap.
  - **S2b:** intervention needs are fulfilled from the sources before generating. It is an algorithm successor.
- **S3. `find_sources` with intents** (`explain` | `remediate` | `alternative` | `worked_example` | `compare`).
  - Misconception-conditioned retrieval that finally reads `correction_source_span_ids`.
  - `compare_sources`, the first-class syntopic operation.
- **S4. The tool interface.**
  - Typed requests that the tutor's and the router's models can issue, each with a receipt and `judgment_ledger` rows.
  - The tutor uses it now.
  - Router R2 wiring is deferred, with a trigger that supersedes router §15.3's.
- **S5. Retrieval in the evidence loop.**
  - A replayable intervention → outcome record, and its report.
  - The records the EVSI calibration track needs to check value-of-information predictions.
  - Reports only.

**Cross-cutting:** the contamination policy (§5).

**Not in scope:**
- any Reader surface (RW4a/b, the Ask rail, the compare UI, figures): the Reader spec;
- router R2 itself;
- generating new practice: PF-b's job; S2b only tries the sources first;
- any change to grading or evidence semantics. The one certification change is C3's gate for unverified answer keys (§7.3a), shared with DL3.

**Deferred, with triggers in §19:**
- router R2 wiring, and choosing the action and its material together;
- a licensing likelihood regime for item point models and screened exercises (the reserved arm A), and a measured reading-exposure adjustment: the calibration track's, on S5's records;
- page-image retrieval;
- source exercises as formal probe instruments;
- randomized choice between interventions, and a learned per-learner intervention preference;
- retrieval-initiated explorable figures;
- automatic background harvesting of source exercises;
- an MCP or OS-level service;
- cross-LO candidates in the post-attempt follow-up chooser.

---

## 2. Standing constraints

- **SC1. Tools propose; serving paths serve.** No operation here writes attempts, evidence, mastery, FSRS or scheduler state, or plan items. A proposal becomes practice only through one of:
  - `plan_learner_pick` (`learnloop_sidecar/handlers/daily_plan.py:256`) or the open-list pick when the plan is off;
  - the post-attempt follow-up path;
  - DL2's "Check once";
  - the quick check's ordinary pool.

  A path that serves a candidate *as an independent check* re-checks its eligibility at serving time (§5.4).
- **SC2. The caller's context sets the policy.** Each call's retrieval policy (§5.1) is derived on the server from where the call comes from: tutor context, item, attempt, cold status. A model's arguments can narrow a request; they can never widen its policy.
- **SC3. Results shown to a model withhold answers.** A tool result returned to an LLM never carries an expected answer, a rubric, a solution block or an item reserved for a cold check. The one exception is the internal `authoring` policy, which never reaches a learner-facing model (§5.3).
- **SC4. Independent checks are unexposed.** A candidate offered as a discriminating or retention check must not have been exposed: not its own span, not its solution, not a revealed sibling, not an equivalent worked example the learner just studied, and not a prompt the learner was already shown in an earlier proposal (§5.4).
- **SC5. Honest labels.** Every result says whether its content is source-authored, AI-written or learner-written. An answer key is "checked" only after a sympy check or a quote-verified source solution passes (§7.3), and only a verified key certifies (§7.3a). Valuations are labelled as LearnLoop's estimates, with their likelihood regime (§8.3.3).
- **SC6. Value of information, not counts.** How many checks a learner gets comes from the valuation's stop rules (§8.3.4: `evsi.rank_feasible`, `scheduling/evsi.py:366`, and `robust_composition.evaluate_selection`, `diagnosis/robust_composition.py:353`, or its credible-set form for mixed ensembles), never from a constant. The numbers in this spec are caps on money, time, prompt size or display, never thresholds that decide learning. Every such number is labelled with what it bounds. Missing or unstable machine data never buys learner effort: it yields a typed abstention or exclusion, never a fallback order (decision-value invariants 4–6).
- **SC7. Embeddings shortlist; judges decide.** Ranked lists are fused by reciprocal rank, as T6 and Phase 5b do. Every learner-visible pick passes an LLM judge, a verifier or an exact key.
- **SC8. Receipts and ledger.** Every paid call goes through `PaidCalls` with a receipt. Every LLM, verifier, Decider or learner-card verdict appends to `judgment_ledger`. Every tool request a model or an external agent issues leaves a `source_tool_calls` row (§10.4); calls from code (the plan, S2b, the Reader's UI) are recorded on the operation's own receipt (the proposal row, the find-sources manifest, the comparison row).
- **SC9. Replay makes zero model calls.** Paid outputs are persisted and never regenerated on rebuild. S5's DERIVED outcome table has exactly one replayer, which reads persisted rows only.
- **SC10. Spend.** Every paid step uses `ai/spend.py`: per-route caps, a daily cap for metered routes, `--dry-run` on every batch command. Codex is `estimated_only`. A metered route without a price is skipped and labelled, never guessed.
- **SC11. Backend only.** The only UI this track touches is outside the Reader: proposals and offers in `components/AskOverlay.tsx` for the practice, feedback and library contexts, and the provenance and key-status line on the practice screen (§6.4, §7.4). The reader context's offers are returned by the backend and rendered by the Reader spec.
- **SC12. Layering.** The homes named in this spec are proposals; a phase agent may move code, but only within these rules.
  - **A composition layer.** A new package, `learnloop.instructional` (not a domain package), holds the contamination policy, the valuation adapter, the source-exercise arm, the tool registry and dispatcher, the tutor offers, S2b's need step and S5's report. It composes `practice_index`, `source_retrieval`, `diagnosis`, `scheduling`, `substrate`, `content` and `ops`. S5's write points call the new store (`db/stores/source_service.py`) directly: `db` sits below every domain, so recording an intervention from the tutor or the remediation path needs no import of the service.
  - **No cycles.** Nothing it imports imports it back. The domain packages (`DOMAIN_PACKAGES` in `tests/test_architecture.py`), `practice_index` and `source_retrieval` reach it only through injected callables, as the sidecar injects `TutorSpanProvider` today (`learnloop_sidecar/handlers/tutor_qa.py:235`). This matters at once for `find_practice`: `source_retrieval` imports `practice_index` (`source_retrieval/search.py:38`, `:39`), so the exercise arm and the valuation are passed into `find_practice` rather than imported by it (§7.1, §8.3). An import-linter contract enforces this (G17).
  - **S1's import pipeline** (author, check, write, attach) lives beside `import_exercises` in `content/authoring/`, with its job handler in `content/pipeline/jobs.py`, and needs nothing from `instructional`.
  - **No `daily_plan` import.** Expected minutes arrive through an injected estimator. The plan calls the service (learner picks, DL3's box), so the reverse import would make a cycle.
  - **The repository's architecture tests hold** (`tests/test_architecture.py`):
    - new SQL writes go in a new registered store, `db/stores/source_service.py`, added to `REGISTERED_SQL_OWNERS`, and in `db/stores/practice_index.py` for the proposal columns;
    - no package imports another package's private name, so what the service needs is made public in its own module first: PF's run-class methods as `ops/pf_verify.py` (S1), `effective_hint` in `source_retrieval/corpus.py` (S1), and a public `misconception_discrimination` in `diagnosis/followups.py` (S2a);
    - no new function-local cross-domain import edge without architecture-owner review (the frozen inventory `tests/architecture_function_local_domain_imports.txt`).

---

## 3. Code truth (audited 2026-10-12 at `57d31c63`)

### 3.1 What exists

| Piece | Where | What it does now |
|---|---|---|
| `find_practice` | `practice_index/retrieval.py:727`; `PracticeConstraints` `:111`; admission `:545`; rerank `:511`; dry run `:660` | Recall (item BM25 plus item vectors, or the two-level dossier path when an evaluation approved it, `:412`), an LLM listwise rerank (`practice_rerank`), and admission under the scheduler's eligibility rules. It writes a proposal receipt (`:799`) and never serves |
| Its callers | CLI `learnloop practice-index find` (`cli/practice_index.py:138`); RPC `find_practice` (`learnloop_sidecar/handlers/practice_index.py:40`); agent tool `run_find_practice_tool` (`practice_index/tool.py:48`) | The CLI is the only caller. No frontend file calls the RPC, and nothing in the app calls the tool function (only `tests/test_practice_index_find.py` does) |
| Proposal receipts and usage | `migrations/169_practice_index.sql:32`; `practice_index/usage.py:39` | One row per call. Learner taps (`practised`, `skipped`, `too_easy`, `not_what_i_asked`) and an attempt join append `judgment_ledger` rows (task `practice_usage`) |
| Admission | `practice_index/admission.py`; `scheduling/serving_exclusions.py:94` | Lifecycle, exam reserves, variant holds, staged ownership, the diagnostic freshness reserve, servability, reserved cold checks, and answers revealed within the cold retrieval delay (1 day, `diagnosis/remediation.py:30`) |
| T6 span search | `source_retrieval/search.py:126` (`search_spans`); caller lists through `extra_lists` (`:138`, `:242`) | FTS5 BM25, dense and rewrite lists over a scope, fused by RRF. No role, LO or facet filter except through the scope |
| Scopes and exclusions | `source_retrieval/corpus.py:104` (library), `:450` (teaching), `:269` (teaching exclusions), `:385` (item exclusions), `:327` (role-hint exclusions), `:158` | The teaching scope excludes non-teaching roles and assessment-linked spans. In item-bound contexts it also drops the item's linked passages and every `exercise` and `solution` block |
| Tutor grounding | `source_retrieval/tutor.py:70` (`TutorSpanProvider`); `tutor/tutor_qa.py:480`, `:1231` | Retrieval on the learner's question, the answer-overlap filter (`source_retrieval/tutor.py:125`) and listwise verification, in the practice, feedback and library contexts. The reader context uses only the selection and its neighbours (`tutor/tutor_qa.py:1299`) |
| The shared listwise judge | `practice_index/listwise.py:149`; T6 verification `source_retrieval/verify.py:156` | Skip check, request identity, ledger-served cache, one capped call plus a retry, append-only verdicts |
| Block roles | `ingest/block_roles.py:14` (`ROLES`), `:124`; `source_blocks.role_hint` (`migrations/032_source_layer.sql:75`) | One deterministic hint per block: `definition`, `theorem`, `proof`, `worked_example`, `exercise`, `solution`, `summary`, `reference`, `equation`, `figure`, `table`, `ordinary_prose` |
| Exercise import | RPC `reader.import_exercise` (`learnloop_sidecar/handlers/reader.py:1512`); job `content/pipeline/jobs.py:2215`; `content/authoring/exercise_authoring.py:241` | A Reader selection becomes practice items. The stem is re-anchored verbatim (`:385`); one call completes the answer, rubric, facets, hints and rung metadata (`:352`); when the author names no facet, the item gets the LO's whole facet union (`:433`); provenance is `canonical_extract` with block-span refs (`:523`), an origin AI authoring proposals over canonical sources share; the item is written at once (`:540`), and a `learner_item_authored` event with `mechanism = reader_exercise_import` marks it (`:544`–`:551`). Its practice mode is authored and it has no `expected_minutes` |
| PF-b verification | `ops/pf_generation.py:1001` (panel solves), `:1027` (agreement plus sympy), `:1124` (ensemble), `:806` and `:835` (source-anchored span support); sandbox `content/authoring/pf_sandbox.py:84`, `:120`, `:341`, `:365` | Solve-first panel agreement, an LLM-written sympy equivalence check in bubblewrap, and a quote-verified span that the reference verifier confirms supports the answer. Every verdict goes to `judgment_ledger`. `_agreement` returns only the combined per-solve result: `confirmed = (not symbolic) or confirmations[index] is True` and `agrees.append(llm and confirmed)` (`ops/pf_generation.py:1050`–`:1051`), so for a numeric answer a sympy run that failed counts as disagreement, and the LLM-only agreement appears only in ledger rows. An absent sandbox raises `SandboxUnavailable` (`content/authoring/pf_sandbox.py:84`); a PF run refuses up front (`ops/pf_generation.py:1713`) |
| Families | `vault/models.py:642` (`ActivityFamily`), `:743` (`family_id`); `substrate/families.py:147` (`apply_family`); `db/stores/families.py:76` (`append_membership`); `ops/pf_publish.py:189`, `:267` | Items carry `family_id` plus `variant_relation`. Membership events are append-only (`migrations/168_activity_family_membership.sql:9`) |
| Probe EIG | `diagnosis/probe_families.py:467`, `:536`, `:621`; `diagnosis/probes.py:786`, `:682`, `:649`; `diagnosis/followups.py:1482`, `:1532`; `diagnosis/probe_targeting.py:621`, `:694`; `diagnosis/probe_episodes.py:818`, `:1386`, `:1576` | EIG over locked hypothesis sets, per-facet EIG over `hypothesis_marginal`, the misconception-discrimination gate and greedy conditional blocks. Live in the scheduler and the post-attempt follow-up slate |
| EVSI | `scheduling/evsi.py:199` (`robust_evsi`), `:293` (`DiagnosticCandidate`), `:366` (`rank_feasible`); `scheduling/action_loss.py:235`; `diagnosis/robust_composition.py:353`; constants `:48`, `:49`, `:55` | Robust EVSI in minutes over a credible set of `P(E|H)` matrices, ranked by LCB per minute, with a stop rule, typed exclusions (`EVSIInputError`, `scheduling/evsi.py:68`) and abstention. A candidate's prior must have a live basis (`LIVE_VALUE_PRIOR_BASES = ("support_weighted",)`, `:65`). It returns one best candidate, not a batch. The only live-path caller is a shadow recorder (`diagnosis/causal_diagnostic_selector.py:300`, called at `diagnosis/causal_orchestrator.py:1493`). `staged_policy.DiagnosticSelector` (`scheduling/staged_policy.py:351`) is never constructed. λ = 1, burden = 0 and 60 minutes per nat are all labelled heuristic |
| Likelihood arms | `diagnosis/causal_diagnostic_selector.py:53` (`LIKELIHOOD_REGIMES`), `:195` (`likelihood_regime_for_candidate`), `:130` (`build_causal_loss_table`) | Arm A (a calibrated causal channel) is reserved: "no calibrated channel exists". Arm B is a noiseless partition built from complete blind bundles with an `H_OTHER` disposition; arm C is a structural audit. The decision-value spec (§6.2) lets arm B license a skip, never live learner effort |
| The robust probe path (live, `mvp-0.8` and later) | `diagnosis/probe_robust.py:51` (`use_robust_probe`), `:75` (`resolve_episode_channel`), `:199` (`instrument_ensemble`), `:288` (`robust_selection`); `diagnosis/robust_composition.py:210` (`build_ensemble`), `:293` (`observed_update`) | Compiled probe-card rows composed with a pinned, calibrated grader channel into a deterministic ensemble, valued by robust EIG per second with `evaluate_selection`'s stop rule and action-agreement abstention (`act` \| `stop` \| `couldnt_reliably_distinguish`). This is the one live path where a value verdict already licenses a probe |
| Item EIG | `diagnosis/probes.py:487` (`conditional_distribution`), `:595` (bridge sensitivity 0.6, specificity 0.9), `:682`, `:731` (`facet_conditional_distribution`), `:786` | Point `P(outcome | H)` tables from IRT parameters and an estimated discrimination row or the bridge default. The EIG functions build these tables internally and return a float |
| Hypothesis state | `hypothesis_sets` (`migrations/001_initial.sql:276`) with `probe_observations` (`migrations/028_probe_episodes.sql:94`); `causal_hypotheses` (`migrations/118_causal_attribution_p1.sql:5`); `unresolved_cause_factors.candidate_causes_json` (`migrations/034_assessment_contract_snapshots.sql:36`); `facet_uncertainty.hypothesis_marginal` (`migrations/012_facet_diagnostic_state.sql:5`) | The rival hypotheses S2 values against |
| Remediation passages | `diagnosis/remediation.py:173` (`prescribe_remediation`), `:233` | For a misconception's target and confused-with facets, the first parseable linked span of each (`:196`–`:215`, ending in `break`). Delivery is recorded as `remediation_delivery` exposure |
| Exposure ledger | `source_exposure_events` (`migrations/150_remediation_delivery_exposure.sql:22`, a closed `context` CHECK); reveal ledger kinds `attempts/reveal_ledger.py:37`; `reader_section_progress` (`migrations/106_reader_section_progress.sql:6`); `activity_exposure_events` (`migrations/065_activity_lineage_substrate.sql:170`) | What source text reached the learner, what answers were revealed, which sections were read. In `activity_exposure_events`, `rendered` is a once-ever burn boundary (unique index, `:188`): writing it for a proposal strip would burn the surface for held-out use. Nothing records a proposal that was displayed but not picked |
| Familiarity | `learner/recall_coverage.py:293` (`familiarity_discount`); `scheduling/scheduler.py:450`; `learner/familiarity.py:217` (`familiarity_projection_v1`) | `familiarity_discount` reads the LO's recent attempts only (`learner/recall_coverage.py:302`); the scheduler multiplies a probe's EIG by its result. No function takes a reading exposure or an equivalence verdict |
| Certification eligibility | `diagnosis/causal_activity_policy.py:145` (`classify_attempt_activity`), `:202` (`resolve_attempt_activity_policy`) | An ordinary independent attempt is eligible for certification. Nothing reads an answer key's verification status; DL3's `practice_attempts.reference_status` gate (`spec_daily_loop_v1.md` §4.4) is specified, not built |
| Source objects | `migrations/094_source_objects.sql:15`; `reader/source_objects.py:19` (types), `:23` (relations: `supports`, `contradicts`, `refines`, `alternate_definition`, `unresolved`, `learner_connects`) | Per-source proposals with span citations. No retrieval or UI reads them |
| The learner's pick | `daily_plan/engine.py:1914` (`learner_pick`); `screens/TodayScreen.tsx:509` (`openPractice`: the plan on → `planLearnerPick`; off → DL0's open) | Any item id becomes a one-item learner-pick block and displaces the plan's tail |
| Intervention needs | `diagnosis/followups.py:381` (`upsert_intervention_need`, `blocked_reason = "no_suitable_item"`); `content/authoring/practice_generation.py:441` (`build_diagnostic_practice_plan`), `:454` | When no LO item fits a follow-up, a need is recorded and the generation lane authors an item for it |
| Tutor answer contract | `tutor/ai_contracts.py:84` (`TutorAnswer`), `:126` (prompt version); `TutorQAContext` `:20` (carries `expected_answer` and `rubric` in the practice and feedback contexts) | One structured call per question |

### 3.2 Findings that shape the design

1. **`find_practice` has no caller in the app** (§3.1). Its value is unrealised until S0.
2. **`correction_source_span_ids` holds source ids, not spans.**
   - `_authored_correction` stores `ref.ref_id` from the facets' source refs (`diagnosis/misconceptions.py:554`–`:560`). For `canonical_source` refs that is the source id (`src_…`). The span lives in the ref's `locator` (`span:<extraction>/<span>`, parsed by `ingest/locators.py:41`).
   - The field (`db/repositories.py:317`) is written at promotion (`diagnosis/misconceptions.py:504`) and never read.
   - S3 reads it as a source filter and resolves the spans from the facets' locators (§9.3). The writer is not changed, so old rows keep their meaning.
3. **Role hints are only ever excluded.** There is one deterministic hint per block. There is no counterexample, intuition, prerequisite or alternative-treatment role, and no confidence. S1 and S3 add a positive role filter. The finer roles, with confidence, are the Reader's RW4e (restored at `df23187e`: proposals in `source_objects` from judgments already being made, plus an owner-run batch labeller); the filter matches them once they exist (§9.1).
4. **`import_exercises` writes before any check and attaches no family.**
   - Its input is a Reader selection (`raw_selection.nodes`). The crosswalk also accepts span ids with offsets (`reader/annotations.py:217`), so a deterministic adapter can build a selection from block spans.
   - Its single function authors and then writes; S1 splits it so that a check can run between the two steps (§7.2).
5. **The PF verifier is private to a PF run, and its result folds two checks into one.** `_panel_solves`, `_agreement` and `_span_support` are methods of the run class in `ops/pf_generation.py`. `_agreement`'s per-solve `agree` is the LLM agreement *and* the sympy confirmation (`ops/pf_generation.py:1050`–`:1051`); an absent sandbox raises. S1 extracts them into a shared function that reports model agreement, the symbolic status and the sandbox status separately, keeping the combined value PF decides on, with a parity test (§7.3).
6. **`apply_family` only creates a family** (`substrate/families.py:183` refuses an existing identity). Adding an item to an existing family is what PF publication does with `append_membership` (`ops/pf_publish.py:267`). S1 reuses that pattern (§7.4).
7. **No provider path supports native tool calling.** The ChatGPT-plan provider refuses `tools` and `tool_choice` (`ai/chatgpt_plan/responses.py:13`, `:41`). Tool use is therefore a field of structured output (§10.2).
8. **EVSI has no live consumer, and its inputs are not what the item EIG functions produce** (§3.1). `rank_feasible` needs credible-set `P(E|H)` matrices with a normalized prior and its basis; `evaluate_selection` needs ensembles; the item EIG functions return floats. S2a defines one valuation input and an adapter per hypothesis and candidate kind (§8.3). S2 and the Reader's RW6b are `rank_feasible`'s first live uses, whichever merges first.
9. **Remediation shows the first linked span per facet** (`diagnosis/remediation.py:196`–`:215`), whatever the misconception says. S3's `remediate` intent ranks and verifies instead (§9.5).
10. **`practice_index_proposals.origin` has a closed CHECK** (`migrations/169_practice_index.sql:35`: `rpc`, `cli`, `tool`, `api`). New callers are recorded in added nullable columns, not in a table rebuild (§6.5).
11. **`limit` is a page size.** `PracticeConstraints.limit` is 1–20 (`practice_index/retrieval.py:126`) and `practice_index.proposals` defaults to 5. For the `practice` intent it stays a display page; the value intents ignore it (§8.3).
12. **`source_exposure_events.context` is a closed CHECK** (migration 150). S5 references existing exposure rows and keeps its own table, so no rebuild is needed.
13. **Admission ignores exposure to equivalent worked examples.** It excludes reserved cold checks and revealed answers only. The dialogue says a textbook exercise from an unread page is still a poor cold test if the learner just studied an equivalent worked example (L1376). S1 and S2 add the rule (§5.4).
14. **The tutor's model sees the current item's key.** `TutorQAContext` carries `expected_answer` and `rubric` in the practice and feedback contexts (`tutor/ai_contracts.py:20`). Any learner-visible text the tutor writes for a tool request passes the same leak check as its answer (§10.3).
15. **Only one regime may license effort today.** Arm A is reserved (no calibrated causal channel); arm B licenses only skips (decision-value §6.2). The live robust probe path (pinned grader channel × authored card rows) is the one place a value verdict already serves a probe. S2a's verdicts follow the same split (§8.3.3), so an abstention is never turned into an EIG-ordered question.
16. **A displayed but unpicked proposal leaves no trace.** Proposal rows record what was retrieved; picks record what was served; nothing records what was shown. S0 adds impressions, and the exposure rule reads them (§5.4, §6.5).
17. **`familiarity_discount` cannot see reading.** It reads attempts only (`learner/recall_coverage.py:302`). The worked-example rule gets its own adjustment rather than fabricated attempts (§5.4).
18. **Imported keys certify today.** Imported exercises' AI-written keys are never checked, and their attempts are eligible for certification like any other (`diagnosis/causal_activity_policy.py:145`). C3 forbids that for unverified keys; S1 applies DL3's gate (§7.3a).
19. **A raw exercise has no facets or minutes until it is authored**, and the import gives an LO's whole facet union to an item whose author named none (`content/authoring/exercise_authoring.py:433`). Exact filters therefore need provisional metadata before import and validation after it (§8.1).
20. **`evaluate_selection` pairs ensemble members by index.** It sizes its agreement loop by the winner's member count and indexes every candidate's members with it (`diagnosis/robust_composition.py:403`, `:408`), and it zips the winner's and the runner-up's series (`:385`). The live robust probe path always passes equal counts: every candidate is built by `build_ensemble` on one pinned channel (`diagnosis/probe_robust.py:220`, `:309`). Other regimes produce other counts, so mixing them in one call raises `IndexError` or silently reads a prefix (§8.3.4).
21. **`limit` does not deepen span recall.** `search_spans` builds every list at the fixed `LIST_DEPTH = 200` (`source_retrieval/search.py:54`; keyword `:172`, rewrite keyword `:199`, dense `:234`), and `limit` only cuts the fused order (`:252`, `:262`). On the item side, BM25 ranks only items that share a term (`practice_index/text.py:75`), and the dossier path ranks only the items under its top facets (`practice_index/retrieval.py:364`, `:376`). Resumable paging therefore needs its own depths (§8.3.4).
22. **An edit keeps the item id.** `edit_item` rewrites the prompt, the expected answer and the hints in place (`content/authoring/item_authoring.py:174`, `:196`, `:203`), so any status looked up by item id alone outlives the content it described (§7.3a).

### 3.3 In-flight work (2026-10-12)

| Branch | State | What this spec uses |
|---|---|---|
| `router/r1` → `merge/r1` | Built and reviewed; `mvp-0.15` and migration 181 at merge | `router_decisions` (`decision_kind` `today_offer` \| `staged_p2` \| `learner_pick`, exact propensities). S5 stores a `router_decision_id` when a pick is logged there (§11.1); S4's R2 design joins retrieved candidates to its candidate set (§10.6). Nothing here waits for it |
| `learner/text-gaps` | Built and reviewed; `mvp-0.16` and migration 182 expected | `named_gaps_for_card()` (`diagnosis/text_gaps/pipeline.py:850` on the branch): each named gap with its target `{kind, id}`. S2 and S3 accept a `named_gap` hypothesis reference through an adapter that is feature-detected (§8.2) |
| `facets/identity` | Built; migration 183 expected | Canonical facet ids. Everything here already goes through `vault.canonical_facet_id` |
| `docs/reader-workbench-spec` | Spec, being revised | The consumer of S0–S4 (§20) |
| `evsi/calibration` | Started at `57d31c63`, nothing committed | Owns calibrating EVSI's heuristic constants and promoting likelihood regimes (§8.3.3). S5 logs what it needs (§11.4) |
| DL2, DL3 | Not built | DL2's "Check once" serves dated checks; DL3's "Practice on…" box is S0's RPC |

**Numbering.** Migrations were taken from 184 upward, in build order (§13, §15), and renumbered at the merge onto `main` (after main's 184 `voi_forecasts`, 185 RW1a and 186 the proof route check): the branch's 184-192 are 187-195, and this spec uses the merged numbers. The two successors took the next free tags at the merge, after main's `mvp-0.15` (router R1), `mvp-0.16` (learner-text gaps) and `mvp-0.17` (the proof route check): S1's certification gate (§7.3a) is **`mvp-0.18`** (built as `mvp-0.15`) and S2b is **`mvp-0.19`** (built as `mvp-0.16`).

---

## 4. The service at a glance

```
callers (server-side context ⇒ policy, §5)
  tutor answer offers (S0/S4) · plan learner pick (S0) · Reader UI (Reader spec)
  · intervention needs (S2b) · RW6b follow-ups · router R2 (deferred)
        │  typed request (natural-language query + typed constraints)
        ▼
learnloop.instructional.tools ── policy derivation, validation, receipt (source_tool_calls)
        │
        ├─ find_practice  ─ items arm (Phase 5b) + source-exercise arm (S1)
        │                   intent ⇒ relevance judge, then value of information (S2)
        ├─ find_sources   ─ search_spans + role filter + intent lists + intent judge (S3)
        ├─ compare_sources─ counterparts per source + one quote-verified comparison (S3)
        ├─ find_facets    ─ dossier/facet shortlist, no model call (S4)
        └─ practice_availability ─ counts and minutes per intent, no model call (S4)
        │
        ▼
admission + exposure rule (§5.4) ── proposals, never served
        │
        ▼
existing serving paths (SC1) ── what was shown or served ⇒ retrieval_interventions (S5)
                                    later outcomes ⇒ retrieval_intervention_outcomes (DERIVED)
```

---

## 5. Contamination policy (cross-cutting; brainstorm L1358–1380)

### 5.1 Policies

The dialogue named five contexts (L1368–1374). Four are learner-facing `find_sources` policies, exactly as the Reader spec's §7.2 defines them (at `df23187e`): `reading`, `assisted_practice`, the restored narrow `post_attempt`, and `cold_attempt`. The fifth, `authoring`, is internal: it is not a `find_sources` policy (the Reader spec's choice too), only the scope S1's verifier builds for itself.

| Policy | Built from | What a learner or a learner-facing model may receive |
|---|---|---|
| `reading` | `library_scope` or `teaching_scope(item_bound=False)` | Every passage in scope, worked examples and solutions included when asked for: reading is never blocked. Each span shown is recorded as exposure, and the exposure rule then keeps the exercises it gives away out of independent checks (§5.4). Results returned to a model still follow §5.3 |
| `assisted_practice` | `teaching_scope(item_bound=True, item=…)` + the answer-overlap filter (`source_retrieval/tutor.py:125`) + verification | No `exercise` or `solution` block, nothing linked to the item, nothing that reproduces its key. Hints and tutor answers are reveal-accounted as today |
| `cold_attempt` | — | **Nothing.** An empty result by construction, and the tool dispatcher refuses every tool (G2). Opening a source ends cold status (P3 invariant 10); it is never blocked |
| `post_attempt` (restored, narrow; the Reader's definition) | `assisted_practice` while the item's attempt window is open (a redo, guided redo or retry is possible: T6's reason for keeping feedback item-bound, `source_retrieval/tutor.py:51`); once the window is closed by a correct submission or by the learner closing the item, `reading` plus the item's own linked passages and solution blocks | After the window closes: the item's solution and the passages it was built from. Every display records a reveal, so the family is treated as revealed afterwards (§5.4 rule 2) |
| `authoring` (internal; not a `find_sources` policy) | the source's own extractions, solutions included, built directly from `extraction_scope` (`source_retrieval/corpus.py:112`) | Used only by S1's verifier to find the book's solution (§7.3). PF's source-anchored path keeps its own retrieval. Never returned by a learner-facing tool, never shown to the learner, never passed to the tutor or the router (SC3) |

### 5.2 Who sets the policy

| Caller | Policy |
|---|---|
| Tutor, practice or feedback context | `assisted_practice` with the item |
| A comparison after the item's attempt window closed (the Reader's "Compare with the book's method") | `post_attempt` with the item |
| Tutor, library or reader context | `reading` |
| Any caller during a cold administration | `cold_attempt` |
| Daily plan learner pick, DL3's box, Reader library | `reading` (proposals only; admission applies) |
| S2b need fulfilment, S1 harvest, S1's interactive import | `reading` for discovery; S1's verifier builds the `authoring` scope itself |
| Router R2 (deferred) | `reading` for discovery; answer visibility `withhold` (SC3) |
| External agent (`learnloop sources tool`) | `reading` |

The derivation lives in `instructional/policy.py`. The tool arguments have no policy field. A request that names an item or attempt it was not called about is refused (G2).

### 5.3 What a model sees

Results returned to an LLM (the tutor's offers, R2's availability pass, an external agent) are compact typed records:
- for items: id, LO, facets, practice mode, prompt (truncated), difficulty, expected minutes, source label;
- for source exercises: span keys, source label and page, the exercise statement;
- for passages: span keys, source, section, page, revision id, verbatim text (truncated).

They never include `expected_answer`, `grading_rubric`, hints, discrimination profiles' expected answers, solution blocks or reserved items. A learner-facing surface may show a source exercise's statement and a passage's text, labelled source-authored.

### 5.4 Independent-check eligibility (the exposure rule)

`instructional/exposure.py:independent_check_eligibility(candidate, *, intent, at, picked_proposal_id=None)` decides it. Its only model call is rule 4's judge, whose verdicts are served from the ledger once written. A candidate offered for the `discriminate` or `retention` intent (§8), or used to fulfil a need (S2b), must be unexposed. That means none of the following (rules 2–5 count within the cold retrieval delay):
1. an attempt on the item (`unattempted_only`);
2. a reveal on the item or on any member of its family (the reveal ledger; `exclude_revealed_families`). A `post_attempt` display of a solution is such a reveal (§5.1);
3. for a source exercise or an item with a `canonical_exercise` (§7.4), a `source_exposure_events` row on its span or its solution region;
4. **an equivalent worked example studied** (built in S2a):
   - The shortlist is every `worked_example` block in the candidate's teaching scope that has an exposure row, or that sits in a section `reader_section_progress` marks as read. It is ranked by keyword and vector similarity to the candidate.
   - One listwise call (route `worked_example_equivalence`) judges each shortlisted example as `equivalent` (the exercise would be a near-copy), `related` or `unrelated`. Every verdict goes to `judgment_ledger`.
   - `equivalent` excludes the candidate from both independent intents; it stays available for `practice`.
   - `related` excludes it from `retention` (a cold retention check must not follow a closely related worked example) and keeps it for `discriminate` under the reading-exposure adjustment below;
   - a studied example the judge could not judge (no route, over budget, a failed call) may be a near-copy, so the candidate is excluded from both independent intents (`worked_example_unjudged`) until a verdict resolves it; it stays available for `practice`, labelled;
5. **an impression of its prompt or statement** (§6.5's `instructional_impressions`), from any proposal other than the one being picked: the learner has already read the question, so it no longer tests unaided retrieval.

**The reading-exposure adjustment** (`exposure_rule_version = "reading_exposure_v1"`). `familiarity_discount` (`learner/recall_coverage.py:293`) cannot express a reading exposure: it reads the LO's recent attempts only, and attempts are never fabricated to feed it. So a `related` verdict does not discount the candidate's value; nothing has measured how much a related example changes these likelihoods, and inventing a factor would be a hand-set constant. Instead:
- the candidate is labelled "you read a worked example like this one";
- a documented dominance rule orders it (decision-value §6.4: non-time harms are constraints, dominance rules or documented tie-breaks): a `related` candidate never goes ahead of an unrelated one whose robust value interval overlaps its own;
- its inputs are recorded on the valuation receipt: the verdict's ledger id, the exposure rows (`source_exposure_events` ids, `reader_section_progress` rows), the seconds since exposure and the rule version;
- S5 records the label beside the outcome, so the calibration track can measure the effect and promote a learned adjustment as its own versioned input (§11.4; decision-value invariant 12).

**Checked again at serving time.** A proposal can wait: a strip left open, a dated check. Every path that serves a candidate *as an independent check* calls `independent_check_eligibility` again at the moment it serves: a learner pick of a `discriminate` or `retention` proposal (§6.3), S2b's fulfilment (§8.5), and RW6b's dated checks through DL2 (a cross-spec request, §20). The impression made by the proposal being picked does not count against that pick; earlier impressions do. If eligibility no longer holds:
- a learner's pick still proceeds, as practice, with the independent label dropped and the reason shown ("you've seen this question since it was suggested");
- a system-initiated check is not served as one (typed reason `exposed_since_valuation`), and its caller re-queries.

S5 stores the serve-time verdict beside the valuation-time one (§11.1).

The delay is `COLD_RETRIEVAL_DELAY` (1 day, `diagnosis/remediation.py:30`), the window admission already uses. Router §15.2 says coldness should be learned rather than hard-coded, so S5 logs the time since each exposure and impression for R3 to fit (§11.1).

### 5.5 Receipts that let anyone reconstruct access (L1378–1380)

Each `source_tool_calls` row (§10.4) and each `find_sources` manifest records:
- the query hash;
- the effective policy and how it was derived;
- the scope's extraction ids, each with its revision id;
- the returned asset ids;
- the verification statuses.

Exposures are recorded where text is shown, as today (`source_exposure_events`, the reveal ledger). Proposals displayed to the learner are recorded as impressions (§6.5). Retrieved, displayed and served stay three separate records: the proposal row or manifest, the impression, the pick or attempt. S5 links them.

---

## 6. S0 — `find_practice` gets real callers

### 6.1 Which live paths propose through it

| Path | Decision | Why |
|---|---|---|
| **The tutor's "Practice this"** (practice, feedback, library and reader contexts) | **Yes, now.** After every tutor answer, a practice request is prepared from the learner's question and the answer's facets (§6.2). The frontend runs it once the answer is on screen, so the answer waits for nothing. S4 lets the tutor's model write the request instead (§10.3) | Router §15.3: "Start with the tutor's 'Practice this', which has the shortest path to value; it needs only `find_practice` and T6" |
| **Daily plan learner picks** | **Yes.** `plan_learner_pick` gains an optional `proposal_id`. A picked proposal becomes a learner-pick block through the unchanged `learner_pick` (`daily_plan/engine.py:1914`). With the plan off, it is DL0's open, exactly as `openPractice` does it (`screens/TodayScreen.tsx:509`) | It is the existing serving path for a learner's own choice (L3, G12). It records the link the usage signals and S5 need |
| **DL3's "Practice on…" box; the Reader's "Practice this question"; RW6b's candidate checks** | **Yes, as consumers** of the same RPC. Their UI belongs to their specs | One function, one receipt table (Reader spec W13) |
| **Post-attempt follow-ups** | **Through S2b, not S0.** The follow-up chooser (`diagnosis/followups.py:1532`) is unchanged. When it finds no suitable item it records an intervention need, and S2b fulfils that need from the sources before generation (§8.5) | Changing the chooser's candidate set changes what is served. S2b is the smallest serving change, and it ships as a successor |
| **The quick check** | **No.** | The quick check chooses by conditional gain over undecided LOs, with no natural-language request (`diagnosis/quick_check.py`). S1's imported exercises are ordinary never-seen items, so they join its pool with no change. Re-open if the quick check ever takes a learner request |

### 6.2 The tutor's practice request

`instructional/offers.py:practice_request_for_answer(question_event)` is pure and makes no model call. It builds:
- `query`: the learner's question;
- `learning_object_ids`: the context's LOs;
- `facet_ids`: the answer's classified facets (`TutorAnswer.facets`);
- `exclude_item_ids`: the current item;
- `intent`: `practice`;
- `kinds`: `both` once S1 has added the field and the exercise arm (§7.1); before that the request has no `kinds`.

It is returned on the `ask_tutor_question` response as `practice_request`, with a `caller` block (kind `tutor`, ref = the question event id).

The frontend sends the request to `find_practice`. The server re-derives the caller context from the question event, so the frontend cannot change the policy (G2).

### 6.3 How a proposal becomes served

- **An item proposal**, picked → `plan_learner_pick(practice_item_id, proposal_id=…)` with the plan on, or the open-list pick with it off. Both append the `practised` usage signal (`practice_index/usage.py:39`) at the pick, not only through the 72-hour attempt join. When the proposal's intent is `discriminate` or `retention`, the pick re-checks independence first (§5.4); a candidate that fails is served as practice, labelled.
- **A source-exercise proposal** (S1), picked → `import_source_exercise(proposal_id, span keys)` (§7.2) → the new item id → the same pick path.
- **"Not what I asked"** takes optional text (learner text over skip buttons). The text is stored on the usage verdict's rationale. Once learner-text gaps has merged, a source adapter reads it like any other learner text (§20).

Nothing else serves a proposal. In particular, a proposal never enters Today's queue by itself.

### 6.4 What the learner sees (outside the Reader)

In `components/AskOverlay.tsx`, for the practice, feedback and library contexts: a "Practice this" strip under the answer. It shows up to `limit` proposals: the prompt, the LO, and the rerank's one-line rationale, labelled "LearnLoop's reason". Each has "Practise" and "Not what I asked…". A source exercise shows "From *Book*, p. *N* · not yet in your practice". The reader context's strip is the Reader spec's.

When the strip renders, it reports what it showed through `record_proposal_impressions` (§6.5). The Reader's and DL3's surfaces call the same RPC (§20). A proposal that was only retrieved, and never rendered, writes no impression.

### 6.5 Data, routes, spend

- **Migration 187:**
  - `practice_index_proposals` gains nullable `caller TEXT`, `caller_ref TEXT` and `intent TEXT` (`ALTER TABLE ADD COLUMN`; the role stays RECEIPT). `origin` keeps its CHECK; S0 calls use `rpc` with `caller` set.
  - **`instructional_impressions`** (RAW_LEDGER: append-only facts of what reached the screen): `id`, `created_at`, `surface` (`tutor_strip` \| `plan` \| `dl3_box` \| `reader` \| `other`), `caller_kind`, `caller_ref`, `proposal_id`, `candidate_kind` (`item` \| `source_exercise`), `practice_item_id`, `extraction_id`, `span_ids_json`, `shown_fields_json` (prompt or statement, rationale), `session_id`. It is deliberately not `activity_exposure_events`: `rendered` there is a once-ever burn boundary for held-out use (`migrations/065_activity_lineage_substrate.sql:188`), and a glimpse in a strip must not burn a surface. Nothing outside §5.4 and S5 reads it, so no projection changes.
- **RPC** `record_proposal_impressions(proposal_id, keys, surface)`: fire-and-forget from the frontend after render; unknown keys are dropped and counted.
- **Routes:** Phase 5b's `practice_rerank` and the query embedding, unchanged. For this interactive path the fast route (ChatGPT-plan) is recommended (D6).
- **Spend:** unchanged per call (`practice_index.rerank_max_cost_usd`).

### 6.6 Successor, kill switch, gates, tests

- **Successor:** none. Proposals never serve, and a learner pick is an existing serving path (Phase 5b's ruling, `config/schema.py:1731`).
- **Kill switch:** `source_service.tutor_offers` (off: no `practice_request` on tutor answers). `practice_index.enabled` still switches `find_practice` itself off.
- **Gates:** G1, G2, G14, G16, G20.
- **Tests:**
  - `test_tutor_practice_request.py`: deterministic request, current item excluded, caller re-derived;
  - `test_learner_pick_proposal.py`: pick with a proposal id, usage verdict, plan parity when the id is absent;
  - `test_practice_proposal_caller_columns.py`;
  - `test_proposal_impressions.py`: rendered keys recorded, retrieved-only keys not, `activity_exposure_events` untouched;
  - the frontend `AskOverlay` strip test, including the impression call;
  - the mobile allowlist pins.

---

## 7. S1 — Textbook exercises as practice candidates (RW4c)

### 7.1 The source-exercise arm

`find_practice` gains a second, injected arm behind `source_service.exercise_arm`: `instructional/exercises.py:exercise_candidates`, passed in by the RPC handler and the tool dispatcher (SC12; `practice_index` never imports `source_retrieval`).
- **Scope.** The teaching scope of the constraints' LOs (`teaching_scope(item_bound=False)`), or every source with a role when no LO is given. The teaching exclusions apply, so exam, problem-set-as-held-out and assessment-linked spans never appear (`source_retrieval/corpus.py:269`).
- **Positive role filter.** `search_spans` gains `roles: Sequence[str] = ()`. When it is set, every list keeps only blocks whose *effective* hint is in `roles`: the hint `_effective_hint` computes (`source_retrieval/corpus.py:310`), which discounts heading-only cues and which S1 makes public as `effective_hint` for the arm (SC12). The arm asks for `("exercise",)`. Each hit is widened to its exercise region (the lead block and the body that follows, the `lead_regions` rule that `_role_hint_exclusions` uses at `:327`).
- **Already imported.** Regions whose span (or the same text in another extraction of the source) is named by any item's `provenance.source_refs` or `canonical_exercise` are dropped. This reuses `item_exclusions`' resolution (`source_retrieval/corpus.py:385`) over all items.
- **One judged pool.** The rerank judges items and source exercises in one listwise call. Each candidate is rendered with its kind: an item as today, a source exercise as its statement plus "from *Book*, p. *N*". The pool is the item pool plus the exercise pool, each `candidate_pool` long (a prompt-size bound). The judge's instruction adds the dialogue's preference (L1163): "prefer a question already in the learner's practice when it serves the request equally well".
- **Choosing arms.** `PracticeConstraints` gains `kinds` (`items` | `source_exercises` | `both`; default `both` while the arm is on, `items` when it is off).
- **Proposals.** A source exercise is proposed as `{kind: "source_exercise", extraction_id, span_ids, source_id, revision_id, source_title, label, page, statement, relevance, rationale}`. It is never an item id until it is imported.

**Worked examples are not practice candidates.** A worked example's solution is right beside it, so it can never stand as an independent check. Worked examples are S3 material (`find_sources(intent="worked_example")`). This narrows the dialogue's "exercise and worked-example records" (L1414) for that reason.

### 7.2 Import: on a pick, and as an owner-run harvest

**The split.** `import_exercises` becomes `author_exercises(...)`, which returns authored drafts, and `write_exercises(...)`. The existing function becomes their composition, so the item the Reader's path writes is unchanged (parity test G5); its job also records the import's key status (§7.3a). The drafts keep today's rules: the verbatim re-anchored stem, the facet registry, rubric arithmetic, the capability vocabulary and the task-feature schema.

**The adapter.** `content/authoring/source_exercise_import.py:selection_for_region(extraction_id, span_ids)` builds `raw_selection.nodes` from block spans, with `start = 0` and `end = len(text)`. The crosswalk accepts that form (`reader/annotations.py:217`). The import pipeline below lives in the same module.

**Interactive import** (a learner picked a proposal): the RPC `import_source_exercise(proposal_id, extraction_id, span_ids)` enqueues a `source_exercise_import` job on the main single-writer lane, like `reader_exercise_import` (`content/pipeline/jobs.py:2215`):
1. **Look for the book's solution** (§7.3 rung 1's search and match, under the internal `authoring` policy).
2. **Author.** When a solution was found, it is passed into the authoring context, so the key is written from the source (the source-anchored "answer first" pattern).
3. **Check within a time box** (`source_service.verify_timeout_seconds`, default 90 s; a time bound). If the ladder (§7.3) finishes inside the box, the item is written with its status. If not, the item is written labelled `checking`, the pick proceeds, and the check finishes in the background (D1). Attempts made while it is `checking` record `unverified` and never certify, even if the key verifies later. A check verifies only the content it was given, so a background result that lands after an edit verifies nothing newer (§7.3a).
4. **Write** with `canonical_exercise` (§7.4) and the key's status.
5. **Attach** to a family (§7.4).
6. **Return** the item id to the pick path (§6.3). The frontend follows the job with the RPC `get_source_exercise_import(import_id)` (status, key label, item id).

**Owner-run harvest:** `learnloop sources exercises harvest [--lo …] [--facet …] --dry-run | --max-cost-usd`.
- **Targets:** facets that `coverage_report` (`practice_index/coverage.py:42`) lists as thin. From S2a on, also facets with open rival hypotheses (§8.2).
- **Per target:** the arm's judged candidates, each imported with the ladder run *before* writing.
- **Bounds:** money (`--max-cost-usd`) and the judge's picks. There is no count of exercises.
- **What reaches the learner:** DL1's new-material admission bounds how many new items appear each day.

**Owner-run verification of existing imports:** `learnloop sources exercises verify [--item …] --dry-run | --max-cost-usd` runs the ladder over imported exercises whose current content is not verified (historical Reader imports and items edited since their last check included, §7.3a) and records each result as a `reference_key_checks` row bound to the content it checked.

Automatic background harvesting is deferred (§19, D7).

### 7.3 The verifier ladder (honest key labels)

`ops/pf_verify.py:verify_reference(stem, reference, *, caller, source=None, on_sandbox_unavailable="raise")` extracts PF-b's verification code:
- the panel solves of `ops/pf_generation.py:1001`;
- the agreement with the sandboxed sympy confirmation of `:1027`;
- the span support of `:806`.

**What it returns.** `_agreement` folds the LLM's agreement and the sympy confirmation into one per-solve `agree` (`:1050`–`:1051`), so for a numeric answer a sympy run that failed, or a missing sandbox, looks exactly like disagreement. The extracted function keeps that combined value and adds what it hides:
- `combined_agree`, `total`, `answer_kind`, `usable`, `normal_form`, `degenerate_check`: today's fields, unchanged;
- `model_agree`: how many solves the LLM equivalence judge found to agree with the key, whatever the symbolic check said;
- `symbolic_status`: `not_applicable` (prose answer) \| `confirmed` \| `rejected` (the check ran and found the solves and the key differ) \| `reference_unreadable` (the check said no, but the sandbox could not read the reference it was given as an expression, so the no says nothing about the key) \| `degenerate_check` \| `no_check_written` \| `sandbox_error` (failed or timed out) \| `sandbox_unavailable`;
- the sandboxed check may compare the solves with a different reference from the one the judge reads (`symbolic_reference`). The source-import ladder passes a worked-solution key's `Final answer:` line when it has one (`substrate/item_fingerprints.py:final_answer_text`, as PF passes its references) and the whole key otherwise. PF passes none, so its sandbox input is unchanged;
- `per_solve`: `model_agree`, `symbolic` (`True` \| `False` \| `None`) and the combined value.

With `on_sandbox_unavailable="report"` (S1's setting), a missing sandbox returns `sandbox_unavailable` instead of raising `SandboxUnavailable`. PF calls it with the default, `"raise"`, and still refuses up front when there is no sandbox (`ops/pf_generation.py:1713`).

**PF's decisions are preserved.** The PF run class calls the extracted function and decides on `combined_agree` exactly as today. A parity test pins that its ledger rows, verdicts and published candidates are unchanged on fixture runs, including a numeric candidate whose sympy run fails. The source-import ladder below is tested on its own (G6).

| Rung | Check | Key status shown | Verified (§7.3a) | Ledger |
|---|---|---|---|---|
| 1. **The book's solution** | Within the source's own extractions, solutions included (the internal `authoring` scope, built directly from `extraction_scope`, `source_retrieval/corpus.py:112`): `search_spans` with `roles=("solution",)`, querying the exercise's label and stem. One listwise call (route `source_solution_match`) names the passage that solves this exercise, or none. Then the quote check (the key's cited quote must appear verbatim in that passage; S1 adds a `cited_quote` field to the authoring contract for this case) and PF's span-support verifier (`pf_reference_verifier`). When rung 1 passes, rung 2 does not run | "Answer from the book's solution, *Book* p. *N*" (`book_solution`) | yes (PF §5.3: a quote-verified span that contains the answer) | `source_solution_match`, `reference_verified` |
| 2. **Panel plus sympy** | A numeric or symbolic answer: at least `pf.min_agreeing_solves` panel solves agree with the key (`model_agree`), solving without seeing it, and the LLM-written sympy check confirms them in bubblewrap, with negative controls (`symbolic_status = confirmed`) | "Checked: independent solvers and a symbolic check agree" (`checked`) | yes | `answer_equivalence`, `reference_verified` |
| 2′. **Panel, prose answer** | A prose answer (`symbolic_status = not_applicable`): at least `pf.min_agreeing_solves` panel solves agree | "Independent model solvers agree" (`panel_agrees`) | yes (PF §5.3 asks for the symbolic check only where the answer is numeric or symbolic) | as rung 2 |
| 2″. **Panel, symbolic check unavailable** | A numeric or symbolic answer: enough panel solves agree (`model_agree`), but the symbolic check could not confirm them (`no_check_written`, `sandbox_error`, `sandbox_unavailable` — macOS and Windows always — `degenerate_check`, or `reference_unreadable`: a worked-solution key with no final answer the sandbox can read) | "Independent model solvers agree; the symbolic check couldn't run here" (`panel_agrees_unconfirmed`) | **no**: PF §5.3 requires the symbolic check for these answers. Retried when a sandbox is available | as rung 2, with the symbolic status |
| 3. **Model's answer** | The check did not run (no route, no price, over budget, timed out), or it is still running | "Model's answer, not checked" (`model_answer`) or "being checked" (`checking`) | no | the skip reason |
| ✗ **Disputed** | The panel's agreeing answer differs from the key, the symbolic check ran and rejected the solves' agreement with the key (`rejected`), or the book's solution was found and the span-support verifier finds it does not support the key | "LearnLoop's check disagrees with this answer key" (`disputed`), with the panel's answer one click away | no | `reference_verified` = `fail` |

**What the labels change.** Each of these reads the item's *effective* status: the latest check of its current stem, key and rubric (§7.3a).
- Only verified keys (`book_solution`, `checked`, `panel_agrees`) qualify for the `discriminate` and `retention` intents and for S2b, whose value depends on the key. The other statuses stay available for `practice`, labelled.
- Only verified keys certify (§7.3a).
- An item edited since its last check shows "answer key changed since it was checked" (`changed_since_check`) and counts as unverified.

### 7.3a Certification follows the key (C3)

The frictionless decision C3 (`daily_loop_frictionless_defaults.md`, owner decision 2026-10-11) says an unverified solution never certifies anything. An imported exercise whose key is not verified may still be practised, labelled, but its attempts must not certify. Keeping such keys out of the value intents does not achieve that: an ordinary independent attempt is eligible for certification (`diagnosis/causal_activity_policy.py:145`). S1 therefore applies DL3's attempt-time gate (`spec_daily_loop_v1.md` §4.4) to imported exercises instead of designing another one.
- **Recorded at attempt time.** `practice_attempts.reference_status` (`not_applicable` \| `verified` \| `unverified`), as DL3 specifies it. The attempt transaction sets it from the served item's effective key status, read through `db/stores/source_service.py:reference_status_for_item(item)` (below). Afterwards only a replacement grade can change it, and only downwards (below), so replay reads the value the grade in force was written under. Items that are neither exercise imports nor DL3 captures record `not_applicable`.
- **Bound to the content checked.** A key check verifies one revision of an item, not the item id: `edit_item` rewrites the prompt and the key in place under the same id (§3.2 item 22), and so can other writers.
  - Every ladder run records the content it was given: `reference_content_hash(item)`, a new function beside `practice_item_hash` in `vault/hashes.py` (`:45`, built with its `content_hash`, `:22`), over the prompt, the expected answer and the grading rubric. The result is one append-only `reference_key_checks` row (§7.5) carrying that hash.
  - `reference_status_for_item(item)` hashes the item exactly as it is served for the attempt. It returns `verified` only when the latest check *with that hash* has a verified status (`book_solution`, `checked`, `panel_agrees`). A check of any other revision never counts. An exercise import with no matching check records `unverified`.
  - **Edits need a fresh check** (D20). After an edit, the item is `changed_since_check` and its attempts record `unverified`. When `exercise_verification` is on, the sidecar's edit handler (`edit_practice_item`, `learnloop_sidecar/handlers/item_authoring.py:200`; its signature is unchanged) queues a check of the new content under the per-import cap, and `learnloop sources exercises verify` covers every such item too.
  - **A late result verifies nothing newer.** A background check that finishes after an edit writes its row with the hash of the content it checked, so it cannot verify the edited key. The import row records `superseded_by_edit`, and a check of the current content is queued as above.
  - DL3's capture gate has the same exposure; §20 asks DL3 to bind `capture_processing.verification` the same way.
- **Replacement grades.** A regrade (`attempts/regrade.py:regrade_attempt`: deferred regrades, a clarification's resolution, `trigger_regrade`) reads the item as it is now, not as it was when the attempt was made, and an adjudication from the `deterministic_key` source is a verdict against the stored key. Each is bound to the content it read, as the attempt was. At or above the gate's tag, when that content's key is not verified, `db/stores/source_service.py:bind_replacement_grade` lowers the attempt's `reference_status` to `unverified`. It does this in the transaction that publishes the new grade, before that grade's replay. It also appends a `judgment_ledger` row (task `attempt_reference_binding`, judge `verifier`) naming the content hash, the content's key status and the attempt-time status. Every reader of the column (the projection, the evidence timeline, the learner field, rebuilds) therefore gates the grade in force. Nothing raises the status: a grade read against verified content leaves it as it was. A human, expert or learner-clarification adjudication is not read from the key and is not bound. Below the tag nothing is bound.
- **Enforced where certification is decided.** `resolve_attempt_activity_policy` (`diagnosis/causal_activity_policy.py:202`) takes `reference_status` as an immutable attempt signal, like `primed` and `hints_used`. `unverified` forces `eligible_for_certification = False` and leaves FSRS eligibility and assistance unchanged. The attempt schedules and teaches; it earns no certification credit. Such items are also kept out of certification cold probes, exam pools and assumed-known checks, as DL3 keeps unverified captures out.
- **Never retroactive.** A key that verifies later does not make earlier attempts certify; attempts on that same content after it record `verified`. A key found wrong is replaced through `edit_item` (`content/authoring/item_authoring.py:174`), the learner sees "answer key corrected", and attempts graded against the old key stay ineligible. The replacement is itself unverified until a check of it passes (above). An attempt's recorded status never rises, whatever later checks or edits find.
- **The Reader's imports too.** `reader.import_exercise` writes the same unchecked, AI-completed key (`content/authoring/exercise_authoring.py:352`). From S1 on its job also writes a `source_exercise_imports` row (`caller = reader`, `key_status = model_answer`) and, when `exercise_verification` is on, queues the ladder in the background. The item it writes is unchanged (G5). The same exercise therefore certifies the same way whichever path imported it.
- **Historical imports.** Reader imports made before S1 have no row. The store resolves them from their append-only `learner_item_authored` event (`mechanism = reader_exercise_import`, `content/authoring/exercise_authoring.py:544`–`:551`) as `model_answer`. Their attempts before the successor keep `not_applicable` and replay as written. Their attempts from the successor on record `unverified` until the owner-run `learnloop sources exercises verify [--dry-run] [--max-cost-usd]` checks them (D2, D15). `canonical_extract` alone does not identify an exercise import, because AI authoring proposals over canonical sources share that origin (`content/proposals/proposals.py:1547`); those are reviewed proposals and keep today's semantics.
- **Successor.** This changes what a projection means, so it ships as an algorithm successor: the next free `mvp-0.N` at S1's merge (expect relabelling). If DL3 has merged first, its column and gate exist (`capture_reference_v1`), and S1 adds only its status source; that still changes which new attempts certify, so S1 still takes its own tag. If S1 merges first, it builds the column and the resolver input exactly as DL3 §4.4 specifies, and DL3 later adds its capture source. With no attempt recorded `unverified`, every projection equals its predecessor's; a shadow rebuild of fixture copies shows zero deltas, because the gate is never retroactive.
- **No switch re-enables certification (C3).** `source_service.unverified_imports` (default true; false: an import whose key does not verify is not written, and the pick says "LearnLoop couldn't check this answer key yet" and offers the exercise in the book) only stops new unverified imports. Vaults below the successor's tag never run the gate.

### 7.4 "Change what cards represent": family attachment and the canonical exercise

**The canonical exercise.**
- `PracticeItem` gains an optional `canonical_exercise: {source_id, revision_id, extraction_id, span_ids, label, relation: "verbatim" | "variant_of"}`. It is omitted when null, as `family_id` is (`vault/models.py:743`).
- It sits outside `practice_item_hash` (`vault/hashes.py:45`), so scheduling hashes are unchanged, and items without it serialize byte-identically (G5).
- Imported exercises get `relation = "verbatim"`. PF-b variants published from a parent with a canonical exercise copy it with `relation = "variant_of"` (one line in `ops/pf_publish.py`'s payload builder).

**The practice screen** shows "From *Book*, Exercise 4.12 · open in source" and the effective key status (§7.3, §7.3a). The link is hidden during a cold administration and shown after submission (P3 invariant 10). Opening it records exposure.

**Family attachment** (`source_service.family_attachment`):
1. **Candidate families:** the `ActivityFamily` rows on the item's LO (`vault/models.py:642`).
2. **Same retrieval target, and which relation?** PF's family judge (ledger task `same_target`, route `pf_family_judge`) judges the new item paired with every current member, with both of its prompts (`pf-same-target-direct-v1`, `pf-same-target-counterexample-v1`; `substrate/families.py:32`). Every pair must be judged `same` by both passes, and the passes must agree on the relation (`same_target` or `isomorph`). This is the complete-link rule `_validate_judgments` enforces for automatic families (`substrate/families.py:96`).
3. **Attach:** the new `substrate/families.py:attach_to_family`, with `apply_family`'s recover and undo discipline: the plan in `family_proposals`, the YAML patch to `family_id` and `variant_relation`, `append_membership` with the decision's ledger id. `apply_family` is unchanged.
4. **No matching family, or only a `near` or `far` kinship:** the item stays unfamilied. `near` and `far` members come only from PF generation, which declares the checkpoints it changes. An unfamilied exercise becomes an ordinary PF-b parent candidate, so variants are generated from the real textbook exercise ("generation on demand", L1163–1165).

### 7.5 Data, routes, spend

- **Migration 188:**
  - **`source_exercise_imports`** (WORKFLOW: paid outputs; never re-run on rebuild):
    - `id`, `proposal_id`, `extraction_id`, `span_ids_json`, `source_id`, `revision_id`, `label`;
    - `practice_item_id`, `content_hash` (`reference_content_hash` of the item as written), `key_status` (the status at import: `book_solution` \| `checked` \| `panel_agrees` \| `panel_agrees_unconfirmed` \| `checking` \| `model_answer` \| `disputed`), `verification_json` (rung, ledger ids, `model_agree`, `symbolic_status`, panel summary);
    - `validation_json` (the post-import constraint check, §8.1), `facet_basis` (`authored` \| `lo_fallback`);
    - `family_proposal_id`, `status` (`authoring` \| `checking` \| `written` \| `rejected` \| `failed`), `reason` (including `superseded_by_edit`);
    - `caller` (`learner` \| `reader` \| `harvest` \| `need`), `created_at`, `updated_at`.
  - **`reference_key_checks`** (RAW_LEDGER: captured verifier output, append-only, never updated, never re-run on rebuild): `id`, `practice_item_id`, `import_id` (nullable), `content_hash` (`reference_content_hash` of the revision checked), `key_status` (a finished status: `book_solution` \| `checked` \| `panel_agrees` \| `panel_agrees_unconfirmed` \| `model_answer` \| `disputed`), `rung`, `verification_json`, `ledger_ids_json`, `trigger` (`import` \| `background` \| `edit` \| `verify`), `started_at`, `created_at`. The attempt gate and the value intents read only this table, through the store (§7.3a).
  - **`practice_attempts.reference_status`** (`TEXT NOT NULL DEFAULT 'not_applicable'`, with DL3's CHECK), unless DL3 has already added it (§7.3a). Existing rows keep `not_applicable`.
- **Store:** `db/stores/source_service.py:reference_status_for_item(item)` and `effective_key_status(item)` (the latest check whose `content_hash` matches the item, else `changed_since_check`, `checking` or `model_answer`), read by the attempt transaction, the value intents, S2b and the practice screen's label (`db` sits below every domain, SC12).
- **Hash:** `vault/hashes.py:reference_content_hash(item)` over the prompt, the expected answer and the grading rubric. It is separate from `practice_item_hash`, which is unchanged.
- **Vault model:** `PracticeItem.canonical_exercise`.
- **Routes:**
  - `authoring` (`exercise_authoring`), `source_solution_match` (new, listwise);
  - PF's `pf_solver_panel`, `pf_reference_verifier`, `pf_family_judge`.
- **Spend:**
  - per import, `source_service.import_max_cost_usd` (default $0.25 metered);
  - `source_service.max_daily_cost_usd` (default $1.00 metered, shared by every S-phase);
  - the harvest has `--dry-run` and `--max-cost-usd`;
  - Codex is `estimated_only`.

### 7.6 Successor, kill switches, gates, tests

- **Successor:** the certification gate only (§7.3a): the next free `mvp-0.N` at S1's merge. The rest of S1 needs none. The arm proposes. An import is a learner-authority write, as today's Reader import is. A harvest is owner-run content, like PF-b publication, which its config calls "a content change … not an algorithm change" (`config/schema.py:1648`). Family attachment is a content change on PF's substrate.
- **Kill switches:**
  - `source_service.exercise_arm` (off: `find_practice` as Phase 5b built it);
  - `source_service.exercise_verification` (off: imports as today, labelled `model_answer`, so their attempts don't certify);
  - `source_service.unverified_imports` (default true; false: only imports whose key verifies are written);
  - `source_service.family_attachment`.
  - No switch turns the certification gate off (C3).
- **Gates:** G1, G3, G4, G5, G6, G7, G14, G15, G19.
- **Tests:**
  - `test_exercise_arm.py`: positive filter, regions, already-imported exclusion, teaching exclusions;
  - `test_import_split_parity.py`;
  - `test_selection_for_region.py`;
  - `test_pf_verify_extraction_parity.py`: PF's ledger rows, verdicts and published candidates unchanged, including a numeric candidate whose sympy run fails; PF still refuses without a sandbox;
  - `test_key_ladder_labels.py`: each rung; a numeric key with agreeing solves and no sandbox, a failed sympy run, no check written and a degenerate check are all `panel_agrees_unconfirmed`; a prose key with agreeing solves is `panel_agrees`; a rejected symbolic check is `disputed`; timed out;
  - `test_reference_gate_imports.py`: attempts on `checking`, `model_answer`, `panel_agrees_unconfirmed` and `disputed` keys record `unverified`, update FSRS and earn no certification credit; verified keys record `verified`; a later verification never rewrites earlier attempts; a historical Reader import resolves to `model_answer` after the tag and `not_applicable` before it; replay reads the stored column; a shadow rebuild of fixture copies shows zero projection deltas;
  - `test_reference_check_binding.py`: a verified import whose prompt, key or rubric is then edited records `unverified` (`changed_since_check`) until a check of the new content passes, and the edit queues that check; a background check that finishes after an edit leaves the edited item unverified and marks `superseded_by_edit`; attempts recorded before the edit keep their status; hints-only edits keep the verification;
  - `test_attach_to_family.py`: attach, undo, recover, refusal on an LO mismatch;
  - `test_canonical_exercise_serialization.py`;
  - `test_harvest_dry_run.py`: `harvest` and `verify`, each with `--dry-run` and `--max-cost-usd`.

---

## 8. S2 — Discriminating search: intents ranked by value of information

### 8.1 Typed constraints (brainstorm L1207–1240)

`PracticeConstraints` (`practice_index/retrieval.py:111`) gains the fields below. All are exact filters except `intent` and `target_hypotheses`. The names are the ones the Reader spec uses (its §9.3, §18); one change, made by whichever lands first.

| Field | Meaning | Dialogue name |
|---|---|---|
| `intent` | `practice` (default; today's relevance ranking) \| `discriminate` \| `retention` \| `remediate`. The Reader's names are accepted as aliases (`diagnostic_probe` → `discriminate`, `retention_check` → `retention`); receipts store the canonical name | `intent` |
| `target_hypotheses` | `HypothesisRef{kind, id}` with kind ∈ `misconception`, `causal_hypothesis`, `episode_label`, `unresolved_cause`, `facet_state`, `named_gap` | target hypotheses |
| `kinds` | `items` \| `source_exercises` \| `both` (added by S1, §7.1) | — |
| `unattempted_only` | No attempt on the item | `unseen_required` |
| `exclude_family_ids`, `exclude_revealed_families` | Families excluded by id, or because a member's answer was revealed within the cold delay | `exclude_exposed_families` |
| `facet_match` | `any` (default) \| `all`: an integrative problem must test every listed facet (L1107) | — |
| `allow_generated` | When false, only `canonical_extract` and owner-authored items | `allow_generated_variants` |
| `max_estimated_minutes` | Through the injected minutes estimator (DL1's `daily_plan/estimates.py:138`, SC12). Refused with a typed error when no estimator was injected, never ignored | `max_estimated_minutes` |

The two filters RW6b needs (`unattempted_only`, `exclude_family_ids`; Reader spec §3.4 item 7) are these. The dialogue's `answer_visibility` is not a field: the caller's policy sets it (§5.2).

**How exact filters are enforced, on both arms.**
- **Items** are filtered on their own fields: `evidence_facets` for `facet_ids` and `facet_match`, the injected estimator for `max_estimated_minutes`, the provenance origin for `allow_generated`, and attempts and the reveal ledger for the exposure filters.
- **Raw source exercises** have no mapped facets and no minutes. The arm's relevance call (`practice_rerank`, a new prompt version) also returns, for each exercise it keeps, **provisional metadata**:
  - the facets the exercise exercises, chosen only from the registry ids it was shown (the constraint facets and the LOs' facet union, canonical ids), each with a verbatim quote from the statement that shows it. Code checks each quote against the statement and drops a facet whose quote fails;
  - its practice mode, from the closed vocabulary.

  Minutes come from the injected estimator for that mode with no item history (`Estimator.estimate`, `daily_plan/estimates.py:118`: the mode median shrunk toward a 3-minute fallback, `:41`), with its `prior_source`. All of it is stored on the proposal's receipt (`provisional_json`: values, the rerank's ledger id, the prompt version).
- **Unknown is not a pass.** When a filter is set and a candidate's value for it is unknown, the candidate fails the filter. The manifest counts it (`failed_unknown`); it is never assumed to pass. `facet_match = all` on a raw exercise passes only when every listed facet has a verified quote.
- **Provisional until validated.** A raw exercise's match is labelled provisional ("matched on the exercise's text"). After authoring, and before the exercise fulfils a need (S2b) or serves as an independent check, the draft is validated against the same constraints:
  - its `evidence_facets` must be ones the author asserted, not the LO-union fallback the import applies when the author names none (`content/authoring/exercise_authoring.py:433`; recorded as `facet_basis`);
  - the estimator's minutes for the authored mode must fit `max_estimated_minutes`.

  A draft that fails does not fulfil the need or the check, and the next candidate is tried. A learner's own pick is still imported (learner authority), and the proposal's claim is corrected on screen ("this exercise turned out to practise X, not Y"). The result is stored on `source_exercise_imports.validation_json`.

### 8.2 Where the rival hypotheses come from

`instructional/valuation.py:open_hypotheses(facets, refs)` reads them where they already live and writes nothing:
- **an open probe episode's** locked set, with its posterior replayed (`episode_posterior`, `diagnosis/probe_episodes.py:1576`);
- **a diagnosed attempt's** rival causes (`unresolved_cause_factors.candidate_causes_json`);
- **open `causal_hypotheses`;**
- **the facet's `hypothesis_marginal`** (facet-solid, facet-absent, misconception labels);
- **active misconceptions** on the facets, from the diagnoser's overlay;
- **named gaps**, once `learner/text-gaps` has merged: `named_gaps_for_card()`'s target `{kind, id}` mapped to the matching misconception or facet hypothesis. Before the merge, a `named_gap` ref returns `unavailable: learner-text gaps not merged`. The adapter is feature-detected by the presence of the branch's table;
- **a router R1 decision's** logged `probe_eig` candidates are not hypotheses; S5 only references the decision id.

With no `target_hypotheses`, the intent uses every open hypothesis space on the constraint facets, one valuation problem each (§8.3.1).

### 8.3 Valuation (the adapter RW6b also uses, built once)

`instructional/valuation.py:value_candidates(problem, candidates, *, mode, caller_kind, estimator)` makes no model call. It computes no value of its own: it converts its inputs into the representations the existing functions take, calls them, and records what they said. Its only write is the idempotent, content-addressed snapshot of a grader channel it pinned (through `probe_robust.resolve_episode_channel`, `diagnosis/probe_robust.py:75`), so replay can rehydrate the channel. It returns a `ValuationReceipt`. `find_practice` receives it as an injected `valuer`; called without one, a value intent is refused with a typed error rather than ranked by relevance alone.

**Relevance comes first.** The listwise judge keeps the candidates that test the capability or bear on the rival hypotheses, quoting what in the candidate does so. It never picks a winner or a number.

#### 8.3.1 The valuation input

The functions this adapter calls speak different representations. The item EIG functions build their tables internally and return a float (`diagnosis/probes.py:682`, `:786`). `evsi.rank_feasible` takes `DiagnosticCandidate`s, each with credible-set `P(E|H)` matrices, a prior and its `prior_basis` (`scheduling/evsi.py:293`, `:366`). `robust_composition.evaluate_selection` takes `Ensemble`s (`diagnosis/robust_composition.py:353`). So the adapter first builds `ValuationProblem`s, one per hypothesis space:
- **One space per problem.** A hypothesis space is what one producer instance holds as mutually exclusive slots under one prior: one probe episode's locked set, one LO's hypothesis set (its misconceptions and its confusable neighbours'), one facet's marginal, one causal factor's candidate causes, one facet's retention pair (§8.3.2). The refs in a request are grouped by the space they belong to, and a named gap joins the space of the target it maps to.
- **Several spaces are separate problems, never a joint one.** Producers' hypotheses can coexist: a learner can hold two misconceptions while a failed attempt's cause is still open. No producer states a joint distribution, and assuming independence or normalizing the concatenated slots would invent one (decision-value invariant 5). So a request naming two misconceptions on one LO and an unresolved cause is two problems: the LO's hypothesis set and the factor's causes. Each is valued, stopped and verdicted on its own, and its receipt is its own. No value is summed or compared across problems. A candidate valued in several problems is listed once, with each problem's value and verdict (D18).
- **What a caller gets.** Results come back per problem. A learner-initiated result shows each problem's groups under the open question it answers ("for your open question about …"). A system-initiated caller acts for one problem (S2b's need, RW6b's open question, the four-caps stage's observation); a candidate licensed by several problems is proposed once, and the plan's minutes bound the total.
- **A decision belongs to one space.** Decision mode needs a loss table over one problem's slots (§8.3.4). A pending decision whose action map names slots of another space is refused with the typed error `mixed_hypothesis_spaces`, never merged.
- **The hypothesis space's slots:** `refs` (`HypothesisRef{kind, id}`), one slot per concrete hypothesis, and the open-set arm `H_OTHER` when the producer declares one. The prior is normalized over the concrete slots. The `H_OTHER` mass is excluded explicitly and recorded, as the causal shadow does (`diagnosis/causal_diagnostic_selector.py:279`). `prior_basis` names the producer (§8.3.2), and `state_hash` pins the state it was read from.
- **Per candidate:**
  - the `outcome_alphabet` (emission keys);
  - `members`: a tuple of `P(E|H)` tables, one row per slot, each row normalized over the alphabet; member 0 is the point estimate;
  - its `likelihood_regime` and `likelihood_basis` (§8.3.3);
  - `expected_minutes`, from the injected estimator with its provenance (`prior_source`, `n_item`, `n_mode`), and `burden_minutes` (0, the registry's);
  - `missing`: the typed reasons when any of these could not be built.
- **A pending decision** (optional): `decision_kind`, `action_by_slot` and the loss table. In v1 the only producer is a causal factor's repair-class decision, through the shadow's own builder (`build_causal_loss_table`, `diagnosis/causal_diagnostic_selector.py:130`, over `action_loss.build_loss_table`). A slot with no action is the typed `no_action_mapping`; it is never dropped and the rest renormalized.

Every table is checked before use: each row sums to 1 over the alphabet, and every prior slot has a row. A failed check is an exclusion with its reason (`EVSIInputError`'s reasons, `scheduling/evsi.py:68`), never a repair.

#### 8.3.2 Adapters per hypothesis kind

| Kind | Slots and prior (`prior_basis`) | Likelihood rows | When something is missing |
|---|---|---|---|
| `episode_label` (an open probe episode) | The locked set. Prior: `episode_posterior` (`diagnosis/probe_episodes.py:1576`); basis: the set's stored `prior_basis`, else `episode_posterior` | Compiled instruments: `probe_robust.instrument_ensemble` on the episode's pinned channel (`diagnosis/probe_robust.py:199`). Ordinary items: `probes.conditional_distribution` (`diagnosis/probes.py:487`) | No live posterior: `no_prior`. Below the robust probe cutover (`use_robust_probe`, `diagnosis/probe_robust.py:51`), instruments are valued as ordinary items |
| `misconception` (active, from the diagnoser's overlay) | `build_hypothesis_set` for the misconception's LO (`diagnosis/probes.py:128`; its slots are `mastered`, `unfamiliar` and one `misconception:<id>` per active belief on the LO and its confusable neighbours, up to `probe.hypothesis_set_max_size`, `:250`), so misconceptions on one LO share one space; basis `hypothesis_set` | `probes.conditional_distribution` with the item's estimated discrimination row, or the bridge default where a rubric fatal error links the belief (`:595`) | No set can be built: `no_hypothesis_set`. A target the size cap left out of the set: `not_in_hypothesis_set`. An item with neither a row nor a linked fatal error is modelled as not discriminating that belief (it can still separate on score), as the follow-up chooser does |
| `facet_state` | The facet's `hypothesis_marginal`; basis `facet_marginal` | `probes.facet_conditional_distribution` (`:731`) | No marginal row: `no_prior` |
| `causal_hypothesis`, `unresolved_cause` | The factor's concrete hypotheses, `H_OTHER` excluded explicitly; basis `hypothesis_sets.prior_basis` (`support_weighted`, `uniform_fallback` or `model_verbalized_prior`) | `likelihood_regime_for_candidate` (`diagnosis/causal_diagnostic_selector.py:195`): arm B gives one noiseless member; arm C gives none | Arm C: `incomplete_likelihoods`. An unmapped slot: `no_action_mapping`. A basis other than `support_weighted`: `prior_unsupported` (`scheduling/evsi.py:65`) |
| `named_gap` | Mapped to the misconception or facet hypothesis its target names, then that row | As that row | Branch absent: `unavailable: learner-text gaps not merged`. A target that maps to neither: `unmapped_named_gap` |
| `retention` | `holds_unaided` and `not_unaided`, for a facet whose recent success was assisted only. Prior: the active predictor's P(success); basis `predictor`, with its version | Declared rows composed with the grader channel resolved for the LO (`probe_robust.resolve_episode_channel`), as the robust probe path composes card rows: `holds_unaided` → the channel's correct class, `not_unaided` → its incorrect classes. How mass splits among the incorrect classes is unknown, so the credible set holds the extreme splits and the robust value covers them. Nothing is invented | No predictor value: `no_prior`. No channel can be resolved: `no_channel`. A channel that fell back records its `fallback_reason` on the receipt |
| Unimported source exercise | Any of the above | The screen (§8.4): a complete partition is arm B; anything else is structural | Not screened (budget): `not_screened`. Incomplete: `structural_only` |

#### 8.3.3 Likelihood regimes, and what each may license

Every candidate's valuation is stamped with its regime:

| Regime | Built from | Credible set |
|---|---|---|
| `pinned_channel` | Declared rows composed with a pinned grader channel: compiled probe instruments; retention checks | `build_ensemble`'s draws (`diagnosis/robust_composition.py:210`): the channel's Dirichlet posterior and perturbed rows. 1 + `ROBUST_DRAW_COUNT` members (`:43`); a retention check holds that many per extreme split |
| `item_point` | Ordinary items, imported exercises: IRT point tables with an estimated discrimination row or the bridge default. `likelihood_basis`: `estimated_row`, `bridge_default`, `authored_profile_unchecked` (an import whose profiles have not passed the persona gate) or `authored_profile_checked` | Member 0 plus `evsi.stress_matrices`' ±0.15 perturbations (`scheduling/evsi.py:276`): three members, a robustness check, labelled as such, not a calibration |
| `arm_b_noiseless` | Complete partitions: causal candidates with complete blind bundles, unimported exercises with a complete screen | One noiseless member, so the value is an upper bound |
| `structural` | Incomplete rows or bundles | None |
| `arm_a_calibrated` | Reserved (`diagnosis/causal_diagnostic_selector.py:53`). The calibration track's to fill (§11.4) | — |

A **learner-initiated** request is the learner's own search or a tutor offer the learner presses; the learner decides what to attempt. A **system-initiated** check is one the learner did not ask for: S2b's fulfilment, RW6b's dated checks, the four-caps stage (§20) and router R2.

| Regime | In a learner-initiated result | Licenses a system-initiated check | Licenses a skip |
|---|---|---|---|
| `pinned_channel` | valued | yes, on `act` or `measure` | yes |
| `item_point` | valued | no | yes |
| `arm_b_noiseless` | bounded: shown with "at most …" | no (decision-value §6.2 B) | yes, when even the bound fails the stop |
| `structural` | unvalued: listed with the reason | no | no |

A learner-initiated result therefore has three groups: valued candidates in value order with the stop marked, bounded ones, and unvalued ones with their reasons ("LearnLoop can't estimate how much this would tell you"). The learner decides.

**S2b takes no license from a valuation.** It uses the verdicts to order candidates, to skip them and to stop (§8.5), and it serves only a draft that passes the follow-up chooser's own gate, the rule the chooser applies to any item it serves. That gate, not the regime, is what licenses an S2b check.

#### 8.3.4 Modes, verdicts and stopping

- **Information mode** (no pending decision). Each candidate's robust EIG over its members is converted to minutes by `VALUE_PER_NAT_MINUTES` and ranked per minute, with `robust_composition`'s stop rule and action-agreement gate. The verdicts are `evaluate_selection`'s: `act`, `stop` and `couldnt_reliably_distinguish` (`diagnosis/robust_composition.py:353`). Compiled instruments are valued exactly as the robust probe path values them (`probe_robust.robust_selection`, `diagnosis/probe_robust.py:288`). An `item_point` candidate's members are wrapped as an `Ensemble` whose hash names its IRT parameters and discrimination rows. A surface made familiar by recent *attempts* has its EIG multiplied by `familiarity_discount`'s `independent_evidence_discount`, as the scheduler does for probes (`learner/recall_coverage.py:293`, `scheduling/scheduler.py:450`). That function reads attempts only, so reading exposure has its own rule (§5.4). Decision mode applies no such multiplier: EVSI comes from the likelihoods alone.
- **Which candidates one selection compares, and how.** A selection runs inside one problem (§8.3.1). Its candidates' credible sets can have different sizes: 129 members for `pinned_channel`, more for retention, three for `item_point`, one for a bound (§8.3.3). `evaluate_selection` pairs members by index and sizes its loop by the winner's count (§3.2 item 20), so unequal sizes raise `IndexError` or silently read a prefix. Therefore:
  1. **Who competes.** A system-initiated caller that takes its license from the verdict (RW6b's dated checks, the four-caps stage, router R2) compares only candidates whose regime licenses it (§8.3.3), in either mode. The others are listed with `regime_cannot_license`; when none is left, the result is `abstain` with that reason. A learner-initiated selection in information mode compares the valued group (`pinned_channel` and `item_point`). In information mode a bound (`arm_b_noiseless`) and an unvalued candidate never enter a selector: a bound is compared only with the stop, to license a skip, and a `structural` candidate is only listed. S2b takes no license from the valuation (§8.3.3); its screened exercises are bounds, which it skips or keeps in information mode and ranks with `rank_feasible` in decision mode (§8.5).
  2. **Same shape: the live selector, unchanged.** When every candidate's ensemble has the same member count and the same construction (one regime, and for `pinned_channel` one channel; `item_point`'s three members pair point with point and each stress with the same stress), the adapter calls `evaluate_selection` exactly as `probe_robust.robust_selection` does. An instrument-only request therefore gets the robust probe path's verdict (a parity test).
  3. **Mixed shapes: independent credible sets.** Otherwise the adapter calls a new `robust_composition.evaluate_selection_credible_sets` (built in S2a beside it). Each candidate's members are an equally weighted credible set of its own, and nothing is paired by index. The live path's pairing already joins independent draws: each candidate's ensemble is seeded from a decision-context hash that names its own card version (`diagnosis/probe_robust.py:211`–`:224`), so member *i* of one candidate has nothing in common with member *i* of another, and the product form computes exactly what index pairing samples.
     - Rank score: `robust_eig_per_second` over the candidate's own members (`diagnosis/robust_composition.py:341`), unchanged.
     - The winner's margin: the `ROBUST_QUANTILE` lower quantile of the winner-minus-runner-up EIG per second over every pair of their members.
     - Action agreement: the probability that the winner tops every rival when each candidate's member is drawn independently. That is the mean, over the winner's members, of the product over rivals of the share of the rival's members that score no higher. Ties go to the winner, as `max` gives them to the first-ranked candidate. It is compared with the same `ENSEMBLE_ACTION_AGREEMENT_THRESHOLD` (`:46`).
     - Stop rule and verdicts: `evaluate_selection`'s, on the winner's own members.
     - No sampling: one EIG per member, then comparisons.
  4. **A guard.** `evaluate_selection` raises a typed `EnsembleShapeError` on unequal member counts instead of indexing past the end or reading a prefix. Live inputs always have equal counts, so the robust probe path is unchanged (its tests pin it).

  Decision mode needs no shape rule: `rank_feasible` values each candidate on its own members (`robust_evsi`, `scheduling/evsi.py:199`) and stresses each on its own, so unequal sizes are well defined there.
- **Several checks** (information mode). After the first pick, each later candidate is valued by its expected robust EIG over the predicted-outcome branches of the picks so far. Each branch's posterior is updated with `robust_composition.observed_update` (`diagnosis/robust_composition.py:293`) on member 0. This is the rule `plan_precommitted_block` uses (`diagnosis/probe_episodes.py:1386`), without its block-size bound. Each step compares the remaining candidates by the rule above. Adding stops at the first `stop`. The branch tree is truncated as that function truncates it, which bounds compute, not the number of checks. Two checks that would say the same thing are therefore not both proposed.
- **Decision mode** (a pending decision with a loss table). `rank_feasible` over `DiagnosticCandidate(members, prior, expected_minutes, burden_minutes, prior_basis)`. In v1 a decision's hypothesis space is the causal factor's own (§8.3.1), so its prior carries the stored basis and `rank_feasible`'s live-basis rule applies unchanged. EVSI values the *next* decision, so the result is the best check for it, if any. The next check is valued after that check's outcome, against the updated state. That is the definition of EVSI, not a count cap.
- **Verdicts, translated as the decision-value spec's §6.5 does:**

  | Verdict | What the caller gets |
  |---|---|
  | `act` or `measure`, from a regime that licenses this caller (§8.3.3) | The check or checks, in order |
  | A system-initiated request in which no candidate's regime licenses the caller | `abstain`, reason `regime_cannot_license`: a point model or an upper bound is not a license for a system-initiated check, so nothing is offered. In a learner-initiated result such candidates stay in their groups (valued, bounded or unvalued) |
  | `stop` with `common_action` | No check. The receipt names the common action for the caller to apply. S2b ends its diagnostic fulfilment of the need (§8.5 step 3) |
  | `stop` with the current optimal action | No check. The receipt names that action and its declared uncertainty. S2b ends its diagnostic fulfilment of the need (§8.5 step 3) |
  | `abstain` (`downstream_action_flip`, `stress_action_flip`, `stress_winner_flip`, `couldnt_reliably_distinguish`, `regime_cannot_license`) | No check. The caller holds the branch-specific action and takes the stronger-instrument or review path: S2b leaves the need open, and its generation lane authors an instrument (persona-gated, §8.5); RW6b records the reason on its card |
  | No evaluable candidate | `no_discriminating_instrument`, with every exclusion's typed reason |

  S2b reads this table as §8.5 step 3 says: `measure` only orders its tries, and the follow-up chooser's gate licenses each one.

- **No fallback.** An abstention or an exclusion never falls back to an entropy order as authority to ask another question (decision-value invariants 4–6). In a learner-initiated result the candidates stay listed in their groups (§8.3.3), and the learner decides.
- **The number follows.** The result is every check that clears the stop: often none, sometimes several. `limit` does not apply. What a learner is actually served stays bounded by the plan's minutes.
- **Paging is resumable, and a rejection says nothing about later candidates.** The judge sees the fused order a page at a time (`candidate_pool`, a prompt-size bound). Paging continues until one of these holds, and the receipt says which:
  1. **Exhausted: every admissible candidate has been offered to the judge.** `limit` plays no part, because it only cuts the fused order (§3.2 item 21). Exhaustion is decided per retrieval list:
     - **Spans.** S1 gives `search_spans` a `list_depth` parameter (default `LIST_DEPTH`, so existing callers are byte-identical) and two result fields: `list_ends`, which says per list whether it reached its source's end, and `fused_keys`, the whole fused order. A keyword, rewrite-keyword or substring list has ended when its query returned fewer rows than asked, counted before the scope filter (`db/stores/source_block_fts.py:75`). A dense list has ended when `DenseIndex.rank`, which applies the scope filter before counting, returned fewer than asked (`source_retrieval/dense.py:90`). An `extra_lists` list is complete as passed. A continuation re-runs `search_spans` with `list_depth` doubled for the lists that have not ended, reusing the stored query vectors and rewrite (`query_vectors`, `rewritten`, `source_retrieval/search.py:141`–`:142`), so it pays for no second embedding or rewrite. It then judges the next unjudged keys of `fused_keys`. Spans are exhausted when every list has ended. A deeper pass that adds no new key while some list has not ended does not end paging.
     - **Items.** With item vectors, the direct path ranks every admissible item that has a vector (`_vector_ranking` with `limit=len(manifest)`, `practice_index/retrieval.py:330`, `:337`). Item BM25 ranks only items that share a term (`practice_index/text.py:75`), and the dossier path ranks only the items under its top facets (`_top_facets`, `practice_index/retrieval.py:364`). So a continuation first widens the dossier's facet stage to the next facets in its fused facet order. Once every facet is in, and every list has ended, the admissible items that no list ranked are offered last, in id order, labelled `unranked` ("didn't match your words; still on these facets"). Items are exhausted when the admissible corpus has been offered in full.
  2. **Budget.** The request's money cap or deadline is reached. The result says how many candidates are still unjudged and returns a continuation cursor: the query hash, each list's depth and end flag, the dossier's facet depth and the judged keys. A later call with the cursor resumes where this one stopped.
  3. **Nothing left can clear the stop** (value intents only). No single check can be worth more than perfect information: in decision mode, the expected value of perfect information under the loss table; in information mode, the target hypotheses' entropy after the checks already chosen, converted by `VALUE_PER_NAT_MINUTES`. When that bound is ≤ λ · (the least expected minutes among the unjudged candidates) + burden, no unjudged candidate can clear the stop. This is the decision-value spec's universal skip bound (§6.2 C).

  For `practice`, the page is a display page, and the cursor continues it when the learner asks for more.
- **No new constants.** λ, the burden and the nat-to-minutes scale are the existing heuristic decision parameters (`diagnosis/robust_composition.py:48`, `:49`, `:55`), read from there so that a calibration lands everywhere at once (§11.4).

**Intents.**
- **`discriminate`:** the steps above, over the rival hypotheses. Information mode, or decision mode when the caller passes a pending decision.
- **`retention`:** information mode over the retention adapter (§8.3.2). Only unexposed candidates qualify, and a `related` worked-example verdict excludes (§5.4). The caller dates the check (RW6b, DL2).
- **`remediate`:** practice that repairs a named misconception. The relevance judge keeps candidates keyed to it (a fatal error or profile naming it, or the target facet), ranked by relevance; no EVSI.
- **`practice`:** today's ranking.

**The receipt** is stored on the proposal row, one section per problem (§8.3.1). Each holds the hypothesis space, its prior and basis, the mode and which selector ran (`evaluate_selection` or `evaluate_selection_credible_sets`). Then, per candidate: the regime and likelihood basis, the missing-data reasons, EIG, EVSI point, LCB and UCB, expected minutes and their provenance, the exposure verdicts and the reading-exposure adjustment (§5.4), the verdict and its translation, the stop reason, the paging outcome, and the module versions. Fields R1 also logs use R1's names (`probe_eig`, `evsi_assignment`), so R3's replay can read both.

### 8.4 Source exercises as discriminating candidates (the "probe" half)

An exercise that has not been imported has no rubric and no profiles. For `discriminate`, the arm's judged exercises go through one screening call (route `exercise_discrimination`, listwise):
- per rival hypothesis, what a holder would visibly write on this exercise (an `observable_signature`, the `DiscriminationProfile` field, `vault/models.py:446`);
- whether the signatures differ observably.

The screen is classified as the decision-value spec classifies blind bundles (its §6.2; `likelihood_regime_for_candidate`, `diagnosis/causal_diagnostic_selector.py:195`):
- **A complete screen** gives every rival hypothesis exactly one signature over one key schema, says what any other cause would produce (the `H_OTHER` disposition), and gives no two hypotheses the same signature. It is a noiseless partition (`arm_b_noiseless`): its EIG is exact for a noiseless channel and an upper bound on the real one. It can license skipping the exercise when even that bound fails the stop. It cannot license asking the learner (§8.3.3), and it is never "softened" into a likelihood with the bridge's binary sensitivity and specificity, which define no multiclass channel.
- **An incomplete screen** is a structural audit (`structural`), not a likelihood. The candidate gets no value.

The receipt stamps the regime and `likelihood_basis = model_screen_unchecked`. The learner-facing label says "LearnLoop's reading of the exercise, not yet checked: at most …". The hypotheses' prior keeps its producer's `prior_basis`, so `rank_feasible`'s rule that only a `support_weighted` causal prior is valued live (`scheduling/evsi.py:65`) applies unchanged.

**How a screened exercise becomes a valued check.** When one is chosen and imported (a learner's pick, or S2b), its profiles are written on the item (`discrimination_profiles`, `vault/models.py:718`) and its rubric's fatal errors link the screened misconceptions. It is then an ordinary item valued under `item_point` (`authored_profile_unchecked`), and `authored_profile_checked` once the planted-persona gate passes (`content/authoring/persona_gate.py`). The diagnoser remains free to say `no_profile_applies`.

Source exercises chosen this way are served as **ordinary items** through the paths in SC1. Promoting them to formal probe instruments (compiled conditionals, probe episodes, the `pinned_channel` regime) is deferred (§19).

### 8.5 S2b — Source-first fulfilment of intervention needs (successor)

When the follow-up chooser finds no suitable item, it records an intervention need with `blocked_reason = "no_suitable_item"` (`diagnosis/followups.py:381`). Adapters fulfil needs on demand through the generation lane (`generate_diagnostic_practice_proposal`, `content/authoring/practice_generation.py:646`, which plans from `:441`):
- the primed-retry handler when the LO has no sibling (`learnloop_sidecar/handlers/feedback.py:571`, calling generation at `:613`);
- the CLI's `learnloop generate-diagnostics` (`cli/app.py:2568`).

S2b adds one step in those two adapters, before they generate. The tutor's promotion path also generates for needs (`tutor/promotions.py:741`); it lives in a domain package, which may not import the service (SC12), so it keeps generating, and wiring it through an injected callable is left to a follow-on.
1. `fulfil_need_from_sources(need)` calls `find_practice` with `kinds = source_exercises` and the need's target facets.
   - The intent is `remediate` in the primed-retry handler, because that item is served primed, as a repair, and a primed answer can't be an independent check. In the CLI path it follows the need: `discriminate` when its diagnostic focus names rival misconceptions, `remediate` otherwise.
   - It also applies the need's `candidate_requirements` (same LO, minimum facet overlap).
2. Candidates are tried in the order the valuation gives (for `remediate`, the judge's order; in decision mode, after step 3's verdict allows it). Screened exercises (§8.4) only order and skip; they never license (§8.3.3). In information mode a screened exercise whose upper bound fails the stop is skipped, and the rest are tried in the order of their bounds per minute. For each candidate, before anything is written:
   - the draft is authored and the ladder runs; only a verified key (§7.3: `book_solution`, `checked` or `panel_agrees`) can fulfil the need;
   - the draft is validated against the request's constraints (§8.1);
   - for `discriminate`, the draft must pass the follow-up chooser's own gate, the one it applies to any item it would serve: `misconception_discrimination` (the public form of `_misconception_discrimination`, `diagnosis/followups.py:1482`) finds it diagnostic-eligible against an active belief. S2b adds no authority of its own; it fulfils the chooser's need by the chooser's rule.

   A draft that passes is written and attached. A draft that fails any check is not written: the `source_exercise_imports` row keeps it with `status = rejected`, its reason and its verdicts, and the next candidate is tried.
3. **Decision mode.** When the need's attempt has an open causal factor (a pending repair choice), the valuation runs in decision mode. This happens on the CLI path only: the primed-retry handler's `remediate` intent has no valuation. Each verdict is handled as decision-value §6.5 says:
   - **`measure`:** step 2 tries the candidates in `rank_feasible`'s order.
   - **`stop`, with the common action or with the current optimal action:** measurement is not worth its minutes for this decision, so S2b ends its diagnostic fulfilment (D19). Nothing is imported and nothing is generated for this need. The need becomes `stale` with `blocked_reason = value_stop:<common_action|current_action>:<proposal id>`, the convention the generation lane already uses for a need that no longer asks for measurement (`content/authoring/practice_generation.py:569`, `:602`).
     - S2b chooses no repair. The causal path's live receipt carries it (`repair_class_ids`, `diagnosis/causal_orchestrator.py:1477`), and that repair proceeds with no further diagnostic.
     - The receipt records the valuation's named action beside the live repair class. If they differ, S2b logs `action_disagreement` for the calibration track and S5 and leaves the live repair alone: letting EVSI choose repairs is the decision-value spec's own promotion, after its shadow baselines (its §6.6).
   - **`abstain`** (an action or winner flip): no source candidate is tried. The need stays pending, and generation, the stronger-instrument path, proceeds (step 5).
   - **`no_discriminating_instrument`** (no candidate, or none evaluable): generation proceeds as today (step 5).

   The verdict, its reason and the named action are stored on the need's receipt: the proposal row S2b's `find_practice` call writes (`caller = need`, `caller_ref` = the need id, the verdict in `valuation_json`). Nothing ever falls back to an EIG-ordered exercise.
4. The written item fulfils the need (`status = fulfilled`, linked in `source_exercise_imports.need_id`). When the follow-up serves it, independence is checked again (§5.4); if it fails, the follow-up serves it as practice, labelled, and S5 records why.
5. Otherwise generation proceeds exactly as today. S2b relaxes none of the requirements a generated check meets before it is served: the generation lane's planted-persona gate and pair gate (`content/authoring/practice_generation.py:682`), which reopen the need instead of consuming it when the new instrument cannot discriminate (`:720`–`:733`); acceptance, which refuses an invalid row; and, at serving, the follow-up chooser's own gate and the independence re-check (§5.4).

This is the dialogue's "retrieval first, generation on demand" (L1163–1165) for the system-initiated path.

**Successor:** the next free `mvp-0.N` at merge, because it changes which item a follow-up serves. Kill switch `source_service.source_first_needs`; off, the generation lane is byte-identical (G10). Vaults below the tag never run it.

### 8.6 Data, routes, spend, gates, tests

- **Migrations:** 190 (S2a) adds `practice_index_proposals.valuation_json` and `provisional_json`; 191 (S2b) adds `source_exercise_imports.need_id`. All are nullable `ADD COLUMN`.
- **Routes:** `practice_rerank` (relevance), `exercise_discrimination` (new), `worked_example_equivalence` (new; §5.4 rule 4 is built here). The valuation makes no call.
- **Spend:** within `source_service.max_daily_cost_usd`; S2b's imports are capped per import.
- **Kill switches:** `source_service.discriminating_search` (off: every intent except `practice` is refused with a typed error); `source_service.source_first_needs` (S2b).
- **Gates:** G1, G8, G9, G10, G13, G14, G20.
- **Tests:**
  - `test_practice_constraints_v2.py`: each filter on both arms, the minutes estimator required, the Reader's intent aliases;
  - `test_exact_filters_raw_exercises.py`: provisional facets need verified quotes; unknown values fail a set filter and are counted; `facet_match = all`; post-import validation rejects LO-union facets and over-long drafts for needs and independent checks, and corrects the claim on a learner's pick;
  - `test_valuation_input.py`: every adapter row of §8.3.2 builds normalized tables or returns its typed missing reason; `H_OTHER` excluded explicitly; an unmapped slot is `no_action_mapping`, never renormalized away; retention's extreme splits are in the credible set; two misconceptions on one LO plus an unresolved cause give two problems, each normalized over its own slots, with no joint prior, no summed value and a candidate listed once with both verdicts; a decision whose action map names another space's slots is refused `mixed_hypothesis_spaces`;
  - `test_value_candidates.py`: a fixture with known EIG and EVSI; stop and its common action; each abstention reason with no fallback; `regime_cannot_license` for `item_point` and `arm_b_noiseless` on a system-initiated request; the three groups of a learner-initiated result; greedy conditional valuation drops a redundant second check; no count cap (three candidates clear and three return); mixed regimes in one learner-initiated problem (a 129-member instrument, a three-member item) with each winning in turn give `evaluate_selection`'s verdict set and no `IndexError`; a system-initiated selection compares only licensing candidates; an instrument-only request matches `probe_robust.robust_selection`;
  - `test_evaluate_selection_credible_sets.py`: the margin's quantile over every member pair and the agreement probability on hand-computed fixtures with unequal sizes; ties go to the winner; `evaluate_selection` raises `EnsembleShapeError` on unequal sizes; the robust probe path's existing tests pass unchanged;
  - `test_valuation_paging.py`: a page whose first candidate is rejected still pages on; exhaustion, budget (with a cursor that resumes) and the perfect-information bound each end paging with their reason; a continuation makes no second embedding or rewrite call; a relevant span ranked below `LIST_DEPTH` in every list (a fixture with more than 200 keyword and dense matches) is reached by a continuation; raising `limit` alone never marks a list ended; an item outside the dossier's first facets and an admissible item no list ranks are both offered before exhaustion is declared;
  - `test_open_hypotheses_adapters.py`, with the named-gap adapter absent and present;
  - `test_exercise_discrimination_screen.py`: complete screens are `arm_b_noiseless` upper bounds, incomplete ones `structural`; no bridge softening;
  - `test_reading_exposure_adjustment.py`: `equivalent` excludes both independent intents; `related` excludes `retention`, keeps `discriminate` with the label and the dominance order, and changes no value; no attempt rows are written;
  - `test_source_first_needs.py`: fulfilment; the chooser's gate applied to the draft; a failing draft not written; disputed and `panel_agrees_unconfirmed` keys refused; `stop` with the common action and with the current action each end fulfilment, with nothing imported, nothing generated, the need `stale` with its `value_stop` reason and the live repair untouched (an `action_disagreement` logged when the actions differ); `abstain` and `no_discriminating_instrument` lead to generation, whose item passes the persona and pair gates before it can fulfil the need; no EIG fallback; serve-time recheck; kill switch parity; version gating.

---

## 9. S3 — `find_sources` with intents, and syntopic retrieval

### 9.1 The function: one shared contract

`source_retrieval/find_sources.py`. The Reader spec's §7.2 (checked at `df23187e`) defines the base signature and policies; this spec adds the intents. Whichever lands first creates the function, and the other extends it. Every parameter the Reader names keeps its name, default and meaning:

```python
RetrievalPolicy = Literal["reading", "assisted_practice", "post_attempt", "cold_attempt"]

def find_sources(
    vault, repository, query: str, *,
    policy: RetrievalPolicy,
    intent: Literal["explain", "remediate", "alternative", "worked_example", "compare"] = "explain",
    scope: Literal["library", "teaching"] = "library",
    learning_object_ids=(), facet_ids=(),
    item: PracticeItem | None = None,      # required for assisted_practice and post_attempt
    roles=(),                              # ingest's role_hint or a Reader RW4e role proposal
    expand=(),                             # "prerequisites" | "applications" | "confusables"
    exclude_span_ids=(),                   # span keys; alias: exclude_span_keys
    target_hypotheses=(), learner_work_md: str | None = None, personalized: bool = True,
    verify: bool = False, limit: int = 8, cursor=None,
    embedder=None, rewrite_client=None, rerank_client=None, deadline=None,
) -> SourceHits   # hits (verbatim span, source, section, page, revision, expansion label) + manifest (§5.5)
```

- **From the Reader's contract, unchanged:**
  - the four policies of §5.1, including the restored `post_attempt`; `cold_attempt` returns nothing;
  - `scope` defaults to `library`; this spec's own callers (the tutor's provider, remediation) pass `teaching`;
  - `roles` is a positive filter: a span matches when its effective `role_hint` or a Reader RW4e role proposal is in the list (`low` confidence only when nothing better exists). Exclusions stay with ingest's hints and item links; a proposal never admits a block into an item-bound scope (the Reader's G44);
  - `expand` fuses each LO-graph expansion as its own RRF list through `extra_lists`, labelled on the hit;
  - `verify` defaults to false for `explain`, as the Reader has it. Every other intent always verifies, because its verdict set is the intent (§9.2).
- **Added here:** `intent`, `target_hypotheses`, `learner_work_md`, `personalized`, and `cursor` (resumable paging, §8.3.4).
- **Span ids.** `exclude_span_ids` takes span keys `(extraction_id, span_id)` or their `block_span_v1` strings (`ingest/locators.py:35`). `exclude_span_keys` is accepted as an alias.
- **`authoring` is not a policy here.** S1's verifier builds its scope itself (§5.1, §7.3), as the Reader spec chose.
- `limit` is a display page; `compare` delegates to `compare_sources` (§9.4).
- **Consumer-contract tests** (G21) make each call exactly as the Reader spec writes it: RW4a's `find_sources(policy="reading", verify=True, expand=["prerequisites", "applications"])`; RW1c's `intent="alternative"` with `exclude_span_ids`; `post_attempt` with an item before and after its attempt window closes (and the reveal it records); `roles` matching an RW4e proposal; RW2c's `find_examples` over `assisted_practice`; and RW6b's `find_practice` with `retention_check` and `diagnostic_probe`. Each returns the documented fields.

### 9.2 Recipes per intent

Every intent runs `search_spans` over the policy's scope, with extra ranked lists fused by RRF. Then one listwise verification call checks fit for the intent (route `source_rerank`, ledger task `source_intent_fit`, with a verdict set per intent), and only picked spans are returned. `explain` verifies only when the caller passes `verify=True` (§9.1); unverified `explain` hits are returned in rank order and labelled so.

| Intent | Extra ranked lists | Verdicts (best first) | Dialogue |
|---|---|---|---|
| `explain` | The LOs' linked spans (as T6's provenance list) | `answers` / `related` / `unrelated` (T6's) | Mode 1–2 material (L1252–1260) |
| `remediate` | §9.3 | `addresses_confusion`, `contrasts` (the passage explicitly separates the two confused ideas), `related`, `unrelated` | Targeted remediation (L1309–1326) |
| `alternative` | Hits from sources other than those of `exclude_span_ids` (the spans already shown in this thread or inquiry, read from the question events' manifests and exposure rows) | `different_treatment` (another source, representation or role), `same_treatment`, `unrelated` | "An alternative explanation of a concept the learner has struggled with" (L1105) |
| `worked_example` | `roles=["worked_example"]` as a positive filter; `learner_work_md` goes into the verification context | `follows_learner_route` ("should not have to restart", L1242–1246), `worked_example`, `unrelated` | L1103, L1242 |
| `compare` | §9.4 | §9.4 | L1328–1342 |

- **Personalization.** `remediate` and `alternative` read learner state, and the result says so ("chosen for your open question about …"). `personalized = False` gives plain retrieval rank, the dialogue's guard against confirmation bubbles (L877). Callers expose the toggle.
- **Source objects** (`migrations/094_source_objects.sql`), where they exist, add one more ranked list for intents whose object type matches: `worked_example` → `worked_example`; `explain` → `definition`, `claim`, `procedure`. Once the Reader's RW4e has written role proposals (`authorial_role`), they add one more: `remediate` reads `contrast` and `counterexample`; `alternative` reads `alternative_treatment` and `intuition`; `explain` reads `explanation`, `definition` and `theorem`. A `low`-confidence proposal counts only when nothing better exists. Citations are resolved from revision to extraction with `resolve_extraction_id`. Nothing is written to them here.

### 9.3 Misconception-conditioned retrieval (`remediate`)

For each target misconception (from `target_hypotheses`, the item's active misconception in the diagnoser's overlay, or a named gap):
- **Query:** the learner's question when there is one, else the misconception's statement plus its `correction_statement`.
- **Extra list `correction_facets`:** the spans named by the `locator`s of the misconception's `target_facet` and `confused_with_facet` source refs, parsed with `parse_block_span` (the remediation path's own resolution, `diagnosis/remediation.py:196`).
- **Extra list `correction_sources`:** keyword hits restricted to the sources named by `correction_source_span_ids` (§3.2 item 2: source ids). The field is read for the first time. Rows whose ids name no current source contribute nothing, and the manifest says so.

### 9.4 `compare_sources`: the syntopic operation (L242–262, L869–875, L1328–1342)

`source_retrieval/compare.py:compare_sources(vault, repository, query, *, caller, facet_ids=(), requested_perspectives=(), pinned_span_ids=(), policy=None, deadline=None) -> Comparison`. The Reader's compare UI (its RW4a and RW4d), the tutor's offer and S4's tool of the same name all call this function. It is the Reader spec's §7.8 signature plus `caller`:
- **`caller`** is the server-derived caller context (§5.2): kind, item, attempt, cold status. The RPC handler and the tool dispatcher build it from the request's context; a model or a UI cannot supply it.
- **`policy`** is derived from `caller`. The Reader's `policy` argument is kept as an assertion: when it is given and differs from the derived policy, the call is refused (G2), so an argument can never widen a policy.
- `pinned_span_ids` takes span keys or `block_span_v1` strings; `pinned_span_keys` is accepted as an alias.

1. **Policy first.** `cold_attempt` refuses. `reading` compares across the library scope. `assisted_practice` compares within the item-bound teaching scope, with every item-linked passage, every `exercise` and `solution` block, and every passage the answer-overlap filter catches excluded (`source_retrieval/tutor.py:125`). `post_attempt` follows §5.1, and a solution it shows records a reveal.
2. **Counterparts: every source in scope is considered.** One `search_spans` per source in the policy's scope, restricted to that source's extractions and sharing one query embedding and rewrite (`query_vectors`, `rewritten`), so no source is missed because another source filled a page. Each requested perspective adds one more query whose hits carry its label (the Reader's rule). Each source's best keys are then verified in pages, best-ranked sources first, until every source with a hit has been verified or the money or time budget is reached. A source left unverified is listed as "possible match, not checked", never dropped silently.
3. **Pins obey the policy.** Pinned spans pass the same filters as discovered ones before anything reaches the comparison model: scope membership, item exclusions, the item-bound role exclusions and the answer-overlap filter. A pin never overrides an exclusion. A pin that fails is dropped and listed with its reason ("not available while you're practising this item").
4. **As many sources as fit are compared.** Sources are ordered by verified relevance, and as many as fit `source_service.compare_max_prompt_tokens` (default 24,000; a prompt-size bound) are compared. The rest are listed as "also discussed in: …", uncompared, with their passages one click away. The result says so honestly. **There is no source cap.**
5. **One comparison call** (route `source_compare`) returns:
   - per source, its distinct contribution, and its perspective as either a requested perspective it satisfies or one it names (for example "geometric view", "application");
   - per requested perspective with no source, "not found in your library";
   - per pair, a relation ∈ `equivalent`, `different_assumptions`, `different_notation`, `disagreement`, `unclear` (the Reader's labels; how two sources complement each other is each one's distinct contribution).

   Every statement quotes its own source's passage. The quote is verified in code: its normalized text must appear in that passage, and a line that fails is dropped, not repaired.
6. **No consensus.** The output schema has no merged or "canonical" answer field (L261, L1342). Source claims, LearnLoop's comparison lines (labelled AI-written) and the learner's notes stay separate.
7. **Stored** in `source_comparisons`, with the caller context and the policy, so a reopened comparison is not paid for twice. A Reader `library_asks` row refers to it by id (§20). Nothing is written to `source_object_relations` here; the Reader's "Keep this comparison" (its RW4d) writes those proposals from a stored comparison.

### 9.5 Consumers built now

- **Tutor grounding.** `TutorSpanProvider` (`source_retrieval/tutor.py:70`) gains an intent: `remediate` when the item's LO has an active misconception in the diagnoser's overlay (practice and feedback contexts), `explain` otherwise. There is no extra call; only the lists and the verification prompt differ. Kill switch `source_service.tutor_intents`.
- **Remediation passages.** `prescribe_remediation` (`diagnosis/remediation.py:173`) calls `find_sources(intent="remediate", policy="assisted_practice")` for the episode's misconception, through an injected provider (diagnosis never imports the service, SC12).
  - It keeps at most the passages the overlay already shows, one per role.
  - When verification cannot run or times out, today's first-linked-span choice is used and labelled.
  - Delivery exposure is recorded as today (`:233`).
  - Kill switch `source_service.remediation_passages` (off: byte-identical prescriptions).
- **The Reader** (RW4a ask and compare, RW4b, RW2b bridging) and **the tutor's offers** (S4).

### 9.6 Data, routes, spend, successor, gates, tests

- **RPCs** (desktop-only, G16): `find_sources` and `compare_sources`, for the Reader's UI and for the tutor's offers.
- **Migration 189: `source_comparisons`** (WORKFLOW; paid output, never re-run on rebuild): `id`, `query_hash`, `query_md`, `requested_perspectives_json`, `counterpart_keys_json`, `comparison_json`, `dropped_lines_json`, `dropped_pins_json`, `unverified_sources_json`, `policy`, `caller_context_json`, `model`, `prompt_version`, `ledger_ids_json`, `caller`, `caller_ref`, `created_at`.
- **Routes:** `source_rerank` (intent prompts), `source_compare` (new), `source_query_rewrite` (unchanged). The interactive routes are recommended on the fast route (D6).
- **Spend:** T6's caps per call; compare is one call capped by `source_service.compare_max_cost_usd` (default $0.05 metered); the daily cap.
- **Successor:** none. Retrieval is context (T6's ruling, `config/schema.py:1769`).
  - For `remediation_passages`, the S3 agent confirms with the reviewer that changing which passage the repair overlay shows is context, not serving.
  - If they rule otherwise, it takes the next free `mvp-0.N` with parity under the switch.
- **Gates:** G2, G3, G11, G12, G13, G14, G21.
- **Tests:**
  - `test_find_sources_intents.py`: lists, verdicts, the positive role filter, `cold_attempt` empty, `authoring` not accepted as a policy;
  - `test_find_sources_reader_contract.py`: the consumer-contract calls of §9.1 (G21);
  - `test_remediate_correction_refs.py`: source ids as a filter, locators resolved, missing sources reported;
  - `test_alternative_excludes_shown.py`;
  - `test_compare_sources.py`: quote verification, dropped lines, no consensus field, no source cap with the prompt bound and "also discussed in"; a source whose best hit ranks below the first page is still compared or listed;
  - `test_compare_sources_policy.py`: a pinned solution, a pinned item-linked passage and an answer-overlapping pin are dropped in a practice context and listed with reasons; a cold-context call is refused; a `policy` argument that differs from the caller's is refused; a pinned solution in a reading context is compared and its exposure recorded;
  - `test_tutor_intent_provider.py`;
  - `test_prescription_passages.py`: ranked, fallback, switch parity.

---

## 10. S4 — The typed tool interface; the tutor uses it now

### 10.1 The registry

`instructional/tools.py` declares five tools, each with a strict pydantic argument model (`extra="forbid"`). Each publishes its JSON schema, as `FIND_PRACTICE_TOOL` does (`practice_index/tool.py:36`).

| Tool | Arguments (all typed; no policy field) | Model call |
|---|---|---|
| `find_practice` | `query`, `intent`, `facet_ids`, `learning_object_ids`, `target_hypotheses`, `kinds`, `unattempted_only`, `max_estimated_minutes`, `reason` | Phase 5b's rerank; S2's screens |
| `find_sources` | `query`, `intent`, `facet_ids`, `target_hypotheses`, `roles`, `reason` | Verification |
| `compare_sources` | `query`, `facet_ids`, `requested_perspectives`, `reason` | One comparison |
| `find_facets` (router §15.3's `facet_lookup`) | `query` | **None.** BM25 and vector shortlist over facet dossiers and labels (`rank_dossier`'s facet stage, `practice_index/retrieval.py:383`), labelled a shortlist. The caller's model decides |
| `practice_availability` (the dialogue's two-stage interface, L1199–1203) | `facet_ids`, `intents` | **None.** Recall plus admission only: per intent, the number of admissible candidates, their expected minutes and their kinds. The cheap discovery pass a router needs before choosing a block |

The dispatcher `run_tool(name, arguments, *, caller)`:
1. derives the policy from the caller (§5.2);
2. validates the arguments and drops unknown ids, recording what it dropped;
3. refuses everything during a cold administration;
4. runs the operation under that caller context (`compare_sources` and `find_sources` receive it, so pins and arguments are filtered by the same policy, §9.4) and filters the result for a model reader (§5.3);
5. writes the `source_tool_calls` row and a `judgment_ledger` row for the model's request (task `source_tool_request`, judge `llm`, verdict = the tool name, rationale = the `reason`).

### 10.2 Protocol: tool requests as structured output

No provider path here supports native tool calling (§3.2 item 7), so a request is a field of the model's structured output. The wire models live in `ai/tool_requests.py`. They are plain `WireModel`s with no behaviour, so the tutor and the router can import them without importing the service: a discriminated union on `tool`, with every field required, as strict schemas need.

The executing side is always code under the caller's context. A model never sees another model's raw request, and no loop runs inside a provider. So no turn cap is needed: each request is one bounded operation.

### 10.3 The tutor's use

- **`TutorAnswer` gains `tool_requests: list[ToolRequest]`** (`tutor/ai_contracts.py:84`; prompt version bumped from `:126`). The tutor may ask for practice on what the learner is struggling with, a passage for an intent, or a comparison, each with a one-line `reason`. The prompt says that tool results go to the learner, not back to the tutor, and that no request may carry or hint at the current item's answer.
- **Validation, before anything is shown.**
  - Each `reason` and `query` passes `answer_leaks_expected` against the current item (`tutor/tutor_qa.py:816`), the same check the answer passes (§3.2 item 14). A request that leaks is dropped and the drop is recorded.
  - Unknown facet, LO and hypothesis ids are dropped.
  - No count cap applies. Money and the time box bound execution.
- **Execution.** The `ask_tutor_question` response carries the validated requests with their `source_tool_calls` ids. The frontend calls `run_source_tool(tool_call_id)`, which re-reads the stored caller context: the policy cannot change between the answer and the run.
  - `find_practice` and `find_sources` run when the offer is shown (eager; cheap and time-boxed).
  - `compare_sources` runs when tapped (lazy; one heavier call). (D5)
- **Offers.** In `AskOverlay` (practice, feedback and library contexts):
  - "Practice this: *reason*" → proposals (§6.3);
  - "From your books: *reason*" → verbatim passages, labelled source-authored, with "open in source";
  - "How do your books treat this?" → comparison.

  S4's `find_practice` request replaces S0's deterministic `practice_request` whenever the tutor wrote one.
- **The third explanation mode** (personalized bridging, L1254–1272). On any passage offer, "Explain this with my work" asks a follow-up tutor question in the same thread. It pins the chosen spans through a pinned-span provider passed as `source_span_provider`, which `ask_question` already accepts (`tutor/tutor_qa.py:311`), and passes the learner's current draft as context. It is a normal tutor question: reveal-accounted and a `question_events` row.
- **The reader context** gets `tool_requests` from the backend too. Rendering them is the Reader spec's (SC11).

### 10.4 Receipts

**Migration 192: `source_tool_calls`** (RECEIPT; append-only, nothing updated in place). A validated request writes a `request` row; running it writes a `run` row that names the request as its `parent_id`.
- `id`, `parent_id`, `row_kind` (`request` | `run`), `created_at`, `caller_kind` (`tutor` | `router` | `agent`), `caller_ref`;
- `context_json` (the stored caller context the policy was derived from), `policy`;
- `tool`, `arguments_json` (as validated), `dropped_json`, `ledger_id`;
- `status` (`requested` | `refused` on a request row; `ran` | `failed` on a run row), `result_ref` (a proposal id, a find-sources manifest hash or a comparison id), `result_keys_json`, `source_versions_json`;
- `model`, `prompt_version`, `latency_ms`, `cost_json`.

### 10.5 External agents

`learnloop sources tools --json` prints every tool's schema. `learnloop sources tool <name> --args '<json>' [--dry-run] --vault …` runs one under caller kind `agent` and policy `reading`. `learnloop practice-index tool-spec` stays.

### 10.6 Router R2 wiring: deferred, with a new trigger (supersedes router §15.3's)

**The design, for when it fires:**
- The router's LLM request gains the same `tool_requests` field, limited to `practice_availability` and `find_facets` at the block-choice stage.
- Availability feeds the planner values of the block candidates.
- After the router chooses a block, the within-block selector calls `find_practice(intent=…)` (router §1: item selection stays with the selectors).
- Retrieved candidates join R1's logged candidate set, so propensities stay exact.
- The router's checks are system-initiated, so only a licensing verdict serves one (§8.3.3).
- SC3 holds: the router's model never sees an answer key.
- §15.3's other uses map onto the same tools:
  - **probe choice** is `find_practice(intent="discriminate")` (S2);
  - **explanation blocks** are `find_sources(intent="remediate" | "explain")` under the block's item-bound policy (S3);
  - **reading blocks ranked against open gaps** call `find_sources(intent="explain")` over the current source's unread sections, with `target_hypotheses` from the card. That ranking changes what DL1's reading block serves, so it ships with R2's own successor;
  - **"when nothing fits"** is S2b's order: source exercises first, then PF generation.

**Trigger:** router R2 is merged and live (`router.enabled`, any mode other than the legacy queue), and S4 has merged.

**Why it supersedes §15.3's trigger**, which was "after R2 is live and T6's re-evaluation (2026-10-12, stronger model) settles hybrid vs dense":
- the hybrid-versus-dense question (T6 review §9 question 1) concerns which lists `search_spans` fuses, which can change behind these tools without changing how a router calls them;
- §15.3's own first step, the tutor's "Practice this", is S0 and S4 here.

### 10.7 Data, routes, spend, successor, gates, tests

- **Migration 192** (above).
- **Routes:** `tutor_qa` (unchanged route, new prompt version), plus whatever each tool's operation uses.
- **Spend:** per tool as its operation; the daily cap.
- **Successor:** none. Offers are proposals and passages (context), served or shown only through SC1's paths.
- **Kill switch:** `source_service.tutor_tools` (off: `tool_requests` dropped from the prompt and the contract, so the tutor is byte-identical to S0's).
- **Gates:** G1, G2, G3, G13, G14, G16.
- **Tests:**
  - `test_tool_registry.py`: schemas, extra fields refused, policy not settable;
  - `test_tool_dispatch_policy.py`: every caller and policy pair, cold refusal, item mismatch refusal;
  - `test_tool_results_withhold_answers.py`: a fake item's answer string never appears;
  - `test_tutor_tool_requests.py`: leak check drops, eager and lazy execution, receipts, ledger rows;
  - `test_pinned_span_bridge.py`;
  - `test_tools_cli.py`;
  - `test_practice_availability.py`: no model call.

---

## 11. S5 — Retrieval in the evidence loop (reports only)

### 11.1 The intervention record (s, a, r, y; L1386–1400)

**Migration 193: `retrieval_interventions`** (RAW_LEDGER: append-only facts captured when something reaches the learner, and inputs to later computation).

**When a row is written:** only when a retrieved asset is *shown or served*, never when it is merely retrieved:
- a passage offer opened or a tutor answer citing retrieved spans;
- a remediation passage delivered;
- a comparison shown;
- a proposal picked;
- an imported source exercise served;
- a need fulfilled from the sources and then served.

**Fields:**
- `id`, `created_at`, `kind` (`source_passage` | `source_exercise` | `practice_pick` | `comparison` | `remediation_passage`);
- `caller_kind`, `caller_ref`, `intent`, `policy`;
- `tool_call_id`, `proposal_id`, `question_event_id`, `remediation_episode_id`, `router_decision_id`: whichever apply. The router id is filled when R1's `learner_pick` row exists for the pick;
- `assets_json`: span keys with revision ids, item ids, family ids, canonical exercises;
- `targets_json`: facets, hypothesis refs;
- `state_ref_json`: references, not copies. The hypothesis set id and a posterior hash, the facet-uncertainty hashes and the named gap ids;
- `valuation_json`: the predicted EIG and EVSI, the likelihood regime and basis, and the predicted outcome distribution P(E) for a valued check;
- `exposure_event_ids_json`, `impression_ids_json` (what was displayed before the pick, §6.5), and the reading-exposure label (§5.4);
- `eligibility_json`: the independence verdict at valuation time and again at serving time (§5.4);
- `seconds_since_related_exposure`: router §15.2's covariate;
- `session_id`, `attempt_id`, `algorithm_version`;
- `design`, `seed`, `propensity`: reserved and null in v1; randomization is deferred (§19).

### 11.2 The outcome join

**`retrieval_intervention_outcomes`** (DERIVED; exactly one replayer in `substrate/rebuild_orchestrator.py`; zero model calls; reads persisted rows only). Per intervention:
- **`R_next`:** the next attempt on the targeted facets within the session or day, with its grade and whether it was assisted;
- **`R_cold`:** the next independent attempt on them, classified with the decision-value spec's outcome states (§4.3: `cold_success`, `cold_failure`, `right_censored_expired`, `learner_declined`, `unmeasurable_*`, `contaminated_or_assisted`, `missing_duration`). Pending outcomes stay right-censored, never failures;
- **hypothesis movement:** the posterior on the target hypotheses before and after the next observation, from replayed state;
- **observed outcome bucket** for a valued check, beside its predicted P(E);
- **learner signals:** usage taps and their text, "doesn't connect" text, undo.

### 11.3 The report

`learnloop sources outcomes [--json] --vault …`:
- outcomes by intent, role class, source, caller and kind;
- `R_next`, `R_cold` with intervals and effective sample sizes;
- key-label rates (S1's `book_solution`, `checked`, `panel_agrees`, `panel_agrees_unconfirmed`, `checking`, `model_answer`, `disputed`, and `changed_since_check` after edits) and the attempts the certification gate made ineligible;
- the exposure rule's exclusions, including those from impressions and the serve-time recheck;
- the valuation's verdicts by regime, with abstention and exclusion reasons.

Labelled throughout: "Associations, not causes: improvement after an explanation doesn't show the explanation caused it (L1402)". Nothing reads the report to serve.

### 11.4 Calibrating value of information from these records

This answers the owner's question of 2026-10-12: can EVSI be calibrated instead of running on unchecked assumptions? Yes, because each of its inputs can be checked against what happens. S5 records what the checks need. The `evsi/calibration` track owns the fitting and any change to the constants, as a successor.

1. **The predicted outcome distribution.** EIG and EVSI are only as good as P(E) = Σ_H P(H)·P(E | H). For every valued check, S5 stores the predicted P(E), its likelihood regime and the observed bucket. Log loss and a reliability table, prequential by date and per regime, show whether the likelihoods (authored profiles, discrimination rows, the IRT-based facet conditionals, the rubric bridge, screened exercises' signatures) are calibrated. This is what can change what a regime may license (§8.3.3): the track may promote `item_point` tables, or a screen's signatures composed with the grader channel, to a licensing regime, or fill the reserved `arm_a_calibrated`. Each promotion is its own versioned input with its own rollback (decision-value invariant 12) and a successor.
2. **Information actually gained.** The predicted EIG against the realized posterior entropy drop on the target hypotheses.
3. **Decisions actually changed.** EVSI predicts that an observation changes the chosen action. S5 records the action before and after the observation (from the episode's or need's receipts), and whether it flipped.
4. **Minutes.** The predicted minutes against the attempt's actual duration, which the loss table and the stop rule both use.
5. **The value of a nat.** `VALUE_PER_NAT_MINUTES` (60, heuristic) can be fitted as the minutes the downstream decision saved per nat resolved: the realized loss difference between the action taken after the check and the action the prior would have taken, where `R_cold` later says which was right.

   λ = 1 is the numeraire and stays fixed. The burden is the learner's: S5 records skips and "not now" on checks, the revealed cost of being asked.
6. **Reading exposure.** S5 records the `related` worked-example label beside each outcome, so the track can measure whether such reading raises success without the capability, and replace §5.4's dominance rule with a measured adjustment.

Until the calibration track replaces them, the heuristic constants are used and every valuation says so ("LearnLoop's estimate; its scale is not yet calibrated").

### 11.5 Successor, kill switch, gates, tests

- **Successor:** none. Reports only; nothing reads these tables to serve.
- **Kill switch:** `source_service.interventions` (off: no rows written; the report says so).
- **Gates:** G13 (one replayer, deterministic rebuild, zero calls), G14.
- **Tests:**
  - `test_retrieval_interventions_write_points.py`: every kind, nothing written on retrieval alone, impressions and serve-time verdicts referenced;
  - `test_intervention_outcomes_replayer.py`: rebuild equality, censoring, outcome states;
  - `test_sources_outcomes_report.py`;
  - `test_valuation_calibration_fields.py`.

---

## 12. Coverage of the dialogue

Rows 86–115 are the coverage audit's numbering for round 3. "Built" means built by a phase here.

| Audit row | Brainstorm lines | Idea | Disposition here |
|---|---|---|---|
| 86 | 1088 | The router's LLM queries the sources for practice and probes | **Built** as the tool interface (S4) and its operations (S0–S3). **Deferred:** the router as caller (§10.6, new trigger) |
| 87 | 1088 | The tutor serves explanations from the sources from natural-language queries | **Built:** the tutor's `tool_requests` (§10.3) and intent-aware grounding (§9.5) |
| 88 | 1092–1109 | Retrieval for a purpose: a discriminating exercise, a worked example in the learner's approach, a prerequisite passage, an alternative explanation, a figure for interaction, an integrative problem | **Built:** discriminating (S2), worked example (`worked_example` with `learner_work_md`), alternative, integrative (`facet_match = all`). **Built** through the shared contract: prerequisite passages through `expand=["prerequisites"]` (the Reader's LO-graph expansion, §9.1) and RW4e's `prerequisite` role once proposed. **Narrowed:** figures through `roles=["figure","equation"]` for RW5's candidates, with tutor-initiated figures deferred |
| 89 | 1111–1121 | Three operations on a shared substrate: `find_sources`, `find_practice`, `find_examples` | **Built** as four operations. **Narrowed:** `find_examples` is `find_sources(intent="worked_example")`, because one function shares the scope, contamination and verification. A separate one would duplicate all three |
| 90 | 1115–1119 | Consumers: Reader, tutor, router, practice selector, diagnostic controller, workbench | **Built:** tutor (S4), practice selection through needs (S2b) and the plan (S0), the diagnostic side through valuation (S2). **Elsewhere:** Reader and workbench (Reader spec). **Deferred:** router (§10.6) |
| 91 | 1131–1161 | Don't eliminate cards; change what they represent | **Built:** family attachment and `canonical_exercise` (§7.4) |
| 92 | 1163–1165 | Retrieval first; generate on demand | **Built:** S2b for needs; unfamilied exercises become PF-b parents (§7.4) |
| 93 | 1167–1169 | A textbook problem needs a competency mapping, a checked answer and exposure checks | **Built:** import's facet mapping with post-import validation (§8.1), the verifier ladder (§7.3) with certification following the key (§7.3a), the exposure rule (§5.4) |
| 94 | 1171–1197, 1364 | Selection separate from retrieval; the router's model never sees a key | **Built:** SC1, SC3, §5.3 |
| 95 | 1199–1203 | A cheap availability pass before the router chooses | **Built:** `practice_availability` (§10.1). Consumed at R2 |
| 96 | 1207–1240 | Natural-language queries with typed, machine-enforced constraints | **Built:** §8.1, enforced on both arms: provisional, quote-verified metadata for raw exercises, unknown values failing a set filter, and validation after import. `answer_visibility` is the caller's policy, not an argument (SC2) |
| 97 | 1242–1246 | A worked example in the learner's own route | **Built:** `worked_example` with `follows_learner_route` (§9.2). The workbench's step history is the Reader's (RW2b) |
| 98 | 1248–1272 | Three explanation modes | **Built:** verbatim passages (mode 1), the grounded tutor (mode 2), "Explain this with my work" (mode 3, §10.3) |
| 99 | 1282 | Cited passages, version identity and the source/AI distinction in the API | **Built:** SC5, §5.5 |
| 100 | 1286–1307 | Index instructional roles, several per passage, with confidence | **Elsewhere:** the Reader's RW4e builds the roles (several per passage, with confidence and provenance, from judgments already being made plus an owner-run batch labeller). **Built here:** `roles` matches ingest's hints and RW4e's proposals as a positive filter, and the intents read the proposals as ranked lists (§9.1, §9.2). Exclusions stay with ingest's hints |
| 101 | 1309–1322 | Misconception-conditioned retrieval: discrimination and remediation | **Built:** S2 (`discriminate`), S3 (`remediate`), §9.3 |
| 102 | 1326 | Index source-authored contrasts | **Built:** the `contrasts` verdict ranks such passages first for `remediate`, which also reads RW4e's `contrast` and `counterexample` proposals (§9.2). **Elsewhere:** the proposals themselves (Reader RW4e) |
| 103 | 1328–1342 | Syntopic retrieval as a first-class operation | **Built:** `compare_sources` (§9.4), callable by the tutor (S4) and the Reader, every source in scope considered. **Elsewhere:** keeping a comparison as source-object proposals is the Reader's RW4d, from the stored comparison |
| 104 | 1344–1356 | Source-conditioned interactive explanations | **Narrowed:** role-filtered retrieval of equations and figures for RW5. **Deferred:** the tutor offering "make this explorable" (§19; needs RW5) |
| 105 | 1358–1374 | Context-dependent retrieval permissions | **Built:** §5.1: the four learner-facing policies as the Reader restored them (a narrow `post_attempt` that opens the item's solution only after its attempt window closes, recording a reveal), and `authoring` internal to S1's verifier |
| 106 | 1376 | A textbook exercise is a poor cold test after an equivalent worked example | **Built:** §5.4 rule 4 |
| 107 | 1378–1380 | Keep generated variants and exposure machinery; a retrieval receipt | **Built:** §5.5, §10.4, and impressions of displayed proposals (§6.5) |
| 108 | 1382–1406 | Retrieval in the evidence loop; causal claims need randomization | **Built:** S5 (reports). **Deferred:** randomization and learned preferences (§19) |
| 109 | 1414 | Source-anchored exercise and worked-example records in the index | **Built** for exercises (the arm, §7.1). **Narrowed** for worked examples, which are passages, not practice (§7.1) |
| 110 | 1415 | `find_practice` searches textbook exercises | **Built:** S1 |
| 111 | 1416 | `find_explanations` with intent, facet targets and citations | **Built:** `find_sources` with intents and `facet_ids` |
| 112 | 1417 | Connect retrieval results to the workbench's step history | **Elsewhere:** Reader RW2b. `learner_work_md` is the backend's input for it |
| 113 | 1418–1419 | Comparison and misconception retrieval; evaluate against delayed independent performance | **Built:** S3, S2, S5's `R_cold` |
| 114 | 1421–1423 | BM25, hybrid and rerank as separate conditions; retrieval quality and instructional effect tested separately | **Built:** §17. Retrieval quality on the T6 and Phase 5b harnesses; instructional effect in S5 |
| 115 | 1431–1461 | The refined proposal: an instructional substrate | **Built:** this spec, with the deferrals in §19 |

**Rounds 1–2, retrieval parts:**

| Brainstorm lines | Idea | Disposition |
|---|---|---|
| 242–262 | Syntopic reading that keeps each source's contribution; preserve differences | **Built:** `compare_sources` (§9.4) |
| 337–380 | Hybrid, source-aware retrieval in stages: exact context, hybrid, learning context, rerank, decision | **Elsewhere:** T6 (built). This spec adds the learning-context and intent stages |
| 381–399 | Candidate models: Qwen3 embedding, Qwen3 reranker, ColQwen, Qwen3-VL, Marker | **Elsewhere:** the embedding model is `qwen3-embedding-8b` via OpenRouter (owner decision); Marker is ingest. **Narrowed:** no cross-encoder reranker, because T6 uses an LLM listwise judge (classic cross-encoders hurt on reasoning-heavy queries, BRIGHT, `spec_embedding_consumers_v1.md` §9). **Deferred:** visual retrieval (B4 found page images worse; §19) |
| 401–427 | Index relationships, not only text; keep source, learner and policy layers apart; abstain when evidence is inadequate | **Built:** the layers stay apart (SC1, SC5); "not found in your library", verification's "none" and the valuation's typed abstentions are first-class outcomes (§8.3.4, §9.4) |
| 427 | Symbolic and numerical checks, not only an LLM judge | **Built:** the verifier ladder (§7.3) |
| 820–877 | Search-first library answers organized by role; a claim comparison verified before it enters a trusted graph; personalization that can be turned off | **Built:** role grouping data in hits, `personalized` (§9.2), quote-verified comparison lines. The UI is the Reader's. **Elsewhere:** kept comparisons enter P3's source-object layer as proposals through the Reader's RW4d, and nothing becomes trusted without P3's review path; the full-library claim index stays deferred in the Reader spec (its §17) |

---

## 13. Persistence summary

| Migration (built from 184 in build order §15; renumbered 187-195 at the merge onto main) | Phase | Table or change | Role |
|---|---|---|---|
| 187 | S0 | `practice_index_proposals` + `caller`, `caller_ref`, `intent`; `instructional_impressions` | RECEIPT (unchanged); RAW_LEDGER |
| 188 | S1 | `source_exercise_imports`; `reference_key_checks`; `practice_attempts.reference_status` (unless DL3 added it) | WORKFLOW; RAW_LEDGER; the attempts table's role is unchanged |
| 189 | S3 | `source_comparisons` | WORKFLOW |
| 190 | S2a | `practice_index_proposals.valuation_json`, `provisional_json` | unchanged |
| 191 | S2b | `source_exercise_imports.need_id` | unchanged |
| 192 | S4 | `source_tool_calls` | RECEIPT |
| 193 | S5 | `retrieval_interventions`; `retrieval_intervention_outcomes` | RAW_LEDGER; DERIVED (one replayer) |
| 194 | SC10 | `source_service_spend` (the daily cap's shared reservations; Codex re-review F2) | WORKFLOW |
| 195 | SC10 | `source_service_spend` rebuilt for the spend accounting (`legacy`, `lease_expires_at`, `resolved_by`, `released`); `model_call_receipts` indexes | WORKFLOW (unchanged) |

**Vault model:** `PracticeItem.canonical_exercise` (S1), omitted when null.

**Every migration** (G18, in every phase that adds one):
- classifies its tables in `db/table_roles.py`; the DERIVED one gets exactly one replayer;
- upgrades and renames `fixtures/migration_head_<N>/` in rollback mode, updating its README and the five hard-coded paths;
- reruns `db_generate_reference.py` and `db_validate_reference.py` (CLAUDE.md).

**Every new config key** moves the defaults fingerprint (`config/template.py:831`). Content-only phases recompute the latest entry with the note "no scoring, scheduling, projection or serving change". S1 (for the certification gate) and S2b record their own entries under their successor tags.

**Config, `[source_service]`:**
- `enabled` (master);
- per phase: `tutor_offers`, `exercise_arm`, `exercise_verification`, `unverified_imports`, `family_attachment`, `discriminating_search`, `source_first_needs`, `tutor_intents`, `remediation_passages`, `compare`, `tutor_tools`, `interventions`;
- time and prompt bounds: `verify_timeout_seconds` (90), `compare_max_prompt_tokens` (24,000);
- money: `import_max_cost_usd` (0.25), `compare_max_cost_usd` (0.05), `max_daily_cost_usd` (1.00), `llm_price_per_million` (unset: metered routes are skipped).

All are on by default except as D-decisions say. No key turns off the certification gate (§7.3a).

**Routes** added to `AITask` (`ai/routing.py:22`): `source_solution_match` (S1), `source_compare` (S3), `exercise_discrimination` and `worked_example_equivalence` (S2a). Each gets a routing default and is skipped and labelled on a metered route without a price.

---

## 14. Algorithm successors and kill switches

| Phase | Changes | Successor | Kill switch (off restores) |
|---|---|---|---|
| S0 | Callers and the pick link | None | `tutor_offers` (no request on answers) |
| S1 | Exercise arm, import, ladder, families | None (proposals; learner-authority and owner-run content) | `exercise_arm`, `exercise_verification`, `unverified_imports`, `family_attachment` (Phase 5b's `find_practice`; today's import) |
| **S1** (gate) | Attempts on unverified imported keys don't certify (§7.3a) | **Next free `mvp-0.N`**, or an extension of DL3's `capture_reference_v1` gate under its own tag | **None that re-enables certification (C3).** Below the tag the gate never runs; with no `unverified` attempts, projections equal the predecessor's |
| S2a | Intents and valuation in `find_practice` | None (proposals) | `discriminating_search` |
| **S2b** | Needs fulfilled from the sources before generation | **Next free `mvp-0.N`** | `source_first_needs` (the generation lane byte-identical) |
| S3 | `find_sources`, `compare_sources`, tutor intents, remediation passages | None (T6's ruling; the reviewer confirms for remediation passages, with the stated fallback) | `tutor_intents`, `remediation_passages`, `compare` |
| S4 | Tool interface and tutor offers | None | `tutor_tools` |
| S5 | Records and report | None | `interventions` |

`source_service.enabled = false` turns every phase off at once: T6, `find_practice`, the tutor and remediation behave exactly as merged (G14). The one exception is the certification gate, which C3 keeps on for every vault at or above its tag.

---

## 15. Build order, sizes and dependencies

| Order | Phase | Builds | Needs (`main` unless noted) | Size |
|---|---|---|---|---|
| 1 | **S0** | `practice_request`, pick link, proposal columns, impressions and their RPC, `AskOverlay` strip, the `instructional` package, its import-linter contract and the `db/stores/source_service.py` store | — | **S** |
| 2 | **S1** | Positive role filter, `list_depth`, `list_ends` and `fused_keys` in `search_spans`, and a public `effective_hint`; the injected exercise arm; the import split; `content/authoring/source_exercise_import.py` (adapter, ladder, write, attach) and its job; `ops/pf_verify.py` with separated agreement and symbolic status; the certification gate and `reference_status` (successor), with `reference_content_hash`, `reference_key_checks` and re-checks after edits; `attach_to_family`; `canonical_exercise`; harvest and verify | S0 | **L** |
| 3 | **S3** | `instructional/policy.py` (§5); `find_sources` intents, correction refs, `compare_sources`, tutor intent provider, remediation passages | S1's role filter (S3 can start in parallel once it lands) | **M** |
| 4 | **S2a** | Constraints with provisional metadata and validation, `open_hypotheses`, the valuation input (one problem per hypothesis space) and its adapters, `value_candidates` (injected as `valuer`) with regimes, `robust_composition.evaluate_selection_credible_sets` and `evaluate_selection`'s shape guard, verdict translation and resumable paging (per-list depths, the dossier's facet depth), the public `misconception_discrimination`, exercise discrimination screen, `independent_check_eligibility` (rules 1–5, the reading-exposure adjustment, the serve-time recheck) | S1 | **M–L** |
| 5 | **S2b** | Source-first need fulfilment (successor) | S2a | **S–M** |
| 6 | **S4** | Registry, wire models, dispatcher, receipts, tutor `tool_requests`, offers, pinned-span bridge, CLI | S0; S2a and S3 for their tools (tools register as their phases land) | **M** |
| 7 | **S5** | Interventions, outcomes replayer, report, calibration fields | S0–S4 write points | **M** |

S0 ships a learner benefit on its own. S1 and S2a together deliver the owner's core ask: "LearnLoop serves textbook exercises as practice and as probes chosen to separate rival misconceptions". The Reader's RW4a and RW6b can consume each phase as it merges. None of these phases waits for R1, R2, learner-text gaps or DL2. Their adapters feature-detect.

---

## 16. Gates and tests

| # | Gate |
|---|---|
| G1 | **Tools never serve.** After any tool or operation runs, the attempts, evidence, mastery, FSRS, scheduler-state and plan-item tables are unchanged. A proposal reaches practice only through SC1's paths |
| G2 | **Policy from the caller.** No argument can widen a policy. Item-bound callers never receive exercise, solution, linked or answer-reproducing spans. `cold_attempt` returns nothing and refuses every tool. `authoring` is not a policy any caller can request: S1's verifier builds that scope itself, and nothing it retrieves reaches a learner-facing model. A `post_attempt` call opens the item's solution only after its attempt window has closed, and records a reveal. A request naming another item or attempt is refused |
| G3 | **Answers withheld from models.** Results returned to an LLM never contain a fake item's expected answer, rubric, hints, profile answers or solution text. Tutor `reason` and `query` strings pass the answer-leak check |
| G4 | **The exercise arm** returns only exercise regions in the teaching scope, never an imported exercise, never an assessment-lane span |
| G5 | **Import parity.** The Reader's import writes the same item as today (the split composes to today's output); it also records a `source_exercise_imports` row and, with verification on, queues the ladder (§7.3a). Stems stay verbatim. Items without `canonical_exercise` serialize byte-identically; `practice_item_hash` is unchanged |
| G6 | **Honest key labels.** `checked` appears only with a passing sympy check; `book_solution` only with a quote-verified, supported solution; `panel_agrees` only for a prose answer. A numeric or symbolic key whose symbolic check could not run is `panel_agrees_unconfirmed`, never `checked` or `panel_agrees`. Only verified keys (`book_solution`, `checked`, `panel_agrees`) qualify for the value intents and S2b. PF's own verification decisions are unchanged by the extraction (parity test) |
| G7 | **Families.** `attach_to_family` is append-only with undo and crash recovery. `apply_family` is unchanged. An LO mismatch is refused |
| G8 | **Valuation.** No model call; its only write is the idempotent channel snapshot. Identical inputs give identical receipts. Every candidate has a regime, normalized tables or a typed missing reason. Verdicts follow `rank_feasible` and `evaluate_selection` and are translated as decision-value §6.5 does; an abstention or exclusion never falls back to an entropy order, and a system-initiated check is licensed only by `pinned_channel` (or S2b's use of the chooser's gate). No count cap: a fixture where three candidates clear the stop returns three. Greedy conditional valuation drops a redundant second check. Each problem holds one hypothesis space; several spaces are separate problems, never a joint one, and a decision spanning spaces is refused. `evaluate_selection` sees only equal-shaped ensembles; mixed credible sets go to `evaluate_selection_credible_sets`, and a system-initiated selection compares only licensing candidates. Paging stops only on exhaustion (every admissible candidate offered, decided per list, never by `limit`), budget (with a resumable cursor) or the perfect-information bound |
| G9 | **Exposure rule.** A candidate whose span or solution was exposed, whose family was revealed, whose prompt was displayed in an earlier proposal, or that an `equivalent` worked-example verdict covers, is excluded from `discriminate`, `retention` and S2b, and kept for `practice`. A `related` verdict excludes it from `retention` only, changes no value and writes no attempt |
| G10 | **S2b successor parity.** With `source_first_needs` off, or below the tag, the generation lane and follow-ups are byte-identical on fixture copies; a shadow rebuild shows zero projection deltas |
| G11 | **Remediation.** `remediate` reads correction refs as specified. With `remediation_passages` off or verification unavailable, prescriptions are byte-identical to today's |
| G12 | **Comparison.** The policy comes from the caller; pins pass the same filters as discovered spans and never override an exclusion; a cold caller is refused. Every source in scope is considered, not only those on a first page. Every comparison line's quote is verified in its own passage; failing lines are dropped and listed. The schema has no consensus field. Uncompared and unverified sources are listed, not hidden |
| G13 | **Receipts and replay.** Every paid verdict has a `judgment_ledger` row and a model-call receipt. Every tool request from a model or an external agent has its request row and, once run, its run row in `source_tool_calls`. A rebuild makes zero model and embedding calls, and `retrieval_intervention_outcomes` rebuilds deterministically from one replayer |
| G14 | **Kill switches.** Each switch, and `source_service.enabled`, restores the previous behaviour exactly (fixture-copy parity). The one exception is the certification gate, which no switch turns off (C3, §7.3a) |
| G15 | **Spend.** Every batch command has `--dry-run` and honours its caps. Metered routes without a price are skipped and labelled. Codex receipts are `estimated_only` |
| G16 | **Mobile.** New RPCs (`record_proposal_impressions`, `import_source_exercise`, `get_source_exercise_import`, `run_source_tool`, `find_sources`, `compare_sources`) and the extended ones (`find_practice`, `record_practice_usage`, `plan_learner_pick`, `ask_tutor_question`) are pinned desktop-only in `tests/test_mobile_allowlist.py` |
| G17 | **Layering.** A new import-linter contract forbids the domain packages, `learnloop.practice_index` and `learnloop.source_retrieval` from importing `learnloop.instructional`, and forbids `learnloop.instructional` from importing `learnloop.daily_plan`. `uv run lint-imports --no-cache` passes, and so does `tests/test_architecture.py`: no private cross-package names, SQL writes only in registered stores, no new frozen-inventory edges |
| G18 | **Migrations.** Every new table is classified; the DERIVED one has exactly one replayer; the head fixture and references are regenerated |
| G19 | **Certification follows the key (C3).** An attempt on an imported exercise whose key is not verified records `reference_status = unverified`, updates FSRS and earns no certification credit; a verified key records `verified`. Verification is bound to the stem, key and rubric checked (`reference_content_hash`): an edit, or a check that finished on an older revision, leaves the current content unverified. Never retroactive. Historical Reader imports resolve as specified. Below the tag, and with no `unverified` attempts, projections equal the predecessor's (shadow rebuild of fixture copies with zero deltas). No switch re-enables certification |
| G20 | **Displayed is not unseen.** Rendered proposals write impressions; retrieved-only ones don't; `activity_exposure_events` is untouched. Independence is re-checked when a candidate is served as an independent check; a failure serves a learner's pick as labelled practice and refuses a system-initiated check |
| G21 | **One contract with the Reader.** The consumer-contract tests (§9.1) pass: the Reader's §7.2 parameters, defaults and policies, `expand`, `exclude_span_ids`, RW4e role filters, `post_attempt`, and RW6b's intent names |

Every phase also runs the full suite (`uv sync --extra dev --extra mobile`, then `uv run pytest -n auto`, with `TMPDIR` set to the worktree's `fixtures-local/tmp`), the durability lane where it adds a migration (`uv run pytest -m durability`), `lint-imports`, and the frontend checks when it touches the app (`npm run typecheck && npm test`).

---

## 17. Evaluation: retrieval quality and instructional effect, separately (L1421–1423)

- **Retrieval quality.** The existing harnesses, with LLM labels in two passes and agreement reported. Eval models are Claude Haiku 5.5 or GPT-6 Luna via OpenRouter, or the ChatGPT-plan route. Owner labels are optional.
  - **The exercise arm:** held-out requests over the owner's textbook copies (`linear_algebra`, `probability`) in the Phase 5b evaluation (`learnloop eval practice-index`, `cli/practice_index.py:286`). Recall@10 and nDCG@10 for items only against both kinds, on copies of the textbook vaults (the owner's live vaults are never evaluated in place).
  - **Intents:** a per-intent query set in the T6 harness (`learnloop embeddings compare --suite source_retrieval`, whose systems already include `keyword`, `meaning`, `hybrid` and `hybrid_rewrite`, `cli/embeddings.py:181`), with verification as one more condition, so BM25 alone, hybrid and verified retrieval stay separate conditions, as the dialogue asks.
  - **The verifier ladder:** on imported exercises whose book solution exists, the rate at which rungs 2, 2′ and 2″ agree with rung 1; per source, the disputed rate and the share left `panel_agrees_unconfirmed`.
- **Instructional effect.** S5's report: `R_next` and `R_cold` by intent and kind, and the calibration fields (§11.4). These are associations until randomization exists (§19).
- **Paid runs** happen only on backup-API copies under `fixtures-local/`. They run dry first, inside caps, with every call and its cost recorded in the phase's review file.

---

## 18. Decisions: recommended defaults (accepted unless the owner overrides at a checkpoint)

| # | Decision | Recommended default |
|---|---|---|
| D1 | Interactive import: check before showing? | Check inside a 90 s box. If the box runs out, serve the item labelled "being checked" and finish the check in the background; a later disagreement marks the key `disputed` |
| D2 | Should unchecked or disputed keys still certify? | **No** (C3, an owner decision): they schedule and teach, labelled, and never certify, through DL3's attempt-time gate, as S1's successor (§7.3a). Not retroactive |
| D3 | S2b: successor or content change? | Successor (§8.5) |
| D4 | Remediation passages in the repair overlay | Live behind `remediation_passages`, no successor (T6's ruling), confirmed by the S3 reviewer, with the stated fallback |
| D5 | Running the tutor's tool requests | Eager for `find_practice` and `find_sources`; lazy (on tap) for `compare_sources` |
| D6 | Routes | The fast route (ChatGPT-plan) for interactive judges (`practice_rerank`, `source_rerank`, `source_compare`); Codex for batch work (verification, harvest, screening); eval roles on Haiku 5.5 or GPT-6 Luna |
| D7 | Harvesting source exercises | An owner-run command with `--dry-run` and caps. Automatic background harvesting deferred (§19) |
| D8 | Router trigger | Supersede §15.3's: R2 live and S4 merged (§10.6) |
| D9 | Sources in a comparison | No source cap; a prompt-token bound, with the rest listed |
| D10 | Equivalent-worked-example rule | The listwise judge over exposed worked examples (§5.4), rather than exact-span exposure alone. `equivalent` excludes from both independent intents; `related` excludes from `retention`, and for `discriminate` is a label plus a dominance rule, with no invented discount |
| D11 | Personalization in `remediate` and `alternative` | On, with an off toggle for callers |
| D12 | Spend | `max_daily_cost_usd` $1.00 metered across the track; Codex `estimated_only` |
| D13 | Where the canonical exercise lives | A typed optional field on `PracticeItem`, rather than a provenance convention, so PF variants can carry `variant_of` |
| D14 | Worked examples as practice candidates | No: they are passages (§7.1) |
| D15 | Reader imports made before S1 | Under the gate from the successor's tag on: `model_answer` until `learnloop sources exercises verify` checks them; earlier attempts unchanged. The alternative is to grandfather them, which would leave the same exercise certifying differently by import date |
| D16 | Learner-initiated results with candidates the valuation can't value | Shown, in their own groups ("at most …" for upper bounds; unvalued with the reason), and the learner decides. System-initiated checks never use them (§8.3.3) |
| D17 | Impressions | Recorded for every rendered proposal, in their own table, never in `activity_exposure_events`; an impression from an earlier proposal excludes the candidate from independent intents within the cold retrieval delay |
| D18 | A request whose target hypotheses come from several producers (two misconceptions and an unresolved cause) | Separate problems, one per hypothesis space, each valued and verdicted on its own; no joint prior is assumed and no value is summed (§8.3.1). The alternative, a joint model of co-occurring beliefs and causes, needs data no producer holds |
| D19 | S2b when the valuation says `stop` | End diagnostic fulfilment: nothing imported or generated, the need `stale` with its reason, the causal path's live repair untouched and any disagreement logged (§8.5). Generation is the stronger-instrument path for `abstain` and for no evaluable candidate only |
| D20 | A verified key that is later edited | Unverified until a check of the new stem, key and rubric passes, re-checked automatically when `exercise_verification` is on; earlier attempts keep their recorded status (§7.3a) |

---

## 19. Deferred, with triggers

| Deferred | Revisit when |
|---|---|
| **Router R2 wiring** and the router choosing material with the action (L1406) | R2 is merged and live, and S4 has merged (§10.6). Joint choice: once R3's replay shows block-level gains (router §13) |
| **This track's own role labeller** (no longer needed while the Reader's RW4e, restored at `df23187e`, builds role proposals with confidence and an owner-run batch labeller) | The Reader cuts RW4e again, and S3's report shows that `remediate` or `alternative` verification returns "none" for most targets |
| **A licensing likelihood regime beyond `pinned_channel`**: promoting `item_point` tables or screened exercises' signatures (composed with the grader channel), or filling the reserved `arm_a_calibrated`, so their verdicts can license system-initiated checks (§8.3.3) | The `evsi/calibration` track's prequential log loss and reliability on S5's records show the regime calibrated (§11.4 item 1). Each promotion is its own versioned input and a successor |
| **A measured reading-exposure adjustment** replacing §5.4's dominance rule | S5 holds enough `related`-labelled outcomes for the calibration track to estimate the effect (§11.4 item 6) |
| **Page-image retrieval** | A multimodal labeller rematch (T6 review §9 question 4) shows page images beat Marker text on the owner's PDFs; B4 found the opposite (`page_image_default = false`) |
| **Source exercises as formal probe instruments** (compiled conditionals, probe episodes) | S5's calibration fields show that the authored-profile predictions of served source exercises are calibrated (§11.4 item 1) |
| **Randomized choice between equally valued interventions** (a registered randomization design, the cue-holdout pattern) and a **learned per-learner intervention preference** (L1404) | S5's report shows comparable interventions served for the same facet class with enough overlap to estimate a difference, and the owner reads it. The learned preference also needs R3's replay infrastructure |
| **Tutor-initiated explorable figures** (L1344–1356) | Reader RW5 has merged |
| **Automatic background harvesting** (bulk import without a pick, a need or the owner's command) | Usage signals show learners pick source exercises from proposals often. RW6b's follow-ups from textbook exercises are not this: they go through `find_practice` and an import per chosen exercise |
| **An MCP or OS-level instructional service** | The Reader spec's trigger for its learning service |
| **Cross-LO candidates in the follow-up chooser** | S5 shows S2b's source-first fulfilment closes needs and its checks resolve hypotheses |
| **Source-first fulfilment on the tutor's promotion path** (`tutor/promotions.py:741`, through an injected callable) | S2b has merged and its report shows source exercises fulfilling needs on the two adapter paths |
| **Cross-learner, data-driven hints** | Not applicable at n=1 (dropped, as the coverage audit recommends) |

---

## 20. Cross-spec notes (record when each phase merges)

- **Reader workbench spec** (checked against `df23187e`).
  - **One `find_sources` contract** (§9.1): the Reader's §7.2 signature, defaults and four policies (with its restored `post_attempt`) are the base; this spec adds `intent`, `target_hypotheses`, `learner_work_md`, `personalized` and `cursor`. `authoring` is not a `find_sources` policy in either spec. The consumer-contract tests (G21) pin the Reader's calls.
  - **One `compare_sources` contract** (§9.4): the Reader's §7.8 signature plus a server-derived `caller`; its `policy` argument becomes an assertion. Requests to the Reader revision: use the five relation labels as both specs now do; store the comparison once in `source_comparisons` and keep its id on the `library_asks` row; make "Keep this comparison" (RW4d) read the stored comparison; use the route `source_compare` for the comparison prompt; and drop `compare_sources.max_sources` in favour of the prompt-token bound, since every source in scope is now considered (D9).
  - **`PracticeConstraints`:** the Reader's field names are the shared ones (`unattempted_only`, `exclude_family_ids`, `max_estimated_minutes`), and its intent names are accepted as aliases (§8.1). Its `integrative` request is `facet_match = all`.
  - **RW6b's valuation** is `instructional/valuation.py:value_candidates` (§8.3), built once, by whichever phase lands first. Requests to the Reader revision, from the Codex review of this spec:
    - RW6b §9.3 step 3's "an `abstain` verdict falls back to the EIG-per-minute order" contradicts decision-value invariants 4–6; it becomes §8.3.4's translation, with no fallback;
    - RW6b's dated checks are system-initiated, so they are created only from a licensing regime (§8.3.3): today, retention checks and compiled probe instruments (`pinned_channel`). Checks valued under `item_point` or `arm_b_noiseless` can be shown, not dated;
    - "shown by reading" uses §5.4's reading-exposure rule, not `familiarity_discount`, which reads attempts only. The Reader's G35 keeps `familiarity_discount` for attempt familiarity;
    - DL2's "Check once" re-checks independence when it serves a dated check (§5.4);
    - an open question is one valuation problem (§8.3.1): a card that mixes, say, a misconception with an unresolved cause shows one result per hypothesis space, never a merged value.
  - RW6b's open questions read the same `open_hypotheses` adapter.
  - **Impressions:** every Reader surface that renders practice proposals (RW4a, RW3's "Check me", RW1c's offers, RW4b) calls `record_proposal_impressions` (§6.5).
  - RW4b's fallback becomes S1's arm. Any RW4c the Reader revision adds is UI over S1 and S2.
  - The Reader spec's note that §15.3's tool is now built here points to §10.6.
- **The four count caps** (the Reader spec's §18 records the owner's decision of 2026-10-12 to lift `probe.episode.session_qualifying_observation_cap`, `scheduler.followup.max_interventions_per_lo_per_session`, `teach_back.session_cap` and `plan.project_probes_max_per_day` on value of information, as a separate serving stage). That stage reuses this valuation adapter, so it inherits §8.3.1–§8.3.4: one problem per hypothesis space, an observation, follow-up, teach-back or project probe is added only on a licensing verdict, an abstention ends the run of checks rather than falling back to EIG order, and each cap's kill switch restores the old count.
- **Router spec §15.3.** A note at its trigger points here: the tool interface is built by S4, and the trigger is superseded (§10.6).
- **Embedding consumers §5.9.** Its consumer list gains the tutor (S0, S4), learner picks (S0), needs (S2b) and the source-exercise arm (S1). Its bar (dossiers must beat direct item search) is unchanged.
- **Daily loop.** DL3's "Practice on…" box is S0's RPC with `caller = plan`, and it records impressions. DL2's dated branch reads `due_hint` for RW6b's checks (Reader spec request, unchanged) and re-checks independence when it serves one (§5.4). **DL3's certification gate** (§4.4 there) is shared: whichever of DL3 and S1 merges first builds `practice_attempts.reference_status` and the resolver input, and the other adds its status source (§7.3a). Request to DL3: bind `capture_processing.verification` to the content it checked, as §7.3a binds key checks with `reference_content_hash`, because DL3's "answer key corrected" path edits the item in place under the same id.
- **Learner-text gaps.** The "not what I asked" text (§6.3) and the "doesn't connect" text on passage offers become one source adapter each once the branch has merged.
- **Decision value.** S5's outcome states are §4.3's. S2a's verdicts are translated as §6.5 says, and arm B licenses skips only (§6.2). `evsi/calibration` owns any change to the heuristic constants and any promotion of a likelihood regime (§11.4).

---

## 21. Agent prompt template (one per phase)

```
You are implementing LearnLoop stage "sources-<phase>" (S0 | S1 | S3 | S2a | S2b | S4 | S5) of
docs/specs/spec_source_practice_and_probes_v1.md, in the worktree <path> on branch
sources/<phase> (base <commit>).

Read first: the spec's §2 (standing constraints), §3 (code truth; re-check every citation you rely
on), §5 (contamination policy), your phase's section, §13 (persistence), §14 (successor and switch),
§16 (gates). Read the Reader spec's consuming sections and router §15.3 for context only.

Build exactly your phase: data, routes, spend caps, kill switch, tests and the gates it lists.
Do not build Reader UI. Do not change grading or evidence semantics; the only certification
change is S1's gate for unverified keys (§7.3a). If your phase changes what is served and the
spec says "no successor", stop and ask the reviewer. S1's certification gate and S2b are
successors (each takes the next free mvp-0.N at merge). A valuation verdict never falls back to
an entropy order (§8.3.4).

Hard rules:
- Work only in your worktree; never edit the main checkout; never commit changes to
  fixtures/linear_algebra, fixtures/probability or fixtures/arxiv_v2.
- Tests use fakes (tests/structured_ai.py StructuredClientFake; tests/helpers.py builders).
- Paid calls only on backup-API copies (learnloop.db.copies.copy_tree_with_databases) under
  fixtures-local/, dry-run first, inside caps; record calls and cost in docs/reviews/<stage>.md.
  Never read ~/.config/learnloop or any .env file; the app loads keys itself.
- Migrations from the next free number; classify tables; upgrade the head fixture (CLAUDE.md).
- Pin new or extended sidecar RPCs desktop-only in tests/test_mobile_allowlist.py.
- Gate: uv sync --extra dev --extra mobile; TMPDIR=<worktree>/fixtures-local/tmp uv run pytest -n auto;
  uv run pytest -m durability when you add a migration; uv run lint-imports --no-cache;
  npm run typecheck && npm test when you touch the app; git diff --check.
- Don't merge, push, rebase onto other branches, or delete branches or worktrees.
- End every commit message with: Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

Return: summary, final commit, review file path, gate results with counts, open questions.
```

---

*Related: `spec_embedding_consumers_v1.md` (§5, §5.9, §9) · `spec_reader_workbench_v1.md` (§7, §9.3) · `spec_action_router_v1.md` (§1, §15.2, §15.3) · `decision_value_and_commissioning_spec_v1.md` (§4.3, §5.3, §6.4) · `spec_daily_loop_v1.md` (§6.9) · `docs/reviews/reader-dialogue-coverage.md` (RS1–RS10) · `docs/brainstorming/Improving Reader's design.md` (round 3)*
