# Canonical sources as a shared instructional service: practice, probes and explanations from the learner's sources (v1)

**Status:** draft for owner review (2026-10-12). A backend track on its own branch (`sources/canonical-practice`), started on the owner's direction of 2026-10-12: "build the router and sources path as its own backend track now". The Reader workbench spec (`docs/specs/spec_reader_workbench_v1.md`, branch `docs/reader-workbench-spec`) owns every Reader surface and consumes this track. This track builds no Reader UI.

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
| `spec_reader_workbench_v1.md` | Consumes this track. RW4a's library ask and compare, RW4b's exercise fallback, RW6b's follow-ups and any RW4c the Reader revision adds are UI over the functions built here. This spec owns `find_sources` (its §7.2 signature is kept as a subset, §9.1), `compare_sources` and the value-of-information adapter that RW6b's §9.3 needs, built once (§8.3) |
| `spec_action_router_v1.md` | §15.3 sketched "canonical sources as a retrieval tool for the router". S4 builds that tool interface and the tutor's use of it now. R2 wiring stays deferred, with a trigger that supersedes §15.3's (§10.6). Item selection within a block stays with P4's selectors and `find_practice` (router §1) |
| `spec_daily_loop_v1.md` | DL3's "Practice on…" box (§6.9) calls S0's RPC. DL1's learner picks are the serving path for proposals. DL2's "Check once" serves the dated checks RW6b creates from S2's valuations |
| `decision_value_and_commissioning_spec_v1.md` | EVSI (§6.4), the repair-linked cold-outcome chain (§4.3) and repair effectiveness (§5.3). S5's outcome states follow §4.3. S2 and the Reader's RW6b are EVSI's first live consumers, whichever merges first |
| `spec_slice_a_practice_and_field_v1.md` | Phase 5a's PF-b verifier and sandbox. Phase 5b's practice index |
| `spec_p3_reader_integration.md` | Invariants 6 (reading is not evidence), 9 (authorship is never laundered) and 10 (cold means no source cue) hold everywhere here |
| `spec_blind_grading_diagnosis_split_v1.md` | The grader stays blind. Retrieval never enters `BlindGradingContext`. Misconception targets are read from the diagnoser's overlay, never from raw grader rows |

**Citation convention.** Every `file:line` was re-checked in this worktree at `57d31c63` (`main`: migration head 180, latest algorithm `mvp-0.14`, the ChatGPT-plan provider merged). Python paths are relative to `src/learnloop/` (sidecar paths, which start with `learnloop_sidecar/`, to `src/`), frontend paths to `apps/learnloop-tauri/src/`, and migrations and docs to the repo root. A bare `:n` refers to the file cited just before it. Unmerged work is named by its branch. "Brainstorm L*n*" means line *n* of the dialogue file.

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
- **S0. `find_practice` gets real callers.** The tutor's "Practice this" offers, the daily plan's learner picks, and the Reader's and DL3's boxes, all through the same RPC. A proposal reaches the learner only through an existing serving path.
- **S1. Textbook exercises as practice candidates (RW4c).**
  - A source-exercise arm in `find_practice`.
  - Import through `import_exercises`, keeping the verbatim stem.
  - The AI-completed key checked by a verifier ladder built from PF-b, with honest labels.
  - Attachment as a surface of a matching practice family.
  - Items that point at their canonical source exercise.
- **S2. Discriminating search**, in two phases.
  - **S2a:** `PracticeConstraints` gains `intent` (`practice` | `discriminate` | `retention` | `remediate`), `target_hypotheses` and the dialogue's typed filters. Candidates are valued by EIG over the learner's rival hypotheses, and by EVSI where a decision is pending. There is no count cap.
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
- any change to grading, evidence or certification semantics.

**Deferred, with triggers in §19:**
- router R2 wiring, and choosing the action and its material together;
- an LLM instructional-role labeller (counterexample, contrast, intuition, prerequisite, alternative treatment) and a source-authored contrast index;
- stored cross-source claim relations;
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
- **SC2. The caller's context sets the policy.** Each call's retrieval policy (§5.1) is derived on the server from where the call comes from: tutor context, item, attempt, cold status. A model's arguments can narrow a request; they can never widen its policy.
- **SC3. Results shown to a model withhold answers.** A tool result returned to an LLM never carries an expected answer, a rubric, a solution block or an item reserved for a cold check. The one exception is the internal `authoring` policy, which never reaches a learner-facing model (§5.3).
- **SC4. Independent checks are unexposed.** A candidate offered as a discriminating or retention check must not have been exposed: not its own span, not its solution, not a revealed sibling, and not an equivalent worked example the learner just studied (§5.4).
- **SC5. Honest labels.** Every result says whether its content is source-authored, AI-written or learner-written. An answer key is "checked" only after a sympy check or a quote-verified source solution passes (§7.3). Valuations are labelled as LearnLoop's estimates.
- **SC6. Value of information, not counts.** How many checks a learner gets comes from the stop rule of `evsi.rank_feasible` (`scheduling/evsi.py:366`), never from a constant. The numbers in this spec are caps on money, time, prompt size or display, never thresholds that decide learning. Every such number is labelled with what it bounds.
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
| Exercise import | RPC `reader.import_exercise` (`learnloop_sidecar/handlers/reader.py:1512`); job `content/pipeline/jobs.py:2215`; `content/authoring/exercise_authoring.py:241` | A Reader selection becomes practice items. The stem is re-anchored verbatim (`:385`); one call completes the answer, rubric, facets, hints and rung metadata (`:352`); provenance is `canonical_extract` with block-span refs (`:523`); the item is written at once (`:540`) |
| PF-b verification | `ops/pf_generation.py:1001` (panel solves), `:1027` (agreement plus sympy), `:1124` (ensemble), `:806` and `:835` (source-anchored span support); sandbox `content/authoring/pf_sandbox.py:84`, `:120`, `:341` | Solve-first panel agreement, an LLM-written sympy equivalence check in bubblewrap, and a quote-verified span that the reference verifier confirms supports the answer. Every verdict goes to `judgment_ledger` |
| Families | `vault/models.py:642` (`ActivityFamily`), `:743` (`family_id`); `substrate/families.py:147` (`apply_family`); `db/stores/families.py:76` (`append_membership`); `ops/pf_publish.py:189`, `:267` | Items carry `family_id` plus `variant_relation`. Membership events are append-only (`migrations/168_activity_family_membership.sql:9`) |
| Probe EIG | `diagnosis/probe_families.py:467`, `:536`, `:621`; `diagnosis/probes.py:786`, `:682`, `:649`; `diagnosis/followups.py:1482`, `:1532`; `diagnosis/probe_targeting.py:621`, `:694`; `diagnosis/probe_episodes.py:818`, `:1386`, `:1576` | EIG over locked hypothesis sets, per-facet EIG over `hypothesis_marginal`, the misconception-discrimination gate and greedy conditional blocks. Live in the scheduler and the post-attempt follow-up slate |
| EVSI | `scheduling/evsi.py:199` (`robust_evsi`), `:293`, `:366` (`rank_feasible`); `scheduling/action_loss.py:235`; `diagnosis/robust_composition.py:353`; constants `:48`, `:49`, `:55` | Robust EVSI in minutes over a credible set, ranked by LCB per minute, with a stop rule and abstention. The only live-path caller is a shadow recorder (`diagnosis/causal_diagnostic_selector.py:300`, called at `diagnosis/causal_orchestrator.py:1493`). `staged_policy.DiagnosticSelector` (`scheduling/staged_policy.py:351`) is never constructed. λ = 1, burden = 0 and 60 minutes per nat are all labelled heuristic |
| Hypothesis state | `hypothesis_sets` (`migrations/001_initial.sql:276`) with `probe_observations` (`migrations/028_probe_episodes.sql:94`); `causal_hypotheses` (`migrations/118_causal_attribution_p1.sql:5`); `unresolved_cause_factors.candidate_causes_json` (`migrations/034_assessment_contract_snapshots.sql:36`); `facet_uncertainty.hypothesis_marginal` (`migrations/012_facet_diagnostic_state.sql:5`) | The rival hypotheses S2 values against |
| Remediation passages | `diagnosis/remediation.py:173` (`prescribe_remediation`), `:233` | For a misconception's target and confused-with facets, the first parseable linked span of each (`:196`–`:215`, ending in `break`). Delivery is recorded as `remediation_delivery` exposure |
| Exposure ledger | `source_exposure_events` (`migrations/150_remediation_delivery_exposure.sql:22`, a closed `context` CHECK); reveal ledger kinds `attempts/reveal_ledger.py:37`; `reader_section_progress` (`migrations/106_reader_section_progress.sql:6`) | What source text reached the learner, what answers were revealed, which sections were read |
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
3. **Role hints are only ever excluded.** There is one deterministic hint per block. There is no counterexample, intuition, prerequisite or alternative-treatment role, and no confidence. S1 and S3 add a positive role filter. An LLM labeller is deferred (§19).
4. **`import_exercises` writes before any check and attaches no family.**
   - Its input is a Reader selection (`raw_selection.nodes`). The crosswalk also accepts span ids with offsets (`reader/annotations.py:217`), so a deterministic adapter can build a selection from block spans.
   - Its single function authors and then writes; S1 splits it so that a check can run between the two steps (§7.2).
