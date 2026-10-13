# Reader workbench: inquiry, worked problems, passage cues, syntopic reading and loop closure (v1)

**Status:** draft for owner review (2026-10-12).

**Source:** `docs/brainstorming/Improving Reader's design.md` (the owner's design dialogue, committed with this spec). Its three rounds:
1. the agent's brainstorm: intentions, textbook pain points, learning loops, features A–G, the workbench layout, retrieval;
2. the owner's reply: interactive figures from selections, syntopic reading, misconception-aware reading, scaffolding that scales with prior knowledge and struggle, "hints I couldn't reconcile with my own work", natural-language questions to the library with an optional tutor, and session summaries feeding the router, then a short unfamiliar cold problem;
3. the owner's proposal that canonical sources become a natural-language retrieval tool for the router and the tutor.

**Owner preferences in force** (from `daily_loop_frictionless_defaults.md`, `implementation_goal.md` and the owner decisions recorded across the specs):
- **Honest labels, generous defaults.** Live changes go behind kill switches. There are no shadow stages by default.
- **LLM judgment over hand-picked constants.** Where a choice is a judgment (which help to offer first, which passage deserves a cue, which section is core for a goal), an LLM or the Decider makes it from typed learner state. Constants appear only as caps.
- **Learner text over skip buttons.** The precedent is "I'm stuck" (`docs/reviews/stuck-prompt.md`): a free-text box replaces a bare skip wherever the text can be used.
- **Embeddings shortlist, judges decide** (`spec_embedding_consumers_v1.md` §1, R1–R6). No cosine cutoff is hand-set and no calibrator is built.
- **Codex on the owner's ChatGPT subscription** may run every paid LLM role, recorded as `estimated_only`. The Decider is `perplexity/pplx-decider-v1.1-27b` on OpenRouter (router R0, merged).

**Relationship to other specs:**

| Spec | Relationship |
|---|---|
| `spec_p3_reader_integration.md` | The Reader's contracts (render views, anchors, capture, salience firewall, restoration). This spec keeps every §1.1 invariant. It implements P3 §5.4's inquiry-thread projection, and it brings syntopic UI, which P3 §1.3 left out, into scope under P3 §7's source-local rules |
| `spec_reader_quick_check_producer.md` | Its producer is reused for RW1's reconnect question, with a passage scope |
| `spec_daily_loop_v1.md` | Reading blocks (§6.10), scheduled checks (§6.1), "Check once" (§5.2) and the intent control (§5) are consumed here, not duplicated. RW6 and RW7 wait on DL1 and DL2 |
| `spec_embedding_consumers_v1.md` | T6 (§9, merged) is the retrieval substrate. PF (§5, merged) supplies verified generation, the sandbox and `find_practice` (§5.9) |
| `spec_action_router_v1.md` | The Reader's within-session help is not the router (two timescales). RW6 adds a reader section to `LearnerStateCardV1` (§4). RW4's `find_sources` facade is the retrieval surface router §15.3 calls when its trigger fires |
| `spec_blind_grading_diagnosis_split_v1.md` | The grader stays blind. The diagnoser sees the workbench trace of the current attempt only |
| `spec_learner_field_v1.md` | Workbench assistance maps onto `hints_used` and `primed`; stuck text in the workbench becomes a `stuck_confusion` signal (§3.1) |
| `implementation_handoffs.md` §4 | The learner-text-gaps pipeline is the "observation compiler" the dialogue asks for. The Reader adds sources to it and does not build a second one |

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
- **session → memory → later check**: nothing summarizes a reading session for the router, and nothing turns assisted understanding into a later independent check.

**The Reader becomes a source-grounded workbench.** Reading still looks like reading. When the learner investigates, the Ask rail branches and reconnects. When the learner works a problem, the source stays beside a step-by-step workspace whose hints start from the learner's own steps. Passages that touch something the learner got wrong before carry a quiet margin mark. A question to the library returns the passages, organized by what each source contributes, with the tutor one click away. When the session ends, LearnLoop keeps a typed record of what happened, gives the router a summary, and schedules one short unfamiliar problem for when forgetting is expected.

Four rules carry over from the dialogue:
1. **Preserve the learner's evolving reasoning,** not only what was asked and whether the final answer was right.
2. **Help is a deliberate, recorded quantity.** The learner can always get more. What LearnLoop offers first adapts to prior knowledge and struggle, and every piece of help is recorded as assistance, so assisted success is never mistaken for independent competence.
3. **Sources keep their identity.** What a source claims, what LearnLoop infers and what the learner believes stay separate. Cross-source reading preserves differences instead of fusing them into a consensus.
4. **No intervention is a legitimate outcome.** Cues are marks in the margin, never interruptions.

---

## 1. Scope

**In scope (v1), as seven phases (§13):**
- **RW1. Inquiry.** A selection intent box (type what you want; the palette stays one key away); branching Ask threads, by porting the unmerged `origin/feat/reader-clarification-branches`; inquiry status on the existing outstanding-question queue; breadcrumbs and return-to-source; a reconnect check when a branch resolves; a reader report baseline.
- **RW2. The exercise workbench.** Step-by-step work beside the source; "check my work" that finds the first questionable step; a six-level help ladder whose hints start from the learner's own valid steps; adaptive first offers; symbolic checks where steps parse; assistance mapped onto existing evidence semantics.
- **RW3. Passage cues.** Misconception-aware reading: margin marks on passages that connect to the learner's open hypotheses, recurring mistakes, named gaps, or demonstrated capabilities; restrained and density-capped, with a logged holdout.
- **RW4. Library questions and syntopic reading.** An instructional-role index over source blocks; a `find_sources` facade with retrieval policies by context; natural-language library questions answered sources-first, organized by role and source, with an optional tutor; "compare sources" with source-local claims and proposed relations; "practice this question" through `find_practice`.
- **RW5. Explorable figures.** "Make this explorable" on a selected equation or figure: a declarative, verified `InteractiveFigureSpecV1` drawn by a trusted renderer, with optional predictions.
- **RW6. Loop closure.** A session digest (typed and deterministic, plus an optional narrative); reader activity in the router's learner-state card; one cold follow-up check per session, scheduled when forgetting is expected (a serving successor).
- **RW7. Goal-aware reading paths.** The Guide labels sections core, prerequisite, enrichment or already shown for the learner's intent, and the daily plan's reading block follows that path (a serving successor).

**Not in scope** (each with a trigger in §17):
- the router querying the source vault as a tool (router §15.3 keeps its own trigger; RW4 builds the surface it will call);
- an OS-level or MCP learning service, and browser or editor capture;
- generated-code figures and their isolated rendering surface;
- page-image (visual) retrieval;
- learned cue and hint policies;
- full solution graphs with alternative branches;
- a CAS calculator tool in the workbench;
- photo-of-work input to the workbench (until DL4's transcription route lands);
- workbench and figures on video transcripts.

---

## 2. Standing constraints

- **W1. Reading and help are not evidence.** P3 invariant 6 holds: dwell, highlights, asks, cue taps, figure play, inquiry status and digests never enter mastery, posterior, certification or FSRS. The only evidence a workbench session produces is its final submitted attempt, graded by the blind grader and discounted for the assistance it recorded (W8).
- **W2. Honest labels.** Every surface distinguishes source-authored, AI-written and learner-written content (P3 invariant 9). Model judgments are labelled as such. "Verified" appears only when a non-LLM check (sympy, exact key, quote match) passed. A cue never says the learner *is* confused, only that a passage connects to something they worked on.
- **W3. Generous defaults, live behind kill switches.** Every phase ships on by default with its switch. No step is added to protect a model.
- **W4. LLM judgment over constants.** First-offer help level, cue selection, passage roles, path roles and follow-up items are model judgments over typed learner state. Numbers in this spec are caps or display limits, never thresholds that decide learning.
- **W5. Learner text over skip buttons.** The intent box, "what's still unclear?", "I'm stuck" in the workbench and "not relevant, because…" on cues take free text. A one-tap path still exists (an empty box is allowed), as with "I'm stuck".
- **W6. Embeddings shortlist, judges decide.** No embedding score alone creates a cue, a relation, a role or a match (R1). Shortlists are top-k; judges decide everything shown.
- **W7. Cold means no source cue.** P3 invariant 10 and `find_sources`' retrieval policies (§7.2): a cold attempt gets no source, hint, tutor or figure; opening one ends cold status. A source-visible attempt never certifies.
- **W8. Grading stays learner-blind.** The grader sees the final answer as today. Steps, hints, checks and learner history never enter `BlindGradingContext`.
- **W9. Replay makes zero model and embedding calls.** Every paid output (checks, hints, cues, roles, claims, figures, digests) is persisted and never regenerated on rebuild.
- **W10. Spend controls.** Every paid step uses the Phase 1 framework (`learnloop/ai/spend.py`): per-route caps, `--dry-run` on every batch command, receipts. Codex is `estimated_only`. Every LLM, Decider, verifier or learner-card verdict appends to `judgment_ledger`.
- **W11. Agency.** The learner can always ask for more help, turn cues off, override a path, hide the source before working, and undo every automatic action.
- **W12. The reading hot path never waits for a model** (P3 invariant 1). Cue links, roles and paths are computed in the background and appear when ready.

---

## 3. Code truth (audited 2026-10-12 on `main` at `68213d96`)

### 3.1 The Reader today

| Capability | Where | What it does now |
|---|---|---|
| Rendering and anchors | `learnloop/reader/source_render_views.py`, `annotations.py`, `span_view.py` | Marker markdown and KaTeX views, block crosswalk, sub-block anchors with reanchoring, original-region fallback |
| Rail | `screens/ReaderScreen.tsx:155` (`"guide" \| "ask" \| "notes"`), 3,991 lines in one component | Guide, Ask and Notes tabs beside the source |
| Capture palette | `screens/ReaderScreen.tsx:71` | Nine presets in three groups: background requests (research, worked example, explain differently, why it matters), "Remember later" (test me later, help me remember, connect it), Mark (confusing, not worth remembering) |
| Ask | `learnloop/reader/reader_dialogue.py:412` (`ask`), `:610` (`ask_history`) | Span-grounded tutor answers in the `reader` context, with answer modes `answer_directly`, `help_me_reason`, `ask_me_first` (`learnloop/tutor/tutor_qa.py:81`). Each exchange is a `reader_answer_submitted` interaction event (`reader_dialogue.py:104`). **History is flat:** P3 §5.4's inquiry-thread projection was never built |
| Outstanding questions | `migrations/102_question_resolution.sql:9`; `components/QuestionQueue.tsx` | Every tutor question carries a learner-owned `resolution` (`open` \| `resolved` \| `dismissed`) and shows on Today until resolved |
| Guide | `learnloop/reader/reader_guidance.py:292` (`build_guide_plan`), `:130` (`_learner_signal`) | Section checks and suggested passages. A passage cited by an item whose LO has an active error gets "Revisit this to resolve: <misconception statement>" (`recent_misunderstanding`). The reason is shown only in the rail, never on the passage |
| Quick checks | `learnloop/reader/reader_quick_check.py`; `migrations/105_reader_authored_questions.sql` | One AI-authored, span-grounded, formative question per section, escalatable to a practice item |
| Exercise import | `learnloop/content/authoring/exercise_authoring.py`; `learnloop_sidecar/handlers/reader.py:1492` | Selected textbook exercises become real practice items: verbatim stem, AI-completed answer, rubric, facets and progressive hints. **Working them happens on the practice screen, away from the source** |
| Section progress | `learnloop/reader/reader_progression.py`; `reader.mark_section_progress` (`handlers/reader.py:1381`) | Section completion triggers practice generation for `as_you_read` sources |
| Source objects | `learnloop/reader/source_objects.py`; `migrations/094_source_objects.sql:63` | Per-source claims, definitions, worked examples and problems, and relations (`supports`, `contradicts`, `refines`, `alternate_definition`, `unresolved`, `learner_connects`), all proposals. **No UI reads the relations** |
| Instructional administrations | `reader_dialogue.py:683` (`administer_reading_question`); `learnloop/substrate/administration_adapters.py:137` | A source-visible reading question is an instructional administration, which mints no certification |
| Video | `reader.watch_plan` (`handlers/reader.py:1189`) | Transcript sources open in the Reader |

### 3.2 Adjacent systems on `main` that this builds on

| System | Where | Used by |
|---|---|---|
| T6 hybrid retrieval: FTS5 BM25 + dense + rewrite, fused by RRF; LLM listwise verification; nearest-LO suggestion | `learnloop/source_retrieval/search.py:126` (`search_spans`), `library.py:117`, `tutor.py:70` (`TutorSpanProvider`), `verify.py:156`, `suggest.py:95` | RW2, RW3, RW4, RW6 |
| T6's assessment exclusion and answer withholding in practice context | `source_retrieval/tutor.py:125` (`span_leaks_expected`); `tutor_qa.py:816` (`answer_leaks_expected`) | RW2 hint leak control, RW4 policies |
| Practice index: `find_practice` (proposes, never serves), dossiers, coverage | `learnloop/practice_index/retrieval.py:727`; `practice_index/tool.py` | RW4 "practice this question", RW6 follow-ups |
| PF-b generation: ensemble and source-anchored paths, verified references, bubblewrap sandbox with sympy | `learnloop/content/authoring/pf_sandbox.py:120` (`run_sandboxed_python`); `ops/pf_generation.py` | RW2 step checks, RW5 figure verification, RW6 follow-ups when nothing fits |
| Blind grader and history-aware diagnoser (Slice 1 M2), PF-c unassessed rule | `learnloop/attempts/blind_grading.py`; `learnloop/diagnosis/split/` | RW2 submission and diagnosis |
| Guided redo: prefix-preserving partial redo as a primed attempt | `learnloop/diagnosis/guided_redo.py` | RW2 after a wrong submission |
| Reveal ledger | `learnloop/attempts/reveal_ledger.py:37` (`tutor_answer`, `repair_display`, `guided_redo`, `source_review`, `answer_display`) | RW2 hint reveals |
| Hints and assistance | `PracticeItem.hints` (`learnloop/vault/models.py:684`), `HintPolicy` (`:370`); `tutor_qa.py:741` (`hint_equivalents_for_submission`); `assistance_discount` (`learnloop/attempts/effective_observation.py:132`) | RW2 assistance mapping |
| "I'm stuck" (`mvp-0.13`) | `learnloop/attempts/stuck.py:271` (`stuck_answers`) | RW2's stuck box |
| T1's generic matcher (shortlist, judge, ledger, no-chaining union) and recurrence groups | `learnloop/matching/`; `learnloop/substrate/recurrence_groups.py` | RW3 passage links, RW4 claim pairs |
| The Decider client (R0) | `ai/providers/` `decider` type, profile `openrouter_decider` | RW1 intent routing, RW2 first-offer choice |
| Manim explainer animations (consent-gated, sandboxed) | `learnloop/content/authoring/concept_animation.py` | Not reused for figures: RW5 runs no generated code |

### 3.3 Unmerged work this spec depends on (2026-10-12)

| Branch | What this spec uses |
|---|---|
| `origin/feat/reader-clarification-branches` (`cf2cbe77`, 2026-10-08) | Branching Ask with explicit parents on the `reader_answer_submitted` payload, the branch tree in the Ask rail, ancestor-only prompts, and 12 backend plus 9 frontend tests. No migration. Its base, PR #5, is in `main`; the commit itself is not, and conflicts are expected in `reader_dialogue.py` and `tutor_qa.py` (T6 changed both) and in `ReaderScreen.tsx` |
| `daily-loop/dl1` (built, waiting to merge) | Reading blocks (§6.10) and scheduled checks (§6.1) |
| DL2 (not built) | Intent resolution, recall targets and "Check once" (§5) |
| `learner/text-gaps` (built) | `learner_text_gaps`, `named_gaps_for_card()`, the `StuckTextSource` interface |
| `providers/chatgpt-plan` (building) | A fast, tool-free route for short structured calls (RW1, RW2) |
| Router R1 (built), R2 (not built) | `router_decisions` and the card that RW6 extends |

### 3.4 What the dialogue asks for that does not exist

- No branching or status on Reader inquiries beyond the flat `resolution` column.
- No workspace for solving: no step capture, no work-aligned hints, no localization before submission.
- No passage-level cue; the Guide's misunderstanding reason never reaches the text.
- Library search returns a ranked list without roles or per-source contributions; nothing compares sources.
- Nothing labels source blocks by instructional role (definition, worked example, exercise, solution).
- No interactive figures.
- No session record, no reader input to the router, no follow-up check after assisted work.
- The Guide's section order is the book's; goals rank passages but never skip or reorder sections.

---

## 4. RW1 — Inquiry: the intent box, branches, status and reconnect

### 4.1 What the learner sees

**The intent box.** Selecting text opens a small box beside the selection: "What do you want to do with this?" with the cursor in it.
- The learner types in their own words ("why are the densities weighted?", "quiz me on this later", "make this a problem I can work"). Enter routes it.
- **Tab** (or clicking "actions") shows today's palette unchanged, so experienced use and keyboard shortcuts keep working.
- An empty Enter runs the default action, Ask.
- The routed action shows as one line before it runs, for example "Asking · help me reason · change". "change" opens the palette with the text kept. There is no confirmation step.

**Routing** is one typed `choice` question to the Decider (route `ai.routing.reader_intent`, a decider task: never a chat fallback). The options are the actions that exist when the call is made:
- ask (with its answer mode: explain / help me reason / ask me first);
- worked example, explain differently, why it matters;
- remember, test me later, connect it, mark confusing, not worth remembering;
- import as exercise, and from RW2 "work through this";
- from RW4 "compare sources" and "practice this question";
- from RW5 "make this explorable".

The learner's text becomes the question (for asks) or the annotation's learner text (for everything else).
- **If the Decider is unavailable,** times out (`reader_intent.timeout_seconds`, 4) or is spent out, the action is Ask. Ask is always valid.
- **Verdicts.** Every routing appends to `judgment_ledger` (task `reader_intent`, judge `decider`). A "change" appends the learner's correction (judge `learner_card`), so routing error stays measurable without a review chore.

**Branching Ask.** Port `origin/feat/reader-clarification-branches` onto `main`, keeping its contract:
- `reader.ask.parentExchangeId` is the parent's `readerAnswerEventId`;
- the parent's spans override the current selection;
- only ancestors enter the prompt (the latest 12, with omitted counts in the manifest);
- the rail shows the tree, with search, expand, "new thread" and return-to-passage.
- The port's job is to compose with T6's injected span provider: a follow-up's retrieval query is the follow-up's own question, and its ancestors are context only.

**Inquiries.** An inquiry is a root exchange and its descendants.
- **Breadcrumb.** The rail shows the current inquiry as one line ("Mixture CDF → conditioning → integration bounds"); clicking a crumb opens that exchange and scrolls the source to its passage.
- **"Back to where I was"** restores the reading position from before the first branch (reader UX state, not source truth; P3 §12).
- **Status reuses what exists.** The root's `question_events.resolution` (`open` / `resolved` / `dismissed`) is the inquiry's status, so open inquiries already appear in Today's outstanding-question queue. Two richer intents map onto existing commit presets on the root's anchor:
  - "Revisit once" → `test_me_later`;
  - "Make it something I can do" → `help_me_remember`.

  No new status vocabulary is added.

**Reconnect.** When a child branch is marked resolved, or the learner returns to the root passage, the rail shows one line: "Does the original passage make sense now?"
- **Yes** resolves the root.
- **A text box, "What's still unclear?",** starts a new branch from the root with that text as its question (W5).
- **"Check me"** asks the quick-check producer for one formative question scoped to the root passage (§4.2). It behaves like today's quick checks: answered, the expected answer is revealed for comparison; it is never an attempt; "add to practice" escalates it through the existing path.
- Ignoring the line does nothing; it disappears when the learner scrolls on (W12).

**Reader report baseline.** `learnloop reader report [--json] [--since]` aggregates, without model calls and without text:
- visits and minutes; selections; intent-box vs palette use; routing corrections;
- asks, branch depth and breadth; inquiries opened, resolved and dismissed; reconnect answers;
- time to first action after opening a source.

Later phases add their blocks (§15).

**Splitting the screen.** RW1 moves the rail into components (`screens/reader/AskRail.tsx`, `GuideRail.tsx`, `NotesRail.tsx`, `IntentBox.tsx`) so that RW2–RW5 can be built in parallel without one 4,000-line conflict.

### 4.2 Data

- **Branches:** no table. The parent lives on the `reader_answer_submitted` payload (as on the branch).
- **Inquiry status:** `question_events.resolution` and commitments, unchanged.
- **Intent routing:** two new kinds on the reader `interaction_events` envelope (migration 091): `reader_intent_routed` (learner text hash, options offered, chosen action, chooser, ledger id) and `reader_intent_corrected`. They are salience-only, and the firewall test is parametrized over them.
- **Reconnect question:** `reader_authored_questions` (migration 105) gains nullable `anchor_span_ids_json` and `inquiry_root_event_id`. Idempotency becomes (extraction, section *or* inquiry root, prompt version); section rows are unchanged.

### 4.3 Routes, spend, privacy

- **Routes.** `reader_intent` (decider; about $0.0004 a call at the listed price; `reader_intent.max_calls_per_day` 200). The reconnect question uses the quick-check producer's existing route.
- **Privacy.** The selection and the learner's text go to OpenRouter's Decider provider (router D6 covers the disclosure). Nothing else is new.

### 4.4 Successor

None. Content and display. Kill switches:
- `reader_inquiry.enabled` (off: the flat rail, exactly as today);
- `reader_intent.enabled` (off: the palette opens on selection, as today).

---

## 5. RW2 — The exercise workbench

### 5.1 What the learner sees

**Where it opens:**
- **In the Reader,** "work through this" on an imported exercise, a quick check or a selected problem, or the intent box. The source stays in the left pane, and the workbench replaces the rail's width.
- **On the practice screen,** "Work in steps" (remembered per learner). It is on by default for items whose trace contract has at least two checkpoints, which is a deterministic rule.
- **From the daily plan,** the same as the practice screen.

**The layout:**
- **Problem:** the verbatim stem, with "original page" when it came from a source.
- **Your work:** an ordered list of steps. Each step is markdown with LaTeX and a live KaTeX preview (the existing `MarkdownMath` renderer). Steps can be added, edited (appending a successor; the earlier text is kept) or deleted (a tombstone).
- **Actions:** **Check my work · Help · I'm stuck · Submit.**
- **Help style** (one control, remembered): **let me struggle · balanced · guide me**, default balanced.

**Check my work** reads the steps and returns, for each step, `valid`, `questionable` or `unchecked`, and names the **first questionable step** with a reason that quotes it. It never gives the correction (ladder level 2). Two things back each verdict:
- **Symbolic check.** Where a step is an equation or expression that parses, a sandboxed sympy harness checks that it follows from the previous step or the declared transformation. The verdict is then labelled "checked".
- **Model reading.** Otherwise the label is "model's reading, not checked" (W2).

**The help ladder.** Help always starts from the learner's **last valid checkpoint**:

| Level | What it is | Example |
|---|---|---|
| 0 | No help | — |
| 1 | A question about the approach or an assumption | "What does F(x) have to equal at the left end of the support?" |
| 2 | Localize: the first questionable step, no correction | "Step 4 is where your expression stops being a CDF." |
| 3 | A targeted hint: the principle or a subgoal, tied to the learner's step | "Your derivative in step 3 matches the PDF; check the constant of integration in step 4 against F(0) = 0." |
| 4 | Partial worked continuation: the next portion, starting from the learner's valid steps | Writes step 5 in the learner's notation |
| 5 | Full walkthrough, keeping the learner's route where it is valid | Completes the solution from step 4 |

- **Help** opens the ladder with one level **offered first** (§5.3), and every other level visible. The learner can take any level at any time (W11).
- **I'm stuck** opens a text box, "Write what you can, or what's confusing you". The text becomes a step of kind `stuck`, the hint writer reads it, and it is a learner-text-gaps source (§5.5). An empty stuck box is allowed and simply asks for help at the offered level.
- **Submit** sends the composed answer through the ordinary attempt path (§5.4).

**The reconciliation contract** answers the owner's pain point. It is checked in code before a hint is shown:
1. **It cites the learner.** Every hint at level 2 or higher names at least one of the learner's step ids that exists, and quotes it.
2. **It continues from a real checkpoint.** `continue_from` must be a step marked `valid` or `unchecked`, and no later than the first questionable step.
3. **It says what stands.** The hint states which of the learner's steps stand ("Your steps 1–3 stand").
4. **It keeps the learner's route.** It never switches to the reference's route unless the learner's route is invalid or the learner pressed "Show me the book's way". A valid but different route is said to be valid; PF-c's valid-alternative rule applies to checks as it does to grading.
5. **It changes strategy when stuck.** After two hints on the same step, a new hint must declare a different `strategy` slug (for example `boundary_check`, `worked_parallel`, `representation_switch`, `counterexample`) from both earlier ones. The dialogue's "change strategy instead of repeating an ineffective hint".

A hint that fails 1, 2 or 5 is re-asked once with the failure named, then shown as level 3 from the last valid step, without its unverified claims.

**Bridging to the book.** When T6 retrieval finds a source passage that the hint relies on, the hint can show it side by side: "Compare its integration limits with your step 4". Retrieval uses the `assisted_practice` policy (§7.2). The item's own solution, expected answer and exercise blocks are never retrieved (T6's practice-context exclusions, `source_retrieval/tutor.py:125`).

**Leak control.** A hint at level 3 or lower must not contain the final answer:
- `answer_leaks_expected` (`tutor_qa.py:816`) is checked on every hint;
- T4's paraphrase detectors run as shadow flags;
- a leaking hint is re-asked once, then withheld with "this hint would give the answer away; take level 4?".

### 5.2 Source visibility

- **In the Reader, the source is visible by default.** The attempt is recorded as an instructional administration with `source_visible = true` (the `administer_reading_question` path, `reader_dialogue.py:683`). It teaches, feeds the diagnoser and updates the learner's picture, but never certifies (W7).
- **"Hide the source"** before the first step makes it an ordinary practice attempt. Opening the source afterwards records contamination exactly as today (P3 §11).
- **On the practice screen and from the plan,** the source is hidden. "Original page" behaves like any other source opening during practice.

### 5.3 The first offer: a judgment, not a rule

When the learner opens Help, the **level chooser** picks which level to offer first.
- **How it is asked.** One typed `choice` over levels 1–5, with descriptions, to the Decider (route `ai.routing.workbench_level_chooser`, a decider task). With no Decider, the LLM route `workbench_hint` answers it.
- **The state it gets** (typed, short):
  - the item's LO status (untested / assumed / learning / demonstrated);
  - for the item's facets and capability: demonstrated vs assisted-only evidence, from the capability ledger and facet timeline;
  - the active predictor's P(success) and interval for this item (`LearnerPredictor.predict_item`);
  - workbench history on these facets: levels taken, and whether the learner continued unaided afterwards;
  - this session's failed checks and hints;
  - the learner's help style.

  Learner history reaches the chooser, never the grader (W8).
- **What it does with that.** The expertise-reversal finding the dialogue cites: novices benefit from more guidance and experts from less, per learner × facet × task. The chooser applies it from evidence, not from a threshold table (W4).
- **Fallback.** With `workbench.level_chooser_enabled = false`, the offer is level 1, then one level up on each further Help press.
- **Logging.** The offered distribution and the level the learner took are logged on the assist row. There is no randomization of help quality (§17).

### 5.4 What an attempt records (no new evidence semantics)

The workbench maps every assist onto fields that already have meaning, so it needs no scoring successor:

| Assist | Recorded as | Existing meaning |
|---|---|---|
| Check my work (level 2), level 1 and level 3 hints | `hints_used` += 1 for each one shown | An assisted attempt: it still schedules FSRS but certifies nothing (`diagnosis/causal_activity_policy.py:145`, "Assisted attempts certify nothing"); its evidence takes the assistance discount (`effective_observation.py:132`); the learner field's `+hints` arm reads it |
| Level 4 or 5 | The attempt is `primed` | The `repair_activity` class: no FSRS feed and no certification, like a guided redo (`guided_redo.py`) |
| Any hint text overlapping the key | A `reveal_events` row of the new kind `workbench_hint`, with its amount | Production admissibility (`reveal_ledger.py`), the reveal-aware cold lane |
| Source opened during a hidden-source attempt | The existing contamination path | Not cold |
| `I'm stuck` with text, then Submit | `declared_stuck` stays false: the steps are an ordinary answer | The stuck step is a confusion signal (§5.5) |

So any check or hint makes that attempt assisted, which is the dialogue's rule: "requesting help transitions the attempt to an assisted activity rather than secretly preserving cold status". Independent credit comes from later unassisted attempts, including RW6's follow-up.

**On Submit:**
- the composed answer (the steps in order, stuck steps excluded) goes through `submit_attempt` with `hints_used` and `primed` set as above;
- the blind grader grades it with no knowledge of the steps' history or the hints (W8);
- the diagnoser's context gains, for this attempt only, the step trace with the assists in order and the work before each assist. The dialogue: "preserve what the learner attempted before each hint". Every other attempt's context hashes as before (the stuck-reading precedent);
- the feedback screen is today's, including guided redo.

**Abandoned sessions** (closed without Submit) write no attempt. Their steps and assists stay as learner work and feed RW6's digest.

### 5.5 Reuse

- **Grading and diagnosis:** the blind grader, the diagnoser, PF-c and guided redo, unchanged.
- **Symbolic checks:** PF's sandbox (`pf_sandbox.run_sandboxed_python`). It fails closed without bubblewrap, and the check is then labelled "model's reading".
- **Authored hints first:** when the item's authored `hints` fit the learner's checkpoint, the hint writer may use one verbatim, labelled "from the item".
- **Retrieval:** T6 (`search_spans` and `verify_spans`) for bridging.
- **Learner text:** `I'm stuck` steps join the learner-text-gaps pipeline through its `StuckTextSource` interface (branch `learner/text-gaps`). A workbench stuck step with text that describes confusion also emits the field's `stuck_confusion` signal for the item's LO (mass 0; it blocks fast-track), as the stuck prompt does.

### 5.6 Data

| Table | Role | Contents |
|---|---|---|
| `workbench_sessions` | WORKFLOW | `id`, `practice_item_id`, `origin` (`reader` \| `practice` \| `plan`), `extraction_id`, `span_ids_json`, `source_visible`, `help_style`, `status` (`open` \| `submitted` \| `abandoned`), `attempt_id`, `created_at`, `closed_at` |
| `workbench_steps` | RAW_LEDGER | `id`, `session_id`, `ordinal`, `kind` (`step` \| `stuck`), `body_md`, `supersedes_id`, `deleted` (tombstone), `created_at` |
| `workbench_assists` | RAW_LEDGER | `id`, `session_id`, `kind` (`check` \| `hint` \| `bridge`), `level`, `offered_level`, `offer_distribution_json`, `chooser` (`decider` \| `llm` \| `fixed`), `step_snapshot_json` (the step ids and their content hashes at request time), `step_verdicts_json` (verdict and method per step), `first_questionable_step_id`, `continue_from_step_id`, `strategy`, `body_md`, `cited_span_ids_json`, `leak_flags_json`, `contract_failures_json`, `model`, `prompt_version`, `input_hash`, `created_at` |
| `reveal_events` (existing) | RAW_LEDGER | The CHECK gains `workbench_hint`. The migration rebuilds the table exactly as migration 179 did, with both indexes and both append-only triggers |

Replay never reads the workbench tables: the attempt row carries `hints_used` and `primed`, and the reveal ledger carries the reveals.

### 5.7 Routes, spend, privacy

- **Routes:**
  - `workbench_check` (chat): step verdicts and localization;
  - `workbench_hint` (chat): hints at levels 1–5;
  - `workbench_level_chooser` (decider);
  - all unset → the active provider (Codex, `estimated_only`), except the decider task.
- **Latency.** Codex blind grading took 29–37 s on the stuck-prompt copy, which is too slow for "I'm stuck". The target is check and hint p50 ≤ 10 s, **reported, not enforced**. The recommended route is the ChatGPT-plan provider once `providers/chatgpt-plan` merges, else a fast OpenRouter chat profile (D7).
- **Caps:**
  - `workbench.max_calls_per_session` (24);
  - `workbench.max_daily_cost_usd` ($1.00 for metered routes);
  - a capped session says so and keeps the authored hints available.
- **Context per call:** the item stem, reference solution and rubric; the session's steps and assists; at most four verified source spans; and, for hints only, the open hypotheses on the item's facets as typed records (statement and status, no prose; Slice 1 S3). About 4–12K input tokens.
- **Privacy:** the learner's work and that slice of their state go to the configured provider, as grading and diagnosis already do. No new disclosure.

### 5.8 Successor

None, because §5.4 writes only existing fields with their existing meanings and adds one reveal kind that only new events use. The RW2 agent confirms this against `resolve_attempt_activity_policy`. **If any mapping needs a new discount rule, stop and make it a successor** (`workbench_assistance_v1`) rather than bending an existing field. Kill switches:
- `workbench.enabled` (off: no workbench entry anywhere; the practice screen is byte-identical);
- `workbench.level_chooser_enabled`;
- `workbench.symbolic_checks_enabled`.

---

## 6. RW3 — Passage cues (misconception-aware reading)

### 6.1 What the learner sees

A thin mark in the margin beside a passage, and a one-line note on hover or focus. There are two kinds, and both say what connects, never what the learner lacks:
- **Revisit a distinction:** "Connects to a distinction you worked on: density vs cumulative probability. Not yet independently checked since."
- **A new application:** "A new use of something you've shown: conditioning on a component."

**Actions on a cue:**
- **Open** shows the earlier work: the cited attempt, its diagnosis, the inquiry, the named gap.
- **Check me** offers one short item through `find_practice` on the cue's facets, as a learner pick: an ordinary attempt, ordinary evidence. Before DL1 merges it opens the item directly.
- **Not relevant** shows an optional text box, "why? (optional)" (W5).
- **Cues off** works for this source or everywhere.

**Restraint (W12):**
- at most `cues.max_per_section` (2) cues are visible in a section, and the cue judge's ranking picks which;
- cues never pop up, never block and never appear in skim mode;
- with `cues.holdout_rate` (0.1), an eligible cue is withheld at random, with a logged seed and propensity, so its effect on the next attempt on those facets can be estimated without asking anything of the learner (§15; D10).

### 6.2 How a passage gets a cue

Links are computed in the background when a source opens (W12) and cached until the learner's state changes.

1. **Targets.** The learner objects worth connecting to:
   - recurrence groups and open causal hypotheses (T1, Slice 1);
   - durable misconceptions and holding-pen candidates;
   - named gaps from `learner_text_gaps` once that branch merges;
   - facets with demonstrated capabilities (for "new application" cues).

   Each is rendered as its LLM-written statement (R3: embed LLM-written text).
2. **Shortlist.** A new `MatchKind` in T1's matcher (`learnloop/matching/`), `passage_gap`, shortlists source blocks (`source_block/text` vectors from T6) for each target: top-k, filtered to the source's sections, plus the blocks provenance-linked to the target's facets (`entity_source_links`). There is no cosine cutoff (W6). With no vectors, the shortlist is provenance links plus BM25 over the target statement.
3. **Judge.** An LLM judge (route `passage_cue_judge`) reads each target with its shortlist in one call and says, per passage, `clarifies_distinction` | `new_application` | `prerequisite_for` | `none`, with a confidence word and the quote it relies on (quote-verified). Every verdict appends to `judgment_ledger` (task `passage_gap_relevance`, judge `llm`).
4. **Rank and cap.** Within a section, the judge's ranking order picks up to the cap. The existing Guide signal (`_learner_signal`, `reader_guidance.py:130`) becomes one of the inputs, so the rail and the margin agree.

**Learner taps** append `learner_card` verdicts on the same ledger task: "not relevant" is `different`, "open" and "check me" are `same`. Judge precision is then measurable with no review chore.

**When state changes,** the cache key is the learner-state fingerprint (target ids plus their status and last-updated). A new hypothesis or a resolved one recomputes only that target's links.

### 6.3 Data

| Table | Role | Contents |
|---|---|---|
| `passage_links` | WORKFLOW (paid outputs; never re-run on rebuild) | `id`, `extraction_id`, `span_id`, `target_kind` (`recurrence_group` \| `hypothesis` \| `misconception` \| `learner_text_gap` \| `demonstrated_facet`), `target_id`, `relation`, `quote`, `ledger_id`, `state_fingerprint`, `model`, `prompt_version`, `created_at` |
| `reader_cue_impressions` | RECEIPT | `id`, `link_id`, `visit_id`, `shown`, `propensity`, `seed`, `response` (`opened` \| `check_me` \| `not_relevant` \| `none`), `response_text_hash`, `created_at`, `responded_at` |

### 6.4 Routes, spend, privacy

- **Route:** `passage_cue_judge` (chat; Codex by default, since it is background work).
- **Caps:** one call per (target, section batch); `cues.max_calls_per_source_open` (12); `cues.max_daily_cost_usd` ($0.50 metered).
- **Privacy:** hypothesis and gap statements plus source passages go to the provider, the same class as diagnosis.

### 6.5 Successor

None: display only, and nothing it writes enters evidence or serving. "Check me" is a learner pick. Kill switch `cues.enabled`; `cues.holdout_rate = 0` turns the holdout off.

---

## 7. RW4 — Library questions, syntopic reading and the instructional index

### 7.1 The instructional-role index

Every source block in a source the learner opens gets role labels, computed in the background per section:
- the roles: `definition`, `theorem`, `explanation`, `intuition`, `worked_example`, `exercise`, `solution`, `figure`, `counterexample`, `contrast` (an explicit "X is not Y" passage), `application`, `proof`;
- a block may have several roles;
- one LLM call per section (route `source_role_labeler`) labels its blocks with a confidence word;
- every label set appends to `judgment_ledger` (task `source_role`, unary, judge `llm`), and `source_block_roles` holds the current labels for lookup.

It is labelled "AI-labelled" wherever it shows, and it is used three ways:
1. **Organizing** library answers (§7.3).
2. **Excluding** `exercise` and `solution` blocks from every learner-facing retrieval under the `assisted_practice` and `cold_attempt` policies (§7.2). This closes the gap T6 has: its exclusion today relies on `exercise` and `assessment_alignment` links, which only exist where ingest made them.
3. **Feeding** the workbench's bridging (`worked_example` first) and RW5's figure candidates (`figure`, `definition`).

### 7.2 `find_sources`: one retrieval surface with policies

A library function in `learnloop/source_retrieval/`, used by RW2, RW3, RW4 and RW6, and later by router §15.3:

```python
RetrievalPolicy = Literal["reading", "assisted_practice", "cold_attempt", "post_attempt", "authoring"]

def find_sources(
    query: str,
    *,
    purpose: Literal["explain", "worked_example", "prerequisite", "contrast", "figure", "compare", "context"],
    policy: RetrievalPolicy,
    scope: SourceScope,             # library | subject teaching sources | named extractions
    roles: Sequence[str] = (),      # role filter from §7.1, when labels exist
    exclude_item_id: str | None = None,
    limit: int = 8,
) -> SourceHits:                     # spans with per-list ranks, roles, basis, policy applied
```

- **Retrieval** is T6's `search_spans`: BM25, dense and rewrite lists fused by RRF, plus a `roles` filter. `verify=True` runs T6's listwise verification (consequential paths only, as T6 does).
- **What each policy allows:**

  | Policy | Learner-facing material |
  |---|---|
  | `reading` | Everything in scope |
  | `assisted_practice` | No `exercise` or `solution` blocks, nothing leaking the item's expected answer, no assessment spans |
  | `cold_attempt` | **Nothing**: an empty result, by construction |
  | `post_attempt` | Everything, including the item's solution |
  | `authoring` | Everything; only for generation pipelines, never shown to a learner |

- **Receipts.** Every call returns a manifest (query hash, policy, basis, hit ids, statuses) that the consumer stores on its own row, as T6's tutor manifest does. Exposure is recorded where the consumer shows text (`source_exposure_events`, `reveal_events`), unchanged.

### 7.3 Ask your library

The library search box today (T6: type for keyword, Enter for meaning plus rewrite) gains **"Ask"** (Shift+Enter, or the intent box from a selection's "where else is this explained?").
- **The default answer is sources first** (D12): no AI essay. Up to eight passages from `find_sources(policy="reading", purpose="explain")`, grouped by role ("Definition", "Geometric view", "Worked example", "Application") and by source. Each carries a one-line "what this passage contributes" written by the organizer (route `library_organizer`) and validated: each line must cite exactly one hit id from the result.
- **"Ask the tutor about these"** opens a library-context tutor exchange whose citation allowlist is the selected hits, across sources. It is a `question_events` row with context `library`, so it joins the outstanding-question queue, field §3.1's signals and the learner-text-gaps pipeline.
- **"Personalized" is a toggle,** default on. When on, the organizer also sees the learner's open gaps on the hits' LOs and may mark one passage "speaks to your open question about …". Off, ordering is plain retrieval rank (the dialogue's guard against confirmation bubbles).
- **"Practice this question"** calls `find_practice(query)`. The learner picks from its proposals: a learner-pick block under DL1, else the item opens directly. When nothing fits, it says so; it never generates live.

### 7.4 Compare sources (syntopic reading)

From a selection or a library answer: "How do my sources treat this?"
1. **Find counterparts.** `find_sources(purpose="compare", policy="reading", scope=library)` finds the counterpart passages in other sources, at most one or two per source and at most four sources.
2. **Extract claims.** Each passage's claims are extracted as **source-local** quoted claims (route `source_claims`; every quote verified against its block), stored as `source_objects` of type `claim` with authorship `ai`, status `proposed` (P3 §7.1: never a cross-source truth claim).
3. **Judge relations.** Candidate claim pairs across sources are shortlisted with T1's matcher (kind `same_claim`; top-k, no cutoff). The relation judge (route `source_relation_judge`) labels each pair:
   - `equivalent`;
   - `different_assumptions`;
   - `different_notation`;
   - `refines`;
   - `contradicts`;
   - `unrelated`.

   Verdicts go to `judgment_ledger` (task `source_relation`). Relations are written to `source_object_relations` as `proposed`, authorship `ai`.
4. **Show a table.** One row per source: its distinct contribution (the organizer's line, citing its claims) and its relations to the others ("same result, assumes independence; Book B assumes only zero covariance"). **Differences are the point:** the UI never shows a merged "consensus" answer.

**Never canonical** (knowledge model §8.1). These relations are source-object relations for display. They never become concept edges, facet merges or prerequisite claims, and nothing reads them for learner state.

### 7.5 Data

| Table | Role | Contents |
|---|---|---|
| `source_block_roles` | WORKFLOW (paid outputs; never re-run on rebuild) | `extraction_id`, `span_id`, `roles_json` (role and confidence), `section_id`, `ledger_id`, `model`, `prompt_version`, `created_at`; unique on (extraction, span, model, prompt version) |
| `source_object_relations` (existing, migration 094) | as today | The CHECK gains `equivalent`, `different_assumptions` and `different_notation`. The migration rebuilds the table, keeping every row and id |
| `question_events` (existing) | RAW_LEDGER | Library asks as today. The organizer's grouping and the `find_sources` manifest ride the existing `source_context_json` column (migration 117), beside T6's `source_retrieval` block |

### 7.6 Routes, spend, privacy

- **Routes:** `source_role_labeler`, `library_organizer`, `source_claims`, `source_relation_judge` (chat; unset → active provider). The organizer and relation judge serve live requests, so the fast route is recommended, as for RW2.
- **Caps:**
  - roles at most `roles.max_sections_per_open` (20) per source open, then on demand;
  - library ask: one retrieval, one organizer call;
  - compare: at most four sources, one claims call per passage and one relation call per batch;
  - `library.max_daily_cost_usd` ($1.00 metered).
- **Batch backfill:** `learnloop sources roles --vault <v> [--source S] [--dry-run]` for owners who want the whole library labelled.
- **Privacy:** source text and the question go to the provider. The personalized toggle adds gap statements, which can be turned off.

### 7.7 Successor

None. Retrieval is context (T6's ruling), relations are proposals, and roles change only which source text a learner-facing model may see. Kill switches:
- `source_roles.enabled` (off: T6's exclusions alone, exactly as today);
- `library_ask.enabled`;
- `compare_sources.enabled`.

---

## 8. RW5 — Explorable figures

### 8.1 What the learner sees

"Make this explorable" on a selected equation, a figure block or a short passage.
- **While it builds,** a small "building an interactive version…" line; reading continues.
- **The result** is a panel beside the passage with sliders for the parameters, one to three linked plots or readouts, and, by default, one **prediction** before the first change:
  - "If p rises to 0.7, which side gains probability?";
  - the learner answers in a word or a choice, then sees the result and the comparison.
- **The label is always visible:**
  - "AI-built interactive · matches the source's equation (checked)" for a verified reconstruction;
  - "AI-built illustration of an interpretation (not checked against the source)" for anything else.
- **Reuse.** The same figure reopens instantly next time from the cache.

### 8.2 The spec, not code

The model writes an **`InteractiveFigureSpecV1`** (JSON, strict schema). A trusted React renderer draws it. **No generated code runs anywhere** (the dialogue's Tauri isolation concern; generated-code fallback is deferred, §17).

```text
spec_version    "ifs-v1"
kind            reconstructed | illustrative
source_claims   [{span_id, quote}]               # quote-verified
parameters      [{name, label, min, max, step, default}]
definitions     [{name, expr}]                    # restricted grammar below
panels          function_plot {x:{var,min,max}, series:[{expr,label}], shade?:{expr,from,to}, markers?}
                pmf_bars      {k:{var,min,max}, expr}
                linear_map_2d {matrix:[[expr,expr],[expr,expr]]}   # unit square and grid under the map
                readout       {label, expr}                         # e.g. P(X<0) = integral(f, x, -inf, 0)
invariants      [{kind: integrates_to_one | monotone_nondecreasing | bounded | equals_source, ...}]
predictions     [{prompt, change:{param:value}, observe:expr | choices}]
```

**The expression grammar.** Numbers; parameter and variable names; `+ - * / ^`; unary minus; `exp log sqrt abs sin cos tan atan erf Phi min max`; `piecewise((cond, expr)…, else)` with comparisons; `pi`, `e`; `integral(expr, var, a, b)` evaluated numerically (Simpson, fixed panel count). There are caps on length and node count.
- **Two evaluators, one grammar:** a hand-written TypeScript parser and evaluator in the renderer (no `eval`, no `Function`), and a Python twin in the sidecar.
- **One golden corpus,** run in both vitest and pytest, keeps them identical within 1e-9 relative error.

### 8.3 Verification (before a figure shows)

Run in the sidecar, with sympy in the PF sandbox:
1. **Structural.** Every expression parses; values are finite on a parameter grid (three points per parameter, at most 81 combinations); panels reference defined names.
2. **Invariants.** Each declared invariant holds on the grid, numerically: a density integrates to 1 within 1e-3; a CDF is non-decreasing and runs from 0 to 1; values stay bounded.
3. **Source match** (`kind = reconstructed` only). An LLM-written sympy check (route `figure_verifier`, the PF equivalence-check pattern with negative controls) must confirm that the spec's defining expression equals the source equation quoted in `source_claims`.

**Outcomes:**
- passing 1–3 makes the figure `verified`;
- failing 3 alone downgrades it to `illustrative`, with its label;
- failing 1 or 2 means it is not shown: "couldn't build a reliable version of this", with the reason.

Verdicts go to `judgment_ledger` (task `figure_verified`, judge `verifier` or `llm`).

### 8.4 Predictions

A prediction is formative (W1):
- it is stored on `figure_predictions`, never as an attempt, an observation or evidence;
- RW6's digest lists predictions that missed, as "worth a second look" items;
- a missed prediction never writes a signal in v1 (§17 names the trigger for using them).

### 8.5 Data, routes, spend, privacy

| Table | Role | Contents |
|---|---|---|
| `interactive_figures` | WORKFLOW (paid outputs; never re-run on rebuild) | `id`, `extraction_id`, `span_ids_json`, `asset_id` (a figure block's image), `spec_json`, `spec_version`, `kind`, `verification` (`verified` \| `illustrative` \| `failed`), `verification_report_json`, `model`, `prompt_version`, `input_hash` (reuse key), `created_at` |
| `figure_predictions` | RAW_LEDGER | `id`, `figure_id`, `prediction_index`, `learner_answer`, `observed_json`, `matched`, `created_at` |

- **Routes:**
  - `figure_author` (chat; image input when a figure asset is included: an OpenRouter vision model, or Codex's image input);
  - `figure_verifier` (chat, writes the sympy check).
- **Caps:** two author attempts and one verifier call per request; `figures.max_per_day` (20).
- **Privacy:** source text and, for figures, the figure image. No learner data.

### 8.6 Successor

None: content and formative. Kill switch `figures.enabled`; `figures.predictions_enabled` turns predictions off.

---

## 9. RW6 — Session digest, reader activity for the router, and cold follow-ups

### 9.1 The session digest

A **reader session** is one visit on the reader envelope (`visit_id`, migration 091), or several visits less than 30 minutes apart. When the learner leaves the Reader, or on the next app open, the session gets a digest.

**The typed summary** is deterministic, built from the ledgers, with no model:
- sections read (from `reader_section_progress`);
- inquiries opened, resolved and still open, with their roots;
- workbench sessions: item, highest help level, submitted or abandoned, grade;
- cues opened or marked not relevant;
- predictions missed;
- gaps named by the learner-text-gaps pipeline;
- facets touched;
- **"claims needing an independent check":** facets where the session's work was assisted only (help level 3 or more, or a source-visible attempt) and no unassisted cold success exists since.

**The narrative** is optional (`digest.narrative_enabled`, default on): at most 120 words, written by route `reader_digest` from the typed summary only, citing event ids (validated against the summary). Labelled "summary written by LearnLoop's model", for example: "Worked through mixture distributions by conditioning on the component. Built the CDF route but slipped on a boundary constant; a level-3 hint fixed it. Independent use on a new distribution is still unchecked."

**At session end** the learner sees a dismissible panel that takes under a minute:
- the summary;
- status chips for open inquiries (resolve / revisit once / keep open);
- the follow-up line (§9.3).

Nothing in it is required.

### 9.2 Reader activity in the router's learner-state card

`reader_activity_for_card(lo_ids, as_of) -> ReaderActivityV1` is a pure read, like `named_gaps_for_card()` on the text-gaps branch. It returns, for the candidates' LOs:
- open inquiries (root question excerpt, age, depth);
- assisted-only work (facet, highest help level, date);
- pending reader follow-ups;
- missed predictions;
- the latest digest narrative, labelled model-written, with its cited event ids.

Router R2 renders it as a "Reader activity" section of `LearnerStateCardV1` (router §4). The card stays deterministic from the ledger (router §4), because the narrative is a persisted, cited row, the same pattern as the teach-back summary (router §15.1). **Nothing in it is evidence** (W1); it informs judgment only. Before R2 the function exists and has tests, but nothing renders it.

### 9.3 Cold follow-ups (the owner's "short unfamiliar problem")

**One per session, at most.** When the digest has a "claim needing an independent check", LearnLoop schedules a follow-up:
1. **Pick the capability.** The follow-up chooser (route `followup_chooser`, LLM) reads the typed summary and picks the one capability most worth checking (W4). It may return none, which is legitimate.
2. **Find an unfamiliar item.** `find_practice(query, constraints)`, with the capability's facets and an unseen requirement: never the same surface, never a surface in an exposed family whose solution was revealed in the session, admissible under the scheduler's rules (reserved cold checks, reveal ledger, exam reserves). Isomorph or near variants from PF families come first; the dialogue warns that new constants alone are not transfer.
3. **Generate only if nothing fits.** One PF-b generation request (ensemble or source-anchored path) for that family. **Only a verified item can be scheduled;** if verification fails, there is no follow-up, and the digest says so.
4. **Pick the date.** When forgetting is expected (router §15.2's direction): the effective due (DL2 §5.3) of the practiced item's FSRS state after the session, bounded to 1–14 days; when the item has no FSRS state, `followups.fallback_days` (3).
5. **Serve it as a scheduled check.** The follow-up is a **scheduled check in the maintain lane** (DL §6.1, next to "Check once", assumed-known first reviews and project probes):
   - capped by `plan.reader_followups_max_per_day` (2);
   - never new material, never counted toward the new-item cap;
   - served cold: no source, hint, tutor or figure (W7), with restoration after the measurement closes (P3 §11).

**Labelled, with undo.** The digest says "Cold check on Thursday: a new mixture-distribution problem · undo". Undo cancels it.

**Ledger.** The chooser's pick appends `judgment_ledger` (task `followup_selection`, judge `llm`). An undo appends a `learner_card` verdict.

**The outcome** joins later in the report: cold success after assisted reader work. This is the dialogue's primary measure (§15).

### 9.4 Data

| Table | Role | Contents |
|---|---|---|
| `reader_session_digests` | WORKFLOW (the narrative is a paid output; never re-run on rebuild) | `id`, `visit_ids_json`, `started_at`, `ended_at`, `summary_json` (typed), `narrative_md`, `cited_event_ids_json`, `model`, `prompt_version`, `dismissed_at`, `created_at` |
| `reader_followups` | WORKFLOW | `id`, `digest_id`, `learning_object_id`, `facet_ids_json`, `practice_item_id`, `item_source` (`find_practice` \| `pf_generated`), `due_at`, `status` (`scheduled` \| `undone` \| `served` \| `answered` \| `expired` \| `no_item`), `ledger_id`, `attempt_id`, `created_at`, `updated_at` |

### 9.5 Routes, spend, privacy

- **Routes:** `reader_digest`, `followup_chooser` (chat; Codex by default, since they are background work). PF generation uses its own routes and caps.
- **Caps:** one narrative and one chooser call per session; one generation request per session.
- **Privacy:** the typed summary goes to the provider, the same class as the router card.

### 9.6 Successor

**`reader_followup_v1`** (the next free algorithm version at landing). Follow-ups change what the daily plan serves: a new class of scheduled checks.
- Kill switch `followups.enabled`. Off: no follow-up is created, and existing ones are not served.
- **Parity:** with the switch off, plan builds are byte-identical to the predecessor on fixture copies.
- The digest and the card function are content and need no successor.

---

## 10. RW7 — Goal-aware reading paths

### 10.1 What the learner sees

The Guide gains a **path** for the learner's intent on this source: DL2's single control on the source or its LOs. One line per section, each with a "why", and the learner can override any section ("read it anyway" / "skip it"):
- **core:** needed for what you're trying to do;
- **prerequisite:** "you'll need this first";
- **enrichment:** optional;
- **already shown:** you have demonstrated this; skip or skim. It requires evidence;
- **assumed:** assumed known (not tested); skim, the first review will check. It requires a Phase 6 assumption.

**Depth wording maps onto DL2's control,** not onto a new object:

| DL2 intent | Path wording |
|---|---|
| Master | Fluency: novel problems, changed assumptions, delayed checks |
| Learn | Learn to use it: explanations, worked examples, practice |
| Keep, Light touch | Get the idea: definitions, examples, visuals; core sections only |

The dialogue's "next suggested activity" is the first unfinished core or prerequisite section, plus, under Learn and Master, one representative exercise from the role index (§7.1) to try in the workbench after reading.

### 10.2 How roles are decided

**One LLM call per source and intent** (route `reading_path_judge`). It sees:
- the section list (titles, roles from §7.1, linked LOs);
- the learner's status on those LOs (untested / assumed / learning / demonstrated);
- the intent;
- the goal, if any.

It returns a role and a why per section.

**Honest labels are enforced in code.** `already shown` stands only if every LO the section teaches is demonstrated (`lo_certification(...).demonstrated`, the headline's predicate), and `assumed` only with an open `assumption_decisions` row. Otherwise the label falls back to `core`.

**Recompute** when the intent or the LOs' statuses change. Each path verdict appends `judgment_ledger` (task `reading_path_role`).

### 10.3 The plan follows the path

DL1's reading block (§6.10) opens "the guide plan's next unfinished section". Under `reading_path_v1` it opens the next unfinished **core or prerequisite** section on the path. Enrichment is never planned, and `already shown` and `assumed` sections are skipped. The block line says so: "Continue §3.2 (core for your goal) · about 12 min".

### 10.4 Data, routes, successor

- **Data:** `reader_path_sections` (WORKFLOW, paid outputs): `extraction_id`, `section_id`, `intent_key`, `role`, `why`, `evidence_refs_json`, `state_fingerprint`, `ledger_id`, `model`, `prompt_version`, `created_at`.
- **Route:** `reading_path_judge` (chat; Codex). One call per (source, intent, state fingerprint).
- **Successor: `reading_path_v1`,** because which section the plan's reading block serves changes.
  - Kill switch `reading_paths.plan_uses_path`. Off: DL1's section order, byte-identical.
  - `reading_paths.enabled` turns the Guide's path display off.

---

## 11. Persistence summary

**Migrations.** Numbers are assigned when each phase lands (`ls migrations/`; head 179 on this base, with DL1, R1, facet identity and learner-text gaps each claiming the next numbers). Follow `CLAUDE.md`'s head-fixture procedure. One migration per phase.

| Table | Role (`db/table_roles.py`) | Phase |
|---|---|---|
| `reader_authored_questions` (existing): `ADD COLUMN anchor_span_ids_json`, `inquiry_root_event_id` | unchanged | RW1 |
| `workbench_sessions` | WORKFLOW | RW2 |
| `workbench_steps`, `workbench_assists` | RAW_LEDGER | RW2 |
| `reveal_events` (existing): CHECK gains `workbench_hint` (rebuilt as in 179) | RAW_LEDGER | RW2 |
| `passage_links` | WORKFLOW | RW3 |
| `reader_cue_impressions` | RECEIPT | RW3 |
| `source_block_roles` | WORKFLOW | RW4 |
| `source_object_relations` (existing): CHECK gains three relation types (rebuilt) | unchanged | RW4 |
| `interactive_figures` | WORKFLOW | RW5 |
| `figure_predictions` | RAW_LEDGER | RW5 |
| `reader_session_digests`, `reader_followups` | WORKFLOW | RW6 |
| `reader_path_sections` | WORKFLOW | RW7 |

**No DERIVED table, so no new replayer.** Replay never reads these tables. The evidence they lead to lives in `practice_attempts` (`hints_used`, `primed`) and `reveal_events`, which replay already reads.

**New interaction-event kinds** (salience-only; the firewall test is parametrized over them): `reader_intent_routed`, `reader_intent_corrected` (RW1); `workbench_opened`, `workbench_closed` (RW2); `cue_shown`, `cue_responded` (RW3; the impressions table is authoritative); `figure_opened` (RW5); `digest_shown` (RW6).

**Config** (all modelled defaults, out of the decision-only template unless it has room):
- `[reader_inquiry]`: `enabled`.
- `[reader_intent]`: `enabled`, `timeout_seconds` (4), `max_calls_per_day` (200).
- `[workbench]`: `enabled`, `level_chooser_enabled`, `symbolic_checks_enabled`, `default_for_multistep` (true), `max_calls_per_session` (24), `max_daily_cost_usd` (1.00), `price_per_million`.
- `[cues]`: `enabled`, `max_per_section` (2), `holdout_rate` (0.1), `max_calls_per_source_open` (12), `max_daily_cost_usd` (0.50).
- `[source_roles]`: `enabled`, `max_sections_per_open` (20). `[library_ask]`: `enabled`, `personalized_default` (true), `max_daily_cost_usd` (1.00). `[compare_sources]`: `enabled`, `max_sources` (4).
- `[figures]`: `enabled`, `predictions_enabled`, `max_per_day` (20).
- `[digest]`: `enabled`, `narrative_enabled`. `[followups]`: `enabled`, `fallback_days` (3); `[plan]` gains `reader_followups_max_per_day` (2).
- `[reading_paths]`: `enabled`, `plan_uses_path`.

**Routes** (each its own `ai.routing.*`, so tiers can be swapped and compared):
- **decider tasks** (never a chat fallback): `reader_intent`, `workbench_level_chooser`;
- **chat tasks:** `workbench_check`, `workbench_hint`, `passage_cue_judge`, `source_role_labeler`, `library_organizer`, `source_claims`, `source_relation_judge`, `figure_author`, `figure_verifier`, `reader_digest`, `followup_chooser`, `reading_path_judge`.

Unset chat routes fall back to the active provider, and receipts record the resolved model.

**`judgment_ledger` tasks:** `reader_intent`, `passage_gap_relevance`, `source_role`, `source_relation`, `figure_verified`, `followup_selection`, `reading_path_role`, plus `learner_card` rows on the same tasks for corrections, taps and undos. The ledger's judge CHECK (R0, migration 175) already admits `llm`, `verifier`, `decider` and `learner_card`, so no change is needed.

---

## 12. Algorithm successors and kill switches

| Change | Kind | Successor | Kill switch | The switch restores |
|---|---|---|---|---|
| Intent box, branches, inquiry status, reconnect (RW1) | Content and display | None | `reader_inquiry.enabled`, `reader_intent.enabled` | Today's flat rail and palette |
| Workbench (RW2): steps, checks, hints; assistance through `hints_used`, `primed`, `reveal_events` | Content, existing evidence semantics | None, unless the RW2 agent finds a mapping that needs a new rule (then `workbench_assistance_v1`) | `workbench.enabled` and its sub-switches | Today's practice screen, byte-identical |
| Diagnoser context gains the current attempt's workbench trace | Context, only when present | None (stuck-reading precedent) | `workbench.enabled` | — |
| Passage cues and holdout (RW3) | Display | None | `cues.enabled`, `cues.holdout_rate` | No cues |
| Roles, `find_sources` policies, library ask, compare (RW4) | Retrieval context and proposals | None (T6's ruling) | `source_roles.enabled`, `library_ask.enabled`, `compare_sources.enabled` | T6 as merged |
| Figures and predictions (RW5) | Content, formative | None | `figures.enabled` | — |
| Digest and router card section (RW6) | Content | None | `digest.enabled` | — |
| **Follow-up checks in the plan (RW6)** | **Serving** | **`reader_followup_v1`** | `followups.enabled` | The predecessor's plan, byte-identical |
| **Plan reading blocks follow the path (RW7)** | **Serving** | **`reading_path_v1`** | `reading_paths.plan_uses_path` | DL1's section order, byte-identical |

**For each successor** (`docs/algorithm-change-playbook.md`):
- append its tag to `SUCCESSOR_CHAIN`, with an upgrade function and a defaults-fingerprint snapshot;
- a shadow rebuild on a `fixtures-local/` backup-API copy of each tracked fixture, showing **zero** mastery, facet and projection deltas (both change serving only);
- a served-set diff in the phase review;
- the head fixture regenerated.

**Kill-switch parity is a gate** for every row: switch off, the RPCs it touches return byte-identical results to the predecessor on fixture copies.

---

## 13. Rollout

Every phase goes through `implementation_goal.md` §2's loop: implement, adversarial review (Codex, or Opus 5.5 when Codex is out), fix, gate, integrate. Phases merge one at a time. Keep at most three of them open at once; they all touch the Reader's frontend.

| Phase | Builds | Needs | Serving change | Gate and owner checkpoint |
|---|---|---|---|---|
| **RW1 Inquiry** | Port `origin/feat/reader-clarification-branches`; the rail split into components; inquiry status on `question_events.resolution`; breadcrumb and return; reconnect line and passage-scope quick check; the intent box with Decider routing; `learnloop reader report` baseline | `main` | None | G1–G4. **Checkpoint:** a week of reading, then the report's intent-vs-palette and correction rates |
| **RW2 Workbench** | §5 in full: steps, check, ladder, reconciliation contract, first-offer chooser, sympy checks, assistance mapping, reveal kind, diagnoser trace, stuck steps into text gaps and field signals | `main` (Slice 1 M2, PF sandbox, T6, stuck prompt). RW1 for the rail split. ChatGPT-plan provider preferred for latency. `learner/text-gaps` merged for its source (otherwise the source yields nothing, as that branch's own stuck adapter does) | None (D6) | G5–G12. **Checkpoint:** the workbench report (help levels by facet over time, recovery after checks, latency) |
| **RW3 Passage cues** | §6: the `passage_gap` match kind, links, judge, margin UI, holdout, impressions | `main` (T1, T6, Slice 1). `learner/text-gaps` merged for gap targets (cues work without them). RW1 | None | G13–G16. **Checkpoint:** cue report (not-relevant rate, check-me rate, holdout comparison once there is data) |
| **RW4 Library and syntopic** | §7: role index, `find_sources` and policies, library ask with organizer and tutor, compare sources, practice this question, the roles backfill command | `main` (T6, Phase 5b). RW1 | None | G17–G20 |
| **RW5 Figures** | §8: spec, grammar, both evaluators with the golden corpus, renderer (four panel types), verification, predictions, cache | `main` (PF sandbox). RW1 for the intent-box entry | None | G21–G24 |
| **RW6 Loop closure** | §9: sessions, digest, the router card function, follow-up chooser and selection, scheduled-check class in the plan, `reader_followup_v1` | DL1 and DL2 merged (scheduled checks, effective due); RW2 (assisted-only work); `learner/text-gaps` | `reader_followup_v1` | G25–G27. **Checkpoint:** two weeks, then the follow-up outcomes block |
| **RW7 Reading paths** | §10: path judge, Guide display, plan reading block under `reading_path_v1` | DL1 and DL2 merged; RW4 (roles); Phase 6 (assumptions; merged) | `reading_path_v1` | G28–G29 |
| *Router R2 (router spec)* | Renders `ReaderActivityV1` in the card | R1; DL1; RW6 for the reader section (R2 may land first and add it later) | Router's successor | Router gates |
| *Router §15.3 (router spec)* | The router and tutor call `find_sources` as a tool | Its own trigger | Router's | Router gates |

**Recommended order:** RW1 first (it splits the rail). Then RW2 alongside RW5 (independent files) and RW4. Then RW3. Then RW6 and RW7 as DL2 lands. RW2 is the core differentiator, and the owner's own pain point. RW1 is the cheapest, and most of it is already built.

---

## 14. Gates and tests

| # | Gate |
|---|---|
| G1 | **Branch port parity.** The branch's 12 backend and 9 frontend tests pass on `main`. A follow-up's prompt holds only its ancestors. T6's retrieval for a follow-up uses the follow-up's own question. Legacy flat histories read as roots |
| G2 | **Inquiry status is not evidence.** Resolving, reopening, "revisit once" and reconnect answers write no attempt, observation, mastery or FSRS row. The salience firewall test covers every new event kind |
| G3 | **Intent routing.** A routed action has exactly the effect of the same palette action (the same RPC and payload). An unavailable, timed-out or spent-out Decider routes to Ask. "change" records a `learner_card` verdict. With `reader_intent.enabled = false`, the selection UI is today's |
| G4 | **Reconnect questions are formative.** They write no attempt. Idempotency per inquiry root holds. Section quick checks are unchanged |
| G5 | **Assistance mapping.** For each level (0–5) and each combination, the submitted attempt's `hints_used`, `primed` and reveal rows match §5.4, and `classify_attempt_activity` gives the stated FSRS and certification eligibility (an attempt with any check or hint earns zero certification credit in both projections). A rebuild reproduces evidence identically. An abandoned session writes no attempt |
| G6 | **The grader stays blind.** The rendered blind-grading prompt for a workbench attempt contains the composed answer only: no step history, assist text, hint or learner state (asserted on fixtures) |
| G7 | **Reconciliation contract.** A fake hint writer that cites no learner step, continues from a step after the first questionable one, or repeats a strategy a third time is caught, re-asked once, then downgraded as §5.1 says |
| G8 | **Leak control.** A level-1–3 hint containing the expected answer (including short numeric answers) is never shown. Bridging retrieval never returns the item's exercise or solution blocks |
| G9 | **Symbolic labels.** "checked" appears only when the sandbox verified the step. Without bubblewrap, every verdict reads "model's reading" |
| G10 | **Source visibility.** A Reader workbench attempt with the source visible is an instructional administration and earns zero certification credit in both projections. "Hide the source" makes an ordinary attempt. Opening the source afterwards records contamination |
| G11 | **Workbench kill switch.** With `workbench.enabled = false`, practice RPCs and screens are byte-identical to the predecessor on fixture copies |
| G12 | **Spend.** Per-session and daily caps hold. A capped session keeps authored hints. Codex receipts are `estimated_only` |
| G13 | **Cues are display only.** With cues on or off, evidence, mastery, projections, FSRS and the plan are byte-identical. "Check me" produces an ordinary learner-pick attempt |
| G14 | **Restraint and holdout.** No section shows more than the cap. No cue in skim mode. The logged propensity equals the draw probability, and seeds reproduce draws |
| G15 | **Judges decide.** With the judge stubbed to `none`, no cue appears, whatever the embedding ranks (R1). Every shown cue has a ledger verdict and a verified quote |
| G16 | **Wording.** Cue copy comes from fixed templates. A lint test rejects "weak", "you don't understand", "you struggle" and similar |
| G17 | **Sources first.** A library ask returns passages and organizer lines, never a tutor essay, until the learner asks the tutor. Each organizer line cites exactly one returned hit |
| G18 | **Compare keeps sources apart.** Every claim shown quotes a verified span of its own source. Relations are `proposed` source-object relations, and no concept edge, facet merge or prerequisite is written (asserted by table diff) |
| G19 | **Retrieval policies.** `cold_attempt` returns nothing. `assisted_practice` returns no `exercise` or `solution` block and nothing leaking the item's answer. Policies are recorded on every manifest |
| G20 | **RW4 kill switches** restore T6's library search, tutor spans and Quick Add behaviour byte-identically |
| G21 | **No generated code runs.** The grammar parser rejects everything outside the grammar (fuzzed). The renderer has no `eval` or `Function`, enforced by a lint rule |
| G22 | **Two evaluators agree** on the golden corpus within 1e-9 relative error, and the corpus covers every grammar construct |
| G23 | **Labels follow verification.** "matches the source's equation" appears only after step 3 passed. A figure failing steps 1 or 2 is never shown |
| G24 | **Predictions are formative.** They write no attempt, observation or signal |
| G25 | **Digest and card.** The typed summary is deterministic from the ledgers (rebuilt twice, identical). The narrative cites only ids in the summary. `ReaderActivityV1` contains no cold-answer or reserved-surface material (router G5) |
| G26 | **Follow-ups are unfamiliar and verified.** Never the same surface; never an exposed family whose solution the session revealed; only verified generated items; at most one per session and `plan.reader_followups_max_per_day` per day; served cold, with restoration after |
| G27 | **`reader_followup_v1` parity.** With `followups.enabled = false`, plan builds equal the predecessor's. Shadow rebuild with zero projection deltas |
| G28 | **Honest path labels.** `already shown` only with a demonstrated predicate; `assumed` only with an open assumption; otherwise `core` |
| G29 | **`reading_path_v1` parity.** With `plan_uses_path = false`, reading blocks equal DL1's. Shadow rebuild with zero projection deltas |

**Every phase also holds:** replay and rebuild make zero model and embedding calls with its tables populated; every new RPC is pinned desktop-only in `tests/test_mobile_allowlist.py`; every new table is classified in `db/table_roles.py`.

**Tests** (fakes only: `tests/structured_ai.py`, `tests/openai_fakes.py`, a fake Decider; vault builders from `tests/helpers.py`):
- **RW1:** the branch's `test_reader_branches.py` and `ReaderAskBranches.test.tsx`, ported; `test_reader_inquiry_status.py`; `test_reader_intent.py` (routing, fallbacks, correction verdicts, palette parity); `test_reader_reconnect.py`; `test_reader_report.py`; vitest for `IntentBox` and the breadcrumb.
- **RW2:** `test_workbench_steps.py`; `test_workbench_check.py` (sympy-checked and model-read labels, the bubblewrap-missing path); `test_workbench_hints.py` (the reconciliation contract, strategy change, leak control, bridging exclusions); `test_workbench_assistance.py` (G5 table-driven, replay); `test_workbench_blind.py` (G6); `test_workbench_source_visibility.py` (G10); `test_workbench_chooser.py` (inputs, fallback, logging); `test_workbench_kill_switch.py`; `test_workbench_text_gaps.py`; vitest for the workbench layout, ladder and stuck box.
- **RW3:** `test_passage_links.py` (the match kind, judge-decides, state-fingerprint recompute); `test_reader_cues.py` (cap, skim, holdout propensity, taps to the ledger, display-only parity); a wording lint; vitest for margin marks.
- **RW4:** `test_source_roles.py`; `test_find_sources_policies.py` (G19); `test_library_ask.py` (G17, the personalization toggle, practice this question); `test_compare_sources.py` (G18); `test_rw4_kill_switches.py`.
- **RW5:** `test_figure_grammar.py` and `figureGrammar.test.ts` (the golden corpus, fuzz); `test_figure_verification.py` (invariants, source match, downgrade, refusal); `test_figure_predictions.py`; vitest for the renderer's four panels.
- **RW6:** `test_reader_digest.py`; `test_reader_activity_card.py`; `test_reader_followups.py` (selection constraints, generation-if-none, verified-only, date rule, caps, cold serving, undo); `test_reader_followup_successor.py` (parity, shadow).
- **RW7:** `test_reading_paths.py` (honest labels, recompute, overrides); `test_reading_path_successor.py`.

**Every phase runs** `uv run lint-imports --no-cache`, `uv run pytest -n auto`, `uv run pytest -m durability`, `npm run typecheck && npm test` (the frontend changes in every phase), and the DB reference generate and validate scripts when the schema changed.

---

## 15. Evaluation: learning, not engagement

The dialogue's warning applies: a better Reader may produce *fewer* interactions, because the learner gets unstuck sooner. So `learnloop reader report` reports outcomes first. As everywhere at n=1, these are **reports with noise floors, not thresholds** (R6).

| Block | Measures | Phase |
|---|---|---|
| Baseline | Visits, minutes, time to first action, intent-box vs palette use, routing corrections, asks, branch depth, inquiries opened, resolved and reopened | RW1 |
| Workbench | Sessions; help level taken vs offered, by facet over time (**hint dependence**); recovery: the share of checks followed by a valid next step without further help; time stuck (from a questionable verdict to the next valid step); submissions vs abandons; grade by highest level used; check and hint latency p50 and p95 | RW2 |
| Cues | Impressions, open, check-me and not-relevant rates; cues per reading hour (**interruption burden**); next attempt on the cue's facets for shown vs held-out cues, IPS-weighted by the logged propensity, with an interval and its sample size | RW3 |
| Library | Asks, tutor follow-up rate, practice-this-question pick rate, compare usage, organizer-line validation failures | RW4 |
| Figures | Requests, verified / illustrative / failed shares, predictions made and missed | RW5 |
| Loop closure | Follow-ups scheduled, undone, served and answered; **cold success after assisted reader work** (the dialogue's primary outcome), beside cold success on comparable items without reader help; digest dismissal rate | RW6 |
| Paths | Sections skipped as shown or assumed, and those LOs' later first-review miss rate; overrides | RW7 |

The three experiments the dialogue proposes map as follows:
- **Generic vs work-aligned hints** is *not* run: it would deliberately give worse help. The reconciliation contract is the design, and recovery and dependence are tracked.
- **Cues vs no cues** is the RW3 holdout.
- **Summaries alone vs typed evidence plus summaries for routing** belongs to router R3, whose replay can ablate the card's reader section.

---

## 16. Decisions: recommended defaults (each default; owner may override)

| # | Decision | Recommended default |
|---|---|---|
| D1 | Phase order | RW1 → RW2 alongside RW5 and RW4 → RW3 → RW6 and RW7 after DL2 (§13) |
| D2 | The selection's first interaction | The intent box, with the palette one key away (Tab). An empty Enter asks |
| D3 | Who routes the intent box | The Decider (one typed `choice`, about 2 s); fallback Ask. The LLM route is an alternative by config |
| D4 | Inquiry status | Reuse `question_events.resolution`, plus `test_me_later` / `help_me_remember` commitments. No new status words |
| D5 | Port or rebuild branching Ask | Port `origin/feat/reader-clarification-branches` (rebase on `main`, resolve against T6) |
| D6 | Workbench evidence mapping | Levels 1–3 and checks add to `hints_used` (assisted: schedules, never certifies); levels 4–5 make the attempt `primed` (no FSRS, no certification); hint text overlapping the key is a `workbench_hint` reveal. No new discount rule, so no successor |
| D7 | Workbench model routes | The ChatGPT-plan provider when merged (fast, tool-free); until then a fast OpenRouter chat profile. Codex only if the latency report is acceptable |
| D8 | First-offer help level | A judgment: the Decider over typed state plus the learner's help style (default "balanced"). Kill switch to "level 1, then up" |
| D9 | Workbench in the Reader | The source is visible by default (an instructional, never-certifying attempt), with "Hide the source" for a cold-eligible attempt. Practice-screen and plan workbenches hide it |
| D10 | Cue restraint | At most 2 per section, none in skim mode, a 10% logged holdout. Set `holdout_rate = 0` to always show |
| D11 | Cue kinds | Both "revisit a distinction" and "a new application of something you've shown" |
| D12 | Library answers | Sources first, organized by role and source; the tutor on request; personalization on, with a toggle |
| D13 | Compare-sources relations | Shown as AI-proposed source-object relations. Never canonical, and no review queue (frictionless R1) |
| D14 | Role index | Computed on demand per opened source (capped), plus an owner-run backfill command |
| D15 | Figures | Declarative only; unverified reconstructions are downgraded to labelled illustrations; one prediction prompt per figure by default |
| D16 | Session digest | On, with the narrative on. A dismissible end-of-session panel |
| D17 | Cold follow-ups | Automatic, at most one per session and two a day, labelled, with undo. The date is the practiced item's effective due (1–14 days), with a 3-day fallback. `find_practice` first, verified PF generation only if nothing fits |
| D18 | Reading paths in the plan | On under `reading_path_v1`: reading blocks follow core and prerequisite sections; enrichment is never planned |
| D19 | Spend | Metered caps of $1.00 a day each for the workbench and library, $0.50 for cues; Codex `estimated_only` |
| D20 | Phone | No new RPC is phone-allowed in v1 |

---

## 17. Deferred, with triggers

| Deferred | Revisit when |
|---|---|
| **The router querying sources as a tool** (`find_sources`, `find_examples` with typed constraints, retrieved candidates in the logged set) | Router §15.3's own trigger: R2 live and T6's hybrid-vs-dense re-evaluation settled. RW4's facade and policies are the surface it calls |
| **OS-level learning service** (an MCP server exposing `find_sources`, `find_practice` and `capture.create`; editor or browser capture) | DL3's capture box is used most days *and* the owner reports capturing from another app as a gap (the same trigger as DL §15's browser extension) |
| **Generated-code figures** in an isolated, unprivileged surface | The RW5 report counts ≥ 10 requests the four panel types couldn't express, *and* a Tauri isolation design (no IPC, files or network for the surface) is reviewed |
| **More figure panels** (vector fields, dynamical systems, attention maps) | The same report names the missing panel type ≥ 5 times |
| **Page-image retrieval** (ColQwen, Qwen3-VL) | T6 open question 4's multimodal labeller rematch shows page images beating Marker text |
| **Local rerankers** (Qwen3-Reranker) | LLM verification latency is the measured bottleneck in the RW4 or RW2 latency blocks |
| **Learned cue and hint policies** (the dialogue's value function over learning gain, information gain and interruption cost) | ≥ 500 cue impressions with matured outcomes and holdout propensities, *and* router §13's learned-scorer conditions, read the same way |
| **Using figure predictions and reconnect answers as weak observations** | The RW5 and RW1 reports show missed predictions or "still unclear" answers precede later misses on the same LO (directional, with an interval) |
| **Full solution graphs** with alternative branches | The workbench report shows learners rejecting hints as "not my approach" in ≥ 20% of hint sessions over a month |
| **A CAS calculator in the workbench** | The owner asks. It would need its own assistance mapping |
| **Photo of handwritten work as workbench steps** | DL4's `image_transcription` route is merged |
| **Workbench and figures on video transcripts** | The owner works exercises from transcript sources |
| **Randomized hint-quality experiments** | Not planned: they would withhold better help on purpose |

---

## 18. Cross-spec notes (record when each phase merges)

- **P3 Reader spec.** §5.4's inquiry-thread projection is implemented through `question_events.resolution` and branch parents, with no projection table. §1.3's "syntopic comparison UI" exclusion is lifted by RW4, under §7.1–7.2's source-local rules. Invariants 1, 6, 9 and 10 are restated as W12, W1, W2 and W7.
- **Quick-check producer.** Gains a passage scope for inquiry roots (RW1); section behaviour is unchanged.
- **Daily loop.**
  - §6.1's scheduled-check class gains reader follow-ups, capped by `plan.reader_followups_max_per_day`, under `reader_followup_v1` (RW6).
  - §6.10's reading block follows the path under `reading_path_v1` (RW7).
  - DL4's pre-questions and RW1's reconnect question share the quick-check producer.
  - The intent box's "remember" and "test me later" call the reader presets, which DL4 moves onto capture adoption. The intent box needs no change when DL4 lands.
- **Router.**
  - `LearnerStateCardV1` gains the "Reader activity" section from `reader_activity_for_card` (RW6).
  - The Reader's in-session help (hint level choice, cues) is not a router decision, matching router §1 (within-block selection stays outside the router).
  - §15.3 calls RW4's `find_sources` with its policies; its retrieved candidates join the logged set as §15.3 says.
- **Embedding consumers.**
  - T6 gains consumers (workbench bridging, cue shortlists, the library organizer, compare) and the role-based exclusion. R1–R6 hold.
  - B4's text-only decision stands.
  - T1's matcher gains the kinds `passage_gap` and `same_claim`.
  - PF-b serves RW6's follow-ups when `find_practice` finds nothing (verified only).
- **Blind grading and diagnosis.** The grader is unchanged (G6). The diagnoser's context gains the current attempt's workbench trace when one exists, so contexts without one hash as before.
- **Learner field.** Workbench assistance flows into `hints_used` and `primed`, so the `+hints` arm sees it. Stuck steps emit `stuck_confusion`. Cues, figures, digests and inquiry status are not signals (W1).
- **Learner-text gaps.** New sources: workbench stuck steps, and RW1's "what's still unclear?" text. Named gaps become RW3 cue targets.
- **Knowledge model.** Passage links, roles and source relations are labels and proposals. They never touch facet identity (§3) or the semantic graph (§8.1).
- **Mobile.** No new phone RPC. Every new RPC is pinned desktop-only.
- **Handoffs.** Add a "Reader workbench" row to `implementation_handoffs.md` §1 per phase, using §19.

---

## 19. Agent prompt template

Fill in `<n>` (RW1–RW7), the phase row from §13 and the base branch. Give it to a fresh agent in the repo. The review and fix steps follow `implementation_goal.md` §2.

```text
Implement LearnLoop reader-workbench phase RW<n>, as specified in
docs/specs/spec_reader_workbench_v1.md (§13 row "RW<n>", plus the sections that row cites).

Before coding, read: CLAUDE.md; docs/specs/implementation_handoffs.md §0 (standard rules
and invariants); spec_reader_workbench_v1.md in full; spec_p3_reader_integration.md §1.1;
docs/specs/daily_loop_frictionless_defaults.md; the sections of other specs the row names;
db/table_roles.py; docs/algorithm-change-playbook.md. Then write a short plan (files,
migrations, successor and kill switches, spend caps and model routes, judgment_ledger
writes, tests) to docs/reviews/reader-workbench-rw<n>.md and proceed.

Work in your own worktree on a new branch reader/rw<n>, created from <base branch>.
Follow §0 of the handoffs and §2 of the spec, especially:
- reading, help, cues, figures, digests and inquiry status never write evidence; the
  only evidence is a submitted attempt, with assistance recorded as §5.4 says;
- the grader stays blind (G6); retrieval follows find_sources' policies (§7.2);
- only the successors §12 lists for this phase; with each kill switch off, behaviour
  is byte-identical to the predecessor;
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
changed; a shadow rebuild on a fixtures-local copy is reported for any successor. The
review file lists what was built, deviations, test results with pass counts, files
touched, migrations, owner-run commands (dry-run first) and open questions. Commit with
clear messages; do not merge or push.
```

---

*Related: `docs/brainstorming/Improving Reader's design.md` (source) · `spec_p3_reader_integration.md` · `spec_reader_quick_check_producer.md` · `spec_daily_loop_v1.md` (§5, §6.1, §6.10) · `spec_embedding_consumers_v1.md` (§1, §5.9, §9) · `spec_action_router_v1.md` (§4, §15) · `spec_blind_grading_diagnosis_split_v1.md` · `spec_learner_field_v1.md` (§3.1) · `implementation_handoffs.md` §4 · `docs/reviews/slice-2-t6.md` · `docs/reviews/stuck-prompt.md`*
