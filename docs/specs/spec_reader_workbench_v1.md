# Reader workbench: inquiry, worked problems, passage cues, syntopic reading and loop closure (v1)

**Status:** draft for owner review (2026-10-12), **revised after the integration review the same day** (§20). The review checked every phase against the code on `main` at `68213d96` and against the in-flight branches. It then split each phase into a small first slice that ships a learner benefit on its own and a second slice that adds the model work. It also folded in a Codex reviewer's high-ROI list (§20.3). **Owner decision, 2026-10-12 (§20.7):** cold follow-ups have no count cap; the existing EIG/EVSI machinery chooses, numbers and dates them (§9.3). A coverage audit of the source dialogue against this spec is `docs/reviews/reader-dialogue-coverage.md`.

**Source:** `docs/brainstorming/Improving Reader's design.md` (the owner's design dialogue, committed with this spec). Its three rounds:
1. the agent's brainstorm: intentions, textbook pain points, learning loops, features A–G, the workbench layout, retrieval;
2. the owner's reply: interactive figures from selections, syntopic reading, misconception-aware reading, scaffolding that scales with prior knowledge and struggle, "hints I couldn't reconcile with my own work", natural-language questions to the library with an optional tutor, and session summaries feeding the router, then a short unfamiliar cold problem;
3. the owner's proposal that canonical sources become a natural-language retrieval tool for the router and the tutor.

**Owner preferences in force** (from `daily_loop_frictionless_defaults.md`, `implementation_goal.md` and the owner decisions recorded across the specs):
- **Honest labels, generous defaults.** Live changes go behind kill switches. There are no shadow stages by default.
- **LLM judgment over hand-picked constants.** Where a choice is a judgment (which help to offer first, which passage deserves a cue), an LLM or the Decider makes it from typed learner state. Constants appear only as caps.
- **Learner text over skip buttons.** The precedent is "I'm stuck" (`docs/reviews/stuck-prompt.md`): a free-text box replaces a bare skip wherever the text can be used.
- **Embeddings shortlist, judges decide** (`spec_embedding_consumers_v1.md` §1, R1–R6). No cosine cutoff is hand-set and no calibrator is built.
- **Your questions and hints are the placement signal** (frictionless S5): they show where the learner is shaky, and asking never lowers the record.
- **Codex on the owner's ChatGPT subscription** may run every paid LLM role, recorded as `estimated_only`. The Decider is `perplexity/pplx-decider-v1.1-27b` on OpenRouter (router R0, merged). The ChatGPT-plan provider (`providers/chatgpt-plan`, built, waiting to merge) is the fast route for short structured calls.

**Relationship to other specs:**

| Spec | Relationship |
|---|---|
| `spec_p3_reader_integration.md` | The Reader's contracts (render views, anchors, capture, salience firewall, restoration). This spec keeps every §1.1 invariant. It implements P3 §5.4's inquiry thread without a projection table, and lifts P3 §1.3's "no syntopic UI" exclusion under P3 §7's source-local rules |
| `spec_reader_quick_check_producer.md` | Its producer gains a passage scope and two question styles (RW1): the reconnect check, "let me try the next step" and "why does this step work" |
| `spec_daily_loop_v1.md` | Consumed, never duplicated: DL1's reading blocks (§6.10) and learner-pick blocks, DL2's "Check once" (§5.2), DL3's "Practice on…" (§6.9), DL4's pre-questions (which share the quick-check producer). RW6b needs DL2 |
| `spec_embedding_consumers_v1.md` | T6 (§9, merged) is the only retrieval substrate: `search_spans`, `teaching_scope`, `TutorSpanProvider`, `verify_spans`. Phase 5b's shared listwise judge (`practice_index/listwise.py`) is the only judge mechanism for cues, the organizer and the follow-up pick. `find_practice` (§5.9) proposes practice. PF supplies the sandbox and its verified-check pattern |
| `spec_action_router_v1.md` | The Reader's in-session help is not the router (two timescales). RW6b adds a reader section to `LearnerStateCardV1` (§4). RW4's `find_sources` is the tool that router §15.3 calls `search_sources` (§18) |
| `spec_blind_grading_diagnosis_split_v1.md` | The grader stays blind. The diagnoser sees the workbench trace of the current attempt only. Cue targets read the diagnoser's overlay, never raw grader rows (§3.4) |
| `spec_learner_field_v1.md` | Workbench assistance reaches the field through `hints_used` and `primed` on the attempt row, which the field already reads. No new signal source in v1 (§5.6) |
| `implementation_handoffs.md` §4 | The learner-text-gaps pipeline is the dialogue's "observation compiler". Reader questions already reach it as tutor questions; RW2b adds one source adapter for workbench stuck text. No second compiler |

**Citation convention.** Every `file:line` was checked on `main` at `68213d96` (migration head 179, latest algorithm `mvp-0.13`). Python paths are relative to `src/`, frontend paths to `apps/learnloop-tauri/src/`, migrations to the repo root. Unmerged work is named by branch.

---

## 0. Thesis

The dialogue's sentence is the design rule:

> Does this interaction help the learner return to the thing they wanted to accomplish, more capable than when they encountered the obstacle?

The Reader today is a good source viewer with an Ask rail, capture presets, quick checks and exercise import (§3). The features are separate rooms. The learner's real loops cross them:
- **encounter → question → resolution → resume**: the Ask history is flat, so one question that leads to a prerequisite loses the original question;
- **attempt → error → diagnosis → repair → retry**: an imported exercise becomes a practice item, but working it happens elsewhere, and hints don't refer to the learner's own work. The owner's own pain point: "when I would be given a hint I wouldn't be able to reconcile with the work I have already done";
- **read → notice → check**: the Guide already knows which passages touch a recent misunderstanding, but says so only in a side list;
- **question → sources → explanation**: library search finds passages but can't say what each source contributes, or how two books differ;
- **session → memory → later check**: nothing brings a returning learner back to where they were, nothing summarizes a reading session for the router, and nothing turns assisted understanding into a later independent check.

**The Reader becomes a source-grounded workbench.** Reading still looks like reading. When the learner investigates, the Ask rail branches and reconnects. When the learner works a problem, the source stays beside a step-by-step workspace that survives navigation and restarts, and whose hints start from the learner's own steps. Passages that touch something the learner got wrong before carry a quiet margin mark. A question to the library returns the passages, organized by what each source contributes, with the tutor one click away. When the learner comes back, the Reader shows where they were and what is still open; LearnLoop gives the router a summary and schedules short unfamiliar problems for later — as many as are worth the learner's time, chosen by how much each would tell LearnLoop (§9.3).

Four rules carry over from the dialogue:
1. **Preserve the learner's evolving reasoning,** not only what was asked and whether the final answer was right.
2. **Help is a deliberate, recorded quantity.** The learner can always get more. What LearnLoop offers first adapts to prior knowledge and struggle, and every piece of help is recorded as assistance, so assisted success is never mistaken for independent competence.
3. **Sources keep their identity.** What a source claims, what LearnLoop infers and what the learner believes stay separate. Cross-source reading preserves differences instead of fusing them into a consensus.
4. **No intervention is a legitimate outcome.** Cues are marks in the margin, never interruptions.

---

## 1. Scope

**In scope (v1).** Each phase has a first slice (**a**) that ships on its own, mostly from existing parts, and a second slice (**b**) that adds the new model work. The order is in §13.

- **RW1a. Inquiry.** Port the unmerged `origin/feat/reader-clarification-branches` (branching Ask); split the rail into components; inquiry status on the existing outstanding-question queue; breadcrumbs and "back to where I was"; a reconnect line with a passage-scoped check; the reader report's workflow funnel.
- **RW1b. Intent box and active reading.** A selection intent box routed by the Decider (the palette stays one key away); "Let me try the next step" and "Why does this step work?" on a selected derivation or worked example.
- **RW2a. The workbench as a resumable scratchpad.** Step-by-step work beside the source, saved as it is typed, reopened by "Resume this problem" after navigation or restart; Submit through the ordinary attempt path with the source-visible rule (§5.4). No model calls of its own.
- **RW2b. Checks and adaptive help.** "Check my work" (first questionable step), the help ladder with the reconciliation contract, the adaptive first offer, narrow symbolic checks, "this doesn't connect to my work" feedback on every hint, stuck text into the learner-text-gaps pipeline.
- **RW3a. Margin cues from the Guide.** The Guide's existing `recent_misunderstanding` passages shown as restrained margin marks, with the misconception read from the diagnoser's overlay.
- **RW3b. Discovered cues.** New passage links found per open hypothesis, named gap or demonstrated facet through T6 retrieval and a listwise judge; a logged holdout.
- **RW4a. Library questions and source comparison.** "Ask" in library search: passages grouped by source and role with a one-line contribution each, the tutor on request; pin up to four passages from different sources and compare them; "Practice this question" through `find_practice`; the `find_sources` function that router §15.3 will call.
- **RW4b. Exercises from my sources.** When `find_practice` finds nothing, find candidate exercise passages in the learner's sources and hand the chosen one to the existing exercise import.
- **RW5. Explorable figures (narrowed pilot).** "Make this explorable" on a selected equation or figure: a declarative, verified figure spec drawn by a trusted renderer with two panel types, with an optional prediction.
- **RW6a. "Last time here".** A deterministic recap on returning to a source: last position, open inquiries, unfinished problems, missed predictions, with resume links.
- **RW6b. Digest, router card and cold follow-ups.** An optional narrative over the recap, reader activity in the router's learner-state card, and cold follow-ups served through DL2's "Check once". Follow-ups have no count cap: the existing value-of-information machinery (probe EIG over the learner's open hypotheses, `scheduling/evsi.py` for the next decision) chooses, numbers and dates them, and the daily plan's finite minutes and the spend caps bound them (§9.3; owner decision 2026-10-12, §20.7).

**Deferred, with triggers in §17:**
- **goal-aware reading paths** (the first draft's RW7; §10 keeps its design);
- source-claim extraction and persistent cross-source relations;
- an LLM role labeller over every source block;
- generated practice for follow-ups when nothing fits;
- the general figure language (integrals, PMF bars, more panels);
- the router querying the source vault as a tool (router §15.3 keeps its own trigger; RW4a builds the function it will call);
- an OS-level or MCP learning service, and browser or editor capture;
- generated-code figures and their isolated rendering surface;
- page-image (visual) retrieval;
- learned cue and hint policies;
- full solution graphs with alternative branches;
- a CAS calculator tool in the workbench;
- photo-of-work input to the workbench (until DL4's transcription route lands);
- workbench and figures on video transcripts;
- interaction signals from abandoned workbench sessions and mid-work stuck steps.

---

## 2. Standing constraints

- **W1. Reading and help are not evidence.** P3 invariant 6 holds: dwell, highlights, asks, cue taps, figure play, inquiry status, recaps and digests never enter mastery, posterior, certification or FSRS. The only evidence a workbench session produces is its final submitted attempt, graded by the blind grader and carrying the assistance it recorded (§5.4).
- **W2. Honest labels.** Every surface distinguishes source-authored, AI-written and learner-written content (P3 invariant 9). Model judgments are labelled as such. "Checked" or "verified" appears only when a non-LLM check (a sandboxed sympy check, an exact key, a quote match) passed. A cue never says the learner *is* confused, only that a passage connects to something they worked on.
- **W3. Generous defaults, live behind kill switches.** Every phase ships on by default with its switch. No step is added to protect a model.
- **W4. LLM judgment and value of information over constants.** First-offer help level and cue selection are model judgments over typed learner state. Follow-ups are valued by the existing EIG and EVSI machinery (§9.3); a model judges only whether an item tests the capability. Numbers in this spec are caps on money, time or display, never thresholds that decide learning. There is no count cap on follow-ups (§20.7).
- **W5. Learner text over skip buttons.** The intent box, "what's still unclear?", "I'm stuck" in the workbench, "this doesn't connect to my work" on a hint, and "not relevant, because…" on cues take free text. A one-tap path still exists (an empty box is allowed), as with "I'm stuck".
- **W6. Embeddings shortlist, judges decide.** No embedding score alone creates a cue, a role or a match (R1). Shortlists are top-k; a judge decides everything shown.
- **W7. Cold means no source cue.** P3 invariant 10 and `find_sources`' policies (§7.2): a cold attempt gets no source, hint, tutor or figure; opening one ends cold status. A source-visible attempt never certifies.
- **W8. Grading stays learner-blind.** The grader sees the final answer as today. Steps, hints, checks and learner history never enter `BlindGradingContext`.
- **W9. Replay makes zero model and embedding calls.** Every paid output (checks, hints, cues, organizer lines, figures, digests) is persisted and never regenerated on rebuild.
- **W10. Spend controls.** Every paid step uses the Phase 1 framework (`learnloop/ai/spend.py`): per-route caps, `--dry-run` on every batch command, receipts. Codex is `estimated_only`. Every LLM, Decider, verifier or learner-card verdict appends to `judgment_ledger`.
- **W11. Agency.** The learner can always ask for more help, turn cues off, hide the source before working, and undo every automatic action.
- **W12. The reading hot path never waits for a model** (P3 invariant 1). Cue links and organizer lines are computed in the background or on request and appear when ready.
- **W13. Reuse before building.** One retrieval substrate (T6), one listwise judge (`practice_index/listwise.judge_listwise`), one practice-proposal function (`find_practice`), one question producer (the quick-check producer), one learner-text compiler (learner-text gaps), one scheduled-check mechanism (DL2's "Check once"), one value-of-information machinery (probe EIG in `diagnosis/probe_families.py` and `diagnosis/probes.py`, EVSI in `scheduling/evsi.py`). A phase that needs a second one stops and records why.

---

## 3. Code truth (audited 2026-10-12 on `main` at `68213d96`)

### 3.1 The Reader today

| Capability | Where | What it does now |
|---|---|---|
| Rendering and anchors | `learnloop/reader/source_render_views.py`, `annotations.py`, `span_view.py` | Marker markdown and KaTeX views, block crosswalk, sub-block anchors with reanchoring, original-region fallback |
| Rail | `screens/ReaderScreen.tsx` (3,991 lines in one component; `screens/reader/` holds only small helpers) | Guide, Ask and Notes tabs beside the source |
| Capture palette | `screens/ReaderScreen.tsx` | Nine presets in three groups: background requests (research, worked example, explain differently, why it matters), "Remember later" (test me later, help me remember, connect it), Mark (confusing, not worth remembering) |
| Ask | `learnloop/reader/reader_dialogue.py:412` (`ask`), `:610` (`ask_history`); `learnloop/tutor/tutor_qa.py:292` (`ask_question`) | Span-grounded tutor answers in the `reader` context, with answer modes `answer_directly`, `help_me_reason`, `ask_me_first`. **History is flat:** P3 §5.4's inquiry thread was never built |
| Outstanding questions | `migrations/102_question_resolution.sql:9`; `components/QuestionQueue.tsx` | Every tutor question carries a learner-owned `resolution` (`open` \| `resolved` \| `dismissed`) and shows on Today until resolved. The RPC sets `resolved` or `dismissed`; there is no reopen |
| Guide | `learnloop/reader/reader_guidance.py:292` (`build_guide_plan`), `:362` (`_passages_by_section`), `:130` (`_learner_signal`) | Section checks and suggested passages, each with `span_id`, `quote`, `reason`, `learning_object_id` and `learner_signal`. A passage cited by an item whose LO has an active error gets "Revisit this to resolve: <statement>" (`recent_misunderstanding`), shown only in the rail. **See §3.4 for a defect under the split** |
| Quick checks | `learnloop/reader/reader_quick_check.py:93` (`author_quick_check`); `migrations/105_reader_authored_questions.sql` | One AI-authored, span-grounded, formative question per section (`section_id NOT NULL`; reuse is "the newest row for the section"), escalatable to a practice item |
| Exercise import | `learnloop/content/authoring/exercise_authoring.py:241` (`import_exercises`) | Selected textbook exercises become real practice items: verbatim stem, AI-completed answer, rubric, facets and progressive hints. **Working them happens on the practice screen, away from the source** |
| Reading questions | `reader_dialogue.py:683` (`administer_reading_question`), `:773` (`submit_reading_question`) | An owner-placed reading question opens an instructional administration and records the answer as an interaction event with `hint_equivalent: true`. **It is not an attempt: nothing is graded or diagnosed** |
| Section progress | `learnloop/reader/reader_progression.py`; `reader.mark_section_progress` | Section completion triggers practice generation for `as_you_read` sources |
| Source objects | `learnloop/reader/source_objects.py`; `migrations/094_source_objects.sql` | Per-source claims, definitions, worked examples and problems, and relations, all proposals. No UI reads the relations |
| Video | `reader.watch_plan` | Transcript sources open in the Reader |

### 3.2 Adjacent systems on `main` that this builds on

| System | Where | Used by |
|---|---|---|
| T6 hybrid retrieval: FTS5 BM25 + dense + rewrite, fused by RRF | `learnloop/source_retrieval/search.py:126` (`search_spans`), `library.py:117` (`search_library`) | RW1b (next-step context), RW3b, RW4a, RW4b |
| T6 scopes and exclusions: teaching scope; in item-bound contexts (practice, feedback) every exercise and solution block (by ingest `role_hint`) and every passage linked to the item is dropped, and spans reproducing the expected answer are withheld | `source_retrieval/corpus.py:450` (`teaching_scope`), `:327` (`_role_hint_exclusions`), `:158`; `source_retrieval/tutor.py:70` (`TutorSpanProvider`); `tutor_qa.py:864` (`span_leaks_expected`), `:816` (`answer_leaks_expected`) | RW2b bridging, RW4a policies |
| Deterministic block roles from ingest: `definition`, `theorem`, `proof`, `worked_example`, `exercise`, `solution`, `summary`, `reference`, `equation`, `figure`, `table`, `ordinary_prose` | `learnloop/ingest/block_roles.py:124` (`classify_block_role`); `source_blocks.role_hint` (`migrations/032_source_layer.sql:75`) | RW4a grouping, RW4b exercise search, RW5 candidates |
| **The shared listwise judge** (skip check, request identity, ledger-served cache, one capped call plus retry, append-only verdicts with pick ranks) | `learnloop/practice_index/listwise.py:149` (`judge_listwise`); used by `find_practice` and `verify_spans` (`source_retrieval/verify.py:156`) | RW3b cue judge, RW4a organizer and compare, RW6b follow-up pick |
| Practice index: `find_practice` (proposes, never serves) with exact `PracticeConstraints` (LOs, subjects, facets, modes, excluded items, difficulty) | `learnloop/practice_index/retrieval.py:727`, `:111` | RW3 "Check me", RW4a "Practice this question", RW6b follow-ups |
| PF-b: verified generation, bubblewrap sandbox with sympy, the LLM-written check with negative controls | `learnloop/content/authoring/pf_sandbox.py:120` (`run_sandboxed_python`); `ops/pf_generation.py` | RW2b symbolic checks, RW5 verification |
| Blind grader and history-aware diagnoser (Slice 1 M2), PF-c unassessed rule | `learnloop/attempts/blind_grading.py`; `learnloop/diagnosis/split/` | RW2a/b submission and diagnosis |
| Attempt submission: `hints_used` (folded with tutor-question hint equivalents, then capped by `max_useful_hints`), `primed`, `declared_stuck`, `answer_confidence` (logged only), `entry_surface` (free text); needs an open practice session | `learnloop_sidecar/handlers/practice.py:101`, `:524`, `:556`–`:561`, `:1143`; `handlers/sessions.py:44` (`start_session`) | RW2a/b |
| Assistance semantics: any `hints_used > 0` or `primed` makes the attempt assisted (certifies nothing; FSRS still fed unless primed); primed non-diagnostic attempts are `repair_activity` | `learnloop/diagnosis/causal_activity_policy.py:145`, `:182` | RW2 mapping |
| Reveal ledger kinds `tutor_answer`, `repair_display`, `guided_redo`, `source_review`, `answer_display` | `learnloop/attempts/reveal_ledger.py:37` | RW2b hint reveals |
| Guided redo | `learnloop/diagnosis/guided_redo.py` | RW2 after a wrong submission |
| "I'm stuck" (`mvp-0.13`) | `learnloop/attempts/stuck.py:271`; `field/signals.py:327` | RW2 stuck box |
| T1's matcher (pairwise `same` / `different` / `unsure`) and recurrence groups | `learnloop/matching/` (`kinds.py`); `learnloop/substrate/recurrence_groups.py` | RW3 targets (groups), not the cue judge (§6.2) |
| The Decider client (R0); `DECIDER_TASKS` | `ai/providers/decider.py`; `ai/decisions.py` (`ChoiceQuestion`); `ai/routing.py:77` | RW1b intent routing, RW2b first offer |
| Commitments with versions, including `due_hint` | `migrations/072_commitments.sql:78`; `learnloop/curriculum/commitments.py` | RW6b follow-ups |
| **Value of information: probe EIG** (live). Mutual information over a locked hypothesis set, an information rate per expected second, greedy conditional EIG for a block of several probes, and per-facet EIG over `facet_uncertainty.hypothesis_marginal`, which the post-attempt follow-up slate already uses together with a misconception-discrimination check | `diagnosis/probe_families.py:467` (`instrument_expected_information_gain`), `:536` (predictive), `:621` (`information_rate`); `diagnosis/probe_episodes.py:818` (`eligible_instruments`), `:1386` (`plan_precommitted_block`), `:1576` (`episode_posterior`); `diagnosis/probes.py:786` (`facet_expected_information_gain`); `diagnosis/followups.py:1532` (`_choose_intervention_item`), `:1482` (`_misconception_discrimination`) | RW6b valuation (§9.3). Audited on `main` at `19798a0c` (2026-10-12, DL1 merged) |
| **Value of information: EVSI** (built, no live consumer yet). EVSI in minutes over a credible set; rank = LCB / (minutes + burden); stop when LCB ≤ λ·minutes + burden; `abstain` when the credible set or the stress test flips the winner. The loss table is wasted learner-minutes per hypothesis and action. The robust EIG-to-minutes conversion serves where no loss table exists. Today it runs only in shadow (`causal_diagnostic_selector.py:300`, called from `causal_orchestrator.py:1493`); `staged_policy.DiagnosticSelector` (`:351`) is never constructed. Live causal probes use the proxy `causal_probe_coherence.decide_probe` (`:413`) | `scheduling/evsi.py:124`, `:199` (`robust_evsi`), `:366` (`rank_feasible`); `scheduling/action_loss.py:235` (`build_loss_table`); `diagnosis/robust_composition.py:353` (`evaluate_selection`), constants `:44`–`:55` (λ = 1, burden 0, 60 minutes per nat, all labelled heuristic) | RW6b valuation and stop rule (§9.3): its first live consumer |
| Hypothesis state the valuation reads | `hypothesis_sets` (`migrations/001_initial.sql:276`) with the posterior replayed from `probe_observations` (`028_probe_episodes.sql:94`); `causal_hypotheses` (`118_causal_attribution_p1.sql:5`); rival causes per attempt in `unresolved_cause_factors.candidate_causes_json` (`034_assessment_contract_snapshots.sql:32`); `facet_uncertainty` (`012_facet_diagnostic_state.sql:1`) | RW6b (§9.3) |
| DL1's finite plan (`mvp-0.14`, on `main` at `19798a0c`): remembered minutes, `split_v1` (maintain ≤ 60% of the minutes), scheduled checks first in the maintain lane, mid-plan follow-ups only within the plan's minutes. `ScheduledCheck.kind` already names `check_once`, with no provider until DL2 | `daily_plan/engine.py:286` (`remembered_minutes`), `:1644` (`_insert_followups`); `daily_plan/split.py:121`; `daily_plan/lanes.py:74`; `daily_plan/chooser.py:36` | RW6b: what bounds follow-ups is minutes, not a count |
| Spend framework: a per-command budget, per-route caps; no global daily dollar cap exists | `ai/spend.py:86` (`SpendCaps`) | Every paid route here (W10) |
| Live markdown and math editing | `render/LiveMarkdownEditor.tsx`, `render/MarkdownMath.tsx` | RW2a step editor |
| Practice-screen draft checkpointing and restore | `screens/PracticeScreen.tsx:306`–`:330`; `save_practice_draft` | RW2a lifecycle pattern |

### 3.3 Unmerged work this spec depends on (2026-10-12)

| Branch | State | What this spec uses |
|---|---|---|
| `origin/feat/reader-clarification-branches` (`cf2cbe77`, 2026-10-08) | Built on PR #5, not merged | Branching Ask: explicit parents on the `reader_answer_submitted` payload, the branch tree (`screens/reader/ReaderAskBranches.tsx`), ancestor-only prompts. 8 backend tests (`tests/test_reader_branches.py`) and 9 frontend tests. No migration. `git merge-tree` against `main`: conflicts in `reader/reader_dialogue.py`, `tutor/tutor_qa.py` and `learnloop_sidecar/handlers/reader.py`; `ReaderScreen.tsx` and `api/dto.ts` merge cleanly |
| `merge/dl1` (`daily-loop/dl1`) | **Merged** to `main` as `19798a0c` (`mvp-0.14`) later on 2026-10-12 | Learner-pick blocks, reading blocks (§6.10), the plan's finite minutes that bound follow-ups (§9.3). DL1 touches no Reader file |
| DL2 | Not built on any branch | "Check once" (§5.2) and effective due (§5.3). RW6b's follow-ups need it; DL1's `ScheduledCheck` already reserves the `check_once` kind (`daily_plan/lanes.py:74`) |
| DL3 | Not built | "Practice on…" (§6.9); RW4a's "Practice this question" is the same `find_practice` call |
| `router/r1` | Built; `mvp-0.15` at merge (`merge/r1` prepared from `19798a0c`) | `router_decisions`, which logs each candidate's `probe_eig` and `evsi_assignment` but values nothing (`router/decisions.py:174`, `:441` on the branch); RW6b's valuation receipt uses the same field names (§9.3). R2 (not built) renders the card section RW6b adds and values pending follow-ups as block candidates |
| `learner/text-gaps` | Built and reviewed; carries its own successor (labelled `mvp-0.13` on the branch, relabelled at merge) | `diagnosis/text_gaps/` (`LearnerText` sources, `StuckTextSource`, `named_gaps_for_card()`). Reader questions are already a source (`tutor_question_text` reads `context = 'reader'`). Touches `tutor_qa.py` (+28 lines) and `PracticeScreen.tsx` (+13) |
| `providers/chatgpt-plan` | Built and gated; the owner's live sign-in pending | Profile type `chatgpt_plan`: one HTTPS structured call, no tools, isolated turn; `learnloop ai latency` |
| `facets/identity` | Built | Nothing directly |

**Successor numbering.** `SUCCESSOR_CHAIN` (`algorithm_versions.py:99`) is linear; `mvp-0.13` is the latest on `main`. DL1 takes `mvp-0.14` and R1 `mvp-0.15` at their merges; learner-text gaps takes the next one at its merge. New vaults start at `LATEST_ALGORITHM_VERSION`. This spec, as revised, needs **no** successor (§12). If a phase agent or its reviewer finds one is needed, it takes the next free `mvp-0.N` tag at its merge, never a named tag.

### 3.4 Corrections to the first draft (found by the integration review)

1. **The Guide misses the diagnoser's statements under the split.** `_learner_signal` reads `repository.active_errors_by_learning_object` (`db/repositories.py:1966`), which selects raw `error_events`. Since Slice 1 M2, a blind-graded attempt's events carry only the grader's localization; the misconception statement is laid over from the live diagnosis by `error_events_for_attempt` (`:1978`). On split vaults the Guide therefore falls back to the error type ("Revisit this to resolve: conceptual error"). RW3a fixes this by reading the overlay.
2. **Source blocks already have instructional roles.** Ingest assigns `role_hint` deterministically, and T6 already excludes `exercise` and `solution` blocks in practice and feedback contexts. The first draft's LLM role index over every section duplicated this; it is cut (§7.1).
3. **A source-visible reading question is not an attempt.** `administer_reading_question` plus `submit_reading_question` writes an interaction event; no grader or diagnoser runs. A Reader workbench submission must go through `submit_attempt` instead (§5.4).
4. **New interaction-event kinds need a table rebuild.** `interaction_events.kind` has a CHECK, last widened by migration 103 with a full temp-then-rename rebuild. This spec adds **no** event kind; it uses existing kinds with a payload `event` field (§4.4).
5. **`passage_gap` and `same_claim` as T1 match kinds do not fit.** T1's judge answers `same` / `different` / `unsure` about a pair. A cue is a relevance judgment of passages for a target, which is what T6's listwise judge already does. RW3b uses T6 plus `judge_listwise` (§6.2).
6. **No LaTeX parser is installed.** sympy 1.14 is a dependency, but neither `lark` nor `antlr4` is, so `parse_latex` is unavailable. Symbolic checks use PF's pattern (the model writes a sympy check, the sandbox runs it with a negative control) on a narrow set of transformations (§5.3).
7. **`find_practice` cannot express "unseen" or "not a family revealed today".** `PracticeConstraints` gains two exact filters for RW6b (§9.3).
8. **`search_sources` is taken.** `learnloop/reader/source_search.py:42` already defines `search_sources` (the legacy keyword search). The new function stays `find_sources`; router §15.3's `search_sources(query)` names it (§18).
9. **Every new config key moves the defaults fingerprint.** `DEFAULTS_SNAPSHOT_BY_ALGORITHM` (`config/template.py:817`) pins the effective defaults per version. Content-only phases recompute the latest entry with a recorded "no scoring, scheduling, projection or serving change" note, as Phase 1, project understanding M1 and T7 did. Branches that merge later recompute again.
10. **Reveal kinds need a table rebuild too.** A new `workbench_hint` kind would rebuild `reveal_events` as migration 179 did. A workbench hint is tutor prose, so it uses the existing `tutor_answer` kind with a distinguishing `basis` (§5.6).
11. **Library questions require a note.** `ask_question` in the `library` context needs `note_id` (`tutor_qa.py:355`). The cross-source tutor in RW4a uses the `reader` context with a pinned-span provider (§7.3).
12. **T6 latency.** On the linear_algebra copy a T6-grounded tutor answer waited about 7 s for retrieval alone (rewrite 1.8 s, embedding 0.8 s, verification 3.9 s; `docs/reviews/slice-2-t6.md` open question 2). Workbench bridging therefore runs after the hint is shown, never before it (§5.3).

### 3.5 What the dialogue asks for that does not exist

- No branching or status on Reader inquiries beyond the flat `resolution` column.
- No workspace for solving: no step capture, no resumable work beside the source, no work-aligned hints, no localization before submission.
- No passage-level cue; the Guide's misunderstanding reason never reaches the text.
- Library search returns a ranked list without per-source contributions; nothing compares sources.
- No interactive figures.
- No re-entry recap, no reader input to the router, no follow-up check after assisted work.

---

## 4. RW1 — Inquiry, the intent box and active reading

### 4.1 RW1a: what the learner sees

**Branching Ask.** Port `origin/feat/reader-clarification-branches` onto `main`, keeping its contract:
- `reader.ask.parentExchangeId` is the parent's `readerAnswerEventId`;
- the parent's spans override the current selection;
- only ancestors enter the prompt (the latest 12, with omitted counts in the manifest);
- the rail shows the tree, with search, expand, "new thread" and return-to-passage.
- The port composes with T6: a follow-up's retrieval query is the follow-up's own question; its ancestors are context only. Resolve the three conflicts (`reader_dialogue.py`, `tutor_qa.py`, `handlers/reader.py`) against T6's injected span provider and, if it has merged first, learner-text gaps' `learner_gap` fields.

**Inquiries.** An inquiry is a root exchange and its descendants.
- **Breadcrumb.** The rail shows the current inquiry as one line ("Mixture CDF → conditioning → integration bounds"); clicking a crumb opens that exchange and scrolls the source to its passage.
- **"Back to where I was"** restores the reading position from before the first branch (reader UX state, not source truth; P3 §12).
- **Status reuses what exists.** The root's `question_events.resolution` is the inquiry's status, so open inquiries already appear in Today's outstanding-question queue. "Revisit once" maps to the existing `test_me_later` preset on the root's anchor and "Make it something I can do" to `help_me_remember`. No new status vocabulary. **Reopen** adds `open` to the resolve RPC's accepted values (no schema change).

**Reconnect.** When a child branch is marked resolved, or the learner returns to the root passage, the rail shows one line: "Does the original passage make sense now?"
- **Yes** resolves the root and is logged as an explicit self-report (used by §15's calibration block).
- **A text box, "What's still unclear?",** starts a new branch from the root with that text as its question (W5). Being a reader question, it reaches learner-text gaps with no new adapter.
- **"Check me"** asks the quick-check producer for one formative question scoped to the root passage (§4.3). Answered, the expected answer is revealed for comparison; it is never an attempt; "add to practice" escalates it through the existing path.
- Ignoring the line does nothing; it disappears when the learner scrolls on (W12).

**Splitting the screen.** RW1a moves the rail into components (`screens/reader/AskRail.tsx`, `GuideRail.tsx`, `NotesRail.tsx`) after the port lands, so later phases don't fight over one 4,000-line file. It is a move, not a redesign: the existing `ReaderScreen` tests pass unchanged, plus the branch's.

**The reader report** (`learnloop reader report [--json] [--since]`, no model calls, no learner text) reports **workflows, with denominators**, not only counts:
- **selection → action → usable result → back to reading:** selections; actions invoked by kind; for model-backed actions, queued, completed, failed (with reason), cancelled and latency (p50/p95, model wait separated from learner time); whether the learner returned to the source passage within the visit;
- **inquiry:** inquiries opened, branch depth and breadth, resolved, dismissed, reopened, still open after 7 days; reconnect answers (yes / still unclear / check me);
- **visits:** visits, active minutes (idle excluded), time to first action after opening a source.

Each later phase adds its own funnel (§15). Model-backed rows carry model and prompt version so a report can be read per route.

### 4.2 RW1b: what the learner sees

**The intent box.** Selecting text opens a small box beside the selection: "What do you want to do with this?" with the cursor in it.
- The learner types in their own words ("why are the densities weighted?", "quiz me on this later", "make this a problem I can work"). Enter routes it.
- **Tab** (or clicking "actions") shows today's palette unchanged, so keyboard shortcuts keep working.
- An empty Enter runs Ask with no model call.
- The routed action shows as one line before it runs, for example "Asking · help me reason · change". "change" opens the palette with the text kept. There is no confirmation step.

**Routing** is one typed `ChoiceQuestion` to the Decider (route `ai.routing.reader_intent`, added to `DECIDER_TASKS`: never a chat fallback). The options are the actions that exist when the call is made: ask (with its answer mode); worked example, explain differently, why it matters; remember, test me later, connect it, mark confusing, not worth remembering; import as exercise; and, as later phases land, "work through this", "let me try the next step", "why does this step work", "compare sources", "practice this question" and "make this explorable".
- The learner's text becomes the question (for asks) or the annotation's learner text (for everything else).
- **If the Decider is unavailable,** times out (`reader_intent.timeout_seconds`, 4) or is spent out, the action is Ask.
- **Verdicts.** Every routing appends to `judgment_ledger` (task `reader_intent`, judge `decider`). A "change" appends the learner's correction (judge `learner_card`), so routing error stays measurable without a review chore.

**Active reading on derivations and worked examples** (the dialogue's "predict the next step" and "justify this step"). Two selection actions, also offered in the intent box:
- **"Let me try the next step."** The producer writes the question "What comes next after this line?" from the selection and the following blocks, keeping the next step as the expected answer. The learner writes their attempt; then the source's next step is shown beside it for comparison.
- **"Why does this step work?"** The producer asks for the justification of the selected step, with the source's or the model's justification as the expected answer, labelled accordingly.

Both are formative quick-check rows (§4.3), answered as today's quick checks are: no attempt, a self-check, "add to practice" to escalate. The learner sees the next step only after answering or pressing "show me".

### 4.3 Data

- **Branches:** no table. The parent lives on the `reader_answer_submitted` payload (as on the branch).
- **Inquiry status:** `question_events.resolution` and commitments, unchanged.
- **Quick-check scopes (one migration, RW1a):** `reader_authored_questions` gains
  - `scope_kind TEXT NOT NULL DEFAULT 'section' CHECK (scope_kind IN ('section', 'inquiry', 'selection'))`;
  - `question_style TEXT NOT NULL DEFAULT 'recall' CHECK (question_style IN ('recall', 'next_step', 'why_step'))` (RW1b writes the last two; RW1a's migration adds the column so there is one migration);
  - nullable `anchor_span_ids_json` and `inquiry_root_event_id`.

  `section_id` stays `NOT NULL`: a passage-scoped row carries the anchor's section. **The section lookup (`latest_reader_authored_question`) filters `scope_kind = 'section'`,** or a reconnect row would shadow the section's quick check. Reuse keys: section rows as today; inquiry rows per (`inquiry_root_event_id`, prompt version); selection rows per (extraction, anchor spans, style, prompt version). A `dismissed` row still suppresses re-authoring for its own key.
- **Events:** no new kinds (§3.4 item 4). Routing, corrections, reconnect answers and the funnel use existing kinds with a payload `event` field and `authority_class = 'salience_only'`:
  - `reader_action_invoked` (`event`: `intent_routed`, `intent_corrected`, `reconnect_answered`, `next_step_requested`, …);
  - `reader_job_queued` and `reader_job_completed` for every model-backed action (status, failure reason, latency, model, prompt version);
  - `reader_source_restored` for "back to where I was".

  The salience-firewall test gains a case per new `event` value.

### 4.4 Routes, spend, privacy

- **Routes.** `reader_intent` (decider; about $0.0004 a call at the listed price; `reader_intent.max_calls_per_day` 200). The reconnect and active-reading questions use the quick-check producer's existing route and its caps.
- **Privacy.** The selection and the learner's text go to OpenRouter's Decider provider (router D6 covers the disclosure). Nothing else is new.

### 4.5 Successor

None: content and display. Kill switches:
- `reader_inquiry.enabled` (off: the flat rail, exactly as today);
- `reader_intent.enabled` (off: the palette opens on selection, as today);
- `reader_active_reading.enabled` (off: no next-step or why-step actions).

---

## 5. RW2 — The exercise workbench

### 5.1 RW2a: the resumable scratchpad

**Where it opens:**
- **In the Reader:** "work through this" on an imported exercise, on a quick check (escalated to a practice item first, through the existing path), or on a selected problem (imported first through `import_exercises`, the existing paid path; the workbench opens when the item exists). The source stays in the left pane; the workbench takes the rail's width.
- **On the practice screen:** a "Work in steps" button on any item (remembered once chosen). It is **not** the default answer surface in v1 (D9).
- **From the daily plan:** the same as the practice screen.

**The layout:**
- **Problem:** the verbatim stem, with "original page" when it came from a source.
- **Your work:** an ordered list of steps. Each step is edited with the existing `LiveMarkdownEditor` (markdown with live KaTeX). Steps can be added, edited (a new version supersedes the old; the old text is kept) or deleted (a tombstone).
- **Actions (RW2a):** **I'm stuck · Submit · Leave for now · Abandon**. RW2b adds **Check my work · Help**.

**Saving and resuming** (the main RW2a benefit):
- Every step change is saved as it is typed, through a write queue modelled on the practice screen's draft checkpoints (`PracticeScreen.tsx:306`). A crash loses at most the keystrokes since the last flush.
- **"Leave for now"** (and navigating away, closing the app or a restart) keeps the session `open`. **"Abandon"** closes it.
- **"Resume this problem"** appears on the source (beside the problem's passage), in the rail, in RW6a's recap and on the item's practice card. It reopens the same steps, the same source anchor and, after RW2b, the same assistance history.
- An open session older than `workbench.open_session_days` (30) is shown as "unfinished" in the recap and never auto-closed.

**I'm stuck** opens a text box, "Write what you can, or what's confusing you". The text becomes a step of kind `stuck`. In RW2a it is kept as learner work; RW2b sends it to the hint writer and to learner-text gaps. Submitting with no steps and an empty box is the existing empty stuck answer (`declared_stuck = true`, scored 0 with no model call).

**Submit** composes the answer (the steps in order, stuck steps and tombstones excluded) and sends it through `submit_attempt` (§5.4).

### 5.2 RW2b: checks and the help ladder

**Check my work** reads the steps and returns, for each step, `valid`, `questionable` or `unchecked`, and names the **first questionable step** with a reason that quotes it. It never gives the correction. Each verdict is labelled by method:
- **"checked"** only when a symbolic check ran and passed or failed (§5.3);
- **"model's reading, not checked"** otherwise (W2).

**The help ladder.** Help always starts from the learner's **last valid checkpoint**:

| Level | What it is | Example |
|---|---|---|
| 0 | No help | — |
| 1 | A question about the approach or an assumption | "What does F(x) have to equal at the left end of the support?" |
| 2 | Localize: the first questionable step, no correction | "Step 4 is where your expression stops being a CDF." |
| 3 | A targeted hint: the principle or a subgoal, tied to the learner's step | "Your derivative in step 3 matches the PDF; check the constant of integration in step 4 against F(0) = 0." |
| 4 | Partial worked continuation: the next portion, starting from the learner's valid steps | Writes step 5 in the learner's notation |
| 5 | Full walkthrough, keeping the learner's route where it is valid | Completes the solution from step 4 |

- **Help** opens the ladder with one level **offered first** (§5.5), and every other level visible. The learner can take any level at any time (W11).
- **Authored hints first:** when the item's authored `hints` fit the learner's checkpoint, the hint writer may use one verbatim, labelled "from the item". A capped or unavailable session keeps the authored hints.
- **"This doesn't connect to my work"** sits under every hint: an optional text box with three shortcuts ("Different approach", "Too big a jump", "I don't understand the notation") and an optional pick of the step it refers to. The next hint reads it with the step snapshot, at once; there is no waiting for two failed hints. It appends a `learner_card` verdict (task `workbench_hint_fit`, verdict `different`) so the report can count unusable hints.

**The reconciliation contract** answers the owner's pain point. It is checked in code before a hint is shown:
1. **It cites the learner.** Every hint at level 2 or higher names at least one of the learner's step ids that exists, and quotes it.
2. **It continues from a real checkpoint.** `continue_from` must be a step marked `valid` or `unchecked`, and no later than the first questionable step.
3. **It says what stands.** The hint states which of the learner's steps stand ("Your steps 1–3 stand").
4. **It keeps the learner's route.** It never switches to the reference's route unless the learner's route is invalid, the learner pressed "Show me the book's way", or the learner said "Different approach". A valid but different route is said to be valid; PF-c's valid-alternative rule applies to checks as it does to grading.
5. **It changes strategy when it isn't working.** After a "doesn't connect" reply, or two hints on the same step, a new hint must declare a different `strategy` slug (for example `boundary_check`, `worked_parallel`, `representation_switch`, `counterexample`) from the earlier ones on that step.

A hint that fails 1, 2 or 5 is re-asked once with the failure named, then shown as a level-3 hint from the last valid step without its unverified claims.

**Leak control.** A hint at level 3 or lower must not contain the final answer: `answer_leaks_expected` (`tutor_qa.py:816`) runs on every hint; a leaking hint is re-asked once, then withheld with "this hint would give the answer away; take level 4?".

**Bridging to the book.** After a hint is shown, a background request may add "Compare with the book": a verified passage the hint relies on, side by side ("compare its integration limits with your step 4"). It uses `TutorSpanProvider` in the `practice` context unchanged (T6's item-bound scope: no exercise or solution blocks, nothing linked to the item, answer-overlap spans withheld, listwise verification). It never delays the hint (§3.4 item 12).

### 5.3 Symbolic checks: narrow and explicit

v1 checks only three transformations, each with stated inputs:
- **equivalence** of two consecutive expressions or of both sides of an equation step;
- **differentiation or integration** of a stated expression with respect to a stated variable;
- **substitution** of a stated value or expression.

How: the check writer (route `workbench_check`) proposes, per step it can classify, the transformation and a sympy check; PF's sandbox runs it with a negative control, as PF's equivalence checks do (§3.4 item 6). Without bubblewrap the sandbox fails closed and the verdict reads "model's reading". Unsupported steps stay `unchecked` or model-read, and the report counts them by kind (§15), which decides any expansion.

### 5.4 Source visibility and what an attempt records

**Source visibility.**
- **In the Reader the source is visible by default.** The submission goes through `submit_attempt` with `entry_surface = 'desktop_reader_workbench'` in a practice session the workbench opens (`start_session`). **The visible source counts as one hint-equivalent**, the same rule `submit_reading_question` already records (`hint_equivalent: true`). The attempt is therefore assisted: graded blind, diagnosed, FSRS-fed, and never certifying (W7). Exposures are recorded on the anchored spans as `OpenInSource` does today.
- **"Hide the source"** before the first step makes it an ordinary attempt. Opening the source afterwards records the exposure, and the hint-equivalent applies from then on.
- **On the practice screen and from the plan,** the source is hidden. "Original page" behaves like any other source opening during practice.

**No new evidence semantics.** Every assist maps onto fields that already have meaning:

| Assist | Recorded as | Existing meaning |
|---|---|---|
| Source visible in the Reader | `hints_used` += 1 | Assisted: schedules, certifies nothing (`causal_activity_policy.py:182`); the field's `+hints` arm reads it |
| Check my work, level 1–3 hints | `hints_used` += 1 for each one shown | The same |
| Level 4 or 5 | `primed = true` | `repair_activity`: no FSRS feed and no certification, like a guided redo |
| Hint text overlapping the key | A `reveal_events` row of the existing kind `tutor_answer`, `basis = 'workbench_hint:L<n>'`, with its overlap amount | Production admissibility and the reveal-aware cold lane |
| Answer confidence (optional, before Submit) | `answer_confidence` (1–5) | Logged only; never grading, certification or scheduling |
| Stuck text, then Submit | The steps are an ordinary answer; `declared_stuck` stays false | — |

Note the existing cap: `hints_used` is clamped to the item's `max_useful_hints` when that is set (`handlers/practice.py:561`). Any value above zero is assisted, so the cap changes no classification; the assist rows keep the true count for reports.

**On Submit:**
- the blind grader grades the composed answer with no knowledge of the steps' history or the hints (W8);
- the diagnoser's context gains, for this attempt only, the step trace with the assists in order and the work before each assist, under a prompt-version suffix (`+workbench-v1`) used only when a trace exists. Every other attempt's context hashes as before (the stuck-reading precedent);
- the feedback screen is today's, including guided redo.

**Abandoned sessions** write no attempt. Their steps and assists stay as learner work and appear in RW6a's recap.

The RW2a agent confirms this table against `resolve_attempt_activity_policy`. **If any mapping needs a new discount or eligibility rule, stop and make it a successor** (the next free `mvp-0.N` tag) rather than bending an existing field.

### 5.5 RW2b: the first offer, a judgment

When the learner opens Help, the **level chooser** picks which level to offer first.
- **How it is asked.** One typed `ChoiceQuestion` over levels 1–5 to the Decider (route `workbench_level_chooser`, added to `DECIDER_TASKS`), with a 3 s time box. On timeout, unavailability or `workbench.level_chooser_enabled = false`, the offer is level 1, then one level up on each further Help press.
- **The state it gets** (typed, short): the item's LO status (untested / assumed / learning / demonstrated); demonstrated vs assisted-only evidence on the item's facets (capability ledger, facet timeline); the active predictor's P(success) and interval for the item; workbench history on these facets (levels taken, and whether the learner continued unaided afterwards, including "doesn't connect" replies); this session's failed checks and hints; the help style (**let me struggle · balanced · guide me**, default balanced, remembered).
- **Why a judgment.** The expertise-reversal finding the dialogue cites: novices benefit from more guidance and experts from less, per learner × facet × task. The chooser applies it from evidence (W4). Learner history reaches the chooser, never the grader (W8).
- **Logging.** The offered level, the chooser and the level taken are on the assist row. There is no randomization of help quality (§17).

### 5.6 Reuse, learner text and signals

- **Grading and diagnosis:** the blind grader, the diagnoser, PF-c and guided redo, unchanged.
- **Retrieval:** `TutorSpanProvider` (practice context) for bridging; nothing new.
- **Learner text (RW2b):** a non-empty stuck step is a learner text. Learner-text gaps gains one source adapter (`workbench_stuck`, beside `tutor_question`, `diagnosis` and `stuck_answer`) that reads stuck steps with their item and anchors. It names gaps exactly as the pipeline does for other sources; nothing else in the pipeline changes. Until `learner/text-gaps` merges, the adapter is not built and stuck steps stay learner work.
- **Field signals: none new in v1.** `stuck_confusion` and "help before work" are derived signals that Phase 6 serving reads (fast-track blocking), so a new source would change serving and need a successor (§3.4; `field/signals.py:327`). A submitted workbench attempt already carries its assistance in `hints_used` and `primed`. Signals from mid-work stuck steps and abandoned sessions are deferred with a trigger (§17).

### 5.7 Data

| Table | Phase | Role | Contents |
|---|---|---|---|
| `workbench_sessions` | RW2a | WORKFLOW | `id`, `practice_item_id`, `origin` (`reader` \| `practice` \| `plan`), `extraction_id`, `span_ids_json`, `source_visible`, `source_hidden_at`, `practice_session_id`, `help_style`, `status` (`open` \| `submitted` \| `abandoned`), `attempt_id`, `created_at`, `updated_at`, `closed_at` |
| `workbench_steps` | RW2a | RAW_LEDGER | `id`, `session_id`, `ordinal`, `kind` (`step` \| `stuck`), `body_md`, `supersedes_id`, `deleted` (tombstone), `client_idempotency_key`, `created_at` |
| `workbench_assists` | RW2b | RAW_LEDGER | `id`, `session_id`, `kind` (`check` \| `hint` \| `bridge` \| `feedback`), `level`, `offered_level`, `chooser` (`decider` \| `fallback`), `step_snapshot_json` (step ids and content hashes at request time), `step_verdicts_json` (verdict and method per step), `first_questionable_step_id`, `continue_from_step_id`, `strategy`, `body_md`, `feedback_text`, `feedback_shortcut`, `feedback_step_id`, `cited_span_ids_json`, `retrieval_manifest_json`, `leak_flags_json`, `contract_failures_json`, `model`, `prompt_version`, `input_hash`, `latency_ms`, `created_at` |

No reveal-table rebuild (§3.4 item 10). Replay never reads the workbench tables: the attempt row carries `hints_used` and `primed`, and the reveal ledger carries the reveals.

### 5.8 Routes, spend, privacy

- **Routes (RW2b):** `workbench_check` (chat: step verdicts, localization and the sympy check text); `workbench_hint` (chat: hints at levels 1–5); `workbench_level_chooser` (decider). Unset chat routes fall back to the active provider.
- **Latency.** Codex blind grading took 29–37 s on the stuck-prompt copy, too slow for "Help". The target is check and hint p50 ≤ 10 s, **reported, not enforced**. The recommended route is a `chatgpt_plan` profile once `providers/chatgpt-plan` merges and the owner has signed in; until then a fast OpenRouter chat profile (D7). `learnloop ai latency` compares candidates before the switch.
- **Caps:** `workbench.max_calls_per_session` (24); `workbench.max_daily_cost_usd` ($1.00 for metered routes); a capped session says so and keeps the authored hints.
- **Context per call:** the item stem, reference solution and rubric; the session's steps, assists and feedback; for hints only, the open hypotheses on the item's facets as typed records (statement and status, no prose; Slice 1 S3). About 4–12K input tokens.
- **Privacy:** the learner's work and that slice of their state go to the configured provider, as grading and diagnosis already do. No new disclosure.

### 5.9 Successor

None (§5.4). Kill switches:
- `workbench.enabled` (off: no workbench entry anywhere; the practice screen is byte-identical);
- `workbench.help_enabled` (off: RW2a only);
- `workbench.level_chooser_enabled`;
- `workbench.symbolic_checks_enabled`.

---

## 6. RW3 — Passage cues (misconception-aware reading)

### 6.1 What the learner sees

A thin mark in the margin beside a passage, and a one-line note on hover or focus. Two kinds, both saying what connects, never what the learner lacks:
- **Revisit a distinction:** "Connects to a distinction you worked on: density vs cumulative probability. Not yet independently checked since."
- **A new application** (RW3b): "A new use of something you've shown: conditioning on a component."

**Actions on a cue:**
- **Open** shows the earlier work: the cited attempt, its diagnosis, the inquiry, the named gap.
- **Check me** offers one short item through `find_practice` constrained to the cue's facets, as a learner pick: an ordinary attempt, ordinary evidence. With DL1 merged it is a learner-pick block; before that it opens the item directly.
- **Not relevant** shows an optional text box, "why? (optional)" (W5).
- **Cues off** works for this source or everywhere.

**Restraint (W12):** at most `cues.max_per_section` (2) visible cues per section; never pop-ups, never blocking, never in skim mode.

### 6.2 How a passage gets a cue

**RW3a: the Guide's own passages.** The Guide already computes, per section, passages cited by items whose LO has an active error (`_passages_by_section`, `reader_guidance.py:362`). RW3a renders those with `learner_signal = 'recent_misunderstanding'` as margin marks:
- **Fix first:** `_learner_signal` reads the misconception statement through the diagnosis overlay (`error_events_for_attempt`) or the open hypothesis it belongs to, not raw `error_events` (§3.4 item 1). The Guide rail benefits too.
- The section's existing ranking picks which cues show, within the cap; the margin and the rail always agree.
- Wording comes from fixed templates (G16); the Guide's "Revisit this to resolve: …" stays in the rail only.
- Taps are logged as `reader_action_invoked` events (`event`: `cue_opened`, `cue_check_me`, `cue_not_relevant`) and as `learner_card` verdicts (task `passage_cue`).

**RW3b: discovered links.** For targets the Guide's provenance links miss:
1. **Targets.** Recurrence groups and open hypotheses (T1, Slice 1), durable misconceptions and holding-pen candidates, named gaps (`learner_text_gaps`, once merged), and facets with demonstrated capabilities (for "new application" cues). Each is rendered as its LLM-written statement (R3).
2. **Shortlist.** `search_spans` with the target's statement as the query, over the open source's extraction (T6: BM25, dense and the provenance list fused by RRF; top-k, no cutoff, W6).
3. **Judge.** One listwise call per target through `judge_listwise` (route `passage_cue_judge`, ledger task `passage_cue`): it judges every shortlisted passage `clarifies_distinction` | `new_application` | `prerequisite_for` | `none`, picks at most two, and quotes what it relies on (quote-verified against the block). The ledger cache makes a repeat free.
4. **Rank and cap.** Within a section, judged links and the Guide's passages share the cap in the judge's order, Guide passages first on ties.
5. **When state changes,** the cache key is the target's statement and status; a new or resolved hypothesis recomputes only its own links. Links are computed in the background when a source opens (W12).
6. **Holdout.** With `cues.holdout_rate` (0.1), an eligible **discovered** cue is withheld at random, with a logged seed and propensity, so its effect on the next attempt on those facets can be estimated without asking anything of the learner (§15; D10). Guide cues (RW3a) are not held out: they show what the rail already shows.

**Learner taps** are judge feedback: "not relevant" appends `learner_card` `different`, "open" and "check me" append `same`, on the judge's ledger task. Judge precision is measurable with no review chore.

### 6.3 Data

| Table | Phase | Role | Contents |
|---|---|---|---|
| — | RW3a | — | No table: cues are computed from the Guide plan; taps are events and ledger rows |
| `passage_links` | RW3b | WORKFLOW (paid outputs; never re-run on rebuild) | `id`, `extraction_id`, `span_id`, `target_kind` (`recurrence_group` \| `hypothesis` \| `misconception` \| `learner_text_gap` \| `demonstrated_facet`), `target_id`, `relation`, `quote`, `ledger_id`, `state_key`, `model`, `prompt_version`, `created_at` |
| `reader_cue_impressions` | RW3b | RECEIPT | `id`, `link_id` (null for a Guide cue), `visit_id`, `shown`, `propensity`, `seed`, `response` (`opened` \| `check_me` \| `not_relevant` \| `none`), `response_text_hash`, `created_at`, `responded_at` |

### 6.4 Routes, spend, privacy

- **Route:** `passage_cue_judge` (RW3b; listwise; Codex by default, since it is background work).
- **Caps:** one call per target per source open; `cues.max_calls_per_source_open` (12); `cues.max_daily_cost_usd` ($0.50 metered).
- **Privacy:** hypothesis and gap statements plus source passages go to the provider, the same class as diagnosis.

### 6.5 Successor

None: display only, and nothing it writes enters evidence or serving. "Check me" is a learner pick. Kill switches `cues.enabled` and `cues.discovery_enabled` (RW3b); `cues.holdout_rate = 0` turns the holdout off.

---

## 7. RW4 — Library questions, source comparison and exercises from sources

### 7.1 Roles come from ingest

No LLM role index is built in v1 (§3.4 item 2). Roles shown or filtered come from `source_blocks.role_hint`:
- **grouping** a library answer ("Definition", "Worked example", "Exercise", "Explanation" for `ordinary_prose`);
- **exclusion**, which T6's item-bound scope already applies (`exercise` and `solution` blocks out of practice and feedback contexts);
- **RW4b's exercise search** (`exercise` blocks) and RW5's candidates (`equation`, `figure`).

Where a passage is `ordinary_prose`, the organizer (§7.3) may add a finer label ("Geometric view", "Application") in its contribution line, labelled as the model's. Nothing is persisted per block. An LLM labeller is deferred with a trigger (§17).

### 7.2 `find_sources`: one function, three policies

A small library function in `learnloop/source_retrieval/`, composed from what T6 built. It is the function router §15.3 will call (§18):

```python
RetrievalPolicy = Literal["reading", "assisted_practice", "cold_attempt"]

def find_sources(
    vault, repository, query: str, *,
    policy: RetrievalPolicy,
    scope: Literal["library", "teaching"] = "library",
    learning_object_ids: Sequence[str] = (),
    item: PracticeItem | None = None,      # required for assisted_practice
    roles: Sequence[str] = (),             # role_hint filter
    verify: bool = False,                  # T6 listwise verification
    limit: int = 8,
    embedder=None, rewrite_client=None, rerank_client=None, deadline=None,
) -> SourceHits:                            # hits + manifest (query hash, policy, basis, keys, statuses)
```

| Policy | Built from | Learner-facing material |
|---|---|---|
| `reading` | `library_scope` or `teaching_scope(item_bound=False)` + `search_spans` | Everything in scope with teaching authority |
| `assisted_practice` | `teaching_scope(item_bound=True, item=…)` + the answer-overlap filter + `verify_spans`, as `TutorSpanProvider` does | No `exercise` or `solution` block, nothing linked to the item, nothing reproducing its answer |
| `cold_attempt` | — | **Nothing**: an empty result, by construction |

`post_attempt` and `authoring` are not added: T6 treats the feedback screen as item-bound on purpose (the next attempt's window spans it), and PF's source-anchored path has its own retrieval. **Receipts:** each call returns a manifest that the consumer stores on its own row, as T6's tutor manifest does. Exposure is recorded where the consumer shows text, unchanged.

### 7.3 RW4a: ask your library

The library search box (T6: type for keyword, Enter for meaning plus rewrite) gains **"Ask"** (Shift+Enter, or "where else is this explained?" from a selection).
- **The answer is sources first** (D12): no AI essay. Up to eight passages from `find_sources(policy="reading", verify=True)`, grouped by source and then by role. Each carries one line, "what this passage contributes", from the organizer: one listwise call through `judge_listwise` (route `library_organizer`, ledger task `library_contribution`) that judges each hit, picks and orders them, and writes a line that must cite exactly that hit's key (validated in code).
- **"Ask the tutor about these"** opens a tutor exchange in the `reader` context whose citation allowlist is the selected hits, across sources, through a pinned-span provider passed as `source_span_provider` (§3.4 item 11). It is a `question_events` row, so it joins the outstanding-question queue, the field's question signals and learner-text gaps with no new adapter.
- **"Personalized" is a toggle,** default on. When on, the organizer also sees the learner's open gaps and hypotheses on the hits' LOs and may mark one passage "speaks to your open question about …". Off, the order is plain retrieval rank (the dialogue's guard against confirmation bubbles).
- **"Practice this question"** calls `find_practice(query)`, the same call as DL3's "Practice on…" box. The learner picks from its proposals: a learner-pick block under DL1, else the item opens directly. When nothing fits, RW4b's "Find an exercise in my sources" is offered; nothing is generated live.

**Compare sources** ("How do my sources treat this?"), from a selection or a library answer:
1. **Counterparts.** `find_sources(policy="reading", scope="library")` with the selection as the query, grouped by source: at most one or two passages per source and at most four sources. The learner can also **pin** passages from any answer (up to four, from different sources).
2. **One comparison call** (route `library_organizer`, a second prompt): per source, its distinct contribution, and per pair, how they differ ("same result, assumes independence; Book B assumes only zero covariance"), each statement quoting its own source's passage (quote-verified; a line that fails is dropped, not repaired).
3. **Show a table:** one row per source, with "Ask the tutor about these" on the pinned set. **Differences are the point:** there is never a merged "consensus" answer.

Nothing is persisted as a source object or relation in v1. These lines are display, labelled AI-written; claim extraction and stored relations are deferred (§17).

### 7.4 RW4b: exercises from my sources

When "Practice this question" (or the cue's "Check me") finds nothing, **"Find an exercise in my sources"**:
- `find_sources(policy="reading", roles=["exercise", "worked_example"], verify=True)` over the teaching scope of the query's LOs;
- each candidate shows its passage, source and page, and "use this one";
- choosing one runs the existing `import_exercises` (verbatim stem, AI-completed answer, rubric, facets, hints) and the new item becomes a learner pick.

The exercise's boundaries are the import's job, as today; the learner can widen the selection in the Reader. Answer quality and exposure rules are those of imported exercises. Automatic follow-up sourcing from textbook exercises is later (§17).

### 7.5 Data

| Table | Phase | Role | Contents |
|---|---|---|---|
| `library_asks` | RW4a | WORKFLOW (paid outputs; never re-run on rebuild) | `id`, `query_md`, `query_hash`, `personalized`, `manifest_json` (the `find_sources` manifest), `organizer_json` (lines with their hit keys and ledger ids), `compare_json`, `question_event_id` (when the tutor was asked), `model`, `prompt_version`, `created_at` |

No change to `source_object_relations` or `source_objects`.

### 7.6 Routes, spend, privacy

- **Routes:** `library_organizer` (listwise; serves live requests, so the fast route is recommended, as for RW2b). T6's routes do the rest.
- **Caps:** library ask: one retrieval (with T6's own caps), one organizer call; compare: one call over at most four sources; `library.max_daily_cost_usd` ($1.00 metered).
- **Privacy:** source text and the question go to the provider. The personalized toggle adds gap statements; it can be turned off.

### 7.7 Successor

None. Retrieval is context (T6's ruling) and the organizer's lines are display. Kill switches: `library_ask.enabled`, `compare_sources.enabled`, `library_exercises.enabled` (off: T6's library search exactly as merged).

---

## 8. RW5 — Explorable figures (narrowed pilot)

### 8.1 What the learner sees

"Make this explorable" on a selected equation, a figure block or a short passage.
- **While it builds,** a small "building an interactive version…" line; reading continues.
- **The result** is a panel beside the passage with sliders for the parameters, one or two linked plots or readouts, and, by default, one **prediction** before the first change ("If p rises to 0.7, which side gains probability?"); the learner answers in a word or a choice, then sees the result.
- **The label is always visible:** "AI-built interactive · matches the source's equation (checked)" for a verified reconstruction; "AI-built illustration of an interpretation (not checked against the source)" otherwise.
- **Unsupported requests** say what was asked for and why it can't be drawn yet ("needs an integral readout"); the report counts them by kind (§17's trigger).
- The same figure reopens instantly from the cache.

### 8.2 The spec, not code

The model writes an **`InteractiveFigureSpecV1`** (JSON, strict schema). A trusted React renderer draws it. **No generated code runs anywhere** (generated-code figures are deferred, §17).

```text
spec_version    "ifs-v1"
kind            reconstructed | illustrative
source_claims   [{span_id, quote}]                     # quote-verified
parameters      [{name, label, min, max, step, default}]
definitions     [{name, expr}]                          # the grammar below
panels          function_plot {x:{var,min,max}, series:[{expr,label}], markers?}
                linear_map_2d {matrix:[[expr,expr],[expr,expr]]}   # unit square and grid under the map
                readout       {label, expr}                         # closed-form values only
invariants      [{kind: finite | bounded | nonnegative | integrates_to_one | monotone_nondecreasing | equals_source, ...}]
predictions     [{prompt, change:{param:value}, observe: expr | choices}]
```

**The grammar (v1):** numbers; parameter and variable names; `+ - * / ^`; unary minus; `exp log sqrt abs sin cos tan atan erf Phi min max`; `piecewise((cond, expr)…, else)` with comparisons; `pi`, `e`. No `integral` in the renderer: numerical integration exists only in the Python verifier (for `integrates_to_one`). Caps on length and node count.
- **Two evaluators, one grammar:** a hand-written TypeScript parser and evaluator (no `eval`, no `Function`), and a Python twin in the sidecar. One golden corpus, run in both vitest and pytest, keeps them identical within 1e-9 relative error.

### 8.3 Verification (before a figure shows)

Run in the sidecar:
1. **Structural.** Every expression parses; values are finite on a parameter grid (three points per parameter, at most 81 combinations); panels reference defined names.
2. **Invariants.** Each declared invariant holds on the grid, numerically (a density integrates to 1 within 1e-3 by Simpson in Python; a CDF is non-decreasing from 0 to 1; values stay bounded).
3. **Source match** (`kind = reconstructed` only). PF's pattern: the verifier (route `figure_verifier`) writes a sympy check, with a negative control, that the spec's defining expression equals the source equation quoted in `source_claims`; the sandbox runs it.

**Outcomes:** passing 1–3 makes the figure `verified`; failing 3 alone downgrades it to `illustrative` with its label; failing 1 or 2 means it is not shown ("couldn't build a reliable version of this", with the reason). Verdicts go to `judgment_ledger` (task `figure_verified`, judge `verifier` or `llm`).

### 8.4 Predictions

A prediction is formative (W1): stored on `figure_predictions`, never as an attempt, an observation or a signal. RW6a's recap lists predictions that missed as "worth a second look".

### 8.5 Data, routes, spend, privacy

| Table | Role | Contents |
|---|---|---|
| `interactive_figures` | WORKFLOW (paid outputs; never re-run on rebuild) | `id`, `extraction_id`, `span_ids_json`, `asset_id`, `spec_json`, `spec_version`, `kind`, `verification` (`verified` \| `illustrative` \| `failed` \| `unsupported`), `verification_report_json`, `unsupported_kind`, `model`, `prompt_version`, `input_hash` (reuse key), `created_at` |
| `figure_predictions` | RAW_LEDGER | `id`, `figure_id`, `prediction_index`, `learner_answer`, `observed_json`, `matched`, `created_at` |

- **Routes:** `figure_author` (chat; image input when a figure asset is included: an OpenRouter vision model or Codex's image input); `figure_verifier` (chat).
- **Caps:** two author attempts and one verifier call per request; `figures.max_per_day` (20).
- **Privacy:** source text and, for figures, the figure image. No learner data.

### 8.6 Successor

None: content and formative. Kill switches `figures.enabled`, `figures.predictions_enabled`.

---

## 9. RW6 — "Last time here", the digest, the router card and cold follow-ups

### 9.1 RW6a: "Last time here" (deterministic, no model)

When the learner opens a source they have read before, the rail shows a compact card above the Guide:
- **the last passage** and "continue there" (P3 restoration, as today);
- **open inquiries** on this source, each with "open" (to the breadcrumb) and status chips (resolve / revisit once / keep open);
- **unfinished problems** from RW2a, each with "Resume this problem";
- **predictions that missed** (RW5) and **reconnect "still unclear"** answers (RW1a), as "worth a second look";
- after RW6b: the narrative and the scheduled follow-ups, each with its date, purpose and undo.

Today's re-entry panel (DL1, goal-optional re-entry) can show the same card for the most recent source. The card is a pure read over `question_events`, `reader_section_progress`, `workbench_sessions`, `figure_predictions` and the reader envelope; nothing new is stored, and it is dismissible per source.

A **reader session** is one visit on the reader envelope (`visit_id`), or several visits less than 30 minutes apart. RW6a's typed summary is computed per session:
- sections read (from `reader_section_progress`);
- inquiries opened, resolved and still open, with their roots;
- workbench sessions: item, highest help level, submitted or abandoned, grade;
- cues opened or marked not relevant; predictions missed;
- gaps named by learner-text gaps from this session's texts;
- facets touched;
- **"claims needing an independent check":** facets where the session's work was assisted only (help level 3 or more, or a source-visible attempt) and no unassisted success exists since.

### 9.2 RW6b: the narrative and the router card

**The narrative** is optional (`digest.narrative_enabled`, default on): at most 120 words, written by route `reader_digest` from the typed summary only, citing event ids (validated against the summary), labelled "summary written by LearnLoop's model". It is generated once per session in the background and shown in the "Last time here" card.

**Reader activity in the router's learner-state card.** `reader_activity_for_card(lo_ids, as_of) -> ReaderActivityV1` is a pure read, like `named_gaps_for_card()` on the text-gaps branch. For the candidates' LOs it returns: open inquiries (root question excerpt, age, depth); assisted-only work (facet, highest help level, date); pending reader follow-ups (each with its purpose, date and valuation); missed predictions; the latest narrative, labelled model-written, with its cited event ids. Router R2 renders it as a "Reader activity" section of `LearnerStateCardV1` (router §4). The card stays deterministic from the ledger, because the narrative is a persisted, cited row (the teach-back summary pattern, router §15.1). **Nothing in it is evidence** (W1). Before R2 the function exists and has tests, but nothing renders it.

### 9.3 RW6b: cold follow-ups (the owner's "short unfamiliar problem")

**No count cap.** The owner's decision of 2026-10-12 (§20.7): value of information chooses, numbers and dates the checks, and the learner's real limits — the daily plan's minutes and the spend caps — bound them. Several follow-ups may be worth it, to find the true misconception, to decide between rival explanations, or to decide between actions. Follow-ups are served through DL2's "Check once". **RW6b builds no valuation of its own** (W13): it assembles the questions and candidates and asks the machinery that already values probes (§3.2).

1. **The open questions.** From the session's typed summary (§9.1), RW6b lists what a later independent attempt could tell LearnLoop about this learner. Each is read where it already lives; no new learner state is written:
   - **claims needing an independent check** (assisted-only work on a facet): the hypotheses are "holds unaided" and "doesn't", with the active predictor's P(success) and interval as the prior (field §4);
   - **rival explanations** still open on the session's facets: the locked hypothesis set and replayed posterior of an open probe episode (`episode_posterior`); a diagnosed attempt's rival causes (`unresolved_cause_factors.candidate_causes_json`); open `causal_hypotheses`; the facet's `hypothesis_marginal`; and, once learner-text gaps has merged, gaps named from this session's text.
2. **Candidate checks.**
   - For each facet with an open question, `find_practice(query, constraints)` proposes unfamiliar items with two new exact filters on `PracticeConstraints` (§3.4 item 7): `unattempted_only` (no attempt on the item) and `exclude_family_ids` (the families of every item whose solution the session revealed, from the reveal ledger). Admission already applies the scheduler's reserves.
   - Open probe episodes on those facets add their eligible instruments (`probe_episodes.eligible_instruments`).
   - **Relevance is the only model judgment.** One listwise call (`judge_listwise`, route `followup_relevance`, ledger task `followup_relevance`) keeps the candidates that test the capability or bear on the rival explanations, quoting what in the item does so. It no longer picks a winner or a number.
3. **Value each candidate with the existing machinery.**
   - **Information about the hypotheses (EIG).** Instruments use `instrument_expected_information_gain`, or the predictive variant when its target set is adequate; the two are never added together (probe EIG spec §7.4). Ordinary items use the per-facet EIG that the post-attempt follow-up slate already computes (`facet_expected_information_gain` over `hypothesis_marginal`), with `_misconception_discrimination` where rival misconceptions are open. Familiar surfaces are discounted with `familiarity_discount` (`learner/recall_coverage.py:293`), as the scheduler does for probes, so a near sibling of a problem just worked counts for less than a genuinely unfamiliar one.
   - **Value for the next decision (EVSI).** Where the session left a decision pending between actions (which repair to try; repair or move on), the loss table is `action_loss.build_loss_table`'s wasted learner-minutes and the value is `evsi.robust_evsi` (point, LCB, UCB). Where no loss table exists, `robust_composition.evaluate_selection` converts the robust EIG to minutes, as the robust probe path already does.
   - **Rank and stop with `evsi.rank_feasible`.** Rank is LCB / (expected minutes + burden); expected minutes come from DL1's estimator (`daily_plan/estimates.py:138`). Checks are added greedily, each valued conditionally on those already chosen (the rule `probe_episodes.plan_precommitted_block` uses for a block), so two checks that would tell LearnLoop the same thing are not both scheduled. Adding stops when the best remaining candidate's LCB ≤ λ·minutes + burden. An `abstain` verdict falls back to the EIG-per-minute order with the same stop, labelled "value uncertain".
   - **The number follows.** A session gets whatever clears the stop: often none, sometimes one, sometimes several, for example to separate two misconceptions and then to check retention.
   - **No new constants.** λ (1, minutes as numeraire), the burden (0) and the nat-to-minutes scale (60) are the existing decision parameters, labelled heuristic in `diagnosis/robust_composition.py:44`–`:55`. Calibrating them is the decision-value spec's job (§9 there); RW6b's receipts give it data.
4. **Date each check by what it is for.**
   - A **discriminating check**, valued for separating rival explanations before a repair decision, is dated for the next day's plan. DL1 never grows today's plan (§6.1), and the check is worth less once the repair is chosen without it.
   - A **retention check**, valued for whether an assisted claim holds unaided, is dated at the practiced item's effective due (DL2 §5.3), when forgetting is expected and a success says most (router §15.2). Without FSRS state the date is `followups.fallback_days` (3) away, labelled as a default.
   - **`followups.max_wait_days` (14) is a time cap:** no claim waits longer than two weeks for its check.
   - The date goes in `due_hint`. **Cross-spec request:** DL2's dated branch reads `due_hint` when present and falls back to `capture.test_me_later_days` otherwise (§18).
5. **Schedule as content, not as a new serving rule.** Each follow-up is a `test_me_later` commitment (disposition `one_check_pending`) on its item, with `provenance = {"via": "reader_followup", "summary_id": …, "purpose": "discriminating" | "retention", "valuation_ref": …}`. DL2 serves each exactly like any other "Check once": a dated learner request among the maintain lane's scheduled checks, cold (W7), with restoration after the measurement closes.
6. **Time and money are the only limits.** There is no count cap per session or per day.
   - **Minutes.** The plan's finite minutes bound what is served on any day. Scheduled checks sit in the maintain lane, which takes at most `plan.maintain_max_share` of the minutes (DL1 §6.2); what doesn't fit stays in the full list as "later", never as debt (DL1 §6.1). Dating by purpose spreads checks across days.
   - **Money.** `followups.max_daily_cost_usd` ($0.50 metered) covers the relevance calls. The valuation itself makes no model call.
   - **From router R2 on,** each pending follow-up is also a block candidate that the router values (planner value with robust EVSI, router §3). On a crowded day it then competes with reviews for the minutes instead of always going first.
7. **Re-valuation.** Before each day's plan is built, RW6b re-values its pending follow-ups with the same machinery against the current state. A follow-up whose question has been answered since — the facet was demonstrated unaided, or the rival explanations resolved — no longer clears the stop and is retired with its reason shown ("No longer needed: you solved a problem like this on Tuesday · undo").
8. **Nothing fits → no follow-up** for that question. The summary records `no_item`, and the card says "No unfamiliar problem on this yet". Generation is deferred with a trigger (§17).

**Labelled, with undo.**
- The card lists every scheduled check with its date and purpose: "Thursday: a problem that tells apart two explanations of your step-4 error · undo"; "Next Monday: a new mixture-distribution problem, cold · undo".
- "Why" shows the valuation as LearnLoop's estimate ("expected to settle which repair to try · about 6 min"), never as a verified fact (W2).
- "Undo all" retires every follow-up from the session. Undo and re-valuation retire the commitment (`commitments.retire`); undo also appends a `learner_card` verdict.
- Each relevance verdict appends `judgment_ledger` (task `followup_relevance`, judge `llm`).

**The valuation receipt** is stored on the digest row (§9.4): the questions, every candidate with its EIG, EVSI point, LCB and UCB, expected minutes, the verdict (`measure`, `stop`, `abstain`) and the stop reason, the chosen ids in order, and the module versions. Fields that R1 also logs for scheduler candidates use R1's names (`probe_eig`, `evsi_assignment`), so router R3's replay can read both. Replay never re-values (W9).

**Why no successor.** The serving algorithm is unchanged: it serves commitments as DL2 defines them. RW6b adds content (commitments) that the learner can undo, behind a kill switch, which is the precedent learner-text gaps set for its live prerequisite creation and seed check. This is the first live use of `evsi.rank_feasible`, but it decides only which commitments to create, never what the scheduler serves or how evidence counts. The RW6b agent confirms this with the reviewer. If they rule otherwise (for example because uncapped checks change the maintain lane's composition), RW6b takes the next free `mvp-0.N` tag with plan parity under `followups.enabled = false`.

**The outcome** joins later in the report: cold success after assisted reader work, and whether each check told LearnLoop what its valuation predicted (§15).

### 9.4 Data

| Table | Phase | Role | Contents |
|---|---|---|---|
| — | RW6a | — | No table: the card and summary are pure reads |
| `reader_session_digests` | RW6b | WORKFLOW (the narrative and the relevance verdicts are paid outputs; never re-run on rebuild) | `id`, `visit_ids_json`, `started_at`, `ended_at`, `summary_json` (typed, including each question's outcome or `no_item`), `narrative_md`, `cited_event_ids_json`, `followup_commitment_ids_json`, `valuation_json` (the receipt, §9.3), `model`, `prompt_version`, `dismissed_at`, `created_at` |

Follow-ups live in `commitments`; re-valuation retirements are commitment events with their reason. Nothing else is added.

### 9.5 Routes, spend, privacy

- **Routes:** `reader_digest` (chat) and `followup_relevance` (listwise, through `judge_listwise`); Codex by default, since both are background work. The valuation makes no model call.
- **Caps (money only):** one narrative per session; `followups.max_daily_cost_usd` ($0.50 metered) for relevance calls. Nothing caps the number of follow-ups (§9.3).
- **Privacy:** the typed summary goes to the provider, the same class as the router card.

### 9.6 Successor

None (§9.3, with the stated fallback). Kill switches: `recap.enabled` (RW6a), `digest.enabled`, `digest.narrative_enabled`, `followups.enabled` (off: no follow-up is created and no re-valuation runs; existing ones stay as the learner's commitments and can be undone).

---

## 10. Deferred phase: goal-aware reading paths (first draft's RW7)

Kept for when its trigger fires (§17). The design stands as drafted, with two corrections: roles come from `role_hint` plus the path judge, not a role index; and the change to DL1's reading block is a serving change, so it takes the next free `mvp-0.N` tag at its merge.

- **What the learner sees.** The Guide gains a path for the learner's intent on this source (DL2's control): per section core / prerequisite / enrichment / already shown / assumed, each with a "why", and "read it anyway" / "skip it" overrides. Depth wording maps onto DL2's intents (Master: fluency; Learn: learn to use it; Keep and Light touch: get the idea).
- **How roles are decided.** One LLM call per source and intent (route `reading_path_judge`) over the section list, the learner's status on the linked LOs, the intent and the goal. `already shown` stands only if every LO the section teaches is demonstrated (`lo_certification(...).demonstrated`), and `assumed` only with an open `assumption_decisions` row; otherwise the label falls back to `core`. Verdicts append `judgment_ledger` (task `reading_path_role`).
- **The plan follows the path.** DL1's reading block opens the next unfinished core or prerequisite section; enrichment is never planned. Kill switch `reading_paths.plan_uses_path` (off: DL1's order, byte-identical).
- **Data:** `reader_path_sections` (WORKFLOW).
- **Gates** (the first draft's G28–G29, kept for when it is built): honest path labels; `reading_paths.plan_uses_path = false` leaves DL1's reading blocks byte-identical, with a shadow rebuild showing zero projection deltas.

---

## 11. Persistence summary

**Migrations.** One per phase that needs one, numbered when it lands (`ls migrations/`; head 179 on this base, with DL1, R1, facet identity, learner-text gaps and the ChatGPT-plan provider claiming numbers first). Follow `CLAUDE.md`'s head-fixture procedure.

| Table | Role (`db/table_roles.py`) | Phase |
|---|---|---|
| `reader_authored_questions` (existing): `ADD COLUMN scope_kind`, `question_style`, `anchor_span_ids_json`, `inquiry_root_event_id` | unchanged | RW1a |
| `workbench_sessions` | WORKFLOW | RW2a |
| `workbench_steps` | RAW_LEDGER | RW2a |
| `workbench_assists` | RAW_LEDGER | RW2b |
| `passage_links` | WORKFLOW | RW3b |
| `reader_cue_impressions` | RECEIPT | RW3b |
| `library_asks` | WORKFLOW | RW4a |
| `interactive_figures` | WORKFLOW | RW5 |
| `figure_predictions` | RAW_LEDGER | RW5 |
| `reader_session_digests` | WORKFLOW | RW6b |

RW1b, RW3a, RW4b and RW6a need no migration. **No DERIVED table, so no new replayer.** Replay never reads these tables; the evidence they lead to lives in `practice_attempts` (`hints_used`, `primed`) and `reveal_events`, which replay already reads. **No table rebuild:** no new `interaction_events` kind and no new reveal kind.

**Events.** Existing reader kinds with a payload `event` field (§4.3): RW2 adds `workbench_opened`, `workbench_resumed`, `workbench_left`, `workbench_closed`; RW3 `cue_shown` (RW3a only; RW3b's impressions table is authoritative), `cue_*` taps; RW4 `library_ask`, `compare_opened`, `exercise_chosen`; RW5 `figure_opened`; RW6 `recap_shown`, `followup_undone`. The salience-firewall test gains each.

**Config** (modelled defaults, out of the decision-only template unless it has room). Each phase recomputes the latest `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry with a "no scoring, scheduling, projection or serving change" note (§3.4 item 9):
- `[reader_inquiry]`: `enabled`. `[reader_intent]`: `enabled`, `timeout_seconds` (4), `max_calls_per_day` (200). `[reader_active_reading]`: `enabled`.
- `[workbench]`: `enabled`, `help_enabled`, `level_chooser_enabled`, `symbolic_checks_enabled`, `open_session_days` (30), `max_calls_per_session` (24), `max_daily_cost_usd` (1.00), `price_per_million`.
- `[cues]`: `enabled`, `discovery_enabled`, `max_per_section` (2), `holdout_rate` (0.1), `max_calls_per_source_open` (12), `max_daily_cost_usd` (0.50).
- `[library_ask]`: `enabled`, `personalized_default` (true), `max_daily_cost_usd` (1.00). `[compare_sources]`: `enabled`, `max_sources` (4). `[library_exercises]`: `enabled`.
- `[figures]`: `enabled`, `predictions_enabled`, `max_per_day` (20).
- `[recap]`: `enabled`. `[digest]`: `enabled`, `narrative_enabled`. `[followups]`: `enabled`, `fallback_days` (3, a dating default without FSRS state), `max_wait_days` (14, a time cap), `max_daily_cost_usd` (0.50). No count cap (§9.3, §20.7).

**Routes** (each its own `ai.routing.*`, added to the `AITask` literal, `ROUTE_FOR_OPERATION` and the config schema):
- **decider tasks** (added to `DECIDER_TASKS`; never a chat fallback, never overridden by `LEARNLOOP_AI_PROVIDER`): `reader_intent`, `workbench_level_chooser`;
- **listwise tasks** (through `judge_listwise`): `passage_cue_judge`, `library_organizer`, `followup_relevance`;
- **chat tasks:** `workbench_check`, `workbench_hint`, `figure_author`, `figure_verifier`, `reader_digest`.

Unset chat routes fall back to the active provider, and receipts record the resolved model.

**`judgment_ledger` tasks:** `reader_intent`, `workbench_hint_fit`, `passage_cue`, `library_contribution`, `figure_verified`, `followup_relevance`, plus `learner_card` rows on the same tasks for corrections, taps, feedback and undos. The ledger's judge CHECK (migration 175) already admits `llm`, `verifier`, `decider` and `learner_card`; `task` is free text. No change.

---

## 12. Algorithm successors and kill switches

| Change | Kind | Successor | Kill switch | The switch restores |
|---|---|---|---|---|
| Branches, inquiry status, reconnect, report (RW1a) | Content and display | None | `reader_inquiry.enabled` | Today's flat rail |
| Intent box, next-step and why-step questions (RW1b) | Content, formative | None | `reader_intent.enabled`, `reader_active_reading.enabled` | Today's palette |
| Workbench scratchpad and submission (RW2a): source visible as one hint-equivalent | Content, existing evidence semantics | None, unless the agent finds a mapping that needs a new rule (then the next free `mvp-0.N`) | `workbench.enabled` | Today's practice screen, byte-identical |
| Checks, hints, chooser, feedback (RW2b); diagnoser trace when present | Content, existing evidence semantics; context only when present | None (stuck-reading precedent) | `workbench.help_enabled` and its sub-switches | RW2a |
| Guide cues in the margin; Guide statement read from the overlay (RW3a) | Display | None | `cues.enabled` | No cues; the rail's statement is still corrected |
| Discovered cues and holdout (RW3b) | Display | None | `cues.discovery_enabled`, `cues.holdout_rate` | RW3a |
| `find_sources`, library ask, compare, exercises (RW4a/b) | Retrieval context and display | None (T6's ruling) | `library_ask.enabled`, `compare_sources.enabled`, `library_exercises.enabled` | T6 as merged |
| Figures and predictions (RW5) | Content, formative | None | `figures.enabled` | — |
| Recap (RW6a); digest and card section (RW6b) | Content | None | `recap.enabled`, `digest.enabled` | — |
| Follow-ups valued by the existing EIG/EVSI machinery, with no count cap, as "Check once" commitments (RW6b) | Content served by DL2's unchanged rule; first live use of `evsi.rank_feasible`, deciding only which commitments to create | None (§9.3; fallback: the next free `mvp-0.N` with plan parity) | `followups.enabled` | No new follow-ups and no re-valuation |

**Kill-switch parity is a gate** for every row: switch off, the RPCs it touches return byte-identical results on fixture copies.

The RW3a fix to `_learner_signal` changes a Guide reason string and ranking input only (the Guide is display; `build_guide_plan` writes no evidence and serves nothing). Its gate is a Guide-plan snapshot test on a split fixture.

---

## 13. Rollout

Every phase goes through `implementation_goal.md` §2's loop: implement, adversarial review (Codex, or Opus 5.5 when Codex is out), fix, gate, integrate. Phases merge one at a time. Keep at most two Reader phases open at once; all of them touch the Reader's frontend. The Reader workbench is not part of the goal's definition of done (`implementation_goal.md` §1), so it yields the merge queue and Codex capacity to the goal's tracks (DL2, DL3, router R2) when they compete.

| Phase | Builds | Needs | Size | Gate and owner checkpoint |
|---|---|---|---|---|
| **RW1a Inquiry** | Port the branch; rail split; inquiry status and reopen; breadcrumb and return; reconnect with passage-scoped check (migration); the report's funnel | `main` | **M** | G1, G2, G4. **Checkpoint:** a week of reading, then the funnel |
| **RW3a Guide cues** | The overlay fix in `_learner_signal`; margin marks; taps; wording templates | RW1a (rail split) | **S** | G13, G14 (cap and skim only), G16, G30 |
| **RW6a "Last time here"** | The recap card; the typed session summary | RW1a. Unfinished problems appear once RW2a lands | **S–M** | G25 (summary part), G31 |
| **RW2a Scratchpad** | Sessions and steps (migration), the step editor, saving and resume, Submit with the source-visible rule, practice-screen "Work in steps" | RW1a (rail split) | **M** | G5 (rows for source visible and no help), G6, G10, G11, G32. **Checkpoint:** a week of solving |
| **RW1b Intent and active reading** | The intent box with the Decider; next-step and why-step questions | RW1a | **S–M** | G3, G4 |
| **RW4a Library and compare** | `find_sources`, library ask with organizer and tutor, pin and compare, practice this question (migration) | RW1a; DL1 merged for learner-pick blocks (optional) | **M** | G17, G18, G19, G20 |
| **RW2b Checks and help** | Assists (migration), check, ladder, contract, feedback, chooser, narrow symbolic checks, bridging, diagnoser trace, stuck-step adapter | RW2a. `providers/chatgpt-plan` merged and signed in (latency). `learner/text-gaps` merged for the adapter (else skipped, recorded) | **L** | G5 (all rows), G7, G8, G9, G12, G33. **Checkpoint:** the workbench report (help levels by facet over time, recovery, unusable-hint rate, latency) |
| **RW3b Discovered cues** | Links, listwise judge, holdout, impressions (migration) | RW3a. `learner/text-gaps` merged for gap targets (works without) | **M** | G13–G16. **Checkpoint:** cue report once there is data |
| **RW4b Exercises from sources** | Exercise search and hand-off to `import_exercises` | RW4a | **S–M** | G19, G34 |
| **RW5 Figures** | Spec, grammar, both evaluators with the golden corpus, renderer (two panels and readouts), verification, predictions, cache (migration) | RW1a (entry point) | **M–L** | G21–G24 |
| **RW6b Digest, card, follow-ups** | Narrative (migration), `reader_activity_for_card`, the relevance judge, the valuation adapter over the existing EIG/EVSI functions (§9.3) with its receipt, `PracticeConstraints` filters, follow-up commitments with `due_hint` and purpose, daily re-valuation, undo | DL2 merged (with `due_hint`); RW2a (assisted work); `main`'s EIG and EVSI modules (no new valuation). R1 merged is recommended, not required: the receipt borrows its field names. R2 later renders the card section and values pending follow-ups as block candidates | **M–L** | G25–G27, G35. **Checkpoint:** two weeks, then the follow-up outcomes and valuation-calibration blocks |
| *Router R2 (router spec)* | Renders `ReaderActivityV1`; values each pending reader follow-up as a block candidate (planner value with robust EVSI, router §3), so follow-ups compete with reviews for a day's minutes | R1; DL1; RW6b for the reader section and follow-up candidates (R2 may land first) | — | Router gates |
| *Router §15.3 (router spec)* | The router and tutor call `find_sources` as a tool | Its own trigger | — | Router gates |

**Size key:** S ≈ one agent session plus review (about a day); M ≈ two to four days of implement, review and fix; L ≈ one to two weeks.

**Recommended order** (dependencies in the table): **RW1a** first (it ports finished work and splits the rail). Then **RW3a** and **RW6a** (small, immediate learner value) alongside **RW2a**. Then **RW1b** and **RW4a**. Then **RW2b** once the ChatGPT-plan provider and learner-text gaps have merged. Then **RW3b**, **RW4b** and **RW5**. **RW6b** waits for DL2. RW2 is the core differentiator and the owner's own pain point; RW2a delivers its non-AI half early.

---

## 14. Gates and tests

| # | Gate |
|---|---|
| G1 | **Branch port parity.** The branch's 8 backend and 9 frontend tests pass on `main`. A follow-up's prompt holds only its ancestors. T6's retrieval for a follow-up uses the follow-up's own question. Legacy flat histories read as roots |
| G2 | **Inquiry status is not evidence.** Resolving, reopening, "revisit once" and reconnect answers write no attempt, observation, mastery or FSRS row. The salience firewall covers every new payload `event` |
| G3 | **Intent routing.** A routed action has exactly the effect of the same palette action (the same RPC and payload). An empty Enter makes no model call. An unavailable, timed-out or spent-out Decider routes to Ask. "change" records a `learner_card` verdict. With `reader_intent.enabled = false`, the selection UI is today's |
| G4 | **Scoped questions are formative and keyed.** Reconnect, next-step and why-step questions write no attempt. A passage-scoped row never shadows its section's quick check (lookup filtered by `scope_kind`). Reuse keys hold. Section quick checks are byte-identical |
| G5 | **Assistance mapping.** For the source visible or hidden, and each help level (0–5) and combination, the submitted attempt's `hints_used`, `primed` and reveal rows match §5.4, and `resolve_attempt_activity_policy` gives the stated FSRS and certification eligibility (any source visibility, check or hint earns zero certification credit in both projections). A rebuild reproduces evidence identically. An abandoned session writes no attempt |
| G6 | **The grader stays blind.** The rendered blind-grading prompt for a workbench attempt contains the composed answer only: no step history, assist text, hint, feedback or learner state |
| G7 | **Reconciliation contract.** A fake hint writer that cites no learner step, continues from a step after the first questionable one, or repeats a strategy after a "doesn't connect" reply is caught, re-asked once, then downgraded as §5.2 says |
| G8 | **Leak control.** A level-1–3 hint containing the expected answer (including short numeric answers) is never shown. Bridging never returns the item's exercise, solution or linked blocks, and never delays the hint |
| G9 | **Symbolic labels.** "checked" appears only when the sandbox ran the check and its negative control behaved. Without bubblewrap every verdict reads "model's reading". Only the three transformations are attempted |
| G10 | **Source visibility.** A Reader workbench attempt with the source visible goes through `submit_attempt`, is graded and diagnosed, and earns zero certification credit in both projections. "Hide the source" makes an ordinary attempt. Opening the source afterwards records the exposure and the hint-equivalent |
| G11 | **Workbench kill switch.** With `workbench.enabled = false`, practice RPCs and screens are byte-identical to `main` on fixture copies |
| G12 | **Spend.** Per-session and daily caps hold. A capped session keeps authored hints. Codex receipts are `estimated_only`. The chooser's time box falls back to level 1 |
| G13 | **Cues are display only.** With cues on or off, evidence, mastery, projections, FSRS and the plan are byte-identical. "Check me" produces an ordinary learner-pick attempt |
| G14 | **Restraint and holdout.** No section shows more than the cap. No cue in skim mode. Guide cues are never held out. For discovered cues the logged propensity equals the draw probability, and seeds reproduce draws |
| G15 | **Judges decide.** With the cue judge stubbed to `none`, no discovered cue appears, whatever retrieval ranks (R1). Every discovered cue has a ledger verdict and a verified quote |
| G16 | **Wording.** Cue copy comes from fixed templates. A lint test rejects "weak", "you don't understand", "you struggle" and similar |
| G17 | **Sources first.** A library ask returns passages and organizer lines, never a tutor essay, until the learner asks the tutor. Each organizer line cites exactly one returned hit. The tutor's citations stay inside the pinned hits |
| G18 | **Compare keeps sources apart.** Every statement shown quotes a verified passage of its own source; a failing line is dropped. No `source_objects`, relation, concept edge, facet merge or prerequisite is written (table diff) |
| G19 | **Retrieval policies.** `cold_attempt` returns nothing. `assisted_practice` equals `TutorSpanProvider`'s scope and filters for the same item (no exercise or solution block, nothing linked, nothing leaking the answer). Policies are recorded on every manifest |
| G20 | **RW4 kill switches** restore T6's library search, tutor spans and Quick Add behaviour byte-identically |
| G21 | **No generated code runs.** The grammar parser rejects everything outside the grammar (fuzzed). The renderer has no `eval` or `Function`, enforced by a lint rule |
| G22 | **Two evaluators agree** on the golden corpus within 1e-9 relative error, and the corpus covers every grammar construct |
| G23 | **Labels follow verification.** "matches the source's equation" appears only after step 3 passed. A figure failing steps 1 or 2 is never shown. Unsupported requests are recorded with their kind |
| G24 | **Predictions are formative.** They write no attempt, observation or signal |
| G25 | **Recap, digest and card.** The typed summary is deterministic from the ledgers (computed twice, identical). The narrative cites only ids in the summary. `ReaderActivityV1` contains no cold-answer or reserved-surface material (router G5) |
| G26 | **Follow-ups are unfamiliar and valued, not counted.** Never an attempted item; never an item in a family whose solution the session revealed; `no_item` when nothing fits; never generated. With a fake valuation where every candidate's LCB is below its minutes, none is created; where several clear it, all of them are created in rank order, with no count cap, and conditional valuation drops a second check that duplicates the first. Every created follow-up has a receipt whose chosen value cleared the stop rule. Re-valuation retires a follow-up whose facet was since demonstrated unaided, with its reason |
| G27 | **Follow-ups are ordinary "Check once" commitments.** Served by DL2's dated branch on `due_hint`, cold, with restoration after; discriminating checks dated for the next day's plan, retention checks at effective due, none later than `followups.max_wait_days`. A day with more due follow-ups than its maintain minutes serves what fits and leaves the rest as "later" (plan minutes never exceeded). Undo and "undo all" retire the commitments. With `followups.enabled = false` no commitment is created and plan builds equal DL2's |
| G35 | **Reuse, not a new chooser.** The valuation calls `evsi.robust_evsi` / `evsi.rank_feasible`, the probe-EIG functions and `familiarity_discount` (asserted by monkeypatching them in the test); RW6b defines no EIG, EVSI or stop rule of its own. The valuation makes no model call; replay never re-values |
| G30 | **The Guide reads the overlay.** On a split fixture with a live diagnosis, the Guide's passage reason names the diagnoser's statement; on a joint-graded fixture it is unchanged |
| G31 | **The recap is a pure read.** Opening a source with the recap on or off writes nothing but the `recap_shown` event |
| G32 | **Resume.** Steps survive navigation, sidecar restart and app restart (flush-on-leave tested); "Leave for now" keeps the session open; "Abandon" closes it; a resumed session shows its full history |
| G33 | **Hint feedback.** A "doesn't connect" reply reaches the next hint's prompt at once and appends a `learner_card` verdict; the next hint changes strategy |
| G34 | **Exercises from sources.** Candidates are `exercise` or `worked_example` blocks from the teaching scope; choosing one runs `import_exercises` unchanged; nothing is imported without the learner's pick |

**Every phase also holds:** replay and rebuild make zero model and embedding calls with its tables populated; every new RPC is pinned desktop-only in `tests/test_mobile_allowlist.py`; every new table is classified in `db/table_roles.py`; the defaults snapshot is recomputed with its note.

**Tests** (fakes only: `tests/structured_ai.py`, `tests/openai_fakes.py`, a fake Decider; vault builders from `tests/helpers.py`):
- **RW1a:** the branch's `test_reader_branches.py`, `ReaderAskBranches.test.tsx` and `ReaderScreen.branches.test.tsx`, ported; `test_reader_inquiry_status.py`; `test_reader_reconnect.py` (scope keys, section shadowing); `test_reader_report.py` (funnel denominators); vitest for the breadcrumb and the split rails.
- **RW1b:** `test_reader_intent.py` (routing, fallbacks, correction verdicts, palette parity); `test_reader_active_reading.py`; vitest for `IntentBox`.
- **RW2a:** `test_workbench_steps.py` (supersede, tombstone, idempotent writes); `test_workbench_resume.py`; `test_workbench_assistance.py` (G5 rows without help, replay); `test_workbench_blind.py` (G6); `test_workbench_source_visibility.py` (G10); `test_workbench_kill_switch.py`; vitest for the layout, the editor and resume.
- **RW2b:** `test_workbench_check.py` (checked and model-read labels, negative controls, the bubblewrap-missing path, unsupported kinds); `test_workbench_hints.py` (contract, strategy change, feedback, leak control, bridging exclusions and ordering); `test_workbench_assistance.py` (all G5 rows); `test_workbench_chooser.py` (inputs, time box, fallback, logging); `test_workbench_text_gaps.py` (the adapter); vitest for the ladder, feedback and stuck box.
- **RW3a:** `test_reader_guidance.py` gains the overlay case (G30); `test_reader_cues.py` (cap, skim, taps to the ledger, display-only parity); a wording lint; vitest for margin marks.
- **RW3b:** `test_passage_links.py` (retrieval shortlist, judge decides, state-key recompute, ledger cache); `test_reader_cue_holdout.py`.
- **RW4a:** `test_find_sources_policies.py` (G19); `test_library_ask.py` (G17, personalization toggle, practice this question, pinned-span tutor); `test_compare_sources.py` (G18); `test_rw4_kill_switches.py`.
- **RW4b:** `test_library_exercises.py` (G34).
- **RW5:** `test_figure_grammar.py` and `figureGrammar.test.ts` (golden corpus, fuzz); `test_figure_verification.py` (invariants, source match, downgrade, refusal, unsupported); `test_figure_predictions.py`; vitest for the renderer's panels.
- **RW6a:** `test_reader_recap.py` (G25 summary part, G31).
- **RW6b:** `test_reader_digest.py`; `test_reader_activity_card.py`; `test_reader_followups.py` (constraints, `no_item`, no count cap, stop rule, conditional valuation, dating by purpose, `max_wait_days`, re-valuation, `due_hint`, undo and undo all, kill switch, spend cap); `test_reader_followup_valuation.py` (G35).

**Every phase runs** `uv run lint-imports --no-cache`, `uv run pytest -n auto`, `uv run pytest -m durability`, `npm run typecheck && npm test` (the frontend changes in every phase), and the DB reference generate and validate scripts when the schema changed. **B3:** while the Rust toolchain on carson is broken, `cargo check` fails and the desktop shell can't be rebuilt; phases are verified with vitest and the sidecar tests, and the owner's in-app check waits for the toolchain fix.

---

## 15. Evaluation: learning, not engagement

The dialogue's warning applies: a better Reader may produce *fewer* interactions, because the learner gets unstuck sooner. So `learnloop reader report` reports outcomes and completed workflows first. As everywhere at n=1, these are **reports with noise floors, not thresholds** (R6).

| Block | Measures | Phase |
|---|---|---|
| Funnel | Selection → action → usable result → back to reading, with denominators: shown or available, requested, completed, failed (reason), cancelled; latency p50/p95 with model wait separated from learner and idle time; per route, model and prompt version | RW1a, extended by every phase |
| Inquiry | Inquiries opened, branch depth, resolved, dismissed, reopened, open after 7 days; reconnect answers; intent-box vs palette use and routing corrections (RW1b); next-step attempts and self-check results | RW1a/b |
| Workbench | Sessions opened, resumed, submitted, abandoned, left open; help level taken vs offered, by facet over time (**hint dependence**); recovery: the share of checks followed by a valid next step without further help; time stuck (questionable verdict to next valid step); **unusable hints** ("doesn't connect" by shortcut); check coverage by transformation kind; grade by highest level used; check and hint latency | RW2a/b |
| Cues | Impressions, open, check-me and not-relevant rates; cues per reading hour (**interruption burden**); for discovered cues, next attempt on the cue's facets for shown vs held-out, IPS-weighted by the logged propensity, with an interval and its sample size | RW3a/b |
| Library | Asks; organizer-line validation failures; tutor follow-up rate; compare usage; practice-this pick rate; "nothing fits" rate and exercise-from-sources picks | RW4a/b |
| Figures | Requests; verified / illustrative / failed / unsupported shares (by kind); predictions made and missed | RW5 |
| Calibration | Confidence before submission (optional) and reconnect "yes" against the next independent outcome on the same facets: counts of **confident misses** and **unconfident successes**, never a score | RW2a, RW1a, RW6b |
| Interventions → outcomes | For each shown hint, bridge, comparison, figure and cue: the next attempt on the same item or facets (immediate continuation) and the later cold outcome; how many have **no follow-up observation yet**. Associations, never causal credit | RW2b, RW6b |
| Loop closure | Follow-ups per session (the distribution, not a cap), by purpose; scheduled, undone, retired by re-valuation, served, answered and left as "later"; `no_item` rate; minutes spent on follow-ups as a share of plan minutes; **cold success after assisted reader work** (the dialogue's primary outcome), beside cold success on comparable items without reader help; recap and narrative dismissal | RW6a/b |
| Valuation calibration | For each answered follow-up: predicted EIG against the realized change in the hypothesis posterior, and whether a pending decision flipped as its EVSI predicted; the `abstain` rate. Fed to the decision-value spec's readiness audit (`diagnosis/causal_selection_audit.py`) as the first live EVSI data. Reports, never thresholds (R6) | RW6b |

The three experiments the dialogue proposes map as follows:
- **Generic vs work-aligned hints** is *not* run: it would deliberately give worse help. The reconciliation contract is the design; recovery, dependence and unusable-hint rates are tracked.
- **Cues vs no cues** is the RW3b holdout.
- **Summaries alone vs typed evidence plus summaries for routing** belongs to router R3, whose replay can ablate the card's reader section.

**Usability walkthrough.** At the RW1a and RW2a checkpoints the owner may do one optional, timed task walkthrough (ask → branch → return; open → solve → leave → resume), recorded in the phase's review file. It is never required (R1).

---

## 16. Decisions: recommended defaults (each default; owner may override)

| # | Decision | Recommended default |
|---|---|---|
| D1 | Phase order | RW1a → RW3a, RW6a, RW2a → RW1b, RW4a → RW2b → RW3b, RW4b, RW5 → RW6b after DL2 (§13) |
| D2 | The selection's first interaction | The intent box, with the palette one key away (Tab). An empty Enter asks |
| D3 | Who routes the intent box | The Decider (one typed choice, about 2 s); fallback Ask |
| D4 | Inquiry status | Reuse `question_events.resolution` (plus reopen), and the `test_me_later` / `help_me_remember` commitments. No new status words |
| D5 | Port or rebuild branching Ask | Port `origin/feat/reader-clarification-branches` |
| D6 | Workbench evidence mapping | A visible source, checks and levels 1–3 add to `hints_used` (assisted: schedules, never certifies); levels 4–5 make the attempt `primed`; hint text overlapping the key is a `tutor_answer` reveal with a workbench basis. No new rule, so no successor |
| D7 | Workbench model routes | The ChatGPT-plan provider when merged and signed in; until then a fast OpenRouter chat profile. Codex only if the latency report is acceptable |
| D8 | First-offer help level | A judgment: the Decider over typed state plus the help style (default "balanced"), time-boxed; fallback "level 1, then up" |
| D9 | Where the workbench is the default | In the Reader, with the source visible ("Hide the source" for a cold-eligible attempt). On the practice screen and in the plan, a remembered "Work in steps" button, not the default, until the RW2b checkpoint |
| D10 | Cue restraint | At most 2 per section, none in skim mode; a 10% logged holdout on discovered cues only |
| D11 | Cue kinds | "Revisit a distinction" from RW3a; "a new application of something you've shown" from RW3b |
| D12 | Library answers | Sources first, grouped by source and role; the tutor on request; personalization on, with a toggle |
| D13 | Compare sources | Display-only, quote-verified contribution and difference lines. No stored claims or relations in v1 |
| D14 | Roles | Ingest's `role_hint`; the organizer may name finer roles in its lines. No LLM labeller in v1 |
| D15 | Figures | Declarative only; two panel types plus readouts; unverified reconstructions downgraded to labelled illustrations; one prediction per figure by default |
| D16 | Recap and digest | "Last time here" on returning, deterministic. The narrative on, shown in the card, not as an exit panel |
| D17 | Cold follow-ups | **Owner, 2026-10-12 (§20.7):** automatic, with **no count cap**. The existing value-of-information machinery chooses, numbers and dates them: probe EIG over the learner's open hypotheses, and EVSI (`scheduling/evsi.py`) for the next decision, stopping when a check's robust value no longer pays for its minutes. Discriminating checks next day; retention checks at effective due; `max_wait_days` 14 as a time cap; 3-day fallback without FSRS state. Bounded by the plan's minutes and a $0.50 daily spend cap. Labelled with purpose and valuation, undo each or all; DL2 "Check once" commitments dated by `due_hint`; `find_practice` only, `no_item` when nothing fits |
| D18 | Reading paths | Deferred (§10, §17) |
| D19 | Spend | Metered caps of $1.00 a day each for the workbench and library, $0.50 for cues; Codex `estimated_only` |
| D20 | Phone | No new RPC is phone-allowed in v1 |
| D21 | Hint feedback | "This doesn't connect to my work" on every hint, with three shortcuts, used immediately |
| D22 | Confidence | Optional before a workbench Submit, logged only; reported as calibration counts |

---

## 17. Deferred, with triggers

| Deferred | Revisit when |
|---|---|
| **Goal-aware reading paths** (§10) | DL2 is merged *and* the owner reports reading sections they didn't need, or the DL1 plan report shows reading blocks skipped more than half the time |
| **The router querying sources as a tool** | Router §15.3's own trigger: R2 live and T6's hybrid-vs-dense re-evaluation settled. RW4a's `find_sources` is the function it calls |
| **An LLM role labeller** over source blocks | The RW4 report shows `ordinary_prose` hits are most of what learners open, or RW4b misses exercises the owner points to |
| **Source claims and stored cross-source relations** (`source_objects` claims, a claim matcher, relation types) | Compare is used ≥ 10 times in a month *and* the owner asks to keep or revisit comparisons |
| **Generated follow-ups** (PF-b when `find_practice` finds nothing) | The `no_item` rate exceeds half of chosen follow-ups over two weeks. Generation runs as a background PF request, never on the session's request path |
| **Follow-ups from textbook exercises automatically** | RW4b's picks show learners choose source exercises often |
| **Field signals from mid-work stuck steps and abandoned sessions** (the S5 placement signal) | The workbench report shows ≥ 20% of sessions abandoned after help; ships as a successor on the field derivation |
| **The general figure language** (integral readouts, PMF bars, shaded areas, more panels) | The RW5 report names one unsupported kind ≥ 5 times |
| **Generated-code figures** in an isolated, unprivileged surface | ≥ 10 unsupported requests the grammar can't express, *and* a Tauri isolation design (no IPC, files or network) is reviewed |
| **Broader symbolic checks** (arbitrary "follows from") | The check-coverage report names an unsupported transformation kind in ≥ 20% of checks |
| **OS-level learning service** (MCP, editor or browser capture) | DL3's capture box is used most days *and* the owner reports capturing from another app as a gap |
| **Page-image retrieval** | T6 open question 4's multimodal rematch shows page images beating Marker text |
| **Local rerankers** | LLM verification latency is the measured bottleneck in the RW4 or RW2b latency blocks |
| **Learned cue and hint policies** | ≥ 500 discovered-cue impressions with matured outcomes and propensities, *and* router §13's learned-scorer conditions |
| **Figure predictions and reconnect answers as weak observations** | The calibration and figure blocks show missed predictions or "still unclear" answers precede later misses on the same LO (directional, with an interval) |
| **Full solution graphs** | Unusable-hint replies with "Different approach" exceed 20% of hint sessions over a month |
| **A CAS calculator in the workbench** | The owner asks. It would need its own assistance mapping |
| **Photo of handwritten work as steps** | DL4's `image_transcription` route is merged |
| **Workbench and figures on video transcripts** | The owner works exercises from transcript sources |
| **Randomized hint-quality experiments** | Not planned: they would withhold better help on purpose |

---

## 18. Cross-spec notes (record when each phase merges)

- **P3 Reader spec.** §5.4's inquiry thread is implemented through `question_events.resolution` and branch parents, with no projection table. §1.3's "syntopic comparison UI" exclusion is lifted by RW4a under §7.1–7.2's source-local rules (display only; no stored relations). Invariants 1, 6, 9 and 10 are restated as W12, W1, W2 and W7.
- **Quick-check producer.** Gains `scope_kind` (section, inquiry, selection) and `question_style` (recall, next step, why step). Section behaviour is unchanged; the section lookup filters on scope.
- **Daily loop.**
  - **DL2 (request):** the dated "Check once" branch reads `commitment_versions.due_hint` when present and falls back to `capture.test_me_later_days`; RW6b's follow-ups depend on it (§9.3). DL2's provider fills DL1's existing `check_once` scheduled-check kind (`daily_plan/lanes.py:74`). Reader follow-ups can make several checks due on one day; the plan's minutes, not a count, bound how many are served (§9.3 item 6).
  - DL1's learner-pick block serves RW3's "Check me", RW4a's "Practice this question" and RW4b's chosen exercise.
  - DL3's "Practice on…" box and RW4a's "Practice this question" are the same `find_practice` call; build one RPC and reuse it.
  - DL4's pre-questions and RW1's scoped questions share the quick-check producer.
  - DL1's re-entry can show RW6a's card.
- **Router.**
  - `LearnerStateCardV1` gains the "Reader activity" section from `reader_activity_for_card` (RW6b).
  - **§15.3's `search_sources(query)` is RW4a's `find_sources`**, with its policies; the existing `reader.source_search.search_sources` is the legacy keyword search and keeps its name. §15.3's "When nothing fits" generation stays the router's.
  - The Reader's in-session help (hint level choice, cues) is not a router decision (router §1).
  - **R2:** each pending reader follow-up becomes a block candidate valued with robust EVSI like any other (router §3), so the router, not the order of lanes, decides whether it is served on a crowded day. RW6b's valuation receipt uses R1's field names (`probe_eig`, `evsi_assignment`) so R3's replay reads both.
- **Embedding consumers.**
  - T6 gains consumers (workbench bridging, discovered cues, the library organizer, compare, exercise search) and one thin function (`find_sources`). R1–R6 hold.
  - `judge_listwise` gains three tasks (`passage_cue`, `library_contribution`, `followup_relevance`).
  - `PracticeConstraints` gains `unattempted_only` and `exclude_family_ids`.
  - T1's matcher gains no kind. B4's text-only decision stands.
- **Blind grading and diagnosis.** The grader is unchanged (G6). The diagnoser's context gains the current attempt's workbench trace when one exists (`+workbench-v1`), so contexts without one hash as before. The Guide reads the diagnoser's overlay (RW3a).
- **Learner field.** Workbench assistance flows into `hints_used` and `primed`, so the `+hints` arm sees it. No new signal source in v1 (§5.6, §17).
- **Decision value and probe EIG.** RW6b is the first live consumer of `scheduling/evsi.py`'s `robust_evsi` and `rank_feasible`, and a new consumer of the probe-EIG functions, through an adapter that writes no learner state (§9.3). It adds no decision parameter; λ, the burden and the nat-to-minutes scale stay the registry's. Its receipts are an input to the decision-value spec's readiness audit (§9 there).
- **Learner-text gaps.** One new source adapter (`workbench_stuck`, RW2b). Reader questions, including "what's still unclear?" and tutor questions from library asks, are already sources. Named gaps become RW3b cue targets.
- **Knowledge model.** Cue links and organizer lines are labels. They never touch facet identity or the semantic graph.
- **Mobile.** No new phone RPC. Every new RPC is pinned desktop-only.
- **Handoffs.** Add a "Reader workbench" row to `implementation_handoffs.md` §1 per phase, using §19.

---

## 19. Agent prompt template

Fill in `<phase>` (RW1a … RW6b), the phase row from §13 and the base branch. Give it to a fresh agent in the repo. The review and fix steps follow `implementation_goal.md` §2.

```text
Implement LearnLoop reader-workbench phase <phase>, as specified in
docs/specs/spec_reader_workbench_v1.md (§13 row "<phase>", plus the sections that row
cites, §3.4 and §20).

Before coding, read: CLAUDE.md; docs/specs/implementation_handoffs.md §0 (standard rules
and invariants); spec_reader_workbench_v1.md in full; spec_p3_reader_integration.md §1.1;
docs/specs/daily_loop_frictionless_defaults.md; the sections of other specs the row names;
db/table_roles.py; docs/algorithm-change-playbook.md. Then write a short plan (files,
migrations, successor and kill switches, spend caps and model routes, judgment_ledger
writes, tests) to docs/reviews/reader-workbench-<phase>.md and proceed.

Work in your own worktree on a new branch reader/<phase>, created from <base branch>.
Follow §0 of the handoffs and §2 of the spec, especially:
- reuse before building (W13): T6 for retrieval, practice_index/listwise.judge_listwise
  for every listwise judgment, find_practice for practice, the quick-check producer for
  questions, learner-text gaps for learner text, DL2's "Check once" for follow-ups,
  and the existing probe-EIG and scheduling/evsi.py functions for valuing them (§9.3);
- no new interaction_events kind and no new reveal kind (payload `event` fields and
  the tutor_answer kind with a workbench basis instead);
- reading, help, cues, figures, recaps and inquiry status never write evidence; the
  only evidence is a submitted attempt, with assistance recorded as §5.4 says;
- the grader stays blind (G6); retrieval follows find_sources' policies (§7.2);
- no algorithm successor unless §12 names one for this phase; if you find one is
  needed, stop the affected part, record why, and take the next free mvp-0.N tag only
  with the orchestrator's agreement; with each kill switch off, behaviour is
  byte-identical;
- recompute the latest DEFAULTS_SNAPSHOT_BY_ALGORITHM entry for new config keys, with a
  "no scoring, scheduling, projection or serving change" note;
- replay makes no model or embedding calls; paid outputs are persisted inputs;
- every paid step uses the spend framework with --dry-run; Codex is allowed for every
  LLM role and is recorded estimated_only; decider tasks never fall back to chat;
- no live or paid AI calls in tests (fakes only); paid runs only on learnloop.db.copies
  backups under fixtures-local/, dry-run first; never commit changes to
  fixtures/linear_algebra, fixtures/probability or fixtures/arxiv_v2;
- if the spec contradicts the code, record it in the review file, take the
  conservative option (switch off, no evidence writes) if work can continue, else stop.

Done means: the phase's gates (§14) pass; its listed tests exist and pass;
uv run lint-imports --no-cache, uv run pytest -n auto and uv run pytest -m durability
pass; npm run typecheck && npm test pass; the DB reference scripts pass if the schema
changed. The review file lists what was built, deviations, test results with pass
counts, files touched, migrations, owner-run commands (dry-run first) and open
questions. Commit with clear messages; do not merge or push.
```

---

## 20. Integration review (2026-10-12)

An Opus 5.5 reviewer checked every phase against the code on `main` at `68213d96`, the in-flight branches (`merge/dl1`, `router/r1`, `learner/text-gaps`, `providers/chatgpt-plan`, `facets/identity`, `origin/feat/reader-clarification-branches`) and the architecture specs. It then took a Codex reviewer's ROI list (job `20261012-222309-txa3sX`) and revised this spec in place.

### 20.1 What changed, and why

| Change | Why |
|---|---|
| Every phase split into a first slice (a) and a model slice (b); RW7 deferred | The first draft bundled cheap learner benefits with new infrastructure (Codex's main point). Each "a" slice now ships alone, mostly from existing parts. Reading paths weren't in the owner's reply, needed DL2 and a successor, and had the lowest ROI |
| No new `interaction_events` kinds; payload `event` fields on existing kinds | The kind CHECK means every new kind is a full rebuild of a large, FK-referenced table (§3.4 item 4) |
| Reconnect questions: `scope_kind` and `question_style` columns, section lookup filtered | `section_id` is `NOT NULL` and reuse was "newest row for the section", so passage rows would have shadowed section checks |
| The Reader workbench submits through `submit_attempt`, with the visible source as one hint-equivalent | The first draft's `administer_reading_question` path grades and diagnoses nothing (§3.4 item 3). The hint-equivalent rule reuses existing semantics (assisted: schedules, never certifies), so there is still no successor |
| `tutor_answer` reveal kind with a workbench basis, not a new kind | Avoids a `reveal_events` rebuild; a workbench hint is tutor prose |
| Symbolic checks narrowed to three transformations, via PF's LLM-written check with a negative control | No LaTeX parser is installed; "follows from" in general is large (Codex A12) |
| No new field signal from the workbench | Field signals feed Phase 6 serving, so a new source is a successor (§5.6) |
| Stuck steps reach learner-text gaps through one adapter | The pipeline is the observation compiler; reader questions already reach it |
| Bridging runs after the hint, never before | T6 retrieval alone measured about 7 s |
| Practice screen: "Work in steps" is opt-in, not the default | Changing the default answer surface of the daily plan before the RW2 checkpoint risks the daily loop's latency and flow |
| RW3a fixes the Guide's statement under the split | The Guide reads raw `error_events` and misses the diagnoser's overlay on split vaults (§3.4 item 1) |
| RW3b uses T6 retrieval plus `judge_listwise`, not new T1 match kinds | T1's judge is pairwise same/different; cue relevance is a listwise judgment, and that judge already exists with ledger caching |
| No LLM role index; roles from ingest's `role_hint` | Ingest already labels roles deterministically and T6 already excludes exercises and solutions (§3.4 item 2) |
| `find_sources` cut to three policies; `post_attempt` and `authoring` dropped | T6 keeps the feedback context item-bound on purpose; PF's source-anchored path has its own retrieval |
| Compare is display-only; no claims extraction, claim matcher or `source_object_relations` rebuild | Codex A9: test demand before the infrastructure |
| The cross-source tutor uses the `reader` context with a pinned-span provider | `library` questions require a note |
| Router §15.3's `search_sources` is named as `find_sources` | `reader.source_search.search_sources` already exists |
| RW6 follow-ups are DL2 "Check once" commitments with `due_hint`; generation deferred; `find_practice` gains two filters | Reuses DL2's scheduled-check mechanism instead of a new serving class, removes the `reader_followup_v1` successor (with a stated fallback), and keeps generation (CPU-slow, batch) off the session path |
| Successor tags: no named tags; "the next free `mvp-0.N` at merge" | The chain is linear (DL1 `mvp-0.14`, R1 `mvp-0.15`, then learner-text gaps); named tags conflicted with it |
| Defaults fingerprint recompute required per phase | Every new config key moves the pinned snapshot (§3.4 item 9) |
| Branch port facts corrected | 8 backend tests, not 12; conflicts are in `handlers/reader.py`, not `ReaderScreen.tsx` |
| Rollout yields to the goal's tracks; at most two Reader phases open | The workbench is not in the goal's definition of done; Codex capacity is limited (B7) |

### 20.2 Implementability findings by phase

- **RW1a.** Buildable now. The port is about 700 lines with three Python conflicts; the rail split is a mechanical move of a 3,991-line component and is the largest part. One small migration.
- **RW1b.** Buildable on `main`: the Decider client and `ChoiceQuestion` exist. It needs two `DECIDER_TASKS` entries, config routes, a Decider question set, and a producer prompt for the two new styles. The Decider adds about 2 s to typed intents only.
- **RW2a.** Buildable on `main`. New: two tables, the step editor around `LiveMarkdownEditor`, a write queue, and opening a practice session from the Reader (`start_session`). The frontend is the bulk; the practice-screen button touches `PracticeScreen.tsx`, which `learner/text-gaps` also edits (+13 lines).
- **RW2b.** The largest phase. New: two chat routes, one decider route, the contract checker, PF-pattern checks, feedback, the chooser's typed state assembly (capability ledger, facet timeline, predictor), the diagnoser context extension, and the text-gaps adapter. Latency depends on the ChatGPT-plan provider; without it the phase works but likely misses the 10 s target on Codex.
- **RW3a.** Small: one backend fix and a frontend margin layer over the Guide plan the rail already loads.
- **RW3b.** Medium: per-target retrieval and a listwise task, two tables, background scheduling on source open. Its gap targets need learner-text gaps merged.
- **RW4a.** Medium: `find_sources` is a thin composition; the organizer and compare are listwise tasks; the tutor needs a pinned-span provider; the library UI changes.
- **RW4b.** Small to medium: a role-filtered search and a hand-off to `import_exercises`.
- **RW5.** Medium to large even narrowed: two evaluators kept in step by a golden corpus, a renderer, a verifier using the sandbox, a figure route with image input. Independent of everything else.
- **RW6a.** Small to medium, all reads. Its summary is reused by RW6b.
- **RW6b.** Medium, blocked on DL2 (not built) and its `due_hint` handling.

### 20.3 The Codex ROI list

| Item | Verdict | Where |
|---|---|---|
| A1 Margin cues from the existing Guide first | **Folded** (RW3a), with the split-overlay fix it needs | §6.2 |
| A2 Resumable scratchpad first | **Folded** (RW2a), reusing `LiveMarkdownEditor` and the draft-queue pattern; "leave" vs "abandon" | §5.1 |
| A3 "This doesn't connect to my work" on hints | **Folded**, used immediately; also drives the strategy-change rule and the solution-graph trigger | §5.2, §17 |
| A4 Workflow funnels with denominators, latency, failures; optional walkthrough | **Folded**, on existing event kinds | §4.1, §15 |
| A5 Recap on return, before the scheduling dependencies | **Folded** (RW6a) | §9.1 |
| A6 "Predict the next step" / "why this step works" | **Folded** into RW1b through the quick-check producer, not a new engine | §4.2 |
| A7 Narrow the first figure | **Partly folded.** Kept the declarative grammar (it generalizes across the owner's three subjects; templates would be per-topic code), but cut the renderer's integrals, PMF bars and shading, kept two panel types, and record unsupported kinds | §8 |
| A8 Connect each explanation to what happened afterwards | **Folded as a report** over existing rows (assists, manifests, attempts), associations only; no new table | §15 |
| A9 Smaller syntopic experience first | **Folded**: grouped sources, contribution lines, pin and compare; no role labelling, claims or relations | §7.3 |
| A10 Exercises from sources when nothing fits | **Folded** (RW4b) | §7.4 |
| A11 Confidence vs independent success | **Folded** as optional, logged-only confidence (the existing `answer_confidence`) and a calibration block | §5.4, §15 |
| A12 Narrow symbolic checks | **Folded**, three transformations, with coverage reporting | §5.3 |

None was rejected outright; A7 was folded in part, with the reason above.

### 20.4 Remaining risks

1. **Hint latency.** RW2b's value depends on fast hints. Without the ChatGPT-plan provider (and the owner's sign-in), Codex hints will likely exceed 10 s. Mitigation: authored hints first, the time-boxed chooser, bridging after the hint, the latency block.
2. **Reconciliation quality is a model capability.** The contract catches structural failures (no citation, wrong checkpoint, repeated strategy), not a plausible-but-unhelpful hint. The "doesn't connect" rate is the measure; a fake-model test can't prove it.
3. **The source-visible hint-equivalent** is an interpretation of existing semantics. The RW2a reviewer must confirm it against `resolve_attempt_activity_policy` and both certification projections; if they disagree, it becomes a successor.
4. **The follow-up "no successor" ruling** (§9.3) relies on the learner-text-gaps precedent and on DL2 reading `due_hint`. If DL2 lands without it, follow-ups fall back to its fixed 7-day date; if the reviewer rules it a serving change, RW6b takes a tag. Without a count cap, the ruling also rests on the plan's minutes bounding what is served (DL1 §6.1–6.2); a reviewer may judge that uncapped checks change the maintain lane's composition enough to need the tag.
9. **First live EVSI.** RW6b is the first consumer to act on `evsi.rank_feasible`, whose decision parameters (λ, burden, 60 minutes per nat) are labelled heuristic and uncalibrated. A badly scaled nat-to-minutes value schedules too many or too few checks. Mitigations: re-valuation retires checks that stop paying, every check is labelled and undoable, the plan's minutes bound the daily cost, and the valuation-calibration block (§15) measures predicted against realized information.
5. **ReaderScreen churn.** Every phase touches the Reader frontend; the rail split must land first and phases must stay serialized (at most two open).
6. **Data volume.** At n=1, the holdout, calibration and intervention reports will be thin for weeks (blocker B2). They are reports, never gates.
7. **The Rust toolchain (B3)** blocks the owner's in-app check of any new desktop UI until it is fixed.
8. **Text-gaps coupling.** RW2b's adapter and RW3b's gap targets assume the text-gaps interfaces as built on its branch (`LearnerText`, `named_gaps_for_card`); a review change there would ripple here.

### 20.5 Build order, dependencies and effort

| Order | Phase | Depends on (merged or in flight) | Effort |
|---|---|---|---|
| 1 | RW1a | `main` only. The port's `tutor_qa.py` hunk is small against `learner/text-gaps` | M |
| 2 | RW3a, RW6a, RW2a (in parallel, two at a time) | RW1a's rail split | S, S–M, M |
| 3 | RW1b, RW4a | RW1a; DL1 merged for learner picks (optional) | S–M, M |
| 4 | RW2b | RW2a; `providers/chatgpt-plan` merged and signed in; `learner/text-gaps` merged | L |
| 5 | RW3b, RW4b, RW5 | RW3a + text-gaps; RW4a; RW1a | M, S–M, M–L |
| 6 | RW6b | DL2 merged with `due_hint`; RW2a; `main`'s EIG/EVSI modules. R1 recommended (receipt field names); R2 later for router-valued serving | M–L |

In total about five to seven weeks of agent work through the implement–review–fix loop, serialized on the Reader frontend.

### 20.6 Start now, or wait?

**Start RW1a now; hold everything else until its dependencies land.** RW1a mostly ports finished, tested work and splits the rail. No in-flight branch touches `ReaderScreen.tsx` or `learnloop/reader/`, and its only overlap (`tutor_qa.py` with learner-text gaps) is a few lines. It needs no model route and no successor. It is also the prerequisite for every other phase, so it removes the main merge hazard early. Two conditions: the integration queue (DL1 now, then R1, facet identity, learner-text gaps, the ChatGPT-plan provider) keeps priority for merges and reviews, and RW1a merges after whichever of those is ready first. RW3a, RW6a and RW2a can follow straight after RW1a. **RW2b should wait** for the ChatGPT-plan provider (latency) and learner-text gaps (its stuck-text adapter). **RW6b must wait** for DL2.

### 20.7 Owner decision (2026-10-12): follow-ups are valued, not counted

**The owner:** "Follow up checks shouldn't be hardcapped artificially at one a session/2 a day. We want learnloop to prioritize EVSI/EIG and multiple follow ups might be high ROI for this to search for the true misconception or decide between hypotheses/decide between actions."

**What changed:**

| Before | After | Where |
|---|---|---|
| At most one follow-up per session and `followups.max_per_day` (2) a day | No count cap. Value of information chooses, numbers and dates follow-ups; the plan's finite minutes and a spend cap bound them | §1, §9.3, §11, §16 D17 |
| An LLM chooser (`followup_chooser`) picked the one capability most worth checking | The existing machinery values every candidate: probe EIG over the open hypotheses (`probe_families.py:467`, `probes.py:786`, `followups.py:1482`), EVSI for the pending decision (`evsi.py:199`), ranked and stopped by `evsi.rank_feasible` (`:366`), with greedy conditional EIG so duplicates drop out. The model only judges relevance (`followup_relevance`) | W4, W13, §3.2, §9.3 |
| One date rule (effective due, 1–14 days) | Dated by purpose: discriminating checks next day, retention checks at effective due; `max_wait_days` 14 is a time cap | §9.3 item 4 |
| — | Daily re-valuation retires follow-ups whose question has since been answered, with the reason shown and undo | §9.3 item 7 |
| One follow-up line with undo | Every check listed with date, purpose and the valuation as LearnLoop's estimate; undo each or all | §9.1, §9.3 |
| — | Valuation receipt on the digest row; a valuation-calibration report block | §9.4, §15 |
| Gates G26–G27 checked the caps | G26–G27 check the stop rule, conditional valuation, dating and minutes; G35 checks reuse | §14 |
| RW6b: DL2 and RW2a; size M | Also `main`'s EIG/EVSI modules; R1 recommended for receipt names; R2 later values pending follow-ups as block candidates; size M–L | §13, §18, §20.5 |

**Every number that remains is a cap on money or time, never a learning threshold** (W4): `followups.max_daily_cost_usd` (money), `followups.max_wait_days` (time a claim waits), `followups.fallback_days` (a dating default when there is no FSRS state), and the plan's own minutes and lane shares (DL1). The valuation's λ, burden and nat-to-minutes scale are not new: they are the existing decision parameters, labelled heuristic in `robust_composition.py`, and RW6b's receipts are data for calibrating them (§20.4 risk 9).

**Not changed here, and worth the owner's look:** the same principle would also apply to count caps that live in other specs and code. RW6b neither applies nor changes them: `probe.episode.session_qualifying_observation_cap` (4) and `maximum_observations` (4) for probe episodes (`config/schema.py:224`, `:209`); `scheduler.followup.max_interventions_per_lo_per_session` (1) for post-attempt follow-ups (`schema.py:40`, enforced at `diagnosis/followups.py:339`); `teach_back.session_cap` (1); and `plan.project_probes_max_per_day` (4) in the daily plan. Each is a candidate for the same change in its own spec.

---

*Related: `docs/brainstorming/Improving Reader's design.md` (source) · `docs/reviews/reader-dialogue-coverage.md` (what the dialogue proposed and where it went) · `decision_value_and_commissioning_spec_v1.md` (§6.4) · `spec_probe_eig_redesign.md` (§7) · `spec_p3_reader_integration.md` · `spec_reader_quick_check_producer.md` · `spec_daily_loop_v1.md` (§5, §6.1, §6.9, §6.10) · `spec_embedding_consumers_v1.md` (§1, §5.9, §9) · `spec_action_router_v1.md` (§3, §4, §15) · `spec_blind_grading_diagnosis_split_v1.md` · `spec_learner_field_v1.md` (§3.1) · `implementation_handoffs.md` §4 · `docs/reviews/slice-2-t6.md` · `docs/reviews/stuck-prompt.md`*