5. **The PF verifier is private to a PF run.** `_panel_solves`, `_agreement` and `_span_support` are methods of the run class in `ops/pf_generation.py`. S1 extracts them unchanged into a shared function (§7.3), with a parity test.
6. **`apply_family` only creates a family** (`substrate/families.py:183` refuses an existing identity). Adding an item to an existing family is what PF publication does with `append_membership` (`ops/pf_publish.py:267`). S1 reuses that pattern (§7.4).
7. **No provider path supports native tool calling.** The ChatGPT-plan provider refuses `tools` and `tool_choice` (`ai/chatgpt_plan/responses.py:13`, `:41`). Tool use is therefore a field of structured output (§10.2).
8. **EVSI has no live consumer** (§3.1). S2 and the Reader's RW6b are its first live uses, whichever merges first, and its stop rule decides how many checks a learner gets.
9. **Remediation shows the first linked span per facet** (`diagnosis/remediation.py:196`–`:215`), whatever the misconception says. S3's `remediate` intent ranks and verifies instead (§9.5).
10. **`practice_index_proposals.origin` has a closed CHECK** (`migrations/169_practice_index.sql:35`: `rpc`, `cli`, `tool`, `api`). New callers are recorded in added nullable columns, not in a table rebuild (§6.5).
11. **`limit` is a page size.** `PracticeConstraints.limit` is 1–20 (`practice_index/retrieval.py:126`) and `practice_index.proposals` defaults to 5. For the `practice` intent it stays a display page; the value intents ignore it (§8.3).
12. **`source_exposure_events.context` is a closed CHECK** (migration 150). S5 references existing exposure rows and keeps its own table, so no rebuild is needed.
13. **Admission ignores exposure to equivalent worked examples.** It excludes reserved cold checks and revealed answers only. The dialogue says a textbook exercise from an unread page is still a poor cold test if the learner just studied an equivalent worked example (L1376). S1 and S2 add the rule (§5.4).
14. **The tutor's model sees the current item's key.** `TutorQAContext` carries `expected_answer` and `rubric` in the practice and feedback contexts (`tutor/ai_contracts.py:20`). Any learner-visible text the tutor writes for a tool request passes the same leak check as its answer (§10.3).

### 3.3 In-flight work (2026-10-12)

| Branch | State | What this spec uses |
|---|---|---|
| `router/r1` → `merge/r1` | Built and reviewed; `mvp-0.15` and migration 181 at merge | `router_decisions` (`decision_kind` `today_offer` \| `staged_p2` \| `learner_pick`, exact propensities). S5 stores a `router_decision_id` when a pick is logged there (§11.1); S4's R2 design joins retrieved candidates to its candidate set (§10.6). Nothing here waits for it |
| `learner/text-gaps` | Built and reviewed; `mvp-0.16` and migration 182 expected | `named_gaps_for_card()` (`diagnosis/text_gaps/pipeline.py:850` on the branch): each named gap with its target `{kind, id}`. S2 and S3 accept a `named_gap` hypothesis reference through an adapter that is feature-detected (§8.2) |
| `facets/identity` | Built; migration 183 expected | Canonical facet ids. Everything here already goes through `vault.canonical_facet_id` |
| `docs/reader-workbench-spec` | Spec, being revised | The consumer of S0–S4 (§20) |
| `evsi/calibration` | Started at `57d31c63`, nothing committed | Owns calibrating EVSI's heuristic constants. S5 logs what it needs (§11.4) |
| DL2, DL3 | Not built | DL2's "Check once" serves dated checks; DL3's "Practice on…" box is S0's RPC |

**Numbering.** Migrations are taken from 184 upward, in build order (§13, §15), and will be renumbered at merge. The one successor (S2b) takes the next free `mvp-0.N` tag at its merge and expects relabelling.

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

The dialogue named five contexts (L1368–1374). Three are learner-facing policies, as in the Reader spec's §7.2. `authoring` is restored as an internal policy. `post_attempt` is narrowed.

| Policy | Built from | What a learner or a learner-facing model may receive |
|---|---|---|
| `reading` | `library_scope` or `teaching_scope(item_bound=False)` | Every passage in scope, worked examples and solutions included when asked for: reading is never blocked. Each span shown is recorded as exposure, and the exposure rule then keeps the exercises it gives away out of independent checks (§5.4). Results returned to a model still follow §5.3 |
| `assisted_practice` | `teaching_scope(item_bound=True, item=…)` + the answer-overlap filter (`source_retrieval/tutor.py:125`) + verification | No `exercise` or `solution` block, nothing linked to the item, nothing that reproduces its key. Hints and tutor answers are reveal-accounted as today |
| `cold_attempt` | — | **Nothing.** An empty result by construction, and the tool dispatcher refuses every tool (G2). Opening a source ends cold status (P3 invariant 10); it is never blocked |
| `authoring` (internal) | the source's own extractions, solutions included | Used only by S1's verifier to find the book's solution (S1 builds this scope directly; from S3 on, `find_sources` accepts the policy from that caller only) and by PF's source-anchored path. Never returned by a learner-facing tool, never shown to the learner, never passed to the tutor or the router (SC3) |
| `post_attempt` | **narrowed**: `assisted_practice` for the attempted item, `reading` for everything else | T6 keeps the feedback screen item-bound on purpose: the next attempt's window spans it (`source_retrieval/tutor.py:51`). After the measurement closes, P3's restoration shows the source as today |

### 5.2 Who sets the policy

| Caller | Policy |
|---|---|
| Tutor, practice or feedback context | `assisted_practice` with the item |
| Tutor, library or reader context | `reading` |
| Any caller during a cold administration | `cold_attempt` |
| Daily plan learner pick, DL3's box, Reader library | `reading` (proposals only; admission applies) |
| S2b need fulfilment, S1 harvest | `reading` for discovery, `authoring` for verification only |
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

A candidate offered for the `discriminate` or `retention` intent (§8), or used to fulfil a need (S2b), must be unexposed. That means none of the following:
1. an attempt on the item (`unattempted_only`);
2. a reveal on the item or on any member of its family within the cold retrieval delay (the reveal ledger; `exclude_revealed_families`);
3. for a source exercise or an item with a `canonical_exercise` (§7.4), a `source_exposure_events` row on its span or its solution region within the cold retrieval delay;
4. **an equivalent worked example studied within the cold retrieval delay** (built in S2a).
   - The shortlist is every `worked_example` block in the candidate's teaching scope that has an exposure row, or that sits in a section `reader_section_progress` marks as read, within the delay. It is ranked by keyword and vector similarity to the candidate.
   - One listwise call (route `worked_example_equivalence`) judges each shortlisted example as `equivalent` (the exercise would be a near-copy), `related` or `unrelated`. Every verdict goes to `judgment_ledger`.
   - `equivalent` excludes the candidate from independent intents; it stays available for `practice`.
   - `related` applies `familiarity_discount` (`learner/recall_coverage.py:293`) to its value, as the scheduler does for familiar probes.

The delay is `COLD_RETRIEVAL_DELAY` (1 day, `diagnosis/remediation.py:30`), the window admission already uses. Router §15.2 says coldness should be learned rather than hard-coded, so S5 logs the time since each exposure for R3 to fit (§11.1).

### 5.5 Receipts that let anyone reconstruct access (L1378–1380)

Each `source_tool_calls` row (§10.4) and each `find_sources` manifest records:
- the query hash;
- the effective policy and how it was derived;
- the scope's extraction ids, each with its revision id;
- the returned asset ids;
- the verification statuses.

Exposures are recorded where text is shown, as today (`source_exposure_events`, the reveal ledger). S5 links the two.

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

- **An item proposal**, picked → `plan_learner_pick(practice_item_id, proposal_id=…)` with the plan on, or the open-list pick with it off. Both append the `practised` usage signal (`practice_index/usage.py:39`) at the pick, not only through the 72-hour attempt join.
- **A source-exercise proposal** (S1), picked → `import_source_exercise(proposal_id, span keys)` (§7.2) → the new item id → the same pick path.
- **"Not what I asked"** takes optional text (learner text over skip buttons). The text is stored on the usage verdict's rationale. Once learner-text gaps has merged, a source adapter reads it like any other learner text (§20).

Nothing else serves a proposal. In particular, a proposal never enters Today's queue by itself.

### 6.4 What the learner sees (outside the Reader)

In `components/AskOverlay.tsx`, for the practice, feedback and library contexts: a "Practice this" strip under the answer. It shows up to `limit` proposals: the prompt, the LO, and the rerank's one-line rationale, labelled "LearnLoop's reason". Each has "Practise" and "Not what I asked…". A source exercise shows "From *Book*, p. *N* · not yet in your practice". The reader context's strip is the Reader spec's.

### 6.5 Data, routes, spend

