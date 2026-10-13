# Reader workbench: inquiry, worked problems, passage cues, syntopic reading and loop closure (v1)

**Status:** draft for owner review (2026-10-12), **revised after the integration review the same day** (§20). The review checked every phase against the code on `main` at `68213d96` and against the in-flight branches. It then split each phase into a small first slice that ships a learner benefit on its own and a second slice that adds the model work. It also folded in a Codex reviewer's high-ROI list (§20.3). **Owner decision, 2026-10-12 (§20.7):** cold follow-ups have no count cap; the existing EIG/EVSI machinery chooses, numbers and dates them (§9.3). A coverage audit of the source dialogue against this spec is `docs/reviews/reader-dialogue-coverage.md`. **Owner decisions, 2026-10-12, restoration (§20.8):** every idea the audit found narrowed, dropped or deferred is restored into a phase, or listed in §17 as an explicitly labelled DEFERRED item with what it would take and a trigger. W1 now separates three tiers of signals and allows the middle one to steer hypotheses and routing, never mastery. The backend that serves canonical sources as practice and probes is a separate track, `docs/specs/spec_source_practice_and_probes_v1.md` (branch `sources/canonical-practice`); this spec consumes it and does not design it.

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
- **No artificial count caps** (owner, 2026-10-12): value of information, time and money bound how much LearnLoop does. Display limits that protect attention (the cue density) are labelled as such and the learner can change them.
- **Codex on the owner's ChatGPT subscription** may run every paid LLM role, recorded as `estimated_only`. The Decider is `perplexity/pplx-decider-v1.1-27b` on OpenRouter (router R0, merged). The ChatGPT-plan provider (merged on `main` at `57d31c63`; the owner's sign-in pending) is the fast route for short structured calls.

**Relationship to other specs:**

| Spec | Relationship |
|---|---|
| `spec_p3_reader_integration.md` | The Reader's contracts (render views, anchors, capture, salience firewall, restoration). This spec keeps every §1.1 invariant. It implements P3 §5.4's inquiry thread without a projection table, and lifts P3 §1.3's "no syntopic UI" exclusion under P3 §7's source-local rules |
| `spec_reader_quick_check_producer.md` | Its producer gains a passage scope and two question styles (RW1): the reconnect check, "let me try the next step" and "why does this step work" |
| `spec_daily_loop_v1.md` | Consumed, never duplicated: DL1's reading blocks (§6.10) and learner-pick blocks, DL2's "Check once" (§5.2), DL3's "Practice on…" (§6.9), DL4's pre-questions (which share the quick-check producer). RW6b needs DL2 |
| `spec_embedding_consumers_v1.md` | T6 (§9, merged) is the only retrieval substrate: `search_spans`, `teaching_scope`, `TutorSpanProvider`, `verify_spans`. Phase 5b's shared listwise judge (`practice_index/listwise.py`) is the only judge mechanism for cues, the organizer and the follow-up pick. `find_practice` (§5.9) proposes practice. PF supplies the sandbox and its verified-check pattern |
| `spec_source_practice_and_probes_v1.md` (branch `sources/canonical-practice`, written in parallel) | **Owns the backend** for canonical sources as practice and probes: textbook exercises as practice candidates (the audit's RW4c), the discriminating search (`intent` and `target_hypotheses` in `PracticeConstraints`, ranked by EIG), `find_sources` intents (`remediate`, `alternative`, reading misconceptions' `correction_source_span_ids`), real callers for `find_practice`, and the router §15.3 tool. This spec consumes it in RW1c, RW2b, RW3, RW4a/b and RW6b and never duplicates its design (§18) |
| `ux_reader_workbench_v1.md` (written in parallel) | The experience design for these phases: how they look, feel and sequence for the learner. This spec owns behaviour, contracts and data; that document owns presentation (§20.8) |
| `spec_action_router_v1.md` | The Reader's in-session help is not the router (two timescales). RW6b adds a reader section to `LearnerStateCardV1` (§4). RW4's `find_sources` is the tool that router §15.3 calls `search_sources` (§18); the tool itself is now built by the sources spec |
| `spec_blind_grading_diagnosis_split_v1.md` | The grader stays blind. The diagnoser sees the workbench trace of the current attempt only. Cue targets read the diagnoser's overlay, never raw grader rows (§3.4) |
| `spec_learner_field_v1.md` | Workbench assistance reaches the field through `hints_used` and `primed` on the attempt row, which the field already reads. Formative reader signals steer hypotheses and routing under F2 (W1). Workbench field signals are RW2d, an algorithm successor under F3 (§5.11) |
| `implementation_handoffs.md` §4 | The learner-text-gaps pipeline is the dialogue's "observation compiler". Reader questions already reach it as tutor questions; this spec adds two source kinds, `workbench_text` (RW2b) and `reader_formative` (RW1b, RW5a), with one migration that widens the pipeline's `source_kind` CHECK (§3.4 item 13). No second compiler |

**Citation convention.** Every `file:line` was checked on `main` at `68213d96` (migration head 179, latest algorithm `mvp-0.13`). Citations added by the restoration (§20.8) were checked on `main` at `57d31c63` (migration head 180, DL1 at `mvp-0.14`, the ChatGPT-plan provider merged). Python paths are relative to `src/`, frontend paths to `apps/learnloop-tauri/src/`, migrations to the repo root. Unmerged work is named by branch.

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

The restoration (§20.8) carries the rest of the dialogue into the same Reader:
- **The learner's books become the instructional substrate** (round 3). The tutor looks things up in them on its own, offers another source's explanation when one didn't help, and offers a textbook exercise to practise or to tell two explanations apart. The retrieval and selection behind this is `spec_source_practice_and_probes_v1.md`; the Reader is where the learner meets it.
- **The workbench asks before it repairs.** When two explanations of an error are open, the first help is a short question whose answer tells them apart (§5.2), as in the dialogue's central scenario.
- **What the learner says while reading counts as signal, never as grade.** Missed predictions, "still unclear", next-step attempts and check verdicts steer hypotheses, hints and follow-ups (W1, tier 2).
- **Explorable figures show areas, sums and motion**, starting with the dialogue's own two-sided exponential (§8). **Comparisons can be kept**, as proposals in the existing source-object layer (§7.8). **Reading paths** say what each section is for at the depth the learner chose (§10).

Four rules carry over from the dialogue:
1. **Preserve the learner's evolving reasoning,** not only what was asked and whether the final answer was right.
2. **Help is a deliberate, recorded quantity.** The learner can always get more. What LearnLoop offers first adapts to prior knowledge and struggle, and every piece of help is recorded as assistance, so assisted success is never mistaken for independent competence.
3. **Sources keep their identity.** What a source claims, what LearnLoop infers and what the learner believes stay separate. Cross-source reading preserves differences instead of fusing them into a consensus.
4. **No intervention is a legitimate outcome.** Cues are marks in the margin, never interruptions.

---

## 1. Scope

**In scope (v1).** Each phase has a first slice (**a**) that ships on its own, mostly from existing parts, and a second slice (**b**) that adds the new model work. The order is in §13.

Phases marked *(restored)* were added or widened by the owner's restoration decision (§20.8); the dialogue rows each one restores are listed in `docs/reviews/reader-dialogue-coverage.md`.