- **Migration 184:** `practice_index_proposals` gains nullable `caller TEXT`, `caller_ref TEXT` and `intent TEXT` (`ALTER TABLE ADD COLUMN`; the role stays RECEIPT). `origin` keeps its CHECK; S0 calls use `rpc` with `caller` set.
- **Routes:** Phase 5b's `practice_rerank` and the query embedding, unchanged. For this interactive path the fast route (ChatGPT-plan) is recommended (D6).
- **Spend:** unchanged per call (`practice_index.rerank_max_cost_usd`).

### 6.6 Successor, kill switch, gates, tests

- **Successor:** none. Proposals never serve, and a learner pick is an existing serving path (Phase 5b's ruling, `config/schema.py:1731`).
- **Kill switch:** `source_service.tutor_offers` (off: no `practice_request` on tutor answers). `practice_index.enabled` still switches `find_practice` itself off.
- **Gates:** G1, G2, G14, G16.
- **Tests:**
  - `test_tutor_practice_request.py`: deterministic request, current item excluded, caller re-derived;
  - `test_learner_pick_proposal.py`: pick with a proposal id, usage verdict, plan parity when the id is absent;
  - `test_practice_proposal_caller_columns.py`;
  - the frontend `AskOverlay` strip test;
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

**The split.** `import_exercises` becomes `author_exercises(...)`, which returns authored drafts, and `write_exercises(...)`. The existing function becomes their composition, so the Reader's path is unchanged (parity test G5). The drafts keep today's rules: the verbatim re-anchored stem, the facet registry, rubric arithmetic, the capability vocabulary and the task-feature schema.

**The adapter.** `content/authoring/source_exercise_import.py:selection_for_region(extraction_id, span_ids)` builds `raw_selection.nodes` from block spans, with `start = 0` and `end = len(text)`. The crosswalk accepts that form (`reader/annotations.py:217`). The import pipeline below lives in the same module.

**Interactive import** (a learner picked a proposal): the RPC `import_source_exercise(proposal_id, extraction_id, span_ids)` enqueues a `source_exercise_import` job on the main single-writer lane, like `reader_exercise_import` (`content/pipeline/jobs.py:2215`):
1. **Look for the book's solution** (§7.3 rung 1's search and match, under the internal `authoring` policy).
2. **Author.** When a solution was found, it is passed into the authoring context, so the key is written from the source (the source-anchored "answer first" pattern).
3. **Check within a time box** (`source_service.verify_timeout_seconds`, default 90 s; a time bound). If the ladder (§7.3) finishes inside the box, the item is written with its status. If not, the item is written labelled `checking`, the pick proceeds, and the check finishes in the background (D1).
4. **Write** with `canonical_exercise` (§7.4) and the key's status.
5. **Attach** to a family (§7.4).
6. **Return** the item id to the pick path (§6.3). The frontend follows the job with the RPC `get_source_exercise_import(import_id)` (status, key label, item id).

**Owner-run harvest:** `learnloop sources exercises harvest [--lo …] [--facet …] --dry-run | --max-cost-usd`.
- **Targets:** facets that `coverage_report` (`practice_index/coverage.py:42`) lists as thin. From S2a on, also facets with open rival hypotheses (§8.2).
- **Per target:** the arm's judged candidates, each imported with the ladder run *before* writing.
- **Bounds:** money (`--max-cost-usd`) and the judge's picks. There is no count of exercises.
- **What reaches the learner:** DL1's new-material admission bounds how many new items appear each day.

Automatic background harvesting is deferred (§19, D7).

### 7.3 The verifier ladder (honest key labels)

`ops/pf_verify.py:verify_reference(stem, reference, *, caller, source=None)` extracts PF-b's code unchanged:
- the panel solves of `ops/pf_generation.py:1001`;
- the agreement with the sandboxed sympy confirmation of `:1027`;
- the span support of `:806`.

The PF run class calls the extracted function; a parity test pins that its ledger rows and decisions are unchanged.

| Rung | Check | Key status shown | Ledger |
|---|---|---|---|
| 1. **The book's solution** | Within the source's own extractions, solutions included (the internal `authoring` policy, built directly from `extraction_scope`, `source_retrieval/corpus.py:112`): `search_spans` with `roles=("solution",)`, querying the exercise's label and stem. One listwise call (route `source_solution_match`) names the passage that solves this exercise, or none. Then the quote check (the key's cited quote must appear verbatim in that passage; S1 adds a `cited_quote` field to the authoring contract for this case) and PF's span-support verifier (`pf_reference_verifier`). When rung 1 passes, rung 2 does not run | "Answer from the book's solution, *Book* p. *N*" (`book_solution`) | `source_solution_match`, `reference_verified` |
| 2. **Panel plus sympy** | At least `pf.min_agreeing_solves` panel solves agree with the key, solving without seeing it. For numeric or symbolic answers the LLM-written sympy check confirms in bubblewrap, with negative controls | "Checked: independent solvers and a symbolic check agree" (`checked`) | `answer_equivalence`, `reference_verified` |
| 2′. **Panel only** | The panel agrees, but the answer is prose, or no sandbox is available (macOS or Windows fail closed: `content/authoring/pf_sandbox.py:84`) | "Independent model solvers agree; not symbolically checked" (`panel_agrees`) | as rung 2 |
| 3. **Model's answer** | The check did not run (no route, no price, over budget, timed out), or it is still running | "Model's answer, not checked" (`model_answer`) or "being checked" (`checking`) | the skip reason |
| ✗ **Disputed** | The panel's agreeing answer differs from the key, or the book's solution was found and the span-support verifier finds it does not support the key | "LearnLoop's check disagrees with this answer key" (`disputed`), with the panel's answer one click away | `reference_verified` = `fail` |

**What the labels change.**
- Only `book_solution`, `checked` and `panel_agrees` keys qualify for the `discriminate` and `retention` intents and for S2b, whose value depends on the key. `checking`, `model_answer` and `disputed` keys stay available for `practice`.
- Grading and evidence semantics are unchanged from today's imported exercises, which are never checked. Whether unchecked or disputed keys should stop certifying is an owner decision for a later successor (D2), and S1's report gives the data.

### 7.4 "Change what cards represent": family attachment and the canonical exercise

**The canonical exercise.**
- `PracticeItem` gains an optional `canonical_exercise: {source_id, revision_id, extraction_id, span_ids, label, relation: "verbatim" | "variant_of"}`. It is omitted when null, as `family_id` is (`vault/models.py:743`).
- It sits outside `practice_item_hash` (`vault/hashes.py:45`), so scheduling hashes are unchanged, and items without it serialize byte-identically (G5).
- Imported exercises get `relation = "verbatim"`. PF-b variants published from a parent with a canonical exercise copy it with `relation = "variant_of"` (one line in `ops/pf_publish.py`'s payload builder).

**The practice screen** shows "From *Book*, Exercise 4.12 · open in source" and the key status (§7.3). The link is hidden during a cold administration and shown after submission (P3 invariant 10). Opening it records exposure.

**Family attachment** (`source_service.family_attachment`):
1. **Candidate families:** the `ActivityFamily` rows on the item's LO (`vault/models.py:642`).
2. **Same retrieval target, and which relation?** PF's family judge (ledger task `same_target`, route `pf_family_judge`) judges the new item paired with every current member, with both of its prompts (`pf-same-target-direct-v1`, `pf-same-target-counterexample-v1`; `substrate/families.py:32`). Every pair must be judged `same` by both passes, and the passes must agree on the relation (`same_target` or `isomorph`). This is the complete-link rule `_validate_judgments` enforces for automatic families (`substrate/families.py:96`).
3. **Attach:** the new `substrate/families.py:attach_to_family`, with `apply_family`'s recover and undo discipline: the plan in `family_proposals`, the YAML patch to `family_id` and `variant_relation`, `append_membership` with the decision's ledger id. `apply_family` is unchanged.
4. **No matching family, or only a `near` or `far` kinship:** the item stays unfamilied. `near` and `far` members come only from PF generation, which declares the checkpoints it changes. An unfamilied exercise becomes an ordinary PF-b parent candidate, so variants are generated from the real textbook exercise ("generation on demand", L1163–1165).

### 7.5 Data, routes, spend

- **Migration 185: `source_exercise_imports`** (WORKFLOW: paid outputs; never re-run on rebuild):
  - `id`, `proposal_id`, `extraction_id`, `span_ids_json`, `source_id`, `revision_id`, `label`;
  - `practice_item_id`, `key_status`, `verification_json` (rung, ledger ids, panel summary);
  - `family_proposal_id`, `status` (`authoring` | `checking` | `written` | `failed`), `reason`;
  - `caller`, `created_at`, `updated_at`.
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

- **Successor:** none. The arm proposes. An import is a learner-authority write, as today's Reader import is. A harvest is owner-run content, like PF-b publication, which its config calls "a content change … not an algorithm change" (`config/schema.py:1648`). Family attachment is a content change on PF's substrate.
- **Kill switches:**
  - `source_service.exercise_arm` (off: `find_practice` as Phase 5b built it);
  - `source_service.exercise_verification` (off: imports as today, labelled `model_answer`);
  - `source_service.family_attachment`.
- **Gates:** G1, G3, G4, G5, G6, G7, G14, G15.
- **Tests:**
  - `test_exercise_arm.py`: positive filter, regions, already-imported exclusion, teaching exclusions;
  - `test_import_split_parity.py`;
  - `test_selection_for_region.py`;
  - `test_pf_verify_extraction_parity.py`;
  - `test_key_ladder_labels.py`: each rung, sandbox unavailable, disputed, timed out;
  - `test_attach_to_family.py`: attach, undo, recover, refusal on an LO mismatch;
  - `test_canonical_exercise_serialization.py`;
  - `test_harvest_dry_run.py`.

---

## 8. S2 — Discriminating search: intents ranked by value of information

### 8.1 Typed constraints (brainstorm L1207–1240)

`PracticeConstraints` (`practice_index/retrieval.py:111`) gains the fields below. All are exact filters except `intent` and `target_hypotheses`.

| Field | Meaning | Dialogue name |
|---|---|---|
| `intent` | `practice` (default; today's relevance ranking) \| `discriminate` \| `retention` \| `remediate` | `intent` |
| `target_hypotheses` | `HypothesisRef{kind, id}` with kind ∈ `misconception`, `causal_hypothesis`, `episode_label`, `unresolved_cause`, `facet_state`, `named_gap` | target hypotheses |
| `kinds` | `items` \| `source_exercises` \| `both` (added by S1, §7.1) | — |
| `unattempted_only` | No attempt on the item | `unseen_required` |
| `exclude_family_ids`, `exclude_revealed_families` | Families excluded by id, or because a member's answer was revealed within the cold delay | `exclude_exposed_families` |
| `facet_match` | `any` (default) \| `all`: an integrative problem must test every listed facet (L1107) | — |
| `allow_generated` | When false, only `canonical_extract` and owner-authored items | `allow_generated_variants` |
| `max_minutes` | Through the injected minutes estimator (DL1's `daily_plan/estimates.py:138`, SC12). Refused with a typed error when no estimator was injected, never ignored | `max_estimated_minutes` |

The two filters RW6b needs (`unattempted_only`, `exclude_family_ids`; Reader spec §3.4 item 7) are these. The dialogue's `answer_visibility` is not a field: the caller's policy sets it (§5.2).

### 8.2 Where the rival hypotheses come from

`instructional/valuation.py:open_hypotheses(facets, refs)` reads them where they already live and writes nothing:
- **an open probe episode's** locked set, with its posterior replayed (`episode_posterior`, `diagnosis/probe_episodes.py:1576`);
- **a diagnosed attempt's** rival causes (`unresolved_cause_factors.candidate_causes_json`);
- **open `causal_hypotheses`;**
- **the facet's `hypothesis_marginal`** (facet-solid, facet-absent, misconception labels);
- **active misconceptions** on the facets, from the diagnoser's overlay;
- **named gaps**, once `learner/text-gaps` has merged: `named_gaps_for_card()`'s target `{kind, id}` mapped to the matching misconception or facet hypothesis. Before the merge, a `named_gap` ref returns `unavailable: learner-text gaps not merged`. The adapter is feature-detected by the presence of the branch's table;
- **a router R1 decision's** logged `probe_eig` candidates are not hypotheses; S5 only references the decision id.

With no `target_hypotheses`, the intent uses every open hypothesis on the constraint facets.

### 8.3 Valuation (the adapter RW6b also uses, built once)

`instructional/valuation.py:value_candidates(candidates, hypotheses, *, decision=None, minutes)` makes no model call. It returns a `ValuationReceipt`. `find_practice` receives it as an injected `valuer`; called without one, a value intent is refused with a typed error rather than ranked by relevance alone.

1. **Relevance first.** The listwise judge keeps the candidates that test the capability or bear on the rival hypotheses, quoting what in the candidate does so. It never picks a winner or a number.
2. **Information (EIG).**
   - Probe instruments: `instrument_expected_information_gain`, or the predictive variant when its target set is adequate, never both added (`diagnosis/probe_families.py:467`, `:536`).
   - Ordinary items: per-facet EIG over `hypothesis_marginal` (`diagnosis/probes.py:786`), plus the misconception EIG behind `_misconception_discrimination`'s Youden-J gate (`diagnosis/followups.py:1482`), which uses an estimated discrimination row where one exists and the rubric-fatal-error bridge otherwise (`diagnosis/probes.py:595`).
   - Source exercises not yet imported: see §8.4.
   - Familiar surfaces are discounted with `familiarity_discount`.
3. **Value for the next decision (EVSI).** When the caller passes a pending `decision` (for example which repair class, from the causal loss table), the value is `robust_evsi` over the candidate's credible set (`scheduling/evsi.py:199`), with the loss table from `action_loss.build_loss_table` (`scheduling/action_loss.py:235`). Without a decision, `robust_composition.evaluate_selection` converts the robust EIG to minutes (`diagnosis/robust_composition.py:353`).
4. **Rank and stop.** `rank_feasible` ranks by LCB / (expected minutes + burden), with expected minutes from the injected estimator. Checks are added greedily, each valued conditionally on those already chosen (the rule of `plan_precommitted_block`, `diagnosis/probe_episodes.py:1386`), so two checks that would say the same thing are not both proposed. Adding stops when the best remaining LCB ≤ λ·minutes + burden. An `abstain` verdict falls back to EIG-per-minute order with the same stop, labelled "value uncertain".
5. **The number follows.** The result is every candidate that clears the stop, in order: often none, sometimes several. `limit` does not apply.
   - The relevance pool is a prompt-size bound. When the judge keeps every candidate in a pool, the next page of the RRF order is judged, money and time permitting. The pool is therefore not a hidden count cap.
   - What a learner is actually served stays bounded by the plan's minutes.
6. **No new constants.** λ, the burden and the nat-to-minutes scale are the existing heuristic decision parameters (`diagnosis/robust_composition.py:48`, `:49`, `:55`), read from there so that a calibration lands everywhere at once (§11.4).

**Intents.**
- **`discriminate`:** the steps above, over the rival hypotheses.
- **`retention`:** the hypotheses are "holds unaided" and "doesn't" for facets whose recent success was assisted only, with the active predictor's P(success) as the prior. Only unexposed, unfamiliar candidates qualify (§5.4). The caller dates the check (RW6b, DL2).
- **`remediate`:** practice that repairs a named misconception. The relevance judge keeps candidates keyed to it (a fatal error or profile naming it, or the target facet), ranked by relevance; no EVSI.
- **`practice`:** today's ranking.

**The receipt** is stored on the proposal row. It holds the hypotheses and their priors, then per candidate: EIG, EVSI point, LCB and UCB, expected minutes, the exposure verdicts, the stop verdict and reason, and the module versions. Fields R1 also logs use R1's names (`probe_eig`, `evsi_assignment`), so R3's replay can read both.

### 8.4 Source exercises as discriminating candidates (the "probe" half)

An exercise that has not been imported has no rubric and no profiles. For `discriminate`, the arm's judged exercises go through one screening call (route `exercise_discrimination`, listwise):
- per rival hypothesis, what would a holder visibly write on this exercise (an `observable_signature`, the `DiscriminationProfile` field, `vault/models.py:446`);
- whether the signatures differ observably.

The screen must give every rival hypothesis a signature and say what any other cause would produce (the `H_OTHER` disposition). That is the completeness the decision-value spec requires before a set of rows counts as a likelihood (its §6.2 arm B, as `likelihood_regime_for_candidate` classifies it, `diagnosis/causal_diagnostic_selector.py:195`).
- **A complete screen** gives provisional likelihoods: the signatures, softened by the rubric bridge's sensitivity and specificity (`diagnosis/probes.py:595`).
- **An incomplete screen** is a structural audit, not a likelihood. The candidate gets no EVSI and is ranked by facet EIG only.

The receipt stamps `likelihood_basis` (`authored_profile_unchecked` or `structural_only`), and the learner-facing label says the value is "estimated from a model's reading of the exercise". The hypotheses' prior keeps its producer's `prior_basis`, so `rank_feasible`'s rule that only a `support_weighted` causal prior is valued live (`scheduling/evsi.py:65`) applies unchanged.

When one is chosen and imported, its profiles are written on the item (`discrimination_profiles`, `vault/models.py:718`) and run through the planted-persona gate (`content/authoring/persona_gate.py`) before any later valuation treats them as checked. The diagnoser remains free to say `no_profile_applies`.

Source exercises chosen this way are served as **ordinary items** through the paths in SC1. Promoting them to formal probe instruments (compiled conditionals, probe episodes) is deferred (§19).

### 8.5 S2b — Source-first fulfilment of intervention needs (successor)

When the follow-up chooser finds no suitable item, it records an intervention need with `blocked_reason = "no_suitable_item"` (`diagnosis/followups.py:381`). Adapters fulfil needs on demand through the generation lane (`generate_diagnostic_practice_proposal`, `content/authoring/practice_generation.py:646`, which plans from `:441`):
- the primed-retry handler when the LO has no sibling (`learnloop_sidecar/handlers/feedback.py:571`, calling generation at `:613`);
- the CLI's `learnloop generate-diagnostics` (`cli/app.py:2568`).

S2b adds one step in those two adapters, before they generate. The tutor's promotion path also generates for needs (`tutor/promotions.py:741`); it lives in a domain package, which may not import the service (SC12), so it keeps generating, and wiring it through an injected callable is left to a follow-on.
1. `fulfil_need_from_sources(need)` calls `find_practice` with `kinds = source_exercises` and the need's target facets.
   - The intent is `remediate` in the primed-retry handler, because that item is served primed, as a repair, and a primed answer can't be an independent check. In the CLI path it follows the need: `discriminate` when its diagnostic focus names rival misconceptions, `remediate` otherwise.
   - It also applies the need's `candidate_requirements` (same LO, minimum facet overlap).
2. If a candidate clears the valuation's stop, or for `remediate` the judge picks one, it is imported with the ladder run *before* writing. Only a key that qualifies (§7.3: `book_solution`, `checked` or `panel_agrees`) can fulfil the need; otherwise the next candidate is tried, and then generation.
3. The imported item fulfils the need (`status = fulfilled`, linked in `source_exercise_imports.need_id`). The follow-up then serves it through the unchanged path.
4. Otherwise generation proceeds exactly as today.

This is the dialogue's "retrieval first, generation on demand" (L1163–1165) for the system-initiated path.

**Successor:** the next free `mvp-0.N` at merge, because it changes which item a follow-up serves. Kill switch `source_service.source_first_needs`; off, the generation lane is byte-identical (G10). Vaults below the tag never run it.

### 8.6 Data, routes, spend, gates, tests

- **Migrations:** 187 (S2a) adds `practice_index_proposals.valuation_json`; 188 (S2b) adds `source_exercise_imports.need_id`. Both are nullable `ADD COLUMN`.
- **Routes:** `practice_rerank` (relevance), `exercise_discrimination` (new), `worked_example_equivalence` (new; §5.4 rule 4 is built here). The valuation makes no call.
- **Spend:** within `source_service.max_daily_cost_usd`; S2b's imports are capped per import.
- **Kill switches:** `source_service.discriminating_search` (off: every intent except `practice` is refused with a typed error); `source_service.source_first_needs` (S2b).
- **Gates:** G1, G8, G9, G10, G13, G14.
- **Tests:**
  - `test_practice_constraints_v2.py`: each filter, the minutes estimator required;
  - `test_value_candidates.py`: fixture with known EIG, EVSI, stop, abstain, greedy conditional, no count cap (three candidates clear and three return);
  - `test_open_hypotheses_adapters.py`, with the named-gap adapter absent and present;
  - `test_exercise_discrimination_screen.py`;
  - `test_source_first_needs.py`: fulfilment, fallback, disputed key refused, kill switch parity, version gating.

---

## 9. S3 — `find_sources` with intents, and syntopic retrieval

### 9.1 The function

`source_retrieval/find_sources.py`. This keeps the Reader spec's §7.2 signature as a subset (`intent` defaults to `explain`):

```python
def find_sources(
    vault, repository, query: str, *,
    intent: Literal["explain", "remediate", "alternative", "worked_example", "compare"] = "explain",
    policy: Literal["reading", "assisted_practice", "cold_attempt", "authoring"],
    scope: Literal["library", "teaching"] = "teaching",
    learning_object_ids=(), facet_ids=(), item=None,
    target_hypotheses=(), exclude_span_keys=(), roles=(),
    learner_work_md: str | None = None, personalized: bool = True,
    verify: bool = True, limit: int = 8,
    embedder=None, rewrite_client=None, rerank_client=None, deadline=None,
) -> SourceHits   # hits (verbatim span, source, section, page, revision) + manifest (§5.5)
```

- `limit` is a display page.
- `cold_attempt` returns nothing.
- `authoring` is accepted only from S1's verifier and PF (G2).
- `compare` delegates to `compare_sources` (§9.4).

### 9.2 Recipes per intent

Every intent runs `search_spans` over the policy's scope, with extra ranked lists fused by RRF. Then one listwise verification call checks fit for the intent (route `source_rerank`, ledger task `source_intent_fit`, with a verdict set per intent). Only picked spans are returned.

| Intent | Extra ranked lists | Verdicts (best first) | Dialogue |
|---|---|---|---|
| `explain` | The LOs' linked spans (as T6's provenance list) | `answers` / `related` / `unrelated` (T6's) | Mode 1–2 material (L1252–1260) |
| `remediate` | §9.3 | `addresses_confusion`, `contrasts` (the passage explicitly separates the two confused ideas), `related`, `unrelated` | Targeted remediation (L1309–1326) |
| `alternative` | Hits from sources other than those of `exclude_span_keys` (the spans already shown in this thread or inquiry, read from the question events' manifests and exposure rows) | `different_treatment` (another source, representation or role), `same_treatment`, `unrelated` | "An alternative explanation of a concept the learner has struggled with" (L1105) |
| `worked_example` | `roles=["worked_example"]` as a positive filter; `learner_work_md` goes into the verification context | `follows_learner_route` ("should not have to restart", L1242–1246), `worked_example`, `unrelated` | L1103, L1242 |
| `compare` | §9.4 | §9.4 | L1328–1342 |

- **Personalization.** `remediate` and `alternative` read learner state, and the result says so ("chosen for your open question about …"). `personalized = False` gives plain retrieval rank, the dialogue's guard against confirmation bubbles (L877). Callers expose the toggle.
- **Source objects** (`migrations/094_source_objects.sql`), where they exist, add one more ranked list for intents whose object type matches: `worked_example` → `worked_example`; `explain` → `definition`, `claim`, `procedure`. Their citations are resolved from revision to extraction with `resolve_extraction_id`. Nothing is written to them.

### 9.3 Misconception-conditioned retrieval (`remediate`)

For each target misconception (from `target_hypotheses`, the item's active misconception in the diagnoser's overlay, or a named gap):
- **Query:** the learner's question when there is one, else the misconception's statement plus its `correction_statement`.
- **Extra list `correction_facets`:** the spans named by the `locator`s of the misconception's `target_facet` and `confused_with_facet` source refs, parsed with `parse_block_span` (the remediation path's own resolution, `diagnosis/remediation.py:196`).
- **Extra list `correction_sources`:** keyword hits restricted to the sources named by `correction_source_span_ids` (§3.2 item 2: source ids). The field is read for the first time. Rows whose ids name no current source contribute nothing, and the manifest says so.

### 9.4 `compare_sources`: the syntopic operation (L242–262, L869–875, L1328–1342)

`source_retrieval/compare.py:compare_sources(query, *, facet_ids=(), requested_perspectives=(), pinned_span_keys=(), policy="reading")`. The Reader's compare UI and S4's tool of the same name both call this function.

1. **Counterparts.** `find_sources(intent="explain", scope="library")`, grouped by source, keeping each source's best verified passage (or two, when they play different roles). Pinned spans are always included.
   - **No source cap.** Sources are ordered by verified relevance, and as many as fit `source_service.compare_max_prompt_tokens` (default 24,000; a prompt-size bound) are compared.
   - The rest are listed as "also discussed in: …", uncompared, with their passages one click away. The result says so honestly.
2. **One comparison call** (route `source_compare`) returns:
   - per source, its distinct contribution, and its perspective as either a requested perspective it satisfies or one it names (for example "geometric view", "application");
   - per requested perspective with no source, "not found in your library";
   - per pair, a relation ∈ `equivalent`, `different_assumptions`, `different_notation`, `complementary`, `disagreement`, `unclear`.

   Every statement quotes its own source's passage. The quote is verified in code: its normalized text must appear in that passage, and a line that fails is dropped, not repaired.
3. **No consensus.** The output schema has no merged or "canonical" answer field (L261, L1342). Source claims, LearnLoop's comparison lines (labelled AI-written) and the learner's notes stay separate.
4. **Stored** in `source_comparisons`, so a reopened comparison is not paid for twice. Nothing is written to `source_object_relations`; keeping a comparison as relation proposals is deferred (§19).

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
- **Migration 186: `source_comparisons`** (WORKFLOW; paid output, never re-run on rebuild): `id`, `query_hash`, `query_md`, `requested_perspectives_json`, `counterpart_keys_json`, `comparison_json`, `dropped_lines_json`, `model`, `prompt_version`, `ledger_ids_json`, `caller`, `caller_ref`, `created_at`.
- **Routes:** `source_rerank` (intent prompts), `source_compare` (new), `source_query_rewrite` (unchanged). The interactive routes are recommended on the fast route (D6).
- **Spend:** T6's caps per call; compare is one call capped by `source_service.compare_max_cost_usd` (default $0.05 metered); the daily cap.
- **Successor:** none. Retrieval is context (T6's ruling, `config/schema.py:1769`).
  - For `remediation_passages`, the S3 agent confirms with the reviewer that changing which passage the repair overlay shows is context, not serving.
  - If they rule otherwise, it takes the next free `mvp-0.N` with parity under the switch.
- **Gates:** G2, G3, G11, G12, G13, G14.
- **Tests:**
  - `test_find_sources_intents.py`: lists, verdicts, the positive role filter, `cold_attempt` empty, `authoring` refused for other callers;
  - `test_remediate_correction_refs.py`: source ids as a filter, locators resolved, missing sources reported;
  - `test_alternative_excludes_shown.py`;
  - `test_compare_sources.py`: quote verification, dropped lines, no consensus field, no source cap with the prompt bound and "also discussed in";
  - `test_tutor_intent_provider.py`;
  - `test_prescription_passages.py`: ranked, fallback, switch parity.

---

## 10. S4 — The typed tool interface; the tutor uses it now

### 10.1 The registry

`instructional/tools.py` declares five tools, each with a strict pydantic argument model (`extra="forbid"`). Each publishes its JSON schema, as `FIND_PRACTICE_TOOL` does (`practice_index/tool.py:36`).

| Tool | Arguments (all typed; no policy field) | Model call |
|---|---|---|
| `find_practice` | `query`, `intent`, `facet_ids`, `learning_object_ids`, `target_hypotheses`, `kinds`, `unattempted_only`, `max_minutes`, `reason` | Phase 5b's rerank; S2's screens |
| `find_sources` | `query`, `intent`, `facet_ids`, `target_hypotheses`, `roles`, `reason` | Verification |
| `compare_sources` | `query`, `facet_ids`, `requested_perspectives`, `reason` | One comparison |
| `find_facets` (router §15.3's `facet_lookup`) | `query` | **None.** BM25 and vector shortlist over facet dossiers and labels (`rank_dossier`'s facet stage, `practice_index/retrieval.py:383`), labelled a shortlist. The caller's model decides |
| `practice_availability` (the dialogue's two-stage interface, L1199–1203) | `facet_ids`, `intents` | **None.** Recall plus admission only: per intent, the number of admissible candidates, their expected minutes and their kinds. The cheap discovery pass a router needs before choosing a block |

The dispatcher `run_tool(name, arguments, *, caller)`:
1. derives the policy from the caller (§5.2);
2. validates the arguments and drops unknown ids, recording what it dropped;
3. refuses everything during a cold administration;
4. runs the operation and filters the result for a model reader (§5.3);
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

**Migration 189: `source_tool_calls`** (RECEIPT; append-only, nothing updated in place). A validated request writes a `request` row; running it writes a `run` row that names the request as its `parent_id`.
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

- **Migration 189** (above).
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

**Migration 190: `retrieval_interventions`** (RAW_LEDGER: append-only facts captured when something reaches the learner, and inputs to later computation).

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
- `valuation_json`: the predicted EIG and EVSI, and the predicted outcome distribution P(E) for a valued check;
- `exposure_event_ids_json`;
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
- key-label rates (S1's `book_solution`, `checked`, `panel_agrees`, `model_answer`, `disputed`);
- the exposure rule's exclusions.

Labelled throughout: "Associations, not causes: improvement after an explanation doesn't show the explanation caused it (L1402)". Nothing reads the report to serve.

### 11.4 Calibrating value of information from these records

This answers the owner's question of 2026-10-12: can EVSI be calibrated instead of running on unchecked assumptions? Yes, because each of its inputs can be checked against what happens. S5 records what the checks need. The `evsi/calibration` track owns the fitting and any change to the constants, as a successor.

1. **The predicted outcome distribution.** EIG and EVSI are only as good as P(E) = Σ_H P(H)·P(E | H). For every valued check, S5 stores the predicted P(E) and the observed bucket. Log loss and a reliability table, prequential by date, show whether the likelihoods (authored profiles, discrimination rows, the IRT-based facet conditionals, the rubric bridge) are calibrated.
2. **Information actually gained.** The predicted EIG against the realized posterior entropy drop on the target hypotheses.
3. **Decisions actually changed.** EVSI predicts that an observation changes the chosen action. S5 records the action before and after the observation (from the episode's or need's receipts), and whether it flipped.
4. **Minutes.** The predicted minutes against the attempt's actual duration, which the loss table and the stop rule both use.
5. **The value of a nat.** `VALUE_PER_NAT_MINUTES` (60, heuristic) can be fitted as the minutes the downstream decision saved per nat resolved: the realized loss difference between the action taken after the check and the action the prior would have taken, where `R_cold` later says which was right.

   λ = 1 is the numeraire and stays fixed. The burden is the learner's: S5 records skips and "not now" on checks, the revealed cost of being asked.

Until the calibration track replaces them, the heuristic constants are used and every valuation says so ("LearnLoop's estimate; its scale is not yet calibrated").

### 11.5 Successor, kill switch, gates, tests

- **Successor:** none. Reports only; nothing reads these tables to serve.
- **Kill switch:** `source_service.interventions` (off: no rows written; the report says so).
- **Gates:** G13 (one replayer, deterministic rebuild, zero calls), G14.
- **Tests:**
  - `test_retrieval_interventions_write_points.py`: every kind, nothing written on retrieval alone;
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
| 88 | 1092–1109 | Retrieval for a purpose: a discriminating exercise, a worked example in the learner's approach, a prerequisite passage, an alternative explanation, a figure for interaction, an integrative problem | **Built:** discriminating (S2), worked example (`worked_example` with `learner_work_md`), alternative, integrative (`facet_match = all`). **Narrowed:** prerequisite passages come from `explain` over the prerequisite LO's teaching scope, because there is no prerequisite role yet (labeller deferred); figures through `roles=["figure","equation"]` for RW5's candidates, with tutor-initiated figures deferred |
| 89 | 1111–1121 | Three operations on a shared substrate: `find_sources`, `find_practice`, `find_examples` | **Built** as four operations. **Narrowed:** `find_examples` is `find_sources(intent="worked_example")`, because one function shares the scope, contamination and verification. A separate one would duplicate all three |
| 90 | 1115–1119 | Consumers: Reader, tutor, router, practice selector, diagnostic controller, workbench | **Built:** tutor (S4), practice selection through needs (S2b) and the plan (S0), the diagnostic side through valuation (S2). **Elsewhere:** Reader and workbench (Reader spec). **Deferred:** router (§10.6) |
| 91 | 1131–1161 | Don't eliminate cards; change what they represent | **Built:** family attachment and `canonical_exercise` (§7.4) |
| 92 | 1163–1165 | Retrieval first; generate on demand | **Built:** S2b for needs; unfamilied exercises become PF-b parents (§7.4) |
| 93 | 1167–1169 | A textbook problem needs a competency mapping, a checked answer and exposure checks | **Built:** import's facet mapping, the verifier ladder (§7.3), the exposure rule (§5.4) |
| 94 | 1171–1197, 1364 | Selection separate from retrieval; the router's model never sees a key | **Built:** SC1, SC3, §5.3 |
| 95 | 1199–1203 | A cheap availability pass before the router chooses | **Built:** `practice_availability` (§10.1). Consumed at R2 |
| 96 | 1207–1240 | Natural-language queries with typed, machine-enforced constraints | **Built:** §8.1. `answer_visibility` is the caller's policy, not an argument (SC2) |
| 97 | 1242–1246 | A worked example in the learner's own route | **Built:** `worked_example` with `follows_learner_route` (§9.2). The workbench's step history is the Reader's (RW2b) |
| 98 | 1248–1272 | Three explanation modes | **Built:** verbatim passages (mode 1), the grounded tutor (mode 2), "Explain this with my work" (mode 3, §10.3) |
| 99 | 1282 | Cited passages, version identity and the source/AI distinction in the API | **Built:** SC5, §5.5 |
| 100 | 1286–1307 | Index instructional roles, several per passage, with confidence | **Narrowed:** a positive filter over ingest's hints plus source objects where they exist (§9.2). **Deferred:** an LLM labeller with confidence and several roles per block (§19). Reason: the deterministic hints already cover `exercise`, `worked_example`, `definition`, `theorem`, `figure` and `equation`. The labeller is needed only for the dialogue's roles that have no hint (explanation or intuition, counterexample, prerequisite passage, alternative treatment) and for source-authored contrasts (row 102) |
| 101 | 1309–1322 | Misconception-conditioned retrieval: discrimination and remediation | **Built:** S2 (`discriminate`), S3 (`remediate`), §9.3 |
| 102 | 1326 | Index source-authored contrasts | **Narrowed:** the `contrasts` verdict ranks such passages first for `remediate`. **Deferred:** a stored contrast index, with the labeller (§19) |
| 103 | 1328–1342 | Syntopic retrieval as a first-class operation | **Built:** `compare_sources` (§9.4), callable by the tutor (S4) and the Reader. **Deferred:** stored claim relations (§19) |
| 104 | 1344–1356 | Source-conditioned interactive explanations | **Narrowed:** role-filtered retrieval of equations and figures for RW5. **Deferred:** the tutor offering "make this explorable" (§19; needs RW5) |
| 105 | 1358–1374 | Context-dependent retrieval permissions | **Built:** §5.1. `authoring` restored as internal; `post_attempt` narrowed (T6's reason) |
| 106 | 1376 | A textbook exercise is a poor cold test after an equivalent worked example | **Built:** §5.4 rule 4 |
| 107 | 1378–1380 | Keep generated variants and exposure machinery; a retrieval receipt | **Built:** §5.5, §10.4 |
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
| 401–427 | Index relationships, not only text; keep source, learner and policy layers apart; abstain when evidence is inadequate | **Built:** the layers stay apart (SC1, SC5); "not found in your library" and verification's "none" are first-class outcomes (§9.4) |
| 427 | Symbolic and numerical checks, not only an LLM judge | **Built:** the verifier ladder (§7.3) |
| 820–877 | Search-first library answers organized by role; a claim comparison verified before it enters a trusted graph; personalization that can be turned off | **Built:** role grouping data in hits, `personalized` (§9.2), quote-verified comparison lines. The UI is the Reader's. **Deferred:** the trusted graph of claims (§19) |

---

## 13. Persistence summary

| Migration (from 184, in build order §15; renumbered at merge) | Phase | Table or change | Role |
|---|---|---|---|
| 184 | S0 | `practice_index_proposals` + `caller`, `caller_ref`, `intent` | RECEIPT (unchanged) |
| 185 | S1 | `source_exercise_imports` | WORKFLOW |
| 186 | S3 | `source_comparisons` | WORKFLOW |
| 187 | S2a | `practice_index_proposals.valuation_json` | unchanged |
| 188 | S2b | `source_exercise_imports.need_id` | unchanged |
| 189 | S4 | `source_tool_calls` | RECEIPT |
| 190 | S5 | `retrieval_interventions`; `retrieval_intervention_outcomes` | RAW_LEDGER; DERIVED (one replayer) |

**Vault model:** `PracticeItem.canonical_exercise` (S1), omitted when null.

**Every migration:**
- classifies its tables in `db/table_roles.py`; the DERIVED one gets exactly one replayer;
- upgrades and renames `fixtures/migration_head_<N>/` in rollback mode, updating its README and the five hard-coded paths;
- reruns `db_generate_reference.py` and `db_validate_reference.py` (CLAUDE.md).

**Every new config key** moves the defaults fingerprint (`config/template.py:831`). Content-only phases recompute the latest entry with the note "no scoring, scheduling, projection or serving change". S2b records its own entry under its successor tag.

**Config, `[source_service]`:**
- `enabled` (master);
- per phase: `tutor_offers`, `exercise_arm`, `exercise_verification`, `family_attachment`, `discriminating_search`, `source_first_needs`, `tutor_intents`, `remediation_passages`, `compare`, `tutor_tools`, `interventions`;
- time and prompt bounds: `verify_timeout_seconds` (90), `compare_max_prompt_tokens` (24,000);
- money: `import_max_cost_usd` (0.25), `compare_max_cost_usd` (0.05), `max_daily_cost_usd` (1.00), `llm_price_per_million` (unset: metered routes are skipped).

All are on by default except as D-decisions say.

**Routes** added to `AITask` (`ai/routing.py:22`): `source_solution_match` (S1), `source_compare` (S3), `exercise_discrimination` and `worked_example_equivalence` (S2a). Each gets a routing default and is skipped and labelled on a metered route without a price.

---

## 14. Algorithm successors and kill switches

| Phase | Changes | Successor | Kill switch (off restores) |
|---|---|---|---|
| S0 | Callers and the pick link | None | `tutor_offers` (no request on answers) |
| S1 | Exercise arm, import, ladder, families | None (proposals; learner-authority and owner-run content) | `exercise_arm`, `exercise_verification`, `family_attachment` (Phase 5b's `find_practice`; today's import) |
| S2a | Intents and valuation in `find_practice` | None (proposals) | `discriminating_search` |
| **S2b** | Needs fulfilled from the sources before generation | **Next free `mvp-0.N`** | `source_first_needs` (the generation lane byte-identical) |
| S3 | `find_sources`, `compare_sources`, tutor intents, remediation passages | None (T6's ruling; the reviewer confirms for remediation passages, with the stated fallback) | `tutor_intents`, `remediation_passages`, `compare` |
| S4 | Tool interface and tutor offers | None | `tutor_tools` |
| S5 | Records and report | None | `interventions` |

`source_service.enabled = false` turns every phase off at once: T6, `find_practice`, the tutor and remediation behave exactly as merged (G14).

---

## 15. Build order, sizes and dependencies

| Order | Phase | Builds | Needs (`main` unless noted) | Size |
|---|---|---|---|---|
| 1 | **S0** | `practice_request`, pick link, proposal columns, `AskOverlay` strip, the `instructional` package, its import-linter contract and the `db/stores/source_service.py` store | — | **S** |
| 2 | **S1** | Positive role filter in `search_spans` and a public `effective_hint`; the injected exercise arm; the import split; `content/authoring/source_exercise_import.py` (adapter, ladder, write, attach) and its job; `ops/pf_verify.py`; `attach_to_family`; `canonical_exercise`; harvest | S0 | **L** |
| 3 | **S3** | `instructional/policy.py` (§5); `find_sources` intents, correction refs, `compare_sources`, tutor intent provider, remediation passages | S1's role filter (S3 can start in parallel once it lands) | **M** |
| 4 | **S2a** | Constraints, `open_hypotheses`, `value_candidates` (injected as `valuer`), the public `misconception_discrimination`, exercise discrimination screen, exposure rule 4 | S1 | **M** |
| 5 | **S2b** | Source-first need fulfilment (successor) | S2a | **S–M** |
| 6 | **S4** | Registry, wire models, dispatcher, receipts, tutor `tool_requests`, offers, pinned-span bridge, CLI | S0; S2a and S3 for their tools (tools register as their phases land) | **M** |
| 7 | **S5** | Interventions, outcomes replayer, report, calibration fields | S0–S4 write points | **M** |

S0 ships a learner benefit on its own. S1 and S2a together deliver the owner's core ask: "LearnLoop serves textbook exercises as practice and as probes chosen to separate rival misconceptions". The Reader's RW4a and RW6b can consume each phase as it merges. None of these phases waits for R1, R2, learner-text gaps or DL2. Their adapters feature-detect.

---

## 16. Gates and tests

| # | Gate |
|---|---|
| G1 | **Tools never serve.** After any tool or operation runs, the attempts, evidence, mastery, FSRS, scheduler-state and plan-item tables are unchanged. A proposal reaches practice only through SC1's paths |
| G2 | **Policy from the caller.** No argument can widen a policy. Item-bound callers never receive exercise, solution, linked or answer-reproducing spans. `cold_attempt` returns nothing and refuses every tool. `authoring` is accepted only from S1's verifier and PF. A request naming another item or attempt is refused |
| G3 | **Answers withheld from models.** Results returned to an LLM never contain a fake item's expected answer, rubric, hints, profile answers or solution text. Tutor `reason` and `query` strings pass the answer-leak check |
| G4 | **The exercise arm** returns only exercise regions in the teaching scope, never an imported exercise, never an assessment-lane span |
| G5 | **Import parity.** The Reader's import is unchanged (the split composes to today's output). Stems stay verbatim. Items without `canonical_exercise` serialize byte-identically; `practice_item_hash` is unchanged |
| G6 | **Honest key labels.** `checked` appears only with a passing sympy check; `book_solution` only with a quote-verified, supported solution. An unavailable sandbox never yields `checked`. `checking`, `model_answer` and `disputed` keys are excluded from the value intents and from S2b |
| G7 | **Families.** `attach_to_family` is append-only with undo and crash recovery. `apply_family` is unchanged. An LO mismatch is refused |
| G8 | **Valuation.** No model call. Identical inputs give identical receipts. The stop rule and abstention follow `rank_feasible`. No count cap: a fixture where three candidates clear the stop returns three. Greedy conditional valuation drops a redundant second check |
| G9 | **Exposure rule.** A candidate whose span or solution was exposed, whose family was revealed, or that an `equivalent` worked-example verdict covers, is excluded from `discriminate`, `retention` and S2b, and kept for `practice` |
| G10 | **S2b successor parity.** With `source_first_needs` off, or below the tag, the generation lane and follow-ups are byte-identical on fixture copies; a shadow rebuild shows zero projection deltas |
| G11 | **Remediation.** `remediate` reads correction refs as specified. With `remediation_passages` off or verification unavailable, prescriptions are byte-identical to today's |
| G12 | **Comparison.** Every comparison line's quote is verified in its own passage; failing lines are dropped and listed. The schema has no consensus field. Uncompared sources are listed, not hidden |
| G13 | **Receipts and replay.** Every paid verdict has a `judgment_ledger` row and a model-call receipt. Every tool request from a model or an external agent has its request row and, once run, its run row in `source_tool_calls`. A rebuild makes zero model and embedding calls, and `retrieval_intervention_outcomes` rebuilds deterministically from one replayer |
| G14 | **Kill switches.** Each switch, and `source_service.enabled`, restores the previous behaviour exactly (fixture-copy parity) |
| G15 | **Spend.** Every batch command has `--dry-run` and honours its caps. Metered routes without a price are skipped and labelled. Codex receipts are `estimated_only` |
| G16 | **Mobile.** New RPCs (`import_source_exercise`, `get_source_exercise_import`, `run_source_tool`, `find_sources`, `compare_sources`) and the extended ones (`find_practice`, `record_practice_usage`, `plan_learner_pick`, `ask_tutor_question`) are pinned desktop-only in `tests/test_mobile_allowlist.py` |
| G17 | **Layering.** A new import-linter contract forbids the domain packages, `learnloop.practice_index` and `learnloop.source_retrieval` from importing `learnloop.instructional`, and forbids `learnloop.instructional` from importing `learnloop.daily_plan`. `uv run lint-imports --no-cache` passes, and so does `tests/test_architecture.py`: no private cross-package names, SQL writes only in registered stores, no new frozen-inventory edges |
| G18 | **Migrations.** Every new table is classified; the DERIVED one has exactly one replayer; the head fixture and references are regenerated |

Every phase also runs the full suite (`uv sync --extra dev --extra mobile`, then `uv run pytest -n auto`, with `TMPDIR` set to the worktree's `fixtures-local/tmp`), the durability lane where it adds a migration (`uv run pytest -m durability`), `lint-imports`, and the frontend checks when it touches the app (`npm run typecheck && npm test`).

---

## 17. Evaluation: retrieval quality and instructional effect, separately (L1421–1423)

- **Retrieval quality.** The existing harnesses, with LLM labels in two passes and agreement reported. Eval models are Claude Haiku 5.5 or GPT-6 Luna via OpenRouter, or the ChatGPT-plan route. Owner labels are optional.
  - **The exercise arm:** held-out requests over the owner's textbook copies (`linear_algebra`, `probability`) in the Phase 5b evaluation (`learnloop eval practice-index`, `cli/practice_index.py:286`). Recall@10 and nDCG@10 for items only against both kinds, on copies of the textbook vaults (the owner's live vaults are never evaluated in place).
  - **Intents:** a per-intent query set in the T6 harness (`learnloop embeddings compare --suite source_retrieval`, whose systems already include `keyword`, `meaning`, `hybrid` and `hybrid_rewrite`, `cli/embeddings.py:181`), with verification as one more condition, so BM25 alone, hybrid and verified retrieval stay separate conditions, as the dialogue asks.
  - **The verifier ladder:** on imported exercises whose book solution exists, the rate at which rungs 2 and 2′ agree with rung 1; per source, the disputed rate.
- **Instructional effect.** S5's report: `R_next` and `R_cold` by intent and kind, and the calibration fields (§11.4). These are associations until randomization exists (§19).
- **Paid runs** happen only on backup-API copies under `fixtures-local/`. They run dry first, inside caps, with every call and its cost recorded in the phase's review file.

---

## 18. Decisions: recommended defaults (accepted unless the owner overrides at a checkpoint)

| # | Decision | Recommended default |
|---|---|---|
| D1 | Interactive import: check before showing? | Check inside a 90 s box. If the box runs out, serve the item labelled "being checked" and finish the check in the background; a later disagreement marks the key `disputed` |
| D2 | Should unchecked or disputed keys still certify? | No change in v1: graded as imported exercises are today, labelled. A later successor decides on S1's report |
| D3 | S2b: successor or content change? | Successor (§8.5) |
| D4 | Remediation passages in the repair overlay | Live behind `remediation_passages`, no successor (T6's ruling), confirmed by the S3 reviewer, with the stated fallback |
| D5 | Running the tutor's tool requests | Eager for `find_practice` and `find_sources`; lazy (on tap) for `compare_sources` |
| D6 | Routes | The fast route (ChatGPT-plan) for interactive judges (`practice_rerank`, `source_rerank`, `source_compare`); Codex for batch work (verification, harvest, screening); eval roles on Haiku 5.5 or GPT-6 Luna |
| D7 | Harvesting source exercises | An owner-run command with `--dry-run` and caps. Automatic background harvesting deferred (§19) |
| D8 | Router trigger | Supersede §15.3's: R2 live and S4 merged (§10.6) |
| D9 | Sources in a comparison | No source cap; a prompt-token bound, with the rest listed |
| D10 | Equivalent-worked-example rule | The listwise judge over exposed worked examples (§5.4), rather than exact-span exposure alone |
| D11 | Personalization in `remediate` and `alternative` | On, with an off toggle for callers |
| D12 | Spend | `max_daily_cost_usd` $1.00 metered across the track; Codex `estimated_only` |
| D13 | Where the canonical exercise lives | A typed optional field on `PracticeItem`, rather than a provenance convention, so PF variants can carry `variant_of` |
| D14 | Worked examples as practice candidates | No: they are passages (§7.1) |

---

## 19. Deferred, with triggers

| Deferred | Revisit when |
|---|---|
| **Router R2 wiring** and the router choosing material with the action (L1406) | R2 is merged and live, and S4 has merged (§10.6). Joint choice: once R3's replay shows block-level gains (router §13) |
| **An LLM instructional-role labeller** (counterexample, contrast, intuition, prerequisite, alternative treatment; several roles per block with confidence) and a **source-authored contrast index** | S3's report shows that `remediate` or `alternative` verification returns "none" for most targets while a role-agnostic search was used, or the owner points to passages S3 missed, or the Reader spec's own labeller trigger fires (its §17) |
| **Stored cross-source claim relations** (`source_object_relations` proposals from comparisons) | The Reader's compare UI ships a "keep this comparison" action |
| **Page-image retrieval** | A multimodal labeller rematch (T6 review §9 question 4) shows page images beat Marker text on the owner's PDFs; B4 found the opposite (`page_image_default = false`) |
| **Source exercises as formal probe instruments** (compiled conditionals, probe episodes) | S5's calibration fields show that the authored-profile predictions of served source exercises are calibrated (§11.4 item 1) |
| **Randomized choice between equally valued interventions** (a registered randomization design, the cue-holdout pattern) and a **learned per-learner intervention preference** (L1404) | S5's report shows comparable interventions served for the same facet class with enough overlap to estimate a difference, and the owner reads it. The learned preference also needs R3's replay infrastructure |
| **Tutor-initiated explorable figures** (L1344–1356) | Reader RW5 has merged |
| **Automatic background harvesting** | Usage signals show learners pick source exercises from proposals often (the trigger the Reader spec's §17 gives "follow-ups from textbook exercises automatically") |
| **An MCP or OS-level instructional service** | The Reader spec's trigger for its learning service |
| **Cross-LO candidates in the follow-up chooser** | S5 shows S2b's source-first fulfilment closes needs and its checks resolve hypotheses |
| **Source-first fulfilment on the tutor's promotion path** (`tutor/promotions.py:741`, through an injected callable) | S2b has merged and its report shows source exercises fulfilling needs on the two adapter paths |
| **Cross-learner, data-driven hints** | Not applicable at n=1 (dropped, as the coverage audit recommends) |

---

## 20. Cross-spec notes (record when each phase merges)

- **Reader workbench spec.**
  - `find_sources` is owned here. The Reader's §7.2 signature is a subset (`intent` defaults to `explain`). Its three policies are kept, `authoring` is internal and `post_attempt` is narrowed as the Reader spec already did.
  - The Reader's compare calls `compare_sources`. The Reader's organizer route stays the Reader's.
  - RW4b's fallback becomes S1's arm. Any RW4c the Reader revision adds is UI over S1 and S2.
  - RW6b's valuation is `instructional/valuation.py:value_candidates` (§8.3), built once, by whichever phase lands first.
  - RW6b's open questions read the same `open_hypotheses` adapter.
  - The Reader spec's §17 deferral "router querying the source vault as a tool" now points to §10.6 here.
- **Router spec §15.3.** A note at its trigger points here: the tool interface is built by S4, and the trigger is superseded (§10.6).
- **Embedding consumers §5.9.** Its consumer list gains the tutor (S0, S4), learner picks (S0), needs (S2b) and the source-exercise arm (S1). Its bar (dossiers must beat direct item search) is unchanged.
- **Daily loop.** DL3's "Practice on…" box is S0's RPC with `caller = plan`. DL2's dated branch reads `due_hint` for RW6b's checks (Reader spec request, unchanged).
- **Learner-text gaps.** The "not what I asked" text (§6.3) and the "doesn't connect" text on passage offers become one source adapter each once the branch has merged.
- **Decision value.** S5's outcome states are §4.3's. `evsi/calibration` owns any change to the heuristic constants (§11.4).

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
Do not build Reader UI. Do not change grading, evidence or certification semantics. If your phase
changes what is served and the spec says "no successor", stop and ask the reviewer; S2b is a
successor (next free mvp-0.N at merge).

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