- **RW1a. Inquiry.** Port the unmerged `origin/feat/reader-clarification-branches` (branching Ask); split the rail into components; inquiry status on the existing outstanding-question queue; breadcrumbs and "back to where I was"; a reconnect line with a passage-scoped check; the reader report's workflow funnel. *(Restored:)* a friction audit before and after; one interaction model on every source kind the Reader opens.
- **RW1b. Intent box and active reading.** A selection intent box routed by the Decider (the palette stays one key away); "Let me try the next step" and "Why does this step work?" on a selected derivation or worked example. *(Restored:)* the five learner intentions organize the actions; "What does this assume?", "Another way to see this" and "Reconstruct this later"; missed answers become learner text (`reader_formative`).
- **RW1c. A tutor that looks things up** *(restored)*. In the Reader, the tutor retrieves from the learner's sources on its own, answers in three modes (the source's own words, a grounded explanation, a bridge to the learner's work), offers "another way" and "that didn't help" through the sources spec's intents, and offers practice, comparison and figures as buttons the learner presses.
- **RW2a. The workbench as a resumable scratchpad.** Step-by-step work beside the source, saved as it is typed, reopened by "Resume this problem" after navigation or restart; Submit through the ordinary attempt path with the source-visible rule (§5.4). No model calls of its own.
- **RW2b. Checks and adaptive help.** "Check my work" (first questionable step), the help ladder with the reconciliation contract, the adaptive first offer, symbolic checks, "this doesn't connect to my work" feedback on every hint, workbench text into the learner-text-gaps pipeline. *(Restored:)* a discriminating question first when rival explanations are open; the check's error-kind guess, step dependencies and assumptions; more transformation kinds; in-session updates.
- **RW2c. What helps this learner** *(restored)*. A replayable record of which help and which passage preceded recovery, read by the hint writer and the chooser; a logged draw between equally good passages; worked examples that take the learner's own route (`find_examples`); "Compare methods" after a correct answer.
- **RW2d. Workbench signals in the learner field** *(restored; algorithm successor)*. Mid-work stuck steps and help before work become field signals, live behind a kill switch.
- **RW3a. Margin cues from the Guide.** The Guide's existing `recent_misunderstanding` passages shown as restrained margin marks, with the misconception read from the diagnoser's overlay.
- **RW3b. Discovered cues.** New passage links found per open hypothesis, named gap or demonstrated facet through T6 retrieval and a listwise judge; a logged holdout. *(Restored:)* cues ordered by the probability that their target is still open; a "Try this step first" cue on worked examples; source-authored contrasts preferred; a learner density control.
- **RW4a. Library questions and source comparison.** "Ask" in library search: passages grouped by source and role with a one-line contribution each, the tutor on request; pin passages from different sources and compare them; "Practice this question" through `find_practice` (with the sources spec's candidates once merged); the `find_sources` function. *(Restored:)* prerequisite and application passages through the concept graph; facet targets; a narrow `post_attempt` policy.
- **RW4b. Exercises from my sources.** The Reader's view of the sources spec's textbook-exercise candidates: passage, page and "use this one". Until that spec merges, the learner-initiated fallback search described in §7.4.
- **RW4d. Syntopic reading as a tool** *(restored)*. `compare_sources(query, facets, requested_perspectives)`, callable by the learner and the tutor; source claims, LearnLoop's inferences and the learner's own take kept apart; "Keep this comparison" stores proposals in the existing `source_objects` and `source_object_relations` layer.
- **RW4e. Instructional roles** *(restored)*. Several roles per passage (including counterexample, contrast, intuition, prerequisite, alternative treatment), with confidence and provenance, accumulated as `source_objects` proposals from judgments already being made, plus an owner-run batch labeller; used as positive retrieval filters.
- **RW5a. Explorable figures.** "Make this explorable" on a selected equation, figure or region of a figure: a declarative, verified figure spec drawn by a trusted renderer, with predictions. *(Restored:)* shaded areas with integral readouts, PMF bars and sums, parameter animation, region selection, "what changed?" answers — enough for the dialogue's two-sided exponential.
- **RW5b. More figure kinds and offered figures** *(restored)*. Heat maps, vector fields and trajectories (objectives, gradients, attention-like weights, dynamical systems); figures offered by the tutor and the library when a retrieved equation can support one.
- **RW6a. "Last time here".** A deterministic recap on returning to a source: last position, open inquiries, unfinished problems, missed predictions, with resume links. *(Restored:)* the session's formative records (`ReaderObservationV1`); an optional "Wrap up" in under a minute.
- **RW6b. Digest, router card and cold follow-ups.** An optional narrative over the recap, reader activity in the router's learner-state card, and cold follow-ups served through DL2's "Check once". Follow-ups have no count cap: the existing value-of-information machinery (probe EIG over the learner's open hypotheses, `scheduling/evsi.py` for the next decision) chooses, numbers and dates them, and the daily plan's finite minutes and the spend caps bound them (§9.3; owner decision 2026-10-12, §20.7). *(Restored:)* formative questions; textbook exercises and typed intents from the sources spec; discounting what reading already showed; novelty labels; background generation when nothing fits; reopening the Reader where the topic was studied; open hypotheses and candidate actions on the card.
- **RW7a. Reading paths in the Guide** *(restored from the deferred §10)*. At the depth the learner picks, each section is core, prerequisite, enrichment, already shown or assumed, with a reason, overrides and one exercise worth trying. Display only.
- **RW7b. The plan follows the path** *(restored; algorithm successor)*. DL1's reading block opens the next core or prerequisite section, behind a kill switch.

**Consumed from `spec_source_practice_and_probes_v1.md`, never designed here:** textbook exercises as practice candidates, attached to families and verified; the discriminating search; `find_sources` intents; the router's retrieval tool. Each consuming phase works without it and gains it when it merges (§18).

**Deferred, labelled, with what each would take and a trigger (§17):** generated-code figures in an isolated surface; page-image retrieval; an OS-level or MCP learning service; local rerankers; learned cue and hint policies; formative signals as numeric observations; alternative reference routes in solution graphs; formal verification of proof steps; cross-learner data-driven hints; a learned, causal model of which help works for this learner; a randomized whole-workflow experiment; claim extraction over the whole library with a claim matcher; the router's availability pass (owned by the sources spec); a CAS calculator; photo-of-work input; randomized hint-quality experiments (not planned).

---

## 2. Standing constraints

- **W1. Reading and help are never evidence; what the learner says may steer.** This restates P3 invariant 6 ("Reading is not evidence", `spec_p3_reader_integration.md` §1.1, with §8.2's firewall) and the learner field's F2 ("Never evidence") and F3 ("Live changes go through the playbook", `spec_learner_field_v1.md` §1), and follows the field's own guard: "Signals change routing and predictor state, never evidence, mastery, certification or the demonstrated record" (§3.1). Signals fall in three tiers, as the dialogue proposed (round 2 §6):

  | Tier | What | May change | Never |
  |---|---|---|---|
  | 1. Engagement | Dwell, scrolling, highlights, opening a passage, cue taps, figure play, inquiry status, recaps, digests and narratives | Retrieval context, suggestions, display. `authority_class = 'salience_only'` (P3 §8.2) | Anything in the next column, or any hypothesis |
  | 2. Formative | Explicit learner answers and learner text that are not graded attempts: questions, "what's still unclear?", next-step, why-step and assumption answers, figure predictions and "what changed?" answers, "Check my work" verdicts on unfinished work, hints taken mid-problem, "this doesn't connect" text, answers to a discriminating question, "not relevant, because…" on a cue | **Hypotheses:** learner-text gaps names candidate prerequisites and misconceptions from the text, as it already does for reader questions. **Routing:** the level chooser, the next hint, cue targets, `ReaderActivityV1`, the field's question signals. **Follow-up valuation:** the open questions RW6b values (§9.3) | The **mastery posterior** (the facet and LO estimator), `grading_evidence`, `facet_recall_state`, `facet_capability_evidence`, certification, coldness, FSRS state and the demonstrated record. No numeric update of any posterior: tier-2 rows write no `probe_observations` and no estimator input. Numeric weak observations are deferred (§17). (What the learner was *shown* is still recorded as exposures and reveals, as today; that is a fact about the material, not a signal from the learner) |
  | 3. Independent performance | A submitted attempt, graded blind, carrying the assistance it recorded (§5.4) | Evidence, as today | — |

  - **The only evidence a workbench session produces is its final submitted attempt.** Abandoned work, checks and hints stay tier 2.
  - **Changing what is served is F3's business.** Tier-2 inputs to content (named gaps, follow-up commitments the learner can undo, cue marks) follow the learner-text-gaps precedent and take no successor. A tier-2 signal that changes serving, such as workbench signals feeding Phase 6's fast-track rule (RW2d) or reading paths steering the plan (RW7b), is an algorithm successor with a kill switch and receipts.
  - **"Posterior" in P3 invariant 6 means the mastery posterior.** The learner field's harness arms may use typed questions as weak predictor observations (field §3.1 item 2, activated only under its §7.4); W1 does not forbid what that spec plans.
  - **Mechanically:** no tier-1 or tier-2 row has a path to the evidence ingestion API (P3 §8.2), and the salience-firewall test covers every new payload `event` and every new learner-text source kind.
- **W2. Honest labels.** Every surface distinguishes source-authored, AI-written and learner-written content (P3 invariant 9). Model judgments are labelled as such. "Checked" or "verified" appears only when a non-LLM check (a sandboxed sympy check, an exact key, a quote match) passed. A cue never says the learner *is* confused, only that a passage connects to something they worked on.
- **W3. Generous defaults, live behind kill switches.** Every phase ships on by default with its switch. No step is added to protect a model.
- **W4. LLM judgment and value of information over constants.** First-offer help level and cue relevance are model judgments over typed learner state. Follow-ups and discriminating questions are valued by the existing EIG and EVSI machinery (§9.3, §5.2); a model judges only whether an item tests the capability and what each rival explanation predicts. Cues are ordered by the probability, read from existing state, that their target is still open (§6.2). Numbers in this spec are caps on money, time or display, never thresholds that decide learning. There is no count cap on follow-ups (§20.7).
- **W5. Learner text over skip buttons.** The intent box, "what's still unclear?", "I'm stuck" in the workbench, "this doesn't connect to my work" on a hint, and "not relevant, because…" on cues take free text. A one-tap path still exists (an empty box is allowed), as with "I'm stuck".
- **W6. Embeddings shortlist, judges decide.** No embedding score alone creates a cue, a role or a match (R1). Shortlists are top-k; a judge decides everything shown.
- **W7. Cold means no source cue.** P3 invariant 10 and `find_sources`' policies (§7.2): a cold attempt gets no source, hint, tutor or figure; opening one ends cold status. A source-visible attempt never certifies.
- **W8. Grading stays learner-blind.** The grader sees the final answer as today. Steps, hints, checks and learner history never enter `BlindGradingContext`.
- **W9. Replay makes zero model and embedding calls.** Every paid output (checks, hints, cues, organizer lines, figures, digests) is persisted and never regenerated on rebuild.
- **W10. Spend controls.** Every paid step uses the Phase 1 framework (`learnloop/ai/spend.py`): per-route caps, `--dry-run` on every batch command, receipts. Codex is `estimated_only`. Every LLM, Decider, verifier or learner-card verdict appends to `judgment_ledger`.
- **W11. Agency.** The learner can always ask for more help, turn cues off, hide the source before working, and undo every automatic action.
- **W12. The reading hot path never waits for a model** (P3 invariant 1). Cue links and organizer lines are computed in the background or on request and appear when ready.
- **W13. Reuse before building.** One retrieval substrate (T6), one listwise judge (`practice_index/listwise.judge_listwise`), one practice-proposal function (`find_practice`, extended only by the sources spec), one source-practice backend (`spec_source_practice_and_probes_v1.md`), one question producer (the quick-check producer), one learner-text compiler (learner-text gaps), one scheduled-check mechanism (DL2's "Check once"), one value-of-information machinery (probe EIG in `diagnosis/probe_families.py` and `diagnosis/probes.py`, EVSI in `scheduling/evsi.py`, reached through one candidate-valuation adapter shared with the sources spec), one per-source object layer (`source_objects`, P3 §7). A phase that needs a second one stops and records why.

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
| *Added by the restoration (checked on `main` at `57d31c63`):* | | |
| Per-source object layer: `OBJECT_TYPES` (claim, definition, procedure, worked_example, problem, proof_move, motif_or_passage, artifact), `RELATION_TYPES` (supports, contradicts, refines, alternate_definition, unresolved, learner_connects); `authorial_role` is free text; versions carry `revision_id`, citations carry span and quote | `reader/source_objects.py:19`, `:23`; `migrations/094_source_objects.sql:22`–`:69` | RW4d kept comparisons, RW4e roles |
| The LO graph: `LearningObject.prerequisites` and `.confusables`; concept edges `prerequisite`, `confusable_with` | `vault/models.py:330`, `:173` | RW4a concept-graph expansion, RW3b contrast cues |
| Span exposures and reading progress | `source_exposure_events` (`migrations/049_source_exposure_events.sql:8`, reader contexts since 092); `reader_section_progress` (`106_reader_section_progress.sql:6`) | RW6b exposure-aware discount |
| Misconception correction spans | `db/repositories.py:317` (`correction_source_span_ids`) | Read by the sources spec's `remediate` intent, which RW1c and RW3b consume |
| Original-region crop of a block | `reader/span_view.py:266` (`build_block_region`) | RW5a region selection |
| Familiarity discount | `learner/recall_coverage.py:293` (`familiarity_discount`) | RW6b valuation, with exposure added |
| Probe-EIG over a compiled instrument (one conditional row per hypothesis; zero EIG when every hypothesis predicts the same outcome) | `diagnosis/probe_families.py:467` (`instrument_expected_information_gain`) | RW2b discriminating questions |
| Count caps that the owner's 2026-10-12 decision lifts in a separate stage (§18) | `config/schema.py:224`, `:209` (probe episodes), `:40` with `diagnosis/followups.py:339`, `:625` with `scheduling/scheduler.py:568` (teach-back), `:1885` with `daily_plan/engine.py:462` (project probes) | Not changed here |

### 3.3 Unmerged work this spec depends on (2026-10-12)

| Branch | State | What this spec uses |
|---|---|---|
| `origin/feat/reader-clarification-branches` (`cf2cbe77`, 2026-10-08) | Built on PR #5, not merged | Branching Ask: explicit parents on the `reader_answer_submitted` payload, the branch tree (`screens/reader/ReaderAskBranches.tsx`), ancestor-only prompts. 8 backend tests (`tests/test_reader_branches.py`) and 9 frontend tests. No migration. `git merge-tree` against `main`: conflicts in `reader/reader_dialogue.py`, `tutor/tutor_qa.py` and `learnloop_sidecar/handlers/reader.py`; `ReaderScreen.tsx` and `api/dto.ts` merge cleanly |
| `merge/dl1` (`daily-loop/dl1`) | **Merged** to `main` as `19798a0c` (`mvp-0.14`) later on 2026-10-12 | Learner-pick blocks, reading blocks (§6.10), the plan's finite minutes that bound follow-ups (§9.3). DL1 touches no Reader file |
| DL2 | Not built on any branch | "Check once" (§5.2) and effective due (§5.3). RW6b's follow-ups need it; DL1's `ScheduledCheck` already reserves the `check_once` kind (`daily_plan/lanes.py:74`) |
| DL3 | Not built | "Practice on…" (§6.9); RW4a's "Practice this question" is the same `find_practice` call |
| `router/r1` | Built; in the merge chain as `mvp-0.15` | `router_decisions`, which logs each candidate's `probe_eig` and `evsi_assignment` but values nothing (`router/decisions.py:174`, `:441` on the branch); RW6b's valuation receipt uses the same field names (§9.3). R2 (not built) renders the card section RW6b adds and values pending follow-ups as block candidates |
| `learner/text-gaps` | Built and reviewed; in the merge chain as `mvp-0.16` | `diagnosis/text_gaps/` (`LearnerText` sources, `StuckTextSource`, `named_gaps_for_card()`). Reader questions are already a source (`tutor_question_text` reads `context = 'reader'`). Touches `tutor_qa.py` (+28 lines) and `PracticeScreen.tsx` (+13). Its `source_kind` columns carry a CHECK (`migrations/177_learner_text_gaps.sql:19`, `:88`), so new Reader source kinds need one widening migration (§3.4 item 13) |
| `providers/chatgpt-plan` | **Merged** to `main` as `57d31c63`; the owner's live sign-in is the remaining condition | Profile type `chatgpt_plan`: one HTTPS structured call, no tools, isolated turn; `learnloop ai latency` |
| `facets/identity` | Built; in the merge chain | Nothing directly |
| `sources/canonical-practice` | `spec_source_practice_and_probes_v1.md` being written (2026-10-12); its build is the separate backend track the owner asked for | Everything §18 lists under "Source practice and probes". Every consuming phase here works before it merges |

**Successor numbering.** `SUCCESSOR_CHAIN` (`algorithm_versions.py:99`) is linear. DL1 is `mvp-0.14` on `main`; R1 takes `mvp-0.15` and learner-text gaps `mvp-0.16` in the merge chain. New vaults start at `LATEST_ALGORITHM_VERSION`. This spec needs **two** successors, both restored phases that change what is served: RW2d (workbench field signals) and RW7b (the plan follows a reading path) (§12). Each takes the next free `mvp-0.N` tag at its merge, never a named tag. If a phase agent or its reviewer finds another is needed, the same rule applies.

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

*Found by the restoration (2026-10-12):*

13. **Learner-text source kinds have a CHECK.** `learner_text_gaps.source_kind` and `learner_text_gap_jobs.source_kind` accept only `tutor_question`, `stuck_answer` and `diagnosis` (`migrations/177_learner_text_gaps.sql:19`, `:88` on `learner/text-gaps`), and three tables reference `learner_text_gaps` by foreign key. The first draft's `workbench_stuck` adapter would have failed its insert. This spec adds two kinds, `workbench_text` (stuck steps, "doesn't connect" text, answers to a discriminating question) and `reader_formative` (missed next-step, why-step and assumption answers, "what still isn't clear" after a reconnect check, missed figure predictions with their "what changed?" text), in **one** widening migration: temp-then-rename with `PRAGMA foreign_keys = OFF`, a `foreign_key_check` before commit, and a durability-lane test. It lands in the first phase that adds an adapter (RW1b if learner-text gaps has merged by then, else RW2b). The dispatcher `learner_text()` (`sources.py:431` on the branch) gains the two kinds.
14. **`source_objects.object_type` has no counterexample, contrast or intuition.** The CHECK (`094_source_objects.sql:28`) admits eight types; `authorial_role` is free text. RW4e stores the finer instructional role in `authorial_role` and maps the type (worked example → `worked_example`, exercise → `problem`, definition or theorem → `definition` or `claim`, everything else → `motif_or_passage`). No rebuild.
15. **Relation types are coarser than a comparison.** `source_object_relations.relation_type` has no "equivalent" or "different assumptions". RW4d maps `equivalent` → `supports` (or `alternate_definition` between two definitions), `different_assumptions` and `different_notation` → `refines`, `disagreement` → `contradicts`, `unclear` → `unresolved`, and keeps the fine label in `library_asks.compare_json` beside the relation ids. No rebuild.

### 3.5 What the dialogue asks for that does not exist

- No branching or status on Reader inquiries beyond the flat `resolution` column.
- No workspace for solving: no step capture, no resumable work beside the source, no work-aligned hints, no localization before submission.
- No passage-level cue; the Guide's misunderstanding reason never reaches the text.
- Library search returns a ranked list without per-source contributions; nothing compares sources.
- No interactive figures.
- No re-entry recap, no reader input to the router, no follow-up check after assisted work.
- The tutor in the Reader sees only the selection and its neighbours (`tutor_qa.py:1299`, `_reader_source_spans`); it never forms its own query.
- Source objects and their relations are written as proposals but read by no retrieval or UI.
- No reading path says what a section is for.

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
- **"Check me"** asks the quick-check producer for one formative question scoped to the root passage (§4.3). Answered, the expected answer is revealed for comparison; it is never an attempt; "add to practice" escalates it through the existing path. When the learner marks their answer "didn't match", the answer becomes a `reader_formative` learner text (tier 2, W1; adapter in RW1b), so the pipeline can name what was missing.
- Ignoring the line does nothing; it disappears when the learner scrolls on (W12).

**Splitting the screen.** RW1a moves the rail into components (`screens/reader/AskRail.tsx`, `GuideRail.tsx`, `NotesRail.tsx`) after the port lands, so later phases don't fight over one 4,000-line file. It is a move, not a redesign: the existing `ReaderScreen` tests pass unchanged, plus the branch's.

**The reader report** (`learnloop reader report [--json] [--since]`, no model calls, no learner text) reports **workflows, with denominators**, not only counts:
- **selection → action → usable result → back to reading:** selections; actions invoked by kind; for model-backed actions, queued, completed, failed (with reason), cancelled and latency (p50/p95, model wait separated from learner time); whether the learner returned to the source passage within the visit;
- **inquiry:** inquiries opened, branch depth and breadth, resolved, dismissed, reopened, still open after 7 days; reconnect answers (yes / still unclear / check me);
- **visits:** visits, active minutes (idle excluded), time to first action after opening a source.

Each later phase adds its own funnel (§15). Model-backed rows carry model and prompt version so a report can be read per route.

**A friction audit before adding interface** (the dialogue's P0, restored). Before RW1a changes any UI, its agent writes a friction audit of today's Reader into the phase's review file: for six core workflows (ask about a selection and get back to reading; follow one prerequisite and return; import and work an exercise; find where else an idea is explained; capture "test me later"; resume after a restart), the number of steps, which of them work from the keyboard, where the learner waits on a model, and where context is lost. It is read from the code and, once the funnel has data, from the funnel. Every later phase's review file repeats the audit for the workflows it touched, so the friction a phase adds is visible. The owner's timed walkthrough (§15) stays optional; the audit needs no owner time.

**One interaction model on every source kind** (round 1's "consistent across books, PDFs, videos and notes", restored). Selection, the intent box, inquiry, cues, library questions, the recap and the workbench work wherever the Reader resolves a selection to a span: Marker markdown, the original-page view of a PDF, and video transcripts (`reader.watch_plan`). On the learner's own notes pane the intent box offers only the actions that need no source anchor (ask, test me later, help me remember, connect it). Figures from a transcript take the transcript text and no image. Each phase's tests include one transcript fixture.

### 4.2 RW1b: what the learner sees

**The intent box.** Selecting text opens a small box beside the selection: "What do you want to do with this?" with the cursor in it.
- The learner types in their own words ("why are the densities weighted?", "quiz me on this later", "make this a problem I can work"). Enter routes it.
- **Tab** (or clicking "actions") shows today's palette unchanged, so keyboard shortcuts keep working.
- An empty Enter runs Ask with no model call.
- The routed action shows as one line before it runs, for example "Asking · help me reason · change". "change" opens the palette with the text kept. There is no confirmation step.

**Routing** is one typed `ChoiceQuestion` to the Decider (route `ai.routing.reader_intent`, added to `DECIDER_TASKS`: never a chat fallback). The options are the actions that exist when the call is made: ask (with its answer mode); worked example, explain differently, why it matters; remember, test me later, connect it, mark confusing, not worth remembering; import as exercise; and, as later phases land, "work through this", "let me try the next step", "why does this step work", "what does this assume", "another way to see this", "reconstruct this later", "compare sources", "practice this question", "make this explorable", "what matters here", "what do I need first" and "where is this used".
- The learner's text becomes the question (for asks) or the annotation's learner text (for everything else).
- **If the Decider is unavailable,** times out (`reader_intent.timeout_seconds`, 4) or is spent out, the action is Ask.
- **Verdicts.** Every routing appends to `judgment_ledger` (task `reader_intent`, judge `decider`). A "change" appends the learner's correction (judge `learner_card`), so routing error stays measurable without a review chore.

**Five intentions organize the actions** (round 1 §1, restored). The dialogue's point was that what the learner is trying to do matters more than which panel is open. The palette and the Decider's options are grouped by intention, and the routed line names it ("Understand · asking · help me reason · change"):

| Intention | Actions |
|---|---|
| **Orient**: what matters, where to start, what I need first | "What matters here?" opens the Guide's reading path (RW7a); "What do I need first?" lists the passage's prerequisite LOs with their status and a prerequisite passage each (RW4a's graph expansion) |
| **Understand** | Ask (with its answer mode); explain differently; why it matters; why does this step work; what does this assume; another way to see this; compare sources; make this explorable |
| **Apply** | Work through this; let me try the next step; practice this question; import as exercise |
| **Consolidate** | Test me later; help me remember; reconstruct this later; check me; mark confusing; not worth remembering |
| **Transfer** | "Where is this used?" (a library ask with the applications expansion, RW4a); practice this in a new setting (`find_practice` with the session's facets and `unattempted_only`) |

The Decider returns the intention with the action; the report counts actions by intention (§15). The grouping changes no action's effect (G3).

**Active reading on derivations and worked examples** (the dialogue's "predict the next step" and "justify this step"). Two selection actions, also offered in the intent box:
- **"Let me try the next step."** The producer writes the question "What comes next after this line?" from the selection and the following blocks, keeping the next step as the expected answer. The learner writes their attempt; then the source's next step is shown beside it for comparison.
- **"Why does this step work?"** The producer asks for the justification of the selected step, with the source's or the model's justification as the expected answer, labelled accordingly.

Both are formative quick-check rows (§4.3), answered as today's quick checks are: no attempt, a self-check, "add to practice" to escalate. The learner sees the next step only after answering or pressing "show me".

*Restored (round 1's "justify steps, identify assumptions, compare alternative methods" and "delayed reconstruction"):*
- **"What does this assume?"** The producer asks which assumptions the selected step or result relies on (style `assumptions`), with the source's stated conditions, or the model's, as the expected answer, labelled accordingly.
- **"Another way to see this."** Calls `find_sources(intent="alternative")` from the sources spec with the selection as the query, excluding the open source's passage, and shows the best one or two passages from other sources or other roles (a geometric view beside an algebraic one) with RW4a's contribution line. Until that intent merges, it is RW4a's "where else is this explained?" with the open passage excluded.
- **"Reconstruct this later."** On a derivation or worked example, the producer writes a `reconstruct` question ("Derive … without looking at the book") with the source's derivation as the expected answer. It is escalated to a practice item through the quick-check's existing escalation, and a `test_me_later` commitment on that item is created, so DL2 serves it as a delayed, cold reconstruction. The commitment is labelled and undoable like any capture.

**Missed answers are learner text** (tier 2, W1). When the learner self-marks a next-step, why-step or assumption answer "didn't match", the answer, the selection and the expected answer become a `reader_formative` learner text (§3.4 item 13). Learner-text gaps names what was missing (a prerequisite, a belief) exactly as it does for reader questions. Matched answers write nothing new. Until learner-text gaps merges, the adapter is not built and the answers stay in the report.

### 4.3 Data

- **Branches:** no table. The parent lives on the `reader_answer_submitted` payload (as on the branch).
- **Inquiry status:** `question_events.resolution` and commitments, unchanged.
- **Quick-check scopes (one migration, RW1a):** `reader_authored_questions` gains
  - `scope_kind TEXT NOT NULL DEFAULT 'section' CHECK (scope_kind IN ('section', 'inquiry', 'selection'))`;
  - `question_style TEXT NOT NULL DEFAULT 'recall' CHECK (question_style IN ('recall', 'next_step', 'why_step', 'assumptions', 'reconstruct'))` (RW1b writes the last four; RW1a's migration adds the column with every value so there is one migration and no later rebuild);
  - nullable `anchor_span_ids_json` and `inquiry_root_event_id`.

  `section_id` stays `NOT NULL`: a passage-scoped row carries the anchor's section. **The section lookup (`latest_reader_authored_question`) filters `scope_kind = 'section'`,** or a reconnect row would shadow the section's quick check. Reuse keys: section rows as today; inquiry rows per (`inquiry_root_event_id`, prompt version); selection rows per (extraction, anchor spans, style, prompt version). A `dismissed` row still suppresses re-authoring for its own key.
- **Events:** no new kinds (§3.4 item 4). Routing, corrections, reconnect answers and the funnel use existing kinds with a payload `event` field and `authority_class = 'salience_only'`:
  - `reader_action_invoked` (`event`: `intent_routed`, `intent_corrected`, `reconnect_answered`, `next_step_requested`, …);
  - `reader_job_queued` and `reader_job_completed` for every model-backed action (status, failure reason, latency, model, prompt version);
  - `reader_source_restored` for "back to where I was".

  The salience-firewall test gains a case per new `event` value.

### 4.4 Routes, spend, privacy

- **Routes.** `reader_intent` (decider; about $0.0004 a call at the listed price; `reader_intent.max_calls_per_day` 200). The reconnect and active-reading questions use the quick-check producer's existing route and its caps. "Another way" uses T6's routes (and the sources spec's, once merged); `reader_formative` texts use learner-text gaps' routes and caps.
- **Privacy.** The selection and the learner's text go to OpenRouter's Decider provider (router D6 covers the disclosure). Nothing else is new.

### 4.5 Successor

None: content and display. Kill switches:
- `reader_inquiry.enabled` (off: the flat rail, exactly as today);
- `reader_intent.enabled` (off: the palette opens on selection, as today);
- `reader_active_reading.enabled` (off: no next-step, why-step, assumption, another-way or reconstruct actions);
- `reader_formative.enabled` (off: no `reader_formative` learner texts are queued; answers stay in the report).

### 4.6 RW1c: a tutor that looks things up (restored)

The owner's round-3 ask: "serve the learner explanations directly from the canonical source based on natural language queries from the tutor". Today the tutor grounds on T6 spans in the practice, feedback and library contexts (`TutorSpanProvider`), but in the Reader context it sees only the selection and its neighbours (§3.5).

**What the learner sees.** Ask in the Reader answers from the learner's books first, then explains:
- **Context it starts from:** the selection, the inquiry's ancestors and, when personalized, the latest session narrative for this source (labelled model-written; round 2's "the narrative summary helps the tutor and learner recover the intellectual context").
- **Three modes** (round 3 §4), chosen per answer by the tutor and labelled:
  1. **"From your books"**: a short cited excerpt (an equation, a definition, a worked step) when a passage answers the question directly. Source-authored, quoted, no paraphrase.
  2. **A grounded explanation** with links back to the passages (today's mode, now with retrieved passages).
  3. **A bridge to your work**: a short explanation that ties a passage to the learner's own recent work or open gap on the same LOs ("Your approach matches §3.4; the difference is the boundary condition — compare its limits with your step 4"). It is offered only when the learner has such work or an open gap, and only when the "personalized" toggle (RW4a) is on.
- **"Explain it another way"** under every answer retrieves with `find_sources(intent="alternative")` (sources spec), excluding every passage already shown in this inquiry, so the second explanation comes from another source or another role.
- **"That didn't help"** opens "What's still unclear?" (W5). The text starts a branch (a reader question, so learner-text gaps reads it), and the next answer retrieves with `find_sources(intent="remediate")` against the gap or misconception it names. The sources spec's `remediate` intent reads the misconception's `correction_source_span_ids`.
- **Offers, not actions.** The tutor's structured answer may carry `offers`: `practice_this` (RW4a's `find_practice` call with the question as the query — router §15.3's suggested first use), `compare` (RW4d's `compare_sources`), `explorable` (RW5b, when a cited block is an equation or figure the figure author judges feasible) and `try_first` (RW1b's next-step question on a cited derivation). Each renders as a button; LearnLoop runs the call only when the learner presses it. The tutor never serves, schedules or imports anything.

**How it works.**
- **The tutor forms its own query.** In the Reader context, `ask_question` gains a source-span provider, as practice, feedback and library already have: T6's rewrite step writes the query from the learner's question, the inquiry's ancestors and, when personalized, the open gaps on the passage's LOs; `find_sources(policy="reading", verify=True)` runs it. The selection and its neighbours stay first in the citation allowlist; retrieved spans are added after them.
- **Policies hold.** Inside a workbench session the provider switches to `assisted_practice` for the session's item; during a cold attempt nothing is retrieved (W7).
- **Receipts.** The `find_sources` manifest is stored with the exchange, as T6's tutor manifest is. Exposure is recorded where text is shown.
- **Before the sources spec merges,** "another way" and "that didn't help" fall back to `find_sources(policy="reading")` with the shown passages excluded; the modes and offers work unchanged.

**Data.** No table: exchanges are `question_events` with the manifest; offers pressed are `reader_action_invoked` events (`event`: `tutor_offer_pressed`).

**Routes, spend, privacy.** The tutor's existing route and caps; T6's routes for retrieval. The bridge adds the open-gap statements and recent workbench steps on the same LOs to the tutor's context, the same class of data the hint writer already sends (§5.8).

**Successor.** None: retrieval is context (T6's ruling) and offers are learner picks. Kill switches `reader_tutor.retrieval_enabled` (off: today's selection-and-neighbours tutor), `reader_tutor.offers_enabled`.

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
- **"Leave for now"** (and navigating away, closing the app or a restart) keeps the session `open`. **"Abandon"** closes it. On Leave, Submit or Abandon the workbench collapses back into ordinary reading at the same passage (the dialogue's "the workspace can collapse back into normal reading").
- **"Resume this problem"** appears on the source (beside the problem's passage), in the rail, in RW6a's recap and on the item's practice card. It reopens the same steps, the same source anchor and, after RW2b, the same assistance history.
- An open session older than `workbench.open_session_days` (30) is shown as "unfinished" in the recap and never auto-closed.

**I'm stuck** opens a text box, "Write what you can, or what's confusing you". The text becomes a step of kind `stuck`. In RW2a it is kept as learner work; RW2b sends it to the hint writer and to learner-text gaps. Submitting with no steps and an empty box is the existing empty stuck answer (`declared_stuck = true`, scored 0 with no model call).

**Submit** composes the answer (the steps in order, stuck steps and tombstones excluded) and sends it through `submit_attempt` (§5.4).

### 5.2 RW2b: checks and the help ladder

**Check my work** reads the steps and returns, for each step, `valid`, `questionable` or `unchecked`, and names the **first questionable step** with a reason that quotes it. It never gives the correction. Each verdict is labelled by method:
- **"checked"** only when a symbolic check ran and passed or failed (§5.3);
- **"model's reading, not checked"** otherwise (W2).

*Restored (rows 18 and 60 of the coverage audit):* the check also returns
- **a partial solution graph:** per step, `depends_on` (the earlier step ids it uses) and any `assumption` it introduces. A questionable step then invalidates only the steps that depend on it, so "what stands" (contract rule 3) can keep later independent work, and `continue_from` can be any valid step the questionable one does not feed;
- **an error-kind guess** for the first questionable step: `transcription` | `missing_prerequisite` | `invalid_algebra` | `wrong_method` | `conceptual` | `unclear`, with its quoted reason. It is shown as "the model's guess" (W2), goes to the diagnoser's trace as context (§5.4), and is never written as a diagnosis or an error event. The diagnoser at Submit remains the only classifier with authority.

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
2. **It continues from a real checkpoint.** `continue_from` must be a step marked `valid` or `unchecked` that does not depend, directly or through other steps, on the first questionable step (the step graph above); where the check returned no graph, no later than the first questionable step.
3. **It says what stands.** The hint states which of the learner's steps stand ("Your steps 1–3 stand").
4. **It keeps the learner's route.** It never switches to the reference's route unless the learner's route is invalid, the learner pressed "Show me the book's way", or the learner said "Different approach". A valid but different route is said to be valid; PF-c's valid-alternative rule applies to checks as it does to grading.
5. **It changes strategy when it isn't working.** After a "doesn't connect" reply, or two hints on the same step, a new hint must declare a different `strategy` slug (for example `boundary_check`, `worked_parallel`, `representation_switch`, `counterexample`) from the earlier ones on that step.
6. **It asks before it repairs** (restored; the dialogue's central scenario, round 1 §8: "two plausible explanations… A discriminating question can distinguish those possibilities before selecting a repair"). See below.

A hint that fails 1, 2 or 5 is re-asked once with the failure named, then shown as a level-3 hint from the last valid step without its unverified claims.

**A question that tells explanations apart** (restored, RS2). When a check leaves a questionable step and two or more rival explanations of it are open — the check's own error-kind guess and its alternatives, the open hypotheses and durable misconceptions on the item's facets (the records the hint writer already receives, §5.8), the rival causes of a diagnosed earlier attempt on the item (`unresolved_cause_factors.candidate_causes_json`), and gaps named from this session's text — the first help offered is a level-1 question with `strategy = discriminate`:
- **What it is.** A short question whose answer differs under each rival: "Before we fix step 4: what should F(0) be for this distribution?" separates a misunderstood support from an integration slip. It never states either rival and never contains the correction (leak control applies).
- **How it is chosen.** The hint writer proposes a few candidate questions, each with the answer it predicts under each rival. Each candidate is compiled as an instrument with one conditional row per rival and ranked with the existing `instrument_expected_information_gain` (`probe_families.py:467`) under the rivals' current weights: the open episode's posterior or the facet's `hypothesis_marginal` where they exist, uniform otherwise (labelled). A candidate whose rivals all predict the same answer has zero EIG and is dropped by construction. The best one is offered; nothing is hand-weighted (W4).
- **What its answer does** (tier 2, W1). It goes into the step trace, so the diagnoser sees it at Submit, and into the next hint's context, which now repairs the explanation the answer pointed to. As `workbench_text` it reaches learner-text gaps. It moves no posterior and writes no probe observation.
- **A short problem instead.** When the sources spec's discriminating search is merged, Help also offers "a short problem that tells these apart": `find_practice(intent="diagnostic_probe", target_hypotheses=…)` over the same rivals. The learner may take it now (a learner pick, ordinary attempt) or leave it to RW6b, which values it with the other follow-ups.
- **When it is skipped.** A single open explanation, help style "guide me", or the learner choosing a higher level. Help always helps (W11): the question is an offer at level 1, and every other level stays visible.

**Leak control.** A hint at level 3 or lower must not contain the final answer: `answer_leaks_expected` (`tutor_qa.py:816`) runs on every hint; a leaking hint is re-asked once, then withheld with "this hint would give the answer away; take level 4?".

**Bridging to the book.** After a hint is shown, a background request may add "Compare with the book": a verified passage the hint relies on, side by side ("compare its integration limits with your step 4"). It uses `TutorSpanProvider` in the `practice` context unchanged (T6's item-bound scope: no exercise or solution blocks, nothing linked to the item, answer-overlap spans withheld, listwise verification). It never delays the hint (§3.4 item 12). RW2c adds a worked example that takes the learner's route and a logged choice between equally good passages (§5.10).

**In-session updates** (restored, row 74: "don't wait for the session to end"). Every `workbench_text` (a stuck step, a "doesn't connect" reply, a discriminating answer) is queued to learner-text gaps when it is written, not at the end of the session. A gap named while the learner is still working joins the open explanations the next hint, the level chooser and the discriminating question read, and RW3b recomputes the cue links of a new hypothesis in the background. That is the dialogue's provisional, in-session state, kept to hypotheses and routing (tier 2); RW6a's summary consolidates at the end.

### 5.3 Symbolic checks: explicit, declared kinds

The check writer declares, per step it can classify, one transformation kind with stated inputs. *Restored (row 33): the list is widened from three to every kind sympy can check with a negative control:*
- **equivalence** of two consecutive expressions or of both sides of an equation step (including expansion, factoring and simplification);
- **differentiation or integration** of a stated expression with respect to a stated variable, including definite integrals with stated bounds;
- **substitution** of a stated value or expression;
- **solving** a stated equation for a stated variable;
- **limits** and **sums or series** with stated bounds;
- **inequality steps**, checked symbolically where sympy can and numerically on sampled points otherwise (labelled "checked numerically");
- **boundary and normalization conditions** (F(0) = 0, a density integrating to one) on a stated expression.

**Hints are verified separately from how they are written** (round 2 §4: "treat hint generation and hint verification separately"; restored). When a hint at level 2 or higher asserts something checkable about the learner's work ("your derivative in step 3 matches the PDF"), the same check path verifies that claim before the hint is shown; a failed claim is removed and the hint re-asked once, and an uncheckable claim is labelled the model's reading.

How: the check writer (route `workbench_check`) proposes the transformation and a sympy check; PF's sandbox runs it with a negative control, as PF's equivalence checks do (§3.4 item 6). Without bubblewrap the sandbox fails closed and the verdict reads "model's reading". Steps of other kinds — prose reasoning, proof moves, a choice of method — stay `unchecked` or model-read, and the report counts them by kind (§15). Formal verification of proof steps is deferred (§17).

### 5.4 Source visibility and what an attempt records

**Source visibility.**
- **In the Reader the source is visible by default.** The submission goes through `submit_attempt` with `entry_surface = 'desktop_reader_workbench'` in a practice session the workbench opens (`start_session`). **The visible source counts as one hint-equivalent**, the same rule `submit_reading_question` already records (`hint_equivalent: true`). The attempt is therefore assisted: graded blind, diagnosed, FSRS-fed, and never certifying (W7). Exposures are recorded on the anchored spans as `OpenInSource` does today.
- **"Hide the source"** before the first step makes it an ordinary attempt. Opening the source afterwards records the exposure, and the hint-equivalent applies from then on.
- **On the practice screen and from the plan,** the source is hidden. "Original page" behaves like any other source opening during practice.

**No new evidence semantics.** Every assist maps onto fields that already have meaning:

| Assist | Recorded as | Existing meaning |
|---|---|---|
| Source visible in the Reader | `hints_used` += 1 | Assisted: schedules, certifies nothing (`causal_activity_policy.py:182`); the field's `+hints` arm reads it |
| Check my work, level 1–3 hints, a discriminating question (a level-1 offer, §5.2) | `hints_used` += 1 for each one shown | The same |
| Level 4 or 5 | `primed = true` | `repair_activity`: no FSRS feed and no certification, like a guided redo |
| Hint text overlapping the key | A `reveal_events` row of the existing kind `tutor_answer`, `basis = 'workbench_hint:L<n>'`, with its overlap amount | Production admissibility and the reveal-aware cold lane |
| Answer confidence (optional, before Submit) | `answer_confidence` (1–5) | Logged only; never grading, certification or scheduling |
| Stuck text, then Submit | The steps are an ordinary answer; `declared_stuck` stays false | — |
| "Compare methods" after a correct Submit (RW2c, §5.10) | Nothing on the submitted attempt; a `reveal_events` row of the existing kind `answer_display` (or `source_review` for a source solution passage) on the item | The reveal-aware cold lane and RW6b's family exclusion treat the family as revealed |

Note the existing cap: `hints_used` is clamped to the item's `max_useful_hints` when that is set (`handlers/practice.py:561`). Any value above zero is assisted, so the cap changes no classification; the assist rows keep the true count for reports.

**On Submit:**
- the blind grader grades the composed answer with no knowledge of the steps' history or the hints (W8);
- the diagnoser's context gains, for this attempt only, the step trace with the assists in order and the work before each assist, under a prompt-version suffix (`+workbench-v1`) used only when a trace exists. The trace includes the step graph, the check's error-kind guesses (labelled as guesses) and any discriminating question with the learner's answer, so the diagnoser can use the separation the question bought. Every other attempt's context hashes as before (the stuck-reading precedent);
- the feedback screen is today's, including guided redo.

**Abandoned sessions** write no attempt. Their steps and assists stay as learner work and appear in RW6a's recap.

The RW2a agent confirms this table against `resolve_attempt_activity_policy`. **If any mapping needs a new discount or eligibility rule, stop and make it a successor** (the next free `mvp-0.N` tag) rather than bending an existing field.

### 5.5 RW2b: the first offer, a judgment

When the learner opens Help, the **level chooser** picks which level to offer first.
- **How it is asked.** One typed `ChoiceQuestion` over levels 1–5 to the Decider (route `workbench_level_chooser`, added to `DECIDER_TASKS`), with a 3 s time box. On timeout, unavailability or `workbench.level_chooser_enabled = false`, the offer is level 1, then one level up on each further Help press.
- **The state it gets** (typed, short): the item's LO status (untested / assumed / learning / demonstrated); demonstrated vs assisted-only evidence on the item's facets (capability ledger, facet timeline); the active predictor's P(success) and interval for the item; workbench history on these facets (levels taken, and whether the learner continued unaided afterwards, including "doesn't connect" replies); after RW2c, the learner's help outcomes on these facets (§5.10); this session's failed checks, hints and named gaps; the help style (**let me struggle · balanced · guide me**, default balanced, remembered).
- **Why a judgment.** The expertise-reversal finding the dialogue cites: novices benefit from more guidance and experts from less, per learner × facet × task. The chooser applies it from evidence (W4). Learner history reaches the chooser, never the grader (W8).
- **Logging.** The offered level, the chooser and the level taken are on the assist row. There is no randomization of help quality (§17).

### 5.6 Reuse, learner text and signals

- **Grading and diagnosis:** the blind grader, the diagnoser, PF-c and guided redo, unchanged.
- **Retrieval:** `TutorSpanProvider` (practice context) for bridging; nothing new.
- **Learner text (RW2b):** a non-empty stuck step, a "this doesn't connect" reply with text, and an answer to a discriminating question are learner texts. Learner-text gaps gains one source kind, `workbench_text` (beside `tutor_question`, `diagnosis` and `stuck_answer`), whose adapter reads the text with its item, step, anchors and role (`stuck` \| `hint_feedback` \| `discriminate_answer`). It names gaps exactly as the pipeline does for other sources; nothing else in the pipeline changes. The kind needs the widening migration (§3.4 item 13). Until `learner/text-gaps` merges, the adapter is not built and the texts stay learner work.
- **Field signals: RW2d.** `stuck_confusion` and "help before work" are derived signals that Phase 6 serving reads (fast-track blocking), so a new source changes serving and needs a successor (§3.4; `field/signals.py:327`). A submitted workbench attempt already carries its assistance in `hints_used` and `primed`. Signals from mid-work stuck steps and help before the first step are restored as RW2d, an algorithm successor with a kill switch (§5.11).

### 5.7 Data

| Table | Phase | Role | Contents |
|---|---|---|---|
| `workbench_sessions` | RW2a | WORKFLOW | `id`, `practice_item_id`, `origin` (`reader` \| `practice` \| `plan`), `extraction_id`, `span_ids_json`, `source_visible`, `source_hidden_at`, `practice_session_id`, `help_style`, `status` (`open` \| `submitted` \| `abandoned`), `attempt_id`, `created_at`, `updated_at`, `closed_at` |
| `workbench_steps` | RW2a | RAW_LEDGER | `id`, `session_id`, `ordinal`, `kind` (`step` \| `stuck`), `body_md`, `supersedes_id`, `deleted` (tombstone), `client_idempotency_key`, `created_at` |
| `workbench_assists` | RW2b | RAW_LEDGER | `id`, `session_id`, `kind` (`check` \| `hint` \| `discriminate` \| `discriminate_answer` \| `bridge` \| `example` \| `compare_methods` \| `feedback`; every value is in RW2b's migration, so RW2c adds no rebuild), `level`, `offered_level`, `chooser` (`decider` \| `fallback`), `step_snapshot_json` (step ids and content hashes at request time), `step_verdicts_json` (verdict, method, `depends_on`, `assumption` per step), `first_questionable_step_id`, `error_kind_guess`, `continue_from_step_id`, `strategy`, `rivals_json` (the open explanations with their weights and source), `predicted_answers_json` and `eig_nats` (for a discriminating question), `body_md`, `feedback_text`, `feedback_shortcut`, `feedback_step_id`, `cited_span_ids_json`, `retrieval_manifest_json`, `alternatives_json`, `propensity`, `seed` (RW2c's logged draw), `leak_flags_json`, `contract_failures_json`, `model`, `prompt_version`, `input_hash`, `latency_ms`, `created_at` |

No reveal-table rebuild (§3.4 item 10). Replay never reads the workbench tables: the attempt row carries `hints_used` and `primed`, and the reveal ledger carries the reveals.

### 5.8 Routes, spend, privacy

- **Routes (RW2b):** `workbench_check` (chat: step verdicts, the step graph, the error-kind guess, localization and the sympy check text); `workbench_hint` (chat: hints at levels 1–5 and the candidate discriminating questions with their predicted answers); `workbench_level_chooser` (decider). Unset chat routes fall back to the active provider.
- **Latency.** Codex blind grading took 29–37 s on the stuck-prompt copy, too slow for "Help". The target is check and hint p50 ≤ 10 s, **reported, not enforced**. The recommended route is a `chatgpt_plan` profile (the provider merged on `main` at `57d31c63`; the owner's sign-in is pending); until then a fast OpenRouter chat profile (D7). `learnloop ai latency` compares candidates before the switch. Ranking discriminating questions adds no model call: the EIG is computed.
- **Caps:** `workbench.max_calls_per_session` (24); `workbench.max_daily_cost_usd` ($1.00 for metered routes); a capped session says so and keeps the authored hints.
- **Context per call:** the item stem, reference solution and rubric; the session's steps, assists and feedback; for hints only, the open hypotheses on the item's facets as typed records (statement and status, no prose; Slice 1 S3). About 4–12K input tokens.
- **Privacy:** the learner's work and that slice of their state go to the configured provider, as grading and diagnosis already do. No new disclosure.

### 5.9 Successor

None (§5.4). Kill switches:
- `workbench.enabled` (off: no workbench entry anywhere; the practice screen is byte-identical);
- `workbench.help_enabled` (off: RW2a only);
- `workbench.level_chooser_enabled`;
- `workbench.symbolic_checks_enabled`;
- `workbench.discriminate_enabled` (off: help starts with the chooser's level, as before the restoration);
- `workbench.error_kind_enabled` (off: no error-kind guess is shown or traced).

### 5.10 RW2c: what helps this learner (restored)

The dialogue's deepest aim (round 2 §9, round 3 §7): "a memory not only of what a learner knows, but of how that learner arrives at understanding, where their reasoning tends to diverge, and which forms of assistance help them recover." RW2c builds the part of it that n=1 data can support now.

**Help outcomes, a replayable read.** `help_outcomes(repository, facet_ids, as_of) -> HelpOutcomesV1` is a pure function over rows that already exist: `workbench_assists` (strategy, level, the passages and their roles from the retrieval manifests), RW1c's tutor exchanges and offers, `library_asks`, figure views, and the outcomes that followed. For each help kind (a hint strategy such as `boundary_check` or `worked_parallel`; a passage role such as worked example, figure or counterexample; a comparison; a figure) on each facet, it returns:
- **the immediate continuation:** whether the next check found a valid next step without further help;
- **the attempt's grade** when the session was submitted;
- **the later independent outcome** on the same facets (the next unassisted attempt, or a RW6b follow-up), and how many have **no later observation yet**.
- It is deterministic from the ledgers, computed twice in tests, and needs no table (so no replayer). Associations only: it is labelled "what preceded recovery for you", never "what works".

**Who reads it** (tier 2, W1):
- **the hint writer** gets the top few lines for the step's facets ("on boundary conditions, a worked parallel preceded recovery 3 of 4 times; a counterexample 0 of 2"). This is the dialogue's data-driven next-step hints (row 61), seeded from the learner's own history, since at n=1 there is no cross-learner data (§17);
- **the level chooser** gets the same lines (§5.5);
- **the report's "Interventions → outcomes" block** reads it instead of recomputing (§15).

**A logged choice where it costs nothing** (round 3 §7: "causal claims need randomized variation"). When bridging, or a worked-example search, finds two or more verified passages that both pass the judge, one is shown by a logged draw (propensity and seed on the assist row) and the others stay one click away ("another passage"). Every option passed the same judge, so no learner gets worse help on purpose: this is the cue holdout's pattern (D10), not a hint-quality experiment (§17 keeps those unplanned). Over months the draws give the report an unconfounded comparison between, say, a figure and a worked example for this learner. Switch: `workbench.passage_draw_enabled`.

**A worked example that takes your route** (round 3: "a worked example using CDF-first derivation… the learner should not have to restart"; rows 89, 97). `find_examples(vault, repository, *, item, steps, facet_ids) -> SourceHits` is a thin function over `find_sources`:
- `policy="assisted_practice"` for the item (no exercise or solution block of the item, nothing linked to it, nothing reproducing its answer), `roles` worked example, proof, figure or equation (ingest's `role_hint` or a RW4e role);
- the query is written by the hint writer from the learner's own route and the questionable step ("CDF-first derivation of a mixture; boundary condition at the edge of the support");
- one listwise call (`judge_listwise`, route `example_fit`, ledger task `example_fit`) keeps the passages that take the learner's approach and quotes the step that corresponds to the learner's.
- It runs in the background after a level-3 or higher hint, or on "Show me a similar example". The result shows beside the learner's step: "A worked example that takes your route: Book A §3.4 · compare its step 2 with your step 4". It is the third explanation mode (a personalized bridge) inside the workbench.

**"Compare methods" after a correct answer** (round 1's "compare alternative methods"; rows 6, 105). After a correct Submit, the feedback screen offers "Compare with the book's method": the learner's route beside the reference solution, or the source's solution passage, with one AI-written line per difference in assumptions or steps (labelled). It uses `find_sources(policy="post_attempt")` (§7.2), which admits the item's own solution only once its attempt window is closed, and records the reveal (§5.4). A valid different route is named valid (PF-c's rule).

**Data.** No new table: `workbench_assists` already holds the kinds, draws and manifests (§5.7). **Routes:** `example_fit` (listwise, background). **Caps:** inside the workbench's per-session and daily caps. **Successor:** none; everything is context, display or a learner pick. Kill switches `workbench.help_outcomes_enabled` (off: the writer and chooser lose the lines), `workbench.examples_enabled`, `workbench.compare_methods_enabled`, `workbench.passage_draw_enabled`.

### 5.11 RW2d: workbench signals in the learner field (restored; algorithm successor)

Restores the deferred "interaction signals from abandoned workbench sessions and mid-work stuck steps" (round 2 §6's formative tier, the S5 placement signal). The owner's preference is live behind kill switches, so it is built as a successor rather than waiting on a usage trigger.
- **What changes.** The field's signal derivation (`field/signals.py:327`) gains two sources: a mid-work stuck step (as `stuck_confusion`, like an "I'm stuck" answer, tied to the item's facets and LOs), and help requested before the first step (as "help before work"). Abandoned sessions contribute only through these two, never as a failure. **Asking is never penalized** (field §3.1's guard): the signals steer routing for new material (taught first, never fast-tracked on early answers alone), never the record.
- **Why a successor.** Phase 6's fast-track rule reads these signals, so what is served changes (F3). RW2d takes the next free `mvp-0.N` at its merge, with receipts that record what the previous derivation would have produced.
- **Kill switch** `workbench.field_signals_enabled` (or the field's own namespace, as the RW2d agent and reviewer decide): off, the field derivation and every plan build are byte-identical to the predecessor on fixture copies.
- **Depends on** RW2b (the stuck and help rows) and the field's Phase 6 serving on `main`. **Gate** G41.

---

## 6. RW3 — Passage cues (misconception-aware reading)

### 6.1 What the learner sees

A thin mark in the margin beside a passage, and a one-line note on hover or focus. Three kinds, each saying what connects or what is on offer, never what the learner lacks:
- **Revisit a distinction:** "Connects to a distinction you worked on: density vs cumulative probability. Not yet independently checked since."
- **A new application** (RW3b): "A new use of something you've shown: conditioning on a component."
- **Try this step first** (RW3b, restored; round 2 §7's "request a prediction", round 1's "an explanation, or try the derivation yourself?"): on a worked example or derivation in a section whose LOs carry a claim needing an independent check (§9.1) or an open hypothesis, "Try the next step before reading it?". Pressing it opens RW1b's "Let me try the next step" at that line. It is an offer in the margin, never a gate on the text.

**Actions on a cue:**
- **Open** shows the earlier work: the cited attempt, its diagnosis, the inquiry, the named gap.
- **Check me** offers one short item, as a learner pick: an ordinary attempt, ordinary evidence. It calls `find_practice` constrained to the cue's facets; once the sources spec merges, the proposals include textbook exercises and, when the cue's target has rival explanations open, the call uses `intent="diagnostic_probe"` with those rivals as `target_hypotheses`, so the item offered is the one that best tells them apart. With DL1 merged it is a learner-pick block; before that it opens the item directly.
- **Not relevant** shows an optional text box, "why? (optional)" (W5).
- **Cues off** works for this source or everywhere.

**Restraint (W12):** an attention budget of visible cues per section, set by the learner's density control "fewer · normal · more" (1, 2 or 4; default normal, remembered; `cues.density`) — the dialogue's "optional, collapsible and density-limited", and a display limit the learner owns, not a count that decides learning. Never pop-ups, never blocking, never in skim mode.

### 6.2 How a passage gets a cue

**RW3a: the Guide's own passages.** The Guide already computes, per section, passages cited by items whose LO has an active error (`_passages_by_section`, `reader_guidance.py:362`). RW3a renders those with `learner_signal = 'recent_misunderstanding'` as margin marks:
- **Fix first:** `_learner_signal` reads the misconception statement through the diagnosis overlay (`error_events_for_attempt`) or the open hypothesis it belongs to, not raw `error_events` (§3.4 item 1). The Guide rail benefits too.
- The section's existing ranking picks which cues show, within the learner's density budget; the margin and the rail always agree.
- Wording comes from fixed templates (G16); the Guide's "Revisit this to resolve: …" stays in the rail only.
- Taps are logged as `reader_action_invoked` events (`event`: `cue_opened`, `cue_check_me`, `cue_not_relevant`) and as `learner_card` verdicts (task `passage_cue`).

**RW3b: discovered links.** For targets the Guide's provenance links miss:
1. **Targets.** Recurrence groups and open hypotheses (T1, Slice 1), durable misconceptions and holding-pen candidates, named gaps (`learner_text_gaps`, once merged), and facets with demonstrated capabilities (for "new application" cues). Each is rendered as its LLM-written statement (R3).
2. **Shortlist.** `search_spans` with the target's statement as the query, over the open source's extraction (T6: BM25, dense and the provenance list fused by RRF; top-k, no cutoff, W6). *Restored (rows 101, 102):* two more lists join the fusion through `extra_lists` — passages with a RW4e `contrast` or `counterexample` role on the target's LOs or their `confusables`, and the misconception's `correction_source_span_ids` (the sources spec's `remediate` intent reads the same; RW3b uses the list directly). Source-authored contrasts ("independence vs zero covariance") are what the dialogue expected to work best for misconceptions.
3. **Judge.** One listwise call per target through `judge_listwise` (route `passage_cue_judge`, ledger task `passage_cue`): it judges every shortlisted passage `clarifies_distinction` | `new_application` | `prerequisite_for` | `try_first` | `none`, picks at most two, and quotes what it relies on (quote-verified against the block). `try_first` applies only to worked-example or derivation passages on a target with an unchecked claim or an open hypothesis. The judge also proposes the passage's instructional roles for RW4e at no extra call. The ledger cache makes a repeat free.
4. **Rank by value, then the budget** (restored, rows 25 and 51). The dialogue's cue value was P(relevant gap) × gain − interruption − false warning. v1 uses the one term LearnLoop already measures: **the probability that the target is still open**, read from existing state — the open episode's posterior or the facet's `hypothesis_marginal` for a hypothesis, the misconception's lifecycle (active or not), a named gap's status, and for "new application" and "try first" the active predictor's P(failure) on the passage's LO. Within a section, judged links and the Guide's passages are ordered by that probability, then by the judge's pick rank, Guide passages first on ties, and shown until the density budget is used. The gain and the two costs are not hand-set: they are what the holdout (item 6) and the "not relevant" rate measure, and learning them is the deferred learned cue policy (§17).
5. **When state changes,** the cache key is the target's statement and status; a new or resolved hypothesis recomputes only its own links. Links are computed in the background when a source opens (W12).
6. **Holdout.** With `cues.holdout_rate` (0.1), an eligible **discovered** cue is withheld at random, with a logged seed and propensity, so its effect on the next attempt on those facets can be estimated without asking anything of the learner (§15; D10). Guide cues (RW3a) are not held out: they show what the rail already shows.

**Learner taps** are judge feedback: "not relevant" appends `learner_card` `different`, "open" and "check me" append `same`, on the judge's ledger task. Judge precision is measurable with no review chore. "Not relevant, because…" text stays judge feedback; it is not a learner-text gap source (it says something about the cue, not about the subject).

**The in-session Reader policy, in one place** (restored, row 75). The dialogue proposed a lightweight, mostly rule-based policy over a small set of actions, with "help always helps" as its one hard rule. It is spread across the phases, so here is the map:

| Dialogue action | Where | Rule |
|---|---|---|
| Continue without intervention | Everywhere | The default: no cue clears the budget, no offer is pending |
| Show a source relationship | Cues (§6.1), RW4d's "compared" mark | Value order, then the density budget |
| A short clarification | Cue "Open"; RW1c's "From your books" excerpt | On the learner's tap or question |
| Request a prediction | "Try this step first" cues; RW5's predictions | An offer in the margin; predictions only before a figure's first change |
| A targeted hint | RW2b's ladder, discriminating question first | Help always helps (W11) |
| A partial worked example | Ladder levels 4–5; RW2c's example in your route | On request |
| Return to the original task | RW1a's reconnect and "back to where I was" | When a branch resolves |

### 6.3 Data

| Table | Phase | Role | Contents |
|---|---|---|---|
| — | RW3a | — | No table: cues are computed from the Guide plan; taps are events and ledger rows |
| `passage_links` | RW3b | WORKFLOW (paid outputs; never re-run on rebuild) | `id`, `extraction_id`, `span_id`, `target_kind` (`recurrence_group` \| `hypothesis` \| `misconception` \| `learner_text_gap` \| `demonstrated_facet`), `target_id`, `relation`, `quote`, `ledger_id`, `state_key`, `model`, `prompt_version`, `created_at` |
| `reader_cue_impressions` | RW3b | RECEIPT | `id`, `link_id` (null for a Guide cue), `visit_id`, `shown`, `propensity`, `seed`, `p_open` and its source (the value used to order the cue), `density`, `response` (`opened` \| `check_me` \| `try_first` \| `not_relevant` \| `none`), `response_text_hash`, `created_at`, `responded_at` |

### 6.4 Routes, spend, privacy

- **Route:** `passage_cue_judge` (RW3b; listwise; Codex by default, since it is background work).
- **Caps:** one call per target per source open; `cues.max_calls_per_source_open` (12); `cues.max_daily_cost_usd` ($0.50 metered).
- **Privacy:** hypothesis and gap statements plus source passages go to the provider, the same class as diagnosis.

### 6.5 Successor

None: display only, and nothing it writes enters evidence or serving. "Check me" and "Try this step first" are learner picks. Kill switches `cues.enabled` and `cues.discovery_enabled` (RW3b); `cues.try_first_enabled`; `cues.value_order_enabled` (off: the judge's order, as before the restoration); `cues.holdout_rate = 0` turns the holdout off.

---

## 7. RW4 — Library questions, source comparison and exercises from sources

### 7.1 Roles: ingest decides exclusions, proposals add detail

Ingest's deterministic `source_blocks.role_hint` stays the authority for **exclusion** (§3.4 item 2): T6's item-bound scope keeps `exercise` and `solution` blocks out of practice and feedback contexts, and nothing in this spec changes that. Roles shown or filtered come from `role_hint` and, after RW4e, from role proposals in `source_objects` (§7.9):
- **grouping** a library answer ("Definition", "Worked example", "Exercise", "Explanation" for `ordinary_prose`, and RW4e's finer roles where proposed);
- **positive filters**: `find_sources(roles=…)` matches a span whose `role_hint` or RW4e role proposal is in the list;
- **RW4b's exercise view** and RW5's candidates (`equation`, `figure`).

Where a passage has no finer role yet, the organizer (§7.3) may add one ("Geometric view", "Application") in its contribution line, labelled as the model's; RW4e persists it as a proposal.

### 7.2 `find_sources`: one function, four policies

A small library function in `learnloop/source_retrieval/`, composed from what T6 built. It is the function router §15.3 calls (§18). This spec defines its base signature and policies; `spec_source_practice_and_probes_v1.md` adds the `intent` parameter (`remediate`, `alternative`, and whatever else it defines) and owns what each intent does. Whichever lands first creates the function; the other extends it.

```python
RetrievalPolicy = Literal["reading", "assisted_practice", "post_attempt", "cold_attempt"]

def find_sources(
    vault, repository, query: str, *,
    policy: RetrievalPolicy,
    scope: Literal["library", "teaching"] = "library",
    learning_object_ids: Sequence[str] = (),
    facet_ids: Sequence[str] = (),         # restored: mapped to their LOs for scope; dossier text joins the query
    item: PracticeItem | None = None,      # required for assisted_practice and post_attempt
    roles: Sequence[str] = (),             # role_hint or an RW4e role proposal
    expand: Sequence[Literal["prerequisites", "applications", "confusables"]] = (),  # restored: the LO graph
    exclude_span_ids: Sequence[str] = (),
    verify: bool = False,                  # T6 listwise verification
    limit: int = 8,
    embedder=None, rewrite_client=None, rerank_client=None, deadline=None,
    # intent: added by spec_source_practice_and_probes_v1.md
) -> SourceHits:                            # hits + manifest (query hash, policy, basis, keys, statuses, expansion lists)
```

| Policy | Built from | Learner-facing material |
|---|---|---|
| `reading` | `library_scope` or `teaching_scope(item_bound=False)` + `search_spans` | Everything in scope with teaching authority |
| `assisted_practice` | `teaching_scope(item_bound=True, item=…)` + the answer-overlap filter + `verify_spans`, as `TutorSpanProvider` does | No `exercise` or `solution` block, nothing linked to the item, nothing reproducing its answer |
| `post_attempt` *(restored, narrow)* | `assisted_practice` while the item's attempt window is open (a redo, guided redo or retry is possible: T6's reason for keeping feedback item-bound); once the window is closed by a correct submission or by the learner closing the item, `reading` plus the item's own linked passages and solution blocks | After the window closes: the item's solution and the passages it was built from. Every display records a reveal (§5.4), so the family is treated as revealed afterwards |
| `cold_attempt` | — | **Nothing**: an empty result, by construction |

- **`authoring` is not added here:** PF's source-anchored path has its own retrieval with full reference material, isolated from learner-facing models. The dialogue's fifth context is that path.
- **`expand`** (restored, row 65: "a concept graph surfaces prerequisites, applications and connected learning objects"). For the query's LOs, `prerequisites` adds the teaching scope of `LearningObject.prerequisites`, `applications` the LOs that list them as a prerequisite, `confusables` the LOs in `.confusables` (`vault/models.py:330`). Each expansion is a separate list fused by RRF through `search_spans`' `extra_lists` and labelled on the hit, so the organizer can group "Prerequisite" and "Application". Similarity never creates an edge (W6); the graph is read as it is.
- **Receipts:** each call returns a manifest that the consumer stores on its own row, as T6's tutor manifest does. Exposure is recorded where the consumer shows text, unchanged.

### 7.3 RW4a: ask your library

The library search box (T6: type for keyword, Enter for meaning plus rewrite) gains **"Ask"** (Shift+Enter, or "where else is this explained?" from a selection).
- **The answer is sources first** (D12): no AI essay. Up to eight passages from `find_sources(policy="reading", verify=True, expand=["prerequisites", "applications"])`, grouped by source and then by role, with the dialogue's own groups where they apply: **Foundation** (definitions and theorems), **Explanation** and finer views ("Geometric view"), **Prerequisite** (from the expansion), **Application** (from the expansion). Each carries one line, "what this passage contributes", from the organizer: one listwise call through `judge_listwise` (route `library_organizer`, ledger task `library_contribution`) that judges each hit, picks and orders them, writes a line that must cite exactly that hit's key (validated in code), and proposes each hit's instructional roles for RW4e at no extra call.
- **"Make this explorable"** appears on a hit that is an `equation` or `figure` block when the organizer marks it feasible (RW5b).
- **"Ask the tutor about these"** opens a tutor exchange in the `reader` context whose citation allowlist is the selected hits, across sources, through a pinned-span provider passed as `source_span_provider` (§3.4 item 11). It is a `question_events` row, so it joins the outstanding-question queue, the field's question signals and learner-text gaps with no new adapter.
- **"Personalized" is a toggle,** default on. When on, the organizer also sees the learner's open gaps and hypotheses on the hits' LOs and may mark one passage "speaks to your open question about …". Off, the order is plain retrieval rank (the dialogue's guard against confirmation bubbles).
- **"Practice this question"** calls `find_practice(query)`, the same call as DL3's "Practice on…" box and RW1c's `practice_this` offer: one RPC, which the sources spec counts among `find_practice`'s real callers. The learner picks from its proposals: a learner-pick block under DL1, else the item opens directly. **Once the sources spec merges,** the proposals include textbook exercises as their own candidate kind (shown as RW4b shows them, with source and page), the call passes the question's LOs and facets, and a chosen textbook exercise goes through that spec's import and verification before it is served. Until then, when nothing fits, RW4b's fallback search is offered. Nothing is generated live.

**Compare sources** ("How do my sources treat this?"), from a selection or a library answer, is RW4d's `compare_sources` (§7.8) with the learner as caller:
1. **Counterparts.** `find_sources(policy="reading", scope="library")` with the selection as the query, grouped by source: one or two passages per source, up to `compare_sources.max_sources` sources (4 by default: a context-size cap, raised freely). The learner can also **pin** passages from any answer, from different sources.
2. **One comparison call** (route `library_organizer`, a second prompt): per source, its distinct contribution as a source-local claim, and per pair, how they relate — equivalent, different assumptions, different notation, a real disagreement, or unclear ("same result, assumes independence; Book B assumes only zero covariance") — each statement quoting its own source's passage (quote-verified; a line that fails is dropped, not repaired).
3. **Show a table:** one row per source, with "Ask the tutor about these" on the pinned set. **Differences are the point:** there is never a merged "consensus" answer. Three voices stay apart on screen: what each source says (quoted), what LearnLoop infers about the relation (labelled AI-written), and the learner's own take (RW4d).

Until RW4d lands, the comparison is display only and stores nothing; RW4d adds "Keep this comparison".

### 7.4 RW4b: exercises from my sources

**The Reader's view of textbook-exercise candidates.** `spec_source_practice_and_probes_v1.md` makes textbook exercises practice candidates: `find_practice` returns them as their own kind, with source, page and span; choosing one imports it, verifies its completed answer with PF-b, maps its competencies and attaches it to a matching family as a surface ("don't eliminate cards — change what they represent"). RW4b designs none of that. It shows the candidates wherever the Reader shows practice proposals (RW4a's "Practice this question", RW3's "Check me", RW1c's offers):
- each candidate shows its passage, source and page, "open in the book" and "use this one";
- "use this one" calls the sources spec's import path; the item becomes a learner pick when it is admitted;
- a candidate whose page the learner has already read in full, or whose worked twin they were shown, carries that spec's exposure label.

**Before the sources spec merges,** a learner-initiated fallback: when `find_practice` finds nothing, "Find an exercise in my sources" runs `find_sources(policy="reading", roles=["exercise", "worked_example"], verify=True)` over the teaching scope of the query's LOs, and "use this one" runs the existing `import_exercises` (verbatim stem, AI-completed answer, rubric, facets, hints). The fallback is retired when the sources spec's candidates are live (its switch, `library_exercises.fallback_enabled`, then defaults off). Automatic sourcing of RW6b's follow-ups from textbook exercises comes through the same `find_practice` call (§9.3).

### 7.5 Data

| Table | Phase | Role | Contents |
|---|---|---|---|
| `library_asks` | RW4a | WORKFLOW (paid outputs; never re-run on rebuild) | `id`, `caller` (`learner` \| `tutor`), `query_md`, `query_hash`, `personalized`, `requested_perspectives_json`, `manifest_json` (the `find_sources` manifest), `organizer_json` (lines with their hit keys and ledger ids), `compare_json` (claims, fine relation labels, and after RW4d the kept object and relation ids), `kept_at`, `question_event_id` (when the tutor was asked), `model`, `prompt_version`, `created_at`. RW4d's columns are in RW4a's migration, so RW4d adds none |

RW4a writes nothing to `source_object_relations` or `source_objects`; RW4d and RW4e write proposals there (§7.8, §7.9).

### 7.6 Routes, spend, privacy

- **Routes:** `library_organizer` (listwise; serves live requests, so the fast route is recommended, as for RW2b). T6's routes do the rest.
- **Caps:** library ask: one retrieval (with T6's own caps; the graph expansion adds lists, not calls), one organizer call; compare: one call over up to `compare_sources.max_sources` sources (a context-size cap); `library.max_daily_cost_usd` ($1.00 metered).
- **Privacy:** source text and the question go to the provider. The personalized toggle adds gap statements; it can be turned off.

### 7.7 Successor

None. Retrieval is context (T6's ruling) and the organizer's lines are display. Kill switches: `library_ask.enabled`, `library_ask.expand_graph`, `compare_sources.enabled`, `library_exercises.enabled`, `library_exercises.fallback_enabled` (all off: T6's library search exactly as merged).

### 7.8 RW4d: syntopic reading as a tool (restored)

The dialogue (round 1 E, round 2 §5, round 3 §5C) asked for syntopic reading as a first-class operation: "`compare_sources(query, facets, requested_perspectives)` … returning source-local claims; equivalent claims, different assumptions and real disagreement kept apart", and for claims to be kept "with their source context" while "model-proposed relations are reviewed before entering a trusted graph". P3 §7.1–7.2 already provides that layer: per-source objects and relations that stay proposals.

**The function.** `compare_sources(vault, repository, query, *, facet_ids=(), requested_perspectives=(), pinned_span_ids=(), policy="reading") -> Comparison`, in `learnloop/source_retrieval/`:
- **Counterparts** as RW4a describes; each requested perspective ("a geometric interpretation", "in the context of PCA") becomes one more `find_sources` query whose hits carry the perspective label;
- **one comparison call** returning source-local claims (each quoted from its passage) and typed pairwise relations (`equivalent` \| `different_assumptions` \| `different_notation` \| `disagreement` \| `unclear`), each citing both quotes; failures are dropped;
- **callers:** the learner (RW4a's Compare), the tutor (RW1c's `compare` offer, which the learner presses), and, through the sources spec's tool surface, the router later. It never serves or schedules anything.

**Keep this comparison.** On the learner's "Keep", and only then:
- each shown claim becomes a `source_objects` row with a version (`object_type = 'claim'`, or `definition` for a definition; `authorship = 'ai'`, `status = 'proposed'`, `revision_id` of its source; one citation with span and quote);
- each relation becomes a `source_object_relations` row, `authorship = 'ai'`, `review_status = 'proposed'`, typed by §3.4 item 15's mapping, with the fine label in `library_asks.compare_json`;
- **"My take"** lets the learner add their own line on any pair or claim: a `learner_connects` relation with `learner_text`, `authorship = 'learner'` (P3 invariant 8's connect-it semantics). The three voices — the source, LearnLoop's inference, the learner's belief — stay separate rows with separate authorship (W2, P3 invariant 9).

**Kept comparisons come back.** A passage with a kept comparison shows a small "compared" mark in the margin (a cue of its own kind, inside the density budget) that opens the table. A later library ask on the same claims says "you compared these on 3 Oct". Reviewing a proposed relation uses P3's existing source-object review path; nothing in this spec promotes one.

**What it never does.** No canonical concept edge, facet merge, prerequisite or learning-object change (P3 §7.3; G18). No claim extraction over passages the learner did not compare: that is the deferred full-library claim index (§17).

**Data.** No new table: `library_asks` holds the comparison (RW4a's migration has the columns), and kept claims and relations live in `source_objects` and `source_object_relations`. **Routes:** `library_organizer`'s comparison prompt. **Caps:** one comparison call per request; `compare_sources.max_sources` as a context cap; within `library.max_daily_cost_usd`. **Successor:** none; proposals and display. Kill switches `compare_sources.keep_enabled`, `compare_sources.tutor_enabled`.

### 7.9 RW4e: instructional roles (restored)

Round 3 §5A: "index instructional roles, not just passages" — definition or theorem, explanation or intuition, worked example, exercise, figure, counterexample, prerequisite passage, alternative treatment — "several roles per passage… with confidence and provenance… anchored to immutable source versions". Ingest's single deterministic `role_hint` covers four of these; the rest need judgment.

**Roles accumulate from judgments already being made.** The library organizer (RW4a), the cue judge (RW3b), the comparison (RW4d) and `example_fit` (RW2c) already read each passage they judge. Their outputs gain one field per passage: `roles`, one or more of `definition`, `theorem`, `explanation`, `intuition`, `worked_example`, `exercise`, `figure`, `counterexample`, `contrast` (a passage that distinguishes two easily confused ideas), `prerequisite`, `alternative_treatment`, `application`, each with a confidence (`high` \| `medium` \| `low`). No extra call.
- **Stored** as a `source_objects` proposal per span and role: `object_type` mapped by §3.4 item 14, `authorial_role` the role, `content_json` holding the confidence, the judge, its ledger id and the prompt version, `authorship = 'ai'`, `status = 'proposed'`, one citation with the span, its block hash and the revision. A second judge proposing the same role on the same span adds a version, so agreement across judges is visible.
- **An owner-run batch labeller** for when the full index is wanted now: `learnloop reader label-roles --source <id> [--dry-run]` walks the source's blocks in reading order in listwise batches (route `role_labeller`, spend cap `roles.batch_max_cost_usd`), writing the same proposals. It never runs on the reading hot path.

**Used positively, never to exclude.** `find_sources(roles=…)` matches a span whose `role_hint` or role proposal is in the list (`low` confidence counts only when nothing better exists). RW3b prefers `contrast` and `counterexample` passages for distinction cues; the sources spec's `remediate` and `alternative` intents can read the same proposals. **Exclusions stay with ingest's `role_hint` and item links:** an AI proposal never admits a block into an item-bound scope and never removes one from an exclusion (G44).

**Data.** No new table. **Routes:** `role_labeller` (listwise, batch only). **Successor:** none; labels on sources. Kill switches `roles.on_demand_enabled`, `roles.positive_filter_enabled`.

---

## 8. RW5 — Explorable figures

RW5a is the first figure phase, now including the dialogue's flagship example (restored: shaded areas, integral readouts, PMF bars, animation and region selection were cut from the pilot). RW5b adds panel kinds for the dialogue's other domains and figures offered by retrieval and the tutor (§8.7).

### 8.1 What the learner sees

"Make this explorable" on a selected equation, a figure block, a short passage or, *restored* (row 46), **a region of a figure**: on the original-page view the learner drags a rectangle over part of a figure, and only that crop (`build_block_region`, `span_view.py:266`, with the selection's bounding box) plus the caption and the surrounding paragraphs go to the figure author.
- **While it builds,** a small "building an interactive version…" line; reading continues.
- **The result** is a panel beside the passage with sliders for the parameters, linked plots or readouts, and, by default, one **prediction** before the first change ("If p rises to 0.7, which side gains probability?"; for the dialogue's two-sided exponential, "Which shaded area is P(X < 0)?"); the learner answers in a word, a choice or a click on an area, then sees the result.
- **"What changed, and why?"** (round 2 §2's "an explanation of what changes and why", restored): after the result, an optional one-line box. A missed prediction with its answer becomes a `reader_formative` learner text (tier 2, W1).
- **Animation** (restored): a parameter marked `animate` gets a play button that sweeps it across its range ("animate the associated CDF"). It is the same evaluation as dragging the slider.
- **The label is always visible:** "AI-built interactive · matches the source's equation (checked)" for a verified reconstruction; "AI-built illustration of an interpretation (not checked against the source)" otherwise.
- **Unsupported requests** say what was asked for and why it can't be drawn yet ("needs a simulation the figure language can't express"); the report counts them by kind, which informs RW5b's order and the deferred generated-code figures (§17).
- The same figure reopens instantly from the cache.

### 8.2 The spec, not code

The model writes an **`InteractiveFigureSpecV1`** (JSON, strict schema). A trusted React renderer draws it. **No generated code runs anywhere** (generated-code figures are deferred, §17).

```text
spec_version    "ifs-v1"
kind            reconstructed | illustrative
source_claims   [{span_id, quote}]                     # quote-verified
region          {span_id, bbox}?                        # restored: a crop of a figure
parameters      [{name, label, min, max, step, default, animate?}]
definitions     [{name, expr}]                          # the grammar below
panels          function_plot {x:{var,min,max}, series:[{expr,label}], markers?,
                               shade?: [{series, from, to, label}]}      # restored: areas under a series
                pmf_bars      {k:{var,min,max}, series:[{expr,label}],
                               highlight?: {from, to, label}}           # restored: discrete distributions
                linear_map_2d {matrix:[[expr,expr],[expr,expr]]}   # unit square and grid under the map
                readout       {label, expr}                         # may use integral() and sum()
                # RW5b: heatmap_2d, vector_field_2d, trajectory_2d (§8.7)
invariants      [{kind: finite | bounded | nonnegative | integrates_to_one | sums_to_one
                       | monotone_nondecreasing | equals_source, ...}]
predictions     [{prompt, change:{param:value}, observe: expr | choices | area_label}]
annotations     [{target, text}]                        # restored: the dialogue's "pedagogical annotations"; AI-written, labelled
```

**The grammar:** numbers; parameter and variable names; `+ - * / ^`; unary minus; `exp log sqrt abs sin cos tan atan erf Phi min max floor`; `piecewise((cond, expr)…, else)` with comparisons; `pi`, `e`; and, *restored*, `integral(expr, var, a, b)` and `sum(expr, k, a, b)` with finite numeric or parameter bounds. Caps on length, node count and nesting (no integral inside an integral).
- **Two evaluators, one grammar:** a hand-written TypeScript parser and evaluator (no `eval`, no `Function`), and a Python twin in the sidecar. Both implement `integral` with the same fixed adaptive Simpson rule (same depth and tolerance) and `sum` exactly over integers. One golden corpus, run in both vitest and pytest, keeps them identical within 1e-9 relative error, and within 1e-6 for integrals.
- **A shaded area** is drawn under its series between `from` and `to` (expressions, clipped to the plot range) and its value is a linked `integral` readout, so moving `p` or `λ` moves the area and its number together.

### 8.3 Verification (before a figure shows)

Run in the sidecar:
1. **Structural.** Every expression parses; values are finite on a parameter grid (three points per parameter, at most 81 combinations); panels reference defined names.
2. **Invariants.** Each declared invariant holds on the grid, numerically (a density integrates to 1 within 1e-3 by Simpson in Python; a PMF sums to 1 within 1e-9 over its support; a CDF is non-decreasing from 0 to 1; values stay bounded). A shaded area's readout is checked against an independent high-resolution integration in Python.
3. **Source match** (`kind = reconstructed` only). PF's pattern: the verifier (route `figure_verifier`) writes a sympy check, with a negative control, that the spec's defining expression equals the source equation quoted in `source_claims`; the sandbox runs it.

**Outcomes:** passing 1–3 makes the figure `verified`; failing 3 alone downgrades it to `illustrative` with its label; failing 1 or 2 means it is not shown ("couldn't build a reliable version of this", with the reason). Verdicts go to `judgment_ledger` (task `figure_verified`, judge `verifier` or `llm`).

### 8.4 Predictions

A prediction is formative (W1, tier 2): stored on `figure_predictions`, never as an attempt or an evidence observation. The dialogue called a recorded prediction "a formative observation" (round 2 §2); restored, that means a missed prediction, its answer and its "what changed?" text become a `reader_formative` learner text, so learner-text gaps can name the belief behind it, and RW6b counts it among the session's open questions (§9.3). RW6a's recap lists predictions that missed as "worth a second look". Numeric use as a weak observation stays deferred (§17).

### 8.5 Data, routes, spend, privacy

| Table | Role | Contents |
|---|---|---|
| `interactive_figures` | WORKFLOW (paid outputs; never re-run on rebuild) | `id`, `extraction_id`, `span_ids_json`, `region_json`, `asset_id`, `origin` (`selection` \| `library` \| `tutor`), `spec_json`, `spec_version`, `kind`, `verification` (`verified` \| `illustrative` \| `failed` \| `unsupported`), `verification_report_json`, `unsupported_kind`, `model`, `prompt_version`, `input_hash` (reuse key), `created_at` |
| `figure_predictions` | RAW_LEDGER | `id`, `figure_id`, `prediction_index`, `learner_answer`, `observed_json`, `matched`, `explanation_text`, `created_at` |

- **Routes:** `figure_author` (chat; image input when a figure asset or crop is included: an OpenRouter vision model or Codex's image input); `figure_verifier` (chat).
- **Caps (money):** two author attempts and one verifier call per request; `figures.max_daily_cost_usd` ($1.00 metered). The first draft's `figures.max_per_day` (20) count is replaced by the spend cap.
- **Privacy:** source text and, for figures, the figure image or crop. No learner data.

### 8.6 Successor

None: content and formative. Kill switches `figures.enabled`, `figures.predictions_enabled`, `figures.region_enabled`.

### 8.7 RW5b: more figure kinds, and figures offered by retrieval (restored)

The dialogue named the domains (round 2 §2): "probability distributions, optimization objectives, matrix transformations, gradients, attention mechanisms, and dynamical systems". RW5a covers distributions and 2-D linear maps. RW5b adds three panel kinds to the same grammar and renderer, and lets retrieval offer figures (round 3 §5D).

**Panels** (both evaluators, golden-corpus parity, the same verification):
- `heatmap_2d {x:{var,min,max}, y:{var,min,max}, expr, contours?}`: objective landscapes, joint densities, and attention-like weight matrices written as expressions over indices (`exp(s(i,j)) / sum(exp(s(i,k)), k, 1, n)`);
- `vector_field_2d {x, y, u: expr, v: expr}`: gradients and flows, with optional overlaid `heatmap_2d`;
- `trajectory_2d {x0, y0, dx: expr, dy: expr, t_max, steps}` or `iterate_2d {x0, y0, fx: expr, fy: expr, n}`: a dynamical system by fixed-step RK4, or a discrete map such as gradient descent with a learning-rate slider. The step count is a parameter cap on computation, and the integrator is identical in both evaluators so their trajectories agree within the corpus tolerance.

**Figures offered, not only requested** (row 104). When the library organizer (RW4a) or the tutor (RW1c) cites an `equation` or `figure` block, its judgment includes `explorable: yes | no` (can the block support a parameterized, verifiable figure?) at no extra call. A `yes` adds "Make this explorable" to that hit or answer; pressing it runs RW5a's pipeline with `origin = library | tutor`. Retrieval supplies the equation, figure and assumptions; the figure pipeline decides feasibility and verifies, as the dialogue kept them separate. Built figures are reused by input hash and versioned by spec version.

**What stays out:** anything the grammar cannot express (general simulations, agent-based models, arbitrary code) — the generated-code figures deferred in §17, with the unsupported-kind counts as their evidence.

**Data:** RW5a's tables (`origin` already has the values). **Routes:** RW5a's. **Successor:** none. Kill switches `figures.advanced_panels_enabled`, `figures.offers_enabled`.

---

## 9. RW6 — "Last time here", the digest, the router card and cold follow-ups

### 9.1 RW6a: "Last time here" (deterministic, no model)

When the learner opens a source they have read before, the rail shows a compact card above the Guide:
- **the last passage** and "continue there" (P3 restoration, as today);
- **open inquiries** on this source, each with "open" (to the breadcrumb) and status chips (resolve / revisit once / keep open);
- **unfinished problems** from RW2a, each with "Resume this problem";
- **predictions that missed** (RW5a) and **reconnect "still unclear"** answers (RW1a), as "worth a second look";
- after RW6b: the narrative and the scheduled follow-ups, each with its date, purpose and undo.

Today's re-entry panel (DL1, goal-optional re-entry) can show the same card for the most recent source. The card is a pure read over `question_events`, `reader_section_progress`, `workbench_sessions`, `figure_predictions` and the reader envelope; nothing new is stored, and it is dismissible per source.

A **reader session** is one visit on the reader envelope (`visit_id`), or several visits less than 30 minutes apart. RW6a's typed summary is computed per session:
- sections read (from `reader_section_progress`);
- inquiries opened, resolved and still open, with their roots;
- workbench sessions: item, highest help level, submitted or abandoned, grade;
- cues opened or marked not relevant; predictions missed;
- gaps named by learner-text gaps from this session's texts;
- facets touched;
- **"claims needing an independent check":** facets where the session's work was assisted only (help level 3 or more, or a source-visible attempt) and no unassisted success exists since;
- *restored (rows 58, 68):* **the session's formative records**, `ReaderObservationV1`, one per tier-2 signal (W1). Each has the shape the dialogue sketched (round 2 §6), restricted to routing: `kind` (`still_unclear`, `next_step_missed`, `why_step_missed`, `assumption_missed`, `prediction_missed`, `check_questionable`, `hint_taken`, `doesnt_connect`, `discriminate_answer`), `source_event_ids`, `span_ids`, `item_id` and `step_id` where they apply, `facet_candidates` (the item's facets, or the LOs of the spans), `observed` (a short typed field, never prose: the verdict, the predicted and observed values, the help level), `hypotheses` (gap ids named from it, rival causes it was asked against), `assistance` (level, reveal), and `authority: "routing_only"`. They are not compiled by a second model: learner text goes through learner-text gaps (the compiler, W13), verdicts and levels are copied from their rows. The numbers stay with the estimator, which never reads these records (W1).

**Wrap up** (restored, row 23: "an optional session-ending synthesis under a minute"). The rail's footer shows "Wrap up (under a minute)" once a session has activity; leaving a source after activity shows the same offer as a one-line, self-dismissing note that never blocks closing (P3 invariant 1, W12). Wrap up shows three short lists from the typed summary — **resolved**, **still open**, **worth reinforcing** (the claims needing an independent check, and after RW6b the follow-ups proposed with their dates) — each line with one action (resolve, keep open, revisit once, undo). The narrative appears in it when ready. Nothing new is stored: actions write what the same chips write elsewhere. Kill switch `recap.wrap_up_enabled`.

### 9.2 RW6b: the narrative and the router card

**The narrative** is optional (`digest.narrative_enabled`, default on): at most 120 words, written by route `reader_digest` from the typed summary only, citing event ids (validated against the summary), labelled "summary written by LearnLoop's model". It is generated once per session in the background and shown in the "Last time here" card.

**Reader activity in the router's learner-state card.** `reader_activity_for_card(lo_ids, as_of) -> ReaderActivityV1` is a pure read, like `named_gaps_for_card()` on the text-gaps branch. For the candidates' LOs it returns: open inquiries (root question excerpt, age, depth); assisted-only work (facet, highest help level, date); pending reader follow-ups (each with its purpose, date and valuation); missed predictions; *restored (rows 59, 72):* **open hypotheses** from the session (gaps named from its text, rival causes still open, with their source rows), **the session's formative records** (`ReaderObservationV1`, typed, no prose), **kept comparisons** on these LOs (RW4d: the source relationships the dialogue asked the card to carry), and **candidate actions** — the dialogue's "possible next actions" — as a typed list with where each came from (a pending follow-up with its valuation; continue reading at the next unfinished section, or the next core section of a reading path; near-transfer practice proposed by `find_practice`), never a choice; the latest narrative, labelled model-written, with its cited event ids. Router R2 renders it as a "Reader activity" section of `LearnerStateCardV1` (router §4). The card stays deterministic from the ledger, because the narrative is a persisted, cited row (the teach-back summary pattern, router §15.1). **Nothing in it is evidence** (W1). Before R2 the function exists and has tests, but nothing renders it.

### 9.3 RW6b: cold follow-ups (the owner's "short unfamiliar problem")

**No count cap.** The owner's decision of 2026-10-12 (§20.7): value of information chooses, numbers and dates the checks, and the learner's real limits — the daily plan's minutes and the spend caps — bound them. Several follow-ups may be worth it, to find the true misconception, to decide between rival explanations, or to decide between actions. Follow-ups are served through DL2's "Check once". **RW6b builds no valuation of its own** (W13): it assembles the questions and candidates and asks the machinery that already values probes (§3.2).

1. **The open questions.** From the session's typed summary (§9.1), RW6b lists what a later independent attempt could tell LearnLoop about this learner. Each is read where it already lives; no new learner state is written:
   - **claims needing an independent check** (assisted-only work on a facet): the hypotheses are "holds unaided" and "doesn't", with the active predictor's P(success) and interval as the prior (field §4);
   - **rival explanations** still open on the session's facets: the locked hypothesis set and replayed posterior of an open probe episode (`episode_posterior`); a diagnosed attempt's rival causes (`unresolved_cause_factors.candidate_causes_json`); open `causal_hypotheses`; the facet's `hypothesis_marginal`; and, once learner-text gaps has merged, gaps named from this session's text;
   - *restored (RS3; rows 45, 52, 70):* **the session's formative records** (§9.1): a missed prediction, a "still unclear", a missed next-step or assumption answer, a questionable check never resolved, a discriminating answer that left two causes standing. Each adds the facets it touched as a question ("does the learner now hold this unaided?") and, where learner-text gaps named a gap from it, that gap as a rival explanation. They change which questions are asked, never a prior's number (W1, tier 2).
2. **Candidate checks.**
   - For each facet with an open question, `find_practice(query, constraints)` proposes unfamiliar items with two new exact filters on `PracticeConstraints` (§3.4 item 7): `unattempted_only` (no attempt on the item) and `exclude_family_ids` (the families of every item whose solution the session revealed, from the reveal ledger). Admission already applies the scheduler's reserves.
   - *Restored, consumed from `spec_source_practice_and_probes_v1.md` once it merges:* the call passes that spec's `intent` — `retention_check` for a claim needing an independent check, `diagnostic_probe` with the rivals as `target_hypotheses` for rival explanations — and its proposals include **textbook exercises** as their own candidate kind. A chosen textbook exercise goes through that spec's import, verification and family attachment before its commitment is created; RW6b values it like any other candidate. The candidate-valuation adapter over the EIG functions is built once and shared: whichever of the sources spec's EIG ranking and RW6b lands first builds it, and the other reuses it (W13, G35).
   - Open probe episodes on those facets add their eligible instruments (`probe_episodes.eligible_instruments`).
   - **Relevance is the only model judgment.** One listwise call (`judge_listwise`, route `followup_relevance`, ledger task `followup_relevance`) keeps the candidates that test the capability or bear on the rival explanations, quoting what in the item does so. It no longer picks a winner or a number. *Restored:* the same call labels two things the valuation needs:
     - **novelty** (row 79: "unseen wording, unseen surface and genuinely unfamiliar application; new constants are not transfer"): `same_surface` (new constants on a problem the session worked), `new_surface`, or `new_application`, relative to the session's worked items. The label sets the purpose wording ("a new application" only for `new_application`) and feeds the familiarity discount below;
     - **shown by reading** (RS8, row 106: "a textbook exercise from an unread page is a poor cold test if the learner has seen an equivalent worked example"): whether a worked example the learner was shown this session solves the candidate by the same method. The judge sees the worked examples on the candidate's facets that the session exposed (`source_exposure_events`, `reader_section_progress`, ingest and RW4e roles).
3. **Value each candidate with the existing machinery.**
   - **Information about the hypotheses (EIG).** Instruments use `instrument_expected_information_gain`, or the predictive variant when its target set is adequate; the two are never added together (probe EIG spec §7.4). Ordinary items use the per-facet EIG that the post-attempt follow-up slate already computes (`facet_expected_information_gain` over `hypothesis_marginal`), with `_misconception_discrimination` where rival misconceptions are open. Familiar surfaces are discounted with `familiarity_discount` (`learner/recall_coverage.py:293`), as the scheduler does for probes, so a near sibling of a problem just worked counts for less than a genuinely unfamiliar one. *Restored (RS8):* a candidate the judge marked **shown by reading** is treated as a familiar surface of the worked example it matches — the same discount function, with the exposure as the familiar item — and it is never valued as a cold retention check; it may still serve as a discriminating check, labelled "you read a worked example like this one". A `same_surface` candidate is never labelled transfer.
   - **Value for the next decision (EVSI).** Where the session left a decision pending between actions (which repair to try; repair or move on), the loss table is `action_loss.build_loss_table`'s wasted learner-minutes and the value is `evsi.robust_evsi` (point, LCB, UCB). Where no loss table exists, `robust_composition.evaluate_selection` converts the robust EIG to minutes, as the robust probe path already does.
   - **Rank and stop with `evsi.rank_feasible`.** Rank is LCB / (expected minutes + burden); expected minutes come from DL1's estimator (`daily_plan/estimates.py:138`). Checks are added greedily, each valued conditionally on those already chosen (the rule `probe_episodes.plan_precommitted_block` uses for a block), so two checks that would tell LearnLoop the same thing are not both scheduled. Adding stops when the best remaining candidate's LCB ≤ λ·minutes + burden. An `abstain` verdict falls back to the EIG-per-minute order with the same stop, labelled "value uncertain".
   - **The number follows.** A session gets whatever clears the stop: often none, sometimes one, sometimes several, for example to separate two misconceptions and then to check retention.
   - **No new constants.** λ (1, minutes as numeraire), the burden (0) and the nat-to-minutes scale (60) are the existing decision parameters, labelled heuristic in `diagnosis/robust_composition.py:44`–`:55`. Calibrating them is the decision-value spec's job (§9 there); RW6b's receipts give it data.
4. **Date each check by what it is for.**
   - A **discriminating check**, valued for separating rival explanations before a repair decision, is dated for the next day's plan. DL1 never grows today's plan (§6.1), and the check is worth less once the repair is chosen without it.
   - A **retention check**, valued for whether an assisted claim holds unaided, is dated at the practiced item's effective due (DL2 §5.3), when forgetting is expected and a success says most (router §15.2). Without FSRS state the date is `followups.fallback_days` (3) away, labelled as a default.
   - **`followups.max_wait_days` (14) is a time cap:** no claim waits longer than two weeks for its check.
   - The date goes in `due_hint`. **Cross-spec request:** DL2's dated branch reads `due_hint` when present and falls back to `capture.test_me_later_days` otherwise (§18).
5. **Schedule as content, not as a new serving rule.** Each follow-up is a `test_me_later` commitment (disposition `one_check_pending`) on its item, with `provenance = {"via": "reader_followup", "summary_id": …, "purpose": "discriminating" | "retention", "novelty": …, "valuation_ref": …, "inquiry_root_event_ids": […], "anchor_span_ids": […]}`. DL2 serves each exactly like any other "Check once": a dated learner request among the maintain lane's scheduled checks, cold (W7), with restoration after the measurement closes.
6. **Time and money are the only limits.** There is no count cap per session or per day.
   - **Minutes.** The plan's finite minutes bound what is served on any day. Scheduled checks sit in the maintain lane, which takes at most `plan.maintain_max_share` of the minutes (DL1 §6.2); what doesn't fit stays in the full list as "later", never as debt (DL1 §6.1). Dating by purpose spreads checks across days.
   - **Money.** `followups.max_daily_cost_usd` ($0.50 metered) covers the relevance calls. The valuation itself makes no model call.
   - **From router R2 on,** each pending follow-up is also a block candidate that the router values (planner value with robust EVSI, router §3). On a crowded day it then competes with reviews for the minutes instead of always going first.
7. **Re-valuation.** Before each day's plan is built, RW6b re-values its pending follow-ups with the same machinery against the current state. A follow-up whose question has been answered since — the facet was demonstrated unaided, or the rival explanations resolved — no longer clears the stop and is retired with its reason shown ("No longer needed: you solved a problem like this on Tuesday · undo").
8. **Nothing fits → generate in the background** (restored, rows 5, 80, 92: "retrieval first; generate on demand… with the practice-family and task-blueprint machinery, freshness checks and source-grounded verification"). The summary records `no_item` for that question, the card says "No unfamiliar problem on this yet — LearnLoop is writing one", and RW6b queues one generation request through PF Phase 5a's source-anchored path, grounded in the session's spans and the question's facets (the same path the sources spec names for "when nothing fits"; if it builds a request API, RW6b calls that). Generation is CPU-slow batch work and never runs on the session's request path. A generated item is verified by PF-b before it exists; the next daily re-valuation (item 7) sees it as a candidate like any other. Money bounds it: `followups.generation_max_daily_cost_usd` ($1.00 metered); a capped request waits for the next day. Kill switch `followups.generate_when_nothing_fits` (off: `no_item` stands, as before the restoration).
9. **Back to where it was studied** (restored, RS9, row 83: "after the cold attempt, reopen the Reader at the most relevant passage or inquiry branch if repair is warranted"). Each follow-up's provenance carries the session's inquiry roots and anchor spans. When a follow-up is answered wrong, or with help, DL2's restoration after the measurement shows "Back to where you studied this: Mixture CDF → integration bounds", which opens the Reader at that inquiry branch or passage. It is a link, never an automatic jump.

**Labelled, with undo.**
- The card lists every scheduled check with its date and purpose: "Thursday: a problem that tells apart two explanations of your step-4 error · undo"; "Next Monday: a new mixture-distribution problem, cold · undo".
- "Why" shows the valuation as LearnLoop's estimate ("expected to settle which repair to try · about 6 min"), never as a verified fact (W2).
- "Undo all" retires every follow-up from the session. Undo and re-valuation retire the commitment (`commitments.retire`); undo also appends a `learner_card` verdict.
- Each relevance verdict appends `judgment_ledger` (task `followup_relevance`, judge `llm`).

**The valuation receipt** is stored on the digest row (§9.4): the questions (with the formative records that raised them), every candidate with its kind (item, instrument, textbook exercise, generated), its novelty and shown-by-reading labels and the discount they caused, its EIG, EVSI point, LCB and UCB, expected minutes, the verdict (`measure`, `stop`, `abstain`) and the stop reason, the chosen ids in order, and the module versions. Fields that R1 also logs for scheduler candidates use R1's names (`probe_eig`, `evsi_assignment`), so router R3's replay can read both. Replay never re-values (W9).

**Why no successor.** The serving algorithm is unchanged: it serves commitments as DL2 defines them. RW6b adds content (commitments) that the learner can undo, behind a kill switch, which is the precedent learner-text gaps set for its live prerequisite creation and seed check. This is the first live use of `evsi.rank_feasible`, but it decides only which commitments to create, never what the scheduler serves or how evidence counts. The RW6b agent confirms this with the reviewer. If they rule otherwise (for example because uncapped checks change the maintain lane's composition), RW6b takes the next free `mvp-0.N` tag with plan parity under `followups.enabled = false`.

**The outcome** joins later in the report: cold success after assisted reader work, and whether each check told LearnLoop what its valuation predicted (§15).

### 9.4 Data

| Table | Phase | Role | Contents |
|---|---|---|---|
| — | RW6a | — | No table: the card and summary are pure reads |
| `reader_session_digests` | RW6b | WORKFLOW (the narrative and the relevance verdicts are paid outputs; never re-run on rebuild) | `id`, `visit_ids_json`, `started_at`, `ended_at`, `summary_json` (typed, including each question's outcome or `no_item`), `narrative_md`, `cited_event_ids_json`, `followup_commitment_ids_json`, `valuation_json` (the receipt, §9.3), `model`, `prompt_version`, `dismissed_at`, `created_at` |

Follow-ups live in `commitments`; re-valuation retirements are commitment events with their reason. Nothing else is added.

### 9.5 Routes, spend, privacy

- **Routes:** `reader_digest` (chat) and `followup_relevance` (listwise, through `judge_listwise`); Codex by default, since both are background work. The valuation makes no model call. Background generation uses PF's routes.
- **Caps (money only):** one narrative per session; `followups.max_daily_cost_usd` ($0.50 metered) for relevance calls; `followups.generation_max_daily_cost_usd` ($1.00 metered) for generation. Nothing caps the number of follow-ups (§9.3).
- **Privacy:** the typed summary goes to the provider, the same class as the router card.

### 9.6 Successor

None (§9.3, with the stated fallback). Kill switches: `recap.enabled` (RW6a), `recap.wrap_up_enabled`, `digest.enabled`, `digest.narrative_enabled`, `followups.enabled` (off: no follow-up is created and no re-valuation runs; existing ones stay as the learner's commitments and can be undone), `followups.formative_questions_enabled`, `followups.exposure_discount_enabled`, `followups.generate_when_nothing_fits`.

---

## 10. RW7 — Goal-aware reading paths (restored)

Deferred in the first revision; restored by the owner's decision (§20.8) as two phases. The dialogue (round 1 D, after Matuschak's "routes of different depths through the canonical text"): the path should "explain why material is included, what can be skipped based on existing evidence, and whether it is a prerequisite or enrichment", and "let the learner override the recommendation". The first revision's two corrections stand: roles come from `role_hint` and RW4e's proposals plus the path judge, not a separate index; and changing DL1's reading block is a serving change.

### 10.1 RW7a: the path in the Guide (display only)

- **The depth is the learner's.** The Guide asks once per source, "How deep do you want to go?": **get the idea** (definitions, examples, visualizations), **learn to use it** (explanations, worked examples, practice), **fluency** (novel problems, changed assumptions, delayed checks). Remembered per source; changeable any time. When DL2's control lands, its intents map onto these (Master: fluency; Learn: learn to use it; Keep and Light touch: get the idea), and the Guide's choice and DL2's stay one setting.
- **What the learner sees.** Per section: **core**, **prerequisite**, **enrichment**, **already shown** or **assumed**, each with a one-line "why" ("needed for the mixture CDF you're working toward"; "you showed this on 2 Oct, unaided"), and "read it anyway" / "skip it". The "Orient" intention's "What matters here?" opens this view (RW1b).
- **One exercise worth trying** (row 34: "the guide identifies a relevant section and one representative exercise"). Each core section can name one exercise to try after it: an `exercise` block of that section, or, once the sources spec merges, its best textbook-exercise candidate for the section's LOs. "Try it" opens it in the workbench, imported through the usual path.
- **How labels are decided.** One LLM call per source and depth (route `reading_path_judge`) over the section list, the sections' roles, the learner's status on the linked LOs, the depth and the goal. `already shown` stands only if every LO the section teaches is demonstrated (`lo_certification(...).demonstrated`), and `assumed` only with an open `assumption_decisions` row; otherwise the label falls back to `core`. Verdicts append `judgment_ledger` (task `reading_path_role`). A learner override appends a `learner_card` verdict and is kept; "skip it" marks nothing as known (W1).
- **Display only.** RW7a changes no plan, no evidence and nothing served. Re-judged when the depth changes or an LO's status changes (cache key: depth, section list hash, LO statuses).
- **Data:** `reader_path_sections` (WORKFLOW: paid outputs; never re-run on rebuild): `id`, `extraction_id`, `depth`, `section_id`, `label`, `reason`, `exercise_span_id`, `learner_override`, `ledger_id`, `state_key`, `model`, `prompt_version`, `created_at`.
- **Successor:** none. Kill switch `reading_paths.enabled` (off: today's Guide).

### 10.2 RW7b: the plan follows the path (algorithm successor)

- **What changes.** DL1's reading block (§6.10 there) opens the next unfinished **core** or **prerequisite** section of the source's path instead of the next section in book order; enrichment is never planned; a learner's "read it anyway" makes a section core for planning.
- **Why a successor.** This changes what is served (F3). RW7b takes the next free `mvp-0.N` at its merge, with receipts recording the section DL1's order would have chosen.
- **Kill switch** `reading_paths.plan_uses_path` (off: DL1's order, byte-identical).
- **Depends on** RW7a and DL1 (merged); not on DL2.
- **Gates** (the first draft's G28–G29, renumbered G47): honest path labels; `reading_paths.plan_uses_path = false` leaves DL1's reading blocks byte-identical, with a rebuild showing zero projection deltas.

---

## 11. Persistence summary

**Migrations.** One per phase that needs one, numbered when it lands (`ls migrations/`; head 180 on `main` at `57d31c63`, with R1, facet identity and learner-text gaps claiming numbers first in the merge chain). Follow `CLAUDE.md`'s head-fixture procedure. Every CHECK'd column is created with all the values any phase here will write, so no later phase rebuilds a table this spec created.

| Table | Role (`db/table_roles.py`) | Phase |
|---|---|---|
| `reader_authored_questions` (existing): `ADD COLUMN scope_kind`, `question_style` (five values), `anchor_span_ids_json`, `inquiry_root_event_id` | unchanged | RW1a |
| `learner_text_gaps`, `learner_text_gap_jobs` (existing, from learner-text gaps): widen the `source_kind` CHECK with `workbench_text` and `reader_formative` (rebuild, FK-safe; §3.4 item 13) | unchanged | The first adapter phase (RW1b or RW2b) |
| `workbench_sessions` | WORKFLOW | RW2a |
| `workbench_steps` | RAW_LEDGER | RW2a |
| `workbench_assists` (with RW2c's kinds and columns) | RAW_LEDGER | RW2b |
| `passage_links` | WORKFLOW | RW3b |
| `reader_cue_impressions` | RECEIPT | RW3b |
| `library_asks` (with RW4d's columns) | WORKFLOW | RW4a |
| `interactive_figures` (with RW5b's `origin` values) | WORKFLOW | RW5a |
| `figure_predictions` | RAW_LEDGER | RW5a |
| `reader_session_digests` | WORKFLOW | RW6b |
| `reader_path_sections` | WORKFLOW | RW7a |

RW1b (unless it carries the widening migration), RW1c, RW2c, RW2d, RW3a, RW4b, RW4d, RW4e, RW5b, RW6a and RW7b need no migration. RW4d and RW4e write proposals into the existing `source_objects`, `source_object_versions`, `source_object_citations` and `source_object_relations` tables (P3 §7). **No DERIVED table, so no new replayer:** RW2c's help outcomes and RW6a's formative records are pure reads. Replay never reads these tables; the evidence they lead to lives in `practice_attempts` (`hints_used`, `primed`) and `reveal_events`, which replay already reads. **One table rebuild, and only of the learner-text tables:** no new `interaction_events` kind and no new reveal kind.

**Events.** Existing reader kinds with a payload `event` field (§4.3): RW1 adds `intent_routed`, `intent_corrected`, `reconnect_answered`, `next_step_requested`, `another_way_opened`, `reconstruct_scheduled`, `tutor_offer_pressed`; RW2 adds `workbench_opened`, `workbench_resumed`, `workbench_left`, `workbench_closed`; RW3 `cue_shown` (RW3a only; RW3b's impressions table is authoritative), `cue_*` taps, `cue_density_changed`; RW4 `library_ask`, `compare_opened`, `comparison_kept`, `my_take_added`, `exercise_chosen`; RW5 `figure_opened`, `figure_animated`, `figure_region_selected`; RW6 `recap_shown`, `wrap_up_opened`, `followup_undone`, `back_to_study_opened`; RW7 `path_depth_set`, `path_override`. The salience-firewall test gains each.

**Config** (modelled defaults, out of the decision-only template unless it has room). Each phase recomputes the latest `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry with a "no scoring, scheduling, projection or serving change" note (§3.4 item 9); RW2d and RW7b record their successor instead:
- `[reader_inquiry]`: `enabled`. `[reader_intent]`: `enabled`, `timeout_seconds` (4), `max_calls_per_day` (200). `[reader_active_reading]`: `enabled`. `[reader_formative]`: `enabled`. `[reader_tutor]`: `retrieval_enabled`, `offers_enabled`.
- `[workbench]`: `enabled`, `help_enabled`, `level_chooser_enabled`, `symbolic_checks_enabled`, `discriminate_enabled`, `error_kind_enabled`, `help_outcomes_enabled`, `examples_enabled`, `compare_methods_enabled`, `passage_draw_enabled`, `field_signals_enabled` (RW2d, a successor's switch), `open_session_days` (30), `max_calls_per_session` (24, a money cap counted in calls), `max_daily_cost_usd` (1.00), `price_per_million`.
- `[cues]`: `enabled`, `discovery_enabled`, `try_first_enabled`, `value_order_enabled`, `density` (`fewer` \| `normal` \| `more`, i.e. 1, 2 or 4 per section; default `normal`), `holdout_rate` (0.1), `max_calls_per_source_open` (12), `max_daily_cost_usd` (0.50).
- `[library_ask]`: `enabled`, `expand_graph` (true), `personalized_default` (true), `max_daily_cost_usd` (1.00). `[compare_sources]`: `enabled`, `keep_enabled`, `tutor_enabled`, `max_sources` (4, a context-size cap). `[library_exercises]`: `enabled`, `fallback_enabled`. `[roles]`: `on_demand_enabled`, `positive_filter_enabled`, `batch_max_cost_usd` (5.00, per batch run).
- `[figures]`: `enabled`, `predictions_enabled`, `region_enabled`, `advanced_panels_enabled`, `offers_enabled`, `max_daily_cost_usd` (1.00).
- `[recap]`: `enabled`, `wrap_up_enabled`. `[digest]`: `enabled`, `narrative_enabled`. `[followups]`: `enabled`, `formative_questions_enabled`, `exposure_discount_enabled`, `generate_when_nothing_fits`, `fallback_days` (3, a dating default without FSRS state), `max_wait_days` (14, a time cap), `max_daily_cost_usd` (0.50), `generation_max_daily_cost_usd` (1.00). No count cap (§9.3, §20.7).
- `[reading_paths]`: `enabled`, `plan_uses_path` (RW7b, a successor's switch).

**Routes** (each its own `ai.routing.*`, added to the `AITask` literal, `ROUTE_FOR_OPERATION` and the config schema):
- **decider tasks** (added to `DECIDER_TASKS`; never a chat fallback, never overridden by `LEARNLOOP_AI_PROVIDER`): `reader_intent`, `workbench_level_chooser`;
- **listwise tasks** (through `judge_listwise`): `passage_cue_judge`, `library_organizer`, `followup_relevance`, `example_fit`, `role_labeller` (batch only);
- **chat tasks:** `workbench_check`, `workbench_hint`, `figure_author`, `figure_verifier`, `reader_digest`, `reading_path_judge`.

Unset chat routes fall back to the active provider, and receipts record the resolved model. RW1c uses the tutor's existing route; background generation uses PF's.

**`judgment_ledger` tasks:** `reader_intent`, `workbench_hint_fit`, `passage_cue`, `library_contribution`, `example_fit`, `source_role`, `compare_relation`, `figure_verified`, `followup_relevance`, `reading_path_role`, plus `learner_card` rows on the same tasks for corrections, taps, feedback, overrides and undos. The ledger's judge CHECK (migration 175) already admits `llm`, `verifier`, `decider` and `learner_card`; `task` is free text. No change.

---

## 12. Algorithm successors and kill switches

| Change | Kind | Successor | Kill switch | The switch restores |
|---|---|---|---|---|
| Branches, inquiry status, reconnect, report, friction audit, every source kind (RW1a) | Content and display | None | `reader_inquiry.enabled` | Today's flat rail |
| Intent box with the five intentions; next-step, why-step, assumption, another-way and reconstruct questions; `reader_formative` texts (RW1b) | Content, formative (tier 2) | None (learner-text-gaps precedent) | `reader_intent.enabled`, `reader_active_reading.enabled`, `reader_formative.enabled` | Today's palette; no new learner texts |
| Tutor retrieval, three modes, another way, that didn't help, offers (RW1c) | Retrieval context and display; offers are learner picks | None (T6's ruling) | `reader_tutor.retrieval_enabled`, `reader_tutor.offers_enabled` | Today's selection-and-neighbours tutor |
| Workbench scratchpad and submission (RW2a): source visible as one hint-equivalent | Content, existing evidence semantics | None, unless the agent finds a mapping that needs a new rule (then the next free `mvp-0.N`) | `workbench.enabled` | Today's practice screen, byte-identical |
| Checks with step graph and error-kind guess, hints, discriminating question, chooser, feedback, `workbench_text` (RW2b); diagnoser trace when present | Content, existing evidence semantics; tier-2 signals; context only when present | None (stuck-reading precedent) | `workbench.help_enabled` and its sub-switches | RW2a |
| Help outcomes, passage draws, examples in your route, compare methods (RW2c) | Context, display, learner picks; reveals through the existing ledger | None | `workbench.help_outcomes_enabled`, `.examples_enabled`, `.compare_methods_enabled`, `.passage_draw_enabled` | RW2b |
| **Workbench signals in the learner field (RW2d)** | **Serving: Phase 6's fast-track reads the signals** | **The next free `mvp-0.N`** | `workbench.field_signals_enabled` | The predecessor's field derivation and plans, byte-identical |
| Guide cues in the margin; Guide statement read from the overlay (RW3a) | Display | None | `cues.enabled` | No cues; the rail's statement is still corrected |
| Discovered cues, value order, try-first cues, contrasts, holdout (RW3b) | Display; "Check me" and "Try first" are learner picks | None | `cues.discovery_enabled`, `cues.value_order_enabled`, `cues.try_first_enabled`, `cues.holdout_rate` | RW3a |
| `find_sources` with graph expansion and `post_attempt`, library ask, compare, exercises view (RW4a/b) | Retrieval context and display | None (T6's ruling) | `library_ask.enabled`, `library_ask.expand_graph`, `compare_sources.enabled`, `library_exercises.enabled` | T6 as merged |
| `compare_sources` tool, kept comparisons, my take (RW4d) | Source-object proposals (P3 §7) and display | None | `compare_sources.keep_enabled`, `compare_sources.tutor_enabled` | RW4a's display-only compare |
| Instructional role proposals and positive filters (RW4e) | Source-object proposals; retrieval context | None | `roles.on_demand_enabled`, `roles.positive_filter_enabled` | Ingest roles only |
| Figures, areas, sums, animation, regions, predictions (RW5a); more panels and offers (RW5b) | Content, formative | None | `figures.enabled` and its sub-switches | — |
| Recap, formative records, wrap up (RW6a); digest and card section (RW6b) | Content | None | `recap.enabled`, `recap.wrap_up_enabled`, `digest.enabled` | — |
| Follow-ups valued by the existing EIG/EVSI machinery, with no count cap, as "Check once" commitments, with formative questions, textbook exercises, exposure discount, novelty, background generation and the way back (RW6b) | Content served by DL2's unchanged rule; first live use of `evsi.rank_feasible`, deciding only which commitments to create | None (§9.3; fallback: the next free `mvp-0.N` with plan parity) | `followups.enabled` and its sub-switches | No new follow-ups and no re-valuation |
| Reading paths in the Guide (RW7a) | Display | None | `reading_paths.enabled` | Today's Guide |
| **The plan follows the path (RW7b)** | **Serving: DL1's reading block** | **The next free `mvp-0.N`** | `reading_paths.plan_uses_path` | DL1's book order, byte-identical |

**Kill-switch parity is a gate** for every row: switch off, the RPCs it touches return byte-identical results on fixture copies.

The RW3a fix to `_learner_signal` changes a Guide reason string and ranking input only (the Guide is display; `build_guide_plan` writes no evidence and serves nothing). Its gate is a Guide-plan snapshot test on a split fixture.

---

## 13. Rollout

Every phase goes through `implementation_goal.md` §2's loop: implement, adversarial review (Codex, or Opus 5.5 when Codex is out), fix, gate, integrate. Phases merge one at a time. Keep at most two Reader phases open at once; all of them touch the Reader's frontend. The Reader workbench is not part of the goal's definition of done (`implementation_goal.md` §1), so it yields the merge queue and Codex capacity to the goal's tracks (DL2, DL3, router R2) when they compete.

| Phase | Builds | Needs | Size | Gate and owner checkpoint |
|---|---|---|---|---|
| **RW1a Inquiry** | Port the branch; rail split; inquiry status and reopen; breadcrumb and return; reconnect with passage-scoped check (migration, with all five question styles); the report's funnel; *the friction audit; transcript and notes parity* | `main` | **M** | G1, G2, G4, G51 (transcripts). **Checkpoint:** a week of reading, then the funnel and the audit |
| **RW3a Guide cues** | The overlay fix in `_learner_signal`; margin marks; taps; wording templates; *the density control* | RW1a (rail split) | **S** | G13, G14 (budget and skim only), G16, G30 |
| **RW6a "Last time here"** | The recap card; the typed session summary; *`ReaderObservationV1` records; Wrap up* | RW1a. Unfinished problems appear once RW2a lands; formative records fill in as their phases land | **M** (was S–M) | G25 (summary part), G31, G50 |
| **RW2a Scratchpad** | Sessions and steps (migration), the step editor, saving and resume, Submit with the source-visible rule, practice-screen "Work in steps" | RW1a (rail split) | **M** | G5 (rows for source visible and no help), G6, G10, G11, G32. **Checkpoint:** a week of solving |
| **RW1b Intent and active reading** | The intent box with the Decider; *the five intentions*; next-step, why-step, *assumption, another-way and reconstruct* questions; *`reader_formative` adapter and, if learner-text gaps has merged, the widening migration* | RW1a. `learner/text-gaps` merged for the adapter (else skipped, recorded) | **M** (was S–M) | G3, G4, G36, G51 |
| **RW4a Library and compare** | `find_sources` (four policies, *facets, graph expansion*), library ask with organizer and tutor, pin and compare (display), practice this question (migration, with RW4d's columns) | RW1a; DL1 merged for learner-pick blocks (optional). Sources spec optional: its candidates and `intent` appear when it merges | **M** | G17, G18, G19, G20, G40 (`post_attempt`), G53 |
| **RW2b Checks and help** | Assists (migration, with RW2c's kinds), check *with step graph and error-kind guess*, ladder, contract *with the discriminating question*, feedback, chooser, *wider* symbolic checks, bridging, diagnoser trace, *`workbench_text` adapter (and the widening migration if RW1b didn't carry it), in-session updates* | RW2a. ChatGPT-plan provider signed in (latency). `learner/text-gaps` merged for the adapter (else skipped, recorded). Sources spec optional ("a short problem instead") | **L** | G5 (all rows), G7, G8, G9, G12, G33, G36, G37, G38. **Checkpoint:** the workbench report (help levels by facet over time, recovery, unusable-hint rate, discriminating answers vs diagnoses, latency) |
| **RW1c Tutor that looks things up** *(new)* | Reader-context span provider with its own query; three modes; another way; that didn't help; offers | RW4a (`find_sources`). Sources spec's `alternative` and `remediate` intents (fallback without them). RW4d and RW5b for their offers (each offer appears when its phase lands) | **M** | G48, G53 |
| **RW3b Discovered cues** | Links, listwise judge, holdout, impressions (migration); *value order from existing state, try-first cues, contrast lists, role proposals from the judge* | RW3a. `learner/text-gaps` merged for gap targets (works without). RW4e for contrast roles (works without) | **M–L** (was M) | G13–G16, G42. **Checkpoint:** cue report once there is data |
| **RW4b Exercises view** | The Reader's view of the sources spec's textbook-exercise candidates; the fallback search until then | RW4a; sources spec for the candidates (fallback without) | **S** (was S–M: the backend moved to the sources spec) | G19, G34, G53 |
| **RW4d Syntopic tool** *(new)* | `compare_sources` with perspectives; keep as source-object proposals; my take; "compared" marks; tutor caller | RW4a | **M** | G18, G43 |
| **RW4e Instructional roles** *(new)* | Role fields in four judges; proposals in `source_objects`; positive filters; the batch labeller | RW4a (the organizer); later judges add roles as they land | **M** | G44 |
| **RW5a Figures** | Spec, grammar *with integral and sum*, both evaluators with the golden corpus, renderer (function plots *with shading*, *PMF bars*, linear maps, readouts, *animation*), *region selection*, verification, predictions *with "what changed?"*, cache (migration) | RW1a (entry point) | **L** (was M–L) | G21–G24, G45 |
| **RW5b More figures** *(new)* | Heat maps, vector fields, trajectories and iterated maps; feasibility in the organizer and tutor; offered figures | RW5a; RW4a and RW1c for offers | **M** | G21, G22, G46 |
| **RW2c What helps** *(new)* | `help_outcomes`; lines to the writer and chooser; passage draws; `find_examples` with `example_fit`; compare methods with `post_attempt` | RW2b; RW4a (`find_sources`) | **M** | G39, G40 |
| **RW2d Workbench field signals** *(new; successor)* | Two signal sources in the field derivation; receipts; parity | RW2b; the field's Phase 6 on `main` | **S–M** | G41 |
| **RW7a Reading paths** *(new; was deferred)* | Depth choice; path judge; labels, reasons, overrides; one exercise per core section (migration) | RW1a; RW4b or the sources spec for exercise candidates (works without) | **M** | G47 (labels) |
| **RW7b Plan follows the path** *(new; successor)* | DL1's reading block reads the path; receipts; parity | RW7a; DL1 (merged) | **S–M** | G47 (parity) |
| **RW6b Digest, card, follow-ups** | Narrative (migration), `reader_activity_for_card` *with open hypotheses, formative records, kept comparisons and candidate actions*, the relevance judge *with novelty and shown-by-reading*, the valuation adapter over the existing EIG/EVSI functions (§9.3, shared with the sources spec) with its receipt, `PracticeConstraints` filters, follow-up commitments with `due_hint` and purpose, daily re-valuation, undo, *formative questions, exposure discount, background generation, the way back* | DL2 merged (with `due_hint`); RW2a (assisted work); `main`'s EIG and EVSI modules (no new valuation). Sources spec optional (intents and textbook exercises). R1 merged is recommended, not required: the receipt borrows its field names. R2 later renders the card section and values pending follow-ups as block candidates | **L** (was M–L) | G25–G27, G35, G49. **Checkpoint:** two weeks, then the follow-up outcomes and valuation-calibration blocks |
| *Sources spec (`spec_source_practice_and_probes_v1.md`)* | Textbook exercises as candidates; the discriminating search; `find_sources` intents; `find_practice` callers; the router §15.3 tool | Its own phases, as a separate backend track | — | Its own gates |
| *Router R2 (router spec)* | Renders `ReaderActivityV1`; values each pending reader follow-up as a block candidate (planner value with robust EVSI, router §3), so follow-ups compete with reviews for a day's minutes | R1; DL1; RW6b for the reader section and follow-up candidates (R2 may land first) | — | Router gates |
| *Count caps on value of information (separate serving stage)* | The owner's decision on the four other count caps (§18) | Its own successor | — | Its own gates |

**Size key:** S ≈ one agent session plus review (about a day); M ≈ two to four days of implement, review and fix; L ≈ one to two weeks. *Italics* in "Builds" mark what the restoration added.

**Recommended order** (dependencies in the table):
1. **RW1a** first (it ports finished work and splits the rail).
2. **RW3a** and **RW6a** (small, immediate learner value) alongside **RW2a**.
3. **RW1b** and **RW4a**.
4. **RW2b** once the ChatGPT-plan sign-in and learner-text gaps are in. RW2 is the core differentiator and the owner's own pain point; RW2a delivers its non-AI half early, and the discriminating question is RW2b's most valuable addition.
5. **RW1c** and **RW4b**, which gain the sources spec's backend as it merges; then **RW3b** and **RW4d**.
6. **RW5a**, **RW4e** and **RW7a** (independent of each other; two at a time).
7. **RW2c**, **RW5b** and **RW2d**; then **RW7b**.
8. **RW6b** whenever DL2 lands (it may move earlier in this list: it depends on DL2, RW2a and `main`, not on phases 3–7).

The sources spec's track runs in parallel throughout: it does not touch the Reader's frontend, so it does not count toward the two-open-phases limit.

---

## 14. Gates and tests

| # | Gate |
|---|---|
| G1 | **Branch port parity.** The branch's 8 backend and 9 frontend tests pass on `main`. A follow-up's prompt holds only its ancestors. T6's retrieval for a follow-up uses the follow-up's own question. Legacy flat histories read as roots |
| G2 | **Inquiry status is not evidence.** Resolving, reopening, "revisit once" and reconnect answers write no attempt, observation, mastery or FSRS row. The salience firewall covers every new payload `event` |
| G3 | **Intent routing.** A routed action has exactly the effect of the same palette action (the same RPC and payload). An empty Enter makes no model call. An unavailable, timed-out or spent-out Decider routes to Ask. "change" records a `learner_card` verdict. With `reader_intent.enabled = false`, the selection UI is today's |
| G4 | **Scoped questions are formative and keyed.** Reconnect, next-step, why-step, assumption and reconstruct questions write no attempt (a reconstruct item is an ordinary practice item only after escalation, and its commitment is an ordinary `test_me_later`). A passage-scoped row never shadows its section's quick check (lookup filtered by `scope_kind`). Reuse keys hold. Section quick checks are byte-identical |
| G5 | **Assistance mapping.** For the source visible or hidden, and each help level (0–5) and combination, the submitted attempt's `hints_used`, `primed` and reveal rows match §5.4, and `resolve_attempt_activity_policy` gives the stated FSRS and certification eligibility (any source visibility, check or hint earns zero certification credit in both projections). A rebuild reproduces evidence identically. An abandoned session writes no attempt |
| G6 | **The grader stays blind.** The rendered blind-grading prompt for a workbench attempt contains the composed answer only: no step history, assist text, hint, feedback or learner state |
| G7 | **Reconciliation contract.** A fake hint writer that cites no learner step, continues from a step that depends on the first questionable one (or, without a graph, comes after it), or repeats a strategy after a "doesn't connect" reply is caught, re-asked once, then downgraded as §5.2 says |
| G8 | **Leak control.** A level-1–3 hint containing the expected answer (including short numeric answers) is never shown. Bridging never returns the item's exercise, solution or linked blocks, and never delays the hint |
| G9 | **Symbolic labels.** "checked" appears only when the sandbox ran the check and its negative control behaved. Without bubblewrap every verdict reads "model's reading". Only declared kinds (§5.3) are attempted; a numerically checked inequality is labelled "checked numerically" |
| G10 | **Source visibility.** A Reader workbench attempt with the source visible goes through `submit_attempt`, is graded and diagnosed, and earns zero certification credit in both projections. "Hide the source" makes an ordinary attempt. Opening the source afterwards records the exposure and the hint-equivalent |
| G11 | **Workbench kill switch.** With `workbench.enabled = false`, practice RPCs and screens are byte-identical to `main` on fixture copies |
| G12 | **Spend.** Per-session and daily caps hold. A capped session keeps authored hints. Codex receipts are `estimated_only`. The chooser's time box falls back to level 1 |
| G13 | **Cues are display only.** With cues on or off, evidence, mastery, projections, FSRS and the plan are byte-identical. "Check me" produces an ordinary learner-pick attempt |
| G14 | **Restraint and holdout.** No section shows more cues than the learner's density budget. No cue in skim mode. Guide cues are never held out. For discovered cues the logged propensity equals the draw probability, and seeds reproduce draws |
| G15 | **Judges decide.** With the cue judge stubbed to `none`, no discovered cue appears, whatever retrieval ranks (R1). Every discovered cue has a ledger verdict and a verified quote |
| G16 | **Wording.** Cue copy comes from fixed templates. A lint test rejects "weak", "you don't understand", "you struggle" and similar |
| G17 | **Sources first.** A library ask returns passages and organizer lines, never a tutor essay, until the learner asks the tutor. Each organizer line cites exactly one returned hit. The tutor's citations stay inside the pinned hits |
| G18 | **Compare keeps sources apart.** Every statement shown quotes a verified passage of its own source; a failing line is dropped. Without "Keep", nothing is written to `source_objects` or relations (table diff); with it, only RW4d's proposals (G43). No concept edge, facet merge, prerequisite or LO change is ever written |
| G19 | **Retrieval policies.** `cold_attempt` returns nothing. `assisted_practice` equals `TutorSpanProvider`'s scope and filters for the same item (no exercise or solution block, nothing linked, nothing leaking the answer). `post_attempt` equals `assisted_practice` while the item's attempt window is open. Policies and expansion lists are recorded on every manifest. An RW4e role proposal never changes what an item-bound scope excludes |
| G20 | **RW4 kill switches** restore T6's library search, tutor spans and Quick Add behaviour byte-identically |
| G21 | **No generated code runs.** The grammar parser rejects everything outside the grammar (fuzzed). The renderer has no `eval` or `Function`, enforced by a lint rule |
| G22 | **Two evaluators agree** on the golden corpus within 1e-9 relative error (1e-6 for `integral`), and the corpus covers every grammar construct and panel kind |
| G23 | **Labels follow verification.** "matches the source's equation" appears only after step 3 passed. A figure failing steps 1 or 2 is never shown. Unsupported requests are recorded with their kind |
| G24 | **Predictions are formative.** They write no attempt, no evidence observation and no field signal; a missed one queues a `reader_formative` learner text (G36) |
| G25 | **Recap, digest and card.** The typed summary is deterministic from the ledgers (computed twice, identical). The narrative cites only ids in the summary. `ReaderActivityV1` contains no cold-answer or reserved-surface material (router G5) |
| G26 | **Follow-ups are unfamiliar and valued, not counted.** Never an attempted item; never an item in a family whose solution the session revealed; `no_item` when nothing fits, with a background generation request (never served unverified, never on the request path). With a fake valuation where every candidate's LCB is below its minutes, none is created; where several clear it, all of them are created in rank order, with no count cap, and conditional valuation drops a second check that duplicates the first. Every created follow-up has a receipt whose chosen value cleared the stop rule. Re-valuation retires a follow-up whose facet was since demonstrated unaided, with its reason |
| G27 | **Follow-ups are ordinary "Check once" commitments.** Served by DL2's dated branch on `due_hint`, cold, with restoration after; discriminating checks dated for the next day's plan, retention checks at effective due, none later than `followups.max_wait_days`. A day with more due follow-ups than its maintain minutes serves what fits and leaves the rest as "later" (plan minutes never exceeded). Undo and "undo all" retire the commitments. With `followups.enabled = false` no commitment is created and plan builds equal DL2's |
| G35 | **Reuse, not a new chooser.** The valuation calls `evsi.robust_evsi` / `evsi.rank_feasible`, the probe-EIG functions and `familiarity_discount` (asserted by monkeypatching them in the test); RW6b defines no EIG, EVSI or stop rule of its own. The valuation makes no model call; replay never re-values |
| G30 | **The Guide reads the overlay.** On a split fixture with a live diagnosis, the Guide's passage reason names the diagnoser's statement; on a joint-graded fixture it is unchanged |
| G31 | **The recap is a pure read.** Opening a source with the recap on or off writes nothing but the `recap_shown` event |
| G32 | **Resume.** Steps survive navigation, sidecar restart and app restart (flush-on-leave tested); "Leave for now" keeps the session open; "Abandon" closes it; a resumed session shows its full history |
| G33 | **Hint feedback.** A "doesn't connect" reply reaches the next hint's prompt at once and appends a `learner_card` verdict; the next hint changes strategy |
| G34 | **Exercises from sources.** Before the sources spec merges: fallback candidates are `exercise` or `worked_example` blocks from the teaching scope, and choosing one runs `import_exercises` unchanged. After: candidates are the sources spec's, and "use this one" calls its import path. Either way nothing is imported without the learner's pick |
| | *Added by the restoration (§20.8):* |
| G36 | **W1's tiers hold.** For every tier-2 path (`reader_formative`, `workbench_text`, check verdicts, hints taken, discriminating answers, predictions), a table diff shows no write to `grading_evidence`, `facet_recall_state`, `facet_capability_evidence`, certification, coldness, FSRS state, `probe_observations` or any mastery projection; the only writes are learner-text gap rows and their jobs, workflow rows and events. The salience firewall covers each new `event` and source kind. The widening migration preserves every existing learner-text row and passes `foreign_key_check` (durability lane) |
| G37 | **Ask before repairing.** With two or more rivals open on a questionable step, the first offer is a `discriminate` question; with one, or help style "guide me", it is not. Candidates are ranked by `instrument_expected_information_gain` (asserted by monkeypatch); a candidate whose rivals all predict the same answer is never offered. The question passes leak control and states neither rival. Its answer reaches the diagnoser trace and the next hint's context, and writes no posterior or probe observation |
| G38 | **The step graph and the guess.** A questionable step marks only its dependents as not standing; `continue_from` may be a later independent valid step. The error-kind guess is labelled "the model's guess", appears in the diagnoser trace, and is never written as a diagnosis or error event. Each declared check kind has a negative-control test |
| G39 | **Help outcomes are a replayable read; draws are honest.** `help_outcomes` is deterministic (computed twice, identical) and reads only existing rows. A passage draw happens only between options that all passed the judge; the logged propensity equals the draw probability, seeds reproduce draws, and the other options are one click away |
| G40 | **Examples and methods respect scopes.** `find_examples` never returns the item's exercise, solution or linked blocks or a span reproducing its answer. "Compare methods" appears only after a correct Submit, uses `post_attempt` only once the attempt window is closed, and records a reveal before showing the item's solution |
| G41 | **RW2d is a proper successor.** With `workbench.field_signals_enabled = false`, the field derivation, Phase 6 serving and plan builds are byte-identical to the predecessor on fixture copies; on, the receipts record what the old derivation would have produced. A stuck step or early help never lowers the record (F2) |
| G42 | **Cue value and offers.** Cues are ordered by the stored `p_open`, then the judge's rank, Guide first on ties; the order uses no hand-set weight. The density control changes only how many show. A try-first cue appears only on a worked example or derivation with an unchecked claim or open hypothesis, and pressing it opens RW1b's question as a learner pick. Contrast and correction-span lists appear in the manifest |
| G43 | **Kept comparisons are proposals.** "Keep" writes `source_objects` (claim or definition) and `source_object_relations` rows with `status` / `review_status = 'proposed'` and the right authorship; "my take" writes a `learner_connects` relation with `authorship = 'learner'`. No keep, no write. No concept edge, facet merge, prerequisite or LO change. The tutor's `compare` offer runs only when the learner presses it |
| G44 | **Roles add, never exclude.** Role proposals carry confidence, judge, ledger id, revision and citation. A span with an AI role but an ingest `exercise` or `solution` hint stays excluded from item-bound scopes, and an item's linked blocks stay excluded whatever their proposed role. `roles=…` filters match ingest or proposed roles. The batch labeller honours `--dry-run` and its spend cap |
| G45 | **Flagship figures.** The two-sided exponential golden case renders shaded areas whose readouts match Python's integration within 1e-6; PMF bars and `sum` readouts satisfy `sums_to_one`; animation calls the same evaluator as the slider; a region selection sends only its crop. A missed prediction stores its explanation text |
| G46 | **More panels and offers.** Heat map, vector field, trajectory and iterated-map panels agree across evaluators on the corpus (RK4 identical step for step). An `explorable` offer appears only when the judge said `yes`, and building runs RW5a's verification unchanged |
| G47 | **Reading paths.** `already shown` only when every LO the section teaches is demonstrated; `assumed` only with an assumption row; otherwise `core`. With RW7a on and RW7b off, plan builds are byte-identical (display only). With `reading_paths.plan_uses_path = false`, DL1's reading blocks are byte-identical and a rebuild shows zero projection deltas; on, receipts record DL1's choice |
| G48 | **The tutor looks things up within policy.** In the Reader context the tutor's retrieval uses `reading`, `assisted_practice` inside a workbench, nothing during a cold attempt. "Another way" never repeats a passage already shown in the inquiry. Offers render as buttons and call nothing until pressed; the tutor never serves, schedules or imports |
| G49 | **Follow-up restorations.** A candidate marked shown-by-reading is never created as a retention check; a `same_surface` candidate is never labelled transfer; formative records add questions but never change a prior's value; a generation request is queued at most once per `no_item` question and day, respects its spend cap, and its item is valued only after PF-b verification; "back to where you studied this" opens the provenance's inquiry or passage and never jumps on its own |
| G50 | **Formative records and Wrap up are pure.** `ReaderObservationV1` records are deterministic from the ledgers, carry `authority: "routing_only"`, and are read by nothing that writes evidence (import-linter contract). Wrap up never blocks closing a source and writes only what the same chips write elsewhere |
| G51 | **Intentions, new actions, every source kind.** Grouping by intention changes no action's RPC or payload. "Another way" excludes the open passage. "Reconstruct this later" creates exactly one escalated item and one `test_me_later` commitment, both undoable. Selection, intent box, inquiry and recap work on a transcript fixture; the notes pane offers only anchor-free actions |
| G52 | **The friction audit exists.** RW1a's review file holds the six-workflow audit before its UI changes, and each later phase's review file repeats it for the workflows it touched |
| G53 | **Sources-spec consumption degrades cleanly.** Each consuming phase (RW1c, RW2b's "a short problem instead", RW3's "Check me", RW4a/b, RW6b) passes its gates with the sources spec absent and with a fake of its interfaces present; the Reader never re-implements its candidate kinds, intents or ranking |

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
- *Added by the restoration:*
  - **RW1a:** a transcript-fixture case in each RW1a test file (G51).
  - **RW1b:** `test_reader_intentions.py` (grouping parity); `test_reader_reconstruct.py`; `test_reader_formative_texts.py` (adapter, matched answers write nothing, G36); `test_learner_text_source_widening.py` (the migration, durability lane).
  - **RW1c:** `test_reader_tutor_retrieval.py` (provider, policies, own query, modes, another way, that didn't help, G48); `test_reader_tutor_offers.py`.
  - **RW2b:** `test_workbench_discriminate.py` (G37); `test_workbench_step_graph.py` (G38); `test_workbench_check_kinds.py` (each declared kind with its negative control); `test_workbench_in_session_gaps.py`.
  - **RW2c:** `test_help_outcomes.py` (G39); `test_workbench_passage_draw.py`; `test_find_examples.py` and `test_compare_methods.py` (G40).
  - **RW2d:** `test_field_workbench_signals.py` (G41, successor parity and receipts).
  - **RW3b:** `test_reader_cue_value.py`, `test_reader_try_first.py` (G42).
  - **RW4a:** `test_find_sources_expand.py`; `test_find_sources_post_attempt.py`.
  - **RW4d:** `test_compare_sources_keep.py` (G43).
  - **RW4e:** `test_source_roles.py` (G44); `test_label_roles_cli.py` (dry-run, cap).
  - **RW5a:** golden cases for `integral`, `sum`, shading, PMF bars and the two-sided exponential (G45) in both `test_figure_grammar.py` and `figureGrammar.test.ts`; `test_figure_region.py`.
  - **RW5b:** golden cases for each new panel (G46); `test_figure_offers.py`.
  - **RW6a:** `test_reader_observation_records.py`, `test_reader_wrap_up.py` (G50).
  - **RW6b:** `test_reader_followup_restorations.py` (G49).
  - **RW7a/b:** `test_reading_paths.py`, `test_plan_follows_path.py` (G47).
  - **Every consuming phase:** a "sources spec absent" and a "sources spec faked" case (G53).

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
| Figures | Requests; verified / illustrative / failed / unsupported shares (by kind); predictions made and missed | RW5a |
| Calibration | Confidence before submission (optional) and reconnect "yes" against the next independent outcome on the same facets: counts of **confident misses** and **unconfident successes**, never a score | RW2a, RW1a, RW6b |
| Interventions → outcomes | For each shown hint, bridge, comparison, figure and cue: the next attempt on the same item or facets (immediate continuation) and the later cold outcome; how many have **no follow-up observation yet**. Associations, never causal credit | RW2b, RW6b |
| Loop closure | Follow-ups per session (the distribution, not a cap), by purpose; scheduled, undone, retired by re-valuation, served, answered and left as "later"; `no_item` rate; minutes spent on follow-ups as a share of plan minutes; **cold success after assisted reader work** (the dialogue's primary outcome), beside cold success on comparable items without reader help, and per hour of active reading and workbench time (the dialogue's "per unit of learner effort"); recap and narrative dismissal | RW6a/b |
| Valuation calibration | For each answered follow-up: predicted EIG against the realized change in the hypothesis posterior, and whether a pending decision flipped as its EVSI predicted; the `abstain` rate. Fed to the decision-value spec's readiness audit (`diagnosis/causal_selection_audit.py`) as the first live EVSI data. Reports, never thresholds (R6) | RW6b |
| *Added by the restoration:* | | |
| Intentions | Actions by intention (orient, understand, apply, consolidate, transfer) per reading hour; routing corrections by intention | RW1b |
| Formative signals | Tier-2 records per session by kind; gaps named per source kind; **precision of reader-named gaps**: the share later matched by a diagnosed misconception or a missed follow-up on the same facet, and the share contradicted by an unassisted success | RW1b, RW2b, RW5a, RW6a |
| Discrimination in the workbench | Discriminating questions offered and answered; how often the answer agreed with the diagnoser's cause at Submit; predicted EIG against how far the answer narrowed the rivals in the diagnoser's verdict; error-kind guesses against the diagnosis | RW2b |
| Tutor and sources | Answers by mode (excerpt, grounded, bridge); "another way" and "that didn't help" rates, and whether the next exchange resolved the inquiry; offers shown and pressed by kind | RW1c |
| What helps | `help_outcomes` by help kind and passage role; for passage draws, the next-step continuation and later cold outcome by option, IPS-weighted, with interval and sample size | RW2c |
| Comparisons and roles | Compares, keeps, my-takes; kept relations by type; role proposals by role and judge, and agreement between judges on the same span | RW4d, RW4e |
| Reading paths | Labels by kind, overrides ("read anyway" on enrichment, "skip" on core), and, after RW7b, misses on LOs whose core section was skipped | RW7a/b |
| Figures (extended) | Requests by panel kind; animation and region use; offered vs requested figures; "what changed?" answers | RW5a/b |
| Follow-up restorations | Candidates by kind (item, instrument, textbook exercise, generated); shown-by-reading and same-surface rates; generation requests, verified items produced and their use; "back to where you studied this" opens | RW6b |

The three experiments the dialogue proposes map as follows:
- **Generic vs work-aligned hints** is *not* run: it would deliberately give worse help. The reconciliation contract is the design; recovery, dependence and unusable-hint rates are tracked. The passage draws (RW2c) are the one randomized comparison of help kinds that withholds nothing.
- **Cues vs no cues** is the RW3b holdout.
- **Summaries alone vs typed evidence plus summaries for routing** belongs to router R3, whose replay can ablate the card's reader section.

**One math-heavy textbook first** (round 2 §9). The first evaluation of each phase runs on a `fixtures-local/` copy of the probability vault (derivations give the most concrete chances to check intermediate reasoning, and it holds the dialogue's own mixture and two-sided exponential examples), then on linear algebra. A randomized whole-workflow comparison against a plain PDF-plus-chat reader (round 1's "first experiment") is deferred and labelled (§17): at n=1 it means withholding the workbench from some sections on purpose.

**Usability walkthrough.** At the RW1a and RW2a checkpoints the owner may do one optional, timed task walkthrough (ask → branch → return; open → solve → leave → resume), recorded in the phase's review file. It is never required (R1). The friction audit (§4.1, G52) is the required, agent-run counterpart.

---

## 16. Decisions: recommended defaults (each default; owner may override)

| # | Decision | Recommended default |
|---|---|---|
| D1 | Phase order | RW1a → RW3a, RW6a, RW2a → RW1b, RW4a → RW2b → RW1c, RW4b → RW3b, RW4d → RW5a, RW4e, RW7a → RW2c, RW5b, RW2d → RW7b; RW6b whenever DL2 lands (§13) |
| D2 | The selection's first interaction | The intent box, with the palette one key away (Tab). An empty Enter asks |
| D3 | Who routes the intent box | The Decider (one typed choice, about 2 s); fallback Ask |
| D4 | Inquiry status | Reuse `question_events.resolution` (plus reopen), and the `test_me_later` / `help_me_remember` commitments. No new status words |
| D5 | Port or rebuild branching Ask | Port `origin/feat/reader-clarification-branches` |
| D6 | Workbench evidence mapping | A visible source, checks and levels 1–3 add to `hints_used` (assisted: schedules, never certifies); levels 4–5 make the attempt `primed`; hint text overlapping the key is a `tutor_answer` reveal with a workbench basis. No new rule, so no successor |
| D7 | Workbench model routes | The ChatGPT-plan provider (merged on `main` at `57d31c63`) once the owner has signed in; until then a fast OpenRouter chat profile. Codex only if the latency report is acceptable |
| D8 | First-offer help level | A judgment: the Decider over typed state plus the help style (default "balanced"), time-boxed; fallback "level 1, then up" |
| D9 | Where the workbench is the default | In the Reader, with the source visible ("Hide the source" for a cold-eligible attempt). On the practice screen and in the plan, a remembered "Work in steps" button, not the default, until the RW2b checkpoint |
| D10 | Cue restraint | A density budget the learner sets (fewer · normal · more = 1, 2, 4 per section; default normal), none in skim mode; ordered by the probability the target is still open; a 10% logged holdout on discovered cues only |
| D11 | Cue kinds | "Revisit a distinction" from RW3a; "a new application of something you've shown" and "try this step first" from RW3b |
| D12 | Library answers | Sources first, grouped by source and role, with prerequisite and application passages from the LO graph; the tutor on request; personalization on, with a toggle |
| D13 | Compare sources | **Restored (§20.8):** quote-verified claims and typed relations; "Keep" stores them as `source_objects` / `source_object_relations` proposals, with the learner's own take as `learner_connects`; callable by the tutor as an offer. No claim extraction beyond what the learner compares |
| D14 | Roles | **Restored:** ingest's `role_hint` decides exclusions; finer roles (several per passage, with confidence) accumulate as `source_objects` proposals from judges already running; an owner-run batch labeller |
| D15 | Figures | Declarative only; RW5a: function plots with shaded areas, PMF bars, linear maps, readouts with integrals and sums, animation, region selection; RW5b: heat maps, vector fields, trajectories, offered figures. Unverified reconstructions downgraded to labelled illustrations; one prediction per figure by default |
| D16 | Recap and digest | "Last time here" on returning, deterministic. **Restored:** an optional "Wrap up" on leaving, never blocking. The narrative on, shown in the card and in Wrap up |
| D17 | Cold follow-ups | **Owner, 2026-10-12 (§20.7):** automatic, with **no count cap**. The existing value-of-information machinery chooses, numbers and dates them: probe EIG over the learner's open hypotheses, and EVSI (`scheduling/evsi.py`) for the next decision, stopping when a check's robust value no longer pays for its minutes. Discriminating checks next day; retention checks at effective due; `max_wait_days` 14 as a time cap; 3-day fallback without FSRS state. Bounded by the plan's minutes and a $0.50 daily spend cap. Labelled with purpose and valuation, undo each or all; DL2 "Check once" commitments dated by `due_hint`; `find_practice` (with the sources spec's textbook exercises and intents once merged); **restored:** formative questions, exposure and novelty labels, background generation when nothing fits, a way back to where it was studied |
| D18 | Reading paths | **Restored:** RW7a in the Guide (display only) now; RW7b, the plan following the path, as a successor with a kill switch |
| D19 | Spend | Metered caps of $1.00 a day each for the workbench and library, $0.50 for cues; Codex `estimated_only` |
| D20 | Phone | No new RPC is phone-allowed in v1 |
| D21 | Hint feedback | "This doesn't connect to my work" on every hint, with three shortcuts, used immediately |
| D22 | Confidence | Optional before a workbench Submit, logged only; reported as calibration counts |
| D23 | W1's middle tier | **Owner, 2026-10-12:** formative signals steer hypotheses (through learner-text gaps), routing and follow-up valuation; never the mastery posterior, evidence, certification or FSRS. Changing serving takes a successor |
| D24 | Ask before repairing | With two or more rival explanations open, the first help offered is a discriminating question ranked by the existing EIG; skipped with one rival or help style "guide me" |
| D25 | What helps | A replayable read of help kinds and later outcomes, read by the hint writer and chooser as associations; logged draws only between options that all passed the judge |
| D26 | Workbench field signals | **Restored as RW2d:** a successor, live behind its kill switch, rather than waiting for a usage trigger |
| D27 | The source-practice backend | Built by `spec_source_practice_and_probes_v1.md` as a separate track; every consuming Reader phase works without it and gains it when it merges |
| D28 | Tutor actions | The tutor offers (practice, compare, figure, try first); the learner presses. The tutor never serves, schedules or imports |

---

## 17. Deferred, with triggers

After the restoration (§20.8), everything left here is either too ambitious to build usefully at n=1 today, blocked on something outside this spec, or would withhold help on purpose. Each item says what it would take. Items the first revision deferred and the restoration built are listed at the end, so nothing silently disappears.

| DEFERRED | What it would take | Revisit when |
|---|---|---|
| **Generated-code figures** in an isolated, unprivileged surface (round 2 §2's fallback "for unusual simulations"; the attention, agent-based and general-simulation cases RW5b's grammar can't express) | A Tauri isolation design with no IPC, file or network access (Tauri warns about iframe isolation on Linux), a working Rust toolchain on carson (B3), a code-review and sandboxing story for model-written JavaScript, and its own verification. The unsupported-kind counts from RW5a/b are its evidence | ≥ 10 unsupported requests the grammar can't express, *and* the isolation design is reviewed, *and* B3 is fixed |
| **Page-image (visual) retrieval** (ColQwen-style page embeddings; round 1 §7) | A page-image index beside T6's text index, a multimodal embedding route, and T6 benchmark B4's verdict that images beat Marker text on this corpus. Owned by the embedding-consumers spec | T6 open question 4's multimodal rematch shows page images beating Marker text |
| **OS-level learning service** (MCP, editor or browser capture; round 1 §10) | A capture endpoint outside the desktop app, consent and scoping for what an outside app may send, and an MCP server exposing read-only tools (`find_sources`, the sources spec's `find_practice`, capture). Belongs with the mobile/tailnet work, not the Reader | DL3's capture box is used most days *and* the owner reports capturing from another app as a gap; or the sources spec's tool interface is merged and the owner wants an outside agent to call it |
| **Local rerankers** (Qwen3-Reranker; round 1 §7) | A local model server on carson and a T6 benchmark showing parity with LLM verification | LLM verification latency is the measured bottleneck in the RW4, RW1c or RW2b latency blocks |
| **Learned cue and hint policies** (the dialogue's "learn which cues are worth showing from later independent performance") | The cue value's gain and cost terms fitted from holdout outcomes; a policy learner with logged propensities; router §13's learned-scorer conditions | ≥ 500 discovered-cue impressions with matured outcomes and propensities, *and* router §13's conditions |
| **Formative signals as numeric weak observations** (round 2 §6: "possibly low-weight evidence if independently validated") | An observation model for each tier-2 kind with its reliability, validated against later independent outcomes; a learner-field harness arm under its §7.4; an algorithm successor. Until then tier 2 steers hypotheses and routing only (W1) | The formative-signals report shows reader-named gaps or missed predictions precede later misses on the same LO, directionally, with an interval |
| **Alternative reference routes in the solution graph** (round 2 §4: "a partial solution graph… possible continuations"; RW2b builds the learner's own step graph) | Several verified reference solutions per item (the book's, generated alternates), route matching between the learner's graph and each, and a hint writer that continues along the matched route | "Different approach" replies exceed 20% of hint sessions over a month |
| **Formal verification of proof steps** (row 33's remainder: "follows from" for proofs) | A proof assistant (Lean) and autoformalization of informal steps; sympy cannot check proof moves | The check-coverage report shows proof steps are most of the unchecked steps *and* an autoformalization route is reliable on the owner's sources |
| **Cross-learner data-driven hints** (Continuous Hint Factory, round 2 §4) | Partial-solution states from many learners on shared items. At n=1 there is no such data; RW2c seeds hints from the learner's own history instead | LearnLoop has more than one learner with workbench sessions on shared items |
| **A learned, causal model of which help works for this learner** (round 3 §7: "learn whether a particular learner benefits more from worked examples, visualizations, counterexamples or hints") | Enough randomized variation (RW2c's draws) with matured cold outcomes to estimate per-kind effects with intervals; a policy that acts on them; router R3's off-policy machinery | RW2c's draws reach ≥ 200 with matured cold outcomes across at least three help kinds |
| **A randomized whole-workflow experiment** (round 1's "PDF-plus-chat vs LearnLoop with a delayed independent test") | An n=1 alternating-treatments design: sections randomized to a plain reader (every RW switch off) or the full Reader, both followed by RW6b's cold checks; the loop-closure block stratified by arm. It withholds the workbench from half the sections on purpose | The owner opts in |
| **Claim extraction over the whole library, with a claim matcher** (round 2 §5: "keep each author's claim"; RW4d keeps the claims the learner compares) | A batch claim extractor into `source_objects`, a cross-source claim matcher (a T1 match kind), and P3's review path for promoting relations | Kept comparisons exceed 10 a month *and* the owner asks to browse claims across sources |
| **The router's availability pass** (round 3 §3: "a cheap candidate-discovery pass tells the router what activities are actually available") | Owned by `spec_source_practice_and_probes_v1.md`'s router-tool track; this spec adds nothing. If that spec does not phase it, it must carry it as its own deferred item | Router R2 values block candidates live |
| **A CAS calculator in the workbench** (the "calculators" in round 1's context-switching pain point) | Its own assistance mapping (a computed step is help) | The owner asks |
| **Photo of handwritten work as steps** | DL4's `image_transcription` route | DL4's route is merged |
| **Randomized hint-quality experiments** | — | Not planned: they would withhold better help on purpose. RW2c's draws compare options that all passed the judge instead |

**Restored from the first revision's deferrals (no longer deferred):** goal-aware reading paths (RW7a/b, §10); the router querying sources as a tool (now built by the sources spec); an LLM role labeller (RW4e, §7.9); source claims and stored cross-source relations, for the comparisons the learner keeps (RW4d, §7.8); generated follow-ups (RW6b item 8); follow-ups from textbook exercises (RW6b through the sources spec); field signals from mid-work stuck steps and early help (RW2d, §5.11); the general figure language (RW5a/b, §8); broader symbolic checks (§5.3); full solution graphs, as the learner's own step graph (§5.2); figure predictions and reconnect answers as signals (tier 2, W1); workbench and figures on video transcripts (§4.1).

---

## 18. Cross-spec notes (record when each phase merges)

- **Source practice and probes (`spec_source_practice_and_probes_v1.md`, branch `sources/canonical-practice`).** The owner's decision of 2026-10-12: "build the router and sources path as its own backend track now". That spec owns, and this spec only consumes:
  - **textbook exercises as practice candidates** (the audit's RW4c): `find_practice` returns them as their own kind; choosing one imports it, verifies it with PF-b, maps its competencies and attaches it to a family as a surface. Consumed by RW4a ("Practice this question"), RW4b (the view), RW3 ("Check me"), RW1c (`practice_this`), RW7a (one exercise per core section) and RW6b (follow-up candidates);
  - **the discriminating search**: `intent` and `target_hypotheses` in `PracticeConstraints`, ranked by EIG. Consumed by RW2b ("a short problem instead"), RW3's "Check me" on a target with rivals, and RW6b (`diagnostic_probe` and `retention_check`);
  - **`find_sources` intents** (`remediate`, `alternative`; `remediate` reads `correction_source_span_ids`). Consumed by RW1b ("another way to see this") and RW1c ("explain it another way", "that didn't help");
  - **real callers for `find_practice`** (RW4a's "Practice this question", RW1c's offer and DL3's "Practice on…" are one RPC) and **the router §15.3 tool**, with whatever availability pass it phases (§17).
  - **Shared pieces, built once.** `find_sources`: this spec defines the base signature, policies, `facet_ids` and `expand` (§7.2); the sources spec adds `intent`. `PracticeConstraints`: this spec adds `unattempted_only` and `exclude_family_ids` (§9.3); the sources spec adds `intent`, `target_hypotheses` and `max_estimated_minutes`; one change, made by whichever lands first. The candidate-valuation adapter over the probe-EIG functions is shared with RW6b (§9.3, G35). RW4e's role proposals are available to that spec's intents as a positive filter.
  - **Requests to that spec:** an `integrative` option (a problem requiring all of several target facets: round 3's "a problem requiring several concepts the learner is trying to integrate"), used by RW6b's transfer checks; an exposure label on candidates whose worked twin the learner has read (RW4b shows it; RW6b computes its own from the session, §9.3); a request API for "when nothing fits" generation, which RW6b would call (§9.3 item 8).
- **Owner decision, 2026-10-12: lift the other four count caps on value of information.** §20.7 removed the Reader's follow-up count caps. The owner has decided that the same basis applies to the four count caps that live elsewhere:
  - `probe.episode.session_qualifying_observation_cap` (4; with `maximum_observations`, 4) for probe episodes (`config/schema.py:224`, `:209`);
  - `scheduler.followup.max_interventions_per_lo_per_session` (1) for post-attempt follow-ups (`schema.py:40`, enforced at `diagnosis/followups.py:339`);
  - `teach_back.session_cap` (1) (`schema.py:625`, enforced at `scheduling/scheduler.py:568`);
  - `plan.project_probes_max_per_day` (4) in the daily plan (`schema.py:1885`, read at `daily_plan/engine.py:462`).

  **It is a separate serving stage, not part of this spec.** Each cap changes what is served, so the stage is an algorithm successor of its own (the next free `mvp-0.N` at its merge), with a kill switch per cap that restores the old count byte-identically, receipts that record what the count would have allowed, and plan parity under the switches. Each count becomes the stop rule RW6b uses: add another observation, follow-up, teach-back or project probe while the best remaining candidate's robust value (EIG converted to minutes, or EVSI where a loss table exists) exceeds λ·minutes + burden, valued conditionally on those already chosen; time (session and plan minutes) and money (spend caps) bound the rest. It reuses the shared candidate-valuation adapter and `evsi.rank_feasible`; it adds no decision parameter. Its calibration inherits RW6b's (§20.4 risk 9). The stage's owner is the orchestrator's next serving track; this spec only records the decision. Noticed while auditing and not part of the decision: `teach_back.max_followups` (4) and `plan.reentry_max_items` (8) are also counts.
- **P3 Reader spec.** §5.4's inquiry thread is implemented through `question_events.resolution` and branch parents, with no projection table. §1.3's "syntopic comparison UI" exclusion is lifted by RW4a under §7.1–7.2's source-local rules. **RW4d and RW4e now write proposals into P3 §7's source-object layer** (kept comparisons; instructional roles), with authorship and review status as P3 §7.1–7.2 require; nothing becomes canonical without P3's review path. Invariants 1, 6, 7, 8, 9 and 10 are restated in W12, W1, G43, RW4d's "my take", W2 and W7. "Posterior" in invariant 6 is read as the mastery posterior (W1).
- **Quick-check producer.** Gains `scope_kind` (section, inquiry, selection) and `question_style` (recall, next step, why step, assumptions, reconstruct). Section behaviour is unchanged; the section lookup filters on scope.
- **Daily loop.**
  - **DL2 (request):** the dated "Check once" branch reads `commitment_versions.due_hint` when present and falls back to `capture.test_me_later_days`; RW6b's follow-ups depend on it (§9.3). DL2's provider fills DL1's existing `check_once` scheduled-check kind (`daily_plan/lanes.py:74`). Reader follow-ups can make several checks due on one day; the plan's minutes, not a count, bound how many are served (§9.3 item 6). **DL2 (request, restored):** its restoration after a measurement shows the follow-up's "back to where you studied this" link from the commitment's provenance (§9.3 item 9). DL2's depth intents map onto RW7a's depth choice as one setting.
  - DL1's learner-pick block serves RW3's "Check me" and "Try this step first", RW4a's "Practice this question", RW4b's chosen exercise and RW1c's offers.
  - DL3's "Practice on…" box and RW4a's "Practice this question" are the same `find_practice` call; build one RPC and reuse it.
  - DL4's pre-questions and RW1's scoped questions share the quick-check producer.
  - DL1's re-entry can show RW6a's card. **RW7b** changes DL1's reading block (a successor, §10.2).
- **Router.**
  - `LearnerStateCardV1` gains the "Reader activity" section from `reader_activity_for_card` (RW6b), now with open hypotheses, formative records, kept comparisons and candidate actions.
  - **§15.3's `search_sources(query)` is RW4a's `find_sources`**, with its policies; the existing `reader.source_search.search_sources` is the legacy keyword search and keeps its name. §15.3 itself (the tool, its guardrails, "when nothing fits" and the availability pass) is now built by the sources spec, not deferred behind R2.
  - The Reader's in-session help (hint level choice, discriminating questions, cues) is not a router decision (router §1).
  - **R2:** each pending reader follow-up becomes a block candidate valued with robust EVSI like any other (router §3), so the router, not the order of lanes, decides whether it is served on a crowded day. RW6b's valuation receipt uses R1's field names (`probe_eig`, `evsi_assignment`) so R3's replay reads both. RW2c's passage draws log propensities in the same style, for R3.
- **Embedding consumers.**
  - T6 gains consumers (workbench bridging and examples, discovered cues, the library organizer, compare, the Reader-context tutor, the exercise view) and one thin function (`find_sources`, with `expand` over the LO graph). R1–R6 hold: the graph is read, never written by similarity.
  - `judge_listwise` gains tasks `passage_cue`, `library_contribution`, `followup_relevance`, `example_fit` and `source_role`.
  - `PracticeConstraints` gains `unattempted_only` and `exclude_family_ids` (and the sources spec's fields).
  - T1's matcher gains no kind. B4's text-only decision stands; page-image retrieval stays deferred (§17).
- **Blind grading and diagnosis.** The grader is unchanged (G6). The diagnoser's context gains the current attempt's workbench trace when one exists (`+workbench-v1`), including the step graph, the labelled error-kind guesses and any discriminating question with its answer; contexts without a trace hash as before. The Guide reads the diagnoser's overlay (RW3a).
- **Learner field.** Workbench assistance flows into `hints_used` and `primed`, so the `+hints` arm sees it. Formative reader signals reach the field only as question signals and named gaps, under F2 (W1). **RW2d adds two signal sources as an algorithm successor under F3** (§5.11). Numeric weak observations from tier 2 stay deferred (§17).
- **Decision value and probe EIG.** RW6b is the first live consumer of `scheduling/evsi.py`'s `robust_evsi` and `rank_feasible`; RW2b's discriminating question is a new consumer of `instrument_expected_information_gain`. Both go through adapters that write no learner state. Neither adds a decision parameter; λ, the burden and the nat-to-minutes scale stay the registry's. RW6b's receipts and RW2b's discriminating answers (predicted EIG against what the diagnoser concluded) are inputs to the decision-value spec's readiness audit (§9 there) and to any EVSI calibration track.
- **Learner-text gaps.** Two new source kinds, `workbench_text` (RW2b) and `reader_formative` (RW1b, RW5a), with one migration widening the `source_kind` CHECK on `learner_text_gaps` and `learner_text_gap_jobs` (§3.4 item 13). Reader questions, including "what's still unclear?", "that didn't help" and tutor questions from library asks, are already sources. Texts are queued when written, so gaps can be named mid-session (§5.2). Named gaps become RW3b cue targets and RW6b questions.
- **Knowledge model.** Cue links, organizer lines, role proposals and kept relations are labels and proposals. They never touch facet identity or the semantic graph.
- **Mobile.** No new phone RPC. Every new RPC is pinned desktop-only.
- **Handoffs.** Add a "Reader workbench" row to `implementation_handoffs.md` §1 per phase, using §19.

---

## 19. Agent prompt template

Fill in `<phase>` (RW1a … RW7b), the phase row from §13 and the base branch. Give it to a fresh agent in the repo. The review and fix steps follow `implementation_goal.md` §2.

```text
Implement LearnLoop reader-workbench phase <phase>, as specified in
docs/specs/spec_reader_workbench_v1.md (§13 row "<phase>", plus the sections that row
cites, §3.4 and §20).

Before coding, read: CLAUDE.md; docs/specs/implementation_handoffs.md §0 (standard rules
and invariants); spec_reader_workbench_v1.md in full; spec_p3_reader_integration.md §1.1;
docs/specs/daily_loop_frictionless_defaults.md; the sections of other specs the row names;
the phase's screens in docs/specs/ux_reader_workbench_v1.md (presentation; this spec wins
on behaviour); spec_source_practice_and_probes_v1.md if the row consumes it;
db/table_roles.py; docs/algorithm-change-playbook.md. Then write a short plan (files,
migrations, successor and kill switches, spend caps and model routes, judgment_ledger
writes, tests) to docs/reviews/reader-workbench-<phase>.md and proceed.

Work in your own worktree on a new branch reader/<phase>, created from <base branch>.
Follow §0 of the handoffs and §2 of the spec, especially:
- reuse before building (W13): T6 for retrieval, practice_index/listwise.judge_listwise
  for every listwise judgment, find_practice for practice, the quick-check producer for
  questions, learner-text gaps for learner text, DL2's "Check once" for follow-ups,
  the existing probe-EIG and scheduling/evsi.py functions for valuing them (§9.3),
  source_objects for roles and kept comparisons, and spec_source_practice_and_probes_v1.md
  for textbook exercises, the discriminating search and find_sources intents: consume
  its interfaces, never re-implement them, and keep working when it has not merged (G53);
- no new interaction_events kind and no new reveal kind (payload `event` fields and
  the tutor_answer kind with a workbench basis instead); the only table rebuild is the
  learner-text source_kind widening (§3.4 item 13);
- W1's tiers: reading, cues, figures, recaps and inquiry status are salience only;
  formative signals (learner text, check verdicts, hints, predictions) may name gaps
  and steer routing and follow-up valuation, never the mastery posterior, evidence,
  certification or FSRS; the only evidence is a submitted attempt, with assistance
  recorded as §5.4 says;
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

## 20. Integration review and owner decisions (2026-10-12)

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

This table records the integration review. The owner's restoration (§20.8) supersedes six of its rows: symbolic checks (now every declared kind sympy can check, §5.3), no field signal (now RW2d, a successor), no LLM role index (now RW4e's proposals), `find_sources`' three policies (now four, with a narrow `post_attempt`; `authoring` stays PF's), display-only compare (now "Keep" as proposals, RW4d), and deferred generation (now a background request, §9.3 item 8). The reasons recorded here still explain why each restoration is built the way it is.

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

*Added by the restoration (§20.8), checked against `main` at `57d31c63` and the branches named:*
- **RW1b (widened).** Two more question styles (in RW1a's migration), the intentions grouping (frontend and the Decider's option set), the `reader_formative` adapter, and possibly the learner-text widening migration. The adapter waits for `learner/text-gaps` (merge chain).
- **RW1c.** Medium. The Reader context gains a span provider (practice, feedback and library already have one, `source_retrieval/tutor.py:70`); the modes and offers are a prompt and response-schema change plus buttons. Its "another way" and "that didn't help" fall back cleanly until the sources spec's intents merge.
- **RW2b (widened).** Still the largest phase. The discriminating question adds a hint-writer output (candidate questions with predicted answers), a small compiler from those predictions to a `CompiledInstrument`, and a call to the existing EIG function; the step graph and error-kind guess are output fields of the existing check call. No new route.
- **RW2c.** Medium, mostly reads: `help_outcomes` is a query over existing rows; `find_examples` is a composition of `find_sources` and one listwise task; compare methods reuses the feedback screen.
- **RW2d.** Small to medium, but a successor: two sources in `field/signals.py`, receipts and parity tests.
- **RW3b (widened).** The value order reads existing posterior and status rows; the try-first kind and the contrast lists are judge and retrieval inputs. Medium to large in total.
- **RW4b (narrowed to a view).** Small: the backend moved to the sources spec.
- **RW4d.** Medium: the source-object writes exist (`reader/source_objects.py`); the comparison prompt gains typed relations; the UI adds keep, my take and the "compared" mark.
- **RW4e.** Medium: a field in four judges' schemas, the source-object writes, a positive filter in `find_sources`, and a batch CLI with `--dry-run`.
- **RW5a (widened).** Large: `integral` and `sum` in both evaluators with corpus parity, shading and PMF panels, animation, region crops (the crop function exists).
- **RW5b.** Medium: three panels and an RK4 integrator in both evaluators, and one judgment field for offers.
- **RW7a.** Medium: a judge route, one table, the Guide view. **RW7b.** Small to medium, but a successor on DL1's reading block (merged).

### 20.2a What the restoration does not make buildable

Nothing in §17 became buildable by being written down. The generated-code figures, page-image retrieval, the OS-level service, local rerankers, learned policies, numeric weak observations, alternative reference routes, formal proof checks, cross-learner hints, a causal help model and the whole-library claim index each wait on something §17 names: a design outside this spec, data that n=1 does not yet have, or the owner's opt-in.

### 20.3 The Codex ROI list

| Item | Verdict | Where |
|---|---|---|
| A1 Margin cues from the existing Guide first | **Folded** (RW3a), with the split-overlay fix it needs | §6.2 |
| A2 Resumable scratchpad first | **Folded** (RW2a), reusing `LiveMarkdownEditor` and the draft-queue pattern; "leave" vs "abandon" | §5.1 |
| A3 "This doesn't connect to my work" on hints | **Folded**, used immediately; also drives the strategy-change rule and the solution-graph trigger | §5.2, §17 |
| A4 Workflow funnels with denominators, latency, failures; optional walkthrough | **Folded**, on existing event kinds | §4.1, §15 |
| A5 Recap on return, before the scheduling dependencies | **Folded** (RW6a) | §9.1 |
| A6 "Predict the next step" / "why this step works" | **Folded** into RW1b through the quick-check producer, not a new engine | §4.2 |
| A7 Narrow the first figure | **Partly folded.** Kept the declarative grammar (it generalizes across the owner's three subjects; templates would be per-topic code), but cut the renderer's integrals, PMF bars and shading, kept two panel types, and record unsupported kinds. *Restored by §20.8:* RW5a now has integrals, sums, shading, PMF bars and animation; RW5b adds three panels | §8 |
| A8 Connect each explanation to what happened afterwards | **Folded as a report** over existing rows (assists, manifests, attempts), associations only; no new table. *§20.8 adds* RW2c's replayable read and logged draws, still with no new table | §15, §5.10 |
| A9 Smaller syntopic experience first | **Folded**: grouped sources, contribution lines, pin and compare; no role labelling, claims or relations. *§20.8 adds them later in the order:* RW4d (kept comparisons) and RW4e (roles) come after RW4a has shipped | §7.3 |
| A10 Exercises from sources when nothing fits | **Folded** (RW4b) | §7.4 |
| A11 Confidence vs independent success | **Folded** as optional, logged-only confidence (the existing `answer_confidence`) and a calibration block | §5.4, §15 |
| A12 Narrow symbolic checks | **Folded**, three transformations, with coverage reporting. *Widened by §20.8* to every declared kind sympy can check with a negative control | §5.3 |

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
8. **Text-gaps coupling.** RW1b's and RW2b's adapters and RW3b's gap targets assume the text-gaps interfaces as built on its branch (`LearnerText`, `named_gaps_for_card`, the `source_kind` CHECK); a review change there would ripple here.

*Added by the restoration:*

10. **Tier-2 noise.** More learner text reaches learner-text gaps (missed answers, predictions, "doesn't connect" replies), and that pipeline creates prerequisite edges and misconception candidates live. A noisy source could name gaps that aren't there. Mitigations: the pipeline's own judges decide every match ("embeddings shortlist, judges decide"); every creation it makes stays undoable as it is today; the formative-signals block measures the precision of reader-named gaps (§15); `reader_formative.enabled` turns the new sources off without touching the rest.
11. **Discriminating questions are only as good as the predicted answers.** EIG is computed from what the hint writer says each rival would answer; a wrong prediction makes a useless question look informative. Mitigations: zero-EIG questions are dropped by construction; the diagnoser, not the question, classifies at Submit; the report compares predicted EIG with how far the answer actually narrowed the diagnoser's verdict (§15), which is also calibration data for EIG itself.
12. **Coupling to a spec being written.** Five phases consume `spec_source_practice_and_probes_v1.md`, which did not exist when this revision was written. Every consumption is specified as "works without it, gains it when it merges" (G53), and the shared pieces (`find_sources`, `PracticeConstraints`, the valuation adapter) are built once by whichever lands first. A different interface there means editing the consuming rows here, not redesigning them.
13. **Scope.** The restoration roughly doubles the agent effort (§20.5). Mitigations: every restored phase is independent of at least one other and has its own kill switch; the order puts the owner's pain points (RW2b's discriminating question, RW1c's tutor, RW6b's follow-ups) before the breadth (RW5b, RW4e, RW7); and the Reader still yields to the goal's tracks (§13).
14. **Two successors.** RW2d and RW7b change what is served. Each needs plan parity under its switch and a reviewer's sign-off under the playbook; neither blocks any other phase.
15. **A learner-text table rebuild.** Widening `source_kind` rebuilds `learner_text_gaps`, which three tables reference. It is small and young, but a botched rebuild would lose named gaps. Mitigation: temp-then-rename with `foreign_key_check` before commit, a durability-lane test, and a fixture with rows in every referencing table (G36).

### 20.5 Build order, dependencies and effort

Re-run for the restored scope (§20.8). "Was" gives the first revision's effort where a phase existed.

| Order | Phase | Depends on (merged or in flight) | Effort (was) |
|---|---|---|---|
| 1 | RW1a | `main` only (DL1 and the ChatGPT-plan provider are merged). The port's `tutor_qa.py` hunk is small against `learner/text-gaps` | M (M) |
| 2 | RW3a, RW6a, RW2a (two at a time) | RW1a's rail split | S (S), M (S–M), M (M) |
| 3 | RW1b, RW4a | RW1a; `learner/text-gaps` merged for RW1b's adapter; DL1 for learner picks | M (S–M), M (M) |
| 4 | RW2b | RW2a; the ChatGPT-plan sign-in; `learner/text-gaps` merged | L (L) |
| 5 | RW1c, RW4b, then RW3b, RW4d | RW4a; the sources spec for intents and candidates (each works without); RW3a + text-gaps for RW3b | M (new), S (S–M), M–L (M), M (new) |
| 6 | RW5a, RW4e, RW7a | RW1a; RW4a; RW1a | L (M–L), M (new), M (new) |
| 7 | RW2c, RW5b, RW2d, then RW7b | RW2b + RW4a; RW5a; RW2b (successor); RW7a + DL1 (successor) | M, M, S–M, S–M (all new) |
| any, after DL2 | RW6b | DL2 merged with `due_hint`; RW2a; `main`'s EIG/EVSI modules; the sources spec optional. R1 recommended (receipt field names); R2 later for router-valued serving | L (M–L) |
| parallel | The sources spec's track | Its own spec; no Reader frontend | Owned there |
| separate | The four-count-caps stage | Its own successor (§18) | Owned by its stage |

**Totals.** Counting S as about one day, S–M two, M three, M–L five and L eight to ten, the first revision's eleven phases came to about 37 agent-days (five to seven weeks, serialized on the Reader frontend). The restored scope has nineteen phases and comes to about 68 agent-days: **roughly nine to twelve weeks** through the implement–review–fix loop with at most two Reader phases open. The increase comes from eight new phases (RW1c, RW2c, RW2d, RW4d, RW4e, RW5b, RW7a, RW7b; about 22 days) and wider RW1b, RW3b, RW5a, RW6a and RW6b (about 10 days), offset by about a day where RW4b's backend moved to the sources spec. The sources spec's track runs in parallel and is not counted here. A learner-visible milestone lands every one to two weeks: inquiry and cues (order 1–2), the scratchpad (2), the discriminating workbench (4), the tutor that looks things up (5), the flagship figure and reading paths (6), follow-ups whenever DL2 lands.

### 20.6 Start now, or wait?

**Start RW1a now; hold everything else until its dependencies land.** RW1a mostly ports finished, tested work and splits the rail. No in-flight branch touches `ReaderScreen.tsx` or `learnloop/reader/`, and its only overlap (`tutor_qa.py` with learner-text gaps) is a few lines. It needs no model route and no successor. It is also the prerequisite for every other phase, so it removes the main merge hazard early. Two conditions: the integration queue (now R1, learner-text gaps and facet identity; DL1 and the ChatGPT-plan provider have merged) keeps priority for merges and reviews, and RW1a merges after whichever of those is ready first. RW3a, RW6a and RW2a can follow straight after RW1a. **RW2b should wait** for the ChatGPT-plan sign-in (latency) and learner-text gaps (its adapter). **RW6b must wait** for DL2. The restoration does not change this answer: RW1a's only additions are the friction audit, which should be written before its UI changes, and a transcript fixture. The sources spec's backend track can start at the same time; it touches no Reader frontend file.

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

**Not changed here:** the same principle applies to count caps that live in other specs and code: `probe.episode.session_qualifying_observation_cap` (4) and `maximum_observations` (4) for probe episodes (`config/schema.py:224`, `:209`); `scheduler.followup.max_interventions_per_lo_per_session` (1) for post-attempt follow-ups (`schema.py:40`, enforced at `diagnosis/followups.py:339`); `teach_back.session_cap` (1); and `plan.project_probes_max_per_day` (4) in the daily plan. **The owner has since decided (2026-10-12) to lift them on the same value-of-information basis, as a separate serving stage with its own successor;** §18 records the decision and §20.8 its place in the restoration. RW6b neither applies nor changes them.


### 20.8 Owner decisions (2026-10-12): restoration

**The owner** (after reading the coverage audit, `docs/reviews/reader-dialogue-coverage.md`): "Restore all of it into the spec." "Build the router and sources path as its own backend track now." "Lift the other 4 caps on the same value of information basis." And: "make sure most of the intentions and ideas are included in the spec, with the most ambitious/impossible to implement at this stage usefully explicitly labeled as deferred in the spec instead of entirely absent."

**What the decisions mean for this spec.**
1. **Every cut the audit found is restored** into the phase where it belongs, or listed in §17 as a labelled DEFERRED item with what it would take and a trigger. The audit's 74 non-BUILT rows (50 narrowed, 9 deferred, 5 dropped, 10 elsewhere) are accounted for in the counts below and in the "Restored" column added to the audit.
2. **The backend for canonical sources as practice and probes is a separate spec**, `spec_source_practice_and_probes_v1.md` (branch `sources/canonical-practice`). This spec consumes it in five phases and designs none of it (§18). That takes the audit's RS1 and its RW4c out of this spec.
3. **The four other count caps** are lifted in a separate serving stage with its own successor (§18). Not built here.
4. **W1 is rewritten** to separate three tiers of signals (§2): what was "not evidence, so not an observation at all" is now "never evidence, may steer hypotheses and routing", consistent with P3 invariant 6 and learner field F2/F3.

**What was restored, by the audit's recommendations:**

| Restoration | What | Where |
|---|---|---|
| RS1 (canonical sources as practice, probes and explanations) and RW4c | Built by the sources spec; the Reader consumes it: "Practice this question", the exercise view, "Check me", RW1c's offers, the workbench's "a short problem instead", RW6b's candidates and intents | §18; §7.3, §7.4, §6.1, §4.6, §5.2, §9.3 |
| RS1 step 3 (explanations from the sources for the tutor) | The Reader-side tutor: its own query, three modes, another way, that didn't help, offers | RW1c, §4.6 |
| RS2 (a discriminating question mid-problem) | Contract rule 6; EIG-ranked; answer to the diagnoser and learner-text gaps; error-kind guess | RW2b, §5.2 |
| RS3 (formative reader signals) | W1's middle tier; `reader_formative` and `workbench_text` source kinds; formative records; questions for follow-ups; in-session updates | W1; §4.2, §5.2, §5.6, §8.4, §9.1, §9.3 |
| RS4 (instructional roles) | Role proposals in `source_objects` from judges already running; batch labeller; positive filters; contrasts | RW4e, §7.9; §6.2 |
| RS5 (figures: the flagship) | Shading with integral readouts, PMF bars and sums, animation, region selection, "what changed?"; then heat maps, vector fields, trajectories, offered figures | RW5a §8.1–8.6; RW5b §8.7 |
| RS6 (syntopic reading as a tool) | `compare_sources` with perspectives, tutor-callable; "Keep" as source-object proposals; my take | RW4d, §7.8 |
| RS7 (retrieval in the evidence loop) | `help_outcomes`, read by the hint writer and chooser; logged draws between equally good passages | RW2c, §5.10 |
| RS8 (exposure-aware unfamiliarity) | Shown-by-reading label and discount; novelty labels | RW6b, §9.3 |
| RS9 (back to the inquiry after a cold miss) | "Back to where you studied this" | RW6b, §9.3 item 9 |
| RS10 (narrative on leaving) | "Wrap up", never blocking | RW6a, §9.1 |
| Rows the audit did not give an RS number | Five intentions; assumptions, another way, reconstruct later; friction audit; one interaction model on every source kind; step graph; wider symbolic checks; value-ordered cues and try-first cues; concept-graph expansion; `facet_ids`; narrow `post_attempt`; find_examples; compare methods; reading paths (RW7a/b); workbench field signals (RW2d); background generation; open hypotheses and candidate actions on the card; own-history hints; one textbook first | §4.1, §4.2, §5.2, §5.3, §5.10, §5.11, §6.1–6.2, §7.2–7.3, §9.2–9.3, §10, §15 |

**What stays deferred, labelled** (§17, each with what it would take and a trigger): generated-code figures; page-image retrieval; the OS-level learning service; local rerankers; learned cue and hint policies; formative signals as numeric observations; alternative reference routes in the solution graph; formal verification of proof steps; cross-learner data-driven hints; a learned causal model of what helps; a randomized whole-workflow experiment (owner opt-in); claim extraction over the whole library; the router's availability pass (owned by the sources spec); a CAS calculator; photo-of-work input. Randomized hint-quality experiments stay "not planned".

**The audit's classes after the restoration** (115 rows; the audit's "Restored" column gives each row's section):

| Class | Before | After |
|---|---|---|
| BUILT | 41 | 94 |
| NARROWED | 50 | 0 |
| DEFERRED | 9 | 3 |
| ELSEWHERE | 10 | 18 |
| DROPPED | 5 | 0 |

- **NARROWED (50):** 42 now BUILT in a phase here; 7 ELSEWHERE, built by the sources spec and consumed here (rows 91, 93, 96, 101, 109, 110, 115); 1 DEFERRED with its reason (row 41, the whole-workflow experiment, which withholds help on purpose and waits for the owner's opt-in).
- **DEFERRED (9):** 6 now BUILT (rows 3, 17, 20, 45, 66, 90); 1 ELSEWHERE in the sources spec (row 86, the router querying the sources); 2 still DEFERRED with what they would take (rows 30, page-image retrieval; 42, the OS-level service).
- **DROPPED (5):** all 5 BUILT (rows 2, 39, 61, 102, 106).
- **ELSEWHERE (10):** unchanged in class. Row 95 (the router's availability pass, mentioned but never planned) is now requested of the sources spec (§18) and listed in §17 so it cannot vanish; row 94 now points at that spec too.
- **The 22 narrowings that stated no reason:** 17 restored here, 4 restored by the sources spec (91, 93, 96, 101), and 1 now carries its reason (41).
- **Parts deferred beside a built main idea:** 13 rows keep a secondary part in §17 — rows 21 and 66 (claims over the whole library), 33 (proof steps), 44, 48 and 49 (generated-code figures for what the grammar can't express), 45 and 70 (numeric weak observations), 51 (a learned cue policy), 60 (alternative reference routes), 61 (cross-learner hints), 65 (page images), 108 (a causal model of what helps).

**Sizing.** Nineteen phases instead of eleven; about 68 agent-days instead of about 37; roughly nine to twelve weeks instead of five to seven (§13, §20.5). Two phases are successors (RW2d, RW7b). The sources spec's track and the count-caps stage are not counted.

**Two questions the owner asked alongside, answered where they belong.**
- *"Is there any way we could better calibrate the EVSI instead of having it run on uncalibrated assumptions?"* This spec contributes data, not a method: RW6b's valuation receipts (predicted EIG and EVSI against the realized posterior change and whether the decision flipped), RW2b's discriminating answers (predicted EIG against how far the diagnoser's verdict narrowed), and RW2c's logged draws. The calibration method — fitting λ, the burden and the nat-to-minutes scale, which `robust_composition.py:44`–`:55` labels heuristic — belongs to the decision-value spec (§9 there) and any EVSI-calibration track; §15's valuation-calibration and discrimination blocks are where its inputs appear.
- *A human-centred UI/UX design pass over the brainstorm.* That is separate work, `docs/specs/ux_reader_workbench_v1.md` (experience design, being written in parallel for this restored scope). It governs how these phases look and feel; this spec governs behaviour, contracts and data, and its wording rules (W2, G16) and restraint rules (W11, W12) are constraints that design keeps. Where the two disagree, the phase agent records it in its review file and asks the owner.

---

*Related: `docs/brainstorming/Improving Reader's design.md` (source) · `docs/reviews/reader-dialogue-coverage.md` (what the dialogue proposed and where it went, with the restored state) · `spec_source_practice_and_probes_v1.md` (the source-practice backend this spec consumes) · `decision_value_and_commissioning_spec_v1.md` (§6.4) · `spec_probe_eig_redesign.md` (§7) · `spec_p3_reader_integration.md` · `spec_reader_quick_check_producer.md` · `spec_daily_loop_v1.md` (§5, §6.1, §6.9, §6.10) · `spec_embedding_consumers_v1.md` (§1, §5.9, §9) · `spec_action_router_v1.md` (§3, §4, §15) · `spec_blind_grading_diagnosis_split_v1.md` · `spec_learner_field_v1.md` (§3.1) · `implementation_handoffs.md` §4 · `docs/reviews/slice-2-t6.md` · `docs/reviews/stuck-prompt.md`*
